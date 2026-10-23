# Rapid Fire iteration 11: profile counters per run kind (solo all-skip / solo played / bot duel / human duel)
import os
import time
import uuid
import pytest
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv("/app/frontend/.env")
load_dotenv("/app/backend/.env")
BASE_URL = (os.environ.get("EXPO_BACKEND_URL") or os.environ.get("EXPO_PUBLIC_BACKEND_URL")).rstrip("/")
API = f"{BASE_URL}/api/rf"
DB = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]


def H(u):
    return {"X-RF-User": u}


def new_uid():
    return "TEST-" + uuid.uuid4().hex[:16]


def cleanup(*uids):
    for u in uids:
        DB.rf_profiles.delete_many({"uid": u})
        DB.rf_sessions.delete_many({"user_id": u})
        DB.rf_awards.delete_many({"uid": u})
        DB.rf_duels.delete_many({"players.uid": u})


@pytest.fixture
def uid():
    u = new_uid()
    yield u
    cleanup(u)


@pytest.fixture
def pair():
    a, b = new_uid(), new_uid()
    yield a, b
    cleanup(a, b)


def prof(u):
    return DB.rf_profiles.find_one({"uid": u}) or {}


def counters(u):
    p = prof(u)
    return {k: p.get(k, 0) for k in ("sessions", "duels", "wins", "rival_games")}


def solo(u, outcome):
    r = requests.post(f"{API}/sessions", json={"subject": "Physics", "count": 5, "request_id": uuid.uuid4().hex}, headers=H(u))
    assert r.status_code == 200, r.text
    s = r.json()
    if outcome == "skipped":
        res = [{"card_id": c["id"], "outcome": "skipped"} for c in s["cards"]]
    else:
        res = [{"card_id": c["id"], "outcome": "correct", "choice": c["answer"], "ms": 900} for c in s["cards"]]
    r = requests.post(f"{API}/sessions/{s['id']}/complete", json={"results": res}, headers=H(u))
    assert r.status_code == 200, r.text
    return r.json()


def wait_counters(u, key, want, timeout=8):
    end = time.time() + timeout
    c = counters(u)
    while time.time() < end and c[key] < want:
        time.sleep(0.4)
        c = counters(u)
    return c


class TestSoloCounters:
    def test_all_skip_solo_increments_nothing(self, uid):
        d = solo(uid, "skipped")
        assert d["reward"]["played"] is False
        c = counters(uid)
        assert c == {"sessions": 0, "duels": 0, "wins": 0, "rival_games": 0}, c
        api = requests.get(f"{API}/profile", headers=H(uid)).json()
        assert api.get("sessions", 0) == 0 and api.get("duels", 0) == 0

    def test_many_all_skip_cannot_farm_duelist(self, uid):
        for _ in range(3):
            solo(uid, "skipped")
        p = prof(uid)
        assert p.get("duels", 0) == 0 and "duelist_10" not in p.get("badges", [])

    def test_answered_solo_increments_sessions_only(self, uid):
        solo(uid, "correct")
        c = counters(uid)
        assert c == {"sessions": 1, "duels": 0, "wins": 0, "rival_games": 0}, c


class TestDuelCounters:
    def test_bot_duel_increments_rival_games(self, uid):
        r = requests.post(f"{API}/duels", json={"subject": "Physics", "mode": "random", "name": "TEST_Bot", "request_id": uuid.uuid4().hex}, headers=H(uid))
        assert r.status_code == 200, r.text
        did = r.json()["id"]
        r = requests.post(f"{API}/duels/{did}/bot", headers=H(uid))
        assert r.status_code == 200, r.text
        d = r.json()
        time.sleep(max(0, d["start_at"] - d["server_now"]) + 0.3)
        for i in range(d["total"]):
            r = requests.post(f"{API}/duels/{did}/answer", json={"index": i, "choice": 0, "outcome": "answer", "ms": 800}, headers=H(uid))
            assert r.status_code == 200, (i, r.text)
        c = wait_counters(uid, "rival_games", 1)
        assert c["rival_games"] == 1 and c["duels"] == 0 and c["sessions"] == 0, c

    def test_human_duel_increments_duels(self, pair):
        a, b = pair
        ra = requests.post(f"{API}/duels", json={"subject": "Physics", "mode": "invite", "name": "TEST_A", "request_id": uuid.uuid4().hex}, headers=H(a))
        assert ra.status_code == 200, ra.text
        code = ra.json()["code"]
        jb = requests.post(f"{API}/duels/join", json={"code": code, "name": "TEST_B"}, headers=H(b))
        assert jb.status_code == 200, jb.text
        d = jb.json()
        did = d["id"]
        time.sleep(max(0, d["start_at"] - d["server_now"]) + 0.5)
        answers = []
        for i in range(d["total"]):
            r = requests.post(f"{API}/duels/{did}/answer", json={"index": i, "choice": 0, "outcome": "answer", "ms": 800}, headers=H(a))
            assert r.status_code == 200, (i, r.text)
            answers.append(r.json()["answer"])
        for i in range(d["total"]):
            r = requests.post(f"{API}/duels/{did}/answer", json={"index": i, "choice": answers[i], "outcome": "answer", "ms": 900}, headers=H(b))
            assert r.status_code == 200, (i, r.text)
        fin = requests.get(f"{API}/duels/{did}", headers=H(b)).json()
        assert fin["status"] == "finished"
        ca = wait_counters(a, "duels", 1)
        cb = wait_counters(b, "duels", 1)
        assert ca["duels"] == 1 and cb["duels"] == 1, (ca, cb)
        assert ca["sessions"] == 0 and cb["sessions"] == 0 and ca["rival_games"] == 0
        winner = fin["winner"]
        assert (ca["wins"], cb["wins"]) == ((1, 0) if winner == a else (0, 1)), (winner, ca, cb)
