"""All India Test Series for any exam: one paper a day on its own dates and times. Students open it inside its exam; only JEE Main has the Home banner."""
import time
from datetime import date, datetime, timedelta
from typing import Annotated, Literal
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from pymongo.errors import DuplicateKeyError
from .auth import current, owner, maybe_current
from .db import db, sets, attempts, now, audit
from .canonical import database_now
from .live_series import SERIES_ID, IST, JEE_TIMES, FIRST, LAST, TOTAL, window, phase, valid_paper, paper_pattern, series_problem

router = APIRouter(prefix='/api', tags=['Test series'])
series = db.tejas_series
Identity = Annotated[str, Field(min_length=1, max_length=100)]
Clock = Annotated[str, Field(pattern=r'^([01]\d|2[0-3]):[0-5]\d$')]
Day = Annotated[str, Field(pattern=r'^\d{4}-\d{2}-\d{2}$')]
JEE = {'id': SERIES_ID, 'exam_slug': 'jee-main', 'section_id': 'jee-main:aits', 'title': 'All India JEE Mains Test Series',
       'first_date': FIRST.isoformat(), 'days': TOTAL, **JEE_TIMES, 'shown': True, 'builtin': True, 'pattern': None}
JEE_DATES_ID = 'jee-series-2026-12-09-50-days'
JEE_RULE = 'All India JEE papers need 75 questions (20 MCQ + 5 numerical in each subject), 180 minutes and +4 / −1 marking.'


class Payload(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)


class SeriesConfig(Payload):
    title: str | None = Field(default=None, min_length=4, max_length=80)
    first_date: Day | None = None
    days: int | None = Field(default=None, ge=1, le=366)
    open_time: Clock | None = None
    last_start: Clock | None = None
    shown: bool | None = None


class SeriesAssign(Payload):
    kind: Literal['written', 'set', 'book_mock']
    id: Identity
    date: Day


class SeriesUnassign(Payload):
    kind: Literal['set', 'book_mock']
    id: Identity


class SeriesLive(Payload):
    id: Identity
    live: bool


async def seed_jee():
    from .structure import sections
    await series.update_one({'_id': SERIES_ID}, {'$setOnInsert': {**JEE, 'created_at': now()}}, upsert=True)
    await sections.update_one({'_id': 'jee-main:aits'}, {'$setOnInsert': {
        'id': 'jee-main:aits', 'exam_slug': 'jee-main', 'slug': 'aits', 'kind': 'aits', 'name': 'All India Test Series',
        'description': 'One paper a day with an all-India rank.', 'layout': 'list', 'builtin': True, 'hidden': False, 'order': 4,
        'series_id': SERIES_ID, 'defaults': {'minutes': 180, 'correct': 4, 'wrong': -1}, 'created_at': now()}}, upsert=True)


def minutes_of(t):
    h, m = map(int, t.split(':'))
    return h * 60 + m


def check_times(open_time, last_start, minutes):
    if minutes_of(last_start) <= minutes_of(open_time):
        raise HTTPException(422, 'The last start time must come after the opening time.')
    if minutes_of(last_start) + minutes > 23 * 60 + 59:
        raise HTTPException(422, f'Leave the full {minutes} minutes before midnight: choose an earlier last start time.')


async def create_series(exam, section_id, body, rules):
    if not body.first_date or not body.days:
        raise HTTPException(422, 'Choose the first date and how many days the series runs.')
    try:
        date.fromisoformat(body.first_date)
    except ValueError:
        raise HTTPException(422, 'Choose a real first date.') from None
    open_time, last = body.open_time or '00:01', body.last_start or '20:59'
    check_times(open_time, last, rules['minutes'])
    sid = f"{exam['slug']}-series-{section_id[:8]}"
    await series.insert_one({'_id': sid, 'id': sid, 'exam_slug': exam['slug'], 'section_id': section_id,
        'title': f"All India {exam['name']} Test Series"[:80], 'first_date': body.first_date, 'days': body.days,
        'open_time': open_time, 'last_start': last, 'close_time': '23:59', 'shown': False, 'builtin': False,
        'pattern': {'count': None, **rules}, 'created_at': now()})
    return sid


