"""Mission share stats: every student gets a personal link for the Mission card caption.

GET /api/rf/mission/me   (signed in, through the Rapid Fire grant) -> {code, helped, week}
GET /api/j/{code}        (public) counts a friend once, then sends them on to https://jeelive.ai

A friend is counted the first time a real browser opens the link: a 1-year visitor cookie plus a hash of
IP + browser, both new for this link. Link-preview robots (WhatsApp, Telegram, Facebook...) are never counted.
No names, numbers or IPs are stored; only the hash.
"""
import hashlib
import re
import secrets
import time
from typing import Optional

from fastapi import APIRouter, Header, Request
from fastapi.responses import RedirectResponse
from pymongo.errors import DuplicateKeyError

from client_ip import client_ip
from jl_track import track_server

SITE = "https://jeelive.ai"
ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # no 0/O, 1/I/L
CODE = re.compile(r"^[A-Z2-9]{7}$")
COOKIE = "jlv"
# Link-preview robots and scripts. "bot" anywhere (Googlebot, TelegramBot, Slackbot, Discordbot...) except CUBOT phones.
BOTS = re.compile(r"(?<!cu)bot|crawl|spider|slurp|preview|whatsapp|facebookexternalhit|"
                  r"curl|wget|python|httpx|aiohttp|go-http|java/|okhttp|headless|lighthouse|embedly|vkshare|"
                  r"bitly|scrapy|postman|insomnia|axios|node-fetch|phantom|selenium|puppeteer|playwright", re.I)
WEEK = 7 * 86400


async def ensure_indexes(db):
    await db.mission_links.create_index("uid", unique=True)
    await db.mission_links.create_index("code", unique=True)
    await db.mission_visits.create_index([("code", 1), ("key", 1)], unique=True)
    await db.mission_visits.create_index([("code", 1), ("counted", 1), ("ts", -1)])


def make_router(db, rf_user):
    r = APIRouter()

    async def link_of(uid: str) -> dict:
        row = await db.mission_links.find_one({"uid": uid})
        while not row:
            code = "".join(secrets.choice(ALPHABET) for _ in range(7))
            try:
                await db.mission_links.insert_one({"uid": uid, "code": code, "helped": 0, "created_ts": time.time()})
                track_server("mission_link_created", uid, {"code": code}, key="mission:" + code)
            except DuplicateKeyError:
                pass  # this code is taken, or a second tab made this student's link at the same moment
            row = await db.mission_links.find_one({"uid": uid})
        return row

    @r.get("/rf/mission/me")
    async def mine(x_rf_user: Optional[str] = Header(None)):
        row = await link_of(rf_user(x_rf_user))
        week = await db.mission_visits.count_documents({"code": row["code"], "counted": True, "ts": {"$gte": time.time() - WEEK}})
        return {"code": row["code"], "helped": row.get("helped", 0), "week": week}

    @r.get("/j/{code}", include_in_schema=False)
    async def open_link(code: str, request: Request):
        code = code.upper()
        visitor = request.cookies.get(COOKIE) or ""
        fresh = not re.fullmatch(r"[A-Za-z0-9_-]{16,64}", visitor)
        if fresh:
            visitor = secrets.token_urlsafe(18)
        # The website learns that the visit came from a Mission link (and whose link) from these three parameters.
        site = f"{SITE}/?utm_source=mission&utm_medium=referral&utm_campaign=mission-{code}" if CODE.fullmatch(code) else SITE
        out = RedirectResponse(site, status_code=302, headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"})
        if fresh:
            out.set_cookie(COOKIE, visitor, max_age=365 * 86400, httponly=True, secure=True, samesite="lax", path="/api/j")
        ua = request.headers.get("user-agent", "")
        if not CODE.fullmatch(code) or not ua or BOTS.search(ua):
            return out  # robots and bad codes still land on the website, uncounted
        link = await db.mission_links.find_one({"code": code}, {"_id": 0, "code": 1, "uid": 1})
        if not link:
            return out
        ip = client_ip(request)
        device = hashlib.sha256(f"{ip}|{ua}".encode()).hexdigest()[:32]
        now = time.time()
        new = []
        for key in ("c:" + visitor, "d:" + device):
            res = await db.mission_visits.update_one({"code": code, "key": key}, {"$setOnInsert": {"ts": now}}, upsert=True)
            new.append(res.upserted_id is not None)
        if all(new):  # a browser this link has never seen: one more friend helped
            await db.mission_visits.update_one({"code": code, "key": "c:" + visitor}, {"$set": {"counted": True}})
            await db.mission_links.update_one({"code": code}, {"$inc": {"helped": 1}})
        # Told about the link's owner only; nothing about the visitor leaves this server.
        track_server("mission_link_opened", link.get("uid", ""), {"code": code, "counted": all(new)})
        return out

    return r
