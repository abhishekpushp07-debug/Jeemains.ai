"""Explicit owner-consented solving only. No content discovery or student dispatch."""
import asyncio
import hashlib
import json
import logging
import subprocess
import sys
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from .auth import owner, staff
from .db import db, sets, users, files, get, now, audit, uid
from .documents import BaseDocument
from .request_contracts import SolvePayload
from .mock_solutions import TenMark, SYSTEM, make_tag, refs_hash, solutions, _thread_loop, _POOL, CALL_TIMEOUT
from .astra import _call, MODEL, reserve_call, AstraUnavailable
from starlette.concurrency import run_in_threadpool
from functools import partial

router = APIRouter(prefix='/api/studio', tags=['Owner requested solutions'])
queue = db.tejas_manual_solves
requests = db.tejas_solution_requests
LEASE_SECONDS = 360


class ManualJob(BaseDocument):
    set_id: str
    question_id: str
    number: int
    fingerprint: str
    requested_by: str
    request_id: str
    requested_at: float
    trigger: str = 'owner_solve'
    state: str = 'queued'
    tries: int = 0
    lease: str | None = None
    lease_until: float = 0
    error: str = ''
    solution: dict | None = None
    provenance: dict | None = None
    finished_at: float | None = None


class SolveRequest(BaseDocument):
    set_id: str
    requested_by: str
    created_at: float
    jobs: list[ManualJob]


class ManualTenMark(TenMark):
    final_answer: str = Field(max_length=128)


PROMPT = SYSTEM.split('Return ONLY JSON')[0].replace('with options (A)-(D)', 'with its supplied response format') + (
    'For an MCQ, final_answer must be an existing option identifier. For an integer question return the exact integer as a string. '
    'Return ONLY JSON matching this schema: ' + json.dumps(ManualTenMark.model_json_schema()))


def fingerprint(q):
    return hashlib.sha256(json.dumps({k: q.get(k) for k in ('id', 'type', 'text', 'options', 'answer', 'q_refs', 'render_mode')}, sort_keys=True).encode()).hexdigest()


def preserved(q):
    if q.get('ai_solution') or q.get('ai_solution_id'):
        return 'ai'
    if q.get('solution_kind') == 'answer_key_only':
        placeholder = f"Supplied answer key: {q.get('answer', '')}. This book does not contain a worked solution."
        accessible = f"Supplied key {q.get('answer', '')}; no worked solution provided."
        if (q.get('solution') or '').strip() not in ('', placeholder) or (q.get('solution_accessible_text') or '').strip() not in ('', accessible):
            return 'owner'
        return None  # s_refs in these books are key crops, not worked explanations.
    if (q.get('solution') or '').strip() or q.get('s_refs') or (q.get('solution_accessible_text') or '').strip():
        return 'owner'
    return None


def eligible(q):
    if preserved(q):
        return False
    if q.get('type') not in ('mcq', 'integer') or not q.get('answer'):
        return False
    if q.get('type') == 'mcq' and q['answer'] not in q.get('options', {}):
        return False
    return bool(q.get('q_refs')) if q.get('render_mode') == 'source' else bool(q.get('text', '').strip())


def job_id(set_id, q):
    return str(uuid5(NAMESPACE_URL, 'manual-solve:' + set_id + ':' + fingerprint(q)))


async def paper(id):
    value = await sets.find_one({'id': id}, {'_id': 0})
    if not value:
        raise HTTPException(404, 'Test not found.')
    return value


async def overview(s):
    rows = {d['_id']: ManualJob.from_mongo(d) async for d in queue.find({'set_id': s['id']})}
    counts = dict(total=len(s.get('questions', [])), owner_saved=0, ai_saved=0, missing=0, blocked=0, queued=0, solving=0, failed=0)
    errors = []
    for q in s.get('questions', []):
        saved = preserved(q)
        if saved:
            counts[saved + '_saved'] += 1
        elif not eligible(q):
            counts['blocked'] += 1
        else:
            j = rows.get(job_id(s['id'], q))
            if j and j.state in ('queued', 'solving'):
                counts[j.state] += 1
            else:
                counts['missing'] += 1
                if j and j.state == 'failed':
                    counts['failed'] += 1
                    if len(errors) < 3:
                        errors.append(f'Q{q["number"]}: {j.error}')
    return {'set_id': s['id'], 'title': s['title'], **counts, 'errors': errors, 'automatic_generation': False}


