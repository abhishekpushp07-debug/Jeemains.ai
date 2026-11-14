"""Iter70: back up / raise / restore QA learner (pid PF37CC308) squad+wallet fields for the diamond-unlock UI test."""
import json, os, sys
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")
db = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
BK = "/tmp/iter70_qa_backup.json"
FIELDS = ["diamonds", "diamonds_spent", "owned", "squad"]
q = {"pid": "PF37CC308"}
cmd = sys.argv[1]
p = db.rf_profiles.find_one(q)
assert p, "QA profile not found"
if cmd == "show":
    print({k: p.get(k, "<absent>") for k in FIELDS + ["cups_won"]})
elif cmd == "backup":
    data = {k: p[k] for k in FIELDS if k in p}
    json.dump({"present": data, "absent": [k for k in FIELDS if k not in p]}, open(BK, "w"))
    print("backed up", data)
elif cmd == "raise":
    db.rf_profiles.update_one(q, {"$set": {"diamonds.red": 10}})
    print("raised red to 10")
elif cmd == "restore":
    b = json.load(open(BK))
    upd = {}
    if b["present"]:
        upd["$set"] = b["present"]
    if b["absent"]:
        upd["$unset"] = {k: "" for k in b["absent"]}
    db.rf_profiles.update_one(q, upd)
    p = db.rf_profiles.find_one(q)
    ok = all(p.get(k) == v for k, v in b["present"].items()) and all(k not in p for k in b["absent"])
    print("restored, exact match:", ok, {k: p.get(k, "<absent>") for k in FIELDS})
