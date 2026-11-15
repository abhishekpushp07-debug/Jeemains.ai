"""TEST-ONLY iteration 181: Master (exam > mock type > mock), written mocks, five statuses, per-exam test series, single-paper PDF.
Isolated disposable DB via iso_harness_book170 (storage + AI mocked). Customer DB never written.
Run: cd /app/backend && timeout 280 python tests/master_iso181.py
"""
import asyncio, io, sys, time, uuid
from datetime import datetime, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fitz  # noqa: E402
import book_publishing_iso170 as T  # noqa: E402,F401
from book_publishing_iso170 import H, mkstaff, client, build_pdf, q3, upload, complete, drain, check, RESULTS  # noqa: E402
from structure_iso173 import mkset, start  # noqa: E402
from tejas import structure, live_series  # noqa: E402

SETS, BM = H.TDB.tejas_sets, H.TDB.tejas_book_mocks
M = '/api/admin/master'


def J(r):
    try: d = r.json()
    except Exception: return {}
    if isinstance(d, dict) and 'data' in d and len(d) <= 2: d = d['data']
    return d if d is not None else {}


def single_pdf(n=3):
    doc = fitz.open(); p = doc.new_page(); p.insert_text((40, 60), 'Physics', fontsize=13); y = 100
    for num, text, opts in q3('ONE')[:n]:
        p.insert_text((40, y), f'Q{num}. {text}', fontsize=11); y += 20
        for lab, o in zip('ABCD', opts): p.insert_text((60, y), f'({lab}) {o}', fontsize=11); y += 18
        y += 22
    p = doc.new_page(); p.insert_text((40, 60), 'Answer Key', fontsize=13); y = 100
    for num, ans in [(1, 'B'), (2, 'B'), (3, 'C')][:n]: p.insert_text((40, y), f'Q{num}. ({ans})', fontsize=11); y += 20
    raw = doc.tobytes(); doc.close(); return raw


def mcq(text, answer='B', **kw):
    return {'id': '', 'subject': 'Physics', 'chapter': '', 'text': text, 'image': '', 'type': 'mcq', 'options': [{'text': x, 'image': ''} for x in 'wxyz'],
            'answer': answer, 'solution': '', 'solution_image': '', **kw}


async def nav(stu, slug, section):
    r = await stu.get(f'/api/exam-navigation/{slug}/catalogue', params={'section': section})
    return [x['id'] for x in J(r).get('items', [])], r.status_code


async def status(own, to, items, **kw):
    r = await own.post(M + '/status', json={'items': items, 'to': to, **kw}); return r.status_code, J(r)


async def written(own, sid, title, n, **kw):
    r = await own.post(f'{M}/types/{sid}/written', json={'title': title, **kw}); wid = J(r).get('id')
    for i in range(n):
        await own.put(f'{M}/written/{wid}/questions', json=mcq(f'{title} question {i + 1}'))
    return wid, r


