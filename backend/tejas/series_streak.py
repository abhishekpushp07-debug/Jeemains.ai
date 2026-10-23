from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from .auth import current
from .db import attempts, now
from .live_series import SERIES_ID, FIRST, LAST, IST, window

router = APIRouter(prefix='/api/series/all-india-jee', tags=['Personal series streak'])
CUPS = [(7, 'Bronze', 'First week'), (15, 'Silver', 'Finding rhythm'),
        (30, 'Gold', 'Going the distance'), (45, 'Diamond', 'Built on consistency'),
        (62, 'Champion', 'The complete journey')]


def streak_progress(completions, active, timestamp):
    today = datetime.fromtimestamp(timestamp, IST).date()
    dates = [(FIRST + timedelta(days=i)).isoformat() for i in range(62)]
    done = {}
    for row in completions:
        day, submitted = row['date'], row['submitted_at']
        if day in dates and window(day)['opens_at'] <= submitted <= min(timestamp, window(day)['closes_at']):
            done[day] = row['attempt_id']
    run = best = 0
    earned = {}
    for day in dates:
        run = run + 1 if day in done else 0
        best = max(best, run)
        if run in (7, 15, 30, 45, 62) and run not in earned:
            earned[run] = day
    anchor = min(today, LAST)
    if FIRST <= today <= LAST and today.isoformat() not in done:
        anchor -= timedelta(days=1)
    current_count = 0
    while anchor >= FIRST and anchor.isoformat() in done:
        current_count += 1
        anchor -= timedelta(days=1)
    by_day = {a['series_date']: a for a in active if a['series_date'] in dates}
    days = []
    for i, day in enumerate(dates):
        a = by_day.get(day)
        state = ('completed' if day in done else 'pending' if a and a['deadline'] <= timestamp
                 else 'in_progress' if a else 'missed' if day < today.isoformat()
                 else 'today' if day == today.isoformat() else 'upcoming')
        days.append({'day': i + 1, 'date': day, 'state': state,
                     'attempt_id': done.get(day) or (a or {}).get('id')})
    milestones = [{'days': n, 'title': title, 'subtitle': subtitle, 'earned': best >= n,
                   'earned_date': earned.get(n)} for n, title, subtitle in CUPS]
    next_cup = next((m for m in milestones if not m['earned']), None)
    today_day = next((d for d in days if d['date'] == today.isoformat()), None)
    next_refresh = datetime.combine(today + timedelta(days=1), datetime.min.time(), IST).timestamp()
    return {'series_id': SERIES_ID, 'server_now': timestamp, 'timezone': 'Asia/Kolkata',
            'first_date': FIRST.isoformat(), 'last_date': LAST.isoformat(), 'today': today.isoformat(),
            'stage': 'prelaunch' if today < FIRST else 'finished' if today > LAST else 'live',
            'total_days': 62, 'completed_count': len(done), 'current_streak': current_count,
            'best_streak': best, 'today_state': (today_day or {}).get('state'), 'days': days,
            'milestones': milestones, 'next_milestone': next_cup, 'next_refresh_at': next_refresh,
            'policy': 'One finalized live test on its scheduled India-time day earns one day, regardless of score. Sealed automatic time-limit submissions count too. Archive practice and retries do not count. An unfinished current day does not break yesterday’s streak until midnight IST. Earned cups use your best consecutive-day streak and remain yours after a break. After 31 January, the ending streak is preserved.'}


@router.get('/streak')
async def progress(u=Depends(current)):
    t = now()
    match = {'user_id': u['id'], 'series_id': SERIES_ID, 'mode': 'series_live',
             'series_date': {'$gte': FIRST.isoformat(), '$lte': LAST.isoformat()},
             'status': 'completed', 'submitted_at': {'$lte': t}, 'parent_attempt': None}
    rows = await attempts.aggregate([
        {'$match': match}, {'$sort': {'submitted_at': 1}},
        {'$group': {'_id': '$series_date', 'attempt_id': {'$first': '$id'}, 'submitted_at': {'$first': '$submitted_at'}}},
        {'$project': {'_id': 0, 'date': '$_id', 'attempt_id': 1, 'submitted_at': 1}},
        {'$limit': 62},
    ]).to_list(62)
    active = await attempts.find({**match, 'status': 'active', 'submitted_at': None},
                                 {'_id': 0, 'id': 1, 'series_date': 1, 'deadline': 1}).limit(62).to_list(62)
    return {'user_id': u['id'], **streak_progress(rows, active, t)}
