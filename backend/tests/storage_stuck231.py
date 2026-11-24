"""TEST-ONLY iteration 231, Pocket 2: one file's fault stays with that file. The app's own routes and the real book worker, Supabase faked at
the wire (tests/fake_supabase231.py returns chosen files with 400 while everything else is saved). Disposable DB, no network, no real keys.
P. a picture Supabase keeps returning while a mock goes Live: only that mock waits ("Atki hai"), another book goes Live meanwhile, one
   15-minute job, Dobara chalao, and the job's own clock finishes it once Supabase takes the picture.
U. publish_batch: the book's other mocks are still tried; Supabase away still stops the batch at once.
T. two mocks in one PDF with the real worker: the second goes Live while the first is stuck; each stuck mock is named.
I. an old paper import whose picture is returned: queued + stuck, not woken by "Supabase is back", woken by the scheduled check.
H. an upload inside a request: the owner is told only this file was returned.   M. the old-files copy: a returned file is listed, the rest are copied.
Run: cd /app/backend && python tests/storage_stuck231.py
"""
import asyncio, hashlib, os, sys, time, types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage_book229 import H, J, BM, DB, S, JOBS, JOBS_COL, RESULTS, check, mkstaff, upload, cut_pdf, cancel_kicks, pump, finish, again, row, job, listed  # noqa: E402
from book_publishing_iso170 import build_pdf, q3  # noqa: E402
import httpx  # noqa: E402
from tejas import structure, book_worker as BW, storage_move as SM, imports as IM  # noqa: E402
from fake_supabase231 import Picky  # noqa: E402

M = '/api/admin/master'


async def live(own, mid):
    r = await own.post(M + '/status', json={'items': [{'kind': 'book_mock', 'id': mid}], 'to': 'live'}); await pump()
    return r


async def item(own, sec, mid):
    r = J(await own.get(f'{M}/types/{sec}/mocks'))
    return next((x for x in r.get('items', []) if x['id'] == mid), {})


async def later():
    """Waits for the runs the app itself started with no delay; the long sleeping ones are left alone."""
    await asyncio.sleep(.2)
    for _ in range(200):
        if not any(not t.done() for t in JOBS._later) or await asyncio.sleep(.1):
            return


async def settle():
    while SM._tasks:
        await asyncio.gather(*list(SM._tasks))


async def until(find, ok, secs=40):
    for _ in range(int(secs / .25)):
        d = await find()
        if ok(d):
            return d
        await asyncio.sleep(.25)
    return d


