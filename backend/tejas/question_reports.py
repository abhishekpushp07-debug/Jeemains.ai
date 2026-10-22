"""Private student issue receipts and authorised editorial triage, never key changes."""
from typing import Literal
from uuid import uuid5, NAMESPACE_URL
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from pymongo.errors import DuplicateKeyError
from .db import db, now, audit
from .auth import current, staff
from .attempts import owned
from .documents import BaseDocument
from .request_contracts import QuestionReportPayload, QuestionReportReviewPayload

router = APIRouter(prefix='/api', tags=['Question reports'])
reports = db.tejas_question_reports


class QuestionReport(BaseDocument):
    user_id: str
    attempt_id: str
    set_id: str
    question_id: str
    number: int
    title: str
    exam: str
    version: int
    category: str
    context: str
    note: str
    status: Literal['open', 'reviewing', 'resolved'] = 'open'
    created_at: float
    review_note: str = ''
    reviewed_at: float | None = None


class Receipt(BaseModel):
    id: str
    question_id: str
    status: str
    category: str
    created_at: float


def receipt(r):
    return Receipt(id=r.id, question_id=r.question_id, status=r.status, category=r.category, created_at=r.created_at)


@router.get('/attempts/{id}/question-reports', response_model=list[Receipt])
async def my_reports(id: str, u=Depends(current)):
    await owned(id, u)
    return [receipt(QuestionReport.from_mongo(d)) async for d in reports.find({'attempt_id': id, 'user_id': u['id']})]


@router.post('/attempts/{id}/questions/{qid}/report-wrong', response_model=Receipt)
async def report_wrong(id: str, qid: str, data: QuestionReportPayload, u=Depends(current)):
    a = await owned(id, u)
    q = next((q for q in a['questions'] if q['id'] == qid), None)
    if not q or (q.get('bonus') and not a.get('bonus_unlocked_at')):
        raise HTTPException(404, 'Question not available in this attempt.')
    released = a['status'] == 'completed' and a.get('competition_end', 0) <= now()
    if not released and (data.context != 'attempt' or data.category in ('key', 'solution')):
        raise HTTPException(403, 'Only question or display issues can be reported before results are released.')
    rid = str(uuid5(NAMESPACE_URL, f"question-report:{u['id']}:{id}:{qid}"))
    r = QuestionReport(id=rid, user_id=u['id'], attempt_id=id, set_id=a['set_id'], question_id=qid,
        number=q['number'], title=a['title'], exam=a['exam'], version=a['version'], category=data.category,
        context=data.context, note=data.note.strip(), created_at=now())
    try:
        await reports.insert_one(r.to_mongo())
    except DuplicateKeyError:
        r = QuestionReport.from_mongo(await reports.find_one({'_id': rid, 'user_id': u['id']}))
    return receipt(r)


@router.get('/studio/question-reports')
async def report_list(status: Literal['open', 'reviewing', 'resolved', 'all'] = 'open', page: int = Query(1, ge=1, le=10000), u=Depends(staff)):
    query = {} if status == 'all' else {'status': status}
    rows = []
    async for d in reports.find(query).sort('created_at', -1).skip((page-1)*30).limit(30):
        r = QuestionReport.from_mongo(d)
        rows.append(r.model_dump(exclude={'user_id'}))
    counts = {state: await reports.count_documents({'status': state}) for state in ('open', 'reviewing', 'resolved')}
    return {'items': rows, 'counts': counts, 'page': page, 'total': await reports.count_documents(query)}


@router.post('/studio/question-reports/{id}/review')
async def review_report(id: str, data: QuestionReportReviewPayload, u=Depends(staff)):
    row = await reports.find_one({'_id': id})
    if not row:
        raise HTTPException(404, 'Report not found.')
    await reports.update_one({'_id': id}, {'$set': {'status': data.status, 'review_note': data.note.strip(), 'reviewed_at': now()}})
    await audit(u['id'], 'Question report reviewed', id, data.status + ': ' + data.note.strip())
    return {'id': id, 'status': data.status}
