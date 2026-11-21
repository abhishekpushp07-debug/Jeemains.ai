"""Crowd control for one server process.

Matches already being played always go first. When this process is overloaded (slow event loop, too many requests in
flight, too many live sockets), NEW matches and sprints are asked to wait a few seconds (503 + `arena_busy`), and the app
retries by itself. Thresholds are per process and can be tuned with env vars without a code change.
"""
import asyncio
import os
import resource
import time

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.requests import ClientDisconnect

LAG_LIMIT = float(os.environ.get("RF_BUSY_LAG_MS", "200")) / 1000
INFLIGHT_LIMIT = int(os.environ.get("RF_BUSY_INFLIGHT", "500"))
SOCKET_LIMIT = int(os.environ.get("RF_BUSY_SOCKETS", "6000"))
RETRY_SECONDS = 5
BUSY_TEXT = "The arena is packed right now. Getting you a seat in a few seconds…"


class Load:
    lag = 0.0  # smoothed event-loop delay, seconds
    inflight = 0  # HTTP requests being served right now
    sockets = 0  # live match sockets open on this process
    turned_away = 0
    answers_quick = 0  # answers taken in one database round trip
    answers_full = 0  # answers that needed the full path (first on this server, replays, late or out-of-order cards)


load = Load()


class ArenaBusy(Exception):
    pass


def busy() -> bool:
    return load.lag > LAG_LIMIT or load.inflight > INFLIGHT_LIMIT or load.sockets > SOCKET_LIMIT


def arena_gate():
    """FastAPI dependency for the doors into a NEW match or sprint (never for answers inside one)."""
    if busy():
        load.turned_away += 1
        raise ArenaBusy()


async def busy_response(_: Request, __: ArenaBusy):
    return JSONResponse({"detail": BUSY_TEXT, "code": "arena_busy"}, status_code=503,
                        headers={"Retry-After": str(RETRY_SECONDS), "Cache-Control": "no-store"})


async def monitor():
    """Measures how late the event loop wakes up (the best single signal that this process is saturated)."""
    loop = asyncio.get_running_loop()
    while True:
        t = loop.time()
        await asyncio.sleep(0.2)
        late = max(0.0, loop.time() - t - 0.2)
        load.lag = late if late > load.lag else load.lag * 0.7 + late * 0.3


class InflightCounter:
    """Pure ASGI: counts HTTP requests in flight without wrapping responses."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        load.inflight += 1
        try:
            await self.app(scope, receive, send)
        except ClientDisconnect:
            # The phone went away while it was still sending (app closed, network dropped): nobody is left to answer,
            # so this is not a server error and must not be logged or answered as one.
            pass
        finally:
            load.inflight -= 1


def raise_fd_limit():
    """Each player holds a socket: lift this process's open-files limit from the 1024 default to the system maximum."""
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    target = hard if hard != resource.RLIM_INFINITY else 1_048_576
    if soft < target:
        try:
            resource.setrlimit(resource.RLIMIT_NOFILE, (target, hard))
        except (ValueError, OSError):
            pass
    return resource.getrlimit(resource.RLIMIT_NOFILE)[0]


def snapshot() -> dict:
    return {"pid": os.getpid(), "lag_ms": round(load.lag * 1000, 1), "inflight": load.inflight, "sockets": load.sockets, "busy": busy(),
            "turned_away": load.turned_away, "answers_quick": load.answers_quick, "answers_full": load.answers_full,
            "open_files_limit": resource.getrlimit(resource.RLIMIT_NOFILE)[0], "ts": time.time()}
