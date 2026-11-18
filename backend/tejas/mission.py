"""Mission share stats: every student gets a personal link for the Mission card caption.

GET /api/mission/me  (signed in) -> {code, helped, week}
GET /api/j/{code}    (public) counts a friend once, then sends them on to the website home.

A friend counts the first time a real browser opens the link: a 1-year visitor cookie plus a hash of IP + browser,
both new for this link. Link-preview robots (WhatsApp, Telegram, Facebook...) never count. Only the hash is stored.
"""
import hashlib
import re
import secrets
import time
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from pymongo.errors import DuplicateKeyError
from .auth import current
from .db import db
from .phone import client_ip

router = APIRouter(prefix='/api', tags=['Mission'])
links, visits = db.tejas_mission_links, db.tejas_mission_visits
ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
CODE = re.compile(r'^[A-Z2-9]{7}$')
COOKIE = 'jlv'
BOTS = re.compile(r'(?<!cu)bot|crawl|spider|slurp|preview|whatsapp|facebookexternalhit|'
                  r'curl|wget|python|httpx|aiohttp|go-http|java/|okhttp|headless|lighthouse|embedly|vkshare|'
                  r'bitly|scrapy|postman|insomnia|axios|node-fetch|phantom|selenium|puppeteer|playwright', re.I)
WEEK = 7 * 86400


async def link_of(uid):
    row = await links.find_one({'uid': uid})
    while not row:
        code = ''.join(secrets.choice(ALPHABET) for _ in range(7))
        try:
            await links.insert_one({'uid': uid, 'code': code, 'helped': 0, 'created_ts': time.time()})
        except DuplicateKeyError:
            pass
        row = await links.find_one({'uid': uid})
    return row


@router.get('/mission/me')
async def mine(u=Depends(current)):
    row = await link_of(u['id'])
    week = await visits.count_documents({'code': row['code'], 'counted': True, 'ts': {'$gte': time.time() - WEEK}})
    return {'code': row['code'], 'helped': row.get('helped', 0), 'week': week}


@router.get('/j/{code}', include_in_schema=False)
async def open_link(code: str, request: Request):
    code = code.upper()
    visitor = request.cookies.get(COOKIE) or ''
    fresh = not re.fullmatch(r'[A-Za-z0-9_-]{16,64}', visitor)
    if fresh:
        visitor = secrets.token_urlsafe(18)
    out = RedirectResponse('/', status_code=302, headers={'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer'})
    if fresh:
        out.set_cookie(COOKIE, visitor, max_age=365 * 86400, httponly=True, secure=True, samesite='lax', path='/api/j')
    ua = request.headers.get('user-agent', '')
    if not CODE.fullmatch(code) or not ua or BOTS.search(ua):
        return out
    if not await links.find_one({'code': code}, {'_id': 0, 'code': 1}):
        return out
    device = hashlib.sha256(f'{client_ip(request) or ""}|{ua}'.encode()).hexdigest()[:32]
    stamp = time.time()
    new = []
    for key in ('c:' + visitor, 'd:' + device):
        res = await visits.update_one({'code': code, 'key': key}, {'$setOnInsert': {'ts': stamp}}, upsert=True)
        new.append(res.upserted_id is not None)
    if all(new):
        await visits.update_one({'code': code, 'key': 'c:' + visitor}, {'$set': {'counted': True}})
        await links.update_one({'code': code}, {'$inc': {'helped': 1}})
    return out
