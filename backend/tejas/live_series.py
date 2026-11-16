from collections import Counter
from datetime import date, datetime, time, timedelta
from typing import Literal
from zoneinfo import ZoneInfo
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from pymongo.errors import DuplicateKeyError
from .auth import current, owner, maybe_current
from .db import db, sets, attempts, get, now, audit
from .canonical import database_now

router = APIRouter(prefix='/api', tags=['All India series'])
SERIES_ID = 'all-india-jee-2026-27'
# The owner's dates: 50 papers, 9 December 2026 to 27 January 2027.
FIRST = date(2026, 12, 9)
TOTAL = 50
LAST = FIRST + timedelta(days=TOTAL - 1)
IST = ZoneInfo('Asia/Kolkata')


def nice(d):
    return f'{d.day} {d:%B %Y}'


JEE_TIMES = {'open_time': '00:01', 'last_start': '20:59', 'close_time': '23:59'}


def window(day, cfg=None):
    cfg = cfg or JEE_TIMES
    d = date.fromisoformat(day)
    out = {}
    for key, value, offset in (('opens_at', cfg['open_time'], 0), ('last_start_at', cfg['last_start'], 0),
                               ('closes_at', cfg.get('close_time', '23:59'), 0), ('archive_at', '00:00', 1)):
        h, m = map(int, value.split(':'))
        out[key] = datetime.combine(d + timedelta(days=offset), time(h, m), IST).timestamp()
    return out


def set_window(s):
    """A series paper keeps the day window it was given; JEE papers from before windows were stored use the JEE times."""
    return s.get('series_window') or window(s['series_date'])


def phase(day, timestamp, w=None):
    w = w or window(day)
    if timestamp < w['opens_at']: return 'upcoming'
    if timestamp <= w['last_start_at']: return 'live'
    if timestamp < w['closes_at']: return 'start_closed'
    if timestamp < w['archive_at']: return 'ended'
    return 'archive'


def series_mode(s, timestamp):
    if not s.get('series_id') or not s.get('series_date'): return None
    state = phase(s['series_date'], timestamp, set_window(s))
    return 'series_practice' if state == 'archive' else 'series_live'


def clock(t):
    d = datetime.fromtimestamp(t, IST)
    return f"{d.hour % 12 or 12}:{d:%M} {'AM' if d.hour < 12 else 'PM'}"


def guard_start(s, timestamp, early=False):
    if not s.get('series_id') or not s.get('series_date'): return
    w = set_window(s)
    state = phase(s['series_date'], timestamp, w)
    # The owner may take a paper before its day; it then counts like a live attempt of that day.
    if early and state == 'upcoming': return
    if state not in ('live', 'archive'):
        raise HTTPException(409, f"Live starts are allowed from {clock(w['opens_at'])} through {clock(w['last_start_at'])} IST on the scheduled day. Archive practice opens the following day.")


def paper_pattern(s):
    r = s.get('rules', {})
    return {'count': len(s.get('questions', [])), 'minutes': r.get('minutes'), 'correct': r.get('correct'), 'wrong': r.get('wrong')}


def valid_paper(s):
    if s.get('series_pattern'):
        return paper_pattern(s) == s['series_pattern'] and not s.get('rules', {}).get('bonus_rule')
    qs, r = s.get('questions', []), s.get('rules', {})
    shape = Counter((q.get('subject', '').lower().replace('maths', 'mathematics'), q.get('type')) for q in qs)
    required = Counter({(subject, kind): count for subject in ('physics', 'chemistry', 'mathematics') for kind, count in [('mcq', 20), ('integer', 5)]})
    return (s.get('exam') == 'JEE Main' and len(qs) == 75 and shape == required
            and r.get('minutes') == 180 and not r.get('bonus_rule')
            and all((q.get('scoring') or r).get('correct') == 4 and (q.get('scoring') or r).get('wrong') == -1
                    and (q.get('scoring') or r).get('skipped', 0) == 0 and not q.get('bonus')
                    and q.get('disposition', 'standard') == 'standard' for q in qs))


