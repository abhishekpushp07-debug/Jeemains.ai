# Iteration113: regression smoke after deployment startup fixes (RF catalog/daily/weak-topics/sessions/leaderboard + match-link visit counting)
import os, time, uuid
from pathlib import Path

import pytest
import requests
from dotenv import dotenv_values
from pymongo import MongoClient

FRONT = dotenv_values(Path(__file__).resolve().parents[2] / "frontend" / ".env")
BACK = dotenv_values(Path(__file__).resolve().parents[1] / ".env")
BASE = (os.environ.get("EXPO_BACKEND_URL") or FRONT.get("EXPO_BACKEND_URL") or FRONT["EXPO_PUBLIC_BACKEND_URL"]).rstrip("/")
UA = "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Mobile Safari/537.36"


@pytest.fixture(scope="module")
def db():
    c = MongoClient(BACK["MONGO_URL"])
    yield c[BACK["DB_NAME"]]
    c.close()


@pytest.fixture(scope="module")
def user(db):
    uid = f"TEST-iter113-{uuid.uuid4().hex[:10]}"
    yield {"X-RF-User": uid}
    # exact-uid cleanup of rows this test user created
    db.rf_sessions.delete_many({"user_id": uid})
    db.rf_learning_events.delete_many({"uid": uid})
    db.rf_profiles.delete_many({"uid": uid})
    db.rf_awards.delete_many({"uid": uid})


# Health (root /health is the probe route)
def test_health():
    r = requests.get(BASE.replace("/api", "") + "/api/health/load", timeout=30)
    assert r.status_code == 200 and r.json()["busy"] is False


# Catalog
def test_catalog(user):
    r = requests.get(f"{BASE}/api/rf/catalog?exam=JEE", headers=user, timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert body, "empty catalog"


# All India daily (read only: do not start)
def test_daily_total_45(user):
    r = requests.get(f"{BASE}/api/rf/daily?exam=JEE", headers=user, timeout=30)
    assert r.status_code == 200, r.text
    assert r.json()["total"] == 45


# Weak topics
def test_weak_topics(user):
    r = requests.get(f"{BASE}/api/rf/weak-topics?exam=JEE", headers=user, timeout=30)
    assert r.status_code == 200, r.text


# Practice session create (idempotent on request_id)
def test_session_create_30(user, db):
    rid = str(uuid.uuid4())
    payload = {"exam": "JEE", "picks": [{"subject": "Physics", "chapter": None}], "count": 30, "request_id": rid}
    r = requests.post(f"{BASE}/api/rf/sessions", headers=user, json=payload, timeout=60)
    assert r.status_code == 200, r.text
    s = r.json()
    assert len(s["cards"]) == 30
    assert all(c["subject"] == "Physics" for c in s["cards"])
    again = requests.post(f"{BASE}/api/rf/sessions", headers=user, json=payload, timeout=60).json()
    assert again["id"] == s["id"]
    assert db.rf_sessions.find_one({"id": s["id"], "user_id": user["X-RF-User"]})


# Leaderboard
def test_leaderboard(user):
    r = requests.get(f"{BASE}/api/rf/leaderboard?exam=JEE", headers=user, timeout=30)
    assert r.status_code == 200, r.text


# Match link visit counting (rf_link_visits without TTL). Challenge row is a TEST fixture inserted directly, removed by id.
def test_match_link_counts_once_per_device(db):
    cid, owner = str(uuid.uuid4()), f"TEST-iter113-owner-{uuid.uuid4().hex[:8]}"
    db.rf_challenges.insert_one({"id": cid, "from_uid": owner, "link": True, "status": "open", "exam": "JEE",
                                 "expires_ts": time.time() + 600, "invites": [], "joined": 0, "cards_n": 30,
                                 "subject": "Physics", "created_ts": time.time()})
    try:
        url = f"{BASE}/api/rf/c/{cid}"  # rooms.py router prefix is /rf
        r1 = requests.get(url, headers={"User-Agent": UA}, timeout=30)
        assert r1.status_code == 200, r1.text[:300]
        r2 = requests.get(url, headers={"User-Agent": UA}, timeout=30)
        assert r2.status_code == 200
        bot = requests.get(url, headers={"User-Agent": "WhatsApp/2.23"}, timeout=30)
        assert bot.status_code == 200
        c = db.rf_challenges.find_one({"id": cid})
        assert c.get("link_opens") == 1, c.get("link_opens")
        assert db.rf_link_visits.count_documents({"cid": cid}) == 1
    finally:
        db.rf_link_visits.delete_many({"cid": cid})
        db.rf_challenges.delete_one({"id": cid})
        db.rf_profiles.delete_many({"uid": owner})
