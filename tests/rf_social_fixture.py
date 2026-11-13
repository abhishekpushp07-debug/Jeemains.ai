"""Local-only QA data for the Rapid Fire friend feed, head-to-head history, Diamond Rush and diamond store.

  python tests/rf_social_fixture.py seed      # add three TEST friends, their activity, four 1 v 1 matches, and diamonds to try the store
  python tests/rf_social_fixture.py cleanup   # remove exactly what seed created and put the player's wallet back

Touches only the Rapid Fire companion collections in this preview database. Nothing is sent to the canonical website.
The player is the approved QA learner (see memory/test_credentials.md); pass --pid to use another one.
"""
import json
import os
import random
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from pymongo import MongoClient

sys.path.insert(0, "/app/backend")
load_dotenv("/app/backend/.env")
from social import make_pid  # noqa: E402

STATE = "/tmp/rf_social_fixture.json"
IST = timezone(timedelta(hours=5, minutes=30))
WALLET = ("coins", "diamonds", "diamonds_spent", "day_stats", "owned", "equipped", "freezes", "avatar")
FRIENDS = [
    ("Aarav Sharma", "av_thunder", 3600, {"red": 9, "blue": 4, "emerald": 2}, 12, ["first_win", "streak_3", "sharpshooter"], {"frame": "frame_gold", "entry": "entry_lightning"}, True),
    ("Diya Patel", "av_crystal", 6400, {"red": 14, "blue": 7, "emerald": 3, "gold": 1}, 16, ["first_win", "streak_7", "perfect", "champion_10"], {"frame": "frame_fire", "entry": "entry_phoenix"}, False),
    ("Kabir Singh", "av_ninja", 900, {"red": 3, "blue": 1}, 6, ["first_sprint", "first_win"], {"frame": None, "entry": "entry_rocket"}, False),
]


def db_of():
    return MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]


def match(db, me, friend, mine, theirs, days_ago, subject):
    """A finished 1 v 1 match on real cards, with the same shape the game writes."""
    cards = list(db.rf_cards.aggregate([{"$match": {"exam": "JEE", "subject": subject, "retired": {"$ne": True}}}, {"$sample": {"size": 30}}, {"$project": {"_id": 0, "id": 1, "answer": 1}}]))
    ts = time.time() - days_ago * 86400

    def answers(score):
        right = set(random.sample(range(30), score))
        return [{"i": i, "choice": c["answer"] if i in right else (c["answer"] + 1) % 4, "outcome": "correct" if i in right else "incorrect", "ms": random.randint(1500, 9000)} for i, c in enumerate(cards)]

    def seat(p, score):
        return {"uid": p["uid"], "pid": p["pid"], "name": p["name"], "level": 1, "wins": 0, "avatar": p.get("avatar"), "frame": (p.get("equipped") or {}).get("frame"), "entry": (p.get("equipped") or {}).get("entry"),
                "answers": answers(score), "score": score, "ms": random.randint(90000, 200000), "done": True, "joined_ts": ts - 300, "seen_ts": ts, "last_ts": ts, "forfeit": False}

    did = str(uuid.uuid4())
    winner = me["uid"] if mine > theirs else friend["uid"] if theirs > mine else "tie"
    db.rf_duels.insert_one({"id": did, "code": None, "exam": "JEE", "mode": "friend", "subject": subject, "chapter": None, "status": "finished", "card_ids": [c["id"] for c in cards],
                            "players": [seat(me, mine), seat(friend, theirs)], "created_ts": ts - 300, "request_id": "fixture:" + did, "request_ids": ["fixture:" + did],
                            "start_at": ts - 290, "ends_at": ts + 160, "entry_seconds": 9.5, "finished_ts": ts, "tie_break": False, "winner": winner})
    reward = {"exam": "JEE", "xp": mine * 10, "coins": mine * 2, "streak": 1, "freeze_used": False, "level_before": 1, "level_after": 1, "level_up": False, "xp_total": me.get("xp", 0), "coins_total": me.get("coins", 0),
              "level_floor": 0, "next_level_xp": 100, "played": True, "quest_ready": False, "diamonds": {"red": 1} if mine >= 12 else {}, "phoenix_streak": 3 if mine >= 12 else 2, "new_badges": []}
    db.rf_awards.insert_one({"uid": me["uid"], "ref": "duel:" + did, "exam": "JEE", "ts": ts, "reward": reward})
    return did


