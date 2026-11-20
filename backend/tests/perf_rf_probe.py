"""Rapid Fire speed probe (local only): times the hot endpoints with one fixed TEST player.

    python tests/perf_rf_probe.py            # solo sprint + practice-rival match, prints server time per call

Nothing goes to the website and nothing is deleted: the player is the local `TEST-perf-probe` id (TEST players never
show on boards or feeds), its sprints and match are finished normally, and its 10-minute grant runs out by itself.
"""
import asyncio
import hashlib
import os
import secrets
import statistics
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import aiohttp
from dotenv import load_dotenv
from pymongo import AsyncMongoClient

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
BASE = os.environ.get("PERF_BASE", "http://localhost:8001") + "/api/rf"


async def main():
    client = AsyncMongoClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    uid, token = "TEST-perf-probe", secrets.token_urlsafe(32)
    await db.rf_access.insert_one({"digest": hashlib.sha256(token.encode()).hexdigest(), "uid": uid, "sid": "", "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10)})
    await db.rf_profiles.update_one({"uid": uid}, {"$set": {"name": "TEST perf"}}, upsert=True)
    rows = {}

    async with aiohttp.ClientSession(headers={"Authorization": f"Bearer {token}"}) as http:
        async def call(label, method, path, body=None):
            started = time.perf_counter()
            async with http.request(method, BASE + path, json=body) as r:
                data = await r.json(content_type=None)
                wall = (time.perf_counter() - started) * 1000
                server = float((r.headers.get("Server-Timing") or "app;dur=0").split("dur=")[1])
                rows.setdefault(label, []).append((server, wall, r.status))
                return data

        try:
            for _ in range(3):
                for label, path in (("GET profile", "/profile"), ("GET inbox", "/inbox"), ("GET daily", "/daily?exam=JEE"), ("GET revision", "/revision?exam=JEE"),
                                    ("GET weak-topics", "/weak-topics?exam=JEE"), ("GET friends", "/friends"), ("GET gangs", "/gangs"), ("GET leaderboard", "/leaderboard?exam=JEE"),
                                    ("GET history", "/history?exam=JEE"), ("GET duels", "/duels?exam=JEE"), ("GET duels/live", "/duels/live"), ("GET cups/night", "/cups/night"),
                                    ("GET cups/champions", "/cups/champions"), ("GET badla", "/badla"), ("GET feed", "/feed"), ("GET shop", "/shop"), ("GET catalog", "/catalog?exam=JEE")):
                    await call(label, "GET", path)
            # Solo sprint: deal 30 cards, then finish it.
            for _ in range(2):
                s = await call("POST sessions (30 cards)", "POST", "/sessions", {"exam": "JEE", "subject": "Physics", "count": 30, "request_id": uuid.uuid4().hex})
                results = [{"card_id": c["id"], "outcome": "correct", "choice": c["answer"], "ms": 3000} for c in s["cards"][:20]]
                await call("POST sessions/complete", "POST", f"/sessions/{s['id']}/complete", {"results": results})
                await call("GET sessions/{id}", "GET", f"/sessions/{s['id']}")
            # Practice Rival: open, seat the rival, answer every card.
            d = await call("POST duels (invite)", "POST", "/duels", {"exam": "JEE", "subject": "Physics", "picks": [{"subject": "Physics", "chapter": None}], "mode": "invite", "name": "TEST perf", "count": 30, "request_id": uuid.uuid4().hex})
            d = await call("POST duels/bot", "POST", f"/duels/{d['id']}/bot", {})
            await asyncio.sleep(max(0, d["start_at"] - d["server_now"]) + 0.2)
            for i in range(len(d["cards"])):
                await call("POST duels/answer", "POST", f"/duels/{d['id']}/answer", {"index": i, "choice": 0, "outcome": "answer", "ms": 1500})
            await call("GET duels/{id}", "GET", f"/duels/{d['id']}")
        finally:
            print(f"{'endpoint':28} {'n':>3} {'server p50':>10} {'server max':>10} {'wall p50':>9}  status")
            for label, v in rows.items():
                print(f"{label:28} {len(v):>3} {statistics.median(x[0] for x in v):>9.1f}ms {max(x[0] for x in v):>9.1f}ms {statistics.median(x[1] for x in v):>8.1f}ms  {sorted({x[2] for x in v})}")
            await client.close()


asyncio.run(main())
