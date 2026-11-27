"""Class statistics for one paper: what everyone did on each question, and the topper / top 10% / average totals.
Built in a background job, never on a request. One entry per student: their first released attempt on the same paper, key and rules."""
import hashlib, math, time, uuid
from array import array
from collections import Counter
from pymongo.errors import DuplicateKeyError
from .db import db, attempts, sets, get, now
from .cohorts import identity
from .analysis import Group, entry_of, frame_for, stretches, clock
from .analysis_rules import VERSION
from tejas_core import score_attempt

entries = db.tejas_class_entries
stats = db.tejas_class_stats
cache = db.tejas_analysis
timelines = db.tejas_attempt_timeline
REFRESH_SECONDS = 600
SMALL_CLASS, SMALL_SECONDS = 300, 5  # a small class is cheap to rebuild, so a new finisher is counted at once
BACKFILL_SECONDS = 240
MODES = ('practice', 'series_live')


def class_id(a):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jeelive-class:' + identity(a) + ':' + ('series_live' if a.get('mode') == 'series_live' else 'practice')))


def handle(set_id, user_id):
    """An opaque name for a student on one paper: never the phone number or the account id."""
    return hashlib.sha256((set_id + user_id).encode()).hexdigest()[:16]


def learner(h):
    return 'Learner ' + h[:8].upper()


async def hints_for(set_id):
    paper = await sets.find_one({'id': set_id}, {'_id': 0, 'questions.id': 1, 'questions.ai_solution.solution.difficulty': 1}) or {}
    return {q['id']: ((q.get('ai_solution') or {}).get('solution') or {}).get('difficulty') for q in paper.get('questions', []) if q.get('ai_solution')}


async def record(a, t=None, touch=True):
    """Keep this student's first released attempt on the paper as short codes. Safe to call again. Returns the class id."""
    if a.get('mode') not in MODES or a.get('status') != 'completed' or not a.get('ledger') or a.get('test_kind') == 'choice':
        return None
    if a.get('competition_end', 0) > (now() if t is None else t):
        return None
    # Owner and reviewer runs are checks, not students.
    if await db.tejas_users.find_one({'id': a['user_id']}, {'_id': 1}):
        return None
    cid = class_id(a)
    result = score_attempt(a)
    by = {q['id']: q for q in result['questions']}
    doc = await timelines.find_one({'_id': a['id']}, {'_id': 0, 'events': 1}) or {}
    start, end = clock(a)
    entry = entry_of(a, result['questions'], by, stretches(doc.get('events'), set(by), start, end), result['summary'])
    row = {'cohort_id': cid, 'user_id': a['user_id'], 'attempt_id': a['id'], 'handle': handle(a['set_id'], a['user_id']),
           'submitted_at': a['submitted_at'], 'score': entry['score'], 'entry': entry, 'stale': False, 'updated_at': now()}
    key = cid + ':' + a['user_id']
    try:
        await entries.update_one({'_id': key}, {'$setOnInsert': row}, upsert=True)
    except DuplicateKeyError:
        pass
    # An earlier attempt of the same student, or a late time record of this one, replaces what is stored.
    await entries.update_one({'_id': key, '$or': [{'submitted_at': {'$gt': a['submitted_at']}}, {'attempt_id': a['id'], 'stale': True}]}, {'$set': row})
    change = {'set_id': a['set_id'], 'sample': a['id']}
    if touch:
        change.update(dirty=True, generation=str(uuid.uuid4()))
    await stats.update_one({'_id': cid}, {'$set': change, '$setOnInsert': {'created_at': now(), 'computed_at': 0}}, upsert=True)
    await attempts.update_one({'id': a['id']}, {'$set': {'class_indexed': cid}})
    return cid


async def forget(attempt_id):
    """A late time record arrived: the saved analysis and this student's class entry are rebuilt on the next read."""
    await cache.delete_many({'attempt_id': attempt_id})
    await entries.update_one({'attempt_id': attempt_id}, {'$set': {'stale': True}})
    await attempts.update_one({'id': attempt_id}, {'$unset': {'class_indexed': ''}})


async def ensure(cid, user_id, set_id, bg=None):
    """The class statistics as they stand. A rebuild is queued at most once in 10 minutes, or at once while a backlog remains."""
    from .jobs import enqueue, run_job
    head = await stats.find_one({'_id': cid}, {'dirty': 1, 'computed_at': 1, 'n': 1, 'pending': 1, 'rules_version': 1})
    old = bool(head) and bool(head.get('computed_at')) and head.get('rules_version') != VERSION
    if head and (head.get('dirty') or head.get('pending') or old):
        t, built = now(), head.get('computed_at') or 0
        wait = SMALL_SECONDS if (head.get('n') or 0) < SMALL_CLASS else REFRESH_SECONDS
        if head.get('pending') or old or t - built >= wait:
            job = await enqueue('class_stats', user_id, set_id, {'cohort_id': cid, 'key': f'{cid}-{int(built)}-{int(t // wait)}-{VERSION}'})
            if bg is not None and job['status'] in ('queued', 'running'):
                bg.add_task(run_job, job['id'])
    return head


