"""Website <-> JEELIVE.AI app server connector (Rank + Mission + Dream college), from the app team's hand-off pack.

All college data and every Rank answer, Mission count and Dream list live on the app server; this file only forwards
(whitelisted paths, status and JSON word for word). Website adaptations:
- signed-in routes first check the website's own session (`current`), so a not-signed-in student gets our normal 401;
  an app-server refusal becomes a 503 "try again" and never signs the student out of the website;
- GET /api/dream first sends the student's released full mocks from this website, so the meter measures them too.
"""
import hashlib
import os
import re
import time
from collections import OrderedDict
from datetime import datetime
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response
from pydantic import BaseModel, ConfigDict

from .auth import current
from .dreams import website_mocks

APP_API = os.environ["JEELIVE_APP_API"].rstrip("/")
SHARE_LINK_BASE = (os.environ.get("JEELIVE_SHARE_LINK_BASE") or f"{APP_API}/j").rstrip("/")
SITE = os.environ["JEELIVE_SITE_URL"]
SESSION_COOKIE = "access_token"

RANK_GET = {"meta", "colleges", "target/bitsat"}
RANK_POST = {"estimate", "percentile", "predict", "college", "bitsat", "comedk", "comedk/college",
             "target/jee", "target/comedk", "compare", "compare/colleges"}
RANK_PDF = {"pdf/jee", "pdf/comedk", "pdf/bitsat", "pdf/target/jee", "pdf/target/comedk", "pdf/target/bitsat", "pdf/saved"}

STATIC_TTL = 600
MAX_BODY = 16 * 1024
GRANT_MEMORY = 50_000
BUSY = "Rank abhi load nahi hua. Retry dabao."
BUSY_ACCOUNT = "Abhi load nahi hua. Thodi der mein dobara try karo."
CODE = re.compile(r"^[A-Za-z2-9]{7}$")
NO_STORE = {"Cache-Control": "no-store"}

router = APIRouter(prefix="/api", tags=["JEELIVE app server"])
_http: Optional[httpx.AsyncClient] = None
_static: dict = {}
_grants: OrderedDict = OrderedDict()
_sent_mocks: OrderedDict = OrderedDict()
MOCK_RECHECK, MOCK_RESEND = 30, 600


class PassThrough(BaseModel):
    """Bodies are checked by the app server itself (its 422 sentences reach the page word for word)."""
    model_config = ConfigDict(extra="allow")


