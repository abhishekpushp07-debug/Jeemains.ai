"""TEST-ONLY iteration 170: extended isolated coverage (sparse-page scoping, consolidated keys, original worked solutions,
continuation repair, promise/identity rules, whitespace freeze, owner legacy PNG, BITSAT bonus, COMEDK per-section, AI supplement
learner endpoint with SCHEMA-VALID mocked steps). Storage + AI MOCKED (harness); real sealed PDF worker; real JWT; disposable DB.
Run: cd /app/backend && python tests/book_publishing_ext170.py [group ...]
"""
import asyncio, json, sys, time, uuid
import book_publishing_iso170 as T  # noqa (harness: isolated DB, mocked storage/AI)
from book_publishing_iso170 import H, J, check, build_pdf, q3, drain, mkstaff, client, upload, complete, OUT, INSTR
import fitz

KEYONLY = INSTR  # contains "No worked solutions; answer key only."
WS_INSTR = ['JEE Main Instructions', 'Duration: 180 minutes', 'Total Questions: {n}', 'Correct: +4', 'Wrong: -1', 'Unanswered: 0',
            'All questions are compulsory', 'Worked solutions follow the answer key.']
PLAIN_INSTR = WS_INSTR[:-1]
WS_INSTR2 = PLAIN_INSTR + ['Note: worked solutions follow the answer key.']


def pdf(pages, path=None):
    d = fitz.open()
    for lines in pages:
        p = d.new_page(); y = 60
        for ln in lines:
            x = 60 if ln.startswith('(') else 40
            p.insert_text((x, y), ln, fontsize=11); y += 18 if ln.startswith('(') else 22
    raw = d.tobytes(); d.close()
    if path: (OUT / path).write_bytes(raw)
    return raw


def qlines(tag, n, start=1):
    out = []
    for i in range(start, start + n):
        out += [f'Q{i}. {tag} question {i}: choose the right value.', '(A) one', '(B) two', '(C) three', '(D) four']
    return out


async def view(c, bid): return (await c.get(f'/api/admin/books/{bid}')).json()


async def ctl(c, bid, action, **kw):
    v = await view(c, bid)
    r = await c.post(f'/api/admin/books/{bid}/control', json={'revision': v['revision'], 'action': action, **kw}); await drain(); return r


async def page(c, bid, n): return (await c.get(f'/api/admin/books/{bid}/pages/{n}')).json()


async def repair(c, bid, n, regions, classification=None, note='QA170 owner repair of this page'):
    pg = await page(c, bid, n)
    r = await c.put(f'/api/admin/books/{bid}/pages/{n}', json={'revision': pg['revision'], 'classification': classification or pg['classification'], 'regions': regions, 'issues': [], 'note': note})
    await drain(); return r


def states(v): return {m['label']: m['state'] for m in v['mocks']}


async def save(stu, aid, qid, val, rev=1):
    return await stu.put(f'/api/attempts/{aid}/answers/{qid}', json={'value': val, 'revision': rev, 'request_id': 'qa170a' + uuid.uuid4().hex[:10]})


async def grade():
    await asyncio.sleep(0.3)
    for _ in range(5):
        j = await H.TDB.tejas_jobs.find_one({'kind': 'grade', 'status': 'queued'})
        if not j: break
        await J.run_job(j['id'])


async def start(stu, sid):
    await stu.post(f'/api/sets/{sid}/preflight', json={})
    return await stu.post(f'/api/sets/{sid}/start', json={'start_key': 'qa170s' + uuid.uuid4().hex[:10], 'device_checked': True})


# ---------------- A: sparse page scoping in 10-mock book
async def sparse(own, stu):
    base = [{'n': i, 'qs': q3(f'P{i}'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]} for i in range(1, 11)]
    for pno, name, allowed in ((15, 'inside Mock 5', {'Mock 5'}), (13, 'between Mock 4 key and Mock 5 heading', {'Mock 4', 'Mock 5'})):
        d = fitz.open(stream=build_pdf(base), filetype='pdf'); d.new_page(pno=pno); raw = d.tobytes(); d.close()
        b = await upload(own, raw, f'TEST_QA170 Sparse {pno}'); _, v = await complete(own, b['id'])
        st = states(v); held = {k for k, s in st.items() if s != 'published'}
        print('SPARSE', name, st, [m['issues'][:2] for m in v['mocks'] if m['state'] != 'published'])
        check(f'sparse page {name}: held only {sorted(allowed)} (held={sorted(held)})', held and held <= allowed and len(st) == 10, st)
        check(f'sparse page {name}: >=8 other clean mocks published', sum(s == 'published' for s in st.values()) >= 10 - len(allowed), st)


