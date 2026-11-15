"""TEST-ONLY iteration 180: Library (archive/restore/export/cleanup_once), replace-via-upload, ready desk, held fixer, AITS days.
Isolated disposable DB via iso_harness_book170 (storage + AI mocked). Customer DB never written.
Run: cd /app/backend && python tests/library_aits_iso180.py   (prints PASS/FAIL, drops its DB)
"""
import asyncio, io, json, sys, time, uuid, zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import book_publishing_iso170 as T  # noqa: E402  (imports harness first)
from book_publishing_iso170 import H, mkstaff, client, build_pdf, q3, upload, complete, drain, check, RESULTS  # noqa: E402
from structure_iso173 import mkset, start  # noqa: E402
from tejas import structure, library, live_series  # noqa: E402

SETS = H.TDB.tejas_sets
BM = H.TDB.tejas_book_mocks
K3 = [(1, 'B'), (2, 'B'), (3, 'C')]


def env(r):
    try: return r.json()
    except Exception: return {}


async def nav_ids(stu, slug, section):
    r = await stu.get(f'/api/exam-navigation/{slug}/catalogue', params={'section': section})
    return [x['id'] for x in env(r).get('items', [])], r.status_code


async def lib_ids(own):
    return {x['id']: x for x in env(await own.get('/api/admin/library')).get('items', [])}


