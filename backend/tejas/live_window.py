"""Live exam start window: new starts stay open 15 minutes and every starter keeps the full duration."""
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from .db import sets, now

START_WINDOW = 15 * 60
IST = ZoneInfo('Asia/Kolkata')


def window(start, minutes, closes=None):
    """(last_start_at, end_at): a student starting at last_start_at still gets all `minutes`."""
    last = start + START_WINDOW if closes is None else max(start + START_WINDOW, closes - minutes * 60)
    return last, max(closes or 0, last + minutes * 60)


def can_start(s, t):
    return not s.get('last_start_at') or t <= s['last_start_at']


def guard(s, t):
    if s.get('competition') and not s.get('series_id') and not can_start(s, t):
        d = datetime.fromtimestamp(s['last_start_at'], IST)
        at = f"{d.day} {d:%b}, {d.hour % 12 or 12}:{d:%M %p}"
        raise HTTPException(409, f"Starting closed at {at} IST so that every student gets the full "
                                 f"{s['rules']['minutes']} minutes. Students who started on time keep their full time.")


def score_sealed(a, t):
    """All India series keep scores sealed until the day closes; other live exams show the score on submission."""
    return bool(a.get('series_id')) and a.get('competition_end', 0) > t


async def apply_to_upcoming():
    """Idempotent: live exams scheduled before the window existed get it before they open."""
    t = now()
    query = {'competition': True, 'series_id': {'$exists': False}, 'start_at': {'$gt': t}, 'last_start_at': {'$exists': False}}
    async for s in sets.find(query, {'_id': 0, 'id': 1, 'start_at': 1, 'end_at': 1, 'rules.minutes': 1}):
        minutes = s['rules']['minutes']
        fixed = abs(s['end_at'] - s['start_at'] - minutes * 60) < 2
        last, end = window(s['start_at'], minutes, None if fixed else s['end_at'])
        await sets.update_one({**query, 'id': s['id'], 'start_at': s['start_at']}, {'$set': {'last_start_at': last, 'end_at': end}})
