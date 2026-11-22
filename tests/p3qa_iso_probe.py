"""Samples date-like strings from RF responses (orjson parity: ISO format) using an ephemeral TEST-p3qa grant; cleans up."""
import hashlib
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import requests
from dotenv import dotenv_values
from pymongo import MongoClient

BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
BE = dotenv_values("/app/backend/.env")
db = MongoClient(BE["MONGO_URL"])[BE["DB_NAME"]]
tok = secrets.token_urlsafe(32)
uid = "TEST-p3qa-iso-" + secrets.token_hex(3)
dg = hashlib.sha256(tok.encode()).hexdigest()
db.rf_access.insert_one({"digest": dg, "uid": uid, "sid": "", "expires_at": datetime.now(timezone.utc) + timedelta(hours=1)})
H = {"Authorization": f"Bearer {tok}"}
DATE = re.compile(r'"([A-Za-z_]+)":"(\d{4}-\d{2}-\d{2}[T ][^"]*)"')
try:
    s = requests.post(f"{BASE}/api/rf/sessions", json={"exam": "JEE", "subject": "Physics", "count": 30, "request_id": uuid.uuid4().hex}, headers=H, timeout=30).json()
    requests.post(f"{BASE}/api/rf/sessions/{s['id']}/complete", json={"results": []}, headers=H, timeout=30)
    for p in ["/api/rf/profile", f"/api/rf/sessions/{s['id']}", "/api/rf/history?exam=JEE", "/api/rf/inbox", "/api/rf/daily?exam=JEE", "/api/rf/duels"]:
        r = requests.get(BASE + p, headers=H, timeout=30)
        found = sorted({(k, v) for k, v in DATE.findall(r.text)})[:4]
        print(p, r.status_code, found)
finally:
    print("cleanup", {c: db[c].delete_many({"uid": uid}).deleted_count for c in ("rf_access", "rf_awards", "rf_learning_events", "rf_profiles")},
          db.rf_sessions.delete_many({"user_id": uid}).deleted_count, db.rf_profiles.delete_many({"_id": uid}).deleted_count)
