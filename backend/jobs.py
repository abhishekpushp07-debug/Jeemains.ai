"""Work the server does by itself: Cup Night's 3-second tick and the 5-minute sweep (one server process at a time).
Each run is recorded for the App Health page (health_stats.job)."""
import asyncio
import logging
import random
import time
from datetime import datetime, timezone

import health_stats
from database import take_turn
from exam_groups import ACTIVE_EXAMS

logger = logging.getLogger("jeelive")


async def cup_night_loop(cups):
    """Cup Night starts at 8 pm IST on its own: every 3 seconds, seat tonight's cups once their moment has come."""
    while True:
        began, ok = time.monotonic(), True
        try:
            await cups.night_tick()
        except Exception:  # noqa: BLE001 - a bad tick must never stop the next one
            ok = False
            logger.exception("cup night tick failed")
        await health_stats.job("cup_night_tick", ok, time.monotonic() - began)
        await asyncio.sleep(3)


async def sweep(db, settle, cups):
    """Closes what nobody came back to: matches left waiting or past their end (their rewards are paid now), sprints
    never finished, and cup payouts cut off by a server restart."""
    now = time.time()
    late = {"$or": [{"status": "waiting", "created_ts": {"$lt": now - 1800}}, {"status": "ready", "ends_at": {"$lt": now - 120}}]}
    # Matches of an archived exam cannot be settled (no rewards there); close them so they never fill the batch below.
    await db.rf_duels.update_many({"$and": [late, {"$or": [{"exam": {"$nin": list(ACTIVE_EXAMS)}}, {"exam": {"$exists": False}, "subject": "Biology"}]}]},
                                  {"$set": {"status": "archived", "archived_ts": now}})
    stale = await db.rf_duels.find(late).limit(500).to_list(500)
    for d in stale:
        try:
            await settle(d)
        except Exception as e:  # noqa: BLE001 - one bad match must not stop the rest
            logger.warning("sweep could not close a match: %s", e)
    old = datetime.fromtimestamp(now - 86400, timezone.utc).isoformat()
    await db.rf_sessions.update_many({"status": "active", "created_at": {"$lt": old}}, {"$set": {"status": "expired"}})
    await cups.resume_payouts()


async def sweep_loop(db, settle, cups):
    while True:
        await asyncio.sleep(300 + random.random() * 30)
        began, ok, mine = time.monotonic(), True, False
        try:
            if await take_turn(db, "sweep", 240):
                mine = True
                await sweep(db, settle, cups)
        except Exception:  # noqa: BLE001
            ok = False
            logger.exception("sweep failed")
        if mine or not ok:
            await health_stats.job("sweep", ok, time.monotonic() - began, db)
