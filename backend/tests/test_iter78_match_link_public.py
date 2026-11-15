"""Iteration 78: match-link edge checks through the PUBLIC preview URL (ingress), with TEST fixtures removed afterwards."""
import asyncio
import os
import sys
import uuid

import httpx
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, os.path.dirname(__file__))
from test_iter77_match_link import _cleanup, _setup  # noqa: E402

PUB = open("/app/frontend/.env").read().split("EXPO_PUBLIC_BACKEND_URL=")[1].split()[0].strip().rstrip("/")


def test_public_match_link_edges():
    asyncio.run(_flow())


async def _flow():
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    users = await _setup(db, "p" + uuid.uuid4().hex[:5])
    a, b, c = users["a"], users["b"], users["c"]
    try:
        async with httpx.AsyncClient(base_url=PUB + "/api/rf", timeout=30, follow_redirects=False) as s:
            # link room without pids
            r = await s.post("/challenges", json={"link": True, "subject": "Physics"}, headers=a["h"])
            assert r.status_code == 200, r.text
            room = r.json()
            cid = room["id"]
            assert room["link"] and room["players"] == [] and room["seats"] == 5 and 170 < room["expires_in"] <= 180
            assert "_id" not in room
            # public page via ingress
            page = (await s.get(f"/c/{cid}")).text
            for tid in ("rf-link-open", "rf-link-browser", "rf-link-download"):
                assert f'data-testid="{tid}"' in page
            assert f"frontend://rapid/room/{cid}" in page and f"/api/arena/rapid/room/{cid}" in page and "4 of 4 seats open" in page
            # stranger view
            seen = (await s.get(f"/challenges/{cid}", headers=b["h"])).json()
            assert seen["my_status"] == "link" and seen["friend"] is False and seen["can_start"] is False
            # unauthenticated GET is rejected
            assert (await s.get(f"/challenges/{cid}")).status_code in (401, 403)
            # join -> friends + notice
            j = (await s.post(f"/challenges/{cid}/accept", json={}, headers=b["h"])).json()
            assert j["my_status"] == "joined" and j["friend"] is True
            assert await db.rf_friends.find_one({"uid": a["uid"], "fid": b["uid"]}) and await db.rf_friends.find_one({"uid": b["uid"], "fid": a["uid"]})
            notes = (await s.get("/inbox", headers=a["h"])).json()["notices"]
            assert any(n["kind"] == "friend_added" and n["from"]["pid"] == b["pid"] for n in notes)
            assert "3 of 4 seats open" in (await s.get(f"/c/{cid}")).text
            # guest cannot START; host can
            assert (await s.post(f"/challenges/{cid}/start", json={}, headers=b["h"])).status_code == 403
            st = (await s.post(f"/challenges/{cid}/start", json={}, headers=a["h"])).json()
            assert st["status"] == "started" and st["duel_id"]
            # outsider after start: sees started room (UI shows room-closed), cannot join
            out = (await s.get(f"/challenges/{cid}", headers=c["h"])).json()
            assert out["status"] == "started" and out["my_status"] == "link"
            assert (await s.post(f"/challenges/{cid}/accept", json={}, headers=c["h"])).status_code == 409
            assert not await db.rf_friends.find_one({"uid": a["uid"], "fid": c["uid"]})
            # invite-only room still hidden from strangers
            priv = (await s.post("/challenges", json={"pids": [b["pid"]], "subject": "Physics"}, headers=a["h"])).json()
            assert priv["link"] is False
            assert (await s.get(f"/challenges/{priv['id']}", headers=c["h"])).status_code == 404
            # bad cid on public page
            assert (await s.get("/c/not-a-room")).status_code == 404
        async with httpx.AsyncClient(timeout=30) as s2:
            arena = await s2.get(f"{PUB}/api/arena/rapid/room/{cid}")
            assert arena.status_code == 200 and "<html" in arena.text.lower()
    finally:
        await _cleanup(db, users)
