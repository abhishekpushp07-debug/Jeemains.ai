# Cleanup helper for iter25 UI probes: removes TEST-ui- duel/profile/award docs and prints the pilot profile counters.
import os
from dotenv import load_dotenv
from pymongo import MongoClient
load_dotenv("/app/backend/.env")
DB = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
rx = {"$regex": "^TEST-ui-"}
print("duels", DB.rf_duels.delete_many({"players.uid": rx}).deleted_count)
for c in ("rf_profiles", "rf_awards", "rf_sessions", "rf_rewards", "rf_game"):
    print(c, DB[c].delete_many({"$or": [{"uid": rx}, {"user_id": rx}]}).deleted_count)
p = DB.rf_profiles.find_one({"uid": "db0c62b8-eeaf-41be-b8b1-05f5f34ac1d8"}, {"_id": 0, "duels": 1, "wins": 1, "coins": 1})
print("pilot profile", p)
print("leftover TEST- duels", DB.rf_duels.count_documents({"players.uid": {"$regex": "^TEST-"}}))
