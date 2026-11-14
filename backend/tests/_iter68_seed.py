"""Iteration 68 helper (tester): seed Champions Wall data / Cup Night reminder for the QA learner, and remove it by exact ids.
Usage: python _iter68_seed.py wall | remind | clean
State in /tmp/iter68_seed.json. Never prints tokens."""
import asyncio
import json
import os
import sys
import time
import uuid

from bson import json_util
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
load_dotenv(os.path.join(ROOT, ".env"))
from cups import DOORS_SECONDS, night_of  # noqa: E402

STATE = "/tmp/iter68_seed.json"


def load():
    return json_util.loads(open(STATE).read()) if os.path.exists(STATE) else {}


def save(s):
    open(STATE, "w").write(json_util.dumps(s))


async def main(cmd):
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    qa = await db.rf_profiles.find_one({"pid": "PF37CC308"})
    s = load()
    now = time.time()
    if cmd == "wall":
        day, start = night_of(now)
        show = day if now >= start else night_of(now - 86400)[0] if now < start - DOORS_SECONDS else None
        print("show day", show)
        tag = uuid.uuid4().hex[:6]
        other = {k: v for k, v in qa.items() if k not in ("_id",)}
        ouid, opid = f"TEST-i68-{tag}", f"P68{tag.upper()}"  # PID_RE: P + 8 hex
        other.update({"uid": ouid, "pid": opid, "name": "TEST_Champ Riya", "cups_won": 2, "cups_real": 1, "friend_code": None})
        for k in ("friend_code", "phone_hash", "phone_last4", "display_name"):
            other.pop(k, None)
        await db.rf_profiles.insert_one(other)
        s.update({"other_uid": ouid, "other_pid": opid, "qa_fields": {k: qa.get(k) for k in ("cups_won", "cups_real")}, "qa_missing": [k for k in ("cups_won", "cups_real") if k not in qa]})
        await db.rf_profiles.update_one({"uid": qa["uid"]}, {"$set": {"cups_won": 1, "cups_real": 1}})
        me = {"uid": qa["uid"], "pid": qa["pid"], "name": qa["name"], "bot": False}
        ot = {"uid": ouid, "pid": opid, "name": "TEST_Champ Riya", "bot": False}
        ids = [f"night-TESTi68-{tag}-{i}" for i in range(3)]
        await db.rf_cups.insert_many([
            {"id": ids[0], "kind": "open", "night": show, "night_no": 1, "size": 4, "label": "Physics", "status": "finished", "champion": qa["uid"], "title_no": 1, "finished_ts": now, "players": [me, {"uid": "bot-TESTi68-a", "name": "Rival", "bot": True}]},
            {"id": ids[1], "kind": "open", "night": show, "night_no": 2, "size": 8, "label": "Physics", "status": "finished", "champion": ouid, "title_no": 2, "finished_ts": now, "players": [ot, {"uid": "bot-TESTi68-b", "name": "Rival", "bot": True}]},
            {"id": ids[2], "kind": "open", "night": show, "night_no": 3, "size": 4, "label": "Physics", "status": "finished", "champion": "bot-TESTi68-c", "finished_ts": now, "players": [{"uid": "bot-TESTi68-c", "name": "Rival", "bot": True}, ot]},
        ])
        s["cups"] = ids
        save(s)
        print("seeded", ids, opid)
    elif cmd == "remind":
        day, _ = night_of(now)
        if await db.rf_cup_nights.find_one({"_id": day}):
            print("night doc exists for today; not touching"); return
        st = now + 290
        await db.rf_cup_nights.insert_one({"_id": day, "uids": [qa["uid"]], "status": "open", "start_ts": st})
        s.update({"night_day": day, "night_start": st})
        save(s)
        for _ in range(15):
            n = await db.rf_notices.find_one({"uid": qa["uid"], "kind": "cup_night", "night.day": day})
            if n:
                s.setdefault("notices", []).append(n["id"]); save(s); print("notice", n["id"], "done", n["done"]); return
            await asyncio.sleep(1)
        print("NO NOTICE after 15s")
    elif cmd == "clean":
        if s.get("cups"):
            print("cups", (await db.rf_cups.delete_many({"id": {"$in": s["cups"]}})).deleted_count)
        if s.get("other_uid"):
            print("other profile", (await db.rf_profiles.delete_one({"uid": s["other_uid"]})).deleted_count)
        if "qa_fields" in s:
            setf = {k: v for k, v in s["qa_fields"].items() if k not in s["qa_missing"]}
            upd = {}
            if setf: upd["$set"] = setf
            if s["qa_missing"]: upd["$unset"] = {k: "" for k in s["qa_missing"]}
            await db.rf_profiles.update_one({"uid": qa["uid"]}, upd)
            print("qa restored", upd)
        if s.get("night_day"):
            print("night", (await db.rf_cup_nights.delete_one({"_id": s["night_day"], "start_ts": s["night_start"]})).deleted_count)
            print("notices", (await db.rf_notices.delete_many({"uid": qa["uid"], "kind": "cup_night", "night.day": s["night_day"]})).deleted_count)
        os.remove(STATE)


asyncio.run(main(sys.argv[1]))