async def series_cfg(sid=None):
    doc = await series.find_one({'_id': sid or SERIES_ID}, {'_id': 0})
    if not doc:
        raise HTTPException(404, 'Series not found.')
    return doc


def is_jee(cfg):
    return cfg['id'] == SERIES_ID


def dates(cfg):
    first = date.fromisoformat(cfg['first_date'])
    return [(first + timedelta(days=i)).isoformat() for i in range(cfg['days'])]


def mock_scope(cfg):
    return {'series_id': {'$in': [None, SERIES_ID]}} if is_jee(cfg) else {'series_id': cfg['id']}


def book_scope(cfg):
    if is_jee(cfg):
        return {'payload.destination.series': True, 'payload.destination.series_id': {'$in': [None, SERIES_ID]}}
    return {'payload.destination.series_id': cfg['id']}


def pattern_problem(cfg, pattern, jee_ok=True):
    if is_jee(cfg):
        return None if jee_ok else JEE_RULE
    want = {k: v for k, v in (cfg.get('pattern') or {}).items() if v is not None}
    if any(pattern.get(k) != v for k, v in want.items()):
        p = cfg['pattern']
        count = f"{p['count']} questions, " if p.get('count') else ''
        return f"Every paper in this series needs {count}{p['minutes']} minutes and +{p['correct']:g} / {p['wrong']:g} marking, so ranks stay fair."
    return None


async def claim_pattern(cfg, pattern):
    if not is_jee(cfg) and not (cfg.get('pattern') or {}).get('count'):
        await series.update_one({'_id': cfg['id']}, {'$set': {'pattern.count': pattern['count']}})


def mock_pattern(m):
    r = m.get('rules') or {}
    return {'count': len(m.get('questions', [])), 'minutes': r.get('minutes'), 'correct': r.get('correct'), 'wrong': r.get('wrong')}


async def series_books(cfg):
    return await db.tejas_books.find({**book_scope(cfg), 'removed': False, 'archived': {'$ne': True}},
                                     {'_id': 1, 'payload.title': 1, 'state': 1}).sort('created_at', 1).to_list(200)


async def candidates(cfg):
    """Papers that can take a day: written papers, built papers without a day, and checked mocks of uploaded books."""
    from .book_models import BookMock
    from .written import problems
    out = []
    for s in await sets.find({'catalog_section_id': cfg['section_id'], 'written': True, 'status': 'draft', 'archived': {'$ne': True}},
                             {'_id': 0}).sort('created_at', 1).to_list(500):
        issues = problems(s)
        out.append({'kind': 'written', 'id': s['id'], 'title': s['title'], 'count': len(s.get('questions', [])),
                    'problem': issues[0] if issues else pattern_problem(cfg, paper_pattern(s), valid_paper(s))})
    books = await series_books(cfg)
    names = {b['_id']: b['payload']['title'] for b in books}
    built = {'$or': [{'catalog_section_id': cfg['section_id']}, {'book_import_id': {'$in': list(names)}}]}
    rows = await sets.find({**built, 'series_import': True, 'series_date': {'$exists': False}, 'status': 'published', 'archived': {'$ne': True}},
                           {'_id': 0, 'id': 1, 'title': 1, 'questions.subject': 1, 'questions.type': 1, 'rules': 1, 'exam': 1}).to_list(500)
    used = set(await attempts.distinct('set_id', {'set_id': {'$in': [r['id'] for r in rows]}, 'mode': {'$ne': 'preview'}}))
    out += [{'kind': 'set', 'id': r['id'], 'title': r['title'], 'count': len(r.get('questions', [])), 'problem': None} for r in rows if r['id'] not in used]
    rank = {b: i for i, b in enumerate(names)}
    mocks = await db.tejas_book_mocks.find({'book_id': {'$in': list(names)}, 'set_id': None, 'series_date': {'$in': [None, '']},
        'archived': {'$ne': True}, 'state': {'$in': ['ready', 'held']}},
        {'questions.subject': 1, 'questions.type': 1, 'rules': 1, 'label': 1, 'order': 1, 'state': 1, 'book_id': 1,
         'issue_count': {'$size': {'$ifNull': ['$issues', []]}}}).to_list(5000)
    mocks.sort(key=lambda m: (rank[m['book_id']], m['order']))
    from .book_delete import reached_students
    reached = await reached_students(names)   # Delete (for good) is offered only for an upload from which no test was ever made
    for m in mocks:
        if m['state'] == 'held':
            problem = f"{m['issue_count']} to fix"
        elif is_jee(cfg):
            problem = series_problem(BookMock.from_mongo({**m, 'issues': []}))
        else:
            problem = pattern_problem(cfg, mock_pattern(m))
        out.append({'kind': 'book_mock', 'id': m['_id'], 'book_id': m['book_id'], 'title': m['label'], 'book': names[m['book_id']],
                    'count': len(m.get('questions', [])), 'held': m['state'] == 'held', 'problem': problem, 'upload_deletable': m['book_id'] not in reached})
    return out


