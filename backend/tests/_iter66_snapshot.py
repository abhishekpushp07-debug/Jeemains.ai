"""Iteration 66 helper: snapshot / restore the QA RF profile and remove the cups (+duels/feed/awards) the QA player won during UI tests.
Usage: python _iter66_snapshot.py save|restore|cups"""
import asyncio
import json
import os
import sys

from bson import json_util
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
SNAP = "/tmp/iter66_profile.json"


async def main(cmd):
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    prof = await db.rf_profiles.find_one({"pid": "PF37CC308"})
    uid = prof["uid"]
    if cmd == "save":
        old = await db.rf_cups.find({"players.uid": uid}, {"id": 1}).to_list(1000)
        open(SNAP, "w").write(json_util.dumps({"prof": prof, "cups": [c["id"] for c in old]}))
        print("saved; existing cups", len(old))
    elif cmd == "cups":
        s = json_util.loads(open(SNAP).read())
        new = await db.rf_cups.find({"players.uid": uid, "id": {"$nin": s["cups"]}}, {"_id": 0, "id": 1, "status": 1, "champion": 1, "title_no": 1}).to_list(50)
        print([(c["id"][:8], c["status"], c.get("champion") == uid, c.get("title_no")) for c in new])
    elif cmd == "restore":
        s = json_util.loads(open(SNAP).read())
        new = await db.rf_cups.find({"players.uid": uid, "id": {"$nin": s["cups"]}}).to_list(50)
        cids = [c["id"] for c in new]
        dids = [m["duel_id"] for c in new for rd in c.get("rounds") or [] for m in rd if m.get("duel_id")]
        print("duels", (await db.rf_duels.delete_many({"id": {"$in": dids}})).deleted_count)
        print("cups", (await db.rf_cups.delete_many({"id": {"$in": cids}})).deleted_count)
        print("feed", (await db.rf_feed.delete_many({"id": {"$in": ["cup:" + c for c in cids]}})).deleted_count)
        extra = sys.argv[2].split(",") if len(sys.argv) > 2 else []  # duel id prefixes of cups already removed
        pat = "^duel:(" + "|".join([d for d in dids] + extra) + ")" if dids or extra else None
        if pat:
            print("duel feed", (await db.rf_feed.delete_many({"uid": uid, "id": {"$regex": pat}})).deleted_count)
        print("awards", (await db.rf_awards.delete_many({"uid": uid, "ref": {"$in": ["duel:" + d for d in dids] + ["cup:" + c for c in cids]}})).deleted_count)
        await db.rf_profiles.replace_one({"_id": s["prof"]["_id"]}, s["prof"])
        print("profile restored", {k: s["prof"].get(k) for k in ("coins", "xp", "cups_won", "cups_real", "badges")})


asyncio.run(main(sys.argv[1]))
