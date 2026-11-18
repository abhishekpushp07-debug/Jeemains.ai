"""Time capture for an attempt: on-screen stretches, answer changes and mark toggles, kept apart from the attempt record.
Each device numbers its own events; the server keeps a cursor per device, so sending the same events again changes nothing."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from pymongo.errors import DuplicateKeyError
from .auth import current
from .canonical import clocked_one
from .db import attempts, db
from .analysis_rules import RULES
from .timeline_models import Batch

router = APIRouter(prefix='/api/attempts', tags=['Time capture'])
timelines = db.tejas_attempt_timeline
MAX_EVENTS, MAX_DEVICES, LATE_SECONDS, SLACK = 2000, 8, 600, 3
HEADER = {'_id': 0, 'status': 1, 'started_at': 1, 'ready_until': 1, 'deadline': 1, 'submitted_at': 1, 'response_schema': 1}


class TimelineReceipt(BaseModel):
    cursor: int
    accepted: bool = True


def sanitize(batch, known, start, end):
    """Keep only events of this paper, inside its window, in order and without overlaps."""
    out, edge, cap = [], start, RULES['stretch_cap']
    for e in batch.events:
        if e.q not in known:
            continue
        if e.k == 'v':
            if e.b is None:
                continue
            a = max(e.a, edge)
            b = min(e.b, end, a + cap)
            if b - a < 0.5:
                continue
            edge = b
            out.append({'s': batch.sid, 'n': e.n, 'k': 'v', 'q': e.q, 'a': round(a, 1), 'b': round(b, 1)})
        elif start - SLACK <= e.a <= end:
            out.append({'s': batch.sid, 'n': e.n, 'k': e.k, 'q': e.q, 'a': round(max(e.a, start), 1), 'v': e.v or ''})
    return out


async def ingest(attempt_id, user_id, batch, known, start, end):
    """Append this device's next events once and return its cursor (the last event number the server holds)."""
    first, last = batch.events[0].n, batch.events[-1].n
    if any(e.n != first + i for i, e in enumerate(batch.events)):
        raise HTTPException(422, 'Number the time events in order, without gaps.')
    clean = sanitize(batch, known, start, end)
    key = 'cursor.' + batch.sid
    cursor, room = first - 1, MAX_EVENTS
    for _ in range(3):
        fresh = [e for e in clean if e['n'] > cursor][:max(0, room)]
        guard = {'_id': attempt_id, 'user_id': user_id, key: cursor if cursor else {'$exists': False},
                 'count': {'$lte': MAX_EVENTS - len(fresh)}}
        change = {'$set': {key: last}, '$inc': {'count': len(fresh)}}
        if fresh:
            change['$push'] = {'events': {'$each': fresh}}
        if not cursor:
            guard['devices'] = {'$lt': MAX_DEVICES}
            change['$inc']['devices'] = 1
        try:
            done = await timelines.update_one(guard, change, upsert=not cursor)
            if done.matched_count or done.upserted_id is not None:
                return last
        except DuplicateKeyError:
            pass
        doc = await timelines.find_one({'_id': attempt_id, 'user_id': user_id}, {'_id': 0, 'cursor': 1, 'count': 1, 'devices': 1})
        if not doc:
            cursor = 0  # the record is gone: start this device again
            continue
        stored = doc.get('cursor', {}).get(batch.sid, 0)
        if stored >= last or (not stored and doc.get('devices', 0) >= MAX_DEVICES):
            return max(stored, last)
        cursor, room = stored, MAX_EVENTS - doc.get('count', 0)
    raise HTTPException(409, 'The time record is busy. Send it again.', headers={'Retry-After': '2'})


async def accept(attempt_id, user_id, batch, a, t):
    """a: the attempt's HEADER fields. Open while the attempt runs and for 10 minutes after it closes."""
    done = a['status'] == 'completed'
    if done and t > (a.get('submitted_at') or 0) + LATE_SECONDS:
        raise HTTPException(409, 'This attempt ended more than 10 minutes ago. Its time record is final.')
    start = a.get('ready_until') or a['started_at']
    end = a['submitted_at'] if done else min(a.get('deadline') or t, t)
    cursor = await ingest(attempt_id, user_id, batch, set(a.get('response_schema') or ()), start, end + SLACK)
    if done:
        from .class_stats import forget
        await forget(attempt_id)
    return cursor


async def accept_for(attempt_id, user_id, batch):
    a = await clocked_one(attempts, {'id': attempt_id, 'user_id': user_id}, HEADER)
    if not a:
        raise HTTPException(404, 'Attempt not found.')
    return await accept(attempt_id, user_id, batch, a, a['_database_now'])


@router.post('/{id}/timeline', response_model=TimelineReceipt)
async def flush_timeline(id: str, data: Batch, u=Depends(current)):
    return TimelineReceipt(cursor=await accept_for(id, u['id'], data))
