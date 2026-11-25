"""TEST-ONLY iteration 233, packet B: a PDF step that goes silent is let go and the PDF lane carries on.
The app's own routes and the real book worker; Supabase faked at the wire (tests/fake_supabase229.py). Disposable DB, no network.
The 10 minutes are shortened to 1.2 s here (tejas.step_guard.SILENCE); nothing else in the guard is changed.
A. a step silent on a wait that can be cancelled (as on 24 Nov, inside the Live step): written down, lock freed, job runs again.
B. a step silent on a worker thread that does not answer: let go; the thread ends by itself later and changes nothing.
B2. a step that cannot be cancelled at all: left behind, its lock taken away, it can save nothing later.
C. three silent steps in a row: only that PDF says "Atki hai"; hourly try; Dobara chalao.
D. a slow step that keeps showing signs of life is never let go.
Run: cd /app/backend && python tests/step_guard233.py
"""
import asyncio, sys, threading, time, types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage_book229 import H, J, BM, DB, S, JOBS, JOBS_COL, RESULTS, check, mkstaff, upload, cut_pdf, cancel_kicks, pump, finish, row, job, listed  # noqa: E402
import fitz, httpx  # noqa: E402
from starlette.concurrency import run_in_threadpool  # noqa: E402
from tejas import structure, book_worker as BW, book_publish as BP, step_guard as G, book_pdf as PDF  # noqa: E402
from fake_supabase229 import FakeSupabase  # noqa: E402

M = '/api/admin/master'
HANGS = DB.tejas_step_hangs


async def live(own, mid):
    r = await own.post(M + '/status', json={'items': [{'kind': 'book_mock', 'id': mid}], 'to': 'live'}); await pump()
    return r


async def due(bid):
    """The job's own wait is over: it runs now."""
    await JOBS_COL.update_one({'id': (await job(bid))['id']}, {'$set': {'next_run_at': 0}}); await pump()


async def item(own, sec, mid):
    r = J(await own.get(f'{M}/types/{sec}/mocks'))
    return next((x for x in r.get('items', []) if x['id'] == mid), {})


def long_pdf(tag, pages=100):
    """A readable paper followed by plain pages: 100 pages are read as one batch of 10 groups."""
    doc = fitz.open(stream=cut_pdf(tag, long=True), filetype='pdf')
    while doc.page_count < pages:
        doc.new_page().insert_text((40, 60), f'{tag} padhne ka page {doc.page_count}', fontsize=11)
    raw = doc.tobytes(); doc.close()
    return raw


