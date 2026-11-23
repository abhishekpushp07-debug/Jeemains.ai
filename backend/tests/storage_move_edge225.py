"""TEST-ONLY (testing agent, iteration 218): edge cases for tejas/storage_move.py.
1) more than BATCH import docs with an un-copyable source must not hide later good imports (run must not say 'done' early)
2) two concurrent begin() calls -> only one run
3) a stale book-worker save after the switch (book_store.save style $set of whole payload) reverts source_path (documents the race)
Disposable DB (iso harness), Supabase faked. Run: cd /app/backend && python tests/storage_move_edge225.py
"""
import asyncio, hashlib, sys, time, uuid
from pathlib import Path
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage_wait224 import FakeSupabase  # noqa: E402
from cut_bridge207 import H, J, DB, mkstaff, cut_pdf  # noqa: E402
from tejas import structure, storage_move as SM  # noqa: E402
import tejas_storage as S  # noqa: E402

RESULTS = []


def check(name, ok, detail=''):
    RESULTS.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:400]), flush=True)


async def settle():
    while SM._tasks:
        await asyncio.gather(*list(SM._tasks))


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    sb = FakeSupabase()
    patches = [mock.patch.object(S, 'configured', lambda: True), mock.patch.object(S, 'sb_put', sb.put), mock.patch.object(S, 'sb_get', sb.get),
               mock.patch.object(S, 'bucket_name', lambda: 'test-bucket')]
    for p in patches:
        p.start()
    S.STATE.update(down_until=0.0, strikes=0, failovers=0, last_failover=None, backup_since=None)
    try:
        own, _ = await mkstaff('owner', 'mve')
        pdf = cut_pdf('MVE')
        h = hashlib.sha256(pdf).hexdigest()
        # 1) 25 imports whose source is missing from Emergent, then 1 good import inserted last
        bad = [{'id': f'TEST_bad_{i}', 'title': f'TEST_bad_{i}', 'created_at': time.time() + i,
                'sources': [{'id': 's', 'path': f'tejas/test/lost_{i}.pdf', 'sha256': h}]} for i in range(25)]
        await DB.tejas_imports.insert_many(bad)
        H.STORE['tejas/test/good_imp.pdf'] = pdf
        await DB.tejas_imports.insert_one({'id': 'TEST_good', 'title': 'TEST_good', 'created_at': time.time() + 100,
                                           'sources': [{'id': 's', 'path': 'tejas/test/good_imp.pdf', 'sha256': h}]})
        # 2) concurrent begin
        toks = await asyncio.gather(SM.begin(True), SM.begin(True))
        check('two concurrent begin() -> exactly one run', sum(1 for t in toks if t) == 1, toks)
        await settle()
        st = J(await own.get('/api/admin/storage/move/status'))
        good = await DB.tejas_imports.find_one({'id': 'TEST_good'})
        check('good import beyond the first 20+ failing imports still gets copied',
              good['sources'][0]['path'].startswith('sb://'), (st['state'], st['moved'], st['failed'], good['sources'][0]['path']))
        check('run not "done" while a copyable file remains', not (st['state'] == 'done' and not good['sources'][0]['path'].startswith('sb://')),
              (st['state'], st['remaining']))
        # 3) worker race, the way the app really does it: a worker saves only while it holds the book's lock (book_store.lock_book/save_book)
        H.STORE['tejas/test/book_race.pdf'] = pdf
        bid = 'TEST_race_book'
        await DB.tejas_books.insert_one({'_id': bid, 'state': 'reading', 'removed': False, 'payload': {'title': 'TEST_race', 'source_path': 'tejas/test/book_race.pdf', 'sha256': h}})
        await DB.tejas_books.update_one({'_id': bid}, {'$set': {'lock_token': 'worker', 'lock_until': time.time() + 900}})  # the worker locks + loads it
        stale = await DB.tejas_books.find_one({'_id': bid})
        await SM.begin(True); await settle()
        mid = await DB.tejas_books.find_one({'_id': bid})
        check('a book a worker holds is not switched under it', mid['payload']['source_path'] == 'tejas/test/book_race.pdf', mid['payload'])
        await DB.tejas_books.update_one({'_id': bid, 'lock_token': 'worker'}, {'$set': {'payload': stale['payload'], 'state': 'ready'}, '$unset': {'lock_token': '', 'lock_until': ''}})  # worker saves + unlocks
        await SM.begin(True); await settle()
        after = await DB.tejas_books.find_one({'_id': bid})
        check('after the worker lets go, the next copy switches it (and it stays switched)', after['payload']['source_path'].startswith('sb://') and after['payload'].get('moved_from') == 'tejas/test/book_race.pdf', after['payload'])
        check('Emergent copy of race book still present', 'tejas/test/book_race.pdf' in H.STORE)
    finally:
        for p in patches:
            p.stop()
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')


if __name__ == '__main__':
    asyncio.run(main())
