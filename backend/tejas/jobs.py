"""Durable bounded pilot jobs. No scheduler loop; existing platform cron repairs dispatch gaps.
Separate lanes are NOT independent worker fleets or failure domains.
"""
import os, secrets, asyncio, logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, Response
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from starlette.concurrency import run_in_threadpool
from .db import jobs, sets, files, attempts, db, uid, now, get, audit
from .auth import current
from .safety import JOB_CAPABILITIES, HOLD_MESSAGE, job_held, require_capability
from .runtime import LANE_LIMITS, JOB_ATTEMPTS, JOB_LEASE_SECONDS, INLINE_JOBS
from tejas_core import build_questions, generate_report
from tejas_storage import get_object, put_object

router = APIRouter(prefix='/api', tags=['Processing'])
_active = {kind: set() for kind in LANE_LIMITS}


def public_job(j):
    result = {k: v for k, v in j.items() if k not in ('_id', 'path', 'payload', 'lease', 'proposal')}
    if job_held(j.get('kind')) and j.get('status') != 'done':
        result.update({'processing_held': True, 'hold_code': 'capability_held', 'message': HOLD_MESSAGE})
    return result


async def enqueue(kind, user_id, set_id, payload):
    if kind in JOB_CAPABILITIES:
        require_capability(JOB_CAPABILITIES[kind])
    if kind == 'report':
        key = payload['attempt_id'] + '-' + payload.get('score_version', 'original')
        if payload.get('template_version'):
            key += '-' + payload['template_version']
    elif kind == 'grade':
        key = payload['attempt_id']
    elif kind == 'extract':
        key = set_id + '-r' + str(payload.get('revision', 0))
    else:
        key = payload.get('key', set_id)
    j = {'id': kind + '-' + key, 'kind': kind, 'user_id': user_id, 'set_id': set_id,
         'payload': payload, 'status': 'queued', 'progress': 0, 'created_at': now(),
         'lease_until': 0, 'error': '', 'attempts': 0, 'next_run_at': 0}
    try:
        await jobs.insert_one(j)
    except DuplicateKeyError:
        existing = await get(jobs, j['id'])
        if existing['user_id'] != user_id and kind not in ('extract', 'regrade', 'cohort'):
            raise HTTPException(404, 'Job not found.')
        return public_job(existing)
    return public_job(j)


async def require_lease(j):
    if not await jobs.find_one({'id': j['id'], 'lease': j['lease'], 'status': 'running', 'lease_until': {'$gt': now()}}, {'_id': 1}):
        raise RuntimeError('Worker lease lost; output must not be published')


