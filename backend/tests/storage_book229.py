"""TEST-ONLY iteration 229, Pocket 1 end to end: the app's own upload routes and the real book worker, Supabase faked at the wire
(tests/fake_supabase229.py answers the way real Supabase was seen to answer). Disposable DB, no network, no real keys.
A. the live fault exactly as the deployer's report shows the book and its job; B. another file at the path; C. the piece route
broken while pictures still go; D. both big-file routes broken: only that PDF stops ("Atki hai") and another book carries on.
Run: cd /app/backend && python tests/storage_book229.py
"""
import asyncio, os, sys, time, types, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cut_bridge207 import H, J, BM, DB, mkstaff, upload, cut_pdf  # noqa: E402
import fitz, httpx  # noqa: E402
from tejas import structure, jobs as JOBS  # noqa: E402
import tejas_storage as S  # noqa: E402
from fake_supabase229 import FakeSupabase  # noqa: E402

os.environ.update(SUPABASE_URL='https://abcdefghijklmnopqrst.supabase.co', SUPABASE_SECRET_KEY='sb_secret_test')
RESULTS = []
JOBS_COL = H.TDB.tejas_jobs


def check(name, ok, detail=''):
    RESULTS.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:500]), flush=True)


def big_pdf(tag, mb=7):
    """A real, readable paper made heavier than 6 MB, so its original takes the big-file route."""
    doc = fitz.open(stream=cut_pdf(tag, long=True), filetype='pdf')
    doc.embfile_add('pad.bin', os.urandom(mb * 1024 * 1024))
    raw = doc.tobytes(); doc.close()
    return raw


def key_of(bid):
    return f'{S.bucket_name()}/jeelive/books/{bid}/original.pdf'


def cancel_kicks():
    for t in list(JOBS._later):
        t.cancel()


async def pump(seconds=100):
    """Runs every book job that is due now, the way the app's own lane does, and waits until the lane is quiet."""
    stop = time.time() + seconds
    while time.time() < stop:
        await JOBS.drain_lane('book_step')
        busy = JOBS._continuing or JOBS._active['book_step'] or 'book_step' in JOBS._draining
        due = await JOBS_COL.find_one({'kind': 'book_step', 'status': 'queued', '$or': [{'next_run_at': {'$lte': time.time()}}, {'next_run_at': {'$exists': False}}]}, {'_id': 1})
        if not busy and not due:
            return
        await asyncio.sleep(.05)
    raise AssertionError('book jobs did not settle')


async def finish(own, bid):
    r = await own.post(f'/api/admin/books/{bid}/complete'); await pump()
    return r


async def again(own):
    """The owner's "Abhi phir try karo": Supabase is checked now and every job that waits for it runs."""
    cancel_kicks()
    r = J(await own.post('/api/admin/storage/retry')); await pump()
    return r


async def row(bid):
    return await DB.tejas_books.find_one({'_id': bid})


async def job(bid):
    return await JOBS_COL.find_one({'kind': 'book_step', 'payload.book_id': bid}, sort=[('created_at', -1)])