def series_problem(mock):
    """Why a book mock cannot be an All India paper, or None."""
    r = mock.rules or {}
    if not r:
        return 'Confirm this mock’s rules first.'
    if r.get('minutes') != 180 or r.get('correct') != 4 or r.get('wrong') != -1 or r.get('mechanic') != 'all_compulsory' or r.get('section_scoring') or r.get('bonus_count'):
        return 'All India papers need 180 minutes and +4 / −1 / 0 marking.'
    paper = {'exam': 'JEE Main', 'rules': {'minutes': 180, 'correct': 4, 'wrong': -1, 'skipped': 0},
             'questions': [{'subject': q.get('subject', ''), 'type': q.get('type')} for q in mock.questions]}
    return None if valid_paper(paper) else 'All India papers need 75 questions: 20 MCQ + 5 numerical in each of Physics, Chemistry and Mathematics.'


async def schedule_data(studio=False, early=False):
    from .content import permitted
    t = await database_now()
    projection = {'_id': 0, 'questions': 0, 'allowed_emails': 0, 'allowed_phones': 0}
    rows = await sets.find({'series_id': SERIES_ID}, projection).limit(TOTAL + 20).to_list(TOTAL + 20)
    by_day = {s['series_date']: s for s in rows}
    slots = []
    for i in range(TOTAL):
        day = (FIRST + timedelta(days=i)).isoformat()
        s = by_day.get(day)
        ready = bool(s and s['status'] == 'published' and permitted(s, series_schedule=True, at=t))
        w = (s or {}).get('series_window') or window(day)
        state = phase(day, t, w)
        soon = early and ready and state == 'upcoming'
        visible = ready and (state != 'upcoming' or soon)
        slots.append({'day': i + 1, 'date': day, **w, 'state': state, 'early': soon,
                      'ready': ready if studio or soon or state != 'upcoming' else False, 'set_id': s['id'] if s and (studio or visible) else None,
                      'title': s['title'] if s and (studio or visible) else f'All India JEE Mains · Test {i + 1:02d}',
                      'can_start': ready and (state in ('live', 'archive') or soon),
                      **({'revision': s['revision'], 'publication_status': s['status'], 'series_import': s.get('series_import', False), 'live_enabled': s.get('live_enabled', False)} if studio and s else {})})
    today = datetime.fromtimestamp(t, IST).date().isoformat()
    return {'id': SERIES_ID, 'title': 'All India JEE Mains Test Series', 'first_date': FIRST.isoformat(),
            'last_date': LAST.isoformat(), 'total': TOTAL, 'timezone': 'Asia/Kolkata', 'server_now': t,
            'today': today, 'slots': slots, 'today_slot': next((s for s in slots if s['date'] == today), None)}


@router.get('/series/all-india-jee')
async def catalogue(request: Request):
    u = await maybe_current(request)
    return await schedule_data(early=(u or {}).get('role') == 'owner')


@router.get('/series/all-india-jee/history')
async def history(page: int = Query(1, ge=1, le=10000), u=Depends(current)):
    from .my_tests import history_item
    t = await database_now()
    match = {'user_id': u['id'], 'series_id': SERIES_ID, 'mode': {'$in': ['series_live', 'series_practice']}}
    fields = {k: 1 for k in ('id', 'set_id', 'title', 'exam', 'mode', 'version', 'started_at', 'submitted_at', 'deadline', 'status', 'count', 'summary', 'answers', 'competition_end', 'series_date')}
    rows = await attempts.find(match, {'_id': 0, **fields}).sort('started_at', -1).skip((page-1)*20).limit(20).to_list(20)
    items = [{**history_item(a, t).model_dump(), 'series_date': a['series_date']} for a in rows]
    latest = await attempts.find_one({**match, 'status': 'completed', 'summary': {'$ne': None}, 'competition_end': {'$not': {'$gt': t}}}, {'_id': 0, 'id': 1}, sort=[('submitted_at', -1)])
    return {'items': items, 'page': page, 'total': await attempts.count_documents(match), 'latest_result_id': (latest or {}).get('id')}


