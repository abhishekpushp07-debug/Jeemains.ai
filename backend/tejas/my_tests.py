"""Saved papers and private attempt history; never starts a timer or substitutes content."""
import math
import re
from datetime import date, datetime, time, timedelta, timezone
from typing import Literal
from uuid import uuid5, NAMESPACE_URL
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from pymongo.errors import DuplicateKeyError
from .db import db, attempts, sets, now
from .auth import current
from .documents import BaseDocument
from .catalog import available, PROJECT
from .content import summary
from .request_contracts import EmptyPayload, CompareAttemptsPayload
from .learning_progress import released, paper_basis, point

router = APIRouter(prefix='/api/my/tests', tags=['My Tests'])
saved = db.tejas_saved_tests
SIZE = 12
EXAMS = {'JEE Main', 'BITSAT', 'COMEDK'}


class SavedPaper(BaseDocument):
    user_id: str
    set_id: str
    title: str
    exam: str
    saved_at: float
    version: int | None = None


class HistoryItem(BaseModel):
    id: str
    set_id: str
    title: str
    exam: str
    status: str
    mode: str
    started_at: float
    submitted_at: float | None = None
    deadline: float = 0
    remaining_seconds: float | None = None
    saved_answers: int = 0
    last_saved_at: float | None = None
    count: int = 0
    summary: dict | None = None
    version: int | None = None
    report_allowed: bool = False
    resumable: bool = False
    result_available: bool = False
    compare_eligible: bool = False


def save_id(user_id, set_id):
    return str(uuid5(NAMESPACE_URL, f'saved-paper:{user_id}:{set_id}'))


def visible_set(u):
    match = available(u)
    t = now()
    match['$and'].extend([{'$or': [{'live_enabled': {'$exists': False}}, {'live_enabled': True}]},
                         {'$or': [{'start_at': {'$exists': False}}, {'start_at': {'$lte': t}}]},
                         {'$or': [{'end_at': {'$exists': False}}, {'end_at': {'$gt': t}}]}])
    return match


def filters(match, exam, q, start, end, field):
    if exam:
        if exam not in EXAMS:
            raise HTTPException(422, 'Unknown exam.')
        match['exam'] = exam
    if q:
        match['title'] = {'$regex': re.escape(q), '$options': 'i'}
    if start and end and start > end:
        raise HTTPException(422, 'Start date must be before the end date.')
    period = {}
    if start:
        period['$gte'] = datetime.combine(start, time.min, timezone.utc).timestamp()
    if end:
        period['$lt'] = datetime.combine(end+timedelta(days=1), time.min, timezone.utc).timestamp()
    if period:
        match[field] = period
    return match


@router.get('/saved/{id}')
async def save_state(id: str, u=Depends(current)):
    return {'set_id': id, 'saved': bool(await saved.find_one({'_id': save_id(u['id'], id), 'user_id': u['id']}, {'_id': 1}))}


@router.post('/saved/{id}')
async def save_paper(id: str, data: EmptyPayload, u=Depends(current)):
    s = await sets.find_one({'$and': [visible_set(u), {'id': id}]}, {'_id': 0, 'id': 1, 'title': 1, 'exam': 1, 'version': 1})
    if not s:
        raise HTTPException(404, 'This paper is not currently available to save.')
    identity = save_id(u['id'], id)
    if await saved.count_documents({'user_id': u['id']}) >= 500 and not await saved.find_one({'_id': identity}):
        raise HTTPException(409, 'Remove a saved paper before adding more (500-paper limit).')
    record = SavedPaper(id=identity, user_id=u['id'], set_id=id, title=s['title'], exam=s['exam'], version=s.get('version'), saved_at=now())
    try:
        await saved.update_one({'_id': identity, 'user_id': u['id']}, {'$setOnInsert': record.to_mongo()}, upsert=True)
    except DuplicateKeyError:
        pass
    return {'set_id': id, 'saved': True}


@router.delete('/saved/{id}')
async def remove_saved(id: str, u=Depends(current)):
    await saved.delete_one({'_id': save_id(u['id'], id), 'user_id': u['id']})
    return {'set_id': id, 'saved': False}


async def saved_page(u, exam, q, start, end, status, page):
    match = filters({'user_id': u['id']}, exam, q, start, end, 'saved_at')
    pipeline = [{'$match': match}, {'$lookup': {'from': sets.name, 'let': {'sid': '$set_id'},
        'pipeline': [{'$match': {'$and': [visible_set(u), {'$expr': {'$eq': ['$id', '$$sid']}}]}}, {'$project': PROJECT}], 'as': 'live'}}]
    if status in ('available', 'unavailable'):
        pipeline.append({'$match': {'live.0': {'$exists': status == 'available'}}})
    pipeline += [{'$sort': {'saved_at': -1, '_id': 1}}, {'$facet': {'count': [{'$count': 'n'}],
                 'items': [{'$skip': (page-1)*SIZE}, {'$limit': SIZE}]}}]
    result = (await saved.aggregate(pipeline).to_list(1))[0]
    items = []
    for row in result['items']:
        record = SavedPaper.from_mongo(row)
        live = row.get('live', [])
        items.append({'id': record.id, 'set_id': record.set_id, 'title': record.title, 'exam': record.exam,
                      'saved_at': record.saved_at, 'available': bool(live), 'paper': summary(live[0]) if live else None,
                      'reason': None if live else 'Unavailable, withdrawn, expired or no longer accessible to this profile.'})
    total = result['count'][0]['n'] if result['count'] else 0
    return items, total