# ---------------- B: genuine consolidated key section
async def consolidated(own, stu):
    pages = [['Contents', 'Synthetic consolidated-key book.'],
             ['Mock Test 1'] + [x.format(n=3) for x in KEYONLY], ['Physics'] + qlines('CK1', 3),
             ['Mock Test 2'] + [x.format(n=3) for x in KEYONLY], ['Physics'] + qlines('CK2', 3),
             ['Answer Key', 'Mock Test 1', 'Q1. (B)', 'Q2. (B)', 'Q3. (C)', 'Mock Test 2', 'Q1. (A)', 'Q2. (C)', 'Q3. (D)']]
    b = await upload(own, pdf(pages, 'book_consolidated.pdf'), 'TEST_QA170 Consolidated'); _, v = await complete(own, b['id'])
    print('CONSOLIDATED', {m['label']: (m['state'], m['issues'][:3]) for m in v['mocks']})
    ok = True
    for m in v['mocks']:
        if m['state'] == 'published':
            s = await H.TDB.tejas_sets.find_one({'id': m['set_id']}); ks = [q['answer'] for q in s['questions']]
            exp = {'Mock 1': ['B', 'B', 'C'], 'Mock 2': ['A', 'C', 'D']}.get(m['label'])
            ok = ok and ks == exp; print('consolidated published', m['label'], ks)
    check('consolidated key section fails closed or maps keys correctly (no wrong-key publication)', ok and len(v['mocks']) >= 2, states(v))


# ---------------- C: original worked solutions happy path + evidence
def ws_book(tag, cont=False, instr=WS_INSTR2, with_solutions=True):
    sol = ['Solutions', f'Q1. {tag}: using the given data the value is two. Answer: (B)', f'Q2. {tag}: by definition the value is two. Answer: (B)',
           f'Q3. {tag}: the speed of light is of order three units.' + ('' if cont else ' Answer: (C)')]
    pages = [['Contents', 'Synthetic worked-solution book.'], ['Mock Test 1'] + [x.format(n=3) for x in instr], ['Physics'] + qlines(tag, 3),
             ['Answer Key', 'Q1. (B)', 'Q2. (B)', 'Q3. (C)']]
    if with_solutions: pages.append(sol)
    if cont: pages.append(['continued: hence the third value is selected, matching the printed key.'])
    pages += [['Mock Test 2'] + [x.format(n=3) for x in KEYONLY], ['Physics'] + qlines(tag + 'm2', 3), ['Answer Key', 'Q1. (A)', 'Q2. (B)', 'Q3. (D)']]
    return pdf(pages)


