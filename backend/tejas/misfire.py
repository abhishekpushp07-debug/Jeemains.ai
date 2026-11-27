"""Misfire: every question a student got wrong or left, from all their papers, in one revision list, and the chapter report
across papers. Built from graded attempts a few at a time (newest first) when the student opens it, so grading is untouched."""
from fractions import Fraction
from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo import UpdateOne
from tejas_core import score_attempt, without_source
from .auth import current
from .db import db, attempts, sets, now
from .live_window import answers_sealed
from .scoring import canonical

router = APIRouter(prefix='/api/my', tags=['Misfire'])
misfires, chapter_rows, synced = db.tejas_misfires, db.tejas_chapter_stats, db.tejas_misfire_sync
BATCH, PAGE = 12, 20
OUTCOME = {'correct': 'correct', 'incorrect': 'wrong', 'skipped': 'skipped'}


def lost_marks(q, rules):
    s = q.get('scoring') or rules
    pos, neg = Fraction(str(s['correct'])), abs(Fraction(str(s['wrong'])))
    return float(pos + neg if q['outcome'] == 'incorrect' else pos)


def entry(a, q, subject, chapter, delivered):
    shown = delivered(q)
    return {'user_id': a['user_id'], 'attempt_id': a['id'], 'question_id': q['id'], 'set_id': a['set_id'], 'title': a['title'], 'exam': a.get('exam'),
            'subject': subject, 'chapter': chapter, 'number': q.get('number'), 'outcome': q['outcome'], 'lost': lost_marks(q, a['rules']),
            'your_answer': str(q.get('response') or ''), 'type': q['type'], 'accepted': [str(x) for x in (q.get('accepted_answers') or [q.get('answer')]) if x is not None],
            'question': shown, 'solution_count': len(q.get('s_refs', [])), 'solution_text': '' if q.get('render_mode') == 'source' else str(q.get('solution') or '')[:4000],
            'at': a.get('submitted_at') or now(), 'status': 'open', 'tries': 0, 'created_at': now()}


async def take(a, delivered):
    """One graded paper into the notebook and the chapter rows. A live paper still in its window waits for its release."""
    if not a.get('ledger') or answers_sealed(a, a.get('_database_now', now())):
        return False
    head = await sets.find_one({'id': a['set_id']}, {'_id': 0, 'test_kind': 1, 'chapter_title': 1}) or {}
    default = head.get('chapter_title') or '' if head.get('test_kind') == 'chapter' else ''
    groups, ops = {}, []
    for q in score_attempt(a)['questions']:
        if q.get('disposition') == 'dropped' or q.get('outcome') not in OUTCOME:
            continue
        subject, chapter = q.get('subject') or 'General', q.get('topic') or default
        g = groups.setdefault((subject, chapter), {'subject': subject, 'chapter': chapter, 'total': 0, 'correct': 0, 'wrong': 0, 'skipped': 0, 'lost': 0.0})
        g['total'] += 1
        g[OUTCOME[q['outcome']]] += 1
        if q['outcome'] != 'correct':
            g['lost'] += lost_marks(q, a['rules'])
            ops.append(UpdateOne({'_id': f"{a['id']}:{q['id']}"}, {'$setOnInsert': entry(a, q, subject, chapter, delivered)}, upsert=True))
    if ops:
        await misfires.bulk_write(ops, ordered=False)
    await chapter_rows.update_one({'_id': a['id']}, {'$set': {'user_id': a['user_id'], 'at': a.get('submitted_at') or now(), 'title': a['title'], 'rows': list(groups.values())}}, upsert=True)
    return True


