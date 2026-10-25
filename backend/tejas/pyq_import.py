import asyncio
import copy
import gzip
import hashlib
import json
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from starlette.concurrency import run_in_threadpool

from .auth import owner
from .canonical import EPOCH_NOW
from .db import db, uid
from .documents import BaseDocument
from tejas_storage import request as storage_request

router = APIRouter(prefix='/api/studio/pyq-import', tags=['Verified source PYQ import'])
ROOT = Path(__file__).resolve().parents[1] / 'resources'
COLLECTIONS = ('tejas_files', 'tejas_versions', 'tejas_sets')
_slot = asyncio.Semaphore(1)


class ImportRecord(BaseDocument):
    model_config = ConfigDict(populate_by_name=True, extra='allow')
    record_id: str = Field(alias='id')


class ImportState(BaseDocument):
    owner_id: str
    bundle_sha: str
    verified_files: int = 0
    cursor: int = 0
    phase: str = 'verifying'
    lease: str = ''
    lease_until: float = 0


class ImportView(BaseModel):
    phase: str
    verified_files: int
    total_files: int
    inserted_records: int
    total_records: int
    published_papers: int
    total_papers: int
    questions: int
    blocked_sources: list[dict] = Field(default_factory=list)


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


@lru_cache(maxsize=1)
def bundle():
    try:
        manifest = json.loads((ROOT / 'jee_pyq_manifest.json').read_text())
        raw = gzip.decompress((ROOT / 'jee_pyq.json.gz').read_bytes())
        data = json.loads(raw)
    except (OSError, ValueError, EOFError) as exc:
        raise HTTPException(503, 'The reviewed PYQ package is not available yet.') from exc
    if hashlib.sha256(raw).hexdigest() != manifest['sha256'] or data['audit']['status'] != 'SOURCE_REVIEWED':
        raise HTTPException(503, 'PYQ package integrity verification failed.')
    if set(data['collections']) != set(COLLECTIONS):
        raise HTTPException(503, 'PYQ package scope is invalid.')
    for name, rows in data['collections'].items():
        if len({r['id'] for r in rows}) != len(rows):
            raise HTTPException(503, 'PYQ package contains duplicate identities.')
        if {r['id']: fingerprint(r) for r in rows} != data['record_sha256'][name]:
            raise HTTPException(503, 'PYQ record integrity verification failed.')
    for paper in data['collections']['tejas_sets']:
        from .content import question_issues
        if paper.get('audience') != 'all' or not paper.get('revision') or not paper.get('file_ids'):
            raise HTTPException(503, 'PYQ publication metadata is incomplete.')
        if any(question_issues(q, paper['exam']) for q in paper['questions']):
            raise HTTPException(503, 'A PYQ question does not satisfy the published content contract.')
        if paper['exam'] != 'JEE Main' or paper['test_kind'] != 'pyq' or len(paper['questions']) != 75 or paper['status'] != 'published':
            raise HTTPException(503, 'Only complete reviewed JEE Main papers may be imported.')
        if any(not q.get('approved') or not q.get('q_refs') or not q.get('s_refs') for q in paper['questions']):
            raise HTTPException(503, 'A question or solution has not passed its source review.')
    return manifest['sha256'], data


def records_for(data, principal):
    records = copy.deepcopy(data['collections'])
    for name in COLLECTIONS:
        for row in records[name]:
            if name in ('tejas_sets', 'tejas_versions'):
                row['rights_attested_by'] = principal['id']
                row['published_by'] = principal['id']
                for source in row['sources'].values():
                    source['uploaded_by'] = principal['id']
            elif name == 'tejas_files':
                row['uploaded_by'] = principal['id']
    return records