async def series_book_mocks():
    """Mocks of books uploaded to the All India Test Series, in book and printed order."""
    from .book_models import BookMock
    books = await db.tejas_books.find({'payload.destination.series': True, 'payload.destination.series_id': {'$in': [None, SERIES_ID]}, 'removed': False, 'archived': {'$ne': True}},
                                      {'_id': 1, 'payload.title': 1, 'state': 1}).sort('created_at', 1).to_list(100)
    title = {b['_id']: b['payload']['title'] for b in books}
    rank = {b['_id']: i for i, b in enumerate(books)}
    rows = await db.tejas_book_mocks.find({'book_id': {'$in': list(title)}}, {'questions.subject': 1, 'questions.type': 1, 'rules': 1, 'label': 1, 'order': 1,
        'state': 1, 'set_id': 1, 'series_date': 1, 'book_id': 1, 'issues': {'$slice': 1}, 'publish_requested': 1}).to_list(5000)
    rows.sort(key=lambda m: (rank[m['book_id']], m['order']))
    built = {s['id']: s for s in await sets.find({'id': {'$in': [m['set_id'] for m in rows if m.get('set_id')]}}, {'_id': 0, 'id': 1, 'series_date': 1, 'revision': 1}).to_list(None)}
    out = []
    for m in rows:
        s = built.get(m.get('set_id'))
        ready = m['state'] == 'ready' and not s
        out.append({'id': m['_id'], 'book_id': m['book_id'], 'book_title': title[m['book_id']], 'label': m['label'], 'order': m['order'],
                    'state': m['state'], 'set_id': s['id'] if s else None, 'series_date': s.get('series_date') if s else m.get('series_date'),
                    'pending': bool(not s and m.get('series_date')), 'issue': (m.get('issues') or [''])[0],
                    'problem': series_problem(BookMock.from_mongo({**m, 'issues': []})) if ready else None})
    return [{'id': b['_id'], 'title': b['payload']['title'], 'state': b['state']} for b in books], out


@router.get('/studio/all-india-jee')
async def studio_schedule(u=Depends(owner)):
    from .imports import imports
    data = await schedule_data(studio=True)
    t = await database_now()
    rows = await sets.find({'exam': 'JEE Main', '$or': [{'status': 'published'}, {'series_import': True}], 'audience': 'all', 'qa_only': {'$ne': True}, 'competition': {'$ne': True}, 'archived': {'$ne': True}}, {'_id': 0, 'questions.ai_solution': 0}).limit(500).to_list(500)
    used = set(await attempts.distinct('set_id', {'set_id': {'$in': [s['id'] for s in rows]}, 'mode': {'$ne': 'preview'}}))
    data['papers'] = [{'id': s['id'], 'title': s['title'], 'revision': s['revision'], 'series_date': s.get('series_date'), 'kind': 'paper'} for s in rows if valid_paper(s) and s['id'] not in used and (not s.get('series_date') or t < window(s['series_date'])['opens_at'])]
    ready = await imports.find({'status': 'ready', 'exam': 'JEE Main', 'qa_only': {'$ne': True}, 'archived': {'$ne': True}}, {'_id': 0}).limit(500).to_list(500)
    existing = set(await sets.distinct('id', {'id': {'$in': [r['id'] for r in ready]}}))
    data['papers'] = [{'id': r['id'], 'title': r['title'], 'revision': 0, 'kind': 'private_import'} for r in ready if r['id'] not in existing and not r.get('issues') and valid_paper({'exam': r['exam'], 'questions': r.get('questions', []), 'rules': {'minutes': r.get('duration_minutes'), 'correct': 4, 'wrong': -1, 'skipped': 0}})] + data['papers']
    books, mocks = await series_book_mocks()
    data['books'], data['book_mocks'] = books, mocks
    data['papers'] = [{'id': m['id'], 'title': f"{m['book_title']} · {m['label']}", 'revision': 0, 'kind': 'book_mock'}
                      for m in mocks if m['state'] == 'ready' and not m['set_id'] and not m['series_date'] and not m['problem']] + data['papers']
    pending = {m['series_date']: m for m in mocks if m['pending']}
    for slot in data['slots']:
        if not slot['set_id'] and slot['date'] in pending:
            m = pending[slot['date']]
            slot['pending'] = {'mock_id': m['id'], 'title': f"{m['book_title']} · {m['label']}"}
    return data


