"""TEST-ONLY iteration 242, Packet E step 3: a PDF mock the owner scheduled for a time never opens late. If that time has passed
before its paper could be made (it waited for its pictures, for Supabase, or the saving itself took too long), the mock stays Draft,
loses its time and says so on its row until the owner chooses Live or a new time. The app's own routes and the real book worker,
Supabase faked at the wire (tests/fake_supabase239.py). Disposable DB, no network. "Time passes" = the publishing code's own clock
(book_publish.database_now) is moved forward; nothing else is touched.
A. it waited because its pictures were not proven ("Atki hai"), its time passed: Draft, the row says so, nothing is sent, nothing stuck.
B. it waited for Supabase (503), its time passed: the same. A new time chosen afterwards works.
C. its time passed while its pictures were being saved: no test; the saved pictures are kept and not sent again at the next Live.
D. two mocks of one PDF: the one whose time passed does not stop the other, which is Scheduled for its own time.
E. unchanged: a healthy schedule; Live now.   F. a time the owner let go on purpose (release now) is not stopped.
Run: cd /app/backend && python tests/picture_late242.py
"""
import asyncio, sys, time, types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage_book229 import H, J, BM, DB, S, RESULTS, check, mkstaff, upload, cancel_kicks, pump, finish, again, row, listed  # noqa: E402
from storage_stuck231 import live, item  # noqa: E402
from picture_gate239 import book, retry, records, posts, matches, is_live  # noqa: E402
import picture_gate239 as PG  # noqa: E402
from book_publishing_iso170 import build_pdf, q3  # noqa: E402
import httpx  # noqa: E402
from tejas import structure, book_publish as BP  # noqa: E402
from fake_supabase239 import Leaky  # noqa: E402

M = '/api/admin/master'
SETS = DB.tejas_sets
HOUR = 3600


class Later:
    """Inside: the publishing code reads a clock that is `secs` ahead."""
    def __init__(self, secs):
        self.secs = secs

    def __enter__(self):
        real, secs = BP.database_now, self.secs
        self.real = real

        async def later():
            return await real() + secs
        BP.database_now = later

    def __exit__(self, *a):
        BP.database_now = self.real


async def schedule(own, at, *mids):
    r = await own.post(M + '/status', json={'items': [{'kind': 'book_mock', 'id': m} for m in mids], 'to': 'scheduled', 'at': at}); await pump()
    return r


def missed(mk, at):
    """Draft again: nothing to fix, no time, not asked to go Live, no test made of it; it remembers which time passed."""
    return (mk['state'] == 'ready' and not mk['issues'] and not mk.get('publish_hold') and not mk.get('publish_requested') and mk.get('release_at') is None
            and not mk.get('set_id') and mk.get('missed_at') == at)


def waits(mk, at):
    return mk['state'] == 'ready' and not mk['issues'] and bool(mk.get('publish_requested')) and mk.get('release_at') == at and not mk.get('set_id') and not mk.get('missed_at')


