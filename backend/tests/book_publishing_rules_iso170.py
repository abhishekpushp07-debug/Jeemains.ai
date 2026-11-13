"""TEST-ONLY iteration 170 part 2: scale (10/50/51 mocks), holds isolation, rules, schedule/competition, AI reading (MOCKED).
Run: cd /app/backend && python tests/book_publishing_rules_iso170.py
"""
import asyncio, json, time, uuid
import book_publishing_iso170 as T  # noqa  (harness: isolated DB, mocked storage/AI)
from book_publishing_iso170 import H, J, check, build_pdf, q3, drain, mkstaff, client, upload, complete, OUT, INSTR
import fitz


def one(tag):
    return [(1, f'{tag}: unit of charge is', ['volt', 'coulomb', 'ohm', 'tesla'])]


async def view(c, bid):
    return (await c.get(f'/api/admin/books/{bid}')).json()


async def ctl(c, bid, action, **kw):
    v = await view(c, bid)
    r = await c.post(f'/api/admin/books/{bid}/control', json={'revision': v['revision'], 'action': action, **kw}); await drain()
    return r


async def scale(own):
    # 10 mocks, per-mock layout, 1 question each
    raw = build_pdf([{'n': i, 'qs': q3(f'S{i}'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]} for i in range(1, 11)], path=OUT / 'book_10mocks.pdf')
    b = await upload(own, raw, 'TEST_QA170 Ten'); t = time.time(); _, v = await complete(own, b['id'])
    st = [m['state'] for m in v['mocks']]
    print('10-mock processed %.1fs pages=%s states=%s' % (time.time() - t, v['pages'], st))
    check('10 mocks detected', len(st) == 10, st)
    check('10 clean mocks all publish (per-mock layout)', st.count('published') == 10, st)
    # 170: Mock 2 is already correctly published -> repairing its page must be immutable 409
    pg = (await own.get(f"/api/admin/books/{b['id']}/pages/5")).json()
    r = await own.put(f"/api/admin/books/{b['id']}/pages/5", json={'revision': pg['revision'], 'classification': pg['classification'], 'regions': pg['regions'], 'issues': [], 'note': 'QA170 attempt edit published Mock 2'})
    check('repair published Mock 2 page immutable 409', r.status_code == 409, (r.status_code, r.text[:200]))
    v = await view(own, b['id']); m = {x['label']: x for x in v['mocks']}
    s1 = await H.TDB.tejas_sets.find_one({'id': m['Mock 1']['set_id']}); s2 = await H.TDB.tejas_sets.find_one({'id': m['Mock 2']['set_id']})
    check('repeated Q1 across mocks distinct ids/sets', s1['id'] != s2['id'] and s1['questions'][0]['id'] != s2['questions'][0]['id'] and 'S2' in s2['questions'][0]['text'] and 'S1' in s1['questions'][0]['text'])
    ks = [[q['answer'] for q in (await H.TDB.tejas_sets.find_one({'id': x['set_id']}))['questions']] for x in v['mocks']]
    check('10-mock keys preserved', all(k == ['B', 'B', 'C'] for k in ks), ks)
    # 50 / 51 mocks
    for n, expect in ((50, True), (51, False)):  # 171: 51 branch now asserts allowed
        raw = build_pdf([{'n': i, 'qs': one(f'F{i}'), 'keys': [(1, 'B')]} for i in range(1, n + 1)], path=OUT / f'book_{n}mocks.pdf')
        b = await upload(own, raw, f'TEST_QA170 {n}'); t = time.time(); _, v = await complete(own, b['id'])
        print(f'{n}-mock processed %.1fs pages=%s state=%s msg=%s detected=%s published=%s' % (time.time() - t, v['pages'], v['state'], v['message'][:90], v['counts']['detected'], v['counts']['published']))
        if expect:
            check('50-mock book structure detected (50)', v['counts']['detected'] == 50, v['counts'])
            check('50 clean mocks ALL auto-publish (short native key pages)', v['counts']['published'] == 50 and v.get('scanned_pages', 0) == 0, (v['counts'], v.get('scanned_pages')))
        else: check('51-mock book now ALLOWED (171: no mock cap), all 51 published', v['counts']['detected'] == 51 and v['counts']['published'] == 51, (v['state'], v['message'], v['counts']))