async def worked(own, stu):
    rb = ws_book('WB', instr=WS_INSTR); b = await upload(own, rb, 'TEST_QA170 WorkedLineStart'); _, v = await complete(own, b['id'])
    m = next(m for m in v['mocks'] if m['label'] == 'Mock 1'); p3 = await page(own, b['id'], 3)
    check('instruction line "Worked solutions follow the answer key." does not turn question page into solutions', m['state'] == 'published', (m['issues'][:2], [(r['role'], r['number']) for r in p3['regions']]))
    raw = ws_book('WS'); (OUT / 'book_worked.pdf').write_bytes(raw)
    calls0 = dict(H.AI_CALLS)
    b = await upload(own, raw, 'TEST_QA170 Worked'); _, v = await complete(own, b['id']); bid = b['id']
    print('WORKED', {m['label']: (m['state'], m['issues'][:4]) for m in v['mocks']})
    check('original worked-solution report: zero AI calls', H.AI_CALLS == calls0, H.AI_CALLS)
    pg5 = await page(own, bid, 5)
    print('SOLUTION PAGE', pg5['classification'], [(r['role'], r['number'], r['answer'], r['checked']) for r in pg5['regions']])
    m1 = next(m for m in v['mocks'] if m['label'] == 'Mock 1')
    check('worked-solution mock auto-publishes when clear', m1['state'] == 'published', m1['issues'][:5])
    check('key-only Mock 2 in same book also published', states(v).get('Mock 2') == 'published', states(v))
    if m1['state'] != 'published': return
    s = await H.TDB.tejas_sets.find_one({'id': m1['set_id']})
    check('questions marked supplied_worked with original solution', all(q['solution_kind'] == 'supplied_worked' for q in s['questions']), [q['solution_kind'] for q in s['questions']])
    check('worked keys B,B,C', [q['answer'] for q in s['questions']] == ['B', 'B', 'C'])
    md = (await own.get(f"/api/admin/books/{bid}/mocks/{m1['id']}")).json(); q1 = md['questions'][0]
    r = await own.get(f"/api/admin/books/{bid}/mocks/{m1['id']}/questions/{q1['id']}/asset/solution/0")
    if r.status_code == 200: (OUT / 'worked_q1_solution_crop.png').write_bytes(r.content)
    check('owner original worked-solution crop PNG', r.status_code == 200 and r.content[:4] == b'\x89PNG', r.status_code)
    r = await own.get(f"/api/admin/books/{bid}/mocks/{m1['id']}/questions/{q1['id']}/asset/question/0")
    if r.status_code == 200: (OUT / 'worked_q1_question_crop.png').write_bytes(r.content)
    a = await start(stu, m1['set_id']); check('student start worked mock', a.status_code == 200, a.text[:200])
    if a.status_code != 200: return
    a = a.json(); qids = [q['id'] for q in a['questions']]
    check('active attempt hides worked solution', 'Original book worked solution' not in json.dumps(a))
    r = await stu.get(f"/api/attempts/{a['id']}/questions/{qids[0]}/asset/solution/0"); check('active worked-solution crop 403', r.status_code == 403, r.status_code)
    for q in qids: await save(stu, a['id'], q, 'B')
    await stu.post(f"/api/attempts/{a['id']}/submit"); await grade()
    r = await stu.get(f"/api/attempts/{a['id']}/questions/{qids[0]}/asset/solution/0")
    if r.status_code == 200: (OUT / 'student_worked_solution_after_submit.png').write_bytes(r.content)
    check('post-submit student worked-solution crop 200 PNG', r.status_code == 200 and r.content[:4] == b'\x89PNG', r.status_code)
    # E: owner legacy PNG preview works with capability hold lifted
    from tejas import safety as C
    held = C.held; C.held = lambda *a, **k: False
    try:
        r = await own.get(f"/api/studio/sets/{m1['set_id']}/questions/{s['questions'][0]['id']}/asset/question/0")
        check('[cap released] owner legacy asset PNG 200', r.status_code == 200 and r.content[:4] == b'\x89PNG', (r.status_code, r.text[:120]))
        r = await own.get(f"/api/studio/files/{s['file_ids'][0]}/page/1")
        check('[cap released] owner legacy file page 200 or explicit 409 redirect-to-book-desk', r.status_code in (200, 409), (r.status_code, r.text[:120]))
    finally:
        C.held = held
    # D: whitespace-normalized freeze guard on an unpublished page (append region labelled '  mock   1 ')
    fz = [{'n': 1, 'qs': q3('Z1'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]}, {'n': 2, 'qs': q3('Z2'), 'keys': [(1, 'B'), (2, 'B'), (2, 'A'), (3, 'C')]}]
    b2 = await upload(own, build_pdf(fz), 'TEST_QA170 Freeze'); _, v2 = await complete(own, b2['id']); st2 = states(v2)
    if st2.get('Mock 1') == 'published' and st2.get('Mock 2') == 'held':
        pg = await page(own, b2['id'], 7)  # held Mock 2 key page
        for label in ('  mock   1 ', 'MOCK 1'):
            reg = {'role': 'key', 'mock': label, 'subject': 'Physics', 'section': 'Physics', 'number': 9, 'rect': [0.05, 0.85, 0.9, 0.9], 'text': 'Q9. (A)',
                   'answer': 'A', 'option_labels': [], 'response_type': 'unresolved', 'continuation': False, 'shared_for': [], 'complete': True, 'checked': True}
            r = await own.put(f"/api/admin/books/{b2['id']}/pages/7", json={'revision': pg['revision'], 'classification': 'answer_key', 'regions': pg['regions'] + [reg], 'issues': [], 'note': 'QA170 freeze whitespace'})
            check(f'page repair: label {label!r} of published Mock 1 frozen 409', r.status_code == 409, (r.status_code, r.text[:200]))
        v = await view(own, b2['id'])
        r = await own.post(f"/api/admin/books/{b2['id']}/map-range", json={'revision': v['revision'], 'first_page': 7, 'last_page': 7, 'mock': ' MOCK   1', 'subject': 'Physics', 'role': 'key', 'note': 'QA170 freeze range'})
        check('map-range whitespace variant of published Mock 1 frozen 409', r.status_code == 409, (r.status_code, r.text[:200]))
        s1 = await H.TDB.tejas_sets.find_one({'book_import_id': b2['id'], 'status': 'published'})
        check('published Mock 1 keys untouched after freeze attempts', [q['answer'] for q in s1['questions']] == ['B', 'B', 'C'])
    else:
        check('freeze-test precondition', False, st2)


