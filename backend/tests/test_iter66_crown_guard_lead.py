"""Iteration 66: crown on every cup win (title_no / first_title / my_crown), Cup Night night_guard on create + join,
night-only 30 s round-1 lead-in. Throwaway TEST-i65-* players (same helpers as iteration 65) removed afterwards."""
import asyncio
import os
import sys
import time

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, os.path.dirname(__file__))
from test_rf_phase3 import _win  # noqa: E402
from test_iter65_cup_night_badla import _run  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from cups import night_of  # noqa: E402

PICKS = [{"subject": "Physics"}]


async def _play_to_end(db, api, cid, me, others=()):
    """`me` wins every match; any other human forfeits theirs."""
    for _ in range(8):
        cup = (await api.get(f"/cups/{cid}", me)).json()
        if cup["status"] != "live":
            break
        if cup["my_duel"]:
            d = await db.rf_duels.find_one({"id": cup["my_duel"]})
            await db.rf_duels.update_one({"id": d["id"]}, {"$set": {"start_at": min(d["start_at"], time.time() - 1)}})
            await _win(db, api, cup["my_duel"], me)
        for o in others:
            v = (await api.get(f"/cups/{cid}", o)).json()
            if v["status"] == "live" and v["my_duel"]:
                await api.post(f"/duels/{v['my_duel']}/forfeit", o)
    return (await api.get(f"/cups/{cid}", me)).json()


async def _cleanup_cups(db, cids):
    for cid in cids:
        c = await db.rf_cups.find_one({"id": cid})
        dids = [m["duel_id"] for rd in (c or {}).get("rounds") or [] for m in rd if m.get("duel_id")]
        await db.rf_duels.delete_many({"id": {"$in": dids}})
        await db.rf_cups.delete_one({"id": cid})
        await db.rf_feed.delete_many({"id": "cup:" + cid})


# Crown on every win: 1st win -> title_no 1 (first_title), 2nd win -> title_no 2, my_crown counts both; loser gets 0 / None
def test_second_crown():
    _run(_second_crown, 2)


async def _second_crown(db, api, u):
    a, b = u[0], u[1]
    cids = []
    try:
        # cup 1: a + b real players, a wins -> gold first crown
        c1 = (await api.post("/cups", a, {"kind": "open", "picks": PICKS})).json()
        cids.append(c1["id"])
        assert (await api.post("/cups", b, {"kind": "open", "picks": PICKS})).json()["id"] == c1["id"]
        await db.rf_cups.update_one({"id": c1["id"]}, {"$set": {"expires_ts": time.time() - 1}})
        v1 = await _play_to_end(db, api, c1["id"], a, [b])
        assert v1["status"] == "finished" and v1["players"][v1["champion"]]["you"]
        assert (v1["title_no"], v1["first_title"], v1["my_crown"]) == (1, True, {"won": 1, "real": 1})
        # cup 2: a alone with practice rivals -> CROWN #2, real stays 1
        c2 = (await api.post("/cups", a, {"kind": "open", "picks": PICKS})).json()
        assert c2["id"] != c1["id"]
        cids.append(c2["id"])
        await db.rf_cups.update_one({"id": c2["id"]}, {"$set": {"expires_ts": time.time() - 1}})
        v2 = await _play_to_end(db, api, c2["id"], a)
        assert v2["status"] == "finished" and v2["players"][v2["champion"]]["you"]
        assert (v2["title_no"], v2["first_title"], v2["real_players"]) == (2, False, 1)
        assert v2["my_crown"] == {"won": 2, "real": 1}
        # the first cup keeps its own number
        again = (await api.get(f"/cups/{c1['id']}", a)).json()
        assert again["title_no"] == 1 and again["first_title"] is True and again["my_crown"] == {"won": 2, "real": 1}
        lost = (await api.get(f"/cups/{c1['id']}", b)).json()
        assert (lost["title_no"], lost["first_title"], lost["my_crown"]) == (0, False, None)
    finally:
        await _cleanup_cups(db, cids)


def _tonight_free():
    async def chk():
        db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
        return not await db.rf_cup_nights.find_one({"_id": night_of(time.time())[0]})
    return asyncio.run(chk())


# night_guard: >15 min before start a joiner may create / join cups; in the last 15 min both give 409 mentioning Cup Night
def test_night_guard_create_and_join():
    if not _tonight_free():
        pytest.skip("Tonight's Cup Night doc already exists; not touching it.")
    _run(_guard, 3)


