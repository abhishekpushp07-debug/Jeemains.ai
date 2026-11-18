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
from .auth import current, forget_student, hash_pin, new_session, owner, pin_hash_heavy, verify
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


CLOUDFLARE = [ipaddress.ip_network(n) for n in (
    '173.245.48.0/20', '103.21.244.0/22', '103.22.200.0/22', '103.31.4.0/22', '141.101.64.0/18', '108.162.192.0/18',
    '190.93.240.0/20', '188.114.96.0/20', '197.234.240.0/22', '198.41.128.0/17', '162.158.0.0/15', '104.16.0.0/13',
    '104.24.0.0/14', '172.64.0.0/13', '131.0.72.0/22', '2400:cb00::/32', '2606:4700::/32', '2803:f800::/32',
    '2405:b500::/32', '2405:8100::/32', '2a06:98c0::/29', '2c0f:f248::/32')]
WRONG_PIN_LIMIT, IP_WRONG_PIN_LIMIT, WRONG_PIN_WAIT = 10, 100, 900


def _ip(raw):
    try:
        return ipaddress.ip_address(raw.strip())
    except ValueError:
        return None


def _cloudflare(ip):
    return any(ip in n for n in CLOUDFLARE if n.version == ip.version)


def client_ip(request):
    """The student's own address. The edge sends X-Forwarded-For as '<anything the client typed>, student, Cloudflare, load balancer',
    so the student is the hop just left of the last Cloudflare hop. Anything left of that can be typed by the client and is ignored.
    None when it cannot be told safely: then only the per-number limit applies, never one shared proxy address for everyone."""
    header = request.headers.get('x-forwarded-for')
    if not header:
        peer = _ip(request.client.host) if request.client else None
        return peer.compressed if peer and peer.is_global else None
    hops = [_ip(h) for h in header.split(',')]
    edge = max((i for i, ip in enumerate(hops) if ip and _cloudflare(ip)), default=None)
    while edge is not None and edge > 0 and hops[edge - 1] and _cloudflare(hops[edge - 1]):
        edge -= 1
    student = hops[edge - 1] if edge else None
    return student.compressed if student and student.is_global else None


def _wrong_pin_keys(phone, request):
    keys = [(hashlib.sha256(f'pin-wrong:number:{phone}'.encode()).hexdigest(), WRONG_PIN_LIMIT)]
    ip = client_ip(request)
    if ip:
        keys.append((hashlib.sha256(f'pin-wrong:ip:{ip}'.encode()).hexdigest(), IP_WRONG_PIN_LIMIT))
    return keys


async def wrong_pin_gate(keys):
    """429 while this number (or this address) is in its 15-minute wait. Correct PINs are never counted."""
    t = datetime.fromtimestamp(now(), timezone.utc)
    try:
        blocked = await db.tejas_phone_limits.find({'_id': {'$in': [k for k, _ in keys]}, 'blocked_until': {'$gt': t}},
                                                   {'blocked_until': 1}).to_list(len(keys))
    except PyMongoError:
        raise HTTPException(503, 'Sign-in protection is temporarily unavailable. Retry shortly.', headers={'Retry-After': '3'})
    if blocked:
        wait = max(1, int((max(d['blocked_until'] for d in blocked) - t).total_seconds()) + 1)
        raise HTTPException(429, f'Too many incorrect PINs. Try again in {max(1, round(wait / 60))} min, or use Forgot PIN.',
                            headers={'Retry-After': str(wait)})


async def count_wrong_pin(keys):
    """One wrong PIN. 10 wrong for a number (100 for one address) within 15 minutes of the first starts a 15-minute wait.
    Returns how many tries this number has left before the wait."""
    t = datetime.fromtimestamp(now(), timezone.utc)
    fresh = {'$lt': [{'$ifNull': ['$started', datetime.fromtimestamp(0, timezone.utc)]}, t - timedelta(seconds=WRONG_PIN_WAIT)]}
    left = None
    try:
        for key, limit in keys:
            doc = await db.tejas_phone_limits.find_one_and_update({'_id': key}, [{'$set': {
                'count': {'$cond': [fresh, 1, {'$add': ['$count', 1]}]}, 'started': {'$cond': [fresh, t, '$started']},
                'expires_at': t + timedelta(seconds=2 * WRONG_PIN_WAIT)}}], upsert=True, return_document=ReturnDocument.AFTER)
            if doc['count'] >= limit:
                await db.tejas_phone_limits.update_one({'_id': key}, {'$set': {'blocked_until': t + timedelta(seconds=WRONG_PIN_WAIT), 'count': 0},
                                                                     '$unset': {'started': ''}})
            if left is None:
                left = max(0, limit - doc['count'])
    except PyMongoError:
        raise HTTPException(503, 'Sign-in protection is temporarily unavailable. Retry shortly.', headers={'Retry-After': '3'})
    return left


