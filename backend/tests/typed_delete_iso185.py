"""TEST-ONLY iteration 185: upload resume from Library, edit-all questions + typed missing options, series day Live/Off,
Library permanent delete (score lines kept), deleted results for students, body limits.
Isolated disposable DB via iso_harness_book170 (storage + AI mocked). Run: cd /app/backend && timeout 280 python tests/typed_delete_iso185.py
"""
import asyncio, hashlib, math, sys, time, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fitz  # noqa: E402
import book_publishing_iso170 as T  # noqa: E402,F401
from book_publishing_iso170 import H, mkstaff, client, q3, upload, put_part, complete, drain, check, RESULTS  # noqa: E402
from structure_iso173 import mkset, start  # noqa: E402
from tejas import structure, live_series  # noqa: E402

DB = H.TDB
SETS, BM = DB.tejas_sets, DB.tejas_book_mocks
M = '/api/admin/master'


def J(r):
    try: d = r.json()
    except Exception: return {}
    return d if d is not None else {}


def two_opt_pdf(tag='TWO'):
    doc = fitz.open(); p = doc.new_page(); p.insert_text((40, 60), 'Physics', fontsize=13); y = 100
    qs = [(1, f'{tag} a ball falls 20 m. Find time.', ['1 s', '2 s', '3 s', '4 s']), (2, f'{tag} a car speed is', ['1 m/s', '2 m/s']),
          (3, f'{tag} unit of force is', ['joule', 'newton', 'watt', 'pascal'])]
    for num, text, opts in qs:
        p.insert_text((40, y), f'Q{num}. {text}', fontsize=11); y += 20
        for lab, o in zip('ABCD', opts): p.insert_text((60, y), f'({lab}) {o}', fontsize=11); y += 18
        y += 22
    p = doc.new_page(); p.insert_text((40, 60), 'Answer Key', fontsize=13); y = 100
    for num, ans in [(1, 'B'), (2, 'B'), (3, 'B')]: p.insert_text((40, y), f'Q{num}. ({ans})', fontsize=11); y += 20
    raw = doc.tobytes(); doc.close(); return raw


async def resume_tests(own, sec):
    raw = two_opt_pdf('RES') + b'\n%' + uuid.uuid4().hex.encode() * 40000  # make it several parts
    sha = hashlib.sha256(raw).hexdigest()
    body = {'filename': 'res.pdf', 'title': 'TEST_Resume', 'sha256': sha, 'size': len(raw), 'rights_confirmed': True, 'section_id': sec}
    b = J(await own.post('/api/admin/books', json=body)); bid = b.get('id'); ch = b.get('chunk_size', 1); total = math.ceil(len(raw) / ch)
    check('resume fixture has >=3 parts', total >= 3, (total, ch))
    for n in range(2):
        r = await put_part(own, bid, n, raw[n * ch:(n + 1) * ch]); assert r.status_code == 200, r.text
    r = await own.post(f'{M}/uploads/book/{bid}/dismiss'); check('half-sent upload moved to Library', r.status_code == 200 and (await DB.tejas_books.find_one({'_id': bid})).get('archived'), (r.status_code, r.text[:200]))
    r = await own.post('/api/admin/books', json=body); d = J(r); doc = await DB.tejas_books.find_one({'_id': bid})
    check('re-upload same PDF+section resumes SAME id', r.status_code == 200 and d.get('id') == bid and d.get('state') == 'uploading', (r.status_code, d.get('id'), bid, d.get('state')))
    check('resumed copy no longer archived', not doc.get('archived') and 'archived_at' not in doc, {k: doc.get(k) for k in ('archived', 'paused')})
    check('received_parts lists already-sent parts', sorted(d.get('received_parts') or []) == [0, 1], d.get('received_parts'))
    for n in range(2, total):
        r = await put_part(own, bid, n, raw[n * ch:(n + 1) * ch]); assert r.status_code == 200, r.text
    r = await own.post(f'/api/admin/books/{bid}/complete'); await drain()
    check('remaining parts + complete works', r.status_code == 200, r.text[:200])
    other = await own.post('/api/admin/catalog/exams', json={'name': 'Resume Exam ' + uuid.uuid4().hex[:4], 'short': 'RX', 'subjects': ['Physics'], 'color': 'rose'})
    slug2 = J(other).get('slug')
    sec2 = J(await own.post(f'/api/admin/catalog/exams/{slug2}/sections', json={'name': 'Mock Tests', 'description': '', 'layout': 'list', 'kind': 'mocks'})).get('id')
    r = await own.post('/api/admin/books', json={**body, 'section_id': sec2})
    check('different section_id creates a new book id', r.status_code == 200 and J(r).get('id') != bid, (r.status_code, r.text[:150]))