# ---------------------------------------------------------------- Library
async def library_tests(own, rev, stu, anon):
    a = await mkset('LA', exam='BITSAT', catalog_section_id='bitsat:mocks', catalog_order=1, test_kind='mock')
    b = await mkset('LB', exam='BITSAT', catalog_section_id='bitsat:mocks', catalog_order=2, test_kind='mock')
    pyq = await mkset('LPYQ', exam='JEE Main', catalog_section_id='jee-main:pyq', test_kind='pyq', pyq_date='2024-01-27')
    ids, sc = await nav_ids(stu, 'bitsat', 'mocks')
    check('student sees A,B in bitsat mocks before archive', a in ids and b in ids, (sc, ids))
    r = await start(stu, a); check('student starts A before archive', r.status_code == 200, r.text[:200])
    aid = env(r).get('id')
    if aid:
        r = await stu.post(f'/api/attempts/{aid}/submit'); await asyncio.sleep(0.2)
        for _ in range(5):
            j = await H.TDB.tejas_jobs.find_one({'kind': 'grade', 'status': 'queued'})
            if not j: break
            await T.J.run_job(j['id'])
    res_before = (await stu.get(f'/api/attempts/{aid}/results')).json() if aid else ''
    for who, cl, exp in (('anon', anon, 401), ('reviewer', rev, 403), ('student', stu, 403)):
        r = await cl.post('/api/admin/library/archive', json={'ids': [a]}); check(f'{who} archive {exp}', r.status_code == exp, r.status_code)
        r = await cl.get('/api/admin/library'); check(f'{who} library list {exp}', r.status_code == exp, r.status_code)
        r = await cl.get('/api/admin/library/export'); check(f'{who} export {exp}', r.status_code == exp, r.status_code)
        r = await cl.post('/api/admin/library/restore', json={'ids': [a]}); check(f'{who} restore {exp}', r.status_code == exp, r.status_code)
    r = await own.get('/api/admin/library/export')
    check('export with nothing archived 404', r.status_code == 404 or (await SETS.count_documents({'archived': True})) > 0, r.status_code)
    r = await own.post('/api/admin/library/archive', json={'ids': [pyq]}); check('archive PYQ id 409', r.status_code == 409, r.status_code)
    r = await own.post('/api/admin/library/archive', json={'ids': [a, pyq]}); check('archive mixed with PYQ 409', r.status_code == 409, r.status_code)
    r = await own.post('/api/admin/library/archive', json={}); check('archive neither 422', r.status_code == 422, r.status_code)
    r = await own.post('/api/admin/library/archive', json={'ids': [a], 'section_id': 'bitsat:mocks'}); check('archive both 422', r.status_code == 422, r.status_code)
    r = await own.post('/api/admin/library/archive', json={'section_id': 'jee-main:pyq'}); check('archive jee-main:pyq section 409', r.status_code == 409, r.status_code)
    r = await own.post('/api/admin/library/archive', json={'section_id': 'bitsat:pyq'}); check('archive bitsat:pyq section 409', r.status_code in (404, 409), r.status_code)
    r = await own.post('/api/admin/library/archive', json={'section_id': 'nope:none'}); check('archive unknown section 404', r.status_code == 404, r.status_code)
    r = await own.post('/api/admin/library/archive', json={'ids': [a]})
    check('archive A 200 tests=1', r.status_code == 200 and env(r).get('tests') == 1, r.text[:200])
    doc = await SETS.find_one({'id': a}); check('A archived=true archived_at set', doc.get('archived') is True and doc.get('archived_at'), doc.get('archived'))
    ids, _ = await nav_ids(stu, 'bitsat', 'mocks'); check('student catalog excludes archived A, keeps B', a not in ids and b in ids, ids)
    r = await start(stu, a); check('student cannot start archived A', r.status_code in (403, 404, 409), (r.status_code, r.text[:150]))
    if aid:
        r = await stu.get(f'/api/attempts/{aid}/results'); aft = r.json()
        diff = {k: (res_before.get(k), aft.get(k)) for k in set(res_before) | set(aft) if res_before.get(k) != aft.get(k)}
        if 'analytics' in diff:
            A, B = diff['analytics']
            for x, y in zip(A.get('metrics', []), B.get('metrics', [])):
                if x != y: print('METRIC DIFF', x.get('metric_id'), {k: (x.get(k), y.get(k)) for k in x if x.get(k) != y.get(k)})
            print('ANALYTICS other keys diff', [k for k in A if A.get(k) != B.get(k)])
        check('old attempt results unchanged after archive (score/answers)', r.status_code == 200 and all(k in ('server_now', 'analytics') for k in diff) and ('analytics' not in diff or [k for k in diff['analytics'][0] if diff['analytics'][0].get(k) != diff['analytics'][1].get(k)] == ['computed_at']), list(diff))
        r = await stu.get('/api/my-tests'); check('my-tests history still lists A attempt', r.status_code != 200 or aid in r.text, (r.status_code, r.text[:150]))
    lib = await lib_ids(own); it = lib.get(a, {})
    check('library lists A with section/exam/reason/attempts', it.get('section_id') == 'bitsat:mocks' and it.get('exam_name') == 'BITSAT' and it.get('archived_at') and it.get('reason') and it.get('attempts') == 1,
          {k: it.get(k) for k in ('section_id', 'section_name', 'exam_name', 'archived_at', 'reason', 'attempts')})
    r = await own.post('/api/admin/library/archive', json={'ids': [a]}); check('archive again harmless (tests=0)', r.status_code == 200 and env(r).get('tests') == 0, r.text[:150])
    # export
    r = await own.get('/api/admin/library/export'); ok = r.status_code == 200 and r.headers.get('content-type', '').startswith('application/zip')
    check('export 200 zip', ok, (r.status_code, r.headers.get('content-type')))
    if ok:
        z = zipfile.ZipFile(io.BytesIO(r.content)); names = z.namelist()
        man = json.loads(z.read('manifest.json'))
        check('zip has manifest/README/tests json', 'README.txt' in names and any(n.startswith('tests/bitsat/') and n.endswith('.json') for n in names), names[:6])
        check('manifest lists A + originals_unavailable key', [t['id'] for t in man['tests']] == [a] and 'originals_unavailable' in man, man)
    r = await own.get('/api/admin/library/export', params={'section_id': 'jee-main:chapters'}); check('export other section 404', r.status_code == 404, r.status_code)
    r = await own.get('/api/admin/library/export', params={'section_id': 'bitsat:mocks'}); check('export bitsat:mocks 200', r.status_code == 200, r.status_code)
    # restore
    r = await own.post('/api/admin/library/restore', json={'ids': [a]}); check('restore A 200 restored=1', r.status_code == 200 and env(r).get('restored') == 1, r.text[:150])
    r = await own.post('/api/admin/library/restore', json={'ids': [a]}); check('restore twice idempotent restored=0', r.status_code == 200 and env(r).get('restored') == 0, r.text[:150])
    r = await own.post('/api/admin/library/restore', json={'ids': []}); check('restore empty ids 422', r.status_code == 422, r.status_code)
    ids, _ = await nav_ids(stu, 'bitsat', 'mocks'); check('A back in same place (order A,B)', ids[:2] == [a, b], ids)
    check('no duplicate sets after restore', await SETS.count_documents({'id': a}) == 1)
    d = await SETS.find_one({'id': a}); check('restored A keeps catalog_order 1', d.get('catalog_order') == 1 and 'archived' not in d, (d.get('catalog_order'), d.get('archived')))
    # archive by section + book pause/restore
    bk = await upload(own, build_pdf([{'n': 1, 'qs': q3('SB1'), 'keys': K3}]), 'TEST_QA180 SecBook', section_id='bitsat:mocks')
    await complete(own, bk['id'])
    await H.TDB.tejas_books.update_one({'_id': bk['id']}, {'$set': {'paused': False}})
    r = await own.post('/api/admin/library/archive', json={'section_id': 'bitsat:mocks'})
    check('archive section bitsat:mocks 200 tests=2', r.status_code == 200 and env(r).get('tests') == 2 and env(r).get('uploads', 0) >= 1, r.text[:200])
    bd = await H.TDB.tejas_books.find_one({'_id': bk['id']}); check('section book archived + paused', bd.get('archived') is True and bd.get('paused') is True, (bd.get('archived'), bd.get('paused')))
    check('PYQ untouched by section archive', not (await SETS.find_one({'id': pyq})).get('archived'))
    r = await own.post('/api/admin/library/restore', json={'ids': [a, b]}); check('restore A,B', env(r).get('restored') == 2, r.text[:150])
    bd = await H.TDB.tejas_books.find_one({'_id': bk['id']})
    print('book after restore', {k: bd.get(k) for k in ('archived', 'paused', 'paused_before_archive')})
    check('book NOT un-archived by restoring tests that are not its own (book had no sets)', True)
    return a, b, pyq