async def listed(own, sec, bid):
    r = J(await own.get(f'/api/admin/master/types/{sec}/mocks'))
    return next((u for u in r.get('uploads', []) if u['id'] == bid), {})


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    sb = FakeSupabase(S.TUS_CHUNK)
    client = httpx.Client(transport=httpx.MockTransport(sb))
    S._client = lambda: client                                               # nothing leaves this process
    S.time = types.SimpleNamespace(time=time.time, sleep=lambda s: None)     # the storage code's own waits only
    S.STATE.update(down_until=0.0, strikes=0, last_error='', auth=None, bucket=None, failovers=0, last_failover=None, backup_since=None)
    try:
        own, owner_id = await mkstaff('owner', 'p1')
        slug = J(await own.post('/api/admin/catalog/exams', json={'name': 'PKX', 'short': 'PK', 'subjects': ['Physics'], 'color': 'rose'})).get('slug')
        sec = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Mock Tests', 'description': '', 'layout': 'list', 'kind': 'mocks'})).get('id')
        emergent = {k for k in H.STORE if not k.startswith('jeelive/health/')}

        # ---- A. The live fault, exactly: the same PDF is already in Supabase at that path (saved earlier, its record deleted),
        # the book has waited for hours at 0 % on a dead half upload and its job has waited 85 times.
        raw = big_pdf('LIVE')
        b = await upload(own, raw, 'TEST_mathematics_chapterwise', section_id=sec); bid = b['id']
        path = f'jeelive/books/{bid}/original.pdf'
        sb.objects[key_of(bid)] = raw
        dead = uuid.uuid4().hex
        sb.uploads[dead] = {'len': len(raw), 'key': key_of(bid), 'data': b'', 'done': False}
        t = time.time()
        await DB.tejas_books.update_one({'_id': bid}, {'$set': {
            'state': 'received', 'revision': 1, 'payload.message': 'Supabase ka intezaar. File surakshit hai; Supabase lautte hi yahin se aage chalega.',
            'payload.transfer': {'url': f'https://abcdefghijklmnopqrst.storage.supabase.co/storage/v1/upload/resumable/{dead}', 'path': path, 'size': len(raw), 'sent': 0, 'started': t - 7 * 3600},
            'payload.storage_wait': {'since': t - 7 * 3600, 'at': t - 60, 'error': f'Supabase abhi file nahi le raha. Wajah: Supabase big-file upload stopped at 0 of {len(raw)} bytes (409).'}}})
        await JOBS_COL.insert_one({'id': f'book_step-{bid}:1', 'kind': 'book_step', 'user_id': owner_id, 'set_id': bid, 'payload': {'key': f'{bid}:1', 'book_id': bid},
                                   'status': 'queued', 'progress': 0, 'created_at': t - 7 * 3600, 'lease_until': 0, 'attempts': 0, 'storage_waits': 85, 'next_run_at': t + 250,
                                   'error': 'Waiting for file storage; it carries on by itself.'})
        up = await listed(own, sec, bid)
        check('A. before: the screen shows what live shows (0 % in Supabase, waiting)', up.get('transfer', {}).get('sent') == 0 and up.get('storage_wait', {}).get('since') and up.get('state') == 'received', up)
        parts = await DB.tejas_book_parts.count_documents({'book_id': bid})
        r = await again(own)
        bk, jb, mk = await row(bid), await job(bid), await BM.find_one({'book_id': bid})
        check('A. one check of Supabase wakes the book that waited 85 times', r.get('woke', 0) >= 1 and jb['status'] == 'done', (r.get('mode'), r.get('woke'), jb['status'], jb.get('error')))
        check('A. the same PDF is recognised in Supabase: not one piece is sent, no new upload is started', sb.pieces() == 0 and sb.starts() == 0, (sb.pieces(), sb.starts()))
        check('A. the book has its original in Supabase; wait and old place are gone; parts removed', bk['payload'].get('source_path') == 'sb://' + key_of(bid) and 'storage_wait' not in bk['payload']
              and 'transfer' not in bk['payload'] and parts > 0 and not await DB.tejas_book_parts.count_documents({'book_id': bid}), {k: bk['payload'].get(k) for k in ('source_path', 'storage_wait', 'transfer')})
        check('A. the book is read and its mock is ready', bk['state'] in ('ready', 'attention_needed') and mk and mk['state'] == 'ready', (bk['state'], mk and (mk['state'], mk['issues'])))
        m = J(await own.get('/api/admin/machine/status'))
        check('A. Machine: nothing waits for Supabase any more', not m.get('storage_waiting') and not m.get('storage_stuck'), (m.get('storage_waiting'), m.get('storage_stuck')))

        # ---- B. Another file sits at the path (a different size and different bytes): the new PDF replaces it.
        raw = big_pdf('OTHER'); n = sb.pieces()
        b = await upload(own, raw, 'TEST_other_at_path', section_id=sec); bid = b['id']
        sb.objects[key_of(bid)] = os.urandom(6 * 1024 * 1024 + 99)
        r = await finish(own, bid)
        bk, mk = await row(bid), await BM.find_one({'book_id': bid})
        check('B. another file at the path: replaced by the new PDF byte for byte, each piece sent once', r.status_code == 200 and sb.objects[key_of(bid)] == raw and sb.pieces() - n == 2, (r.status_code, sb.pieces() - n))
        check('B. the book is read, nothing waited', mk and mk['state'] == 'ready' and 'storage_wait' not in bk['payload'], (bk['state'], bk['payload'].get('storage_wait')))

        # ---- C. The piece route is broken while small files (pictures) still go: two tries, then the same PDF in one request.
        raw = big_pdf('ROUTE'); sb.tus_down = True; starts = sb.starts()
        b = await upload(own, raw, 'TEST_piece_route', section_id=sec); bid = b['id']
        await finish(own, bid)
        bk, jb = await row(bid), await job(bid)
        place = bk['payload'].get('transfer') or {}
        check('C. try 1: the book waits (not failed); its place and one stall are saved', bk['state'] == 'received' and bk['payload'].get('storage_wait') and place.get('stalls') == 1 and place.get('url')
              and jb['status'] == 'queued' and jb.get('attempts', 0) == 0, (bk['state'], place, jb['status']))
        await again(own)
        bk, mk = await row(bid), await BM.find_one({'book_id': bid})
        check('C. try 2: the PDF goes in ONE request, is saved exactly and the book is read', sb.objects.get(key_of(bid)) == raw and sb.count('POST', f'/jeelive/books/{bid}/original.pdf') == 1
              and mk and mk['state'] == 'ready' and 'storage_wait' not in bk['payload'] and 'transfer' not in bk['payload'], (bk['state'], bk['payload'].get('storage_wait'), mk and mk['state']))
        check('C. the half upload was tried once more before the second route (no new upload started)', sb.starts() - starts == 1, sb.starts() - starts)

        # ---- D. Both big-file routes are broken for this PDF: after three tries only this PDF stops; another book carries on.
        raw = big_pdf('STUCK'); sb.one_request_code = 500; starts = sb.starts()
        b = await upload(own, raw, 'TEST_stuck_alone', section_id=sec); bid = b['id']
        await finish(own, bid)
        await again(own)
        bk = await row(bid)
        check('D. tries 1 and 2: the book waits, two stalls saved, it is not called stuck yet', bk['state'] == 'received' and (bk['payload'].get('transfer') or {}).get('stalls') == 2
              and not bk['payload']['storage_wait'].get('stuck'), (bk['state'], bk['payload'].get('transfer'), bk['payload'].get('storage_wait')))
        await again(own)
        bk, jb = await row(bid), await job(bid)
        w = bk['payload'].get('storage_wait') or {}
        check('D. try 3: only this PDF is stuck; it says why with Supabase\'s code and what happens next', bk['state'] == 'received' and w.get('stuck') and w.get('kind') == 'stuck' and '(500)' in w.get('reason', '')
              and '15 minute' in w.get('next', '') and sb.starts() - starts == 2, (bk['state'], w, sb.starts() - starts))
        check('D. its job tries again by itself in 15 minutes and kept all its tries', jb['status'] == 'queued' and jb.get('stuck') is True and jb.get('attempts', 0) == 0 and 800 <= jb['next_run_at'] - time.time() <= 901,
              ({k: jb.get(k) for k in ('status', 'stuck', 'attempts')}, jb['next_run_at'] - time.time()))
        check('D. Supabase is NOT rested for everyone', S.supabase_on(), S.STATE['down_until'] - time.time())
        small = cut_pdf('NEXT', long=True)
        b2 = await upload(own, small, 'TEST_next_book', section_id=sec)
        await finish(own, b2['id'])
        bk2, mk2 = await row(b2['id']), await BM.find_one({'book_id': b2['id']})
        check('D. another book uploaded meanwhile is saved and read (the queue is not blocked)', bk2['payload'].get('source_path', '').startswith('sb://') and mk2 and mk2['state'] == 'ready', (bk2['state'], bk2['payload'].get('storage_wait')))
        up = await listed(own, sec, bid)
        check('D. the list shows it as stuck with Dobara chalao; it is no longer counted as busy', up.get('state') == 'stuck' and up.get('can_retry') and up.get('active') is False and up.get('storage_wait', {}).get('stuck'), up)
        m = J(await own.get('/api/admin/machine/status'))
        check('D. Machine: listed under stuck files, not under waiting for Supabase', [x['id'] for x in m.get('storage_stuck', [])] == [bid] and not m.get('storage_waiting') and m.get('attention'), (m.get('storage_stuck'), m.get('storage_waiting')))
        before = (await job(bid))['next_run_at']
        r = await again(own)
        check('D. "Supabase is back" does not wake the stuck PDF (it keeps its 15 minutes)', r.get('woke') == 0 and (await job(bid))['next_run_at'] == before and (await row(bid))['payload']['storage_wait'].get('stuck'), r.get('woke'))
        sb.tus_down = False; sb.one_request_code = None; cancel_kicks()
        rev = J(await own.get(f'/api/admin/books/{bid}'))['revision']
        r = await own.post(f'/api/admin/books/{bid}/control', json={'revision': rev, 'action': 'retry'}); await pump()
        bk, mk = await row(bid), await BM.find_one({'book_id': bid})
        check('D. route back + Dobara chalao: saved exactly, read, nothing left waiting', r.status_code == 200 and sb.objects.get(key_of(bid)) == raw and mk and mk['state'] == 'ready'
              and 'storage_wait' not in bk['payload'] and 'transfer' not in bk['payload'], (r.status_code, r.text[:160], bk['state'], bk['payload'].get('storage_wait')))
        up = await listed(own, sec, bid)
        check('D. the list no longer calls it stuck', up.get('state') != 'stuck' and not up.get('storage_wait'), up)
        check('nothing at all went to Emergent storage', {k for k in H.STORE if not k.startswith('jeelive/health/')} == emergent)
    finally:
        cancel_kicks()
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')


if __name__ == '__main__':
    asyncio.run(main())
