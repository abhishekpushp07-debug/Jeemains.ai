"""CEO dashboard API (read-only) for the JEELIVE.AI app server.

A SEPARATE dashboard project (its own repo) calls these endpoints server-to-server to show how the app is being used.
Everything here is read-only and protected by one shared secret in the CEO_API_TOKEN environment variable
(`Authorization: Bearer <token>`); with the variable unset every route answers 503, so it is closed by default.

What this server can and cannot give:
- CAN: the app's own engagement — how many app profiles exist, who is active, streaks, coins, each app user's
  name + player code + canonical user id (so the dashboard can join on uid).
- CANNOT: raw signup phone numbers. The app deliberately does not store them (friend-search keeps only an HMAC hash and
  the last four digits). The authoritative signup list with contact numbers lives on the jeelive.ai website backend.
  The dashboard reads contacts from the website and joins them to this data on `uid`. See memory/CEO_DASHBOARD.md.
"""
import hmac
import os
import re
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import JSONResponse

IST = timezone(timedelta(hours=5, minutes=30))
MOST_DAYS = 92  # the longest from..to one daily call answers
# Real students only. A real profile is made only after the website verified the session (rf_access.py), so its uid is
# the website's account id: a UUID (`tejas_phone_profiles.id`). Every other id (TEST-…, TESTUSER…, qa…, ms-…, tester-…)
# and every name starting TEST was made by this project's automated tests and is left out of every number here.
WEBSITE_ID = "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"  # lowercase, as the dashboard counts
WEBSITE_ID_RE = re.compile(WEBSITE_ID)
REAL = {"uid": {"$regex": WEBSITE_ID}, "name": {"$not": {"$regex": "^TEST"}}}
NO_STORE = {"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"}
CONTACTS_NOTE = ("Signup phone numbers are not on this app server. The app stores only an HMAC hash and the last four "
                 "digits for friend-search. Read full contacts from the jeelive.ai website backend and join on `uid`.")


def _auth(authorization: str) -> None:
    token = os.environ.get("CEO_API_TOKEN", "").strip()
    if not token:
        raise HTTPException(503, "CEO API is not configured on this server yet.", headers=NO_STORE)
    given = authorization[7:].strip() if authorization and authorization.lower().startswith("bearer ") else ""
    if not given or not hmac.compare_digest(given, token):
        raise HTTPException(401, "A valid CEO API bearer token is required.", headers=NO_STORE)


def _ist_day(offset_days: int = 0) -> str:
    return (datetime.now(IST) - timedelta(days=offset_days)).strftime("%Y-%m-%d")


def _is_test(uid, name) -> bool:
    return not (isinstance(uid, str) and WEBSITE_ID_RE.match(uid)) or str(name or "").startswith("TEST")


def _days(from_: str, to: str) -> list:
    """The IST dates from..to (both included); by default the last 30 days up to today."""
    try:
        end = datetime.strptime(to[:10] if to else _ist_day(0), "%Y-%m-%d")
        start = datetime.strptime(from_[:10], "%Y-%m-%d") if from_ else end - timedelta(days=29)
    except ValueError:
        raise HTTPException(400, "from and to are IST dates like 2026-11-28.", headers=NO_STORE)
    n = (end - start).days + 1
    if n < 1 or n > MOST_DAYS:
        raise HTTPException(400, f"from must be on or before to, and the range at most {MOST_DAYS} days.", headers=NO_STORE)
    return [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(n)]


def _window(days: list) -> tuple:
    """Unix seconds from IST midnight of the first day to IST midnight after the last."""
    start = datetime.strptime(days[0], "%Y-%m-%d").replace(tzinfo=IST)
    return start.timestamp(), (datetime.strptime(days[-1], "%Y-%m-%d").replace(tzinfo=IST) + timedelta(days=1)).timestamp()


def _ist_date(field: str) -> dict:
    """Mongo expression: the IST date (YYYY-MM-DD) of a unix-seconds field."""
    return {"$dateToString": {"format": "%Y-%m-%d", "date": {"$toDate": {"$multiply": [field, 1000]}}, "timezone": "+05:30"}}


def _gems(field: str) -> dict:
    """Mongo expression: all diamonds in a {colour: n} field (a plain number in old profiles)."""
    return {"$switch": {"branches": [
        {"case": {"$eq": [{"$type": field}, "object"]}, "then": {"$sum": {"$map": {"input": {"$objectToArray": field}, "in": "$$this.v"}}}},
        {"case": {"$in": [{"$type": field}, ["int", "long", "double", "decimal"]]}, "then": field}], "default": 0}}


