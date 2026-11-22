"""Delete my account: asked for in the app or on the public web page, with the mobile number + PIN.

The website (jeelive.ai) has no account-deletion operation (checked against its live API list), so a request runs in
three parts:
1. The PIN is checked by the website itself: a sign-in in a separate, throwaway session that is ended at once. The PIN
   is never stored or logged. Wrong PINs count against the same limits as the sign-in screen (login_guard).
2. Everything this server keeps about the player is erased at once (erase_companion): Rapid Fire profile, friends,
   blocks, notices, feed, sprints, learning history, rewards, dreams, All India plays, Cup Night seats, mission links,
   access grants and this app's signed-in device sessions. Matches played with other people stay for them, but the
   player's name, picture and look are taken out of them ("Deleted player").
3. The website account waits in the owner panel (/api/owner/deletions) until the owner deletes it on the website and
   marks it done (target: 30 days). Until then this app does not let that account sign in again.
A repeated request (double tap, a retry after a timeout) returns the same request and erases again; erasing twice is safe.
Nothing erases in the background: a match still running at that moment may pay out a little later and bring a bare
profile row back, so the owner's "Website account deleted" press (owner_panel.py) erases once more before closing it.
"""
import hashlib
import json
import logging
import os
import re
import secrets
import time
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

import login_guard
from client_ip import client_ip
from jl_transport import UpstreamError, canonical_request
from legal_pages import CONTENT
from rf_access import forget_grants, verified_grant

logger = logging.getLogger("account_deletion")
API = os.environ['JEELIVE_API'].rstrip('/')
DUE_DAYS = 30
RESET_COOLDOWN = timedelta(hours=72)
DELETED_NAME = "Deleted player"
CODE = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
RID_RE = re.compile(r"^DEL-[A-HJ-NP-Z2-9]{4}-[A-HJ-NP-Z2-9]{4}$")
SIGN_INS = ("auth/phone", "auth/phone/signup")
PENDING_MESSAGE = ("This account is being deleted, so it cannot sign in here any more. If this is a mistake, write to "
                   f"{CONTENT['supportEmail']} (never send your PIN).")
NOTHING_DELETED = "Nothing was deleted."


class DeleteRequest(BaseModel):
    """Checked by hand (not by pattern) so a 422 never echoes the PIN back."""
    model_config = ConfigDict(extra='forbid', hide_input_in_errors=True)
    phone: str = Field(max_length=32)
    pin: str = Field(max_length=8)
    confirm: str = Field(max_length=12)

    def problem(self) -> str:
        if not re.fullmatch(r"\+?[0-9]{8,15}", re.sub(r"[\s()-]", "", self.phone)):
            return "Enter your registered mobile number."
        if not re.fullmatch(r"[0-9]{4}", self.pin):
            return "Your PIN is exactly 4 digits."
        if self.confirm.strip().upper() != "DELETE":
            return "Type DELETE to confirm."
        return ""


def _now():
    return datetime.now(timezone.utc)


def _iso(value):
    return value.replace(tzinfo=timezone.utc).isoformat() if isinstance(value, datetime) else None


def _digits(phone) -> str:
    return re.sub(r"\D", "", phone or "")


def _unwrap(body):
    return body.get('data') if isinstance(body, dict) and isinstance(body.get('meta'), dict) and body['meta'].get('api_version') else body


def _website_message(r) -> str:
    try:
        body = r.json()
    except ValueError:
        return ""
    message = (body.get("error") or {}).get("message") if isinstance(body, dict) and isinstance(body.get("error"), dict) else None
    message = message or (body.get("detail") if isinstance(body, dict) else None)
    return message if isinstance(message, str) else ""


def _cookie_name(field: str) -> str:
    """Jar fields are cookie names made safe for Mongo (server.jar_field); this turns them back."""
    return field.replace("%24", "$").replace("%2E", ".").replace("%25", "%")


def new_cookies(headers) -> str:
    """The cookies a website answer sets, as one Cookie header (to end that session again)."""
    pairs = [raw.split(";", 1)[0].strip() for raw in headers.getall("set-cookie", [])]
    return "; ".join(p for p in pairs if "=" in p and p.split("=", 1)[1].strip('"'))


def signed_in_uid(r) -> str:
    try:
        user = _unwrap(r.json())
    except ValueError:
        return ""
    uid = user.get("id") if isinstance(user, dict) else None
    return uid if isinstance(uid, str) else ""


