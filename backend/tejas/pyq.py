from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field
from .auth import current
from .canonical import database_now
from .db import db
from .catalog import available

router = APIRouter(prefix='/api/pyq', tags=['Date-wise JEE Main PYQs'])


class PaperAttempt(BaseModel):
    id: str
    status: str
    started_at: float
    deadline: float = 0
    score: float | None = None


class PyqPaper(BaseModel):
    id: str
    title: str
    exam_date: str
    year: int
    shift: int
    count: int
    minutes: float
    maximum: float
    attempt: PaperAttempt | None = None
    latest_result_id: str | None = None
    attempt_count: int = 0


class PyqCatalogue(BaseModel):
    items: list[PyqPaper]
    years: list[int]
    total: int
    server_now: float
    source_note: str = 'Original PDF questions with matched supplied explanations or answer keys; independent practice, not an NTA service.'


@router.get('/jee-main', response_model=PyqCatalogue)
async def catalogue(response: Response, u=Depends(current)):
    response.headers['Cache-Control'] = 'private, no-store'
    match = {**available(u, 'JEE Main'), 'test_kind': 'pyq', 'qa_only': {'$ne': True}, 'is_deleted': {'$ne': True}}
    fields = {'_id': 0, 'id': 1, 'title': 1, 'pyq_date': 1, 'pyq_year': 1, 'pyq_shift': 1,
              'rules.minutes': 1, 'rules.correct': 1, 'count': {'$size': '$questions'}}
    rows = await db.tejas_sets.find(match, fields).sort([('pyq_date', -1), ('pyq_shift', 1), ('id', 1)]).limit(500).to_list(500)
    stamp = await database_now()
    ids = [row['id'] for row in rows]
    state = await db.tejas_attempts.aggregate([
        {'$match': {'user_id': u['id'], 'set_id': {'$in': ids}, 'mode': {'$nin': ['preview', 'retry']}}},
        {'$sort': {'started_at': -1, 'id': -1}},
        {'$facet': {
            'latest': [{'$group': {'_id': '$set_id', 'count': {'$sum': 1}, 'attempt': {'$first': {
                'id': '$id', 'status': '$status', 'started_at': '$started_at', 'deadline': '$deadline', 'score': '$summary.score'}}}}],
            'results': [{'$match': {'status': 'completed'}}, {'$group': {'_id': '$set_id', 'id': {'$first': '$id'}}}],
        }},
    ]).to_list(1)
    state = state[0] if state else {'latest': [], 'results': []}
    latest = {row['_id']: row for row in state['latest']}
    results = {row['_id']: row['id'] for row in state['results']}
    papers = []
    for row in rows:
        own = latest.get(row['id'], {})
        attempt = own.get('attempt')
        if attempt and attempt['status'] == 'active' and attempt.get('deadline') and attempt['deadline'] <= stamp:
            attempt['status'] = 'completed'
            results[row['id']] = attempt['id']
        papers.append(PyqPaper(id=row['id'], title=row['title'], exam_date=row['pyq_date'], year=row['pyq_year'],
                              shift=row['pyq_shift'], count=row['count'], minutes=row['rules']['minutes'],
                              maximum=row['count'] * row['rules']['correct'], attempt=attempt,
                              latest_result_id=results.get(row['id']), attempt_count=own.get('count', 0)))
    return PyqCatalogue(items=papers, years=sorted({p.year for p in papers}, reverse=True), total=len(papers), server_now=stamp)
