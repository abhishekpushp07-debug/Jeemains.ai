"""JEELIVE website proxy (/api/jl/...): every platform signs in and reads its tests through here.

The app sends a session handle (X-JL-Sid); the website's cookies for it live in Mongo (`jl_jars`), so any server process
can serve any request of any student."""
import json
import os
import re
from datetime import datetime, timezone

import aiohttp
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import Response

import account_deletion
import login_guard
from client_ip import client_ip
from database import db, from_field, now_iso, to_field
from jl_transport import UpstreamError, WebsiteDown, canonical_request
from later import later
from load_guard import load
from rf_access import trust_key
from session_coordination import session_rotation

JEELIVE_API = os.environ['JEELIVE_API'].rstrip('/')
SID_RE = re.compile(r"^[A-Za-z0-9-]{16,64}$")
PASS_HEADERS = ("content-type", "retry-after", "location", "cache-control", "etag", "last-modified", "content-range", "accept-ranges")
JAR_IDLE_DAYS = 90  # a jar no request used for 90 days is removed by Mongo (TTL on seen_at)
JAR_TOUCH_SECONDS = 86400  # seen_at is refreshed at most once a day per jar, not on every request
WEB_INFLIGHT_LIMIT = int(os.environ.get("JL_MAX_INFLIGHT", "3000"))  # website calls waiting at once in one process

http: aiohttp.ClientSession | None = None  # the shared website client (pooled connections), opened at startup
router = APIRouter()


def client() -> aiohttp.ClientSession | None:
    return http


async def load_jar(sid: str) -> dict:
    # Always read from Mongo (one indexed read): with several server processes a per-process copy could send a
    # refresh cookie another process has just rotated, which signs the student out.
    jar = await db.jl_jars.find_one({"sid": sid}, {"_id": 0, "cookies": 1, "seen_at": 1})
    if not jar:
        return {}
    now = datetime.now(timezone.utc)
    seen = jar.get("seen_at")
    if not isinstance(seen, datetime) or (now - seen.replace(tzinfo=timezone.utc)).total_seconds() > JAR_TOUCH_SECONDS:
        await later(db.jl_jars.update_one({"sid": sid}, {"$set": {"seen_at": now}}))  # nobody waits for the daily touch
    return {from_field(k): v for k, v in (jar.get("cookies") or {}).items()}


def cookie_changes(cookies: dict, headers) -> tuple[dict, list]:
    """The cookies a website answer sets (new or changed values) and the ones it expires."""
    sets, gone = {}, []
    for raw in headers.getall("set-cookie", []):
        first, *attrs = raw.split(";")
        if "=" not in first:
            continue
        name, value = first.split("=", 1)
        name, value = name.strip(), value.strip().strip('"')
        if any(a.strip().lower().startswith("max-age=0") for a in attrs) or value == "":
            sets.pop(name, None)
            gone.append(name)
        else:
            if name in gone:
                gone.remove(name)
            if cookies.get(name) != value:
                sets[name] = value
    return sets, gone


async def save_cookie_changes(sid: str, sets: dict, gone: list, uid: str = ""):
    # One field per cookie, never the whole set: two servers renewing different cookies at the same moment both keep theirs.
    update = {"$set": {**{f"cookies.{to_field(k)}": v for k, v in sets.items()}, "updated_at": now_iso(), "seen_at": datetime.now(timezone.utc)}}
    if uid:  # whose jar this is, so deleting that account can sign this device out
        update["$set"]["uid"] = uid
    if gone:
        update["$unset"] = {f"cookies.{to_field(k)}": "" for k in gone}
    await db.jl_jars.update_one({"sid": sid}, update, upsert=True)