async def typed_tests(own, rev, stu, sec, slug):
    b = await upload(own, two_opt_pdf(), 'TEST_TwoOpt', section_id=sec); await complete(own, b['id']); await drain()
    m = await BM.find_one({'book_id': b['id']}) or {}
    mid = m.get('_id'); base = f"/api/admin/books/{b['id']}/mocks/{mid}"
    print('two-option mock', m.get('state'), m.get('issues', [])[:3], [(q['original_number'], list(q.get('options', {}))) for q in m.get('questions', [])])
    p = J(await own.get(base + '/problems', params={'all': 'true'}))
    q0 = next((x for x in p.get('questions', []) if x['number'] == 2), {})
    if m.get('state') == 'held':  # parser holds a 2-option question: confirm it as a 2-option MCQ first so the mock is READY
        r = await own.post(base + '/fix', json={'revision': p['revision'], 'question_id': q0.get('id'), 'response_type': 'mcq', 'option_labels': ['A', 'B'], 'answer': 'B', 'complete': True}); await drain()
        m = await BM.find_one({'_id': mid}); check('2-option confirm makes mock ready', r.status_code == 200 and m['state'] == 'ready', (r.status_code, m['state'], m.get('issues')))
        p = J(await own.get(base + '/problems', params={'all': 'true'}))
    qs = p.get('questions', [])
    check('owner all=true lists every question', len(qs) == len(m.get('questions', [])) == 3, (len(qs), p.get('state')))
    q = next((x for x in qs if x['number'] == 2), {})
    check('all=true question has fields', all(k in q for k in ('id', 'subject', 'number', 'type', 'options', 'typed_options', 'answer', 'pages', 'question_images')), sorted(q))
    check('Q2 shows only 2 options', q.get('options') == ['A', 'B'], q.get('options'))
    p2 = J(await own.get(base + '/problems'))
    check('without all only marked questions', all(x['issues'] for x in p2.get('questions', [])), [(x['number'], x['issues']) for x in p2.get('questions', [])])
    r = await rev.get(base + '/problems', params={'all': 'true'})
    check('reviewer all=true on ready mock 404', (m.get('state') != 'held' and r.status_code == 404) or (m.get('state') == 'held' and all(x['issues'] for x in J(r).get('questions', []))), (r.status_code, m.get('state')))
    fix = {'revision': p['revision'], 'question_id': q.get('id'), 'response_type': 'mcq', 'option_labels': ['A', 'B', 'C', 'D'], 'answer': 'C', 'complete': True}
    r = await own.post(base + '/fix', json={**fix, 'option_texts': {'C': 'x' * 2001}}); check('typed option over 2000 chars 422', r.status_code == 422, (r.status_code, r.text[:150]))
    r = await own.post(base + '/fix', json={**fix, 'option_texts': {'C': '\u221a' * 1500 + ' 2\u221a3 m/s', 'D': 'y' * 1900}, 'revision': p['revision'] + 999})
    check('~10KB body accepted by route limit (409 revision, not 413)', r.status_code == 409, (r.status_code, r.text[:150]))
    r = await own.post(base + '/fix', json={**fix, 'option_texts': {'C': '2\u221a3 m/s', 'D': '4 m/s', 'E': 'dropped'}}); await drain()
    check('typed fix on ready mock 200 + Saved message', r.status_code == 200 and 'Saved' in J(r).get('message', ''), (r.status_code, r.text[:200]))
    m = await BM.find_one({'_id': mid}); mq = next((x for x in m['questions'] if x['original_number'] == 2), {})
    bk = await DB.tejas_books.find_one({'_id': b['id']})
    check('book back to ready after recheck', bk.get('state') == 'ready' and m['state'] == 'ready', (bk.get('state'), m['state'], m.get('issues')))
    check('question now A-D with typed C,D; E dropped', sorted(mq.get('options', {})) == ['A', 'B', 'C', 'D'] and mq.get('typed_options') == {'C': '2\u221a3 m/s', 'D': '4 m/s'}, (mq.get('options'), mq.get('typed_options')))
    p = J(await own.get(base + '/problems', params={'all': 'true'})); q = next((x for x in p.get('questions', []) if x['number'] == 2), {})
    check('all=true shows typed_options + answer C', q.get('typed_options') == {'C': '2\u221a3 m/s', 'D': '4 m/s'} and q.get('answer') == 'C', (q.get('typed_options'), q.get('answer')))
    row = next((x for x in J(await own.get(f'{M}/types/{sec}/mocks'))['items'] if x['id'] == mid), {})
    check('Master row Draft, nothing to fix', row.get('status') == 'draft' and row.get('to_fix') == 0 and row.get('kind') == 'book_mock', row)
    r = await own.post(M + '/status', json={'items': [{'kind': 'book_mock', 'id': mid}], 'to': 'live'}); await drain()
    sid = (await BM.find_one({'_id': mid})).get('set_id'); s = await SETS.find_one({'id': sid}) or {}
    sq = next((x for x in s.get('questions', []) if x.get('typed_options')), {})
    check('published set question carries typed_options', J(r).get('done') == 1 and sq.get('typed_options') == {'C': '2\u221a3 m/s', 'D': '4 m/s'}, (r.text[:200], [x.get('typed_options') for x in s.get('questions', [])]))
    r = await start(stu, sid); a = J(r); aid = a.get('id')
    aq = [x for x in (a.get('questions') or J(await stu.get(f'/api/attempts/{aid}')).get('questions', [])) if x.get('typed_options')]
    check('student attempt question has typed_options', r.status_code == 200 and aq and aq[0]['typed_options'].get('D') == '4 m/s', (r.status_code, r.text[:200]))
    r = await stu.post(f'/api/attempts/{aid}/submit'); await asyncio.sleep(0.5)
    res = J(await stu.get(f'/api/attempts/{aid}/results'))
    check('results review includes typed_options', '4 m/s' in str(res) and 'typed_options' in str(res), (r.status_code, str(res)[:300]))
    return sid, aid


