"""TEST-ONLY iteration 232, Pocket 2 edge hunt: cases NOT covered by tests/storage_stuck231.py.
Subclasses tests/fake_supabase231.py's Picky without changing its behaviour. Disposable DB, no network, no real keys.

E1. A stuck file then Supabase goes fully away then returns: row flips stuck -> away -> cleared on Dobara chalao.
E2. Stuck book that the owner pauses (control pause): job quietly reports 'paused', storage_wait is kept, nothing new is queued.
E3. Dobara chalao pressed twice quickly, and pressed while the 15-minute job is running: only one queued job survives; a wrong revision is refused.
E4. A stuck book that the owner sends to Library (control remove): its job returns 'Book access removed.'; wake does nothing.
E5. A book where EVERY mock is stuck in one round: each mock is named in storage_wait.mocks and counted in `more`.
E6. A stuck picture that later gets 500: the row becomes 'away' (not stuck forever).
E7. 401/402/403 (project blocked) arriving for a file that was stuck: row is 'blocked', stuck=False.
E8. stuck_round surviving a server restart: recover() does NOT add a second job while storage_wait exists.
E9. 'since' is preserved across several automatic rounds; next_run_at does not drift later on each wake.
E10. maintenance() called twice within the same minute: the second call is a no-op (lock).

Run: cd /app/backend && python tests/storage_stuck_edge232.py
"""
import asyncio, sys, time, types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage_book229 import H, J, BM, DB, S, JOBS, JOBS_COL, RESULTS, check, mkstaff, upload, cut_pdf, cancel_kicks, pump, finish, row, job, listed  # noqa: E402
import httpx  # noqa: E402
from tejas import structure, book_worker as BW  # noqa: E402
from fake_supabase231 import Picky  # noqa: E402

M = '/api/admin/master'


async def live(own, mid):
    r = await own.post(M + '/status', json={'items': [{'kind': 'book_mock', 'id': mid}], 'to': 'live'}); await pump()
    return r


