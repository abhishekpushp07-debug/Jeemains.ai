import os, hashlib, time
from collections import OrderedDict
from datetime import datetime, timezone, timedelta
import bcrypt, jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field, EmailStr, field_validator
from starlette.concurrency import run_in_threadpool
from pymongo.errors import DuplicateKeyError
from pymongo import ReturnDocument
from .db import db, users, sessions, uid, now

router = APIRouter(prefix="/api/auth", tags=["Staff accounts and sessions"])


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=64)
    name: str = Field(default="Reviewer", min_length=1, max_length=80)
    exam: str = "JEE Main"
    consent: bool = False

    @field_validator("password")
    @classmethod
    def password_bytes(cls, value):
        if len(value.encode()) > 72:
            raise ValueError("Use at most 72 UTF-8 bytes for the password.")
        return value


def view(u):
    result = {k: u[k] for k in ["id", "name", "email", "phone", "role", "exam", "access_type"] if k in u}
    if u.get('access_type') == 'unverified_phone':
        result['pin_configured'] = u.get('pin_version', 0) > 0
    return result


def hashpw(p):
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()


def verify(p, h):
    return bcrypt.checkpw(p.encode(), h.encode())


# A 4-digit PIN gains little from a slow hash (rate limits protect it); a light one keeps exam-day sign-in fast.
PIN_ROUNDS = 8


def hash_pin(p):
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt(PIN_ROUNDS)).decode()


def pin_hash_heavy(h):
    return int(h.split('$')[2]) > PIN_ROUNDS


def token(u, sid, kind, seconds):
    return jwt.encode(
        {
            "sub": u["id"],
            "sid": sid,
            "type": kind,
            "access_type": u.get("access_type", "staff_password"),
            "exp": int(now()) + seconds,
        },
        os.environ["JWT_SECRET"],
        algorithm="HS256",
    )


def cookies(response, u, sid):
    for kind, duration in [("access", 900), ("refresh", 604800)]:
        response.set_cookie(
            kind + "_token",
            token(u, sid, kind, duration),
            max_age=duration,
            httponly=True,
            secure=True,
            samesite="lax",
            path="/",
        )


async def new_session(u, response):
    from .staff_credentials import generation, check_session_generation
    sid = uid()
    record = {
        'id': sid, 'user_id': u['id'],
        'access_type': u.get('access_type', 'staff_password'),
        'expires_at': datetime.now(timezone.utc) + timedelta(days=7),
    }
    if record['access_type'] == 'unverified_phone':
        record['pin_version'] = u.get('pin_version', 0)
    else:
        try:
            record['credential_generation'] = generation(u)
            if u.get('staff_auth_held') is True:
                raise ValueError()
        except ValueError:
            raise HTTPException(401, 'Staff sign-in is unavailable. Use the protected operator recovery channel.')
    await sessions.insert_one(record)
    if record['access_type'] == 'unverified_phone':
        latest = await db.tejas_phone_profiles.find_one({'id': u['id']}, {'_id': 0, 'pin_hash': 0})
        try:
            if not latest:
                raise ValueError()
            check_session_generation(record, latest, 'unverified_phone')
        except ValueError:
            await sessions.delete_one({'id': sid})
            raise HTTPException(401, 'Your PIN changed during sign-in. Sign in with your current PIN.')
        u = {**latest, 'role': 'student', 'access_type': 'unverified_phone'}
    else:
        latest = await users.find_one({'id': u['id']}, {'_id': 0, 'password_hash': 0})
        try:
            if not latest or latest.get('role') not in ('owner', 'reviewer'):
                raise ValueError()
            check_session_generation(record, latest)
        except ValueError:
            await sessions.delete_one({'id': sid})
            raise HTTPException(401, 'Staff credentials changed during sign-in. Enter the current credentials again.')
        u = latest
    cookies(response, u, sid)
    return view(u)


async def identity(p):
    coll = (
        db.tejas_phone_profiles if p.get("access_type") == "unverified_phone" else users
    )
    u = await coll.find_one({"id": p["sub"]}, {"_id": 0, "password_hash": 0, "pin_hash": 0})
    if not u:
        raise ValueError()
    if p.get("access_type") == "unverified_phone":
        u["role"] = "student"
        u["access_type"] = "unverified_phone"
    return u


# Student session checks are reused for at most STUDENT_SESSION_SECONDS per process; JWT signature and expiry
# are still verified on every request. Staff sessions are never cached. Logout/PIN changes clear this process at once.
STUDENT_SESSION_SECONDS = 10
_STUDENT_MAX = 20000
_students = OrderedDict()


def forget_student(user_id=None, token=None):
    if token:
        _students.pop(hashlib.sha256(token.encode()).digest(), None)
    if user_id:
        for key in [k for k, v in _students.items() if v[1] == user_id]:
            _students.pop(key, None)


def remember_student(key, u):
    stamp = time.monotonic()
    _students[key] = (stamp + STUDENT_SESSION_SECONDS, u['id'], dict(u))
    _students.move_to_end(key)
    while _students and (len(_students) > _STUDENT_MAX or next(iter(_students.values()))[0] <= stamp):
        _students.popitem(last=False)


