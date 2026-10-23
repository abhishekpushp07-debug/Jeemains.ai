from collections import Counter
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from pymongo.errors import DuplicateKeyError
from .auth import current, owner
from .db import sets, attempts, get, now, audit

router = APIRouter(prefix='/api', tags=['All India series'])
SERIES_ID = 'all-india-jee-2026-27'
FIRST = date(2026, 12, 1)
LAST = date(2027, 1, 31)
IST = ZoneInfo('Asia/Kolkata')


def window(day):
    d = date.fromisoformat(day)
    return {key: datetime.combine(d + timedelta(days=offset), time(h, m), IST).timestamp()
            for key, h, m, offset in [('opens_at', 0, 1, 0), ('last_start_at', 20, 59, 0),
                                     ('closes_at', 23, 59, 0), ('archive_at', 0, 0, 1)]}


def phase(day, timestamp):
    w = window(day)
    if timestamp < w['opens_at']: return 'upcoming'
    if timestamp <= w['last_start_at']: return 'live'
    if timestamp < w['closes_at']: return 'start_closed'
    if timestamp < w['archive_at']: return 'ended'
    return 'archive'


def series_mode(s, timestamp):
    if s.get('series_id') != SERIES_ID: return None
    state = phase(s['series_date'], timestamp)
    return 'series_practice' if state == 'archive' else 'series_live'


def guard_start(s, timestamp):
    if s.get('series_id') != SERIES_ID: return
    if phase(s['series_date'], timestamp) not in ('live', 'archive'):
        raise HTTPException(409, 'Live starts are allowed from 12:01 AM through 8:59:00 PM IST on the scheduled day. Archive practice opens the following day.')


def valid_paper(s):
    qs, r = s.get('questions', []), s.get('rules', {})
    shape = Counter((q.get('subject', '').lower().replace('maths', 'mathematics'), q.get('type')) for q in qs)
    required = Counter({(subject, kind): count for subject in ('physics', 'chemistry', 'mathematics') for kind, count in [('mcq', 20), ('integer', 5)]})
    return (s.get('exam') == 'JEE Main' and len(qs) == 75 and shape == required
            and r.get('minutes') == 180 and not r.get('bonus_rule')
            and all((q.get('scoring') or r).get('correct') == 4 and (q.get('scoring') or r).get('wrong') == -1
                    and (q.get('scoring') or r).get('skipped', 0) == 0 and not q.get('bonus')
                    and q.get('disposition', 'standard') == 'standard' for q in qs))


async def schedule_data(studio=False):
    from .content import permitted
    t = now()
    projection = {'_id': 0, 'questions': 0, 'allowed_emails': 0, 'allowed_phones': 0}
    rows = await sets.find({'series_id': SERIES_ID}, projection).limit(62).to_list(62)
    by_day = {s['series_date']: s for s in rows}
    slots = []
    for i in range(62):
        day = (FIRST + timedelta(days=i)).isoformat()
        s = by_day.get(day)
        ready = bool(s and s['status'] == 'published' and permitted(s, series_schedule=True))
        state = phase(day, t)
        visible = ready and state != 'upcoming'
        slots.append({'day': i + 1, 'date': day, **window(day), 'state': state,
                      'ready': ready if studio or state != 'upcoming' else False, 'set_id': s['id'] if s and (studio or visible) else None,
                      'title': s['title'] if s and (studio or visible) else f'All India JEE Mains · Test {i + 1:02d}',
                      'can_start': ready and state in ('live', 'archive'),
                      **({'revision': s['revision'], 'publication_status': s['status'], 'series_import': s.get('series_import', False), 'live_enabled': s.get('live_enabled', False)} if studio and s else {})})
    today = datetime.fromtimestamp(t, IST).date().isoformat()
    return {'id': SERIES_ID, 'title': 'All India JEE Mains Test Series', 'first_date': FIRST.isoformat(),
            'last_date': LAST.isoformat(), 'total': 62, 'timezone': 'Asia/Kolkata', 'server_now': t,
            'today': today, 'slots': slots, 'today_slot': next((s for s in slots if s['date'] == today), None)}


@router.get('/series/all-india-jee')
async def catalogue():
    return await schedule_data()


@router.get('/series/all-india-jee/history')
async def history(page: int = Query(1, ge=1, le=10000), u=Depends(current)):
    from .my_tests import history_item
    t = now()
    match = {'user_id': u['id'], 'series_id': SERIES_ID, 'mode': {'$in': ['series_live', 'series_practice']}}
    fields = {k: 1 for k in ('id', 'set_id', 'title', 'exam', 'mode', 'version', 'started_at', 'submitted_at', 'deadline', 'status', 'count', 'summary', 'answers', 'competition_end', 'series_date')}
    rows = await attempts.find(match, {'_id': 0, **fields}).sort('started_at', -1).skip((page-1)*20).limit(20).to_list(20)
    items = [{**history_item(a, t).model_dump(), 'series_date': a['series_date']} for a in rows]
    latest = await attempts.find_one({**match, 'status': 'completed', 'summary': {'$ne': None}, 'competition_end': {'$not': {'$gt': t}}}, {'_id': 0, 'id': 1}, sort=[('submitted_at', -1)])
    return {'items': items, 'page': page, 'total': await attempts.count_documents(match), 'latest_result_id': (latest or {}).get('id')}


