"""WhatsApp match links: a link room seats anyone with the link (up to 4 + host), each joiner becomes the host's friend at once,
blocked players can't see it, the 3-minute room starts on START / full / timer, and the public link page offers app, browser and download.

Uses TEST-prefixed throwaway players with grants written straight into rf_access and removes every document it created.
"""
import asyncio
import hashlib
import os
import secrets
import sys
import uuid
from datetime import datetime, timedelta, timezone

import httpx
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
from social import make_pid, remember_identity  # noqa: E402

BASE = "http://localhost:8001/api/rf"


async def _setup(db, tag):
    users = {}
    for i, k in enumerate("abcdefg"):
        uid = f"TEST-link-{tag}-{k}"
        token = secrets.token_urlsafe(24)
        await db.rf_access.insert_one({"digest": hashlib.sha256(token.encode()).hexdigest(), "uid": uid, "sid": "", "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10)})
        await remember_identity(db, uid, {"name": f"TESTLink{k.upper()}", "phone": f"90000001{i:02d}"})
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
    await db.rf_duels.delete_many({"players.uid": {"$in": uids}})


def test_match_link_flow():
    asyncio.run(_flow())


async def _flow():
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    users = await _setup(db, uuid.uuid4().hex[:6])
    a, b, c, d, e, f, g = (users[k] for k in "abcdefg")
    try:
        async with httpx.AsyncClient(base_url=BASE, timeout=20) as s:
            post = lambda path, who, body=None: s.post(path, json=body or {}, headers=who["h"])  # noqa: E731
            get = lambda path, who: s.get(path, headers=who["h"])  # noqa: E731
            is_friend = lambda x, y: db.rf_friends.find_one({"uid": x["uid"], "fid": y["uid"]})  # noqa: E731

            # a link room needs nobody invited; it is not a 1 v 1 and has 5 seats
            room = (await post("/challenges", a, {"link": True, "subject": "Physics"})).json()
            cid = room["id"]
            assert room["link"] is True and room["single"] is False and room["players"] == [] and room["seats"] == 5 and room["expires_in"] > 170
            assert (await post("/challenges", a, {"subject": "Physics"})).status_code == 400  # without link, still needs someone

            # public page: app, browser and download, no login
            page = (await s.get(f"/c/{cid}")).text
            assert 'data-testid="rf-link-browser"' in page and f"/api/arena/rapid/room/{cid}" in page and f"frontend://rapid/room/{cid}" in page
            assert "become friends" in page and "4 of 4 seats open" in page and 'property="og:title"' in page

            # a stranger with the link sees the room, is not a friend yet
            seen = (await get(f"/challenges/{cid}", b)).json()
            assert seen["my_status"] == "link" and seen["friend"] is False and not seen["is_host"]
            # blocked players can't see or join it
            await post("/blocks", g, {"pid": a["pid"]})
            assert (await get(f"/challenges/{cid}", g)).status_code == 404
            assert (await post(f"/challenges/{cid}/accept", g)).status_code == 404
            # the host can't take a guest seat
            assert (await post(f"/challenges/{cid}/accept", a)).status_code == 403

            # taking a seat makes both friends at once; the host gets a "friend added" notice; the room stays open
            joined = (await post(f"/challenges/{cid}/accept", b)).json()
            assert joined["my_status"] == "joined" and joined["friend"] is True and joined["status"] == "open" and joined["joined"] == 2
            assert await is_friend(a, b) and await is_friend(b, a)
            notes = (await get("/inbox", a)).json()["notices"]
            assert ("friend_added", b["pid"], "link") in [(n["kind"], n["from"]["pid"], n["via"]) for n in notes]
            assert (await post(f"/challenges/{cid}/accept", b)).json()["joined"] == 2  # tapping again keeps one seat
            host = (await get(f"/challenges/{cid}", a)).json()
            assert host["can_start"] and host["friend"] is None and [p["pid"] for p in host["players"]] == [b["pid"]]

            # leave and come back through the link: still one seat, still friends
            assert (await post(f"/challenges/{cid}/leave", b)).json()["joined"] == 1
            assert (await post(f"/challenges/{cid}/accept", b)).json()["joined"] == 2

            # four guests fill the room and it starts by itself; a fifth is too late
            for other in (c, d, e):
                last = (await post(f"/challenges/{cid}/accept", other)).json()
            assert last["status"] == "started" and last["duel_id"]
            for other in (c, d, e):
                assert await is_friend(a, other) and await is_friend(other, a)
            assert not await is_friend(b, c)  # guests become friends with the host, not with each other
            late = await post(f"/challenges/{cid}/accept", f)
            assert late.status_code == 409
            assert (await get(f"/challenges/{cid}", f)).json()["status"] == "started"
            assert not await is_friend(a, f)
            duel = (await get(f"/duels/{last['duel_id']}", e)).json()
            assert len(duel["players"]) == 5
            assert "This match has started" in (await s.get(f"/c/{cid}")).text

            # START with one guest; an invite-only room is still closed to strangers
            room2 = (await post("/challenges", a, {"link": True, "subject": "Chemistry"})).json()
            await post(f"/challenges/{room2['id']}/accept", f)
            assert (await post(f"/challenges/{room2['id']}/start", a)).json()["status"] == "started"
            assert await is_friend(a, f)
            private = (await post("/challenges", a, {"pids": [b["pid"]], "subject": "Physics"})).json()
            assert private["link"] is False
            assert (await get(f"/challenges/{private['id']}", c)).status_code == 404
            assert (await post(f"/challenges/{private['id']}/accept", c)).status_code == 404
            assert "frontend://rapid/room/" in (await s.get(f"/c/{private['id']}")).text and "rf-link-browser" in (await s.get(f"/c/{private['id']}")).text
    finally:
        await _cleanup(db, users)
