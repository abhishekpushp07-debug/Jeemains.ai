# Test helper (iter25 UI): dumps answer keys of TEST-ui- duels to /tmp/iter25_keys.json so the browser probe can answer correctly.
import os, json, time
from dotenv import load_dotenv
from pymongo import MongoClient
load_dotenv("/app/backend/.env")
DB = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
end = time.time() + 240
while time.time() < end:
    out = {}
    for d in DB.rf_duels.find({"players.uid": {"$regex": "^TEST-ui-"}}, {"id": 1, "card_ids": 1}):
        keys = {c["id"]: c["answer"] for c in DB.rf_cards.find({"id": {"$in": d["card_ids"]}}, {"id": 1, "answer": 1})}
        out[d["id"]] = [keys.get(c) for c in d["card_ids"]]
    json.dump(out, open("/tmp/iter25_keys.json", "w"))
    time.sleep(1)