async def day_papers(cfg, studio):
    rows = await sets.find({'series_id': cfg['id']}, {'_id': 0, 'questions': 0, 'allowed_emails': 0, 'allowed_phones': 0}).to_list(cfg['days'] + 100)
    pending = {}
    if studio:
        from .master import stuck_marks
        ids = [b['_id'] for b in await series_books(cfg)]
        held_up, hung = await stuck_marks({'_id': {'$in': ids}})
        for m in await db.tejas_book_mocks.find({'book_id': {'$in': ids}, 'series_date': {'$nin': [None, '']}, 'set_id': None, **mock_scope(cfg)},
                                                {'_id': 1, 'label': 1, 'series_date': 1, 'book_id': 1}).to_list(5000):
            mark = held_up.get(m['_id']) or hung.get(m['book_id'])  # its paper could not be made for its day ("Atki hai"): the day says why
            pending[m['series_date']] = {**m, **({'stuck': mark} if mark else {})}
    return {s['series_date']: s for s in rows}, pending


async def slots(cfg, t, studio=False, early=False):
    from .content import permitted
    by_day, pending = await day_papers(cfg, studio)
    out = []
    for i, day in enumerate(dates(cfg)):
        s = by_day.get(day)
        w = (s or {}).get('series_window') or window(day, cfg)
        ready = bool(s and s['status'] == 'published' and permitted(s, series_schedule=True, at=t))
        state = phase(day, t, w)
        soon = early and ready and state == 'upcoming'
        visible = studio or (ready and (state != 'upcoming' or soon))
        slot = {'day': i + 1, 'date': day, **w, 'state': state, 'ready': ready if visible else False, 'early': soon,
                'set_id': s['id'] if s and visible else None, 'title': (s.get('display_title') or s['title']) if s and visible else f"{cfg['title']} · Test {i + 1:02d}",
                'can_start': ready and (state in ('live', 'archive') or soon)}
        if studio:
            m = pending.get(day)
            slot.update(opened=t >= w['opens_at'], paper={'kind': 'set', 'id': s['id'], 'title': s.get('display_title') or s['title'], 'written': bool(s.get('written')), 'off': bool(s.get('owner_unlive'))} if s
                        else {'kind': 'book_mock', 'id': m['_id'], 'title': m['label'], 'pending': True, **({'stuck': m['stuck']} if m.get('stuck') else {})} if m else None)
        out.append(slot)
    return out


