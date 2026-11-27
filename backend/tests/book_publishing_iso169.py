"""TEST-ONLY iteration 169: adversarial isolated workflow for source-first PDF-to-mock book publishing.
Run: cd /app/backend && python tests/book_publishing_iso169.py   (prints PASS/FAIL lines, drops its isolated DB at end)
"""
import asyncio, hashlib, json, math, sys, time, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import iso_harness_book169 as H  # noqa: E402  (must import first: rebinds DB + mocks storage/AI)
import fitz, httpx, bcrypt  # noqa: E402
from tejas import jobs as J  # noqa: E402
from tejas.book_pdf import inspect  # noqa: E402

_oj = httpx.Response.json
httpx.Response.json = lambda self: (lambda d: d['data'] if isinstance(d, dict) and 'meta' in d and 'data' in d else d)(_oj(self))  # unwrap v1 envelope
OUT = Path('/tmp/book169'); OUT.mkdir(exist_ok=True)
RESULTS = []


def check(name, ok, detail=''):
    RESULTS.append((name, bool(ok), str(detail)[:400]))
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:400]), flush=True)


INSTR = ['JEE Main Instructions', 'Duration: 180 minutes', 'Total Questions: {n}', 'Correct: +4', 'Wrong: -1',
         'Unanswered: 0', 'All questions are compulsory', 'No worked solutions; answer key only.']


def build_pdf(mocks, contents=True, path=None):
    doc = fitz.open()
    if contents:
        p = doc.new_page(); p.insert_text((40, 60), 'Contents', fontsize=14)
        p.insert_text((40, 90), 'This practice book contains labelled synthetic papers with answer keys.', fontsize=10)
    for m in mocks:
        p = doc.new_page(); p.insert_text((40, 60), f"Mock Test {m['n']}", fontsize=14); y = 90
        for line in m.get('instr', INSTR):
            p.insert_text((40, y), line.format(n=len(m['qs'])), fontsize=11); y += 20
        p = doc.new_page(); p.insert_text((40, 60), m.get('subject', 'Physics'), fontsize=13); y = 100
        for num, text, opts in m['qs']:
            p.insert_text((40, y), f'Q{num}. {text}', fontsize=11); y += 20
            for lab, o in zip('ABCD', opts):
                p.insert_text((60, y), f'({lab}) {o}', fontsize=11); y += 18
            y += 22
        p = doc.new_page(); p.insert_text((40, 60), 'Answer Key', fontsize=13); y = 100
        for num, ans in m['keys']:
            p.insert_text((40, y), f'Q{num}. ({ans})', fontsize=11); y += 20
    raw = doc.tobytes(); doc.close()
    if path: Path(path).write_bytes(raw)
    return raw


def q3(tag):
    return [(1, f'{tag}: a ball falls 20 m. Find time.', ['1 s', '2 s', '3 s', '4 s']),
            (2, f'{tag}: unit of force is', ['joule', 'newton', 'watt', 'pascal']),
            (3, f'{tag}: speed of light order', ['1e3', '1e5', '1e8', '1e10'])]


async def drain(limit=200):
    n = 0
    while n < limit:
        j = await H.TDB.tejas_jobs.find_one({'kind': 'book_step', 'status': 'queued'}, sort=[('created_at', 1)])
        if not j: j = await H.TDB.tejas_jobs.find_one({'kind': 'book_step', 'status': 'queued'})
        if not j: break
        await J.run_job(j['id']); n += 1
    return n


async def mkstaff(role, tag):
    email = f'qa169-{tag}-{uuid.uuid4().hex[:6]}@example.com'; pw = 'Qa169!' + uuid.uuid4().hex[:10]
    uid = str(uuid.uuid4())
    await H.TDB.tejas_users.insert_one({'id': uid, 'name': 'QA169 ' + tag, 'email': email, 'role': role, 'credential_generation': 0,
                                  'password_hash': bcrypt.hashpw(pw.encode(), bcrypt.gensalt(4)).decode(), 'created_at': time.time()})
    c = client(); r = await c.post('/api/auth/login', json={'email': email, 'password': pw})
    assert r.status_code == 200, r.text
    return c, uid


