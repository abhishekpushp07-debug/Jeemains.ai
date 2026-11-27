"""TEST-ONLY (testing agent, iteration 232): adversarial + app-contract checks for Student Choice on a throw-away isolated DB.
Reuses seed/staff/student of tests/choice_iso229.py (which imports iso_harness_book170 first: DB rebound, storage/AI mocked).
Run: cd /app/backend && bash tests/runners/solo.sh python -u tests/choice_adversarial_t1_232.py
"""
import asyncio, re, sys, time, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import iso_harness_book170 as H  # noqa: E402  (must import first)
import choice_iso229 as C  # noqa: E402
import httpx  # noqa: E402
from tejas import choice  # noqa: E402

RESULTS = []
T = H.TDB
SETID = re.compile(r'^[A-Za-z0-9_-]{6,80}$')


def check(name, ok, detail=''):
    RESULTS.append((name, bool(ok), str(detail)[:400]))
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:400]), flush=True)


err = C.err
BODY = {'expected_revision': 0, 'pick': True, 'random': True, 'max_questions': 75, 'max_per_subject': None,
        'minutes_per_question': {'Physics': 2.4, 'Chemistry': 1.6, 'Mathematics': 3.2}, 'daily_limit': 50}
REV = {'n': 0}


async def save(owner, **kw):
    r = await owner.put('/api/admin/choice/jee-main', json={**BODY, **kw, 'expected_revision': REV['n']})
    if r.status_code == 200:
        REV['n'] = r.json()['settings']['revision']
    return r


def paper(c, **kw):
    return c.post('/api/choice/papers', json={'exam': 'jee-main', 'request_key': kw.pop('key', None) or str(uuid.uuid4()), **kw})


async def ids_of(c, sid, page=1):
    r = await c.get(f'/api/choice/chapters/{sid}/questions', params={'page': page})
    return r.json()['items'] if r.status_code == 200 else []