async def current(request: Request):
    try:
        raw = request.cookies.get("access_token")
        p = jwt.decode(
            raw,
            os.environ["JWT_SECRET"],
            algorithms=["HS256"],
        )
        if p["type"] != "access":
            raise ValueError()
        key = hashlib.sha256(raw.encode()).digest() if p.get("access_type") == "unverified_phone" else None
        hit = _students.get(key) if key else None
        if hit and hit[0] > time.monotonic():
            return dict(hit[2])
        record = await sessions.find_one(
            {
                "id": p["sid"],
                "user_id": p["sub"],
                "expires_at": {"$gt": datetime.now(timezone.utc)},
            }
        )
        if not record:
            raise ValueError()
        u = await identity(p)
        from .staff_credentials import check_session_generation
        check_session_generation(record, u, p.get('access_type'))
        if key:
            remember_student(key, u)
        return u
    except (jwt.PyJWTError, ValueError, KeyError, TypeError, AttributeError):
        raise HTTPException(
            401, "Sign in again with your current credentials. Saved work is retained."
        )


async def maybe_current(request: Request):
    """The signed-in user, or None for a visitor."""
    try:
        return await current(request)
    except HTTPException:
        return None


async def staff(u=Depends(current)):
    if u.get("access_type") == "unverified_phone" or u["role"] not in [
        "owner",
        "reviewer",
    ]:
        raise HTTPException(403, "Use authorized staff login to enter Content Studio.")
    return u


async def owner(u=Depends(staff)):
    if u["role"] != "owner":
        raise HTTPException(
            403, "Only the owner can publish or manage reviewer access."
        )
    return u


@router.post("/register")
async def register():
    raise HTTPException(
        410,
        "Students register at /api/auth/phone/signup and sign in with a mobile number and PIN. Staff accounts are issued by the owner.",
    )


@router.post("/login")
async def login(data: Credentials, response: Response):
    email = str(data.email).lower()
    window = int(now() // 900)
    key = hashlib.sha256(f"staff:{email}:{window}".encode()).hexdigest()
    from .rate_limits import increment
    count = await increment(db.tejas_login_limits, key, datetime.now(timezone.utc) + timedelta(minutes=30))
    if count > 5:
        raise HTTPException(429, "Too many sign-in attempts. Please wait before trying again.", headers={"Retry-After": str(max(1, int((window + 1) * 900 - now()) + 1))})
    u = await users.find_one({"email": email})
    if (
        not u
        or u.get("role") not in ["owner", "reviewer"]
        or not await run_in_threadpool(verify, data.password, u["password_hash"])
    ):
        raise HTTPException(
            401,
            "Staff email or password is incorrect. Students sign in with a mobile number and PIN.",
        )
    await db.tejas_login_limits.delete_one({"_id": key})
    return await new_session(u, response)


@router.get("/session")
async def session(request: Request, response: Response):
    if not request.cookies.get("access_token") and not request.cookies.get(
        "refresh_token"
    ):
        return {"user": None}
    try:
        return {"user": view(await current(request))}
    except HTTPException as exc:
        if exc.status_code != 401:
            raise
    try:
        return {"user": await refresh(request, response)}
    except HTTPException as exc:
        if exc.status_code != 401:
            raise
        return {"user": None}


@router.get("/me")
async def me(u=Depends(current)):
    return view(u)


@router.post("/refresh")
async def refresh(request: Request, response: Response):
    try:
        p = jwt.decode(
            request.cookies.get("refresh_token"),
            os.environ["JWT_SECRET"],
            algorithms=["HS256"],
        )
        if p["type"] != "refresh":
            raise ValueError()
        record = await sessions.find_one(
            {
                "id": p["sid"],
                "user_id": p["sub"],
                "expires_at": {"$gt": datetime.now(timezone.utc)},
            }
        )
        if not record:
            raise ValueError()
        u = await identity(p)
        from .staff_credentials import check_session_generation
        check_session_generation(record, u, p.get('access_type'))
        cookies(response, u, p["sid"])
        return view(u)
    except (jwt.PyJWTError, ValueError, KeyError, TypeError):
        raise HTTPException(401, "Your session has ended. Enter again to continue.")


@router.post("/logout")
async def logout(request: Request, response: Response):
    for name in ["access_token", "refresh_token"]:
        try:
            p = jwt.decode(
                request.cookies.get(name),
                os.environ["JWT_SECRET"],
                algorithms=["HS256"],
            )
        except (jwt.PyJWTError, ValueError, TypeError):
            p = None
        if p and p.get("sid"):
            await sessions.delete_one({"id": p["sid"]})
            forget_student(user_id=p.get("sub"))
        response.delete_cookie(
            name, path="/", secure=True, httponly=True, samesite="lax"
        )
    return {"ok": True}


@router.patch("/preferences")
async def preferences(data: dict, u=Depends(current)):
    exam = data.get("exam")
    if exam not in ["JEE Main", "BITSAT"]:
        raise HTTPException(400, "Choose a supported exam.")
    coll = (
        db.tejas_phone_profiles if u.get("access_type") == "unverified_phone" else users
    )
    await coll.update_one({"id": u["id"]}, {"$set": {"exam": exam}})
    return {"exam": exam}


async def seed_owner():
    email = os.environ["ADMIN_EMAIL"].lower()
    if not await users.find_one({"email": email}):
        try:
            await users.insert_one(
                {
                    "id": uid(),
                    "email": email,
                    "name": "Tejas Owner",
                    "role": "owner",
                    "exam": "JEE Main",
                    "access_type": "staff_password",
                    "password_hash": await run_in_threadpool(
                        hashpw, os.environ["ADMIN_PASSWORD"]
                    ),
                    "created_at": now(),
                }
            )
        except DuplicateKeyError:
            pass
