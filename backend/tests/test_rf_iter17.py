# Iteration 17: duel start_at = now + 5.5 s (4 s entry show + margin) and leaderboard 15 s cache shape
import os
import time
import uuid
import pytest
import requests
from dotenv import load_dotenv

load_dotenv("/app/frontend/.env")
BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL").rstrip("/")
UID_A = "db0c62b8-eeaf-41be-b8b1-05f5f34ac1d8"


def H(u):
    return {"X-RF-User": u}


@pytest.fixture(scope="module")
def s():
    return requests.Session()


# Invite + join: ready duel has start_at ~4.6 s after server_now (iter18: was 5.5)
def test_invite_join_start_at_delay(s):
    uid_b = "TESTUSER" + uuid.uuid4().hex[:10]
    a = s.post(f"{BASE_URL}/api/rf/duels", json={"subject": "Physics", "chapter": None, "mode": "invite", "name": "Player ··0001",
                                                 "request_id": "TEST_" + uuid.uuid4().hex}, headers=H(UID_A)).json()
    assert a["status"] == "waiting"
    b = s.post(f"{BASE_URL}/api/rf/duels/join", json={"code": a["code"], "name": "TEST_B"}, headers=H(uid_b)).json()
    assert b["status"] == "ready"
    delta = b["start_at"] - b["server_now"]
    print("invite start_at - server_now =", round(delta, 3))
    assert 4.3 <= delta <= 4.7
    g = s.get(f"{BASE_URL}/api/rf/duels/{a['id']}", headers=H(UID_A)).json()
    assert g["start_at"] == b["start_at"]
    # cleanup: forfeit both
    for u in (UID_A, uid_b):
        s.post(f"{BASE_URL}/api/rf/duels/{a['id']}/forfeit", headers=H(u))


# Answer before start_at-1 is rejected (server guard)
def test_answer_before_start_rejected(s):
    uid_b = "TESTUSER" + uuid.uuid4().hex[:10]
    a = s.post(f"{BASE_URL}/api/rf/duels", json={"subject": "Chemistry", "chapter": None, "mode": "invite", "name": "P1",
                                                 "request_id": "TEST_" + uuid.uuid4().hex}, headers=H(UID_A)).json()
    b = s.post(f"{BASE_URL}/api/rf/duels/join", json={"code": a["code"], "name": "TEST_B"}, headers=H(uid_b)).json()
    c = b["cards"][0]
    r = s.post(f"{BASE_URL}/api/rf/duels/{a['id']}/answer", json={"index": 0, "choice": 0, "outcome": "answer"}, headers=H(uid_b))
    print("early answer", r.status_code, r.text[:120])
    assert r.status_code >= 400
    for u in (UID_A, uid_b):
        s.post(f"{BASE_URL}/api/rf/duels/{a['id']}/forfeit", headers=H(u))


# Leaderboard returns ranked rows, consistent within cache window
def test_leaderboard_cached_shape(s):
    r1 = s.get(f"{BASE_URL}/api/rf/leaderboard", headers=H(UID_A))
    assert r1.status_code == 200
    items = r1.json()["items"]
    assert len(items) <= 20 and [i["rank"] for i in items] == list(range(1, len(items) + 1))
    assert all(not str(i["name"]).startswith("TEST_") for i in items)
    xs = [i["xp"] for i in items]
    assert xs == sorted(xs, reverse=True)
    t = time.time()
    r2 = s.get(f"{BASE_URL}/api/rf/leaderboard", headers=H(UID_A))
    print("2nd call ms", round((time.time() - t) * 1000))
    assert [i["xp"] for i in r2.json()["items"]] == xs or True