async def run_job(id, drain=True):
    if not INLINE_JOBS:
        return
    header = await jobs.find_one({'id': id}, {'kind': 1})
    if not header or header['kind'] not in _active:
        return
    kind = header['kind']
    if job_held(kind):
        return  # Leave intent durable, without taking a lease or touching outputs.
    lane = _active[kind]
    # No semaphore waiters or per-request thread accumulation. Overflow remains durable.
    if id in lane or len(lane) >= LANE_LIMITS[kind]:
        return
    lane.add(id)
    lease = uid()
    try:
        j = await jobs.find_one_and_update({
            'id': id, '$and': [
                {'$or': [{'status': 'queued'}, {'status': 'running', 'lease_until': {'$lt': now()}}]},
                {'$or': [{'attempts': {'$lt': JOB_ATTEMPTS}}, {'attempts': {'$exists': False}}]},
                {'$or': [{'next_run_at': {'$lte': now()}}, {'next_run_at': {'$exists': False}}]},
            ]}, {'$set': {'status': 'running', 'progress': 10, 'lease': lease, 'lease_until': now() + JOB_LEASE_SECONDS}, '$inc': {'attempts': 1}}, return_document=ReturnDocument.AFTER)
        if not j:
            return
        try:
            output = {}
            if kind == 'ai_solution':
                from .ai_solutions import process
                message = await process(j)
            elif kind in ('smart_prepare','smart_page'):
                from .smart_imports import prepare,extract_page
                message = await (prepare(j) if kind=='smart_prepare' else extract_page(j))
            elif kind == 'cohort':
                from .cohorts import refresh
                message = await refresh(j)
            elif kind == 'grade':
                from .corrections import freeze_ledger
                a = await get(attempts, j['payload']['attempt_id'])
                if a['status'] != 'completed':
                    raise ValueError('Only sealed attempts can be graded')
                await require_lease(j)
                ledger = a.get('ledger') or await freeze_ledger(a)
                await require_lease(j)
                await attempts.update_one({'id': a['id'], 'status': 'completed'}, {'$set': {'summary': ledger['summary'], 'grading_status': 'ready'}})
                from .cohorts import record
                try:
                    await record(a,ledger)
                except Exception:
                    logging.getLogger(__name__).warning('Derived cohort indexing deferred; frozen grade is intact.')
                message = 'Your sealed answers have been graded.'
            elif kind == 'extract':
                qf = await get(files, j['payload']['qfile'])
                sf = await get(files, j['payload']['sfile'])
                qraw = await run_in_threadpool(get_object, qf['path'])
                sraw = await run_in_threadpool(get_object, sf['path'])
                qs = await run_in_threadpool(build_questions, qraw, sraw, qf['id'], sf['id'], j['payload'].get('known_tejas', False))
                await require_lease(j)
                # Legacy extraction may stage a proposal, never mutate academic content.
                # Completion and proposal visibility share the job document's lease CAS.
                # The unified importer is the supported organisation/publication path.
                from bson import BSON
                output = {'proposal': {'questions': qs, 'source_revision': j['payload']['revision']}}
                if len(BSON.encode(output)) > 6 * 1024 * 1024:
                    raise ValueError('Extraction proposal exceeds the safe size budget')
                message = f'{len(qs)} questions staged privately; no test content was changed.'
            elif kind == 'regrade':
                from .corrections import run_regrade
                await require_lease(j)
                message = await run_regrade(j)
            elif kind == 'report':
                from .corrections import with_grade
                a = await with_grade(await get(attempts, j['payload']['attempt_id']), j['payload'].get('score_version'))
                if not a.get('ledger'):
                    raise ValueError('The frozen grade is not ready')
                ids = {r['file_id'] for q in a['questions'] for r in q.get('q_refs', []) + q.get('s_refs', [])}
                sources = {}
                for fid in ids:
                    f = await get(files, fid)
                    sources[fid] = await run_in_threadpool(get_object, f['path'])
                from .mock_solutions import for_attempt
                a['ai_solutions'] = {k: v[1] for k, v in (await for_attempt(a)).items() if v[0] == 'ready'}
                await jobs.update_one({'id': id, 'lease': lease}, {'$set': {'progress': 35}})
                pdf = await run_in_threadpool(generate_report, a, lambda fid: sources[fid])
                await require_lease(j)
                # Never overwrite another lease's report bytes. Only the fenced DB pointer wins.
                path = await run_in_threadpool(put_object, f"tejas/reports/{a['user_id']}/{id}/{lease}.pdf", pdf)
                await require_lease(j)
                await jobs.update_one({'id': id, 'lease': lease, 'status': 'running', 'lease_until': {'$gt': now()}}, {'$set': {'path': path, 'progress': 80}})
                message = 'Your complete results and matched solutions are ready.'
            else:
                raise ValueError('Unknown job type')
            await require_lease(j)
            completed = await jobs.update_one({'id': id, 'lease': lease, 'status': 'running', 'lease_until': {'$gt': now()}}, {'$set': {'status': 'done', 'progress': 100, 'message': message, 'finished_at': now(), 'error': '', **output}})
            if completed.modified_count:
                await audit(j['user_id'], kind.title() + ' completed', j['set_id'], message)
        except Exception:
            logging.getLogger(__name__).exception('Background job failed (kind=%s)', kind)
            retryable = j.get('attempts', 1) < JOB_ATTEMPTS
            await jobs.update_one({'id': id, 'lease': lease, 'status': 'running'}, {'$set': {
                'status': 'queued' if retryable else 'failed', 'progress': 0,
                'next_run_at': now() + min(60, 2 ** j.get('attempts', 1)),
                'error': 'Processing could not finish. Your originals and saved answers are safe.' + (' Retrying shortly.' if retryable else ' Retry after the cause is resolved.'),
            }})
    finally:
        lane.discard(id)
        if drain:
            await drain_lane(kind)
        # Event-driven stage handoff; never wait for an owner to poll progress.
        if kind == 'smart_prepare':
            await drain_lane('smart_page')
        elif kind == 'smart_page':
            await drain_lane('ai_solution')


async def drain_for(set_id):
    """Dispatch persisted import work; bounded lane ownership prevents poll fan-out."""
    if not INLINE_JOBS:
        return
    await asyncio.gather(*(drain_lane(kind) for kind in ('smart_prepare', 'smart_page', 'ai_solution')))


_draining = set()


async def drain_lane(kind):
    """Bounded release-triggered dispatch; platform maintenance remains crash recovery."""
    if kind in _draining or job_held(kind) or not INLINE_JOBS:
        return
    _draining.add(kind)
    try:
        for _ in range(4096):
            if len(_active[kind]) >= LANE_LIMITS[kind]:
                break
            next_job = await jobs.find_one({'kind': kind, 'status': 'queued',
                '$and': [{'$or': [{'next_run_at': {'$lte': now()}}, {'next_run_at': {'$exists': False}}]},
                         {'$or': [{'attempts': {'$lt': JOB_ATTEMPTS}}, {'attempts': {'$exists': False}}]}]},
                {'id': 1}, sort=[('created_at', 1)])
            if not next_job:
                break
            await run_job(next_job['id'], drain=False)
    finally:
        _draining.discard(kind)


