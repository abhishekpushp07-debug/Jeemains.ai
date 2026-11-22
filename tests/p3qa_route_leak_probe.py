"""Probe: does a letter-only friend code in the URL show up in App Health routes? Creates TEST-p3qa grant + owner session,
cleans both up exactly."""
import hashlib
import secrets
import time
from datetime import datetime, timedelta, timezone

import requests
from dotenv import dotenv_values
from pymongo import MongoClient

BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
BE = dotenv_values("/app/backend/.env")
db = MongoClient(BE["MONGO_URL"])[BE["DB_NAME"]]
tok, otok = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
uid = "TEST-p3qa-code-" + secrets.token_hex(3)
dg, odg = hashlib.sha256(tok.encode()).hexdigest(), hashlib.sha256(otok.encode()).hexdigest()
exp = datetime.now(timezone.utc) + timedelta(hours=1)
db.rf_access.insert_one({"digest": dg, "uid": uid, "sid": "", "expires_at": exp})
db.owner_sessions.insert_one({"digest": odg, "who": "qa***@test", "expires_at": exp})
try:
    code = "QAZWSXED"
    for _ in range(40):
        r = requests.get(f"{BASE}/api/rf/friends/code/{code}", headers={"Authorization": f"Bearer {tok}"}, timeout=20)
    print("friend code lookup:", r.status_code, r.text[:120])
    time.sleep(12)
    d = requests.get(f"{BASE}/api/owner/health/data", cookies={"jl_owner": otok}, timeout=20)
    routes = [x["route"] for x in d.json()["routes"]]
    print("routes:", routes)
    print("LEAK" if any(code in x for x in routes) else "no leak", "| raw contains code:", code in d.text)
finally:
    print("cleanup", db.rf_access.delete_many({"digest": dg}).deleted_count, db.owner_sessions.delete_many({"digest": odg}).deleted_count,
          db.rf_profiles.delete_many({"_id": uid}).deleted_count, db.rf_profiles.delete_many({"uid": uid}).deleted_count)