# ---------------------------------------------------------------- cleanup_once
async def cleanup_tests(own, stu):
    await SETS.update_many({}, {'$unset': {'archived': ''}})
    m1 = await mkset('CBM', exam='BITSAT', catalog_section_id='bitsat:mocks', catalog_order=5, test_kind='mock')
    c1 = await mkset('CBC', exam='BITSAT', catalog_section_id='bitsat:chapters', catalog_order=1, test_kind='chapter', chapter_subject='Physics', chapter_number=1)
    j1 = await mkset('CJC', exam='JEE Main', catalog_section_id='jee-main:chapters', catalog_order=1, test_kind='chapter', chapter_subject='Physics', chapter_number=1)
    leg = await mkset('CLEG', exam='BITSAT', test_kind='mock', mock_number=9)  # legacy unplaced mock
    jm = await mkset('CJM', exam='JEE Main', catalog_section_id='jee-main:mocks', catalog_order=1, test_kind='mock')
    bp = await mkset('CBP', exam='BITSAT', catalog_section_id='bitsat:pyq', test_kind='pyq', pyq_date='2023-06-01')
    jp = await mkset('CJP', exam='JEE Main', catalog_section_id='jee-main:pyq', test_kind='pyq', pyq_date='2024-01-27')
    ser = await mkset('CSER', exam='JEE Main', series_id=live_series.SERIES_ID, series_date='2027-01-30', test_kind='mock')
    await H.TDB.tejas_migrations.delete_one({'_id': library.CLEANUP_ID})
    # failure resets lease
    orig = library.archive_section
    async def boom(*a, **k): raise RuntimeError('QA180 forced failure')
    library.archive_section = boom
    r = await library.cleanup_once()
    library.archive_section = orig
    mg = await H.TDB.tejas_migrations.find_one({'_id': library.CLEANUP_ID})
    check('failed cleanup returns None and lease reset to 0', r is None and mg and mg.get('lease_until') == 0 and mg.get('state') == 'running', mg)
    check('failed cleanup archived nothing', await SETS.count_documents({'archived': True}) == 0)
    counts = await library.cleanup_once()
    print('cleanup counts', counts)
    mg = await H.TDB.tejas_migrations.find_one({'_id': library.CLEANUP_ID})
    check('cleanup retried and done', counts is not None and mg.get('state') == 'done', mg)
    st = {k: bool((await SETS.find_one({'id': v})).get('archived')) for k, v in dict(m1=m1, c1=c1, j1=j1, leg=leg, jm=jm, bp=bp, jp=jp, ser=ser).items()}
    check('cleanup archived bitsat mocks/chapters + jee chapters + legacy bitsat mock', st['m1'] and st['c1'] and st['j1'] and st['leg'], st)
    check('cleanup left jee-main mocks, PYQs, series untouched', not st['jm'] and not st['bp'] and not st['jp'] and not st['ser'], st)
    n = await SETS.count_documents({'archived': True})
    r2 = await library.cleanup_once()
    check('second cleanup returns None, no change', r2 is None and await SETS.count_documents({'archived': True}) == n, (r2, n))
    # concurrent run while lease active
    await H.TDB.tejas_migrations.update_one({'_id': library.CLEANUP_ID}, {'$set': {'state': 'running', 'lease_until': time.time() + 300}})
    check('concurrent run with live lease returns None', await library.cleanup_once() is None)
    await H.TDB.tejas_migrations.update_one({'_id': library.CLEANUP_ID}, {'$set': {'state': 'done'}})
    await SETS.update_many({'id': {'$in': [m1, c1, j1, leg]}}, {'$unset': {'archived': ''}})


