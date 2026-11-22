"""Short-lived companion access derived ONLY from a verified canonical session.

No PIN/password storage, no new accounts, no client-asserted identity. Web reuses
the existing proxy SID; native supplies its canonical access cookie after refresh.
"""
import hashlib
import os
import re
import secrets
import time
from collections import OrderedDict
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse
from starlette.datastructures import Headers, MutableHeaders
from jl_transport import UpstreamError, canonical_request
from load_guard import BACKGROUND_RETRY, BUSY_TEXT, background_look, load, player_allowed, shed_background

load_dotenv()

SLOW_DOWN = 'Too many requests at once. Please wait a moment.'
# Website down (Phase 3, Level 7): a session the website verified in the last TRUST_HOURS can still get Rapid Fire
# grants while the website cannot answer. Keyed by a hash of the device handle (web) or of the access cookie (phone);
# never extended without the website (only a real verification renews it); erased with the account.
TRUST_HOURS = 6


def trust_key(sid: str, cookie: str) -> str:
    return hashlib.sha256((("sid:" + sid) if sid else ("cookie:" + cookie)).encode()).hexdigest()


def token_digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


# Every Rapid Fire request carries a grant. Checking Mongo each time costs one read per request, so a verified grant is
# remembered in this process for GRANT_RECHECK seconds (never past its own expiry). Revoking drops it here at once;
# another server process may honour a revoked grant for at most GRANT_RECHECK seconds.
GRANT_RECHECK, GRANT_MEMORY = 30, 200_000
_grants: OrderedDict = OrderedDict()
_maintenance = {"at": -1e9, "on": False}


def _expires(grant):
    return grant['expires_at'].replace(tzinfo=timezone.utc)


async def verified_grant(db, token):
    if not isinstance(token, str) or not token or len(token) > 128:
        raise HTTPException(401, 'Sign in to use Rapid Fire.')
    digest, now = token_digest(token), datetime.now(timezone.utc)
    hit = _grants.get(digest)
    if hit and time.monotonic() - hit[1] < GRANT_RECHECK and _expires(hit[0]) > now:
        return hit[0]
    grant = await db.rf_access.find_one({'digest': digest, 'expires_at': {'$gt': now}}, {'_id': 0})
    if not grant:
        _grants.pop(digest, None)
        raise HTTPException(401, 'Rapid Fire session expired. Please reconnect.')
    _grants[digest] = (grant, time.monotonic())
    _grants.move_to_end(digest)
    while len(_grants) > GRANT_MEMORY:
        _grants.popitem(last=False)
    return grant


def forget_grants(uid):
    """Account deleted: this process stops honouring the player's grants at once (others within GRANT_RECHECK)."""
    for digest in [d for d, (grant, _) in _grants.items() if grant.get('uid') == uid]:
        _grants.pop(digest, None)


async def maintenance_on(db) -> bool:
    """The question-bank refresh switch, read from Mongo at most every 5 seconds per process."""
    if time.monotonic() - _maintenance["at"] > 5:
        _maintenance["on"] = bool(await db.rf_maintenance.find_one({'_id': 'portrait-cleanup', 'active': True}, {'_id': 1}))
        _maintenance["at"] = time.monotonic()
    return _maintenance["on"]


class AccessRequest(BaseModel):
    access_cookie: str | None = Field(default=None, max_length=8192)


