"""Iteration 78 UI fixture for match links: TEST players with short grants (tokens kept in a 0600 /tmp file), plus exact cleanup.

python tests/iter78_link_fixture.py setup | host <subject> <key> | accept <cid> <key> | start <cid> <key> | cleanup
"""
import asyncio
import hashlib
import json
import os
import secrets
import sys
from datetime import datetime, timedelta, timezone

import httpx
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
from social import make_pid, remember_identity  # noqa: E402

STATE = "/tmp/iter78_link_fixture.json"
QA_PID = "PF37CC308"
BASE = os.environ.get("RF_BASE", "http://localhost:8001/api/rf")


def load():
    return json.load(open(STATE)) if os.path.exists(STATE) else {}


async def main(cmd, *args):
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    st = load()
    if cmd == "setup":
        tag = secrets.token_hex(3)
        users = {}
        for i, k in enumerate(["joiner", "host", "outsider"]):
            uid = f"TEST-iter78-{tag}-{k}"
            token = secrets.token_urlsafe(24)
            await db.rf_access.insert_one({"digest": hashlib.sha256(token.encode()).hexdigest(), "uid": uid, "sid": "", "expires_at": datetime.now(timezone.utc) + timedelta(minutes=90)})
            await remember_identity(db, uid, {"name": f"TEST {k.title()}78", "phone": f"90000078{i:02d}"})
            users[k] = {"uid": uid, "pid": make_pid(uid), "token": token}
        st = {"users": users}
        fd = os.open(STATE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        os.write(fd, json.dumps(st).encode())
        os.close(fd)
        print({k: v["pid"] for k, v in users.items()})
        return
    users = st["users"]
    h = lambda k: {"Authorization": "Bearer " + users[k]["token"]}  # noqa: E731
    async with httpx.AsyncClient(base_url=BASE, timeout=20) as s:
        if cmd == "host":
            r = await s.post("/challenges", json={"link": True, "subject": args[0]}, headers=h(args[1]))
            print(r.status_code, r.json().get("id"))
        elif cmd == "invite":  # invite-only room for the QA learner (needs friendship first)
            r = await s.post("/challenges", json={"pids": [QA_PID], "subject": "Physics"}, headers=h(args[0]))
            print(r.status_code, r.json().get("id"), r.json().get("single"), r.json().get("link"))
        elif cmd in ("accept", "start", "get", "cancel"):
            fn = s.get if cmd == "get" else s.post
            path = f"/challenges/{args[0]}" + ("" if cmd == "get" else f"/{cmd}")
            r = await (fn(path, headers=h(args[1])) if cmd == "get" else fn(path, json={}, headers=h(args[1])))
            j = r.json()
            print(r.status_code, {k: j.get(k) for k in ("status", "my_status", "joined", "friend", "duel_id", "detail")})
        elif cmd == "cleanup":
            uids = [u["uid"] for u in users.values()]
            qa = (await db.rf_profiles.find_one({"pid": QA_PID}, {"uid": 1}))["uid"]
            out = {
                "access": (await db.rf_access.delete_many({"uid": {"$in": uids}})).deleted_count,
                "friends": (await db.rf_friends.delete_many({"$or": [{"uid": {"$in": uids}}, {"fid": {"$in": uids}}]})).deleted_count,
                "notices": (await db.rf_notices.delete_many({"$or": [{"uid": {"$in": uids}}, {"uid": qa, "from_uid": {"$in": uids}}]})).deleted_count,
                "challenges": (await db.rf_challenges.delete_many({"$or": [{"from_uid": {"$in": uids}}, {"invites.uid": {"$in": uids}}]})).deleted_count,
                "duels": (await db.rf_duels.delete_many({"players.uid": {"$in": uids}})).deleted_count,
                "blocks": (await db.rf_blocks.delete_many({"$or": [{"uid": {"$in": uids}}, {"bid": {"$in": uids}}]})).deleted_count,
                "profiles": (await db.rf_profiles.delete_many({"uid": {"$in": uids}})).deleted_count,
            }
            print(out, "qa friends left:", await db.rf_friends.count_documents({"uid": qa}))
            os.remove(STATE)


if __name__ == "__main__":
    asyncio.run(main(*sys.argv[1:]))