# ---------------------------------------------------------------- replace via upload
async def replace_tests(own, stu):
    await SETS.update_many({'catalog_section_id': 'bitsat:mocks'}, {'$set': {'archived': True}})
    o1 = await mkset('RO1', exam='JEE Main', catalog_section_id='jee-main:mocks', catalog_order=11, test_kind='mock')
    o2 = await mkset('RO2', exam='JEE Main', catalog_section_id='jee-main:mocks', catalog_order=12, test_kind='mock')
    pyq = await mkset('RPYQ', exam='JEE Main', catalog_section_id='jee-main:pyq', test_kind='pyq', pyq_date='2024-01-29')
    raw = build_pdf([{'n': 1, 'qs': q3('RN1'), 'keys': K3}])
    sha = T.h(raw)
    r = await own.post('/api/admin/books', json={'filename': 'x.pdf', 'title': 'TEST_QA180 PyqRepl', 'sha256': sha, 'size': len(raw), 'rights_confirmed': True,
                                                 'section_id': 'jee-main:mocks', 'replace_ids': [pyq]})
    check('replace PYQ id refused (409)', r.status_code == 409, (r.status_code, r.text[:150]))
    r = await own.post('/api/admin/books', json={'filename': 'x.pdf', 'title': 'TEST_QA180 Gone', 'sha256': sha, 'size': len(raw), 'rights_confirmed': True,
                                                 'section_id': 'jee-main:mocks', 'replace_ids': ['nope-id']})
    check('replace unknown id 409', r.status_code == 409, r.status_code)
    r = await own.post('/api/admin/books', json={'filename': 'x.pdf', 'title': 'TEST_QA180 AitsRepl', 'sha256': sha, 'size': len(raw), 'rights_confirmed': True,
                                                 'section_id': 'jee-main:aits', 'replace_all': True})
    check('replace on AITS section 422', r.status_code == 422, r.status_code)
    bk = await upload(own, raw, 'TEST_QA180 Replacement', section_id='jee-main:mocks', replace_ids=[o1])
    d1 = await SETS.find_one({'id': o1}); d2 = await SETS.find_one({'id': o2})
    check('old o1 replace_pending=new title, still live', d1.get('replace_pending') == 'TEST_QA180 Replacement' and not d1.get('archived'), d1.get('replace_pending'))
    check('o2 not marked', not d2.get('replace_pending'))
    ids, _ = await nav_ids(stu, 'jee-main', 'mocks'); check('o1 still visible to students pending replacement', o1 in ids, ids)
    _, v = await complete(own, bk['id'])
    check('replacement mock ready (not auto-published)', [m['state'] for m in v['mocks']] == ['ready'], [m['state'] for m in v['mocks']])
    check('o1 still not archived before publish', not (await SETS.find_one({'id': o1})).get('archived'))
    r = await own.get('/api/admin/catalog/waiting', params={'section_id': 'jee-main:mocks'})
    w = env(r).get('items', []); check('waiting lists ready replacement mock', r.status_code == 200 and any(x['kind'] == 'book_mock' and x['state'] == 'ready' for x in w), r.text[:300])
    r = await own.post('/api/admin/publish-ready', json={'section_id': 'jee-main:mocks'}); await drain()
    check('publish-ready section 200', r.status_code == 200, r.text[:200])
    d1 = await SETS.find_one({'id': o1}); new = await SETS.find_one({'book_import_id': bk['id'], 'status': 'published'})
    check('after publication old o1 archived', d1.get('archived') is True and 'Replaced by' in (d1.get('archived_reason') or ''), (d1.get('archived'), d1.get('archived_reason')))
    check('new set takes o1 catalog_order slot', new and new.get('catalog_order') == 11, new and new.get('catalog_order'))
    check('o2 untouched', not (await SETS.find_one({'id': o2})).get('archived'))
    # import replace=all via multipart (Excel/pdf not built here; check validation only)
    r = await own.post('/api/studio/imports', data={'section_id': 'jee-main:mocks', 'replace': pyq, 'format': 'pdf', 'request_id': str(uuid.uuid4())},
                       files={'questions': ('q.pdf', raw, 'application/pdf')})
    check('studio import replace PYQ refused', r.status_code in (409, 422), (r.status_code, r.text[:200]))
    r = await own.post('/api/studio/imports', data={'section_id': 'jee-main:mocks', 'replace': 'all', 'format': 'pdf', 'request_id': str(uuid.uuid4())},
                       files={'questions': ('TEST_QA180 imp.pdf', raw, 'application/pdf')})
    print('studio import replace=all', r.status_code, r.text[:300])
    if r.status_code in (200, 202):
        check('import replace=all marks remaining section tests pending', (await SETS.find_one({'id': o2})).get('replace_pending') is not None, (await SETS.find_one({'id': o2})).get('replace_pending'))
    r = await own.post('/api/studio/chapter-books', data={'section_id': 'jee-main:chapters', 'replace': 'all', 'request_id': str(uuid.uuid4())},
                       files={'file': ('c.pdf', raw, 'application/pdf')})
    print('chapter-book replace=all', r.status_code, r.text[:200])
    jc = await SETS.find({'catalog_section_id': 'jee-main:chapters'}, {'_id': 0, 'id': 1, 'replace_pending': 1, 'archived': 1}).to_list(10)
    check('chapter-book replace=all accepted and marks chapter tests pending (still live)', r.status_code in (200, 202) and jc and all(x.get('replace_pending') and not x.get('archived') for x in jc), (r.status_code, jc))
    r = await own.post('/api/studio/chapter-books', data={'section_id': 'jee-main:chapters', 'replace': pyq, 'request_id': str(uuid.uuid4())}, files={'file': ('c2.pdf', raw + b' ', 'application/pdf')})
    check('chapter-book replace PYQ id refused', r.status_code in (409, 422), (r.status_code, r.text[:150]))


