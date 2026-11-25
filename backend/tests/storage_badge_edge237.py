"""TEST-ONLY iteration 237, packet D edges not already covered by storage_badge236.py.
Edges tested here, all in-process, isolated DB, fake Supabase (fake_supabase231.Picky), no network:
  1. concurrent GET /api/admin/storage/health triggers ONE probe (the in-process asyncio shield)
  2. a probe whose own DELETE fails leaves one check file; the daily sweep removes it later
  3. a crashed check_lease (set to a future value by a server that then died) expires and does not
     block the next check for ever: the record only guards by `$not: {$gt: t}` so once the lease
     time is in the past the next probe runs
  4. a crashed big_lease (same story) expires and the next /big-test runs
  5. summary() on an EMPTY record (just _id, rev) and on a PARTIALLY filled record: valid shape,
     no crash, level=yellow 'Storage ki jaanch chal rahi hai.'
  6. 50 failure notes at once: the errors list is still capped at 20, readings never exceed 20
  7. a probe whose DELETE fails is ALSO counted: the folder keeps the stale file until sweep
Run: cd /app/backend && python tests/storage_badge_edge237.py
"""
import asyncio, sys, time, types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage_book229 import H, DB, S, RESULTS, check, mkstaff, cancel_kicks  # noqa: E402
import httpx  # noqa: E402
from tejas import structure, storage_health as SH  # noqa: E402
from fake_supabase231 import Picky  # noqa: E402

COL = DB.tejas_storage_state
HEALTH, BIG = '/api/admin/storage/health', '/api/admin/storage/big-test'


def deletes(sb):
    return [p for m, _, p in sb.calls if m == 'DELETE']


async def rec():
    return await COL.find_one({'_id': 'state'})


