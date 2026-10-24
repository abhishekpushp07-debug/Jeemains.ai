# Iteration 18 retest: duel start_at = now + 4.6 s, opponent-forfeit flag visible to the remaining player, leaderboard single-flight cache
import os
import time
import uuid
import concurrent.futures as cf
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


def _invite_join(s, subject="Physics"):
    uid_b = "TESTUSER" + uuid.uuid4().hex[:10]
    a = s.post(f"{BASE_URL}/api/rf/duels", json={"subject": subject, "chapter": None, "mode": "invite", "name": "Player ··0001",
                                                 "request_id": "TEST_" + uuid.uuid4().hex}, headers=H(UID_A)).json()
    assert a["status"] == "waiting"
    b = s.post(f"{BASE_URL}/api/rf/duels/join", json={"code": a["code"], "name": "TEST_B"}, headers=H(uid_b)).json()
    assert b["status"] == "ready"
    return a, b, uid_b


def _cleanup(s, did, uids):
    for u in uids:
        s.post(f"{BASE_URL}/api/rf/duels/{did}/forfeit", headers=H(u))


# Invite + join: start_at is ~4.6 s after server_now (was 5.5)
def test_invite_join_start_at_4_6(s):
    a, b, uid_b = _invite_join(s)
    delta = b["start_at"] - b["server_now"]
    print("invite start_at - server_now =", round(delta, 3))
    assert 4.3 <= delta <= 4.7
    _cleanup(s, a["id"], [UID_A, uid_b])


# Quick match -> AI rival (bot): start_at is ~4.6 s after server_now
def test_bot_start_at_4_6(s):
    a = s.post(f"{BASE_URL}/api/rf/duels", json={"subject": "Chemistry", "chapter": None, "mode": "invite", "name": "Player ··0001",
                                                 "request_id": "TEST_" + uuid.uuid4().hex}, headers=H(UID_A)).json()
    v = s.post(f"{BASE_URL}/api/rf/duels/{a['id']}/bot", headers=H(UID_A)).json()
    assert v["status"] == "ready" and v["vs_bot"] is True
    delta = v["start_at"] - v["server_now"]
    print("bot start_at - server_now =", round(delta, 3))
    assert 4.3 <= delta <= 4.7
    _cleanup(s, a["id"], [UID_A])


# Opponent forfeit: A's view of the duel must expose opp forfeit (frontend banner uses opp.forfeit)
def test_opponent_forfeit_visible_to_a(s):
    a, b, uid_b = _invite_join(s)
    r = s.post(f"{BASE_URL}/api/rf/duels/{a['id']}/forfeit", headers=H(uid_b))
    assert r.status_code == 200
    g = s.get(f"{BASE_URL}/api/rf/duels/{a['id']}", headers=H(UID_A)).json()
    opp = [p for p in g["players"] if not p["you"]][0]
    print("status", g["status"], "opp keys", sorted(opp.keys()), "opp", {k: opp.get(k) for k in ("done", "forfeit")})
    _cleanup(s, a["id"], [UID_A])
    assert opp.get("forfeit") is True, "players[].forfeit is not serialised in view(); duel-opponent-left banner can never render"


# Leaderboard: ranked, sorted, no TEST_ rows; concurrent burst returns identical non-empty boards
def test_leaderboard_single_flight(s):
    r = s.get(f"{BASE_URL}/api/rf/leaderboard", headers=H(UID_A))
    assert r.status_code == 200
    items = r.json()["items"]
    assert 0 < len(items) <= 20
    assert [i["rank"] for i in items] == list(range(1, len(items) + 1))
    assert all(not str(i["name"]).startswith("TEST_") for i in items)
    xs = [i["xp"] for i in items]
    assert xs == sorted(xs, reverse=True)
    time.sleep(16)  # let the 15 s cache expire, then burst

    def one(_):
        return requests.get(f"{BASE_URL}/api/rf/leaderboard", headers=H(UID_A), timeout=20).json()["items"]
    with cf.ThreadPoolExecutor(20) as ex:
        res = list(ex.map(one, range(20)))
    lens = [len(x) for x in res]
    print("burst lengths", lens)
    assert all(l > 0 for l in lens)
    assert all([i["rank"] for i in x] == list(range(1, len(x) + 1)) for x in res)
