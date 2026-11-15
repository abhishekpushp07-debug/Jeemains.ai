"""TEST-ONLY iteration 173: organised Super Admin structure (exams -> sections -> tests) + book destination/publish_ready.
Isolated disposable DB via iso_harness_book170 (storage + AI mocked, real PDF worker). Customer DB never written.
Run: cd /app/backend && python tests/structure_iso173.py   (prints PASS/FAIL, drops its DB)
"""
import asyncio, hashlib, json, sys, time, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import book_publishing_iso170 as T  # noqa: E402  (imports harness first)
from book_publishing_iso170 import H, mkstaff, client, build_pdf, q3, upload, complete, drain, check, RESULTS  # noqa: E402
from tejas import structure  # noqa: E402

RULES = {'minutes': 10, 'correct': 4, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'}
SETS = H.TDB.tejas_sets


def qs(tag, n=3):
    return [{'id': str(uuid.uuid4()), 'number': i + 1, 'type': 'mcq', 'subject': 'Physics', 'section': 'A', 'options': {'A': 'a', 'B': 'b', 'C': 'c', 'D': 'd'},
             'answer': 'A', 'text': f'{tag} q{i}', 'solution': f'{tag} sol'} for i in range(n)]


async def mkset(tag, **kw):
    sid = 'TEST_S173_' + tag + '_' + uuid.uuid4().hex[:6]
    t = time.time()
    doc = {'id': sid, 'status': 'published', 'audience': 'all', 'title': f'TEST_{tag}', 'version': 1, 'revision': 1, 'created_at': t,
           'questions': qs(tag), 'rules': dict(RULES), **kw}
    await SETS.insert_one(dict(doc))
    return sid


def ids(resp):
    d = resp.json()
    return [x['id'] for x in d.get('items', [])]


async def start(c, sid):
    await c.post(f'/api/sets/{sid}/preflight', json={})
    return await c.post(f'/api/sets/{sid}/start', json={'start_key': 'k173-' + uuid.uuid4().hex[:12], 'device_checked': True})


async def main():
    check('no customer DB handles', not H.leftover_real_handles(), H.leftover_real_handles())
    check('structure collections patched', structure.exams.database.name == H.TEST_DB and structure.sections.database.name == H.TEST_DB)
    await structure.seed()
    own, _ = await mkstaff('owner', 'own')
    rev, _ = await mkstaff('reviewer', 'rev')
    stu = client(); phone = '97' + str(uuid.uuid4().int)[:8]
    r = await stu.post('/api/auth/phone/signup', json={'phone': phone, 'pin': '4826', 'confirm_pin': '4826'})
    check('student signup', r.status_code == 200, r.text)
    # fixtures
    pyq = await mkset('PYQ', exam='JEE Main', test_kind='pyq', pyq_date='2024-01-27')
    bm1 = await mkset('BM1', exam='BITSAT', test_kind='mock', mock_number=1)
    bm2 = await mkset('BM2', exam='BITSAT', test_kind='mock', mock_number=2)
    t = time.time()
    jch = await mkset('JCH', exam='JEE Main', test_kind='chapter', chapter_book_id='TEST_CB173', chapter_subject='Physics', chapter_number=1,
                      live_enabled=True, start_at=t - 3600, end_at=t + 86400 * 30)
    jpr = await mkset('JPRAC', exam='JEE Main')  # practice, no kind -> unplaced
    # ---- exams
    r = await stu.get('/api/catalog/exams'); slugs = [e['slug'] for e in r.json()['items']]
    check('student sees 3 built-in exams', slugs == ['jee-main', 'bitsat', 'comedk'], slugs)
    r = await own.post('/api/admin/catalog/exams', json={'name': 'TEST NEET', 'short': 'TNEET', 'subjects': ['Physics', 'Biology'], 'color': 'teal'})
    check('create exam 200 hidden', r.status_code == 200 and r.json()['shown'] is False, r.text)
    slug = r.json().get('slug'); print('custom slug', slug)
    r = await own.post('/api/admin/catalog/exams', json={'name': 'test neet', 'short': 'X', 'subjects': ['P'], 'color': 'teal'})
    check('duplicate exam name 409', r.status_code == 409, r.status_code)
    r = await own.post('/api/admin/catalog/exams', json={'name': 'jee main', 'short': 'X', 'subjects': ['P'], 'color': 'teal'})
    check('duplicate builtin name 409', r.status_code == 409, r.status_code)
    r = await own.post('/api/admin/catalog/exams', json={'name': 'TEST Bad', 'short': 'X', 'subjects': ['P'], 'color': 'black'})
    check('bad colour 422', r.status_code == 422, r.status_code)
    check('student does not see hidden exam', slug not in [e['slug'] for e in (await stu.get('/api/catalog/exams')).json()['items']])
    check('owner sees hidden exam', slug in [e['slug'] for e in (await own.get('/api/catalog/exams')).json()['items']])
    r = await own.patch('/api/admin/catalog/exams/bitsat', json={'shown': False}); check('builtin exam PATCH 422', r.status_code == 422, r.status_code)
    r = await stu.get(f'/api/catalog/exams/{slug}'); check('hidden exam detail student 404', r.status_code == 404, r.status_code)
    r = await own.get(f'/api/catalog/exams/{slug}'); check('hidden exam detail owner 200', r.status_code == 200, r.status_code)
    # ---- built-in sections
    r = await stu.get('/api/catalog/exams/jee-main'); secs = [s['slug'] for s in r.json()['sections']]
    check('jee-main student sections pyq,chapters (no live mocks)', secs == ['pyq', 'chapters'], secs)
    r = await stu.get('/api/catalog/exams/bitsat'); secs = [s['slug'] for s in r.json()['sections']]
    check('bitsat sections mocks only (no chapters live)', secs == ['mocks'], r.json()['sections'])
    r = await stu.get('/api/catalog/exams/comedk'); check('comedk no sections', r.status_code == 200 and r.json()['sections'] == [], r.text[:200])
    # ---- sections
    r = await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'TEST Full Mocks', 'description': 'one line', 'layout': 'list'})
    check('create custom list section', r.status_code == 200 and r.json()['layout'] == 'list', r.text); nsec = r.json()['id']
    r = await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'TEST Chapters', 'layout': 'chapters'})
    check('create custom chapters section', r.status_code == 200, r.text); nch = r.json()['id']
    r = await own.post('/api/admin/catalog/exams/bitsat/sections', json={'name': 'TEST Extra Mocks', 'description': 'd', 'layout': 'list'})
    check('create section in builtin exam', r.status_code == 200, r.text); bx = r.json()['id']; bxslug = r.json()['slug']
    r = await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Results', 'layout': 'list'})
    check('section named Results gets non-colliding slug', r.status_code == 200 and r.json()['slug'] != 'results', r.json().get('slug')); rsec = r.json()['id']
    r = await own.post('/api/admin/catalog/exams/bitsat/sections', json={'name': 'TEST X', 'layout': 'grid'}); check('bad layout 422', r.status_code == 422, r.status_code)
    r = await own.patch(f'/api/admin/catalog/sections/{nsec}', json={'name': 'TEST Full Mocks 2', 'description': 'new'})
    check('rename section', r.status_code == 200 and r.json()['name'] == 'TEST Full Mocks 2', r.text)
    r = await own.post('/api/admin/catalog/exams/bitsat/sections/order', json={'ids': ['bitsat:mocks', bx]})
    check('partial section order 409', r.status_code == 409, r.status_code)
    r = await own.post('/api/admin/catalog/exams/bitsat/sections/order', json={'ids': [bx, 'bitsat:chapters', 'bitsat:mocks']})
    check('full section order 200', r.status_code == 200, r.text)
    # ---- legacy placement + catalogue
    for q in ('section=mocks', 'kind=mocks'):
        r = await stu.get(f'/api/exam-navigation/bitsat/catalogue?{q}'); d = r.json()
        got = [x['id'] for x in d.get('items', [])]
        check(f'bitsat catalogue ?{q} lists legacy mocks', r.status_code == 200 and set(got) == {bm1, bm2}, (r.status_code, got, str(d)[:200]))
        check(f'catalogue ?{q} has section.layout', (d.get('section') or {}).get('layout') == 'list', d.get('section'))
    r = await stu.get('/api/exam-navigation/jee-main/catalogue?kind=chapters'); got = [x['id'] for x in r.json().get('items', [])]
    check('jee chapters legacy placement', jch in got and pyq not in got and jpr not in got, got)
    r = await stu.get('/api/exam-navigation/jee-main/catalogue?section=pyq'); got = [x['id'] for x in r.json().get('items', [])]
    check('jee pyq section lists pyq', got == [pyq], (r.status_code, got))
    r = await stu.get('/api/exam-navigation/jee-main/catalogue?section=mocks'); check('jee mocks section empty', r.status_code == 200 and r.json()['items'] == [], r.text[:200])
    # ---- admin section tests / order
    r = await own.get('/api/admin/catalog/sections/bitsat:mocks/tests'); items = r.json().get('items', [])
    check('admin section tests list w/ state live', r.status_code == 200 and {x['id'] for x in items} == {bm1, bm2} and all(x['state'] == 'live' for x in items), [(x['id'], x['state']) for x in items])
    r = await own.post('/api/admin/catalog/sections/bitsat:mocks/order', json={'ids': [bm2]}); check('partial test order 409', r.status_code == 409, r.status_code)
    r = await own.post('/api/admin/catalog/sections/bitsat:mocks/order', json={'ids': [bm2, bm1]}); check('test order 200', r.status_code == 200, r.text)
    got = ids(await stu.get('/api/exam-navigation/bitsat/catalogue?section=mocks'))
    check('student catalogue follows owner order', got == [bm2, bm1], got)
    # rename
    r = await own.patch(f'/api/admin/catalog/tests/{bm1}', json={'title': 'Mock Test 07'}); check('rename test', r.status_code == 200 and r.json()['title'] == 'Mock Test 07', r.text)
    r = await stu.get(f'/api/sets/{bm1}'); check('display_title in /api/sets/{id}', r.json().get('title') == 'Mock Test 07', r.json().get('title'))
    rows = (await stu.get('/api/exam-navigation/bitsat/catalogue?section=mocks')).json()['items']
    check('display_title in catalogue', any(x['id'] == bm1 and x['title'] == 'Mock Test 07' for x in rows), [x['title'] for x in rows])
    r = await stu.get(f'/api/my/sets/{bm1}'); check('my/sets has catalog_path', r.json().get('catalog_path') == '/exams/bitsat/mocks', r.json().get('catalog_path'))
    # attempt then unlive
    r = await start(stu, bm1); check('student start bm1', r.status_code == 200, r.text[:300]); aid = r.json().get('id')
    nattempts = await H.TDB.tejas_attempts.count_documents({'set_id': bm1})
    r = await own.patch(f'/api/admin/catalog/tests/{bm1}', json={'live': False}); check('unlive 200 state unlive', r.status_code == 200 and r.json()['state'] == 'unlive', r.text)
    got = ids(await stu.get('/api/exam-navigation/bitsat/catalogue?section=mocks')); check('unlive gone from catalogue', bm1 not in got, got)
    check('unlive /api/sets/{id} 404', (await stu.get(f'/api/sets/{bm1}')).status_code == 404)
    check('unlive /api/my/sets/{id} 404', (await stu.get(f'/api/my/sets/{bm1}')).status_code == 404)
    r = await start(stu, bm1); print('unlive resume by same student (active attempt) ->', r.status_code)
    stu2 = client(); await stu2.post('/api/auth/phone/signup', json={'phone': '96' + str(uuid.uuid4().int)[:8], 'pin': '4826', 'confirm_pin': '4826'})
    check('unlive NEW start (other student) 404', (await start(stu2, bm1)).status_code == 404)
    check('unlive not in /api/sets list', bm1 not in ids(await stu.get('/api/sets?q=TEST_BM1')))
    r = await stu.get(f'/api/attempts/{aid}'); check('existing attempt still readable', r.status_code == 200, r.status_code)
    r = await own.patch(f'/api/admin/catalog/tests/{bm1}', json={'live': True}); check('live again', r.status_code == 200 and r.json()['state'] == 'live', r.text)
    check('restored in catalogue', bm1 in ids(await stu.get('/api/exam-navigation/bitsat/catalogue?section=mocks')))
    # move
    r = await own.patch(f'/api/admin/catalog/tests/{bm1}', json={'section_id': bx}); check('move within exam 200', r.status_code == 200, r.text)
    got = ids(await stu.get(f'/api/exam-navigation/bitsat/catalogue?section={bxslug}')); check('moved test in new section', got == [bm1], got)
    check('moved test gone from old section', bm1 not in ids(await stu.get('/api/exam-navigation/bitsat/catalogue?section=mocks')))
    check('attempts unchanged after move', await H.TDB.tejas_attempts.count_documents({'set_id': bm1}) == nattempts and (await stu.get(f'/api/attempts/{aid}')).status_code == 200)
    r = await own.patch(f'/api/admin/catalog/tests/{bm1}', json={'section_id': 'jee-main:chapters'}); check('move to other exam 409', r.status_code == 409, r.status_code)
    r = await own.patch(f'/api/admin/catalog/tests/{jpr}', json={'section_id': 'jee-main:pyq'}); check('non-pyq into PYQ 409', r.status_code == 409, r.status_code)
    r = await stu.get('/api/catalog/exams/bitsat'); secs = [s['slug'] for s in r.json()['sections']]
    check('bitsat sections in owner order (custom first)', secs == [bxslug, 'mocks'], secs)
    r = await own.patch(f'/api/admin/catalog/sections/{bx}', json={'hidden': True}); check('hide section 200', r.status_code == 200)
    r = await stu.get('/api/catalog/exams/bitsat'); check('hidden section not listed', bxslug not in [s['slug'] for s in r.json()['sections']])
    r = await stu.get(f'/api/exam-navigation/bitsat/catalogue?section={bxslug}'); check('hidden section catalogue 404 for student', r.status_code == 404, r.status_code)
    await own.patch(f'/api/admin/catalog/sections/{bx}', json={'hidden': False})
    # unplaced
    r = await own.get('/api/admin/catalog/exams/jee-main/unplaced'); got = ids(r)
    check('unplaced lists jee practice test', jpr in got and pyq not in got and jch not in got, got)
    r = await own.get('/api/admin/catalog'); check('admin catalog 200 with counts', r.status_code == 200 and any(e['slug'] == slug for e in r.json()['items']), r.status_code)
    # ---- hidden exam enforcement
    cx = await mkset('CUST', exam='TEST NEET', catalog_section_id=nsec, test_kind='mock')
    cy = await mkset('CUSTKEY', exam='TEST NEET', test_kind='mock')  # exam key only
    for sid in (cx, cy):
        check(f'hidden {sid[-11:]} my/sets 404', (await stu.get(f'/api/my/sets/{sid}')).status_code == 404)
        check(f'hidden {sid[-11:]} preflight 404', (await stu.post(f'/api/sets/{sid}/preflight', json={})).status_code == 404)
        check(f'hidden {sid[-11:]} start 404', (await start(stu, sid)).status_code == 404)
        check(f'hidden {sid[-11:]} /api/sets/id 404', (await stu.get(f'/api/sets/{sid}')).status_code == 404)
        check(f'hidden {sid[-11:]} not in /api/sets', sid not in ids(await client().get('/api/sets?q=TEST_CUST')))
        check(f'hidden {sid[-11:]} not in /api/my/sets', sid not in ids(await stu.get('/api/my/sets?q=TEST_CUST')))
    r = await stu.get(f'/api/exam-navigation/{slug}/catalogue?section=test-full-mocks'); check('hidden exam catalogue 404 student', r.status_code == 404, r.status_code)
    check('owner can open hidden test', (await own.get(f'/api/my/sets/{cx}')).status_code == 200)
    r = await own.patch(f'/api/admin/catalog/exams/{slug}', json={'shown': True}); check('show exam 200', r.status_code == 200 and r.json()['shown'] is True, r.text)
    check('student sees shown custom exam after built-ins', [e['slug'] for e in (await stu.get('/api/catalog/exams')).json()['items']] == ['jee-main', 'bitsat', 'comedk', slug])
    r = await stu.get(f'/api/catalog/exams/{slug}'); secs = r.json().get('sections', [])
    check('shown exam: only sections with live tests', [s['id'] for s in secs] == [nsec] and secs[0]['live_count'] == 1, secs)
    check('shown exam: my/sets 200', (await stu.get(f'/api/my/sets/{cx}')).status_code == 200)
    sec_slug = secs[0]['slug'] if secs else ''
    got = ids(await stu.get(f'/api/exam-navigation/{slug}/catalogue?section={sec_slug}')); check('custom section catalogue lists test', got == [cx], got)
    check('custom exam key-only test NOT in custom list section', cy not in got)
    await own.patch(f'/api/admin/catalog/exams/{slug}', json={'shown': False})
    check('hide again -> student 404', (await stu.get(f'/api/my/sets/{cx}')).status_code == 404)
    await own.patch(f'/api/admin/catalog/exams/{slug}', json={'shown': True})
    # ---- role checks
    for path in ('/api/admin/catalog', f'/api/admin/catalog/exams/{slug}/unplaced', '/api/admin/overview', '/api/admin/books', '/api/admin/schedule/timed', '/api/studio/reviewers', '/api/admin/catalog/sections/bitsat:mocks/tests'):
        r = await rev.get(path); check(f'reviewer 403 {path}', r.status_code == 403, r.status_code)
        r = await stu.get(path); check(f'student 403 {path}', r.status_code == 403, r.status_code)
    r = await rev.post('/api/admin/catalog/exams', json={'name': 'TEST R', 'short': 'R', 'subjects': ['P'], 'color': 'teal'}); check('reviewer create exam 403', r.status_code == 403)
    r = await rev.patch(f'/api/admin/catalog/tests/{bm2}', json={'live': False}); check('reviewer test patch 403', r.status_code == 403)
    r = await rev.get('/api/admin/review/held'); check('reviewer held 200', r.status_code == 200, r.status_code)
    r = await stu.get('/api/admin/review/held'); check('student held 403', r.status_code == 403, r.status_code)
    for path in ('/api/admin/overview', '/api/admin/schedule/timed', '/api/studio/reviewers'):
        r = await own.get(path); check(f'owner 200 {path}', r.status_code == 200, (r.status_code, r.text[:200]))
    # ---- book destination
    mocks = [{'n': 1, 'qs': q3('S1'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]},
             {'n': 2, 'qs': q3('S2'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]},
             {'n': 3, 'qs': q3('S3'), 'keys': [(1, 'B'), (2, 'B'), (2, 'A'), (3, 'C')]}]
    raw = build_pdf(mocks); sha = hashlib.sha256(raw).hexdigest()
    base = {'filename': 'b.pdf', 'title': 'TEST_QA173 Book', 'sha256': sha, 'size': len(raw), 'rights_confirmed': True}
    for sid_, label in ((None, 'missing'), ('nope', 'invalid'), ('jee-main:pyq', 'pyq')):
        r = await own.post('/api/admin/books', json={**base, **({'section_id': sid_} if sid_ else {})})
        check(f'book create section {label} 422', r.status_code == 422, (r.status_code, r.text[:150]))
    # Iteration 182: chapter-wise types take PDFs through the chapter reader (one test per chapter).
    for sid_, label in (('bitsat:chapters', 'chapters layout'), (nch, 'custom chapters')):
        r = await own.post('/api/admin/books', json={**base, 'title': 'TEST_QA173 Chapters ' + label, 'section_id': sid_})
        check(f'book create section {label} accepted as chapter-wise', r.status_code == 200, (r.status_code, r.text[:150]))
    b = await upload(own, raw, 'TEST_QA173 Book', section_id='bitsat:mocks', auto_publish=True)
    bid = b['id']
    check('book destination stored', (b.get('destination') or {}).get('section_id') == 'bitsat:mocks' and b['auto_publish'] is False, (b.get('destination'), b.get('auto_publish')))
    r = await own.post('/api/admin/books', json={**base, 'section_id': 'bitsat:mocks'}); check('same sha returns same book', r.json().get('id') == bid)
    r, view = await complete(own, bid)
    st = {m['label']: m['state'] for m in view['mocks']}; print('STATES', st)
    check('after reading nothing published', 'published' not in st.values() and await SETS.count_documents({'book_import_id': bid}) == 0, st)
    check('ready + held detected', list(st.values()).count('ready') == 2 and st.get('Mock 3') == 'held', st)
    mid = {m['label']: m['id'] for m in view['mocks']}
    rules_exam = [(m.get('rules') or {}).get('exam') for m in view['mocks'] if m['state'] == 'ready']
    check('mock rules exam from destination (BITSAT)', rules_exam and all(e == 'BITSAT' for e in rules_exam), rules_exam)
    r = await own.post(f'/api/admin/books/{bid}/control', json={'revision': view['revision'], 'action': 'publish_ready', 'mock_id': mid['Mock 3']})
    check('publish held mock 409 with message', r.status_code == 409 and 'not ready' in r.text, (r.status_code, r.text[:200]))
    view = (await own.get(f'/api/admin/books/{bid}')).json()
    r = await own.post(f'/api/admin/books/{bid}/control', json={'revision': view['revision'], 'action': 'publish_ready', 'mock_id': mid['Mock 1']})
    check('publish one ready mock 200', r.status_code == 200, r.text[:200]); await drain()
    view = (await own.get(f'/api/admin/books/{bid}')).json(); st = {m['label']: (m['state'], m.get('set_id')) for m in view['mocks']}
    check('only Mock 1 published', st['Mock 1'][0] == 'published' and st['Mock 2'][0] == 'ready', st)
    s1 = await SETS.find_one({'id': st['Mock 1'][1]}) or {}
    check('published title == label', s1.get('title') == 'Mock 1', s1.get('title'))
    check('published exam/section', s1.get('exam') == 'BITSAT' and s1.get('catalog_section_id') == 'bitsat:mocks', (s1.get('exam'), s1.get('catalog_section_id')))
    orders = {x['id']: x.get('catalog_order') for x in await SETS.find({'id': {'$in': [bm2, s1.get('id')]}}).to_list(5)}
    check('catalog_order after existing', (orders.get(s1.get('id')) or 0) > (orders.get(bm2) or 99), orders)
    got = ids(await stu.get('/api/exam-navigation/bitsat/catalogue?section=mocks')); check('student sees existing then new mock', got[-1:] == [s1.get('id')] and bm2 in got, got)
    future = time.time() + 86400
    r = await own.post(f'/api/admin/books/{bid}/control', json={'revision': view['revision'], 'action': 'publish_ready', 'release_at': future})
    check('publish all ready scheduled 200', r.status_code == 200, r.text[:200]); await drain()
    view = (await own.get(f'/api/admin/books/{bid}')).json(); st = {m['label']: (m['state'], m.get('set_id')) for m in view['mocks']}
    check('book view shows Mock 2 scheduled (per-mock release_at), Mock 3 held', st['Mock 2'][0] == 'scheduled' and st['Mock 3'][0] == 'held', st)
    s2 = await SETS.find_one({'id': st['Mock 2'][1]}) or {}
    check('scheduled set start_at = release_at', abs((s2.get('start_at') or 0) - future) < 2, s2.get('start_at'))
    check('scheduled not visible to students', st['Mock 2'][1] not in ids(await stu.get('/api/exam-navigation/bitsat/catalogue?section=mocks')))
    r = await stu.get(f'/api/book-series/{bid}'); check('book-series path', r.status_code == 200 and r.json().get('path') == '/exams/bitsat/mocks', (r.status_code, r.text[:200]))
    r = await own.post(f'/api/admin/books/{bid}/control', json={'revision': view['revision'], 'action': 'publish_ready'})
    check('publish_ready with nothing ready 409', r.status_code == 409, r.status_code)
    # legacy 'publish' action still sets auto_publish (should be gone)
    view = (await own.get(f'/api/admin/books/{bid}')).json()
    r = await own.post(f'/api/admin/books/{bid}/control', json={'revision': view['revision'], 'action': 'publish'})
    check('legacy publish action must not re-enable auto_publish', r.status_code != 200 or r.json().get('auto_publish') is False, (r.status_code, r.json().get('auto_publish') if r.status_code == 200 else r.text[:100]))
    await drain()
    # ---- custom exam book
    raw2 = build_pdf([{'n': 1, 'qs': q3('C1'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]}])
    b2 = await upload(own, raw2, 'TEST_QA173 Custom', section_id=nsec)
    r, v2 = await complete(own, b2['id']); print('CUSTOM', v2['state'], v2['message'], [(m['label'], m['state'], m['issues']) for m in v2['mocks']])
    check('custom exam book mock ready', [m['state'] for m in v2['mocks']] == ['ready'], [(m['state'], m['issues']) for m in v2['mocks']])
    check('custom rules exam Custom', [(m.get('rules') or {}).get('exam') for m in v2['mocks']] == ['Custom'], [(m.get('rules') or {}).get('exam') for m in v2['mocks']])
    r = await own.post(f'/api/admin/books/{b2["id"]}/control', json={'revision': v2['revision'], 'action': 'publish_ready'}); await drain()
    v2 = (await own.get(f'/api/admin/books/{b2["id"]}')).json(); m = v2['mocks'][0] if v2['mocks'] else {}
    check('custom mock published', m.get('state') == 'published', (m.get('state'), m.get('issues'), v2.get('message')))
    sc = await SETS.find_one({'id': m.get('set_id')}) or {}
    check('custom set exam == TEST NEET, section', sc.get('exam') == 'TEST NEET' and sc.get('catalog_section_id') == nsec, (sc.get('exam'), sc.get('catalog_section_id')))
    if sc:
        r = await start(stu, sc['id']); check('student can start custom mock', r.status_code == 200, r.text[:200])
    # ---- imports section_id invalid
    r = await own.post('/api/studio/imports', files={'questions': ('q.xlsx', b'x', 'application/octet-stream')}, data={'request_id': uuid.uuid4().hex, 'section_id': 'jee-main:pyq'})
    check('imports with PYQ section rejected 4xx', r.status_code in (400, 409, 415, 422), (r.status_code, r.text[:150]))


async def run():
    try:
        await main()
    except Exception as e:
        import traceback; traceback.print_exc(); check('completed without exception', False, repr(e))
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
        f = [r for r in RESULTS if not r[1]]
        print(f'TOTAL {len(RESULTS)} PASS {len(RESULTS) - len(f)} FAIL {len(f)}')
        for x in f: print('  FAILED', x[0], '::', x[2])

if __name__ == '__main__':
    asyncio.run(run())
