"""TEST-ONLY iteration 224: Supabase away = the book WAITS (never Emergent), shows its place, and carries on from there when Supabase is back.
Disposable DB (iso harness), Supabase faked in memory. No real storage, no real data.
Run: cd /app/backend && python tests/storage_wait224.py
"""
import asyncio, sys, time
from pathlib import Path
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cut_bridge207 import H, J, BM, DB, mkstaff, drain, upload, complete, cut_pdf  # noqa: E402
from tejas import structure, jobs as JOBS  # noqa: E402
import tejas_storage as S  # noqa: E402

RESULTS = []


def check(name, ok, detail=''):
    RESULTS.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:400]), flush=True)


class FakeSupabase:
    """put/get like tejas_storage.sb_put / sb_get. A big file (one with on_progress) reports its pieces like the real resumable upload."""
    def __init__(self):
        self.objects, self.down, self.cut, self.resumes = {}, False, None, []

    def put(self, path, data, content_type, resume=None, on_progress=None):
        if on_progress is not None:
            self.resumes.append(resume)
            info = {**resume} if resume else {'url': 'tus://test/' + path, 'path': path, 'size': len(data), 'started': time.time()}
            sent = resume['sent'] if resume else 0
            on_progress({**info, 'sent': sent})
            step = max(1, len(data) // 4)
            while sent < len(data):
                if self.down or (self.cut is not None and sent >= self.cut):
                    raise S.StorageError(f'Supabase big-file upload stopped at {sent} of {len(data)} bytes (no answer).')
                sent = min(len(data), sent + step); on_progress({**info, 'sent': sent})
        elif self.down:
            raise S.StorageError('Supabase connection failed: ConnectError')
        self.objects[path] = bytes(data)
        return S.SB + 'test-bucket/' + path

    def get(self, bucket, path, tries=4):
        if self.down:
            raise S.StorageWaiting('Supabase abhi file nahi de raha (TEST).')
        return self.objects[path]


def emergent_keys():
    return {k for k in H.STORE if not k.startswith('jeelive/health/')}


async def kicks_done():
    """Waits for the wake-up tasks the app itself started (Supabase back) and drops the long sleeping ones."""
    for _ in range(50):
        pending = [t for t in JOBS._later if not t.done()]
        if not pending:
            return
        await asyncio.sleep(0.1)


def cancel_kicks():
    for t in list(JOBS._later):
        t.cancel()


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
        own, _ = await mkstaff('owner', 'sw')
        slug = J(await own.post('/api/admin/catalog/exams', json={'name': 'SWX', 'short': 'SW', 'subjects': ['Physics'], 'color': 'rose'})).get('slug')
        sec = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Mock Tests', 'description': '', 'layout': 'list', 'kind': 'mocks'})).get('id')
        before = emergent_keys()
        # 1. Supabase goes away half way through the original PDF.
        raw = cut_pdf('SW', long=True)
        b = await upload(own, raw, 'TEST_SW', section_id=sec)
        r = J(await own.get(f'/api/admin/master/types/{sec}/mocks'))
        up = next((u for u in r['uploads'] if u['id'] == b['id']), {})
        check('while parts arrive: Super Admin sees parts X/Y', up.get('parts', {}).get('got') == up.get('parts', {}).get('total') and up['parts']['total'] >= 1, up)
        sb.cut = len(raw) // 2
        await complete(own, b['id'])
        row = await DB.tejas_books.find_one({'_id': b['id']})
        job = await H.TDB.tejas_jobs.find_one({'kind': 'book_step', 'payload.book_id': b['id']}, sort=[('created_at', -1)])
        check('Supabase cut off mid-PDF: book is NOT failed, it waits', row['state'] == 'received' and row['payload'].get('storage_wait'), (row['state'], row['payload'].get('message')))
        check('...the job waits too: queued, a try given back, next run scheduled', job['status'] == 'queued' and job.get('storage_waits') == 1 and job.get('attempts', 0) == 0 and job['next_run_at'] > time.time(), {k: job.get(k) for k in ('status', 'storage_waits', 'attempts', 'error')})
        saved = row['payload'].get('transfer') or {}
        check('...its place in the PDF is saved (sent bytes + upload address)', saved.get('sent', 0) >= len(raw) // 2 and saved.get('url'), saved)
        check('...uploaded parts are kept for the carry-on', await DB.tejas_book_parts.count_documents({'book_id': b['id']}) > 0)
        check('...NOTHING written to Emergent', emergent_keys() == before, emergent_keys() - before)
        r = J(await own.get(f'/api/admin/master/types/{sec}/mocks'))
        up = next((u for u in r['uploads'] if u['id'] == b['id']), {})
        check('Super Admin row: Supabase % and the wait shown', up.get('transfer', {}).get('sent') == saved['sent'] and up['transfer']['size'] == len(raw) and up.get('storage_wait', {}).get('since'), up)
        # 2. Many waits never use up the job's tries.
        for _ in range(6):
            await H.TDB.tejas_jobs.update_one({'id': job['id']}, {'$set': {'next_run_at': 0}}); await JOBS.run_job(job['id'], drain=False)
        job = await H.TDB.tejas_jobs.find_one({'id': job['id']}); row = await DB.tejas_books.find_one({'_id': b['id']})
        check('7 waits in a row: still queued, tries untouched, book not failed', job['status'] == 'queued' and job['storage_waits'] == 7 and job.get('attempts', 0) == 0 and row['state'] == 'received', {k: job.get(k) for k in ('status', 'storage_waits', 'attempts')})
        check('wait time grows (capped at 5 min)', 250 <= job['next_run_at'] - time.time() <= 301, job['next_run_at'] - time.time())
        check('first wait time kept across waits', row['payload']['storage_wait']['since'] <= row['payload']['storage_wait']['at'])
        # 3. Machine panel and badge tell the owner plainly.
        sb.down = True
        m = J(await own.get('/api/admin/machine/status'))
        check('Machine: the book is listed as waiting for Supabase (not as stuck/failed)', [w['id'] for w in m['storage_waiting']] == [b['id']] and m['storage_waiting_jobs'] >= 1 and not m['stuck'] and not m['failed_books'] and m['attention'], {k: m.get(k) for k in ('storage_waiting', 'storage_waiting_jobs', 'stuck', 'failed_books')})
        h = J(await own.get('/api/admin/storage/health?fresh=true'))
        check('badge mode: waiting (never "Emergent backup")', h['mode'] == 'waiting', h['mode'])
        r = J(await own.post('/api/admin/storage/retry'))
        check('Abhi phir try karo while still down: says waiting, wakes nothing', r['mode'] == 'waiting' and r['woke'] == 0, (r['mode'], r.get('woke')))
        rev, _ = await mkstaff('reviewer', 'sw')
        r = await rev.post('/api/admin/storage/retry')
        check('retry is owner-only (a reviewer is refused)', r.status_code in (401, 403), r.status_code)
        # 4. Supabase back: one tap carries the book on from its saved place.
        sb.down = False; sb.cut = None; cancel_kicks()
        r = J(await own.post('/api/admin/storage/retry'))
        check('Supabase back: retry wakes the waiting job at once', r['mode'] in ('supabase', 'slow') and r['woke'] >= 1, (r['mode'], r.get('woke')))
        await kicks_done(); await drain()
        row = await DB.tejas_books.find_one({'_id': b['id']})
        check('carried on from the saved place (same upload address and offset, not from 0)', sb.resumes and sb.resumes[-1] and sb.resumes[-1]['url'] == saved['url'] and sb.resumes[-1]['sent'] == saved['sent'], sb.resumes[-1:])
        check('original in Supabase, wait + place cleared, parts removed', row['payload']['source_path'].startswith('sb://') and 'storage_wait' not in row['payload'] and 'transfer' not in row['payload'] and not await DB.tejas_book_parts.count_documents({'book_id': b['id']}), {k: row['payload'].get(k) for k in ('source_path', 'storage_wait', 'transfer')})
        mk = await BM.find_one({'book_id': b['id']})
        check('book read and cut after Supabase came back: mock ready', mk and mk['state'] == 'ready', mk and (mk['state'], mk['issues']))
        # 5. Supabase away while the pictures are saved at publishing: the mock is NOT held, the book waits, then publishes.
        bk = J(await own.get(f"/api/admin/books/{b['id']}"))
        sb.down = True; S.STATE['down_until'] = 0.0
        r = await own.post(f"/api/admin/books/{b['id']}/control", json={'revision': bk['revision'], 'action': 'publish_ready'}); await drain()
        row = await DB.tejas_books.find_one({'_id': b['id']}); mk = await BM.find_one({'book_id': b['id']})
        check('pictures cannot be saved: mock NOT held, book NOT failed, book waits', r.status_code == 200 and mk['state'] == 'ready' and not mk.get('publish_hold') and row['state'] != 'failed' and row['payload'].get('storage_wait'), (r.status_code, mk['state'], mk.get('publish_hold'), row['state']))
        check('...still nothing in Emergent', emergent_keys() == before, emergent_keys() - before)
        sb.down = False; cancel_kicks()
        r = J(await own.post('/api/admin/storage/retry')); await kicks_done(); await drain()
        mk = await BM.find_one({'book_id': b['id']}); row = await DB.tejas_books.find_one({'_id': b['id']})
        check('Supabase back: the mock publishes by itself, wait cleared', mk['state'] in ('published', 'scheduled') and mk.get('set_id') and 'storage_wait' not in row['payload'], (mk['state'], mk.get('issues'), row['payload'].get('storage_wait')))
        paths = [f['path'] async for f in DB.tejas_files.find({'set_id': mk.get('set_id')}, {'path': 1})] + [f['path'] async for f in DB.tejas_files.find({'path': {'$regex': b['id']}}, {'path': 1})]
        check('every file of this paper lives in Supabase (one store, never split)', paths and all(p.startswith('sb://') for p in paths), [p for p in paths if not p.startswith('sb://')][:5])
        check('in the end: zero new Emergent files', emergent_keys() == before, emergent_keys() - before)
        j = J(await own.get(f'/api/admin/master/types/{sec}/mocks'))
        check('type list still opens after all this', 'uploads' in j and 'items' in j)
        # 6. A Studio import whose saved source cannot be read: queued + waiting (not failed); a Supabase wake runs it again.
        from tejas import imports as IMP
        iid = '00000000-0000-4000-8000-0000000002a4'; src = cut_pdf('IMP')
        sb.objects['tejas/imports/src.pdf'] = src
        import hashlib
        await DB.tejas_imports.insert_one({'id': iid, 'title': 'TEST_IMP', 'format': 'pdf', 'fingerprint': 'x', 'status': 'queued', 'created_at': time.time(), 'created_by': 'owner',
                                           'questions': [], 'issues': [], 'sources': [{'id': 's1', 'kind': 'questions', 'name': 'q.pdf', 'sha256': hashlib.sha256(src).hexdigest(), 'size': len(src), 'path': 'sb://test-bucket/tejas/imports/src.pdf'}]})
        sb.down = True; cancel_kicks(); S._source_cache = S.ByteCache(64 * 1024 * 1024)
        await IMP.process_import(iid)
        rec = await DB.tejas_imports.find_one({'id': iid})
        check('import: Supabase away -> queued and waiting (not failed), one wait counted', rec['status'] == 'queued' and rec.get('storage_wait') and rec.get('storage_waits') == 1, (rec['status'], rec.get('message')))
        check('import: a re-run is scheduled by itself', any(not t.done() for t in JOBS._later))
        sb.down = False; cancel_kicks()
        woke = await JOBS.wake_storage(); await kicks_done()
        rec = await DB.tejas_imports.find_one({'id': iid})
        check('import: Supabase back -> the wake runs it again (no longer waiting)', woke >= 1 and rec['status'] != 'queued' and 'storage_wait' not in rec, (woke, rec['status'], rec.get('message')))
    finally:
        cancel_kicks()
        for p in patches:
            p.stop()
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')


if __name__ == '__main__':
    asyncio.run(main())
