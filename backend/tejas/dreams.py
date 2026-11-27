"""The result celebration (own best broken or 40%+) and the released full mocks this website sends to the app server's
Dream College Meter. Dream lists themselves live on the app server (app_connect.py)."""
from fastapi import APIRouter, Depends
from .auth import current
from .canonical import database_now
from .db import attempts
from .learning_progress import released
from .live_window import answers_sealed

router = APIRouter(prefix='/api/dream', tags=['Dream college'])
MAX_MOCKS = 30
FULL = {'jee': 300, 'bitsat': 390, 'comedk': 180}
FULL_QUESTIONS = {'jee': 75, 'bitsat': 130, 'comedk': 180}
GOOD_PCT = 40
FIELDS = {'_id': 0, 'id': 1, 'title': 1, 'exam': 1, 'count': 1, 'summary.score': 1, 'summary.maximum': 1, 'submitted_at': 1,
          'series_id': 1, 'competition_end': 1, 'mode': 1, 'test_kind': 1}


def exam_of(name):
    n = (name or '').lower()
    return 'bitsat' if 'bitsat' in n else 'comedk' if 'comedk' in n else 'jee' if 'jee' in n and 'adv' not in n else None


def is_full(exam, a):
    s = a.get('summary') or {}
    # A chapter test and a Student Choice paper never count as a full mock (owner's rule, app book Part 1.9).
    return bool(exam) and a.get('test_kind') not in ('chapter', 'choice') and (s.get('maximum') or 0) >= FULL[exam] / 2 and (a.get('count') or 0) >= FULL_QUESTIONS[exam] * 0.9


def scaled(exam, raw, top):
    return round(raw if top >= FULL[exam] else raw / top * FULL[exam])


async def released_attempts(uid, extra=None, limit=200):
    t = await database_now()
    query = {'user_id': uid, 'status': 'completed', 'summary': {'$ne': None}, 'mode': {'$ne': 'preview'}, **(extra or {})}
    rows = await attempts.find(query, FIELDS).sort([('submitted_at', -1)]).limit(limit).to_list(limit)
    return [a for a in rows if not answers_sealed(a, t) and (a.get('summary') or {}).get('maximum')]


def mock_of(a):
    exam = exam_of(a.get('exam'))
    if not is_full(exam, a):
        return None
    s = a['summary']
    return {'id': a['id'][:64], 'exam': exam, 'score': scaled(exam, s['score'], s['maximum']), 'max': FULL[exam], 'raw': s['score'],
            'rawMax': s['maximum'], 'title': (a.get('title') or 'Mock')[:120], 'at': (a.get('submitted_at') or 0) * 1000}


async def website_mocks(uid):
    return [m for m in map(mock_of, await released_attempts(uid)) if m][:MAX_MOCKS]


def pct_of(a):
    s = a['summary']
    return round(100 * s['score'] / s['maximum'], 1)


@router.get('/celebration/{id}')
async def celebration(id: str, u=Depends(current)):
    """Should this released result sparkle? Yes when it beats the student's own best on the same exam and kind of paper
    (full mock vs chapter/part test), or when it is 40% or more of full marks."""
    a = await released(id, u)
    exam = exam_of(a.get('exam'))
    full = is_full(exam, a)
    pct = pct_of(a)
    before = [p for p in await released_attempts(u['id'], {'exam': a['exam'], 'id': {'$ne': a['id']}, 'submitted_at': {'$lt': a.get('submitted_at') or 0}})
              if is_full(exam_of(p.get('exam')), p) == full]
    best = max(before, key=pct_of, default=None)
    beat = bool(best) and pct > pct_of(best)
    good = pct >= GOOD_PCT
    s = a['summary']
    return {'exam': a['exam'], 'dream_exam': exam, 'title': a.get('title'), 'score': s['score'], 'maximum': s['maximum'], 'pct': pct,
            'full': full, 'scaled': scaled(exam, s['score'], s['maximum']) if full else None,
            'best_before': {'score': best['summary']['score'], 'maximum': best['summary']['maximum'], 'pct': pct_of(best)} if best else None,
            'previous': len(before), 'beat_best': beat, 'good': good, 'celebrate': s['score'] > 0 and (beat or good)}
