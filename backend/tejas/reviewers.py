from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from starlette.concurrency import run_in_threadpool
from pymongo.errors import DuplicateKeyError
from .auth import owner, hashpw
from .db import users, audit, uid, now

router = APIRouter(prefix="/api/studio", tags=["Reviewer authorization"])


class Access(BaseModel):
    email: EmailStr
    role: str
    initial_password: str = Field(default="", max_length=64)


@router.post("/reviewers")
async def update_access(data: Access, u=Depends(owner)):
    if data.role not in ["student", "reviewer"]:
        raise HTTPException(400, "Choose reviewer or remove access.")
    email = str(data.email).lower()
    target = await users.find_one({"email": email})
    if not target:
        if (
            data.role != "reviewer"
            or len(data.initial_password) < 10
            or len(data.initial_password.encode()) > 72
        ):
            raise HTTPException(
                400,
                "For a new reviewer, provide a temporary password of at least 10 characters (at most 72 UTF-8 bytes). Share it through your own secure channel.",
            )
        target = {
            "id": uid(),
            "email": email,
            "name": "Content Reviewer",
            "exam": "JEE Main",
            "role": "reviewer",
            "access_type": "staff_password",
            "created_at": now(),
            "password_hash": await run_in_threadpool(hashpw, data.initial_password),
        }
        try:
            await users.insert_one(target)
        except DuplicateKeyError:
            raise HTTPException(
                409,
                "Reviewer was created in another session. Reload before changing access.",
            )
    else:
        if target["role"] == "owner":
            raise HTTPException(400, "Owner privileges cannot be changed here.")
        await users.update_one({"id": target["id"]}, {"$set": {"role": data.role}})
    await audit(u["id"], "Reviewer access updated", target["id"], data.role)
    return {"ok": True}
