# Iteration113: read-only post-test checks (QA learner's All India try unplayed today, no leftover iter113 rows, qa30 leaderboard residue)
import os
from pathlib import Path
from dotenv import dotenv_values
from pymongo import MongoClient

env = dotenv_values(Path(__file__).resolve().parents[1] / ".env")
db = MongoClient(env["MONGO_URL"])[env["DB_NAME"]]
qa = db.rf_profiles.find_one({"pid": "PF37CC308"}, {"uid": 1})
latest = list(db.rf_daily_plays.find({"uid": qa["uid"]}, {"_id": 0, "day": 1, "status": 1, "exam": 1}).sort("day", -1).limit(2)) if qa else None
print("QA learner latest daily plays:", latest)
print("latest rf_daily days:", [d.get("day") for d in db.rf_daily.find({}, {"day": 1}).sort("day", -1).limit(2)])
for c in ["rf_sessions", "rf_profiles", "rf_learning_events", "rf_challenges", "rf_link_visits", "rf_daily_plays"]:
    key = "user_id" if c == "rf_sessions" else ("from_uid" if c == "rf_challenges" else ("cid" if c == "rf_link_visits" else "uid"))
    print(c, "iter113 leftovers:", db[c].count_documents({key: {"$regex": "^TEST-iter113"}}))
print("TEST_iter113 scratch collections:", [n for n in db.list_collection_names() if n.startswith("TEST_iter113")])
print("qa30 profiles:", db.rf_profiles.count_documents({"uid": {"$regex": "^qa30"}}))
print("TEST-daily leftovers:", db.rf_daily_plays.count_documents({"uid": {"$regex": "^TEST-"}}), db.rf_profiles.count_documents({"uid": {"$regex": "^TEST-(daily|weak)"}}))
