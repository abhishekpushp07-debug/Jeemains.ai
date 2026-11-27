"""TEST-ONLY iteration 258 (pocket C1b edges). First written by the testing agent (iteration 231, stopped at its time limit); put right
by the builder: 3 reads the real answer shapes, 4 sits a real chapter-wise test, 7 counts the record by `resource` and expects only
real changes on it, 8 changes the chapter name the real way (the Draft's printed line, then "Dobara jodo").
The real app in a disposable DB (storage mocked, no AI, no network). Starts where tests/question_names256.py starts.
1  a record on the owner's list gives no name
8  a chapter name with markup in it comes back as the very same letters (the page prints it as text, never as markup)
2  the chapter upload is deleted for good, "Dobara jodo": the paper question keeps the name it had proven
3  the question list and the comparative view say the same chapter as the personal analysis
4  a chapter-wise test (not a series paper) whose questions sit on named records is never changed by the switch
5  only the owner; a wrong body 422; an unknown exam 404
6  another exam's switch does not change the JEE analysis
7  a press that changes nothing is not written; presses at the same moment end whole
9  On for an exam where "Jod banao" was never pressed: nothing breaks, and its analysis gets no mark
10 the report PDF follows the switch (On: the chapter; Off: "no chapter tags" as before)
Run: cd /app/backend && bash /root/p2/solo.sh python -u tests/question_names_edge258.py   (drops only its own disposable database)
"""
import asyncio, sys
from pathlib import Path
import fitz
sys.path.insert(0, str(Path(__file__).resolve().parent))
from question_names256 import (H, BM, DB, J, RESULTS, NAME, M, API, SLUG, check, mkstaff, client, drain, edit, run, setup, analysis, shape,  # noqa: E402
                               frozen, switch, chapter8, run_book, graded, start, structure)
from tejas import question_records as QR  # noqa: E402

MARK = '<script>alert(1)</script>' + NAME
AUDIT = {'action': {'$regex': '^Chapter names in All India analysis'}, 'resource': QR.OP + SLUG}


async def record():
    return await DB.tejas_question_records.find_one({'exam_slug': SLUG, 'mock': 6, 'q': 65}) or {}


async def topic(stu, aid, qid):
    _, an = await analysis(stu, aid)
    return next(q['topic'] for q in an['questions'] if q['id'] == qid), an


async def on_the_list(own, stu, aid, pq, cm, cq):
    await edit(cm, cq, answer=next(x for x in 'ABCD' if x != cq['answer'])); _, st = await run(own)
    rec = await record(); name, _ = await topic(stu, aid, pq['id'])
    check("1 the chapter copy gets another answer: the record is on the owner's list, is not proven, and gives the paper question no name",
          st['counts']['review'] == 1 and rec.get('state') == 'review' and rec.get('chapter_ok') is False and name == '', (st.get('counts'), rec.get('state'), rec.get('chapter_ok'), name))
    await edit(cm, cq, answer=cq['answer']); await run(own)


async def markup(own, stu, aid, pq, cm, cq):
    line = 'CH 08 / ' + NAME
    await edit(cm, cq, text=cq['text'].replace(line, 'CH 08 / ' + MARK, 1)); await run(own)
    rec = await record(); name, an = await topic(stu, aid, pq['id'])
    check('8 the chapter line printed on the Draft carries markup: still joined (the line is not part of the question), and the analysis gives the name back as the very same letters',
          line in cq['text'] and rec.get('state') == 'linked' and (rec.get('chapter') or {}).get('name') == MARK and name == MARK and [w['name'] for w in an['performance']['weak']] == [MARK],
          (rec.get('state'), (rec.get('chapter') or {}).get('name'), name))
    await edit(cm, cq, text=cq['text']); await run(own)
    name, _ = await topic(stu, aid, pq['id'])
    check('8 the line is put back and joined again: the plain name is shown again', name == NAME, name)


async def deleted(own, stu, aid, pq, cm):
    r = await own.post(f"/api/admin/master/uploads/book/{cm['book_id']}/delete", json={'confirm': 'DELETE'})
    for _ in range(120):
        row = await DB.tejas_books.find_one({'_id': cm['book_id']}, {'removed': 1})
        if not row or row.get('removed'):
            break
        await asyncio.sleep(.25)
    await run(own)
    rec = await record(); name, an = await topic(stu, aid, pq['id'])
    check('2 the chapter upload is deleted for good and "Dobara jodo" pressed: the record is paper-only, keeps the chapter it had proven, and the analysis still shows it',
          r.status_code == 200 and rec.get('state') == 'paper' and rec.get('chapter_ok') is True and (rec.get('chapter') or {}).get('name') == NAME and name == NAME
          and [(w['subject'], w['name']) for w in an['performance']['weak']] == [('Chemistry', NAME)], (r.status_code, rec.get('state'), rec.get('chapter_ok'), name))


