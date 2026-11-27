"""TEST-ONLY iteration 256 (pocket C1b): chapter names in the analysis of an All India paper, taken from the join, behind the owner's switch.
The real app in a disposable DB (storage mocked, no AI, no network). Mock 06 of the owner's AITS book is given a day and built; chapter 8
of the owner's chemistry book is a Draft in Chapter-wise; "Jod banao" joins Mock 06 / Q65. A student sits the paper (Q65 answered wrong).
A  the switch is Off as it starts: the analysis has no chapter anywhere, as today.
B  On: the joined question carries its chapter; the chapter-wise table and the weak chapter appear; the score, the result, the test and
   the frozen paper are not changed.
C  Off again: the analysis is what it was.
D  the join breaks (the chapter copy gets another answer, "Dobara jodo"): the name is no longer shown; put right: it is shown again.
E  only the owner can switch; an unknown exam 404; a wrong body 422.
F  the paper's Draft gets new question ids (a corrected version): an attempt on the older paper still shows the chapter.
Run: cd /app/backend && python -u tests/question_names256.py   (drops only its own disposable database)
"""
import asyncio, hashlib, json, sys, time, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from question_records_iso254 import H, BM, DB, J, RESULTS, check, mkstaff, client, upload, drain, aits_slice, drafts, edit, run, API, SLUG  # noqa: E402
from book_speed211 import chapter8, run_book  # noqa: E402
from source_hidden248 import student, graded  # noqa: E402
from structure_iso173 import start  # noqa: E402
from tejas import structure, series_admin  # noqa: E402

SERIES, M = 'all-india-jee-2026-27', '/api/admin/master'
NAME = 'Redox Reactions'


async def analysis(c, aid):
    r, d = None, None
    for _ in range(40):
        r = await c.get(f'/api/attempts/{aid}/analysis'); d = J(r) if r.status_code == 200 else None
        if d and d['class']['state'] != 'preparing':
            break
        await asyncio.sleep(.5)
    return r, d


def shape(an):
    """What must and must not change with the switch."""
    return {'topics': {q['id']: q['topic'] for q in an['questions']}, 'has': an['performance']['has_chapters'],
            'chapters': {g['name']: [(c['name'], c['count']) for c in g['chapters']] for g in an['performance']['subjects']},
            'weak': [(w['subject'], w['name'], w['wrong'], w['lost']) for w in an['performance']['weak']],
            'score': an['overview']['score'], 'outcomes': {q['id']: (q['outcome'], q['marks']) for q in an['questions']}}


async def frozen(sid, aid):
    """A fingerprint of the test, the paper frozen for the student, and the student's answers and marks."""
    a = await DB.tejas_attempts.find_one({'id': aid}, {'_id': 0, 'answers': 1, 'summary': 1, 'pack_id': 1, 'questions': 1, 'status': 1, 'version': 1})
    rows = [await DB.tejas_sets.find_one({'id': sid}, {'_id': 0, 'questions': 1, 'rules': 1, 'status': 1, 'title': 1, 'series_date': 1, 'series_window': 1}), await DB.tejas_packs.find_one({'id': a.get('pack_id')}) or await DB.tejas_packs.find_one({'_id': a.get('pack_id')}), a,
            await DB.tejas_ledgers.find_one({'id': aid})]
    return hashlib.sha256(json.dumps(rows, sort_keys=True, default=str).encode()).hexdigest()


async def switch(c, on, slug=SLUG):
    r = await c.put(API + slug + '/analysis', json={'on': on})
    return r, J(r)