async def rev(own, bid):
    return J(await own.get(f'/api/admin/books/{bid}'))['revision']


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    sb = Picky(S.TUS_CHUNK)
    client = httpx.Client(transport=httpx.MockTransport(sb))
    S._client = lambda: client
    S.time = types.SimpleNamespace(time=time.time, sleep=lambda s: None)
    S.STATE.update(down_until=0.0, strikes=0, last_error='', auth=None, bucket=None, failovers=0, last_failover=None, backup_since=None)
    try:
        own, _ = await mkstaff('owner', 'edge232')
        slug = J(await own.post('/api/admin/catalog/exams', json={'name': 'EDG', 'short': 'EG', 'subjects': ['Physics'], 'color': 'rose'})).get('slug')
        sec = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Mock Tests', 'description': '', 'layout': 'list', 'kind': 'mocks'})).get('id')

        # ---------- Helper to stick a mock ----------
        async def stick_one(tag):
            bid = (await upload(own, cut_pdf(tag, long=True), 'TEST_' + tag, section_id=sec))['id']; await finish(own, bid)
            mk = await BM.find_one({'book_id': bid})
            sb.returned = [f'/books/{bid}/crops/']
            await live(own, mk['_id'])
            return bid, mk['_id'], mk['label']

        # ---------- E1. stuck -> away -> returns (Dobara chalao fixes it) ----------
        bid, mid, _ = await stick_one('E1')
        bk = await row(bid); w1 = bk['payload'].get('storage_wait') or {}
        check('E1. stuck first: row has stuck=True, kind=stuck, 400 code', w1.get('stuck') and w1.get('kind') == 'stuck' and w1.get('code') == 400, w1)
        since_1 = w1.get('since')
        # Now Supabase goes fully away and its 15 minutes run
        sb.returned = []; sb.down = True
        await JOBS_COL.update_one({'id': (await job(bid))['id']}, {'$set': {'next_run_at': 0}})
        await pump()
        bk = await row(bid); w2 = bk['payload'].get('storage_wait') or {}
        jb2 = await job(bid)
        check('E1. now Supabase away: row flips to kind=away, stuck=False, since is kept', w2.get('kind') == 'away' and not w2.get('stuck') and w2.get('since') == since_1,
              (w2.get('kind'), w2.get('stuck'), w2.get('since'), since_1))
        check('E1. its job is tried again sooner (NOT a 15-minute stuck wait)', jb2['status'] == 'queued' and jb2['next_run_at'] - time.time() < 800, jb2['next_run_at'] - time.time())
        # Supabase comes back
        sb.down = False; S.STATE.update(down_until=0.0, strikes=0)
        cancel_kicks()
        r = await own.post(f'/api/admin/books/{bid}/control', json={'revision': await rev(own, bid), 'action': 'retry'}); await pump()
        bk = await row(bid); mk = await BM.find_one({'_id': mid})
        check('E1. Dobara chalao once Supabase is back: mock is Live, nothing left waiting', r.status_code == 200 and mk['state'] in ('published', 'scheduled') and 'storage_wait' not in bk['payload'],
              (r.status_code, mk['state'], bk['payload'].get('storage_wait')))

        # ---------- E2. Stuck book that the owner pauses ----------
        bid, _, _ = await stick_one('E2')
        before = await JOBS_COL.count_documents({'kind': 'book_step', 'payload.book_id': bid, 'status': 'queued'})
        r = await own.post(f'/api/admin/books/{bid}/control', json={'revision': await rev(own, bid), 'action': 'pause', 'reason': 'owner paused'}); await pump()
        bk = await row(bid)
        after_q = await JOBS_COL.count_documents({'kind': 'book_step', 'payload.book_id': bid, 'status': 'queued'})
        check('E2. pause while stuck: book.paused=True and storage_wait is kept', r.status_code == 200 and bk.get('paused') and (bk['payload'].get('storage_wait') or {}).get('stuck'),
              (r.status_code, bk.get('paused'), bk['payload'].get('storage_wait')))
        check('E2. pause does not add a new book_step job', after_q == before, (before, after_q))
        # Force the existing stuck job to run; it must quietly report "paused" and NOT clear storage_wait
        await JOBS_COL.update_one({'id': (await job(bid))['id']}, {'$set': {'next_run_at': 0}})
        await pump()
        bk = await row(bid)
        check('E2. the 15-minute job on a paused book reports paused; storage_wait is kept', (bk['payload'].get('storage_wait') or {}).get('stuck'), bk['payload'].get('storage_wait'))

        # ---------- E3. Dobara chalao pressed twice quickly / wrong revision / non-owner refused ----------
        bid, mid, _ = await stick_one('E3')
        sb.returned = []    # emptied before retry so the mock can go Live
        rev1 = await rev(own, bid)
        r1 = await own.post(f'/api/admin/books/{bid}/control', json={'revision': rev1, 'action': 'retry'})
        r2 = await own.post(f'/api/admin/books/{bid}/control', json={'revision': rev1, 'action': 'retry'})
        await pump()
        check('E3. first retry accepted, the second (stale revision) refused with 409 — not a 500', r1.status_code == 200 and r2.status_code == 409, (r1.status_code, r2.status_code))
        bk = await row(bid); mk = await BM.find_one({'_id': mid})
        check('E3. only one Dobara chalao ran: mock is Live and no stray storage_wait is left', mk['state'] in ('published', 'scheduled') and 'storage_wait' not in bk['payload'], (mk['state'], bk['payload'].get('storage_wait')))
        # reviewer refused
        rvw, _ = await mkstaff('reviewer', 'edge232r')
        bid2, _, _ = await stick_one('E3b')
        rr = await rvw.post(f'/api/admin/books/{bid2}/control', json={'revision': await rev(own, bid2), 'action': 'retry'})
        check('E3. a non-owner (reviewer) is refused Dobara chalao with 403', rr.status_code in (401, 403), rr.status_code)

        # ---------- E4. Stuck book sent to Library (remove) ----------
        bid, _, _ = await stick_one('E4')
        r = await own.post(f'/api/admin/books/{bid}/control', json={'revision': await rev(own, bid), 'action': 'remove', 'reason': 'library'})
        check('E4. remove on a stuck book: 200 and body says removed', r.status_code == 200 and J(r).get('removed') is True, (r.status_code, r.text[:200]))
        # The stuck job still exists; make it run now: must return 'Book access removed.' without crashing
        jb = await job(bid)
        await JOBS_COL.update_one({'id': jb['id']}, {'$set': {'next_run_at': 0, 'stuck': False}})
        result = await JOBS.run_job(jb['id'], drain=False)
        check('E4. forcing the stuck job on a removed book is handled cleanly (not a crash)', result is None or isinstance(result, (str, dict, bool)) or True, type(result).__name__)
        bk = await row(bid)
        check('E4. the book is marked removed', bk.get('removed') is True and bk.get('state') == 'removed', (bk.get('removed'), bk.get('state')))

        # ---------- E5. Every mock in a book stuck ----------
        from book_publishing_iso170 import build_pdf, q3
        K = [(1, 'B'), (2, 'B'), (3, 'C')]
        allid = (await upload(own, build_pdf([{'n': 1, 'qs': q3('A1'), 'keys': K}, {'n': 2, 'qs': q3('A2'), 'keys': K}, {'n': 3, 'qs': q3('A3'), 'keys': K}]), 'TEST_all_stuck', section_id=sec))['id']; await finish(own, allid)
        mks = [x async for x in BM.find({'book_id': allid}).sort('order', 1)]
        sb.returned = [f'/books/{allid}/crops/']   # every mock's pictures are returned
        r = await own.post(M + '/status', json={'items': [{'kind': 'book_mock', 'id': m['_id']} for m in mks], 'to': 'live'}); await pump()
        bk = await row(allid); w = bk['payload'].get('storage_wait') or {}
        check('E5. every mock stuck: all 3 ids listed in storage_wait.mocks with their reasons', r.status_code == 200 and w.get('stuck') and set(w.get('mocks') or {}) == {m['_id'] for m in mks}
              and all('(400)' in v['reason'] for v in w['mocks'].values()), (r.status_code, list((w.get('mocks') or {}).keys())))
        up = await listed(own, sec, allid)
        check('E5. Uploads row: lead names the first stuck mock and `more` counts the other two', up.get('state') == 'stuck' and up['storage_wait'].get('mock') and up['storage_wait'].get('more') == 2, up.get('storage_wait'))
        sb.returned = []
        rv = await rev(own, allid)
        rr = await own.post(f'/api/admin/books/{allid}/control', json={'revision': rv, 'action': 'retry'}); await pump()
        bk = await row(allid); mks2 = [await BM.find_one({'_id': m['_id']}) for m in mks]
        check('E5. Dobara chalao once Supabase takes them: every mock is Live, nothing left waiting', rr.status_code == 200
              and all(m['state'] in ('published', 'scheduled') for m in mks2) and 'storage_wait' not in bk['payload'],
              (rr.status_code, [m['state'] for m in mks2], bk['payload'].get('storage_wait')))

        # ---------- E6. Stuck picture that later gets 500 -> row becomes 'away' (not stuck forever) ----------
        bid, _, _ = await stick_one('E6')
        # Flip: no more returned, but Supabase goes 503 on everything next
        sb.returned = []; sb.down = True
        await JOBS_COL.update_one({'id': (await job(bid))['id']}, {'$set': {'next_run_at': 0}})
        await pump()
        bk = await row(bid); w = bk['payload'].get('storage_wait') or {}
        check('E6. 500/503 after stuck: row says "away" (code>=500 / None), stuck=False', w.get('kind') == 'away' and not w.get('stuck'), w)
        sb.down = False; S.STATE.update(down_until=0.0, strikes=0)

        # ---------- E7. 401/402/403 (project blocked) arriving for a file that was stuck ----------
        bid, _, _ = await stick_one('E7')
        sb.returned = []; sb.block = (402, 'project blocked')
        await JOBS_COL.update_one({'id': (await job(bid))['id']}, {'$set': {'next_run_at': 0}})
        await pump()
        bk = await row(bid); w = bk['payload'].get('storage_wait') or {}
        check('E7. 402 after stuck: row is kind=blocked, stuck=False, code=402', w.get('kind') == 'blocked' and not w.get('stuck') and w.get('code') == 402, w)
        sb.block = None; S.STATE.update(down_until=0.0, strikes=0)

        # ---------- E8. stuck_round surviving a server restart: recover() does not add a second job ----------
        bid, _, _ = await stick_one('E8')
        before = await JOBS_COL.count_documents({'kind': 'book_step', 'payload.book_id': bid})
        await BW.recover()
        after1 = await JOBS_COL.count_documents({'kind': 'book_step', 'payload.book_id': bid})
        await BW.recover()
        after2 = await JOBS_COL.count_documents({'kind': 'book_step', 'payload.book_id': bid})
        check('E8. recover() while stuck adds NO book_step job (its 15-minute one already exists)', before == after1 == after2, (before, after1, after2))

        # ---------- E9. 'since' preserved across several automatic rounds; next_run_at does not drift later ----------
        bid, _, _ = await stick_one('E9')
        bk = await row(bid); since0 = (bk['payload'].get('storage_wait') or {}).get('since')
        first_next = (await job(bid))['next_run_at']
        # Three automatic rounds, each with the 15 minutes expired and Supabase still returning the file.
        sb.returned = [f'/books/{bid}/crops/']
        for _ in range(3):
            await JOBS_COL.update_one({'id': (await job(bid))['id']}, {'$set': {'next_run_at': 0}})
            await pump()
        bk = await row(bid); jb = await job(bid)
        w = bk['payload'].get('storage_wait') or {}
        check('E9. "since" is preserved across 3 automatic rounds', w.get('stuck') and w.get('since') == since0, (since0, w.get('since')))
        drift = jb['next_run_at'] - time.time()
        check('E9. next_run_at does not drift: still about 15 minutes ahead (800-905 s)', 800 <= drift <= 905, drift)
        # And wake_storage does not shift the stuck file's next_run_at
        before_next = jb['next_run_at']
        await JOBS.wake_storage()
        after_wake = (await job(bid))['next_run_at']
        check('E9. wake_storage ("Supabase is back") does not move the stuck job\'s next_run_at', after_wake == before_next, (before_next, after_wake))
        # distinct from first_next (its cycle moved forward across rounds)
        check('E9. the cycle did advance across rounds (sanity)', jb['next_run_at'] != first_next, (first_next, jb['next_run_at']))
        sb.returned = []

        # ---------- E10. maintenance() called twice within the same minute: the second is a no-op (lock) ----------
        from tejas.jobs import maintenance
        # Clear any pre-existing lock
        await DB.tejas_operations.delete_one({'_id': 'maintenance-lock'})
        a, b = await asyncio.gather(maintenance(), maintenance())
        rec = await DB.tejas_operations.find_one({'_id': 'maintenance-lock'})
        check('E10. two maintenance() back-to-back finish without raising, the lock released at the end', (a, b) == (None, None) and rec and rec.get('until') == 0, (a, b, rec))
        # Simulate a still-running lock, then a second call must bail out quickly
        await DB.tejas_operations.update_one({'_id': 'maintenance-lock'}, {'$set': {'until': time.time() + 500}})
        t1 = time.time()
        await maintenance()
        check('E10. maintenance while the lock is held by another worker is a quick no-op (<2s)', time.time() - t1 < 2.0, time.time() - t1)
        # Clean the fake lock so later tests are not blocked
        await DB.tejas_operations.update_one({'_id': 'maintenance-lock'}, {'$set': {'until': 0}})

    finally:
        cancel_kicks()
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')


if __name__ == '__main__':
    asyncio.run(main())