async def pending(db, uid: str) -> bool:
    return bool(uid) and bool(await db.account_deletions.find_one({"uid": uid, "active": True}, {"_id": 1}))


def pending_response() -> Response:
    return Response(json.dumps({"data": None, "error": {"code": "account_deletion_pending", "message": PENDING_MESSAGE}, "meta": {"api_version": "1"}}),
                    status_code=403, media_type="application/json", headers={"Cache-Control": "no-store"})


async def end_session(client, cookie: str):
    """Signs a website session out (best effort: a session nobody holds any more also runs out by itself)."""
    if not cookie:
        return
    try:
        await canonical_request(client, "POST", f"{API}/auth/logout", path="auth/logout", params=None, body=b"{}",
                                headers={"Content-Type": "application/json", "Accept": "application/json", "Cookie": cookie})
    except UpstreamError:
        logger.warning("website sign-out did not answer")


async def check_pin(db, client, request: Request, phone: str, pin: str) -> dict:
    """The website's own sign-in decides whether the PIN is right. Its session is ended straight away."""
    body = json.dumps({"phone": phone, "pin": pin}).encode()
    guard, paused = await login_guard.check(db, request, login_guard.SIGN_IN, body)
    if paused:
        raise HTTPException(429, json.loads(paused.body)["error"]["message"], headers={"Retry-After": paused.headers["retry-after"]})
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    ip = client_ip(request)
    if ip:
        headers["X-Forwarded-For"] = ip
    try:
        r = await canonical_request(client, "POST", f"{API}/auth/phone", path="auth/phone", params=None, body=body, headers=headers)
    except UpstreamError:
        raise HTTPException(503, f"Connection interrupted. {NOTHING_DELETED} Please try again.")
    await login_guard.record(db, guard, r.status_code)
    await end_session(client, new_cookies(r.headers))
    if r.status_code in login_guard.WRONG:
        raise HTTPException(401, f"{_website_message(r) or 'Wrong mobile number or PIN.'} {NOTHING_DELETED}".strip())
    if r.status_code == 429:
        raise HTTPException(429, _website_message(r) or "Too many tries. Please wait a few minutes.", headers={"Retry-After": r.headers.get("retry-after", "60")})
    if r.status_code == 422:
        raise HTTPException(422, f"This mobile number or PIN was not accepted. Check the number you signed up with. {NOTHING_DELETED}")
    if not r.is_success:
        raise HTTPException(503, f"The account service is busy. {NOTHING_DELETED} Please try again in a minute.")
    try:
        user = _unwrap(r.json())
    except ValueError:
        user = None
    if not isinstance(user, dict) or not isinstance(user.get("id"), str) or not user["id"]:
        raise HTTPException(503, f"The account could not be confirmed. {NOTHING_DELETED} Please try again.")
    return user


async def end_devices(db, client, uid: str) -> int:
    """Signs out every device session of this player that this server knows (its sign-in jars)."""
    sids = {s for s in await db.rf_access.distinct("sid", {"uid": uid}) if s} | set(await db.jl_jars.distinct("sid", {"uid": uid}))
    ended = 0
    for sid in list(sids)[:200]:
        # A jar tagged with someone else signed in on that phone later: theirs, not this player's.
        jar = await db.jl_jars.find_one({"sid": sid, "uid": {"$in": [uid, None]}}, {"_id": 0, "cookies": 1})
        if not jar:
            continue
        await end_session(client, "; ".join(f"{_cookie_name(k)}={v}" for k, v in (jar.get("cookies") or {}).items()))
        await db.jl_jars.delete_one({"sid": sid})
        ended += 1
    return ended


