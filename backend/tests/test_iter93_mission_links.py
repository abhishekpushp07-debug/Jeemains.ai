"""Iter93: Mission share stats. GET /api/j/{code} friend counting + GET /api/rf/mission/me (RF grant).
Creates TEST- mission_links rows directly in Mongo and removes them (and their mission_visits) by exact code."""
import os
import secrets
import time
import uuid

import pytest
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv("/app/backend/.env")
load_dotenv("/app/frontend/.env")
BASE = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "").rstrip("/")
ALPHA = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
db = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]


def ua(n):
    return f"Mozilla/5.0 (Linux; Android 14; Pixel {n}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.{n}.{secrets.randbelow(9999)} Mobile Safari/537.36"


def helped(code):
    return db.mission_links.find_one({"code": code})["helped"]


@pytest.fixture
def link():
    code = "".join(secrets.choice(ALPHA) for _ in range(7))
    db.mission_links.insert_one({"uid": f"TEST-iter93-{uuid.uuid4().hex[:10]}", "code": code, "helped": 0, "created_ts": time.time()})
    yield code
    db.mission_links.delete_one({"code": code})
    db.mission_visits.delete_many({"code": code})


def hit(code, user_agent, session=None, path_code=None):
    s = session or requests.Session()
    return s.get(f"{BASE}/api/j/{path_code or code}", headers={"User-Agent": user_agent} if user_agent is not None else {}, allow_redirects=False, timeout=20)


# Redirect + cookie on first visit, counted once
def test_redirect_cookie_and_first_count(link):
    s = requests.Session()
    r = hit(link, ua(1), s)
    assert r.status_code == 302
    assert r.headers["location"].rstrip("/") == "https://jeelive.ai"
    assert "no-store" in r.headers.get("cache-control", "")
    assert "jlv=" in r.headers.get("set-cookie", "")
    assert helped(link) == 1
    # same cookie + same UA again: not counted, no new cookie
    r2 = hit(link, ua(1), s)
    assert r2.status_code == 302 and "jlv=" not in r2.headers.get("set-cookie", "")
    assert helped(link) == 1
    v = db.mission_visits.find_one({"code": link, "key": {"$regex": "^c:"}, "counted": True})
    assert v is not None


# Same cookie, different UA -> cookie not new -> not counted; new cookie same UA -> device not new -> not counted
def test_both_keys_must_be_new(link):
    s = requests.Session()
    u = ua(2)
    hit(link, u, s)
    assert helped(link) == 1
    hit(link, ua(3), s)  # same cookie, new device
    assert helped(link) == 1
    hit(link, u)  # fresh cookie, same device
    assert helped(link) == 1
    hit(link, ua(4))  # fresh cookie + new device
    assert helped(link) == 2


# Distinct friends counted
def test_three_friends(link):
    for i in range(3):
        hit(link, ua(10 + i))
    assert helped(link) == 3


@pytest.mark.parametrize("bot", ["WhatsApp/2.23.20.0 A", "facebookexternalhit/1.1", "TelegramBot (like TwitterBot)", "curl/8.4.0",
                                 "python-requests/2.31", "Mozilla/5.0 HeadlessChrome/126.0", "Mozilla/5.0 Playwright/1.4", ""])
def test_robots_not_counted(link, bot):
    r = hit(link, bot)
    assert r.status_code == 302 and r.headers["location"].rstrip("/") == "https://jeelive.ai"
    assert helped(link) == 0
    assert db.mission_visits.count_documents({"code": link}) == 0


def test_lowercase_code_counted(link):
    r = hit(link, ua(20), path_code=link.lower())
    assert r.status_code == 302
    assert helped(link) == 1


@pytest.mark.parametrize("code", ["ZZZZZZ2", "abc", "ABCDEFGH", "AB0DEFG", "AB-DEFG"])
def test_unknown_or_malformed_code(code):
    r = hit(code, ua(30))
    assert r.status_code == 302 and r.headers["location"].rstrip("/") == "https://jeelive.ai"
    assert db.mission_visits.count_documents({"code": code.upper()}) == 0


# /api/rf/mission/me
def test_mission_me_requires_grant():
    r = requests.get(f"{BASE}/api/rf/mission/me", timeout=20)
    assert r.status_code == 401
    r = requests.get(f"{BASE}/api/rf/mission/me", headers={"Authorization": "Bearer nope"}, timeout=20)
    assert r.status_code == 401


@pytest.fixture(scope="module")
def grant():
    phone, pin = os.environ.get("QA_PHONE"), os.environ.get("QA_PIN")
    if not phone or not pin:
        pytest.skip("QA_PHONE/QA_PIN not set")
    sid = str(uuid.uuid4())
    r = requests.post(f"{BASE}/api/jl/auth/phone", headers={"X-JL-Sid": sid}, json={"phone": phone, "pin": pin}, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"login {r.status_code}")
    a = requests.post(f"{BASE}/api/rf/access", headers={"X-JL-Sid": sid}, json={}, timeout=30)
    if a.status_code != 200:
        pytest.skip(f"rf/access {a.status_code}")
    return {"Authorization": "Bearer " + a.json()["token"]}


def test_mission_me_stable(grant):
    a = requests.get(f"{BASE}/api/rf/mission/me", headers=grant, timeout=20)
    b = requests.get(f"{BASE}/api/rf/mission/me", headers=grant, timeout=20)
    assert a.status_code == 200 and b.status_code == 200
    ja, jb = a.json(), b.json()
    assert set(ja) == {"code", "helped", "week"}
    assert ja["code"] == jb["code"] and len(ja["code"]) == 7
    assert isinstance(ja["helped"], int) and isinstance(ja["week"], int)
    row = db.mission_links.find_one({"code": ja["code"]})
    assert row["helped"] == ja["helped"]
    wk = db.mission_visits.count_documents({"code": ja["code"], "counted": True, "ts": {"$gte": time.time() - 7 * 86400}})
    assert wk == ja["week"]
    print("mission/me", ja)
