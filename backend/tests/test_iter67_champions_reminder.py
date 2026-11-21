"""Iteration 67: Champions Wall (/cups/champions) and the 7:55 pm Cup Night reminder in the inbox.
Throwaway TEST-i65-* players (same helper as iteration 65); today's Cup Night doc is only touched when nobody real joined it."""
import asyncio
import os
import sys
import time
import uuid

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, os.path.dirname(__file__))
from test_iter65_cup_night_badla import _run  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from cups import DOORS_SECONDS, night_of  # noqa: E402


def _wall_day(now):
    day, start = night_of(now)
    if now >= start:
        return day
    return night_of(now - 86400)[0] if now < start - DOORS_SECONDS else None


def _db():
    return AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]


# The wall lists real champions of the shown night (a cup a practice rival won is left out), with pid, crown and title number
def test_champions_wall():
    _run(_wall, 2)


async def _wall(db, api, u):
    show = _wall_day(time.time())
    if not show:
        pytest.skip("Doors are open: the wall is empty until tonight's champions are crowned.")
    tag = uuid.uuid4().hex[:6]
    real, bot = f"night-TESTi67-{tag}-1", f"night-TESTi67-{tag}-2"
    me = {"uid": u[0]["uid"], "pid": u[0]["pid"], "name": "TESTI650", "bot": False}
    try:
        await db.rf_cups.insert_many([
            {"id": real, "kind": "open", "night": show, "night_no": 98, "size": 4, "status": "finished", "champion": me["uid"], "title_no": 3, "finished_ts": time.time(),
             "players": [me, {"uid": "bot-TESTi67-a", "name": "Rival", "bot": True}]},
            {"id": bot, "kind": "open", "night": show, "night_no": 99, "size": 4, "status": "finished", "champion": "bot-TESTi67-b", "finished_ts": time.time(),
             "players": [{"uid": "bot-TESTi67-b", "name": "Rival", "bot": True}, {**me}]},
        ])
        await db.rf_profiles.update_one({"uid": me["uid"]}, {"$set": {"cups_won": 3, "cups_real": 1}})
        w = (await api.get("/cups/champions", u[1])).json()
        assert w["day"] == show and w["tonight"] is (show == night_of(time.time())[0]) and w["time_label"]
        mine = [c for c in w["items"] if c["cup_id"] == real]
        assert len(mine) == 1 and not any(c["cup_id"] == bot for c in w["items"])
        c = mine[0]
        assert c["pid"] == me["pid"] and c["no"] == 98 and c["size"] == 4 and c["real_players"] == 1 and c["title_no"] == 3 and c["you"] is False
        assert c["crown"] == {"won": 3, "real": 1}
        assert any(x["cup_id"] == real and x["you"] for x in (await api.get("/cups/champions", u[0])).json()["items"])
    finally:
        await db.rf_cups.delete_many({"id": {"$in": [real, bot]}})


# 7:55 pm: every seat holder gets one cup_night notice with the countdown; leaving Cup Night clears it; expired notices never show
def test_cup_night_reminder():
    async def guard():
        return bool(await _db().rf_cup_nights.find_one({"_id": night_of(time.time())[0]}))
    if asyncio.run(guard()):
        pytest.skip("Tonight's Cup Night doc already exists; not touching it.")
    _run(_remind, 2)


async def _remind(db, api, u):
    day, _ = night_of(time.time())
    start = time.time() + 200
    try:
        await db.rf_notices.insert_one({"id": str(uuid.uuid4()), "uid": u[1]["uid"], "from_uid": u[1]["uid"], "kind": "cup_night", "ts": time.time() - 900, "done": False,
                                        "expires_ts": time.time() - 60, "night": {"day": day, "start_ts": time.time() - 180, "time_label": "8:00 pm"}})
        # the seat first: the server's loop reminds whoever holds a seat the moment it sees tonight's document
        await db.rf_night_seats.insert_one({"_id": f"{day}:{u[0]['uid']}", "day": day, "uid": u[0]["uid"], "ts": time.time()})
        await db.rf_cup_nights.insert_one({"_id": day, "status": "open", "start_ts": start})
        note = None
        for _ in range(16):  # the server's night loop ticks every 3 s
            got = [n for n in (await api.get("/inbox", u[0])).json()["notices"] if n["kind"] == "cup_night"]
            if got:
                note = got[0]
                break
            await asyncio.sleep(1)
        assert note, "no cup_night reminder within 16 s"
        assert note["night"]["day"] == day and 150 < note["night"]["starts_in"] <= 200 and note["night"]["time_label"]
        assert (await db.rf_cup_nights.find_one({"_id": day}))["reminded"] is True
        assert await db.rf_notices.count_documents({"uid": u[0]["uid"], "kind": "cup_night"}) == 1  # once per night
        assert not [n for n in (await api.get("/inbox", u[1])).json()["notices"] if n["kind"] == "cup_night"]  # expired one is hidden
        r = await api.post("/cups/night/leave", u[0], {})
        assert r.status_code == 200
        assert not [n for n in (await api.get("/inbox", u[0])).json()["notices"] if n["kind"] == "cup_night"]
    finally:
        await db.rf_cup_nights.delete_one({"_id": day, "start_ts": start})
        await db.rf_night_seats.delete_many({"day": day, "uid": {"$in": [u[0]["uid"], u[1]["uid"]]}})
        await db.rf_notices.delete_many({"uid": {"$in": [u[0]["uid"], u[1]["uid"]]}, "kind": "cup_night"})