async def agree(stu, aid, pq):
    r = await stu.get(f'/api/attempts/{aid}/analysis/questions'); items = J(r).get('items') or []
    check('3 the question list (analysis/questions): 75 rows, the joined one says its chapter, no other row has one',
          r.status_code == 200 and len(items) == 75 and [q['id'] for q in items if q.get('topic')] == [pq['id']] and next(q['topic'] for q in items if q['id'] == pq['id']) == NAME,
          (r.status_code, len(items), [q.get('topic') for q in items if q.get('topic')][:3]))
    r = await stu.get(f'/api/attempts/{aid}/analysis', params={'mode': 'comparative', 'compare': 'topper'}); d = J(r)
    check('3 the comparative view says the same chapter, in the questions and in the chapter-wise part', r.status_code == 200 and d.get('view') == 'comparative' and 'compare' in d
          and [q['topic'] for q in d['questions'] if q['id'] == pq['id']] == [NAME] and d['performance']['has_chapters'] is True, (r.status_code, d.get('view'), (d.get('performance') or {}).get('has_chapters')))


async def pdf_words(stu, aid):
    r = await stu.get(f'/api/attempts/{aid}/analysis/report.pdf')
    if r.status_code != 200 or r.content[:5] != b'%PDF-':
        return r.status_code, ''
    doc = fitz.open(stream=r.content, filetype='pdf')
    return 200, ' '.join(' '.join(p.get_text() for p in doc).split())


async def report(own, stu, aid):
    c1, on = await pdf_words(stu, aid)
    await switch(own, False); c2, off = await pdf_words(stu, aid)
    await switch(own, True); c3, again = await pdf_words(stu, aid)
    check('10 the report PDF follows the switch: On it lists the chapter; Off it says, as before, that the paper has no chapter tags; On again it lists the chapter again',
          (c1, c2, c3) == (200, 200, 200) and NAME in on and 'Marks kis chapter se gaye' in on and NAME not in off and 'chapter ka tag nahi hai' in off and NAME in again,
          ((c1, c2, c3), NAME in on, NAME in off, 'chapter ka tag nahi hai' in off, NAME in again))


async def chapter_test(own, stu):
    _, rows, _, _ = await run_book(own, 'jee-main:chapters', chapter8(), 'TEST_CHEM_CH08_AGAIN'); m = rows[0]
    await run(own)
    r = await own.post(M + '/status', json={'items': [{'kind': 'book_mock', 'id': m['_id']}], 'to': 'live'}); await drain(100000)
    mk = await BM.find_one({'_id': m['_id']}) or {}; sid = mk.get('set_id'); rec = await record()
    mine = {q['id'] for q in m['questions']} & set(rec.get('qids', []))
    check('4 the chapter book is uploaded again and joined again; its chapter 8 goes Live as a chapter-wise test; one of its questions sits on the named record',
          r.status_code == 200 and bool(sid) and mk.get('state') == 'published' and rec.get('state') == 'linked' and len(mine) == 1, (r.status_code, r.text[:200], mk.get('state'), (mk.get('issues') or [])[:2], rec.get('state')))
    if not sid:
        return
    await asyncio.sleep(2); await structure.visibility(force=True)
    r = await start(stu, sid); aid = J(r).get('id')
    row = await DB.tejas_attempts.find_one({'id': aid}, {'_id': 0, 'mode': 1, 'series_id': 1}) or {}
    check('4 the student starts it: an ordinary practice attempt, not a series one', r.status_code == 200 and row.get('mode') == 'practice' and 'series_id' not in row, (r.status_code, r.text[:200], row))
    if not aid:
        return
    await stu.post(f'/api/attempts/{aid}/begin'); await asyncio.sleep(.2); await stu.post(f'/api/attempts/{aid}/submit'); await graded(stu, aid)
    await switch(own, False); _, off = await analysis(stu, aid)
    await switch(own, True); _, on = await analysis(stu, aid)
    check('4 its analysis is the very same with the switch Off and On: the switch adds no chapter to it', bool(off and on) and mine <= {q['id'] for q in on['questions']} and shape(on) == shape(off),
          (bool(off), bool(on), [v for v in shape(on)['topics'].values() if v][:2] if on else None))


