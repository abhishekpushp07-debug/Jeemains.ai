"""Lists (and with --delete removes) records left by Phase 3 QA TEST-p3qa-* players, matching uid-like fields exactly by regex
^TEST-p3qa-. Also lists rf_health_nodes. Run: python tests/p3qa_leftovers.py [--delete]"""
import re
import sys
import time

from dotenv import dotenv_values
from pymongo import MongoClient

BE = dotenv_values("/app/backend/.env")
db = MongoClient(BE["MONGO_URL"])[BE["DB_NAME"]]
rx = re.compile("^TEST-p3qa-")
FIELDS = ("uid", "_id", "user_id", "host_uid", "players.uid", "uids", "a", "b", "owner", "player")
for col in db.list_collection_names():
    for f in FIELDS:
        try:
            n = db[col].count_documents({f: rx})
        except Exception:
            continue
        if n:
            print(col, f, n)
            if "--delete" in sys.argv:
                print("  deleted", db[col].delete_many({f: rx}).deleted_count)
for n in db.rf_health_nodes.find({}, {"_id": 1, "started": 1, "ts": 1}):
    print("node", n["_id"][:6], "age", round(time.time() - n["ts"]), "up", round(time.time() - n.get("started", 0)))
