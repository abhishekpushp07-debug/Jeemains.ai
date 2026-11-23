"""JEELIVE.AI website  <->  JEELIVE.AI app server connector  (Rank + Mission + Dream college)

One file. Drop it into the website's FastAPI backend and mount it under the existing /api prefix:

    from jeelive_app_connect import router as jeelive_app_router, close as close_jeelive_app

    api_router.include_router(jeelive_app_router)            # before app.include_router(api_router)
    app.add_event_handler("shutdown", close_jeelive_app)

The browser then talks ONLY to the website's own origin (no CORS, no app-server address in the page):

    GET  /api/rank/meta | /api/rank/colleges | /api/rank/target/bitsat | /api/rank/cutoff/options   public
    POST /api/rank/estimate | percentile | predict | college | bitsat | comedk | comedk/college
         /api/rank/target/jee | target/comedk | compare | compare/colleges | cutoff                 public
    POST /api/rank/pdf/jee | pdf/comedk | pdf/bitsat | pdf/target/jee | pdf/target/comedk
         /api/rank/pdf/target/bitsat | pdf/saved                               public, application/pdf
    GET  /api/mission/me                                                       signed-in student
    GET  /api/dream     PUT /api/dream/dreams     POST /api/dream/mocks     POST /api/dream/cheered   signed-in student
    GET  /api/j/{code}                                                         optional pretty share link

Environment (all optional, see ../.env.example):
    JEELIVE_APP_API          the app server's API root          default https://jeelive-mobile.emergent.host/api
    JEELIVE_SESSION_COOKIE   the website's session cookie name   default access_token
    JEELIVE_SHARE_LINK_BASE  where a student's share link lives  default <JEELIVE_APP_API>/j
    JEELIVE_SITE_URL         where a broken share link lands     default https://jeelive.ai

How a signed-in call works (Mission, Dream college):
    1. the student's browser sends the website its session cookie as usual;
    2. this file hands that cookie to the app server once (POST /rf/access {"access_cookie": ...}); the app server asks
       the website's own GET /auth/me who it is and answers with a 15-minute pass {token, user_id, expires_at};
    3. the pass is kept in memory (never on disk, never logged) and sent as "Authorization: Bearer <token>".
The app server never receives a phone number or PIN, and never trusts a user id typed by the caller.

Needs: fastapi, httpx (both are already in a standard Emergent FastAPI backend).
"""
import hashlib
import os
import re
import time
from collections import OrderedDict
from datetime import datetime
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response

APP_API = os.environ.get("JEELIVE_APP_API", "https://jeelive-mobile.emergent.host/api").rstrip("/")
SESSION_COOKIE = os.environ.get("JEELIVE_SESSION_COOKIE", "access_token")
SHARE_LINK_BASE = os.environ.get("JEELIVE_SHARE_LINK_BASE", f"{APP_API}/j").rstrip("/")
SITE = os.environ.get("JEELIVE_SITE_URL", "https://jeelive.ai")

# Only these paths are forwarded; anything else is a 404 here and never reaches the app server.
RANK_GET = {"meta", "colleges", "target/bitsat", "cutoff/options"}
RANK_POST = {"estimate", "percentile", "predict", "college", "bitsat", "comedk", "comedk/college",
             "target/jee", "target/comedk", "compare", "compare/colleges", "cutoff"}
RANK_PDF = {"pdf/jee", "pdf/comedk", "pdf/bitsat", "pdf/target/jee", "pdf/target/comedk", "pdf/target/bitsat", "pdf/saved"}

STATIC_TTL = 600          # the four GET lists (meta, colleges, target/bitsat, cutoff/options) only change when the app server is redeployed
MAX_BODY = 16 * 1024      # the largest real request (saved-list PDF) is under 8 KB
GRANT_MEMORY = 50_000     # signed-in students remembered per process
BUSY = "Rank abhi load nahi hua. Retry dabao."
BUSY_ACCOUNT = "Abhi load nahi hua. Thodi der mein dobara try karo."
SIGN_IN = "Please sign in again."
CODE = re.compile(r"^[A-Za-z2-9]{7}$")

router = APIRouter()
_http: Optional[httpx.AsyncClient] = None
_static: dict = {}                      # path -> (good until, body)
_grants: OrderedDict = OrderedDict()    # sha256(session cookie) -> (token, expires at)


def http() -> httpx.AsyncClient:
    """One pooled client for the whole process (no TLS handshake per request)."""
    global _http
    if _http is None or _http.is_closed:
        _http = httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=5.0),
                                  limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
                                  headers={"User-Agent": "jeelive-website-connector/1.0", "Accept": "application/json"})
    return _http


async def close():
    if _http is not None and not _http.is_closed:
        await _http.aclose()


async def _call(method: str, path: str, *, content: Optional[bytes] = None, json=None, token: Optional[str] = None,
                timeout: Optional[float] = None, busy: str = BUSY) -> httpx.Response:
    headers = {}
    if content is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        res = await http().request(method, APP_API + path, content=content, json=json, headers=headers,
                                   **({"timeout": timeout} if timeout else {}))
    except httpx.HTTPError as exc:  # the app server is unreachable or too slow: the page shows its Retry box
        raise HTTPException(503, busy, headers={"Retry-After": "5", "Cache-Control": "no-store"}) from exc
    if res.status_code >= 500:
        raise HTTPException(503, busy, headers={"Retry-After": res.headers.get("retry-after", "5"), "Cache-Control": "no-store"})
    return res


