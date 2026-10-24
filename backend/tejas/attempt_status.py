from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from .auth import current
from .db import attempts
from .canonical import clocked_one
from .attempts import finalize

router = APIRouter(prefix='/api/attempts', tags=['Attempt status'])
HEADER = {key: 1 for key in ('id', 'user_id', 'set_id', 'status', 'deadline', 'pack_id', 'rules',
                             'competition_end', 'bonus_unlocked_at', 'solution_events_version',
                             'submitted_at', 'receipt', 'grading_status', 'sealed_seq', 'summary')}
HEADER['_id'] = 0


async def owned_header(id, user):
    record = await clocked_one(attempts, {'id': id, 'user_id': user['id']}, HEADER)
    if not record:
        raise HTTPException(404, 'Attempt not found.')
    if record['status'] == 'active' and record.get('deadline', 0) and record['deadline'] <= record['_database_now']:
        await finalize(id, 'time_limit', projection=HEADER)
        record = await clocked_one(attempts, {'id': id, 'user_id': user['id']}, HEADER)
    return record


class AttemptStatus(BaseModel):
    id: str
    status: str
    deadline: float
    server_now: float
    receipt: str | None = None
    submitted_at: float | None = None
    grading_status: str | None = None
    sealed_seq: int | None = None


@router.get('/{id}/status', response_model=AttemptStatus)
async def status_attempt(id: str, u=Depends(current)):
    a = await owned_header(id, u)
    return AttemptStatus(**{k: a.get(k) for k in ('id', 'status', 'deadline', 'receipt', 'submitted_at', 'grading_status', 'sealed_seq')}, server_now=a['_database_now'])
