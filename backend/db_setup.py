"""Indexes, one-time migrations and the first card sync: run once per code version, by one server process."""
import asyncio
import hashlib
import logging
import time
from datetime import datetime, timezone

from pymongo.errors import OperationFailure

import account_deletion
import health_stats
import login_guard
import owner_panel
from card_bank import sync_cards
from daily import ensure_indexes as daily_indexes
from database import ROOT_DIR, take_turn
from exam_groups import SUBJECTS
from jl_proxy import JAR_IDLE_DAYS
from mission_links import ensure_indexes as mission_indexes

logger = logging.getLogger("jeelive")
SETUP_VERSION = hashlib.sha1(b"".join(p.read_bytes() for p in sorted(ROOT_DIR.glob("*.py")))).hexdigest()[:16]
SETUP_WAIT = 30  # seconds a start waits for the setup, the same as a copy that waits for another copy's setup


async def run_before_serving(db, cups, wait: float = SETUP_WAIT):
    """The server answers only after the setup, as before (a release that adds nothing big takes well under a second).
    A setup that needs longer than `wait` (a new index over millions of rows, a slow database) goes on in the background
    while the server starts answering, so it can never keep the server unreachable. Returns that task, or None."""
    task = asyncio.create_task(run_once(db, cups))
    done, _ = await asyncio.wait({task}, timeout=wait)
    if done:
        task.result()  # a setup that failed stops the start, as before
        return None
    logger.warning("database setup still running after %s s: the server starts answering while it finishes", wait)
    task.add_done_callback(_late_setup_ended)
    return task


def _late_setup_ended(task):
    if task.cancelled():
        return
    if task.exception():
        logger.error("database setup failed after the server started answering", exc_info=task.exception())
    else:
        logger.warning("database setup finished after the server started answering")


async def run_once(db, cups):
    """The other processes of a big deployment wait for the one doing it (at most 30 s) instead of all repeating ~60
    index calls and ~14k card writes."""
    done = {"_id": "setup:" + SETUP_VERSION, "done": True}
    if await db.rf_meta.find_one(done, {"_id": 1}):
        return
    if await take_turn(db, "setup:" + SETUP_VERSION, 600):
        began = time.monotonic()
        await setup_database(db, cups)
        await db.rf_meta.update_one({"_id": done["_id"]}, {"$set": {"done": True, "ts": time.time()}}, upsert=True)
        await health_stats.job("database_setup", True, time.monotonic() - began, db)
        # Old version markers stay (a few bytes each); nothing is deleted at startup.
        return
    for _ in range(30):
        if await db.rf_meta.find_one(done, {"_id": 1}):
            break
        await asyncio.sleep(1)


async def backfill_cup_crowns(db):
    """Once: count every cup each player has won, and how many of those beat real players (cups_real arrived after the first cups)."""
    if await db.rf_meta.find_one({"_id": "cup_crowns_v1"}):
        return
    humans = {"$size": {"$filter": {"input": "$players", "cond": {"$ne": ["$$this.bot", True]}}}}
    rows = await db.rf_cups.aggregate([{"$match": {"status": "finished", "champion": {"$type": "string"}}},
                                       {"$group": {"_id": "$champion", "won": {"$sum": 1}, "real": {"$sum": {"$cond": [{"$gt": [humans, 1]}, 1, 0]}}}}])
    async for row in rows:
        if not row["_id"].startswith("bot-"):
            await db.rf_profiles.update_one({"uid": row["_id"]}, {"$set": {"cups_won": row["won"], "cups_real": row["real"]}})
    await db.rf_meta.update_one({"_id": "cup_crowns_v1"}, {"$set": {"ts": time.time()}}, upsert=True)