async def put(change):
    await COL.update_one({'_id': 'state'}, {'$set': change, '$inc': {'rev': 1}})


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    sb = Picky(S.TUS_CHUNK)
    client = httpx.Client(transport=httpx.MockTransport(sb))
    S._client = lambda: client
    S.time = types.SimpleNamespace(time=time.time, sleep=lambda s: None)
    S.STATE.update(down_until=0.0, strikes=0, last_error='', auth=None, bucket=None, failovers=0, last_failover=None, backup_since=None, last_ok=0.0, struck_at=0.0)
    S.EVENTS.clear(); S._recent.clear()
    b = S.bucket_name()
    try:
        own, _ = await mkstaff('owner', 'p3')

        # ---- 1. Concurrent GET /health: one probe only.
        # Force stale so the first call runs probe; the second must share the asyncio task.
        S.probe()  # make a baseline so structure exists
        await SH.flush()
        await put({'checked_at': time.time() - 7200})  # clearly stale
        posts_before = len([1 for m, _, p in sb.calls if m == 'POST' and 'health/check-' in p])
        r1, r2, r3 = await asyncio.gather(own.get(HEALTH), own.get(HEALTH), own.get(HEALTH))
        posts_after = len([1 for m, _, p in sb.calls if m == 'POST' and 'health/check-' in p])
        check('1. three concurrent GET /health: only ONE new probe is sent to Supabase (asyncio.shield)',
              r1.status_code == r2.status_code == r3.status_code == 200 and posts_after - posts_before == 1, (r1.status_code, posts_after - posts_before))

        # ---- 2. A probe whose DELETE fails: the file stays, sweep removes it later.
        # Monkey-patch _drop_checks for one call: raise. Then confirm sweep clears what was left.
        real_drop = S._drop_checks
        def flaky_drop(bucket, names):
            raise S.StorageError('TEST: delete failed')
        S._drop_checks = flaky_drop
        out = S.probe()
        S._drop_checks = real_drop
        left_files = sorted(k.split('/', 1)[1] for k in sb.objects if k.split('/', 1)[1].startswith('health/check-'))
        check('2. a probe whose DELETE fails: the check itself passes (ok) and one check file is left behind',
              out['supabase']['ok'] and len(left_files) == 1, (out['supabase']['ok'], left_files))
        # Age the file back so the sweep (older>=3600s) removes it.
        t = int(time.time())
        aged = f'health/check-{t - 7200}-aaaaaaaaaaaa.bin'
        sb.objects[f'{b}/{aged}'] = sb.objects.pop(f'{b}/{left_files[0]}')
        swept = S.sweep_checks()
        after = sorted(k.split('/', 1)[1] for k in sb.objects if k.split('/', 1)[1].startswith('health/'))
        check('2. the daily sweep removes a check file left behind by a failed delete', swept == 1 and after == [], (swept, after))

        # ---- 3. A crashed check_lease (future value a crashed server left) expires on its own.
        # First: a lease in the future blocks the next probe (control).
        await put({'check_lease': time.time() + 300, 'checked_at': time.time() - 7200})
        posts_before = len([1 for m, _, p in sb.calls if m == 'POST' and 'health/check-' in p])
        await SH.check()
        posts_after = len([1 for m, _, p in sb.calls if m == 'POST' and 'health/check-' in p])
        check('3. control: a check_lease still in the future blocks the next probe', posts_after == posts_before, posts_after - posts_before)
        # Now set the lease to the past: it must no longer block.
        await put({'check_lease': time.time() - 10, 'checked_at': time.time() - 7200})
        SH._running['check'] = None  # clear in-process shield so a new task starts
        before = len([1 for m, _, p in sb.calls if m == 'POST' and 'health/check-' in p])
        await SH.check()
        after = len([1 for m, _, p in sb.calls if m == 'POST' and 'health/check-' in p])
        check('3. a check_lease whose time is in the past (a crashed server) does NOT block the next probe', after - before == 1, after - before)
        # Also: after the check finishes, the record's check_lease is cleared back to 0.
        d = await rec()
        check('3. after a successful probe the record\'s check_lease is 0 again', d.get('check_lease') == 0, d.get('check_lease'))

        # ---- 4. A crashed big_lease expires on its own; the next /big-test runs.
        # Control: future lease → /big-test returns 409.
        await put({'big_lease': time.time() + 400})
        r = await own.post(BIG)
        check('4. control: a big_lease still in the future refuses a new test with 409', r.status_code == 409, r.status_code)
        # Expired lease: /big-test runs.
        await put({'big_lease': time.time() - 10})
        pieces_before = sb.pieces()
        r = await own.post(BIG)
        check('4. a big_lease whose time is in the past does NOT block the next big-file test', r.status_code == 200 and sb.pieces() > pieces_before, (r.status_code, sb.pieces() - pieces_before))
        d = await rec()
        check('4. after a big-file test the record\'s big_lease is 0 again', d.get('big_lease') == 0, d.get('big_lease'))

        # ---- 5. summary() on an empty / partially filled record: valid shape, no crash.
        await COL.delete_one({'_id': 'state'})
        await COL.insert_one({'_id': 'state', 'rev': 0})
        # Reset STATE so configured() is unchanged but there are no in-memory writes/failovers.
        empty = await SH.summary()
        check('5. summary() on EMPTY record: level=yellow, mode=unknown, one jaanch-reason, shape has all three sub-blocks',
              empty['level'] == 'yellow' and empty['mode'] == 'unknown' and 'jaanch chal rahi' in empty['reasons'][0]
              and set(empty.keys()) >= {'supabase', 'big', 'emergent', 'speed', 'held', 'backup'}, (empty['level'], empty['mode'], empty['reasons']))
        check('5. ...all three sub-blocks are safe defaults: supabase.ok=False, big.state=unknown, emergent.ok=False',
              empty['supabase']['ok'] is False and empty['big']['state'] == 'unknown' and empty['emergent']['ok'] is False
              and empty['speed']['supabase'] == {'n': 0} and empty['held'] == {'stuck': 0, 'waiting': 0, 'hung': 0}, (empty['supabase']['ok'], empty['big']['state']))
        # Partially filled: only emergent present, no small/big.
        await COL.delete_one({'_id': 'state'})
        await COL.insert_one({'_id': 'state', 'rev': 0, 'emergent': {'ok': True, 'at': time.time(), 'write_ms': 50, 'read_ms': 20, 'error': ''}})
        partial = await SH.summary()
        check('5. summary() on PARTIAL record (only emergent set, no small/big): still yellow, still "jaanch chal rahi"',
              partial['level'] == 'yellow' and partial['mode'] == 'unknown' and partial['emergent']['ok'] is True
              and partial['supabase']['ok'] is False and partial['big']['state'] == 'unknown', (partial['level'], partial['emergent']['ok']))

        # ---- 6. 50 failure notes at once: the errors list is still capped at 20.
        S._recent.clear()
        for i in range(50):
            S._note_error(f'jeelive/written/TESTflood{i:02d}/a.png', 'supabase', 'small', S._error(f'flood {i:02d}', 400), 400, 'stuck')
        await SH.flush()
        errs = await SH.errors()
        check('6. 50 failure notes at once: the list is capped at 20, newest first', len(errs) == 20 and errs[0]['reason'] == 'flood 49' and errs[-1]['reason'] == 'flood 30', (len(errs), errs[0]['reason'], errs[-1]['reason']))

        # ---- 7. 25 checks: readings for each store never exceed 20.
        for _ in range(25):
            S.probe()
        await SH.flush()
        d = await rec()
        check('7. 25 probes in a row: readings are capped at 20 per store', len(d['readings']['supabase']) == 20 and len(d['readings']['emergent']) == 20, {k: len(d['readings'][k]) for k in d['readings']})
    finally:
        SH._mem['loop'] = None
        cancel_kicks()
        late = SH._running['flush']
        if late and not late.done():
            await asyncio.gather(late, return_exceptions=True)
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')


if __name__ == '__main__':
    asyncio.run(main())
