"""Rapid Fire Phase 4 backend: Badla pending (up to 4 losses in a row), first-crown celebration flag and the daily Cup Night.

Same throwaway TEST players as test_rf_phase3. Cup Night is tested on today's IST night only when no real player has
joined it yet; the test moves that night's start (the night keeps the start it was opened with) and removes it after.
"""
import asyncio
import os
import sys
import time
import uuid

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, os.path.dirname(__file__))
from test_rf_phase3 import _win, run  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from cups import night_of  # noqa: E402


async def _duel(db, a, b, winner, ago):
    """A finished 1 v 1 between a and b, `ago` seconds back; winner is a, b or 'tie'."""
    did = "TEST-p4-" + uuid.uuid4().hex[:10]
    w = winner if winner == "tie" else winner["uid"]
    await db.rf_duels.insert_one({"id": did, "exam": "JEE", "mode": "friend", "subject": "Physics", "chapter": None, "picks": [{"subject": "Physics", "chapter": None}],
                                  "status": "finished", "players": [{"uid": a["uid"], "score": 10}, {"uid": b["uid"], "score": 12}], "winner": w, "finished_ts": time.time() - ago, "card_ids": []})
    return did


def test_badla_pending():
    run(_badla)


async def _badla(db, api, u, tag):
    a, b, c = u["a"], u["b"], u["c"]
    assert (await api.get("/badla", a)).json() == {"items": [], "max": 5}  # no friends yet
    await api.befriend(a, b)
    # older win, then a tie (skipped) and 3 losses: Badla pending x3 against b, on the newest loss
    await _duel(db, a, b, a, 900)
    newest = None
    for k, w in enumerate([b, "tie", b, b]):
        did = await _duel(db, a, b, w, 800 - k * 100)
        newest = did if w is b else newest
    await _duel(db, a, c, c, 50)  # c is not a friend: never listed
    got = (await api.get("/badla", a)).json()
    assert got["max"] == 5 and [(x["pid"], x["streak"], x["left"], x["match_id"], x["label"]) for x in got["items"]] == [(b["pid"], 3, 2, newest, "Mixed Physics")]
    assert got["items"][0]["picks"] == [{"subject": "Physics", "chapter": None}] and "crown" in got["items"][0]
    assert (await api.get("/badla", b)).json()["items"] == []  # b won: b owes nothing
    # a 4th loss keeps it; the 5th in a row drops it
    await _duel(db, a, b, b, 300)
    assert (await api.get("/badla", a)).json()["items"][0]["streak"] == 4
    await _duel(db, a, b, b, 200)
    assert (await api.get("/badla", a)).json()["items"] == []
    await _duel(db, a, b, b, 150)  # still more losses: stays dropped until a wins one
    assert (await api.get("/badla", a)).json()["items"] == []
    # a wins one back, then loses again: a new Badla starts at 1
    await _duel(db, a, b, a, 100)
    assert (await api.get("/badla", a)).json()["items"] == []
    await _duel(db, a, b, b, 10)
    assert [x["streak"] for x in (await api.get("/badla", a)).json()["items"]] == [1]


def test_cup_night():
    async def guard():
        db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
        n = await db.rf_cup_nights.find_one({"_id": night_of(time.time())[0]})
        return n and any(not x.startswith("TEST") for x in n.get("uids", []))
    if asyncio.run(guard()):
        pytest.skip("Real players joined tonight's Cup Night; not touching it.")
    run(_night)


async def _night(db, api, u, tag):
    a, b, c, d = u["a"], u["b"], u["c"], u["d"]
    day, start = night_of(time.time())
    before = await db.rf_cup_nights.find_one({"_id": day})
    try:
        # doors open: 30 minutes to go
        await db.rf_cup_nights.update_one({"_id": day}, {"$set": {"start_ts": time.time() + 1800, "status": "open"}, "$setOnInsert": {"uids": []}}, upsert=True)
        n = (await api.get("/cups/night", a)).json()
        assert (n["day"], n["phase"], n["joined"], n["seats"], n["label"], n["cards"]) == (day, "doors", False, 16, "PCM Mixed", 15)
        assert n["doors_ts"] == n["start_ts"] - 3600 and n["time_label"].endswith(("am", "pm")) and n["cups"] == [] and n["my_cup"] is None
        for who in (a, b, c):
            assert (await api.post("/cups/night/join", who)).json()["joined"] is True
        await api.befriend(a, b)
        n = (await api.post("/cups/night/join", a)).json()  # twice is once
        assert n["count"] == 3 and [f["pid"] for f in n["friends"]] == [b["pid"]]
        assert (await api.post("/cups/night/leave", c)).json()["joined"] is False
        assert (await api.get("/cups/night", a)).json()["count"] == 2
        # doors not open yet: 2 hours to go
        await db.rf_cup_nights.update_one({"_id": day}, {"$set": {"start_ts": time.time() + 7200}})
        assert (await api.post("/cups/night/join", d)).status_code == 409
        assert (await api.get("/cups/night", d)).json()["phase"] == "soon"
        # 8 pm: a and b are drawn into one cup of 4 (two practice rivals) and round 1 starts
        await db.rf_cup_nights.update_one({"_id": day}, {"$set": {"start_ts": time.time() - 1}})
        n = (await api.get("/cups/night", a)).json()
        assert n["phase"] == "live" and n["status"] == "seated" and len(n["cups"]) == 1 and n["my_cup"] == n["cups"][0]["id"]
        cup = n["cups"][0]
        assert (cup["no"], cup["size"], cup["real_players"], cup["mine"], cup["status"]) == (1, 4, 2, True, "live") and len(cup["code"]) == 6
        assert (await api.post("/cups/night/join", d)).status_code == 409  # too late
        assert (await api.post("/cups/night/leave", a)).status_code == 409
        view = (await api.get(f"/cups/{cup['id']}", a)).json()
        assert view["night"] == day and view["night_no"] == 1 and view["status"] == "live" and view["my_duel"] and view["label"] == "PCM Mixed"
        assert (await api.get("/inbox", a)).json()["cup"] == cup["id"]
        other = (await api.get("/cups/night", c)).json()  # left before the start: can watch with the code
        assert other["my_cup"] is None and other["cups"][0]["mine"] is False
        assert (await api.post("/cups/watch", c, {"code": cup["code"]})).json()["spectating"] is True
        await _win(db, api, view["my_duel"], a)
        assert (await api.get("/cups/night", a)).json()["cups"][0]["status"] in ("live", "finished")
    finally:
        await db.rf_cups.delete_many({"night": day, "players.uid": {"$in": [x["uid"] for x in u.values()]}})
        if before and any(not x.startswith("TEST") for x in before.get("uids", [])):
            await db.rf_cup_nights.replace_one({"_id": day}, before)
        else:
            await db.rf_cup_nights.delete_one({"_id": day})


if __name__ == "__main__":
    pytest.main([__file__, "-q", "-o", "addopts="])
