"""Iteration 65: drive an Open Cup (4) for the QA learner to a championship so the first-crown celebration can be seen.
Usage: python _iter65_crown.py start   -> snapshot profile, create cup via the RF API (same as FIND A CUP), win every round
       python _iter65_crown.py restore -> delete that cup, its duels, and put the profile fields back
Never prints tokens."""
import asyncio
import json
import os
import sys
import time

import requests
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, ".env"))
BASE = [l.split("=", 1)[1].strip() for l in open("/app/frontend/.env") if l.startswith("EXPO_PUBLIC_BACKEND_URL=")][0].rstrip("/") + "/api/rf"
STATE = "/tmp/iter65_crown.json"
FIELDS = ["coins", "xp", "level", "cups_won", "cups_real", "badges", "wins", "losses", "streak", "best_streak", "trophies", "stats"]


def bearer():
    sid = open("/tmp/jl_sid.txt").read().strip()
    r = requests.post(BASE + "/access", headers={"X-JL-Sid": sid, "Content-Type": "application/json"}, json={}, timeout=20)
    r.raise_for_status()
    return {"Authorization": "Bearer " + r.json()["token"], "Content-Type": "application/json"}


async def start():
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    prof = await db.rf_profiles.find_one({"pid": "PF37CC308"})
    uid = prof["uid"]
    h = bearer()
    cup = requests.post(BASE + "/cups", headers=h, json={"kind": "open", "size": 4, "picks": [{"subject": "Physics", "chapter": None}]}, timeout=20).json()
    cid = cup["id"]
    json.dump({"cid": cid, "uid": uid, "snap": {k: prof.get(k) for k in FIELDS if k in prof}, "missing": [k for k in FIELDS if k not in prof]}, open(STATE, "w"), default=str)
    print("cup", cid, cup["status"], len(cup["players"]))
    await db.rf_cups.update_one({"id": cid}, {"$set": {"expires_ts": time.time() - 1}})
    done = set()
    for _ in range(60):
        v = requests.get(f"{BASE}/cups/{cid}", headers=h, timeout=20).json()
        if v["status"] == "finished":
            print("finished; champion idx", v["champion"], "you?", v["players"][v["champion"]]["you"], "first_title", v["first_title"], "real", v["real_players"])
            return
        did = v.get("my_duel")
        if did and did not in done:
            d = await db.rf_duels.find_one({"id": did})
            if d["start_at"] > time.time():
                await db.rf_duels.update_one({"id": did}, {"$set": {"start_at": time.time() - 1}})
            total = len(d["card_ids"])
            answers = [{"i": i, "choice": 0, "outcome": "correct", "ms": 1000} for i in range(total)]
            await db.rf_duels.update_one({"id": did, "players.uid": uid}, {"$set": {"players.$.answers": answers, "players.$.score": total, "players.$.ms": total * 1000}})
            await db.rf_duels.update_one({"id": did}, {"$set": {"players.$[h].done": True}}, array_filters=[{"h.bot": {"$ne": True}}])
            r = requests.get(f"{BASE}/duels/{did}", headers=h, timeout=20).json()
            print("round", v["round"], "duel", r.get("status"), "winner me?", r.get("winner") == uid)
            done.add(did)
        time.sleep(4)
    print("not finished in time", v["status"], v["round"])


async def restore():
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    s = json.load(open(STATE))
    c = await db.rf_cups.find_one({"id": s["cid"]})
    dids = [m["duel_id"] for rd in (c or {}).get("rounds") or [] for m in rd if m.get("duel_id")]
    print("duels deleted", (await db.rf_duels.delete_many({"id": {"$in": dids}})).deleted_count)
    print("cup deleted", (await db.rf_cups.delete_one({"id": s["cid"]})).deleted_count)
    await db.rf_feed.delete_many({"id": "cup:" + s["cid"]})
    upd = {"$set": s["snap"]}
    if s["missing"]:
        upd["$unset"] = {k: "" for k in s["missing"]}
    await db.rf_profiles.update_one({"uid": s["uid"]}, upd)
    print("profile restored fields", list(s["snap"]))


async def watch():
    """DB-only driver: the cup was opened in the UI (FIND A CUP); the browser keeps polling it, this wins every QA match."""
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    prof = await db.rf_profiles.find_one({"pid": "PF37CC308"})
    uid = prof["uid"]
    c = None
    for _ in range(30):
        c = await db.rf_cups.find_one({"players.uid": uid, "status": {"$in": ["open", "live"]}, "kind": "open", "night": None}, sort=[("created_ts", -1)])
        if c:
            break
        time.sleep(2)
    if not c:
        print("no cup found"); return
    cid = c["id"]
    json.dump({"cid": cid, "uid": uid, "snap": {k: prof.get(k) for k in FIELDS if k in prof}, "missing": [k for k in FIELDS if k not in prof]}, open(STATE, "w"), default=str)
    print("cup", cid, flush=True)
    await db.rf_cups.update_one({"id": cid, "status": "open"}, {"$set": {"expires_ts": time.time() - 1}})
    done = set()
    for _ in range(90):
        c = await db.rf_cups.find_one({"id": cid})
        if c["status"] == "finished":
            print("finished champion is QA:", c.get("champion") == uid, flush=True); return
        rnd = c.get("round", -1)
        cur = c["rounds"][rnd] if c.get("rounds") and 0 <= rnd < len(c["rounds"]) else []
        m = next((m for m in cur if uid in (m["a"], m["b"]) and m.get("duel_id") and not m.get("winner")), None)
        if m and m["duel_id"] not in done:
            d = await db.rf_duels.find_one({"id": m["duel_id"]})
            total = len(d["card_ids"])
            answers = [{"i": i, "choice": 0, "outcome": "correct", "ms": 1000} for i in range(total)]
            await db.rf_duels.update_one({"id": d["id"]}, {"$set": {"start_at": min(d["start_at"], time.time() - 1)}})
            await db.rf_duels.update_one({"id": d["id"], "players.uid": uid}, {"$set": {"players.$.answers": answers, "players.$.score": total, "players.$.ms": total * 1000}})
            await db.rf_duels.update_one({"id": d["id"]}, {"$set": {"players.$[h].done": True}}, array_filters=[{"h.bot": {"$ne": True}}])
            done.add(d["id"])
            print("won round", rnd, d["id"][:8], flush=True)
        time.sleep(3)
    print("timeout", c["status"], c.get("round"))


if __name__ == "__main__":
    asyncio.run({"start": start, "watch": watch}.get(sys.argv[1], restore)())
