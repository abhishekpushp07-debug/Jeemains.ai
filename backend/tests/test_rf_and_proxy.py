# Rapid Fire (/api/rf/*) and jeelive pass-through proxy (/api/jl/*) regression tests
import os
import uuid
import pytest
import requests
from dotenv import load_dotenv

load_dotenv("/app/frontend/.env")
BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL").rstrip("/")
UID = "db0c62b8-eeaf-41be-b8b1-05f5f34ac1d8"
H = {"X-RF-User": UID}
SID = "TESTSID" + uuid.uuid4().hex[:20]


@pytest.fixture(scope="module")
def s():
    return requests.Session()


# ---------- Rapid Fire catalog ----------
def test_catalog(s):
    r = s.get(f"{BASE_URL}/api/rf/catalog")
    assert r.status_code == 200
    d = r.json()
    names = [x["name"] for x in d["subjects"]]
    assert names == ["Physics", "Chemistry", "Mathematics"] or set(names) == {"Physics", "Chemistry", "Mathematics"}
    total = sum(x["total"] for x in d["subjects"])
    print("catalog total", total, [(x["name"], x["total"], len(x["chapters"])) for x in d["subjects"]])
    assert total >= 4000
    for sub in d["subjects"]:
        assert all("count" in c and "name" in c for c in sub["chapters"])


# ---------- Rapid Fire sessions ----------
def test_auth_required(s):
    assert s.post(f"{BASE_URL}/api/rf/sessions", json={"subject": "Physics", "request_id": "TESTreq12345"}).status_code == 401
    assert s.get(f"{BASE_URL}/api/rf/history").status_code == 401


def test_create_idempotent_and_complete(s):
    rid = "TEST_" + uuid.uuid4().hex
    body = {"subject": "Physics", "chapter": None, "count": 10, "request_id": rid}
    r1 = s.post(f"{BASE_URL}/api/rf/sessions", json=body, headers=H)
    assert r1.status_code == 200, r1.text
    d1 = r1.json()
    assert len(d1["cards"]) == 10 and d1["seconds_per_card"] == 20
    assert all(c["subject"] == "Physics" and len(c["options"]) == 4 for c in d1["cards"])
    assert "_id" not in d1 and "user_id" not in d1
    r2 = s.post(f"{BASE_URL}/api/rf/sessions", json=body, headers=H)
    assert r2.json()["id"] == d1["id"]
    assert [c["id"] for c in r2.json()["cards"]] == [c["id"] for c in d1["cards"]]
    cards = d1["cards"]
    # lie about correctness on card 0 (wrong choice claimed correct) & card 1 correct claimed incorrect
    res = [
        {"card_id": cards[0]["id"], "outcome": "correct", "choice": (cards[0]["answer"] + 1) % 4, "ms": 3000},
        {"card_id": cards[1]["id"], "outcome": "incorrect", "choice": cards[1]["answer"], "ms": 3000},
        {"card_id": cards[2]["id"], "outcome": "timed_out", "ms": 20000},
        {"card_id": cards[3]["id"], "outcome": "skipped"},
    ]
    rc = s.post(f"{BASE_URL}/api/rf/sessions/{d1['id']}/complete", json={"results": res}, headers=H)
    assert rc.status_code == 200, rc.text
    sm = rc.json()["summary"]
    print("summary", sm)
    assert sm["correct"] == 1 and sm["incorrect"] == 1 and sm["timed_out"] == 1 and sm["skipped"] == 7 and sm["total"] == 10
    rc2 = s.post(f"{BASE_URL}/api/rf/sessions/{d1['id']}/complete", json={"results": []}, headers=H)
    assert rc2.json()["summary"] == sm
    g = s.get(f"{BASE_URL}/api/rf/sessions/{d1['id']}", headers=H)
    assert g.status_code == 200 and g.json()["status"] == "completed"
    h = s.get(f"{BASE_URL}/api/rf/history", headers=H)
    assert h.status_code == 200
    assert any(i["id"] == d1["id"] for i in h.json()["items"])
    assert h.json()["totals"]["sessions"] >= 1
    # repeat missed
    missed = [cards[0]["id"], cards[2]["id"]]
    rm = s.post(f"{BASE_URL}/api/rf/sessions", json={"subject": "Physics", "card_ids": missed, "request_id": "TEST_" + uuid.uuid4().hex}, headers=H)
    assert rm.status_code == 200
    assert rm.json()["mode"] == "repeat_missed" and sorted(c["id"] for c in rm.json()["cards"]) == sorted(missed)


def test_chapter_session(s):
    cat = s.get(f"{BASE_URL}/api/rf/catalog").json()
    ch = next(c for c in cat["subjects"][1]["chapters"] if c["count"] >= 10)
    r = s.post(f"{BASE_URL}/api/rf/sessions", json={"subject": cat["subjects"][1]["name"], "chapter": ch["name"], "count": 10,
               "request_id": "TEST_" + uuid.uuid4().hex}, headers=H)
    assert r.status_code == 200
    assert all(c["chapter"] == ch["name"] for c in r.json()["cards"]) and len(r.json()["cards"]) == 10


def test_empty_selection_404(s):
    r = s.post(f"{BASE_URL}/api/rf/sessions", json={"subject": "Physics", "chapter": "TEST_NoSuchChapter", "request_id": "TEST_" + uuid.uuid4().hex}, headers=H)
    assert r.status_code == 404


def test_validation(s):
    assert s.post(f"{BASE_URL}/api/rf/sessions", json={"subject": "Biology", "request_id": "TEST_abcdefgh"}, headers=H).status_code == 422
    assert s.post(f"{BASE_URL}/api/rf/sessions", json={"subject": "Physics", "count": 50, "request_id": "TEST_abcdefgh"}, headers=H).status_code == 422
    assert s.post(f"{BASE_URL}/api/rf/sessions/nope/complete", json={"results": []}, headers=H).status_code == 404


# ---------- jeelive proxy ----------
def test_proxy_invalid_sid(s):
    assert s.get(f"{BASE_URL}/api/jl/auth/me", headers={"X-JL-Sid": "short"}).status_code == 400
    print("missing sid ->", s.get(f"{BASE_URL}/api/jl/auth/me").status_code)


def test_proxy_login_and_me(s):
    r = s.post(f"{BASE_URL}/api/jl/auth/phone", json={"phone": "9000000001"}, headers={"X-JL-Sid": SID})
    print("login", r.status_code, r.text[:300])
    assert r.status_code == 200
    me = s.get(f"{BASE_URL}/api/jl/auth/me", headers={"X-JL-Sid": SID})
    print("me", me.status_code, me.text[:300])
    assert me.status_code == 200
    assert UID in me.text
    other = s.get(f"{BASE_URL}/api/jl/auth/me", headers={"X-JL-Sid": "TESTSID" + uuid.uuid4().hex[:20]})
    print("other sid me", other.status_code, other.text[:200])
    assert UID not in other.text


def test_proxy_series(s):
    r = s.get(f"{BASE_URL}/api/jl/series/all-india-jee", headers={"X-JL-Sid": SID})
    print("series", r.status_code, r.text[:300])
    assert r.status_code == 200
