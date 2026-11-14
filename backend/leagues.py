"""Leagues and boards.

Friends League: you and your friends ranked by the week's XP (Monday to Sunday, IST); last week's top 3 collect coins.
Gang War board: the top 100 scorers of every Gang vs Gang battle ever played (no weekly table).
"""
import time
from typing import Optional

from fastapi import APIRouter, Header, HTTPException

from gamify import crown_of, ist_week, level_of, week_ends_in
from shop import equipped_of, safe_avatar
from social import blocked_uids, public_name

FRIEND_PRIZES = (150, 100, 50)
EMPTY = {"xp": 0, "wins": 0, "correct": 0, "matches": 0}
BOARD_SIZE = 100


def week_stats(p: dict, key: str) -> dict:
    """A player's totals for one league week (this week's, or last week's once the week has turned)."""
    for field in ("week_stats", "last_week"):
        s = p.get(field) or {}
        if s.get("week") == key:
            return {**EMPTY, **s}
    return {**EMPTY, "week": key}


async def record_battle(db, d: dict, win: str):
    """A Gang War ended: both gangs' all-time record, counted once."""
    for side in ("a", "b"):
        result = "ties" if win == "tie" else "wins" if win == "team:" + side else "losses"
        await db.rf_gangs.update_one({"id": d["teams"][side]["id"]}, {"$inc": {result: 1}})


def make_router(db, rf_user):
    r = APIRouter(prefix="/rf/league")
    last_week = lambda: ist_week(time.time() - 7 * 86400)  # noqa: E731

    # ---------- Friends League ----------
    async def circle(uid):
        """Me and my friends."""
        hidden = await blocked_uids(db, uid)
        fids = [e["fid"] for e in await db.rf_friends.find({"uid": uid}, {"_id": 0, "fid": 1}).to_list(500) if e["fid"] not in hidden]
        profs = await db.rf_profiles.find({"uid": {"$in": [uid, *fids]}}).to_list(len(fids) + 1)
        return profs if any(p["uid"] == uid for p in profs) else [*profs, {"uid": uid}]

    def table(profs, uid, value):
        ranked = sorted(profs, key=lambda p: (-value(p)[0], -value(p)[1], p["uid"]))
        return [{"rank": i + 1, "pid": p.get("pid"), "name": public_name(p), "avatar": safe_avatar(p.get("avatar")), "frame": equipped_of(p).get("frame"),
                 "level": level_of(p.get("xp", 0)), "xp": value(p)[0], "wins": value(p)[1], "you": p["uid"] == uid, "crown": crown_of(p)} for i, p in enumerate(ranked)]

    def weekly(profs, uid, key):
        return table(profs, uid, lambda p: (week_stats(p, key)["xp"], week_stats(p, key)["wins"]))

    def friend_result(profs, uid, key):
        """Last week's final table (players who scored), my row, and my prize: top 3 of a league with at least 3 active players."""
        rows = [x for x in weekly(profs, uid, key) if x["xp"] > 0]
        mine = next((x for x in rows if x["you"]), None)
        return rows, mine, FRIEND_PRIZES[mine["rank"] - 1] if mine and mine["rank"] <= 3 and len(rows) >= 3 else 0

    @r.get("/friends")
    async def friends_league(x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        profs = await circle(uid)
        last = last_week()
        rows, mine, prize = friend_result(profs, uid, last)
        claimed = f"f:{last}" in (next(p for p in profs if p["uid"] == uid).get("league_claims") or [])
        return {"week": ist_week(), "ends_in": week_ends_in(), "friends": len(profs) - 1, "items": weekly(profs, uid, ist_week())[:100],
                "all_time": table(profs, uid, lambda p: (p.get("xp", 0), p.get("wins", 0)))[:100], "prizes": FRIEND_PRIZES,
                "last": {"week": last, "items": rows[:3], "rank": mine["rank"] if mine else None, "prize": prize, "claimed": claimed, "can_claim": bool(prize) and not claimed}}

    @r.post("/friends/claim")
    async def claim_friends(x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        last = last_week()
        _, _, prize = friend_result(await circle(uid), uid, last)
        if not prize:
            raise HTTPException(409, "No prize this time. Finish in the top 3 of a league with at least 3 active players.")
        p = await db.rf_profiles.find_one_and_update({"uid": uid, "league_claims": {"$ne": f"f:{last}"}}, {"$inc": {"coins": prize}, "$addToSet": {"league_claims": f"f:{last}"}}, return_document=True)
        if not p:
            raise HTTPException(409, "You already collected this prize.")
        return {"coins": prize, "coins_total": p["coins"]}

    # ---------- Gang War board ----------
    totals = [{"$match": {"team_mode": True, "status": "finished"}}, {"$unwind": "$players"}, {"$match": {"players.bot": {"$ne": True}}},
              {"$group": {"_id": "$players.uid", "score": {"$sum": "$players.score"}, "matches": {"$sum": 1},
                          "wins": {"$sum": {"$cond": [{"$in": ["$players.uid", {"$ifNull": ["$winners", []]}]}, 1, 0]}}}}]
    order = {"$sort": {"score": -1, "wins": -1, "_id": 1}}
    top_cache: dict = {}

    async def top():
        hit = top_cache.get("t")
        if hit and time.time() - hit[0] < 20:
            return hit[1]
        rows = await (await db.rf_duels.aggregate([*totals, order, {"$limit": BOARD_SIZE}])).to_list(BOARD_SIZE)
        top_cache["t"] = (time.time(), rows)
        return rows

    @r.get("/gangwar")
    async def gang_war_board(x_rf_user: Optional[str] = Header(None)):
        """Everyone who played Gang vs Gang, ranked by the points they scored for their gang. Top 100, all time."""
        uid = rf_user(x_rf_user)
        rows = await top()
        profs = {p["uid"]: p for p in await db.rf_profiles.find({"uid": {"$in": [x["_id"] for x in rows] + [uid]}}).to_list(len(rows) + 1)}
        items = [{"rank": i + 1, "pid": (profs.get(x["_id"]) or {}).get("pid"), "name": public_name(profs.get(x["_id"]) or {}), "avatar": safe_avatar((profs.get(x["_id"]) or {}).get("avatar")),
                  "frame": equipped_of(profs.get(x["_id"]) or {}).get("frame"), "level": level_of((profs.get(x["_id"]) or {}).get("xp", 0)),
                  "score": x["score"], "matches": x["matches"], "wins": x["wins"], "you": x["_id"] == uid, "crown": crown_of(profs.get(x["_id"]) or {})} for i, x in enumerate(rows)]
        me = next((x for x in items if x["you"]), None)
        if not me:
            mine = await (await db.rf_duels.aggregate([{"$match": {"team_mode": True, "status": "finished", "players.uid": uid}}, *totals[1:], {"$match": {"_id": uid}}])).to_list(1)
            if mine:
                ahead = await (await db.rf_duels.aggregate([*totals, {"$match": {"$or": [{"score": {"$gt": mine[0]["score"]}}, {"score": mine[0]["score"], "wins": {"$gt": mine[0]["wins"]}}]}}, {"$count": "n"}])).to_list(1)
                me = {"rank": (ahead[0]["n"] if ahead else 0) + 1, "score": mine[0]["score"], "matches": mine[0]["matches"], "wins": mine[0]["wins"]}
        return {"items": items, "you": {k: me[k] for k in ("rank", "score", "matches", "wins")} if me else None, "size": BOARD_SIZE}

    return r