def client():
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=H.app), base_url='https://rank-predictor-11--5rzs66bc.preview.emergentagent.com', timeout=120,
                             headers={'Origin': 'https://rank-predictor-11--5rzs66bc.preview.emergentagent.com'})


async def upload(c, raw, title, edition='', parts=None, **extra):
    sha = hashlib.sha256(raw).hexdigest()
    r = await c.post('/api/admin/books', json={'filename': title + '.pdf', 'title': title, 'sha256': sha, 'size': len(raw),
                                              'edition': edition, 'rights_confirmed': True, **extra})
    assert r.status_code == 200, r.text
    b = r.json()
    if 'chunk_size' not in b: print('CREATE RESP', r.status_code, r.text[:600])
    ch = b['chunk_size']; total = math.ceil(len(raw) / ch)
    for n in (range(total) if parts is None else parts):
        pr = await c.put(f"/api/admin/books/{b['id']}/parts/{n}", content=raw[n * ch:(n + 1) * ch], headers={'content-type': 'application/octet-stream'})
        assert pr.status_code == 200, pr.text
    return b


async def complete(c, bid):
    r = await c.post(f'/api/admin/books/{bid}/complete'); await drain()
    return r, (await c.get(f'/api/admin/books/{bid}')).json()


def leak(text):
    return 'jeelive/books' in text or 'source_path' in text


