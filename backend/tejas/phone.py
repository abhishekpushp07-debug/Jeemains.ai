import hashlib
import ipaddress
import logging
from datetime import datetime, timezone, timedelta
import phonenumbers
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError, PyMongoError
from .db import audit, db, uid, now
from .auth import current, hashpw, new_session, owner, verify
from .documents import BaseDocument
from .request_contracts import PhonePayload, PhoneSignupPayload, PinChangePayload, OwnerPinResetPayload
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
    checks = []
    try:
        peer = ipaddress.ip_address(request.client.host) if request.client else None
    except ValueError:
        peer = None
    if peer and peer.is_global:
        checks.append((f'pin:ip:{peer.compressed}', 60))
    checks.append((f'{action}:number:{phone}', 5))
    account_key = hashlib.sha256(f'{action}:number:{phone}:{window}'.encode()).hexdigest()
    for identity, maximum in checks:
        key = hashlib.sha256(f'{identity}:{window}'.encode()).hexdigest()
        count = await increment(db.tejas_phone_limits, key, datetime.now(timezone.utc) + timedelta(minutes=30))
        if count > maximum:
            raise HTTPException(429, 'Too many attempts. Please wait before trying again.',
                                headers={'Retry-After': str(max(1, int((window + 1) * 900 - stamp) + 1))})
    return account_key


@router.post('/phone')
async def access(data: PhonePayload, request: Request, response: Response):
    phone = normalize_phone(data.phone)
    limit_key = await limit_pin(phone, request, 'login')
    u = await db.tejas_phone_profiles.find_one({'phone': phone}, {'_id': 0})
    stamp = now()
    hour = int(stamp // 3600)
    budget_key = hashlib.sha256(f'pin:failed-hour:{phone}:{hour}'.encode()).hexdigest()
    reserved = await increment(db.tejas_phone_limits, budget_key, datetime.now(timezone.utc) + timedelta(hours=2))
    if reserved > 20:
        await db.tejas_phone_limits.update_one({'_id': budget_key, 'count': {'$gt': 0}}, {'$inc': {'count': -1}})
        raise HTTPException(429, 'Too many incorrect PIN attempts. Please wait before signing in again.',
                            headers={'Retry-After': str(max(1, int((hour + 1) * 3600 - stamp) + 1))})
    if not u or not u.get('pin_hash') or not await run_in_threadpool(verify, data.pin, u['pin_hash']):
        raise HTTPException(401, 'Mobile number or PIN is incorrect. Older profiles must set a PIN from their existing signed-in session.')
    await db.tejas_phone_limits.update_one({'_id': budget_key, 'count': {'$gt': 0}}, {'$inc': {'count': -1}})
    await db.tejas_phone_profiles.update_one({'id': u['id']}, {'$set': {'last_seen_at': now()}})
    result = await new_session({**u, 'role': 'student', 'access_type': 'unverified_phone'}, response)
    await db.tejas_phone_limits.delete_one({'_id': limit_key})
    return result


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
    result = await new_session({**updated, 'role': 'student', 'access_type': 'unverified_phone'}, response)
    try:
        await db.tejas_sessions.delete_many({'user_id': u['id'], 'access_type': 'unverified_phone', '$or': [
            {'pin_version': {'$lt': updated['pin_version']}}, {'pin_version': {'$exists': False}}]})
    except PyMongoError:
        logging.getLogger(__name__).warning('Stale PIN sessions remain fenced; physical cleanup deferred to expiry.')
    return result


class OwnerPinResetReceipt(BaseModel):
    ok: bool = True
    student_id: str
    pin_version: int
    old_sessions_revoked: bool = True


@router.post('/owner/student-pin-reset', response_model=OwnerPinResetReceipt)
async def owner_reset_pin(data: OwnerPinResetPayload, response: Response, u=Depends(owner)):
    response.headers['Cache-Control'] = 'private, no-store'
    phone = normalize_phone(data.phone)
    stamp = now()
    window = int(stamp // 900)
    for scope, identity, maximum in [('actor', u['id'], 10), ('target', phone, 5)]:
        key = hashlib.sha256(f'owner-pin-reset:{scope}:{identity}:{window}'.encode()).hexdigest()
        count = await increment(db.tejas_phone_limits, key, datetime.now(timezone.utc) + timedelta(minutes=30))
        if count > maximum:
            raise HTTPException(429, 'Too many PIN resets. Please wait before trying again.',
                                headers={'Retry-After': str(max(1, int((window + 1) * 900 - stamp) + 1))})
    hashed = await run_in_threadpool(hashpw, data.new_pin)
    updated = await db.tejas_phone_profiles.find_one_and_update(
        {'phone': phone, 'role': {'$in': ['student', None]}, 'access_type': {'$in': ['unverified_phone', None]},
         '$expr': {'$eq': [{'$ifNull': ['$pin_version', 0]}, data.expected_pin_version]}},
        {'$set': {'pin_hash': hashed, 'pin_reset_by': u['id'], 'pin_reset_at': stamp}, '$inc': {'pin_version': 1}},
        return_document=ReturnDocument.AFTER, projection={'_id': 0, 'id': 1, 'pin_version': 1})
    if not updated:
        raise HTTPException(409, 'Student changed or is not resettable. Refresh the student list before trying again.')
    try:
        await audit(u['id'], 'owner_student_pin_reset', updated['id'], f"pin_version={updated['pin_version']}")
    except PyMongoError:
        logging.getLogger(__name__).warning('PIN reset audit retained on profile; central audit delivery failed.')
    try:
        await db.tejas_sessions.delete_many({'user_id': updated['id'], 'access_type': 'unverified_phone', '$or': [
            {'pin_version': {'$lt': updated['pin_version']}}, {'pin_version': {'$exists': False}}]})
    except PyMongoError:
        logging.getLogger(__name__).warning('Reset student sessions remain version-fenced; physical cleanup deferred to expiry.')
    return OwnerPinResetReceipt(student_id=updated['id'], pin_version=updated['pin_version'])
