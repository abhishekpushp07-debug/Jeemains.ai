"""Iteration 68 (tester): Champions Wall edge cases — blocked champions hidden, doors window empty, after-start shows tonight, auth required.
Throwaway TEST-i65-* players (iteration 65 helper). Today's Cup Night doc is only inserted when none exists and is removed by exact id + start_ts."""
import asyncio
import os
import sys
import time
import uuid

import httpx
import pytest
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, os.path.dirname(__file__))
from test_iter65_cup_night_badla import BASE, _run  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from cups import DOORS_SECONDS, night_of  # noqa: E402


def _db():
    return AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]


def _no_night_doc():
    async def g():
        return not await _db().rf_cup_nights.find_one({"_id": night_of(time.time())[0]})
    return asyncio.run(g())


def _cup(cid, day, champ):
    return {"id": cid, "kind": "open", "label": "Physics", "night": day, "night_no": 97, "size": 4, "status": "finished", "champion": champ["uid"], "title_no": 1,
            "finished_ts": time.time(), "players": [champ, {"uid": "bot-TESTi68-x", "name": "Rival", "bot": True}]}


# Auth: the wall needs an RF bearer
def test_champions_requires_auth():
    r = httpx.get(BASE + "/cups/champions", timeout=20)
    assert r.status_code == 401


# A champion who blocked the viewer (or was blocked by them) is not on the viewer's wall; others still see them
def test_champions_blocked_hidden():
    _run(_blocked, 3)


async def _blocked(db, api, u):
    now = time.time()
    day, start = night_of(now)
    show = day if now >= start else night_of(now - 86400)[0] if now < start - DOORS_SECONDS else None
    if not show:
        pytest.skip("Doors are open: the wall is empty.")
    cid = f"night-TESTi68b-{uuid.uuid4().hex[:6]}"
    champ = {"uid": u[0]["uid"], "pid": u[0]["pid"], "name": "TESTI680", "bot": False}
    bids = []
    try:
        await db.rf_cups.insert_one(_cup(cid, show, champ))
        r = await db.rf_blocks.insert_one({"uid": u[1]["uid"], "bid": u[0]["uid"], "ts": now})
        bids.append(r.inserted_id)
        r = await db.rf_blocks.insert_one({"uid": u[0]["uid"], "bid": u[2]["uid"], "ts": now})
        bids.append(r.inserted_id)
        for k in (1, 2):  # blocker and blocked both lose the champion
            items = (await api.get("/cups/champions", u[k])).json()["items"]
            assert not any(c["cup_id"] == cid for c in items), f"viewer {k} still sees a blocked champion"
        mine = [c for c in (await api.get("/cups/champions", u[0])).json()["items"] if c["cup_id"] == cid]
        assert len(mine) == 1 and mine[0]["you"] is True
    finally:
        await db.rf_cups.delete_one({"id": cid})
        await db.rf_blocks.delete_many({"_id": {"$in": bids}})


# 7–8 pm (doors open): the wall is empty; once tonight starts it shows tonight's champions until the next doors
def test_champions_doors_then_tonight():
    if not _no_night_doc():
        pytest.skip("Tonight's Cup Night doc already exists; not touching it.")
    _run(_doors, 1)


async def _doors(db, api, u):
    day, _ = night_of(time.time())
    cid = f"night-TESTi68d-{uuid.uuid4().hex[:6]}"
    champ = {"uid": u[0]["uid"], "pid": u[0]["pid"], "name": "TESTI680", "bot": False}
    st = time.time() + 1800
    try:
        await db.rf_cups.insert_one(_cup(cid, day, champ))
        await db.rf_cup_nights.insert_one({"_id": day, "uids": [], "status": "open", "start_ts": st})
        w = (await api.get("/cups/champions", u[0])).json()
        assert w["day"] is None and w["items"] == [] and w["time_label"]
        _doors.shape = set(w)
    finally:
        await db.rf_cup_nights.delete_one({"_id": day, "start_ts": st})
    st = time.time() - 60  # empty, already started: nothing gets seated
    try:
        await db.rf_cup_nights.insert_one({"_id": day, "uids": [], "status": "open", "start_ts": st})
        w = (await api.get("/cups/champions", u[0])).json()
        assert w["day"] == day and w["tonight"] is True
        assert any(c["cup_id"] == cid and c["you"] for c in w["items"])
        assert w["until_ts"] > time.time() + 20 * 3600  # next night's doors
    finally:
        await db.rf_cup_nights.delete_one({"_id": day, "start_ts": st})
        await db.rf_cups.delete_one({"id": cid})


# Contract: the doors-window answer has the same keys as the others ({day, tonight, items, until_ts, time_label})
def test_champions_doors_shape():
    if not hasattr(_doors, "shape"):
        pytest.skip("doors test did not run")
    assert "tonight" in _doors.shape, f"doors branch keys: {sorted(_doors.shape)}"
