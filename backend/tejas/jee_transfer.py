import asyncio
import copy
import gzip
import hashlib
import threading
from functools import lru_cache
from pathlib import Path
from bson import json_util
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from .auth import owner
from .db import db, now, uid
from .documents import BaseDocument
from tejas_storage import request as storage_request

router = APIRouter(prefix='/api/studio/jee-transfer', tags=['Verified JEE transfer'])
BUNDLE_SHA = '3551e344ef2d33f765bfd0015836ebdaec83c918d32830ca9521f62d688191b2'
TRANSFER_ID = 'jee-chapters-' + BUNDLE_SHA
BUNDLE_PATH = Path(__file__).resolve().parents[1] / 'resources' / 'jee_chapters.json.gz'
COLLECTIONS = ('tejas_files', 'tejas_chapter_books', 'tejas_sets')
COUNTS = {'tejas_files': 81, 'tejas_chapter_books': 3, 'tejas_sets': 78}
TIMINGS = {'Physics': 90, 'Mathematics': 120, 'Chemistry': 70}
SOURCE_SLOT = threading.Lock()


class ContentRecord(BaseDocument):
    model_config = ConfigDict(populate_by_name=True, extra='allow')
    record_id: str = Field(alias='id')

    def to_mongo(self):
        return self.model_dump(by_alias=True)


class TransferReceipt(BaseDocument):
    owner_id: str
    phase: str = 'verifying'
    verified_files: int = 0
    cursor: int = 0
    baseline: dict = Field(default_factory=dict)
    before_counts: dict = Field(default_factory=dict)
    lease_token: str = ''
    lease_until: float = 0
    created_at: float
    completed_at: float | None = None


class TransferStatus(BaseModel):
    phase: str
    verified_files: int
    total_files: int = 81
    processed_records: int
    total_records: int = 162
    chapter_tests: int
    total_chapter_tests: int = 78
    questions: int = 3900
    supplied_solutions: int = 3900
    timings: dict = TIMINGS
    marking: dict = {'correct': 4, 'wrong': -1, 'skipped': 0}
    existing_content_unchanged: bool | None = None


