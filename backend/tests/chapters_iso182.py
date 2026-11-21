"""TEST-ONLY iteration 182: chapter-wise PDF reader (headings, bookmarks, owner-marked starts, subjects) and Draft preview.
Run: cd /app/backend && python tests/chapters_iso182.py   (isolated DB, storage + AI mocked; prints PASS/FAIL; drops its DB at end)
"""
import asyncio, re, sys, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import book_publishing_iso170 as T  # noqa: E402  (rebinds DB + mocks storage/AI first)
from book_publishing_iso170 import H, check, mkstaff, upload, complete, drain, RESULTS  # noqa: E402
import fitz  # noqa: E402
from tejas import structure  # noqa: E402
from tejas.chapter_reader import heading, syllabus_subject, bookmark_plan  # noqa: E402

DB = H.TDB
SRC = '/app/data/chapter50/physics.pdf'


def unit_checks():
    cases = {'CHAPTER 03 \u2014 KINEMATICS': (3, 'Kinematics', None), 'Ch-2: Gravitation': (2, 'Gravitation', None), 'Unit 4 Thermodynamics': (4, 'Thermodynamics', None),
             'Answer Key \u2013 Chapter 3': (3, '', 'key'), 'Chapter 7 \u2014 Solutions': (7, 'Solutions', 'solution'), 'Chapter 12: Liquid Solutions': (12, 'Liquid Solutions', None),
             'Chapter 5 Laws of Motion': (5, 'Laws of Motion', None)}
    for text, (n, title, role) in cases.items():
        h = heading(text)
        check(f'unit heading {text!r}', h and h['number'] == n and h['title'] == title and h['role'] == role, h)
    for text in ['Q1. A ball is dropped from 20 m. Find the time.', 'the chapter 3 results show that', '12. A block of mass 2 kg', 'Chapter-wise practice / Questions and answer keys']:
        check(f'unit not a heading {text[:30]!r}', heading(text) is None, heading(text))
    check('unit subject from chapter name', syllabus_subject('Kinematics') == 'Physics' and syllabus_subject('Mole Concept') == 'Chemistry' and syllabus_subject('Thermodynamics') == '')
    plan = bookmark_plan([[1, 'Physics', 1], [2, 'Units & Measurements', 3], [2, 'Kinematics', 9]], 16)
    check('unit bookmarks become chapter starts', [(e['page'], e['title']) for e in plan if e['role'] == 'question'] == [(3, 'Units & Measurements'), (9, 'Kinematics')], plan)


def headless(pages, toc=None):
    """Physics pages with every printed chapter heading and chapter name removed: the reader must not guess."""
    src = fitz.open(SRC); names = {t for _, t, _ in src.get_toc()}
    doc = fitz.open(); doc.insert_pdf(src, from_page=pages[0] - 1, to_page=pages[1] - 1)
    for p in doc:
        for b in p.get_text('dict')['blocks']:
            for line in b.get('lines', []):
                text = ''.join(s['text'] for s in line['spans']).strip()
                if re.fullmatch(r'Chapter \d+', text) or text in names:
                    p.add_redact_annot(fitz.Rect(line['bbox']))
        p.apply_redactions()
    doc.set_toc(toc or [])
    raw = doc.tobytes(); doc.close()
    return raw


def layout_b():
    """A different layout: CAPS headings with the name on the same line, plain '1.' numbering, all keys at the back."""
    doc = fitz.open()
    chapters = [('KINEMATICS', ['A car moves 10 m in 2 s. Its speed is', 'Unit of acceleration is', 'Slope of v-t graph gives']),
                ('MOLE CONCEPT', ['Moles in 18 g of water are', 'Avogadro number order is', 'Molar mass of CO2 is'])]
    for n, (name, qs) in enumerate(chapters, 1):
        p = doc.new_page(); p.insert_text((40, 60), f'CHAPTER {n} \u2014 {name}', fontsize=15); y = 100
        for i, q in enumerate(qs, 1):
            p.insert_text((40, y), f'{i}. {q}', fontsize=11); y += 20
            for lab, o in zip('ABCD', ['1', '2', '5', '10']):
                p.insert_text((60, y), f'({lab}) {o}', fontsize=11); y += 18
            y += 22
    for n in (1, 2):
        p = doc.new_page(); p.insert_text((40, 60), f'Answer Key \u2013 Chapter {n}', fontsize=13); y = 100
        for i, a in enumerate('BCA', 1):
            p.insert_text((40, y), f'Q{i}. ({a})', fontsize=11); y += 20
    raw = doc.tobytes(); doc.close()
    return raw


async def book_of(bid):
    return await DB.tejas_books.find_one({'_id': bid})


