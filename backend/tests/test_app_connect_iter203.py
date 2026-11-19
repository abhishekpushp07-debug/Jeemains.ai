# Iteration 203: app_connect fixes - _grant/mission_me 503 on malformed 200, mock re-send memory, signed-out regressions
import asyncio
import os
import sys
import time

import httpx
import pytest
import requests
from fastapi import HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
from tejas import app_connect as ac  # noqa: E402

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    for line in open("/app/frontend/.env"):
        if line.startswith("REACT_APP_BACKEND_URL="):
            BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
API = f"{BASE_URL}/api"


def run(c):
    return asyncio.get_event_loop().run_until_complete(c) if False else asyncio.run(c)


def resp(status, body):
    return httpx.Response(status, json=body, request=httpx.Request("GET", "http://x"))


class FakeReq:
    cookies = {"access_token": "TEST_cookie_value"}


@pytest.fixture(autouse=True)
def clean():
    ac._grants.clear(); ac._sent_mocks.clear()
    yield
    ac._grants.clear(); ac._sent_mocks.clear()


# _grant: malformed 200 answers -> 503 BUSY_ACCOUNT
@pytest.mark.parametrize("body", [{}, {"token": "t"}, {"expires_at": "2030-01-01T00:00:00Z"},
                                  {"token": "t", "expires_at": None}, {"token": "t", "expires_at": "garbage"}, [], "x"])
def test_grant_malformed_503(monkeypatch, body):
    async def fake(*a, **k):
        return resp(200, body)
    monkeypatch.setattr(ac, "_call", fake)
    with pytest.raises(HTTPException) as e:
        run(ac._grant("TEST_cookie"))
    assert e.value.status_code == 503 and e.value.detail == ac.BUSY_ACCOUNT


def test_grant_ok(monkeypatch):
    async def fake(*a, **k):
        return resp(200, {"token": "tok", "expires_at": "2099-01-01T00:00:00Z"})
    monkeypatch.setattr(ac, "_call", fake)
    assert run(ac._grant("TEST_cookie")) == "tok"


# mission_me: 200 without code -> 503
@pytest.mark.parametrize("body", [{}, {"dost": 3}, [], "x", 5])
def test_mission_me_malformed_503(monkeypatch, body):
    async def fake(req, m, p, content=None):
        return resp(200, body)
    monkeypatch.setattr(ac, "_as_student", fake)
    with pytest.raises(HTTPException) as e:
        run(ac.mission_me(FakeReq(), u={"id": "TEST_u"}))
    assert e.value.status_code == 503 and e.value.detail == ac.BUSY_ACCOUNT


def test_mission_me_ok(monkeypatch):
    async def fake(req, m, p, content=None):
        return resp(200, {"code": "AB2CDEF", "dost": 1})
    monkeypatch.setattr(ac, "_as_student", fake)
    r = run(ac.mission_me(FakeReq(), u={"id": "TEST_u"}))
    assert r.status_code == 200 and b"/j/AB2CDEF" in r.body


# _send_website_mocks memory logic
def _setup(monkeypatch, mocks, status=200):
    calls = {"db": 0, "send": 0}
    async def wm(uid):
        calls["db"] += 1
        return list(mocks["v"])
    async def st(req, m, p, content=None):
        calls["send"] += 1
        return resp(status, {})
    monkeypatch.setattr(ac, "website_mocks", wm)
    monkeypatch.setattr(ac, "_as_student", st)
    return calls


def test_mocks_first_call_sends_then_throttles_then_resends(monkeypatch):
    mocks = {"v": [{"id": "a", "score": 100}]}
    calls = _setup(monkeypatch, mocks)
    clock = [1000.0]
    monkeypatch.setattr(ac.time, "time", lambda: clock[0])
    run(ac._send_website_mocks(FakeReq(), "TEST_u"))
    assert calls == {"db": 1, "send": 1}
    clock[0] += 10  # within 30 s -> no DB
    run(ac._send_website_mocks(FakeReq(), "TEST_u"))
    assert calls == {"db": 1, "send": 1}
    clock[0] += 31  # recheck, unchanged, < 10 min -> no send
    run(ac._send_website_mocks(FakeReq(), "TEST_u"))
    assert calls == {"db": 2, "send": 1}
    clock[0] += 31
    mocks["v"] = [{"id": "a", "score": 100}, {"id": "b", "score": 120}]  # changed -> send
    run(ac._send_website_mocks(FakeReq(), "TEST_u"))
    assert calls == {"db": 3, "send": 2}
    clock[0] += 601  # unchanged but > 10 min -> resend
    run(ac._send_website_mocks(FakeReq(), "TEST_u"))
    assert calls == {"db": 4, "send": 3}


def test_mocks_unchanged_keeps_sent_at(monkeypatch):
    mocks = {"v": [{"id": "a", "score": 100}]}
    calls = _setup(monkeypatch, mocks)
    clock = [1000.0]
    monkeypatch.setattr(ac.time, "time", lambda: clock[0])
    run(ac._send_website_mocks(FakeReq(), "TEST_u"))
    for _ in range(19):  # 19*31 = 589 s, checks keep happening but sent_at stays 1000
        clock[0] += 31
        run(ac._send_website_mocks(FakeReq(), "TEST_u"))
    assert calls["send"] == 1
    clock[0] += 31  # now 620 s since send
    run(ac._send_website_mocks(FakeReq(), "TEST_u"))
    assert calls["send"] == 2


def test_mocks_empty_list_never_sends_but_throttles(monkeypatch):
    mocks = {"v": []}
    calls = _setup(monkeypatch, mocks)
    clock = [1000.0]
    monkeypatch.setattr(ac.time, "time", lambda: clock[0])
    run(ac._send_website_mocks(FakeReq(), "TEST_u"))
    run(ac._send_website_mocks(FakeReq(), "TEST_u"))
    assert calls == {"db": 1, "send": 0}
    clock[0] += 31
    mocks["v"] = [{"id": "a", "score": 1}]
    run(ac._send_website_mocks(FakeReq(), "TEST_u"))
    assert calls == {"db": 2, "send": 1}


def test_mocks_failed_send_backs_off_then_retries(monkeypatch):
    calls = _setup(monkeypatch, {"v": [{"id": "a", "score": 1}]}, status=422)
    clock = [1000.0]
    monkeypatch.setattr(ac.time, "time", lambda: clock[0])
    run(ac._send_website_mocks(FakeReq(), "TEST_u"))
    run(ac._send_website_mocks(FakeReq(), "TEST_u"))
    assert calls["send"] == 1 and ac._sent_mocks["TEST_u"][2] == 0
    clock[0] += 31
    run(ac._send_website_mocks(FakeReq(), "TEST_u"))
    assert calls["send"] == 2


# Live signed-out regressions
def test_live_mission_401():
    assert requests.get(f"{API}/mission/me", timeout=30).status_code == 401


def test_live_dream_401():
    assert requests.get(f"{API}/dream", timeout=30).status_code == 401


def test_live_share_redirect():
    r = requests.get(f"{API}/j/AB2CDEF", allow_redirects=False, timeout=30)
    assert r.status_code == 302 and r.headers["location"] == "https://jeelive-mobile.emergent.host/api/j/AB2CDEF"


def test_live_bitsat_280():
    r = requests.post(f"{API}/rank/bitsat", json={"score": 280}, timeout=30)
    assert r.status_code == 200, r.text[:200]
    assert r.json()
