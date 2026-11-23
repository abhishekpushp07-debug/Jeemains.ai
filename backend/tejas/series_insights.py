"""All India Series, every day together, for one student: subject trend, accuracy and time trend, where marks keep going,
and each day's class average and topper (the same live attempts the day's rank counts, shown once the rank is out).
Read-only, the student's own attempts only."""
import time
from datetime import timedelta
from fastapi import APIRouter, Depends
from .auth import current
from .canonical import database_now
from .db import attempts
from .live_series import SERIES_ID, FIRST, TOTAL

router = APIRouter(prefix='/api/series/all-india-jee', tags=['Personal series insights'])
DAY_OF = {(FIRST + timedelta(days=i)).isoformat(): i + 1 for i in range(TOTAL)}
RANKED = {'mode': 'series_live', 'status': 'completed', 'grading_status': 'ready'}
FIELDS = {'_id': 0, 'id': 1, 'set_id': 1, 'mode': 1, 'series_date': 1, 'submitted_at': 1, 'competition_end': 1, 'summary': 1}
ORDER = ('Physics', 'Chemistry', 'Mathematics')
_class = {}


def pct(a, b):
    return round(100 * a / b, 1) if b else None


def mean(xs):
    return round(sum(xs) / len(xs), 1) if xs else None


def direction(values, step):
    """Last 3 days against the 3 before them (fewer when there are fewer days); 'early' under 4 days."""
    if len(values) < 4:
        return 'early', None
    k = min(3, len(values) // 2)
    change = round(sum(values[-k:]) / k - sum(values[-2 * k:-k]) / k, 1)
    return ('up' if change >= step else 'down' if change <= -step else 'flat'), change


async def class_of(set_id):
    hit = _class.get(set_id)
    if hit and hit[0] > time.monotonic():
        return hit[1]
    rows = await attempts.aggregate([{'$match': {'set_id': set_id, **RANKED}}, {'$group': {
        '_id': None, 'n': {'$sum': 1}, 'avg': {'$avg': '$summary.score'}, 'top': {'$max': '$summary.score'}, 'acc': {'$avg': '$summary.accuracy'}}}]).to_list(1)
    r = rows[0] if rows else {}
    value = {'students': r.get('n', 0), 'average': round(r['avg'], 1) if r.get('avg') is not None else None,
             'topper': r.get('top'), 'accuracy': round(r['acc'], 1) if r.get('acc') is not None else None}
    _class[set_id] = (time.monotonic() + 300, value)
    while len(_class) > 300:
        _class.pop(next(iter(_class)))
    return value


def pick_days(rows):
    """One attempt per series day: the live one, else the latest practice."""
    out = {}
    for a in rows:
        d, old = a.get('series_date'), out.get(a.get('series_date'))
        if d not in DAY_OF:
            continue
        if not old or (a['mode'] == 'series_live') > (old['mode'] == 'series_live') or (a['mode'] == old['mode'] and (a.get('submitted_at') or 0) > (old.get('submitted_at') or 0)):
            out[d] = a
    return [out[d] for d in sorted(out)]


def day_row(a):
    s = a['summary']
    each = (s.get('maximum') or 0) / (s.get('eligible_count') or sum(g.get('count', 0) for g in (s.get('subjects') or {}).values()) or 1)
    subjects = {name: {'score': g.get('score', 0), 'maximum': round(g.get('count', 0) * each), 'accuracy': pct(g.get('correct', 0), g.get('attempted', 0)),
                       'attempted': g.get('attempted', 0), 'count': g.get('count', 0)} for name, g in (s.get('subjects') or {}).items()}
    total = s.get('total_seconds') or 0
    return {'day': DAY_OF[a['series_date']], 'date': a['series_date'], 'attempt_id': a['id'], 'mode': 'live' if a['mode'] == 'series_live' else 'practice',
            'score': s.get('score'), 'maximum': s.get('maximum'), 'accuracy': s.get('accuracy'), 'attempt_rate': s.get('attempt_rate'),
            'correct': s.get('correct'), 'incorrect': s.get('incorrect'), 'skipped': s.get('skipped'), 'minutes': round(total / 60, 1),
            'sec_per_attempted': round(total / s['attempted']) if s.get('attempted') and total else None, 'subjects': subjects, 'class': None}


def chapters_of(picked):
    """Chapters where questions went wrong or were left, across days. Papers whose questions carry no chapter tag give none."""
    found = {}
    for a in picked:
        s = a['summary']
        names, whole = set(s.get('subjects') or {}), s.get('eligible_count') or s.get('count')
        for topic, g in (s.get('topics') or {}).items():
            if not topic or topic in names or g.get('count', 0) >= (whole or 10 ** 6):
                continue
            wrong, left = g.get('attempted', 0) - g.get('correct', 0), g.get('count', 0) - g.get('attempted', 0)
            c = found.setdefault(topic, {'chapter': topic, 'wrong': 0, 'skipped': 0, 'questions': 0, 'days': 0})
            c.update(wrong=c['wrong'] + wrong, skipped=c['skipped'] + left, questions=c['questions'] + g.get('count', 0), days=c['days'] + (wrong + left > 0))
    rows = [c for c in found.values() if c['wrong'] + c['skipped']]
    return sorted(rows, key=lambda c: (-c['days'], -(c['wrong'] + c['skipped']), c['chapter']))[:8], bool(found)


def subject_trends(days):
    names = sorted({n for d in days for n in d['subjects']}, key=lambda n: (ORDER.index(n) if n in ORDER else 9, n))
    out = []
    for name in names:
        rows = [(d['day'], d['subjects'][name]) for d in days if name in d['subjects']]
        scores = [g['score'] for _, g in rows]
        accs = [g['accuracy'] for _, g in rows if g['accuracy'] is not None]
        way, change = direction(scores, 4)
        out.append({'subject': name, 'points': [{'day': day, 'score': g['score'], 'maximum': g['maximum'], 'accuracy': g['accuracy']} for day, g in rows],
                    'average': mean(scores), 'best': max(scores), 'maximum': max(g['maximum'] for _, g in rows), 'direction': way, 'change': change,
                    'lost': sum(g['maximum'] - g['score'] for _, g in rows), 'accuracy': mean(accs)})
    return out


@router.get('/insights')
async def insights(u=Depends(current)):
    t = await database_now()
    rows = await attempts.find({'user_id': u['id'], 'series_id': SERIES_ID, 'mode': {'$in': ['series_live', 'series_practice']},
                                'status': 'completed', 'summary': {'$ne': None}}, FIELDS).sort('submitted_at', 1).to_list(300)
    picked = pick_days(rows)
    days = [day_row(a) for a in picked]
    for a, d in zip(picked, days):
        if a['mode'] == 'series_live':
            end = a.get('competition_end') or 0
            d['class'] = {'state': 'sealed', 'release_at': end} if end > t else {'state': 'ready', **await class_of(a['set_id'])}
    scores, accs = [d['score'] for d in days], [d['accuracy'] for d in days if d['accuracy'] is not None]
    way, change = direction(scores, 4)
    acc_way, acc_change = direction(accs, 3)
    ready = [d for d in days if (d['class'] or {}).get('state') == 'ready' and d['class'].get('average') is not None]
    chapters, tagged = chapters_of(picked)
    return {'total_days': TOTAL, 'days': days, 'subjects': subject_trends(days), 'chapters': chapters, 'chapters_tagged': tagged,
            'overall': {'days': len(days), 'live_days': sum(d['mode'] == 'live' for d in days), 'average': mean(scores), 'best': max(scores) if scores else None,
                        'direction': way, 'change': change, 'accuracy': mean(accs), 'accuracy_direction': acc_way, 'accuracy_change': acc_change,
                        'minutes': mean([d['minutes'] for d in days]), 'compared_days': len(ready),
                        'above_average_days': sum(d['score'] > d['class']['average'] for d in ready)}}