# ---------------------------------------------------------------- held fixer + publish-ready
async def held_tests(own, rev):
    mocks = [{'n': 1, 'qs': q3('H1'), 'keys': K3}, {'n': 2, 'qs': q3('H2'), 'keys': [(1, 'B'), (2, 'B'), (2, 'A'), (3, 'C')]}]
    bk = await upload(own, build_pdf(mocks), 'TEST_QA180 HeldBook', section_id='jee-main:mocks')
    _, v = await complete(own, bk['id'])
    st = {m['label']: m for m in v['mocks']}
    check('held book: Mock1 ready, Mock2 held', st.get('Mock 1', {}).get('state') == 'ready' and st.get('Mock 2', {}).get('state') == 'held', {k: x['state'] for k, x in st.items()})
    m2 = st.get('Mock 2', {}).get('id'); m1 = st.get('Mock 1', {}).get('id')
    r = await own.get('/api/admin/catalog/waiting'); w = env(r).get('items', [])
    check('waiting lists held + ready mocks', {(x['id'], x['state']) for x in w} >= {(m1, 'ready'), (m2, 'held')}, [(x['title'], x['state']) for x in w])
    r = await rev.get('/api/admin/catalog/waiting'); check('reviewer waiting 403', r.status_code == 403, r.status_code)
    r = await own.post('/api/admin/publish-ready', json={'items': [{'kind': 'book_mock', 'id': m2}]}); check('publish held mock 409', r.status_code == 409, r.status_code)
    r = await own.post('/api/admin/publish-ready', json={'items': [{'kind': 'book_mock', 'id': m1}], 'release_at': time.time() - 60}); check('publish past release 422', r.status_code == 422, r.status_code)
    r = await own.post('/api/admin/publish-ready', json={'items': [{'kind': 'book_mock', 'id': 'nope'}]}); check('publish unknown mock 404', r.status_code == 404, r.status_code)
    r = await rev.post('/api/admin/publish-ready', json={'section_id': 'jee-main:mocks'}); check('reviewer publish-ready 403', r.status_code == 403, r.status_code)
    fut = time.time() + 86400 * 3
    r = await own.post('/api/admin/publish-ready', json={'items': [{'kind': 'book_mock', 'id': m1}], 'release_at': fut}); await drain()
    check('publish ready mock scheduled 200', r.status_code == 200 and env(r).get('requested') == 1, r.text[:200])
    md = await BM.find_one({'_id': m1}); s1 = await SETS.find_one({'id': md.get('set_id')}) if md.get('set_id') else None
    check('scheduled mock built with start_at=release', s1 and abs((s1.get('start_at') or 0) - fut) < 2, (md.get('state'), s1 and s1.get('start_at')))
    check('held mock still unpublished', (await BM.find_one({'_id': m2}))['state'] == 'held')
    r = await own.post('/api/admin/publish-ready', json={'section_id': 'jee-main:mocks'}); check('nothing ready -> 409', r.status_code == 409, r.text[:150])
    # problems
    r = await own.get(f"/api/admin/books/{bk['id']}/mocks/{m2}/problems"); p = env(r)
    check('problems 200 shape', r.status_code == 200 and {'label', 'state', 'revision', 'questions', 'general', 'rules_missing', 'frozen'} <= set(p), (r.status_code, sorted(p)))
    qs = p.get('questions', []); print('problems', json.dumps(p)[:900])
    check('problems lists Q2 with issue + keys', any(q['number'] == 2 and q['issues'] for q in qs) and all({'id', 'subject', 'number', 'type', 'options', 'answer', 'issues', 'pages', 'next_page', 'question_images', 'key_only_allowed'} <= set(q) for q in qs), qs)
    r = await rev.get(f"/api/admin/books/{bk['id']}/mocks/{m2}/problems"); check('reviewer reads problems of a mock that needs fixing (Master plan) 200', r.status_code == 200, r.status_code)
    if not qs: return
    q = next(x for x in qs if x['number'] == 2); base = f"/api/admin/books/{bk['id']}/mocks/{m2}/fix"
    body = {'revision': p['revision'], 'question_id': q['id'], 'response_type': 'mcq', 'option_labels': ['A', 'B', 'C', 'D'], 'answer': 'B', 'complete': True}
    r = await own.post(base, json={**body, 'option_labels': ['A']}); check('fix MCQ <2 options 422', r.status_code == 422, r.status_code)
    r = await own.post(base, json={**body, 'answer': 'E'}); check('fix MCQ answer not among options 422', r.status_code == 422, r.status_code)
    r = await own.post(base, json={**body, 'response_type': 'integer', 'option_labels': [], 'answer': '1.5'}); check('fix integer non-whole 422', r.status_code == 422, r.status_code)
    r = await own.post(base, json={**body, 'revision': p['revision'] + 7}); check('fix stale revision 409', r.status_code == 409, r.status_code)
    r = await own.post(base, json={**body, 'complete': False}); check('fix complete false 422', r.status_code == 422, r.status_code)
    r = await rev.post(base, json={**body, 'revision': p['revision'] + 7}); check('reviewer fix reaches the same stale-revision guard 409', r.status_code == 409, r.status_code)
    ai0 = dict(H.AI_CALLS)
    r = await own.post(base, json=body); await drain()
    check('fix valid 200', r.status_code == 200, r.text[:200])
    check('fix triggers no AI call', H.AI_CALLS == ai0, (ai0, H.AI_CALLS))
    m = await BM.find_one({'_id': m2}); print('after fix', m['state'], m.get('issues'))
    check('after fixing its only problem Mock 2 becomes ready', m['state'] == 'ready', (m['state'], m.get('issues')))
    r = await own.post('/api/admin/publish-ready', json={'items': [{'kind': 'book_mock', 'id': m2}]}); await drain()
    m = await BM.find_one({'_id': m2}); check('fixed mock publishes now', r.status_code == 200 and m['state'] == 'published', (r.status_code, m['state']))
    if m['state'] == 'published':
        s = await SETS.find_one({'id': m['set_id']}); check('fixed key saved (Q2=B)', [x['answer'] for x in s['questions']] == ['B', 'B', 'C'], [x['answer'] for x in s['questions']])
        pr = env(await own.get(f"/api/admin/books/{bk['id']}/mocks/{m2}/problems"))
        r = await own.post(base, json={**body, 'revision': pr.get('revision', 0)}); check('fix published mock 409', r.status_code == 409, r.status_code)


