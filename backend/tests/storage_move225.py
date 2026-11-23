"""TEST-ONLY iteration 225: old Emergent files are copied into Supabase with the SAME bytes, so a phone sees the same ETag and
asset_revision (nothing downloaded again); a file that cannot be copied stays on Emergent and keeps working; Emergent copies are kept.
Disposable DB (iso harness), Supabase faked in memory. Run: cd /app/backend && python tests/storage_move225.py
"""
import asyncio, hashlib, io, sys, time, uuid
from pathlib import Path
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage_wait224 import FakeSupabase  # noqa: E402
from cut_bridge207 import H, J, DB, mkstaff, cut_pdf  # noqa: E402
from tejas import structure, storage_move as SM, jobs as JOBS  # noqa: E402
from tejas.derivatives import render_crop  # noqa: E402
from tejas.pictures import etag_of, revisions  # noqa: E402
import tejas_storage as S  # noqa: E402

RESULTS = []


def check(name, ok, detail=''):
    RESULTS.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:400]), flush=True)


def png_bytes():
    from PIL import Image
    out = io.BytesIO(); Image.new('RGB', (40, 20), (200, 30, 30)).save(out, 'PNG'); return out.getvalue()


def sha(b):
    return hashlib.sha256(b).hexdigest()


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
        own, _ = await mkstaff('owner', 'mv'); rev, _ = await mkstaff('reviewer', 'mv')
        png, pdf, pdf2 = png_bytes(), cut_pdf('MV'), cut_pdf('MV2')
        old = {'png': 'tejas/test/a.png', 'pdf': 'tejas/test/src.pdf', 'nosha': 'tejas/test/nosha.pdf', 'bad': 'tejas/test/bad.png',
               'missing': 'tejas/test/missing.png', 'book': 'tejas/test/book.pdf', 'cb': 'tejas/test/cb.pdf', 'imp': 'tejas/test/i1.pdf'}
        for k, raw in (('png', png), ('pdf', pdf), ('nosha', pdf2), ('bad', png), ('book', pdf), ('cb', pdf), ('imp', pdf)):
            H.STORE[old[k]] = raw
        ids = {k: str(uuid.uuid4()) for k in ('png', 'pdf', 'nosha', 'bad', 'missing')}
        await DB.tejas_files.insert_many([
            {'id': ids['png'], 'kind': 'rendered_png', 'path': old['png'], 'sha256': sha(png), 'filename': 'q1.png', 'created_at': time.time()},
            {'id': ids['pdf'], 'kind': 'combined', 'path': old['pdf'], 'sha256': sha(pdf), 'filename': 'paper.pdf', 'created_at': time.time()},
            {'id': ids['nosha'], 'kind': 'combined', 'path': old['nosha'], 'filename': 'old.pdf', 'created_at': time.time()},
            {'id': ids['bad'], 'kind': 'rendered_png', 'path': old['bad'], 'sha256': 'ab' * 32, 'filename': 'bad.png', 'created_at': time.time()},
            {'id': ids['missing'], 'kind': 'rendered_png', 'path': old['missing'], 'sha256': sha(png), 'filename': 'gone.png', 'created_at': time.time()},
            {'id': str(uuid.uuid4()), 'kind': 'rendered_png', 'path': 'sb://test-bucket/already.png', 'sha256': sha(png), 'created_at': time.time()}])
        bid, cbid, iid = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
        await DB.tejas_books.insert_one({'_id': bid, 'state': 'ready', 'removed': True, 'payload': {'title': 'TEST_MV_BOOK', 'source_path': old['book'], 'sha256': sha(pdf)}})
        await DB.tejas_chapter_books.insert_one({'id': cbid, 'title': 'TEST_MV_CB', 'status': 'ready', 'archived': True, 'source': {'path': old['cb'], 'sha256': sha(pdf)}})
        await DB.tejas_imports.insert_one({'id': iid, 'title': 'TEST_MV_IMP', 'status': 'ready', 'sources': [{'id': 's1', 'path': old['imp'], 'sha256': sha(pdf)}, {'id': 's2', 'path': 'sb://test-bucket/x.pdf'}]})
        ref = {'page': 1, 'rect': [20, 40, 400, 140]}
        q = {'id': str(uuid.uuid4()), 'q_refs': [{'file_id': ids['png'], 'page': 1, 'rect': [0, 0, 40, 20], 'prerendered': True}],
             's_refs': [{'file_id': ids['nosha'], **ref}], 'c_refs': [{'file_id': ids['pdf'], **ref}]}

        async def look():
            src = {f['id']: f async for f in DB.tejas_files.find({'id': {'$in': list(ids.values())}}, {'_id': 0})}
            S._source_cache = S.ByteCache(64 * 1024 * 1024)
            tags = {k: etag_of(await asyncio.to_thread(render_crop, src[ids[k]], r)) for k, r in (('png', q['q_refs'][0]), ('pdf', q['c_refs'][0]), ('nosha', q['s_refs'][0]))}
            return tags, (await revisions([q]))[q['id']]
        tags0, rev0 = await look()
        check('before: pictures render from Emergent with ETags + an asset_revision', len(tags0) == 3 and rev0, (tags0, rev0))
        # 1. Owner only.
        r = await rev.post('/api/admin/storage/move/start')
        check('copy is owner-only (reviewer refused)', r.status_code in (401, 403), r.status_code)
        st = J(await own.get('/api/admin/storage/move/status'))
        check('status counts every old file (5 files, 1 book, 1 chapter book, 1 import source)', st['remaining'] == {'files': 5, 'books': 1, 'chapter_books': 1, 'imports': 1} and st['state'] == 'idle', st['remaining'])
        check('status shows no storage paths', 'tejas/test' not in str(st), st)
        # 2. Supabase away: Start says so at once (fresh check); a run Supabase drops in the middle waits, nothing switches.
        sb.down = True
        r = await own.post('/api/admin/storage/move/start')
        check('Start while Supabase is down: clear 409 from a fresh check', r.status_code == 409 and 'Supabase' in r.text, (r.status_code, r.text[:160]))
        S.STATE.update(down_until=0.0, strikes=0)
        await SM.begin(True); await settle()
        st = J(await own.get('/api/admin/storage/move/status'))
        check('Supabase drops mid-run: the copy waits (not failed), nothing switched', st['state'] == 'waiting' and st['moved'] == 0 and st['failed'] == 0 and st['remaining_total'] == 8, (st['state'], st['moved'], st['failed']))
        # 3. Supabase back: a healthy check carries the copy on by itself.
        sb.down = False
        r = J(await own.post('/api/admin/storage/retry')); await settle()
        st = J(await own.get('/api/admin/storage/move/status'))
        check('Supabase back: the copy carries on by itself and finishes', st['state'] == 'done' and st['moved'] == 6 and st['failed'] == 2, {k: st[k] for k in ('state', 'moved', 'failed', 'skipped', 'remaining')})
        rows = {f['id']: f async for f in DB.tejas_files.find({'id': {'$in': list(ids.values())}}, {'_id': 0})}
        moved_ok = all(rows[ids[k]]['path'] == 'sb://test-bucket/' + old[k] and rows[ids[k]]['moved_from'] == old[k] for k in ('png', 'pdf', 'nosha'))
        check('copied files point to Supabase (same key) and remember where they came from', moved_ok, {k: rows[ids[k]].get('path') for k in ids})
        check('Supabase holds byte-exact copies', all(sb.objects.get(old[k]) == H.STORE[old[k]] for k in ('png', 'pdf', 'nosha', 'book', 'cb', 'imp')))
        check('Emergent copies are all still there (nothing deleted)', all(old[k] in H.STORE for k in ('png', 'pdf', 'nosha', 'bad', 'book', 'cb', 'imp')))
        book = await DB.tejas_books.find_one({'_id': bid}); cb = await DB.tejas_chapter_books.find_one({'id': cbid}); imp = await DB.tejas_imports.find_one({'id': iid})
        check('book, chapter book and import sources switched too (with moved_from)', book['payload']['source_path'].startswith('sb://') and book['payload']['moved_from'] == old['book']
              and cb['source']['path'].startswith('sb://') and cb['source']['moved_from'] == old['cb'] and imp['sources'][0]['path'].startswith('sb://') and imp['sources'][1]['path'] == 'sb://test-bucket/x.pdf',
              (book['payload'].get('source_path'), cb['source'].get('path'), [s['path'] for s in imp['sources']]))
        check('wrong-hash and missing files stay on Emergent (not switched)', rows[ids['bad']]['path'] == old['bad'] and rows[ids['missing']]['path'] == old['missing'] and 'moved_from' not in rows[ids['bad']])
        labels = ' | '.join(f['label'] + ': ' + f['reason'] for f in st['failures'])
        check('owner sees which files could not be copied and why', len(st['failures']) == 2 and 'bad.png' in labels and 'gone.png' in labels and 'hash' in labels, labels)
        check('remaining after the copy = just the 2 that could not be copied', st['remaining_total'] == 2, st['remaining'])
        # 4. The phone sees nothing new: same bytes -> same ETag; same asset_revision (also for a file that had no saved hash).
        tags1, rev1 = await look()
        check('after the copy: every picture has the SAME ETag (read from Supabase now)', tags1 == tags0, (tags0, tags1))
        check('after the copy: asset_revision unchanged (no re-download)', rev1 == rev0, (rev0, rev1))
        sb.down = True
        S._source_cache = S.ByteCache(64 * 1024 * 1024)
        try:
            await asyncio.to_thread(render_crop, rows[ids['png']], q['q_refs'][0]); reads_sb = False
        except S.StorageWaiting:
            reads_sb = True
        check('a copied picture is really read from Supabase now', reads_sb)
        sb.down = False; S.STATE.update(down_until=0.0, strikes=0)
        from tejas.media import _render
        part = [(q['id'], 0, {'file_id': ids['png'], 'page': 1, 'rect': [0, 0, 40, 20], 'prerendered': True}, 'question'), (q['id'], 1, {'file_id': ids['missing'], 'page': 1, 'rect': [0, 0, 40, 20], 'prerendered': True}, 'question')]
        S._source_cache = S.ByteCache(64 * 1024 * 1024)
        got = await asyncio.to_thread(_render, rows, part)
        check('a picture missing everywhere is just left out of the pack (app shows its retry box), the others still come', [x[1] for x in got] == [0], [x[1] for x in got])
        # 5. A picture that really changes gets a new asset_revision.
        from PIL import Image
        out = io.BytesIO(); Image.new('RGB', (40, 20), (10, 200, 30)).save(out, 'PNG'); new_png = out.getvalue()
        H.STORE['tejas/test/a2.png'] = new_png
        await DB.tejas_files.update_one({'id': ids['png']}, {'$set': {'path': 'tejas/test/a2.png', 'sha256': sha(new_png)}, '$unset': {'moved_from': ''}})
        _, rev2 = await look()
        check('a picture that really changed: asset_revision changes', rev2 != rev0, (rev0, rev2))
        # 6. Copy again later: retries the two that failed (still failing), copies the new one.
        r = await own.post('/api/admin/storage/move/start'); await settle()
        st = J(await own.get('/api/admin/storage/move/status'))
        row = await DB.tejas_files.find_one({'id': ids['png']})
        check('second copy: the changed picture moves too, the 2 broken ones are tried again and listed again', r.status_code == 200 and st['state'] == 'done' and st['moved'] == 1 and st['failed'] == 2 and row['path'] == 'sb://test-bucket/tejas/test/a2.png',
              {k: st[k] for k in ('state', 'moved', 'failed')})
        # 7. Stop and carry on.
        H.STORE['tejas/test/late.png'] = png
        await DB.tejas_files.insert_one({'id': 'late-1', 'kind': 'rendered_png', 'path': 'tejas/test/late.png', 'sha256': sha(png), 'filename': 'late.png', 'created_at': time.time()})
        sb.down = True; S.STATE.update(down_until=0.0, strikes=0)
        await SM.begin(False); await settle()
        st = J(await own.post('/api/admin/storage/move/stop'))
        check('Roko: a waiting copy stops', st['state'] == 'stopped', st['state'])
        sb.down = False; S.STATE.update(down_until=0.0, strikes=0)
        await JOBS.wake_storage(); await settle()
        st = J(await own.get('/api/admin/storage/move/status'))
        check('a stopped copy does NOT restart by itself on a Supabase wake', st['state'] == 'stopped', st['state'])
        r = await own.post('/api/admin/storage/move/start'); await settle()
        st = J(await own.get('/api/admin/storage/move/status')); row = await DB.tejas_files.find_one({'id': 'late-1'})
        check('Copy after Roko carries on and finishes', st['state'] == 'done' and row['path'].startswith('sb://'), (st['state'], row['path']))
        # 8. One run at a time.
        await DB.tejas_files.update_one({'id': 'late-1'}, {'$set': {'path': 'tejas/test/late.png'}})
        first = await SM.begin(True); second = await SM.begin(True); await settle()
        check('only one copy runs at a time', first and second is None, (first, second))
    finally:
        for t in list(JOBS._later):
            t.cancel()
        for p in patches:
            p.stop()
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')


if __name__ == '__main__':
    asyncio.run(main())