async def limit_pin(phone, request, action):
    stamp = now()
    window = int(stamp // 900)
    checks = []
    ip = client_ip(request)
    if ip:
        checks.append((f'pin:ip:{ip}', 60))
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
    keys = _wrong_pin_keys(phone, request)
    await wrong_pin_gate(keys)
    u = await db.tejas_phone_profiles.find_one({'phone': phone}, {'_id': 0})
    if not u or not u.get('pin_hash') or not await run_in_threadpool(verify, data.pin, u['pin_hash']):
        left = await count_wrong_pin(keys)
        if not left:
            raise HTTPException(429, f'Too many incorrect PINs. Try again in {WRONG_PIN_WAIT // 60} min, or use Forgot PIN.',
                                headers={'Retry-After': str(WRONG_PIN_WAIT)})
        raise HTTPException(401, f'Mobile number or PIN is incorrect. {left} {"try" if left == 1 else "tries"} left before a '
                                 f'{WRONG_PIN_WAIT // 60}-minute wait. Forgot your PIN? Use Forgot PIN to set a new one.')
    change = {'last_seen_at': now()}
    if pin_hash_heavy(u['pin_hash']):
        change['pin_hash'] = await run_in_threadpool(hash_pin, data.pin)
    await db.tejas_phone_profiles.update_one({'id': u['id'], 'pin_hash': u['pin_hash']}, {'$set': change})
    result = await new_session({**u, 'role': 'student', 'access_type': 'unverified_phone'}, response)
    await db.tejas_phone_limits.delete_one({'_id': keys[0][0]})
    return result


@router.post('/phone/signup')
async def signup(data: PhoneSignupPayload, request: Request, response: Response):
    phone = normalize_phone(data.phone)
    await limit_pin(phone, request, 'signup')
    if await db.tejas_phone_profiles.find_one({'phone': phone}, {'_id': 1}):
        raise HTTPException(409, 'This number already has an account. Sign in, or use Forgot PIN to set a new PIN.')
    stamp = now()
    pid = uid()
    profile = PhoneProfile.from_mongo({'_id': pid, 'id': pid, 'phone': phone,
        'pin_hash': await run_in_threadpool(hash_pin, data.pin), 'created_at': stamp,
        'consent_at': stamp, 'last_seen_at': stamp})
    try:
        await db.tejas_phone_profiles.insert_one(profile.to_mongo())
    except DuplicateKeyError:
        raise HTTPException(409, 'This number already has a profile. Sign in instead.')
    return await new_session(profile.model_dump(by_alias=True, exclude={'id', 'pin_hash'}), response)


async def replace_pin(u, phone, new_pin, response, action, extra=None):
    """New PIN, a fresh session here, every other session of this student signed out. Saved work stays."""
    version = u.get('pin_version', 0)
    hashed = await run_in_threadpool(hash_pin, new_pin)
    updated = await db.tejas_phone_profiles.find_one_and_update(
        {'id': u['id'], 'phone': phone, '$expr': {'$eq': [{'$ifNull': ['$pin_version', 0]}, version]}},
        {'$set': {'pin_hash': hashed, **(extra or {})}, '$inc': {'pin_version': 1}},
        return_document=ReturnDocument.AFTER, projection={'_id': 0, 'pin_hash': 0})
    if not updated:
        raise HTTPException(409, 'This PIN was changed a moment ago. Try again.')
    forget_student(user_id=u['id'])
    await audit(u['id'], action, u['id'])
    result = await new_session({**updated, 'role': 'student', 'access_type': 'unverified_phone'}, response)
    try:
        await db.tejas_sessions.delete_many({'user_id': u['id'], 'access_type': 'unverified_phone', '$or': [
            {'pin_version': {'$lt': updated['pin_version']}}, {'pin_version': {'$exists': False}}]})
    except PyMongoError:
        logging.getLogger(__name__).warning('Stale PIN sessions remain fenced; physical cleanup deferred to expiry.')
    return result


async def live_paper_guard(user_id, what):
    """No PIN change while this student's live ranked paper (series day or live exam) is running."""
    from .canonical import database_now
    t = await database_now()
    if await db.tejas_attempts.find_one({'user_id': user_id, 'status': 'active', 'competition_end': {'$gt': t},
                                         '$or': [{'deadline': 0}, {'deadline': {'$gt': t}}]}, {'_id': 1}):
        raise HTTPException(409, f'A live ranked paper is running on this number. {what} works again after that paper ends.')


@router.post('/pin')
async def change_pin(data: PinChangePayload, request: Request, response: Response, u=Depends(current)):
    phone = normalize_phone(data.phone)
    if u.get('access_type') != 'unverified_phone' or phone != u.get('phone'):
        raise HTTPException(403, 'You can change only your own student PIN.')
    await limit_pin(phone, request, 'change')
    await live_paper_guard(u['id'], 'PIN change')
    return await replace_pin(u, phone, data.new_pin, response, 'student_pin_changed')


@router.post('/pin/reset')
async def reset_pin(data: PinChangePayload, request: Request, response: Response):
    """Forgot PIN: number + new PIN, no OTP and no old PIN (owner's choice). Signs the student in like sign-in does."""
    phone = normalize_phone(data.phone)
    await limit_pin(phone, request, 'reset')
    u = await db.tejas_phone_profiles.find_one({'phone': phone}, {'_id': 0, 'id': 1, 'pin_version': 1})
    if not u:
        raise HTTPException(404, 'No account with this number. Create one instead.')
    await live_paper_guard(u['id'], 'Forgot PIN')
    return await replace_pin(u, phone, data.new_pin, response, 'student_pin_reset_forgot',
                             {'pin_reset_at': now(), 'pin_reset_via': 'forgot_pin'})


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
    hashed = await run_in_threadpool(hash_pin, data.new_pin)
    updated = await db.tejas_phone_profiles.find_one_and_update(
        {'phone': phone, 'role': {'$in': ['student', None]}, 'access_type': {'$in': ['unverified_phone', None]},
         '$expr': {'$eq': [{'$ifNull': ['$pin_version', 0]}, data.expected_pin_version]}},
        {'$set': {'pin_hash': hashed, 'pin_reset_by': u['id'], 'pin_reset_at': stamp}, '$inc': {'pin_version': 1}},
        return_document=ReturnDocument.AFTER, projection={'_id': 0, 'id': 1, 'pin_version': 1})
    if not updated:
        raise HTTPException(409, 'Student changed or is not resettable. Refresh the student list before trying again.')
    forget_student(user_id=updated['id'])
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