def history_item(a, t):
    expired = a['status'] == 'active' and bool(a.get('deadline')) and a['deadline'] <= t
    released = a.get('competition_end', 0) <= t
    active = a['status'] == 'active' and not expired
    status = 'active' if active else 'expired' if expired else 'embargoed' if not released else 'completed' if a.get('summary') else 'grading'
    summary_value = a.get('summary') if not active and not expired and released else None
    acknowledgements = [v.get('accepted_at', 0) for v in (a.get('answers') or {}).values() if v.get('accepted_at')]
    return HistoryItem(id=a['id'], set_id=a['set_id'], title=a['title'], exam=a['exam'], status=status,
        mode=a.get('mode', 'practice'), started_at=a['started_at'], submitted_at=a.get('submitted_at'),
        deadline=a.get('deadline', 0), remaining_seconds=max(0, a['deadline']-t) if active and a.get('deadline') else None,
        saved_answers=sum(bool(str(v.get('value', '')).strip()) for v in (a.get('answers') or {}).values()),
        last_saved_at=max(acknowledgements) if acknowledgements else None, count=a.get('count', len(a.get('questions', []))),
        summary=summary_value, version=a.get('version'), report_allowed=bool(a.get('report_allowed')) and bool(summary_value),
        resumable=active, result_available=not active,
        compare_eligible=bool(summary_value) and a.get('mode') == 'practice' and not a.get('parent_attempt') and not a.get('competition_end'))


@router.get('')
async def my_tests(tab: Literal['progress', 'saved', 'completed'] = 'progress', exam: str = Query('', max_length=30),
                   q: str = Query('', max_length=100), status: str = Query('all', max_length=30),
                   start: date | None = None, end: date | None = None, page: int = Query(1, ge=1, le=10000), u=Depends(current)):
    if status not in ({'all', 'active'} if tab == 'progress' else {'all', 'available', 'unavailable'} if tab == 'saved' else {'all', 'completed', 'expired', 'grading', 'embargoed'}):
        raise HTTPException(422, 'This status does not apply to the selected My Tests tab.')
    t = now()
    active = {'status': 'active', '$or': [{'deadline': 0}, {'deadline': {'$gt': t}}]}
    expired = {'status': 'active', 'deadline': {'$gt': 0, '$lte': t}}
    base = {'user_id': u['id'], 'mode': {'$ne': 'preview'}}
    counts = {'progress': await attempts.count_documents({'$and': [base, active]}),
              'completed': await attempts.count_documents({'$and': [base, {'$or': [{'status': 'completed'}, expired]}]}),
              'saved': await saved.count_documents({'user_id': u['id']})}
    if tab == 'saved':
        items, total = await saved_page(u, exam, q, start, end, status, page)
    else:
        match = filters(dict(base), exam, q, start, end, 'started_at')
        match['$and'] = [active if tab == 'progress' else {'$or': [{'status': 'completed'}, expired]}]
        if status == 'expired': match['$and'].append(expired)
        elif status == 'completed': match['$and'].append({'status': 'completed', 'summary': {'$ne': None}, 'competition_end': {'$not': {'$gt': t}}})
        elif status == 'grading': match['$and'].append({'status': 'completed', 'summary': None, 'competition_end': {'$not': {'$gt': t}}})
        elif status == 'embargoed': match['$and'].append({'status': 'completed', 'competition_end': {'$gt': t}})
        elif status == 'active': match['$and'].append(active)
        total = await attempts.count_documents(match)
        projection = {k: 1 for k in ('id', 'set_id', 'title', 'exam', 'status', 'mode', 'started_at', 'submitted_at', 'deadline', 'count', 'summary', 'version', 'report_allowed', 'answers', 'competition_end', 'parent_attempt')}
        rows = await attempts.find(match, {'_id': 0, **projection}).sort([('started_at', -1), ('id', -1)]).skip((page-1)*SIZE).limit(SIZE).to_list(SIZE)
        items = [history_item(a, t).model_dump() for a in rows]
    return {'items': items, 'total': total, 'page': page, 'pages': max(1, math.ceil(total/SIZE)), 'counts': counts, 'server_now': t}


@router.post('/compare')
async def compare(data: CompareAttemptsPayload, u=Depends(current)):
    if data.left == data.right:
        raise HTTPException(409, 'Choose two different completed attempts.')
    left, right = await released(data.left, u), await released(data.right, u)
    if any(a.get('mode') != 'practice' or a.get('parent_attempt') or a.get('competition_end') for a in (left, right)) or paper_basis(left) != paper_basis(right):
        raise HTTPException(409, 'Compare only the same paper, frozen version and marking basis. Chapter/full-paper mixes, revision retries and different versions are not equivalent.')
    left, right = sorted((left, right), key=lambda a: (a['submitted_at'], a['id']))
    l, r = point(left), point(right)
    subjects = sorted(set(l['subjects']) | set(r['subjects']))
    return {'left': l, 'right': r, 'score_delta': round(r['score']-l['score'], 2),
            'accuracy_delta': round(r['accuracy']-l['accuracy'], 1) if r['accuracy'] is not None and l['accuracy'] is not None else None,
            'time_delta': r['seconds']-l['seconds'] if r['seconds'] is not None and l['seconds'] is not None else None,
            'subjects': [{'name': name, 'before': l['subjects'].get(name), 'after': r['subjects'].get(name)} for name in subjects],
            'basis': 'Same frozen paper, original key and marking rules. Retakes measure practice progress, not fresh-paper readiness.'}