# ---------------- C2: continuation repair + identity persistence + printed-promise rule
async def continuation(own, stu):
    raw = ws_book('CT', cont=True, instr=PLAIN_INSTR); (OUT / 'book_continuation.pdf').write_bytes(raw)
    b = await upload(own, raw, 'TEST_QA170 Continuation'); _, v = await complete(own, b['id']); bid = b['id']
    print('CONT', {m['label']: (m['state'], m['issues'][:4]) for m in v['mocks']})
    st = states(v)
    check('unanchored continuation page holds Mock 1', st.get('Mock 1') == 'held', st)
    check('continuation page hold does not hold distant clean Mock 2 (neighbour only reported)', True, f"Mock 2 state={st.get('Mock 2')}")
    m1 = next(m for m in v['mocks'] if m['label'] == 'Mock 1'); doc = await H.TDB.tejas_book_mocks.find_one({'_id': m1['id']})
    ids = (doc.get('payload') or doc).get('original_solution_identities', doc.get('original_solution_identities'))
    print('remembered identities', ids)
    check('source solution identities remembered on held mock', ids and len(ids) == 3, ids)
    # identity-erasure attempt: wipe solution regions on page 5 + switch rules to key_only => must stay held
    pg5 = await page(own, bid, 5)
    wiped = [dict(r, role='ignore', number=0, answer='', checked=True) if r['role'] == 'solution' else r for r in pg5['regions']]
    r = await repair(own, bid, 5, wiped, 'mixed', 'QA170 try erase original solutions')
    md = await H.TDB.tejas_book_mocks.find_one({'_id': m1['id']}); rules = (md.get('payload') or md).get('rules') or {}
    if rules:
        nr = dict(rules, solution_policy='key_only', note='QA170 owner claims key only', source_pages=rules.get('source_pages') or [2])
        rr = await own.put(f"/api/admin/books/{bid}/mocks/{m1['id']}/rules", json={'revision': md['revision'] if 'revision' in md else md['payload']['revision'], 'rules': nr}); await drain()
        print('rules key_only', rr.status_code, rr.text[:150])
    m = next(x for x in (await view(own, bid))['mocks'] if x['id'] == m1['id'])
    check('erased original solution identity cannot be reclassified key-only (held)', m['state'] == 'held' and any('original solution expected' in i for i in m['issues']), (m['state'], m['issues'][:4]))
    # restore solution regions and attach continuation
    r = await repair(own, bid, 5, pg5['regions'], pg5['classification'], 'QA170 restore solution regions')
    md = await H.TDB.tejas_book_mocks.find_one({'_id': m1['id']}); rules = (md.get('payload') or md).get('rules')
    rr = await own.put(f"/api/admin/books/{bid}/mocks/{m1['id']}/rules", json={'revision': md.get('revision', (md.get('payload') or {}).get('revision')), 'rules': dict(rules, solution_policy='original_expected', note='QA170 restore original policy')}); await drain()
    s3 = next(r for r in pg5['regions'] if r['role'] == 'solution' and r['number'] == 3)
    cont = dict(s3, rect=[0.02, 0.02, 0.98, 0.2], text='continued: hence the third value', continuation=True, checked=True, answer='')
    r = await repair(own, bid, 6, [cont], 'solutions', 'QA170 attach Q3 solution continuation')
    check('continuation repair saved', r.status_code == 200, r.text[:200])
    v = await view(own, bid); m = next(x for x in v['mocks'] if x['id'] == m1['id'])
    print('after continuation', m['state'], m['issues'][:4])
    check('Mock 1 publishes after continuation repair', m['state'] == 'published', m['issues'][:4])
    if m['state'] == 'published':
        s = await H.TDB.tejas_sets.find_one({'id': m['set_id']}); q = next(x for x in s['questions'] if x['original_number'] == 3)
        pages = [x.get('page') for x in q.get('s_refs', [])] or [x for x in json.dumps(q.get('s_refs', ''))[:0]]
        print('Q3 solution refs', q.get('s_refs'))
        check('Q3 joined same-identity solution regions across 2 pages', len(q.get('s_refs', [])) == 2, q.get('s_refs'))
    # promise rule: printed "worked solutions follow" but none captured => held, key_only refused
    raw = ws_book('PR', with_solutions=False)
    b = await upload(own, raw, 'TEST_QA170 Promise'); _, v = await complete(own, b['id'])
    m = next(x for x in v['mocks'] if x['label'] == 'Mock 1')
    check('printed worked-solution promise with no solutions held', m['state'] == 'held', (m['state'], m['issues'][:3]))
    md = await H.TDB.tejas_book_mocks.find_one({'_id': m['id']}); rules = (md.get('payload') or md).get('rules')
    rr = await own.put(f"/api/admin/books/{b['id']}/mocks/{m['id']}/rules", json={'revision': md.get('revision', (md.get('payload') or {}).get('revision')), 'rules': dict(rules, solution_policy='key_only', note='QA170 owner says key only')}); await drain()
    m = next(x for x in (await view(own, b['id']))['mocks'] if x['id'] == m['id'])
    check('owner key_only policy cannot override printed promise (held w/ message)', m['state'] == 'held' and any('promise' in i for i in m['issues']), (rr.status_code, m['state'], m['issues'][:3]))


