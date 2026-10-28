"""Per-session rotation ordering for the web proxy's current worker.

Native ordering lives in the client; ordinary reads and unrelated sessions are
not serialized. Multi-worker distributed session coordination is a separate gate.
"""
import asyncio
from contextlib import asynccontextmanager
from weakref import WeakValueDictionary

from fastapi import HTTPException

_locks = WeakValueDictionary()
ROTATING = {"auth/session", "auth/refresh", "auth/phone", "auth/phone/signup",
            "auth/login", "auth/logout", "auth/pin"}


@asynccontextmanager
async def session_rotation(sid, path):
    if path not in ROTATING:
        yield
        return
    lock = _locks.setdefault(sid, asyncio.Lock())
    try:
        await asyncio.wait_for(lock.acquire(), timeout=4)
    except asyncio.TimeoutError as error:
        raise HTTPException(503, "Account verification is already in progress. Please retry.",
                            headers={"Retry-After": "2", "Cache-Control": "no-store"}) from error
    try:
        yield
    finally:
        lock.release()