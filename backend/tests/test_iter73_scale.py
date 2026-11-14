"""Iteration 73: crowd scale. Load gate, live-engine lite frames, Cup Night seat documents, the lighter inbox.

Run:  cd /app/backend && python -m pytest tests/test_iter73_scale.py -q -o addopts=
Uses only TEST-scale-* accounts (grants written straight into rf_access) and removes everything it made.
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
BASE = os.environ.get("RF_TEST_BASE", "http://127.0.0.1:8001/api/rf")
PREFIX = "TEST-scale-"


@pytest.fixture(scope="module")
def db():
    d = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    yield d
    q = {"$regex": "^" + PREFIX}
    d.rf_duels.delete_many({"players.uid": q})
    for name, field in (("rf_profiles", "uid"), ("rf_awards", "uid"), ("rf_learning_events", "uid"), ("rf_access", "uid"), ("rf_night_seats", "uid"), ("rf_notices", "uid")):
        d[name].delete_many({field: q})


def grant(db, n):
    token, uid = secrets.token_urlsafe(32), f"{PREFIX}{n}-{secrets.token_hex(3)}"
    db.rf_access.insert_one({"digest": hashlib.sha256(token.encode()).hexdigest(), "uid": uid, "sid": "", "expires_at": datetime.now(timezone.utc) + timedelta(minutes=20)})
    return token, uid


def h(token):
    return {"Authorization": "Bearer " + token}


def test_health_load_numbers_only():
    r = httpx.get(BASE.replace("/api/rf", "/api/health/load"), timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert set(body) >= {"lag_ms", "inflight", "sockets", "busy", "open_files_limit"}
    assert body["open_files_limit"] > 1024  # the 1024 default capped a process at ~1000 players


def test_gate_answers_busy_with_retry_after():
    from fastapi import Depends, FastAPI
    from fastapi.testclient import TestClient
    import load_guard
    app = FastAPI()
    app.add_exception_handler(load_guard.ArenaBusy, load_guard.busy_response)

    @app.post("/new", dependencies=[Depends(load_guard.arena_gate)])
    def new():
        return {"ok": True}
    c = TestClient(app)
    assert c.post("/new").status_code == 200
    load_guard.load.sockets = load_guard.SOCKET_LIMIT + 1
    try:
        r = c.post("/new")
        assert r.status_code == 503 and r.json()["code"] == "arena_busy" and r.headers["retry-after"] == "5"
    finally:
        load_guard.load.sockets = 0
    assert c.post("/new").status_code == 200


def test_practice_rival_match_lite_and_full_frames(db):
    async def run():
        token, uid = grant(db, "lite")
        async with httpx.AsyncClient(base_url=BASE, headers=h(token), timeout=30) as c:
            d = (await c.post("/duels", json={"exam": "JEE", "subject": "Physics", "picks": [{"subject": "Physics", "chapter": None}], "mode": "invite", "name": "Scale", "request_id": secrets.token_hex(8)})).json()
            d = (await c.post(f"/duels/{d['id']}/bot", json={})).json()
            assert d["status"] == "ready" and len(d["cards"]) == 30
            lite = await websockets.connect(BASE.replace("http", "ws", 1) + f"/duels/{d['id']}/ws")
            full = await websockets.connect(BASE.replace("http", "ws", 1) + f"/duels/{d['id']}/ws")
            await lite.send(json.dumps({"token": token, "lite": 1}))
            await full.send(json.dumps({"token": token}))
            first_lite, first_full = json.loads(await lite.recv()), json.loads(await full.recv())
            assert len(first_lite["cards"]) == 30 and len(first_full["cards"]) == 30
            await asyncio.sleep(max(0, d["start_at"] - d["server_now"]) + 0.3)
            r = (await c.post(f"/duels/{d['id']}/answer", json={"index": 0, "choice": 0, "outcome": "answer", "ms": 900})).json()
            assert r["index"] == 0 and r["outcome"] in ("correct", "incorrect")
            nl = json.loads(await asyncio.wait_for(lite.recv(), 5))
            nf = json.loads(await asyncio.wait_for(full.recv(), 5))
            assert "cards" not in nl and nl["players"][0]["answered"] + nl["players"][1]["answered"] >= 1
            assert len(nf["cards"]) == 30  # installed older apps still get every card in every push
            # idempotent replay and order guard still hold
            again = (await c.post(f"/duels/{d['id']}/answer", json={"index": 0, "choice": 1, "outcome": "answer", "ms": 900})).json()
            assert again["outcome"] == r["outcome"]
            skip = await c.post(f"/duels/{d['id']}/answer", json={"index": 5, "choice": 1, "outcome": "answer", "ms": 900})
            assert skip.status_code == 409
            assert (await c.post(f"/duels/{d['id']}/forfeit", json={})).json()["ok"] is True
            end = None
            for _ in range(20):
                v = json.loads(await asyncio.wait_for(lite.recv(), 5))
                if v["status"] == "finished":
                    end = v
                    break
            assert end and len(end["cards"]) == 30 and "answer" in end["cards"][0]  # the reveal deck is sent once, with keys
            await lite.close()
            await full.close()
    asyncio.run(run())


def test_inbox_reads_and_marks_seen(db):
    token, uid = grant(db, "inbox")
    r = httpx.get(BASE + "/inbox", headers=h(token), timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert {"me", "room", "cup", "cups", "challenges", "notices"} <= set(body)
    assert db.rf_profiles.find_one({"uid": uid})["seen_ts"] > time.time() - 30
    seen = db.rf_profiles.find_one({"uid": uid})["seen_ts"]
    httpx.get(BASE + "/inbox", headers=h(token), timeout=15)
    assert db.rf_profiles.find_one({"uid": uid})["seen_ts"] == seen  # online is refreshed every 20 s, not on every poll


def test_cup_night_seat_documents(db):
    from cups import night_of
    day, start = night_of(time.time())
    if db.rf_cup_nights.find_one({"_id": day}) or not (start - 3600 <= time.time() < start):
        pytest.skip("Only runs during tonight's doors hour on a night nobody has joined yet.")
    token, uid = grant(db, "night")
    try:
        r = httpx.post(BASE + "/cups/night/join", headers=h(token), json={}, timeout=15).json()
        assert r["joined"] is True and r["count"] >= 1
        assert db.rf_night_seats.find_one({"_id": f"{day}:{uid}"})
        assert "uids" not in db.rf_cup_nights.find_one({"_id": day})
        r = httpx.post(BASE + "/cups/night/leave", headers=h(token), json={}, timeout=15).json()
        assert r["joined"] is False and not db.rf_night_seats.find_one({"_id": f"{day}:{uid}"})
    finally:
        db.rf_night_seats.delete_many({"day": day, "uid": uid})
        if not db.rf_night_seats.find_one({"day": day}):
            db.rf_cup_nights.delete_one({"_id": day})