async def series_tests(own, stu):
    t = time.time(); w = live_series.window('2026-12-02'); shift = t - w['opens_at'] - 600
    w = {k: (v + shift if isinstance(v, (int, float)) else v) for k, v in w.items()}
    pid = await mkset('SDAY', exam='JEE Main', series_id=live_series.SERIES_ID, series_date='2026-12-02', test_kind='mock', series_import=True, series_window=w, live_enabled=True, start_at=0, end_at=4e9)
    await DB.tejas_series.update_one({'_id': live_series.SERIES_ID}, {'$set': {'shown': True}})
    await structure.exams.update_one({'_id': 'jee-main'}, {'$set': {'shown': True}})
    url = f'/api/series/{live_series.SERIES_ID}/schedule'
    day = lambda d: next((x for x in J(d).get('slots', []) if x['date'] == '2026-12-02'), {})
    sl = day(await stu.get(url)); check('open day paper visible to students', sl.get('ready') and sl.get('set_id') == pid, (sl, (await stu.get(url)).status_code))
    st = next((x for x in J(await own.get(f'{M}/series/{live_series.SERIES_ID}')).get('slots', []) if x['date'] == '2026-12-02'), {})
    check('studio day paper kind set, off False', (st.get('paper') or {}).get('kind') == 'set' and (st.get('paper') or {}).get('off') is False, st.get('paper'))
    r = await own.post(f'{M}/series/{live_series.SERIES_ID}/live', json={'id': pid, 'live': False})
    sl = day(await stu.get(url)); st = next((x for x in J(await own.get(f'{M}/series/{live_series.SERIES_ID}')).get('slots', []) if x['date'] == '2026-12-02'), {})
    check('Off hides open day paper (not ready, no set_id)', r.status_code == 200 and 'Switched off' in J(r).get('message', '') and not sl.get('ready') and not sl.get('set_id'), (r.text[:150], sl))
    check('studio shows paper off', (st.get('paper') or {}).get('off') is True, st.get('paper'))
    r = await stu.post(f'/api/sets/{pid}/preflight', json={}); check('Off paper cannot be started', r.status_code in (403, 404, 409), r.status_code)
    r = await own.post(f'{M}/series/{live_series.SERIES_ID}/live', json={'id': pid, 'live': True}); sl = day(await stu.get(url))
    check('Live again restores', r.status_code == 200 and sl.get('ready') and sl.get('set_id') == pid, sl)
    other = await mkset('NOSER', exam='JEE Main', test_kind='mock')
    r = await own.post(f'{M}/series/{live_series.SERIES_ID}/live', json={'id': other, 'live': False}); check('set not in series 404', r.status_code == 404, r.status_code)
    rev_r = await stu.post(f'{M}/series/{live_series.SERIES_ID}/live', json={'id': pid, 'live': False}); check('student denied series live', rev_r.status_code in (401, 403), rev_r.status_code)


