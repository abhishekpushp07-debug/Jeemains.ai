"""All India Rapid board: every place must equal a plain count of the runs ahead (more right; then less time; then earlier).

The server keeps a copy of the board (top 100, the number of players, and how many runs ended on each score in each
10 s of time) instead of counting everyone ahead for every student. These checks compare its answers with the plain
order: 140 runs on a finished day (ties on score, on the 10 s edges and on the exact time), and a live run that ends
below the top 100 while the copy is in memory.

Nothing is deleted. The same TEST-brd-* runs are used on every run of this file (the QA board, never the real one):
they are moved to the day under test, and afterwards retired in place (status "retired": on no board, in no count).
The 140 runs sit on a random day long ago; the live check puts 105 runs with 5..20 right on today's QA board (below
what the other All India suites assert on).

Run:  cd /app/backend && python -m pytest tests/test_daily_board_ranks.py -q
"""
import os
import random
import sys
import time
import uuid

import pytest
import requests
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from gamify import ist_day  # noqa: E402

BASE = os.environ.get("RF_TEST_BASE", "http://127.0.0.1:8001/api/rf")
s = requests.Session()


@pytest.fixture(scope="module")
def db():
    return MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]


def run_doc(uid, day, correct, ms, finished_ts, status="done"):
    return {"exam": "JEE", "day": day, "uid": uid, "test": True, "status": status, "i": 45, "served_ts": None, "rows": [],
            "correct": correct, "ms": ms, "started_ts": finished_ts - 900, "finished_ts": finished_ts}


def place_runs(db, runs):
    """Each throwaway player has one run, moved to wherever this check needs it (made on the first ever run of this file)."""
    db.rf_daily_plays.bulk_write([UpdateOne({"exam": "JEE", "uid": r["uid"]}, {"$set": r}, upsert=True) for r in runs], ordered=False)


def retire(db, uids):
    db.rf_daily_plays.update_many({"exam": "JEE", "uid": {"$in": uids}}, {"$set": {"status": "retired"}})


def head(uid):
    return {"X-RF-User": uid}  # conftest swaps this for a short-lived grant (TEST players only)


def test_every_place_on_a_finished_day_is_the_plain_order(db):
    rng = random.Random(uuid.uuid4().hex)
    day = f"19{rng.randint(10, 99)}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
    times = [0, 9_999, 10_000, 10_001, 19_999, 20_000, 35_000, 35_000, 61_234, 899_000]  # both sides of the 10 s edges, and equal times
    runs = [run_doc(f"TEST-brd-p{k:03d}", day, rng.randint(0, 12), rng.choice(times), 2_000.0 + k * 0.5) for k in rng.sample(range(140), 140)]
    still_playing = run_doc("TEST-brd-popen", day, 12, 0, 1_000.0, status="playing")  # not finished: never on the board
    place_runs(db, runs + [still_playing])
    try:
        order = sorted(runs, key=lambda r: (-r["correct"], r["ms"], r["finished_ts"]))
        place = {r["uid"]: n + 1 for n, r in enumerate(order)}
        for r in runs:
            got = s.get(f"{BASE}/daily/board?exam=JEE&day={day}", headers=head(r["uid"]), timeout=30).json()
            assert got["players"] == 140 and len(got["items"]) == 100
            assert got["you"]["rank"] == place[r["uid"]], (r["correct"], r["ms"], got["you"])
            mine = [row for row in got["items"] if row["you"]]
            assert [row["rank"] for row in mine] == ([place[r["uid"]]] if place[r["uid"]] <= 100 else [])
        assert [(row["rank"], row["correct"], row["ms"]) for row in got["items"]] == [(n + 1, r["correct"], r["ms"]) for n, r in enumerate(order[:100])]
        watcher = s.get(f"{BASE}/daily/board?exam=JEE&day={day}", headers=head(still_playing["uid"]), timeout=30).json()
        assert watcher["you"]["status"] == "playing" and watcher["you"]["rank"] is None and not any(row["you"] for row in watcher["items"])
    finally:
        retire(db, [r["uid"] for r in runs] + [still_playing["uid"]])


def test_a_live_run_ending_below_the_top_100_gets_its_exact_place(db):
    rng = random.Random(uuid.uuid4().hex)
    day, now = ist_day(), time.time()
    runs = [run_doc(f"TEST-brd-t{k:03d}", day, rng.randint(5, 20), rng.randint(100_000, 800_000), now - 120 + k * 0.01) for k in range(105)]
    me = head("TEST-brd-live")
    done = {"exam": "JEE", "day": day, "test": True, "status": "done"}
    place_runs(db, runs)
    # The live player's one run is put back to "not started" for today, so the same player can play on every run of this file.
    db.rf_daily_plays.update_one({"exam": "JEE", "uid": me["X-RF-User"]}, {"$set": {"day": day, "test": True, "status": "playing", "i": 0, "served_ts": None, "rows": [],
                                                                                    "correct": 0, "ms": 0, "started_ts": now}, "$unset": {"finished_ts": ""}}, upsert=True)
    try:
        st = s.post(f"{BASE}/daily/start", headers=me, json={"exam": "JEE"}, timeout=60).json()
        for _ in range(2):  # two right answers, then leave: nobody else on the QA board ends on exactly 2
            time.sleep(st["show_in_ms"] / 1000)
            c = st["card"]
            key = db.rf_cards.find_one({"prompt": c["prompt"], "chapter": c["chapter"], "subject": c["subject"], "retired": {"$ne": True}})["answer"]
            st = s.post(f"{BASE}/daily/answer", headers=me, json={"exam": "JEE", "i": c["i"], "choice": key}, timeout=60).json()
            assert st["outcome"] == "correct"
        time.sleep(max(0, now + 15.5 - time.time()))  # a copy of the board is kept 15 s: the next one has the 105 runs
        seen = s.get(f"{BASE}/daily?exam=JEE", headers=me, timeout=30).json()  # the copy the finish below is added to
        assert seen["you"]["status"] == "playing" and seen["players"] >= 105
        ahead_before = db.rf_daily_plays.count_documents({**done, "correct": {"$gte": 3}})
        fin = s.post(f"{BASE}/daily/finish", headers=me, json={"exam": "JEE"}, timeout=30).json()
        ahead_after = db.rf_daily_plays.count_documents({**done, "correct": {"$gte": 2}, "uid": {"$ne": me["X-RF-User"]}})
        res = fin["result"]
        assert fin["status"] == "done" and res["correct"] == 2
        assert 100 < 1 + ahead_before <= res["rank"] <= 1 + ahead_after, (ahead_before, res, ahead_after)
        assert seen["players"] + 1 <= res["players"] <= db.rf_daily_plays.count_documents(done) and res["players"] >= res["rank"]
        board = s.get(f"{BASE}/daily/board?exam=JEE", headers=me, timeout=30).json()
        assert board["you"]["rank"] == res["rank"] and not any(row["you"] for row in board["items"]) and len(board["items"]) == 100
    finally:
        retire(db, [r["uid"] for r in runs] + [me["X-RF-User"]])