async def sync(u):
    """Takes in up to BATCH new graded papers; returns how many are still waiting."""
    from .attempts import owned, delivered
    from .canonical import database_now
    recent = await attempts.find({'user_id': u['id'], 'status': 'completed', 'mode': {'$nin': ['preview', 'retry']}, 'set_deleted': {'$ne': True}},
                                 {'_id': 0, 'id': 1, 'series_id': 1, 'competition_end': 1}).sort('submitted_at', -1).limit(300).to_list(300)
    ids = [r['id'] for r in recent]
    done = {r['_id'] for r in await synced.find({'_id': {'$in': ids}}, {'_id': 1}).to_list(len(ids))}
    t = await database_now()
    # A live paper still inside its window is passed over (cheaply) until its answers are released.
    todo = [r['id'] for r in recent if r['id'] not in done and not answers_sealed(r, t)]
    # Only graded papers (a ledger here or on the paper): ungraded or failed ones never take a slot or count as waiting.
    graded = {x['id'] for x in await db.tejas_ledgers.find({'id': {'$in': todo}}, {'_id': 0, 'id': 1}).to_list(len(todo))}
    graded |= {x['id'] for x in await attempts.find({'id': {'$in': todo}, 'ledger': {'$exists': True}}, {'_id': 0, 'id': 1}).to_list(len(todo))}
    todo = [i for i in todo if i in graded]
    took = pending = 0
    # Papers still being graded return False and are passed over, so they never hold up newer papers.
    for aid in todo[:BATCH * 3]:
        if took >= BATCH:
            break
        try:
            taken = await take(await owned(aid, u), delivered)
        except (HTTPException, ValueError):  # gone or unreadable for good: never retried on every visit
            taken = True
        except Exception:  # noqa: BLE001  a passing database hiccup: tried again on the next visit
            taken = False
        if taken:
            took += 1
            await synced.update_one({'_id': aid}, {'$set': {'user_id': u['id'], 'at': now()}}, upsert=True)
        else:
            pending += 1
    return max(0, len(todo) - took - pending)


def view(m):
    out = {k: m.get(k) for k in ('attempt_id', 'question_id', 'title', 'exam', 'subject', 'chapter', 'number', 'outcome', 'lost', 'your_answer', 'type',
                                 'question', 'solution_count', 'status', 'tries', 'last_correct', 'at')}
    out['id'] = m['_id']
    shown = out.get('question') or {}
    if shown.get('render_mode') == 'source' and shown.get('accessible_text'):  # rows kept before the 'Source' line was hidden
        out['question'] = {**shown, 'accessible_text': without_source(shown['accessible_text'])}
    if m.get('tries'):
        out.update(answer=', '.join(m['accepted']), solution_text=m.get('solution_text', ''))
    return out


@router.get('/misfire/summary')
async def summary(u=Depends(current)):
    waiting = await sync(u)
    rows = await misfires.aggregate([{'$match': {'user_id': u['id']}}, {'$group': {'_id': {'s': '$subject', 'st': '$status'}, 'n': {'$sum': 1}}}]).to_list(200)
    subjects = {}
    for r in rows:
        subjects.setdefault(r['_id']['s'], {'name': r['_id']['s'], 'open': 0, 'fixed': 0})[r['_id']['st']] += r['n']
    items = sorted(subjects.values(), key=lambda s: -s['open'])
    return {'open': sum(s['open'] for s in items), 'fixed': sum(s['fixed'] for s in items), 'subjects': items, 'waiting': waiting}


