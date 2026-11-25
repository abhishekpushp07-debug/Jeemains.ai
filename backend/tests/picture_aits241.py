"""TEST-ONLY iteration 241, Packet E step 2 on the All India Test Series path: a PDF mock that is given a day becomes that day's paper
only when every picture of it is proven in storage. The app's own routes and the real book worker, Supabase faked at the wire
(tests/fake_supabase239.py). Disposable DB, no network.
A. healthy: the paper is built for its day, the proof is noted.
B. Supabase keeps none of its pictures: no paper is made, the mock keeps its day, the PDF says "Atki hai", the day's row carries the
   reason, students see nothing of it, another PDF's day is built meanwhile, Dobara chalao builds it once Supabase keeps the pictures.
C. its day opens while it still waits: it does not open late; it loses its day and nothing is called stuck any more.
Run: cd /app/backend && python tests/picture_aits241.py
"""
import asyncio, sys, time, types, uuid
from datetime import datetime, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage_book229 import H, J, BM, DB, S, RESULTS, check, mkstaff, cancel_kicks, pump, row, job, listed  # noqa: E402
from picture_gate239 import book, retry, records, posts, matches  # noqa: E402
import picture_gate239 as PG  # noqa: E402
from book_publishing_iso170 import client  # noqa: E402
import httpx  # noqa: E402
from tejas import structure, series_admin, book_publish as BP  # noqa: E402
from tejas.live_series import IST  # noqa: E402
from fake_supabase239 import Leaky  # noqa: E402

M = '/api/admin/master'
SETS = DB.tejas_sets


async def give(own, sid, mid, day):
    r = await own.post(f'{M}/series/{sid}/assign', json={'kind': 'book_mock', 'id': mid, 'date': day}); await pump()
    return r


async def slot(c, path, day):
    d = J(await c.get(path))
    return next((x for x in d.get('slots', []) if x['date'] == day), {}), d


