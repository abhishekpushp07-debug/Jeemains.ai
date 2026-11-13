"""Iteration 61 — Rapid Fire 2.0 new endpoints.

Covers:
  (a) GET  /api/rf/feed              — only friends in last 7 days, hides blocks, removing friend hides them.
  (b) GET  /api/rf/players/{pid}/h2h — 1 v 1 finished matches, 404 self/unknown/blocked, counts match profile.
  (c) POST /api/rf/rush/claim        — unknown step 404, insufficient 409, day mismatch 409, replay 409, concurrency.
  (d) Diamond store: shop lists gem prices, buy decrements diamonds and adds owned, 409 short/already-owned,
      avatar 403 until bought, diamonds_total = diamonds + diamonds_spent.
  (e) GET  /api/rf/duels/{id} — players[].streak numeric trailing count.

Uses TEST-prefixed throwaway profiles + rf_access grants (same pattern as test_rf_social.py).
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
from gamify import ist_day  # noqa: E402
from social import make_pid, remember_identity  # noqa: E402

BASE = "http://localhost:8001/api/rf"


async def _mk_users(db, tag, n=3):
    users = {}
    for k in range(n):
        uid = f"TEST-iter61-{tag}-{k}"
        token = secrets.token_urlsafe(24)
        await db.rf_access.insert_one({
            "digest": hashlib.sha256(token.encode()).hexdigest(),
            "uid": uid, "sid": "",
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
        })
        await remember_identity(db, uid, {"name": f"TESTIter61U{k}", "phone": f"900100100{k}"})
        users[k] = {"uid": uid, "pid": make_pid(uid), "h": {"Authorization": "Bearer " + token}}
    return users


async def _cleanup(db, users, extra_duel_ids=None):
    uids = [u["uid"] for u in users.values()]
    await db.rf_access.delete_many({"uid": {"$in": uids}})
    await db.rf_profiles.delete_many({"uid": {"$in": uids}})
    await db.rf_friends.delete_many({"$or": [{"uid": {"$in": uids}}, {"fid": {"$in": uids}}]})
    await db.rf_blocks.delete_many({"$or": [{"uid": {"$in": uids}}, {"bid": {"$in": uids}}]})
    await db.rf_feed.delete_many({"uid": {"$in": uids}})
    await db.rf_notices.delete_many({"uid": {"$in": uids}})
    await db.rf_duels.delete_many({"players.uid": {"$in": uids}})
    if extra_duel_ids:
        await db.rf_duels.delete_many({"id": {"$in": extra_duel_ids}})
    await db.rf_awards.delete_many({"uid": {"$in": uids}})


# ---------- (a) /feed ----------
def test_feed():
    asyncio.run(_feed())


async def _feed():
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    users = await _mk_users(db, uuid.uuid4().hex[:6])
    me, friend, stranger = users[0], users[1], users[2]
    now = time.time()
    try:
        async with httpx.AsyncClient(base_url=BASE, timeout=20) as s:
            # befriend only user1
            code = (await s.get("/friends/code", headers=friend["h"])).json()["code"]
            r = await s.post("/friends", headers=me["h"], json={"code": code})
            assert r.status_code == 200
            # Insert feed events: 2 by friend (recent + 8-day-old), 1 by stranger
            at = datetime.now(timezone.utc)
            await db.rf_feed.insert_many([
                {"id": f"iter61-feed-{me['uid']}-fresh", "uid": friend["uid"], "kind": "win",
                 "data": {"vs": "Rival", "mine": 20, "theirs": 10}, "ts": now - 3600, "at": at},
                {"id": f"iter61-feed-{me['uid']}-old", "uid": friend["uid"], "kind": "gem",
                 "data": {"colour": "emerald"}, "ts": now - 8 * 86400, "at": at},
                {"id": f"iter61-feed-{me['uid']}-stranger", "uid": stranger["uid"], "kind": "win",
                 "data": {"vs": "X", "mine": 1, "theirs": 0}, "ts": now - 60, "at": at},
            ])
            r = await s.get("/feed", headers=me["h"])
            assert r.status_code == 200
            items = r.json()["items"]
            ids = [e["id"] for e in items]
            assert f"iter61-feed-{me['uid']}-fresh" in ids
            assert f"iter61-feed-{me['uid']}-old" not in ids, "events older than 7 days must be hidden"
            assert f"iter61-feed-{me['uid']}-stranger" not in ids, "non-friend events must be hidden"
            fresh = next(e for e in items if e["id"] == f"iter61-feed-{me['uid']}-fresh")
            assert fresh["from"]["pid"] == friend["pid"]
            assert "name" in fresh["from"] and fresh["kind"] == "win"

            # block: friend blocks me → their feed events vanish for me
            await s.post("/blocks", headers=friend["h"], json={"pid": me["pid"]})
            after = (await s.get("/feed", headers=me["h"])).json()["items"]
            assert all(e["from"]["pid"] != friend["pid"] for e in after)
            await s.delete(f"/blocks/{me['pid']}", headers=friend["h"])

            # remove friend → their events vanish
            r = await s.delete(f"/friends/{friend['pid']}", headers=me["h"])
            assert r.status_code == 200
            after = (await s.get("/feed", headers=me["h"])).json()["items"]
            assert all(e["from"]["pid"] != friend["pid"] for e in after)
    finally:
        await db.rf_feed.delete_many({"id": {"$regex": "^iter61-feed-"}})
        await _cleanup(db, users)


# ---------- (b) /players/{pid}/h2h ----------
def test_h2h():
    asyncio.run(_h2h())


async def _h2h():
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    users = await _mk_users(db, uuid.uuid4().hex[:6])
    me, friend, stranger = users[0], users[1], users[2]
    now = time.time()
    duel_ids = []
    try:
        # Make sure profiles exist
        for u in users.values():
            await db.rf_profiles.update_one({"uid": u["uid"]}, {"$set": {"pid": u["pid"], "name": "TEST61"}}, upsert=True)

        def seat(u, score):
            return {"uid": u["uid"], "pid": u["pid"], "name": "TEST61", "score": score,
                    "answers": [], "done": True, "ms": 100000, "forfeit": False}

        # 3 finished 1v1 matches: me wins 2, loses 1
        for k, (mine, theirs) in enumerate([(20, 10), (15, 5), (5, 20)]):
            did = f"iter61-h2h-{uuid.uuid4().hex[:8]}"
            duel_ids.append(did)
            winner = me["uid"] if mine > theirs else friend["uid"] if theirs > mine else "tie"
            await db.rf_duels.insert_one({
                "id": did, "exam": "JEE", "mode": "friend", "subject": "Physics",
                "status": "finished", "players": [seat(me, mine), seat(friend, theirs)],
                "card_ids": [], "finished_ts": now - k * 3600, "winner": winner,
            })
        # A gang/team match should NOT count in h2h
        did_team = f"iter61-h2h-team-{uuid.uuid4().hex[:8]}"
        duel_ids.append(did_team)
        await db.rf_duels.insert_one({
            "id": did_team, "exam": "JEE", "mode": "gang", "subject": "Chemistry",
            "status": "finished", "team_mode": True,
            "teams": {"a": {"name": "Kota", "emblem": "lion", "uids": [me["uid"]]},
                      "b": {"name": "Delhi", "emblem": "wolf", "uids": [friend["uid"]]}},
            "players": [{**seat(me, 1), "team": "a"}, {**seat(friend, 2), "team": "b"}],
            "card_ids": [], "finished_ts": now, "winner": friend["uid"],
        })

        async with httpx.AsyncClient(base_url=BASE, timeout=20) as s:
            r = await s.get(f"/players/{friend['pid']}/h2h", headers=me["h"])
            assert r.status_code == 200, r.text
            items = r.json()["items"]
            assert len(items) == 3, f"expected 3 (team mode excluded), got {len(items)}: {items}"
            # newest first
            assert items[0]["id"] == duel_ids[0]
            won = sum(1 for d in items if d["won"])
            lost = sum(1 for d in items if not d["won"] and not d["tie"])
            assert won == 2 and lost == 1

            # counts match profile.head_to_head
            prof = (await s.get(f"/players/{friend['pid']}", headers=me["h"])).json()
            assert prof["head_to_head"] == {"you": 2, "them": 1, "played": 3, "last": {"id": duel_ids[0], "won": True, "tie": False}}

            # 404 for self
            assert (await s.get(f"/players/{me['pid']}/h2h", headers=me["h"])).status_code == 404
            # 404 unknown pid
            assert (await s.get("/players/PXXXXXXXX/h2h", headers=me["h"])).status_code == 404
            # stranger has no 1v1 but exists → 200 with empty items
            r = await s.get(f"/players/{stranger['pid']}/h2h", headers=me["h"])
            assert r.status_code == 200 and r.json()["items"] == []
            # if they block me → 404
            await s.post("/blocks", headers=stranger["h"], json={"pid": me["pid"]})
            assert (await s.get(f"/players/{stranger['pid']}/h2h", headers=me["h"])).status_code == 404
    finally:
        await _cleanup(db, users, extra_duel_ids=duel_ids)


# ---------- (c) /rush/claim ----------
def test_rush_claim():
    asyncio.run(_rush_claim())


async def _rush_claim():
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    users = await _mk_users(db, uuid.uuid4().hex[:6], n=1)
    me = users[0]
    today = ist_day()
    try:
        # seed: 3 gems today, no rush opened; coins=0
        await db.rf_profiles.update_one(
            {"uid": me["uid"]},
            {"$set": {"coins": 0, "day_stats": {"day": today, "gems": 3, "rush": [], "sprints": 0, "correct": 0, "wins": 0, "claimed": []}}},
            upsert=True,
        )
        async with httpx.AsyncClient(base_url=BASE, timeout=20) as s:
            # unknown step → 404
            r = await s.post("/rush/claim", headers=me["h"], json={"at": 99})
            assert r.status_code == 404, r.text
            # locked step (10) → 409
            r = await s.post("/rush/claim", headers=me["h"], json={"at": 10})
            assert r.status_code == 409
            # Bronze (1) success
            r = await s.post("/rush/claim", headers=me["h"], json={"at": 1})
            assert r.status_code == 200, r.text
            body = r.json()
            assert body["chest"] == "Bronze" and body["coins"] == 25 and body["coins_total"] == 25
            steps = {s_["at"]: s_ for s_ in body["rush"]["steps"]}
            assert steps[1]["claimed"] and steps[1]["done"]
            # replay same step → 409
            r = await s.post("/rush/claim", headers=me["h"], json={"at": 1})
            assert r.status_code == 409
            # Silver (3)
            r = await s.post("/rush/claim", headers=me["h"], json={"at": 3})
            assert r.status_code == 200 and r.json()["coins_total"] == 75
            # profile rush reflects both claims
            prof = (await s.get("/profile", headers=me["h"])).json()
            prof_steps = {s_["at"]: s_ for s_ in prof["rush"]["steps"]}
            assert prof_steps[1]["claimed"] and prof_steps[3]["claimed"]
            assert not prof_steps[6]["claimed"] and not prof_steps[6]["done"]

            # concurrency: reset to fresh day with gems=3, two concurrent claims pay only once
            await db.rf_profiles.update_one({"uid": me["uid"]},
                {"$set": {"coins": 0, "day_stats": {"day": today, "gems": 3, "rush": [], "sprints": 0, "correct": 0, "wins": 0, "claimed": []}}})
            r1, r2 = await asyncio.gather(
                s.post("/rush/claim", headers=me["h"], json={"at": 1}),
                s.post("/rush/claim", headers=me["h"], json={"at": 1}),
                return_exceptions=False,
            )
            statuses = sorted([r1.status_code, r2.status_code])
            assert statuses == [200, 409], f"got {statuses}"
            p = await db.rf_profiles.find_one({"uid": me["uid"]})
            assert p["coins"] == 25, f"paid twice: coins={p['coins']}"

            # day mismatch: force yesterday's day_stats → claim → 409
            await db.rf_profiles.update_one({"uid": me["uid"]},
                {"$set": {"day_stats": {"day": "2020-01-01", "gems": 15, "rush": [], "sprints": 0, "correct": 0, "wins": 0, "claimed": []}}})
            r = await s.post("/rush/claim", headers=me["h"], json={"at": 3})
            assert r.status_code == 409
    finally:
        await _cleanup(db, users)


# ---------- (d) diamond store ----------
def test_diamond_store():
    asyncio.run(_shop())


async def _shop():
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    users = await _mk_users(db, uuid.uuid4().hex[:6], n=1)
    me = users[0]
    try:
        # Give me diamonds: 6 red, 4 blue, 2 emerald, 0 gold, 0 kohinoor; 100 coins
        await db.rf_profiles.update_one(
            {"uid": me["uid"]},
            {"$set": {"coins": 100, "diamonds": {"red": 6, "blue": 4, "emerald": 2, "gold": 0, "kohinoor": 0},
                      "diamonds_spent": {"red": 1, "blue": 0, "emerald": 0, "gold": 0, "kohinoor": 0}}},
            upsert=True,
        )
        async with httpx.AsyncClient(base_url=BASE, timeout=20) as s:
            shop = (await s.get("/shop", headers=me["h"])).json()
            # Find gem items
            gem_items = [it for it in shop["items"] if it.get("gems")]
            assert any(it["id"] == "frame_ruby" for it in gem_items)
            ruby = next(it for it in gem_items if it["id"] == "frame_ruby")
            assert ruby["gems"] == {"red": 6} and ruby["price"] == 0
            # Avatar section: av_ruby must be a gems item
            avatars = shop.get("avatars") or []
            av_ruby = next((a for a in avatars if a["id"] == "av_ruby"), None)
            assert av_ruby, "av_ruby avatar missing"
            assert av_ruby.get("gems") == {"red": 8, "blue": 2}

            # diamonds_total = diamonds + diamonds_spent
            prof = (await s.get("/profile", headers=me["h"])).json()
            assert prof["diamonds_total"]["red"] == 7  # 6 + 1
            assert prof["diamonds_total"]["blue"] == 4
            coins_before = prof["coins"]

            # Buy ruby → success, decrements red, increments spent, coins unchanged
            r = await s.post("/shop/buy", headers=me["h"], json={"item_id": "frame_ruby"})
            assert r.status_code == 200, r.text
            after = (await s.get("/profile", headers=me["h"])).json()
            assert after["diamonds"]["red"] == 0
            assert after["diamonds_total"]["red"] == 7  # preserved
            assert after["coins"] == coins_before
            assert "frame_ruby" in after["owned"]

            # Buy again → 409 already owned
            r = await s.post("/shop/buy", headers=me["h"], json={"item_id": "frame_ruby"})
            assert r.status_code == 409

            # Not enough → emerald avatar costs 2 emerald but we only have 2, so buy emerald frame first
            # frame_emerald: 2 emerald — we still have 2 → buy succeeds; then 2nd attempt 409 (owned)
            r = await s.post("/shop/buy", headers=me["h"], json={"item_id": "frame_emerald"})
            assert r.status_code == 200, r.text
            # Kohinoor needs 3 emerald + 1 gold — we have 0 emerald now → 409 short
            r = await s.post("/shop/buy", headers=me["h"], json={"item_id": "frame_kohinoor"})
            assert r.status_code == 409

            # av_ruby 403 until bought
            r = await s.post("/profile/avatar", headers=me["h"], json={"avatar": "av_ruby"})
            assert r.status_code == 403, f"expected 403, got {r.status_code}: {r.text}"

            # buy av_ruby fails (need 8 red, have 0), confirm 409
            r = await s.post("/shop/buy", headers=me["h"], json={"item_id": "av_ruby"})
            assert r.status_code == 409
    finally:
        await _cleanup(db, users)


# ---------- (e) /duels/{id} streak ----------
def test_duel_streak():
    asyncio.run(_streak())


async def _streak():
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    users = await _mk_users(db, uuid.uuid4().hex[:6], n=2)
    me, opp = users[0], users[1]
    did = f"iter61-streak-{uuid.uuid4().hex[:8]}"
    try:
        def seat(u, answers, score):
            return {"uid": u["uid"], "pid": u["pid"], "name": "TEST61",
                    "answers": answers, "score": score, "done": False, "level": 1, "wins": 0,
                    "ms": 50000, "forfeit": False}

        # Me: 3 correct in a row. Opp: C,C,W,C,C → trailing 2
        me_ans = [{"i": i, "outcome": "correct"} for i in range(3)]
        opp_ans = [{"i": 0, "outcome": "correct"}, {"i": 1, "outcome": "correct"},
                   {"i": 2, "outcome": "incorrect"}, {"i": 3, "outcome": "correct"},
                   {"i": 4, "outcome": "correct"}]
        await db.rf_duels.insert_one({
            "id": did, "exam": "JEE", "mode": "friend", "subject": "Physics",
            "status": "running", "players": [seat(me, me_ans, 3), seat(opp, opp_ans, 4)],
            "card_ids": ["c" + str(i) for i in range(10)], "start_at": time.time() - 30,
            "ends_at": time.time() + 120, "entry_seconds": 9.5, "server_now": time.time(),
        })
        async with httpx.AsyncClient(base_url=BASE, timeout=20) as s:
            d = (await s.get(f"/duels/{did}", headers=me["h"])).json()
            streaks = {p["pid"]: p["streak"] for p in d["players"]}
            assert streaks[me["pid"]] == 3
            assert streaks[opp["pid"]] == 2
            for p in d["players"]:
                assert isinstance(p["streak"], int)
    finally:
        await db.rf_duels.delete_one({"id": did})
        await _cleanup(db, users)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