def digest(value):
    return hashlib.sha256(json_util.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def content(raw):
    try:
        return ContentRecord.from_mongo(raw).model_dump(by_alias=True, exclude={'id'})
    except ValidationError:
        raise HTTPException(409, 'An existing content record has an invalid identity. Import is blocked rather than changing that record.')


@lru_cache(maxsize=1)
def load_bundle():
    raw = gzip.decompress(BUNDLE_PATH.read_bytes())
    if hashlib.sha256(raw).hexdigest() != BUNDLE_SHA:
        raise HTTPException(503, 'The verified transfer package failed its integrity check. Import is blocked.')
    bundle = json_util.loads(raw)
    data = bundle['collections']
    if set(data) != set(COLLECTIONS) or bundle['independent_audit']['status'] != 'PASS':
        raise HTTPException(503, 'The approved transfer scope is invalid.')
    for name in COLLECTIONS:
        docs = data[name]
        hashes = {d['id']: digest(d) for d in docs}
        if len(docs) != COUNTS[name] or len(hashes) != COUNTS[name] or hashes != bundle['record_sha256'][name]:
            raise HTTPException(503, 'A transfer record failed its source audit.')
    for s in data['tejas_sets']:
        if (s['exam'] != 'JEE Main' or s['test_kind'] != 'chapter' or len(s['questions']) != 50
                or [s['rules'][k] for k in ('minutes', 'correct', 'wrong', 'skipped')] != [TIMINGS[s['chapter_subject']], 4, -1, 0]
                or any(q['solution_kind'] != 'supplied_worked' or not q['approved'] or not q['q_refs'] or not q['s_refs'] for q in s['questions'])):
            raise HTTPException(503, 'A chapter differs from the approved questions, solutions or rules.')
    return data


def target_records(data, principal):
    records = copy.deepcopy(data)
    for b in records['tejas_chapter_books']:
        b['created_by'] = principal['id']
    for s in records['tejas_sets']:
        s['rights_attested_by'] = principal['id']
    return records


async def inventory(records):
    counts = {}
    for name in COLLECTIONS:
        expected = {d['id']: digest(d) for d in records[name]}
        rows = await db[name].find({'id': {'$in': list(expected)}}).to_list(COUNTS[name] + 1)
        for row in rows:
            d = content(row)
            if digest(d) != expected[d['id']]:
                raise HTTPException(409, 'An existing chapter or source record differs. Nothing will be overwritten; resolve the conflict before continuing.')
        counts[name] = len(rows)
    return counts


async def baseline_snapshot(records):
    hashes, counts = {}, {}
    for name in COLLECTIONS:
        hashes[name] = {}
        async for row in db[name].find({'id': {'$nin': [d['id'] for d in records[name]]}}):
            d = content(row)
            hashes[name][d['id']] = digest(d)
        counts[name] = await db[name].count_documents({})
    return hashes, counts


async def verify_baseline(baseline):
    for name, hashes in baseline.items():
        found = {}
        async for row in db[name].find({'id': {'$in': list(hashes)}}):
            d = content(row)
            found[d['id']] = digest(d)
        if found != hashes:
            raise HTTPException(409, 'Existing content changed during the transfer. Import paused without overwriting it; review before continuing.')


def verify_pdf(f):
    raw = storage_request('GET', f['path']).content
    if len(raw) != f['size'] or not raw.startswith(b'%PDF-') or hashlib.sha256(raw).hexdigest() != f['sha256']:
        raise HTTPException(409, 'A private source PDF failed its size or hash check. No chapter will be imported until all sources pass.')


def guarded_pdf_check(f):
    try:
        verify_pdf(f)
    finally:
        SOURCE_SLOT.release()


async def status_view(principal):
    raw = await db.tejas_content_transfers.find_one({'_id': TRANSFER_ID})
    state = TransferReceipt.from_mongo(raw) if raw else None
    count = await db.tejas_sets.count_documents({'id': {'$in': [d['id'] for d in load_bundle()['tejas_sets']]}})
    return TransferStatus(phase=state.phase if state else 'not_started', verified_files=state.verified_files if state else 0,
                          processed_records=state.cursor if state else 0, chapter_tests=count,
                          existing_content_unchanged=True if state and state.phase == 'complete' else None)


@router.get('', response_model=TransferStatus)
async def transfer_status(u=Depends(owner)):
    return await status_view(u)


async def claim(principal, records):
    receipts = db.tejas_content_transfers
    raw = await receipts.find_one({'_id': TRANSFER_ID})
    if raw and raw.get('owner_id') != principal['id']:
        raise HTTPException(409, 'This transfer was started by a different owner account. Continue with that original owner; no records have been overwritten.')
    if not raw:
        await inventory(records)
        baseline, counts = await baseline_snapshot(records)
        state = TransferReceipt(id=TRANSFER_ID, owner_id=principal['id'], baseline=baseline,
                                before_counts=counts, created_at=now())
        try:
            await receipts.insert_one(state.to_mongo())
        except DuplicateKeyError:
            pass
    token = uid()
    raw = await receipts.find_one_and_update(
        {'_id': TRANSFER_ID, 'owner_id': principal['id'], 'lease_until': {'$lte': now()}},
        {'$set': {'lease_token': token, 'lease_until': now() + 300}}, return_document=ReturnDocument.AFTER)
    if not raw:
        raise HTTPException(409, 'Another owner import step is running. Wait for it to finish, then resume.')
    return TransferReceipt.from_mongo(raw)


async def assert_claim(state):
    if not await db.tejas_content_transfers.find_one({'_id': TRANSFER_ID, 'lease_token': state.lease_token, 'lease_until': {'$gt': now()}}, {'_id': 1}):
        raise HTTPException(409, 'The import step expired. Resume to continue safely.')


async def append_record(name, doc, state):
    await assert_claim(state)
    old = await db[name].find_one({'id': doc['id']})
    if old:
        if digest(content(old)) != digest(doc):
            raise HTTPException(409, 'A destination record changed. Import stopped without overwriting it.')
        return
    record = ContentRecord.from_mongo({'_id': TRANSFER_ID + ':' + doc['id'], **doc})
    try:
        await db[name].insert_one(record.to_mongo())
    except DuplicateKeyError:
        old = await db[name].find_one({'id': doc['id']})
        if not old or digest(content(old)) != digest(doc):
            raise HTTPException(409, 'A conflicting record appeared. Import stopped without overwriting it.')


async def advance(state, records):
    if state.phase == 'complete':
        return
    if state.phase == 'verifying':
        f = records['tejas_files'][state.verified_files]
        if not SOURCE_SLOT.acquire(blocking=False):
            raise HTTPException(429, 'The previous PDF check is still finishing. Wait before resuming.', headers={'Retry-After': '30'})
        task = asyncio.create_task(asyncio.to_thread(guarded_pdf_check, f))
        task.add_done_callback(lambda completed: completed.exception() if not completed.cancelled() else None)
        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=45)
        except TimeoutError:
            raise HTTPException(503, 'Source verification timed out. Resume to retry this PDF; no chapters were written.')
        state.verified_files += 1
        if state.verified_files == 81:
            await inventory(records)
            await verify_baseline(state.baseline)
            state.phase = 'importing'
        return
    ordered = [(name, doc) for name in COLLECTIONS for doc in records[name]]
    if state.cursor <= 84 < state.cursor + 8:
        await inventory(records)
        await verify_baseline(state.baseline)
    for name, doc in ordered[state.cursor:state.cursor + 8]:
        await append_record(name, doc, state)
        state.cursor += 1
    if state.cursor == len(ordered):
        await inventory(records)
        await verify_baseline(state.baseline)
        state.phase = 'complete'
        state.completed_at = now()


@router.post('/step', response_model=TransferStatus)
async def transfer_step(u=Depends(owner)):
    records = target_records(load_bundle(), u)
    state = await claim(u, records)
    fence = {'_id': TRANSFER_ID, 'lease_token': state.lease_token}
    try:
        await advance(state, records)
        await assert_claim(state)
        await db.tejas_content_transfers.update_one(fence, {'$set': {
            'phase': state.phase, 'verified_files': state.verified_files,
            'cursor': state.cursor, 'completed_at': state.completed_at}})
    finally:
        await db.tejas_content_transfers.update_one(fence, {'$set': {'lease_until': 0, 'lease_token': ''}})
    return await status_view(u)
