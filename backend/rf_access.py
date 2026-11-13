"""Short-lived companion access derived ONLY from a verified canonical session.

No PIN/password storage, no new accounts, no client-asserted identity. Web reuses
the existing proxy SID; native supplies its canonical access cookie after refresh.
"""
import hashlib
import asyncio
import os
import secrets
from datetime import datetime, timedelta, timezone

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse
from starlette.datastructures import Headers, MutableHeaders
from jl_transport import canonical_request

load_dotenv()


def token_digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


async def verified_grant(db, token):
    if not isinstance(token, str) or not token or len(token) > 128:
        raise HTTPException(401, 'Sign in to use Rapid Fire.')
    grant = await db.rf_access.find_one({'digest': token_digest(token), 'expires_at': {'$gt': datetime.now(timezone.utc)}}, {'_id': 0})
    if not grant:
        raise HTTPException(401, 'Rapid Fire session expired. Please reconnect.')
    return grant


class AccessRequest(BaseModel):
    access_cookie: str | None = Field(default=None, max_length=8192)


def make_access_router(db):
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
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                result = await canonical_request(client, 'GET', os.environ['JEELIVE_API'].rstrip('/') + '/auth/me', path='auth/me',
                                                  params=None, body=None, headers={'Cookie': 'access_token=' + cookie, 'Accept': 'application/json'})
            if result.status_code in (401, 403):
                raise HTTPException(401, 'Your canonical session needs refreshing.')
            if not result.is_success:
                raise HTTPException(503, 'Could not verify your session. Please retry.')
            payload = result.json()
            user = payload.get('data') if payload.get('meta', {}).get('api_version') else payload
            uid = user.get('id') if isinstance(user, dict) else None
            if not isinstance(uid, str) or not uid:
                raise HTTPException(401, 'Canonical identity could not be verified.')
        except (httpx.HTTPError, ValueError, asyncio.TimeoutError) as exc:
            raise HTTPException(503, 'Could not verify your session. Please retry.') from exc
        from social import remember_identity
        await remember_identity(db, uid, user)
        token = secrets.token_urlsafe(32)
        expiry = datetime.now(timezone.utc) + timedelta(minutes=15)
        await db.rf_access.insert_one({'digest': token_digest(token), 'uid': uid, 'sid': sid, 'expires_at': expiry})
        return {'token': token, 'user_id': uid, 'expires_at': expiry.isoformat()}

    @router.post('/access/revoke')
    async def revoke(request: Request):
        token = request.headers.get('authorization', '').removeprefix('Bearer ')
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
        if await self.db.rf_maintenance.find_one({'_id': 'portrait-cleanup', 'active': True}):
            response = JSONResponse({'detail': 'Rapid Fire is refreshing its question bank. Please retry shortly.'}, status_code=503, headers={'Retry-After': '15', 'Cache-Control': 'no-store'})
            return await response(scope, receive, send)
        # WhatsApp link pages are public HTML that reveal only a display name, subject and player code.
        public = path in ('/api/rf/catalog', '/api/rf/cards', '/api/rf/access') or path.startswith(('/api/rf/invite/', '/api/rf/c/', '/api/rf/g/'))
        if not public and scope['method'] != 'OPTIONS':
            try:
                grant = await verified_grant(self.db, Headers(scope=scope).get('authorization', '').removeprefix('Bearer '))
            except HTTPException as exc:
                response = JSONResponse({'detail': exc.detail}, status_code=exc.status_code, headers={'Cache-Control': 'no-store'})
                return await response(scope, receive, send)
            scope = {**scope, 'headers': [(k, v) for k, v in scope['headers'] if k.lower() != b'x-rf-user'] + [(b'x-rf-user', grant['uid'].encode())]}

        async def private_send(message):
            # /access issues a token and is uncached too, despite not requiring a grant.
            if message['type'] == 'http.response.start' and path not in ('/api/rf/catalog', '/api/rf/cards'):
                MutableHeaders(scope=message)['Cache-Control'] = 'no-store'
            await send(message)

        await self.app(scope, receive, private_send)


def install_access_guard(app, db):
    app.add_middleware(RFAccessGuard, db=db)