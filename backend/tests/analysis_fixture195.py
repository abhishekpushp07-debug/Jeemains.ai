"""TEST-ONLY iteration 195 fixture: one 30-question paper and a class of 14 students with time records, in the isolated disposable DB.
The hero's paper is scripted so that every Attempt Quality tag, an answer change each way, revisits and marks all appear."""
import asyncio, random, uuid
import book_publishing_iso170 as T  # noqa: F401  (imports the harness first)
from book_publishing_iso170 import H, client
from structure_iso173 import mkset, RULES
from tejas import structure

DB = H.TDB
CHAPTERS = {'Physics': ['Kinematics', 'Laws of Motion', 'Electrostatics'], 'Chemistry': ['Mole Concept', 'Chemical Bonding', 'Thermodynamics'],
            'Mathematics': ['Quadratic Equations', 'Matrices', 'Integration']}
# (question number, seconds on screen, 'OK' right answer | 'NO' wrong answer | None no answer, mark for review)
HERO = [(1, 60, 'OK', None), (2, 200, 'OK', None), (3, 20, 'NO', None), (4, 100, 'NO', None), (5, 260, 'NO', None), (6, 120, None, True), (7, 10, None, None),
        (9, 100, 'OK', None), (10, 30, 'NO', None), (11, 50, 'NO', None), (12, 40, 'OK', None), (13, 70, 'OK', True), (14, 60, 'OK', None), (15, 75, 'OK', None),
        (16, 80, 'OK', None), (17, 90, 'OK', None), (18, 65, 'OK', None), (19, 120, 'OK', None), (21, 20, None, None), (22, 70, 'OK', None), (23, 70, 'OK', None),
        (24, 70, 'OK', None), (25, 70, 'OK', None), (26, 60, 'NO', None), (27, 15, None, None), (28, 300, 'NO', None), (29, 150, 'OK', None),
        (11, 30, 'OK', None), (12, 30, 'NO', None), (21, 60, 'OK', None)]
HERO_TAGS = {1: 'perfect', 2: 'slow_correct', 3: 'wasted', 4: 'concept_gap', 5: 'costly_overtime', 6: 'confused', 7: 'smart_skip', 8: 'not_seen', 9: 'perfect',
             10: 'wasted', 11: 'perfect', 12: 'concept_gap', 20: 'not_seen', 21: 'perfect', 26: 'concept_gap', 27: 'smart_skip', 28: 'costly_overtime', 29: 'perfect', 30: 'not_seen'}