async def schedule(cfg, studio=False, early=False):
    t = await database_now()
    days = await slots(cfg, t, studio, early)
    today = datetime.fromtimestamp(t, IST).date().isoformat()
    from .structure import exams
    e = await exams.find_one({'_id': cfg['exam_slug']}, {'_id': 0, 'name': 1, 'color': 1, 'slug': 1, 'shown': 1}) or {}
    return {'id': cfg['id'], 'title': cfg['title'], 'exam': {k: e.get(k) for k in ('slug', 'name', 'color')}, 'first_date': cfg['first_date'],
            'last_date': dates(cfg)[-1], 'total': cfg['days'], 'timezone': 'Asia/Kolkata', 'open_time': cfg['open_time'],
            'last_start': cfg['last_start'], 'close_time': cfg.get('close_time', '23:59'), 'server_now': t, 'today': today,
            'slots': days, 'today_slot': next((s for s in days if s['date'] == today), None), 'builtin': cfg.get('builtin', False),
            'shown': cfg.get('shown', False), 'exam_shown': e.get('shown', False), 'pattern': cfg.get('pattern')}


async def visible_series():
    from .structure import exams, sections
    shown_exams = {e['slug']: e for e in await exams.find({'shown': True}, {'_id': 0}).to_list(200)}
    hidden = set(await sections.distinct('id', {'kind': 'aits', 'hidden': True}))
    return [c for c in await series.find({'shown': True}, {'_id': 0}).sort('created_at', 1).to_list(100)
            if c['exam_slug'] in shown_exams and c['section_id'] not in hidden]


# Students: public schedule metadata, like the JEE series

@router.get('/series')
async def public_list():
    out = []
    for cfg in await visible_series():
        data = await schedule(cfg)
        out.append({k: data[k] for k in ('id', 'title', 'exam', 'first_date', 'last_date', 'total', 'open_time', 'last_start', 'today', 'today_slot', 'builtin', 'server_now')})
    return {'items': out}


@router.get('/series/{sid}/schedule')
async def public_schedule(sid: str, request: Request):
    cfg = next((c for c in await visible_series() if c['id'] == sid), None)
    if not cfg:
        raise HTTPException(404, 'This test series is not open.')
    u = await maybe_current(request)
    return await schedule(cfg, early=(u or {}).get('role') == 'owner')


@router.get('/series/{sid}/history')
async def public_history(sid: str, page: int = Query(1, ge=1, le=10000), u=Depends(current)):
    from .my_tests import history_item
    t = await database_now()
    match = {'user_id': u['id'], 'series_id': sid, 'mode': {'$in': ['series_live', 'series_practice']}}
    fields = {k: 1 for k in ('id', 'set_id', 'title', 'exam', 'mode', 'version', 'started_at', 'submitted_at', 'deadline', 'status', 'count', 'summary', 'answers', 'competition_end', 'series_date', 'series_id')}
    rows = await attempts.find(match, {'_id': 0, **fields}).sort('started_at', -1).skip((page - 1) * 20).limit(20).to_list(20)
    return {'items': [{**history_item(a, t).model_dump(), 'series_date': a['series_date']} for a in rows], 'page': page,
            'total': await attempts.count_documents(match)}


# Owner: days, papers and settings

@router.get('/admin/master/series/{sid}')
async def owner_view(sid: str, u=Depends(owner)):
    cfg = await series_cfg(sid)
    return {**await schedule(cfg, studio=True), 'candidates': await candidates(cfg), 'section_id': cfg['section_id']}