class Assignment(BaseModel):
    model_config = ConfigDict(extra='forbid')
    set_id: str = Field(min_length=1, max_length=100)
    date: date
    expected_revision: int = Field(ge=0)
    kind: Literal['paper', 'private_import', 'book_mock'] = 'paper'
    replace: bool = False


class Fill(BaseModel):
    model_config = ConfigDict(extra='forbid')
    book_id: str = Field(min_length=1, max_length=100)
    start_date: date
    replace: bool = False


class Clear(BaseModel):
    model_config = ConfigDict(extra='forbid')
    book_id: str = Field(default='', max_length=100)


def check_range(day):
    if not FIRST <= day <= LAST:
        raise HTTPException(422, f'Choose a date from {nice(FIRST)} to {nice(LAST)}.')


async def set_problem(s, day):
    """Why this built paper cannot take this day (None when it can); checked before any day is freed."""
    if (s['status'] != 'published' and not s.get('series_import')) or s.get('audience') != 'all' or s.get('qa_only') or s.get('competition') or s.get('archived') or not valid_paper(s):
        return 'Select a published public JEE Main paper: 75 questions, 20 MCQ + 5 numerical per subject, 180 minutes, +4/−1/0.'
    if now() >= window(day)['opens_at'] or (s.get('series_date') and now() >= window(s['series_date'])['opens_at']):
        return 'A day that has opened cannot be assigned or moved.'
    if await attempts.find_one({'set_id': s['id'], 'mode': {'$ne': 'preview'}}, {'_id': 0, 'id': 1}):
        return 'Use a fresh paper without student attempts for a fair live series.'
    if s.get('expires') and s['expires'] < day:
        return 'The paper permissions expire before its scheduled date.'
    if not s.get('series_import') and (s.get('import_id') or s.get('chapter_book_id')) and (not s.get('live_enabled') or s.get('start_at', float('inf')) > window(day)['opens_at'] or s.get('end_at', 0) < window(day)['closes_at']):
        return 'Enable publication and extend its availability to cover the full scheduled day first.'
    return None


async def book_mock_problem(mid):
    from .book_models import BookMock
    row = await db.tejas_book_mocks.find_one({'_id': mid})
    if not row:
        return 'Mock not found. Reload.'
    if not await db.tejas_books.find_one({'_id': row['book_id'], 'payload.destination.series': True, 'payload.destination.series_id': {'$in': [None, SERIES_ID]}, 'removed': False, 'archived': {'$ne': True}}, {'_id': 1}):
        return 'Only books uploaded to the All India Test Series can fill its days.'
    m = BookMock.from_mongo(row)
    if m.state != 'ready' or m.issues or m.set_id:
        return f'{m.label} is not ready for a day yet.'
    problem = series_problem(m)
    return f'{m.label}: {problem}' if problem else None


async def import_problem(import_id):
    from .imports import imports
    r = await imports.find_one({'id': import_id, 'status': 'ready', 'exam': 'JEE Main', 'qa_only': {'$ne': True}, 'archived': {'$ne': True}}, {'_id': 0})
    if not r or r.get('issues'):
        return 'Choose a ready private import without problems.'
    if not valid_paper({'exam': r['exam'], 'questions': r.get('questions', []), 'rules': {'minutes': r.get('duration_minutes'), 'correct': 4, 'wrong': -1, 'skipped': 0}}):
        return 'Select a JEE Main paper: 75 questions, 20 MCQ + 5 numerical per subject, 180 minutes, +4/−1/0.'
    return None


