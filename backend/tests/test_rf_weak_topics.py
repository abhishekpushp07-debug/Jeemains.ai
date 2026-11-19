"""Weak Topic Sprint: a 20-second sprint dealt only from the subtopics a student keeps missing. TEST-* players only."""
import os
import uuid

import requests
from pymongo import MongoClient

BASE = os.environ["EXPO_BACKEND_URL"].rstrip("/") + "/api"
db = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
s = requests.Session()


def user():
    return {"X-RF-User": f"TEST-weak-{uuid.uuid4().hex[:10]}"}


def cleanup(h):
    uid = h["X-RF-User"]
    for c in ("rf_sessions",):
        db[c].delete_many({"user_id": uid})
    for c in ("rf_learning_events", "rf_profiles", "rf_awards"):
        db[c].delete_many({"uid": uid})


def sprint(h, body, wrong=True):
    r = s.post(f"{BASE}/rf/sessions", headers=h, json={"exam": "JEE", "request_id": uuid.uuid4().hex, **body}, timeout=60)
    assert r.status_code == 200, r.text
    sess = r.json()
    keys = {c["id"]: db.rf_cards.find_one({"id": c["id"]})["answer"] for c in sess["cards"]}
    results = [{"card_id": cid, "outcome": "incorrect" if wrong else "correct", "choice": (k + 1) % 4 if wrong else k, "ms": 3000} for cid, k in keys.items()]
    r = s.post(f"{BASE}/rf/sessions/{sess['id']}/complete", headers=h, json={"results": results}, timeout=60)
    assert r.status_code == 200, r.text
    return sess


def test_new_player_has_no_weak_topics():
    h = user()
    try:
        r = s.get(f"{BASE}/rf/weak-topics?exam=JEE", headers=h, timeout=30)
        assert r.status_code == 200 and r.json()["topics"] == [] and r.json()["cards"] == 0 and r.json()["seconds"] == 20
        r = s.post(f"{BASE}/rf/sessions", headers=h, json={"exam": "JEE", "request_id": uuid.uuid4().hex, "weak_topics": True}, timeout=30)
        assert r.status_code == 404 and "No weak subtopics" in r.text
    finally:
        cleanup(h)


def test_sprint_deals_only_missed_subtopics():
    h = user()
    try:
        chapter = "Laws of Motion"
        sprint(h, {"picks": [{"subject": "Physics", "chapter": chapter}], "count": 30})
        sprint(h, {"picks": [{"subject": "Physics", "chapter": chapter}], "count": 30})
        r = s.get(f"{BASE}/rf/weak-topics?exam=JEE", headers=h, timeout=30)
        d = r.json()
        assert r.status_code == 200 and 1 <= len(d["topics"]) <= 8 and d["cards"] > 0
        assert all(t["chapter"] == chapter and t["misses"] >= 1 and t["tries"] >= t["misses"] for t in d["topics"])
        assert [t["misses"] for t in d["topics"]] == sorted((t["misses"] for t in d["topics"]), reverse=True)
        allowed = {(t["subject"], t["chapter"], t["topic"]) for t in d["topics"]}

        sess = sprint(h, {"weak_topics": True, "count": 30}, wrong=False)
        assert sess["mode"] == "weak_topics" and sess["seconds_per_card"] == 20 and sess["label"].startswith("Weak Topic Sprint")
        assert 0 < len(sess["cards"]) <= 30
        assert all((c["subject"], c["chapter"], c["topic"] or c["chapter"]) in allowed for c in sess["cards"])
        assert len({c["prompt"] for c in sess["cards"]}) == len(sess["cards"])  # no prompt twice
        hist = s.get(f"{BASE}/rf/history?exam=JEE", headers=h, timeout=30).json()["items"]
        assert hist[0]["mode"] == "weak_topics"
    finally:
        cleanup(h)