@router.get('/solve-tests')
async def solve_tests(u=Depends(owner)):
    rows = await sets.find({'qa_only': {'$ne': True}, 'status': {'$in': ['draft', 'review', 'published']}},
                           {'_id': 0, 'id': 1, 'title': 1, 'exam': 1, 'full_length': 1, 'chapter_book_id': 1}).sort('title', 1).to_list(2000)
    return {'items': [{'id': s['id'], 'title': s['title'], 'exam': s.get('exam', ''),
                       'kind': 'Mock' if s.get('full_length') else 'Chapter' if s.get('chapter_book_id') else 'Test'} for s in rows]}


@router.get('/sets/{id}/solve')
async def solve_status(id: str, u=Depends(owner)):
    return await overview(await paper(id))


@router.post('/sets/{id}/solve')
async def request_solve(id: str, data: SolvePayload, bg: BackgroundTasks, u=Depends(owner)):
    s = await paper(id)
    rid = str(uuid5(NAMESPACE_URL, f"owner-request:{u['id']}:{id}:{data.request_id}"))
    existing = await requests.find_one({'_id': rid})
    if existing:
        request = SolveRequest.from_mongo(existing)
    else:
        t = now()
        proposed = [ManualJob(id=job_id(id, q), set_id=id, question_id=q['id'], number=q['number'],
                     fingerprint=fingerprint(q), requested_by=u['id'], request_id=rid, requested_at=t)
                    for q in s.get('questions', []) if eligible(q)]
        request = SolveRequest(id=rid, set_id=id, requested_by=u['id'], created_at=t, jobs=proposed)
        try:
            await requests.insert_one(request.to_mongo())
            await audit(u['id'], 'Solve explicitly requested', id, f'{len(proposed)} eligible questions; existing solutions protected.')
        except DuplicateKeyError:
            request = SolveRequest.from_mongo(await requests.find_one({'_id': rid}))
    for j in request.jobs:
        # Atomic identity prevents repeat clicks and concurrent requests duplicating model work.
        try:
            await queue.update_one({'_id': j.id}, {'$setOnInsert': j.to_mongo()}, upsert=True)
        except DuplicateKeyError:
            pass
        await queue.update_one({'_id': j.id, 'state': {'$in': ['failed', 'skipped']}, 'requested_at': {'$lt': request.created_at}},
                               {'$set': {'state': 'queued', 'tries': 0, 'error': '', 'request_id': rid,
                                         'requested_by': u['id'], 'requested_at': request.created_at}})
    bg.add_task(dispatch_manual)
    return {'request_id': rid, **await overview(await paper(id))}


async def dispatch_manual():
    # Called only by the explicit request or recovery of already consented records, never a student GET.
    pending = await queue.find_one({'trigger': 'owner_solve', '$or': [{'state': 'queued'}, {'state': 'solving', 'lease_until': {'$lt': now()}}]})
    if not pending:
        return
    script = Path(__file__).resolve().parents[1] / 'tools' / 'solution_worker.py'
    with open('/var/log/supervisor/solution_worker.log', 'a') as log:
        subprocess.Popen([sys.executable, str(script), '--manual'], start_new_session=True, stdout=log, stderr=subprocess.STDOUT)


async def claim_manual():
    row = await queue.find_one_and_update({'trigger': 'owner_solve', 'tries': {'$lt': 2}, '$or': [
        {'state': 'queued'}, {'state': 'solving', 'lease_until': {'$lt': now()}}]},
        {'$set': {'state': 'solving', 'lease': uid(), 'lease_until': now() + LEASE_SECONDS}, '$inc': {'tries': 1}},
        sort=[('requested_at', 1), ('number', 1)], return_document=ReturnDocument.AFTER)
    return ManualJob.from_mongo(row) if row else None


async def finish_job(j, state, **fields):
    return await queue.update_one({'_id': j.id, 'state': 'solving', 'lease': j.lease, 'lease_until': {'$gt': now()}},
                                 {'$set': {'state': state, 'finished_at': now(), **fields}, '$unset': {'lease': '', 'lease_until': ''}})


async def checked_question(j):
    principal = await users.find_one({'id': j.requested_by}, {'_id': 0, 'password_hash': 0})
    if not principal or principal.get('staff_auth_held'):
        raise HTTPException(403, 'Owner access is no longer available.')
    await staff(principal)
    await owner(principal)
    request_doc = await requests.find_one({'_id': j.request_id, 'requested_by': j.requested_by, 'set_id': j.set_id})
    request = SolveRequest.from_mongo(request_doc) if request_doc else None
    if not request or not any(x.id == j.id and x.fingerprint == j.fingerprint for x in request.jobs):
        raise HTTPException(403, 'An explicit owner Solve request is required.')
    s = await paper(j.set_id)
    q = next((x for x in s['questions'] if x['id'] == j.question_id), None)
    if not q or fingerprint(q) != j.fingerprint or not eligible(q):
        return s, None
    return s, q


