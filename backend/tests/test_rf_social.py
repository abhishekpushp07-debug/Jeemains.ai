"""Rapid Fire 2.0 social layer: identity, friends, blocks, Match Rooms (1 friend / several / gang), gangs, 2-5 player matches and diamonds.

Uses TEST-prefixed throwaway players with grants written straight into rf_access (no canonical accounts touched)
and removes every document it created.
"""
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

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
from gamify import phoenix  # noqa: E402
from social import make_pid, remember_identity  # noqa: E402

BASE = "http://localhost:8001/api/rf"


def test_phoenix_streak_rules():
    assert phoenix(["correct"] * 2 + ["incorrect"]) == ({}, 2)
    assert phoenix(["correct"] * 5) == ({"red": 1, "blue": 1}, 5)
    assert phoenix(["correct"] * 20) == ({"red": 1, "blue": 1, "emerald": 1, "gold": 1, "kohinoor": 1}, 20)
    # a broken streak restarts at 0 and the same colour can be won again; skips and time-outs break it too
    assert phoenix(["correct"] * 3 + ["skipped"] + ["correct"] * 3 + ["timed_out"] + ["correct"] * 2) == ({"red": 2}, 3)


async def _setup(db, tag):
    users = {}
    for k, (name, phone) in {"a": ("TESTAsha", "9000000001"), "b": ("", "9000000002"), "c": ("TESTChirag", "9000000003"), "d": ("TESTDiya", "9000000004")}.items():
        uid = f"TEST-social-{tag}-{k}"
        token = secrets.token_urlsafe(24)
        await db.rf_access.insert_one({"digest": hashlib.sha256(token.encode()).hexdigest(), "uid": uid, "sid": "", "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10)})
        await remember_identity(db, uid, {"name": name, "phone": phone})
        users[k] = {"uid": uid, "pid": make_pid(uid), "h": {"Authorization": "Bearer " + token}}
    return users


async def _cleanup(db, users):
    uids = [u["uid"] for u in users.values()]
    await db.rf_access.delete_many({"uid": {"$in": uids}})
    await db.rf_profiles.delete_many({"uid": {"$in": uids}})
    await db.rf_friends.delete_many({"$or": [{"uid": {"$in": uids}}, {"fid": {"$in": uids}}]})
    await db.rf_blocks.delete_many({"$or": [{"uid": {"$in": uids}}, {"bid": {"$in": uids}}]})
    await db.rf_notices.delete_many({"uid": {"$in": uids}})
    await db.rf_challenges.delete_many({"from_uid": {"$in": uids}})
    await db.rf_gangs.delete_many({"members.by": {"$in": uids}})
    await db.rf_gang_reports.delete_many({"uid": {"$in": uids}})
    await db.rf_duels.delete_many({"players.uid": {"$in": uids}})
    await db.rf_awards.delete_many({"uid": {"$in": uids}})
    await db.rf_learning_events.delete_many({"uid": {"$in": uids}})


async def _befriend(s, who, other):
    """`who` enters `other`'s Friend Code: both become friends at once."""
    code = (await s.get("/friends/code", headers=other["h"])).json()["code"]
    return await s.post("/friends", json={"code": code}, headers=who["h"])


def test_rooms_flow():
    asyncio.run(_rooms())


async def _rooms():
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    users = await _setup(db, uuid.uuid4().hex[:6])
    a, b, c, d = users["a"], users["b"], users["c"], users["d"]
    try:
        async with httpx.AsyncClient(base_url=BASE, timeout=20) as s:
            post = lambda path, who, body=None: s.post(path, json=body or {}, headers=who["h"])  # noqa: E731
            get = lambda path, who: s.get(path, headers=who["h"])  # noqa: E731
            befriend = lambda who, other: _befriend(s, who, other)  # noqa: E731
            # identity: account name, else masked number; never the full number
            pa = (await get(f"/players/{a['pid']}", b)).json()
            pb = (await get(f"/players/{b['pid']}", a)).json()
            assert pa["name"] == "TESTAsha" and pa["is_me"] is False and set(pa["diamonds"]) == {"red", "blue", "emerald", "gold", "kohinoor"}
            assert pb["name"] == "••••••0002" and "9000000002" not in str(pb)
            assert (await s.get("/players/search", params={"q": "TESTAsh"}, headers=b["h"])).status_code == 404  # players are found only by Friend Code
            # a challenge needs a friend edge first
            assert (await post("/challenges", a, {"pids": [b["pid"]], "subject": "Physics"})).status_code == 403
            assert (await befriend(a, b)).json()["relation"]["friend"] is True
            inbox = (await get("/inbox", b)).json()
            assert [(n["kind"], n["from"]["pid"]) for n in inbox["notices"]] == [("friend_added", a["pid"])]
            assert (await befriend(b, a)).json()["relation"] == {"friend": True, "follows_you": True, "blocked": False}
            assert (await get("/inbox", b)).json()["notices"] == []
            friends = (await get("/friends", a)).json()["items"]
            assert friends[0]["pid"] == b["pid"] and friends[0]["online"] is True and friends[0]["follows_you"] is True

            # 1 v 1 room: sent -> seen (inbox) -> declined closes the room
            room = (await post("/challenges", a, {"pids": [b["pid"]], "subject": "Physics"})).json()
            assert room["status"] == "open" and room["single"] and room["is_host"] and room["expires_in"] > 170 and room["players"][0]["status"] == "sent"
            inbox = (await get("/inbox", b)).json()
            assert inbox["challenges"][0]["id"] == room["id"] and inbox["challenges"][0]["from"]["pid"] == a["pid"]
            assert (await get(f"/challenges/{room['id']}", a)).json()["players"][0]["status"] == "seen"
            assert (await get(f"/challenges/{room['id']}", d)).status_code == 404  # not invited
            assert (await post(f"/challenges/{room['id']}/decline", b)).json()["status"] == "declined"
            # accept starts at once: one duel, both seated, 9.5 s entry show, 15 s cards
            room = (await post("/challenges", a, {"pids": [b["pid"]], "subject": "Physics", "chapter": None})).json()
            acc = (await post(f"/challenges/{room['id']}/accept", b)).json()
            assert acc["status"] == "started" and acc["duel_id"]
            assert (await post(f"/challenges/{room['id']}/accept", b)).json()["duel_id"] == acc["duel_id"]
            duel = (await get(f"/duels/{acc['duel_id']}", a)).json()
            assert duel["status"] == "ready" and duel["mode"] == "friend" and len(duel["players"]) == 2 and duel["entry_seconds"] == 9.5 and duel["seconds_per_card"] == 15
            assert 9.5 <= duel["start_at"] - duel["server_now"] <= 10.6
            opp = next(p for p in duel["players"] if not p["you"])
            assert opp["pid"] == b["pid"] and opp["name"] == "••••••0002" and {"level", "wins", "rank"} <= set(opp)

            # several friends: host presses START once one has joined; a player can leave and come back
            for other in (c, d):
                await befriend(a, other)
            room = (await post("/challenges", a, {"pids": [b["pid"], c["pid"], d["pid"]], "subject": "Chemistry"})).json()
            assert not room["single"] and room["joined"] == 1 and not room["can_start"]
            assert (await post(f"/challenges/{room['id']}/start", a)).status_code == 409
            assert (await post(f"/challenges/{room['id']}/accept", b)).json()["joined"] == 2
            assert (await post(f"/challenges/{room['id']}/accept", c)).json()["joined"] == 3
            assert (await post(f"/challenges/{room['id']}/leave", c)).json()["my_status"] == "left"
            assert (await post(f"/challenges/{room['id']}/accept", c)).json()["status"] == "open"
            started = (await post(f"/challenges/{room['id']}/start", a)).json()
            assert started["status"] == "started"
            duel = (await get(f"/duels/{started['duel_id']}", c)).json()
            assert len(duel["players"]) == 3 and duel["entry_seconds"] == 13.0 and sorted(p["rank"] for p in duel["players"]) == [1, 2, 3]
            assert (await post(f"/challenges/{room['id']}/accept", d)).status_code == 409  # already started
            # everyone invited has answered and one joined: starts by itself
            room = (await post("/challenges", a, {"pids": [b["pid"], c["pid"]], "subject": "Physics"})).json()
            await post(f"/challenges/{room['id']}/accept", b)
            assert (await post(f"/challenges/{room['id']}/decline", c)).json()["status"] == "started"
            # one open challenge at a time: sending a new one closes the earlier room
            first = (await post("/challenges", a, {"pids": [b["pid"]], "subject": "Physics"})).json()
            await post("/challenges", a, {"pids": [c["pid"]], "subject": "Physics"})
            assert (await get(f"/challenges/{first['id']}", a)).json()["status"] == "cancelled"
            # rematch: the first press opens a room for everyone in that match, the second press takes the seat and starts
            await db.rf_duels.update_one({"id": acc["duel_id"]}, {"$set": {"status": "finished", "winner": "tie", "finished_ts": time.time()}})
            r1 = (await post("/challenges", a, {"subject": "Physics", "rematch_of": acc["duel_id"]})).json()
            assert r1["status"] == "open" and r1["single"] and [p["pid"] for p in r1["players"]] == [b["pid"]]
            r2 = (await post("/challenges", b, {"subject": "Physics", "rematch_of": acc["duel_id"]})).json()
            assert r2["id"] == r1["id"] and r2["status"] == "started" and r2["duel_id"] != acc["duel_id"]
            prof = (await get(f"/players/{b['pid']}", a)).json()
            assert set(prof["stats"]) == {"matches", "wins", "win_rate", "best_streak", "accuracy"} and "head_to_head" in prof
    finally:
        await _cleanup(db, users)


def test_gangs_and_blocks():
    asyncio.run(_gangs())


async def _gangs():
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    users = await _setup(db, uuid.uuid4().hex[:6])
    a, b, c, d = users["a"], users["b"], users["c"], users["d"]
    try:
        async with httpx.AsyncClient(base_url=BASE, timeout=20) as s:
            post = lambda path, who, body=None: s.post(path, json=body or {}, headers=who["h"])  # noqa: E731
            get = lambda path, who: s.get(path, headers=who["h"])  # noqa: E731
            await _befriend(s, a, b)
            await _befriend(s, a, c)
            await _befriend(s, b, d)
            # names: length and blocked words; emblem must be one of the 8
            assert (await post("/gangs", a, {"name": "x ", "emblem": "lion"})).status_code == 400
            assert (await post("/gangs", a, {"name": "Ch0d Squad", "emblem": "lion"})).status_code == 400
            assert (await post("/gangs", a, {"name": "Kota Warriors", "emblem": "cat"})).status_code == 400
            made = (await post("/gangs", a, {"name": "Kota Warriors", "emblem": "lion", "pids": [b["pid"], d["pid"]]})).json()
            gid = made["id"]
            assert made["added"] == 1 and made["skipped"] == ["Not in your friends"]  # d is not a's friend
            notice = (await get("/inbox", b)).json()["notices"][0]
            assert notice["kind"] == "gang_added" and notice["gang"] == {"id": gid, "name": "Kota Warriors", "emblem": "lion"}
            # any member adds their own friends; only the leader edits or removes
            assert (await post(f"/gangs/{gid}/members", b, {"pids": [d["pid"]]})).json()["added"] == 1
            assert (await s.patch(f"/gangs/{gid}", json={"name": "Nope"}, headers=b["h"])).status_code == 403
            assert (await s.patch(f"/gangs/{gid}", json={"emblem": "dragon"}, headers=a["h"])).status_code == 200
            detail = (await get(f"/gangs/{gid}", d)).json()
            assert detail["emblem"] == "dragon" and len(detail["members"]) == 3 and detail["members"][0]["you"] and not detail["is_leader"]
            assert (await get(f"/gangs/{gid}", c)).status_code == 404  # not a member
            assert (await get("/gangs", b)).json()["items"][0]["members"] == 3
            # gang challenge reaches every member, friends or not; a member who blocked the sender is skipped
            await post("/blocks", d, {"pid": a["pid"]})
            room = (await post("/challenges", a, {"gang_id": gid, "subject": "Mathematics"})).json()
            assert room["gang"]["name"] == "Kota Warriors" and [p["pid"] for p in room["players"]] == [b["pid"]] and not room["single"]
            assert (await get("/inbox", d)).json()["challenges"] == []
            banner = (await get("/inbox", b)).json()["challenges"][0]
            assert banner["gang"]["id"] == gid and banner["joined"] == 1 and banner["seats"] == 5
            started = (await post(f"/challenges/{room['id']}/accept", b)).json()
            assert started["status"] == "started"  # everyone who was invited has answered
            assert (await db.rf_duels.find_one({"id": started["duel_id"]}))["gang_id"] == gid
            # block also stops adds (the code looks unknown) and hides the blocker's profile
            assert (await _befriend(s, a, d)).status_code == 404
            assert (await get(f"/players/{d['pid']}", a)).status_code == 404
            assert (await post(f"/gangs/{gid}/report", b, {"reason": "test"})).status_code == 200
            # leader leaves: the longest-standing member takes over; the last one out closes the gang
            assert (await post(f"/gangs/{gid}/leave", a)).status_code == 200
            assert (await get(f"/gangs/{gid}", b)).json()["is_leader"] is True
            await post(f"/gangs/{gid}/leave", b)
            await post(f"/gangs/{gid}/leave", d)
            assert (await db.rf_gangs.find_one({"id": gid}))["closed"] is True
            # public link pages: no login, no phone number
            page = await s.get(f"/c/{room['id']}")
            assert page.status_code == 200 and "://rapid/room/" + room["id"] in page.text and "9000000001" not in page.text
            assert (await s.get(f"/invite/{a['pid']}")).status_code == 404  # friends are made with a Friend Code, not a public link
            assert (await s.get("/friends")).status_code == 401
    finally:
        await _cleanup(db, users)


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