async def batch(n, bad, make, payload=None):
    """One round of publish_batch over n ready mocks, batch after batch the way the worker runs them; publishing the ones in `bad` raises make().
    Returns what the round ended with, the mocks tried in order, how many were tried in each batch, and the mocks that went Live."""
    calls, sizes = [], []
    rows = [types.SimpleNamespace(id=f'm{i}', label=f'Mock {i}', chapter={}, publish_requested=True, state='ready', issues=[], published_generation=0, generation=1) for i in range(1, n + 1)]

    async def ready(book, token, source, mid):
        calls.append(mid)
        if mid in bad:
            raise make()
        next(m for m in rows if m.id == mid).published_generation = 1

    async def mocks(book):
        return rows
    book = types.SimpleNamespace(paused=False, payload=dict(payload or {}))
    keep = BW.publish_ready, BW.mocks_for
    BW.publish_ready, BW.mocks_for = ready, mocks
    try:
        more = True
        while more:
            seen = len(calls)
            try:
                more = out = await BW.publish_batch(book, 't', b'')
            except Exception as exc:  # noqa: BLE001
                more, out = False, exc
            sizes.append(len(calls) - seen)
    finally:
        BW.publish_ready, BW.mocks_for = keep
    return types.SimpleNamespace(out=out, calls=calls, sizes=sizes, live=[m.id for m in rows if m.published_generation], left='stuck_round' in book.payload)


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    sb = Picky(S.TUS_CHUNK)
    client = httpx.Client(transport=httpx.MockTransport(sb))
    S._client = lambda: client                                               # nothing leaves this process
    S.time = types.SimpleNamespace(time=time.time, sleep=lambda s: None)     # the storage code's own waits only
    S.STATE.update(down_until=0.0, strikes=0, last_error='', auth=None, bucket=None, failovers=0, last_failover=None, backup_since=None)
    try:
        own, _ = await mkstaff('owner', 'p2')
        slug = J(await own.post('/api/admin/catalog/exams', json={'name': 'SKX', 'short': 'SK', 'subjects': ['Physics'], 'color': 'rose'})).get('slug')
        sec = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Mock Tests', 'description': '', 'layout': 'list', 'kind': 'mocks'})).get('id')
        emergent = {k for k in H.STORE if not k.startswith('jeelive/health/')}

        # ---- P. One picture of one mock is returned by Supabase while the mock goes Live.
        a = (await upload(own, cut_pdf('PICA', long=True), 'TEST_picture_stuck', section_id=sec))['id']; await finish(own, a)
        mk = await BM.find_one({'book_id': a}); mid, label = mk['_id'], mk['label']
        check('P. setup: the PDF is read and its mock is ready', mk['state'] == 'ready' and (await row(a))['payload']['source_path'].startswith('sb://'), (mk['state'], mk['issues']))
        await DB.tejas_books.update_one({'_id': a}, {'$set': {'payload.rereading': True}})   # as after an automatic re-read: the worker clears the mark once the mocks are rebuilt
        sb.returned = [f'/books/{a}/crops/']
        r = await live(own, mid)
        bk, mk, jb = await row(a), await BM.find_one({'_id': mid}), await job(a)
        w = bk['payload'].get('storage_wait') or {}
        check('P. Live pressed: the mock is NOT Live, NOT held and has nothing to fix; its Live request is kept', r.status_code == 200 and mk['state'] == 'ready' and not mk['issues'] and not mk.get('publish_hold')
              and mk.get('publish_requested') and not mk.get('set_id'), (r.status_code, mk['state'], mk['issues'], mk.get('publish_hold'), mk.get('set_id')))
        check('P. the book says "Atki hai": which mock, Supabase\'s code and what happens next', bk['state'] == 'matching' and w.get('stuck') and w.get('kind') == 'stuck' and w.get('mock') == label and w.get('mock_id') == mid
              and '(400)' in w.get('reason', '') and '15 minute' in w.get('next', '') and 'Atki hai' in bk['payload'].get('message', ''), (bk['state'], w, bk['payload'].get('message')))
        check('P. its job tries again by itself in 15 minutes and kept all its tries', jb['status'] == 'queued' and jb.get('stuck') is True and jb.get('attempts', 0) == 0 and 800 <= jb['next_run_at'] - time.time() <= 901,
              ({k: jb.get(k) for k in ('status', 'stuck', 'attempts')}, jb['next_run_at'] - time.time()))
        check('P. Supabase is NOT rested for everyone', S.supabase_on() and S.STATE['strikes'] == 0, (S.STATE['down_until'] - time.time(), S.STATE['strikes']))
        check('P. the re-read that finished before the stuck picture stays finished (the mark is cleared)', 'rereading' not in bk['payload'], bk['payload'].get('rereading'))
        since = w.get('since')
        up, it = await listed(own, sec, a), await item(own, sec, mid)
        check('P. Uploads: the PDF is listed as stuck with Dobara chalao, names the mock, no longer counted as busy', up.get('state') == 'stuck' and up.get('can_retry') and up.get('active') is False
              and up.get('storage_wait', {}).get('mock') == label and up['storage_wait'].get('stuck') and up.get('message') == '', up)
        check('P. Mocks: its row carries the reason instead of "Live ho raha hai" for ever', it.get('status') == 'publishing' and '(400)' in (it.get('stuck') or {}).get('reason', ''), it)
        m = J(await own.get('/api/admin/machine/status'))
        check('P. Machine: listed under stuck files with the mock\'s name, not under waiting for Supabase', [(x['id'], x.get('mock')) for x in m.get('storage_stuck', [])] == [(a, label)]
              and not m.get('storage_waiting') and m.get('attention'), (m.get('storage_stuck'), m.get('storage_waiting')))
        await DB.tejas_books.update_one({'_id': a}, {'$set': {'payload.storage_wait': {'since': since, 'at': time.time(), 'retrying': True}}})   # as while Dobara chalao runs
        m = J(await own.get('/api/admin/machine/status'))
        check('P. Machine: a PDF whose Dobara chalao is running is not called "waiting for Supabase"', not m.get('storage_waiting') and not m.get('storage_stuck'), (m.get('storage_waiting'), m.get('storage_stuck')))
        await DB.tejas_books.update_one({'_id': a}, {'$set': {'updated_at': time.time() - 1000}})
        m = J(await own.get('/api/admin/machine/status'))
        check('P. Machine: a Dobara chalao that has not finished in 15 minutes is listed under "15 min se atki PDF" (never hidden)', [x['id'] for x in m.get('stuck', [])] == [a] and m.get('attention'), m.get('stuck'))
        await DB.tejas_books.update_one({'_id': a}, {'$set': {'payload.storage_wait': w, 'updated_at': time.time()}})
        b = (await upload(own, cut_pdf('PICB', long=True), 'TEST_next_book', section_id=sec))['id']; await finish(own, b)
        mb = await BM.find_one({'book_id': b}); await live(own, mb['_id']); mb = await BM.find_one({'book_id': b})
        check('P. another book uploaded meanwhile is read and goes Live (the queue is not blocked)', mb['state'] in ('published', 'scheduled') and mb.get('set_id'), (mb['state'], mb['issues']))
        before = (await job(a))['next_run_at']
        r = await again(own)
        check('P. "Supabase is back" does not wake the stuck mock (it keeps its 15 minutes)', r.get('woke') == 0 and (await job(a))['next_run_at'] == before, r.get('woke'))
        n = await JOBS_COL.count_documents({'kind': 'book_step', 'payload.book_id': a})
        await BW.recover()
        check('P. the 15-minute check does not add a second job for the stuck PDF', await JOBS_COL.count_documents({'kind': 'book_step', 'payload.book_id': a}) == n, n)
        cancel_kicks()
        rev = J(await own.get(f'/api/admin/books/{a}'))['revision']
        r = await own.post(f'/api/admin/books/{a}/control', json={'revision': rev, 'action': 'retry'}); await pump()
        bk, mk = await row(a), await BM.find_one({'_id': mid})
        w = bk['payload'].get('storage_wait') or {}
        waiting = await JOBS_COL.count_documents({'kind': 'book_step', 'payload.book_id': a, 'status': 'queued'})
        check('P. Dobara chalao while Supabase still returns it: stuck again, still not held, "since" kept', r.status_code == 200 and w.get('stuck') and w.get('mock') == label and w.get('since') == since
              and mk['state'] == 'ready' and not mk.get('set_id'), (r.status_code, w, mk['state']))
        check('P. ...and only ONE job keeps the 15-minute clock (the older one stepped aside)', waiting == 1, waiting)
        sb.returned = []; cancel_kicks()
        await JOBS_COL.update_one({'id': (await job(a))['id']}, {'$set': {'next_run_at': 0}})   # its 15 minutes are over
        await pump()
        bk, mk, jb = await row(a), await BM.find_one({'_id': mid}), await job(a)
        paths = [f['path'] async for f in DB.tejas_files.find({'book_import_id': a}, {'path': 1})]
        check('P. Supabase takes the picture: the mock goes Live by itself at its next try, nothing left waiting', mk['state'] in ('published', 'scheduled') and mk.get('set_id') and 'storage_wait' not in bk['payload']
              and jb['status'] == 'done' and not jb.get('stuck'), (mk['state'], mk['issues'], bk['payload'].get('storage_wait'), jb['status']))
        check('P. every picture of that paper lives in Supabase', paths and all(p.startswith('sb://') for p in paths), paths[:3])
        up, m = await listed(own, sec, a), J(await own.get('/api/admin/machine/status'))
        r = J(await own.get(f'{M}/types/{sec}/mocks'))
        check('P. the screens no longer call anything stuck', up.get('state') != 'stuck' and not m.get('storage_stuck') and not any(x.get('stuck') for x in r['items']), (up, m.get('storage_stuck')))

        # ---- T. Two mocks in one PDF, the real worker: one picture of the first is returned, the second goes Live in the same run.
        K = [(1, 'B'), (2, 'B'), (3, 'C')]
        two = (await upload(own, build_pdf([{'n': 1, 'qs': q3('T1'), 'keys': K}, {'n': 2, 'qs': q3('T2'), 'keys': K}]), 'TEST_two_mocks', section_id=sec))['id']; await finish(own, two)
        m1, m2 = [x async for x in BM.find({'book_id': two}).sort('order', 1)]
        check('T. setup: the PDF gives two ready mocks', (m1['state'], m2['state']) == ('ready', 'ready'), (m1['state'], m1['issues'], m2['state'], m2['issues']))
        sb.returned, sb.only_first = [f'/books/{two}/crops/'], 1   # exactly one picture, of the mock that is published first
        r = await own.post(M + '/status', json={'items': [{'kind': 'book_mock', 'id': m1['_id']}, {'kind': 'book_mock', 'id': m2['_id']}], 'to': 'live'}); await pump()
        bk, a1, a2 = await row(two), await BM.find_one({'_id': m1['_id']}), await BM.find_one({'_id': m2['_id']})
        w = bk['payload'].get('storage_wait') or {}
        check('T. mock 2 is Live although mock 1 of the same PDF is stuck; mock 1 keeps its Live request and is not held', r.status_code == 200 and a2['state'] in ('published', 'scheduled') and a2.get('set_id')
              and a1['state'] == 'ready' and not a1['issues'] and a1.get('publish_requested') and not a1.get('set_id'), (a1['state'], a1['issues'], a2['state'], a2['issues']))
        check('T. the book names only mock 1, with the reason; no half-finished round is left', w.get('stuck') and list(w.get('mocks') or {}) == [m1['_id']] and w.get('mock') == m1['label'] and w.get('mock_id') == m1['_id']
              and '(400)' in w['mocks'][m1['_id']]['reason'] and 'stuck_round' not in bk['payload'], (w, bk['payload'].get('stuck_round')))
        check('T. what mock 2 changed in the book is kept although the batch ended stuck (its place in the list, the first-ready time)', bk['payload'].get('catalog_base') is not None
              and (bk['payload'].get('metrics') or {}).get('first_ready_seconds') is not None, (bk['payload'].get('catalog_base'), bk['payload'].get('metrics')))
        items = J(await own.get(f'{M}/types/{sec}/mocks'))['items']
        check('T. Mocks list: only mock 1 says "Atki hai" (no stale picture count); mock 2 is Live', [(x['id'], x.get('publish_progress')) for x in items if x.get('stuck')] == [(m1['_id'], None)]
              and any(x['id'] == a2['set_id'] and x['status'] == 'live' for x in items), [(x['id'], x['status'], x.get('stuck')) for x in items])
        up = await listed(own, sec, two)
        check('T. Uploads: the PDF is stuck, names mock 1 and counts no other stuck mock', up.get('state') == 'stuck' and up['storage_wait'].get('mock') == m1['label'] and up['storage_wait'].get('more') == 0, up)
        sb.returned, sb.only_first = [], None; cancel_kicks()
        rev = J(await own.get(f'/api/admin/books/{two}'))['revision']
        r = await own.post(f'/api/admin/books/{two}/control', json={'revision': rev, 'action': 'retry'}); await pump()
        bk, a1 = await row(two), await BM.find_one({'_id': m1['_id']})
        check('T. Dobara chalao once Supabase takes the picture: mock 1 is Live too, nothing left waiting', r.status_code == 200 and a1['state'] in ('published', 'scheduled') and a1.get('set_id')
              and 'storage_wait' not in bk['payload'] and 'stuck_round' not in bk['payload'] and bk['state'] == 'published', (a1['state'], a1['issues'], bk['state'], bk['payload'].get('storage_wait')))

        # ---- U. The loop that publishes a book's mocks.
        stuck = lambda: S._wait(S.StorageStuck, 'x', 400, 'stuck', 'raw')  # noqa: E731
        away = lambda: S._wait(S.StorageWaiting, 'x', None, 'away', 'raw')  # noqa: E731
        every = [f'm{i}' for i in range(1, 8)]
        names = lambda r: [(i, v['mock']) for i, v in getattr(r.out, 'mocks', {}).items()]  # noqa: E731
        r = await batch(3, {'m2'}, stuck)
        check('U. mock 2 of 3 is stuck: mocks 1 and 3 go Live, then the book reports mock 2 with its reason', isinstance(r.out, S.StorageStuck) and names(r) == [('m2', 'Mock 2')] and '(400)' in r.out.mocks['m2']['reason']
              and r.out.code == 400 and '15 minute' in r.out.step and r.calls == ['m1', 'm2', 'm3'] and r.live == ['m1', 'm3'] and not r.left, (r.out, names(r), r.calls, r.live))
        r = await batch(3, {'m1', 'm3'}, stuck)
        check('U. two stuck mocks: every mock is tried once and BOTH stuck ones are named', isinstance(r.out, S.StorageStuck) and names(r) == [('m1', 'Mock 1'), ('m3', 'Mock 3')] and r.calls == ['m1', 'm2', 'm3'] and r.live == ['m2'], (names(r), r.calls))
        r = await batch(3, {'m2'}, away)
        check('U. Supabase away is not a stuck file: the batch stops at once and the whole book waits', isinstance(r.out, S.StorageWaiting) and r.out.scope == 'away' and r.calls == ['m1', 'm2'], (r.out, r.calls))
        r = await batch(7, {'m1'}, stuck)
        check('U. more mocks than one batch: the stuck one is tried ONCE, the other six go Live, then the book reports it', isinstance(r.out, S.StorageStuck) and names(r) == [('m1', 'Mock 1')] and r.calls == every
              and r.sizes == [BW.MOCKS_PER_STEP, 2] and r.live == every[1:] and not r.left, (r.out, r.calls, r.sizes, r.live))
        r = await batch(7, set(every[:5]), stuck)
        check('U. a whole batch of five stuck mocks does not block mocks 6 and 7: they go Live; each stuck one was tried once', isinstance(r.out, S.StorageStuck) and [i for i, _ in names(r)] == every[:5] and r.calls == every
              and r.sizes == [BW.MOCKS_PER_STEP, 2] and r.live == every[5:], (names(r), r.calls, r.sizes, r.live))
        r = await batch(3, set(), stuck)
        check('U. nothing stuck: the round ends quietly and leaves no note behind', r.out is False and r.calls == ['m1', 'm2', 'm3'] and not r.left, (r.out, r.calls, r.left))
        r = await batch(2, {'m1'}, stuck, {'stuck_round': {'since': 123.0, 'mocks': {}}})
        check('U. a mock stuck again keeps the time it first got stuck', isinstance(r.out, S.StorageStuck) and r.out.since == 123.0 and r.live == ['m2'], (r.out, getattr(r.out, 'since', None)))

        # ---- I. An old paper import: one of its pictures is returned.
        from structure_imports_iso174 import pdf_import, chapter_upload
        imports = DB.tejas_imports
        sb.returned = ['/renders/']
        r = await pdf_import(own, 'BITSAT Practice Paper', 'PS231', 'bitsat:mocks'); iid = J(r).get('id')
        rec = await until(lambda: imports.find_one({'id': iid}), lambda d: d and (d.get('stuck') or d['status'] in ('failed', 'ready', 'blocked')))
        check('I. the import is not failed: it waits as stuck with the reason and Supabase\'s code', r.status_code == 202 and rec['status'] == 'queued' and rec.get('stuck') is True and rec.get('storage_wait')
              and 'Atki hai' in rec['message'] and '(400)' in rec['message'], (r.status_code, rec and (rec['status'], rec.get('stuck'), rec.get('message'))))
        check('I. it will try again by itself, and Supabase is not rested', any(not t.done() for t in JOBS._later) and S.supabase_on())
        cancel_kicks()
        await JOBS.wake_storage(); await later()
        rec = await imports.find_one({'id': iid})
        check('I. "Supabase is back" does not run the stuck import', rec['status'] == 'queued' and rec.get('stuck') is True, (rec['status'], rec.get('stuck')))
        first = rec['lease_token']
        check('I. the scheduled check leaves a freshly stuck import to its own 15 minutes', await JOBS.wake_uploads(stuck=True) == 0)
        await imports.update_one({'id': iid}, {'$set': {'storage_wait': time.time() - 900}})   # its 15 minutes are over and its timer was lost in a restart
        woke = await JOBS.wake_uploads(stuck=True)
        rec = await until(lambda: imports.find_one({'id': iid}), lambda d: d['status'] == 'queued' and d.get('stuck') and d['lease_token'] != first)
        check('I. after its 15 minutes the scheduled check tries it again; still returned, so it is stuck again', woke == 1 and rec['status'] == 'queued' and rec.get('stuck') is True and rec['lease_token'] != first,
              (woke, rec['status'], rec.get('stuck')))
        cancel_kicks()
        await IM.stuck_again(iid, first)
        same = await imports.find_one({'id': iid})
        check('I. the older try\'s timer does nothing: one stuck import keeps ONE 15-minute clock', same['status'] == 'queued' and same['lease_token'] == rec['lease_token'] and same['storage_waits'] == rec['storage_waits'],
              (same['status'], same['storage_waits'], rec['storage_waits']))
        sb.returned = []
        await IM.stuck_again(iid, rec['lease_token'])
        rec = await imports.find_one({'id': iid})
        check('I. its own timer runs it: Supabase takes the picture, the import is ready, nothing left waiting', rec['status'] == 'ready' and 'stuck' not in rec and 'storage_wait' not in rec,
              (rec['status'], rec.get('message'), rec.get('stuck')))

        # ---- H. A file sent inside the owner's own request.
        sb.returned = ['chapter-books/']
        r = await chapter_upload(own, 'bitsat:chapters')
        check('H. only this file returned: the owner is told so, with the code; nothing is half-saved', r.status_code == 503 and 'Yeh file Supabase mein save nahi hui' in r.text and '(400)' in r.text
              and 'Supabase abhi file nahi le raha' not in r.text and not await DB.tejas_chapter_books.count_documents({}) and S.supabase_on(), (r.status_code, r.text[:300]))
        sb.returned = []; sb.down = True
        r = await chapter_upload(own, 'bitsat:chapters')
        check('H. Supabase away: the old words stay', r.status_code == 503 and 'Supabase abhi file nahi le raha' in r.text and not S.supabase_on(), (r.status_code, r.text[:300]))
        sb.down = False; S.STATE.update(down_until=0.0, strikes=0)
        check('nothing at all went to Emergent storage', {k for k in H.STORE if not k.startswith('jeelive/health/')} == emergent)

        # ---- M. Old Emergent files copied into Supabase: a returned file is listed, the others are copied.
        old = {'ok.png': os.urandom(40_000), 'b_returned.png': os.urandom(41_000), 'c.pdf': cut_pdf('MV231'), 'big_returned.pdf': os.urandom(7 * 1024 * 1024 + 5)}
        for i, (name, raw) in enumerate(old.items()):
            H.STORE['tejas/t231/' + name] = raw
            await DB.tejas_files.insert_one({'id': 'T231-' + name, 'kind': 'combined', 'path': 'tejas/t231/' + name, 'sha256': hashlib.sha256(raw).hexdigest(), 'filename': name, 'created_at': time.time() + i})
        sb.returned = ['_returned']; starts = sb.starts()
        await SM.begin(True); await settle()
        st = J(await own.get('/api/admin/storage/move/status'))
        docs = {d['filename']: d['path'] async for d in DB.tejas_files.find({'id': {'$regex': '^T231-'}})}
        check('M. the copy is NOT left waiting for one file: it finishes, 2 copied, 2 listed', st['state'] == 'done' and st['moved'] == 2 and st['failed'] == 2, {k: st[k] for k in ('state', 'moved', 'failed', 'skipped')})
        check('M. each listed file says why, with Supabase\'s code and no path', len(st['failures']) == 2 and all('Supabase ne yeh file nahi li' in f['reason'] and '(400)' in f['reason'] for f in st['failures'])
              and 'tejas/' not in str(st['failures']), st['failures'])
        check('M. the good files switched to Supabase, the returned ones stay on Emergent', docs['ok.png'].startswith('sb://') and docs['c.pdf'].startswith('sb://')
              and docs['b_returned.png'] == 'tejas/t231/b_returned.png' and docs['big_returned.pdf'] == 'tejas/t231/big_returned.pdf', docs)
        check('M. the big file was tried on both routes before it was listed (a fresh upload, then one request)', sb.starts() - starts == 2 and sb.count('POST', '/big_returned.pdf') == 2, (sb.starts() - starts, sb.count('POST', '/big_returned.pdf')))
        check('M. Supabase is NOT rested', S.supabase_on() and S.STATE['strikes'] == 0, S.STATE['strikes'])
        sb.returned = []
        r = await own.post('/api/admin/storage/move/start'); await settle()
        st = J(await own.get('/api/admin/storage/move/status'))
        check('M. Copy again once Supabase takes them: both are copied byte for byte, nothing left on Emergent', r.status_code == 200 and st['state'] == 'done' and st['moved'] == 2 and st['failed'] == 0 and st['remaining_total'] == 0
              and all(sb.objects.get(S.bucket_name() + '/tejas/t231/' + k) == old[k] for k in old), {k: st[k] for k in ('state', 'moved', 'failed', 'remaining_total')})
    finally:
        cancel_kicks()
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')


if __name__ == '__main__':
    asyncio.run(main())
