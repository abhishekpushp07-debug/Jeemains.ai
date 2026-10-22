"""Private, original-score practice journeys. No national-rank inference or AI calls."""
import hashlib
import json
from collections import Counter
from fastapi import APIRouter, Depends, HTTPException
from .auth import current
from .attempts import owned
from .db import attempts, now
from .packs import hydrate

router = APIRouter(prefix='/api/attempts', tags=['Personal mock progress'])
EXAM_COUNTS = {'JEE Main': (75, 0), 'BITSAT': (130, 12), 'COMEDK': (180, 0)}


def family(a):
    if a.get('mode') != 'practice' or a.get('parent_attempt') or a.get('test_kind') != 'mock' or a.get('competition_end'):
        return None
    rules = a.get('rules') or {}
    if not rules.get('minutes'):
        return None
    questions = a.get('questions') or []
    actual = (sum(not q.get('bonus') for q in questions), sum(bool(q.get('bonus')) for q in questions))
    if EXAM_COUNTS.get(a.get('exam')) != actual:
        return None
    shape = Counter()
    for q in questions:
        if q.get('disposition', 'standard') != 'standard':
            return None
        scoring = q.get('scoring') or rules
        shape[json.dumps([q.get('section') or q.get('subject'), q.get('type'), bool(q.get('bonus')),
                          [float(scoring[k]) if scoring.get(k) is not None else None for k in ('correct', 'wrong', 'skipped')]], sort_keys=True)] += 1
    bonus = {k: v for k, v in (rules.get('bonus_rule') or {}).items() if k not in ('message', 'warning', 'notice', 'description', 'note')} if actual[1] else None
    spec = {'exam': a['exam'], 'minutes': float(rules['minutes']), 'shape': sorted(shape.items()),
            'navigation': rules.get('navigation'), 'numeric_policy': rules.get('numeric_policy'),
            'bonus_rule': bonus}
    return hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()


def paper_basis(a):
    spec = {k: a.get(k) for k in ('set_id', 'version', 'pack_id', 'key_version', 'rules', 'mode')}
    if not a.get('pack_id'):
        spec['questions'] = [{k: q.get(k) for k in ('id', 'type', 'text', 'options', 'answer', 'q_refs', 'scoring', 'disposition')}
                             for q in a.get('questions', [])]
    return hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()


async def released(id, u):
    a = await owned(id, u)
    if a.get('status') != 'completed':
        raise HTTPException(409, 'Complete this attempt before viewing its progress.')
    if a.get('competition_end', 0) > now():
        raise HTTPException(403, 'Results remain sealed until release.')
    if not a.get('summary'):
        raise HTTPException(409, 'The original score is still being prepared.')
    return a


def point(a):
    s = a['summary']
    tried = s.get('attempted', 0)
    return {'id': a['id'], 'title': a['title'], 'set_id': a['set_id'], 'version': a.get('version'),
            'submitted_at': a['submitted_at'], 'score': s['score'], 'maximum': s['maximum'],
            'accuracy': round(100*s.get('correct', 0)/tried, 1) if tried else None,
            'correct': s.get('correct', 0), 'attempted': tried, 'skipped': s.get('skipped', 0),
            'seconds': s.get('total_seconds'), 'subjects': s.get('subjects', {})}


@router.get('/{id}/journey')
async def journey(id: str, score_version: str = 'original', u=Depends(current)):
    a = await released(id, u)
    key = family(a)
    if score_version != 'original' or not key:
        return {'state': 'unavailable', 'reason': 'Journey uses completed, timed, original-score full mocks with compatible section counts, marking and bonus rules. Chapter tests, retries, corrections and competitions stay separate.', 'series': []}
    match = {'user_id': u['id'], 'exam': a['exam'], 'mode': 'practice', 'status': 'completed',
             'summary': {'$ne': None}, 'test_kind': 'mock', 'rules.minutes': a['rules']['minutes'],
             '$and': [{'$or': [{'progress_family': key}, {'progress_family': {'$exists': False}}]},
                      {'$or': [{'submitted_at': {'$lt': a['submitted_at']}}, {'submitted_at': a['submitted_at'], 'id': {'$lte': a['id']}}]}]}
    fields = {'_id': 0, 'answers': 0, 'command_receipts': 0, 'response_schema': 0, 'first_answers': 0}
    recent, scanned, limited = [], 0, False
    async for candidate in attempts.find(match, fields).sort([('submitted_at', -1), ('id', -1)]).limit(501):
        scanned += 1
        if scanned > 500:
            limited = True
            break
        if candidate.get('progress_family') == key or family(await hydrate(candidate)) == key:
            recent.append(point(candidate))
            if len(recent) > 250:
                recent.pop()
                limited = True
                break
    if not recent:
        return {'state': 'unavailable', 'reason': 'No compatible scored full mocks are available yet.', 'series': []}
    baseline = None
    async for candidate in attempts.find(match, fields).sort([('submitted_at', 1), ('id', 1)]).limit(500):
        if candidate.get('progress_family') == key or family(await hydrate(candidate)) == key:
            baseline = point(candidate)
            break
    latest = recent[0]
    last5 = recent[:5]
    attempted = sum(x['attempted'] for x in last5)
    correct = sum(x['correct'] for x in last5)
    series = list(reversed(recent))
    if baseline and baseline['id'] not in {p['id'] for p in series}:
        series.insert(0, baseline)
    delta = None if not baseline else {'score': round(latest['score']-baseline['score'], 2),
        'accuracy': round(latest['accuracy']-baseline['accuracy'], 1) if latest['accuracy'] is not None and baseline['accuracy'] is not None else None}
    return {'state': 'available', 'family': key, 'exam': a['exam'], 'as_of': a['submitted_at'], 'latest': latest,
            'first': baseline, 'delta': delta, 'series': series, 'limited': limited,
            'confidence': {'accuracy': round(100*correct/attempted, 1) if attempted else None, 'correct': correct,
                           'attempted': attempted, 'window_size': len(last5), 'attempt_ids': [x['id'] for x in last5]},
            'basis': 'Original scores up to this attempt. Same exam, duration, full-paper sections, marking and bonus rules. Retakes included.',
            'limitation': 'Different papers can differ in difficulty; repeated exposure can improve scores. This is descriptive progress, not an equal-difficulty ability measure or a psychological confidence assessment.',
            'coverage': 'Latest 250 matching mocks plus earliest reconciled baseline; scan capped at 500 candidates per direction.' if limited else 'All matching attempts up to this result within the bounded history scan.'}