@router.put('/admin/master/series/{sid}')
async def update_config(sid: str, body: SeriesConfig, u=Depends(owner)):
    cfg = await series_cfg(sid)
    change = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    if not change:
        raise HTTPException(422, 'Nothing to change.')
    if cfg.get('builtin') and set(change) - {'title'}:
        raise HTTPException(409, f'The JEE Main series keeps its {TOTAL} days ({FIRST.day} {FIRST:%b} – {LAST.day} {LAST:%b}), its times and its Home banner.')
    new = {**cfg, **change}
    try:
        date.fromisoformat(new['first_date'])
    except ValueError:
        raise HTTPException(422, 'Choose a real first date.') from None
    check_times(new['open_time'], new['last_start'], (cfg.get('pattern') or {}).get('minutes') or 180)
    if not set(change) & {'first_date', 'days', 'open_time', 'last_start'}:
        await series.update_one({'_id': sid}, {'$set': change})
        await audit(u['id'], 'Test series settings changed', sid, ', '.join(f'{k}={v}' for k, v in change.items()))
        return {'message': ('Students can now open it inside its exam.' if change.get('shown') else 'Closed to students.') if 'shown' in change else 'Series saved.', 'moved': 0}
    t = await database_now()
    keep = set(dates(new))
    rows = await sets.find({'series_id': sid}, {'_id': 0, 'id': 1, 'series_date': 1, 'series_window': 1, 'revision': 1}).to_list(None)
    for s in rows:
        if t >= (s.get('series_window') or window(s['series_date'], cfg))['opens_at'] and s['series_date'] not in keep:
            raise HTTPException(409, f"{s['series_date']} has already opened, so the series must still include that day.")
    moved = 0
    for s in rows:
        w = s.get('series_window') or window(s['series_date'], cfg)
        if t >= w['opens_at']:
            continue
        if s['series_date'] not in keep:
            await unassign_set(cfg, s['id'], u)
            moved += 1
        else:
            # Only the paper as it was read is rewritten. A paper changed meanwhile is read again and placed by its current day.
            for _ in range(3):
                nw = window(s['series_date'], new)
                done = await sets.update_one({'id': s['id'], 'series_id': sid, 'series_date': s['series_date'], 'revision': s.get('revision')},
                                             {'$set': {'series_window': nw, 'start_at': nw['opens_at'], 'end_at': nw['closes_at']}, '$inc': {'revision': 1}})
                if done.matched_count:
                    break
                s = await sets.find_one({'id': s['id'], 'series_id': sid}, {'_id': 0, 'id': 1, 'series_date': 1, 'series_window': 1, 'revision': 1})
                if not s or not s.get('series_date'):
                    break
                if s['series_date'] not in keep:
                    await unassign_set(cfg, s['id'], u)
                    moved += 1
                    break
            else:
                raise HTTPException(409, 'A paper in this series keeps changing. Reload and save again.')
    for m in await db.tejas_book_mocks.find({'series_date': {'$nin': [None, '']}, 'set_id': None, **mock_scope(cfg)}, {'_id': 1, 'series_date': 1}).to_list(5000):
        if m['series_date'] not in keep:
            await db.tejas_book_mocks.update_one({'_id': m['_id'], 'series_date': m['series_date'], 'set_id': None}, {'$set': {'series_date': None, 'series_id': None, 'publish_requested': False, 'release_at': None}, '$inc': {'revision': 1}})
            moved += 1
        else:
            await db.tejas_book_mocks.update_one({'_id': m['_id'], 'series_date': m['series_date'], 'set_id': None}, {'$set': {'release_at': window(m['series_date'], new)['opens_at']}})
    await series.update_one({'_id': sid}, {'$set': change})
    await audit(u['id'], 'Test series settings changed', sid, ', '.join(f'{k}={v}' for k, v in change.items()))
    note = f" {moved} paper{'s' if moved != 1 else ''} lost {'their' if moved != 1 else 'its'} day and can be given a new one." if moved else ''
    return {'message': 'Series saved.' + note, 'moved': moved}


async def free_day(cfg, day):
    w = window(day, cfg)
    if await database_now() >= w['opens_at']:
        raise HTTPException(409, 'A day that has opened cannot be changed.')
    if await sets.find_one({'series_id': cfg['id'], 'series_date': day}, {'_id': 1}) or \
       await db.tejas_book_mocks.find_one({'series_date': day, 'set_id': None, **mock_scope(cfg)}, {'_id': 1}):
        raise HTTPException(409, f'{day} already has a paper. Remove it first.')
    return w