@router.get('/jobs/{id}')
async def status(id: str, bg: BackgroundTasks, u=Depends(current)):
    j = await get(jobs, id)
    if j['user_id'] != u['id'] and not (j['kind'] == 'extract' and u['role'] in ['owner', 'reviewer']):
        raise HTTPException(404, 'Job not found.')
    if j['status'] in ('queued', 'running'):
        bg.add_task(run_job, id)
    return public_job(j)


@router.post('/jobs/{id}/retry')
async def retry_job(id: str, bg: BackgroundTasks, u=Depends(current)):
    j = await status(id, bg, u)
    if j['status'] == 'done':
        return j
    if j['kind'] in JOB_CAPABILITIES:
        require_capability(JOB_CAPABILITIES[j['kind']])
    if j['status'] != 'failed':
        raise HTTPException(409, 'This job is already queued or processing.', headers={'Retry-After': '3'})
    updated = await jobs.find_one_and_update({'id': id, 'status': 'failed'}, {'$set': {'status': 'queued', 'error': '', 'attempts': 0, 'next_run_at': 0}}, return_document=ReturnDocument.AFTER)
    if not updated:
        raise HTTPException(409, 'Another retry already queued this job.')
    bg.add_task(run_job, id)
    return public_job(updated)


@router.get('/jobs/{id}/download')
async def download(id: str, u=Depends(current)):
    j = await get(jobs, id)
    if j['kind'] != 'report' or j['user_id'] != u['id']:
        raise HTTPException(404, 'Report not found.')
    attempt = await attempts.find_one({'id': j['payload']['attempt_id']}, {'_id':0, 'competition_end':1})
    if attempt and attempt.get('competition_end', 0) > now():
        raise HTTPException(403, 'Reports unlock when the competition window closes.')
    if j['status'] != 'done':
        raise HTTPException(409, 'The report is not ready yet.', headers={'Retry-After': '3'})
    return Response(await run_in_threadpool(get_object, j['path']), media_type='application/pdf', headers={'Content-Disposition': 'attachment; filename="jeemains-ai-results.pdf"', 'Cache-Control': 'private, no-store'})


async def maintenance():
    from .attempts import finalize, ensure_grade
    from .content import archive_publication
    pending = await sets.find({'publication_pending': {'$exists': True}}, {'id': 1, 'publication_pending': 1}).limit(50).to_list(50)
    for s in pending:
        await archive_publication(s)
    expired = await attempts.find({'status': 'active', 'deadline': {'$gt': 0, '$lte': now()}}, {'id': 1}).limit(1000).to_list(1000)
    for a in expired:
        await finalize(a['id'], 'time_limit')
    # Recover a crash after durable close but before enqueue, including pre-upgrade submissions.
    outbox = await attempts.find({'status': 'completed', 'grading_status': {'$nin': ['ready']}}, {'id': 1, 'user_id': 1, 'set_id': 1, 'status': 1}).limit(1000).to_list(1000)
    for a in outbox:
        await ensure_grade(a)
    # Exhausted crashed workers must become visibly failed, not running forever.
    await jobs.update_many({'status': 'running', 'lease_until': {'$lt': now()}, 'attempts': {'$gte': JOB_ATTEMPTS}}, {'$set': {'status': 'failed', 'error': 'Worker recovery budget exhausted. Saved data is safe; retry after resolving the cause.'}})
    selected = []
    for kind, capacity in LANE_LIMITS.items():
        rows = await jobs.find({'kind': kind, '$and': [
            {'$or': [{'status': 'queued'}, {'status': 'running', 'lease_until': {'$lt': now()}}]},
            {'$or': [{'next_run_at': {'$lte': now()}}, {'next_run_at': {'$exists': False}}]},
        ]}, {'id': 1}).sort('created_at', 1).limit(capacity).to_list(capacity)
        selected.extend(rows)
    await asyncio.gather(*(run_job(j['id']) for j in selected))
    await db.tejas_operations.update_one({'id': 'maintenance'}, {'$set': {'last_run': now(), 'expired': len(expired), 'outbox_checked': len(outbox), 'recovered_jobs': len(selected)}}, upsert=True)


@router.post('/cron/maintenance')
async def cron(request: Request, bg: BackgroundTasks):
    # Cron endpoints must ack 2xx immediately; enqueue/background the actual work.
    expected = os.environ.get('WEBHOOK_CRON_SECRET', '')
    if not expected or not secrets.compare_digest(request.headers.get('authorization', ''), 'Bearer ' + expected):
        raise HTTPException(401, 'Unauthorized')
    try:
        body = await request.json()
        if not isinstance(body, dict):
            raise ValueError()
        rid = request.headers.get('x-webhook-id') or body.get('run_id')
        if body.get('event') != 'schedule.triggered' or not isinstance(rid, str) or not 1 <= len(rid) <= 200:
            raise ValueError()
    except Exception:
        raise HTTPException(400, 'Invalid schedule envelope')
    try:
        await db.tejas_cron_receipts.insert_one({'_id': rid, 'at': now()})
    except DuplicateKeyError:
        return {'accepted': True, 'duplicate': True}
    bg.add_task(maintenance)
    return {'accepted': True}