async def setup(own):
    b = await upload(own, aits_slice(), 'TEST_AITS_06_07', section_id='jee-main:aits')
    await own.post(f"/api/admin/books/{b['id']}/complete"); await drain(100000)
    papers = await BM.find({'book_id': b['id']}).sort('order', 1).to_list(10)
    check("setup: Mock 06 and 07 of the owner's AITS book arrive as two ready Drafts of 75 questions", [(m['label'], m['state'], len(m['questions'])) for m in papers] == [('Mock 6', 'ready', 75), ('Mock 7', 'ready', 75)],
          [(m['label'], m['state'], len(m['questions']), m['issues'][:2]) for m in papers])
    if not papers:
        return None
    mock = papers[0]
    chem, _, _, _ = await run_book(own, 'jee-main:chapters', chapter8(), 'TEST_CHEM_CH08')
    cfg = await DB.tejas_series.find_one({'_id': SERIES})
    day = next(d for d in series_admin.dates(cfg) if series_admin.window(d, cfg)['opens_at'] > time.time() + 3600)
    r = await own.post(f'{M}/series/{SERIES}/assign', json={'kind': 'book_mock', 'id': mock['_id'], 'date': day}); await drain(100000)
    mk = await BM.find_one({'_id': mock['_id']}); sid = mk.get('set_id')
    check('setup: the paper is given a day and built for it', r.status_code == 200 and bool(sid), (r.status_code, r.text[:300], mk['state'], mk['issues'][:3]))
    if not sid:
        return None
    # TEST: the paper keeps its series day; only its window is opened now for an hour (the app itself opens a paper only on its day).
    t = time.time(); w = {'opens_at': t - 3600, 'last_start_at': t + 3600, 'closes_at': t + 7200, 'archive_at': t + 10800}
    await DB.tejas_sets.update_one({'id': sid}, {'$set': {'series_window': w, 'start_at': w['opens_at'], 'end_at': w['closes_at']}, '$inc': {'revision': 1}})
    P, C = await drafts(b['id']), await drafts(chem)
    r, st = await run(own)
    both = set(P) & set(C)
    check('setup: "Jod banao": Mock 06 / Q65 is joined to chapter 8; the screen says how many AITS questions got a chapter name; the switch is Off',
          r.status_code == 200 and (6, 65) in both and st['counts']['linked'] == len(both) == st.get('named') and st.get('show_chapters') is False, (r.status_code, st.get('counts'), st.get('named'), st.get('show_chapters')))
    await asyncio.sleep(2); await structure.visibility(force=True)
    stu = await student()
    r = await start(stu, sid); a = J(r); aid = a.get('id')
    check('setup: a student starts the paper on its day', r.status_code == 200 and len(a.get('questions', [])) == 75 and a.get('mode') == 'series_live', (r.status_code, r.text[:300]))
    if not aid:
        return None
    (pm, pq), (cm, cq) = P[(6, 65)], C[(6, 65)]
    await stu.post(f'/api/attempts/{aid}/begin'); await asyncio.sleep(.2)
    sq = next(q for q in (await DB.tejas_sets.find_one({'id': sid}))['questions'] if q['id'] == pq['id'])   # as the built paper holds it
    wrong = next(x for x in sq['options'] if x != sq['answer'])
    r1 = await stu.put(f"/api/attempts/{aid}/answers/{pq['id']}", json={'value': wrong, 'marked': False, 'revision': 1, 'request_id': str(uuid.uuid4())})
    r2 = await stu.post(f'/api/attempts/{aid}/submit')
    r, res = await graded(stu, aid)
    check('setup: the student answers Mock 06 / Q65 wrong and nothing else, submits, and the result arrives: -1', r1.status_code == 200 and r2.status_code in (200, 202) and r.status_code == 200
          and (res.get('summary') or {}).get('score') == -1, (r1.status_code, r1.text[:200], r2.status_code, r.status_code, res.get('summary')))
    return sid, stu, aid, pm, pq, cm, cq, res