def http() -> httpx.AsyncClient:
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
    headers = {"Content-Type": "application/json"} if content is not None else {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        res = await http().request(method, APP_API + path, content=content, json=json, headers=headers,
                                   **({"timeout": timeout} if timeout else {}))
    except httpx.HTTPError as exc:
        raise HTTPException(503, busy, headers={"Retry-After": "5", **NO_STORE}) from exc
    if res.status_code >= 500:
        raise HTTPException(503, busy, headers={"Retry-After": res.headers.get("retry-after", "5"), **NO_STORE})
    return res


def _relay(res: httpx.Response, private: bool = False) -> Response:
    return Response(res.content, status_code=res.status_code, media_type=res.headers.get("content-type", "application/json"),
                    headers=NO_STORE if private else None)


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
        return Response(res.content, media_type="application/pdf", headers={"Content-Disposition": name, **NO_STORE})
    return _relay(await _call("POST", f"/rank/{path}", content=body))


# ------------------------------------------------------------------ signed-in student (Mission, Dream college)
def _cookie(request: Request) -> str:
    value = request.cookies.get(SESSION_COOKIE, "")
    if not value or any(c in value for c in "\r\n;"):
        raise HTTPException(503, BUSY_ACCOUNT, headers=NO_STORE)
    return value


async def _grant(cookie: str, fresh: bool = False) -> str:
    key = hashlib.sha256(cookie.encode()).hexdigest()
    hit = _grants.get(key)
    if hit and not fresh and hit[1] > time.time() + 60:
        return hit[0]
    res = await _call("POST", "/rf/access", json={"access_cookie": cookie}, busy=BUSY_ACCOUNT)
    if res.status_code != 200:
        _grants.pop(key, None)
        raise HTTPException(503, BUSY_ACCOUNT, headers={"Retry-After": "5", **NO_STORE})
    try:
        data = res.json()
        token, until = data["token"], datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00")).timestamp()
        if not isinstance(token, str) or not token:
            raise ValueError("empty token")
    except (ValueError, KeyError, TypeError, AttributeError):
        raise HTTPException(503, BUSY_ACCOUNT, headers={"Retry-After": "5", **NO_STORE})
    _grants[key] = (token, until)
    _grants.move_to_end(key)
    while len(_grants) > GRANT_MEMORY:
        _grants.popitem(last=False)
    return token


async def _as_student(request: Request, method: str, path: str, content: Optional[bytes] = None) -> httpx.Response:
    cookie = _cookie(request)
    res = await _call(method, path, content=content, token=await _grant(cookie), busy=BUSY_ACCOUNT)
    if res.status_code == 401:
        res = await _call(method, path, content=content, token=await _grant(cookie, fresh=True), busy=BUSY_ACCOUNT)
    if res.status_code == 401:
        raise HTTPException(503, BUSY_ACCOUNT, headers=NO_STORE)
    return res


async def _json_body(request: Request) -> bytes:
    body = await request.body()
    if len(body) > MAX_BODY * 4:
        raise HTTPException(413, "Request too large")
    return body


async def _send_website_mocks(request: Request, uid: str):
    """Released full mocks taken on this website join the account's list on the app server (same id = replaced)."""
    now, hit = time.time(), _sent_mocks.get(uid)
    if hit and now - hit[1] < MOCK_RECHECK:
        return
    mocks = await website_mocks(uid)
    digest = hashlib.sha256(repr([(m["id"], m["score"]) for m in mocks]).encode()).hexdigest()
    if not mocks or (hit and hit[0] == digest and now - hit[2] < MOCK_RESEND):
        _remember_mocks(uid, (digest, now, hit[2] if hit and hit[0] == digest else now))
        return
    import json
    _remember_mocks(uid, (digest, now, 0))
    res = await _as_student(request, "POST", "/rf/dream/mocks", json.dumps({"mocks": mocks}).encode())
    if res.status_code == 200:
        _remember_mocks(uid, (digest, now, now))


def _remember_mocks(uid: str, entry: tuple):
    _sent_mocks[uid] = entry
    _sent_mocks.move_to_end(uid)
    while len(_sent_mocks) > GRANT_MEMORY:
        _sent_mocks.popitem(last=False)


@router.get("/mission/me")
async def mission_me(request: Request, u=Depends(current)):
    res = await _as_student(request, "GET", "/rf/mission/me")
    if res.status_code != 200:
        return _relay(res, private=True)
    try:
        data = res.json()
        code = data["code"]
        if not isinstance(code, str) or not code:
            raise ValueError("empty code")
    except (ValueError, KeyError, TypeError):
        raise HTTPException(503, BUSY_ACCOUNT, headers=NO_STORE)
    return JSONResponse({**data, "link": f"{SHARE_LINK_BASE}/{code}"}, headers=NO_STORE)


@router.get("/dream")
async def dream_read(request: Request, u=Depends(current)):
    try:
        await _send_website_mocks(request, u["id"])
    except HTTPException:
        pass
    return _relay(await _as_student(request, "GET", "/rf/dream"), private=True)


@router.put("/dream/dreams")
async def dream_save(request: Request, u=Depends(current)):
    return _relay(await _as_student(request, "PUT", "/rf/dream/dreams", await _json_body(request)), private=True)


@router.post("/dream/mocks")
async def dream_mocks(request: Request, u=Depends(current)):
    return _relay(await _as_student(request, "POST", "/rf/dream/mocks", await _json_body(request)), private=True)


@router.post("/dream/cheered")
async def dream_cheered(request: Request, u=Depends(current)):
    return _relay(await _as_student(request, "POST", "/rf/dream/cheered", await _json_body(request)), private=True)


# ------------------------------------------------------------------ pretty share link (redirect only, never fetched here)
@router.get("/j/{code}", include_in_schema=False)
async def share_link(code: str):
    target = f"{APP_API}/j/{code.upper()}" if CODE.fullmatch(code) else SITE
    return RedirectResponse(target, status_code=302, headers={**NO_STORE, "Referrer-Policy": "no-referrer"})