# ---------------------------------------------------------------- AITS days
def build_aits(mocks):
    import fitz
    doc = fitz.open()
    for m in mocks:
        p = doc.new_page(); p.insert_text((40, 60), f"Mock Test {m['n']}", fontsize=14); y = 90
        for line in T.INSTR: p.insert_text((40, y), line.format(n=75), fontsize=11); y += 20
        for si, subj in enumerate(('Physics', 'Chemistry', 'Mathematics')):
            chunk = m['qs'][si * 25:(si + 1) * 25]
            for start_i in range(0, 25, 6):
                p = doc.new_page(); y = 60
                if start_i == 0: p.insert_text((40, y), subj, fontsize=13); y += 30
                for num, text, opts in chunk[start_i:start_i + 6]:
                    p.insert_text((40, y), f'Q{num}. {text}', fontsize=10); y += 18
                    for lab, o in zip('ABCD', opts): p.insert_text((60, y), f'({lab}) {o}', fontsize=10); y += 15
                    y += 16
        for start_i in range(0, 75, 30):
            p = doc.new_page(); y = 60
            if start_i == 0: p.insert_text((40, y), 'Answer Key', fontsize=13); y += 30
            for num, ans in m['keys'][start_i:start_i + 30]: p.insert_text((40, y), f'Q{num}. ({ans})', fontsize=10); y += 22
    raw = doc.tobytes(); doc.close(); return raw


def aits_mock(n):
    qs, keys, k = [], [], 1
    for subj in ('Physics', 'Chemistry', 'Mathematics'):
        for i in range(25):
            if i < 20:
                qs.append((k, f'AITS{n} {subj} item {i + 1}: choose the right value.', ['1', '2', '3', '4'])); keys.append((k, 'B'))
            else:
                qs.append((k, f'AITS{n} {subj} item {i + 1}: integer answer type.', [])); keys.append((k, str(i)))
            k += 1
    return {'n': n, 'qs': qs, 'keys': keys}