async def assign_set(s, day, u):
    problem = await set_problem(s, day)
    if problem:
        raise HTTPException(409, problem)
    if await db.tejas_book_mocks.find_one({'series_date': day, 'set_id': None}, {'_id': 1}):
        raise HTTPException(409, 'This date already has a paper. Remove its assignment before replacing it.')
    update = {'series_id': SERIES_ID, 'series_date': day, 'test_kind': 'mock'}
    if s.get('series_import'):
        update.update(start_at=window(day)['opens_at'], end_at=window(day)['closes_at'], live_enabled=True, status='published')
    try:
        changed = await sets.update_one({'id': s['id'], 'revision': s['revision']}, {'$set': update, '$inc': {'revision': 1}})
    except DuplicateKeyError:
        raise HTTPException(409, 'This date already has a paper. Remove its assignment before replacing it.')
    if not changed.modified_count: raise HTTPException(409, 'The paper changed. Reload before assigning it.')
    await audit(u['id'], 'All India series date assigned', s['id'], day)


async def unassign_set(s, u):
    if not s.get('series_date'): return
    if now() >= window(s['series_date'])['opens_at']:
        raise HTTPException(409, 'An opened series day cannot be removed.')
    update = {'$unset': {'series_id': '', 'series_date': ''}, '$inc': {'revision': 1}}
    if s.get('series_import'):
        update['$set'] = {'status': 'withdrawn', 'live_enabled': False}
    changed = await sets.update_one({'id': s['id'], 'revision': s['revision']}, update)
    if not changed.modified_count: raise HTTPException(409, 'The paper changed. Reload before removing the assignment.')
    await audit(u['id'], 'All India series date removed', s['id'], s['series_date'])


async def clear_pending(query, u):
    """Book mocks waiting for their day go back to unassigned; nothing was built or shown yet."""
    rows = await db.tejas_book_mocks.find({**query, 'series_date': {'$nin': [None, '']}, 'set_id': None}, {'_id': 1, 'series_date': 1}).to_list(5000)
    cleared = 0
    for m in rows:
        if now() >= window(m['series_date'])['opens_at']:
            continue
        changed = await db.tejas_book_mocks.update_one({'_id': m['_id'], 'set_id': None}, {'$set': {'series_date': None, 'publish_requested': False, 'release_at': None}, '$inc': {'revision': 1}})
        if changed.modified_count:
            cleared += 1
            await audit(u['id'], 'All India book mock day removed', m['_id'], m['series_date'])
    return cleared


async def free_day(day, u):
    if now() >= window(day)['opens_at']:
        raise HTTPException(409, 'A day that has opened cannot be changed.')
    s = await sets.find_one({'series_id': SERIES_ID, 'series_date': day}, {'_id': 0, 'questions': 0})
    if s:
        await unassign_set(s, u)
    await clear_pending({'series_date': day}, u)


