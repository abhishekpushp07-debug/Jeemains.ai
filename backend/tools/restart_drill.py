"""Restart drill (Phase 3, Level 6): a live match keeps going when the server copy holding it stops.

Two server copies on one database (A and B, e.g. ports 8002 and 8005). A TEST player starts a Practice Rival match on A,
listens on A's live socket, answers half the cards, then A is stopped gracefully (SIGTERM, like a new release). The drill
checks that A's socket closes with 1012 ("service restart"), that the player reconnects to B and finishes the match
there, and that the reward is paid exactly once. Only a `TEST-drill-*` identity is used; `--cleanup` removes it.

    python tools/restart_drill.py --a 8002 --b 8005 --a-pid <uvicorn pid of A>
    python tools/restart_drill.py --cleanup
"""
import argparse
import asyncio
import hashlib
import json
import os
import secrets
import signal
import time
import uuid
from datetime import datetime, timedelta, timezone

import httpx
import websockets
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
PREFIX = "TEST-drill-"


def mongo():
    return MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]


def cleanup():
    db, q = mongo(), {"$regex": "^" + PREFIX}
    print(json.dumps({"cleanup": {k: c.delete_many(f).deleted_count for k, c, f in (
        ("duels", db.rf_duels, {"players.uid": q}), ("profiles", db.rf_profiles, {"uid": q}), ("awards", db.rf_awards, {"uid": q}),
        ("learning", db.rf_learning_events, {"uid": q}), ("access", db.rf_access, {"uid": q}))}}))


async def drill(a, b, a_pid):
    uid, token = PREFIX + uuid.uuid4().hex[:8], secrets.token_urlsafe(32)
    mongo().rf_access.insert_one({"digest": hashlib.sha256(token.encode()).hexdigest(), "uid": uid, "sid": "", "expires_at": datetime.now(timezone.utc) + timedelta(minutes=20)})
    h = {"Authorization": "Bearer " + token}
    report = {"uid": uid}
    async with httpx.AsyncClient(headers=h, timeout=30) as c:
        base_a, base_b = f"http://127.0.0.1:{a}/api/rf", f"http://127.0.0.1:{b}/api/rf"
        d = (await c.post(base_a + "/duels", json={"exam": "JEE", "subject": "Physics", "mode": "invite", "name": "Drill", "request_id": uuid.uuid4().hex})).json()
        d = (await c.post(f"{base_a}/duels/{d['id']}/bot", json={})).json()
        did, total = d["id"], d["total"]
        ws = await websockets.connect(f"ws://127.0.0.1:{a}/api/rf/duels/{did}/ws")
        await ws.send(json.dumps({"token": token, "lite": 1}))
        await ws.recv()
        await asyncio.sleep(max(0, d["start_at"] - d["server_now"]) + 0.2)
        half = total // 2
        for k in range(half):
            r = await c.post(f"{base_a}/duels/{did}/answer", json={"index": k, "choice": k % 4, "outcome": "answer", "ms": 800})
            assert r.status_code == 200, r.text
        t0 = time.time()
        os.kill(a_pid, signal.SIGTERM)  # a new release: copy A stops
        try:
            while True:
                await asyncio.wait_for(ws.recv(), timeout=10)
        except websockets.ConnectionClosed as closed:
            report["socket_close_code"] = closed.rcvd.code if closed.rcvd else None
            report["socket_closed_after_s"] = round(time.time() - t0, 2)
        ws = await websockets.connect(f"ws://127.0.0.1:{b}/api/rf/duels/{did}/ws")  # the app reconnects (to copy B)
        await ws.send(json.dumps({"token": token, "lite": 1}))
        first = json.loads(await ws.recv())
        report["copy_b_sees_answers"] = next(p["answered"] for p in first["players"] if p["you"])
        for k in range(half, total):
            r = await c.post(f"{base_b}/duels/{did}/answer", json={"index": k, "choice": k % 4, "outcome": "answer", "ms": 800})
            assert r.status_code == 200, r.text
        final = (await c.get(f"{base_b}/duels/{did}")).json()
        await ws.close()
    db = mongo()
    report.update(status=final["status"], answered=next(p["answered"] for p in final["players"] if p["you"]), total=total,
                  rewards_paid=db.rf_awards.count_documents({"uid": uid, "ref": "duel:" + did}),
                  paid_refs=db.rf_profiles.find_one({"uid": uid}, {"paid_refs": 1})["paid_refs"].count("duel:" + did),
                  ws_nodes_left=len(db.rf_duels.find_one({"id": did}, {"ws_nodes": 1}).get("ws_nodes") or []))
    report["passed"] = (report.get("socket_close_code") == 1012 and report["copy_b_sees_answers"] == half and report["status"] == "finished"
                        and report["answered"] == total and report["rewards_paid"] == 1 and report["paid_refs"] == 1)
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", type=int, default=8002)
    ap.add_argument("--b", type=int, default=8005)
    ap.add_argument("--a-pid", type=int, default=0)
    ap.add_argument("--cleanup", action="store_true")
    args = ap.parse_args()
    if args.cleanup:
        cleanup()
    else:
        asyncio.run(drill(args.a, args.b, args.a_pid))