def _relay(res: httpx.Response, private: bool = False) -> Response:
    """The app server's own status and JSON (so its 404 / 422 messages reach the page word for word)."""
    return Response(res.content, status_code=res.status_code, media_type=res.headers.get("content-type", "application/json"),
                    headers={"Cache-Control": "no-store"} if private else None)


# ------------------------------------------------------------------ Rank (public)
@router.get("/rank/{path:path}")
async def rank_get(path: str):
    if path not in RANK_GET:
        raise HTTPException(404, "Not found")
    hit = _static.get(path)
    if hit and hit[0] > time.monotonic():
        return Response(hit[1], media_type="application/json", headers={"Cache-Control": "public, max-age=300"})
    res = await _call("GET", f"/rank/{path}")
    if res.status_code == 200:
        _static[path] = (time.monotonic() + STATIC_TTL, res.content)
        return Response(res.content, media_type="application/json", headers={"Cache-Control": "public, max-age=300"})
    return _relay(res)


@router.post("/rank/{path:path}")
async def rank_post(path: str, request: Request):
    if path not in RANK_POST and path not in RANK_PDF:
        raise HTTPException(404, "Not found")
    body = await request.body()
    if len(body) > MAX_BODY:
        raise HTTPException(413, "Request too large")
    if path in RANK_PDF:
        res = await _call("POST", f"/rank/{path}", content=body, timeout=30.0, busy="PDF nahi bani. Network check karke dobara try karo.")
        if res.status_code != 200:
            return _relay(res)
        name = res.headers.get("content-disposition", 'attachment; filename="JEELIVE-Rank.pdf"')
        return Response(res.content, media_type="application/pdf", headers={"Content-Disposition": name, "Cache-Control": "no-store"})
    return _relay(await _call("POST", f"/rank/{path}", content=body))


# ------------------------------------------------------------------ signed-in student (Mission, Dream college)
def session_cookie(request: Request) -> str:
    """The student's website session. Replace this one function if the website keeps its session somewhere else."""
    value = request.cookies.get(SESSION_COOKIE, "")
    if not value or any(c in value for c in "\r\n;"):
        raise HTTPException(401, SIGN_IN, headers={"Cache-Control": "no-store"})
    return value


async def _grant(cookie: str, fresh: bool = False) -> str:
    key = hashlib.sha256(cookie.encode()).hexdigest()
    hit = _grants.get(key)
    if hit and not fresh and hit[1] > time.time() + 60:
        return hit[0]
    res = await _call("POST", "/rf/access", json={"access_cookie": cookie}, busy=BUSY_ACCOUNT)
    if res.status_code == 401:
        _grants.pop(key, None)
        raise HTTPException(401, SIGN_IN, headers={"Cache-Control": "no-store"})
    if res.status_code != 200:
        raise HTTPException(503, BUSY_ACCOUNT, headers={"Retry-After": "5", "Cache-Control": "no-store"})
    data = res.json()
    _grants[key] = (data["token"], datetime.fromisoformat(data["expires_at"]).timestamp())
    _grants.move_to_end(key)
    while len(_grants) > GRANT_MEMORY:
        _grants.popitem(last=False)
    return data["token"]


async def _as_student(request: Request, method: str, path: str, content: Optional[bytes] = None) -> httpx.Response:
    cookie = session_cookie(request)
    res = await _call(method, path, content=content, token=await _grant(cookie), busy=BUSY_ACCOUNT)
    if res.status_code == 401:  # the pass ended early (app server restarted or it was revoked): one new pass, one retry
        res = await _call(method, path, content=content, token=await _grant(cookie, fresh=True), busy=BUSY_ACCOUNT)
    if res.status_code == 401:
        raise HTTPException(401, SIGN_IN, headers={"Cache-Control": "no-store"})
    return res


async def _json_body(request: Request) -> bytes:
    body = await request.body()
    if len(body) > MAX_BODY * 4:
        raise HTTPException(413, "Request too large")
    return body


@router.get("/mission/me")
async def mission_me(request: Request):
    """{code, helped, week, link}: the student's own share link and how many friends opened it (all time / last 7 days)."""
    res = await _as_student(request, "GET", "/rf/mission/me")
    if res.status_code != 200:
        return _relay(res, private=True)
    data = res.json()
    return JSONResponse({**data, "link": f"{SHARE_LINK_BASE}/{data['code']}"}, headers={"Cache-Control": "no-store"})


@router.get("/dream")
async def dream_read(request: Request):
    return _relay(await _as_student(request, "GET", "/rf/dream"), private=True)


@router.put("/dream/dreams")
async def dream_save(request: Request):
    return _relay(await _as_student(request, "PUT", "/rf/dream/dreams", await _json_body(request)), private=True)


@router.post("/dream/mocks")
async def dream_mocks(request: Request):
    return _relay(await _as_student(request, "POST", "/rf/dream/mocks", await _json_body(request)), private=True)


@router.post("/dream/cheered")
async def dream_cheered(request: Request):
    return _relay(await _as_student(request, "POST", "/rf/dream/cheered", await _json_body(request)), private=True)


# ------------------------------------------------------------------ pretty share link (optional)
@router.get("/j/{code}", include_in_schema=False)
async def share_link(code: str):
    """https://<website>/api/j/<code> -> the app server's counter -> the website's home page.
    The friend's own browser makes the second hop, so the app server sees the friend (cookie, address, browser) and
    counts them once. Never fetch the counter from this server: that would count the server, not the friend.
    To use these links, set JEELIVE_SHARE_LINK_BASE=https://<website>/api/j."""
    target = f"{APP_API}/j/{code.upper()}" if CODE.fullmatch(code) else SITE
    return RedirectResponse(target, status_code=302, headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"})
