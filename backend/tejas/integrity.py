"""Database integrity: read-only checks that return counts only (never student details), plus safe, idempotent repairs.
A submitted result is never re-invented: the frozen ledger is the single source of truth for a score."""
import asyncio, logging, time, uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pymongo.errors import DuplicateKeyError
from .auth import owner
from .db import db, attempts, jobs, now, audit
from .canonical import CanonicalIntegrityError, verify_ledger

router = APIRouter(prefix='/api/admin/integrity', tags=['Data integrity'])
ops = db.tejas_operations
archive = db.tejas_integrity_archive
IST = ZoneInfo('Asia/Kolkata')
ACTOR = 'system:integrity'
BATCH = 2000
QUERY_MS = 120000
log = logging.getLogger(__name__)


def absent(coll, local, foreign):
    return [{'$lookup': {'from': coll, 'localField': local, 'foreignField': foreign, 'as': '_m',
                         'pipeline': [{'$project': {'_id': 1}}, {'$limit': 1}]}}, {'$match': {'_m': {'$size': 0}}}]


def twins(key, match=None):
    return ([{'$match': match}] if match else []) + [{'$group': {'_id': key, 'n': {'$sum': 1}}}, {'$match': {'n': {'$gt': 1}}}]


def differs(local, field):
    return [{'$lookup': {'from': 'tejas_ledgers', 'localField': local, 'foreignField': 'id', 'as': '_l',
                         'pipeline': [{'$project': {'_id': 0, 's': '$summary.score_exact'}}]}},
            {'$unwind': '$_l'}, {'$match': {'$expr': {'$ne': [field, '$_l.s']}}}]


