"""All India Rapid (iteration 112): 45 PCM cards, 15 Physics/15 Chemistry/15 Maths, 15 different chapters each, 20 s, no repeats.
TEST-* players only (flagged test, never on real boards). Cleans up only its own uid."""
import os
import time
import uuid

import requests
from pymongo import MongoClient

BASE = (os.environ.get("EXPO_BACKEND_URL") or os.environ["EXPO_PUBLIC_BACKEND_URL"]).rstrip("/") + "/api"
db = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
s = requests.Session()


def user():
    return {"X-RF-User": f"TEST-pcm45-{uuid.uuid4().hex[:10]}"}


def cleanup(h):
    uid = h["X-RF-User"]
    for c in ("rf_daily_plays", "rf_profiles", "rf_awards", "rf_learning_events"):
        db[c].delete_many({"uid": uid})


# Status endpoint: 45 cards, 20 s
def test_status_45_cards_20s():
    h = user()
    try:
        r = s.get(f"{BASE}/rf/daily?exam=JEE", headers=h, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["total"] == 45 and d["seconds"] == 20 and d["you"]["status"] == "new"
        assert isinstance(d["players"], int) and isinstance(d["ends_in"], int)
    finally:
        cleanup(h)


# Full skip-through run: 45 cards, PCM 15/15/15, distinct chapters per subject, no repeated prompt
def test_full_run_pcm_mix():
    h = user()
    try:
        st = s.post(f"{BASE}/rf/daily/start", headers=h, json={"exam": "JEE"}, timeout=60).json()
        seen = []
        while st["status"] == "playing":
            time.sleep(st["show_in_ms"] / 1000 + 0.05)
            c = st["card"]
            assert set(c) == {"i", "subject", "chapter", "prompt", "options"} and len(c["options"]) == 4
            assert st["total"] == 45 and st["seconds"] == 20
            seen.append(c)
            r = s.post(f"{BASE}/rf/daily/answer", headers=h, json={"exam": "JEE", "i": c["i"], "choice": None, "skip": True}, timeout=60)
            assert r.status_code == 200, r.text
            st = r.json()
            assert st["outcome"] == "skipped"
        assert len(seen) == 45 and [c["i"] for c in seen] == list(range(45))
        for subj in ("Physics", "Chemistry", "Mathematics"):
            rows = [c for c in seen if c["subject"] == subj]
            assert len(rows) == 15, (subj, len(rows))
            assert len({c["chapter"] for c in rows}) == 15, (subj, sorted(c["chapter"] for c in rows))
        assert len({c["prompt"] for c in seen}) == 45
        assert st["result"]["total"] == 45 and st["result"]["correct"] == 0
        play = db.rf_daily_plays.find_one({"uid": h["X-RF-User"]})
        assert play["test"] is True and len(play["rows"]) == 45
    finally:
        cleanup(h)


# Finish early: remaining count as skipped, 45 rows
def test_finish_early_45_rows():
    h = user()
    try:
        st = s.post(f"{BASE}/rf/daily/start", headers=h, json={"exam": "JEE"}, timeout=60).json()
        time.sleep(st["show_in_ms"] / 1000 + 0.05)
        s.post(f"{BASE}/rf/daily/answer", headers=h, json={"exam": "JEE", "i": 0, "choice": None, "skip": True}, timeout=30)
        fin = s.post(f"{BASE}/rf/daily/finish", headers=h, json={"exam": "JEE"}, timeout=30).json()
        assert fin["status"] == "done" and fin["result"]["total"] == 45
        play = db.rf_daily_plays.find_one({"uid": h["X-RF-User"]})
        assert len(play["rows"]) == 45 and all(r["outcome"] == "skipped" for r in play["rows"])
    finally:
        cleanup(h)


# Fairness probe: answering a card before its show time (during the 3-2-1) should not be accepted as an instant answer
def test_answer_before_shown_is_not_instant():
    h = user()
    try:
        st = s.post(f"{BASE}/rf/daily/start", headers=h, json={"exam": "JEE"}, timeout=60).json()
        assert st["show_in_ms"] > 1500
        r = s.post(f"{BASE}/rf/daily/answer", headers=h, json={"exam": "JEE", "i": 0, "choice": 0}, timeout=30).json()
        # If accepted, ms must not be 0 (it would beat every honest player on the tie-break)
        assert "outcome" not in r or r["ms"] > 0, f"answered before shown: {r.get('outcome')} ms={r.get('ms')}"
    finally:
        cleanup(h)
