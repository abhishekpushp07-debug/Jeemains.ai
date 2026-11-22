"""Phase 2 speed probe (live preview): Server-Timing app;dur of warm Rapid Fire GETs with a TEST player (5 calls each)."""
import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone

import requests
from dotenv import dotenv_values
from pymongo import MongoClient

BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
BE = dotenv_values("/app/backend/.env")
db = MongoClient(BE["MONGO_URL"])[BE["DB_NAME"]]
tok, uid = secrets.token_urlsafe(32), "TEST-p2qa-probe-" + secrets.token_hex(3)
db.rf_access.insert_one({"digest": hashlib.sha256(tok.encode()).hexdigest(), "uid": uid, "sid": "", "expires_at": datetime.now(timezone.utc) + timedelta(hours=1)})
s = requests.Session()
s.headers["Authorization"] = f"Bearer {tok}"
for p in ["/api/rf/catalog?exam=JEE", "/api/rf/daily?exam=JEE", "/api/rf/daily/board?exam=JEE", "/api/rf/leaderboard?exam=JEE",
          "/api/rf/league/gangwar", "/api/rf/league/friends", "/api/rf/history?exam=JEE", "/api/rf/revision?exam=JEE",
          "/api/rf/weak-topics?exam=JEE", "/api/rf/profile?exam=JEE"]:
    ts = []
    for _ in range(6):
        r = s.get(BASE + p, timeout=30)
        m = re.search(r"app;dur=([\d.]+)", r.headers.get("Server-Timing", ""))
        ts.append(float(m.group(1)) if m else -1)
    print(f"{p:40s} status={r.status_code} first={ts[0]:.1f}ms warm_max={max(ts[1:]):.1f}ms warm={[round(t,1) for t in ts[1:]]}")