async def delete_tests(own, rev, stu, typed_sid, typed_aid):
    L = '/api/admin/library'
    # Archived tests with attempts.
    a1 = await mkset('DEL1', exam='JEE Main', catalog_section_id='jee-main:mocks', test_kind='mock')
    a2 = await mkset('DEL2', exam='JEE Main', catalog_section_id='jee-main:mocks', test_kind='mock')
    live = await mkset('KEEP', exam='JEE Main', catalog_section_id='jee-main:mocks', test_kind='mock')
    r = await start(stu, a1); att = J(r).get('id'); await stu.post(f'/api/attempts/{att}/submit'); await asyncio.sleep(0.3)
    before = J(await stu.get(f'/api/attempts/{att}/results'))
    await DB.tejas_saved_tests.insert_one({'id': 'sv-' + a1, 'set_id': a1, 'user_id': 'x'}); await DB.tejas_versions.insert_one({'id': 'v-' + a1, 'set_id': a1})
    await DB.tejas_question_solutions.insert_one({'id': 'qs-' + a1, 'set_id': a1})
    r = await own.post(M + '/status', json={'items': [{'kind': 'set', 'id': a1}, {'kind': 'set', 'id': a2}], 'to': 'library'}); check('two tests to Library', J(r).get('done') == 2, r.text[:200])
    for who, c in (('student', stu), ('reviewer', rev), ('anon', client())):
        r = await c.post(L + '/delete', json={'ids': [a1], 'confirm': 'DELETE'}); check(f'{who} cannot delete ({r.status_code})', r.status_code in (401, 403), r.status_code)
    r = await own.post(L + '/delete', json={'ids': [a1]}); check('missing confirm 422', r.status_code == 422, r.status_code)
    r = await own.post(L + '/delete', json={'ids': [a1], 'confirm': 'delete'}); check('wrong confirm 422', r.status_code == 422, r.status_code)
    # active attempt blocks
    r = await start(stu, a2); act = J(r).get('id')
    if not act:  # a2 archived: cannot start, inject an active attempt
        act = 'TEST_act_' + uuid.uuid4().hex[:6]
        await DB.tejas_attempts.insert_one({'id': act, 'set_id': a2, 'user_id': 'x', 'status': 'active', 'deadline': time.time() + 3600, 'title': 'x'})
    r = await own.post(L + '/delete', json={'ids': [a1, a2], 'confirm': 'DELETE'})
    check('active attempt -> 409, nothing deleted', r.status_code == 409 and 'still writing' in r.text and await SETS.find_one({'id': a1}), (r.status_code, r.text[:150]))
    await DB.tejas_attempts.update_one({'id': act}, {'$set': {'deadline': time.time() - 10}})
    r = await own.post(L + '/delete', json={'ids': [a1, a2, live], 'confirm': 'DELETE'}); d = J(r)
    check('delete 2 archived, ignore non-archived', r.status_code == 200 and d.get('deleted') == 2 and '2 tests deleted for good. Students keep their score lines.' in d.get('message', ''), r.text[:200])
    check('non-archived test kept', await SETS.find_one({'id': live}) is not None)
    check('sets + saved/solutions/versions removed', not await SETS.find_one({'id': a1}) and not await DB.tejas_saved_tests.find_one({'set_id': a1})
          and not await DB.tejas_versions.find_one({'set_id': a1}) and not await DB.tejas_question_solutions.find_one({'set_id': a1}))
    at = await DB.tejas_attempts.find_one({'id': att})
    check('attempt kept with set_deleted + title/summary', at and at.get('set_deleted') and at.get('title') and at.get('summary') is not None, at and {k: at.get(k) for k in ('set_deleted', 'title')})
    r = await stu.get(f'/api/attempts/{att}/results'); d = J(r)
    check('student results status deleted with title + summary', r.status_code == 200 and d.get('status') == 'deleted' and d.get('title') and 'summary' in d and 'questions' not in d, (r.status_code, str(d)[:300], str(before)[:100]))
    hist = J(await stu.get('/api/my/history')) if (await stu.get('/api/my/history')).status_code == 200 else {}
    print('history keys', str(hist)[:200])
    # Typed book mock published from a PDF: archive set -> delete -> upload gone when last test.
    bid = (await SETS.find_one({'id': typed_sid}) or {}).get('book_import_id')
    r = await own.post(M + '/status', json={'items': [{'kind': 'set', 'id': typed_sid}], 'to': 'library'})
    others = [x['_id'] for x in await BM.find({'book_id': bid, 'set_id': None}).to_list(10)]
    bk = await DB.tejas_books.find_one({'_id': bid}) or {}
    print('book after archiving its live test', bk.get('archived'), 'other mocks', others)
    await DB.tejas_books.update_one({'_id': bid}, {'$set': {'archived': True}})
    r = await own.post(L + '/delete', json={'ids': [typed_sid], 'confirm': 'DELETE'}); d = J(r)
    check('last test of archived upload: upload + pages/mocks/parts removed', r.status_code == 200 and not await DB.tejas_books.find_one({'_id': bid}) and not await DB.tejas_book_pages.find_one({'book_id': bid}) and not await BM.find_one({'book_id': bid}) and not await DB.tejas_book_parts.find_one({'book_id': bid}) and d.get('uploads') == 1, (r.text[:200]))
    r = await stu.get(f'/api/attempts/{typed_aid}/results'); check('typed attempt shows deleted', J(r).get('status') == 'deleted', r.text[:150])
    # Upload still used by a test outside Library is NOT removed.
    await DB.tejas_imports.insert_one({'id': 'imp-185', 'title': 'TEST imp', 'archived': True, 'destination': {}})
    u1 = await mkset('IMP1', exam='JEE Main', test_kind='mock', import_id='imp-185', archived=True)
    u2 = await mkset('IMP2', exam='JEE Main', test_kind='mock', import_id='imp-185')
    r = await own.post(L + '/delete', json={'ids': [u1], 'confirm': 'DELETE'})
    check('upload used outside Library kept', r.status_code == 200 and await DB.tejas_imports.find_one({'id': 'imp-185'}) and await SETS.find_one({'id': u2}), r.text[:150])
    r = await own.post(L + '/delete', json={'uploads': [{'kind': 'import', 'id': 'imp-185'}], 'confirm': 'DELETE'})
    check('upload ref with test outside Library -> 409 nothing changes', r.status_code == 409 and await DB.tejas_imports.find_one({'id': 'imp-185'}) and await SETS.find_one({'id': u2}), (r.status_code, r.text[:150]))
    await SETS.update_one({'id': u2}, {'$set': {'archived': True}})
    r = await own.post(L + '/delete', json={'uploads': [{'kind': 'import', 'id': 'imp-185'}], 'confirm': 'DELETE'}); d = J(r)
    check('upload ref delete removes upload + its Library tests', r.status_code == 200 and not await DB.tejas_imports.find_one({'id': 'imp-185'}) and not await SETS.find_one({'id': u2}) and d.get('uploads') == 1, r.text[:200])
    # Draft book mock in Library -> deleted:true and gone from uploads list.
    await DB.tejas_books.insert_one({'_id': 'bk-185', 'removed': False, 'paused': False, 'state': 'ready', 'created_at': time.time(), 'payload': {'title': 'bk185', 'destination': {'section_id': 'jee-main:mocks'}}})
    await BM.insert_one({'_id': 'bm-185', 'book_id': 'bk-185', 'label': 'Mock 9', 'set_id': None, 'state': 'ready', 'archived': True, 'order': 1, 'questions': []})
    ups = [u for u in J(await own.get(L)).get('uploads', []) if u['id'] == 'bm-185']; check('archived draft mock listed in uploads', len(ups) == 1, ups)
    r = await own.post(L + '/delete', json={'uploads': [{'kind': 'book_mock', 'id': 'bm-185'}], 'confirm': 'DELETE'})
    ups = [u for u in J(await own.get(L)).get('uploads', []) if u['id'] == 'bm-185']
    check('book_mock delete -> deleted:true, gone from uploads', r.status_code == 200 and (await BM.find_one({'_id': 'bm-185'})).get('deleted') and not ups, (r.text[:150], ups))
    # Bulk restore of 160 ids accepted (128 KB limit).
    ids = ['TEST_S173_BULK_' + uuid.uuid4().hex for _ in range(160)]
    r = await own.post(L + '/restore', json={'ids': ids}); check('bulk restore 160 ids accepted', r.status_code == 200, (r.status_code, r.text[:150]))
    r = await own.post(L + '/delete', json={'ids': ids, 'confirm': 'DELETE'}); check('bulk delete 160 ids accepted', r.status_code == 200 and J(r).get('deleted') == 0, (r.status_code, r.text[:150]))
    r = await own.post(L + '/delete', json={'ids': [], 'uploads': [], 'confirm': 'DELETE'}); check('empty delete 422', r.status_code == 422, r.status_code)


