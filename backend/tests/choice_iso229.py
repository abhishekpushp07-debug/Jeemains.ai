"""TEST-ONLY iteration 229: Student Choice (JEE Main) doors A/B/C, owner settings, the made paper's start/grade/results,
and every exclusion (rank, class, Dream, compare), on a throw-away isolated DB (dropped at the end). Storage and AI mocked.
Run: cd /app/backend && bash tests/runners/solo.sh python -u tests/choice_iso229.py
"""
import asyncio, json, sys, time, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import iso_harness_book170 as H  # noqa: E402  (must import first: rebinds DB + mocks storage/AI)
import bcrypt, fitz, httpx  # noqa: E402
from tejas import jobs as J, choice, structure, dreams  # noqa: E402
from tejas.packs import hydrate  # noqa: E402
import tejas_storage  # noqa: E402

_oj = httpx.Response.json
httpx.Response.json = lambda self: (lambda d: d['data'] if isinstance(d, dict) and 'meta' in d and 'data' in d else d)(_oj(self))
BASE = [l.split('=', 1)[1].strip() for l in open('/app/frontend/.env') if l.startswith('REACT_APP_BACKEND_URL')][0].rstrip('/')
RESULTS = []
T = H.TDB


def check(name, ok, detail=''):
    RESULTS.append((name, bool(ok), str(detail)[:400]))
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:400]), flush=True)


def client(origin=True):
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=H.app), base_url=BASE, timeout=120, headers={'Origin': BASE} if origin else {})


def err(r):
    try:
        return (_oj(r).get('error') or {}).get('message')
    except Exception:  # noqa: BLE001
        return r.text[:200]


RULES = {'minutes': 60, 'correct': 4, 'wrong': -1, 'skipped': 0, 'numeric_rule': '', 'navigation': 'free', 'numeric_policy': 'integer_exact',
         'solution_release': 'after_submit'}


def qset(sid, subject, number, mcq, integer, exam='JEE Main', **extra):
    qs = []
    for i in range(mcq + integer):
        kind = 'mcq' if i < mcq else 'integer'
        qs.append({'id': f'{sid}-q{i + 1}', 'number': i + 1, 'type': kind, 'subject': subject, 'section': f'{subject} Section {"A" if kind == "mcq" else "B"}',
                   'topic': f'TEST {subject} chapter {number}', 'text': f'TEST {subject} {number} question {i + 1}: what is {i}+1?',
                   'options': {'A': '1', 'B': '2', 'C': '3', 'D': '4'} if kind == 'mcq' else {}, 'answer': 'B' if kind == 'mcq' else '5',
                   'solution': 'TEST_SECRET_SOLUTION', 'difficulty': 'moderate', 'scoring': {'correct': 9, 'wrong': -9}})
    t = time.time()
    return {'id': sid, 'title': f'{number:02d} TEST {subject} chapter {number}', 'exam': exam, 'year': '', 'status': 'published', 'audience': 'all',
            'rules': RULES, 'version': 1, 'revision': 1, 'test_kind': 'chapter', 'chapter_book_id': 'TEST_book229', 'chapter_subject': subject,
            'chapter_number': number, 'live_enabled': True, 'start_at': t - 3600, 'end_at': t + 30 * 86400, 'rights_report': True,
            'attribution': '', 'source': 'TEST', 'created_at': t, 'questions': qs, **extra}