async def main():
    assert not H.leftover_real_handles()
    choice.reset()
    await C.seed()
    # extra seeds: one 320-question Physics chapter (6-page cap) and one 80-question Maths chapter (75 Maths)
    await T.tejas_sets.insert_many([C.qset('TEST_PX', 'Physics', 10, 320, 0), C.qset('TEST_MX', 'Mathematics', 11, 60, 20)])
    owner = await C.staff('owner')
    reviewer = await C.staff('reviewer')
    s1, s2, s3, s4 = [await C.student(p) for p in ('9811132901', '9811132902', '9811132903', '9811132904')]

    # ---- default Off: never 5xx, 404; reviewer refused
    r = await s1.get('/api/choice/bank', params={'exam': 'jee-main'})
    check('A: default Off -> 404', r.status_code == 404, r.status_code)
    check('A: weird exam value never 5xx', (await s1.get('/api/choice/bank', params={'exam': '../$where'})).status_code == 404)
    check('A: missing exam -> 404 not 5xx', (await s1.get('/api/choice/bank')).status_code == 404)
    check('owner GET: reviewer 403', (await reviewer.get('/api/admin/choice/jee-main')).status_code == 403)
    check('owner PUT: reviewer 403', (await reviewer.put('/api/admin/choice/jee-main', json=BODY)).status_code == 403)
    check('owner GET: unknown exam 404', (await owner.get('/api/admin/choice/bitsat')).status_code == 404)
    r = await save(owner)
    check('owner save both On', r.status_code == 200, r.text[:200])
    r = await owner.put('/api/admin/choice/jee-main', json={**BODY, 'expected_revision': 0})
    check('owner save stale revision 0 -> 409', r.status_code == 409, r.status_code)
    r = await owner.put('/api/admin/choice/jee-main', json={**BODY, 'expected_revision': REV['n'] + 5})
    check('owner save future revision -> 409', r.status_code == 409, r.status_code)
    for name, extra in (('max_questions 0', {'max_questions': 0}), ('max_questions 76', {'max_questions': 76}),
                        ('daily_limit 0', {'daily_limit': 0}), ('max_per_subject 0', {'max_per_subject': 0}),
                        ('pick as string', {'pick': 'true'}), ('extra key', {'evil': 1})):
        r = await owner.put('/api/admin/choice/jee-main', json={**BODY, **extra, 'expected_revision': REV['n']})
        check(f'owner save {name} -> 422', r.status_code == 422, (r.status_code, r.text[:120]))

    # ---- door A exact shape
    r = await s1.get('/api/choice/bank', params={'exam': 'jee-main'})
    check('A: keys exactly 5', set(r.json()) == {'pick', 'random', 'max_questions', 'max_per_subject', 'minutes_per_question'}, r.json())
    check('A: minutes keys/values', r.json()['minutes_per_question'] == {'Physics': 2.4, 'Chemistry': 1.6, 'Mathematics': 3.2})

    # ---- door B: pages, shape, stems
    r = await s1.get('/api/choice/chapters/TEST_PX/questions', params={'page': 1})
    check('B: 320-question chapter capped to 6 pages of 50', r.status_code == 200 and r.json()['pages'] == 6 and len(r.json()['items']) == 50, r.json().get('pages'))
    check('B: page 6 ok', (await s1.get('/api/choice/chapters/TEST_PX/questions', params={'page': 6})).status_code == 200)
    check('B: page 7 -> 404', (await s1.get('/api/choice/chapters/TEST_PX/questions', params={'page': 7})).status_code == 404)
    check('B: page 0 -> 422', (await s1.get('/api/choice/chapters/TEST_PX/questions', params={'page': 0})).status_code == 422)
    check('B: page abc -> 422', (await s1.get('/api/choice/chapters/TEST_PX/questions', params={'page': 'abc'})).status_code == 422)
    check('B: no session -> 401', (await C.client().get('/api/choice/chapters/TEST_PX/questions')).status_code == 401)
    allitems = []
    for sid in ('TEST_P1', 'TEST_PO', 'TEST_C1', 'TEST_M1'):
        allitems += await ids_of(s1, sid)
    check('B: every item keys exactly {id,number,type,text,stem}', all(set(i) == {'id', 'number', 'type', 'text', 'stem'} for i in allitems))
    stems = [st for i in allitems for st in i['stem']]
    check('B: stems {url,w,h} both-or-neither', stems and all(set(st) in ({'url'}, {'url', 'w', 'h'}) for st in stems), stems)
    check('B: types only mcq/integer, text str', all(i['type'] in ('mcq', 'integer') and isinstance(i['text'], str) for i in allitems))

    # ---- picture links: expired, wrong index, far future, wrong set
    po = await ids_of(s1, 'TEST_PO')
    it = next(i for i in po if i['stem'])
    url = it['stem'][0]['url'].replace(C.BASE, '')
    bare = httpx.AsyncClient(transport=httpx.ASGITransport(app=H.app), base_url=C.BASE, timeout=60)
    check('pic: valid link 200', (await bare.get(url)).status_code == 200)
    tok = it['id']
    past = int(time.time()) - 10
    far = int(time.time()) + 10 * 86400
    cur = int(choice._NAME.fullmatch(url.rsplit('/', 1)[1])[2])
    for name, idx, exp, sid in (('expired exp (valid sig)', 0, past, 'TEST_PO'), ('wrong index (valid sig)', 1, cur, 'TEST_PO'),
                                ('exp 10 days ahead (valid sig)', 0, far, 'TEST_PO'), ('other set id (valid sig)', 0, cur, 'TEST_P1')):
        u2 = f'/api/media/choice/{sid}/{tok}/{idx}-{exp}-{choice._sig(sid, tok, idx, exp)}'
        r = await bare.get(u2)
        check(f'pic: {name} -> 404', r.status_code == 404, r.status_code)

    # ---- door C validation (strict types, request_key shape)
    for name, cnt in (('float', 10.0), ('bool', True), ('string', '10'), ('null', None)):
        r = await paper(s1, mode='random', count=cnt)
        check(f'C: random count {name} -> 422', r.status_code == 422, (r.status_code, r.text[:120]))
    for name, key in (('7 chars', 'a' * 7), ('101 chars', 'a' * 101), ('bad char', 'abcdefg!h'), ('space', 'abcd efgh'), ('empty', '')):
        r = await paper(s1, mode='random', count=3, key=key) if key else await s1.post('/api/choice/papers', json={'exam': 'jee-main', 'request_key': '', 'mode': 'random', 'count': 3})
        check(f'C: request_key {name} -> 422', r.status_code == 422, (r.status_code, err(r)))
    r = await paper(s1, mode='other', count=3)
    check('C: unknown mode refused (4xx)', 400 <= r.status_code < 500, r.status_code)
    r = await paper(s1, mode='random', count=3, extra=1)
    check('C: extra key -> 422', r.status_code == 422, r.status_code)
    r = await s1.post('/api/choice/papers', json={'exam': 'neet', 'request_key': str(uuid.uuid4()), 'mode': 'random', 'count': 3})
    check('C: other exam -> 422', r.status_code == 422, r.status_code)
    r = await C.client().post('/api/choice/papers', json={'exam': 'jee-main', 'request_key': str(uuid.uuid4()), 'mode': 'random', 'count': 3})
    check('C: no session -> 401', r.status_code == 401, r.status_code)
    r = await s1.post('/api/choice/papers', json={'exam': 'jee-main', 'request_key': 'k' * 60000, 'mode': 'pick', 'question_ids': ['x']})
    check('C: >48KB body -> 413', r.status_code == 413, r.status_code)
    check('C: none of the refused calls used quota', (await s1.get('/api/choice/home')).json()['made_today'] == 0)
    r = await paper(s1, mode='random', count=3, key='a' * 8)
    check('C: request_key 8 chars ok', r.status_code == 200 and SETID.match(r.json()['set_id']), r.text[:200])
    r = await paper(s1, mode='random', count=3, key='Z-_9' * 25)
    check('C: request_key 100 chars ok', r.status_code == 200, r.text[:200])

    # ---- same key race -> one paper, one quota slot
    k = str(uuid.uuid4())
    rs = await asyncio.gather(*[paper(s2, mode='random', count=5, key=k) for _ in range(6)])
    got = {x.json().get('set_id') for x in rs if x.status_code == 200}
    check('C: 6 racing same-key -> 1 paper', len(got) == 1 and all(x.status_code == 200 for x in rs), [x.status_code for x in rs])
    check('C: same-key race -> 1 db paper', await T.tejas_choice_papers.count_documents({'request_key': k}) == 1)
    r = await paper(s2, mode='pick', question_ids=[allitems[0]['id']], key=k)
    check('C: same key, other body -> still same paper', r.json().get('set_id') in got, r.text[:200])

    # ---- minutes (contract)
    p1, c1, m1 = await ids_of(s3, 'TEST_P1'), await ids_of(s3, 'TEST_C1'), await ids_of(s3, 'TEST_M1')
    mx = await ids_of(s3, 'TEST_MX') + await ids_of(s3, 'TEST_MX', 2)
    r = await paper(s3, mode='pick', question_ids=[x['id'] for x in p1[:10] + c1[:10] + m1[:10]])
    doc = await T.tejas_choice_papers.find_one({'id': r.json().get('set_id')})
    check('minutes: 10P+10C+10M = 72', doc and doc['rules']['minutes'] == 72, doc and doc['rules'])
    r = await paper(s3, mode='pick', question_ids=[x['id'] for x in m1[:25]])
    doc = await T.tejas_choice_papers.find_one({'id': r.json().get('set_id')})
    check('minutes: 25 Maths = 80', doc and doc['rules']['minutes'] == 80 and doc['maximum'] == 100, doc and doc['rules'])
    r = await paper(s3, mode='pick', question_ids=[x['id'] for x in mx[:75]])
    sid75 = r.json().get('set_id')
    doc = await T.tejas_choice_papers.find_one({'id': sid75})
    check('minutes: 75 Maths = 240 (no 180 cap)', doc and doc['rules']['minutes'] == 240 and doc['maximum'] == 300, (r.status_code, doc and doc['rules']))
    order = [i['type'] for i in doc['items']] if doc else []
    check('75 Maths: MCQ first then numerical', order == sorted(order, key=lambda t: t != 'mcq'), order[:5])

    # ---- the paper: no Origin, other student, my/tests, cohort
    nori = C.client(origin=False); nori.cookies = s3.cookies
    r = await nori.get(f'/api/my/sets/{sid75}')
    check('my/sets no Origin -> 200 choice', r.status_code == 200 and r.json()['test_kind'] == 'choice' and r.json()['count'] == 75, r.text[:200])
    check('my/sets other student 404', (await s4.get(f'/api/my/sets/{sid75}')).status_code == 404)
    check('preflight other student 404', (await s4.post(f'/api/sets/{sid75}/preflight', json={})).status_code == 404)
    check('start other student 404', (await s4.post(f'/api/sets/{sid75}/start', json={'start_key': 'TEST' + uuid.uuid4().hex})).status_code == 404)
    r = await nori.post(f'/api/sets/{sid75}/start', json={'start_key': 'TEST' + uuid.uuid4().hex})
    check('start no Origin -> 200, 75 q, 240 min', r.status_code == 200 and r.json()['count'] == 75, r.text[:200])
    aid = r.json().get('id')
    check('attempt of another student: results 404/403', (await s4.get(f'/api/attempts/{aid}/results')).status_code in (403, 404))
    await s3.post(f'/api/attempts/{aid}/submit')
    await C.results(s3, aid)
    r = await s3.get(f'/api/attempts/{aid}/cohort')
    check('cohort reason', r.status_code == 200 and r.json().get('reason') == 'Is test par Rank nahi banta.', r.text[:200])
    r = await s3.get('/api/my/tests', params={'tab': 'completed'})
    items = r.json().get('items', [])
    check('my/tests: items carry test_kind', items and all('test_kind' in x for x in items) and any(x['id'] == aid and x['test_kind'] == 'choice' for x in items),
          [(x.get('id'), x.get('test_kind')) for x in items][:5])

    # ---- chapter goes un-live after listing
    m2 = await ids_of(s4, 'TEST_M2')
    await T.tejas_sets.update_one({'id': 'TEST_M2'}, {'$set': {'live_enabled': False}})
    r = await paper(s4, mode='pick', question_ids=[x['id'] for x in m2[:3]])
    cached = r.status_code
    if r.status_code == 200:
        st = await s4.post(f"/api/sets/{r.json()['set_id']}/start", json={'start_key': 'TEST' + uuid.uuid4().hex})
        check('INFO-ONLY un-live within 30 s pool cache: Start of the new paper', True, (st.status_code, err(st)))
    choice.reset()
    r = await paper(s4, mode='pick', question_ids=[x['id'] for x in m2[:3]])
    check('un-live after cache: pick -> 422 GONE', r.status_code == 422 and err(r) == choice.GONE, (r.status_code, err(r), 'first try', cached))
    await T.tejas_sets.update_one({'id': 'TEST_M2'}, {'$set': {'live_enabled': True}}); choice.reset()

    # ---- owner limits: max_per_subject, max_questions, daily_limit
    r = await save(owner, max_per_subject=5)
    check('owner save max_per_subject 5', r.status_code == 200, r.text[:200])
    check('A: shows max_per_subject 5', (await s4.get('/api/choice/bank', params={'exam': 'jee-main'})).json()['max_per_subject'] == 5)
    r = await paper(s4, mode='pick', question_ids=[x['id'] for x in p1[:6]])
    check('cap: pick 6 Physics -> 422 sentence', r.status_code == 422 and err(r) == choice.PER_SUBJECT.format(s='Physics', n=5), (r.status_code, err(r)))
    r = await paper(s4, mode='pick', question_ids=[x['id'] for x in p1[:5] + m1[:5]])
    check('cap: pick 5P+5M ok', r.status_code == 200, r.text[:200])
    r = await paper(s4, mode='random', count=15)
    doc = await T.tejas_choice_papers.find_one({'id': r.json().get('set_id')}) if r.status_code == 200 else None
    check('cap: random 15 -> 5+5+5', doc and doc['counts'] == {'Physics': 5, 'Chemistry': 5, 'Mathematics': 5}, (r.status_code, err(r)))
    r = await paper(s4, mode='random', count=20)
    check('cap: random 20 over 3x5 refused 422 (not a silent paper over the cap)', r.status_code == 422, (r.status_code, err(r)))
    print('INFO random 20 with cap 5 says:', err(r), flush=True)
    r = await save(owner, max_per_subject=None, max_questions=10)
    r = await paper(s4, mode='random', count=11)
    check('max_questions 10: random 11 -> 422 RANGE 10', r.status_code == 422 and err(r) == choice.RANGE.format(n=10), (r.status_code, err(r)))
    r = await paper(s4, mode='pick', question_ids=[x['id'] for x in p1[:11]])
    check('max_questions 10: pick 11 -> 422 TOO_MANY 10', r.status_code == 422 and err(r) == choice.TOO_MANY.format(n=10), (r.status_code, err(r)))
    r = await save(owner, max_questions=75, daily_limit=2)
    s5 = await C.student('9811132905')
    a1, a2, a3 = [await paper(s5, mode='random', count=3) for _ in range(3)]
    check('daily 2: two papers ok', a1.status_code == 200 and a2.status_code == 200, (a1.status_code, a2.status_code))
    check("daily 2: third -> 429 'Aaj ke 2 paper ban chuke hain...'", a3.status_code == 429 and err(a3) == 'Aaj ke 2 paper ban chuke hain. Kal naya paper bana sakte ho.', (a3.status_code, err(a3)))
    r = await s5.get('/api/choice/home')
    check('home: made_today 2 / limit 2', r.json()['made_today'] == 2 and r.json()['daily_limit'] == 2, r.text[:150])
    r = await paper(s4, mode='random', count=3)
    check('daily 2: s4 who already made >2 today -> 429', r.status_code == 429, r.status_code)
    # pick Off, random On: door B 404, door A pick false, random works
    r = await save(owner, pick=False, daily_limit=50)
    check('pick Off: B 404', (await s4.get('/api/choice/chapters/TEST_P1/questions')).status_code == 404)
    r = await paper(s4, mode='random', count=3)
    check('pick Off: random still 200', r.status_code == 200, r.text[:200])
    check('no real DB handle touched', not H.leftover_real_handles())


async def run():
    try:
        await main()
    except Exception as e:
        import traceback; traceback.print_exc(); check('harness completed without exception', False, repr(e))
    finally:
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        f = [r for r in RESULTS if not r[1]]
        print(f'TOTAL {len(RESULTS)} PASS {len(RESULTS) - len(f)} FAIL {len(f)}')


if __name__ == '__main__':
    asyncio.run(run())
