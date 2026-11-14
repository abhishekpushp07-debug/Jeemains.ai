"""TEST-ONLY iteration 174: destination-first paper/Excel import, chapter-book destination, book scheduled view, legacy publish.
Isolated disposable DB via iso_harness_book170 (storage + AI mocked; real sandboxed PDF/Excel organiser workers).
Chapter organiser is replaced by a scripted fake ONLY for the process_book destination/mismatch paths (no TEJAS200 combined fixture).
Run: cd /app/backend && python tests/structure_imports_iso174.py   (prints PASS/FAIL, drops its DB)
"""
import asyncio, io, sys, time, uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import book_publishing_iso170 as T  # noqa: E402  (imports harness first)
from book_publishing_iso170 import H, mkstaff, client, build_pdf, q3, upload, complete, drain, check, RESULTS  # noqa: E402
from structure_iso173 import mkset  # noqa: E402
from tejas import structure, chapter_books  # noqa: E402
import fitz  # noqa: E402
from openpyxl import load_workbook  # noqa: E402

SETS = H.TDB.tejas_sets
IMPORTS = H.TDB.tejas_imports
BOOKS = H.TDB.tejas_chapter_books


# --- synthetic paired paper PDFs
def paper(header, tag, n=3):
    q = fitz.open(); s = fitz.open()
    pq = q.new_page(); y = 60
    for line in [header, 'Duration: 180 minutes', 'Physics']:
        pq.insert_text((50, y), line, fontsize=11); y += 20
    for i in range(1, n + 1):
        for line in [f'Q{i}. {tag} question number {i} about force?', '(A) Newton', '(B) Joule', '(C) Watt', '(D) Pascal']:
            pq.insert_text((50, y), line, fontsize=11); y += 18
        y += 14
    ps = s.new_page(); y = 60
    ps.insert_text((50, y), 'Physics', fontsize=11); y += 20
    for i in range(1, n + 1):
        for line in [f'Q{i}. Answer: A', f'{tag} solution {i}: force is in newtons.']:
            ps.insert_text((50, y), line, fontsize=11); y += 18
        y += 14
    return q.tobytes(), s.tobytes()


async def pdf_import(c, header, tag, section_id=None, rid=None):
    qb, sb = paper(header, tag)
    data = {'request_id': rid or str(uuid.uuid4()), 'format': 'pdf', **({'section_id': section_id} if section_id else {})}
    return await c.post('/api/studio/imports', data=data, files={'questions': (f'TEST_{tag}_q.pdf', qb, 'application/pdf'), 'solutions': (f'TEST_{tag}_s.pdf', sb, 'application/pdf')})


async def wait_import(c, iid, tries=60):
    for _ in range(tries):
        r = await c.get(f'/api/studio/imports/{iid}')
        if r.json().get('status') not in ('queued', 'organising'): return r.json()
        await asyncio.sleep(0.5)
    return r.json()


def iso(dt): return dt.astimezone(timezone.utc).isoformat()


def section_ids(resp): return [x['id'] for x in resp.json().get('items', [])]


# --- fake chapter organiser result (only used for process_book destination paths)
def fake_chapter_result(exam):
    qs = [{'number': i, 'q_refs': [{'page': 1, 'rect': [0, 0, 10, 10]}], 's_refs': [], 'type': 'mcq', 'options': {'A': 'a', 'B': 'b', 'C': 'c', 'D': 'd'},
           'answer': 'A', 'text': f'cq{i}', 'subject': 'Physics'} for i in range(1, 4)]
    return {'exam': exam, 'subject': 'Physics', 'pages': 3, 'minutes': 60, 'solution_kind': 'answer_key_only',
            'chapters': [{'number': 1, 'title': 'TEST Units', 'questions': qs, 'verification': {'key_checks_agree': True}, 'start_page': 1, 'end_page': 2, 'key_page': 3, 'minutes': 60}]}


async def chapter_upload(c, section_id=None, raw=None, extra=None):
    raw = raw or (b'%PDF-1.4\n' + uuid.uuid4().hex.encode() + b'\n%%EOF')
    data = {'request_id': str(uuid.uuid4()), **({'section_id': section_id} if section_id else {}), **(extra or {})}
    return await c.post('/api/studio/chapter-books', data=data, files={'file': ('TEST_chapter.pdf', raw, 'application/pdf')})