def waits(mk, day):
    """The mock is as the owner left it: checked, given this day, asked to become its paper; no paper was made of it."""
    return mk['state'] == 'ready' and not mk['issues'] and not mk.get('publish_hold') and bool(mk.get('publish_requested')) and mk.get('series_date') == day and not mk.get('set_id')


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    sb = Leaky(S.TUS_CHUNK); PG.sb = sb
    wire = httpx.Client(transport=httpx.MockTransport(sb))
    S._client = lambda: wire                                                 # nothing leaves this process
    S.time = types.SimpleNamespace(time=time.time, sleep=lambda s: None)     # the storage code's own waits only
    S.STATE.update(down_until=0.0, strikes=0, last_error='', auth=None, bucket=None, failovers=0, last_failover=None, backup_since=None)
    try:
        own, _ = await mkstaff('owner', 'a241'); anon = client()
        stu = client(); await stu.post('/api/auth/phone/signup', json={'phone': '93' + str(uuid.uuid4().int)[:8], 'pin': '8261', 'confirm_pin': '8261'})
        slug = J(await own.post('/api/admin/catalog/exams', json={'name': 'AIX', 'short': 'AX', 'subjects': ['Physics'], 'color': 'rose'})).get('slug')
        first = datetime.now(IST).date() + timedelta(days=2)
        days = [(first + timedelta(days=i)).isoformat() for i in range(6)]
        made = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'All India Test Series', 'description': '', 'layout': 'list', 'kind': 'aits',
                 'first_date': days[0], 'days': 6, 'open_time': '09:00', 'last_start': '11:00', 'minutes': 10, 'correct': 4, 'wrong': -1}))
        sec, sid = made.get('id'), made.get('series_id')
        await structure.exams.update_one({'_id': slug}, {'$set': {'shown': True}})
        r = await own.put(f'{M}/series/{sid}', json={'shown': True})
        check('setup: a test series of its own exam, shown to students', bool(sec and sid) and r.status_code == 200, (made, r.status_code))
        cfg = await series_admin.series_cfg(sid)
        view, public = f'{M}/series/{sid}', f'/api/series/{sid}/schedule'

        # ---- A. A healthy PDF mock is given a day.
        a, ma, _ = await book(own, sec, 'aits_clean'); n = len(sb.calls)
        r = await give(own, sid, ma, days[0])
        mk, recs = await BM.find_one({'_id': ma}), await records(a)
        st, p = await SETS.find_one({'id': mk.get('set_id')}) or {}, await DB.tejas_picture_proofs.find_one({'_id': mk.get('set_id')}) or {}
        check('A. a healthy PDF mock given a day: its paper is built for that day, as before', r.status_code == 200 and mk['state'] == 'scheduled' and st.get('status') == 'published'
              and st.get('series_id') == sid and st.get('series_date') == days[0] and abs(st.get('start_at', 0) - series_admin.window(days[0], cfg)['opens_at']) < 1,
              (r.status_code, r.text[:200], mk['state'], mk['issues'], {k: st.get(k) for k in ('status', 'series_id', 'series_date')}))
        check('A. every picture was proven before the paper was made; each was sent once', p.get('ok') is True and p.get('total') == p.get('proven') == len(recs) and p.get('store') == 'supabase'
              and matches(recs) and set(posts(n, a).values()) == {1}, (p, posts(n, a)))
        s, _ = await slot(own, view, days[0])
        check('A. Master: the day shows the built paper; nothing is called stuck', (s.get('paper') or {}).get('kind') == 'set' and s['paper']['id'] == mk['set_id'] and 'stuck' not in s['paper'], s.get('paper'))

        # ---- B. Supabase says yes to every picture of this PDF and keeps none.
        b, mb, label = await book(own, sec, 'aits_stuck')
        sb.vanish = [f'/books/{b}/crops/']; n = len(sb.calls)
        r = await give(own, sid, mb, days[1])
        bk, mk, jb, recs = await row(b), await BM.find_one({'_id': mb}), await job(b), await records(b)
        w = bk['payload'].get('storage_wait') or {}
        want = f"{len(recs)} pictures storage me nahi mili"
        check('B. given a day while Supabase keeps none of its pictures: no paper is made; the mock keeps its day and is not held', r.status_code == 200 and waits(mk, days[1])
              and not await SETS.count_documents({'book_import_id': b}), (r.status_code, r.text[:200], mk['state'], mk['issues'], mk.get('series_date'), mk.get('set_id')))
        check('B. the PDF says "Atki hai": which mock, how many pictures, what happens next', bk['state'] == 'matching' and w.get('stuck') and w.get('what') == 'proof' and w.get('mock') == label
              and (w.get('mocks') or {}).get(mb, {}).get('kind') == 'proof' and w.get('reason') == want and '15 minute' in w.get('next', '') and 'saabit' in bk['payload'].get('message', ''), (bk['state'], w, bk['payload'].get('message')))
        check('B. every picture was saved once more exactly once (two sends each)', set(posts(n, b).values()) == {2} and len(posts(n, b)) == len(recs), posts(n, b))
        check('B. its job tries again by itself in 15 minutes and kept all its tries', jb['status'] == 'queued' and jb.get('stuck') is True and jb.get('attempts', 0) == 0 and 800 <= jb['next_run_at'] - time.time() <= 901,
              ({k: jb.get(k) for k in ('status', 'stuck', 'attempts')}, jb['next_run_at'] - time.time()))
        check('B. Supabase is NOT rested for everyone', S.supabase_on() and S.STATE['strikes'] == 0, S.STATE['strikes'])
        s, _ = await slot(own, view, days[1])
        pp = s.get('paper') or {}
        check("B. Master: the day's row names the waiting paper and carries the reason", pp.get('kind') == 'book_mock' and pp.get('id') == mb and pp.get('pending') is True
              and (pp.get('stuck') or {}).get('kind') == 'proof' and pp['stuck'].get('reason') == want and pp['stuck'].get('since') == w.get('since'), pp)
        s, _ = await slot(own, view, days[0])
        check('B. Master: the day that already has its paper is unchanged', (s.get('paper') or {}).get('kind') == 'set' and 'stuck' not in s['paper'], s.get('paper'))
        up = await listed(own, sec, b)
        check('B. Uploads on the series page: the PDF is listed as stuck, about the proof, with Dobara chalao', up.get('state') == 'stuck' and up.get('can_retry') and up.get('active') is False
              and up.get('storage_wait', {}).get('what') == 'proof' and up['storage_wait'].get('mock') == label and up['storage_wait'].get('reason') == want, up)
        for who, c in (('a student', stu), ('a visitor', anon)):
            x, d = await slot(c, public, days[1])
            check(f'B. {who} sees no paper on that day and nothing about the wait', bool(x) and x.get('set_id') is None and not x.get('can_start') and not x.get('ready') and x.get('title', '').endswith('Test 02')
                  and 'paper' not in x and 'stuck' not in x and label not in str(d) and 'saabit' not in str(d), x)
        h = J(await own.get('/api/admin/storage/health'))
        check('B. Badge: not green; it says the pictures were not proven; Supabase itself shows working', h.get('level') == 'yellow' and h['held']['stuck'] == 1 and any('saabit nahi hui' in x for x in h['reasons'])
              and h['supabase']['ok'], (h.get('level'), h.get('held'), h.get('reasons')))
        c, mc, _ = await book(own, sec, 'aits_next'); r = await give(own, sid, mc, days[2])
        mk3 = await BM.find_one({'_id': mc})
        check("B. another PDF's day is built meanwhile (the queue is not blocked)", r.status_code == 200 and mk3['state'] == 'scheduled' and (await SETS.find_one({'id': mk3.get('set_id')}) or {}).get('series_date') == days[2], (r.status_code, mk3['state'], mk3['issues']))
        r = await retry(own, b)
        bk, mk = await row(b), await BM.find_one({'_id': mb})
        w2 = bk['payload'].get('storage_wait') or {}
        s, _ = await slot(own, view, days[1])
        check('B. Dobara chalao while it still happens: stuck again, the day is kept, "since" kept', r.status_code == 200 and waits(mk, days[1]) and w2.get('stuck') and w2.get('what') == 'proof' and w2.get('since') == w.get('since')
              and ((s.get('paper') or {}).get('stuck') or {}).get('kind') == 'proof', (r.status_code, mk['state'], w2, s.get('paper')))
        sb.vanish = []; n = len(sb.calls)
        r = await retry(own, b)
        bk, mk, recs = await row(b), await BM.find_one({'_id': mb}), await records(b)
        st = await SETS.find_one({'id': mk.get('set_id')}) or {}
        check('B. Supabase keeps the pictures now + Dobara chalao: the paper is built for the day it was given', r.status_code == 200 and mk['state'] == 'scheduled' and st.get('series_date') == days[1]
              and abs(st.get('start_at', 0) - series_admin.window(days[1], cfg)['opens_at']) < 1 and 'storage_wait' not in bk['payload'], (mk['state'], mk['issues'], st.get('series_date'), bk['payload'].get('storage_wait')))
        check('B. every picture is in Supabase with its noted size and fingerprint; each was sent once in this try', matches(recs) and set(posts(n, b).values()) == {1} and len(posts(n, b)) == len(recs), (len(recs), posts(n, b)))
        s, _ = await slot(own, view, days[1])
        up = await listed(own, sec, b)
        check('B. the screens no longer call anything stuck: the day shows the built paper', (s.get('paper') or {}).get('kind') == 'set' and s['paper']['id'] == mk['set_id'] and 'stuck' not in s['paper'] and up.get('state') != 'stuck', (s.get('paper'), up))
        x, _ = await slot(stu, public, days[1])
        check('B. a student still cannot open it before its day', x.get('set_id') is None and not x.get('can_start'), x)

        # ---- C. Its day opens while it still waits.
        e, me, _ = await book(own, sec, 'aits_late')
        sb.vanish = [f'/books/{e}/crops/']
        r = await give(own, sid, me, days[3])
        mk = await BM.find_one({'_id': me})
        check('C. setup: a mock that waits for its pictures, with a day', r.status_code == 200 and waits(mk, days[3]) and ((await row(e))['payload'].get('storage_wait') or {}).get('what') == 'proof', (mk['state'], mk.get('series_date')))
        real, n = BP.database_now, len(sb.calls)

        async def later():
            return await real() + 30 * 86400
        BP.database_now = later   # for the publishing code only: every day of this series has opened
        try:
            r = await retry(own, e)
        finally:
            BP.database_now = real
        bk, mk = await row(e), await BM.find_one({'_id': me})
        check('C. its day opened while it waited: no paper is made late; the mock loses its day and waits for a new one', r.status_code == 200 and mk['state'] == 'ready' and not mk['issues'] and mk.get('series_date') is None
              and not mk.get('publish_requested') and mk.get('release_at') is None and not mk.get('set_id') and not await SETS.count_documents({'book_import_id': e}),
              (r.status_code, mk['state'], mk['issues'], mk.get('series_date'), mk.get('publish_requested'), mk.get('set_id')))
        check('C. no picture of it was sent again', not posts(n, e), posts(n, e))
        s, d = await slot(own, view, days[3])
        up, h = await listed(own, sec, e), J(await own.get('/api/admin/storage/health'))
        check('C. nothing is called stuck any more: the day is empty, the PDF does not wait, the badge counts no stuck file', 'storage_wait' not in bk['payload'] and s.get('paper') is None and up.get('state') != 'stuck'
              and h['held']['stuck'] == 0 and not any('saabit nahi hui' in x for x in h['reasons']), (bk['payload'].get('storage_wait'), s.get('paper'), up, h.get('held'), h.get('reasons')))
        check('C. the mock is back in the list of papers without a day', any(x['id'] == me and x['kind'] == 'book_mock' for x in d.get('candidates', [])), [x['id'] for x in d.get('candidates', [])])
        sb.vanish = []
    finally:
        cancel_kicks()
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')


if __name__ == '__main__':
    asyncio.run(main())
