"""Iteration 65: Cup Night split (>16 joiners -> several cups), busy-player handling at the draw, and Badla filters (team / 3-player duels).
Throwaway TEST-i65-* players with hashed short-lived grants, removed afterwards. Today's Cup Night is only touched when no real player joined it."""
import asyncio
import hashlib
import os
import secrets
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, os.path.dirname(__file__))
from test_rf_phase3 import Api, BASE, _cleanup  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from cups import night_of  # noqa: E402
from social import make_pid, remember_identity  # noqa: E402


async def _users(db, tag, n):
    users = {}
    for k in range(n):
        uid = f"TEST-i65-{tag}-{k}"
        token = secrets.token_urlsafe(24)
        await db.rf_access.insert_one({"digest": hashlib.sha256(token.encode()).hexdigest(), "uid": uid, "sid": "", "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10)})
        await remember_identity(db, uid, {"name": f"TESTI65{k}", "phone": ""})
        users[k] = {"uid": uid, "pid": make_pid(uid), "h": {"Authorization": "Bearer " + token}}
    return users


def _run(body, n):
    async def main():
        db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
        users = await _users(db, uuid.uuid4().hex[:6], n)
        try:
            async with httpx.AsyncClient(base_url=BASE, timeout=60) as s:
                await body(db, Api(s), users)
        finally:
            await _cleanup(db, users)
    asyncio.run(main())


# Cup Night: 17 seated joiners are split evenly into 2 cups (9 + 8 -> sizes 16 and 8); a joiner who opened another cup is not seated
def test_cup_night_split():
    async def guard():
        db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
        n = await db.rf_cup_nights.find_one({"_id": night_of(time.time())[0]})
        return bool(n)
    if asyncio.run(guard()):
        pytest.skip("Tonight's Cup Night doc already exists; not touching it.")
    _run(_split, 18)


async def _split(db, api, u):
    day, _ = night_of(time.time())
    try:
        await db.rf_cup_nights.update_one({"_id": day}, {"$set": {"start_ts": time.time() + 1800, "status": "open"}, "$setOnInsert": {"uids": []}}, upsert=True)
        for k in range(18):
            r = await api.post("/cups/night/join", u[k])
            assert r.json()["joined"] is True
        # player 17 joined the night and then opened an Open Cup: is that allowed?
        r = await api.post("/cups", u[17], {"kind": "open", "picks": [{"subject": "Physics"}]})
        print("open cup after joining night:", r.status_code)
        busy_allowed = r.status_code == 200
        # in the last 15 minutes a seated joiner cannot start another cup
        await db.rf_cup_nights.update_one({"_id": day}, {"$set": {"start_ts": time.time() + 600}})
        r = await api.post("/cups", u[16], {"kind": "open", "picks": [{"subject": "Physics"}]})
        assert r.status_code == 409 and "Cup Night" in r.json()["detail"]
        await db.rf_cup_nights.update_one({"_id": day}, {"$set": {"start_ts": time.time() - 1}})
        n = (await api.get("/cups/night", u[0])).json()
        assert n["phase"] == "live" and n["count"] == (17 if busy_allowed else 18)  # after the draw: the seated number
        assert (await api.get("/cups/night", u[17])).json()["missed"] is busy_allowed
        sizes = sorted((c["size"], c["real_players"]) for c in n["cups"])
        print("cups:", sizes, [c["id"] for c in n["cups"]])
        expected_real = 17 if busy_allowed else 18
        assert sum(r for _, r in sizes) == expected_real
        assert len(n["cups"]) == 2 and all(r <= 16 for _, r in sizes)
        assert max(r for _, r in sizes) - min(r for _, r in sizes) <= 1  # evenly split
        assert [c["no"] for c in n["cups"]] == [1, 2] and all(c["id"] == f"night-{day}-{c['no']}" for c in n["cups"])
        for c in n["cups"]:
            assert c["size"] == (16 if c["real_players"] > 8 else 8 if c["real_players"] > 4 else 4)
        if busy_allowed:
            me = (await api.get("/cups/night", u[17])).json()
            print("busy joiner: joined flag", me["joined"], "my_cup", me["my_cup"], "(counted but not seated)")
        view = (await api.get(f"/cups/{n['cups'][1]['id']}", u[0])).json()  # not my cup but... check privacy
        print("other night cup view status:", view.get("status"), view.get("detail"))
    finally:
        await db.rf_cups.delete_many({"night": day, "players.uid": {"$in": [x["uid"] for x in u.values()]}})
        await db.rf_cup_nights.delete_one({"_id": day})
        await db.rf_night_seats.delete_many({"day": day})


# Badla: 3-player and team duels never count; a ghost (non-friend) is never listed
def test_badla_filters():
    _run(_badla_filters, 3)


async def _badla_filters(db, api, u):
    a, b, c = u[0], u[1], u[2]
    await api.befriend(a, b)
    base = {"exam": "JEE", "mode": "friend", "subject": "Physics", "chapter": None, "picks": [{"subject": "Physics", "chapter": None}], "status": "finished", "card_ids": []}
    await db.rf_duels.insert_one({**base, "id": "TEST-i65-" + uuid.uuid4().hex[:8], "players": [{"uid": a["uid"], "score": 1}, {"uid": b["uid"], "score": 5}, {"uid": c["uid"], "score": 2}], "winner": b["uid"], "finished_ts": time.time() - 30})
    await db.rf_duels.insert_one({**base, "id": "TEST-i65-" + uuid.uuid4().hex[:8], "team_mode": True, "players": [{"uid": a["uid"], "score": 1}, {"uid": b["uid"], "score": 5}], "winner": b["uid"], "finished_ts": time.time() - 20})
    assert (await api.get("/badla", a)).json()["items"] == []
    await db.rf_duels.insert_one({**base, "id": "TEST-i65-" + uuid.uuid4().hex[:8], "status": "live", "players": [{"uid": a["uid"], "score": 1}, {"uid": b["uid"], "score": 5}], "winner": b["uid"], "finished_ts": time.time() - 10})
    assert (await api.get("/badla", a)).json()["items"] == []  # unfinished: no badla
    await db.rf_duels.insert_one({**base, "id": "TEST-i65-" + uuid.uuid4().hex[:8], "players": [{"uid": a["uid"], "score": 1}, {"uid": b["uid"], "score": 5}], "winner": b["uid"], "finished_ts": time.time() - 5})
    got = (await api.get("/badla", a)).json()["items"]
    assert [(x["pid"], x["streak"], x["left"]) for x in got] == [(b["pid"], 1, 4)]
    assert (await api.s.get("/badla")).status_code == 401  # unauthenticated


if __name__ == "__main__":
    pytest.main([__file__, "-q", "-o", "addopts="])