@router.api_route("/jl/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def jeelive_proxy(path: str, request: Request, x_jl_sid: str = Header(...)):
    if not SID_RE.match(x_jl_sid):
        raise HTTPException(400, "Invalid session handle.")
    if load.inflight_web > WEB_INFLIGHT_LIMIT:  # the website is answering so slowly that calls pile up here: stop adding more
        return busy_website(5)
    async with session_rotation(db, x_jl_sid, path):
        return await forward_jeelive(path, request, x_jl_sid)


WEBSITE_BUSY = "The website is not answering right now. Your saved work is safe. Please try again in a moment."
TECHNICAL_TEXT = re.compile(r"cloudflare|origin (web )?server|malformed|bad gateway|gateway time|upstream|traceback|exception|internal server error|<html", re.I)


def busy_website(retry_after) -> Response:
    return Response(json.dumps({"data": None, "error": {"code": "website_unavailable", "message": WEBSITE_BUSY}, "meta": {"api_version": "1"}}),
                    status_code=503, media_type="application/json",
                    headers={"Cache-Control": "no-store", "Vary": "X-JL-Sid", "Retry-After": str(retry_after)})


def website_trouble(r) -> bool:
    """The website's own server trouble (21 Nov 2026: its origin answered 520 for ~1 minute and the app showed
    Cloudflare's technical text). Its own plain 500/503 messages still pass; everything else 5xx is replaced."""
    if r.status_code < 500:
        return False
    if r.status_code not in (500, 503):
        return True
    try:
        body = r.json()
    except ValueError:
        return True
    error = body.get("error") if isinstance(body, dict) else None
    message = error.get("message") if isinstance(error, dict) else body.get("detail") if isinstance(body, dict) else None
    return not isinstance(message, str) or not message.strip() or bool(TECHNICAL_TEXT.search(message))


async def forward_jeelive(path: str, request: Request, x_jl_sid: str):
    cookies = dict(await load_jar(x_jl_sid))
    headers = {"Accept": request.headers.get("accept", "application/json")}
    if request.headers.get("content-type"):
        headers["Content-Type"] = request.headers["content-type"]
    for name in ("if-none-match", "if-modified-since", "if-range", "range"):
        if request.headers.get(name):
            headers[name] = request.headers[name]
    if cookies:
        headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in cookies.items())
    ip = client_ip(request)  # only the verified student address: entries a caller wrote themselves are never passed on
    if ip:
        headers["X-Forwarded-For"] = ip
    body = await request.body()
    guard, paused = await login_guard.check(db, request, path, body)
    if paused:
        return paused
    try:
        r = await canonical_request(http, request.method, f"{JEELIVE_API}/{path}", path=path,
                                    params=request.query_params, body=body or None, headers=headers)
    except WebsiteDown as down:  # the shield is shut: answered at once, nothing sent to the website
        return busy_website(down.retry_after)
    except UpstreamError:
        return Response(json.dumps({"data": None, "error": {"code": "upstream_unreachable",
                        "message": "Connection interrupted. Your last saved work is safe. Please try again."},
                        "meta": {"api_version": "1"}}), status_code=503, media_type="application/json", headers={'Cache-Control': 'no-store', 'Vary': 'X-JL-Sid'})
    if guard:
        await login_guard.record(db, guard, r.status_code)
    sets, gone = cookie_changes(cookies, r.headers)
    uid = account_deletion.signed_in_uid(r) if path in account_deletion.SIGN_INS and r.is_success else ""
    if uid and await account_deletion.pending(db, uid):  # asked to be deleted: this app does not sign that account in again
        await account_deletion.end_session(http, "; ".join(f"{k}={v}" for k, v in sets.items()))
        return account_deletion.pending_response()
    if path == "auth/logout" and 200 <= r.status_code < 300:
        await db.jl_jars.delete_one({"sid": x_jl_sid})  # signed out: this session handle carries nothing any more
        await db.rf_trust.delete_one({"_id": trust_key(x_jl_sid, "")})  # nor can it keep playing while the website is down
    elif sets or gone:
        await save_cookie_changes(x_jl_sid, sets, gone, uid)
    if website_trouble(r):  # e.g. its Cloudflare "520" page: a plain line instead, and the app tries again
        return busy_website(r.headers.get("retry-after") or "5")
    out = {k: r.headers[k] for k in PASS_HEADERS if k in r.headers}
    out['Vary'] = 'X-JL-Sid'
    if path.startswith('auth/'):
        out['Cache-Control'] = 'no-store'
    return Response(content=r.content, status_code=r.status_code, headers=out)