def seed(pid):
    if os.path.exists(STATE):
        cleanup()
    db, run, now = db_of(), uuid.uuid4().hex[:6], time.time()
    me = db.rf_profiles.find_one({"pid": pid})
    if not me:
        raise SystemExit(f"No Rapid Fire player {pid}. Sign in once and open Rapid Fire first.")
    state = {"me": me["uid"], "wallet": {k: me[k] for k in WALLET if k in me}, "friends": [], "duels": [], "feed": f"fixture-{run}:"}
    with open(STATE, "w", encoding="utf-8") as f:  # written first, so a failed seed can still be cleaned up
        json.dump(state, f)
    friends = []
    for k, (name, avatar, xp, diamonds, best, badges, equipped, online) in enumerate(FRIENDS):
        uid = f"TEST-fixture-{run}-{k}"
        p = {"uid": uid, "pid": make_pid(uid), "name": name, "display_name": name, "avatar": avatar, "xp": xp, "coins": 0, "diamonds": diamonds, "best_phoenix": best, "badges": badges,
             "equipped": equipped, "owned": [v for v in equipped.values() if v], "wins": 4 + k, "duels": 9 + k, "seen_ts": now + 3600 if online else now - (k + 1) * 5400}
        db.rf_profiles.insert_one(dict(p))
        db.rf_friends.insert_one({"uid": me["uid"], "fid": uid, "ts": now})
        friends.append(p)
        state["friends"].append(uid)
    db.rf_friends.insert_one({"uid": friends[0]["uid"], "fid": me["uid"], "ts": now})
    a, b, c = friends
    events = [(a, "win", {"vs": "Riya M.", "mine": 24, "theirs": 19}, 0.3), (b, "gem", {"colour": "emerald"}, 2), (c, "run", {"n": 5}, 5), (a, "level", {"level": 7}, 26),
              (b, "badge", {"title": "Sharpshooter"}, 50), (c, "win", {"team": "Kota Warriors", "vs": "Delhi Dynamos", "mine": 61, "theirs": 54}, 74), (b, "gem", {"colour": "kohinoor"}, 98), (a, "win", {"players": 4, "mine": 22}, 120)]
    db.rf_feed.insert_many([{"id": f"{state['feed']}{k}", "uid": p["uid"], "kind": kind, "data": data, "ts": now - hours * 3600, "at": datetime.now(timezone.utc)} for k, (p, kind, data, hours) in enumerate(events)])
    for mine, theirs, days, subject in ((18, 14, 0.2, "Physics"), (11, 16, 1, "Chemistry"), (15, 15, 3, "Mathematics"), (21, 12, 6, "Physics")):
        state["duels"].append(match(db, me, a, mine, theirs, days, subject))
    # Three diamonds won today (two Diamond Rush chests ready) and enough diamonds in hand for one store special.
    today = datetime.fromtimestamp(now, IST).strftime("%Y-%m-%d")
    old = me.get("day_stats") or {}
    day = old if old.get("day") == today else {"day": today, "sprints": 0, "correct": 0, "wins": 0, "claimed": []}
    db.rf_profiles.update_one({"uid": me["uid"]}, {"$set": {"day_stats": {**day, "gems": 3, "rush": []}, "diamonds": {"red": 7, "blue": 4, "emerald": 1}}})
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state, f)
    print(json.dumps({"ok": True, "player": pid, "friends": [{"name": p["name"], "pid": p["pid"]} for p in friends], "duels": state["duels"]}))


def cleanup():
    if not os.path.exists(STATE):
        print(json.dumps({"ok": True, "note": "nothing to clean"}))
        return
    with open(STATE, encoding="utf-8") as f:
        state = json.load(f)
    db, me, uids = db_of(), state["me"], state["friends"]
    db.rf_profiles.delete_many({"uid": {"$in": uids}})
    db.rf_friends.delete_many({"$or": [{"uid": {"$in": uids}}, {"fid": {"$in": uids}}]})
    db.rf_feed.delete_many({"uid": {"$in": uids}})
    db.rf_notices.delete_many({"$or": [{"uid": {"$in": uids}}, {"from_uid": {"$in": uids}}]})
    db.rf_challenges.delete_many({"$or": [{"from_uid": {"$in": uids}}, {"invites.uid": {"$in": uids}}]})
    db.rf_duels.delete_many({"$or": [{"id": {"$in": state["duels"]}}, {"players.uid": {"$in": uids}}]})
    db.rf_awards.delete_many({"$or": [{"uid": me, "ref": {"$in": ["duel:" + d for d in state["duels"]]}}, {"uid": {"$in": uids}}]})
    wallet = state["wallet"]
    gone = {k: "" for k in WALLET if k not in wallet}
    db.rf_profiles.update_one({"uid": me}, {"$set": wallet, **({"$unset": gone} if gone else {})})
    os.remove(STATE)
    print(json.dumps({"ok": True, "removed_friends": len(uids), "removed_duels": len(state["duels"]), "wallet_restored": sorted(wallet)}))


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "seed":
        seed(sys.argv[sys.argv.index("--pid") + 1] if "--pid" in sys.argv else "PF37CC308")
    elif command == "cleanup":
        cleanup()
    else:
        raise SystemExit(__doc__)