SCORED = {'status': 'completed', 'grading_status': 'ready'}
STUDENT = absent('tejas_phone_profiles', 'user_id', 'id') + absent('tejas_users', 'user_id', 'id')
CHECKS = [
    ('open_after_time', 'Tests still open after their time ended', 'high', 'repair', 'tejas_attempts',
     lambda t: [{'$match': {'status': 'active', 'deadline': {'$gt': 0, '$lte': t}}}]),
    ('waiting_for_score', 'Submitted tests still waiting for a score', 'high', 'repair', 'tejas_attempts',
     lambda t: [{'$match': {'status': 'completed', 'grading_status': {'$nin': ['ready', 'failed']}}}]),
    ('score_failed', 'Submitted tests whose scoring stopped with an error', 'high', 'repair', 'tejas_attempts',
     lambda t: [{'$match': {'status': 'completed', 'grading_status': 'failed'}}]),
    ('score_without_record', 'Scores shown without their frozen score record', 'high', 'repair', 'tejas_attempts',
     lambda t: [{'$match': SCORED}] + absent('tejas_ledgers', 'id', 'id')),
    ('score_differs', 'Shown score differs from its frozen score record', 'high', 'repair', 'tejas_attempts',
     lambda t: [{'$match': SCORED}] + differs('id', '$summary.score_exact')),
    ('peer_entry_orphan', 'Ranking entries for attempts that no longer exist', 'high', 'repair', 'tejas_cohort_entries',
     lambda t: absent('tejas_attempts', 'attempt_id', 'id')),
    ('peer_score_differs', 'Ranking entries whose score differs from the frozen record', 'high', 'repair', 'tejas_cohort_entries',
     lambda t: differs('attempt_id', '$score_exact')),
    ('score_record_orphan', 'Frozen score records left by attempts that no longer exist', 'low', 'repair', 'tejas_ledgers',
     lambda t: absent('tejas_attempts', 'id', 'id')),
    ('session_orphan', 'Sign-in sessions for accounts that no longer exist', 'low', 'repair', 'tejas_sessions',
     lambda t: STUDENT),
    ('job_stopped', 'Scoring, report or ranking work that stopped after errors', 'medium', 'repair', 'tejas_jobs',
     lambda t: [{'$match': {'status': 'failed', 'kind': {'$in': ['grade', 'report', 'cohort']}, 'integrity_retried': {'$ne': True}}}]),
    ('questions_missing', 'Attempts whose saved question pack is missing', 'high', 'report', 'tejas_attempts',
     lambda t: [{'$match': {'pack_id': {'$type': 'string'}}}] + absent('tejas_packs', 'pack_id', '_id')),
    ('attempt_without_test', 'Attempts whose test no longer exists', 'medium', 'report', 'tejas_attempts',
     lambda t: absent('tejas_sets', 'set_id', 'id')),
    ('attempt_without_student', 'Attempts whose student account no longer exists', 'medium', 'report', 'tejas_attempts',
     lambda t: STUDENT),
    ('duplicate_phone', 'Two student accounts on one mobile number', 'high', 'report', 'tejas_phone_profiles',
     lambda t: twins('$phone')),
    ('duplicate_staff_email', 'Two staff accounts on one email', 'high', 'report', 'tejas_users',
     lambda t: twins('$email')),
    ('duplicate_open_attempt', 'One student with two open attempts of the same test', 'high', 'report', 'tejas_attempts',
     lambda t: twins({'u': '$user_id', 's': '$set_id', 'm': '$mode'}, {'status': 'active'})),
    ('duplicate_live_attempt', 'One student with two attempts in the same live exam', 'high', 'report', 'tejas_attempts',
     lambda t: twins({'u': '$user_id', 's': '$set_id'}, {'competition_end': {'$exists': True}, 'mode': {'$ne': 'retry'}})),
    ('duplicate_peer_entry', 'One student counted twice in a ranking', 'high', 'report', 'tejas_cohort_entries',
     lambda t: twins({'c': '$cohort_id', 'u': '$user_id'})),
    ('submitted_before_start', 'Tests submitted before they started', 'medium', 'report', 'tejas_attempts',
     lambda t: [{'$match': {'status': 'completed', '$expr': {'$lt': ['$submitted_at', '$started_at']}}}]),
    ('submitted_after_time', 'Tests accepted more than 5 seconds after their time ended', 'medium', 'report', 'tejas_attempts',
     lambda t: [{'$match': {'status': 'completed', 'deadline': {'$gt': 0}, '$expr': {'$gt': ['$submitted_at', {'$add': ['$deadline', 5]}]}}}]),
]
SAFEGUARDS = [
    ('tejas_users', [('email', 1)], 'One staff account per email'),
    ('tejas_phone_profiles', [('phone', 1)], 'One student account per mobile number'),
    ('tejas_attempts', [('id', 1)], 'Unique attempt identity'),
    ('tejas_attempts', [('user_id', 1), ('start_key', 1)], 'One attempt per start request'),
    ('tejas_attempts', [('user_id', 1), ('set_id', 1), ('mode', 1)], 'One open attempt per student and test'),
    ('tejas_ledgers', [('id', 1)], 'One frozen score per attempt'),
    ('tejas_cohort_entries', [('cohort_id', 1), ('user_id', 1)], 'One ranking entry per student'),
    ('tejas_sessions', [('id', 1)], 'Unique sign-in session'),
    ('tejas_jobs', [('id', 1)], 'One background job per piece of work'),
    ('tejas_sets', [('id', 1)], 'Unique test identity'),
]


async def rows(coll, pipeline, fields, limit=BATCH):
    return await db[coll].aggregate(pipeline + [{'$limit': limit}, {'$project': {'_id': 1, **{f: 1 for f in fields}}}],
                                    allowDiskUse=True, maxTimeMS=QUERY_MS).to_list(limit)


async def count(coll, pipeline):
    found = await db[coll].aggregate(pipeline + [{'$count': 'n'}], allowDiskUse=True, maxTimeMS=QUERY_MS).to_list(1)
    return found[0]['n'] if found else 0


async def measure(t):
    out = {}
    for key, label, severity, action, coll, build in CHECKS:
        try:
            out[key] = {'key': key, 'label': label, 'severity': severity, 'action': action, 'found': await count(coll, build(t))}
        except Exception as exc:  # a slow or failed check must not hide the others
            log.warning('Integrity check %s not completed: %s', key, type(exc).__name__)
            out[key] = {'key': key, 'label': label, 'severity': severity, 'action': action, 'found': None}
    return out


async def safeguards():
    missing = []
    for coll, keys, label in SAFEGUARDS:
        info = await db[coll].index_information()
        if not any(v.get('unique') and list(v['key']) == keys for v in info.values()):
            missing.append(label)
    return missing