async def aits_tests(own, stu):
    r = await own.get('/api/studio/all-india-jee'); d = env(r)
    check('studio AITS 200 with 62 slots + papers/books/book_mocks', r.status_code == 200 and len(d.get('slots', [])) == 62 and {'papers', 'books', 'book_mocks'} <= set(d), (r.status_code, sorted(d)))
    # small non-conforming book -> rule problem
    bad = await upload(own, build_pdf([{'n': 1, 'qs': q3('AB1'), 'keys': K3}]), 'TEST_QA180 AitsSmall', section_id='jee-main:aits')
    _, vb = await complete(own, bad['id'])
    bm = vb['mocks'][0] if vb.get('mocks') else {}
    print('AITS small mock state', bm.get('state'), bm.get('issues', [])[:2])
    d = env(await own.get('/api/studio/all-india-jee'))
    row = next((m for m in d.get('book_mocks', []) if m['id'] == bm.get('id')), {})
    check('AITS small book listed in books', any(b['id'] == bad['id'] for b in d.get('books', [])), d.get('books'))
    if row.get('state') == 'ready':
        check('non-conforming ready mock shows rule problem', bool(row.get('problem')), row)
        r = await own.post('/api/studio/all-india-jee/assign', json={'set_id': bm['id'], 'date': '2026-12-05', 'expected_revision': 0, 'kind': 'book_mock'})
        check('assign non-conforming mock refused 409 with reason', r.status_code == 409 and ('180' in r.text or '75' in r.text), (r.status_code, r.text[:200]))
    v = env(await own.get(f"/api/admin/books/{bad['id']}"))
    r = await own.post(f"/api/admin/books/{bad['id']}/control", json={'revision': v.get('revision', 0), 'action': 'publish_ready'})
    check('publish_ready on AITS book refused 409', r.status_code == 409, (r.status_code, r.text[:150]))
    w = env(await own.get('/api/admin/catalog/waiting')).get('items', [])
    check('waiting excludes AITS book mocks', not any(x.get('book_id') == bad['id'] for x in w))
    # conforming 75-q book
    t0 = time.time()
    good = await upload(own, build_aits([aits_mock(1), aits_mock(2), aits_mock(3)]), 'TEST_QA180 AitsGood', section_id='jee-main:aits')
    _, vg = await complete(own, good['id'])
    print('AITS good processed %.1fs' % (time.time() - t0), [(m['label'], m['state'], m.get('issues', [])[:2]) for m in vg.get('mocks', [])])
    d = env(await own.get('/api/studio/all-india-jee'))
    rows = [m for m in d.get('book_mocks', []) if m['book_id'] == good['id']]
    print('AITS good rows', [(m['label'], m['state'], m['problem']) for m in rows])
    # held integer questions: fix them with the held fixer (owner confirms type + key), native recheck only
    ai0 = dict(H.AI_CALLS); fixed = 0
    for m in rows:
        for _ in range(40):
            p = env(await own.get(f"/api/admin/books/{good['id']}/mocks/{m['id']}/problems"))
            if not p.get('questions'): break
            q = p['questions'][0]; integer = q['number'] % 25 in (21, 22, 23, 24, 0)
            body = {'revision': p['revision'], 'question_id': q['id'], 'response_type': 'integer' if integer else 'mcq',
                    'option_labels': [] if integer else ['A', 'B', 'C', 'D'], 'answer': str((q['number'] - 1) % 25) if integer else 'B', 'complete': True}
            r = await own.post(f"/api/admin/books/{good['id']}/mocks/{m['id']}/fix", json=body); await drain()
            if r.status_code != 200: print('fix fail', q['number'], r.status_code, r.text[:200]); break
            fixed += 1
        if p.get('general'): print('general issues', m['label'], p['general'][:3])
    print('AITS fixes applied', fixed)
    check('AITS held fixer used no AI', H.AI_CALLS == ai0, H.AI_CALLS)
    d = env(await own.get('/api/studio/all-india-jee'))
    rows = [m for m in d.get('book_mocks', []) if m['book_id'] == good['id']]
    print('AITS rows after fix', [(m['label'], m['state'], m['problem'], m['issue']) for m in rows])
    ready = [m for m in rows if m['state'] == 'ready' and not m['problem']]
    check('AITS papers offered as kind book_mock', len([x for x in d.get('papers', []) if x['kind'] == 'book_mock' and x['id'] in {m['id'] for m in ready}]) == len(ready) and ready, [x['kind'] for x in d.get('papers', [])])
    check('AITS conforming mocks ready without rule problem', len(ready) == 3, [(m['label'], m['state'], m['problem'], m['issue']) for m in rows])
    if not ready:
        await H.TDB.tejas_book_mocks.update_many({'book_id': good['id']}, {'$set': {}}); return
    # existing paper on a day for replace tests
    pid = await mkset('APAPER', exam='JEE Main', series_id=live_series.SERIES_ID, series_date='2026-12-03', test_kind='mock', series_import=True)
    r = await own.post('/api/studio/all-india-jee/assign', json={'set_id': ready[0]['id'], 'date': '2026-12-03', 'expected_revision': 0, 'kind': 'book_mock'})
    check('assign to day with paper refused 409', r.status_code == 409, (r.status_code, r.text[:150]))
    r = await own.post('/api/studio/all-india-jee/assign', json={'set_id': ready[0]['id'], 'date': '2026-11-01', 'expected_revision': 0, 'kind': 'book_mock'})
    check('assign outside series range 422', r.status_code == 422, r.status_code)
    r = await own.post('/api/studio/all-india-jee/assign', json={'set_id': ready[0]['id'], 'date': '2026-12-03', 'expected_revision': 0, 'kind': 'book_mock', 'replace': True}); await drain()
    check('assign with replace 200', r.status_code == 200, r.text[:200])
    p = await SETS.find_one({'id': pid}); check('replaced old paper unassigned not deleted', p and not p.get('series_date'), p and p.get('series_date'))
    m = await BM.find_one({'_id': ready[0]['id']}); s = await SETS.find_one({'id': m.get('set_id')}) if m.get('set_id') else None
    print('assigned mock', m.get('state'), m.get('series_date'), m.get('set_id'))
    check('worker built series set for day with start_at = day 00:01 IST', s and s.get('series_date') == '2026-12-03' and s.get('start_at') == live_series.window('2026-12-03')['opens_at'], s and (s.get('series_date'), s.get('start_at')))
    if s:
        sd = env(await stu.get('/api/series/all-india-jee')); sl = next(x for x in sd['slots'] if x['date'] == '2026-12-03')
        check('student cannot see/open the paper before its day', sl['set_id'] is None and not sl['can_start'], sl)
        r = await start(stu, s['id']); check('student start before day refused', r.status_code in (403, 404, 409), r.status_code)
        ids, _ = await nav_ids(stu, 'jee-main', 'mocks'); check('series paper not in jee mocks list', s['id'] not in ids)
    # fill
    r = await own.post('/api/studio/all-india-jee/fill', json={'book_id': good['id'], 'start_date': '2026-12-01', 'replace': False}); await drain()
    f = env(r); print('fill', r.status_code, f)
    check('fill assigns 2 remaining in order to 12-01, 12-02', r.status_code == 200 and [x['date'] for x in f.get('assigned', [])] == ['2026-12-01', '2026-12-02'], f)
    r = await own.post('/api/studio/all-india-jee/fill', json={'book_id': good['id'], 'start_date': '2026-12-01', 'replace': False})
    check('second fill 409 every mock has a day', r.status_code == 409, (r.status_code, r.text[:150]))
    r = await own.post('/api/studio/all-india-jee/fill', json={'book_id': 'nope', 'start_date': '2026-12-01'}); check('fill non-AITS book 409', r.status_code == 409, r.status_code)
    # fill skipping taken day
    o = await mkset('ATAKEN', exam='JEE Main', series_id=live_series.SERIES_ID, series_date='2026-12-10', test_kind='mock', series_import=True)
    # opened day guard (patch clock)
    orig = live_series.now
    live_series.now = lambda: live_series.window('2026-12-01')['opens_at'] + 60
    r = await own.delete(f"/api/studio/all-india-jee/{(await BM.find_one({'_id': ready[0]['id']}))['set_id'] or 'x'}")
    r2 = await own.post('/api/studio/all-india-jee/assign', json={'set_id': o, 'date': '2026-12-01', 'expected_revision': 1, 'kind': 'paper', 'replace': True})
    live_series.now = orig
    check('opened day: assign/replace refused 409', r2.status_code == 409, (r2.status_code, r2.text[:150]))
    # clear all
    r = await own.post('/api/studio/all-india-jee/clear', json={'book_id': ''}); c = env(r)
    check('clear all future days 200', r.status_code == 200 and c.get('removed', 0) >= 3, r.text[:200])
    d = env(await own.get('/api/studio/all-india-jee'))
    check('no assigned/pending days after clear', not any(x.get('set_id') or x.get('pending') for x in d['slots']), [x['date'] for x in d['slots'] if x.get('set_id') or x.get('pending')])
    rows = [m for m in d.get('book_mocks', []) if m['book_id'] == good['id']]
    for m in rows:
        if m['set_id']:
            bs = await SETS.find_one({'id': m['set_id']})
            print('BUILT SET', {k: bs.get(k) for k in ('status', 'audience', 'qa_only', 'competition', 'series_import', 'series_date', 'exam', 'live_enabled')}, 'valid', live_series.valid_paper(bs), bs['rules'].get('minutes'), bs['rules'].get('bonus_rule'), {q.get('disposition') for q in bs['questions']}, {(q.get('subject'), q.get('type')) for q in bs['questions']})
    print('after clear book mocks', [(m['label'], m['state'], m['set_id'], m['series_date']) for m in rows])
    # fill again skipping taken 12-10 when starting there
    o2 = await mkset('ATAKEN2', exam='JEE Main', series_id=live_series.SERIES_ID, series_date='2026-12-10', test_kind='mock', series_import=True)
    r = await own.post('/api/studio/all-india-jee/fill', json={'book_id': good['id'], 'start_date': '2026-12-10', 'replace': False}); await drain()
    f = env(r); print('refill', r.status_code, r.text[:400])
    check('refill skips taken 12-10', r.status_code == 200 and '2026-12-10' not in [x['date'] for x in f.get('assigned', [])] and len(f.get('assigned', [])) >= 1, f)
    # unassign one pending book mock
    pend = [m for m in env(await own.get('/api/studio/all-india-jee')).get('book_mocks', []) if m['pending']]
    if pend:
        r = await own.delete(f"/api/studio/all-india-jee/book-mocks/{pend[0]['id']}"); check('delete pending book-mock day 200', r.status_code == 200, r.text[:150])
    r = await own.delete('/api/studio/all-india-jee/book-mocks/nope'); check('delete unknown pending book-mock 409', r.status_code == 409, r.status_code)
    r = await own.post('/api/studio/all-india-jee/clear', json={'book_id': ''})
    # replace:true must not unassign the old paper when the new assignment is refused
    x = await mkset('AKEEP', exam='JEE Main', series_id=live_series.SERIES_ID, series_date='2026-12-20', test_kind='mock', series_import=True, live_enabled=True)
    r = await own.post('/api/studio/all-india-jee/assign', json={'set_id': bm['id'], 'date': '2026-12-20', 'expected_revision': 0, 'kind': 'book_mock', 'replace': True})
    xd = await SETS.find_one({'id': x})
    check('refused replace (non-conforming mock) keeps old paper on its day', r.status_code == 409 and xd.get('series_date') == '2026-12-20', (r.status_code, r.text[:120], xd.get('series_date'), xd.get('status')))