async def assign_book_mocks(book_id, pairs, bg, u):
    """Give ready mocks of an All India book their days; the worker builds each paper privately for its day."""
    from .book_models import BookMock
    from .book_store import lock_book_waiting, save_book, unlock, mocks_for, save_mock
    from .book_imports import dispatch
    row = await db.tejas_books.find_one({'_id': book_id, 'removed': False, 'archived': {'$ne': True}}, {'payload.destination': 1})
    if not row or not (row['payload'].get('destination') or {}).get('series'):
        raise HTTPException(409, 'Only books uploaded to the All India Test Series can fill its days.')
    book, token = await lock_book_waiting(book_id)
    try:
        by_id = {m.id: m for m in await mocks_for(book)}
        for mid, day in pairs:
            m = by_id.get(mid)
            if not isinstance(m, BookMock):
                raise HTTPException(404, 'Mock not found. Reload.')
            if m.state != 'ready' or m.issues or m.set_id:
                raise HTTPException(409, f'{m.label} is not ready for a day yet.')
            problem = series_problem(m)
            if problem:
                raise HTTPException(409, f'{m.label}: {problem}')
            if now() >= window(day)['opens_at']:
                raise HTTPException(409, 'A day that has opened cannot be assigned.')
            if await sets.find_one({'series_id': SERIES_ID, 'series_date': day}, {'_id': 1}) or await db.tejas_book_mocks.find_one({'series_date': day, 'set_id': None, '_id': {'$ne': mid}}, {'_id': 1}):
                raise HTTPException(409, f'{day} already has a paper. Remove it first, or choose to replace it.')
            m.series_date = day; m.publish_requested = True; m.release_at = window(day)['opens_at']; m.revision += 1
            await save_mock(m)
        book.paused = False; book.state = 'matching'
        await save_book(book, token)
        await audit(u['id'], 'All India book mocks given days', book_id, ', '.join(f'{by_id[m].label}={d}' for m, d in pairs)[:1900])
    finally:
        await unlock(book, token)
    await dispatch(book, bg)


@router.post('/studio/all-india-jee/assign')
async def assign(data: Assignment, bg: BackgroundTasks, u=Depends(owner)):
    check_range(data.date)
    day = data.date.isoformat()
    if now() >= window(day)['opens_at']:
        raise HTTPException(409, 'A day that has opened cannot be assigned or moved.')
    if data.kind == 'book_mock':
        m = await db.tejas_book_mocks.find_one({'_id': data.set_id}, {'book_id': 1})
        if not m: raise HTTPException(404, 'Mock not found. Reload.')
        if data.replace:
            problem = await book_mock_problem(data.set_id)
            if problem: raise HTTPException(409, problem)
            await free_day(day, u)
        await assign_book_mocks(m['book_id'], [(data.set_id, day)], bg, u)
        return {'ok': True}
    s = await sets.find_one({'id': data.set_id}, {'_id': 0})
    if s is None and data.replace:
        problem = await import_problem(data.set_id)
        if problem: raise HTTPException(409, problem)
        await free_day(day, u)
    if s is None:
        if await db.tejas_book_mocks.find_one({'series_date': day, 'set_id': None}, {'_id': 1}):
            raise HTTPException(409, 'This date already has a paper. Remove its assignment before replacing it.')
        from .imports import schedule_import
        from .import_models import ScheduleInput
        await schedule_import(data.set_id, ScheduleInput(start_at=data.date.isoformat()+'T00:01:00+05:30', revision=data.expected_revision, series_date=data.date.isoformat()), u)
        await audit(u['id'], 'Private import published directly to All India series', data.set_id, data.date.isoformat())
        return {'ok': True}
    if s['revision'] != data.expected_revision:
        raise HTTPException(409, 'The paper changed. Reload before assigning it.')
    if data.replace:
        problem = await set_problem(s, day)
        if problem: raise HTTPException(409, problem)
        await free_day(day, u)
        s = await sets.find_one({'id': s['id']}, {'_id': 0})
    await assign_set(s, day, u)
    return {'ok': True}