async def _guard(db, api, u):
    day, _ = night_of(time.time())
    a, b, c = u[0], u[1], u[2]
    cids = []
    try:
        await db.rf_cup_nights.update_one({"_id": day}, {"$set": {"start_ts": time.time() + 1800, "status": "open"}, "$setOnInsert": {"uids": []}}, upsert=True)
        assert (await api.post("/cups/night/join", a)).json()["joined"] is True
        # 30 min before: allowed
        r = await api.post("/cups", a, {"kind": "open", "picks": PICKS})
        assert r.status_code == 200, r.text
        cids.append(r.json()["id"])
        assert (await api.post(f"/cups/{r.json()['id']}/leave", a)).status_code == 200
        # b hosts an open cup; inside the window a cannot create or join
        host = (await api.post("/cups", b, {"kind": "open", "picks": [{"subject": "Chemistry"}]})).json()
        cids.append(host["id"])
        await db.rf_cup_nights.update_one({"_id": day}, {"$set": {"start_ts": time.time() + 600}})
        r = await api.post("/cups", a, {"kind": "open", "picks": [{"subject": "Mathematics"}]})
        assert r.status_code == 409 and "Cup Night" in r.json()["detail"], r.text
        r = await api.post(f"/cups/{host['id']}/join", a)
        assert r.status_code == 409 and "Cup Night" in r.json()["detail"], r.text
        # a non-joiner is never guarded
        r = await api.post(f"/cups/{host['id']}/join", c)
        assert r.status_code == 200, r.text
        # 16 min before: allowed again
        await db.rf_cup_nights.update_one({"_id": day}, {"$set": {"start_ts": time.time() + 960}})
        r = await api.post(f"/cups/{host['id']}/join", a)
        assert r.status_code == 200, r.text
    finally:
        await _cleanup_cups(db, cids)
        await db.rf_cups.delete_many({"night": day, "players.uid": {"$in": [x["uid"] for x in u.values()]}})
        await db.rf_cup_nights.delete_one({"_id": day})
        await db.rf_night_seats.delete_many({"day": day})


# lead-in: night round-1 duel starts ~30 s + show later than a normal cup's round-1 duel
def test_night_lead_in():
    if not _tonight_free():
        pytest.skip("Tonight's Cup Night doc already exists; not touching it.")
    _run(_lead, 3)


async def _lead(db, api, u):
    day, _ = night_of(time.time())
    cids = []
    try:
        # normal open cup
        n1 = (await api.post("/cups", u[2], {"kind": "open", "picks": PICKS})).json()
        cids.append(n1["id"])
        await db.rf_cups.update_one({"id": n1["id"]}, {"$set": {"expires_ts": time.time() - 1}})
        t0 = time.time()
        v = (await api.get(f"/cups/{n1['id']}", u[2])).json()
        normal = (await db.rf_duels.find_one({"id": v["my_duel"]}))["start_at"] - t0
        # night cup with 2 joiners
        await db.rf_cup_nights.update_one({"_id": day}, {"$set": {"start_ts": time.time() + 1800, "status": "open"}, "$setOnInsert": {"uids": []}}, upsert=True)
        for k in (0, 1):
            assert (await api.post("/cups/night/join", u[k])).json()["joined"] is True
        await db.rf_cup_nights.update_one({"_id": day}, {"$set": {"start_ts": time.time() - 1}})
        t1 = time.time()
        n = (await api.get("/cups/night", u[0])).json()
        assert n["phase"] == "live" and n["count"] == 2 and n["missed"] is False, n
        cid = n["my_cup"] if isinstance(n["my_cup"], str) else (n["my_cup"] or {}).get("id") or n["cups"][0]["id"]
        v = (await api.get(f"/cups/{cid}", u[0])).json()
        night = (await db.rf_duels.find_one({"id": v["my_duel"]}))["start_at"] - t1
        print(f"normal round-1 lead {normal:.1f}s, night round-1 lead {night:.1f}s")
        assert 25 <= night - normal <= 32, (normal, night)
        assert normal < 15
    finally:
        await _cleanup_cups(db, cids)
        await db.rf_cups.delete_many({"night": day, "players.uid": {"$in": [x["uid"] for x in u.values()]}})
        await db.rf_cup_nights.delete_one({"_id": day})
        await db.rf_night_seats.delete_many({"day": day})