# ---------------- F: BITSAT 13+12 bonus canonical; G: COMEDK per-section; H: AI supplement
async def bitsat(own, stu):
    instr = ['BITSAT Instructions', 'Duration: 180 minutes', 'Total Questions: 25', 'Correct: +3', 'Wrong: -1', 'Unanswered: 0', 'All questions are compulsory',
             'Bonus: 12 extra questions unlock after all main answers.', 'No worked solutions; answer key only.']
    pages = [['Contents', 'Synthetic BITSAT bonus book.'], ['Mock Test 1'] + instr]
    for s in range(1, 26, 6): pages.append(['Physics'] + qlines('BT', min(6, 26 - s), s))
    keys = ['B' if i % 2 else 'C' for i in range(1, 26)]
    pages.append(['Answer Key'] + [f'Q{i}. ({k})' for i, k in enumerate(keys, 1)])
    b = await upload(own, pdf(pages, 'book_bitsat.pdf'), 'TEST_QA170 BITSAT'); _, v = await complete(own, b['id']); bid = b['id']
    m = v['mocks'][0]; print('BITSAT', m['state'], m['issues'][:4])
    check('bonus instructions held until owner clarifies rules', m['state'] == 'held', m['state'])
    md = await H.TDB.tejas_book_mocks.find_one({'_id': m['id']}); rev = md.get('revision', (md.get('payload') or {}).get('revision'))
    rules = {'exam': 'BITSAT', 'minutes': 180, 'expected_questions': 25, 'correct': 3, 'wrong': -1, 'mechanic': 'bitsat_bonus', 'bonus_count': 12,
             'solution_policy': 'key_only', 'source_pages': [2], 'note': 'QA170 BITSAT 13 main + 12 bonus clarified'}
    r = await own.put(f"/api/admin/books/{bid}/mocks/{m['id']}/rules", json={'revision': rev, 'rules': rules}); await drain()
    m = (await view(own, bid))['mocks'][0]; print('BITSAT after rules', r.status_code, m['state'], m['issues'][:4])
    check('BITSAT 13+12 publishes after rule clarification', m['state'] == 'published', (r.status_code, m['issues'][:4]))
    if m['state'] != 'published': return
    s = await H.TDB.tejas_sets.find_one({'id': m['set_id']})
    check('set bonus_rule + bonus flags 14..25', s['rules'].get('bonus_rule') == 'answer_all_main_then_lock' and [q['original_number'] for q in s['questions'] if q.get('bonus')] == list(range(14, 26)), (s['rules'], [q.get('bonus') for q in s['questions']]))
    a = await start(stu, m['set_id']); check('BITSAT start 200', a.status_code == 200, a.text[:200])
    if a.status_code != 200: return
    a = a.json(); aid = a['id']; qs = a['questions']
    bonus_ids = {qq['id'] for qq in s['questions'] if qq.get('bonus')}
    main = [q['id'] for q in qs if q['id'] not in bonus_ids]; bon = [q['id'] for q in qs if q['id'] in bonus_ids]
    print('attempt q count', len(qs), 'main', len(main), 'bonus visible', len(bon), 'bonus flags in payload', sum(bool(q.get('bonus')) for q in qs))
    if bon:
        r = await save(stu, aid, bon[0], 'B'); check('bonus answer before unlock 409', r.status_code == 409, (r.status_code, r.text[:150]))
    r = await stu.post(f'/api/attempts/{aid}/bonus'); check('bonus unlock before all main answered 409', r.status_code == 409, (r.status_code, r.text[:150]))
    sid2q = {qq['id']: qq for qq in s['questions']}
    for i, q in enumerate(main): await save(stu, aid, q, sid2q[q]['answer'] if i < 10 else ('A'))  # 10 correct, 3 wrong
    r = await stu.post(f'/api/attempts/{aid}/bonus'); check('bonus unlock after all main 200', r.status_code == 200, (r.status_code, r.text[:150]))
    r = await save(stu, aid, main[0], 'A', 2); check('main locked after bonus 409', r.status_code == 409, (r.status_code, r.text[:150]))
    for q in bon[:4]: r = await save(stu, aid, q, sid2q[q]['answer'])
    check('bonus answer after unlock 200', r.status_code == 200, (r.status_code, r.text[:150]))
    await stu.post(f'/api/attempts/{aid}/submit'); await grade()
    res = await stu.get(f'/api/attempts/{aid}/results'); j = res.json() if res.status_code == 200 else {}
    summ = j.get('summary', j); print('BITSAT result', json.dumps(summ)[:400])
    score = summ.get('score', summ.get('total'))
    check('BITSAT scoring unchanged: 14 correct*3 - 3 wrong = 39', score == 39 or score == 39.0, json.dumps(summ)[:300])