async def main():
    check('no customer DB handles', not H.leftover_real_handles(), H.leftover_real_handles())
    await H.tdbmod.indexes(); await structure.seed()
    own, _ = await mkstaff('owner', 'd'); rev, _ = await mkstaff('reviewer', 'd')
    stu = client(); await stu.post('/api/auth/phone/signup', json={'phone': '92' + str(uuid.uuid4().int)[:8], 'pin': '8261', 'confirm_pin': '8261'})
    try:
        r = await own.post('/api/admin/catalog/exams', json={'name': 'NEETX', 'short': 'NX', 'subjects': ['Physics', 'Chemistry', 'Biology'], 'color': 'rose'})
        slug = J(r).get('slug')
        sec = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Mock Tests', 'description': '', 'layout': 'list', 'kind': 'mocks'})).get('id')
        await structure.exams.update_one({'_id': slug}, {'$set': {'shown': True}})
        for name, coro in (('resume', resume_tests(own, sec)), ('typed', typed_tests(own, rev, stu, sec, slug))):
            try: out = await coro
            except Exception as e: check(f'{name} block crashed', False, repr(e)); out = None
            if name == 'typed': typed = out
        try: await series_tests(own, stu)
        except Exception as e: check('series block crashed', False, repr(e))
        try: await delete_tests(own, rev, stu, *(typed or (None, None)))
        except Exception as e: import traceback; traceback.print_exc(); check('delete block crashed', False, repr(e))
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
    failed = [r for r in RESULTS if not r[1]]
    print(f'\nTOTAL {len(RESULTS)} PASS {len(RESULTS) - len(failed)} FAIL {len(failed)}')
    sys.exit(1 if failed else 0)

if __name__ == '__main__':
    asyncio.run(main())
