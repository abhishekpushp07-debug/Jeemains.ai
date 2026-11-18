"""Forgot PIN: mobile number + new PIN + confirm PIN, with no OTP.

This is the site owner's explicit product decision: anyone who knows a number can set its PIN.
The canonical website has no public reset, so this server signs in as the site owner
(JEELIVE_OWNER_EMAIL / JEELIVE_OWNER_PASSWORD, backend env only) and uses the owner-only reset.
Owner credentials and cookies never leave the server; attempts are throttled per number and per IP.
"""
import asyncio
import hashlib
import logging
import os
import re
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from client_ip import client_ip

logger = logging.getLogger("pin_reset")
API = os.environ['JEELIVE_API'].rstrip('/')
PIN = r'^[0-9]{4}$'
LIMITS = (('phone', 5), ('ip', 30))  # reset attempts per hour
UNAVAILABLE = 'PIN reset is unavailable right now. Please try again in a few minutes.'


class ForgotPin(BaseModel):
    model_config = ConfigDict(extra='forbid')
    phone: str = Field(pattern=r'^\+?[0-9]{8,15}$')
    new_pin: str = Field(pattern=PIN)
    confirm_pin: str = Field(pattern=PIN)


def digits(phone: str) -> str:
    """Compare numbers by their last 10 digits so +91 / 0 prefixes still match."""
    return re.sub(r'\D', '', phone or '')[-10:]


def unwrap(response):
    body = response.json()
    return body.get('data') if isinstance(body, dict) and isinstance(body.get('meta'), dict) and body['meta'].get('api_version') else body


class Owner:
    """One signed-in owner session per server process, renewed when the website asks."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(20, connect=5), follow_redirects=False)
        self.lock = asyncio.Lock()
        self.signed_in = False

    async def login(self):
        email, password = os.environ.get('JEELIVE_OWNER_EMAIL'), os.environ.get('JEELIVE_OWNER_PASSWORD')
        if not email or not password:
            raise HTTPException(503, UNAVAILABLE)
        self.client.cookies.clear()
        r = await self.client.post(f'{API}/auth/login', json={'email': email, 'password': password})
        if r.status_code != 200:
            logger.warning("owner_login_failed status=%s", r.status_code)
            raise HTTPException(503, UNAVAILABLE)
        self.signed_in = True

    async def call(self, method: str, path: str, **kwargs):
        for attempt in (0, 1):
            async with self.lock:
                if not self.signed_in:
                    await self.login()
            r = await self.client.request(method, f'{API}/{path}', **kwargs)
            if r.status_code in (401, 403) and attempt == 0:
                self.signed_in = False  # owner session expired: sign in again once
                continue
            return r


def make_pin_reset(db):
    router = APIRouter()
    owner = Owner()

    async def throttle(request: Request, phone: str) -> dict:
        # The rightmost X-Forwarded-For hop is the one our ingress added; earlier ones are caller-controlled.
        ip = client_ip(request)
        keys = {'phone': hashlib.sha256(phone.encode()).hexdigest(), 'ip': hashlib.sha256(ip.encode()).hexdigest()}
        since = datetime.now(timezone.utc) - timedelta(hours=1)
        for kind, limit in LIMITS:
            if await db.pin_resets.count_documents({kind: keys[kind], 'at': {'$gte': since}}) >= limit:
                raise HTTPException(429, 'Too many PIN resets for now. Please try again in an hour.', headers={'Retry-After': '3600'})
        return keys

    @router.post('/account/forgot-pin')
    async def forgot_pin(body: ForgotPin, request: Request):
        if body.new_pin != body.confirm_pin:
            raise HTTPException(422, 'PINs do not match. Please check both fields.')
        number = digits(body.phone)
        keys = await throttle(request, number)

        async def log(result: str):
            await db.pin_resets.insert_one({**keys, 'at': datetime.now(timezone.utc), 'result': result})

        try:
            r = await owner.call('GET', 'admin/students', params={'q': number})
            if r.status_code != 200:
                await log(f'lookup_{r.status_code}')
                raise HTTPException(503, UNAVAILABLE)
            student = next((s for s in (unwrap(r) or {}).get('items') or [] if digits(s.get('phone', '')) == number), None)
            if not student:
                await log('not_found')
                raise HTTPException(404, 'No account uses this number. Create an account instead.')
            if not isinstance(student.get('pin_version'), int) or not student.get('phone'):
                await log('lookup_incomplete')
                raise HTTPException(503, UNAVAILABLE)
            r = await owner.call('POST', 'auth/owner/student-pin-reset', json={
                'phone': student['phone'], 'new_pin': body.new_pin, 'confirm_pin': body.confirm_pin,
                'expected_pin_version': student['pin_version'],
            })
        except httpx.HTTPError:
            await log('unreachable')
            raise HTTPException(503, 'Connection interrupted. Please try again.')
        if r.status_code != 200:
            await log(f'reset_{r.status_code}')
            raise HTTPException(503, UNAVAILABLE)
        await log('reset')
        return {'ok': True}

    return router
