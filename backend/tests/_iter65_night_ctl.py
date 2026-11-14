"""Iteration 65 helper: move tonight's Cup Night start (doors / live) or restore it. Usage: python _iter65_night_ctl.py doors|live|state|restore"""
import asyncio
import os
import sys
import time

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
from cups import night_of  # noqa: E402

QA_PID = "PF37CC308"


async def main(cmd):
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    day = night_of(time.time())[0]
    qa = (await db.rf_profiles.find_one({"pid": QA_PID}, {"uid": 1}))["uid"]
    if cmd == "doors":
        await db.rf_cup_nights.update_one({"_id": day}, {"$set": {"start_ts": time.time() + 1800, "status": "open"}, "$setOnInsert": {"uids": []}}, upsert=True)
    elif cmd == "live":
        await db.rf_cup_nights.update_one({"_id": day}, {"$set": {"start_ts": time.time() - 1}})
    elif cmd == "restore":
        cups = await db.rf_cups.find({"night": day, "players.uid": qa}, {"_id": 0, "id": 1, "rounds": 1}).to_list(50)
        duel_ids = [m["duel_id"] for c in cups for rd in c.get("rounds") or [] for m in rd if m.get("duel_id")]
        print("night cups with QA:", [c["id"] for c in cups], "duels:", len(duel_ids))
        r = await db.rf_cups.delete_many({"night": day, "players.uid": qa})
        print("deleted cups", r.deleted_count)
        n = await db.rf_cup_nights.find_one({"_id": day})
        others = [u for u in (n or {}).get("uids", []) if u != qa and not u.startswith("TEST")]
        if others:
            print("REAL players present; only pulling QA", len(others))
            await db.rf_cup_nights.update_one({"_id": day}, {"$pull": {"uids": qa}})
        else:
            print("deleted night", (await db.rf_cup_nights.delete_one({"_id": day})).deleted_count)
    n = await db.rf_cup_nights.find_one({"_id": day})
    if n:
        n["start_in"] = round(n.get("start_ts", 0) - time.time())
        n["uids"] = ["QA" if u == qa else u[:8] for u in n.get("uids", [])]
    print("night:", n)
    print("QA active cups:", await db.rf_cups.find({"players.uid": qa, "status": {"$in": ["open", "live"]}}, {"_id": 0, "id": 1, "status": 1, "night": 1, "size": 1}).to_list(10))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "state"))
