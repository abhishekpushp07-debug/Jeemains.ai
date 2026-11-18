"""QA helper: temporarily pull ONE mock (4ff8dce7) from the QA account's rf_dreams doc so the result page must re-record it.
usage: python qa_mock_pull.py pull|check|restore  (restore puts the saved copy back only if it's missing)"""
import json
import os
import sys

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv("/app/backend/.env")
db = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
MID = "4ff8dce7-c1a2-4b3a-b9a9-723e13252d00"
SAVE = "/tmp/qa_mock_saved.json"
doc = db.rf_dreams.find_one({"mocks.id": MID}) if sys.argv[1] == "pull" else None
cmd = sys.argv[1]
if cmd == "pull":
    assert doc, "mock not found"
    m = next(x for x in doc["mocks"] if x["id"] == MID)
    json.dump({"uid": doc["uid"], "mock": m}, open(SAVE, "w"))
    db.rf_dreams.update_one({"uid": doc["uid"]}, {"$pull": {"mocks": {"id": MID}}})
    print("pulled; saved copy", {k: m[k] for k in ("score", "raw", "rawMax", "at", "title")})
saved = json.load(open(SAVE))
cur = db.rf_dreams.find_one({"uid": saved["uid"]})
has = [x for x in cur["mocks"] if x["id"] == MID]
print("present now:", bool(has), {k: has[0][k] for k in ("score", "raw", "rawMax", "at", "title")} if has else "")
print("n mocks", len(cur["mocks"]), "dreams", [d["id"] for d in cur["dreams"]])
if cmd == "restore" and not has:
    db.rf_dreams.update_one({"uid": saved["uid"]}, {"$push": {"mocks": {"$each": [saved["mock"]], "$sort": {"at": -1}, "$slice": 30}}})
    print("restored saved copy")
