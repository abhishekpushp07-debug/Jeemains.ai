"""Iteration 74: many servers, one arena. Answers in one round trip, pushes across servers, spectators counted everywhere.

Run:  cd /app/backend && python -m pytest tests/test_iter74_multiserver.py -q -o addopts=
Cross-server tests need a second backend (several worker processes) on RF_NODE_B, e.g.
      uvicorn server:app --port 8002 --workers 3   then   RF_NODE_B=http://127.0.0.1:8002 pytest ...
Uses only TEST-ms74-* accounts (grants written straight into rf_access) and removes everything it made.
"""
import asyncio
import hashlib
import json
import os
import secrets
import time
from datetime import datetime, timedelta, timezone

import httpx
import pytest
import websockets
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
A = os.environ.get("RF_NODE_A", "http://127.0.0.1:8001").rstrip("/") + "/api/rf"
B = os.environ.get("RF_NODE_B", "").rstrip("/")
B = B + "/api/rf" if B else ""
PREFIX = "TEST-ms74-"
needs_b = pytest.mark.skipif(not B, reason="RF_NODE_B not set")


@pytest.fixture(scope="module")
def db():
    d = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    yield d
    q = {"$regex": "^" + PREFIX}
    dids = [x["id"] for x in d.rf_duels.find({"players.uid": q}, {"id": 1})]
    d.rf_watch.delete_many({"did": {"$in": dids}})
    d.rf_duels.delete_many({"players.uid": q})
    for name, field in (("rf_profiles", "uid"), ("rf_awards", "uid"), ("rf_learning_events", "uid"), ("rf_access", "uid"), ("rf_friends", "uid"), ("rf_feed", "uid")):
        d[name].delete_many({field: q})
    d.rf_friends.delete_many({"fid": q})


def grant(db, n):
    token, uid = secrets.token_urlsafe(32), f"{PREFIX}{n}-{secrets.token_hex(3)}"
    db.rf_access.insert_one({"digest": hashlib.sha256(token.encode()).hexdigest(), "uid": uid, "sid": "", "expires_at": datetime.now(timezone.utc) + timedelta(minutes=20)})
    return token, uid


def h(token):
    return {"Authorization": "Bearer " + token}


async def rival_match(c):
    d = (await c.post("/duels", json={"exam": "JEE", "subject": "Physics", "picks": [{"subject": "Physics", "chapter": None}], "mode": "invite", "name": "MS", "request_id": secrets.token_hex(8)})).json()
    d = (await c.post(f"/duels/{d['id']}/bot", json={})).json()
    assert d["status"] == "ready" and len(d["cards"]) == 30
    return d


def test_one_trip_answers_keep_every_rule(db):
    """First answer takes the full path, the rest the one-trip path: same scores, server-measured time, same guards."""
    async def run():
        token, uid = grant(db, "rules")
        async with httpx.AsyncClient(base_url=A, headers=h(token), timeout=30) as c:
            d = await rival_match(c)
            early = await c.post(f"/duels/{d['id']}/answer", json={"index": 0, "choice": 0, "outcome": "answer", "ms": 500})
            assert early.status_code == 409  # before card 1 opens
            await asyncio.sleep(max(0, d["start_at"] - d["server_now"]) + 0.2)
            score, got = 0, []
            for k in range(6):
                await asyncio.sleep(0.35)
                body = {"index": k, "choice": k % 4, "outcome": "answer", "ms": 900} if k != 3 else {"index": k, "outcome": "skipped", "ms": 0}
                r = (await c.post(f"/duels/{d['id']}/answer", json=body)).json()
                score += r["outcome"] == "correct"
                assert r["index"] == k and r["score"] == score and "answer" in r
                got.append(r["outcome"])
            assert got[3] == "skipped"
            again = (await c.post(f"/duels/{d['id']}/answer", json={"index": 2, "choice": 3, "outcome": "answer", "ms": 900})).json()
            assert again["outcome"] == got[2] and again["score"] == score  # a replay is never re-scored
            assert (await c.post(f"/duels/{d['id']}/answer", json={"index": 9, "choice": 1, "outcome": "answer", "ms": 900})).status_code == 409
            doc = db.rf_duels.find_one({"id": d["id"]})
            me = next(p for p in doc["players"] if p["uid"] == uid)
            assert [a["i"] for a in me["answers"]] == list(range(6)) and me["score"] == score
            assert all(isinstance(a["ms"], int) and 0 <= a["ms"] <= 16000 for a in me["answers"])
            assert sum(a["ms"] for a in me["answers"]) == me["ms"] and me["answers"][1]["ms"] >= 300  # measured by the server
            assert [a["outcome"] for a in me["answers"]] == got and me["answers"][3]["choice"] is None
            assert (await c.post(f"/duels/{d['id']}/forfeit", json={})).json()["ok"] is True
            assert (await c.post(f"/duels/{d['id']}/answer", json={"index": 6, "choice": 1, "outcome": "answer", "ms": 900})).status_code == 409
    asyncio.run(run())