async def seed():
    await structure.seed()
    rows = [qset('TEST_P1', 'Physics', 1, 40, 10), qset('TEST_P2', 'Physics', 2, 12, 4), qset('TEST_C1', 'Chemistry', 1, 20, 5),
            qset('TEST_C2', 'Chemistry', 2, 10, 3), qset('TEST_M1', 'Mathematics', 1, 26, 6), qset('TEST_M2', 'Mathematics', 2, 8, 2),
            qset('TEST_P9', 'Physics', 9, 5, 1, archived=True), qset('TEST_P8', 'Physics', 8, 5, 1, live_enabled=False),
            qset('TEST_B1', 'Physics', 1, 5, 1, exam='BITSAT'), qset('TEST_PL', 'Physics', 7, 60, 0, start_at=time.time() + 86400)]
    p1 = rows[0]['questions']
    p1[3]['disposition'] = 'dropped'
    p1[4]['bonus'] = True
    # one old-look picture chapter: MCQ words up to '(A)', a numerical's whole crop, an MCQ with no '(A)' marker left out
    doc = fitz.open(); page = doc.new_page(width=400, height=400)
    page.insert_text((40, 60), 'Q1. Find the force. (A) 1 N (B) 2 N', fontsize=11); page.insert_text((40, 200), 'Q2. Integer: value of g?', fontsize=11)
    raw = doc.tobytes(); doc.close()
    import hashlib
    ref = tejas_storage.put_object('TEST/choice229/source.pdf', raw)
    await T.tejas_files.insert_one({'id': 'TEST_file229', 'path': ref, 'sha256': hashlib.sha256(raw).hexdigest(), 'filename': 'TEST.pdf', 'size': len(raw)})
    old = qset('TEST_PO', 'Physics', 3, 2, 1)
    q_ref = lambda y: {'file_id': 'TEST_file229', 'page': 1, 'rect': [30, y, 380, y + 40]}  # noqa: E731
    old['questions'][0].update(render_mode='source', text='Q1.\nSingle correct\nFind the force on the block.\n(A) 1 N (B) 2 N', q_refs=[q_ref(40)])
    old['questions'][1].update(render_mode='source', text='Q2.\nSingle correct\nNo option marker here', q_refs=[q_ref(100)])
    old['questions'][2].update(render_mode='source', text='Q3.\nInteger response\nValue of g?', q_refs=[q_ref(180)])
    rows.append(old)
    await T.tejas_sets.insert_many(rows)


async def staff(role):
    email, pw = f'qa229-{uuid.uuid4().hex[:6]}@example.com', 'Qa229!' + uuid.uuid4().hex[:10]
    await T.tejas_users.insert_one({'id': str(uuid.uuid4()), 'name': 'QA229 ' + role, 'email': email, 'role': role, 'credential_generation': 0,
                                    'password_hash': bcrypt.hashpw(pw.encode(), bcrypt.gensalt(4)).decode(), 'created_at': time.time()})
    c = client(); r = await c.post('/api/auth/login', json={'email': email, 'password': pw})
    assert r.status_code == 200, r.text
    return c


async def student(phone):
    c = client()
    r = await c.post('/api/auth/phone/signup', json={'phone': phone, 'pin': '8261', 'confirm_pin': '8261'})
    assert r.status_code == 200, r.text
    return c


async def drain(limit=60):
    for _ in range(limit):
        j = await T.tejas_jobs.find_one({'status': 'queued'}, sort=[('created_at', 1)])
        if not j:
            return
        await J.run_job(j['id'])


async def results(c, aid):
    for _ in range(30):
        r = await c.get(f'/api/attempts/{aid}/results')
        if r.status_code == 200 and r.json().get('ledger_summary', r.json().get('summary')) and r.json().get('status') == 'completed':
            return r
        await drain(); await asyncio.sleep(0.2)
    return r


def save(c, aid, qid, value):
    return c.put(f'/api/attempts/{aid}/answers/{qid}', json={'value': value, 'revision': 1, 'request_id': 'TEST' + uuid.uuid4().hex})