async def erase_companion(db, uid: str) -> dict:
    """Everything this server keeps about one player: personal rows are removed, shared matches keep only the game
    record (score and time) without the name, picture or look. Safe to run again."""
    now = time.time()
    profile = await db.rf_profiles.find_one({"uid": uid}, {"_id": 0, "name": 1, "display_name": 1, "phone_last4": 1}) or {}
    names = {n for n in (profile.get("name"), profile.get("display_name"), "••••••" + profile["phone_last4"] if profile.get("phone_last4") else None) if n}
    anon = {f"players.$[p].{k}": v for k, v in {"name": DELETED_NAME, "avatar": None, "frame": None, "entry": None, "pid": None, "deleted": True}.items()}
    pick = [{"p.uid": uid}]
    done = {}
    # Seats nobody has taken yet are closed, so no one is matched against a deleted player.
    await db.rf_duels.update_many({"players.uid": uid, "status": "waiting"}, {"$set": {"status": "archived", "archived_ts": now}})
    await db.rf_cups.update_many({"players.uid": uid, "status": "open", "host_uid": {"$ne": uid}}, {"$pull": {"players": {"uid": uid}}})
    await db.rf_cups.update_many({"host_uid": uid, "status": "open"}, {"$set": {"status": "cancelled"}})
    await db.rf_cups.update_many({"$or": [{"invites": uid}, {"spectators": uid}]}, {"$pull": {"invites": uid, "spectators": uid}})
    await db.rf_challenges.update_many({"from_uid": uid, "status": "open"}, {"$set": {"status": "expired"}})
    if names:  # the friend feed tells "won against <name>": that name goes too (feeds show the last 7 days)
        recent = await db.rf_duels.find({"players.uid": uid, "finished_ts": {"$gt": now - 8 * 86400}}, {"_id": 0, "id": 1, "players.uid": 1}).limit(500).to_list(500)
        rivals = list({p["uid"] for d in recent for p in d["players"] if p["uid"] != uid and not p["uid"].startswith("bot-")})
        if rivals:
            await db.rf_feed.update_many({"uid": {"$in": rivals}, "ts": {"$gt": now - 8 * 86400}, "kind": "win", "data.vs": {"$in": list(names)},
                                          "id": {"$in": [f"duel:{d['id']}:{k}" for d in recent for k in range(8)]}}, {"$set": {"data.vs": DELETED_NAME}})
    done["matches"] = (await db.rf_duels.update_many({"players.uid": uid}, {"$set": anon}, array_filters=pick)).modified_count
    done["cups"] = (await db.rf_cups.update_many({"players.uid": uid}, {"$set": anon}, array_filters=pick)).modified_count
    gangs = 0
    async for g in db.rf_gangs.find({"members.uid": uid}, {"_id": 0, "id": 1, "members": 1, "leader_uid": 1}):
        rest = sorted((m for m in g["members"] if m["uid"] != uid), key=lambda m: m.get("ts", 0))
        update = {"$pull": {"members": {"uid": uid}}}
        if not rest:
            update["$set"] = {"closed": True}
        elif g.get("leader_uid") == uid:  # the longest-standing member takes over, as when a leader leaves
            update["$set"] = {"leader_uid": rest[0]["uid"]}
        await db.rf_gangs.update_one({"id": g["id"]}, update)
        gangs += 1
    done["gangs_left"] = gangs
    codes = await db.mission_links.distinct("code", {"uid": uid})
    if codes:
        await db.mission_visits.delete_many({"code": {"$in": codes}})
    for key, collection, query in (
            ("profile", db.rf_profiles, {"uid": uid}),
            ("friends", db.rf_friends, {"$or": [{"uid": uid}, {"fid": uid}]}),
            ("blocks", db.rf_blocks, {"$or": [{"uid": uid}, {"bid": uid}]}),
            ("notices", db.rf_notices, {"$or": [{"uid": uid}, {"from_uid": uid}]}),
            ("feed", db.rf_feed, {"uid": uid}),
            ("sprints", db.rf_sessions, {"user_id": uid}),
            ("learning", db.rf_learning_events, {"uid": uid}),
            ("rewards", db.rf_awards, {"uid": uid}),
            ("dreams", db.rf_dreams, {"uid": uid}),
            ("all_india", db.rf_daily_plays, {"uid": uid}),
            ("cup_night_seats", db.rf_night_seats, {"uid": uid}),
            ("mission_links", db.mission_links, {"uid": uid}),
            ("gang_reports", db.rf_gang_reports, {"uid": uid}),
            ("access", db.rf_access, {"uid": uid}),
            ("trusted_sessions", db.rf_trust, {"uid": uid})):
        done[key] = (await collection.delete_many(query)).deleted_count
    forget_grants(uid)
    return done


def new_id() -> str:
    pick = lambda: "".join(secrets.choice(CODE) for _ in range(4))  # noqa: E731
    return f"DEL-{pick()}-{pick()}"