@router.get('/misfire')
async def listing(status: str = Query('open', pattern='^(open|fixed)$'), subject: str = Query('', max_length=80), chapter: str = Query('', max_length=200),
                  page: int = Query(1, ge=1, le=500), u=Depends(current)):
    waiting = await sync(u)
    where = {'user_id': u['id'], 'status': status, **({'subject': subject} if subject else {}), **({'chapter': chapter} if chapter else {})}
    total = await misfires.count_documents(where)
    rows = await misfires.find(where).sort([('at', -1), ('number', 1)]).skip((page - 1) * PAGE).limit(PAGE).to_list(PAGE)
    chapters = await misfires.aggregate([{'$match': {'user_id': u['id'], 'status': status, **({'subject': subject} if subject else {})}},
                                         {'$group': {'_id': '$chapter', 'n': {'$sum': 1}}}, {'$sort': {'n': -1}}, {'$limit': 60}]).to_list(60)
    return {'items': [view(m) for m in rows], 'total': total, 'page': page, 'pages': max(1, -(-total // PAGE)), 'waiting': waiting,
            'chapters': [{'name': c['_id'], 'count': c['n']} for c in chapters if c['_id']]}


async def mine(mid, u):
    m = await misfires.find_one({'_id': mid, 'user_id': u['id']})
    if not m:
        raise HTTPException(404, 'Yeh sawaal aapki Misfire list mein nahi hai.')
    return m


@router.post('/misfire/{mid}/try')
async def try_answer(mid: str, body: dict, u=Depends(current)):
    m = await mine(mid, u)
    try:
        got = canonical(body.get('value', ''), m['type'])
        keys = {canonical(v, m['type']) for v in m['accepted']}
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if not got:
        raise HTTPException(422, 'Pehle apna jawab chuniye.')
    right = got in keys
    m = await misfires.find_one_and_update({'_id': mid, 'user_id': u['id']}, {'$inc': {'tries': 1}, '$set': {'last_correct': right, 'last_value': got, 'last_try_at': now()}},
                                           return_document=True)
    return {'correct': right, 'item': view(m)}


@router.post('/misfire/{mid}/done')
async def done(mid: str, u=Depends(current)):
    m = await mine(mid, u)
    if not m.get('last_correct'):
        raise HTTPException(409, 'Pehle sahi jawab dijiye, phir "Samajh gaya" dabaiye.')
    await misfires.update_one({'_id': mid}, {'$set': {'status': 'fixed', 'fixed_at': now()}})
    return {'id': mid, 'status': 'fixed'}


@router.post('/misfire/{mid}/reopen')
async def reopen(mid: str, u=Depends(current)):
    await mine(mid, u)
    await misfires.update_one({'_id': mid}, {'$set': {'status': 'open', 'last_correct': False, 'tries': 0}, '$unset': {'fixed_at': '', 'last_value': ''}})
    return {'id': mid, 'status': 'open'}


def trend(history):
    """Sahi share in the latest papers (up to 3) against the papers before them."""
    if len(history) < 2:
        return None
    k = min(3, len(history) // 2)
    delta = sum(history[-k:]) / k - sum(history[:-k]) / (len(history) - k)
    return 'up' if delta >= .05 else 'down' if delta <= -.05 else 'same'


def close(g):
    h = g.pop('history')
    attempted = g['correct'] + g['wrong']
    return {**g, 'lost': round(g['lost'], 2), 'sahi': round(100 * g['correct'] / g['total']) if g['total'] else 0,
            'accuracy': round(100 * g['correct'] / attempted) if attempted else None, 'trend': trend(h)}


FIELDS = ('total', 'correct', 'wrong', 'skipped', 'lost')


def fold(store, key, part):
    """Adds one paper's totals for a chapter (or a subject) and remembers that paper's sahi share for the trend."""
    g = store.setdefault(key, {'subject': part['subject'], 'chapter': part['chapter'], 'papers': 0, 'history': [], **{f: 0 for f in FIELDS}})
    for f in FIELDS:
        g[f] += part[f]
    g['papers'] += 1
    g['history'].append(part['correct'] / part['total'] if part['total'] else 0)


@router.get('/chapters')
async def chapters(u=Depends(current)):
    waiting = await sync(u)
    papers = await chapter_rows.find({'user_id': u['id']}, {'_id': 0, 'at': 1, 'rows': 1}).sort('at', 1).to_list(1000)
    by, subjects = {}, {}
    for p in papers:
        per_subject = {}
        for r in p['rows']:
            fold(by, (r['subject'], r['chapter']), r)
            s = per_subject.setdefault(r['subject'], {'subject': r['subject'], 'chapter': '', **{f: 0 for f in FIELDS}})
            for f in FIELDS:
                s[f] += r[f]
        for name, s in per_subject.items():
            fold(subjects, name, s)
    rows = sorted((close(g) for k, g in by.items() if k[1]), key=lambda g: -g['lost'])
    return {'papers': len(papers), 'waiting': waiting, 'chapters': rows,
            'subjects': sorted((close(g) for g in subjects.values()), key=lambda g: -g['lost']), 'untagged': sum(g['total'] for k, g in by.items() if not k[1])}