async def mocks(bid):
    return await DB.tejas_book_mocks.find({'book_id': bid}).sort('order', 1).to_list(500)


async def send(c, raw, title, **extra):
    b = await upload(c, raw, title, section_id='bitsat:chapters', **extra)
    await complete(c, b['id']); await drain(3000)
    return b['id']


async def main():
    unit_checks()
    await H.tdbmod.indexes(); await structure.seed()
    own, _ = await mkstaff('owner', 'own'); rev, _ = await mkstaff('reviewer', 'rev')
    stu = T.client(); await stu.post('/api/auth/phone/signup', json={'phone': '93' + str(uuid.uuid4().int)[:8], 'pin': '8261', 'confirm_pin': '8261'})
    try:
        # 1. A real 257-page chapter-wise PDF splits into one test per chapter by itself.
        pid = await send(own, Path(SRC).read_bytes(), 'Physics chapters')
        ms = await mocks(pid)
        check('real PDF: 30 chapter tests', len(ms) == 30, len(ms))
        # PDF Engine 2.0 holds a question whose options touch (no blank line between A and C) instead of guessing: physics ch15 Q33 and ch21 Q38.
        waits = {m['label']: m['issues'] for m in ms if m['state'] != 'ready'}
        check('real PDF: every chapter has 50 questions; only the two questions whose options touch are held', all(len(m['questions']) == 50 for m in ms) and set(waits) == {'Chapter 15', 'Chapter 21'}
              and all(len(v) == 1 and 'khaali jagah nahi' in v[0] for v in waits.values()) and 'Q33' in waits['Chapter 15'][0] and 'Q38' in waits['Chapter 21'][0],
              [(m['label'], m['state'], len(m['questions']), m['issues'][:2]) for m in ms if m['state'] != 'ready' or len(m['questions']) != 50][:4])
        check('real PDF: chapter names read', [m['chapter']['title'] for m in ms[:3]] == ['Units & Measurements', 'Kinematics', 'Laws of Motion'], [m.get('chapter') for m in ms[:3]])
        check('real PDF: subject read from the PDF', all(m['chapter']['subject'] == 'Physics' for m in ms), {m['chapter'].get('subject_from') for m in ms})
        r = await own.get(f'/api/admin/master/chapters/{pid}')
        d = r.json()
        check('chapters view lists 30 with pages', r.status_code == 200 and len(d['chapters']) == 30 and d['chapters'][0]['question_page'] == 5 and d['chapters'][0]['key_page'] == 12 and d['plan_source'] == 'headings', r.text[:300])
        r = await own.get('/api/admin/master/types/bitsat:chapters/mocks')
        up = [u for u in r.json()['uploads'] if u['id'] == pid]
        check('type page keeps the chapter upload listed with chapters link data', up and up[0]['chapters'] and up[0]['state'] == 'done', up)
        items = [i for i in r.json()['items'] if i.get('book_id') == pid]
        check('type page shows chapter names and subject', len(items) == 30 and items[0]['title'] == 'Units & Measurements' and items[0]['subject'] == 'Physics', items[:1])
        rr = await rev.get(f'/api/admin/master/chapters/{pid}'); rs = await stu.get(f'/api/admin/master/chapters/{pid}')
        check('chapters view is owner-only', rr.status_code == 403 and rs.status_code == 403, (rr.status_code, rs.status_code))
        img = await own.get(f'/api/admin/master/chapters/{pid}/asset/page/5')
        check('page picture for marking', img.status_code == 200 and img.headers['content-type'] == 'image/png' and img.content[:4] == b'\x89PNG', img.status_code)
        bad = await own.get(f'/api/admin/master/chapters/{pid}/asset/page/999')
        check('page picture out of range 404', bad.status_code == 404, bad.status_code)

        # 2. Rename + subject change; invalid subject refused.
        first = d['chapters'][0]
        r = await own.put(f'/api/admin/master/chapters/{pid}/details', json={'items': [{'label': first['label'], 'title': 'Units and Dimensions', 'subject': 'Physics'}]})
        await drain(500)
        m0 = (await mocks(pid))[0]
        check('rename chapter saved; unchanged subject keeps its source', r.status_code == 200 and m0['chapter']['title'] == 'Units and Dimensions' and m0['chapter']['subject_from'] == 'book', (r.text[:200], m0.get('chapter')))
        r = await own.put(f'/api/admin/master/chapters/{pid}/details', json={'items': [{'label': first['label'], 'title': 'Units and Dimensions', 'subject': 'Mathematics'}]})
        await drain(500)
        m0 = (await mocks(pid))[0]
        check('changed subject is chosen by you', r.status_code == 200 and m0['chapter']['subject'] == 'Mathematics' and m0['chapter']['subject_from'] == 'you', m0.get('chapter'))
        r = await own.put(f'/api/admin/master/chapters/{pid}/details', json={'items': [{'label': first['label'], 'title': 'X chapter', 'subject': 'Biology'}]})
        check('subject outside the exam refused', r.status_code == 422, r.status_code)
        r = await rev.put(f'/api/admin/master/chapters/{pid}/details', json={'items': [{'label': first['label'], 'title': 'Hack', 'subject': ''}]})
        check('reviewer cannot rename chapters', r.status_code == 403, r.status_code)

        # 3. Subject picked at upload wins over the PDF; unknown subject or non-chapter type refused.
        raw_b = layout_b()
        r = await own.post('/api/admin/books', json={'filename': 'b.pdf', 'title': 'b', 'sha256': T.h(raw_b), 'size': len(raw_b), 'rights_confirmed': True, 'section_id': 'bitsat:chapters', 'subject': 'Biology'})
        check('upload with a subject the exam lacks refused', r.status_code == 422, r.status_code)
        r = await own.post('/api/admin/books', json={'filename': 'b.pdf', 'title': 'b', 'sha256': T.h(raw_b), 'size': len(raw_b), 'rights_confirmed': True, 'section_id': 'bitsat:mocks', 'subject': 'Physics'})
        check('subject at upload only for chapter-wise types', r.status_code == 422, r.status_code)

        # 4. A different layout: caps headings, keys at the back, subjects from chapter names.
        bid = await send(own, raw_b, 'Mixed layout')
        ms = await mocks(bid)
        check('layout B: 2 chapter tests with 3 questions', len(ms) == 2 and all(len(m['questions']) == 3 for m in ms), [(m['label'], len(m['questions']), m['issues'][:2]) for m in ms])
        check('layout B: names and subjects by chapter name', [(m['chapter']['title'], m['chapter']['subject']) for m in ms] == [('Kinematics', 'Physics'), ('Mole Concept', 'Chemistry')], [m.get('chapter') for m in ms])
        check('layout B: keys at the back joined to their chapter', all(m['pages'].get('key') for m in ms) and all(q['answer'] for m in ms for q in m['questions']), [m['pages'] for m in ms])

        # 5. No headings and no bookmarks: the owner marks the pages.
        raw_h = headless((5, 20))
        hid = await send(own, raw_h, 'No headings')
        b = await book_of(hid)
        check('no headings: asks to mark chapter starts', b['state'] == 'chapters_needed' and not await mocks(hid), (b['state'], b['payload'].get('message')))
        d = (await own.get(f'/api/admin/master/chapters/{hid}')).json()
        check('no headings: pages where Q1 is printed are suggested', {1, 9} <= set(d['restarts']), d['restarts'])
        up = [u for u in (await own.get('/api/admin/master/types/bitsat:chapters/mocks')).json()['uploads'] if u['id'] == hid]
        check('no headings: type page shows Mark chapter starts', up and up[0]['state'] == 'chapters_needed', up)
        bad = await own.put(f'/api/admin/master/chapters/{hid}/starts', json={'chapters': [{'title': 'A', 'subject': ''}, {'title': 'Bee', 'subject': ''}], 'starts': [{'page': 1, 'chapter': 0, 'role': 'question'}]})
        check('every chapter needs its question start', bad.status_code == 422, bad.status_code)
        bad = await own.put(f'/api/admin/master/chapters/{hid}/starts', json={'chapters': [{'title': 'Alpha', 'subject': ''}], 'starts': [{'page': 99, 'chapter': 0, 'role': 'question'}]})
        check('start beyond the last page refused', bad.status_code == 422, bad.status_code)
        r = await own.put(f'/api/admin/master/chapters/{hid}/starts', json={'chapters': [{'title': 'Units', 'subject': 'Physics'}, {'title': 'Motion in a line', 'subject': ''}],
                                                                            'starts': [{'page': 1, 'chapter': 0, 'role': 'question'}, {'page': 9, 'chapter': 1, 'role': 'question'}]})
        await drain(3000)
        ms = await mocks(hid)
        check('marked starts: 2 chapters read', r.status_code == 200 and len(ms) == 2 and [len(m['questions']) for m in ms] == [50, 50], (r.text[:200], [(m['label'], len(m['questions']), m['issues'][:2]) for m in ms]))
        check('marked starts: names kept and subject asked when unclear', [m['chapter']['title'] for m in ms] == ['Units', 'Motion in a line'] and ms[0]['chapter']['subject'] == 'Physics' and ms[0]['chapter']['subject_from'] == 'you', [m.get('chapter') for m in ms])
        d = (await own.get(f'/api/admin/master/chapters/{hid}')).json()
        check('marked starts: plan shown back to the owner', d['plan_source'] == 'owner' and len(d['draft']['starts']) == 2, d['draft'])

        # 6. No headings but PDF bookmarks: split by the bookmarks by itself.
        kid = await send(own, headless((5, 20), [[1, 'Physics', 1], [2, 'Units & Measurements', 1], [2, 'Kinematics', 9]]), 'Bookmarks only')
        ms = await mocks(kid)
        check('bookmarks: 2 chapters by themselves', len(ms) == 2 and [m['chapter']['title'] for m in ms] == ['Units & Measurements', 'Kinematics'] and all(len(m['questions']) == 50 for m in ms), [(m['label'], m.get('chapter'), len(m['questions'])) for m in ms])
        check('bookmarks: subject from the bookmark outline', all(m['chapter']['subject'] == 'Physics' for m in ms), [m.get('chapter') for m in ms])

        # 7. Draft preview: private copy, full student flow for owner and reviewers only.
        target = (await mocks(pid))[1]
        r = await stu.post(f"/api/admin/master/preview/{target['_id']}")
        check('student cannot open a Draft preview', r.status_code == 403, r.status_code)
        r = await own.post(f"/api/admin/master/preview/{target['_id']}")
        check('owner opens preview', r.status_code == 200 and r.json()['state'] in ('building', 'ready'), r.text[:200])
        for _ in range(60):
            s = (await own.get(f"/api/admin/master/preview/{target['_id']}")).json()
            if s['state'] != 'building': break
            await asyncio.sleep(0.5)
        check('preview ready', s['state'] == 'ready' and s['set_id'], s)
        sid = s['set_id']; ps = await DB.tejas_sets.find_one({'id': sid}) if 'tejas_sets' in await DB.list_collection_names() else None
        from tejas.db import sets as SETS
        ps = await SETS.find_one({'id': sid})
        check('preview set is private and never Live', ps and ps['status'] == 'draft' and ps['qa_only'] and ps['audience'] == 'restricted' and len(ps['questions']) == 50 and ps['test_kind'] == 'chapter' and ps['title'] == 'Kinematics', {k: ps.get(k) for k in ('status', 'qa_only', 'audience', 'test_kind', 'title')} if ps else None)
        r = await own.post(f"/api/admin/master/preview/{target['_id']}")
        check('same Draft reuses its preview', r.json().get('set_id') == sid, r.text[:200])
        r = await stu.get(f'/api/my/sets/{sid}')
        check('student cannot see the preview set', r.status_code == 404, r.status_code)
        r = await stu.post(f'/api/sets/{sid}/preflight', json={'preview': True, 'test_response': 'ok'})
        check('student cannot start the preview set', r.status_code == 404, r.status_code)
        for who, c in (('owner', own), ('reviewer', rev)):
            g = await c.get(f'/api/studio/sets/{sid}')
            pf = await c.post(f'/api/sets/{sid}/preflight', json={'preview': True, 'test_response': 'ok'})
            st = await c.post(f'/api/sets/{sid}/start', json={'preview': True, 'device_checked': True, 'start_key': 'k-' + uuid.uuid4().hex})
            a = st.json() if st.status_code == 200 else {}
            check(f'{who} takes the Draft like a student', g.status_code == 200 and pf.status_code == 200 and st.status_code == 200 and a.get('mode') == 'preview', (g.status_code, pf.text[:150], st.text[:200]))
            if a.get('id'):
                at = await c.get(f"/api/attempts/{a['id']}")
                check(f'{who} preview attempt serves 50 questions', at.status_code == 200 and len(at.json().get('questions', [])) == 50, at.text[:150])
                sub = await c.post(f"/api/attempts/{a['id']}/submit", json={'submit_key': 'sk-' + uuid.uuid4().hex})
                check(f'{who} preview attempt can be submitted', sub.status_code in (200, 422), sub.text[:200])
        r = await rev.post(f"/api/admin/master/preview/{ms[0]['_id']}")
        check('reviewer can open any Draft', r.status_code == 200, r.text[:200])
        cat = await stu.get('/api/my/sets?exam=bitsat')
        check('preview never listed to students', sid not in cat.text, cat.status_code)
        none = (await mocks(hid))[0]
        await DB.tejas_book_mocks.update_one({'_id': none['_id']}, {'$set': {'set_id': 'x', 'published_generation': 1}})
        r = await own.post(f"/api/admin/master/preview/{none['_id']}")
        check('a Live mock has no Draft preview', r.status_code == 404, r.status_code)
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
    failed = [r for r in RESULTS if not r[1]]
    print(f'\n{len(RESULTS) - len(failed)}/{len(RESULTS)} passed')
    sys.exit(1 if failed else 0)

if __name__ == '__main__':
    asyncio.run(main())