def _match_mode(kind: str, d: dict) -> str:
    """The mode of one paid Rapid Fire match, named as the app's analytics name it."""
    if kind == "daily":
        return "daily"
    if kind == "solo":
        return "offline" if d.get("offline") else "solo"
    if d.get("cup_id") or d.get("mode") == "cup":
        return "cup"
    if d.get("team_mode"):
        return "gang"
    if d.get("mode") == "random":
        return "quick"
    return "rival" if d.get("vs_bot") else "duel"


def _row(p: dict) -> dict:
    dia = p.get("diamonds")
    return {
        "uid": p.get("uid"),
        "is_test": _is_test(p.get("uid"), p.get("name")),
        "name": p.get("name") or None,
        "player_code": p.get("pid") or None,
        "coins": p.get("coins") or 0,
        "diamonds": sum(dia.values()) if isinstance(dia, dict) else (dia or 0),
        "current_streak": p.get("streak") or 0,
        "best_streak": p.get("best_streak") or 0,
        "last_active": p.get("last_day") or None,
        "phone_last4": p.get("phone_last4") or None,  # only the 2–4 digits the app ever kept; usually null
    }


def make_router(db) -> APIRouter:
    router = APIRouter(prefix="/ceo")

    @router.get("/overview")
    async def overview(authorization: str = Header(default="")):
        _auth(authorization)
        profiles = db.rf_profiles
        everyone, total = await profiles.count_documents({}), await profiles.count_documents(REAL)
        active = {
            "today": await profiles.count_documents({**REAL, "last_day": _ist_day(0)}),
            "last_7_days": await profiles.count_documents({**REAL, "last_day": {"$gte": _ist_day(6)}}),
            "last_30_days": await profiles.count_documents({**REAL, "last_day": {"$gte": _ist_day(29)}}),
        }
        on_streak = await profiles.count_documents({**REAL, "streak": {"$gt": 0}})
        # Played Rapid Fire at least once: a solo session, a duel or a rival game (a win is not needed).
        rapid_fire_players = await profiles.count_documents(
            {**REAL, "$or": [{"sessions": {"$gt": 0}}, {"duels": {"$gt": 0}}, {"rival_games": {"$gt": 0}}]})
        best = await profiles.find(REAL, {"_id": 0, "best_streak": 1}).sort("best_streak", -1).limit(1).to_list(1)
        return JSONResponse({
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "app_users": total,
            "test_profiles_left_out": everyone - total,
            "active": active,
            "on_streak": on_streak,
            "rapid_fire_players": rapid_fire_players,
            "best_streak_seen": (best[0].get("best_streak") if best else 0) or 0,
            "contacts": CONTACTS_NOTE,
        }, headers=NO_STORE)

    @router.get("/users")
    async def users(authorization: str = Header(default=""), page: int = 1, limit: int = 100,
                    active_since: str = "", q: str = "", include_test: int = 0):
        _auth(authorization)
        page = max(1, page)
        limit = max(1, min(500, limit))
        query: dict = {} if include_test else dict(REAL)
        if active_since:
            query["last_day"] = {"$gte": active_since[:10]}
        if q.strip():
            safe = re.escape(q.strip()[:60])  # plain text search: no pattern typed into `q` can reach the database
            query["$or"] = [{"name": {"$regex": safe, "$options": "i"}}, {"pid": {"$regex": safe, "$options": "i"}}]
        total = await db.rf_profiles.count_documents(query)
        cursor = db.rf_profiles.find(query, {"_id": 0, "uid": 1, "name": 1, "pid": 1, "coins": 1, "diamonds": 1,
                                             "streak": 1, "best_streak": 1, "last_day": 1, "phone_last4": 1})
        # Most recently active first; the same day is ordered by uid, so a page never repeats or skips a student.
        docs = await cursor.sort([("last_day", -1), ("uid", 1)]).skip((page - 1) * limit).limit(limit).to_list(limit)
        return JSONResponse({
            "total": total, "page": page, "pages": (total + limit - 1) // limit, "limit": limit,
            "items": [_row(d) for d in docs], "contacts": CONTACTS_NOTE,
        }, headers=NO_STORE)

    async def real_uids(include_test: int) -> dict:
        """The filter on a `uid` field that keeps real students only (nothing with include_test=1)."""
        if include_test:
            return {}
        named = await db.rf_profiles.distinct("uid", {"uid": {"$regex": WEBSITE_ID}, "name": {"$regex": "^TEST"}})
        return {"$regex": WEBSITE_ID, "$nin": named}

    async def paid(days: list, include_test: int) -> dict:
        """rf_awards rows (one per player per paid match) inside the IST days."""
        start, end = _window(days)
        uid = await real_uids(include_test)
        return {"ts": {"$gte": start, "$lt": end}, "reward": {"$exists": True}, **({"uid": uid} if uid else {})}

    @router.get("/rapid/daily")
    async def rapid_daily(authorization: str = Header(default=""), from_: str = Query("", alias="from"), to: str = "",
                          include_test: int = 0):
        """Rapid Fire per IST day, from the paid-match ledger (rf_awards). players = students who finished a match;
        solo_completed = solo sprints (online + offline); duels_finished = 2-player-or-more matches (friend, quick,
        rival, cup, gang); daily_plays = All India Rapid plays. by_mode counts matches: solo, offline, daily, duel,
        quick, rival, cup, gang (a match two students played counts once)."""
        _auth(authorization)
        days = _days(from_, to)
        match = await paid(days, include_test)
        players = {r["_id"]: r["n"] for r in await (await db.rf_awards.aggregate([
            {"$match": match}, {"$group": {"_id": {"day": _ist_date("$ts"), "uid": "$uid"}}},
            {"$group": {"_id": "$_id.day", "n": {"$sum": 1}}}], allowDiskUse=True)).to_list(None)}
        first_day = {}  # ref -> the IST day it was first paid (a duel paid across midnight counts on its first day)
        async for r in await db.rf_awards.aggregate([
                {"$match": match}, {"$group": {"_id": "$ref", "day": {"$min": _ist_date("$ts")}}}], allowDiskUse=True):
            first_day[r["_id"]] = r["day"]
        ids = {"solo": [], "duel": []}
        for ref in first_day:
            kind, _, rid = ref.partition(":")
            if kind in ids:
                ids[kind].append(rid)
        offline, duels = set(), {}
        for i in range(0, len(ids["solo"]), 5000):
            offline.update(s["id"] for s in await db.rf_sessions.find(
                {"id": {"$in": ids["solo"][i:i + 5000]}, "offline": True}, {"_id": 0, "id": 1}).to_list(None))
        for i in range(0, len(ids["duel"]), 5000):
            async for d in db.rf_duels.find({"id": {"$in": ids["duel"][i:i + 5000]}},
                                            {"_id": 0, "id": 1, "mode": 1, "cup_id": 1, "team_mode": 1, "vs_bot": 1}):
                duels[d["id"]] = d
        modes = ("solo", "offline", "daily", "duel", "quick", "rival", "cup", "gang")
        rows = {day: {"date": day, "players": players.get(day, 0), "solo_completed": 0, "duels_finished": 0, "daily_plays": 0,
                      "by_mode": {m: 0 for m in modes}} for day in days}
        for ref, day in first_day.items():
            kind, _, rid = ref.partition(":")
            if day not in rows or kind not in ("solo", "duel", "daily"):
                continue
            mode = _match_mode(kind, {"offline": rid in offline} if kind == "solo" else duels.get(rid, {}))
            row = rows[day]
            row["by_mode"][mode] += 1
            row["solo_completed" if kind == "solo" else "duels_finished" if kind == "duel" else "daily_plays"] += 1
        return JSONResponse({"from": days[0], "to": days[-1], "rows": [rows[d] for d in days]}, headers=NO_STORE)

    @router.get("/economy/daily")
    async def economy_daily(authorization: str = Header(default=""), from_: str = Query("", alias="from"), to: str = "",
                            include_test: int = 0):
        """Coins, diamonds and XP paid for Rapid Fire matches per IST day (rf_awards), and every wallet today."""
        _auth(authorization)
        days = _days(from_, to)
        got = {r["_id"]: r for r in await (await db.rf_awards.aggregate([
            {"$match": await paid(days, include_test)},
            {"$group": {"_id": _ist_date("$ts"), "coins": {"$sum": {"$ifNull": ["$reward.coins", 0]}},
                        "xp": {"$sum": {"$ifNull": ["$reward.xp", 0]}}, "diamonds": {"$sum": _gems("$reward.diamonds")}}}],
            allowDiskUse=True)).to_list(None)}
        rows = [{"date": d, "coins_awarded": got.get(d, {}).get("coins", 0), "diamonds_awarded": got.get(d, {}).get("diamonds", 0),
                 "xp_awarded": got.get(d, {}).get("xp", 0)} for d in days]
        total = await (await db.rf_profiles.aggregate([
            {"$match": {} if include_test else REAL},
            {"$group": {"_id": None, "coins": {"$sum": {"$ifNull": ["$coins", 0]}}, "diamonds": {"$sum": _gems("$diamonds")}}}])).to_list(1)
        return JSONResponse({"from": days[0], "to": days[-1], "rows": rows, "totals": {
            "coins_balance": total[0]["coins"] if total else 0, "diamonds_balance": total[0]["diamonds"] if total else 0}}, headers=NO_STORE)

    @router.get("/mission")
    async def mission(authorization: str = Header(default=""), from_: str = Query("", alias="from"), to: str = "",
                      include_test: int = 0):
        """Mission links: how many students made one, friends helped in all, and per IST day the browsers that first
        opened a link (visits) and how many of those counted as a friend helped."""
        _auth(authorization)
        days = _days(from_, to)
        start, end = _window(days)
        uid = await real_uids(include_test)
        links = {"uid": uid} if uid else {}
        links_total = await db.mission_links.count_documents(links)
        helped = await (await db.mission_links.aggregate([{"$match": links}, {"$group": {"_id": None, "n": {"$sum": "$helped"}}}])).to_list(1)
        got = {r["_id"]: r for r in await (await db.mission_visits.aggregate([
            {"$match": {"ts": {"$gte": start, "$lt": end}, "key": {"$regex": "^c:"}}},
            {"$lookup": {"from": "mission_links", "localField": "code", "foreignField": "code", "as": "link"}},
            {"$unwind": "$link"}, *([{"$match": {"link.uid": uid}}] if uid else []),
            {"$group": {"_id": _ist_date("$ts"), "visits": {"$sum": 1}, "helped": {"$sum": {"$cond": ["$counted", 1, 0]}}}}],
            allowDiskUse=True)).to_list(None)}
        return JSONResponse({"links_total": links_total, "helped_total": helped[0]["n"] if helped else 0, "visits_daily": [
            {"date": d, "visits": got.get(d, {}).get("visits", 0), "helped": got.get(d, {}).get("helped", 0)} for d in days]},
            headers=NO_STORE)

    @router.get("/mission/links")
    async def mission_links(authorization: str = Header(default=""), page: int = 1, limit: int = 100, include_test: int = 0):
        """Every Mission link, newest first (same moment: by code, so a page never repeats or skips one)."""
        _auth(authorization)
        page = max(1, page)
        limit = max(1, min(500, limit))
        uid = await real_uids(include_test)
        query = {"uid": uid} if uid else {}
        total = await db.mission_links.count_documents(query)
        docs = await db.mission_links.find(query, {"_id": 0, "uid": 1, "code": 1, "helped": 1, "created_ts": 1}).sort(
            [("created_ts", -1), ("code", 1)]).skip((page - 1) * limit).limit(limit).to_list(limit)
        return JSONResponse({"total": total, "page": page, "pages": (total + limit - 1) // limit, "limit": limit, "items": [{
            "uid": d.get("uid"), "code": d.get("code"), "helped": d.get("helped") or 0,
            "created_at": datetime.fromtimestamp(d["created_ts"], timezone.utc).isoformat(timespec="seconds") if d.get("created_ts") else None}
            for d in docs]}, headers=NO_STORE)

    @router.get("/dream")
    async def dream(authorization: str = Header(default=""), limit: int = 20, include_test: int = 0):
        """Students with at least one dream college, and the colleges chosen by the most students."""
        _auth(authorization)
        limit = max(1, min(100, limit))
        uid = await real_uids(include_test)
        query = {"dreams.0": {"$exists": True}, **({"uid": uid} if uid else {})}
        top = await (await db.rf_dreams.aggregate([
            {"$match": query}, {"$unwind": "$dreams"}, {"$group": {"_id": {"college": "$dreams.college", "uid": "$uid"}}},
            {"$group": {"_id": "$_id.college", "count": {"$sum": 1}}}, {"$sort": {"count": -1, "_id": 1}}, {"$limit": limit}])).to_list(limit)
        return JSONResponse({"students_with_dream": await db.rf_dreams.count_documents(query),
                             "top_colleges": [{"college": t["_id"], "count": t["count"]} for t in top if t["_id"]]}, headers=NO_STORE)

    return router
