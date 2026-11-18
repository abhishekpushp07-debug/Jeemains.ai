"""Wrong-PIN limit on our side. A 4-digit PIN has only 10,000 values and every sign-in reaches the website through this
server, so failed sign-ins are counted here per phone number (hashed) and per caller address:
8 wrong PINs for one number in 15 minutes, or 100 from one address, pause sign-in for that number / address until the
window passes. The address limit is high on purpose: Indian mobile networks put thousands of phones behind one address
(carrier NAT) and a school Wi-Fi is one address too. A correct PIN clears that number's count. Rows remove themselves
(TTL), so nothing is kept long."""
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone

from fastapi import Request
from starlette.responses import Response

from client_ip import client_ip as caller_ip

SIGN_IN = "auth/phone"
WINDOW = timedelta(minutes=15)
PHONE_LIMIT, IP_LIMIT = 8, 100
WRONG = (401, 403)  # what the website answers for a wrong PIN / unknown number


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _phone(body: bytes) -> str:
    try:
        value = json.loads(body or b"{}").get("phone")
    except (ValueError, AttributeError):
        return ""
    return re.sub(r"\D", "", value)[-10:] if isinstance(value, str) else ""


def _paused(seconds: int) -> Response:
    message = "Too many wrong PINs. Please wait a few minutes, or use Forgot PIN."
    return Response(json.dumps({"data": None, "error": {"code": "rate_limited", "message": message}, "meta": {"api_version": "1"}}),
                    status_code=429, media_type="application/json", headers={"Retry-After": str(seconds), "Cache-Control": "no-store"})


async def setup(db):
    await db.login_fails.create_index([("phone", 1), ("at", -1)])
    await db.login_fails.create_index([("ip", 1), ("at", -1)])
    await db.login_fails.create_index("at", expireAfterSeconds=int(WINDOW.total_seconds()) * 2)


async def check(db, request: Request, path: str, body: bytes):
    """Before a sign-in goes to the website: (keys, None) to go ahead, or (None, 429 response) while paused. Not a sign-in: (None, None)."""
    if path != SIGN_IN or request.method != "POST":
        return None, None
    phone = _phone(body)
    keys = {"phone": _hash(phone) if phone else "", "ip": _hash(caller_ip(request))}
    now = datetime.now(timezone.utc)
    for kind, limit in (("phone", PHONE_LIMIT), ("ip", IP_LIMIT)):
        if not keys[kind]:
            continue
        rows = await db.login_fails.find({kind: keys[kind], "at": {"$gte": now - WINDOW}}, {"_id": 0, "at": 1}).sort("at", 1).to_list(limit)
        if len(rows) >= limit:
            oldest = rows[0]["at"].replace(tzinfo=timezone.utc)
            return None, _paused(max(1, int((oldest + WINDOW - now).total_seconds()) + 1))
    return keys, None


async def record(db, keys: dict, status: int):
    if status in WRONG:
        await db.login_fails.insert_one({**keys, "at": datetime.now(timezone.utc)})
    elif 200 <= status < 300 and keys["phone"]:
        await db.login_fails.delete_many({"phone": keys["phone"]})