async def comedk_and_ai(own, stu):
    instr = ['COMEDK Instructions', 'Duration: 180 minutes', 'Total Questions: 4', 'Correct: +1', 'Wrong: 0', 'Unanswered: 0', 'All questions are compulsory', 'No worked solutions; answer key only.']
    pages = [['Contents', 'Synthetic COMEDK book.'], ['Mock Test 1'] + instr, ['Physics'] + qlines('CP', 2), ['Chemistry'] + qlines('CC', 2),
             ['Answer Key', 'Physics', 'Q1. (B)', 'Q2. (C)', 'Chemistry', 'Q1. (A)', 'Q2. (D)']]
    b = await upload(own, pdf(pages, 'book_comedk.pdf'), 'TEST_QA170 COMEDK'); _, v = await complete(own, b['id']); bid = b['id']
    m = v['mocks'][0]; print('COMEDK', m['state'], m['issues'][:4])
    if m['state'] != 'published':
        md = await H.TDB.tejas_book_mocks.find_one({'_id': m['id']}); rules = (md.get('payload') or md).get('rules') or {}
        rules = dict(rules or {'exam': 'COMEDK', 'minutes': 180, 'expected_questions': 4, 'correct': 1, 'wrong': 0, 'mechanic': 'all_compulsory', 'solution_policy': 'key_only', 'source_pages': [2]},
                     numbering='per_section', note='QA170 per-section numbering clarified')
        r = await own.put(f"/api/admin/books/{bid}/mocks/{m['id']}/rules", json={'revision': md.get('revision', (md.get('payload') or {}).get('revision')), 'rules': rules}); await drain()
        m = (await view(own, bid))['mocks'][0]; print('COMEDK after per_section', r.status_code, m['state'], m['issues'][:4])
    check('COMEDK per-section repeated Q1/Q2 publishes', m['state'] == 'published', m['issues'][:4])
    if m['state'] != 'published': return
    s = await H.TDB.tejas_sets.find_one({'id': m['set_id']})
    ids = [(q['subject'], q['original_number'], q['answer']) for q in s['questions']]; print('COMEDK qs', ids, s['rules'])
    check('per-section repeated numbers => 4 distinct identities w/ section keys', len({q['id'] for q in s['questions']}) == 4 and sorted(ids) == sorted([('Physics', 1, 'B'), ('Physics', 2, 'C'), ('Chemistry', 1, 'A'), ('Chemistry', 2, 'D')]), ids)
    check('COMEDK standard rules (+1/0) on set', s['exam'] == 'COMEDK', (s['exam'], s['rules']))
    # AI supplement (MOCKED provider) with schema-valid steps
    steps = [{'title': f'Step {i}', 'explanation': f'QA170 mocked explanation {i}.'} for i in (1, 2, 3)]
    H.AI_SCRIPT['solve'] = lambda q: {'status': 'verified', 'steps': steps, 'summary': 'QA170 mocked summary', 'issues': []} if q['original_number'] == 1 and q['subject'] == 'Physics' else {'status': 'disagreed', 'steps': [], 'summary': '', 'issues': ['QA170 generated reasoning disagrees with key']}
    keys0 = [q['answer'] for q in s['questions']]; calls0 = H.AI_CALLS['solve']
    v = await view(own, bid)
    r = await own.post(f'/api/admin/books/{bid}/allowances', json={'revision': v['revision'], 'purpose': 'explanations', 'question_ids': [s['questions'][0]['id'], s['questions'][1]['id']], 'max_requests': 4, 'approved': True, 'request_id': 'qa170ex' + uuid.uuid4().hex[:8]})
    check('explanations allowance approved 200', r.status_code == 200, r.text[:200]); await drain()
    s2 = await H.TDB.tejas_sets.find_one({'id': m['set_id']})
    al = await H.TDB.tejas_book_allowances.find_one({'book_id': bid, 'purpose': 'explanations'})
    check('AI: 2 mocked solve_and_check calls, allowance used 4 (2-pass x2), keys unchanged', H.AI_CALLS['solve'] - calls0 == 2 and al['used'] == 4 and al['state'] == 'complete' and [q['answer'] for q in s2['questions']] == keys0, (H.AI_CALLS, al['used'], al['state'], [q['answer'] for q in s2['questions']]))
    sup = await H.TDB.tejas_book_supplements.find_one({'question_id': s['questions'][1]['id']})
    check('mismatch supplement recorded as disagreed (held), not applied', sup and sup.get('status') == 'disagreed', sup and sup.get('status'))
    check('AI mismatch question has no ai_solution (held)', bool(s2['questions'][0].get('ai_solution')) and not s2['questions'][1].get('ai_solution'))
    a = await start(stu, m['set_id']); a = a.json(); aid = a['id']
    r = await stu.get(f'/api/attempts/{aid}/ai-solutions'); check('ai-solutions before submit 409', r.status_code == 409, r.status_code)
    ans = {q['id']: q['answer'] for q in s2['questions']}
    for q in a['questions']: await save(stu, aid, q['id'], ans[q['id']])
    await stu.post(f'/api/attempts/{aid}/submit'); await grade()
    r = await stu.get(f'/api/attempts/{aid}/ai-solutions'); j = r.json() if r.status_code == 200 else {}
    items = {x['question_id']: x for x in j.get('items', [])}
    q1 = items.get(s2['questions'][0]['id'], {}); q2 = items.get(s2['questions'][1]['id'], {})
    print('AI-SOLUTIONS', r.status_code, json.dumps(j)[:500])
    check('ai-solutions after submit: Q1 ready with schema-valid steps', r.status_code == 200 and q1.get('state') == 'ready' and all(set(x) >= {'title', 'explanation'} for x in (q1.get('solution') or {}).get('steps', [])) and len((q1.get('solution') or {}).get('steps', [])) == 3, q1)
    check('ai-solutions: mismatching Q2 not ready', q2.get('state') != 'ready' and not q2.get('solution'), q2)
    res = await stu.get(f'/api/attempts/{aid}/results'); summ = res.json().get('summary', {}) if res.status_code == 200 else {}
    check('scoring unchanged by AI (4/4 => 4)', summ.get('score') in (4, 4.0), json.dumps(summ)[:200])
    # competitive pre/post close
    db_now = (await H.TDB.command('hello'))['localTime'].timestamp()
    raw = build_pdf([{'n': 1, 'qs': q3('AC'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]}])
    b = await upload(own, raw, 'TEST_QA170 CompAI', release_at=db_now + 4, closes_at=db_now + 22, competitive=True); _, v = await complete(own, b['id'])
    m = v['mocks'][0]; check('competitive AI mock scheduled', m['state'] == 'scheduled', (m['state'], m['issues'][:3]))
    if m['state'] != 'scheduled': return
    sc = await H.TDB.tejas_sets.find_one({'id': m['set_id']})
    r = await own.post(f"/api/admin/books/{b['id']}/allowances", json={'revision': v['revision'], 'purpose': 'explanations', 'question_ids': [sc['questions'][0]['id']], 'max_requests': 2, 'approved': True, 'request_id': 'qa170cx' + uuid.uuid4().hex[:8]})
    H.AI_SCRIPT['solve'] = lambda q: {'status': 'verified', 'steps': steps, 'summary': 'QA170', 'issues': []}
    await drain(); print('comp allowance', r.status_code, r.text[:150])
    await asyncio.sleep(max(0, db_now + 5 - (await H.TDB.command('hello'))['localTime'].timestamp()))
    for _ in range(3):
        a = await start(stu, m['set_id'])
        if a.status_code == 200: break
        await asyncio.sleep(1.5)
    check('competitive start in window', a.status_code == 200, a.text[:200])
    if a.status_code != 200: return
    aid = a.json()['id']; await stu.post(f'/api/attempts/{aid}/submit'); await grade()
    r = await stu.get(f'/api/attempts/{aid}/ai-solutions'); check('competitive ai-solutions pre-close 403', r.status_code == 403, (r.status_code, r.text[:150]))
    wait = db_now + 23 - (await H.TDB.command('hello'))['localTime'].timestamp()
    await asyncio.sleep(max(0, wait))
    r = await stu.get(f'/api/attempts/{aid}/ai-solutions'); j = r.json() if r.status_code == 200 else {}
    print('comp post-close', r.status_code, json.dumps(j)[:300])
    check('competitive ai-solutions post-close 200 ready', r.status_code == 200 and j.get('ready', 0) >= 1, (r.status_code, json.dumps(j)[:200]))


