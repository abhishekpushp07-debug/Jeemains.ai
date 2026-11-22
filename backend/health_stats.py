"""The eyes of the server (Phase 3, Level 7): what the App Health page shows.

- RouteStats (pure ASGI): every HTTP answer is counted per route and per minute (count, server errors, a speed histogram).
  A row is named by the route's own pattern ("/api/rf/friends/code/{code}"), never by the address the phone sent, so no
  code, id or name is kept. Only addresses no route answered (and the website's own paths) are folded by hand.
- jobs: when each background job last ran, how long it took and whether it worked. Jobs that one copy does for everybody
  (the sweep, database setup) are also written to `rf_meta` (job:<name>), so every copy sees them.
- beat(): every BEAT seconds each server copy writes one small document (`rf_health_nodes`) with its load, its last 5
  minutes of routes, its website shield and its jobs. A copy that stops removes its own document at once (leave()); one
  that crashes drops off the page after LIVE_WINDOW seconds (Mongo deletes the document 2 minutes later). The App Health
  page adds the copies up, so it shows the whole app however many run. Counts and timings only: no player id, name or number."""
import asyncio
import logging
import os
import re
import socket
import time
import uuid
from datetime import datetime, timezone

NODE = uuid.uuid4().hex[:12]
STARTED = time.time()
BOUNDS = (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000)  # ms; one more bucket above the last
MAX_ROUTES = 300
BEAT, LIVE_WINDOW = 5, 16  # seconds: a copy reports every BEAT; one silent for LIVE_WINDOW (3 missed beats) is gone
logger = logging.getLogger("jeelive")
WORD = re.compile(r"^[a-z][a-z_-]{0,39}$")  # a plain lower-case word ("answer", "weak-topics"); anything else may be a code
_minutes: dict = {}  # minute -> {route: [count, errors, *hist]}
_jobs: dict = {}  # name -> {"ts", "took_ms", "ok"}


def route_of(path: str, template: str | None = None) -> str:
    """The route's own pattern when one answered; otherwise the address with every part that is not a plain lower-case
    word replaced by {id} (codes like QAZWSXED, ids, numbers). The website's paths keep their kind of call only."""
    if template and ":path}" not in template:
        return template
    parts = path.rstrip("/").split("/")
    if path.startswith("/api/jl/"):  # attempts/{id}/answers/{id}
        parts = parts[:7]
    return "/".join(p if not p or WORD.match(p) else "{id}" for p in parts) or "/"


def bucket(ms: float) -> int:
    return next((i for i, b in enumerate(BOUNDS) if ms <= b), len(BOUNDS))


def count(route: str, status: int, ms: float):
    m = int(time.time() // 60)
    rows = _minutes.get(m)
    if rows is None:
        rows = _minutes[m] = {}
        for old in [k for k in _minutes if k < m - 6]:
            del _minutes[old]
    row = rows.get(route)
    if row is None:
        if len(rows) >= MAX_ROUTES:
            route = "(other)"
            row = rows.get(route)
        if row is None:
            row = rows[route] = [0, 0] + [0] * (len(BOUNDS) + 1)
    row[0] += 1
    row[1] += status >= 500
    row[2 + bucket(ms)] += 1


def recent_routes(minutes: int = 5) -> dict:
    now, out = int(time.time() // 60), {}
    for m, rows in _minutes.items():
        if m > now - minutes:
            for route, row in rows.items():
                have = out.get(route)
                out[route] = [a + b for a, b in zip(have, row)] if have else list(row)
    return out


class RouteStats:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        began, status = time.perf_counter(), [500]

        async def watched(message):
            if message["type"] == "http.response.start":
                status[0] = message["status"]
            await send(message)
        try:
            await self.app(scope, receive, watched)
        finally:  # the router wrote the matched route into this same scope (middlewares below must not copy it)
            count(route_of(scope.get("path", ""), getattr(scope.get("route"), "path", None)), status[0], (time.perf_counter() - began) * 1000)


async def job(name: str, ok: bool, took: float, db=None):
    """A background job finished. With `db`, the run is also recorded for every copy (jobs one copy does for all)."""
    row = {"ts": time.time(), "took_ms": round(took * 1000, 1), "ok": bool(ok)}
    _jobs[name] = row
    if db is not None:
        try:
            await db.rf_meta.update_one({"_id": "job:" + name}, {"$set": {**row, "node": NODE}}, upsert=True)
        except Exception:  # noqa: BLE001 - the record is for the owner's page; the job itself already ran
            logger.warning("job record failed: %s", name)


def node_doc(load_snapshot: dict, website: dict, pending: int) -> dict:
    return {"_id": NODE, "host": socket.gethostname()[:40], "pid": os.getpid(), "started": STARTED, "ts": time.time(),
            "at": datetime.now(timezone.utc), "load": load_snapshot, "routes": recent_routes(), "website": website,
            "jobs": dict(_jobs), "later_pending": pending}


async def beat(db, load_snapshot, website_snapshot, pending):
    while True:
        try:
            doc = node_doc(load_snapshot(), website_snapshot(), pending())
            await db.rf_health_nodes.replace_one({"_id": NODE}, doc, upsert=True)
        except Exception:  # noqa: BLE001 - the page misses one beat; the server keeps serving
            logger.warning("health beat failed")
        await asyncio.sleep(BEAT)


async def leave(db, beating: asyncio.Task):
    """This copy is stopping: no more beats, and it leaves the App Health page now (not LIVE_WINDOW seconds later)."""
    beating.cancel()
    try:
        await db.rf_health_nodes.delete_one({"_id": NODE})
    except Exception:  # noqa: BLE001 - the page then drops this copy after LIVE_WINDOW seconds
        logger.warning("health leave failed")