async def main():
    assert not H.leftover_real_handles()
    choice.reset()
    await seed()
    sets_before = await T.tejas_sets.count_documents({})
    owner, riya, arjun = await staff('owner'), await student('9811122901'), await student('9811122902')
    anon = client()

    # ---------------- both Off: today's behaviour
    r = await riya.get('/api/choice/bank', params={'exam': 'jee-main'})
    check('A: both Off -> 404', r.status_code == 404, r.text)
    check('A: no session -> 401', (await anon.get('/api/choice/bank', params={'exam': 'jee-main'})).status_code == 401)
    check('A: unsupported exam -> 404', (await riya.get('/api/choice/bank', params={'exam': 'bitsat'})).status_code == 404)
    check('B: both Off -> 404', (await riya.get('/api/choice/chapters/TEST_P1/questions')).status_code == 404)
    r = await riya.post('/api/choice/papers', json={'exam': 'jee-main', 'request_key': str(uuid.uuid4()), 'mode': 'random', 'count': 10})
    check('C: both Off -> 409 closed sentence', r.status_code == 409 and err(r) == choice.CLOSED, r.text)

    # ---------------- owner settings
    check('owner view: student refused', (await riya.get('/api/admin/choice/jee-main')).status_code == 403)
    r = await owner.get('/api/admin/choice/jee-main')
    v = r.json()
    check('owner view: defaults Off, 75, 5, minutes', r.status_code == 200 and v['settings']['pick'] is False and v['settings']['random'] is False and
          v['settings']['max_questions'] == 75 and v['settings']['daily_limit'] == 5 and v['settings']['minutes'] == choice.MINUTES, v.get('settings'))
    chapters = {c['id']: c for s in v['pool'] for c in s['chapters']}
    check('pool: only live JEE Main chapter tests', set(chapters) == {'TEST_P1', 'TEST_P2', 'TEST_PO', 'TEST_C1', 'TEST_C2', 'TEST_M1', 'TEST_M2'}, sorted(chapters))
    check('pool: dropped and bonus questions left out', chapters['TEST_P1']['count'] == 48, chapters['TEST_P1'])
    check('pool: chapter title without its number', chapters['TEST_P1']['title'] == 'TEST Physics chapter 1', chapters['TEST_P1']['title'])
    body = {'expected_revision': 0, 'pick': True, 'random': True, 'max_questions': 75, 'max_per_subject': None,
            'minutes_per_question': {'Physics': 2.4, 'Chemistry': 1.6, 'Mathematics': 3.2}, 'daily_limit': 5}
    check('owner save: bad minutes 422', (await owner.put('/api/admin/choice/jee-main', json={**body, 'minutes_per_question': {'Physics': 0.1, 'Chemistry': 1.6, 'Mathematics': 3.2}})).status_code == 422)
    r = await owner.put('/api/admin/choice/jee-main', json=body)
    check('owner save: both On', r.status_code == 200 and r.json()['settings']['revision'] == 1, r.text)
    r = await owner.put('/api/admin/choice/jee-main', json=body)
    check('owner save: stale revision 409', r.status_code == 409, r.text)
    check('owner save: student refused', (await riya.put('/api/admin/choice/jee-main', json={**body, 'expected_revision': 1})).status_code == 403)
    check('owner save: audit row', await T.tejas_audits.count_documents({'action': 'Student Choice settings saved'}) == 1)

    # ---------------- door A
    r = await riya.get('/api/choice/bank', params={'exam': 'jee-main'})
    a = r.json()
    check('A: exact contract answer', r.status_code == 200 and a == {'pick': True, 'random': True, 'max_questions': 75, 'max_per_subject': None,
          'minutes_per_question': {'Physics': 2.4, 'Chemistry': 1.6, 'Mathematics': 3.2}}, a)

    # ---------------- door B
    r = await riya.get('/api/choice/chapters/TEST_P1/questions', params={'page': 1})
    b = r.json()
    raw = r.text
    check('B: page 1 of 1, 48 items', r.status_code == 200 and b['pages'] == 1 and len(b['items']) == 48, (r.status_code, b.get('pages'), len(b.get('items', []))))
    check('B: chapter block', b['chapter'] == {'id': 'TEST_P1', 'title': 'TEST Physics chapter 1', 'subject': 'Physics'}, b.get('chapter'))
    check('B: never options/answer/solution', all(k not in raw for k in ('"options"', '"answer"', 'TEST_SECRET_SOLUTION', '"solution"')), raw[:300])
    item = b['items'][0]
    check('B: item shape', set(item) == {'id', 'number', 'type', 'text', 'stem'} and item['type'] == 'mcq' and item['number'] == 1 and
          choice.ID.fullmatch(item['id']), item)
    check('B: ids stable over two reads', [x['id'] for x in (await riya.get('/api/choice/chapters/TEST_P1/questions')).json()['items']] == [x['id'] for x in b['items']])
    check('B: page beyond end 404', (await riya.get('/api/choice/chapters/TEST_P1/questions', params={'page': 2})).status_code == 404)
    for bad in ('TEST_P9', 'TEST_P8', 'TEST_B1', 'TEST_PL', 'nope12345'):
        check(f'B: {bad} not choosable -> 404', (await riya.get(f'/api/choice/chapters/{bad}/questions')).status_code == 404)
    r = await riya.get('/api/choice/chapters/TEST_PO/questions')
    po = r.json()['items']
    check('B: old-look MCQ words cut at (A), no picture', po[0]['text'] == 'Find the force on the block.' and po[0]['stem'] == [], po[0])
    check('B: old-look MCQ without (A) left out, numerical whole crop', len(po) == 2 and po[1]['type'] == 'integer' and po[1]['text'] == '' and
          len(po[1]['stem']) == 1 and po[1]['stem'][0]['w'] == 350 and po[1]['stem'][0]['h'] == 40, po)
    url = po[1]['stem'][0]['url']
    check('B: picture link absolute https, <= 900', url.startswith('https://') and ' ' not in url and len(url) <= 900, url)
    bare = httpx.AsyncClient(transport=httpx.ASGITransport(app=H.app), base_url=BASE, timeout=60)
    pr = await bare.get(url.replace(BASE, ''))
    check('B: picture loads with no cookie, public cache', pr.status_code == 200 and pr.headers['content-type'] in ('image/webp', 'image/png') and
          'public' in pr.headers.get('cache-control', '') and len(pr.content) > 200, (pr.status_code, dict(pr.headers)))
    check('B: tampered picture link 404', (await bare.get(url.replace(BASE, '')[:-3] + 'AAA')).status_code == 404)
    r = await riya.get('/api/choice/chapters/TEST_P1/questions')
    check('B: still answered after picture', r.status_code == 200)

    # ---------------- door C, pick
    ids = {s: (await riya.get(f'/api/choice/chapters/{s}/questions')).json()['items'] for s in ('TEST_P1', 'TEST_C1', 'TEST_M1')}
    pick = [ids['TEST_M1'][0]['id'], ids['TEST_P1'][45]['id'], ids['TEST_C1'][0]['id'], ids['TEST_P1'][0]['id'], ids['TEST_P1'][1]['id'],
            ids['TEST_C1'][1]['id'], ids['TEST_M1'][30]['id']]
    key = str(uuid.uuid4())
    nori = client(origin=False)
    nori.cookies = riya.cookies
    r = await nori.post('/api/choice/papers', json={'exam': 'jee-main', 'request_key': key, 'mode': 'pick', 'question_ids': pick})
    check('C: pick 3P+2C+2M -> set_id (no Origin header)', r.status_code in (200, 201) and choice.ID.fullmatch(r.json().get('set_id', '')), r.text)
    sid = r.json()['set_id']
    r2 = await riya.post('/api/choice/papers', json={'exam': 'jee-main', 'request_key': key, 'mode': 'pick', 'question_ids': pick})
    check('C: same request_key -> same paper', r2.json().get('set_id') == sid, r2.text)
    day = await T.tejas_choice_days.find_one({})
    check('C: one quota slot for one key', day and day['count'] == 1, day)
    p = await T.tejas_choice_papers.find_one({'id': sid})
    check('C: 3P+2C+2M = 17 minutes, +4/-1/0, max 28', p['rules']['minutes'] == 17 and p['rules']['correct'] == 4 and p['rules']['wrong'] == -1 and
          p['maximum'] == 28 and p['counts'] == {'Physics': 3, 'Chemistry': 2, 'Mathematics': 2}, p['rules'])
    order = [(i['subject'], i['type']) for i in p['items']]
    check('C: order P, C, M; MCQ before numerical', order == [('Physics', 'mcq'), ('Physics', 'mcq'), ('Physics', 'integer'), ('Chemistry', 'mcq'),
          ('Chemistry', 'mcq'), ('Mathematics', 'mcq'), ('Mathematics', 'integer')], order)
    check('C: not in tejas_sets', await T.tejas_sets.count_documents({}) == sets_before)
    for name, extra, msg in [('76 ids', {'question_ids': [ids['TEST_P1'][0]['id']] * 76}, choice.TOO_MANY.format(n=75)),
                             ('unknown id', {'question_ids': [str(uuid.uuid4())]}, choice.GONE),
                             ('duplicate id', {'question_ids': [pick[0], pick[0]]}, choice.GONE),
                             ('empty', {'question_ids': []}, choice.NONE_PICKED)]:
        r = await riya.post('/api/choice/papers', json={'exam': 'jee-main', 'request_key': str(uuid.uuid4()), 'mode': 'pick', **extra})
        check(f'C: pick {name} -> 422 sentence', r.status_code == 422 and err(r) == msg, (r.status_code, err(r)))

    # ---------------- door C, random
    for n, msg in ((2, choice.RANGE.format(n=75)), (76, choice.RANGE.format(n=75)), (0, choice.RANGE.format(n=75))):
        r = await riya.post('/api/choice/papers', json={'exam': 'jee-main', 'request_key': str(uuid.uuid4()), 'mode': 'random', 'count': n})
        check(f'C: random {n} -> 422 sentence', r.status_code == 422 and err(r) == msg, (r.status_code, err(r)))
    r = await riya.post('/api/choice/papers', json={'exam': 'jee-main', 'request_key': str(uuid.uuid4()), 'mode': 'random', 'count': 10})
    p10 = await T.tejas_choice_papers.find_one({'id': r.json()['set_id']})
    check('C: random 10 = 4+3+3, 24 minutes', p10['counts'] == {'Physics': 4, 'Chemistry': 3, 'Mathematics': 3} and p10['rules']['minutes'] == 24, p10['counts'])
    r = await riya.post('/api/choice/papers', json={'exam': 'jee-main', 'request_key': str(uuid.uuid4()), 'mode': 'random', 'count': 75})
    p75 = await T.tejas_choice_papers.find_one({'id': r.json()['set_id']})
    check('C: random 75 = 25+25+25, 180 minutes, max 300', p75['counts'] == {'Physics': 25, 'Chemistry': 25, 'Mathematics': 25} and
          p75['rules']['minutes'] == 180 and p75['maximum'] == 300, p75['counts'])
    m = sum(1 for i in p75['items'] if i['subject'] == 'Physics' and i['type'] == 'integer')
    check('C: random about 4 MCQ to 1 numerical', m == 5, m)
    check('C: random spreads over chapters', len({i['set_id'] for i in p75['items'] if i['subject'] == 'Physics'}) >= 2)
    check('C: random items unique', len({i['token'] for i in p75['items']}) == 75)
    r = await riya.post('/api/choice/papers', json={'exam': 'jee-main', 'request_key': str(uuid.uuid4()), 'mode': 'random', 'count': 11})
    p11 = await T.tejas_choice_papers.find_one({'id': r.json()['set_id']})
    check('C: random 11 = 4+4+3', p11['counts'] == {'Physics': 4, 'Chemistry': 4, 'Mathematics': 3}, p11['counts'])

    # ---------------- quota: 5 a day
    r = await riya.post('/api/choice/papers', json={'exam': 'jee-main', 'request_key': str(uuid.uuid4()), 'mode': 'random', 'count': 3})
    check('C: 5th paper of the day ok', r.status_code == 200, r.text)
    r = await riya.post('/api/choice/papers', json={'exam': 'jee-main', 'request_key': str(uuid.uuid4()), 'mode': 'random', 'count': 3})
    check('C: 6th paper -> 429 daily sentence', r.status_code == 429 and err(r) == choice.DAILY.format(n=5), (r.status_code, err(r)))
    r = await riya.post('/api/choice/papers', json={'exam': 'jee-main', 'request_key': key, 'mode': 'pick', 'question_ids': pick})
    check('C: an old key still returns its paper after the limit', r.json().get('set_id') == sid, r.text)
    keys = [str(uuid.uuid4()) for _ in range(8)]
    rs = await asyncio.gather(*[arjun.post('/api/choice/papers', json={'exam': 'jee-main', 'request_key': keys[i % 6], 'mode': 'random', 'count': 3}) for i in range(8)])
    made = {x.json().get('set_id') for x in rs if x.status_code == 200}
    check('C: 8 racing requests (6 keys) -> exactly 5 papers, 1 refused key', len(made) == 5 and sum(x.status_code == 429 for x in rs) >= 1 and
          (await T.tejas_choice_days.find_one({'user_id': {'$ne': day['user_id']}}))['count'] == 5, [x.status_code for x in rs])
    r = await (await student('9811122903')).get('/api/choice/home')
    check('website home: own count, chapters', r.status_code == 200 and r.json()['made_today'] == 0 and r.json()['chapters'] == 7, r.text[:200])
    r = await riya.get('/api/choice/home')
    check('website home: riya made 5', r.json()['made_today'] == 5 and r.json()['daily_limit'] == 5)

    # ---------------- the made paper: owner only
    r = await riya.get(f'/api/my/sets/{sid}')
    ms = r.json()
    check('my/sets: owner reads, test_kind choice', r.status_code == 200 and ms['test_kind'] == 'choice' and ms['count'] == 7 and ms['maximum'] == 28 and
          ms['rules']['minutes'] == 17 and ms['exam'] == 'JEE Main', ms)
    check('my/sets: another student 404', (await arjun.get(f'/api/my/sets/{sid}')).status_code == 404)
    check('start: another student 404', (await arjun.post(f'/api/sets/{sid}/start', json={'start_key': 'TEST' + uuid.uuid4().hex})).status_code == 404)
    check('preflight: owner ok', (await riya.post(f'/api/sets/{sid}/preflight', json={'test_response': 'ok'})).status_code == 200)
    r = await nori.post(f'/api/sets/{sid}/start', json={'start_key': 'TEST' + uuid.uuid4().hex})
    st = r.json()
    check('start: owner starts, test_kind choice, 7 questions', r.status_code == 200 and st['test_kind'] == 'choice' and st['count'] == 7, r.text[:300])
    check('start: no answers delivered', 'TEST_SECRET_SOLUTION' not in r.text and '"answer"' not in r.text)
    att = await hydrate(await T.tejas_attempts.find_one({'id': st['id']}, {'_id': 0}))
    qs = att['questions']
    check('frozen copy: subject sections, own ids, numbering 1..7', [q['section'] for q in qs] == ['Physics'] * 3 + ['Chemistry'] * 2 + ['Mathematics'] * 2 and
          [q['number'] for q in qs] == list(range(1, 8)) and [q['id'] for q in qs] == [i['token'] for i in p['items']], [(q['section'], q['number']) for q in qs])
    check('frozen copy: source map + topic kept, per-question scoring dropped', all(q['source_set_id'] and q['source_question_id'] and q['topic'] and
          'scoring' not in q for q in qs), qs[0])
    # answer: 4 right, 1 wrong, 2 skipped
    for q, v in zip(qs, ['B', 'B', '5', 'A', 'B']):
        rr = await save(riya, st['id'], q['id'], v)
        assert rr.status_code == 200, rr.text
    r = await riya.post(f"/api/attempts/{st['id']}/submit")
    check('submit accepted', r.status_code in (200, 202), r.text[:200])
    r = await results(riya, st['id'])
    res = r.json()
    s = res.get('summary') or {}
    check('results: test_kind choice, 4x4 - 1 = 15 / 28', res.get('test_kind', 'choice') == 'choice' and s.get('score') == 15 and s.get('maximum') == 28, s)
    r = await riya.get(f"/api/attempts/{st['id']}/cohort")
    check('cohort: "Is test par Rank nahi banta."', r.status_code == 200 and r.json().get('reason') == 'Is test par Rank nahi banta.', r.text[:200])
    check('class stats: none for choice', await T.tejas_class_entries.count_documents({}) == 0 if 'tejas_class_entries' in await T.list_collection_names() else True)
    check('cohort entries: none for choice', await T.tejas_cohort_entries.count_documents({}) == 0)
    r = await riya.get('/api/my/tests', params={'tab': 'completed'})
    item = next((x for x in r.json()['items'] if x['id'] == st['id']), {})
    check('my tests: test_kind choice, not comparable', item.get('test_kind') == 'choice' and item.get('compare_eligible') is False, item)
    full = await T.tejas_attempts.find_one({'id': st['id']}, {'_id': 0, 'questions': 0})
    check('Dream: never a full mock', not dreams.is_full('jee', {**full, 'count': 75, 'summary': {'maximum': 300}}))
    check('Dream: a long chapter test never counts either', not dreams.is_full('jee', {'test_kind': 'chapter', 'count': 75, 'summary': {'maximum': 300}}))
    check('Dream: a real full mock still counts', dreams.is_full('jee', {'test_kind': 'mock', 'count': 75, 'summary': {'maximum': 300}}))
    check('Dream: website mocks list leaves the choice paper out', all(m.get('id') != st['id'] for m in await dreams.website_mocks(full['user_id'])))
    r = await riya.post(f"/api/attempts/{st['id']}/questions/{qs[3]['id']}/report-wrong", json={'category': 'key', 'context': 'results', 'note': 'TEST'})
    rep = await T.tejas_question_reports.find_one({'attempt_id': st['id']})
    check('report: lands on the source chapter question', r.status_code == 200 and rep and rep['set_id'] == qs[3]['source_set_id'] and
          rep['question_id'] == qs[3]['source_question_id'], (r.status_code, r.text[:200], rep and rep.get('set_id')))
    r = await riya.get(f"/api/attempts/{st['id']}/ai-solutions")
    check('ai solutions read for a choice paper', r.status_code == 200, r.text[:200])

    # ---------------- freeze: a chapter edit never changes a started paper; an un-started one refuses when a source goes
    await T.tejas_sets.update_one({'id': 'TEST_P1'}, {'$set': {'questions.0.text': 'TEST CHANGED'}, '$inc': {'revision': 1}})
    choice.reset()
    r = await riya.post(f'/api/sets/{sid}/start', json={'start_key': 'TEST' + uuid.uuid4().hex})
    again = await hydrate(await T.tejas_attempts.find_one({'id': r.json()['id']}, {'_id': 0}))
    check('second start reuses the frozen copy', r.status_code == 200 and again['id'] != st['id'] and
          [q['text'] for q in again['questions']] == [q['text'] for q in qs], r.text[:200])
    await T.tejas_sets.update_one({'id': 'TEST_C1'}, {'$set': {'live_enabled': False}})
    r = await riya.post(f"/api/sets/{p10['id']}/start", json={'start_key': 'TEST' + uuid.uuid4().hex})
    check('un-started paper with a gone chapter -> 409 sentence (fresh read, no cache reset)', r.status_code == 409 and err(r) == choice.STALE, (r.status_code, err(r)))
    choice.reset()
    r = await riya.post(f"/api/sets/{p10['id']}/preflight", json={})
    check('preflight says the same', r.status_code == 409 and err(r) == choice.STALE, (r.status_code, err(r)))
    await T.tejas_sets.update_one({'id': 'TEST_C1'}, {'$set': {'live_enabled': True}})
    choice.reset()

    # ---------------- switches: pick Off / random Off / both Off
    await owner.put('/api/admin/choice/jee-main', json={**body, 'expected_revision': 1, 'pick': False})
    check('pick Off: A says pick false', (await riya.get('/api/choice/bank', params={'exam': 'jee-main'})).json()['pick'] is False)
    check('pick Off: B 404', (await riya.get('/api/choice/chapters/TEST_P1/questions')).status_code == 404)
    r = await arjun.post('/api/choice/papers', json={'exam': 'jee-main', 'request_key': str(uuid.uuid4()), 'mode': 'pick', 'question_ids': pick[:1]})
    check('pick Off: C pick 409', r.status_code == 409 and err(r) == choice.CLOSED, (r.status_code, err(r)))
    await owner.put('/api/admin/choice/jee-main', json={**body, 'expected_revision': 2, 'pick': False, 'random': False})
    check('both Off: A 404 again', (await riya.get('/api/choice/bank', params={'exam': 'jee-main'})).status_code == 404)
    r = await riya.post(f'/api/sets/{sid}/start', json={'start_key': 'TEST' + uuid.uuid4().hex})
    check('both Off: an already made paper still opens', r.status_code == 200, r.text[:200])
    r = await owner.get('/api/admin/choice/jee-main')
    stt = r.json()['stats']
    check('owner stats: 10 papers, 2 creators', stt['total'] == 10 and stt['creators'] == 2 and stt['today'] == 10 and stt['pick'] == 1, stt)
    check('catalogue never lists a made paper', sid not in json.dumps((await riya.get('/api/my/sets')).json()))
    await owner.put('/api/admin/choice/jee-main', json={**body, 'expected_revision': 3, 'max_per_subject': 5})
    neha = await student('9811122904')
    r = await neha.post('/api/choice/papers', json={'exam': 'jee-main', 'request_key': str(uuid.uuid4()), 'mode': 'random', 'count': 20})
    check('random over the owner per-subject top -> its own sentence', r.status_code == 422 and err(r) == choice.TOO_MANY.format(n=15), (r.status_code, err(r)))
    check('no slot used by a refused paper', (await neha.get('/api/choice/home')).json()['made_today'] == 0)
    check('no real DB handle touched', not H.leftover_real_handles())


async def run():
    try:
        await main()
    except Exception as e:
        import traceback; traceback.print_exc(); check('harness completed without exception', False, repr(e))
    finally:
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)  # the throw-away test DB only
        f = [r for r in RESULTS if not r[1]]
        print(f'TOTAL {len(RESULTS)} PASS {len(RESULTS) - len(f)} FAIL {len(f)}')


if __name__ == '__main__':
    asyncio.run(run())