def make_access_router(db, client):
    """`client` returns the server's shared canonical HTTP client (pooled connections, no TLS handshake per sign-in)."""
    router = APIRouter(prefix='/rf')

    @router.post('/access')
    async def access(data: AccessRequest, request: Request):
        sid = request.headers.get('x-jl-sid', '')
        if sid:
            jar = await db.jl_jars.find_one({'sid': sid}, {'_id': 0, 'cookies': 1})
            cookies = (jar or {}).get('cookies', {})
            cookie = cookies.get('access_token')
        else:
            cookie = data.access_cookie
        if not cookie or '\r' in cookie or '\n' in cookie or ';' in cookie:
            raise HTTPException(401, 'Your canonical session needs refreshing.')
        key = trust_key(sid, cookie)
        user = None
        try:
            result = await canonical_request(client(), 'GET', os.environ['JEELIVE_API'].rstrip('/') + '/auth/me', path='auth/me',
                                              params=None, body=None, headers={'Cookie': 'access_token=' + cookie, 'Accept': 'application/json'})
            if result.status_code in (401, 403):
                raise HTTPException(401, 'Your canonical session needs refreshing.')
            if result.status_code < 500 and not result.is_success:  # the website answered: this is not an outage
                raise HTTPException(503, 'Could not verify your session. Please retry.')
            if result.is_success:
                payload = result.json()
                user = payload.get('data') if payload.get('meta', {}).get('api_version') else payload
                uid = user.get('id') if isinstance(user, dict) else None
                if not isinstance(uid, str) or not uid:
                    raise HTTPException(401, 'Canonical identity could not be verified.')
        except (*UpstreamError, ValueError):
            user = None
        if user is None:
            # The website is down or answered with its own trouble: this same session (same device handle, or the same
            # access cookie) was verified by the website in the last TRUST_HOURS, so Rapid Fire keeps playing.
            trust = await db.rf_trust.find_one({'_id': key, 'until': {'$gt': datetime.now(timezone.utc)}}, {'_id': 0, 'uid': 1})
            if not trust:
                raise HTTPException(503, 'Could not verify your session. Please retry.')
            uid = trust['uid']
        from account_deletion import PENDING_MESSAGE, pending
        if await pending(db, uid):
            raise HTTPException(403, PENDING_MESSAGE)
        if user is not None:
            from social import remember_identity
            await remember_identity(db, uid, user)
            if sid:  # the jar knows whose it is, so deleting the account can sign this device out
                await db.jl_jars.update_one({'sid': sid, 'uid': {'$ne': uid}}, {'$set': {'uid': uid}})
            now = datetime.now(timezone.utc)
            await db.rf_trust.update_one({'_id': key}, {'$set': {'uid': uid, 'verified_at': now, 'until': now + timedelta(hours=TRUST_HOURS)}}, upsert=True)
        token = secrets.token_urlsafe(32)
        expiry = datetime.now(timezone.utc) + timedelta(minutes=15)
        await db.rf_access.insert_one({'digest': token_digest(token), 'uid': uid, 'sid': sid, 'expires_at': expiry, **({} if user is not None else {'trusted': True})})
        return {'token': token, 'user_id': uid, 'expires_at': expiry.isoformat()}

    @router.post('/access/revoke')
    async def revoke(request: Request):
        token = request.headers.get('authorization', '').removeprefix('Bearer ')
        _grants.pop(token_digest(token), None)
        await db.rf_access.delete_one({'digest': token_digest(token)})
        return {'ok': True}

    return router


class RFAccessGuard:
    """Same authorization, pure ASGI: no streaming/task wrapper around every response."""
    def __init__(self, app, db):
        self.app, self.db = app, db

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        path = scope.get('path', '').rstrip('/')
        if not path.startswith('/api/rf/'):
            return await self.app(scope, receive, send)
        if await maintenance_on(self.db):
            response = JSONResponse({'detail': 'Rapid Fire is refreshing its question bank. Please retry shortly.'}, status_code=503, headers={'Retry-After': '15', 'Cache-Control': 'no-store'})
            return await response(scope, receive, send)
        # WhatsApp link pages are public HTML that reveal only a display name, subject and player code.
        public = path in ('/api/rf/catalog', '/api/rf/cards', '/api/rf/access') or path.startswith(('/api/rf/invite/', '/api/rf/c/', '/api/rf/g/', '/api/rf/art/'))
        if not public and scope['method'] != 'OPTIONS':
            try:
                grant = await verified_grant(self.db, Headers(scope=scope).get('authorization', '').removeprefix('Bearer '))
            except HTTPException as exc:
                response = JSONResponse({'detail': exc.detail}, status_code=exc.status_code, headers={'Cache-Control': 'no-store'})
                return await response(scope, receive, send)
            if not player_allowed(grant['uid']):
                response = JSONResponse({'detail': SLOW_DOWN, 'code': 'slow_down'}, status_code=429, headers={'Retry-After': '2', 'Cache-Control': 'no-store'})
                return await response(scope, receive, send)
            # Changed in place (not a copy): the App Health counter reads the matched route from this same scope.
            scope['headers'] = [(k, v) for k, v in scope['headers'] if k.lower() != b'x-rf-user'] + [(b'x-rf-user', grant['uid'].encode())]
        background = background_look(scope['method'], path)
        if background:
            if shed_background():
                response = JSONResponse({'detail': BUSY_TEXT, 'code': 'arena_busy'}, status_code=503, headers={'Retry-After': str(BACKGROUND_RETRY), 'Cache-Control': 'no-store'})
                return await response(scope, receive, send)
            load.background += 1

        async def private_send(message):
            # /access issues a token and is uncached too, despite not requiring a grant.
            if message['type'] == 'http.response.start' and path not in ('/api/rf/catalog', '/api/rf/cards') and not path.startswith('/api/rf/art/'):
                MutableHeaders(scope=message)['Cache-Control'] = 'no-store'
            await send(message)

        try:
            await self.app(scope, receive, private_send)
        finally:
            if background:
                load.background -= 1


def install_access_guard(app, db):
    app.add_middleware(RFAccessGuard, db=db)


def rf_user(x_rf_user: str | None) -> str:
    """The player id the guard above wrote into X-RF-User from a verified grant (anything the phone sent is replaced)."""
    if not x_rf_user or not re.match(r"^[A-Za-z0-9-]{8,64}$", x_rf_user):
        raise HTTPException(401, "Sign in to use Rapid Fire.")
    return x_rf_user