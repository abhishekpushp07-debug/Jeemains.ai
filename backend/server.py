"""JEELIVE.AI app server: puts the routers, middleware and background work together.

Where things live:
  database.py   - the MongoDB connection and shared helpers      jl_proxy.py  - the website proxy (/api/jl/...)
  card_bank.py  - Rapid Fire question bank sync + catalog        sprints.py   - solo Rapid Fire sprints
  db_setup.py   - indexes and one-time migrations                jobs.py      - Cup Night tick and the 5-minute sweep
  Phase 3: fast_json.py (orjson answers) · later.py (work nobody waits for) · website_shield.py (jeelive.ai down/slow)
           health_stats.py + health_panel.py (App Health page /api/owner/health) · log_redact.py (no PIN in any log)
  everything else (duels, cups, daily, gangs, rank, ...) keeps its own module with a make_router() factory."""
from database import client, db  # first: loads backend/.env for every module below

import asyncio
import logging
import os
import time

from fastapi import APIRouter, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

import account_deletion
import app_switches
import card_bank
import ceo_api
import db_setup
import health_alerts
import health_panel
import health_stats
import jl_proxy
import jobs
import later
import log_redact
import owner_panel
import sprints
from arena_web import router as arena_web_router
from branding import router as branding_router
from cors_config import allowed_origins
from cups import make_router as make_cups
from daily import make_router as make_daily
from dream import make_router as make_dream
from duels import make_router as make_duels
from exam_groups import SUBJECTS
from fast_json import FastJSONResponse
from gamify import make_router as make_gamify
from gangs import make_router as make_gangs
from jl_transport import make_client
from leagues import make_router as make_leagues
from legal_pages import router as legal_router
from load_guard import ArenaBusy, InflightCounter, busy_response, monitor as load_monitor, raise_fd_limit, snapshot as load_snapshot
from marketing_media import router as marketing_router
from metadata_cache import metadata_cache
from mission_links import make_router as make_mission_links
from owner_downloads import make_router as make_owner_downloads
from performance import AssetAwareCompression, ServerTiming
from pin_reset import make_pin_reset
from rank_predictor import make_router as make_rank
from rapid_deck import selection_pool
from revision import live_cards, make_router as make_revision
from rf_access import install_access_guard, make_access_router, rf_user
from rooms import make_router as make_rooms
from social import make_router as make_social
from squads import make_router as make_squads
from website_shield import shield

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_redact.install()

# Plain-data answers are written by orjson (fast_json.py): the same JSON as before for a fraction of the CPU.
app = FastAPI(default_response_class=FastJSONResponse)
api = APIRouter(prefix="/api")


@app.get("/health", include_in_schema=False)
@app.head("/health", include_in_schema=False)
async def health():
    return {"status": "ok"}


game_router, award = make_gamify(db, rf_user)
duel_router, duel_api = make_duels(db, rf_user, card_bank.public_card, award)
cups_router = make_cups(db, rf_user, duel_api)
catalog_router = card_bank.make_router(db)
leagues_router = make_leagues(db, rf_user)

api.include_router(jl_proxy.router)
api.include_router(catalog_router)
api.include_router(sprints.make_router(db, rf_user, award))
api.include_router(make_daily(db, rf_user, award))
api.include_router(duel_router)
api.include_router(make_social(db, rf_user))
api.include_router(make_rooms(db, rf_user, duel_api["seat"]))
api.include_router(make_gangs(db, rf_user))
api.include_router(leagues_router)
api.include_router(cups_router)
api.include_router(make_squads(db, rf_user))
api.include_router(make_pin_reset(db))
api.include_router(game_router)
api.include_router(make_revision(db, rf_user))
api.include_router(make_owner_downloads(db))
api.include_router(branding_router)
api.include_router(marketing_router)
api.include_router(legal_router)
api.include_router(arena_web_router)
api.include_router(make_rank())
api.include_router(make_mission_links(db, rf_user))
api.include_router(make_dream(db, rf_user))
api.include_router(make_access_router(db, jl_proxy.client))
api.include_router(account_deletion.make_router(db, jl_proxy.client))
api.include_router(owner_panel.make_router(db, jl_proxy.client))
api.include_router(health_panel.make_router(db))
api.include_router(health_alerts.make_router(db))
api.include_router(ceo_api.make_router(db))
api.include_router(app_switches.router)
app.include_router(api)
install_access_guard(app, db)
app.add_middleware(AssetAwareCompression, minimum_size=1024, compresslevel=4)
app.add_middleware(ServerTiming)
app.add_middleware(InflightCounter)
app.add_middleware(health_stats.RouteStats)
app.add_exception_handler(ArenaBusy, busy_response)
app.add_exception_handler(RequestValidationError, log_redact.validation_error)
app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=allowed_origins(), allow_methods=["*"], allow_headers=["*"], expose_headers=['Server-Timing', 'X-Cache', 'Retry-After'])


@app.get("/api/health/load", include_in_schema=False)
async def health_load():
    """This process's load (no player data): event-loop delay, requests in flight, live sockets, whether new matches wait."""
    return JSONResponse({**load_snapshot(), "website": shield.snapshot()["state"]}, headers={"Cache-Control": "no-store"})


@app.on_event("startup")
async def startup():
    raise_fd_limit()  # one open file per player socket: the 1024 default capped a process at ~1000 players
    log_redact.install()  # again: uvicorn's handlers exist by now
    asyncio.create_task(load_monitor())
    if os.environ.get("RF_ACCESS_LOG") != "1":  # a log line per request costs real CPU at crowd scale
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)  # httpx logs every request at INFO
    jl_proxy.http = make_client()
    await db_setup.run_once(db, cups_router)
    asyncio.create_task(jobs.cup_night_loop(cups_router))
    asyncio.create_task(card_bank.card_sync_loop(db))
    asyncio.create_task(jobs.sweep_loop(db, duel_api["settle"], cups_router))
    app.state.health_beat = asyncio.create_task(health_stats.beat(db, load_snapshot, shield.snapshot, later.pending))
    asyncio.create_task(health_alerts.watch(db))
    asyncio.create_task(warm_up())


async def warm_up():
    """Right after a start, read what the first students would otherwise wait for: the deal pools of every subject, the
    weak-list card map, the catalog and the XP ladder (each a pass over thousands of rows, then kept in memory)."""
    began, ok = time.monotonic(), True
    try:
        for subject in SUBJECTS["JEE"]:
            await selection_pool(db, "JEE", subject)
        await live_cards(db, "JEE")
        await catalog_router.warm_catalog("JEE")
        await game_router.warm_ladder("JEE")
        await leagues_router.warm_standings()
    except Exception:  # noqa: BLE001 - a failed warm-up only means the first student reads it instead
        ok = False
        logging.getLogger("jeelive").exception("warm-up failed")
    await health_stats.job("warm_up", ok, time.monotonic() - began)


@app.on_event("shutdown")
async def shutdown():
    # A copy that stops (new release, restart) hands its live players over first: their phones reconnect to another
    # copy at once; work that was waiting to be written (friend feed rows) is written before the database closes.
    await health_stats.leave(db, app.state.health_beat)
    try:
        await asyncio.wait_for(duel_api["close_all"](), timeout=5)
    except Exception:  # noqa: BLE001 - phones also reconnect by themselves when the socket simply drops
        logging.getLogger("jeelive").warning("closing live sockets at shutdown failed")
    await later.drain()
    await metadata_cache.close()
    if jl_proxy.http:
        await jl_proxy.http.close()
    await client.close()
