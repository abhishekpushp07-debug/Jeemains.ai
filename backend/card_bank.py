"""The Rapid Fire question bank: card files on disk -> `rf_cards` (synced every minute by content hash) and the public catalog."""
import asyncio
import hashlib
import json
import logging
import time
from typing import List, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pymongo import UpdateOne

import health_stats
from database import ROOT_DIR, BaseDocument, from_field, to_field
from exam_groups import ACTIVE_EXAMS, SUBJECTS, Exam, require_active_exam
from metadata_cache import metadata_cache
from rf_access import maintenance_on
from scope import CARD_COUNTS

CARDS_DIR = ROOT_DIR / 'rapidfire' / 'cards'
MAX_ROUND = max(CARD_COUNTS)
logger = logging.getLogger("jeelive")


class Card(BaseDocument):
    id: str
    subject: str
    chapter: str
    topic: str = ""
    prompt: str
    formula: str = ""
    options: List[str]
    answer: int
    explain: str = ""
    review_status: str = "pilot_review_pending"
    syllabus: str = "JEE Main"
    exam: Optional[Exam] = None
    diagram: Optional[dict] = None
    source_card_id: Optional[str] = None
    provenance: str = ""


def public_card(c: Card) -> dict:
    return c.model_dump(exclude={"mongo_id", "syllabus"})


CARD_HASHES: dict[str, str] = {}  # card file -> content hash already in Mongo (shared by every process via rf_meta)
CARD_KEYS: dict[str, list] = {}
CARD_STAT: dict[str, tuple] = {}  # card file -> (mtime, size) when its hash was last checked: unchanged files are not re-read


async def sync_cards(db):
    if await maintenance_on(db):
        return
    if not CARD_HASHES:  # first run in this process: what the other servers already synced
        saved = (await db.rf_meta.find_one({"_id": "card_files"}) or {}).get("files", {})
        CARD_HASHES.update({from_field(k): v for k, v in saved.items()})
    changed, synced, refreshed = False, {}, False
    # NEET is a preserved archive, not an actively synced/live bank in this app.
    for exam, directory in (("JEE", CARDS_DIR),):
        if not directory.exists():
            continue
        keys = sorted(exam + ":" + f.name for f in directory.glob("*.json"))
        for f in directory.glob("*.json"):
            key, stat = exam + ":" + f.name, f.stat()
            if CARD_STAT.get(key) == (stat.st_mtime_ns, stat.st_size) and key in CARD_HASHES:
                continue  # the file did not change since it was last checked: no 11 MB re-read every minute
            raw = f.read_bytes()
            digest = hashlib.sha1(raw).hexdigest()
            if CARD_HASHES.get(key) != digest and not refreshed:
                # Another copy of the server may have written this file already (every copy runs this loop): read what
                # the bank holds now, once per pass, instead of all copies writing the same thousands of cards again.
                saved = (await db.rf_meta.find_one({"_id": "card_files"}) or {}).get("files", {})
                fresh = {from_field(k): v for k, v in saved.items()}
                changed |= any(CARD_HASHES.get(k) != v for k, v in fresh.items())  # this copy's cached bank is out of date
                CARD_HASHES.update(fresh)
                refreshed = True
            if CARD_HASHES.get(key) == digest:
                CARD_STAT[key] = (stat.st_mtime_ns, stat.st_size)
                continue
            try:
                cards = [Card(**{**c, "exam": exam}) for c in json.loads(raw) if c["subject"] in SUBJECTS[exam]]
            except Exception:
                logger.warning("Skipping invalid or mid-write card file: %s", f.name)
                continue
            ops = [UpdateOne({"id": c.id}, {"$set": {**c.to_mongo(), "retired": False, "source_file": key}}, upsert=True) for c in cards]
            if ops:
                await db.rf_cards.bulk_write(ops, ordered=False)
                await db.rf_cards.update_many({"exam": exam, "subject": cards[0].subject, "chapter": cards[0].chapter,
                                               "id": {"$nin": [c.id for c in cards]}}, {"$set": {"retired": True}})
                changed = True
            else:
                result = await db.rf_cards.update_many({"source_file": key, "retired": {"$ne": True}}, {"$set": {"retired": True}})
                changed |= bool(result.modified_count)
            CARD_HASHES[key] = synced[key] = digest
            CARD_STAT[key] = (stat.st_mtime_ns, stat.st_size)
        if CARD_KEYS.get(exam) != keys:  # a card file was removed: retire its cards (only when the file list changes)
            result = await db.rf_cards.update_many({"source_file": {"$regex": "^" + exam + ":", "$nin": keys}, "retired": {"$ne": True}}, {"$set": {"retired": True}})
            changed |= bool(result.modified_count)
            CARD_KEYS[exam] = keys
    if synced:
        await db.rf_meta.update_one({"_id": "card_files"}, {"$set": {f"files.{to_field(k)}": v for k, v in synced.items()}}, upsert=True)
    if changed:
        await metadata_cache.invalidate_prefix(f'{db.name}:')


async def card_sync_loop(db):
    while True:
        began, ok = time.monotonic(), True
        try:
            await sync_cards(db)
        except Exception as e:  # noqa: BLE001
            ok = False
            logger.warning("card sync failed: %s", e)
        await health_stats.job("card_sync", ok, time.monotonic() - began)
        await asyncio.sleep(60)


def make_router(db):
    r = APIRouter(prefix="/rf")

    @r.get("/catalog")
    async def rf_catalog(exam: Optional[Exam] = None):
        exam = require_active_exam(exam)

        async def load():
            scope = {"exam": exam}
            rows = await (await db.rf_cards.aggregate([{"$match": {"retired": {"$ne": True}, **scope}}, {"$group": {"_id": {"s": "$subject", "c": "$chapter"}, "n": {"$sum": 1}, "diagrams": {"$sum": {"$cond": [{"$ifNull": ["$diagram", False]}, 1, 0]}}}}])).to_list(1000)
            order = {subject: chapters for subject, chapters in json.loads((ROOT_DIR / "rapidfire" / "chapters.json").read_text()).items() if subject in SUBJECTS[exam]}
            counts = {(r["_id"]["s"], r["_id"]["c"]): r["n"] for r in rows}
            return {"exam": exam, "diagram_count": sum(r["diagrams"] for r in rows), "subjects": [{"name": s, "total": sum(counts.get((s, c), 0) for c in chs),
                                  "chapters": [{"name": c, "count": counts.get((s, c), 0)} for c in chs]} for s, chs in order.items()],
                    "exams": {active: SUBJECTS[active] for active in ACTIVE_EXAMS},
                    "review_status": "quick_recall_reviewed_v1",
                    "note": "Full-bank quick-recall suitability pass completed. Answer time is an editorial estimate, not a student timing guarantee."}
        value, state = await metadata_cache.get_or_load(f'{db.name}:catalog:{exam}', load, ttl=60)
        return JSONResponse(value, headers={'X-Cache': state, 'Cache-Control': 'no-cache'})

    r.warm_catalog = rf_catalog
    return r
