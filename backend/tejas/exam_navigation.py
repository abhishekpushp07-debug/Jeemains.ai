"""Exam-scoped navigation. Never infer a full mock from its title or length."""
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from .auth import current
from .live_window import score_sealed
from .catalog import PROJECT
from .content import summary
from .db import attempts, sets, now, db
from .canonical import EPOCH_NOW
from .structure import CHAPTER_FILTER, MOCK_FILTER, ORDER, exam_doc, section_by_slug, section_view, live_query, visibility

router = APIRouter(prefix='/api/exam-navigation', tags=['Exam navigation'])
PAGE_SIZE = 12


def classify_set(s):
    if s.get('test_kind') == 'pyq':
        return 'pyq'
    if s.get('chapter_book_id') or s.get('test_kind') == 'chapter':
        return 'chapter'
    if s.get('test_kind') == 'mock' or s.get('full_length') is True:
        return 'mock'
    return 'practice'


class NavigationCatalogue(BaseModel):
    exam: str
    kind: str
    items: list[dict]
    subject_counts: dict[str, int] = Field(default_factory=dict)
    total: int
    page: int
    pages: int
    section: dict = Field(default_factory=dict)


class NavigationHistory(BaseModel):
    exam: str
    items: list[dict]
    total: int
    page: int
    pages: int


@router.get('/{slug}/catalogue', response_model=NavigationCatalogue)
async def catalogue(slug: str, kind: Literal['mocks', 'chapters'] = 'chapters', section: str = Query('', max_length=60),
                    subject: str = Query('', max_length=100), q: str = Query('', max_length=100),
                    page: int = Query(1, ge=1, le=10000), user=Depends(current)):
    await visibility()
    exam = await exam_doc(slug, user)
    found = await section_by_slug(slug, section or kind, user)
    kind = 'chapters' if found['layout'] == 'chapters' else 'mocks'
    query = live_query(user, exam, found, q)
    if subject:
        query['$and'].append({'$or': [{'chapter_subject': subject}, {'questions.subject': subject}]})
    total = await sets.count_documents(query)
    rows = await sets.find(query, {**PROJECT, 'test_kind': 1, 'full_length': 1}).sort(ORDER).skip((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).to_list(PAGE_SIZE)
    subjects = []
    if kind == 'chapters':
        subjects = await sets.aggregate([
            {'$match': live_query(user, exam, found)},
            {'$project': {'subjects': {'$cond': [
                {'$ne': [{'$ifNull': ['$chapter_subject', '']}, '']},
                ['$chapter_subject'], {'$setUnion': ['$questions.subject', []]},
            ]}}},
            {'$unwind': '$subjects'},
            {'$group': {'_id': '$subjects', 'count': {'$sum': 1}}},
            {'$sort': {'_id': 1}}, {'$limit': 30},
        ]).to_list(30)
    latest = {}
    if rows:
        history = await attempts.aggregate([
            {'$match': {'user_id': user['id'], 'set_id': {'$in': [s['id'] for s in rows]}, 'mode': 'practice'}},
            {'$sort': {'set_id': 1, 'started_at': -1, 'id': -1}},
            {'$group': {'_id': '$set_id', 'item': {'$first': {
                'id': '$id', 'status': '$status', 'deadline': '$deadline', '_database_now': EPOCH_NOW,
            }}}},
        ]).to_list(PAGE_SIZE)
        for a in history:
            value = a['item']
            t = value.pop('_database_now')
            if value.get('deadline') and value['deadline'] <= t:
                value['status'] = 'completed'
            latest[a['_id']] = value
    saved_ids = {d['set_id'] async for d in db.tejas_saved_tests.find({'user_id': user['id'], 'set_id': {'$in': [s['id'] for s in rows]}}, {'_id': 0, 'set_id': 1})} if rows else set()
    return NavigationCatalogue(exam=exam['name'], kind=kind, section=section_view(found), total=total, page=page,
        pages=max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE),
        subject_counts={s['_id']: s['count'] for s in subjects if s['_id']},
        items=[{**summary(s), 'test_kind': classify_set(s), 'attempt': latest.get(s['id']), 'saved': s['id'] in saved_ids} for s in rows])


@router.get('/{slug}/history', response_model=NavigationHistory)
async def history(slug: str, kind: Literal['all', 'mock', 'pyq', 'chapter', 'practice'] = 'all',
                  days: Literal['all', '7', '30', '90'] = 'all',
                  page: int = Query(1, ge=1, le=10000), user=Depends(current)):
    from .attempts import finalize
    await visibility()
    exam = (await exam_doc(slug, user))['key']
    match = {'user_id': user['id'], 'exam': exam, 'mode': {'$ne': 'preview'}}
    if days != 'all':
        match['started_at'] = {'$gte': now() - int(days) * 86400}
    fields = {k: 1 for k in ('id', 'set_id', 'title', 'exam', 'mode', 'version', 'started_at',
        'deadline', 'status', 'submitted_at', 'receipt', 'reason', 'summary', 'count',
        'grading_status', 'competition_end', 'test_kind', 'series_id')}
    pipeline = [
        {'$match': match},
        {'$sort': {'started_at': -1, 'id': -1}},
        {'$project': {'_id': 0, **fields}},
        {'$lookup': {'from': sets.name, 'let': {'sid': '$set_id'}, 'pipeline': [
            {'$match': {'$expr': {'$eq': ['$id', '$$sid']}}},
            {'$project': {'_id': 0, 'chapter_book_id': 1, 'test_kind': 1, 'full_length': 1}},
            {'$limit': 1},
        ], 'as': '_sources'}},
        {'$set': {'_source': {'$arrayElemAt': ['$_sources', 0]}}},
        {'$set': {'test_kind': {'$ifNull': ['$test_kind', {'$switch': {'branches': [
            {'case': {'$eq': ['$_source.test_kind', 'pyq']}, 'then': 'pyq'},
            {'case': {'$or': [{'$ne': [{'$ifNull': ['$_source.chapter_book_id', '']}, '']}, {'$eq': ['$_source.test_kind', 'chapter']}]}, 'then': 'chapter'},
            {'case': {'$or': [{'$eq': ['$_source.test_kind', 'mock']}, {'$eq': ['$_source.full_length', True]}]}, 'then': 'mock'},
        ], 'default': 'practice'}}]}}},
    ]
    if kind != 'all':
        pipeline.append({'$match': {'test_kind': kind}})
    pipeline.append({'$facet': {
        'items': [{'$skip': (page - 1) * 20}, {'$limit': 20}, {'$project': {**fields, '_database_now': EPOCH_NOW}}],
        'meta': [{'$count': 'total'}],
    }})
    result = (await attempts.aggregate(pipeline).to_list(1))[0]
    rows = result['items']
    for a in rows:
        t = a.pop('_database_now')
        if a['status'] == 'active' and a.get('deadline') and a['deadline'] <= t:
            closed = await finalize(a['id'], 'time_limit', projection={'_id': 0, **fields})
            a.update({k: v for k, v in closed.items() if k in fields})
        if score_sealed(a, t):
            a['summary'] = None
        a['server_now'] = t
    total = result['meta'][0]['total'] if result['meta'] else 0
    return NavigationHistory(exam=exam, items=rows, total=total, page=page, pages=max(1, (total + 19) // 20))