async def shape(bid):
    bk = await row(bid)
    return (bk['revision'], bk['state'], bk['updated_at'], await DB.tejas_book_pages.count_documents({'book_id': bid}), 'lock_token' in bk)


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    sb = FakeSupabase(S.TUS_CHUNK)
    client = httpx.Client(transport=httpx.MockTransport(sb))
    S._client = lambda: client
    S.time = types.SimpleNamespace(time=time.time, sleep=lambda s: None)
    S.STATE.update(down_until=0.0, strikes=0, last_error='', auth=None, bucket=None, failovers=0, last_failover=None, backup_since=None)
    keep = (G.SILENCE, G.CHECK, G.LET_GO, G.DB_WAIT, BP.source_questions, BW.extract, BP.crop_ref)
    G.SILENCE, G.CHECK, G.LET_GO, G.DB_WAIT = 1.2, .2, 1.0, 5
    silent, blocked, gate, deaf_gate = set(), [], threading.Event(), threading.Event()
    real_questions, real_extract, real_crop, real_run = BP.source_questions, BW.extract, BP.crop_ref, PDF.run
    mute = {'on': False}   # True: the page reader gets no way to show a sign of life (the code as it was before the fix)

    async def silent_source_questions(book, mock, raw, guard=None, strict=True):
        if book.id in silent:
            await asyncio.sleep(3600)
        return await real_questions(book, mock, raw, guard, strict)

    async def blocked_extract(source, numbers, alive=None):
        how = blocked.pop() if blocked else None
        if how == 'thread':
            await run_in_threadpool(gate.wait, 60)   # a worker thread that does not answer
        while how == 'deaf' and not deaf_gate.is_set():
            try:
                await asyncio.sleep(.05)
            except asyncio.CancelledError:
                pass                                  # a wait that cannot be cancelled
        return await real_extract(source, numbers, None if mute['on'] else alive)
    BP.source_questions, BW.extract = silent_source_questions, blocked_extract
    try:
        own, _ = await mkstaff('owner', 'guard233')
        slug = J(await own.post('/api/admin/catalog/exams', json={'name': 'GRD', 'short': 'GD', 'subjects': ['Physics'], 'color': 'rose'})).get('slug')
        sec = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Mock Tests', 'description': '', 'layout': 'list', 'kind': 'mocks'})).get('id')

        # ---- A. Silent inside the Live step (a wait that can be cancelled).
        a = (await upload(own, cut_pdf('HGA', long=True), 'TEST_hang_a', section_id=sec))['id']; await finish(own, a)
        mk = await BM.find_one({'book_id': a}); mid = mk['_id']
        check('A. setup: the PDF is read and its mock is ready', mk['state'] == 'ready', (mk['state'], mk['issues']))
        silent.add(a)
        t0 = time.time(); r = await live(own, mid); took = time.time() - t0
        bk, mk, jb, h = await row(a), await BM.find_one({'_id': mid}), await job(a), await HANGS.find_one({'book_id': a})
        check('A. the silent step was let go by itself (well under the test limit)', r.status_code == 200 and took < 12 and h is not None, (r.status_code, took))
        check('A. where it stood is written down: the Live step, the last sign of life, the stack', h and 'publish_ready' in h['where'] and 'silent_source_questions' in h['where']
              and h['last_beat'] and 'the silent step' in h['stack'] and h['freed'] is True and h['count'] == 1, {k: (h or {}).get(k) for k in ('where', 'last_beat', 'freed', 'count')})
        check('A. its lock is free and the PDF says what happened (1/3)', 'lock_token' not in bk and bk['payload'].get('hang', {}).get('count') == 1 and '(1/3)' in bk['payload']['message']
              and 'storage_wait' not in bk['payload'], (bk.get('lock_token'), bk['payload'].get('hang'), bk['payload'].get('message')))
        check('A. its job kept all its tries and runs again in about 20 s', jb['status'] == 'queued' and jb.get('attempts', 0) == 0 and not jb.get('stuck') and 5 < jb['next_run_at'] - time.time() <= 21,
              ({k: jb.get(k) for k in ('status', 'attempts', 'stuck')}, jb['next_run_at'] - time.time()))
        check('A. the mock is untouched: still ready, its Live request kept, nothing half-made for students', mk['state'] == 'ready' and mk.get('publish_requested') and not mk.get('set_id')
              and not await DB.tejas_sets.find_one({'book_import_id': a, 'status': 'published'}), (mk['state'], mk.get('set_id')))
        check('A. no leftover picture count ("0 of 21") for that mock', not await DB.tejas_publish_progress.find_one({'_id': mid}))
        b = (await upload(own, cut_pdf('HGB', long=True), 'TEST_next_b', section_id=sec))['id']; await finish(own, b)
        mb = await BM.find_one({'book_id': b}); await live(own, mb['_id']); mb = await BM.find_one({'book_id': b})
        check('A. the next PDF on this server is read and goes Live (the lane is not blocked)', mb['state'] in ('published', 'scheduled') and mb.get('set_id'), (mb['state'], mb['issues']))
        m = J(await own.get('/api/admin/machine/status'))
        check('A. Machine: "Latke kadam (24 ghante)" counts it and names the last one; nothing is called Atki yet', m.get('step_hangs', {}).get('day') == 1 and 'publish_ready' in (m['step_hangs'].get('last') or {}).get('where', '')
              and m.get('hung_books') == [] and not m.get('storage_stuck'), (m.get('step_hangs'), m.get('hung_books')))
        silent.discard(a); cancel_kicks(); await due(a)
        bk, mk, jb = await row(a), await BM.find_one({'_id': mid}), await job(a)
        check('A. next try (nothing silent now): the mock goes Live from the saved place; the count of silent steps is gone', mk['state'] in ('published', 'scheduled') and mk.get('set_id')
              and 'hang' not in bk['payload'] and 'storage_wait' not in bk['payload'] and jb['status'] == 'done', (mk['state'], mk['issues'], bk['payload'].get('hang'), jb['status']))

        # ---- B. Silent on a worker thread that does not answer (while the pages are read).
        c = (await upload(own, cut_pdf('HGC', long=True), 'TEST_hang_c', section_id=sec))['id']
        blocked.append('thread')
        await finish(own, c)
        bk, jb, h = await row(c), await job(c), await HANGS.find_one({'book_id': c})
        check('B. a step waiting on a thread that does not answer is let go and written down, with every thread\'s stack', h is not None and h['freed'] is True and 'read_batch' in h['where']
              and 'blocked_extract' in h['where'] and '--- thread' in h['stack'], {k: (h or {}).get(k) for k in ('where', 'freed')})
        check('B. its lock is free, its job waits to run again and the lane is free', 'lock_token' not in bk and jb['status'] == 'queued' and not JOBS._active['book_step'], (bk.get('lock_token'), jb['status'], JOBS._active))
        cancel_kicks(); await due(c)
        bk = await row(c); mk = await BM.find_one({'book_id': c})
        check('B. the next try reads the PDF fully while that thread still hangs', mk and mk['state'] == 'ready' and bk['payload']['read_pages'] == bk['payload']['pages'] and not gate.is_set(),
              (mk and mk['state'], bk['payload'].get('read_pages')))
        before = await shape(c)
        gate.set(); await asyncio.sleep(.6)
        check('B. the thread answers at last: nothing changes in the PDF', await shape(c) == before, (before, await shape(c)))

        # ---- B2. A step that cannot be cancelled at all.
        g = (await upload(own, cut_pdf('HGG', long=True), 'TEST_hang_g', section_id=sec))['id']
        blocked.append('deaf')
        await finish(own, g)
        bk, jb, h = await row(g), await job(g), await HANGS.find_one({'book_id': g})
        check('B2. a step that ignores being cancelled is left behind and written down', h is not None and h['freed'] is False and 'read_batch' in h['where'] and len(G._left) == 1,
              ({k: (h or {}).get(k) for k in ('where', 'freed')}, len(G._left)))
        check('B2. its lock was taken away, its job waits to run again and the lane is free', 'lock_token' not in bk and jb['status'] == 'queued' and not JOBS._active['book_step'], (bk.get('lock_token'), jb['status'], JOBS._active))
        cancel_kicks(); await due(g)
        bk = await row(g); mk = await BM.find_one({'book_id': g})
        check('B2. the next try reads the PDF fully while the old step still hangs', mk and mk['state'] == 'ready' and bk['payload']['read_pages'] == bk['payload']['pages'] and len(G._left) == 1,
              (mk and mk['state'], bk['payload'].get('read_pages'), len(G._left)))
        before = await shape(g)
        deaf_gate.set()
        for _ in range(100):
            if not G._left:
                break
            await asyncio.sleep(.1)
        check('B2. the old step wakes up at last: it saves NOTHING (its lock is gone)', not G._left and await shape(g) == before and before[4] is False, (len(G._left), before, await shape(g)))

        # ---- C. Three silent steps in a row: only this PDF stops ("Atki hai").
        d = (await upload(own, cut_pdf('HGD', long=True), 'TEST_hang_d', section_id=sec))['id']; await finish(own, d)
        mk = await BM.find_one({'book_id': d}); mid = mk['_id']
        silent.add(d)
        await live(own, mid)
        for _ in range(2):
            cancel_kicks(); await due(d)
        bk, jb = await row(d), await job(d)
        w = bk['payload'].get('storage_wait') or {}
        check('C. third silent step in a row: the PDF says "Atki hai" with the reason and what happens next', w.get('stuck') and w.get('kind') == 'hang' and '3 baar' in w.get('reason', '')
              and 'Dobara chalao' in w.get('next', '') and bk['payload']['hang']['count'] == 3 and w.get('since') == bk['payload']['hang']['since'] and 'Atki hai' in bk['payload']['message'], (w, bk['payload'].get('hang')))
        check('C. its job is tried again in an hour, kept its tries, and is marked stuck', jb['status'] == 'queued' and jb.get('stuck') is True and jb.get('attempts', 0) == 0 and 3500 <= jb['next_run_at'] - time.time() <= 3601,
              ({k: jb.get(k) for k in ('status', 'stuck', 'attempts')}, jb['next_run_at'] - time.time()))
        up, it, m = await listed(own, sec, d), await item(own, sec, mid), J(await own.get('/api/admin/machine/status'))
        check('C. Uploads: listed as stuck with Dobara chalao; not counted as busy', up.get('state') == 'stuck' and up.get('can_retry') and up.get('active') is False and up.get('storage_wait', {}).get('kind') == 'hang'
              and '3 baar' in up['storage_wait'].get('reason', ''), up)
        check('C. Mocks: its row says Atki hai (kind hang), not "Live ho raha hai" for ever', it.get('status') == 'publishing' and (it.get('stuck') or {}).get('kind') == 'hang' and it.get('publish_progress') is None, it)
        check('C. Machine: listed under hung PDFs (not under the Supabase lists), asks for attention, counts 6 silent steps today', [x['id'] for x in m.get('hung_books', [])] == [d] and not m.get('storage_stuck')
              and not m.get('storage_waiting') and m.get('attention') and m['step_hangs']['day'] == 6, (m.get('hung_books'), m.get('storage_stuck'), m.get('step_hangs')))
        before = jb['next_run_at']; n = await JOBS_COL.count_documents({'kind': 'book_step', 'payload.book_id': d})
        await JOBS.wake_storage(); await BW.recover()
        check('C. "Supabase is back" and the 15-minute check neither wake it early nor add a second job', (await job(d))['next_run_at'] == before
              and await JOBS_COL.count_documents({'kind': 'book_step', 'payload.book_id': d}) == n, ((await job(d))['next_run_at'], before))
        e = (await upload(own, cut_pdf('HGE', long=True), 'TEST_next_e', section_id=sec))['id']; await finish(own, e)
        me = await BM.find_one({'book_id': e}); await live(own, me['_id']); me = await BM.find_one({'book_id': e})
        check('C. another PDF uploaded meanwhile goes Live', me['state'] in ('published', 'scheduled') and me.get('set_id'), (me['state'], me['issues']))
        silent.discard(d); cancel_kicks()
        rev = J(await own.get(f'/api/admin/books/{d}'))['revision']
        r = await own.post(f'/api/admin/books/{d}/control', json={'revision': rev, 'action': 'retry'}); await pump()
        bk, mk = await row(d), await BM.find_one({'_id': mid})
        check('C. Dobara chalao (nothing silent now): the mock goes Live; no stuck mark, no count left', r.status_code == 200 and mk['state'] in ('published', 'scheduled') and mk.get('set_id')
              and 'storage_wait' not in bk['payload'] and 'hang' not in bk['payload'], (r.status_code, mk['state'], bk['payload'].get('storage_wait'), bk['payload'].get('hang')))
        up, m = await listed(own, sec, d), J(await own.get('/api/admin/machine/status'))
        check('C. the screens no longer call it stuck', up.get('state') != 'stuck' and m.get('hung_books') == [], (up.get('state'), m.get('hung_books')))

        # ---- D. Slow but alive: every picture takes a while, far longer in total than the silence limit.
        f = (await upload(own, cut_pdf('HGF', long=True), 'TEST_slow_f', section_id=sec))['id']; await finish(own, f)
        mk = await BM.find_one({'book_id': f}); saved = []

        async def slow_crop(book, mock, crop, region, role):
            await asyncio.sleep(.6); saved.append(1)
            return await real_crop(book, mock, crop, region, role)
        BP.crop_ref = slow_crop
        t0 = time.time(); await live(own, mk['_id']); took = time.time() - t0
        mk = await BM.find_one({'book_id': f})
        check('D. a slow step that keeps saving pictures is NOT let go (it ran longer than the silence limit)', mk['state'] in ('published', 'scheduled') and took > G.SILENCE and len(saved) > 8
              and not await HANGS.find_one({'book_id': f}) and 'hang' not in (await row(f))['payload'], (mk['state'], took, len(saved)))
        check('D. nothing is watched once the steps are over', not G._watched and not G._left, (G._watched, len(G._left)))

        # ---- E. One long batch of pages (100 pages = 10 groups, each made slow). Found by the code review: the batch gave no sign of life.
        calls = []; PDF.run = lambda source, g: [{'n': i['n']} for i in g]
        out = PDF.inspect_many('x', [{'n': i} for i in range(45)], 10, lambda: calls.append(1)); single = PDF.inspect_many('x', [{'n': 1}], 10, lambda: calls.append(1))
        check('E. the page reader gives one sign of life after every finished group, and the results stay in order', [r['n'] for r in out] == list(range(45)) and len(calls) == 6 and single == [{'n': 1}], (len(calls), out[:3]))
        slow, busy, lock = {'on': True, 'drop': False}, {'n': 0}, threading.Lock()

        def slow_run(source, items):
            if not (slow['on'] and items and items[0].get('action') == 'text'):
                return real_run(source, items)
            with lock:
                busy['n'] += 1
            try:
                if slow['drop']:
                    raise ValueError('TEST: dropped')
                time.sleep(.6)
                return real_run(source, items)
            finally:
                with lock:
                    busy['n'] -= 1
        PDF.run = slow_run; G.SILENCE = 2.5
        e = (await upload(own, long_pdf('HGE'), 'TEST_long_read', section_id=sec))['id']
        mute['on'] = True; await finish(own, e)
        h, bk = await HANGS.find_one({'book_id': e}), await row(e)
        check('E. control: that long batch with NO sign of life is let go (so the next check means something)', h is not None and 'read_batch' in h['where'] and bk['payload'].get('read_pages', 0) == 0,
              ((h or {}).get('where'), bk['payload'].get('read_pages')))
        slow['drop'] = True; idle = 0   # the groups left behind by the control end at once, so they do not slow the real try
        for _ in range(150):
            idle = idle + 1 if not busy['n'] else 0
            if idle >= 4:
                break
            await asyncio.sleep(.1)
        slow['drop'] = False; mute['on'] = False
        t0 = time.time(); await due(e); took = time.time() - t0
        bk = await row(e)
        check('E. the same long batch with a sign of life after every group is NOT let go: all 100 pages are read', bk['payload']['read_pages'] == bk['payload']['pages'] == 100 and took > G.SILENCE
              and await HANGS.count_documents({'book_id': e}) == 1 and 'hang' not in bk['payload'], (bk['payload'].get('read_pages'), bk['payload'].get('pages'), took, await HANGS.count_documents({'book_id': e})))
        slow['on'] = False; G.SILENCE = 1.2
        check('E. nothing is watched once the steps are over', not G._watched and not G._left, (G._watched, len(G._left)))
    finally:
        PDF.run = real_run
        gate.set(); deaf_gate.set(); cancel_kicks()
        for _ in range(50):
            if not G._left:
                break
            await asyncio.sleep(.1)
        G.SILENCE, G.CHECK, G.LET_GO, G.DB_WAIT, BP.source_questions, BW.extract, BP.crop_ref = keep
        # the disposable test database of this run only (its name is checked first); the app's own database is never touched
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')


if __name__ == '__main__':
    asyncio.run(main())
