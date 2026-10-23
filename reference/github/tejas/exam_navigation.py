"""Exam-scoped navigation. Never infer a full mock from its title or length."""
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from .auth import current
from .catalog import available, PROJECT
from .content import summary
from .db import attempts, sets, now, db

router = APIRouter(prefix='/api/exam-navigation', tags=['Exam navigation'])
EXAMS = {'jee-main': 'JEE Main', 'bitsat': 'BITSAT', 'comedk': 'COMEDK'}
PAGE_SIZE = 12
CHAPTER_FILTER = {'$or': [
    {'chapter_book_id': {'$exists': True, '$nin': [None, '']}},
    {'test_kind': 'chapter'},
]}
MOCK_FILTER = {'$and': [
    {'$or': [{'chapter_book_id': {'$exists': False}}, {'chapter_book_id': None}, {'chapter_book_id': ''}]},
    {'$or': [{'test_kind': 'mock'}, {'full_length': True}]},
    {'test_kind': {'$ne': 'chapter'}},
]}


def exam_name(slug):
    if slug not in EXAMS:
        raise HTTPException(404, 'This exam is not supported.')
    return EXAMS[slug]


def classify_set(s):
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


class NavigationHistory(BaseModel):
    exam: str
    items: list[dict]
    total: int
    page: int
    pages: int


def live_query(user, exam, kind, search=''):
    q = available(user, exam, search)
    q['qa_only'] = {'$ne': True}
    t = now()
    q['$and'].extend([
        CHAPTER_FILTER if kind == 'chapters' else MOCK_FILTER,
        {'$or': [{'live_enabled': {'$exists': False}}, {'live_enabled': True}]},
        {'$or': [{'start_at': {'$exists': False}}, {'start_at': {'$lte': t}}]},
        {'$or': [{'end_at': {'$exists': False}}, {'end_at': {'$gt': t}}]},
    ])
    return q


@router.get('/{slug}/catalogue', response_model=NavigationCatalogue)
async def catalogue(slug: str, kind: Literal['mocks', 'chapters'] = 'chapters',
                    subject: str = Query('', max_length=100), q: str = Query('', max_length=100),
                    page: int = Query(1, ge=1, le=10000), user=Depends(current)):
    exam = exam_name(slug)
    query = live_query(user, exam, kind, q)
    if subject:
        query['$and'].append({'$or': [{'chapter_subject': subject}, {'questions.subject': subject}]})
    total = await sets.count_documents(query)
    rows = await sets.find(query, {**PROJECT, 'test_kind': 1, 'full_length': 1}).sort(
        [('chapter_subject', 1), ('chapter_number', 1), ('mock_number', 1), ('created_at', -1), ('id', 1)]
    ).skip((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).to_list(PAGE_SIZE)
    subjects = []
    if kind == 'chapters':
        subjects = await sets.aggregate([
            {'$match': live_query(user, exam, kind)},
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
                'id': '$id', 'status': '$status', 'deadline': '$deadline',
            }}}},
        ]).to_list(PAGE_SIZE)
        for a in history:
            value = a['item']
            if value.get('deadline') and value['deadline'] <= now():
                value['status'] = 'completed'
            latest[a['_id']] = value
    saved_ids = {d['set_id'] async for d in db.tejas_saved_tests.find({'user_id': user['id'], 'set_id': {'$in': [s['id'] for s in rows]}}, {'_id': 0, 'set_id': 1})} if rows else set()
    return NavigationCatalogue(exam=exam, kind=kind, total=total, page=page,
        pages=max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE),
        subject_counts={s['_id']: s['count'] for s in subjects if s['_id']},
        items=[{**summary(s), 'test_kind': classify_set(s), 'attempt': latest.get(s['id']), 'saved': s['id'] in saved_ids} for s in rows])


@router.get('/{slug}/history', response_model=NavigationHistory)
async def history(slug: str, kind: Literal['all', 'mock', 'chapter', 'practice'] = 'all',
                  days: Literal['all', '7', '30', '90'] = 'all',
                  page: int = Query(1, ge=1, le=10000), user=Depends(current)):
    from .attempts import finalize
    exam = exam_name(slug)
    match = {'user_id': user['id'], 'exam': exam, 'mode': {'$ne': 'preview'}}
    if days != 'all':
        match['started_at'] = {'$gte': now() - int(days) * 86400}
    fields = {k: 1 for k in ('id', 'set_id', 'title', 'exam', 'mode', 'version', 'started_at',
        'deadline', 'status', 'submitted_at', 'receipt', 'reason', 'summary', 'count',
        'grading_status', 'competition_end', 'test_kind')}
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
        {'$set': {'test_kind': {'$ifNull': ['$test_kind', {'$cond': [
            {'$or': [
                {'$ne': [{'$ifNull': ['$_source.chapter_book_id', '']}, '']},
                {'$eq': ['$_source.test_kind', 'chapter']},
            ]}, 'chapter', {'$cond': [
                {'$or': [{'$eq': ['$_source.test_kind', 'mock']}, {'$eq': ['$_source.full_length', True]}]},
                'mock', 'practice',
            ]},
        ]}]}}},
    ]
    if kind != 'all':
        pipeline.append({'$match': {'test_kind': kind}})
    pipeline.append({'$facet': {
        'items': [{'$skip': (page - 1) * 20}, {'$limit': 20}, {'$project': fields}],
        'meta': [{'$count': 'total'}],
    }})
    result = (await attempts.aggregate(pipeline).to_list(1))[0]
    rows = result['items']
    for a in rows:
        if a['status'] == 'active' and a.get('deadline') and a['deadline'] <= now():
            closed = await finalize(a['id'], 'time_limit')
            a.update({k: v for k, v in closed.items() if k in fields})
        if a.get('competition_end', 0) > now():
            a['summary'] = None
        a['server_now'] = now()
    total = result['meta'][0]['total'] if result['meta'] else 0
    return NavigationHistory(exam=exam, items=rows, total=total, page=page, pages=max(1, (total + 19) // 20))
