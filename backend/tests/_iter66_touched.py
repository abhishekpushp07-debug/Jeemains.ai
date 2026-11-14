"""Iteration 66: list QA-player docs created/updated since the test run started (any collection with uid + ts/at fields)."""
import asyncio
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))


async def main(since):
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    uid = (await db.rf_profiles.find_one({"pid": "PF37CC308"}))["uid"]
    for name in sorted(await db.list_collection_names()):
        if not name.startswith("rf"):
            continue
        q = {"$and": [{"$or": [{"uid": uid}, {"players.uid": uid}, {"uids": uid}]},
                      {"$or": [{"ts": {"$gte": since}}, {"created_ts": {"$gte": since}}, {"at": {"$gte": datetime.fromtimestamp(since, timezone.utc)}}, {"start_at": {"$gte": since}}]}]}
        n = await db[name].count_documents(q)
        if n:
            docs = await db[name].find(q, {"_id": 1, "id": 1, "ref": 1, "kind": 1}).to_list(20)
            print(name, n, [str(d.get("id") or d.get("ref") or d.get("kind") or d["_id"])[:40] for d in docs])
            if len(sys.argv) > 2 and sys.argv[2] == "delete" and name in ("rf_events", "rf_activity", "rf_history", "rf_day", "rf_inbox", "rf_notifications"):
                print("  deleted", (await db[name].delete_many(q)).deleted_count)


asyncio.run(main(float(sys.argv[1])))