async def assign_written(cfg, id, day, w, u):
    from .content import publish_validated
    from .written import problems
    s = await sets.find_one({'id': id, 'catalog_section_id': cfg['section_id'], 'written': True, 'status': 'draft', 'archived': {'$ne': True}}, {'_id': 0})
    if not s:
        raise HTTPException(404, 'Paper not found here. Reload.')
    issue = (problems(s) or [None])[0] or pattern_problem(cfg, paper_pattern(s), valid_paper(s))
    if issue:
        raise HTTPException(409, issue)
    from .written import photo_trouble, unchecked
    so = 'isliye is paper ko din nahi mila (Draft hi hai)'
    why = await photo_trouble(s, so)
    if why:
        raise HTTPException(409, why)
    update = {'series_id': cfg['id'], 'series_date': day, 'series_window': w, 'series_import': True, 'start_at': w['opens_at'],
              'end_at': w['closes_at'], 'live_enabled': True, 'test_kind': 'mock', 'full_length': True}
    if not is_jee(cfg):
        update['series_pattern'] = {**(cfg.get('pattern') or {}), 'count': paper_pattern(s)['count']}
    try:
        done = await sets.update_one({'id': id, 'revision': s['revision']}, {'$set': update, '$inc': {'revision': 1}})
    except DuplicateKeyError:
        raise HTTPException(409, f'{day} already has a paper.') from None
    if not done.modified_count:
        raise HTTPException(409, 'The paper changed. Reload and try again.')
    from tejas_storage import StorageError
    try:
        await publish_validated(id, {'confirm': True}, u)
    except (HTTPException, StorageError) as exc:
        # The paper could not be made: its day is given back at once, so the day never looks filled while students would get nothing.
        await sets.update_one({'id': id}, {'$unset': {k: '' for k in update if k not in ('test_kind', 'full_length')}, '$inc': {'revision': 1}})
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(409, unchecked(exc, so)) from None
    await claim_pattern(cfg, paper_pattern(s))


async def assign_built(cfg, id, day, w):
    s = await sets.find_one({'id': id, 'series_import': True, 'series_date': {'$exists': False}, 'status': 'published', 'archived': {'$ne': True}}, {'_id': 0})
    if not s or await attempts.find_one({'set_id': id, 'mode': {'$ne': 'preview'}}, {'_id': 1}):
        raise HTTPException(409, 'Use a fresh paper without student attempts.')
    update = {'series_id': cfg['id'], 'series_date': day, 'series_window': w, 'start_at': w['opens_at'], 'end_at': w['closes_at'], 'live_enabled': True}
    if not is_jee(cfg):
        update['series_pattern'] = {**(cfg.get('pattern') or {}), 'count': paper_pattern(s)['count']}
    try:
        await sets.update_one({'id': id, 'revision': s['revision']}, {'$set': update, '$inc': {'revision': 1}})
    except DuplicateKeyError:
        raise HTTPException(409, f'{day} already has a paper.') from None


async def assign_mocks(cfg, pairs, bg, u):
    """Checked mocks of a series book get their days; the worker builds each paper privately for its day."""
    from .book_models import BookMock
    from .book_store import lock_book_waiting, save_book, unlock, save_mock, load_book
    from .book_imports import dispatch
    books = {b['_id'] for b in await series_books(cfg)}
    by_book = {}
    count = (cfg.get('pattern') or {}).get('count')
    for mid, day, w in pairs:
        row = await db.tejas_book_mocks.find_one({'_id': mid, 'archived': {'$ne': True}})
        if not row or row['book_id'] not in books:
            raise HTTPException(404, 'Mock not found in this series. Reload.')
        m = BookMock.from_mongo(row)
        if m.state != 'ready' or m.issues or m.set_id or m.series_date:
            raise HTTPException(409, f'{m.label} is not ready for a day yet.')
        issue = series_problem(m) if is_jee(cfg) else pattern_problem(cfg, mock_pattern(row))
        if issue:
            raise HTTPException(409, f'{m.label}: {issue}')
        if not is_jee(cfg):
            count = count or len(m.questions)
            if len(m.questions) != count:
                raise HTTPException(409, f'{m.label}: every paper in this series needs {count} questions, so ranks stay fair.')
        by_book.setdefault(m.book_id, []).append((m, day, w))
    until = time.monotonic() + 30
    for bid, items in by_book.items():
        book, token = await lock_book_waiting(bid, max(1.5, until - time.monotonic()))
        try:
            for m, day, w in items:
                m.series_date, m.series_id, m.publish_requested, m.release_at = day, cfg['id'], True, w['opens_at']
                m.revision += 1
                await save_mock(m)
                await claim_pattern(cfg, mock_pattern(m.model_dump()))
            book.paused = False
            book.state = 'matching'
            await save_book(book, token)
        finally:
            await unlock(book, token)
        await dispatch(await load_book(bid), bg)
        await audit(u['id'], 'Test series days given', bid, ', '.join(f'{m.label}={d}' for m, d, _ in items)[:1900])


