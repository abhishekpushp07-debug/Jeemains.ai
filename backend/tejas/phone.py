import hashlib
from datetime import datetime, timezone, timedelta
import phonenumbers
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import Field
from starlette.concurrency import run_in_threadpool
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from .db import db, uid, now
from .auth import current, hashpw, new_session, verify
from .documents import BaseDocument
from .request_contracts import PhonePayload, PhoneSignupPayload, PinChangePayload
from .rate_limits import increment

router = APIRouter(prefix="/api/auth", tags=["Student phone and PIN access"])


class PhoneProfile(BaseDocument):
    profile_id: str = Field(alias='id')
    phone: str
    name: str = 'Learner'
    role: str = 'student'
    exam: str = 'JEE Main'
    access_type: str = 'unverified_phone'
    pin_hash: str
    pin_version: int = 1
    created_at: float
    consent_at: float
    last_seen_at: float


def normalize_phone(raw):
    try:
        p = phonenumbers.parse(raw, "IN")
        if not phonenumbers.is_valid_number(p):
            raise ValueError()
        return phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.E164)
    except (phonenumbers.NumberParseException, ValueError):
        raise HTTPException(
            422,
            "Enter a valid mobile number. For international numbers, include + and the country code.",
        )


async def limit_pin(phone, request, action):
    stamp = now()
    window = int(stamp // 900)
    ip = request.client.host if request.client else 'unknown'
    for identity, maximum in [(f'{action}:number:{phone}', 5), (f'pin:ip:{ip}', 60)]:
        key = hashlib.sha256(f'{identity}:{window}'.encode()).hexdigest()
        count = await increment(db.tejas_phone_limits, key, datetime.now(timezone.utc) + timedelta(minutes=30))
        if count > maximum:
            raise HTTPException(429, 'Too many attempts. Please wait before trying again.',
                                headers={'Retry-After': str(max(1, int((window + 1) * 900 - stamp) + 1))})


@router.post('/phone')
async def access(data: PhonePayload, request: Request, response: Response):
    phone = normalize_phone(data.phone)
    await limit_pin(phone, request, 'login')
    u = await db.tejas_phone_profiles.find_one({'phone': phone}, {'_id': 0})
    if not u or not u.get('pin_hash') or not await run_in_threadpool(verify, data.pin, u['pin_hash']):
        raise HTTPException(401, 'Mobile number or PIN is incorrect. Older profiles must set a PIN from their existing signed-in session.')
    await db.tejas_phone_profiles.update_one({'id': u['id']}, {'$set': {'last_seen_at': now()}})
    return await new_session(u, response)


@router.post('/phone/signup')
async def signup(data: PhoneSignupPayload, request: Request, response: Response):
    phone = normalize_phone(data.phone)
    await limit_pin(phone, request, 'signup')
    if await db.tejas_phone_profiles.find_one({'phone': phone}, {'_id': 1}):
        raise HTTPException(409, 'This number already has a profile. Sign in, or set a PIN from its existing signed-in session.')
    stamp = now()
    profile = PhoneProfile.from_mongo({'_id': uid(), 'id': uid(), 'phone': phone,
        'pin_hash': await run_in_threadpool(hashpw, data.pin), 'created_at': stamp,
        'consent_at': stamp, 'last_seen_at': stamp})
    try:
        await db.tejas_phone_profiles.insert_one(profile.to_mongo())
    except DuplicateKeyError:
        raise HTTPException(409, 'This number already has a profile. Sign in instead.')
    return await new_session(profile.model_dump(by_alias=True, exclude={'id', 'pin_hash'}), response)


@router.post('/pin')
async def change_pin(data: PinChangePayload, request: Request, response: Response, u=Depends(current)):
    phone = normalize_phone(data.phone)
    if u.get('access_type') != 'unverified_phone' or phone != u.get('phone'):
        raise HTTPException(403, 'You can change only your own student PIN.')
    await limit_pin(phone, request, 'change')
    version = u.get('pin_version', 0)
    hashed = await run_in_threadpool(hashpw, data.new_pin)
    updated = await db.tejas_phone_profiles.find_one_and_update(
        {'id': u['id'], 'phone': phone, '$expr': {'$eq': [{'$ifNull': ['$pin_version', 0]}, version]}},
        {'$set': {'pin_hash': hashed}, '$inc': {'pin_version': 1}},
        return_document=ReturnDocument.AFTER, projection={'_id': 0, 'pin_hash': 0})
    if not updated:
        raise HTTPException(409, 'Your account changed. Sign in again before changing the PIN.')
    from .db import audit
    await audit(u['id'], 'student_pin_changed', u['id'])
    return await new_session(updated, response)
