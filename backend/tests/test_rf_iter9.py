# Rapid Fire iteration 9: all-skip reward gating, reward progress fields, hidden answers on /cards, leaderboard filtering, card sync deletion
import os
import time
import uuid
from datetime import datetime, timedelta, timezone
import pytest
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv("/app/frontend/.env")
load_dotenv("/app/backend/.env")
BASE_URL = (os.environ.get("EXPO_BACKEND_URL") or os.environ.get("EXPO_PUBLIC_BACKEND_URL")).rstrip("/")
API = f"{BASE_URL}/api/rf"
DB = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
IST = timezone(timedelta(hours=5, minutes=30))


def day(offset=0):
    return datetime.fromtimestamp(time.time() - offset * 86400, IST).strftime("%Y-%m-%d")


def H(u):
    return {"X-RF-User": u}


@pytest.fixture
def uid():
    u = "TEST-" + uuid.uuid4().hex[:16]
    yield u
    DB.rf_profiles.delete_many({"uid": u})
    DB.rf_sessions.delete_many({"user_id": u})
    DB.rf_awards.delete_many({"uid": u})


def start(u, count=10):
    r = requests.post(f"{API}/sessions", json={"subject": "Physics", "count": count, "request_id": uuid.uuid4().hex}, headers=H(u))
    assert r.status_code == 200, r.text
    return r.json()


# ---------- Reward gating ----------
class TestSkipReward:
    def test_all_skip_earns_nothing_and_keeps_streak_state(self, uid):
        DB.rf_profiles.insert_one({"uid": uid, "xp": 500, "coins": 40, "streak": 2, "best_streak": 2, "last_day": day(1), "badges": [],
                                   "day_stats": {"day": day(), "sprints": 0, "correct": 0, "wins": 0, "claimed": []}})
        s = start(uid)
        res = [{"card_id": c["id"], "outcome": "skipped"} for c in s["cards"]]
        r = requests.post(f"{API}/sessions/{s['id']}/complete", json={"results": res}, headers=H(uid))
        assert r.status_code == 200, r.text
        rw = r.json()["reward"]
        assert rw["xp"] == 0 and rw["coins"] == 0 and rw["played"] is False
        p = DB.rf_profiles.find_one({"uid": uid})
        assert p["last_day"] == day(1), "last_day bumped by all-skip"
        assert p["streak"] == 2
        assert p["day_stats"]["sprints"] == 0
        assert p["xp"] == 500 and p["coins"] == 40

    def test_all_skip_does_not_award_first_sprint_badge(self, uid):
        s = start(uid, 5)
        r = requests.post(f"{API}/sessions/{s['id']}/complete", json={"results": [{"card_id": c["id"], "outcome": "skipped"} for c in s["cards"]]}, headers=H(uid))
        rw = r.json()["reward"]
        assert [b["id"] for b in rw["new_badges"]] == [], f"all-skip earned badges {rw['new_badges']}"

    def test_answered_session_reward_fields(self, uid):
        s = start(uid, 10)
        res = [{"card_id": c["id"], "outcome": "correct", "choice": c["answer"], "ms": 3000} for c in s["cards"][:3]]
        r = requests.post(f"{API}/sessions/{s['id']}/complete", json={"results": res}, headers=H(uid))
        assert r.status_code == 200, r.text
        rw = r.json()["reward"]
        assert rw["played"] is True and rw["xp"] == 30 and rw["coins"] == 6
        assert rw["xp_total"] == 30 and rw["coins_total"] == 6
        assert rw["level_floor"] == 0 and rw["next_level_xp"] == 100
        assert isinstance(rw["quest_ready"], bool)
        p = DB.rf_profiles.find_one({"uid": uid})
        assert p["last_day"] == day() and p["streak"] == 1 and p["day_stats"]["sprints"] == 1
        # replay is idempotent
        r2 = requests.post(f"{API}/sessions/{s['id']}/complete", json={"results": res}, headers=H(uid))
        assert r2.json()["reward"]["xp_total"] == 30


# ---------- Public cards ----------
class TestCards:
    def test_cards_hide_answer_and_explain(self):
        r = requests.get(f"{API}/cards", params={"subject": "Physics", "limit": 200})
        assert r.status_code == 200
        items = r.json()["items"]
        assert items and all("answer" not in c and "explain" not in c for c in items)
        assert all({"id", "prompt", "options"} <= set(c) for c in items)


# ---------- Leaderboard ----------
class TestLeaderboard:
    def test_excludes_test_and_names_unnamed(self):
        a, b = "TEST-" + uuid.uuid4().hex[:12], "TEST-" + uuid.uuid4().hex[:12]
        DB.rf_profiles.insert_many([{"uid": a, "xp": 10 ** 9, "exam_stats": {"JEE": {"xp": 10 ** 9}}, "name": "TEST_Hidden"},
                                    {"uid": b, "xp": 10 ** 9 - 1, "exam_stats": {"JEE": {"xp": 10 ** 9 - 1}}}])
        try:
            items = requests.get(f"{API}/leaderboard", headers=H(b)).json()["items"]
            assert all(not (i["name"] or "").startswith("TEST_") for i in items)
            assert all(not i["you"] for i in items)  # TEST players are never ranked, not even for themselves
        finally:
            DB.rf_profiles.delete_many({"uid": {"$in": [a, b]}})