async def regrade(ids):
    from .jobs import enqueue
    for aid in ids:
        await jobs.update_one({'id': 'grade-' + aid, 'status': {'$in': ['done', 'failed']}},
                              {'$set': {'status': 'queued', 'attempts': 0, 'next_run_at': 0, 'error': '', 'integrity_retried': True}})
        changed = await attempts.update_one({'id': aid, 'status': 'completed'}, {'$set': {'grading_status': 'queued'}})
        if changed.matched_count:
            a = await attempts.find_one({'id': aid}, {'_id': 0, 'id': 1, 'user_id': 1, 'set_id': 1})
            await enqueue('grade', a['user_id'], a['set_id'], {'attempt_id': aid})
    return len(ids)


async def stash(kind, docs, reason):
    for d in docs:
        await archive.update_one({'_id': f"{kind}:{d['_id']}"}, {'$setOnInsert': {'kind': kind, 'reason': reason, 'doc': d, 'archived_at': now()}}, upsert=True)


async def dirty(cohort_ids):
    for cid in set(cohort_ids):
        await db.tejas_cohorts.update_one({'id': cid}, {'$set': {'dirty': True, 'generation': str(uuid.uuid4())}})


async def fix(key, t):
    from .attempts import finalize, ensure_grade
    coll, build = next((c[4], c[5]) for c in CHECKS if c[0] == key)
    if key == 'open_after_time':
        found = await rows(coll, build(t), ['id'])
        for a in found:
            closed = await finalize(a['id'], 'time_limit', projection={'_id': 0, 'id': 1, 'user_id': 1, 'set_id': 1, 'status': 1, 'grading_status': 1})
            await ensure_grade(closed)
        return len(found)
    if key == 'waiting_for_score':
        found = await rows(coll, build(t), ['id', 'user_id', 'set_id', 'status'])
        for a in found:
            await ensure_grade(a)
        return len(found)
    if key == 'score_failed':
        return await regrade([a['id'] for a in await rows(coll, build(t), ['id'])])
    if key == 'score_without_record':
        from .db import get
        from .corrections import freeze_ledger
        fixed = 0
        for a in await rows(coll, build(t), ['id']):
            try:  # rebuild from the sealed answers; the visible score stays untouched if that is impossible
                ledger = await freeze_ledger(await get(attempts, a['id']))
            except Exception:
                log.warning('Frozen score record could not be rebuilt for one attempt')
                continue
            fixed += (await attempts.update_one({'id': a['id'], 'status': 'completed'}, {'$set': {'summary': ledger['summary'], 'grading_status': 'ready'}})).matched_count
        return fixed
    if key == 'score_differs':
        fixed = 0
        for a in await rows(coll, build(t), ['id']):
            full = await attempts.find_one({'id': a['id']}, {'_id': 0, 'id': 1, 'user_id': 1, 'pack_id': 1, 'sealed_seq': 1, 'answers': 1,
                                                             'rules': 1, 'profile': 1, 'version': 1, 'key_version': 1})
            ledger = await db.tejas_ledgers.find_one({'id': a['id']}, {'_id': 0})
            try:
                verify_ledger({**full, 'ledger': ledger})
            except CanonicalIntegrityError:
                continue  # left visible in the report; a broken commitment is never auto-resolved
            fixed += (await attempts.update_one({'id': a['id'], 'status': 'completed'}, {'$set': {'summary': ledger['summary']}})).modified_count
        return fixed
    if key == 'peer_entry_orphan':
        found = await db.tejas_cohort_entries.aggregate(build(t) + [{'$limit': BATCH}, {'$project': {'_m': 0}}], allowDiskUse=True, maxTimeMS=QUERY_MS).to_list(BATCH)
        await stash('cohort_entry', found, 'attempt no longer exists')
        await db.tejas_cohort_entries.delete_many({'_id': {'$in': [d['_id'] for d in found]}})
        await dirty(d['cohort_id'] for d in found)
        return len(found)
    if key == 'peer_score_differs':
        found = await rows(coll, build(t), ['attempt_id', 'cohort_id'])
        for d in found:
            s = (await db.tejas_ledgers.find_one({'id': d['attempt_id']}, {'_id': 0, 'summary': 1}))['summary']
            await db.tejas_cohort_entries.update_one({'_id': d['_id']}, {'$set': {
                'score': s['score'], 'score_exact': s.get('score_exact', str(s['score'])), 'maximum': s['maximum'], 'updated_at': now(),
                'sections': [{'name': x['name'], 'score': x['score']} for x in s.get('sections') or []]}})
        await dirty(d['cohort_id'] for d in found)
        return len(found)
    if key == 'score_record_orphan':
        found = await db.tejas_ledgers.aggregate(build(t) + [{'$limit': BATCH}, {'$project': {'_m': 0}}], allowDiskUse=True, maxTimeMS=QUERY_MS).to_list(BATCH)
        await stash('ledger', found, 'attempt no longer exists')
        await db.tejas_ledgers.delete_many({'_id': {'$in': [d['_id'] for d in found]}})
        return len(found)
    if key == 'session_orphan':
        found = await rows(coll, build(t), [])
        return (await db.tejas_sessions.delete_many({'_id': {'$in': [d['_id'] for d in found]}})).deleted_count
    if key == 'job_stopped':
        found = await rows(coll, build(t), ['id'])
        done = await jobs.update_many({'_id': {'$in': [d['_id'] for d in found]}, 'status': 'failed'},
                                      {'$set': {'status': 'queued', 'attempts': 0, 'next_run_at': 0, 'error': '', 'integrity_retried': True}})
        return done.modified_count
    return 0


