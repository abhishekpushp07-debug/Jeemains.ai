"""All India Rapid (daily challenge): same 45 PCM cards for everyone, server-paced cards (no key before answering),
one try a day, fair board. TEST-* players only; they see a board of TEST players and never the real one."""
import os
import time
import uuid

import requests
from pymongo import MongoClient

BASE = os.environ["EXPO_BACKEND_URL"].rstrip("/") + "/api"
db = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
s = requests.Session()


def user():
    return {"X-RF-User": f"TEST-daily-{uuid.uuid4().hex[:10]}"}


def cleanup(*hs):
    for h in hs:
        uid = h["X-RF-User"]
        db.rf_daily_plays.delete_many({"uid": uid})
        db.rf_profiles.delete_many({"uid": uid})
        db.rf_awards.delete_many({"uid": uid})
        db.rf_learning_events.delete_many({"uid": uid})


def start(h):
    r = s.post(f"{BASE}/rf/daily/start", headers=h, json={"exam": "JEE"}, timeout=60)
    assert r.status_code == 200, r.text
    return r.json()


def key_of(c):
    return db.rf_cards.find_one({"prompt": c["prompt"], "chapter": c["chapter"], "subject": c["subject"], "retired": {"$ne": True}})["answer"]


def run(h, wrong_from=45):
    """Plays the whole round, answering right until card `wrong_from`, then wrong. Waits out the server's reveal pause."""
    st = start(h)
    seen = []
    while st["status"] == "playing":
        time.sleep(st["show_in_ms"] / 1000)
        c = st["card"]
        assert set(c) == {"i", "subject", "chapter", "prompt", "options"}  # no key, no id, no explanation
        seen.append(c)
        k = key_of(c)
        r = s.post(f"{BASE}/rf/daily/answer", headers=h, json={"exam": "JEE", "i": c["i"], "choice": k if c["i"] < wrong_from else (k + 1) % 4}, timeout=60)
        assert r.status_code == 200, r.text
        st = r.json()
        assert st["answer"] == k and st["outcome"] == ("correct" if c["i"] < wrong_from else "incorrect")
    return seen, st


def test_same_thirty_cards_paced_and_ranked():
    a, b = user(), user()
    try:
        seen_a, done_a = run(a)
        assert len(seen_a) == 45 and [c["i"] for c in seen_a] == list(range(45))
        assert [c["subject"] for c in seen_a[:3]] == ["Physics", "Chemistry", "Mathematics"]
        assert len({c["prompt"] for c in seen_a}) == 45
        for subject in ("Physics", "Chemistry", "Mathematics"):
            assert len({c["chapter"] for c in seen_a if c["subject"] == subject}) == 15
        assert done_a["status"] == "done" and done_a["result"]["correct"] == 45 and done_a["result"]["rank"] == 1
        assert done_a["result"]["reward"]["xp"] > 0

        seen_b, done_b = run(b, wrong_from=25)
        assert [c["prompt"] for c in seen_b] == [c["prompt"] for c in seen_a]  # everyone gets the same 45
        assert done_b["result"]["correct"] == 25 and done_b["result"]["rank"] == 2

        # One try a day: starting again shows the result, never a new round.
        again = start(a)
        assert again["status"] == "done" and again["result"]["correct"] == 45

        st = s.get(f"{BASE}/rf/daily?exam=JEE", headers=b, timeout=30).json()
        assert st["you"]["status"] == "done" and st["you"]["rank"] == 2 and st["total"] == 45 and st["seconds"] == 20
        board = s.get(f"{BASE}/rf/daily/board?exam=JEE", headers=a, timeout=30).json()
        mine = [row for row in board["items"] if row["you"]]
        assert mine and mine[0]["rank"] == 1 and mine[0]["correct"] == 45 and "uid" not in mine[0]
        # Misses feed Weak cards.
        assert db.rf_learning_events.find_one({"uid": b["X-RF-User"]})
    finally:
        cleanup(a, b)


def test_server_clock_and_retries():
    h = user()
    try:
        st = start(h)
        assert st["status"] == "playing" and st["i"] == 0 and 2000 <= st["show_in_ms"] <= 3100
        # Too early for card 2: a wrong index just returns where the run really is.
        r = s.post(f"{BASE}/rf/daily/answer", headers=h, json={"exam": "JEE", "i": 5, "choice": 0}, timeout=30).json()
        assert r["status"] == "playing" and r["i"] == 0 and "answer" not in r
        time.sleep(st["show_in_ms"] / 1000)
        c = st["card"]
        k = key_of(c)
        first = s.post(f"{BASE}/rf/daily/answer", headers=h, json={"exam": "JEE", "i": 0, "choice": k}, timeout=30).json()
        assert first["outcome"] == "correct" and first["i"] == 1
        # A double tap of the same card never counts twice.
        dup = s.post(f"{BASE}/rf/daily/answer", headers=h, json={"exam": "JEE", "i": 0, "choice": k}, timeout=30).json()
        assert dup["i"] == 1 and dup["correct"] == 1 and "answer" not in dup
        # A card left on screen past 20 s + grace is timed out by the server, even if the phone says otherwise.
        db.rf_daily_plays.update_one({"uid": h["X-RF-User"]}, {"$set": {"served_ts": time.time() - 40}})
        late = s.post(f"{BASE}/rf/daily/answer", headers=h, json={"exam": "JEE", "i": 1, "choice": 0}, timeout=30).json()
        assert late["outcome"] == "timed_out" and late["ms"] == 20000
        # Leaving early: the rest count as skipped and the score is on the board.
        fin = s.post(f"{BASE}/rf/daily/finish", headers=h, json={"exam": "JEE"}, timeout=30).json()
        assert fin["status"] == "done" and fin["result"]["correct"] == 1
        play = db.rf_daily_plays.find_one({"uid": h["X-RF-User"]})
        assert len(play["rows"]) == 45 and sum(r["outcome"] == "skipped" for r in play["rows"]) == 43
    finally:
        cleanup(h)
