"""Crowd control for one server process.

Matches already being played always go first. When this process is overloaded (slow event loop, too many requests in
flight, too many live sockets), NEW matches and sprints are asked to wait a few seconds (503 + `arena_busy`), and the app
retries by itself. Thresholds are per process and can be tuned with env vars without a code change.

A crowd is a loop that STAYS late. One late wake-up (a long report being built, the container paused for a moment) is a
hiccup: it is measured and reported, but it never closes the doors, so no student waits 5-7 seconds for nothing.
"""
import asyncio
import os
import re
import resource
import time
from collections import OrderedDict

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.requests import ClientDisconnect

LAG_LIMIT = float(os.environ.get("RF_BUSY_LAG_MS", "200")) / 1000
INFLIGHT_LIMIT = int(os.environ.get("RF_BUSY_INFLIGHT", "500"))
SOCKET_LIMIT = int(os.environ.get("RF_BUSY_SOCKETS", "6000"))
SAMPLE_SECONDS = 0.2
WINDOW = 3  # the doors follow the middle one of the last 3 samples: late twice in 0.6 s closes them, on time twice reopens them
RETRY_SECONDS = 5
BUSY_TEXT = "The arena is packed right now. Getting you a seat in a few seconds…"


class Load:
    lag = 0.0  # smoothed event-loop delay, seconds: jumps up at once on a stall (what /api/health/load reports)
    sustained = 0.0  # delay the loop has kept up over the last WINDOW samples: the one the doors listen to
    inflight = 0  # HTTP requests being served right now
    inflight_web = 0  # ...of which website calls (/api/jl): they wait on the website, not on this server's CPU
    background = 0  # ...of which background looks (boards, feeds, history), the first to wait in a big crowd
    sockets = 0  # live match sockets open on this process
    turned_away = 0
    shed = 0  # background looks asked to come back later while this process was packed
    limited = 0  # requests refused because one player sent far more than a phone ever does
    answers_quick = 0  # answers taken in one database round trip
    answers_full = 0  # answers that needed the full path (first on this server, replays, late or out-of-order cards)


load = Load()


class ArenaBusy(Exception):
    pass


def busy() -> bool:
    # Website calls waiting on a slow website do not make Rapid Fire busy: they cost this server no CPU.
    return load.sustained > LAG_LIMIT or load.inflight - load.inflight_web > INFLIGHT_LIMIT or load.sockets > SOCKET_LIMIT


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
    recent = [0.0] * WINDOW
    while True:
        t = loop.time()
        await asyncio.sleep(SAMPLE_SECONDS)
        late = max(0.0, loop.time() - t - SAMPLE_SECONDS)
        load.lag = late if late > load.lag else load.lag * 0.7 + late * 0.3
        recent = recent[1:] + [late]
        load.sustained = sorted(recent)[WINDOW // 2]


class InflightCounter:
    """Pure ASGI: counts HTTP requests in flight without wrapping responses."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        web = scope.get("path", "").startswith("/api/jl/")
        load.inflight += 1
        load.inflight_web += web
        try:
            await self.app(scope, receive, send)
        except ClientDisconnect:
            # The phone went away while it was still sending (app closed, network dropped): nobody is left to answer,
            # so this is not a server error and must not be logged or answered as one.
            pass
        finally:
            load.inflight -= 1
            load.inflight_web -= web


# ---------- Who goes first in a big crowd (Phase 3, Level 7) ----------
# 1. Answers, match sockets, finishing a round, coins: never wait.  2. New matches and sprints: wait a few seconds when
# this process is packed (arena_gate above).  3. Background looks (boards, feeds, history, profiles of others, the live
# strip): while packed, at most BACKGROUND_BUSY of them run at once; the others are asked to come back in a few seconds
# (the app keeps showing what it already has).
BACKGROUND = re.compile(r"^/api/rf/(duels/live|duels|feed|leaderboard|daily/board|league/gangwar|league/friends|history|revision|weak-topics"
                        r"|cups/champions|badla|gangs/search|players/[^/]+(/h2h)?)/?$")
BACKGROUND_BUSY = int(os.environ.get("RF_BUSY_BACKGROUND", "16"))
BACKGROUND_RETRY = 10


def background_look(method: str, path: str) -> bool:
    return method == "GET" and bool(BACKGROUND.match(path))


def shed_background() -> bool:
    """True when this background look must come back later (the process is packed and enough of them already run)."""
    if busy() and load.background >= BACKGROUND_BUSY:
        load.shed += 1
        return True
    return False


# ---------- Limits per player ----------
# A phone sends a burst of ~15 calls when the lobby opens and at most a few per second while playing. One player (one
# grant uid) may send RATE per second with bursts of BURST; a script hammering the server gets 429 for the rest, so it
# can never take the room of other students. Kept per process (each copy guards itself).
PLAYER_RATE = float(os.environ.get("RF_PLAYER_RATE", "20"))
PLAYER_BURST = float(os.environ.get("RF_PLAYER_BURST", "120"))
_buckets: OrderedDict = OrderedDict()  # uid -> [tokens, last refill]
MAX_BUCKETS = 200_000


def player_allowed(uid: str) -> bool:
    now = time.monotonic()
    b = _buckets.get(uid)
    if b is None:
        b = _buckets[uid] = [PLAYER_BURST, now]
        if len(_buckets) > MAX_BUCKETS:
            _buckets.popitem(last=False)
    else:
        _buckets.move_to_end(uid)
        b[0] = min(PLAYER_BURST, b[0] + (now - b[1]) * PLAYER_RATE)
        b[1] = now
    if b[0] < 1:
        load.limited += 1
        return False
    b[0] -= 1
    return True


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
    return {"pid": os.getpid(), "lag_ms": round(load.lag * 1000, 1), "lag_sustained_ms": round(load.sustained * 1000, 1), "inflight": load.inflight,
            "inflight_web": load.inflight_web, "background": load.background, "sockets": load.sockets, "busy": busy(),
            "turned_away": load.turned_away, "shed": load.shed, "limited": load.limited, "answers_quick": load.answers_quick, "answers_full": load.answers_full,
            "open_files_limit": resource.getrlimit(resource.RLIMIT_NOFILE)[0], "ts": time.time()}
