"""TEST-ONLY iteration 251 (pocket S1b at full size): the owner's whole chapter-wise Chemistry book (24 chapters, 1,250 questions)
through the real app (upload -> Draft -> every chapter Live). Its whole-question and solution pictures are put back to what was saved
before the printed 'Source' line was hidden, then "Line hatao" is pressed once. Says how long the owner waits and proves every picture:
switched, the old one still in storage, only the heading line differs (white), and the picture proof of every test passes.
Supabase faked at the wire, disposable DB, no network, no AI.
Run: cd /app/backend && python -u tests/source_repaint_full251.py   (drops only its own disposable database)
"""
import asyncio, sys, time, types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import source_repaint250 as T  # noqa: E402
from source_repaint250 import H, BM, S, J, RESULTS, check, mkstaff, upload, cancel_kicks, age, rows_of, switched, untouched, held, Bent, API, SETS  # noqa: E402
from storage_book229 import pump  # noqa: E402
from source_hidden248 import painted  # noqa: E402
from book_speed211 import REAL  # noqa: E402
import httpx  # noqa: E402
from tejas import structure, source_repaint as SR  # noqa: E402
from tejas.picture_proof import prove  # noqa: E402

STATUS = '/api/admin/master/status'


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    T.sb = sb = Bent(S.TUS_CHUNK)
    wire = httpx.Client(transport=httpx.MockTransport(sb))
    S._client = lambda: wire                                                 # nothing leaves this process
    S.time = types.SimpleNamespace(time=time.time, sleep=lambda s: None)     # the storage code's own waits only
    S.STATE.update(down_until=0.0, strikes=0, last_error='', auth=None, bucket=None, failovers=0, last_failover=None, backup_since=None)
    try:
        own, _ = await mkstaff('owner', 'rp251')
        slug = J(await own.post('/api/admin/catalog/exams', json={'name': 'RPFX', 'short': 'RF', 'subjects': ['Chemistry'], 'color': 'rose'})).get('slug')
        chap = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Chapter-wise', 'description': '', 'layout': 'chapters', 'kind': 'chapters'})).get('id')
        await structure.exams.update_one({'_id': slug}, {'$set': {'shown': True}})
        t = time.time()
        bid = (await upload(own, Path(REAL).read_bytes(), 'TEST_RP251_CHEM', section_id=chap, subject='Chemistry'))['id']
        await own.post(f'/api/admin/books/{bid}/complete'); await pump(3000)
        mocks = await BM.find({'book_id': bid}).sort('order', 1).to_list(100)
        check('the whole book is read: 24 chapters, 1,250 questions, none held', len(mocks) == 24 and sum(len(m['questions']) for m in mocks) == 1250 and all(m['state'] == 'ready' for m in mocks),
              (len(mocks), sum(len(m['questions']) for m in mocks), [(m['label'], m['issues'][:2]) for m in mocks if m['state'] != 'ready'][:3]))
        print(f'  upload to Draft: {time.time() - t:.0f} s', flush=True)
        t = time.time()
        for i in range(0, len(mocks), 6):
            await own.post('/api/auth/refresh')  # TEST: this walk is longer than one 15-minute sign-in
            r = await own.post(STATUS, json={'items': [{'kind': 'book_mock', 'id': m['_id']} for m in mocks[i:i + 6]], 'to': 'live'}); await pump(3000)
            assert r.status_code == 200, (r.status_code, r.text[:300])
        mocks = await BM.find({'book_id': bid}).sort('order', 1).to_list(100)
        sids = [m['set_id'] for m in mocks if m['state'] == 'published' and m.get('set_id')]
        check('every chapter is Live', len(sids) == 24, [(m['label'], m['state'], m['issues'][:2]) for m in mocks if m['state'] != 'published'][:4])
        print(f'  Draft to Live: {time.time() - t:.0f} s', flush=True)
        old = {}
        for sid in sids:
            old.update((await age(sid, REAL, unshrunk=2))[1])
        want = sum(1 for o in old.values() if o['line'])
        await own.post('/api/auth/refresh')
        st = J(await own.get(API + '/status'))
        check('before: every whole-question and solution picture of the 24 tests waits', st.get('waiting') == len(old) >= 2500 and want > 0, (st, len(old), want))
        sets0 = {s['id']: s for s in await SETS.find({'id': {'$in': sids}}).to_list(None)}
        t = time.time(); r = await own.post(API + '/start'); await T.ran(own, 3000); took = time.time() - t
        await own.post('/api/auth/refresh'); st = J(await own.get(API + '/status'))
        print(f'  "Line hatao": {len(old)} pictures ({want} with the line) in {took:.0f} s', flush=True)
        check('"Line hatao" once: the run finishes; every picture with the line is done, none is left', r.status_code == 200 and st.get('state') == 'done' and st.get('painted') == want
              and st.get('clean') == len(old) - want and st.get('left') == 0 and st.get('failures') == [] and st.get('waiting') == 0, st)
        rows = await rows_of(old)
        check('each is switched to a new picture beside the old one; the record keeps where the old one is', all(switched(rows[i], o) for i, o in old.items() if o['line']),
              [(o['at'], rows[i].get('source_mask')) for i, o in old.items() if o['line'] and not switched(rows[i], o)][:3])
        check('a picture without the line is left exactly as it was', all(untouched(rows[i], o) for i, o in old.items() if not o['line']), '')
        check('no old picture was removed or overwritten', all(held(o['path']) == o['bytes'] for o in old.values()), [o['at'] for o in old.values() if held(o['path']) != o['bytes']][:4])
        lined = [(i, o) for i, o in old.items() if o['line']]
        found = await asyncio.gather(*(asyncio.to_thread(painted, REAL, o['ref'], held(rows[i]['path']), o['bytes']) for i, o in lined))
        bad = [(o['at'], o['ref']['page'], why) for (i, o), (ok, why) in zip(lined, found) if not ok]
        check(f"every one of the {want} new pictures differs from the old one inside the heading 'Source' line alone, and that line is white", not bad, (len(bad), bad[:3]))
        check('the tests themselves are not touched', {s['id']: s for s in await SETS.find({'id': {'$in': sids}}).to_list(None)} == sets0, '')
        proofs = [await prove(await SETS.find_one({'id': sid}, {'_id': 0}), full=True) for sid in sids]
        check('the picture proof of every test passes: every picture read back, all in Supabase', all(p and p['ok'] and p['store'] == 'supabase' for p in proofs), [p for p in proofs if not (p and p['ok'])][:2])
    finally:
        cancel_kicks()
        for task in list(SR._tasks):
            task.cancel()
        # Only the disposable database this run created; never the app's own.
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB, H.TEST_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB, flush=True)
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}', flush=True)


if __name__ == '__main__':
    asyncio.run(main())
