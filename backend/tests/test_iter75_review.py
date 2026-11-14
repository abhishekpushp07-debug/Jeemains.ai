"""Iteration 75 (tester): independent checks for one-trip answers, ws_nodes, watcher limit, load counters and Cheer Squad buying.

Run:  cd /app/backend && RF_NODE_B=http://127.0.0.1:8002 python -m pytest tests/test_iter75_review.py -q -o addopts=
Uses only TEST-rv75-* identities (grants written into rf_access) and removes exactly what it made.
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
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", ".env"))
PUBLIC = (os.environ.get("EXPO_BACKEND_URL") or os.environ["EXPO_PUBLIC_BACKEND_URL"]).rstrip("/")
A = PUBLIC + "/api/rf"
LOCAL_A = "http://127.0.0.1:8001/api/rf"
B = os.environ.get("RF_NODE_B", "").rstrip("/")
B = B + "/api/rf" if B else ""
PREFIX = "TEST-rv75-"
needs_b = pytest.mark.skipif(not B, reason="RF_NODE_B not set")


@pytest.fixture(scope="module")
def db():
    d = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    yield d
    q = {"$regex": "^" + PREFIX}
    dids = [x["id"] for x in d.rf_duels.find({"players.uid": q}, {"id": 1})]
    d.rf_watch.delete_many({"did": {"$in": dids}})
    d.rf_duels.delete_many({"players.uid": q})
    for name in ("rf_profiles", "rf_awards", "rf_learning_events", "rf_access", "rf_friends", "rf_feed"):
        d[name].delete_many({"uid": q})
    d.rf_friends.delete_many({"fid": q})


def grant(db, n, profile=None):
    token, uid = secrets.token_urlsafe(32), f"{PREFIX}{n}-{secrets.token_hex(3)}"
    db.rf_access.insert_one({"digest": hashlib.sha256(token.encode()).hexdigest(), "uid": uid, "sid": "", "expires_at": datetime.now(timezone.utc) + timedelta(minutes=20)})
    if profile is not None:
        db.rf_profiles.insert_one({"uid": uid, "name": "TEST rv75", **profile})
    return token, uid


def h(token):
    return {"Authorization": "Bearer " + token}


async def rival_match(c):
    d = (await c.post("/duels", json={"exam": "JEE", "subject": "Physics", "picks": [{"subject": "Physics", "chapter": None}], "mode": "invite", "name": "RV", "request_id": secrets.token_hex(8)})).json()
    d = (await c.post(f"/duels/{d['id']}/bot", json={})).json()
    assert d["status"] == "ready" and len(d["cards"]) == 30
    return d


# --- Cheer Squads: shortfall text, atomic buy, guards ---
QA_LIKE = {"diamonds": {"red": 9, "blue": 4, "emerald": 1, "gold": 0}, "cups_won": 2}


def test_squad_shortfall_exact_text_and_no_charge(db):
    tok, uid = grant(db, "short", dict(QA_LIKE))
    royal = httpx.post(A + "/squads/buy", headers=h(tok), json={"id": "squad_royal"}, timeout=20)
    assert royal.status_code == 409 and "You need 2 more Blue, 1 more Emerald" in royal.json()["detail"], royal.text
    legend = httpx.post(A + "/squads/buy", headers=h(tok), json={"id": "squad_legend"}, timeout=20)
    assert legend.status_code == 409 and "You need 2 more Emerald, 2 more Gold" in legend.json()["detail"], legend.text
    assert db.rf_profiles.find_one({"uid": uid})["diamonds"] == QA_LIKE["diamonds"]


def test_squad_buy_success_deducts_and_equips(db):
    tok, uid = grant(db, "buy", dict(QA_LIKE))
    r = httpx.post(A + "/squads/buy", headers=h(tok), json={"id": "squad_gold"}, timeout=20)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["diamonds"] == {**body["diamonds"], "red": 1, "blue": 2, "emerald": 1, "gold": 0}
    assert body["equipped"] == "squad_gold"
    gold = next(i for i in body["items"] if i["id"] == "squad_gold")
    assert gold["bought"] and gold["unlocked"]
    g = httpx.get(A + "/squads", headers=h(tok), timeout=20).json()
    assert g["equipped"] == "squad_gold" and g["diamonds"]["red"] == 1
    p = db.rf_profiles.find_one({"uid": uid})
    assert p["diamonds_spent"] == {"red": 8, "blue": 2} and "squad_gold" in p["owned"]
    again = httpx.post(A + "/squads/buy", headers=h(tok), json={"id": "squad_gold"}, timeout=20)
    assert again.status_code == 409 and "already" in again.json()["detail"].lower()


def test_squad_not_for_sale_and_unknown(db):
    tok, _ = grant(db, "nfs", dict(QA_LIKE))
    for body in ({"id": "squad_rookie"}, {"id": "squad_nope"}, {}):
        r = httpx.post(A + "/squads/buy", headers=h(tok), json=body, timeout=20)
        assert r.status_code == 404, (body, r.status_code)
    assert httpx.post(A + "/squads/buy", json={"id": "squad_gold"}, timeout=20).status_code == 401


def test_squad_buy_without_profile_shows_full_price(db):
    tok, _ = grant(db, "noprof")
    r = httpx.post(A + "/squads/buy", headers=h(tok), json={"id": "squad_gold"}, timeout=20)
    assert r.status_code == 409 and "8 more Red, 2 more Blue" in r.json()["detail"], r.text


def test_squad_parallel_buys_charge_once(db):
    tok, uid = grant(db, "race", {"diamonds": {"red": 8, "blue": 2, "emerald": 0, "gold": 0}, "cups_won": 0})

    async def run():
        async with httpx.AsyncClient(base_url=A, headers=h(tok), timeout=30) as c:
            return await asyncio.gather(*[c.post("/squads/buy", json={"id": "squad_gold"}) for _ in range(6)])
    codes = sorted(r.status_code for r in asyncio.run(run()))
    assert codes == [200, 409, 409, 409, 409, 409], codes
    p = db.rf_profiles.find_one({"uid": uid})
    assert p["diamonds"]["red"] == 0 and p["diamonds"]["blue"] == 0


def test_squad_already_unlocked_by_cups_is_not_charged(db):
    """A squad opened by cup wins should not cost diamonds (UI hides the button, but the API is the guard)."""
    tok, uid = grant(db, "cups", {"diamonds": {"red": 9, "blue": 4, "emerald": 1, "gold": 0}, "cups_won": 3})
    r = httpx.post(A + "/squads/buy", headers=h(tok), json={"id": "squad_gold"}, timeout=20)
    after = db.rf_profiles.find_one({"uid": uid})["diamonds"]
    assert after["red"] == 9, f"status={r.status_code}: diamonds spent on a squad already opened by cups -> {after}"


# --- One-trip answers: validation, replays of skipped cards, counters ---
def test_answer_validation_and_counters(db):
    async def run():
        tok, uid = grant(db, "val")
        async with httpx.AsyncClient(base_url=LOCAL_A, headers=h(tok), timeout=30) as c:
            before = (await c.get("/../health/load")).json() if False else httpx.get("http://127.0.0.1:8001/api/health/load", timeout=10).json()
            d = await rival_match(c)
            await asyncio.sleep(max(0, d["start_at"] - d["server_now"]) + 0.2)
            for bad in ({"index": 30, "outcome": "answer", "choice": 1}, {"index": -1, "outcome": "answer", "choice": 1},
                        {"index": 0, "outcome": "answer", "choice": 5}, {"index": 0, "outcome": "cheat"}, {"index": 0, "outcome": "answer", "choice": 1, "score": 99}):
                assert (await c.post(f"/duels/{d['id']}/answer", json=bad)).status_code == 422, bad
            r0 = (await c.post(f"/duels/{d['id']}/answer", json={"index": 0, "outcome": "timed_out"})).json()
            assert r0["outcome"] == "timed_out" and r0["score"] == 0
            r1 = (await c.post(f"/duels/{d['id']}/answer", json={"index": 1, "outcome": "answer", "choice": 0})).json()
            r1b = (await c.post(f"/duels/{d['id']}/answer", json={"index": 1, "outcome": "answer", "choice": (r1["answer"] + 1) % 4})).json()
            assert r1b["outcome"] == r1["outcome"] and r1b["score"] == r1["score"]
            r0b = (await c.post(f"/duels/{d['id']}/answer", json={"index": 0, "outcome": "answer", "choice": r0["answer"]})).json()
            assert r0b["outcome"] == "timed_out" and r0b["score"] == r1["score"]  # replay of a timed-out card cannot score
            assert (await c.post(f"/duels/{d['id']}/answer", json={"index": 5, "outcome": "skipped"})).status_code == 409
            other, _ = grant(db, "intruder")
            assert (await c.post(f"/duels/{d['id']}/answer", headers=h(other), json={"index": 2, "outcome": "skipped"})).status_code in (403, 404)
            after = httpx.get("http://127.0.0.1:8001/api/health/load", timeout=10).json()
            assert after["answers_quick"] + after["answers_full"] >= before["answers_quick"] + before["answers_full"] + 4
            assert isinstance(after["answers_quick"], int) and after["answers_quick"] > before["answers_quick"]
            await c.post(f"/duels/{d['id']}/forfeit", json={})
            doc = db.rf_duels.find_one({"id": d["id"]})
            me = next(p for p in doc["players"] if p["uid"] == uid)
            assert [a["i"] for a in me["answers"]] == [0, 1] and sum(a["ms"] for a in me["answers"]) == me["ms"]
    asyncio.run(run())


# --- ws_nodes is written while a socket is open and removed after it closes ---
@needs_b
def test_ws_nodes_added_and_removed(db):
    async def run():
        tok, _ = grant(db, "nodes")
        async with httpx.AsyncClient(base_url=LOCAL_A, headers=h(tok), timeout=30) as c:
            d = await rival_match(c)
        ws = await websockets.connect(B.replace("http", "ws", 1) + f"/duels/{d['id']}/ws")
        await ws.send(json.dumps({"token": tok, "lite": 1}))
        first = json.loads(await asyncio.wait_for(ws.recv(), 5))
        assert len(first["cards"]) == 30
        nodes = db.rf_duels.find_one({"id": d["id"]}).get("ws_nodes") or []
        assert len(nodes) >= 1, nodes
        await ws.close()
        left = nodes
        for _ in range(12):
            await asyncio.sleep(0.5)
            left = db.rf_duels.find_one({"id": d["id"]}).get("ws_nodes") or []
            if not left:
                break
        assert left == [], left
    asyncio.run(run())


# --- 100-watcher limit counted across servers; spectators who stop looking drop out ---
@needs_b
def test_watch_limit_across_servers(db):
    async def run():
        (tp, up), (tf, uf), (tg, ug) = grant(db, "wp"), grant(db, "wf"), grant(db, "wg")
        for f in (uf, ug):
            db.rf_friends.insert_one({"uid": f, "fid": up, "ts": time.time()})
        async with httpx.AsyncClient(base_url=LOCAL_A, headers=h(tp), timeout=30) as p:
            d = await rival_match(p)
        async with httpx.AsyncClient(base_url=B, headers=h(tg), timeout=30) as g:
            assert (await g.get(f"/duels/{d['id']}/watch")).status_code == 200  # g holds a seat on server B
        now = time.time()
        db.rf_watch.insert_many([{"_id": f"{d['id']}:{PREFIX}ghost{i}", "did": d["id"], "ts": now, "at": datetime.now(timezone.utc)} for i in range(99)])
        async with httpx.AsyncClient(base_url=LOCAL_A, headers=h(tf), timeout=30) as f:
            full = await f.get(f"/duels/{d['id']}/watch")
            assert full.status_code == 409 and "100" in full.json()["detail"], full.text
        async with httpx.AsyncClient(base_url=B, headers=h(tg), timeout=30) as g:
            assert (await g.get(f"/duels/{d['id']}/watch")).status_code == 200  # an existing spectator keeps their seat
    asyncio.run(run())