@router.post('/studio/all-india-jee/fill')
async def fill(data: Fill, bg: BackgroundTasks, u=Depends(owner)):
    """Ready mocks of one All India book take free days in printed order from the start date."""
    from .book_models import BookMock
    check_range(data.start_date)
    if not await db.tejas_books.find_one({'_id': data.book_id, 'payload.destination.series': True, 'payload.destination.series_id': {'$in': [None, SERIES_ID]}, 'removed': False, 'archived': {'$ne': True}}, {'_id': 1}):
        raise HTTPException(409, 'Only books uploaded to the All India Test Series can fill its days.')
    mocks = [BookMock.from_mongo(r) async for r in db.tejas_book_mocks.find({'book_id': data.book_id}).sort('order', 1)]
    built = {s['id']: s for s in await sets.find({'book_import_id': data.book_id, 'series_import': True}, {'_id': 0}).to_list(None)}
    used = set(await attempts.distinct('set_id', {'set_id': {'$in': list(built)}, 'mode': {'$ne': 'preview'}}))
    own = {s['series_date'] for s in built.values() if s.get('series_date')} | {m.series_date for m in mocks if m.series_date and not m.set_id}
    queue, left = [], []
    for m in mocks:
        s = built.get(m.set_id) if m.set_id else None
        if s:
            if not s.get('series_date') and s['id'] not in used:
                queue.append((m, s))
        elif m.series_date:
            continue
        elif m.state == 'ready' and not m.issues and not series_problem(m):
            queue.append((m, None))
        else:
            left.append({'label': m.label, 'reason': series_problem(m) if m.state == 'ready' else 'Held: fix its problems first.'})
    t = now()
    taken = {s['series_date'] for s in await sets.find({'series_id': SERIES_ID}, {'_id': 0, 'series_date': 1}).to_list(None)}
    taken |= {r['series_date'] for r in await db.tejas_book_mocks.find({'series_date': {'$nin': [None, '']}, 'set_id': None}, {'series_date': 1}).to_list(None)}
    # Plan and check every placement first, so a refused paper never leaves a day half-cleared.
    day, plan = data.start_date, []
    for m, s in queue:
        while day <= LAST and (t >= window(day.isoformat())['opens_at'] or day.isoformat() in own or (day.isoformat() in taken and not data.replace)):
            day += timedelta(days=1)
        if day > LAST:
            left.append({'label': m.label, 'reason': f'No free day left before {LAST.day} {LAST:%B}.'})
            continue
        iso = day.isoformat()
        problem = await set_problem(s, iso) if s else None
        if problem:
            left.append({'label': m.label, 'reason': problem})
            continue
        plan.append((m, s, iso))
        day += timedelta(days=1)
    assigned, pairs = [], []
    for m, s, iso in plan:
        if iso in taken:
            await free_day(iso, u)
        if s:
            await assign_set(s, iso, u)
        else:
            pairs.append((m.id, iso))
        assigned.append({'label': m.label, 'date': iso})
    if pairs:
        await assign_book_mocks(data.book_id, pairs, bg, u)
    if not assigned and not left:
        raise HTTPException(409, 'Every ready mock of this book already has a day.')
    return {'assigned': assigned, 'left': left,
            'message': f"{len(assigned)} mock{'s' if len(assigned) != 1 else ''} given a day" + (f'; {len(left)} could not be placed.' if left else '.')}


@router.post('/studio/all-india-jee/clear')
async def clear(data: Clear, u=Depends(owner)):
    """Remove every future day (of one book, or all), so the series can be refilled. Opened days never change."""
    t = now()
    query = {'series_id': SERIES_ID, **({'book_import_id': data.book_id} if data.book_id else {})}
    removed = 0
    for s in await sets.find(query, {'_id': 0, 'questions': 0}).to_list(None):
        if t < window(s['series_date'])['opens_at']:
            await unassign_set(s, u); removed += 1
    removed += await clear_pending({'book_id': data.book_id} if data.book_id else {}, u)
    return {'removed': removed, 'message': f"{removed} future day{'s' if removed != 1 else ''} cleared. Opened days are unchanged."}


@router.delete('/studio/all-india-jee/book-mocks/{mock_id}')
async def unassign_book_mock(mock_id: str, u=Depends(owner)):
    n = await clear_pending({'_id': mock_id}, u)
    if not n: raise HTTPException(409, 'This mock has no waiting day, or its paper is already built. Remove it from the assigned list instead.')
    return {'ok': True}


@router.delete('/studio/all-india-jee/{set_id}')
async def unassign(set_id: str, u=Depends(owner)):
    s = await get(sets, set_id)
    if s.get('series_id') not in (None, SERIES_ID):
        raise HTTPException(404, 'Manage this paper from its own series.')
    await unassign_set(s, u)
    return {'ok': True}
