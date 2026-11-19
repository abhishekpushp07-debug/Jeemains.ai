"""Weak Topic Sprint extra regressions (iteration 110): idempotency, count cap, card counts, missed counter. TEST-* players only."""
import os
import uuid

import requests
from pymongo import MongoClient

from test_rf_weak_topics import BASE, cleanup, sprint, user, s

db = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]


def _seed_misses(h, chapter="Laws of Motion", times=2):
    for _ in range(times):
        sprint(h, {"picks": [{"subject": "Physics", "chapter": chapter}], "count": 30})


# Weak-topics list shape + types
def test_weak_topics_shape():
    h = user()
    try:
        _seed_misses(h)
        d = s.get(f"{BASE}/rf/weak-topics?exam=JEE", headers=h, timeout=30).json()
        assert d["exam"] == "JEE" and d["seconds"] == 20 and isinstance(d["cards"], int)
        for t in d["topics"]:
            assert set(t) >= {"subject", "chapter", "topic", "misses", "tries", "missed"}
            assert "weak_ids" not in t
            assert isinstance(t["misses"], int) and 0 <= t["missed"] <= t["misses"]
    finally:
        cleanup(h)


# Same request_id returns the same session (idempotent) and count caps the deck
def test_weak_sprint_idempotent_and_count_cap():
    h = user()
    try:
        _seed_misses(h)
        rid = uuid.uuid4().hex
        body = {"exam": "JEE", "request_id": rid, "weak_topics": True, "count": 5}
        a = s.post(f"{BASE}/rf/sessions", headers=h, json=body, timeout=30)
        b = s.post(f"{BASE}/rf/sessions", headers=h, json=body, timeout=30)
        assert a.status_code == 200 and b.status_code == 200
        assert a.json()["id"] == b.json()["id"]
        assert len(a.json()["cards"]) <= 5
        assert db.rf_sessions.count_documents({"user_id": h["X-RF-User"], "request_id": rid}) == 1
    finally:
        cleanup(h)


# Dealt cards never exceed the advertised "cards" figure; and the deck uses all subtopics (round robin)
def test_weak_sprint_spreads_across_topics():
    h = user()
    try:
        _seed_misses(h)
        d = s.get(f"{BASE}/rf/weak-topics?exam=JEE", headers=h, timeout=30).json()
        r = s.post(f"{BASE}/rf/sessions", headers=h, json={"exam": "JEE", "request_id": uuid.uuid4().hex, "weak_topics": True, "count": 100}, timeout=30)
        assert r.status_code == 200
        cards = r.json()["cards"]
        assert len(cards) <= d["cards"]
        dealt = {(c["subject"], c["chapter"], c["topic"] or c["chapter"]) for c in cards}
        allowed = {(t["subject"], t["chapter"], t["topic"]) for t in d["topics"]}
        assert dealt <= allowed
        # every weak subtopic that has cards should be represented
        assert len(dealt) == len(allowed), f"dealt {len(dealt)} of {len(allowed)} topics"
        print(f"advertised cards={d['cards']} dealt={len(cards)} topics={len(allowed)}")
    finally:
        cleanup(h)


# Invalid payloads are rejected with 422
def test_weak_sprint_validation():
    h = user()
    try:
        r = s.post(f"{BASE}/rf/sessions", headers=h, json={"exam": "JEE", "request_id": "short", "weak_topics": True}, timeout=30)
        assert r.status_code == 422
        r = s.post(f"{BASE}/rf/sessions", headers=h, json={"exam": "JEE", "request_id": uuid.uuid4().hex, "weak_topics": True, "count": 0}, timeout=30)
        assert r.status_code == 422
        r = s.get(f"{BASE}/rf/weak-topics?exam=XYZ", headers=h, timeout=30)
        assert r.status_code in (400, 422)
    finally:
        cleanup(h)