async def setup_database(db, cups):
    await db.rf_cards.create_index("id", unique=True)
    await db.rf_access.create_index('digest', unique=True)
    await db.rf_access.create_index('expires_at', expireAfterSeconds=0)
    await db.rf_cards.create_index([("subject", 1), ("chapter", 1)])
    await db.rf_sessions.create_index([("user_id", 1), ("request_id", 1)], unique=True)
    await db.rf_sessions.create_index("id", unique=True)
    await db.rf_sessions.create_index([("user_id", 1), ("status", 1), ("completed_at", -1)])
    await db.jl_jars.create_index("sid", unique=True)
    # Jars nobody used for JAR_IDLE_DAYS are removed; rows from before seen_at existed get the full period from now.
    await db.jl_jars.update_many({"seen_at": None}, {"$set": {"seen_at": datetime.now(timezone.utc)}})
    await db.jl_jars.create_index("seen_at", expireAfterSeconds=JAR_IDLE_DAYS * 86400)
    await db.jl_locks.create_index("until", expireAfterSeconds=60)
    await db.rf_night_seats.create_index([("day", 1), ("group", 1)])
    await db.rf_night_seats.create_index([("day", 1), ("ts", 1)])
    await mission_indexes(db)
    await db.pin_resets.create_index([("phone", 1), ("at", -1)])
    await db.pin_resets.create_index([("ip", 1), ("at", -1)])
    await login_guard.setup(db)
    await account_deletion.ensure_indexes(db)
    await owner_panel.ensure_indexes(db)
    await db.rf_duels.create_index("id", unique=True)
    await db.rf_duels.create_index("code")
    await db.rf_duels.create_index([("status", 1), ("mode", 1), ("subject", 1), ("created_ts", 1)])
    await db.rf_duels.create_index("players.uid")
    await db.rf_awards.create_index([("uid", 1), ("ref", 1)], unique=True)
    await db.rf_awards.create_index("ts")  # CEO API: the paid matches of a range of days
    await db.mission_links.create_index([("created_ts", -1), ("code", 1)])  # CEO API: links newest first
    await db.rf_profiles.create_index("uid", unique=True)
    await db.rf_profiles.create_index([("xp", -1)])
    await db.rf_cards.create_index([("exam", 1), ("subject", 1), ("chapter", 1), ("retired", 1)])
    await db.rf_cards.create_index([('exam', 1), ('subject', 1), ('chapter', 1), ('id', 1)])
    await db.rf_sessions.create_index([("user_id", 1), ("exam", 1), ("status", 1), ("completed_at", -1)])
    await db.rf_duels.create_index([("exam", 1), ("status", 1), ("mode", 1), ("subject", 1), ("created_ts", 1)])
    await db.rf_duels.create_index([('players.uid', 1), ('exam', 1), ('status', 1), ('finished_ts', -1)])
    await db.rf_learning_events.create_index([("uid", 1), ("ref", 1)], unique=True)
    # Rapid Fire social layer (profiles, friends, blocks, notices, challenges).
    await db.rf_profiles.create_index("pid", unique=True, partialFilterExpression={"pid": {"$type": "string"}})
    await db.rf_profiles.create_index("phone_hash", sparse=True)
    await db.rf_friends.create_index([("uid", 1), ("fid", 1)], unique=True)
    await db.rf_friends.create_index("fid")
    await db.rf_blocks.create_index([("uid", 1), ("bid", 1)], unique=True)
    await db.rf_blocks.create_index("bid")
    await db.rf_notices.create_index([("uid", 1), ("done", 1), ("ts", -1)])
    await db.rf_challenges.create_index("id", unique=True)
    await db.rf_challenges.create_index([("invites.uid", 1), ("status", 1), ("expires_ts", 1)])
    await db.rf_challenges.create_index([("from_uid", 1), ("status", 1)])
    await db.rf_link_visits.create_index([("cid", 1), ("key", 1)], unique=True)
    # Link visits are kept (one row per phone per link); retire the old 30-day auto-delete index if present.
    if (await db.rf_link_visits.index_information()).get("ts_1", {}).get("expireAfterSeconds") is not None:
        await db.rf_link_visits.drop_index("ts_1")
    await db.rf_link_visits.create_index("ts")
    await db.rf_gangs.create_index("id", unique=True)
    await db.rf_gangs.create_index([("members.uid", 1), ("closed", 1)])
    await db.rf_duels.create_index([("gang_id", 1), ("finished_ts", -1)], sparse=True)
    await db.rf_duels.create_index("challenge_id", sparse=True)
    await db.rf_duels.create_index([("teams.a.id", 1), ("finished_ts", -1)], sparse=True)
    await db.rf_duels.create_index([("teams.b.id", 1), ("finished_ts", -1)], sparse=True)
    await db.rf_feed.create_index([("uid", 1), ("ts", -1)])
    await db.rf_profiles.create_index("friend_code", unique=True, partialFilterExpression={"friend_code": {"$type": "string"}})
    await db.rf_cups.create_index("id", unique=True)
    await db.rf_cups.create_index([("players.uid", 1), ("status", 1)])
    await db.rf_cups.create_index([("invites", 1), ("status", 1)])
    await db.rf_cups.create_index([("kind", 1), ("status", 1), ("scope_key", 1)])
    await db.rf_duels.create_index([("status", 1), ("players.uid", 1)])
    await db.rf_cups.create_index("code", unique=True, partialFilterExpression={"code": {"$type": "string"}})
    await db.rf_cups.create_index([("champion", 1), ("status", 1), ("finished_ts", -1)], sparse=True)
    await db.rf_cups.create_index("night", sparse=True)
    await db.rf_cups.create_index([("night", 1), ("night_no", 1)], sparse=True)
    await backfill_cup_crowns(db)
    await cups.migrate_nights()
    await db.rf_cups.create_index("payout", sparse=True)
    await db.rf_duels.create_index([("team_mode", 1), ("status", 1)], sparse=True)
    # Spectators of a live match, shared by every server (count + 100-watcher limit); rows vanish a minute after the last look.
    await db.rf_watch.create_index([("did", 1), ("ts", 1)])
    await db.rf_watch.create_index("at", expireAfterSeconds=60)
    # Feed rows are kept (reads already show only the last 7 days); retire the old auto-delete index if present.
    if "at_1" in await db.rf_feed.index_information():
        await db.rf_feed.drop_index("at_1")
    await db.rf_learning_events.create_index([("uid", 1), ("exam", 1), ("completed_at", 1), ("ref", 1)])
    for exam in SUBJECTS:
        await db.rf_profiles.create_index([(f"exam_stats.{exam}.xp", -1), ("uid", 1)])
    await db.rf_cards.update_many({"exam": {"$exists": False}, "subject": "Biology"}, {"$set": {"exam": "NEET"}})
    await db.rf_cards.update_many({"exam": {"$exists": False}, "subject": {"$ne": "Biology"}}, {"$set": {"exam": "JEE"}})
    # The card sync retires the cards of a removed file by source file: read through this index, not the whole bank.
    await db.rf_cards.create_index([("source_file", 1), ("retired", 1)])
    await sync_cards(db)
    from exam_migration import migrate_exam_data
    await migrate_exam_data(db)
    # Duel live channel must be a capped collection before any event is written (see duels.py tail()).
    from duels import EVENTS_BYTES, EVENTS_MAX
    if "rf_events" not in await db.list_collection_names():
        try:
            await db.create_collection("rf_events", capped=True, size=EVENTS_BYTES, max=EVENTS_MAX)
        except Exception:  # noqa: BLE001
            pass
    elif not (await db.rf_events.options()).get("capped"):
        await db.command("convertToCapped", "rf_events", size=EVENTS_BYTES)
    await db.rf_sessions.create_index([("status", 1), ("created_at", 1)])
    # Database audit at crowd scale (tools/db_audit.py): each index below turns a read of a player's whole history, or
    # of every waiting match, into a read of only the rows that are needed.
    await db.rf_sessions.create_index([("user_id", 1), ("exam", 1), ("created_at", -1)])  # the last 40 sprints (cards already seen), on every new round
    await db.rf_duels.create_index([("players.uid", 1), ("status", 1), ("finished_ts", -1)])  # a player's matches, newest first (profile, Badla, head-to-head)
    await db.rf_duels.create_index("request_id")  # a repeated "new match" request finds its match directly
    # Quick match: the oldest waiting seat on exactly this battleground. Only waiting quick matches are in this index, so it stays tiny.
    await db.rf_duels.create_index([("exam", 1), ("scope_key", 1), ("cards_n", 1), ("created_ts", 1)], name="quick_match_waiting",
                                   partialFilterExpression={"status": "waiting", "mode": "random"})
    await db.rf_profiles.create_index("name")  # a rank counts QA players (TEST…) out without reading every profile above
    await db.rf_profiles.create_index([("last_day", -1), ("uid", 1)])  # CEO dashboard student list: most recent first, then id (a stable page order)
    # Closing a gang cancels its open challenges; only challenges made inside a gang are in this index, so it stays small.
    await db.rf_challenges.create_index([("gang_id", 1), ("status", 1)], name="gang_challenges", partialFilterExpression={"gang_id": {"$type": "string"}})
    await daily_indexes(db)
    await db.rf_dreams.create_index("uid", unique=True)
    # One report per player per gang (reports are upserted on gang + player). Reports are never deleted at startup: if old
    # duplicate rows block the unique index, they are kept and the index waits (logged) until someone resolves them.
    try:
        await db.rf_gang_reports.create_index([("gang_id", 1), ("uid", 1)], unique=True)
    except OperationFailure as e:
        logger.warning("rf_gang_reports unique index not created (duplicate reports kept): %s", e)
    # Phase 3: sessions the website verified (Rapid Fire keeps playing while the website is down), removed when they run
    # out or with the account; and one health document per server copy, removed 2 minutes after the copy stops.
    await db.rf_trust.create_index("until", expireAfterSeconds=0)
    await db.rf_trust.create_index("uid")
    await db.rf_health_nodes.create_index("at", expireAfterSeconds=120)