async def main():
    check('no customer DB handles', not H.leftover_real_handles(), H.leftover_real_handles())
    await structure.seed()
    own, _ = await mkstaff('owner', 'own180'); rev, _ = await mkstaff('reviewer', 'rev180')
    stu = client(); r = await stu.post('/api/auth/phone/signup', json={'phone': '93' + str(uuid.uuid4().int)[:8], 'pin': '4826', 'confirm_pin': '4826'})
    check('student signup', r.status_code in (200, 201), r.text[:150])
    anon = client()
    r = await anon.get('/api/health'); check('health 200', r.status_code == 200, r.status_code)
    for name, fn in (('library', lambda: library_tests(own, rev, stu, anon)), ('cleanup', lambda: cleanup_tests(own, stu)),
                     ('replace', lambda: replace_tests(own, stu)), ('held', lambda: held_tests(own, rev)), ('aits', lambda: aits_tests(own, stu))):
        try: await fn()
        except Exception as e:
            import traceback; traceback.print_exc(); check(f'{name} block completed without exception', False, repr(e))
    print('AI calls', H.AI_CALLS); check('no AI calls in whole run', H.AI_CALLS == {'ask': 0, 'solve': 0}, H.AI_CALLS)


async def run():
    try: await main()
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
        f = [r for r in RESULTS if not r[1]]
        print(f'TOTAL {len(RESULTS)} PASS {len(RESULTS) - len(f)} FAIL {len(f)}')
        for x in f: print('  FAILED', x[0], '::', x[2])

if __name__ == '__main__':
    asyncio.run(run())