def receipt(doc: dict) -> dict:
    """What the student may see: no number, name or account id."""
    state = doc["state"]
    return {"request_id": doc["id"], "state": state, "requested_at": _iso(doc["requested_at"]), "due_at": _iso(doc["due_at"]),
            "completed_at": _iso(doc.get("completed_at")), "rapid_fire_erased": bool(doc.get("erased_at")),
            "website_account": {"owner_completed": "deleted", "cancelled": "kept"}.get(state, "pending"), "signed_out": True}


async def ensure_indexes(db):
    await db.account_deletions.create_index("id", unique=True)
    await db.account_deletions.create_index("uid", unique=True, name="one_active_request", partialFilterExpression={"active": True})
    await db.account_deletions.create_index([("state", 1), ("requested_at", -1)])
    await db.jl_jars.create_index("uid", sparse=True)


def make_router(db, client):
    """`client` returns the server's shared website HTTP client."""
    router = APIRouter(prefix="/account")

    @router.post("/delete-request")
    async def request_deletion(data: DeleteRequest, request: Request):
        if data.problem():
            raise HTTPException(422, data.problem())
        phone_typed = re.sub(r"[\s()-]", "", data.phone)
        # Forgot PIN needs no OTP (owner's choice), so someone who only knows the number could reset the PIN and
        # erase the student at once. Deletion therefore opens RESET_COOLDOWN after a Forgot-PIN reset of that number.
        reset = await db.pin_resets.find_one({"phone": hashlib.sha256(_digits(phone_typed)[-10:].encode()).hexdigest(), "result": "reset",
                                              "at": {"$gte": _now() - RESET_COOLDOWN}}, {"_id": 0, "at": 1}, sort=[("at", -1)])
        if reset:
            opens = reset["at"].replace(tzinfo=timezone.utc) + RESET_COOLDOWN
            hours = max(1, -(-int((opens - _now()).total_seconds()) // 3600))
            raise HTTPException(423, f"This number's PIN was reset recently. To keep accounts safe, deletion opens 3 days after a PIN reset "
                                     f"(in about {hours} hour{'s' if hours != 1 else ''}). {NOTHING_DELETED}")
        user = await check_pin(db, client(), request, phone_typed, data.pin)
        uid = user["id"]
        # Signed in inside the app: the number must belong to the account signed in there.
        token = request.headers.get("authorization", "").removeprefix("Bearer ")
        if token:
            try:
                grant = await verified_grant(db, token)
            except HTTPException:
                grant = None
            if grant and grant["uid"] != uid:
                raise HTTPException(403, f"This mobile number belongs to a different account than the one signed in here. {NOTHING_DELETED}")
        now = _now()
        phone = _digits(user.get("phone")) or _digits(phone_typed)
        doc = {"id": new_id(), "uid": uid, "phone": phone, "phone_last4": phone[-4:], "name": re.sub(r"\s+", " ", str(user.get("name") or "")).strip()[:60],
               "source": "app" if token else "web", "state": "erasing", "active": True, "requested_at": now, "due_at": now + timedelta(days=DUE_DAYS),
               "history": [{"at": now, "event": "requested", "by": "app" if token else "web page"}]}
        try:
            await db.account_deletions.insert_one(doc)
        except DuplicateKeyError:  # already asked (double tap / retry): same request, erased again below
            doc = await db.account_deletions.find_one({"uid": uid, "active": True}, {"_id": 0})
            if not doc:
                raise HTTPException(409, "This request just changed. Please try again.")
        ended = await end_devices(db, client(), uid)
        erased = await erase_companion(db, uid)
        first = not doc.get("erased_at")
        update = {"$set": {"state": "owner_pending" if doc["state"] == "erasing" else doc["state"], "erased_at": doc.get("erased_at") or _now()},
                  "$inc": {"sessions_ended": ended}}
        if first:
            update["$set"]["erased"] = erased
            update["$push"] = {"history": {"at": _now(), "event": "rapid_fire_erased", "by": "server"}}
        doc = await db.account_deletions.find_one_and_update({"id": doc["id"]}, update, projection={"_id": 0}, return_document=ReturnDocument.AFTER)
        logger.info("account deletion requested id=%s first=%s", doc["id"], first)
        return receipt(doc)

    @router.get("/delete-request/{rid}")
    async def request_status(rid: str):
        doc = await db.account_deletions.find_one({"id": rid}, {"_id": 0}) if RID_RE.match(rid) else None
        if not doc:
            raise HTTPException(404, "No deletion request has this number.")
        return receipt(doc)

    return router