def paper():
    out, n = [], 0
    for subject, topics in CHAPTERS.items():
        for i in range(10):
            n += 1
            kind = 'integer' if i >= 8 else 'mcq'
            out.append({'id': str(uuid.uuid4()), 'number': n, 'type': kind, 'subject': subject, 'section': 'B' if kind == 'integer' else 'A',
                        'options': {} if kind == 'integer' else {'A': 'a', 'B': 'b', 'C': 'c', 'D': 'd'}, 'answer': '5' if kind == 'integer' else 'ABCD'[n % 4],
                        'text': f'TEST {subject} question {i + 1}', 'solution': f'TEST solution {n}', 'topic': topics[i * 3 // 10],
                        'difficulty': ['Easy', 'Moderate', 'Hard'][n % 3] if n <= 15 else ''})
    return out


def random_steps(seed, count=30):
    rnd = random.Random(seed)
    skill, speed, steps, total = 0.35 + 0.045 * seed, rnd.uniform(0.6, 1.3), [], 0
    for number in range(1, count + 1):
        if rnd.random() < 0.08:
            continue
        secs = round(rnd.uniform(25, 150) * speed)
        if total + secs > 2700:
            break
        total += secs
        act = None if rnd.random() < 0.12 else 'OK' if rnd.random() < skill else 'NO'
        steps.append((number, secs, act, True if rnd.random() < 0.1 else None))
    return steps


async def student():
    c = client()
    r = await c.post('/api/auth/phone/signup', json={'phone': '95' + str(uuid.uuid4().int)[:8], 'pin': '8261', 'confirm_pin': '8261'})
    assert r.status_code == 200, r.text
    return c


async def sit(c, sid, questions, steps, timed=True, back=3000):
    """Start the paper, move its clock back, answer by the script, send the time record once (twice to prove it is taken once), submit."""
    await c.post(f'/api/sets/{sid}/preflight', json={})
    r = await c.post(f'/api/sets/{sid}/start', json={'start_key': 'k195-' + uuid.uuid4().hex[:12], 'device_checked': True})
    assert r.status_code == 200, r.text
    aid = r.json()['id']
    doc = await DB.tejas_attempts.find_one({'id': aid})
    shift = {k: doc[k] - back for k in ('started_at', 'deadline', 'ready_until') if doc.get(k)}
    await DB.tejas_attempts.update_one({'id': aid}, {'$set': shift})
    start = shift.get('ready_until') or shift['started_at']
    by = {q['number']: q for q in questions}
    t, events, rev, stamps, firsts, marked = start + 5, [], {}, {}, {}, {}
    put = lambda **e: events.append({'n': len(events) + 1, **e})
    for number, secs, act, mark in steps:
        q = by[number]
        qid = q['id']
        put(k='v', q=qid, a=round(t, 1), b=round(t + secs, 1))
        if mark is not None:
            marked[qid] = mark
            put(k='m', q=qid, a=round(t + 1.0, 1), v='1' if mark else '0')
        if act is not None:
            wrong = '7' if q['type'] == 'integer' else 'ABCD'[('ABCD'.index(q['answer']) + 1) % 4]
            value = q['answer'] if act == 'OK' else wrong
            rev[qid] = rev.get(qid, 0) + 1
            r = await c.put(f'/api/attempts/{aid}/answers/{qid}', json={'value': value, 'marked': bool(marked.get(qid)), 'revision': rev[qid], 'request_id': str(uuid.uuid4())})
            assert r.status_code == 200, r.text
            put(k='a', q=qid, a=round(t + secs - 1.0, 1), v=value)
            stamps[qid] = t + secs - 1
            firsts.setdefault(qid, t + secs - 1)
        t += secs + 1
    assert t - start < back - 5, 'script longer than the paper'
    stored = {}
    if timed and events:
        batch = {'sid': 'dev-' + uuid.uuid4().hex[:10], 'events': events}
        one = await c.post(f'/api/attempts/{aid}/timeline', json=batch)
        two = await c.post(f'/api/attempts/{aid}/timeline', json=batch)
        tl = await DB.tejas_attempt_timeline.find_one({'_id': aid})
        stored = {'first': one.status_code, 'again': two.status_code, 'cursor': one.json().get('cursor'), 'cursor_again': two.json().get('cursor'),
                  'count': tl['count'], 'sent': len(events)}
    change = {}
    for qid, at in stamps.items():
        change[f'answers.{qid}.accepted_at'] = at
        change[f'first_answers.{qid}.accepted_at'] = firsts[qid]
    if change:
        await DB.tejas_attempts.update_one({'id': aid}, {'$set': change})
    r = await c.post(f'/api/attempts/{aid}/submit')
    assert r.status_code in (200, 202), r.text
    for _ in range(40):
        if ((await c.get(f'/api/attempts/{aid}/results')).json() or {}).get('summary'):
            break
        await asyncio.sleep(0.25)
    return aid, stored


async def analysis(c, aid, query='', tries=20):
    for _ in range(tries):
        r = await c.get(f'/api/attempts/{aid}/analysis' + query)
        d = r.json() if r.status_code == 200 else None
        if not d or d['class']['state'] != 'preparing':
            return r, d
        await asyncio.sleep(0.5)
    return r, d


async def build(others=12):
    await H.tdbmod.indexes()
    await structure.seed()
    await structure.exams.update_one({'_id': 'jee-main'}, {'$set': {'shown': True}})
    questions = paper()
    sid = await mkset('AN195', exam='JEE Main', catalog_section_id='jee-main:mocks', test_kind='mock', title='TEST_JEE Main Full Mock 7',
                      questions=questions, rules={**RULES, 'minutes': 60})
    await asyncio.sleep(1)
    await structure.visibility(force=True)
    f = {'set': sid, 'questions': questions, 'class': []}
    for seed in range(1, others + 1):
        c = await student()
        aid, _ = await sit(c, sid, questions, random_steps(seed))
        f['class'].append((c, aid))
    old = await student()
    f['old'] = (old, (await sit(old, sid, questions, random_steps(99), timed=False))[0])
    f['hero'] = await student()
    f['hero_attempt'], f['hero_timeline'] = await sit(f['hero'], sid, questions, HERO)
    return f