@needs_b
def test_push_crosses_servers(db):
    """Answers go to server A, the live socket sits on server B (several workers): every answer still reaches the phone."""
    async def run():
        token, uid = grant(db, "cross")
        async with httpx.AsyncClient(base_url=A, headers=h(token), timeout=30) as a, httpx.AsyncClient(base_url=B, headers=h(token), timeout=30) as b:
            d = await rival_match(a)
            ws = await websockets.connect(B.replace("http", "ws", 1) + f"/duels/{d['id']}/ws")
            await ws.send(json.dumps({"token": token, "lite": 1}))
            first = json.loads(await asyncio.wait_for(ws.recv(), 5))
            assert len(first["cards"]) == 30
            await asyncio.sleep(max(0, d["start_at"] - d["server_now"]) + 0.2)
            lat = []
            for k in range(5):
                client = a if k % 2 == 0 else b  # answers land on either side
                t = time.perf_counter()
                await client.post(f"/duels/{d['id']}/answer", json={"index": k, "choice": 1, "outcome": "answer", "ms": 900})
                while True:
                    v = json.loads(await asyncio.wait_for(ws.recv(), 5))
                    mine = next(p for p in v["players"] if p["you"])
                    if mine["answered"] >= k + 1:
                        lat.append(time.perf_counter() - t)
                        assert "cards" not in v
                        break
            assert max(lat) < 1.0, lat
            await a.post(f"/duels/{d['id']}/forfeit", json={})
            end = None
            for _ in range(30):
                v = json.loads(await asyncio.wait_for(ws.recv(), 5))
                if v["status"] == "finished":
                    end = v
                    break
            assert end and len(end["cards"]) == 30
            await ws.close()
    asyncio.run(run())


@needs_b
def test_spectators_counted_on_every_server(db):
    """Two friends watch from different servers: the player's screen shows both."""
    async def run():
        (tp, up), (tf1, uf1), (tf2, uf2) = grant(db, "p"), grant(db, "f1"), grant(db, "f2")
        for f in (uf1, uf2):
            db.rf_friends.insert_one({"uid": f, "fid": up, "ts": time.time()})
        async with httpx.AsyncClient(base_url=A, headers=h(tp), timeout=30) as p:
            d = await rival_match(p)
        async with httpx.AsyncClient(base_url=A, headers=h(tf1), timeout=30) as f1, httpx.AsyncClient(base_url=B, headers=h(tf2), timeout=30) as f2:
            assert (await f1.get(f"/duels/{d['id']}/watch")).status_code == 200
            w = await f2.get(f"/duels/{d['id']}/watch")
            assert w.status_code == 200 and w.json()["watchers"] == 2
        for base in (A, B):
            async with httpx.AsyncClient(base_url=base, headers=h(tp), timeout=30) as p:
                n = 0
                for _ in range(8):  # each server learns within a couple of seconds
                    n = (await p.get(f"/duels/{d['id']}")).json()["watchers"]
                    if n == 2:
                        break
                    await asyncio.sleep(0.5)
                assert n == 2, base
    asyncio.run(run())


def test_inbox_tells_the_phone_how_often_to_look(db):
    token, _ = grant(db, "inbox")
    body = httpx.get(A + "/inbox", headers=h(token), timeout=15).json()
    assert body["poll_s"] in (8, 20)