async def backfill(job, a, cid, stop):
    """Released attempts of this paper that are not counted yet: live papers are counted only after their window closes."""
    from .jobs import require_lease
    match = {'set_id': a['set_id'], 'version': a['version'], 'status': 'completed', 'grading_status': 'ready', 'mode': a['mode'],
             'class_indexed': {'$exists': False}, 'class_skipped': {'$ne': cid}}
    while time.monotonic() < stop:
        batch = await attempts.find(match, {'_id': 0, 'id': 1}).limit(200).to_list(200)
        if not batch:
            return 0
        await require_lease(job)
        for row in batch:
            other = await get(attempts, row['id'])
            if not other.get('ledger') or class_id(other) != cid or not await record(other, other['_database_now'], touch=False):
                await attempts.update_one({'id': row['id']}, {'$set': {'class_skipped': cid}})
    return await attempts.count_documents(match)


async def refresh(job):
    from .jobs import require_lease
    cid = job['payload']['cohort_id']
    head = await stats.find_one({'_id': cid}, {'sample': 1, 'generation': 1})
    if not head:
        return 'No class to build.'
    a = await get(attempts, head['sample'])
    pending = await backfill(job, a, cid, time.monotonic() + BACKFILL_SECONDS)
    questions, minutes = a['questions'], (a.get('rules') or {}).get('minutes') or 0
    n = len(questions)
    count = [[0, 0, 0] for _ in range(n)]
    options = [Counter() for _ in range(n)]
    solved = [array('I') for _ in range(n)]
    spent = [[0, 0] for _ in range(n)]
    board, scores = [], Counter()
    # Pass 1: what the class did on each question.
    async for e in entries.find({'cohort_id': cid}, {'entry': 1, 'score': 1, 'handle': 1, 'submitted_at': 1}).batch_size(200):
        x = e['entry']
        if len(x['o']) != n:
            continue
        board.append((-e['score'], e['submitted_at'], e['_id'], e['handle']))
        scores[e['score']] += 1
        timed = bool(x.get('t'))
        for i, o in enumerate(x['o']):
            k = 'cws'.find(o)
            if k >= 0:
                count[i][k] += 1
            if x['r'][i]:
                options[i][x['r'][i]] += 1
            if timed and o != 'u':
                spent[i][0] += x['t'][i]
                spent[i][1] += 1
                if o == 'c' and x['t'][i] > 0:
                    solved[i].append(x['t'][i])
    board.sort()
    q = {}
    for i, item in enumerate(questions):
        c, w, s = count[i]
        times = sorted(solved[i])
        q[item['id']] = {'n': c + w + s, 'correct': c, 'incorrect': w, 'skipped': s, 'attempted': c + w, 'options': dict(options[i]),
                         'solvers': len(times), 'median': (times[(len(times) - 1) // 2] + times[len(times) // 2]) / 2 if times else None,
                         'avg': round(spent[i][0] / spent[i][1]) if spent[i][1] else None, 'topper': None}
    frame = frame_for(questions, q, minutes, a['rules'], await hints_for(a['set_id']))
    duration = round(minutes * 60)
    first = board[0][2] if board else None
    top = {b[2] for b in board[:max(1, math.ceil(len(board) / 10))]}
    groups = {k: Group(frame, duration) for k in ('topper', 'top10', 'average')}
    await require_lease(job)
    # Pass 2: totals of the topper, the top 10% and everyone.
    async for e in entries.find({'cohort_id': cid}, {'entry': 1}).batch_size(200):
        x = e['entry']
        if len(x['o']) != n:
            continue
        groups['average'].add(x)
        if e['_id'] in top:
            groups['top10'].add(x)
        if e['_id'] == first:
            groups['topper'].add(x)
            if x.get('t'):
                for i, item in enumerate(questions):
                    q[item['id']]['topper'] = x['t'][i]
    leaders = []
    for i, b in enumerate(board[:10]):
        leaders.append({'handle': b[3], 'learner': learner(b[3]), 'score': -b[0], 'rank': leaders[-1]['rank'] if i and -b[0] == leaders[-1]['score'] else i + 1})
    maximum = score_attempt(a)['summary']['maximum']
    await require_lease(job)
    await stats.update_one({'_id': cid}, {'$set': {
        'n': len(board), 'scores': sorted([s, c] for s, c in scores.items()), 'q': q, 'frame': frame, 'duration': duration, 'maximum': maximum,
        'groups': {k: {**g.profile(maximum), 'qt': g.times()} for k, g in groups.items()}, 'leaders': leaders, 'pending': pending,
        'computed_at': now(), 'rules_version': VERSION}})
    await stats.update_one({'_id': cid, 'generation': head.get('generation')}, {'$set': {'dirty': False}})
    return f'Class statistics built from {len(board)} students. Still to count: {pending}.'
