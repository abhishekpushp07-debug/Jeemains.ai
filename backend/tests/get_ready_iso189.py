"""TEST-ONLY iteration 189 retest: answer save blocked (409) while ready_until > now; /assets/pack skips crops that fail to
render or whose source file is missing (no 500). Isolated disposable DB. Run: cd /app/backend && timeout 290 python tests/get_ready_iso189.py
"""
import asyncio, json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import get_ready_iso188 as G  # noqa: E402
from get_ready_iso188 import H, mkstaff, upload, complete, drain, check, RESULTS, J, go, student, answer, unpack, mkset, structure, two_opt_pdf, M, BM, ATT  # noqa: E402
from tejas import attempts as ATTMOD  # noqa: E402

DB = H.TDB


# answers: ready_until guard
async def save_guard(a):
    sid = await mkset('GUARD', exam='JEE Main', catalog_section_id='jee-main:mocks', test_kind='mock', title='TEST_Guard')
    x = J(await go(a, sid)); aid = x['id']; qid = x['questions'][0]['id']
    r = await answer(a, aid, qid, 'A')
    check('PUT answer during countdown -> 409', r.status_code == 409, (r.status_code, r.text[:200]))
    check('409 message "Your paper opens in a few seconds"', 'paper opens in a few seconds' in r.text.lower(), r.text[:200])
    check('409 Retry-After header', r.headers.get('retry-after') == '2', dict(r.headers))
    row = await ATT.find_one({'id': aid}); check('nothing saved during countdown', not (row.get('answers') or {}).get(qid), row.get('answers'))
    await a.post(f'/api/attempts/{aid}/begin')
    r = await answer(a, aid, qid, 'A'); d = J(r)
    check('PUT answer after /begin -> 200 saved', r.status_code == 200 and (d.get('accepted') or {}).get('value') == 'A', (r.status_code, r.text[:200]))
    await a.post(f'/api/attempts/{aid}/submit')
    # countdown elapsed naturally (simulate by moving ready_until into the past)
    y = J(await go(a, sid)); bid = y['id']; q2 = y['questions'][0]['id']
    await ATT.update_one({'id': bid}, {'$set': {'ready_until': time.time() - 1}})
    r = await answer(a, bid, q2, 'B')
    check('PUT answer after countdown elapsed -> 200', r.status_code == 200, (r.status_code, r.text[:200]))
    r = await a.post(f'/api/attempts/{bid}/submit'); check('submit ok (200/202)', r.status_code in (200, 202), r.status_code)
    # no get_ready attempt saves immediately
    z = J(await go(a, sid, ready=False)); r = await answer(a, z['id'], z['questions'][0]['id'], 'A')
    check('no get_ready attempt saves immediately', r.status_code == 200, (r.status_code, r.text[:150]))
    await a.post(f"/api/attempts/{z['id']}/submit")


# pack: one bad crop skipped, missing file skipped
async def pack_skip(own, stu):
    b = await upload(own, two_opt_pdf('PSKIP'), 'TEST_PSKIP', section_id='jee-main:mocks'); await complete(own, b['id']); await drain()
    m = await BM.find_one({'book_id': b['id']}); base = f"/api/admin/books/{b['id']}/mocks/{m['_id']}"
    p = J(await own.get(base + '/problems', params={'all': 'true'}))
    for q in p.get('questions', []):
        p = J(await own.get(base + '/problems', params={'all': 'true'}))
        await own.post(base + '/fix', json={'revision': p['revision'], 'question_id': q['id'], 'response_type': 'mcq', 'option_labels': ['A', 'B'], 'answer': 'B', 'complete': True}); await drain()
    await own.post(M + '/status', json={'items': [{'kind': 'book_mock', 'id': m['_id']}], 'to': 'live'}); await drain()
    sid = (await BM.find_one({'_id': m['_id']})).get('set_id')
    await asyncio.sleep(2); await structure.visibility(force=True)
    check('pskip set built', bool(sid), m.get('state'))
    if not sid: return
    x = J(await go(stu, sid)); aid = x['id']
    r = await stu.get(f'/api/attempts/{aid}/assets/pack'); head, imgs, _ = unpack(r.content)
    full = [(i['question_id'], i['index']) for i in head['items']]
    check('baseline pack has >=2 items', r.status_code == 200 and len(full) >= 2, (r.status_code, head))
    orig = ATTMOD.render_crop; calls = {'n': 0}

    def bad(src, ref):
        calls['n'] += 1
        if calls['n'] == 1: raise RuntimeError('TEST broken crop')
        return orig(src, ref)
    ATTMOD.render_crop = bad
    try:
        r = await stu.get(f'/api/attempts/{aid}/assets/pack'); h2, i2, exact = unpack(r.content) if r.status_code == 200 else ({}, [], False)
    finally:
        ATTMOD.render_crop = orig
    check('pack with 1 failing crop -> 200 (not 500)', r.status_code == 200, (r.status_code, r.text[:200]))
    got = [(i['question_id'], i['index']) for i in h2.get('items', [])]
    check('failing crop omitted, others returned, header lists only rendered', len(got) == len(full) - 1 and set(got) <= set(full) and exact and h2.get('total') == head['total'], (got, full))
    check('remaining images PNG', all(i[:8] == b'\x89PNG\r\n\x1a\n' for i in i2), '')
    # missing source file: hide file record
    att = await ATT.find_one({'id': aid}); qs = att.get('questions') or []
    if att.get('pack_id'):
        from tejas.packs import entry_for
        qs = (await entry_for(att['pack_id'])).questions
    fids = {r_['file_id'] for q in qs for r_ in q.get('q_refs', [])}
    await DB.tejas_files.update_many({'id': {'$in': list(fids)}}, [{'$set': {'id': {'$concat': ['$id', '-hidden189']}}}])
    try:
        r = await stu.get(f'/api/attempts/{aid}/assets/pack'); h3 = unpack(r.content)[0] if r.status_code == 200 else {}
    finally:
        for f in fids:
            await DB.tejas_files.update_one({'id': f + '-hidden189'}, {'$set': {'id': f}})
    check('pack with missing source files -> 200, items empty, total kept', r.status_code == 200 and h3.get('items') == [] and h3.get('total') == head['total'], (r.status_code, r.text[:200], h3))
    r = await stu.get(f'/api/attempts/{aid}/assets/pack'); check('pack recovers after restore', r.status_code == 200 and len(unpack(r.content)[0]['items']) == len(full), r.status_code)
    await stu.post(f'/api/attempts/{aid}/submit')


async def main():
    own, _ = await mkstaff('owner', 'g189'); a = await student('93'); b = await student('92')
    await structure.exams.update_one({'_id': 'jee-main'}, {'$set': {'shown': True}})
    print('files coll ok', 'tejas_files' in await DB.list_collection_names(), flush=True)
    for fn in (lambda: save_guard(a), lambda: pack_skip(own, b)):
        try: await fn()
        except Exception:
            import traceback; traceback.print_exc(); check('section ran', False, 'exception above')


async def run():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    try: await main()
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
        for r in RESULTS: print('PASS' if r[1] else 'FAIL', r[0], '' if r[1] else r[2])
        ok = sum(1 for r in RESULTS if r[1]); print(f'TOTAL {len(RESULTS)} PASS {ok} FAIL {len(RESULTS) - ok}'); print('dropped', H.TEST_DB)

if __name__ == '__main__':
    asyncio.run(run())