async def run(trigger, repair=True):
    t = now()
    try:
        await ops.update_one({'_id': 'integrity-lock', 'until': {'$lt': t}}, {'$set': {'until': t + 1800, 'trigger': trigger}}, upsert=True)
    except DuplicateKeyError:
        return None
    started = time.monotonic()
    try:
        before = await measure(t)
        fixed = {}
        if repair:
            for key, item in before.items():
                if item['action'] == 'repair' and item['found']:
                    try:
                        fixed[key] = await fix(key, t)
                    except Exception:
                        log.exception('Integrity repair %s deferred', key)
                        fixed[key] = 0
        after = await measure(now()) if fixed else before
        checks = []
        for key, item in before.items():
            left = after[key]['found']
            state = 'not_checked' if item['found'] is None else 'ok' if not item['found'] else 'fixed' if left == 0 else 'needs_attention'
            if key == 'waiting_for_score' and left and fixed.get(key):
                state = 'fixing'
            checks.append({**item, 'fixed': fixed.get(key, 0), 'left': left, 'state': state})
        report = {'last_run': now(), 'duration_s': round(time.monotonic() - started, 2), 'trigger': trigger, 'checks': checks,
                  'missing_safeguards': await safeguards(),
                  'found': sum(c['found'] or 0 for c in checks), 'fixed': sum(c['fixed'] for c in checks),
                  'needs_attention': sum(c['state'] == 'needs_attention' for c in checks)}
        await ops.update_one({'id': 'integrity'}, {'$set': {'id': 'integrity', 'report': report}}, upsert=True)
        if report['fixed']:
            await audit(ACTOR, 'Data integrity repair', 'integrity', ', '.join(f'{k}={v}' for k, v in fixed.items() if v))
        if fixed.get('waiting_for_score') or fixed.get('score_failed') or fixed.get('open_after_time'):
            from .jobs import drain_lane
            await drain_lane('grade')
        return report
    finally:
        await ops.update_one({'_id': 'integrity-lock'}, {'$set': {'until': 0}})


def due(report, at):
    last = (report or {}).get('last_run', 0)
    return not last or (at - last > 20 * 3600 and 2 <= datetime.fromtimestamp(at, IST).hour < 5)


async def scheduled():
    state = await ops.find_one({'id': 'integrity'}, {'_id': 0, 'report.last_run': 1})
    if due((state or {}).get('report'), now()):
        await run('nightly')


@router.get('')
async def report(u=Depends(owner)):
    state = await ops.find_one({'id': 'integrity'}, {'_id': 0, 'report': 1}) or {}
    lock = await ops.find_one({'_id': 'integrity-lock'}, {'until': 1}) or {}
    return {'report': state.get('report'), 'running': lock.get('until', 0) > now(),
            'schedule': 'Runs by itself once a night between 2 and 5 AM IST, and after the first deploy.'}


@router.post('/run')
async def start_run(bg: BackgroundTasks, u=Depends(owner)):
    lock = await ops.find_one({'_id': 'integrity-lock'}, {'until': 1}) or {}
    if lock.get('until', 0) > now():
        raise HTTPException(409, 'A data check is already running. Results appear here when it finishes.')
    await audit(u['id'], 'Data integrity check requested', 'integrity')
    bg.add_task(run, 'owner')
    return {'started': True}


_tasks = set()


def launch():
    task = asyncio.create_task(scheduled())
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