async def main():
    print('DB', H.TEST_DB, 'patched', len(H.PATCHED), 'leftover', H.leftover_real_handles())
    check('no customer DB handles remain', not H.leftover_real_handles(), H.leftover_real_handles())
    own, own_id = await mkstaff('owner', 'owner')
    own2, _ = await mkstaff('owner', 'owner2')
    rev, _ = await mkstaff('reviewer', 'rev')
    stu = client(); phone = '98' + str(uuid.uuid4().int)[:8]
    r = await stu.post('/api/auth/phone/signup', json={'phone': phone, 'pin': '4826', 'confirm_pin': '4826'})
    check('student phone signup (isolated)', r.status_code == 200, r.text)
    anon = client()
    # ---- auth on book routes
    for who, cl, exp in (('anon', anon, 401), ('student', stu, 403), ('reviewer', rev, 403)):
        r = await cl.get('/api/admin/books'); check(f'{who} denied book list ({exp})', r.status_code == exp, r.status_code)
        r = await cl.post('/api/admin/books', json={}); check(f'{who} denied book create', r.status_code in (401, 403, 422) and r.status_code != 200, r.status_code)
    # ---- fixture: 3 mocks; mock 3 has conflicting key (two keys for Q2)
    mocks = [{'n': 1, 'qs': q3('M1'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]},
             {'n': 2, 'qs': q3('M2'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]},
             {'n': 3, 'qs': q3('M3'), 'keys': [(1, 'B'), (2, 'B'), (2, 'A'), (3, 'C')]}]
    raw = build_pdf(mocks, path=OUT / 'book_A_3mocks.pdf')
    sha = hashlib.sha256(raw).hexdigest()
    # ---- upload contract
    b = await upload(own, raw, 'TEST_QA169 Book A', parts=[])
    bid = b['id']
    check('create returns no storage path', not leak(json.dumps(b)), b)
    r = await own.put(f'/api/admin/books/{bid}/parts/0', content=raw[:10], headers={'content-type': 'text/plain'})
    check('part wrong content-type 415', r.status_code == 415, r.status_code)
    r = await own.put(f'/api/admin/books/{bid}/parts/99', content=raw[:10], headers={'content-type': 'application/octet-stream'})
    check('part out of range 422', r.status_code == 422, r.status_code)
    r = await own.put(f'/api/admin/books/{bid}/parts/0', content=raw[:10], headers={'content-type': 'application/octet-stream'})
    check('part incomplete 422', r.status_code == 422 and len(raw) > 10, r.status_code)
    r = await own.post(f'/api/admin/books/{bid}/complete')
    check('complete with missing parts 409', r.status_code == 409, r.status_code)
    r = await own2.get(f'/api/admin/books/{bid}'); check('other owner GET 404', r.status_code == 404, r.status_code)
    r = await own2.put(f'/api/admin/books/{bid}/parts/0', content=raw, headers={'content-type': 'application/octet-stream'})
    check('other owner part 404', r.status_code == 404, r.status_code)
    # resume via re-create (dedupe)
    b2 = await upload(own, raw, 'TEST_QA169 Book A')
    check('same pdf+edition dedupes to same id', b2['id'] == bid, (b2['id'], bid))
    r = await own.put(f'/api/admin/books/{bid}/parts/0', content=bytes(reversed(raw))[:len(raw)] if len(raw) <= b['chunk_size'] else raw[:b['chunk_size']][::-1], headers={'content-type': 'application/octet-stream'})
    check('different bytes for stored part 409 (immutable)', r.status_code == 409, r.status_code)
    r = await own.put(f'/api/admin/books/{bid}/parts/0', content=raw[:b['chunk_size']], headers={'content-type': 'application/octet-stream'})
    check('identical part retry idempotent 200', r.status_code == 200, r.status_code)
    other_edition = await own.post('/api/admin/books', json={'filename': 'a.pdf', 'title': 't', 'sha256': sha, 'size': len(raw), 'edition': 'v2', 'rights_confirmed': True})
    check('different edition => different import id', other_edition.json()['id'] != bid)
    r = await own.post('/api/admin/books', json={'filename': 'a.pdf', 'title': 't', 'sha256': sha, 'size': 50 * 1024 * 1024 + 1, 'rights_confirmed': True})
    check('size > 50MB rejected 422', r.status_code == 422, r.status_code)
    r = await own.post('/api/admin/books', json={'filename': 'a.pdf', 'title': 't', 'sha256': sha, 'size': 10, 'rights_confirmed': False})
    check('rights not confirmed rejected 422', r.status_code == 422, r.status_code)
    r = await own.post('/api/admin/books', json={'filename': 'a.pdf', 'title': 't', 'sha256': sha, 'size': 10, 'rights_confirmed': True, 'release_at': time.time() - 60})
    check('past release_at rejected 422', r.status_code == 422, r.status_code)
    # ---- process
    t0 = time.time(); r, view = await complete(own, bid)
    print('processed in %.1fs state=%s msg=%s' % (time.time() - t0, view['state'], view['message']))
    check('complete 200', r.status_code == 200, r.text)
    check('all pages read', view['read_pages'] == view['pages'] == 10, (view['read_pages'], view['pages']))
    check('original stored in mocked storage', any(k.endswith(bid + '/original.pdf') for k in H.STORE), list(H.STORE)[:3])
    check('no paid AI during automatic processing', H.AI_CALLS == {'ask': 0, 'solve': 0}, H.AI_CALLS)
    check('book view hides storage path', not leak(json.dumps(view)))
    states = {m['label']: (m['state'], m['issues']) for m in view['mocks']}
    print('MOCK STATES', json.dumps(states, indent=1)[:3000])
    check('3 mocks detected', len(states) == 3, list(states))
    check('Mock 1 clean => published', states.get('Mock 1', ('',))[0] == 'published', states.get('Mock 1'))
    check('Mock 2 clean (per-mock key layout) => published', states.get('Mock 2', ('',))[0] == 'published', states.get('Mock 2'))
    check('Mock 3 conflicting key => held', states.get('Mock 3', ('',))[0] == 'held', states.get('Mock 3'))
    check('Mock 3 issue cites conflict', any('conflict' in i.lower() for i in states.get('Mock 3', ('', []))[1]), states.get('Mock 3'))
    published = [m for m in view['mocks'] if m['state'] == 'published']
    # ---- page image + page detail (owner only)
    r = await own.get(f'/api/admin/books/{bid}/pages/3/image')
    if r.status_code == 200: (OUT / 'page3_questions.png').write_bytes(r.content)
    check('owner page image 200 png', r.status_code == 200 and r.content[:4] == b'\x89PNG', r.status_code)
    r = await rev.get(f'/api/admin/books/{bid}/pages/3/image'); check('reviewer page image 403', r.status_code == 403, r.status_code)
    r = await own2.get(f'/api/admin/books/{bid}/pages/3/image'); check('other owner page image 404', r.status_code == 404, r.status_code)
    r = await own.get(f'/api/admin/books/{bid}/pages'); check('page list 200 (10)', r.status_code == 200 and len(r.json()['items']) == 10, r.text[:200])
    pd = (await own.get(f'/api/admin/books/{bid}/pages/3')).json()
    print('PAGE3 REGIONS', [(x['role'], x['mock'], x['subject'], x['number'], x['option_labels'], x['checked'], [round(v, 3) for v in x['rect']]) for x in pd['regions']])
    if not published:
        print('NO PUBLISHED MOCK; stopping downstream canonical tests'); return
    pm = published[0]; md = (await own.get(f"/api/admin/books/{bid}/mocks/{pm['id']}")).json()
    qid = md['questions'][0]['id']
    r = await own.get(f"/api/admin/books/{bid}/mocks/{pm['id']}/questions/{qid}/asset/question/0")
    if r.status_code == 200: (OUT / 'mock1_q1_question_crop.png').write_bytes(r.content)
    check('owner preview question crop 200', r.status_code == 200, r.status_code)
    r = await own.get(f"/api/admin/books/{bid}/mocks/{pm['id']}/questions/{qid}/asset/solution/0")
    if r.status_code == 200: (OUT / 'mock1_q1_key_crop.png').write_bytes(r.content)
    check('owner preview key crop 200', r.status_code == 200, r.status_code)
    sid = pm['set_id']; s = await H.TDB.tejas_sets.find_one({'id': sid}) or await H.TDB.tejas_sets.find_one({'id': sid})
    check('published set exists status published', s and s['status'] == 'published', s and s.get('status'))
    if s:
        print('SET answers', [(q['original_number'], q['answer'], q['solution_kind'], list(q['options'])) for q in s['questions']], 'rules', s['rules'])
        check('keys preserved from book (B,B,C)', [q['answer'] for q in s['questions']] == ['B', 'B', 'C'], [q['answer'] for q in s['questions']])
    fids = s['file_ids'] if s else []
    # ---- legacy studio/file exposure to reviewer
    for path in [f'/api/studio/sets/{sid}', f'/api/studio/files/{fids[0]}/download' if fids else None, f'/api/studio/files/{fids[0]}/page/1' if fids else None,
                 f"/api/studio/sets/{sid}/questions/{s['questions'][0]['id']}/asset/question/0" if s else None]:
        if not path: continue
        r = await rev.get(path)
        check(f'reviewer legacy {path.split("/api")[1][:40]} blocked (403/404/503-hold)', r.status_code in (403, 404, 503), (r.status_code, r.text[:150]))
        if r.status_code == 200: check('reviewer legacy response no private path', not leak(r.text), r.text[:200])
    # latent exposure: release the SOURCE_PARSE capability hold for legacy staff read routes
    from tejas import safety as C
    held = C.held; C.held = lambda *a, **k: False
    try:
        q0 = s['questions'][0]
        for path in [f"/api/studio/sets/{sid}/questions/{q0['id']}/asset/question/0", f"/api/studio/sets/{sid}/questions/{q0['id']}/asset/solution/0",
                     f'/api/studio/files/{fids[0]}/page/1', f'/api/studio/files/{fids[0]}/text/1']:
            for who, cl in (('reviewer', rev), ('other-owner', own2)):
                try: r = await cl.get(path)
                except Exception as e:
                    print(f'[cap released] {who} {path.split("/")[-3:]} -> unhandled {e!r} (HTTP 500 in server; no book guard)'); continue
                if r.status_code == 200 and r.content[:4] == b'\x89PNG': (OUT / f'LEAK_{who}_{path.split("/")[-2]}.png').write_bytes(r.content)
                check(f'[cap released] {who} legacy {"/".join(path.split("/")[-3:])} blocked', r.status_code in (403, 404), (r.status_code, r.text[:120]))
    finally:
        C.held = held
    # ---- student series + canonical attempt
    r = await stu.get('/api/book-series'); check('student series lists book', r.status_code == 200 and any(i['id'] == bid for i in r.json()['items']), r.text[:300])
    r = await stu.get(f'/api/book-series/{bid}'); check('student series detail', r.status_code == 200 and not leak(r.text), r.text[:300])
    check('series detail excludes answers/source', r.status_code == 200 and '"answer"' not in r.text and 'source_evidence' not in r.text, r.text[:300])
    r = await anon.get('/api/book-series'); check('anon series 401', r.status_code == 401, r.status_code)
    r = await stu.get(f'/api/admin/books/{bid}/pages/3/image'); check('student original page 403', r.status_code == 403, r.status_code)
    r = await stu.post(f'/api/sets/{sid}/preflight', json={}); check('preflight 200', r.status_code == 200, r.text[:300])
    r = await stu.post(f'/api/sets/{sid}/start', json={'start_key': 'qa169start' + uuid.uuid4().hex[:8], 'device_checked': True})
    check('start 200', r.status_code == 200, r.text[:300])
    if r.status_code != 200: return
    att = r.json(); aid = att['id']
    i = r.text.find('"answer"'); print('ATTEMPT "answer" context:', r.text[max(0, i - 150):i + 80] if i >= 0 else None)
    print('ATTEMPT leak flags', leak(r.text), 'source_evidence' in r.text, [k for k in ('jeelive/books', 'source_path') if k in r.text])
    i = r.text.find('source_evidence'); print('SRC_EVIDENCE context:', r.text[max(0, i - 300):i + 400])
    print('printed_answer in active attempt:', 'printed_answer' in r.text)
    aq = r.json()['questions'][0]; print('ATTEMPT Q KEYS', sorted(aq))
    check('attempt view no key/solution/source path', not leak(r.text) and 'printed_answer' not in r.text and not any(k in aq for k in ('answer', 'solution', 's_refs', 'ai_solution', 'source_evidence')), sorted(aq))
    qids = [q['id'] for q in att['questions']]
    r = await stu.get(f'/api/attempts/{aid}/questions/{qids[0]}/asset/question/0')
    if r.status_code == 200: (OUT / 'student_q1_crop.png').write_bytes(r.content)
    check('active question crop 200', r.status_code == 200 and r.content[:4] == b'\x89PNG', r.status_code)
    r = await stu.get(f'/api/attempts/{aid}/questions/{qids[0]}/asset/solution/0'); check('active solution crop 403', r.status_code == 403, r.status_code)
    for i, (q, v) in enumerate(zip(qids, ['B', 'A', 'C'])):
        r = await stu.put(f'/api/attempts/{aid}/answers/{q}', json={'value': v, 'revision': 1, 'request_id': 'qa169ans' + uuid.uuid4().hex[:8]})
        if i == 0: check('save answer 200', r.status_code == 200, r.text[:200])
    r = await stu.post(f'/api/attempts/{aid}/submit'); check('submit 200/202', r.status_code in (200, 202), (r.status_code, r.text[:200]))
    await asyncio.sleep(0.5)
    for _ in range(5):
        j = await H.TDB.tejas_jobs.find_one({'kind': 'grade', 'status': 'queued'})
        if not j: break
        await J.run_job(j['id'])
    res = await stu.get(f'/api/attempts/{aid}/results'); check('results 200', res.status_code == 200, res.text[:200])
    res1 = res.json() if res.status_code == 200 else {}
    score1 = json.dumps(res1.get('summary', res1.get('score', '')), sort_keys=True)
    print('RESULT summary', score1[:300])
    check('results no private storage path', not leak(res.text))
    r = await stu.get(f'/api/attempts/{aid}/questions/{qids[0]}/asset/solution/0')
    if r.status_code == 200: (OUT / 'student_q1_key_after_submit.png').write_bytes(r.content)
    check('post-submit key crop 200', r.status_code == 200, r.status_code)
    # ---- published frozen: repair/rules rejected; new_version
    page = (await own.get(f'/api/admin/books/{bid}/pages/3')).json()
    body = {'revision': page['revision'], 'classification': page['classification'], 'regions': page['regions'], 'issues': [], 'note': 'QA169 attempt edit published'}
    r = await own.put(f'/api/admin/books/{bid}/pages/3', json=body); check('repair published page 409', r.status_code == 409, r.text[:200])
    v = (await own.get(f'/api/admin/books/{bid}')).json()
    r = await own.post(f'/api/admin/books/{bid}/control', json={'revision': v['revision'], 'action': 'new_version', 'mock_id': pm['id'], 'reason': 'QA169 corrected key'})
    check('new_version 200', r.status_code == 200, r.text[:200])
    page = (await own.get(f'/api/admin/books/{bid}/pages/4')).json()  # Mock1 key page
    regs = page['regions']
    for x in regs:
        if x['role'] == 'key' and x['number'] == 2: x['answer'] = 'A'
    r = await own.put(f'/api/admin/books/{bid}/pages/4', json={'revision': page['revision'], 'classification': page['classification'], 'regions': regs, 'issues': [], 'note': 'QA169 erratum Q2 key A'})
    check('repair after new_version 200', r.status_code == 200, r.text[:200])
    v = (await own.get(f'/api/admin/books/{bid}')).json()
    r = await own.post(f'/api/admin/books/{bid}/control', json={'revision': v['revision'], 'action': 'resume'}); await drain()
    check('resume 200', r.status_code == 200, r.text[:200])
    v = (await own.get(f'/api/admin/books/{bid}')).json(); m1 = next(m for m in v['mocks'] if m['id'] == pm['id'])
    print('after new_version', m1['state'], m1['generation'], m1['set_id'], m1['history'], m1['issues'][:3])
    check('v2 published new set id, old in history', m1['state'] == 'published' and m1['set_id'] != sid and sid in m1['history'], (m1['state'], m1['issues'][:3]))
    old = await H.TDB.tejas_sets.find_one({'id': sid}); check('old set withdrawn', old['status'] == 'withdrawn', old['status'])
    check('old set keys unchanged', [q['answer'] for q in old['questions']] == ['B', 'B', 'C'])
    new = await H.TDB.tejas_sets.find_one({'id': m1['set_id']})
    if new: check('v2 key corrected', [q['answer'] for q in new['questions']] == ['B', 'A', 'C'], [q['answer'] for q in new['questions']])
    res = await stu.get(f'/api/attempts/{aid}/results')
    check('old attempt result unchanged after v2', res.status_code == 200 and json.dumps(res.json().get('summary', res.json().get('score', '')), sort_keys=True) == score1, res.text[:200])
    r = await stu.get(f'/api/attempts/{aid}/questions/{qids[0]}/asset/question/0'); check('old attempt crop still served', r.status_code == 200, r.status_code)
    n_sets = await H.TDB.tejas_sets.count_documents({'book_import_id': bid})
    v = (await own.get(f'/api/admin/books/{bid}')).json()
    await own.post(f'/api/admin/books/{bid}/control', json={'revision': v['revision'], 'action': 'retry'}); await drain()
    check('retry does not duplicate sets', await H.TDB.tejas_sets.count_documents({'book_import_id': bid}) == n_sets, n_sets)
    # ---- AI explanations (mocked)
    newq = new['questions'] if new else []
    H.AI_SCRIPT['solve'] = lambda q: {'status': 'verified', 'steps': ['QA169 mocked step'], 'summary': 'mock', 'issues': []} if q['original_number'] == 1 else {'status': 'disagreed', 'steps': [], 'summary': '', 'issues': ['answer differs']}
    v = (await own.get(f'/api/admin/books/{bid}')).json()
    r = await own.post(f'/api/admin/books/{bid}/allowances', json={'revision': v['revision'], 'purpose': 'explanations', 'question_ids': [newq[0]['id'], newq[1]['id']], 'max_requests': 4, 'approved': True, 'request_id': 'qa169expl01'})
    check('explanations allowance 200', r.status_code == 200, r.text[:300]); await drain()
    a = await H.TDB.tejas_book_allowances.find_one({'book_id': bid, 'purpose': 'explanations'})
    print('allowance', a and {k: a[k] for k in ('state', 'used', 'cursor', 'error', 'results')}, 'calls', H.AI_CALLS)
    check('explanations used 4 (2-pass x2) and complete', a and a['used'] == 4 and a['state'] == 'complete', a and (a['used'], a['state'], a['error']))
    after = await H.TDB.tejas_sets.find_one({'id': m1['set_id']})
    if after:
        check('only verified Q1 got ai_solution', bool(after['questions'][0].get('ai_solution')) and not after['questions'][1].get('ai_solution'))
        check('keys unchanged after AI', [q['answer'] for q in after['questions']] == ['B', 'A', 'C'])
    v = (await own.get(f'/api/admin/books/{bid}')).json()
    r = await own.post(f'/api/admin/books/{bid}/allowances', json={'revision': v['revision'], 'purpose': 'explanations', 'question_ids': [newq[2]['id']], 'max_requests': 1, 'approved': True, 'request_id': 'qa169expl02'})
    await drain(); a2 = await H.TDB.tejas_book_allowances.find_one({'_id': {'$ne': a['_id']}, 'book_id': bid, 'purpose': 'explanations'})
    check('allowance below 2-pass cost => budget_required, no call', a2 and a2['state'] == 'budget_required' and H.AI_CALLS['solve'] == 2, a2 and (a2['state'], H.AI_CALLS))
    # ---- pause/remove
    v = (await own.get(f'/api/admin/books/{bid}')).json()
    r = await own.post(f'/api/admin/books/{bid}/control', json={'revision': v['revision'], 'action': 'remove'})
    check('remove 200', r.status_code == 200, r.text[:200])
    r = await own.get(f'/api/admin/books/{bid}'); check('removed book 404', r.status_code == 404, r.status_code)
    res = await stu.get(f'/api/attempts/{aid}/results'); check('history retained after remove', res.status_code == 200, res.status_code)
    r = await stu.get(f'/api/attempts/{aid}/questions/{qids[0]}/asset/question/0'); check('history crop retained after remove', r.status_code == 200, r.status_code)
    r = await stu.get(f'/api/book-series/{bid}'); check('removed series 404 for student', r.status_code == 404, r.status_code)
    # ---- revoked owner cannot process
    raw2 = build_pdf([{'n': 1, 'qs': q3('R1'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]}], path=OUT / 'book_R.pdf')
    b = await upload(own2, raw2, 'TEST_QA169 Revoke')
    o2 = await H.TDB.tejas_users.find_one({'role': 'owner', 'email': {'$regex': 'owner2'}})
    await H.TDB.tejas_users.update_one({'id': o2['id']}, {'$set': {'role': 'reviewer'}})
    r = await own2.post(f"/api/admin/books/{b['id']}/complete"); check('revoked owner complete denied', r.status_code == 403, r.status_code)
    await H.TDB.tejas_users.update_one({'id': o2['id']}, {'$set': {'role': 'owner'}})
    J.INLINE_JOBS = False; await own2.post(f"/api/admin/books/{b['id']}/complete"); J.INLINE_JOBS = True
    await H.TDB.tejas_users.update_one({'id': o2['id']}, {'$set': {'role': 'reviewer'}}); await drain()
    bk = await H.TDB.tejas_books.find_one({'_id': b['id']})
    check('worker refuses to publish for revoked owner', await H.TDB.tejas_sets.count_documents({'book_import_id': b['id'], 'status': 'published'}) == 0, bk['state'])
    print('revoked book state', bk['state'], bk['payload'].get('message'))


async def limits():
    d = fitz.open()
    for _ in range(1001): d.new_page(width=200, height=200)
    raw1001 = d.tobytes(); d.delete_page(1000); raw1000 = d.tobytes(); d.close()
    t = time.time(); info = inspect(raw1000); check('1000-page inspect ok', info['pages'] == 1000, info)
    print('1000-page inspect %.1fs scanned_sample=%s' % (time.time() - t, info.get('scanned_sample')))
    try: inspect(raw1001); check('1001-page rejected', False, 'accepted')
    except ValueError as e: check('1001-page rejected', '1,000' in str(e), e)


async def run():
    try:
        await limits(); await main()
    except Exception as e:
        import traceback; traceback.print_exc(); check('harness completed without exception', False, repr(e))
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB, 'remaining', [n for n in await H.tdbmod.client.list_database_names() if 'book169' in n])
        f = [r for r in RESULTS if not r[1]]
        print(f'TOTAL {len(RESULTS)} PASS {len(RESULTS) - len(f)} FAIL {len(f)}')
        json.dump(RESULTS, open(OUT / 'results.json', 'w'), indent=1)

if __name__ == '__main__':
    asyncio.run(run())