async def view_for(principal):
    sha, data = bundle()
    raw = await db.tejas_content_transfers.find_one({'_id': 'jee-pyq-' + sha, 'owner_id': principal['id']})
    state = ImportState.from_mongo(raw) if raw else None
    ids = [r['id'] for r in data['collections']['tejas_sets']]
    published = await db.tejas_sets.count_documents({'id': {'$in': ids}, 'status': 'published', 'test_kind': 'pyq'})
    return ImportView(phase=state.phase if state else 'ready', verified_files=state.verified_files if state else 0,
                      total_files=len(data['collections']['tejas_files']), inserted_records=state.cursor if state else 0,
                      total_records=sum(len(rows) for rows in data['collections'].values()), published_papers=published,
                      total_papers=len(ids), questions=len(ids) * 75, blocked_sources=data['audit'].get('blocked_sources', []))


@router.get('/status', response_model=ImportView)
async def import_status(u=Depends(owner)):
    return await view_for(u)


def check_pdf(source):
    raw = storage_request('GET', source['path']).content
    if not raw.startswith(b'%PDF-') or len(raw) != source['size'] or hashlib.sha256(raw).hexdigest() != source['sha256']:
        raise HTTPException(409, 'A private source PDF differs from its reviewed original. No papers were published.')


async def assert_lease(state):
    if not await db.tejas_content_transfers.find_one({'_id': state.id, 'owner_id': state.owner_id, 'lease': state.lease,
                                                     '$expr': {'$gt': ['$lease_until', EPOCH_NOW]}}, {'_id': 1}):
        raise HTTPException(409, 'PYQ import lease expired; resume safely.')


async def append(name, row, state):
    await assert_lease(state)
    old = await db[name].find_one({'id': row['id']})
    if old:
        parsed = ImportRecord.from_mongo(old).model_dump(by_alias=True, exclude={'id'})
        if fingerprint(parsed) != fingerprint(row):
            raise HTTPException(409, 'Existing content differs; it will not be overwritten.')
        return
    record = ImportRecord.from_mongo({'_id': state.id + ':' + row['id'], **row})
    try:
        await db[name].insert_one(record.to_mongo())
    except DuplicateKeyError:
        old = await db[name].find_one({'id': row['id']})
        if not old or fingerprint(ImportRecord.from_mongo(old).model_dump(by_alias=True, exclude={'id'})) != fingerprint(row):
            raise HTTPException(409, 'A content identity conflict was found. Import stopped safely.')


@router.post('/step', response_model=ImportView)
async def import_step(u=Depends(owner)):
    sha, data = bundle()
    identity = 'jee-pyq-' + sha
    initial = ImportState(id=identity, owner_id=u['id'], bundle_sha=sha)
    try:
        await db.tejas_content_transfers.update_one({'_id': identity}, {'$setOnInsert': initial.to_mongo()}, upsert=True)
    except DuplicateKeyError:
        pass
    lease = uid()
    raw = await db.tejas_content_transfers.find_one_and_update(
        {'_id': identity, 'owner_id': u['id'], '$expr': {'$lte': ['$lease_until', EPOCH_NOW]}},
        [{'$set': {'lease': lease, 'lease_until': {'$add': [EPOCH_NOW, 600]}}}], return_document=ReturnDocument.AFTER)
    if not raw:
        raise HTTPException(409, 'Another PYQ import step is still active; retry shortly.')
    state = ImportState.from_mongo(raw)
    fence = {'_id': identity, 'lease': lease, 'owner_id': u['id']}
    records = records_for(data, u)
    try:
        if state.phase == 'verifying':
            source = records['tejas_files'][state.verified_files]
            async with _slot:
                await run_in_threadpool(check_pdf, source)
            await assert_lease(state)
            state.verified_files += 1
            if state.verified_files == len(records['tejas_files']):
                state.phase = 'importing'
        elif state.phase == 'importing':
            ordered = [(name, row) for name in COLLECTIONS for row in records[name]]
            for name, row in ordered[state.cursor:state.cursor + 4]:
                await append(name, row, state)
                state.cursor += 1
            if state.cursor == len(ordered):
                state.phase = 'complete'
        await assert_lease(state)
        await db.tejas_content_transfers.update_one(fence, {'$set': {'verified_files': state.verified_files, 'cursor': state.cursor, 'phase': state.phase}})
    finally:
        await db.tejas_content_transfers.update_one(fence, {'$set': {'lease_until': 0, 'lease': ''}})
    return await view_for(u)
