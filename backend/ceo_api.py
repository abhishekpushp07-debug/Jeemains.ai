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

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import JSONResponse

IST = timezone(timedelta(hours=5, minutes=30))
# Real students only. A real profile is made only after the website verified the session (rf_access.py), so its uid is
# the website's account id: a UUID (`tejas_phone_profiles.id`). Every other id (TEST-…, TESTUSER…, qa…, ms-…, tester-…)
# and every name starting TEST was made by this project's automated tests and is left out of every number here.
WEBSITE_ID = "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
REAL = {"uid": {"$regex": WEBSITE_ID, "$options": "i"}, "name": {"$not": {"$regex": "^TEST"}}}
NO_STORE = {"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"}
CONTACTS_NOTE = ("Signup phone numbers are not on this app server. The app stores only an HMAC hash and the last four "
                 "digits for friend-search. Read full contacts from the jeelive.ai website backend and join on `uid`.")


def _auth(authorization: str) -> None:
    token = os.environ.get("CEO_API_TOKEN", "").strip()
    if not token:
        raise HTTPException(503, "CEO API is not configured on this server yet.")
    given = authorization[7:].strip() if authorization and authorization.lower().startswith("bearer ") else ""
    if not given or not hmac.compare_digest(given, token):
        raise HTTPException(401, "A valid CEO API bearer token is required.")


def _ist_day(offset_days: int = 0) -> str:
    return (datetime.now(IST) - timedelta(days=offset_days)).strftime("%Y-%m-%d")


def _row(p: dict) -> dict:
    dia = p.get("diamonds")
    return {
        "uid": p.get("uid"),
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
                    active_since: str = "", q: str = ""):
        _auth(authorization)
        page = max(1, page)
        limit = max(1, min(500, limit))
        query: dict = dict(REAL)
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

    return router
