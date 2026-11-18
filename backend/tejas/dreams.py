"""Dream colleges (up to 5 per exam) kept with the student's account, the released full mocks they are measured
against, and the result celebration (own best broken or 40%+). Same rules as the app's Dream College Meter."""
from typing import Annotated, List, Literal, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from pymongo.errors import DuplicateKeyError
from .auth import current
from .canonical import database_now
from .db import db, attempts, now
from .learning_progress import released
from .live_window import answers_sealed

router = APIRouter(prefix='/api/dream', tags=['Dream college'])
store = db.tejas_dreams
DreamExam = Literal['jee', 'bitsat', 'comedk']
MAX_DREAMS, MAX_MOCKS = 5, 30
FULL = {'jee': 300, 'bitsat': 390, 'comedk': 180}
FULL_QUESTIONS = {'jee': 75, 'bitsat': 130, 'comedk': 180}
GOOD_PCT = 40
FIELDS = {'_id': 0, 'id': 1, 'title': 1, 'exam': 1, 'count': 1, 'summary.score': 1, 'summary.maximum': 1, 'submitted_at': 1,
          'series_id': 1, 'competition_end': 1, 'mode': 1}


class Dream(BaseModel):
    model_config = ConfigDict(extra='ignore')
    id: str = Field(min_length=1, max_length=80)
    exam: DreamExam
    college: str = Field(max_length=160)
    branch: str = Field(max_length=200)
    need: float = Field(ge=-100, le=400)
    range: Optional[List[float]] = Field(default=None, min_length=2, max_length=2)
    note: str = Field(default='', max_length=200)
    at: float


class DreamsIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    dreams: List[Dream] = Field(max_length=MAX_DREAMS * 3)
    base: List[str] = Field(default_factory=list, max_length=MAX_DREAMS * 3)


class CheeredIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    ids: List[Annotated[str, Field(min_length=1, max_length=80)]] = Field(min_length=1, max_length=MAX_DREAMS * 3)


def exam_of(name):
    n = (name or '').lower()
    return 'bitsat' if 'bitsat' in n else 'comedk' if 'comedk' in n else 'jee' if 'jee' in n and 'adv' not in n else None


def is_full(exam, a):
    s = a.get('summary') or {}
    return bool(exam) and (s.get('maximum') or 0) >= FULL[exam] / 2 and (a.get('count') or 0) >= FULL_QUESTIONS[exam] * 0.9


def scaled(exam, raw, top):
    return round(raw if top >= FULL[exam] else raw / top * FULL[exam])


def merge(current_list, base, mine):
    """The browser's changes on the account's current list: removed dreams go, added ones join while that exam has room."""
    had, here = set(base), {d['id']: d for d in mine}
    out = [here.get(d['id'], d) for d in current_list if d['id'] not in had or d['id'] in here]
    for d in mine:
        if d['id'] not in had and all(x['id'] != d['id'] for x in out) and sum(x['exam'] == d['exam'] for x in out) < MAX_DREAMS:
            out.append(d)
    return out


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
    return {'id': a['id'], 'exam': exam, 'score': scaled(exam, s['score'], s['maximum']), 'max': FULL[exam], 'raw': s['score'],
            'rawMax': s['maximum'], 'title': a.get('title') or 'Mock', 'at': (a.get('submitted_at') or 0) * 1000}


@router.get('')
async def read(u=Depends(current)):
    doc = await store.find_one({'uid': u['id']}, {'_id': 0, 'dreams': 1, 'cheered': 1}) or {}
    mocks = [m for m in map(mock_of, await released_attempts(u['id'])) if m][:MAX_MOCKS]
    return {'dreams': doc.get('dreams', []), 'cheered': doc.get('cheered', []), 'mocks': mocks}


@router.put('/dreams')
async def save_dreams(data: DreamsIn, u=Depends(current)):
    ids = [d.id for d in data.dreams]
    if len(ids) != len(set(ids)):
        raise HTTPException(400, 'Ek college do baar hai.')
    if any(sum(d.exam == e for d in data.dreams) > MAX_DREAMS for e in FULL):
        raise HTTPException(400, f'Har exam ke {MAX_DREAMS} dream college hi ho sakte hain.')
    mine = [d.model_dump() for d in data.dreams]
    for _ in range(10):
        doc = await store.find_one({'uid': u['id']}, {'_id': 0, 'dreams': 1, 'rev': 1}) or {}
        rev = doc.get('rev')
        dreams = merge(doc.get('dreams', []), data.base, mine)
        try:
            res = await store.update_one({'uid': u['id'], 'rev': rev}, {'$set': {'dreams': dreams, 'rev': (rev or 0) + 1, 'ts': now()}}, upsert=True)
        except DuplicateKeyError:
            continue
        if res.matched_count or res.upserted_id is not None:
            return {'dreams': dreams}
    raise HTTPException(503, 'Abhi bahut badlav ek saath aa rahe hain. Thodi der mein phir try karo.')


@router.post('/cheered')
async def cheered(data: CheeredIn, u=Depends(current)):
    change = {'$addToSet': {'cheered': {'$each': list(dict.fromkeys(data.ids))}}, '$set': {'ts': now()}}
    try:
        await store.update_one({'uid': u['id']}, change, upsert=True)
    except DuplicateKeyError:
        await store.update_one({'uid': u['id']}, change)
    return {'ok': True}


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