async def holds(own):
    # Mock 1 clean; Mock 2 has a blank (scanned) page after its questions
    doc = fitz.open(stream=build_pdf([{'n': 1, 'qs': q3('H1'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]}, {'n': 2, 'qs': q3('H2'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]}]), filetype='pdf')
    doc.new_page(pno=6); raw = doc.tobytes(); (OUT / 'book_scanned_page.pdf').write_bytes(raw)
    b = await upload(own, raw, 'TEST_QA170 Scan'); _, v = await complete(own, b['id'])
    st = {m['label']: (m['state'], m['issues'][:2]) for m in v['mocks']}
    print('SCAN', v['scanned_pages'], json.dumps(st)[:600])
    check('scanned page counted', v['scanned_pages'] >= 1, v['scanned_pages'])
    check('scanned page in Mock 2 does not hold clean Mock 1', st['Mock 1'][0] == 'published', st['Mock 1'])
    check('no automatic paid AI for scanned page', H.AI_CALLS['ask'] == 0, H.AI_CALLS)
    # AI reading allowance (MOCKED provider)
    H.AI_SCRIPT['ask'] = lambda user: {'classification': 'unresolved', 'regions': [], 'issues': ['QA170 mocked: blank page']}
    r = await own.post(f"/api/admin/books/{b['id']}/allowances", json={'revision': v['revision'], 'purpose': 'reading', 'pages': [7], 'max_requests': 1, 'approved': True, 'request_id': 'qa170read01'})
    check('reading allowance 200', r.status_code == 200, r.text[:200]); await drain()
    a = await H.TDB.tejas_book_allowances.find_one({'book_id': b['id'], 'purpose': 'reading'})
    pg = (await own.get(f"/api/admin/books/{b['id']}/pages/7")).json()
    check('reading used exactly 1 mocked call, page AI-proposed', H.AI_CALLS['ask'] == 1 and a['used'] == 1 and a['state'] == 'complete' and pg['provenance'].get('kind') == 'ai_proposal', (H.AI_CALLS, a['used'], a['state'], pg['provenance']))
    r = await own.post(f"/api/admin/books/{b['id']}/allowances", json={'revision': (await view(own, b['id']))['revision'], 'purpose': 'reading', 'pages': [6], 'max_requests': 1, 'approved': True, 'request_id': 'qa170read01'})
    check('reused approval id for different work 409', r.status_code == 409, r.status_code)
    # interrupted running allowance -> failed, no silent paid retry
    await H.TDB.tejas_book_allowances.insert_one({'_id': 'qa170-running', 'book_id': b['id'], 'owner_id': 'x', 'purpose': 'reading', 'targets': [7], 'max_requests': 2, 'used': 1, 'cursor': 0, 'state': 'running', 'created_at': 0, 'error': '', 'results': []})
    await ctl(own, b['id'], 'retry'); a = await H.TDB.tejas_book_allowances.find_one({'_id': 'qa170-running'})
    check('restart of running allowance -> failed, no extra call', a['state'] == 'failed' and H.AI_CALLS['ask'] == 1, (a['state'], H.AI_CALLS))
    # pause one published mock
    m1 = next(m for m in (await view(own, b['id']))['mocks'] if m['label'] == 'Mock 1')
    if m1['state'] == 'published':
        r = await ctl(own, b['id'], 'pause_mock', mock_id=m1['id'], reason='QA170 pause')
        s = await H.TDB.tejas_sets.find_one({'id': m1['set_id']})
        check('pause_mock withdraws set', r.status_code == 200 and s['status'] == 'withdrawn', (r.status_code, s['status']))
    r = await ctl(own, b['id'], 'pause_mock', mock_id=m1['id'], reason='  ')
    check('control without reason 422', r.status_code == 422, r.status_code)