async def stuck_count(own):
    return J(await own.get('/api/admin/storage/health'))['held']['stuck']


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    sb = Leaky(S.TUS_CHUNK); PG.sb = sb
    wire = httpx.Client(transport=httpx.MockTransport(sb))
    S._client = lambda: wire                                                 # nothing leaves this process
    S.time = types.SimpleNamespace(time=time.time, sleep=lambda s: None)     # the storage code's own waits only
    S.STATE.update(down_until=0.0, strikes=0, last_error='', auth=None, bucket=None, failovers=0, last_failover=None, backup_since=None)
    try:
        own, _ = await mkstaff('owner', 'l242')
        slug = J(await own.post('/api/admin/catalog/exams', json={'name': 'LTX', 'short': 'LT', 'subjects': ['Physics'], 'color': 'rose'})).get('slug')
        sec = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Mock Tests', 'description': '', 'layout': 'list', 'kind': 'mocks'})).get('id')

        # ---- A. Scheduled; its pictures are not proven, so it waits ("Atki hai"); its time passes while it waits.
        a, ma, _ = await book(own, sec, 'late_proof'); at = time.time() + HOUR
        sb.vanish = [f'/books/{a}/crops/']
        r = await schedule(own, at, ma)
        bk, mk, it = await row(a), await BM.find_one({'_id': ma}), await item(own, sec, ma)
        check('A. setup: scheduled, pictures not proven: it waits with its time ("Atki hai")', r.status_code == 200 and waits(mk, at) and (bk['payload'].get('storage_wait') or {}).get('what') == 'proof'
              and it.get('status') == 'scheduled' and (it.get('stuck') or {}).get('kind') == 'proof' and await stuck_count(own) == 1, (r.status_code, mk['state'], mk.get('release_at'), bk['payload'].get('storage_wait'), it))
        sb.vanish = []; n = len(sb.calls)   # Supabase would keep the pictures now: the mock could be built, but its time is over
        with Later(2 * HOUR):
            r = await retry(own, a)
        bk, mk, it = await row(a), await BM.find_one({'_id': ma}), await item(own, sec, ma)
        check('A. its time passed while it waited: no test is made late; the mock is Draft again without a time', r.status_code == 200 and missed(mk, at) and not await SETS.count_documents({'book_import_id': a}),
              (r.status_code, {k: mk.get(k) for k in ('state', 'issues', 'publish_requested', 'release_at', 'set_id', 'missed_at')}))
        check('A. nothing was cut or sent for a paper that will not open', not posts(n, a), posts(n, a))
        check('A. Mocks: its row is Draft, carries the time that passed, and is not called stuck', it.get('status') == 'draft' and it.get('missed_at') == at and 'stuck' not in it and it.get('start_at') is None
              and it.get('to_fix') == 0, it)
        up = await listed(own, sec, a)
        check('A. nothing is called stuck any more: the PDF does not wait, the badge counts no stuck file', 'storage_wait' not in bk['payload'] and up.get('state') != 'stuck' and await stuck_count(own) == 0,
              (bk['payload'].get('storage_wait'), up))
        check('A. it is written down once (audit)', await DB.tejas_audits.count_documents({'action': 'Book mock missed its time', 'resource': ma}) == 1)
        r = await live(own, ma)
        mk, recs = await BM.find_one({'_id': ma}), await records(a)
        it = await item(own, sec, mk.get('set_id'))
        check('A. the owner presses Live karo: it goes Live now; the note about the passed time is gone', r.status_code == 200 and mk['state'] == 'published' and bool(mk.get('set_id')) and not mk.get('missed_at')
              and it.get('status') == 'live' and 'missed_at' not in it and matches(recs), (r.status_code, mk['state'], mk['issues'], mk.get('missed_at'), it.get('status')))

        # ---- B. Scheduled; Supabase cannot answer (503), so the book waits for it; its time passes; Supabase comes back.
        b, mb, _ = await book(own, sec, 'late_away'); at = time.time() + HOUR
        sb.list_code = 503
        r = await schedule(own, at, mb)
        bk, mk = await row(b), await BM.find_one({'_id': mb})
        w = bk['payload'].get('storage_wait') or {}
        check('B. setup: scheduled while Supabase is away: the book waits for Supabase, the mock keeps its time', r.status_code == 200 and waits(mk, at) and w.get('kind') == 'away' and not w.get('stuck'), (mk['state'], mk.get('release_at'), w))
        sb.list_code = None; n = len(sb.calls)
        with Later(2 * HOUR):
            r = await again(own)
        bk, mk, it = await row(b), await BM.find_one({'_id': mb}), await item(own, sec, mb)
        check('B. Supabase is back after the chosen time: the mock does NOT open late; Draft, with the time that passed', r.get('woke', 0) >= 1 and missed(mk, at) and not await SETS.count_documents({'book_import_id': b})
              and 'storage_wait' not in bk['payload'] and it.get('status') == 'draft' and it.get('missed_at') == at and not posts(n, b), (r.get('woke'), mk['state'], mk.get('missed_at'), bk['payload'].get('storage_wait'), it, posts(n, b)))
        at2 = time.time() + 2 * 86400; n = len(sb.calls)
        r = await schedule(own, at2, mb)
        mk = await BM.find_one({'_id': mb})
        st, it = await SETS.find_one({'id': mk.get('set_id')}, {'start_at': 1, 'status': 1}) or {}, await item(own, sec, mk.get('set_id'))
        check('B. the owner chooses a new time: Scheduled for it; the old note is gone; no picture is sent again', r.status_code == 200 and mk['state'] == 'scheduled' and abs((st.get('start_at') or 0) - at2) < 2
              and not mk.get('missed_at') and it.get('status') == 'scheduled' and 'missed_at' not in it and not posts(n, b), (r.status_code, mk['state'], mk['issues'], st, mk.get('missed_at'), it.get('status'), posts(n, b)))

        # ---- C. Its time passes while its pictures are being saved and proven (a long paper, a slow storage).
        c, mc, _ = await book(own, sec, 'late_slow'); at = time.time() + HOUR
        real_proven, real_now, n = BP.proven, BP.database_now, len(sb.calls)

        async def after():
            return await real_now() + 2 * HOUR

        async def slow(*args, **kw):
            out = await real_proven(*args, **kw)
            BP.database_now = after   # the pictures are saved and proven; meanwhile the chosen time went by
            return out
        BP.proven = slow
        try:
            r = await schedule(own, at, mc)
        finally:
            BP.proven, BP.database_now = real_proven, real_now
        mk, recs, it = await BM.find_one({'_id': mc}), await records(c), await item(own, sec, mc)
        check('C. its time passed while its pictures were being saved: no test is made; Draft, with the time that passed', r.status_code == 200 and missed(mk, at) and not await SETS.count_documents({'book_import_id': c})
              and it.get('status') == 'draft' and it.get('missed_at') == at and 'storage_wait' not in (await row(c))['payload'], (r.status_code, mk['state'], mk['issues'], mk.get('missed_at'), it))
        check('C. the pictures that were saved are kept (each sent once, all in Supabase with size and fingerprint)', matches(recs) and set(posts(n, c).values()) == {1} and len(posts(n, c)) == len(recs), (len(recs), posts(n, c)))
        n = len(sb.calls)
        r = await live(own, mc)
        mk = await BM.find_one({'_id': mc})
        p = await DB.tejas_picture_proofs.find_one({'_id': mk.get('set_id')}) or {}
        check('C. Live karo afterwards: Live now, proven, and no picture is sent a second time', r.status_code == 200 and mk['state'] == 'published' and not mk.get('missed_at') and p.get('ok') is True
              and p.get('proven') == len(recs) and not posts(n, c), (mk['state'], mk['issues'], p, posts(n, c)))

        # ---- D. Two mocks of one PDF, each with its own time; only the first one's time passes.
        K = [(1, 'B'), (2, 'B'), (3, 'C')]
        d = (await upload(own, build_pdf([{'n': 1, 'qs': q3('LT1'), 'keys': K}, {'n': 2, 'qs': q3('LT2'), 'keys': K}]), 'TEST_late_two', section_id=sec))['id']; await finish(own, d)
        pair = [m async for m in BM.find({'book_id': d}).sort('order', 1)]
        assert len(pair) == 2 and all(m['state'] == 'ready' for m in pair), [(m['label'], m['state'], m['issues']) for m in pair]
        d1, d2 = pair[0]['_id'], pair[1]['_id']; at1, at2 = time.time() + HOUR, time.time() + 3 * 86400
        sb.vanish = [f'/books/{d}/crops/']
        r1 = await schedule(own, at1, d1); r2 = await schedule(own, at2, d2)
        m1, m2, bk = await BM.find_one({'_id': d1}), await BM.find_one({'_id': d2}), await row(d)
        check('D. setup: both mocks wait with their own times; the PDF names both', r1.status_code == 200 and r2.status_code == 200 and waits(m1, at1) and waits(m2, at2)
              and set((bk['payload'].get('storage_wait') or {}).get('mocks') or {}) == {d1, d2}, (m1['state'], m1.get('release_at'), m2['state'], m2.get('release_at'), bk['payload'].get('storage_wait')))
        sb.vanish = []
        with Later(2 * HOUR):
            r = await retry(own, d)
        m1, m2, bk = await BM.find_one({'_id': d1}), await BM.find_one({'_id': d2}), await row(d)
        st = await SETS.find_one({'id': m2.get('set_id')}, {'start_at': 1, 'status': 1}) or {}
        check('D. the first mock missed its time: Draft; it did not stop the second, which is Scheduled for its own time', r.status_code == 200 and missed(m1, at1) and m2['state'] == 'scheduled'
              and abs((st.get('start_at') or 0) - at2) < 2 and st.get('status') == 'published' and not m2.get('missed_at'), (m1['state'], m1.get('missed_at'), m2['state'], m2['issues'], st))
        check('D. the PDF is not called stuck; exactly one test was made of it', 'storage_wait' not in bk['payload'] and await SETS.count_documents({'book_import_id': d}) == 1 and await stuck_count(own) == 0, bk['payload'].get('storage_wait'))

        # ---- E. Unchanged behaviour.
        e, me, _ = await book(own, sec, 'late_ok'); at = time.time() + 86400
        r = await schedule(own, at, me)
        mk = await BM.find_one({'_id': me})
        st = await SETS.find_one({'id': mk.get('set_id')}, {'start_at': 1}) or {}
        check('E. a healthy mock scheduled for tomorrow is Scheduled for that time, as before', r.status_code == 200 and mk['state'] == 'scheduled' and abs((st.get('start_at') or 0) - at) < 2 and not mk.get('missed_at'),
              (r.status_code, mk['state'], mk['issues'], st))
        f, mf, _ = await book(own, sec, 'late_now')
        with Later(2 * HOUR):
            r = await live(own, mf)
        mk = await BM.find_one({'_id': mf})
        check('E. Live karo (no time chosen) is never touched by this rule', r.status_code == 200 and mk['state'] == 'published' and is_live(mk) and not mk.get('missed_at'), (mk['state'], mk['issues'], mk.get('missed_at')))

        # ---- F. A time the owner let go on purpose ("release now" of the older screen). The fields are set directly: Master has no button for it.
        g, mg, _ = await book(own, sec, 'late_override')
        await BM.update_one({'_id': mg}, {'$set': {'publish_requested': True, 'release_at': time.time() - 60, 'release_override': True}})
        r = await retry(own, g)
        mk = await BM.find_one({'_id': mg})
        check('F. a mock released on purpose after its time is published now, as before (not stopped by this rule)', r.status_code == 200 and mk['state'] == 'published' and bool(mk.get('set_id')) and not mk.get('missed_at'),
              (r.status_code, mk['state'], mk['issues'], mk.get('missed_at')))
    finally:
        cancel_kicks()
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')


if __name__ == '__main__':
    asyncio.run(main())
