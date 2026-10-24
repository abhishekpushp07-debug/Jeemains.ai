"""Number-only convenience access, explicitly not verification or secure identity."""

import hashlib
from datetime import datetime, timezone, timedelta
import phonenumbers
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from .db import db, uid, now
from .auth import new_session

router = APIRouter(prefix="/api/auth", tags=["Unverified phone access"])


class PhoneInput(BaseModel):
    phone: str = Field(min_length=5, max_length=32)


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


@router.post("/phone")
async def access(data: PhoneInput, response: Response):
    phone = normalize_phone(data.phone)
    window = int(now() // 600)
    key = hashlib.sha256(f"phone:{phone}:{window}".encode()).hexdigest()
    from .rate_limits import increment
    count = await increment(db.tejas_phone_limits, key, datetime.now(timezone.utc) + timedelta(minutes=20))
    if count > 30:
        raise HTTPException(
            429, "Too many requests for this number. Please try again in a few minutes.",
            headers={"Retry-After": str(max(1, int((window + 1) * 600 - now()) + 1))},
        )
    profile = {
        "id": uid(),
        "phone": phone,
        "name": "Learner",
        "role": "student",
        "exam": "JEE Main",
        "access_type": "unverified_phone",
        "created_at": now(),
        "consent_at": now(),
    }
    try:
        await db.tejas_phone_profiles.update_one(
            {"phone": phone},
            {"$setOnInsert": profile, "$set": {"last_seen_at": now()}},
            upsert=True,
        )
    except DuplicateKeyError:
        pass
    u = await db.tejas_phone_profiles.find_one({"phone": phone}, {"_id": 0})
    return await new_session(u, response)
