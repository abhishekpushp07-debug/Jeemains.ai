"""A small usage log for the CEO dashboard: which pages and Rank tools people open. Short words and ids only,
never answers, scores, phone numbers or sessions. Staff visits are not kept."""
import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request, Response
from .auth import maybe_current
from .db import db, uid, now
from .phone import client_ip
from .request_contracts import EventPayload

router = APIRouter(prefix='/api', tags=['Usage events'])
events = db.tejas_events
KEEP, LIMIT = 400 * 86400, 120
_seen = {}


@router.post('/events', status_code=204)
async def record_event(data: EventPayload, request: Request, u=Depends(maybe_current)):
    u = u or {}
    who, slot = u.get('id') or client_ip(request) or data.vid or 'anon', int(time.time() // 600)
    last = _seen.get(who)
    count = (last[1] if last and last[0] == slot else 0) + 1
    _seen[who] = (slot, count)
    if len(_seen) > 50000:
        _seen.clear()
    if count <= LIMIT and u.get('role', 'student') == 'student':
        t = now()
        await events.insert_one({'id': uid(), 'name': data.name, 'at': t, 'user_id': u.get('id'), 'vid': data.vid,
                                 'props': data.props.model_dump(exclude_none=True) if data.props else {},
                                 'expires_at': datetime.fromtimestamp(t + KEEP, timezone.utc)})
    return Response(status_code=204)
