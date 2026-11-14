"""Per-session ordering of the canonical requests that rotate cookies (sign-in, refresh, PIN, session).

Two of these for the same session must never overlap, even when they land on different server processes: the second
would send a refresh token the first one has just used up. A local lock orders them inside one process; a short Mongo
lease (`jl_locks`, one document per session, self-expiring) orders them across processes. Ordinary reads and
different sessions are never serialized.
"""
import asyncio
import secrets
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from weakref import WeakValueDictionary

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

_locks = WeakValueDictionary()
ROTATING = {"auth/session", "auth/refresh", "auth/phone", "auth/phone/signup",
            "auth/login", "auth/logout", "auth/pin"}
WAIT_SECONDS, LEASE_SECONDS = 4, 30


def busy_error():
    return HTTPException(503, "Account verification is already in progress. Please retry.",
                         headers={"Retry-After": "2", "Cache-Control": "no-store"})


async def _lease(db, sid, deadline):
    owner = secrets.token_hex(8)
    while True:
        now = datetime.now(timezone.utc)
        until = now + timedelta(seconds=LEASE_SECONDS)
        try:
            await db.jl_locks.insert_one({"_id": sid, "owner": owner, "until": until})
            return owner
        except DuplicateKeyError:
            # A lease left behind by a process that died is taken over once it has run out.
            if await db.jl_locks.find_one_and_update({"_id": sid, "until": {"$lt": now}}, {"$set": {"owner": owner, "until": until}}):
                return owner
        if time.monotonic() > deadline:
            raise busy_error()
        await asyncio.sleep(0.05)


@asynccontextmanager
async def session_rotation(db, sid, path):
    if path not in ROTATING:
        yield
        return
    deadline = time.monotonic() + WAIT_SECONDS
    lock = _locks.setdefault(sid, asyncio.Lock())
    try:
        await asyncio.wait_for(lock.acquire(), timeout=WAIT_SECONDS)
    except asyncio.TimeoutError as error:
        raise busy_error() from error
    try:
        owner = await _lease(db, sid, deadline)
        try:
            yield
        finally:
            await db.jl_locks.delete_one({"_id": sid, "owner": owner})
    finally:
        lock.release()