@router.get('/studio/all-india-jee')
async def studio_schedule(u=Depends(owner)):
    from .imports import imports
    data = await schedule_data(studio=True)
    t = now()
    rows = await sets.find({'exam': 'JEE Main', '$or': [{'status': 'published'}, {'series_import': True}], 'audience': 'all', 'qa_only': {'$ne': True}, 'competition': {'$ne': True}}, {'_id': 0, 'questions.ai_solution': 0}).limit(500).to_list(500)
    used = set(await attempts.distinct('set_id', {'set_id': {'$in': [s['id'] for s in rows]}, 'mode': {'$ne': 'preview'}}))
    data['papers'] = [{'id': s['id'], 'title': s['title'], 'revision': s['revision'], 'series_date': s.get('series_date'), 'kind': 'paper'} for s in rows if valid_paper(s) and s['id'] not in used and (not s.get('series_date') or t < window(s['series_date'])['opens_at'])]
    ready = await imports.find({'status': 'ready', 'exam': 'JEE Main', 'qa_only': {'$ne': True}}, {'_id': 0}).limit(500).to_list(500)
    existing = set(await sets.distinct('id', {'id': {'$in': [r['id'] for r in ready]}}))
    data['papers'] = [{'id': r['id'], 'title': r['title'], 'revision': 0, 'kind': 'private_import'} for r in ready if r['id'] not in existing and not r.get('issues') and valid_paper({'exam': r['exam'], 'questions': r.get('questions', []), 'rules': {'minutes': r.get('duration_minutes'), 'correct': 4, 'wrong': -1, 'skipped': 0}})] + data['papers']
    return data


class Assignment(BaseModel):
    model_config = ConfigDict(extra='forbid')
    set_id: str = Field(min_length=1, max_length=100)
    date: date
    expected_revision: int = Field(ge=0)


@router.post('/studio/all-india-jee/assign')
async def assign(data: Assignment, u=Depends(owner)):
    if not FIRST <= data.date <= LAST:
        raise HTTPException(422, 'Choose a date from 1 December 2026 to 31 January 2027.')
    s = await sets.find_one({'id': data.set_id}, {'_id': 0})
    if s is None:
        from .imports import schedule_import
        from .import_models import ScheduleInput
        await schedule_import(data.set_id, ScheduleInput(start_at=data.date.isoformat()+'T00:01:00+05:30', revision=data.expected_revision, series_date=data.date.isoformat()), u)
        await audit(u['id'], 'Private import published directly to All India series', data.set_id, data.date.isoformat())
        return {'ok': True}
    if s['revision'] != data.expected_revision:
        raise HTTPException(409, 'The paper changed. Reload before assigning it.')
    if (s['status'] != 'published' and not s.get('series_import')) or s.get('audience') != 'all' or s.get('qa_only') or s.get('competition') or not valid_paper(s):
        raise HTTPException(409, 'Select a published public JEE Main paper: 75 questions, 20 MCQ + 5 numerical per subject, 180 minutes, +4/−1/0.')
    day = data.date.isoformat()
    if now() >= window(day)['opens_at'] or (s.get('series_date') and now() >= window(s['series_date'])['opens_at']):
        raise HTTPException(409, 'A day that has opened cannot be assigned or moved.')
    if await attempts.find_one({'set_id': s['id'], 'mode': {'$ne': 'preview'}}, {'_id': 0, 'id': 1}):
        raise HTTPException(409, 'Use a fresh paper without student attempts for a fair live series.')
    if s.get('expires') and s['expires'] < day:
        raise HTTPException(409, 'The paper permissions expire before its scheduled date.')
    if not s.get('series_import') and (s.get('import_id') or s.get('chapter_book_id')) and (not s.get('live_enabled') or s.get('start_at', float('inf')) > window(day)['opens_at'] or s.get('end_at', 0) < window(day)['closes_at']):
        raise HTTPException(409, 'Enable publication and extend its availability to cover the full scheduled day first.')
    update = {'series_id': SERIES_ID, 'series_date': day, 'test_kind': 'mock'}
    if s.get('series_import'):
        update.update(start_at=window(day)['opens_at'], end_at=window(day)['closes_at'], live_enabled=True, status='published')
    try:
        changed = await sets.update_one({'id': s['id'], 'revision': data.expected_revision}, {'$set': update, '$inc': {'revision': 1}})
    except DuplicateKeyError:
        raise HTTPException(409, 'This date already has a paper. Remove its assignment before replacing it.')
    if not changed.modified_count: raise HTTPException(409, 'The paper changed. Reload before assigning it.')
    await audit(u['id'], 'All India series date assigned', s['id'], day)
    return {'ok': True}


@router.delete('/studio/all-india-jee/{set_id}')
async def unassign(set_id: str, u=Depends(owner)):
    s = await get(sets, set_id)
    if not s.get('series_date'): return {'ok': True}
    if now() >= window(s['series_date'])['opens_at']:
        raise HTTPException(409, 'An opened series day cannot be removed.')
    update = {'$unset': {'series_id': '', 'series_date': ''}, '$inc': {'revision': 1}}
    if s.get('series_import'):
        update['$set'] = {'status': 'withdrawn', 'live_enabled': False}
    changed = await sets.update_one({'id': set_id, 'revision': s['revision']}, update)
    if not changed.modified_count: raise HTTPException(409, 'The paper changed. Reload before removing the assignment.')
    await audit(u['id'], 'All India series date removed', set_id, s['series_date'])
    return {'ok': True}