async def assign_one(cfg, kind, id, day, bg, u):
    if day not in dates(cfg):
        raise HTTPException(422, 'Choose a day of this series.')
    w = await free_day(cfg, day)
    if kind == 'written':
        await assign_written(cfg, id, day, w, u)
    elif kind == 'set':
        await assign_built(cfg, id, day, w)
    else:
        await assign_mocks(cfg, [(id, day, w)], bg, u)
    await audit(u['id'], 'Test series day assigned', id, f"{cfg['id']} {day}")


@router.post('/admin/master/series/{sid}/assign')
async def assign(sid: str, body: SeriesAssign, bg: BackgroundTasks, u=Depends(owner)):
    cfg = await series_cfg(sid)
    await assign_one(cfg, body.kind, body.id, body.date, bg, u)
    return {'message': f'Paper given {body.date}. Students see it only from that day.'}


@router.post('/admin/master/series/{sid}/fill')
async def fill(sid: str, bg: BackgroundTasks, u=Depends(owner)):
    cfg = await series_cfg(sid)
    t = await database_now()
    by_day, pending = await day_papers(cfg, True)
    free = [d for d in dates(cfg) if d not in by_day and d not in pending and t < window(d, cfg)['opens_at']]
    queue = [c for c in await candidates(cfg) if not c['problem']]
    left = len([c for c in await candidates(cfg) if c['problem']])
    placed, mocks = 0, []
    for c, day in zip(queue, free):
        w = window(day, cfg)
        if c['kind'] == 'book_mock':
            mocks.append((c['id'], day, w))
        else:
            try:
                if c['kind'] == 'written':
                    await assign_written(cfg, c['id'], day, w, u)
                else:
                    await assign_built(cfg, c['id'], day, w)
            except HTTPException:
                left += 1
                continue
            cfg = await series_cfg(sid)
        placed += 1
    if mocks:
        await assign_mocks(cfg, mocks, bg, u)
    if not placed:
        raise HTTPException(409, 'No ready paper could take a day. Fix or finish papers first, or free some future days.' if queue else 'Every ready paper already has a day.')
    await audit(u['id'], 'Test series days filled in order', sid, f'{placed} placed')
    extra = f' {len(queue) - placed} waiting for more days.' if len(queue) > placed else ''
    return {'placed': placed, 'message': f"{placed} paper{'s' if placed != 1 else ''} given days in order.{extra}" + (f" {left} still need{'s' if left == 1 else ''} work." if left else '')}


async def unassign_set(cfg, id, u):
    s = await sets.find_one({'id': id, 'series_id': cfg['id']}, {'_id': 0, 'questions': 0})
    if not s:
        raise HTTPException(404, 'This paper has no day in this series.')
    if await database_now() >= (s.get('series_window') or window(s['series_date'], cfg))['opens_at']:
        raise HTTPException(409, 'An opened day cannot be changed.')
    await sets.update_one({'id': id}, {'$unset': {k: '' for k in ('series_id', 'series_date', 'series_window', 'series_pattern', 'start_at', 'end_at')}, '$inc': {'revision': 1}})
    await audit(u['id'], 'Test series day removed', id, s['series_date'])


