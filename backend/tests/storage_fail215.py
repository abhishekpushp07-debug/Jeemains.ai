"""TEST-ONLY iteration 215: storage failures never sink a whole book, and the same PDF chosen again after a failure carries on.
Disposable DB, storage mocked (iso harness). No real storage, no real data.
Run: cd /app/backend && python tests/storage_fail215.py
"""
import asyncio, hashlib, importlib.util, sys, uuid
from pathlib import Path
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cut_bridge207 as B  # noqa: E402
from cut_bridge207 import H, J, BM, DB, mkstaff, drain, upload, complete, cut_pdf  # noqa: E402
from tejas import structure, book_publish  # noqa: E402
import tejas_storage  # noqa: E402

RESULTS = []


def check(name, ok, detail=''):
    RESULTS.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:400]), flush=True)


def storage_unit():
    # The harness swaps tejas_storage.request for an in-memory store; the real retry code is loaded fresh from its file here.
    spec = importlib.util.spec_from_file_location('real_storage215', str(Path(__file__).resolve().parents[1] / 'tejas_storage.py'))
    S = importlib.util.module_from_spec(spec); spec.loader.exec_module(S)
    calls = {'n': 0}

    class R:
        def __init__(self, code): self.status_code, self.ok = code, code == 200
        def json(self): return {'path': 'x/y.png'}

    def fake(codes):
        def go(*a, **k):
            calls['n'] += 1; return R(codes[min(calls['n'] - 1, len(codes) - 1)])
        return go
    with mock.patch.object(S, 'init_storage', lambda force=False: 'k'), mock.patch.object(S.time, 'sleep', lambda s: None):
        with mock.patch.object(S.requests, 'request', fake([500, 502, 200])):
            calls['n'] = 0; r = S.request('PUT', 'a/b', b'x')
            check('storage: two 5xx then OK succeeds (retried)', r.ok and calls['n'] == 3, calls)
        with mock.patch.object(S.requests, 'request', fake([500])):
            calls['n'] = 0
            try:
                S.request('PUT', 'a/b', b'x'); ok = False
            except S.StorageError:
                ok = True
            check('storage: lasting 500 gives up after 4 tries with a clear error', ok and calls['n'] == 4, calls)


async def main():
    storage_unit()
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    try:
        own, _ = await mkstaff('owner', 'sf')
        slug = J(await own.post('/api/admin/catalog/exams', json={'name': 'SFX', 'short': 'SF', 'subjects': ['Physics'], 'color': 'rose'})).get('slug')
        sec = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Mock Tests', 'description': '', 'layout': 'list', 'kind': 'mocks'})).get('id')
        raw = cut_pdf('SF', long=True)
        b = await upload(own, raw, 'TEST_SF', section_id=sec); await complete(own, b['id']); await drain()
        m = await BM.find_one({'book_id': b['id']})
        check('book read and cut: mock ready', m and m['state'] == 'ready', m and (m['state'], m['issues']))
        bk = J(await own.get(f"/api/admin/books/{b['id']}"))

        def broken(*a, **k):
            raise tejas_storage.StorageError('Private storage unavailable (500). Retry later or check account storage permissions and quota.')
        with mock.patch.object(book_publish, 'put_object', broken):
            r = await own.post(f"/api/admin/books/{b['id']}/control", json={'revision': bk['revision'], 'action': 'publish_ready'})
            check('publish requested', r.status_code == 200, r.text[:200]); await drain()
        row = await DB.tejas_books.find_one({'_id': b['id']}); m = await BM.find_one({'book_id': b['id']})
        check('storage down while publishing: the book is NOT failed', row['state'] != 'failed', (row['state'], row['payload'].get('message')))
        check('storage down: only that mock waits, with the storage reason', m['state'] == 'held' and any('storage' in x.lower() for x in m['issues']), (m['state'], m['issues']))
        r = await own.get(f'/api/admin/master/types/{sec}/mocks')
        check('type list still opens', r.status_code == 200, r.status_code)
        # Storage is back: Retry re-runs the saved work and honours the Publish the owner already asked for.
        bk = J(await own.get(f"/api/admin/books/{b['id']}"))
        r = await own.post(f"/api/admin/books/{b['id']}/control", json={'revision': bk['revision'], 'action': 'retry'}); await drain()
        m = await BM.find_one({'book_id': b['id']})
        check('storage back + Retry: the mock publishes, nothing re-uploaded', r.status_code == 200 and m['state'] in ('published', 'scheduled') and m.get('set_id'), (r.status_code, m['state'], m['issues']))
        # Book page shows counts without loading every question.
        bk = J(await own.get(f"/api/admin/books/{b['id']}"))
        mm = bk['mocks'][0]
        check('book page: counts right, no questions/cuts sent', mm['count'] == len(m['questions']) and 'questions' not in mm and 'cuts' not in mm, {k: mm.get(k) for k in ('count', 'key_only', 'original_solutions')})
        # A failed book: the same PDF chosen again carries on instead of doing nothing.
        raw2 = cut_pdf('SF2')
        b2 = await upload(own, raw2, 'TEST_SF2', section_id=sec); await complete(own, b2['id']); await drain()
        await DB.tejas_books.update_one({'_id': b2['id']}, {'$set': {'state': 'failed', 'payload.message': 'Processing interrupted.'}})
        r = await own.get(f'/api/admin/master/types/{sec}/mocks')
        up = [u for u in J(r)['uploads'] if u['id'] == b2['id']]
        check('failed book offers Dobara chalao (can_retry + revision)', up and up[0]['can_retry'] and isinstance(up[0].get('revision'), int), up)
        sha = hashlib.sha256(raw2).hexdigest()
        r = await own.post('/api/admin/books', json={'filename': 'TEST_SF2.pdf', 'title': 'TEST_SF2', 'sha256': sha, 'size': len(raw2), 'edition': '', 'rights_confirmed': True, 'section_id': sec})
        d = J(r)
        check('same PDF again after failure: accepted and carrying on', r.status_code == 200 and d.get('state') in ('reading', 'matching', 'received') and 'again' in d.get('message', ''), (r.status_code, d.get('state'), d.get('message')))
        await drain()
        row = await DB.tejas_books.find_one({'_id': b2['id']})
        check('...and it finishes', row['state'] in ('ready', 'attention_needed', 'published'), (row['state'], row['payload'].get('message')))
        r = await own.post('/api/admin/books', json={'filename': 'TEST_SF2.pdf', 'title': 'TEST_SF2', 'sha256': sha, 'size': len(raw2), 'edition': '', 'rights_confirmed': True, 'section_id': sec})
        check('same PDF again when nothing failed: just opens it (no re-run)', r.status_code == 200 and J(r).get('state') == row['state'], (J(r).get('state'), row['state']))
    finally:
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')


if __name__ == '__main__':
    asyncio.run(main())
