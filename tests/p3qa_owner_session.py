"""Temporary owner_sessions row for the App Health browser check. `create` prints the token to /tmp/p3_owner.json (0600);
`delete` removes exactly that digest."""
import hashlib
import json
import os
import secrets
import sys
from datetime import datetime, timedelta, timezone

from dotenv import dotenv_values
from pymongo import MongoClient

BE = dotenv_values("/app/backend/.env")
db = MongoClient(BE["MONGO_URL"])[BE["DB_NAME"]]
F = "/tmp/p3_owner.json"
if sys.argv[1] == "create":
    tok = secrets.token_urlsafe(32)
    dg = hashlib.sha256(tok.encode()).hexdigest()
    db.owner_sessions.insert_one({"digest": dg, "who": "qa***@test", "expires_at": datetime.now(timezone.utc) + timedelta(hours=1)})
    fd = os.open(F, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.write(fd, json.dumps({"token": tok, "digest": dg}).encode())
    os.close(fd)
    print("created", len(tok))
else:
    d = json.load(open(F))
    print("deleted", db.owner_sessions.delete_many({"digest": d["digest"]}).deleted_count)
    os.remove(F)
