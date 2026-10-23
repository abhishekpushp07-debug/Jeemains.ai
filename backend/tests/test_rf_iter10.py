# Rapid Fire iteration 10: all-skip solo gating (sessions/first_sprint/duels counters), revise_topics excludes skipped
import os
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


@pytest.fixture
def uid():
    u = "TEST-" + uuid.uuid4().hex[:16]
    yield u
    DB.rf_profiles.delete_many({"uid": u})
    DB.rf_sessions.delete_many({"user_id": u})
    DB.rf_awards.delete_many({"uid": u})


def start(u, count=10, subject="Physics"):
    r = requests.post(f"{API}/sessions", json={"subject": subject, "count": count, "request_id": uuid.uuid4().hex}, headers=H(u))
    assert r.status_code == 200, r.text
    return r.json()


def complete(u, s, res):
    r = requests.post(f"{API}/sessions/{s['id']}/complete", json={"results": res}, headers=H(u))
    assert r.status_code == 200, r.text
    return r.json()


# ---------- All-skip gating ----------
class TestAllSkipGating:
    def test_all_skip_no_first_sprint_no_sessions(self, uid):
        s = start(uid, 5)
        d = complete(uid, s, [{"card_id": c["id"], "outcome": "skipped"} for c in s["cards"]])
        rw = d["reward"]
        assert rw["played"] is False
        assert all(b["id"] != "first_sprint" for b in rw["new_badges"]), rw["new_badges"]
        p = DB.rf_profiles.find_one({"uid": uid})
        assert p.get("sessions", 0) == 0
        assert "first_sprint" not in p.get("badges", [])
        prof = requests.get(f"{API}/profile", headers=H(uid)).json()
        assert prof["sessions"] == 0

    def test_all_skip_does_not_count_as_duel(self, uid):
        s = start(uid, 5)
        complete(uid, s, [{"card_id": c["id"], "outcome": "skipped"} for c in s["cards"]])
        p = DB.rf_profiles.find_one({"uid": uid})
        assert p.get("duels", 0) == 0, f"all-skip solo incremented duels counter: {p.get('duels')}"

    def test_empty_results_also_gated(self, uid):
        s = start(uid, 5)
        d = complete(uid, s, [])
        assert d["summary"]["skipped"] == len(s["cards"])
        assert d["reward"]["played"] is False
        p = DB.rf_profiles.find_one({"uid": uid})
        assert p.get("sessions", 0) == 0 and "first_sprint" not in p.get("badges", [])

    def test_answered_then_grants_first_sprint(self, uid):
        s = start(uid, 5)
        res = [{"card_id": s["cards"][0]["id"], "outcome": "correct", "choice": s["cards"][0]["answer"], "ms": 1000}]
        d = complete(uid, s, res)
        assert any(b["id"] == "first_sprint" for b in d["reward"]["new_badges"])
        p = DB.rf_profiles.find_one({"uid": uid})
        assert p["sessions"] == 1 and p.get("duels", 0) == 0


# ---------- revise_topics ----------
class TestReviseTopics:
    def test_all_skip_empty_revise(self, uid):
        s = start(uid, 10)
        d = complete(uid, s, [{"card_id": c["id"], "outcome": "skipped"} for c in s["cards"]])
        assert d["summary"]["revise_topics"] == []

    def test_revise_only_from_wrong_or_timeout(self, uid):
        s = start(uid, 10)
        cards = s["cards"]
        wrong = cards[0]
        bad = next(i for i in [0, 1, 2, 3] if i != wrong["answer"])
        res = [{"card_id": wrong["id"], "outcome": "incorrect", "choice": bad, "ms": 900},
               {"card_id": cards[1]["id"], "outcome": "timed_out", "ms": 20000},
               {"card_id": cards[2]["id"], "outcome": "correct", "choice": cards[2]["answer"], "ms": 800}]
        res += [{"card_id": c["id"], "outcome": "skipped"} for c in cards[3:]]
        d = complete(uid, s, res)
        sm = d["summary"]
        assert sm["incorrect"] == 1 and sm["timed_out"] == 1 and sm["correct"] == 1
        doc = DB.rf_sessions.find_one({"id": s["id"]})
        allowed = {r["topic"] or r["chapter"] for r in doc["results"] if r["outcome"] in ("incorrect", "timed_out")}
        assert set(sm["revise_topics"]) <= allowed, (sm["revise_topics"], allowed)
        assert len(sm["revise_topics"]) >= 1