async def doors(own, stu):
    anon = client(); rev, _ = await mkstaff('reviewer', 'c258r')
    codes = [(await switch(c, False))[0].status_code for c in (anon, rev, stu)]
    check('5 only the owner can switch: no login 401; a reviewer and a student 403', codes == [401, 403, 403], codes)
    bad = [(await own.put(API + SLUG + '/analysis', json=b)).status_code for b in ({}, {'on': 'yes'}, {'on': 1}, {'on': True, 'extra': 'x'}, {'on': None}, {'ON': True})]
    r, _ = await switch(own, True, 'no-such-exam')
    check('5 a body that is not exactly on: true/false: 422; an unknown exam: 404; the switch stays On', bad == [422] * 6 and r.status_code == 404
          and J(await own.get(API + SLUG)).get('show_chapters') is True, (bad, r.status_code))


async def another_exam(own, stu, aid):
    slug = J(await own.post('/api/admin/catalog/exams', json={'name': 'EDGEX', 'short': 'EX', 'subjects': ['Chemistry'], 'color': 'violet'})).get('slug')
    _, an = await analysis(stu, aid); was = shape(an); seen = []
    for on in (True, False, True):
        r, st = await switch(own, on, slug); seen.append((r.status_code, st.get('show_chapters')))
    _, an = await analysis(stu, aid)
    check("6 another exam's switch goes On, Off, On: the JEE switch stays On and the JEE analysis is not changed", bool(slug) and slug != SLUG and seen == [(200, True), (200, False), (200, True)]
          and J(await own.get(API + SLUG)).get('show_chapters') is True and was['has'] is True and shape(an) == was, (slug, seen, was['has']))


async def presses(own):
    await switch(own, True); n0 = await DB.tejas_audits.count_documents(AUDIT)
    codes = [(await switch(own, v))[0].status_code for v in (True, False, False, True, True, False)]
    n1 = await DB.tejas_audits.count_documents(AUDIT); state = J(await own.get(API + SLUG)).get('show_chapters')
    check('7 six presses one after another, three of them changing nothing: all answer 200, it ends Off, and only the three real changes are on the record',
          codes == [200] * 6 and state is False and n1 - n0 == 3, (codes, state, n1 - n0))
    rs = await asyncio.gather(*(own.put(API + SLUG + '/analysis', json={'on': v}) for v in (True, False) * 4))
    k = await DB.tejas_audits.count_documents(AUDIT) - n1; state = J(await own.get(API + SLUG)).get('show_chapters')
    check('7 eight presses at the same moment: all answer 200; it ends plainly On or Off, and the record has exactly the changes that happened (an odd number if it ended On, even if Off)',
          all(r.status_code == 200 for r in rs) and isinstance(state, bool) and 1 <= k <= 8 and k % 2 == int(state), ([r.status_code for r in rs], state, k))
    await switch(own, True)


async def never_made(own):
    slug = J(await own.post('/api/admin/catalog/exams', json={'name': 'NOCHAIN', 'short': 'NC', 'subjects': ['Chemistry'], 'color': 'amber'})).get('slug')
    r, st = await switch(own, True, slug)
    await DB.tejas_series.insert_one({'_id': 'test-nochain', 'id': 'test-nochain', 'exam_slug': slug})   # TEST: a series of that exam, only to ask for its mark
    mark = await QR.names_mark('test-nochain')
    check('9 On for an exam where "Jod banao" was never pressed: 200, shown On, nothing counted, and a series of that exam gets no mark (its analysis is built exactly as with Off)',
          r.status_code == 200 and st.get('show_chapters') is True and st.get('named') == 0 and st.get('ran_at') is None and not any(st['counts'].values()) and mark == '', (r.status_code, st.get('named'), st.get('ran_at'), mark))


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    try:
        own, _ = await mkstaff('owner', 'c258')
        got = await setup(own)
        if got and all(ok for _, ok in RESULTS):
            sid, stu, aid, _pm, pq, cm, cq, _res = got
            before = await frozen(sid, aid)
            await switch(own, True)
            await on_the_list(own, stu, aid, pq, cm, cq)
            await markup(own, stu, aid, pq, cm, cq)
            await deleted(own, stu, aid, pq, cm)
            await agree(stu, aid, pq)
            await report(own, stu, aid)
            await chapter_test(own, stu)
            await doors(own, stu)
            await another_exam(own, stu, aid)
            await presses(own)
            await never_made(own)
            check('nothing was written into the series test, the paper frozen for the student, the answers or the marks by any of this', await frozen(sid, aid) == before, '')
    finally:
        # Only the disposable database this run created; never the app's own.
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB, H.TEST_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB, flush=True)
        bad = [n for n, ok in RESULTS if not ok]
        print(f'TOTAL {len(RESULTS)} PASS {len(RESULTS) - len(bad)} FAIL {len(bad)}', flush=True)


if __name__ == '__main__':
    asyncio.run(main())