async def names(own, sid, stu, aid, pm, pq, cm, cq, res):
    r, an = await analysis(stu, aid)
    if not an:
        check('A the analysis opens', False, (r.status_code, r.text[:300]))
        return
    a0 = shape(an)
    check('A the switch is Off as it starts: no question carries a chapter, there is no chapter-wise table and no weak chapter, as today',
          len(a0['topics']) == 75 and not any(a0['topics'].values()) and a0['has'] is False and not any(a0['chapters'].values()) and a0['weak'] == [] and a0['score'] == -1, {k: a0[k] for k in ('has', 'chapters', 'weak', 'score')})
    before = await frozen(sid, aid)
    r, st = await switch(own, True)
    check('B the owner switches it On: the screen shows On', r.status_code == 200 and st.get('show_chapters') is True and st.get('named', 0) >= 1, (r.status_code, r.text[:200]))
    r, an = await analysis(stu, aid); b = shape(an)
    rest = {k: v for k, v in b['topics'].items() if k != pq['id']}
    check('B the joined question now carries its chapter; the other 74 carry none', b['topics'][pq['id']] == NAME and not any(rest.values()) and len(rest) == 74, (b['topics'][pq['id']], [v for v in rest.values() if v][:3]))
    check('B the chapter-wise table and the weak chapter appear for it: Chemistry › Redox Reactions, 1 question, 1 wrong, 5 marks lost',
          b['has'] is True and b['chapters'].get('Chemistry') == [(NAME, 1)] and b['weak'] == [('Chemistry', NAME, 1, 5)] and not any(v for k, v in b['chapters'].items() if k != 'Chemistry'), (b['has'], b['chapters'], b['weak']))
    after = J(await stu.get(f'/api/attempts/{aid}/results'))
    check('B the score and every right / wrong / marks are as they were; the result page is the same', b['score'] == a0['score'] and b['outcomes'] == a0['outcomes'] and after.get('summary') == res.get('summary')
          and [(q['id'], q.get('topic') or '') for q in after['questions']] == [(q['id'], q.get('topic') or '') for q in res['questions']], (b['score'], after.get('summary')))
    check('B nothing is written into the test, the paper frozen for the student, the answers or the marks', await frozen(sid, aid) == before, '')
    r, st = await switch(own, False)
    r2, an = await analysis(stu, aid)
    check('C switched Off again: the analysis is what it was', r.status_code == 200 and st.get('show_chapters') is False and shape(an) == a0, (r.status_code, shape(an)['topics'].get(pq['id'])))
    await switch(own, True)
    other = next(x for x in 'ABCD' if x != cq['answer'])
    await edit(cm, cq, answer=other); r, st = await run(own)
    r2, an = await analysis(stu, aid)
    check('D On, and the join breaks (the chapter copy gets another answer, "Dobara jodo"): the question is on the owner\'s list and its chapter name is no longer shown',
          st['counts']['review'] == 1 and st.get('named') == st['counts']['linked'] and shape(an) == a0, (st.get('counts'), st.get('named'), shape(an)['topics'].get(pq['id'])))
    await edit(cm, cq, answer=cq['answer']); r, st = await run(own)
    r2, an = await analysis(stu, aid)
    check('D the Draft is put right and joined again: the name is shown again', st['counts']['review'] == 0 and shape(an) == b, (st.get('counts'), shape(an)['topics'].get(pq['id'])))
    new = str(uuid.uuid4())
    # TEST: the paper's Draft question gets a new id, the way a corrected version of a paper gives its questions new ids.
    await BM.update_one({'_id': pm['_id'], 'questions.id': pq['id']}, {'$set': {'questions.$.id': new}, '$inc': {'revision': 1}})
    r, st = await run(own); r2, an = await analysis(stu, aid)
    rec = await DB.tejas_question_records.find_one({'qids': new}) or {}
    check("F the paper's Draft is made again with a new question id (as a corrected version does): the record has the new id, remembers the old one, and the older attempt still shows the chapter",
          pq['id'] not in rec.get('qids', [pq['id']]) and {pq['id'], new} <= set(rec.get('seen', [])) and shape(an) == b, (rec.get('qids'), rec.get('seen'), shape(an)['topics'].get(pq['id'])))
    check('B nothing was written into the test, the frozen paper, the answers or the marks by any of this', await frozen(sid, aid) == before, '')
    anon = client(); rev, _ = await mkstaff('reviewer', 'c256r')
    codes = [(await switch(c, False))[0].status_code for c in (anon, rev, stu)]
    still = J(await own.get(API + SLUG)).get('show_chapters')
    check('E only the owner can switch: no login 401; a reviewer and a student 403; the switch stays On', codes == [401, 403, 403] and still is True, (codes, still))
    r, _ = await switch(own, True, 'no-such-exam')
    bad = [(await own.put(API + SLUG + '/analysis', json=body)).status_code for body in ({'on': 'yes'}, {}, {'on': True, 'extra': 1}, {'on': 1})]
    check('E an unknown exam: 404; a body that is not exactly on: true/false: 422; the switch is not changed by them', r.status_code == 404 and bad == [422] * 4
          and J(await own.get(API + SLUG)).get('show_chapters') is True, (r.status_code, bad))
    n = await DB.tejas_audits.count_documents({'action': {'$regex': '^Chapter names in All India analysis'}})
    check('E each real switch is on the record (audit), saying that only names and labels change', n == 3, n)


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    try:
        own, _ = await mkstaff('owner', 'c256')
        got = await setup(own)
        if got and all(ok for _, ok in RESULTS):
            await names(own, *got)
    finally:
        # Only the disposable database this run created; never the app's own.
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB, H.TEST_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB, flush=True)
        bad = [n for n, ok in RESULTS if not ok]
        print(f'TOTAL {len(RESULTS)} PASS {len(RESULTS) - len(bad)} FAIL {len(bad)}', flush=True)


if __name__ == '__main__':
    asyncio.run(main())
