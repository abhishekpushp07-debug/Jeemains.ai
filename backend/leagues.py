"""Weekly leagues, Monday to Sunday (IST).

Friends League: you and your friends ranked by the week's XP. Gang League: gangs ranked by Gang War points
(3 for a win, 1 for a tie). Last week's top 3 collect coins once the new week begins.
"""
import time
from typing import Optional

from fastapi import APIRouter, Header, HTTPException

from gamify import ist_week, level_of, week_ends_in
from shop import equipped_of, safe_avatar
from social import blocked_uids, public_name

FRIEND_PRIZES = (150, 100, 50)
GANG_PRIZES = (300, 200, 100)
POINTS = {"wins": 3, "ties": 1, "losses": 0}
RIVAL_CAP = 3  # wars against the same gang that count for points in one week
EMPTY = {"xp": 0, "wins": 0, "correct": 0, "matches": 0}


def week_stats(p: dict, key: str) -> dict:
    """A player's totals for one league week (this week's, or last week's once the week has turned)."""
    for field in ("week_stats", "last_week"):
        s = p.get(field) or {}
        if s.get("week") == key:
            return {**EMPTY, **s}
    return {**EMPTY, "week": key}


def gang_week(g: dict, key: str) -> dict:
    for field in ("league", "last_league"):
        s = g.get(field) or {}
        if s.get("week") == key:
            return {k: s.get(k, 0) for k in ("pts", "wins", "losses", "ties")}
    return {"pts": 0, "wins": 0, "losses": 0, "ties": 0}


async def record_battle(db, d: dict, win: str):
    """A Gang War ended: both gangs' all-time record and this week's league points, counted once."""
    week = ist_week()
    for side, other in (("a", "b"), ("b", "a")):
        gid, rival = d["teams"][side]["id"], d["teams"][other]["id"]
        g = await db.rf_gangs.find_one({"id": gid}, {"league": 1}) or {}
        lg, rolled = g.get("league") or {}, {}
        if lg.get("week") != week:
            rolled = {"last_league": lg} if lg.get("week") else {}
            lg = {"week": week, "pts": 0, "wins": 0, "losses": 0, "ties": 0, "vs": {}}
        result = "ties" if win == "tie" else "wins" if win == "team:" + side else "losses"
        met = (lg.get("vs") or {}).get(rival, 0)
        lg = {**lg, result: lg.get(result, 0) + 1, "pts": lg.get("pts", 0) + (POINTS[result] if met < RIVAL_CAP else 0), "vs": {**(lg.get("vs") or {}), rival: met + 1}}
        await db.rf_gangs.update_one({"id": gid}, {"$set": {"league": lg, **rolled}, "$inc": {result: 1}})


def make_router(db, rf_user):
    r = APIRouter(prefix="/rf/league")
    live = {"closed": {"$ne": True}}
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
                 "level": level_of(p.get("xp", 0)), "xp": value(p)[0], "wins": value(p)[1], "you": p["uid"] == uid} for i, p in enumerate(ranked)]

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

    # ---------- Gang League ----------
    async def gang_table(key):
        gangs = await db.rf_gangs.find({**live, "$or": [{"league.week": key}, {"last_league.week": key}]},
                                       {"_id": 0, "id": 1, "name": 1, "emblem": 1, "kind": 1, "members.uid": 1, "league": 1, "last_league": 1}).to_list(3000)
        rows = [{"id": g["id"], "name": g["name"], "emblem": g["emblem"], "kind": g.get("kind", "gang"), "members": len(g["members"]), **gang_week(g, key)} for g in gangs]
        rows.sort(key=lambda x: (-x["pts"], -x["wins"], x["losses"], x["id"]))
        return [{**x, "rank": i + 1} for i, x in enumerate(rows)]

    async def my_gangs(uid):
        return {g["id"]: g for g in await db.rf_gangs.find({"members.uid": uid, **live}, {"_id": 0, "id": 1, "name": 1, "emblem": 1, "kind": 1, "members": 1}).to_list(20)}

    def gang_prize(row, g, uid):
        """Top 3 with points, for players who were already in the gang before this week began."""
        joined = next((m["ts"] for m in g["members"] if m["uid"] == uid), time.time())
        week_start = time.time() + week_ends_in() - 7 * 86400
        return GANG_PRIZES[row["rank"] - 1] if row["rank"] <= 3 and row["pts"] > 0 and joined < week_start else 0

    @r.get("/gangs")
    async def gangs_league(x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        mine, week, last = await my_gangs(uid), ist_week(), last_week()
        rows = [{**x, "mine": x["id"] in mine} for x in await gang_table(week)]
        final = await gang_table(last)
        claims = set((await db.rf_profiles.find_one({"uid": uid}, {"league_claims": 1}) or {}).get("league_claims") or [])
        ranked = {x["id"] for x in rows}
        unranked = [{"id": g["id"], "name": g["name"], "emblem": g["emblem"], "kind": g.get("kind", "gang"), "members": len(g["members"]), "pts": 0, "wins": 0, "losses": 0, "ties": 0, "rank": None, "mine": True}
                    for g in mine.values() if g["id"] not in ranked]
        return {"week": week, "ends_in": week_ends_in(), "items": rows[:50], "mine": [x for x in rows[50:] if x["mine"]] + unranked,
                "points": POINTS, "prizes": GANG_PRIZES, "rival_cap": RIVAL_CAP,
                "last": {"week": last, "items": final[:3],
                         "prizes": [{"id": x["id"], "name": x["name"], "emblem": x["emblem"], "rank": x["rank"], "prize": gang_prize(x, mine[x["id"]], uid), "claimed": f"g:{x['id']}:{last}" in claims}
                                    for x in final[:3] if x["id"] in mine and gang_prize(x, mine[x["id"]], uid)]}}

    @r.post("/gangs/{gid}/claim")
    async def claim_gang(gid: str, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        g, last = (await my_gangs(uid)).get(gid), last_week()
        row = next((x for x in await gang_table(last) if x["id"] == gid), None) if g else None
        prize = gang_prize(row, g, uid) if row else 0
        if not prize:
            raise HTTPException(409, "No prize here. Your gang must finish the week in the top 3, and you must have been a member that week.")
        key = f"g:{gid}:{last}"
        p = await db.rf_profiles.find_one_and_update({"uid": uid, "league_claims": {"$ne": key}}, {"$inc": {"coins": prize}, "$addToSet": {"league_claims": key}}, return_document=True)
        if not p:
            raise HTTPException(409, "You already collected this prize.")
        return {"coins": prize, "coins_total": p["coins"]}

    return r
