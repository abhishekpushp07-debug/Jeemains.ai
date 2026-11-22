"""Read-only: live health-alert watcher rows on the preview DB (rf_meta alert:* and turn:health_alerts)."""
import time

from dotenv import dotenv_values
from pymongo import MongoClient

BE = dotenv_values("/app/backend/.env")
db = MongoClient(BE["MONGO_URL"])[BE["DB_NAME"]]


def snap():
    out = {}
    for k in ("website", "errors", "packed", "jobs"):
        d = db.rf_meta.find_one({"_id": "alert:" + k}) or {}
        out[k] = {"checked_ago": round(time.time() - d["checked"], 1) if d.get("checked") else None, "active": d.get("active"),
                  "hits": d.get("hits"), "clears": d.get("clears"), "last_mail_at": bool(d.get("last_mail_at")),
                  "problem_mailed_at": bool(d.get("problem_mailed_at")), "detail": d.get("detail")}
    t = db.rf_meta.find_one({"_id": "turn:health_alerts"}) or {}
    out["turn_until_in_s"] = round(t["until"] - time.time(), 1) if t.get("until") else None
    out["host"] = (db.rf_meta.find_one({"_id": "alert:host"}) or {}).get("host")
    out["test_at_ago"] = round(time.time() - (db.rf_meta.find_one({"_id": "alert:test"}) or {}).get("at", 0))
    out["days"] = list(db.rf_meta.find({"_id": {"$regex": "^alert:day:"}}))
    return out


if __name__ == "__main__":
    a = snap()
    print(a)
    time.sleep(35)
    b = snap()
    print(b)
    for k in ("website", "errors", "packed", "jobs"):
        print(k, "checked advanced:", a[k]["checked_ago"] is not None and b[k]["checked_ago"] is not None and b[k]["checked_ago"] < a[k]["checked_ago"] + 35 - 1)