async def jee_dates_job():
    """One time: the JEE Main series moves to the owner's 50 days; papers on other days lose their day and wait to be given one again."""
    cfg = await series_cfg(SERIES_ID)
    new = {'first_date': FIRST.isoformat(), 'days': TOTAL}
    keep = set(dates({**cfg, **new}))
    t = await database_now()
    moved = 0
    for s in await sets.find({'series_id': SERIES_ID}, {'_id': 0, 'id': 1, 'series_date': 1, 'series_window': 1}).to_list(None):
        if s['series_date'] in keep or t >= (s.get('series_window') or window(s['series_date'], cfg))['opens_at']:
            continue
        await unassign_set(cfg, s['id'], {'id': 'system'})
        moved += 1
    for m in await db.tejas_book_mocks.find({'series_date': {'$nin': [None, '']}, 'set_id': None, **mock_scope(cfg)}, {'_id': 1, 'series_date': 1}).to_list(5000):
        if m['series_date'] not in keep:
            await db.tejas_book_mocks.update_one({'_id': m['_id']}, {'$set': {'series_date': None, 'series_id': None, 'publish_requested': False, 'release_at': None}, '$inc': {'revision': 1}})
            moved += 1
    await series.update_one({'_id': SERIES_ID}, {'$set': new})
    return {'moved': moved, **new}


async def jee_dates_once():
    from .library import run_once
    return await run_once(JEE_DATES_ID, jee_dates_job, 'JEE Main series moved to 9 Dec 2026 – 27 Jan 2027')


@router.post('/admin/master/series/{sid}/unassign')
async def unassign(sid: str, body: SeriesUnassign, u=Depends(owner)):
    cfg = await series_cfg(sid)
    if body.kind == 'set':
        await unassign_set(cfg, body.id, u)
    else:
        m = await db.tejas_book_mocks.find_one({'_id': body.id, 'set_id': None, 'series_date': {'$nin': [None, '']}, **mock_scope(cfg)}, {'series_date': 1})
        if not m:
            raise HTTPException(409, 'This mock has no waiting day.')
        if await database_now() >= window(m['series_date'], cfg)['opens_at']:
            raise HTTPException(409, 'An opened day cannot be changed.')
        await db.tejas_book_mocks.update_one({'_id': body.id}, {'$set': {'series_date': None, 'series_id': None, 'publish_requested': False, 'release_at': None}, '$inc': {'revision': 1}})
        await audit(u['id'], 'Test series day removed', body.id, m['series_date'])
    return {'message': 'Day freed. The paper is back in the list without a day.'}


@router.post('/admin/master/series/{sid}/live')
async def paper_live(sid: str, body: SeriesLive, u=Depends(owner)):
    """Off hides one day's paper from students; Live shows it again. The day still decides when it opens."""
    cfg = await series_cfg(sid)
    done = await sets.update_one({'id': body.id, 'series_id': cfg['id'], 'series_date': {'$nin': [None, '']}, 'archived': {'$ne': True}}, {'$unset': {'owner_unlive': ''}} if body.live else {'$set': {'owner_unlive': True}})
    if not done.matched_count:
        raise HTTPException(404, 'This paper has no day in this series. Reload.')
    await audit(u['id'], 'Test series paper ' + ('Live' if body.live else 'Off'), body.id, '')
    return {'message': 'Live again. Students see it on its day.' if body.live else "Switched off. Students do not see this day's paper until you switch it back on."}


@router.post('/admin/master/series/{sid}/clear')
async def clear(sid: str, u=Depends(owner)):
    cfg = await series_cfg(sid)
    t = await database_now()
    by_day, pending = await day_papers(cfg, True)
    n = 0
    for day, s in by_day.items():
        if t < (s.get('series_window') or window(day, cfg))['opens_at']:
            await unassign_set(cfg, s['id'], u)
            n += 1
    for day, m in pending.items():
        if t < window(day, cfg)['opens_at']:
            await db.tejas_book_mocks.update_one({'_id': m['_id']}, {'$set': {'series_date': None, 'series_id': None, 'publish_requested': False, 'release_at': None}, '$inc': {'revision': 1}})
            n += 1
    return {'message': f"{n} future day{'s' if n != 1 else ''} freed. Opened days are unchanged."}