async def solve_manual(j):
    s, q = await checked_question(j)
    if not q:
        saved = next((x.get('ai_solution') for x in s['questions'] if x['id'] == j.question_id), None)
        if saved and saved.get('solution_id') == j.id and saved.get('content_hash') == j.fingerprint:
            await finish_job(j, 'ready', solution=saved['solution'])
        else:
            await finish_job(j, 'skipped', error='Content changed or a saved solution now exists; nothing overwritten.')
        return
    from .derivatives import render_crop
    images = [await run_in_threadpool(render_crop, await get(files, r['file_id']), r, 1.6) for r in q.get('q_refs', [])[:4]]
    if len(q.get('q_refs', [])) > 4:
        raise ValueError('Question spans more source regions than the current solver can safely read.')
    text = json.dumps({k: q.get(k) for k in ('number', 'type', 'subject', 'text', 'options', 'answer')})
    await reserve_call()
    call = asyncio.get_running_loop().run_in_executor(_POOL, partial(_call, PROMPT, text, images, ManualTenMark, 4000, 180, _thread_loop))
    value, provenance = await asyncio.wait_for(call, CALL_TIMEOUT)
    from .scoring import canonical
    if value['final_answer']:
        answer = canonical(value['final_answer'], q['type'])
        if q['type'] == 'mcq' and answer not in q['options']:
            raise ValueError('AI returned an option that is not in this question.')
        value['final_answer'] = answer
    s, q = await checked_question(j)
    if not q:
        await finish_job(j, 'skipped', error='Content or owner solution changed during processing; nothing overwritten.')
        return
    if not await queue.find_one({'_id': j.id, 'state': 'solving', 'lease': j.lease, 'lease_until': {'$gt': now()}}):
        return
    tag = make_tag({'id': j.id, 'key': q['answer'], 'refs_hash': refs_hash(q), 'model': MODEL, 'solution': value, 'ready_at': now()})
    tag['content_hash'] = j.fingerprint
    # Compare all source and explanation inputs, not just the question ID. A concurrent owner edit wins.
    expected = {k: q.get(k) for k in ('id', 'type', 'answer', 'text', 'options', 'q_refs', 's_refs', 'solution', 'solution_kind', 'solution_accessible_text')}
    expected['ai_solution'] = None
    result = await sets.update_one({'id': j.set_id, 'revision': s.get('revision'), 'questions': {'$elemMatch': expected}},
                                  {'$set': {'questions.$.ai_solution': tag}})
    if not result.modified_count:
        await finish_job(j, 'skipped', error='A newer explanation or edit was preserved; nothing overwritten.')
        return
    await solutions.update_one({'id': j.id}, {'$setOnInsert': {'id': j.id, 'set_id': j.set_id, 'question_id': j.question_id,
        'number': j.number, 'key': q['answer'], 'state': 'ready', 'model': MODEL, 'solution': value, 'ready_at': now(),
        'refs_hash': refs_hash(q), 'trigger': 'owner_solve', 'requested_by': j.requested_by, 'request_id': j.request_id}}, upsert=True)
    await finish_job(j, 'ready', solution=value, provenance=provenance)


async def run_manual():
    await queue.update_many({'trigger': 'owner_solve', 'state': 'solving', 'lease_until': {'$lt': now()}, 'tries': {'$gte': 2}},
                           {'$set': {'state': 'failed', 'error': 'Processing was interrupted twice. Click Solve to retry missing solutions.'}})
    while True:
        j = await claim_manual()
        if not j:
            return
        try:
            await solve_manual(j)
        except Exception as exc:
            if isinstance(exc, HTTPException) and exc.status_code == 403:
                message = 'Owner access or the original Solve request is no longer valid. No generation was permitted.'
            else:
                message = str(exc) if isinstance(exc, (AstraUnavailable, ValueError)) else 'Processing could not finish. Click Solve to retry missing solutions.'
            logging.getLogger(__name__).warning('Manual solution failed (%s)', type(exc).__name__)
            await finish_job(j, 'failed', error=message[:400])