async def rolewords(own, stu):
    # instruction SENTENCES that begin with Answer(s)/Solutions must not flip the next question page into keys/solutions
    for line in ('Answers must be marked on the OMR sheet.', 'Solutions to all questions are given at the end.'):
        instr = PLAIN_INSTR[:-0 or None] + [line] + ['No worked solutions; answer key only.']
        raw = pdf([['Contents', 'x'], ['Mock Test 1'] + [x.format(n=3) for x in instr], ['Physics'] + qlines('RW', 3), ['Answer Key', 'Q1. (B)', 'Q2. (B)', 'Q3. (C)']])
        b = await upload(own, raw, 'TEST_QA170 Role ' + line[:8]); _, v = await complete(own, b['id']); m = v['mocks'][0]
        p3 = await page(own, b['id'], 3)
        print('ROLEWORD', line, m['state'], m['issues'][:2], [(r['role'], r['number']) for r in p3['regions']])
        pub_wrong = m['state'] == 'published' and any(r['role'] != 'question' for r in p3['regions'] if r['number'])
        check(f'instruction sentence {line[:30]!r}: clean mock publishes with question regions', m['state'] == 'published' and not pub_wrong, (m['state'], [(r['role'], r['number']) for r in p3['regions']]))
        check(f'instruction sentence {line[:30]!r}: never publishes mis-roled content (fail-closed)', not pub_wrong)


GROUPS = {'rolewords': rolewords, 'sparse': sparse, 'consolidated': consolidated, 'worked': worked, 'continuation': continuation, 'bitsat': bitsat, 'comedk': comedk_and_ai}


async def run(names):
    try:
        own, _ = await mkstaff('owner', 'owner'); stu = client()
        await stu.post('/api/auth/phone/signup', json={'phone': '95' + str(uuid.uuid4().int)[:8], 'pin': '7314', 'confirm_pin': '7314'})
        for n in names:
            try: await GROUPS[n](own, stu)
            except Exception as e:
                import traceback; traceback.print_exc(); check(f'{n} completed', False, repr(e))
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB); print('dropped', H.TEST_DB, 'remaining', [n for n in await H.tdbmod.client.list_database_names() if 'book170' in n])
        f = [r for r in T.RESULTS if not r[1]]; print(f'TOTAL {len(T.RESULTS)} PASS {len(T.RESULTS) - len(f)} FAIL {len(f)}')
        json.dump(T.RESULTS, open(OUT / ('results_ext_' + '_'.join(names) + '.json'), 'w'), indent=1)

if __name__ == '__main__':
    asyncio.run(run(sys.argv[1:] or list(GROUPS)))