async def rules_and_leaks(own):
    mocks = [{'n': 1, 'qs': q3('U1'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')], 'instr': INSTR[:2] + ['Total Questions: {n}', 'Attempt any 2 questions', 'Correct: +4', 'Wrong: -1', 'Unanswered: 0']},
             {'n': 2, 'qs': [(1, 'V2: g value is. Answer: B', ['1', '9.8', '20', '0'])] + q3('V2')[1:], 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]},
             {'n': 3, 'qs': q3('W3'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')], 'instr': ['Instructions for this paper follow the owner schedule.']}]
    raw = build_pdf(mocks, path=OUT / 'book_rules.pdf')
    b = await upload(own, raw, 'TEST_QA170 Rules'); _, v = await complete(own, b['id'])
    st = {m['label']: m for m in v['mocks']}
    print('RULES', json.dumps({k: (m['state'], m['issues'][:4]) for k, m in st.items()})[:1500])
    check('optional "attempt any" instruction held', st['Mock 1']['state'] == 'held' and any('rules' in i.lower() or 'optional' in i.lower() or 'unsupported' in i.lower() for i in st['Mock 1']['issues']), st['Mock 1']['issues'])
    check('answer visible in question crop held', st['Mock 2']['state'] == 'held' and any('answer' in i.lower() and 'visible' in i.lower() for i in st['Mock 2']['issues']), st['Mock 2']['issues'])
    m3 = st['Mock 3']; check('missing printed rules held', m3['state'] == 'held' and any('rules' in i.lower() for i in m3['issues']), m3['issues'])
    md = (await T.H.TDB.tejas_book_mocks.find_one({'_id': m3['id']}))
    base = {'exam': 'Custom', 'minutes': 60.0, 'expected_questions': 3, 'correct': 4.0, 'wrong': -1.0, 'mechanic': 'all_compulsory', 'solution_policy': 'key_only',
            'section_scoring': [{'subject': 'Physics', 'section': 'Physics', 'correct': 3.0, 'wrong': -1.0}], 'source_pages': [8], 'note': 'QA170 owner clarified printed rules'}
    r = await own.put(f"/api/admin/books/{b['id']}/mocks/{m3['id']}/rules", json={'revision': md['revision'], 'rules': base | {'source_pages': [999]}})
    check('rule evidence page outside book 422', r.status_code == 422, r.status_code)
    r = await own.put(f"/api/admin/books/{b['id']}/mocks/{m3['id']}/rules", json={'revision': md['revision'], 'rules': base | {'mechanic': 'bitsat_bonus', 'bonus_count': 12}})
    check('bitsat_bonus on Custom/3q accepted then held', r.status_code == 200, r.text[:200]); await drain()
    m = next(x for x in (await view(own, b['id']))['mocks'] if x['id'] == m3['id'])
    check('unsupported bonus held with message', m['state'] == 'held' and any('BITSAT bonus' in i for i in m['issues']), m['issues'])
    md = await T.H.TDB.tejas_book_mocks.find_one({'_id': m3['id']})
    r = await own.put(f"/api/admin/books/{b['id']}/mocks/{m3['id']}/rules", json={'revision': md['revision'], 'rules': base})
    check('custom section-scoring rules 200', r.status_code == 200, r.text[:200]); await drain()
    m = next(x for x in (await view(own, b['id']))['mocks'] if x['id'] == m3['id'])
    print('Mock3 after rules', m['state'], m['issues'][:4])
    check('Mock 3 publishes after rule clarification', m['state'] == 'published', m['issues'])
    if m['state'] == 'published':
        s = await H.TDB.tejas_sets.find_one({'id': m['set_id']})
        check('per-section scoring copied to questions', all(q.get('scoring') == {'correct': 3.0, 'wrong': -1.0, 'skipped': 0} for q in s['questions']), [q.get('scoring') for q in s['questions']])
        check('Custom exam retained', s['exam'] == 'Custom', s['exam'])
    # shared passage leakage via owner mapping of Mock 2 question page (page 6 has "Answer: B" inside Q1)
    pg = (await own.get(f"/api/admin/books/{b['id']}/pages/6")).json()
    regs = [x for x in pg['regions'] if x['role'] == 'question']
    q1 = next(x for x in regs if x['number'] == 1)
    shared = dict(q1, role='shared', number=0, shared_for=[2], checked=True, option_labels=[], response_type='unresolved')
    q1b = dict(q1, rect=[q1['rect'][0], q1['rect'][1] + 0.0, q1['rect'][2], q1['rect'][3]])
    r = await own.put(f"/api/admin/books/{b['id']}/pages/6", json={'revision': pg['revision'], 'classification': 'questions', 'regions': [shared] + [x for x in regs if x['number'] != 1], 'issues': [], 'note': 'QA170 map shared passage'})
    check('shared passage repair saved', r.status_code == 200, r.text[:200]); await drain()
    m = next(x for x in (await view(own, b['id']))['mocks'] if x['label'] == 'Mock 2')
    check('shared passage exposing key held', m['state'] == 'held' and any('shared passage exposes' in i for i in m['issues']), m['issues'][:5])
    # overlapping question crop with key region
    pg = (await own.get(f"/api/admin/books/{b['id']}/pages/6")).json()
    qs = [x for x in pg['regions'] if x['role'] == 'question']
    key = dict(qs[0], role='key', answer='B', option_labels=[], response_type='unresolved')
    r = await own.put(f"/api/admin/books/{b['id']}/pages/6", json={'revision': pg['revision'], 'classification': 'mixed', 'regions': qs + [key], 'issues': [], 'note': 'QA170 overlap test'})
    await drain(); m = next(x for x in (await view(own, b['id']))['mocks'] if x['label'] == 'Mock 2')
    check('question overlapping key region held', any('overlaps' in i for i in m['issues']), m['issues'][:6])


async def schedule(own, stu):
    raw = build_pdf([{'n': 1, 'qs': q3('T1'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]}], path=OUT / 'book_sched.pdf')
    db_now = (await H.TDB.command('hello'))['localTime'].timestamp()
    b = await upload(own, raw, 'TEST_QA170 Sched', release_at=db_now + 6); _, v = await complete(own, b['id'])
    m = v['mocks'][0]; print('sched state', m['state'], m['issues'][:2])
    check('future schedule => scheduled (not visible yet)', m['state'] == 'scheduled', (m['state'], m['issues']))
    r = await stu.get(f"/api/book-series/{b['id']}"); check('student cannot see before release', r.status_code == 404, r.status_code)
    await asyncio.sleep(7)
    r = await stu.get(f"/api/book-series/{b['id']}"); check('student sees after release', r.status_code == 200, r.status_code)
    # missed release
    raw = build_pdf([{'n': 1, 'qs': q3('X1'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]}], path=OUT / 'book_missed.pdf')
    db_now = (await H.TDB.command('hello'))['localTime'].timestamp()
    b = await upload(own, raw, 'TEST_QA170 Missed', release_at=db_now + 2); await asyncio.sleep(3); _, v = await complete(own, b['id'])
    m = v['mocks'][0]; print('missed', m['state'], m['missed_release'], m['issues'][:2])
    check('missed release held, not launched late', m['state'] == 'held' and m['missed_release'], (m['state'], m['issues']))
    r = await ctl(own, b['id'], 'release_now', mock_id=m['id'], reason='QA170 release now decision')
    m = (await view(own, b['id']))['mocks'][0]
    check('release_now publishes missed mock', r.status_code == 200 and m['state'] == 'published', (r.status_code, m['state'], m['issues'][:3]))
    # competitive: missed -> release_now 409
    raw = build_pdf([{'n': 1, 'qs': q3('C1'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]}], path=OUT / 'book_comp.pdf')
    db_now = (await H.TDB.command('hello'))['localTime'].timestamp()
    b = await upload(own, raw, 'TEST_QA170 Comp', release_at=db_now + 2, closes_at=db_now + 600, competitive=True); await asyncio.sleep(3); _, v = await complete(own, b['id'])
    m = v['mocks'][0]
    r = await ctl(own, b['id'], 'release_now', mock_id=m['id'], reason='QA170 comp late')
    check('competitive missed window release_now 409', r.status_code == 409, r.status_code)
    # competitive embargo of solutions
    raw = build_pdf([{'n': 1, 'qs': q3('E1'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]}], path=OUT / 'book_embargo.pdf')
    db_now = (await H.TDB.command('hello'))['localTime'].timestamp()
    b = await upload(own, raw, 'TEST_QA170 Embargo', release_at=db_now + 5, closes_at=db_now + 25, competitive=True); _, v = await complete(own, b['id'])
    m = v['mocks'][0]; check('competitive mock scheduled', m['state'] == 'scheduled', (m['state'], m['issues'][:3]))
    if m['state'] != 'scheduled': return
    await asyncio.sleep(6)
    pf = await stu.post(f"/api/sets/{m['set_id']}/preflight", json={}); check('competitive preflight in window 200', pf.status_code == 200, pf.text[:200])
    r = await stu.post(f"/api/sets/{m['set_id']}/start", json={'start_key': 'qa170comp' + uuid.uuid4().hex[:8], 'device_checked': True})
    check('competitive start in window', r.status_code == 200, r.text[:200])
    if r.status_code != 200: return
    a = r.json(); q = a['questions'][0]['id']
    await stu.post(f"/api/attempts/{a['id']}/submit")
    r = await stu.get(f"/api/attempts/{a['id']}/questions/{q}/asset/solution/0"); check('key crop embargoed until competition end', r.status_code == 403, r.status_code)
    r = await stu.get(f"/api/attempts/{a['id']}/results"); print('comp results', r.status_code, r.text[:160])
    check('results do not reveal key before close', '"answer"' not in r.text or r.status_code != 200, r.text[:200])


async def run():
    try:
        own, _ = await mkstaff('owner', 'owner')
        stu = client(); phone = '97' + str(uuid.uuid4().int)[:8]
        await stu.post('/api/auth/phone/signup', json={'phone': phone, 'pin': '5937', 'confirm_pin': '5937'})
        for f in (scale, holds, rules_and_leaks):
            try: await f(own)
            except Exception as e:
                import traceback; traceback.print_exc(); check(f'{f.__name__} completed', False, repr(e))
        try: await schedule(own, stu)
        except Exception as e:
            import traceback; traceback.print_exc(); check('schedule completed', False, repr(e))
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
        f = [r for r in T.RESULTS if not r[1]]
        print(f'TOTAL {len(T.RESULTS)} PASS {len(T.RESULTS) - len(f)} FAIL {len(f)}')
        json.dump(T.RESULTS, open(OUT / 'results_rules.json', 'w'), indent=1)

asyncio.run(run())