async def main():
    own, _ = await mkstaff('owner', 'm'); rev, _ = await mkstaff('reviewer', 'm'); anon = client()
    stu = client(); await stu.post('/api/auth/phone/signup', json={'phone': '93' + str(uuid.uuid4().int)[:8], 'pin': '8261', 'confirm_pin': '8261'})
    # --- structure
    r = await own.post('/api/admin/catalog/exams', json={'name': 'NEET', 'short': 'NEET', 'subjects': ['Physics', 'Chemistry', 'Biology'], 'color': 'rose'})
    slug = J(r).get('slug'); check('create exam', r.status_code == 200 and slug, r.text[:200])
    async def add(kind, name, **kw):
        return await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': name, 'description': '', 'layout': 'list', 'kind': kind, **kw})
    r = await add('mocks', 'Mock Tests', minutes=200, correct=4, wrong=-1); mock_t = J(r); check('add Mock type with defaults', r.status_code == 200 and mock_t.get('defaults') == {'minutes': 200, 'correct': 4, 'wrong': -1}, r.text[:300])
    r = await add('mocks', 'Mock Tests 2'); check('second Mock type refused 409', r.status_code == 409, r.status_code)
    r = await add('custom', 'Revision Tests'); r2 = await add('custom', 'Crash Course'); check('two own types allowed', r.status_code == 200 and r2.status_code == 200, (r.status_code, r2.status_code))
    r = await add('pyq', 'PYQ'); pyq_t = J(r); check('add PYQ type', r.status_code == 200 and pyq_t.get('kind') == 'pyq', r.text[:200])
    r = await add('chapters', 'Chapter-wise'); chap_t = J(r); check('chapter type has chapters layout', chap_t.get('layout') == 'chapters', chap_t)
    today = datetime.now(live_series.IST).date()
    r = await add('aits', 'All India Test Series', first_date=(today + timedelta(days=3)).isoformat(), days=5, open_time='09:00', last_start='11:00'); aits_t = J(r)
    ser = aits_t.get('series_id'); check('add series type', r.status_code == 200 and ser, r.text[:300])
    r = await add('aits', 'Series 2', first_date=today.isoformat(), days=5); check('second series refused 409', r.status_code == 409, r.status_code)
    r = await rev.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'X1', 'description': '', 'layout': 'list'}); check('reviewer cannot add type 403', r.status_code == 403, r.status_code)
    r = await own.patch('/api/admin/catalog/sections/' + mock_t['id'], json={'minutes': 180}); check('type defaults editable', J(r).get('defaults', {}).get('minutes') == 180, r.text[:200])
    # --- written mock
    r = await own.post(f"{M}/types/{mock_t['id']}/written", json={'title': 'Written One'}); wid = J(r).get('id'); check('create written draft', r.status_code == 200 and wid, r.text[:200])
    sc, d = await status(own, 'live', [{'kind': 'set', 'id': wid}]); check('empty written cannot go live', d.get('done') == 0 and d.get('skipped'), d)
    r = await own.put(f'{M}/written/{wid}/questions', json=mcq('A ball of mass $m$ falls. Find $v^2$.')); q1 = J(r).get('id'); check('save mcq question', r.status_code == 200 and q1, r.text[:300])
    r = await own.put(f'{M}/written/{wid}/questions', json={**mcq('Value of n?'), 'type': 'integer', 'options': [], 'answer': '-12'}); check('save numerical question', r.status_code == 200, r.text[:200])
    r = await own.put(f'{M}/written/{wid}/questions', json=mcq('Bad', answer='E')); check('answer outside options 422', r.status_code == 422, r.status_code)
    r = await own.put(f'{M}/written/{wid}/questions', json={**mcq('Dec'), 'type': 'integer', 'options': [], 'answer': '1.5'}); check('decimal numerical 422', r.status_code == 422, r.status_code)
    r = await own.put(f'{M}/written/{wid}/questions', json=mcq('Broken $\\frac{1}{$ maths')); check('unreadable maths 422', r.status_code == 422, (r.status_code, r.text[:120]))
    paste = 'Chemistry\n3. Which is a noble gas?\n(A) He (B) O (C) N (D) H\nAnswer: A\n4. Atomic number of carbon is\n5. pH of pure water at 25 C is\n(1) 1\n(2) 7\n(3) 9\n(4) 14\n\nAnswer Key\n4. 6  5. 2\nSolutions\n5. Neutral water has pH 7.'
    r = await own.post(f'{M}/written/{wid}/paste', json={'text': paste}); d = J(r); check('paste splits 3 questions, none flagged', r.status_code == 200 and d.get('added') == 3 and d.get('flags') == 0, r.text[:300])
    doc = J(await own.get(f'{M}/written/{wid}')); qs = doc.get('questions', [])
    check('pasted: subject, key list, numbered options, solution', len(qs) == 5 and qs[2]['subject'] == 'Chemistry' and qs[2]['answer'] == 'A' and qs[3]['type'] == 'integer' and qs[3]['answer'] == '6' and qs[4]['answer'] == 'B' and 'pH 7' in qs[4]['solution'], [(q['subject'], q['type'], q['answer']) for q in qs])
    r = await own.post(f'{M}/written/{wid}/paste', json={'text': 'Physics\n6. No key here?\n(A) a (B) b (C) c (D) d'}); check('paste without key is flagged', J(r).get('flags') == 1, r.text[:200])
    items = J(await own.get(f"{M}/types/{mock_t['id']}/mocks")).get('items', []); row = next((x for x in items if x['id'] == wid), {})
    check('list row: draft with 1 to fix', row.get('status') == 'draft' and row.get('to_fix') == 1 and row.get('count') == 6, row)
    sc, d = await status(own, 'live', [{'kind': 'set', 'id': wid}]); check('flagged mock cannot go live, reason given', d.get('done') == 0 and 'fix' in d['skipped'][0]['reason'], d)
    # reviewer scope
    flagged = next(q for q in J(await own.get(f'{M}/written/{wid}'))['questions'] if q['flag'])
    r = await rev.get(f'{M}/written/{wid}'); check('reviewer reads flagged draft', r.status_code == 200, r.status_code)
    r = await rev.put(f'{M}/written/{wid}/questions', json={**mcq('x'), 'id': q1}); check('reviewer cannot edit unmarked question 403', r.status_code == 403, r.status_code)
    r = await rev.put(f'{M}/written/{wid}/questions', json=mcq('new')); check('reviewer cannot add question 403', r.status_code == 403, r.status_code)
    for name, call in (('paste', rev.post(f'{M}/written/{wid}/paste', json={'text': '1. abcdefghij'})), ('status', rev.post(M + '/status', json={'items': [{'kind': 'set', 'id': wid}], 'to': 'live'})),
                       ('type list', rev.get(f"{M}/types/{mock_t['id']}/mocks")), ('summary', rev.get(M + '/summary')), ('series', rev.get(f'{M}/series/{ser}'))):
        r = await call; check(f'reviewer {name} 403', r.status_code == 403, r.status_code)
    r = await rev.get(M + '/fix'); check('reviewer fix list has the written mock, no ready list', any(x['id'] == wid for x in J(r).get('items', [])) and J(r).get('ready') == [], r.text[:200])
    r = await rev.put(f'{M}/written/{wid}/questions', json={**mcq('No key here?', answer='C'), 'id': flagged['id']}); check('reviewer fixes the marked question', r.status_code == 200 and J(r).get('flags') == 0, r.text[:200])
    r = await rev.get(f'{M}/written/{wid}'); check('reviewer loses access once nothing is marked 404', r.status_code == 404, r.status_code)
    for who, c, exp in (('anon', anon, 401), ('student', stu, 403)):
        r = await c.get(f'{M}/written/{wid}'); check(f'{who} written read {exp}', r.status_code == exp, r.status_code)
        r = await c.post(M + '/status', json={'items': [{'kind': 'set', 'id': wid}], 'to': 'live'}); check(f'{who} status {exp}', r.status_code == exp, r.status_code)
    # photo
    from PIL import Image
    buf = io.BytesIO(); Image.new('RGB', (40, 30), 'white').save(buf, 'PNG')
    r = await own.post(f'{M}/written/{wid}/images', files={'file': ('fig.png', buf.getvalue(), 'image/png')}); fid = J(r).get('id'); check('photo upload', r.status_code == 200 and fid, r.text[:200])
    r = await own.put(f'{M}/written/{wid}/questions', json={**mcq(''), 'image': fid, 'options': [{'text': '', 'image': fid}, {'text': 'two', 'image': ''}], 'answer': 'A'}); check('photo-only question with photo option', r.status_code == 200, r.text[:200])
    r = await own.post(f'{M}/written/{wid}/images', files={'file': ('x.txt', b'not an image', 'text/plain')}); check('non-image refused 422', r.status_code == 422, r.status_code)
    import openpyxl
    r = await own.get('/api/studio/imports/template', params={'variant': 'combined'}); wb = openpyxl.load_workbook(io.BytesIO(r.content)); ws = wb.worksheets[0]
    heads = [str(c.value or '').strip().lower() for c in ws[1]]
    vals = {'question_no': '901', 'question_text': 'Excel question?', 'option_a': 'a', 'option_b': 'b', 'option_c': 'c', 'option_d': 'd', 'correct_option': 'B', 'solution_text': 'Because.', 'subject': 'Physics', 'exam': 'JEE Main', 'duration_minutes': '180'}
    ws.append([vals.get(h, 'mcq' if 'type' in h else '') for h in heads]); xbuf = io.BytesIO(); wb.save(xbuf)
    wx, _ = await written(own, mock_t['id'], 'Excel Mock', 0)
    r = await own.post(f'{M}/written/{wx}/excel', files={'file': ('q.xlsx', xbuf.getvalue(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}); check('Excel rows become written questions', r.status_code == 200 and J(r).get('added', 0) >= 1, (r.status_code, r.text[:300], heads))
    r = await rev.post(f'{M}/written/{wx}/excel', files={'file': ('q.xlsx', xbuf.getvalue(), 'application/octet-stream')}); check('reviewer Excel import 403', r.status_code == 403, r.status_code)
    # live / student
    sc, d = await status(own, 'live', [{'kind': 'set', 'id': wid}]); check('complete written mock goes Live', d.get('done') == 1, d)
    ids, sc = await nav(stu, slug, 'mock-tests'); check('hidden exam: student cannot list', sc == 404, (sc, ids))
    await own.patch('/api/admin/catalog/exams/' + slug, json={'shown': True})
    structure._seen['at'] = -1e9
    ids, sc = await nav(stu, slug, 'mock-tests'); check('student sees Live written mock', wid in ids, (sc, ids))
    r = await start(stu, wid); a = J(r); aid = a.get('id'); pq = a.get('questions') or []
    check('student starts written mock; no answers leak', r.status_code == 200 and aid and len(pq) == 7 and all('answer' not in q and 'solution' not in q for q in pq), r.text[:200])
    last = pq[-1] if pq else {}
    check('written question delivers text mode + figure labels', last.get('render_mode') == 'written' and last.get('asset_count') == 2 and last.get('asset_labels') == ['', 'Option A'], {k: last.get(k) for k in ('render_mode', 'asset_count', 'asset_labels')})
    r = await stu.get(f"/api/attempts/{aid}/questions/{last.get('id')}/asset/question/0"); check('student loads question photo', r.status_code == 200 and r.content[:4] == b'\x89PNG', r.status_code)
    v1 = (await SETS.find_one({'id': wid}))['version']
    r = await own.put(f'{M}/written/{wid}/questions', json={**mcq('Edited while live', answer='D'), 'id': q1}); v2 = (await SETS.find_one({'id': wid}))['version']
    old = await H.TDB.tejas_attempts.find_one({'id': aid}, {'version': 1}); check('live edit makes a new version; old attempt keeps its version', r.status_code == 200 and v2 == v1 + 1 and old['version'] == v1, (v1, v2, old))
    sc, d = await status(own, 'off', [{'kind': 'set', 'id': wid}]); ids, _ = await nav(stu, slug, 'mock-tests'); check('Off hides from students', d.get('done') == 1 and wid not in ids, (d, ids))
    r = await stu.get(f'/api/attempts/{aid}'); check('attempt in progress survives Off', r.status_code == 200, r.status_code)
    at = time.time() + 3600
    sc, d = await status(own, 'scheduled', [{'kind': 'set', 'id': wid}], at=at, live_exam=True); check('students already took it: cannot become live exam', d.get('done') == 0, d)
    sc, d = await status(own, 'scheduled', [{'kind': 'set', 'id': wid}], at=at); s = await SETS.find_one({'id': wid}); ids, _ = await nav(stu, slug, 'mock-tests')
    check('Scheduled for practice: hidden until its time, no live-exam flag', d.get('done') == 1 and abs(s['start_at'] - at) < 1 and not s.get('competition') and wid not in ids, (d, s.get('start_at')))
    sc, _ = await status(own, 'scheduled', [{'kind': 'set', 'id': wid}], at=time.time() - 5); check('past schedule time 422', sc == 422, sc)
    sc, d = await status(own, 'live', [{'kind': 'set', 'id': wid}]); ids, _ = await nav(stu, slug, 'mock-tests'); check('Make Live now opens a scheduled mock', d.get('done') == 1 and wid in ids, (d, ids))
    w2, _ = await written(own, mock_t['id'], 'Written Two', 2)
    sc, d = await status(own, 'scheduled', [{'kind': 'set', 'id': w2}], at=at, live_exam=True); s = await SETS.find_one({'id': w2})
    check('Scheduled live exam: 15-minute start window', d.get('done') == 1 and s.get('competition') is True and abs(s['last_start_at'] - (at + 900)) < 1 and s['status'] == 'published', (d, s.get('last_start_at')))
    row = next(x for x in J(await own.get(f"{M}/types/{mock_t['id']}/mocks"))['items'] if x['id'] == w2); check('row shows Scheduled + live exam', row['status'] == 'scheduled' and row['live_exam'], row)
    sc, d = await status(own, 'library', [{'kind': 'set', 'id': wid}, {'kind': 'set', 'id': w2}]); lib = [x['id'] for x in J(await own.get('/api/admin/library'))['items']]
    check('bulk Library; attempt history kept', d.get('done') == 2 and wid in lib and w2 in lib and await H.TDB.tejas_attempts.count_documents({'id': aid}) == 1, d)
    r = await own.post('/api/admin/library/restore', json={'ids': [wid], 'uploads': []}); ids, _ = await nav(stu, slug, 'mock-tests'); check('restore from Library', wid in ids, ids)
    # --- locked verified PYQ
    vp = await mkset('VPYQ', exam='JEE Main', catalog_section_id='jee-main:pyq', test_kind='pyq', pyq_date='2024-01-27', pyq_year=2024, pyq_shift=1)
    for to, kw in (('library', {}), ('scheduled', {'at': at})):
        sc, d = await status(own, to, [{'kind': 'set', 'id': vp}], **kw); check(f'verified PYQ refuses {to}', d.get('done') == 0 and 'locked' in d['skipped'][0]['reason'].lower(), d)
    r = await own.patch('/api/admin/catalog/tests/' + vp, json={'title': 'Renamed'}); check('verified PYQ rename 409', r.status_code == 409, r.status_code)
    sc, d = await status(own, 'off', [{'kind': 'set', 'id': vp}]); sc, d2 = await status(own, 'live', [{'kind': 'set', 'id': vp}]); check('verified PYQ Off then Live', d.get('done') == 1 and d2.get('done') == 1, (d, d2))
    r = await own.post(f"{M}/types/{pyq_t['id']}/written", json={'title': 'NEET 2024'}); check('written PYQ needs a year 422', r.status_code == 422, r.status_code)
    wp, r = await written(own, pyq_t['id'], 'NEET 2024', 2, year=2024); s = await SETS.find_one({'id': wp}); check('written PYQ paper: year stored, not locked', s.get('pyq_year') == 2024 and s.get('master_pyq') and s.get('test_kind') == 'pyq', r.text[:200])
    sc, d = await status(own, 'live', [{'kind': 'set', 'id': wp}]); ids, _ = await nav(stu, slug, 'pyq'); check('written PYQ goes Live for students', d.get('done') == 1 and wp in ids, (d, ids))
    sc, d = await status(own, 'library', [{'kind': 'set', 'id': wp}]); check('own PYQ can move to Library', d.get('done') == 1, d)
    r = await own.post(f"{M}/types/{chap_t['id']}/written", json={'title': 'Kinematics T1'}); check('chapter test needs subject + chapter 422', r.status_code == 422, r.status_code)
    wc, r = await written(own, chap_t['id'], 'Kinematics T1', 2, subject='Physics', chapter='Kinematics'); sc, d = await status(own, 'live', [{'kind': 'set', 'id': wc}])
    r = await stu.get(f'/api/exam-navigation/{slug}/catalogue', params={'section': 'chapter-wise', 'subject': 'Physics'}); check('chapter-wise written test listed under its subject', wc in [x['id'] for x in J(r).get('items', [])], r.text[:200])
    # --- PDF upload: one paper without a mock heading, default time and marks
    b = await upload(own, single_pdf(), 'Single Paper', section_id=mock_t['id']); await complete(own, b['id']); await drain()
    mocks = [m async for m in BM.find({'book_id': b['id']})]
    check('heading-less PDF becomes ONE draft named after the upload', len(mocks) == 1 and mocks[0]['label'] == 'Single Paper', [(m['label'], m['state'], m['issues'][:3]) for m in mocks])
    m0 = mocks[0] if mocks else {}
    check('it is complete with the type default time and marks', m0.get('state') == 'ready' and m0.get('rules', {}).get('minutes') == 180 and len(m0.get('questions', [])) == 3, (m0.get('state'), m0.get('issues'), m0.get('rules')))
    row = next((x for x in J(await own.get(f"{M}/types/{mock_t['id']}/mocks"))['items'] if x['kind'] == 'book_mock'), {}); check('PDF mock listed as Draft', row.get('status') == 'draft' and row.get('to_fix') == 0, row)
    sc, d = await status(own, 'live', [{'kind': 'book_mock', 'id': m0.get('_id', 'x')}]); await drain(); sid = (await BM.find_one({'_id': m0.get('_id')}) or {}).get('set_id')
    ids, _ = await nav(stu, slug, 'mock-tests'); check('PDF mock goes Live for students (answer key only)', d.get('done') == 1 and sid in ids, (d, sid, ids))
    s = await SETS.find_one({'id': sid}) or {}; check('published with key-only solutions and default rules', s.get('rules', {}).get('minutes') == 180 and all(q['solution_kind'] == 'answer_key_only' for q in s.get('questions', [{'solution_kind': ''}])), s.get('rules'))
    b2 = await upload(own, build_pdf([{'n': 1, 'qs': q3('P1'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]}, {'n': 2, 'qs': q3('P2'), 'keys': [(1, 'A'), (2, 'B'), (3, 'C')]}]), 'Two Mocks', section_id=mock_t['id']); await complete(own, b2['id']); await drain()
    two = [m async for m in BM.find({'book_id': b2['id']}).sort('order', 1)]; check('PDF with two printed mocks gives two drafts', [m['label'] for m in two] == ['Mock 1', 'Mock 2'] and all(m['state'] == 'ready' for m in two), [(m['label'], m['state'], m['issues'][:2]) for m in two])
    sc, d = await status(own, 'library', [{'kind': 'book_mock', 'id': two[0]['_id']}]); left = [x['title'] for x in J(await own.get(f"{M}/types/{mock_t['id']}/mocks"))['items'] if x['kind'] == 'book_mock']
    ups = [x for x in J(await own.get('/api/admin/library')).get('uploads', []) if x['kind'] == 'book_mock']; check('draft PDF mock moves to Library and leaves the list', d.get('done') == 1 and left == ['Mock 2'] and len(ups) == 1, (d, left, ups))
    r = await own.post('/api/admin/library/restore', json={'ids': [], 'uploads': [{'kind': 'book_mock', 'id': two[0]['_id']}]}); check('draft PDF mock restores', J(r).get('uploads') == 1, r.text[:200])
    sc, d = await status(own, 'scheduled', [{'kind': 'book_mock', 'id': two[1]['_id']}], at=at, live_exam=True); await drain(); s = await SETS.find_one({'book_import_id': b2['id'], 'mock_number': 2}) or {}
    check('PDF mock scheduled as live exam', d.get('done') == 1 and s.get('competition') is True and abs(s.get('start_at', 0) - at) < 1 and abs(s.get('last_start_at', 0) - at - 900) < 1, (d, s.get('start_at'), s.get('last_start_at')))
    r = await own.post('/api/admin/books', json={'filename': 'p.pdf', 'title': 'P', 'sha256': 'a' * 64, 'size': 10, 'rights_confirmed': True, 'section_id': pyq_t['id']}); check('PYQ PDF upload needs a year 422', r.status_code == 422, r.status_code)
    b3 = await upload(own, single_pdf(2), 'NEET 2023 Paper', section_id=pyq_t['id'], year=2023); await complete(own, b3['id']); await drain()
    m3 = await BM.find_one({'book_id': b3['id']}) or {}; sc, d = await status(own, 'live', [{'kind': 'book_mock', 'id': m3.get('_id', 'x')}]); await drain(); s = await SETS.find_one({'book_import_id': b3['id']}) or {}
    check('PYQ PDF publishes as a PYQ paper with its year', d.get('done') == 1 and s.get('test_kind') == 'pyq' and s.get('pyq_year') == 2023 and s.get('master_pyq'), (d, m3.get('state'), m3.get('issues')))
    blank = fitz.open(); blank.new_page(); braw = blank.tobytes(); blank.close()
    b4 = await upload(own, braw, 'Scanned Paper', section_id=mock_t['id']); await complete(own, b4['id']); await drain()
    ups = [x for x in J(await own.get(f"{M}/types/{mock_t['id']}/mocks")).get('uploads', []) if x['id'] == b4['id']]
    check('unreadable PDF stays visible with a plain reason, not endlessly reading', len(ups) == 1 and ups[0]['state'] == 'failed' and not ups[0]['active'] and 'Write' in ups[0]['message'], ups)
    r = await own.post(f"{M}/uploads/book/{b4['id']}/dismiss"); ups = [x for x in J(await own.get(f"{M}/types/{mock_t['id']}/mocks")).get('uploads', []) if x['id'] == b4['id']]
    check('dismissed upload leaves the list for the Library', r.status_code == 200 and not ups and any(x['id'] == b4['id'] for x in J(await own.get('/api/admin/library')).get('uploads', [])), r.text[:200])
    r = await rev.post(f"{M}/uploads/book/{b4['id']}/dismiss"); check('reviewer dismiss 403', r.status_code == 403, r.status_code)
    summ = J(await own.get(M + '/summary')); check('summary counts and waiting map', isinstance(summ.get('to_fix'), int) and summ.get('ready', 0) >= 1 and isinstance(summ.get('waiting'), dict), summ)
    # --- test series for the new exam
    v = J(await own.get(f'{M}/series/{ser}')); check('series has 5 days from its first date', len(v.get('slots', [])) == 5 and v['slots'][0]['date'] == (today + timedelta(days=3)).isoformat() and not v['shown'], [s['date'] for s in v.get('slots', [])])
    sa, _ = await written(own, aits_t['id'], 'Series A', 3); sb, _ = await written(own, aits_t['id'], 'Series B', 3); sx, _ = await written(own, aits_t['id'], 'Series Short', 2); se, _ = await written(own, aits_t['id'], 'Series Empty', 0)
    s = await SETS.find_one({'id': sa}); check('series paper uses the series time and marks', s['rules']['minutes'] == 180 and s['rules']['correct'] == 4, s['rules'])
    sc, d = await status(own, 'live', [{'kind': 'set', 'id': sa}]); check('series paper cannot be made Live directly', d.get('done') == 0, d)
    d1, d2 = v['slots'][0]['date'], v['slots'][1]['date']
    r = await own.post(f'{M}/series/{ser}/assign', json={'kind': 'written', 'id': sa, 'date': d1}); s = await SETS.find_one({'id': sa})
    check('assign a day: built privately for that day', r.status_code == 200 and s['series_id'] == ser and s['series_date'] == d1 and s['status'] == 'published' and s['series_pattern']['count'] == 3, r.text[:300])
    r = await own.post(f'{M}/series/{ser}/assign', json={'kind': 'written', 'id': sb, 'date': d1}); check('taken day refused 409', r.status_code == 409, r.status_code)
    r = await own.post(f'{M}/series/{ser}/assign', json={'kind': 'written', 'id': sb, 'date': '2031-01-01'}); check('day outside the series 422', r.status_code == 422, r.status_code)
    r = await own.post(f'{M}/series/{ser}/assign', json={'kind': 'written', 'id': sx, 'date': d2}); check('different question count refused 409 (fair rank)', r.status_code == 409, (r.status_code, r.text[:160]))
    r = await start(stu, sa); check('student cannot start before its day', r.status_code in (404, 409), r.status_code)
    r = await anon.get('/api/series'); check('series not public while switched off', all(x['id'] != ser for x in J(r).get('items', [])) and any(x.get('builtin') for x in J(r).get('items', [])), r.text[:200])
    r = await own.put(f'{M}/series/{ser}', json={'shown': True}); r = await anon.get('/api/series'); item = next((x for x in J(r).get('items', []) if x['id'] == ser), None)
    check('Show on Home: series listed for everyone with its exam colour', item and item['exam']['color'] == 'rose' and item['total'] == 5, r.text[:300])
    r = await anon.get(f'/api/series/{ser}/schedule'); sl = J(r).get('slots', [{}]); check('public schedule hides the upcoming paper', r.status_code == 200 and sl[0]['set_id'] is None and sl[0]['ready'] is False and 'Series A' not in r.text, sl[0])
    r = await own.post(f'{M}/series/{ser}/fill'); v = J(await own.get(f'{M}/series/{ser}')); placed = {s['date']: s['paper']['title'] for s in v['slots'] if s['paper']}
    check('Fill days in order places only complete, matching papers', J(r).get('placed') == 1 and placed == {d1: 'Series A', d2: 'Series B'}, (r.text[:200], placed))
    check('unplaced papers show why', {c['title']: bool(c['problem']) for c in v['candidates']} == {'Series Short': True, 'Series Empty': True}, v['candidates'])
    r = await own.post(f'{M}/series/{ser}/unassign', json={'kind': 'set', 'id': sb}); v = J(await own.get(f'{M}/series/{ser}')); check('free a future day; paper returns without a day', r.status_code == 200 and any(c['id'] == sb and c['kind'] == 'set' for c in v['candidates']), v['candidates'])
    r = await own.post(f'{M}/series/{ser}/assign', json={'kind': 'set', 'id': sb, 'date': v['slots'][4]['date']}); check('built paper takes another day', r.status_code == 200, r.text[:200])
    r = await own.put(f'{M}/series/{ser}', json={'days': 3}); s = await SETS.find_one({'id': sb}); check('shorter series: paper on a removed day loses its day', r.status_code == 200 and J(r).get('moved') == 1 and 'series_date' not in s, (r.text[:200], s.get('series_date')))
    r = await own.put(f'{M}/series/{ser}', json={'open_time': '10:00', 'last_start': '12:00'}); s = await SETS.find_one({'id': sa}); check('new times move future days', r.status_code == 200 and datetime.fromtimestamp(s['series_window']['opens_at'], live_series.IST).hour == 10 and s['start_at'] == s['series_window']['opens_at'], r.text[:200])
    r = await own.put(f'{M}/series/{ser}', json={'last_start': '22:30'}); check('last start must leave the full time before midnight 422', r.status_code == 422, r.status_code)
    # day opens: move Series A to today inside an open window (direct DB edit, test only)
    now_ist = datetime.now(live_series.IST); cfg = {'open_time': '00:00', 'last_start': '23:58', 'close_time': '23:59'}; w = live_series.window(today.isoformat(), cfg)
    await H.TDB.tejas_series.update_one({'_id': ser}, {'$set': {'first_date': today.isoformat(), **cfg}})
    await SETS.update_one({'id': sa}, {'$set': {'series_date': today.isoformat(), 'series_window': w, 'start_at': w['opens_at'], 'end_at': w['closes_at']}, '$inc': {'revision': 1}})
    if now_ist.hour == 23 and now_ist.minute >= 55: print('SKIP live-day checks near midnight IST')
    else:
        r = await anon.get(f'/api/series/{ser}/schedule'); t0 = J(r).get('today_slot') or {}; check('on its day the paper is visible and startable', t0.get('set_id') == sa and t0.get('can_start') and t0.get('state') == 'live', t0)
        r = await start(stu, sa); a = J(r); att = await H.TDB.tejas_attempts.find_one({'id': a.get('id')}) or {}
        check('live series attempt: one ranked attempt, sealed until the day closes', r.status_code == 200 and att.get('mode') == 'series_live' and att.get('series_id') == ser and abs(att.get('competition_end', 0) - w['closes_at']) < 1, (r.status_code, r.text[:200]))
        r2 = await start(stu, sa); check('second start returns the same live attempt', J(r2).get('id') == a.get('id'), r2.text[:120])
        r = await own.post(f'{M}/series/{ser}/unassign', json={'kind': 'set', 'id': sa}); check('opened day cannot be freed 409', r.status_code == 409, r.status_code)
        r = await own.put(f'{M}/series/{ser}', json={'first_date': (today + timedelta(days=2)).isoformat(), 'open_time': '00:01', 'last_start': '20:59'}); check('opened day must stay in the series 409', r.status_code == 409, r.status_code)
        r = await own.put(f'{M}/written/{sa}/questions', json=mcq('late edit')); check('opened series paper cannot be edited 409', r.status_code == 409, r.status_code)
        r = await stu.get(f'/api/series/{ser}/history'); check('student series history', r.status_code == 200 and J(r).get('total') == 1, r.text[:200])
    cat = J(await stu.get('/api/catalog/exams/' + slug)); check('student exam page lists types with live mocks, never the series', 'all-india-test-series' not in [s['slug'] for s in cat.get('sections', [])] and 'mock-tests' in [s['slug'] for s in cat.get('sections', [])], [s['slug'] for s in cat.get('sections', [])])
    # --- JEE series unchanged
    r = await anon.get('/api/series/all-india-jee'); check('JEE series public schedule unchanged: 62 days', r.status_code == 200 and J(r).get('total') == 62 and J(r)['slots'][0]['date'] == '2026-12-01', r.status_code)
    v = J(await own.get(f'{M}/series/{live_series.SERIES_ID}')); check('JEE series in Master: 62 days, built in', len(v.get('slots', [])) == 62 and v.get('builtin'), len(v.get('slots', [])))
    r = await own.put(f'{M}/series/{live_series.SERIES_ID}', json={'shown': False}); r2 = await own.put(f'{M}/series/{live_series.SERIES_ID}', json={'days': 10}); check('JEE series dates and banner locked 409', r.status_code == 409 and r2.status_code == 409, (r.status_code, r2.status_code))
    cat = J(await own.get('/api/admin/catalog')); jee = next(e for e in cat['items'] if e['slug'] == 'jee-main'); check('JEE Main has its All India type in Master', any(s['kind'] == 'aits' and s['series_id'] == live_series.SERIES_ID for s in jee['sections']), [s['kind'] for s in jee['sections']])
    check('no AI calls in whole run', H.AI_CALLS == {'ask': 0, 'solve': 0}, H.AI_CALLS)


async def run():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    try: await main()
    except Exception:
        import traceback; traceback.print_exc(); check('suite ran to the end', False, 'exception above')
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
        ok = sum(1 for r in RESULTS if r[1]); print(f'TOTAL {len(RESULTS)} PASS {ok} FAIL {len(RESULTS) - ok}'); print('dropped', H.TEST_DB)

if __name__ == '__main__':
    asyncio.run(run())
