"""CEO dashboard API: read-only numbers for the owner's separate dashboard project.
Every call needs the header X-CEO-Key equal to CEO_DASHBOARD_KEY. Students only (staff, TEST_ names and CEO_EXCLUDE_PHONES
left out), days in India time, answers kept for a minute or more so the dashboard never loads the site."""
import hmac, os, re, statistics, time
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from .db import db, attempts, now, INDEX_PROBLEMS
from .live_series import SERIES_ID, FIRST, LAST, TOTAL, IST
from .phone import client_ip

router = APIRouter(prefix='/api/ceo/v1', tags=['CEO dashboard (read-only)'])
profiles, contacts, events = db.tejas_phone_profiles, db.tejas_invite_contacts, db.tejas_events
DAY, WEEK, PAGE = 86400, 604800, 100
DATE = r'^\d{4}-\d{2}-\d{2}$'
DATES = [(FIRST + timedelta(days=i)).isoformat() for i in range(TOTAL)]
_cache, _wrong = {}, {}


async def ceo_key(request: Request, response: Response):
    response.headers['Cache-Control'] = 'no-store'
    want = os.environ.get('CEO_DASHBOARD_KEY', '')
    if len(want) < 24:
        raise HTTPException(503, 'CEO dashboard ki key abhi set nahi hai. Secrets mein CEO_DASHBOARD_KEY (kam se kam 24 akshar) daalo.')
    ip, slot = client_ip(request), int(time.time() // 600)
    tries = _wrong.get(ip) if ip else None
    if tries and tries[0] == slot and tries[1] >= 20:
        raise HTTPException(429, 'Bahut baar galat key aayi. 10 minute baad dobara try karo.')
    if not hmac.compare_digest(request.headers.get('x-ceo-key', '').encode(), want.encode()):
        if ip:  # an unknown caller IP is never locked out, so one bad client cannot block the real dashboard
            _wrong[ip] = (slot, (tries[1] if tries and tries[0] == slot else 0) + 1)
        if len(_wrong) > 10000:
            _wrong.clear()
        raise HTTPException(401, 'CEO key galat hai.')


def day_of(ts):
    return datetime.fromtimestamp(ts, IST).date()


def start_of(d):
    return datetime.combine(d, datetime.min.time(), IST).timestamp()


def iso(ts):
    return datetime.fromtimestamp(ts, IST).isoformat(timespec='seconds') if ts else None


def day_key(field):
    return {'$dateToString': {'format': '%Y-%m-%d', 'date': {'$toDate': {'$multiply': ['$' + field, 1000]}}, 'timezone': 'Asia/Kolkata'}}


def span(frm, to, days=30, cap=400):
    try:
        end = date.fromisoformat(to) if to else day_of(now())
        start = date.fromisoformat(frm) if frm else end - timedelta(days=days - 1)
    except ValueError:
        raise HTTPException(422, 'Date YYYY-MM-DD mein bhejo.')
    if start > end or (end - start).days >= cap:
        raise HTTPException(422, f'"from" "to" se pehle ho aur range {cap} din se kam ho.')
    return start, end


async def cached(key, build, ttl=60):
    hit = _cache.get(key)
    if hit and hit[0] > time.monotonic():
        return hit[1]
    value = await build()
    _cache[key] = (time.monotonic() + ttl, value)
    while len(_cache) > 200:
        _cache.pop(next(iter(_cache)))
    return value


def _phone(p):
    return '+91' + p if re.fullmatch(r'[6-9]\d{9}', p) else p


async def left_out():
    """Ids never counted: staff accounts, students named TEST_..., and the numbers in CEO_EXCLUDE_PHONES."""
    async def build():
        phones = [_phone(p.strip()) for p in os.environ.get('CEO_EXCLUDE_PHONES', '').split(',') if p.strip()]
        rules = [{'name': {'$regex': '^TEST_'}}, {'display_name': {'$regex': '^TEST_'}}] + ([{'phone': {'$in': phones}}] if phones else [])
        students = await profiles.distinct('id', {'$or': rules})
        return {'students': students, 'all': students + await db.tejas_users.distinct('id')}
    return await cached('left_out', build)


def since(field, marks):
    return {k: {'$sum': {'$cond': [{'$gte': [{'$ifNull': ['$' + field, 0]}, v]}, 1, 0]}} for k, v in marks.items()}


def streaks(days, today):
    """(current, best) live-day streak from a set of 'YYYY-MM-DD' days, the same way the student's own streak counts."""
    anchor = min(today, LAST)
    if FIRST <= today <= LAST and today.isoformat() not in days:
        anchor -= timedelta(days=1)
    current = 0
    while anchor >= FIRST and anchor.isoformat() in days:
        current, anchor = current + 1, anchor - timedelta(days=1)
    best = run = 0
    for d in DATES:
        run = run + 1 if d in days else 0
        best = max(best, run)
    return current, best


LIVE_DAY = {'mode': 'series_live', 'status': 'completed', '$expr': {'$eq': [day_key('submitted_at'), '$series_date']}}


@router.get('/summary')
async def summary(_=Depends(ceo_key)):
    return await cached('summary', _summary)


async def _summary():
    t = now(); today = day_of(t); s1 = start_of(today)
    marks = {'today': s1, 'last_7_days': s1 - 6 * DAY, 'last_30_days': s1 - 29 * DAY}
    out = await left_out()
    group = {'_id': None, 'total': {'$sum': 1}, 'blocked': {'$sum': {'$cond': [{'$ifNull': ['$blocked_at', False]}, 1, 0]}}}
    for name, field in (('signups', 'created_at'), ('signed_in', 'last_seen_at'), ('active', 'last_active_at')):
        group.update({f'{name}:{k}': v for k, v in since(field, marks).items()})
    for ch in ('web', 'app', 'other'):
        group['channel:' + ch] = {'$sum': {'$cond': [{'$eq': ['$signup_channel', ch]}, 1, 0]}}
    p = (await profiles.aggregate([{'$match': {'id': {'$nin': out['students']}}}, {'$group': group}]).to_list(1) or [{}])[0]
    pick = lambda name: {k: p.get(f'{name}:{k}', 0) for k in marks}
    act = (await attempts.aggregate([
        {'$match': {'user_id': {'$nin': out['all']}, 'started_at': {'$gte': marks['last_30_days'] - DAY}}},
        {'$group': {'_id': '$user_id', 'last': {'$max': {'$max': ['$started_at', {'$ifNull': ['$submitted_at', 0]}]}}}},
        {'$group': {'_id': None, **since('last', marks)}}]).to_list(1) or [{}])[0]
    who = {'user_id': {'$nin': out['all']}}
    aits = None
    if FIRST <= today <= LAST:
        q = {**who, 'series_id': SERIES_ID, 'series_date': today.isoformat(), 'mode': 'series_live', 'parent_attempt': None}
        aits = {'date': today.isoformat(), 'day': (today - FIRST).days + 1, 'live_started': await attempts.count_documents(q),
                'live_completed': await attempts.count_documents({**q, 'status': 'completed'})}
    c = (await contacts.aggregate([{'$match': who},
        {'$group': {'_id': '$user_id', 'n': {'$sum': 1}, 'today': {'$sum': {'$cond': [{'$gte': ['$at', s1]}, 1, 0]}}}},
        {'$group': {'_id': None, 'students': {'$sum': 1}, 'contacts': {'$sum': '$n'}, 'today': {'$sum': '$today'}}}]).to_list(1) or [{}])[0]
    ai = await db.tejas_ai_daily.find_one({'id': datetime.now(timezone.utc).date().isoformat()}, {'_id': 0, 'used': 1})
    return {'generated_at': iso(t), 'timezone': 'Asia/Kolkata', 'today': today.isoformat(),
            'students': {'total': p.get('total', 0), 'blocked': p.get('blocked', 0), 'by_signup_channel': {ch: p.get('channel:' + ch, 0) for ch in ('web', 'app', 'other')}},
            'signups': pick('signups'), 'active_test_takers': {k: act.get(k, 0) for k in marks},
            'active_on_site': pick('active'), 'signed_in': pick('signed_in'),
            'attempts_today': {'started': await attempts.count_documents({**who, 'started_at': {'$gte': s1}}),
                               'completed': await attempts.count_documents({**who, 'status': 'completed', 'submitted_at': {'$gte': s1}})},
            'aits_today': aits,
            'contacts': {'students_who_shared': c.get('students', 0), 'total': c.get('contacts', 0), 'today': c.get('today', 0)},
            'ai_calls_today_utc': int((ai or {}).get('used', 0))}


@router.get('/daily')
async def daily(frm: str | None = Query(None, alias='from', pattern=DATE), to: str | None = Query(None, pattern=DATE), _=Depends(ceo_key)):
    start, end = span(frm, to)
    return await cached(f'daily:{start}:{end}', lambda: _daily(start, end), 120)


async def _daily(start, end):
    out = await left_out(); a, b = start_of(start), start_of(end) + DAY
    days = [(start + timedelta(days=i)).isoformat() for i in range((end - start).days + 1)]
    rows = {d: {'date': d, 'signups': 0, 'signups_web': 0, 'signups_app': 0, 'active_test_takers': 0, 'attempts_started': 0,
                'attempts_completed': 0, 'mocks_completed': 0, 'avg_mock_score_pct': None, 'aits_live_completed': 0,
                'contacts_shared': 0, 'reports_new': 0, 'ai_calls_utc': 0} for d in days}
    who = {'user_id': {'$nin': out['all']}}

    async def each(coll, pipeline, apply):
        async for r in coll.aggregate(pipeline):
            if r['_id'] in rows:
                apply(rows[r['_id']], r)

    count_ch = lambda ch: {'$sum': {'$cond': [{'$eq': ['$signup_channel', ch]}, 1, 0]}}
    await each(profiles, [{'$match': {'id': {'$nin': out['students']}, 'created_at': {'$gte': a, '$lt': b}}},
                          {'$group': {'_id': day_key('created_at'), 'n': {'$sum': 1}, 'web': count_ch('web'), 'app': count_ch('app')}}],
               lambda row, r: row.update(signups=r['n'], signups_web=r['web'], signups_app=r['app']))
    await each(attempts, [{'$match': {**who, 'started_at': {'$gte': a, '$lt': b}}},
                          {'$group': {'_id': {'d': day_key('started_at'), 'u': '$user_id'}, 'n': {'$sum': 1}}},
                          {'$group': {'_id': '$_id.d', 'users': {'$sum': 1}, 'n': {'$sum': '$n'}}}],
               lambda row, r: row.update(active_test_takers=r['users'], attempts_started=r['n']))
    mock = {'$eq': ['$test_kind', 'mock']}
    await each(attempts, [{'$match': {**who, 'status': 'completed', 'submitted_at': {'$gte': a, '$lt': b}}},
                          {'$group': {'_id': day_key('submitted_at'), 'n': {'$sum': 1}, 'mocks': {'$sum': {'$cond': [mock, 1, 0]}},
                                      'pct': {'$avg': {'$cond': [{'$and': [mock, {'$gt': ['$summary.maximum', 0]}]},
                                                                 {'$multiply': [100, {'$divide': ['$summary.score', '$summary.maximum']}]}, None]}},
                                      'aits': {'$sum': {'$cond': [{'$and': [{'$eq': ['$mode', 'series_live']}, {'$eq': [{'$ifNull': ['$parent_attempt', None]}, None]}]}, 1, 0]}}}}],
               lambda row, r: row.update(attempts_completed=r['n'], mocks_completed=r['mocks'], aits_live_completed=r['aits'],
                                         avg_mock_score_pct=round(r['pct'], 1) if r['pct'] is not None else None))
    for coll, field, key in ((contacts, 'at', 'contacts_shared'), (db.tejas_question_reports, 'created_at', 'reports_new')):
        await each(coll, [{'$match': {**who, field: {'$gte': a, '$lt': b}}}, {'$group': {'_id': day_key(field), 'n': {'$sum': 1}}}],
                   lambda row, r, key=key: row.update({key: r['n']}))
    async for r in db.tejas_ai_daily.find({'id': {'$in': days}}, {'_id': 0, 'id': 1, 'used': 1}):
        rows[r['id']]['ai_calls_utc'] = int(r.get('used', 0))
    return {'from': start.isoformat(), 'to': end.isoformat(), 'timezone': 'Asia/Kolkata', 'rows': [rows[d] for d in days]}


@router.get('/funnel')
async def funnel(frm: str | None = Query(None, alias='from', pattern=DATE), to: str | None = Query(None, pattern=DATE), _=Depends(ceo_key)):
    start, end = span(frm, to)
    return await cached(f'funnel:{start}:{end}', lambda: _funnel(start, end), 300)


async def _funnel(start, end):
    out = await left_out(); a, b = start_of(start), start_of(end) + DAY
    born = {p['id']: p['created_at'] async for p in profiles.find(
        {'id': {'$nin': out['students']}, 'created_at': {'$gte': a, '$lt': b}}, {'_id': 0, 'id': 1, 'created_at': 1})}
    found = {}
    if born:
        async for r in attempts.aggregate([{'$match': {'user_id': {'$in': list(born)}, 'parent_attempt': None}},
                {'$group': {'_id': '$user_id', 'first': {'$min': '$started_at'},
                            'done': {'$push': {'$cond': [{'$eq': ['$status', 'completed']}, '$submitted_at', '$$REMOVE']}}}}]):
            found[r['_id']] = r
    n = dict.fromkeys(('started_in_24h', 'completed_in_24h', 'completed_in_7d', 'second_test_in_7d', 'never_started'), 0)
    waits = []
    for user, joined in born.items():
        r = found.get(user)
        if not r:
            n['never_started'] += 1
            continue
        waits.append(max(0, r['first'] - joined))
        done = sorted(x for x in r['done'] if x)
        n['started_in_24h'] += r['first'] <= joined + DAY
        n['completed_in_24h'] += bool(done) and done[0] <= joined + DAY
        n['completed_in_7d'] += bool(done) and done[0] <= joined + 7 * DAY
        n['second_test_in_7d'] += len(done) > 1 and done[1] <= joined + 7 * DAY
    return {'from': start.isoformat(), 'to': end.isoformat(), 'signed_up': len(born), **{k: int(v) for k, v in n.items()},
            'median_minutes_to_first_test': round(statistics.median(waits) / 60, 1) if waits else None}


@router.get('/retention')
async def retention(weeks: int = Query(12, ge=2, le=26), _=Depends(ceo_key)):
    return await cached(f'retention:{weeks}', lambda: _retention(weeks), 600)


async def _retention(weeks):
    out = await left_out(); today = day_of(now())
    monday = today - timedelta(days=today.weekday()) - timedelta(weeks=weeks - 1)
    a = start_of(monday)
    born = {p['id']: int((p['created_at'] - a) // WEEK) async for p in profiles.find(
        {'id': {'$nin': out['students']}, 'created_at': {'$gte': a}}, {'_id': 0, 'id': 1, 'created_at': 1})}
    seen = defaultdict(set)
    if born:
        async for r in attempts.aggregate([{'$match': {'user_id': {'$in': list(born)}, 'started_at': {'$gte': a}}},
                {'$group': {'_id': {'u': '$user_id', 'w': {'$floor': {'$divide': [{'$subtract': ['$started_at', a]}, WEEK]}}}}}]):
            seen[r['_id']['u']].add(int(r['_id']['w']))
    cohorts = []
    for w in range(weeks):
        members = [u for u, cw in born.items() if cw == w]
        cells = [round(100 * sum(1 for u in members if w + k in seen[u]) / len(members), 1) if members else None for k in range(weeks - w)]
        cohorts.append({'week_start': (monday + timedelta(weeks=w)).isoformat(), 'size': len(members), 'active_pct': cells})
    return {'weeks': weeks, 'timezone': 'Asia/Kolkata', 'cohorts': cohorts,
            'definition': 'Week 0 = sign-up week (Monday to Sunday, India time). A cell = % of that week\'s sign-ups who started at least one test in that week.'}


@router.get('/aits')
async def aits(_=Depends(ceo_key)):
    return await cached('aits', _aits, 300)


async def _aits():
    out = await left_out(); today = day_of(now())
    base = {'series_id': SERIES_ID, 'series_date': {'$in': DATES}, 'user_id': {'$nin': out['all']}, 'parent_attempt': None}
    papers = {s['series_date']: s async for s in db.tejas_sets.find({'series_id': SERIES_ID, 'series_date': {'$in': DATES}},
                                                                      {'_id': 0, 'id': 1, 'title': 1, 'status': 1, 'series_date': 1})}
    stats = defaultdict(lambda: {'live_started': 0, 'live_completed': 0, 'practice_completed': 0, 'scores': [], 'maximum': None})
    async for r in attempts.aggregate([{'$match': base}, {'$group': {'_id': {'d': '$series_date', 'm': '$mode', 's': '$status'}, 'n': {'$sum': 1},
                                                                       'scores': {'$push': '$summary.score'}, 'max': {'$max': '$summary.maximum'}}}]):
        k, s = r['_id'], stats[r['_id']['d']]
        if k['m'] == 'series_live':
            s['live_started'] += r['n']
            if k['s'] == 'completed':
                s.update(live_completed=s['live_completed'] + r['n'], maximum=r['max'], scores=[x for x in r['scores'] if isinstance(x, (int, float))])
        elif k['s'] == 'completed':
            s['practice_completed'] += r['n']
    now_buckets = dict.fromkeys((1, 7, 15, 30, 45, TOTAL), 0)
    best_buckets = dict.fromkeys((1, 7, 15, 30, 45, TOTAL), 0)
    with_day1 = defaultdict(int)
    first_day_people = 0
    async for r in attempts.aggregate([{'$match': {**base, **LIVE_DAY}}, {'$group': {'_id': '$user_id', 'days': {'$addToSet': '$series_date'}}}]):
        got = set(r['days'])
        current, best = streaks(got, today)
        for n in now_buckets:
            now_buckets[n] += current >= n
            best_buckets[n] += best >= n
        if DATES[0] in got:
            first_day_people += 1
            for d in got:
                with_day1[d] += 1
    rows = []
    for i, d in enumerate(DATES):
        paper, s = papers.get(d), stats.get(d)
        row = {'day': i + 1, 'date': d, 'paper': {'id': paper['id'], 'title': paper.get('title'), 'status': paper.get('status')} if paper else None,
               'paper_ready': bool(paper and paper.get('status') == 'published')}
        if d <= today.isoformat():
            scores = sorted((s or {}).get('scores', []))
            row.update(live_started=(s or {}).get('live_started', 0), live_completed=(s or {}).get('live_completed', 0),
                       practice_completed=(s or {}).get('practice_completed', 0), max_marks=(s or {}).get('maximum'),
                       avg_marks=round(sum(scores) / len(scores), 1) if scores else None,
                       median_marks=statistics.median(scores) if scores else None, top_marks=scores[-1] if scores else None,
                       day1_people_still_here_pct=round(100 * with_day1[d] / first_day_people, 1) if first_day_people else None)
        rows.append(row)
    nxt = next((d for d in DATES if d >= today.isoformat() and not (papers.get(d) or {}).get('status') == 'published'), None)
    return {'series_id': SERIES_ID, 'first_date': DATES[0], 'last_date': DATES[-1], 'today': today.isoformat(),
            'stage': 'prelaunch' if today < FIRST else 'finished' if today > LAST else 'live',
            'papers_ready': sum(r['paper_ready'] for r in rows), 'next_day_without_paper': nxt,
            'streak_now_at_least': {str(k): int(v) for k, v in now_buckets.items()},
            'best_streak_at_least': {str(k): int(v) for k, v in best_buckets.items()}, 'days': rows,
            'rule': 'A live day counts when its live paper was submitted on that same India-time day. Archive practice and retakes do not count.'}


@router.get('/content')
async def content(_=Depends(ceo_key)):
    return await cached('content', _content, 600)


async def _content():
    t = now()
    kinds = await db.tejas_sets.aggregate([{'$match': {'status': 'published', 'archived': {'$ne': True}}},
        {'$group': {'_id': {'exam': '$exam', 'kind': {'$ifNull': ['$test_kind', 'other']}}, 'papers': {'$sum': 1},
                    'questions': {'$sum': {'$size': {'$ifNull': ['$questions', []]}}}}}, {'$sort': {'_id.exam': 1, '_id.kind': 1}}]).to_list(500)
    jobs = await db.tejas_jobs.aggregate([{'$match': {'status': {'$in': ['queued', 'running']}}}, {'$group': {'_id': {'kind': '$kind', 'status': '$status'}, 'n': {'$sum': 1}}}]).to_list(200)
    reports = await db.tejas_question_reports.aggregate([{'$group': {'_id': '$status', 'n': {'$sum': 1}}}]).to_list(50)
    return {'published': [{'exam': k['_id'].get('exam'), 'test_kind': k['_id']['kind'], 'papers': k['papers'], 'questions': k['questions']} for k in kinds],
            'papers_total': sum(k['papers'] for k in kinds), 'questions_total': sum(k['questions'] for k in kinds),
            'published_last_7_days': await db.tejas_sets.count_documents({'status': 'published', 'published_at': {'$gte': t - 7 * DAY}}),
            'aits_days_ready': await db.tejas_sets.count_documents({'series_id': SERIES_ID, 'series_date': {'$in': DATES}, 'status': 'published'}),
            'jobs_waiting': [{'kind': j['_id'].get('kind'), 'status': j['_id']['status'], 'count': j['n']} for j in jobs],
            'question_reports': {str(r['_id']): r['n'] for r in reports}}


@router.get('/health')
async def health(_=Depends(ceo_key)):
    return await cached('health', _health, 60)


async def _health():
    t = now()
    failed = await db.tejas_jobs.aggregate([{'$match': {'status': 'failed'}}, {'$sort': {'created_at': -1}},
        {'$group': {'_id': '$kind', 'count': {'$sum': 1}, 'last_at': {'$first': '$created_at'}, 'last_error': {'$first': '$error'}}}]).to_list(100)
    storage = None
    try:
        from .storage_health import _last, summary as storage_summary
        if _last.get('result'):
            s = storage_summary(_last['result'])
            storage = {'mode': s['mode'], 'checked_at': iso(s['checked_at']), 'alert': s['backup']['alert']}
    except Exception:
        storage = None
    return {'server_time': iso(t), 'grading_failed': await attempts.count_documents({'grading_status': 'failed'}),
            'grading_waiting_over_5_min': await attempts.count_documents({'status': 'completed', 'grading_status': {'$nin': ['ready', 'failed']}, 'submitted_at': {'$lt': t - 300}}),
            'jobs_failed': [{'kind': j['_id'], 'count': j['count'], 'last_at': iso(j['last_at']), 'last_error': (j.get('last_error') or '')[:200]} for j in failed],
            'storage': storage, 'index_problems': len(INDEX_PROBLEMS)}


@router.get('/alerts')
async def alerts(_=Depends(ceo_key)):
    return await cached('alerts', _alerts, 60)


async def _alerts():
    """Things the CEO should hear about now (brief section 5.5). The dashboard decides how to send them."""
    from .astra import quota_status
    t = now(); today = day_of(t); hour = datetime.fromtimestamp(t, IST).hour; found = []
    add = lambda code, level, title, value=None: found.append({'code': code, 'level': level, 'title': title, 'value': value})
    tomorrow = today + timedelta(days=1)
    if FIRST <= tomorrow <= LAST and not await db.tejas_sets.count_documents(
            {'series_id': SERIES_ID, 'series_date': tomorrow.isoformat(), 'status': 'published'}):
        add('aits_tomorrow_no_paper', 'red' if hour >= 18 else 'amber', f'Kal ({tomorrow.isoformat()}) ka AITS paper abhi Live nahi hai.', tomorrow.isoformat())
    h = await _health()
    if h['grading_failed']:
        add('grading_failed', 'red', f"{h['grading_failed']} test ki checking fail hui hai.", h['grading_failed'])
    slow = await attempts.count_documents({'status': 'completed', 'grading_status': {'$nin': ['ready', 'failed']}, 'submitted_at': {'$lt': t - 900}})
    if slow:
        add('grading_waiting', 'red', f'{slow} test 15 minute se zyada se checking ka intezaar kar rahe hain.', slow)
    if (h['storage'] or {}).get('alert'):
        add('storage', 'red', 'Nayi files Supabase mein nahi ja pa rahi hain.', h['storage']['mode'])
    jobs = await db.tejas_jobs.count_documents({'status': 'failed', 'created_at': {'$gte': t - DAY}})
    if jobs:
        add('jobs_failed_24h', 'amber', f'Pichhle 24 ghante mein {jobs} background kaam fail hue.', jobs)
    q = await quota_status()
    if q['limit'] and q['used'] >= 0.8 * q['limit']:
        add('ai_near_limit', 'red' if q['used'] >= q['limit'] else 'amber', f"AI calls aaj {q['used']}/{q['limit']} ho gaye.", q['used'])
    if hour >= 21:
        out = await left_out(); s1 = start_of(today)
        week = await profiles.count_documents({'id': {'$nin': out['students']}, 'created_at': {'$gte': s1 - 7 * DAY, '$lt': s1}})
        got = await profiles.count_documents({'id': {'$nin': out['students']}, 'created_at': {'$gte': s1}})
        if week >= 14 and got < 0.5 * week / 7:
            add('signups_low', 'amber', f'Aaj sirf {got} sign-up, pichhle 7 din ka average {round(week / 7, 1)} hai.', got)
    level = 'red' if any(a['level'] == 'red' for a in found) else 'amber' if found else 'green'
    return {'generated_at': iso(t), 'level': level, 'alerts': found}


def _who(q):
    q = q.strip()
    digits = re.sub(r'\D', '', q)
    if digits and len(digits) >= 3 and not re.search(r'[A-Za-z]', q):
        return {'phone': {'$regex': re.escape(digits)}}
    return {'$or': [{'name': {'$regex': re.escape(q), '$options': 'i'}}, {'display_name': {'$regex': re.escape(q), '$options': 'i'}}]} if q else {}


def _student(p, tests=None, shared=0):
    tests = tests or {}
    return {'id': p['id'], 'phone': p.get('phone'), 'name': p.get('display_name') or p.get('name') or '', 'exam': p.get('exam'),
            'signed_up_at': iso(p.get('created_at')), 'signup_channel': p.get('signup_channel'), 'signup_device': p.get('signup_device'),
            'signup_source': p.get('signup_source'), 'last_signin_at': iso(p.get('last_seen_at')), 'last_active_at': iso(p.get('last_active_at')),
            'blocked': bool(p.get('blocked_at')), 'attempts': tests.get('n', 0), 'completed': tests.get('done', 0),
            'last_attempt_at': iso(tests.get('last')), 'contacts_shared': shared}


PROFILE = {'_id': 0, 'pin_hash': 0, 'pin_version': 0}


@router.get('/students')
async def students(page: int = Query(1, ge=1, le=100000), q: str = Query('', max_length=40), sort: Literal['new', 'active'] = 'new', _=Depends(ceo_key)):
    out = await left_out()
    match = {'id': {'$nin': out['students']}, **_who(q)}
    total = await profiles.count_documents(match)
    order = [('created_at', -1)] if sort == 'new' else [('last_active_at', -1), ('last_seen_at', -1)]
    rows = await profiles.find(match, PROFILE).sort(order).skip((page - 1) * PAGE).limit(PAGE).to_list(PAGE)
    ids = [p['id'] for p in rows]
    tests = {r['_id']: r async for r in attempts.aggregate([{'$match': {'user_id': {'$in': ids}}}, {'$group': {'_id': '$user_id', 'n': {'$sum': 1},
             'done': {'$sum': {'$cond': [{'$eq': ['$status', 'completed']}, 1, 0]}}, 'last': {'$max': '$started_at'}}}])}
    shared = {r['_id']: r['n'] async for r in contacts.aggregate([{'$match': {'user_id': {'$in': ids}}}, {'$group': {'_id': '$user_id', 'n': {'$sum': 1}}}])}
    return {'total': total, 'page': page, 'pages': max(1, -(-total // PAGE)), 'items': [_student(p, tests.get(p['id']), shared.get(p['id'], 0)) for p in rows]}


@router.get('/students/{id}')
async def student(id: str, _=Depends(ceo_key)):
    p = await profiles.find_one({'id': id}, PROFILE)
    if not p or id in (await left_out())['students']:
        raise HTTPException(404, 'Yeh student nahi mila.')
    tests = await attempts.find({'user_id': id}, {'_id': 0, 'id': 1, 'title': 1, 'exam': 1, 'mode': 1, 'test_kind': 1, 'status': 1, 'started_at': 1,
                                                  'submitted_at': 1, 'series_date': 1, 'parent_attempt': 1, 'summary.score': 1, 'summary.maximum': 1,
                                                  'summary.accuracy': 1}).sort('started_at', -1).limit(300).to_list(300)
    live = {a['series_date'] for a in tests if a.get('mode') == 'series_live' and a.get('status') == 'completed' and not a.get('parent_attempt')
            and a.get('submitted_at') and day_of(a['submitted_at']).isoformat() == a.get('series_date')}
    current, best = streaks(live, day_of(now()))
    friends = await contacts.find({'user_id': id}, {'_id': 0, 'name': 1, 'phone': 1, 'at': 1}).sort('at', -1).limit(500).to_list(500)
    used = await events.aggregate([{'$match': {'user_id': id, 'at': {'$gte': now() - 90 * DAY}}}, {'$group': {'_id': {'name': '$name', 'page': '$props.page', 'tool': '$props.tool'}, 'n': {'$sum': 1}}},
                                   {'$sort': {'n': -1}}, {'$limit': 50}]).to_list(50)
    done = [a for a in tests if a.get('status') == 'completed']
    return {**_student(p, {'n': len(tests), 'done': len(done), 'last': tests[0]['started_at'] if tests else None}, len(friends)),
            'aits': {'live_days_done': len(live), 'current_streak': current, 'best_streak': best},
            'attempts_shown': len(tests),
            'tests': [{'id': a['id'], 'title': a.get('title'), 'exam': a.get('exam'), 'mode': a.get('mode'), 'test_kind': a.get('test_kind'),
                       'status': a.get('status'), 'started_at': iso(a.get('started_at')), 'submitted_at': iso(a.get('submitted_at')),
                       'series_date': a.get('series_date'), 'retake': bool(a.get('parent_attempt')),
                       'score': (a.get('summary') or {}).get('score'), 'maximum': (a.get('summary') or {}).get('maximum'),
                       'accuracy': (a.get('summary') or {}).get('accuracy')} for a in tests],
            'contacts': [{'name': f.get('name', ''), 'phone': f['phone'], 'shared_at': iso(f['at'])} for f in friends],
            'usage_last_90_days': [{**u['_id'], 'count': u['n']} for u in used]}


@router.get('/contacts')
async def contact_list(page: int = Query(1, ge=1, le=100000), q: str = Query('', max_length=40), _=Depends(ceo_key)):
    out = await left_out()
    match = {'user_id': {'$nin': out['all']}}
    digits = re.sub(r'\D', '', q)
    if digits:
        match['phone'] = {'$regex': re.escape(digits)}
    total = await contacts.count_documents(match)
    rows = await contacts.find(match, {'_id': 0}).sort('at', -1).skip((page - 1) * PAGE).limit(PAGE).to_list(PAGE)
    people = {p['id']: p async for p in profiles.find({'id': {'$in': list({r['user_id'] for r in rows})}}, {'_id': 0, 'id': 1, 'phone': 1, 'name': 1, 'display_name': 1})}
    joined = {p['phone']: p async for p in profiles.find({'phone': {'$in': [r['phone'] for r in rows]}, 'id': {'$nin': out['students']}},
                                                       {'_id': 0, 'id': 1, 'phone': 1, 'created_at': 1})}
    items = []
    for r in rows:
        by, friend = people.get(r['user_id'], {}), joined.get(r['phone'])
        items.append({'name': r.get('name', ''), 'phone': r['phone'], 'shared_at': iso(r['at']),
                      'shared_by': {'id': r['user_id'], 'phone': by.get('phone'), 'name': by.get('display_name') or by.get('name') or ''},
                      'already_student': bool(friend), 'joined_after_share': bool(friend and friend.get('created_at', 0) > r['at']),
                      'student_id': (friend or {}).get('id')})
    return {'total': total, 'page': page, 'pages': max(1, -(-total // PAGE)), 'items': items}


@router.get('/events')
async def event_counts(frm: str | None = Query(None, alias='from', pattern=DATE), to: str | None = Query(None, pattern=DATE), _=Depends(ceo_key)):
    start, end = span(frm, to)
    return await cached(f'events:{start}:{end}', lambda: _events(start, end), 120)


async def _events(start, end):
    out = await left_out(); a, b = start_of(start), start_of(end) + DAY
    match = {'at': {'$gte': a, '$lt': b}, 'user_id': {'$nin': out['all']}}
    days = await events.aggregate([{'$match': match}, {'$group': {'_id': {'d': day_key('at'), 'name': '$name'}, 'n': {'$sum': 1},
                                                                   'people': {'$addToSet': {'$ifNull': ['$user_id', '$vid']}}}},
                                   {'$project': {'n': 1, 'people': {'$size': '$people'}}}, {'$sort': {'_id.d': 1}}]).to_list(20000)
    top = await events.aggregate([{'$match': match}, {'$group': {'_id': {'name': '$name', 'page': '$props.page', 'tool': '$props.tool'}, 'n': {'$sum': 1}}},
                                  {'$sort': {'n': -1}}, {'$limit': 50}]).to_list(50)
    return {'from': start.isoformat(), 'to': end.isoformat(), 'timezone': 'Asia/Kolkata',
            'daily': [{'date': d['_id']['d'], 'name': d['_id']['name'], 'count': d['n'], 'people': d['people']} for d in days],
            'top': [{**t['_id'], 'count': t['n']} for t in top]}