async def main():
    check('no customer DB handles', not H.leftover_real_handles(), H.leftover_real_handles())
    await structure.seed()
    own, _ = await mkstaff('owner', 'own174')
    rev, _ = await mkstaff('reviewer', 'rev174')
    stu = client(); await stu.post('/api/auth/phone/signup', json={'phone': '93' + str(uuid.uuid4().int)[:8], 'pin': '4826', 'confirm_pin': '4826'})
    bm1 = await mkset('BM1', exam='BITSAT', test_kind='mock', mock_number=1, catalog_order=5)
    r = await own.post('/api/admin/catalog/exams', json={'name': 'TEST NEET174', 'short': 'TN174', 'subjects': ['Physics'], 'color': 'teal'})
    slug = r.json()['slug']; ckey = (await H.TDB.tejas_catalog_exams.find_one({'_id': slug}) or {}).get('key')
    print('custom exam', slug, 'key', ckey)
    nsec = (await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'TEST Papers', 'layout': 'list'})).json()['id']
    nch = (await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'TEST Chaps', 'layout': 'chapters'})).json()['id']
    start = iso(datetime.now(timezone.utc) + timedelta(minutes=2))

    # ===== paper import -> bitsat:mocks
    r = await pdf_import(own, 'BITSAT Practice Paper', 'PB', 'bitsat:mocks')
    check('pdf import 202', r.status_code == 202, (r.status_code, r.text[:200])); iid = r.json().get('id')
    rec = await IMPORTS.find_one({'id': iid}) or {}
    check('pdf import record destination bitsat:mocks', (rec.get('destination') or {}).get('section_id') == 'bitsat:mocks', rec.get('destination'))
    v = await wait_import(own, iid)
    check('pdf import processed ready, exam BITSAT', v.get('status') == 'ready' and v.get('exam') == 'BITSAT' and v.get('count') == 3, (v.get('status'), v.get('exam'), v.get('count'), v.get('message'), v.get('issues')))
    r = await own.post(f'/api/studio/imports/{iid}/schedule', json={'start_at': start, 'revision': 0})
    check('schedule pdf import 200', r.status_code == 200, (r.status_code, r.text[:300]))
    s = await SETS.find_one({'id': iid}) or {}
    check('set catalog_section_id + catalog_order after existing', s.get('catalog_section_id') == 'bitsat:mocks' and (s.get('catalog_order') or 0) > 5, (s.get('catalog_section_id'), s.get('catalog_order')))
    check('set exam BITSAT', s.get('exam') == 'BITSAT', s.get('exam'))
    r = await own.get('/api/admin/catalog/sections/bitsat:mocks/tests'); items = r.json().get('items', [])
    check('imported set listed in admin section tests', iid in [x['id'] for x in items], [(x['id'][-6:], x.get('state')) for x in items])
    print('admin state for import', [x.get('state') for x in items if x['id'] == iid])
    # idempotent same request id
    # mismatch: JEE-read paper into BITSAT
    r = await pdf_import(own, 'JEE Main Practice Paper', 'PJ', 'bitsat:mocks'); jid = r.json().get('id')
    v = await wait_import(own, jid); check('jee paper reads JEE Main', v.get('exam') == 'JEE Main' and v.get('status') == 'ready', (v.get('exam'), v.get('status'), v.get('issues')))
    r = await own.post(f'/api/studio/imports/{jid}/schedule', json={'start_at': start, 'revision': 0})
    check('mismatch builtin destination 409 clear message', r.status_code == 409 and 'reads as JEE Main' in r.text and 'BITSAT' in r.text, (r.status_code, r.text[:250]))
    check('mismatch created no set', await SETS.count_documents({'id': jid}) == 0)
    # custom exam destination
    r = await pdf_import(own, 'Practice Paper', 'PC', nsec); cid = r.json().get('id')
    v = await wait_import(own, cid); check('custom paper ready', v.get('status') == 'ready', (v.get('status'), v.get('issues')))
    r = await own.post(f'/api/studio/imports/{cid}/schedule', json={'start_at': start, 'revision': 0})
    check('custom schedule 200', r.status_code == 200, (r.status_code, r.text[:300]))
    s = await SETS.find_one({'id': cid}) or {}
    check('custom set exam == custom exam key', s.get('exam') == ckey and s.get('catalog_section_id') == nsec and s.get('catalog_order') == 1, (s.get('exam'), ckey, s.get('catalog_section_id'), s.get('catalog_order')))
    r = await own.get(f'/api/admin/catalog/sections/{nsec}/tests'); check('custom section lists imported set', cid in section_ids(r), (r.status_code, r.text[:200]))
    r = await own.get(f'/api/studio/imports/{cid}'); print('import view exam after schedule (custom):', r.json().get('exam'))
    # list-layout invalids
    for sid_, label in (('bitsat:chapters', 'chapters layout'), ('nope', 'unknown'), (nch, 'custom chapters'), ('jee-main:pyq', 'pyq')):
        r = await pdf_import(own, 'BITSAT Paper', 'PX' + label[:3], sid_)
        check(f'pdf import section {label} 422', r.status_code == 422, (r.status_code, r.text[:150]))
    r = await pdf_import(rev, 'BITSAT Paper', 'PR', 'bitsat:mocks'); check('reviewer pdf import 403', r.status_code == 403, r.status_code)
    # no section (legacy) still allowed?
    r = await pdf_import(own, 'BITSAT Paper', 'PN'); print('pdf import without section_id ->', r.status_code)
    nid = r.json().get('id') if r.status_code == 202 else None
    if nid:
        rec = await IMPORTS.find_one({'id': nid}) or {}
        check('import without section has no destination', 'destination' not in rec)

    # ===== Excel combined workbook
    r = await own.get('/api/studio/imports/template?variant=combined'); check('template combined 200 xlsx', r.status_code == 200 and r.content[:2] == b'PK', r.status_code)
    wb = load_workbook(io.BytesIO(r.content)); ws = wb['Questions']
    head = [c.value for c in ws[1]]; ws.delete_rows(2, ws.max_row)
    for i in range(1, 4):
        row = dict(zip(head, [None] * len(head)))
        row.update(question_id=f'TEST-x{i}', question_no=i, subject='Physics', question_text=f'TEST excel q{i}: unit of force?', option_a='Newton', option_b='Joule', option_c='Watt', option_d='Pascal',
                   correct_option='A', type='mcq', topic='Units', difficulty='Easy', exam='BITSAT', duration_minutes=180, solution_text='Force is in newtons.')
        ws.append([row[h] for h in head])
    out = io.BytesIO(); wb.save(out); xb = out.getvalue()
    r = await own.post('/api/studio/imports', data={'request_id': str(uuid.uuid4()), 'format': 'xlsx', 'section_id': 'bitsat:mocks'}, files={'questions': ('TEST_excel174.xlsx', xb, 'application/octet-stream')})
    check('xlsx import 202', r.status_code == 202, (r.status_code, r.text[:200])); xid = r.json().get('id')
    check('xlsx destination stored', ((await IMPORTS.find_one({'id': xid}) or {}).get('destination') or {}).get('section_id') == 'bitsat:mocks')
    v = await wait_import(own, xid); check('xlsx ready BITSAT 3', v.get('status') == 'ready' and v.get('exam') == 'BITSAT' and v.get('count') == 3, (v.get('status'), v.get('exam'), v.get('issues'), v.get('message')))
    r = await own.post(f'/api/studio/imports/{xid}/schedule', json={'start_at': start, 'revision': 0}); check('xlsx schedule 200', r.status_code == 200, r.text[:200])
    sx = await SETS.find_one({'id': xid}) or {}; si = await SETS.find_one({'id': iid}) or {}
    check('xlsx set placed after pdf set', sx.get('catalog_section_id') == 'bitsat:mocks' and (sx.get('catalog_order') or 0) > (si.get('catalog_order') or 0), (sx.get('catalog_order'), si.get('catalog_order')))
    check('xlsx in admin section tests', xid in section_ids(await own.get('/api/admin/catalog/sections/bitsat:mocks/tests')))
    # excel JEE into BITSAT mismatch
    wb2 = load_workbook(io.BytesIO(xb)); w2 = wb2['Questions']; ei = head.index('exam') + 1
    for rr in range(2, w2.max_row + 1): w2.cell(rr, ei).value = 'JEE Main'
    o2 = io.BytesIO(); wb2.save(o2)
    r = await own.post('/api/studio/imports', data={'request_id': str(uuid.uuid4()), 'format': 'xlsx', 'section_id': 'bitsat:mocks'}, files={'questions': ('TEST_excel174j.xlsx', o2.getvalue(), 'application/octet-stream')})
    xj = r.json().get('id'); v = await wait_import(own, xj)
    r = await own.post(f'/api/studio/imports/{xj}/schedule', json={'start_at': start, 'revision': 0})
    check('xlsx mismatch 409', r.status_code == 409 and 'reads as JEE Main' in r.text, (v.get('status'), r.status_code, r.text[:200]))
    # excel custom exam
    r = await own.post('/api/studio/imports', data={'request_id': str(uuid.uuid4()), 'format': 'xlsx', 'section_id': nsec}, files={'questions': ('TEST_excel174c.xlsx', o2.getvalue(), 'application/octet-stream')})
    xc = r.json().get('id'); await wait_import(own, xc)
    r = await own.post(f'/api/studio/imports/{xc}/schedule', json={'start_at': start, 'revision': 0})
    sc = await SETS.find_one({'id': xc}) or {}
    check('xlsx custom exam key + order 2', r.status_code == 200 and sc.get('exam') == ckey and sc.get('catalog_order') == 2, (r.status_code, sc.get('exam'), sc.get('catalog_order')))
    r = await own.post('/api/studio/imports', data={'request_id': str(uuid.uuid4()), 'format': 'xlsx', 'section_id': 'bitsat:chapters'}, files={'questions': ('TEST_e.xlsx', xb, 'application/octet-stream')})
    check('xlsx chapters section accepted (Excel fits chapter sections)', r.status_code == 202, r.status_code)

    # ===== chapter books
    r = await chapter_upload(own, 'bitsat:mocks'); check('chapter book list-layout section 422', r.status_code == 422, (r.status_code, r.text[:150]))
    r = await chapter_upload(own, 'jee-main:pyq'); check('chapter book pyq section 422', r.status_code == 422, r.status_code)
    r = await chapter_upload(own, 'nope'); check('chapter book unknown section 422', r.status_code == 422, r.status_code)
    r = await own.post('/api/studio/chapter-books', data={'section_id': 'bitsat:chapters'}, files={'file': ('a.pdf', b'%PDF-1.4 x', 'application/pdf')})
    check('chapter book missing request_id 422', r.status_code == 422, r.status_code)
    r = await own.post('/api/studio/chapter-books', data={'request_id': str(uuid.uuid4()), 'section_id': 'bitsat:chapters'}, files={'file': ('a.txt', b'%PDF-1.4 x', 'text/plain')})
    check('chapter book non-pdf name 422', r.status_code == 422, r.status_code)
    r = await chapter_upload(own, 'bitsat:chapters', extra={'format': 'pdf'}); check('chapter book extra field 422', r.status_code == 422, r.status_code)
    r = await chapter_upload(rev, 'bitsat:chapters'); check('reviewer chapter upload 403', r.status_code == 403, r.status_code)
    # real organiser on junk PDF: destination stored, processing fails cleanly
    r = await chapter_upload(own, 'bitsat:chapters'); check('chapter upload chapters section 202', r.status_code == 202, (r.status_code, r.text[:200]))
    bid = r.json().get('id'); bk = await BOOKS.find_one({'id': bid}) or {}
    check('chapter book destination stored', (bk.get('destination') or {}).get('section_id') == 'bitsat:chapters', bk.get('destination'))
    print('junk chapter book status/message:', bk.get('status'), bk.get('message'))
    # scripted organiser for process_book paths
    real_org = chapter_books.organise_pdfs
    try:
        async def fake_jee(*a, **k): return fake_chapter_result('JEE Main')
        chapter_books.organise_pdfs = fake_jee
        r = await chapter_upload(own, 'bitsat:chapters'); mb = r.json().get('id')
        bk = await BOOKS.find_one({'id': mb}) or {}
        check('chapter mismatch -> failed with clear message, no sets', bk.get('status') == 'failed' and 'reads as JEE Main' in (bk.get('message') or '') and await SETS.count_documents({'chapter_book_id': mb}) == 0, (bk.get('status'), bk.get('message')))
        async def fake_bit(*a, **k): return fake_chapter_result('BITSAT')
        chapter_books.organise_pdfs = fake_bit
        r = await chapter_upload(own, 'bitsat:chapters'); ob = r.json().get('id')
        bk = await BOOKS.find_one({'id': ob}) or {}; ss = await SETS.find({'chapter_book_id': ob}).to_list(5)
        check('chapter ok -> ready, sets placed in bitsat:chapters exam BITSAT', bk.get('status') == 'ready' and ss and all(x.get('catalog_section_id') == 'bitsat:chapters' and x.get('exam') == 'BITSAT' for x in ss), (bk.get('status'), bk.get('message'), [(x.get('catalog_section_id'), x.get('exam')) for x in ss]))
        check('chapter sets stay draft/not live (nothing auto-publishes)', ss and all(x.get('status') == 'draft' and not x.get('live_enabled') for x in ss), [(x.get('status'), x.get('live_enabled')) for x in ss])
        r = await chapter_upload(own, nch); cb = r.json().get('id')
        bk = await BOOKS.find_one({'id': cb}) or {}; ss = await SETS.find({'chapter_book_id': cb}).to_list(5)
        check('custom chapters section -> set exam == custom key', bk.get('status') == 'ready' and ss and all(x.get('exam') == ckey and x.get('catalog_section_id') == nch for x in ss), (bk.get('status'), bk.get('message'), [(x.get('exam'), x.get('catalog_section_id')) for x in ss]))
    finally:
        chapter_books.organise_pdfs = real_org

    # ===== book_view scheduled override + legacy publish
    mocks = [{'n': 1, 'qs': q3('V1'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]}, {'n': 2, 'qs': q3('V2'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]}]
    b = await upload(own, build_pdf(mocks), 'TEST_QA174 Book', section_id='bitsat:mocks'); bkid = b['id']
    r, view = await complete(own, bkid); mid = {m['label']: m['id'] for m in view['mocks']}
    check('book 2 ready', [m['state'] for m in view['mocks']] == ['ready', 'ready'], [m['state'] for m in view['mocks']])
    fut = time.time() + 3600
    r = await own.post(f'/api/admin/books/{bkid}/control', json={'revision': view['revision'], 'action': 'publish_ready', 'mock_id': mid['Mock 1'], 'release_at': fut}); await drain()
    view = (await own.get(f'/api/admin/books/{bkid}')).json(); st = {m['label']: m for m in view['mocks']}
    check('mock 1 scheduled; counts.scheduled==1', st['Mock 1']['state'] == 'scheduled' and view['counts']['scheduled'] == 1 and view['counts']['ready'] == 1, (st['Mock 1']['state'], view['counts']))
    check('book-level release_at not set by per-mock schedule', view.get('release_at') in (None, 0), view.get('release_at'))
    r = await own.post(f'/api/admin/books/{bkid}/control', json={'revision': view['revision'], 'action': 'publish_ready', 'mock_id': mid['Mock 2']}); await drain()
    view = (await own.get(f'/api/admin/books/{bkid}')).json(); st = {m['label']: m for m in view['mocks']}
    check('mock 2 published now, mock 1 still scheduled', st['Mock 2']['state'] == 'published' and st['Mock 1']['state'] == 'scheduled', {k: v['state'] for k, v in st.items()})
    # time passes for mock 1: move its release_at + set start into the past
    past = time.time() - 5
    await H.TDB.tejas_book_mocks.update_one({'_id': mid['Mock 1']}, {'$set': {'release_at': past}})
    await SETS.update_one({'id': st['Mock 1']['set_id']}, {'$set': {'start_at': past}})
    view = (await own.get(f'/api/admin/books/{bkid}')).json(); st = {m['label']: m for m in view['mocks']}
    check('after its release_at mock 1 shows published', st['Mock 1']['state'] == 'published' and view['counts']['scheduled'] == 0 and view['counts']['published'] == 2, (st['Mock 1']['state'], view['counts']))
    # legacy publish
    r = await own.post(f'/api/admin/books/{bkid}/control', json={'revision': view['revision'], 'action': 'publish'}); await drain()
    check('legacy publish 200 and auto_publish False', r.status_code == 200 and r.json().get('auto_publish') is False, (r.status_code, r.text[:150]))
    bdoc = await H.TDB.tejas_books.find_one({'_id': bkid}) or await H.TDB.tejas_books.find_one({'id': bkid}) or {}
    print('book doc auto_publish (db):', (bdoc.get('payload') or bdoc).get('auto_publish'))
    # resume_mock of a per-mock scheduled mock
    b3 = await upload(own, build_pdf([{'n': 1, 'qs': q3('R1'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]}]), 'TEST_QA174 Resume', section_id='bitsat:mocks')
    r, v3 = await complete(own, b3['id']); m3 = v3['mocks'][0]['id']
    await own.post(f'/api/admin/books/{b3["id"]}/control', json={'revision': v3['revision'], 'action': 'publish_ready', 'release_at': time.time() + 7200}); await drain()
    v3 = (await own.get(f'/api/admin/books/{b3["id"]}')).json()
    await own.post(f'/api/admin/books/{b3["id"]}/control', json={'revision': v3['revision'], 'action': 'pause_mock', 'mock_id': m3, 'reason': 'TEST pause'})
    v3 = (await own.get(f'/api/admin/books/{b3["id"]}')).json()
    r = await own.post(f'/api/admin/books/{b3["id"]}/control', json={'revision': v3['revision'], 'action': 'resume_mock', 'mock_id': m3, 'reason': 'TEST resume'})
    v3 = (await own.get(f'/api/admin/books/{b3["id"]}')).json()
    check('resume_mock keeps per-mock scheduled state (release in future)', v3['mocks'][0]['state'] == 'scheduled', (r.status_code, v3['mocks'][0]['state'], v3['mocks'][0].get('release_at')))


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
