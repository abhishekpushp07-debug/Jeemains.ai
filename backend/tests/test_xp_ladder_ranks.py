"""All India XP board: "Your rank" must equal a plain count of everyone ahead, for players far below the list too.

The server no longer counts everyone above a player on every look: one pass over the XP index (the "ladder") answers for
everybody, and a new pass is made at most every 30 s. These checks compare that answer with the plain count:
ties (same XP: the lower id is ahead), QA players left out, a player's own gain at once, and somebody else's overtake
after a quiet spell (the next look must wait for a fresh pass instead of reading the old ladder).

Nothing is deleted. The same 26 throwaway players are used on every run (`qa-ladder-*`, ranked like real ones with tiny
XP so they sit at the bottom, and one `TEST-ladder-qa` QA player). Afterwards they are retired in place: XP back to 0
and a TEST name, which takes them off every board. Their sign-in grants run out by themselves after 5 minutes.

Run:  cd /app/backend && python -m pytest tests/test_xp_ladder_ranks.py -q
"""
import hashlib
import os
import secrets
import time
from datetime import datetime, timedelta, timezone

import pytest
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
BASE = os.environ.get("RF_TEST_BASE", "http://127.0.0.1:8001/api/rf")
FIELD = "exam_stats.JEE.xp"
REAL = {"name": {"$not": {"$regex": "^TEST"}}, "uid": {"$not": {"$regex": "^TEST"}}}
PASS_GAP = 31.5  # a new pass over the XP index is due 30 s after the last one; a rank is also kept 30 s per player
# 20 fillers (XP 20..39) keep the measured players (XP 1..7) off the top-20 list, so their rank comes from the ladder.
# The QA player is level with b and c and its id sorts before theirs: it must never be counted.
CAST = [(f"filler{k}", f"qa-ladder-f{k:02d}", f"Ladder QA filler {k}", 20 + k) for k in range(20)] + \
       [(key, f"qa-ladder-{key}", f"Ladder QA {key.upper()}", xp) for key, xp in (("a", 7), ("b", 5), ("c", 5), ("d", 3), ("e", 1))] + \
       [("qa", "TEST-ladder-qa", "TEST ladder", 5)]


@pytest.fixture(scope="module")
def db():
    return MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]


@pytest.fixture(scope="module")
def players(db):
    made = {}
    uids = [uid for _, uid, _, _ in CAST]
    try:
        for key, uid, name, xp in CAST:
            token = secrets.token_urlsafe(32)
            db.rf_access.insert_one({"digest": hashlib.sha256(token.encode()).hexdigest(), "uid": uid, "sid": "", "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5)})
            db.rf_profiles.update_one({"uid": uid}, {"$set": {"name": name, "xp": xp, FIELD: xp, "exam_stats.JEE.wins": 0}}, upsert=True)
            made[key] = {"uid": uid, "h": {"Authorization": "Bearer " + token}}
        yield made
    finally:  # retired in place, never removed: no XP and a TEST name keep them off every board until the next run
        db.rf_profiles.update_many({"uid": {"$in": uids}}, {"$set": {"name": "TEST ladder (retired)", "xp": 0, FIELD: 0}})


def counted(db, uid):
    """The plain count: everyone real with more XP, or the same XP and a lower id, is ahead."""
    xp = db.rf_profiles.find_one({"uid": uid})["exam_stats"]["JEE"]["xp"]
    return 1 + db.rf_profiles.count_documents({**REAL, "$or": [{FIELD: {"$gt": xp}}, {FIELD: xp, "uid": {"$lt": uid}}]})


def board(player):
    r = requests.get(f"{BASE}/leaderboard?exam=JEE", headers=player["h"], timeout=30)
    assert r.status_code == 200, r.text
    return r.json()


def test_ranks_equal_the_plain_count_and_follow_an_overtake(db, players):
    time.sleep(PASS_GAP)  # whatever ladder the server had before these players had XP is due for a new pass now
    first = {}
    for key in "abcde":
        got = board(players[key])
        assert not any(row["you"] for row in got["items"]), "measured players must be below the list for this check"
        first[key] = got["you"]["rank"]
        assert first[key] == counted(db, players[key]["uid"]), (key, got["you"])
    assert first["a"] < first["b"] < first["c"] < first["d"] < first["e"]
    assert first["c"] == first["b"] + 1  # level on XP: the lower id is one place ahead, and the QA player between them is not counted
    assert first["a"] > 20
    assert board(players["qa"])["you"]["rank"] is None  # QA players are never ranked

    # d earns 3 XP and passes b and c. d's own place is right at once ...
    db.rf_profiles.update_one({"uid": players["d"]["uid"]}, {"$inc": {FIELD: 3, "xp": 3}})
    moved = board(players["d"])["you"]
    assert moved["xp"] == 6 and moved["rank"] == first["b"] == counted(db, players["d"]["uid"])
    # ... and after a quiet spell the first look of somebody who was passed must not be answered from the old ladder.
    time.sleep(PASS_GAP)
    for key in "bc":
        assert board(players[key])["you"]["rank"] == first[key] + 1 == counted(db, players[key]["uid"]), key
    assert board(players["a"])["you"]["rank"] == first["a"]
    assert board(players["e"])["you"]["rank"] == first["e"]


def test_a_player_on_the_list_sees_the_same_place_in_both(db, players):
    top = players["filler19"]  # the best throwaway player: on the top-20 list unless 20 real players are ahead
    for _ in range(18):  # the list itself is refreshed every 15 s
        got = board(top)
        mine = [row for row in got["items"] if row["you"]]
        if mine or counted(db, top["uid"]) > 20:
            break
        time.sleep(1)
    if not mine:
        pytest.skip("20 real players are ahead of the throwaway player: it is not on the list here.")
    assert got["you"]["rank"] == mine[0]["rank"] == got["items"].index(mine[0]) + 1
