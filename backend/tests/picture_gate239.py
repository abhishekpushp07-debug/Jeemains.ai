"""TEST-ONLY iteration 239, Packet E step 2: a mock made from a PDF becomes a test only when every picture of it is proven in storage.
The app's own routes and the real book worker, Supabase faked at the wire (tests/fake_supabase239.py). Disposable DB, no network.
A. healthy: Live, sizes noted, proof noted.   B. Supabase said yes to one picture that is not there: saved once more, then Live.
C. it keeps happening: the mock stays Draft, only it waits ("Atki hai") with the reason, another book goes Live, Dobara chalao.
D. records exist but the files are gone or cut short (after "Try as student"): only those are saved again.
E. Supabase cannot list (503): the book waits for Supabase, nothing is held, Supabase is not rested.   F. the list is refused (400).
S. Scheduled: proven when scheduled (not at opening); an unproven one keeps its time and makes no test.
G. pictures split between the two stores: never Live.
H. Supabase not set up (Emergent only): each picture is read back; a gone or changed one is saved again; Emergent keeping none: Draft.
Run: cd /app/backend && python tests/picture_gate239.py
"""
import asyncio, hashlib, os, sys, time, types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage_book229 import H, J, BM, DB, S, JOBS_COL, RESULTS, check, mkstaff, upload, cut_pdf, cancel_kicks, pump, finish, again, row, job, listed  # noqa: E402
from storage_stuck231 import live, item  # noqa: E402
import httpx  # noqa: E402
from tejas import structure  # noqa: E402
from fake_supabase239 import Leaky, LIST  # noqa: E402

M = '/api/admin/master'
sb = None


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def inner(f):
    return f['path'][len(S.SB):]   # "<bucket>/<path>": the fake's own key


async def records(bid):
    return [f async for f in DB.tejas_files.find({'book_import_id': bid})]


def posts(n, bid):
    """How many times each picture of this upload was sent to Supabase since call n."""
    out = {}
    for m, _, p in sb.calls[n:]:
        if m == 'POST' and f'/jeelive/books/{bid}/crops/' in p:
            out[p.rsplit('/', 1)[1]] = out.get(p.rsplit('/', 1)[1], 0) + 1
    return out


def lists(n):
    return sum(1 for _, _, p in sb.calls[n:] if p.startswith(LIST))


def matches(recs):
    return bool(recs) and all(isinstance(f.get('size'), int) and inner(f) in sb.objects and f['size'] == len(sb.objects[inner(f)]) and f['sha256'] == sha(sb.objects[inner(f)]) for f in recs)


async def book(own, sec, tag):
    bid = (await upload(own, cut_pdf(tag, long=True), 'TEST_' + tag, section_id=sec))['id']; await finish(own, bid)
    mk = await BM.find_one({'book_id': bid})
    assert mk['state'] == 'ready', (mk['state'], mk['issues'])
    return bid, mk['_id'], mk['label']


async def tried(own, mid):
    """"Try as student": the Draft's pictures are saved and recorded without making a test."""
    await own.post(f'{M}/preview/{mid}')
    for _ in range(160):
        s = J(await own.get(f'{M}/preview/{mid}'))
        if s.get('state') != 'building':
            return s
        await asyncio.sleep(.25)
    return s


async def retry(own, bid):
    cancel_kicks()
    rev = J(await own.get(f'/api/admin/books/{bid}'))['revision']
    r = await own.post(f'/api/admin/books/{bid}/control', json={'revision': rev, 'action': 'retry'}); await pump()
    return r


def is_live(mk):
    return mk['state'] in ('published', 'scheduled') and bool(mk.get('set_id'))


def is_draft(mk):
    return mk['state'] == 'ready' and not mk['issues'] and not mk.get('publish_hold') and bool(mk.get('publish_requested')) and not mk.get('set_id')


async def main():
    global sb
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    sb = Leaky(S.TUS_CHUNK)
    client = httpx.Client(transport=httpx.MockTransport(sb))
    S._client = lambda: client                                               # nothing leaves this process
    S.time = types.SimpleNamespace(time=time.time, sleep=lambda s: None)     # the storage code's own waits only
    S.STATE.update(down_until=0.0, strikes=0, last_error='', auth=None, bucket=None, failovers=0, last_failover=None, backup_since=None)
    try:
        own, _ = await mkstaff('owner', 'pg')
        slug = J(await own.post('/api/admin/catalog/exams', json={'name': 'PGX', 'short': 'PG', 'subjects': ['Physics'], 'color': 'rose'})).get('slug')
        sec = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Mock Tests', 'description': '', 'layout': 'list', 'kind': 'mocks'})).get('id')
        emergent = {k for k in H.STORE if not k.startswith('jeelive/health/')}

        # ---- A. A healthy mock.
        a, ma, _ = await book(own, sec, 'gate_clean'); n = len(sb.calls)
        r = await live(own, ma)
        mk, recs = await BM.find_one({'_id': ma}), await records(a)
        check('A. a healthy mock goes Live as before', r.status_code == 200 and is_live(mk), (r.status_code, mk['state'], mk['issues']))
        check('A. every picture record carries the size and fingerprint of what Supabase holds', matches(recs), [(f.get('size'), inner(f) in sb.objects) for f in recs][:4])
        check('A. each picture was sent once; the proof looked at the folder list once', set(posts(n, a).values()) == {1} and len(posts(n, a)) == len(recs) and lists(n) == 1, (posts(n, a), len(recs), lists(n)))
        p = await DB.tejas_picture_proofs.find_one({'_id': mk['set_id']}) or {}
        check('A. the proof is noted beside the test: all pictures, in Supabase', p.get('ok') is True and p.get('total') == p.get('proven') == len(recs) and p.get('store') == 'supabase' and p.get('at'), p)
        it = await item(own, sec, mk['set_id'])
        check('A. Mocks: the Live row carries "Pictures: n / n · Storage: Supabase"', it.get('status') == 'live' and {k: (it.get('pictures') or {}).get(k) for k in ('proven', 'total', 'store')}
              == {'proven': len(recs), 'total': len(recs), 'store': 'supabase'}, it.get('pictures'))

        # ---- B. Supabase said yes to one picture, but it is not there.
        b, mb, _ = await book(own, sec, 'gate_once')
        sb.vanish, sb.vanish_first, sb.lost = [f'/books/{b}/crops/'], 1, []; n = len(sb.calls)
        r = await live(own, mb)
        mk, recs, sent = await BM.find_one({'_id': mb}), await records(b), posts(n, b)
        lost = [k.rsplit('/', 1)[1] for k in sb.lost]
        check('B. the picture that was not there is found by the proof and saved once more; the mock then goes Live', is_live(mk) and len(lost) == 1 and sent.get(lost[0]) == 2
              and sorted(v for k, v in sent.items() if k != lost[0]) == [1] * (len(recs) - 1) and lists(n) == 2, (mk['state'], mk['issues'], lost, sent, lists(n)))
        check('B. every picture of the Live mock is in Supabase with its noted size and fingerprint', matches(recs), len(recs))
        check('B. nothing was held and nothing waits', 'storage_wait' not in (await row(b))['payload'] and (await job(b))['status'] == 'done', (await row(b))['payload'].get('storage_wait'))
        sb.vanish, sb.vanish_first = [], None

        # ---- C. It keeps happening for every picture of one mock.
        c, mc, label = await book(own, sec, 'gate_stuck')
        sb.vanish = [f'/books/{c}/crops/']; n = len(sb.calls)
        r = await live(own, mc)
        bk, mk, jb, recs = await row(c), await BM.find_one({'_id': mc}), await job(c), await records(c)
        w = bk['payload'].get('storage_wait') or {}
        want = f"{len(recs)} pictures storage me nahi mili"
        check('C. Live pressed: the mock is NOT Live, NOT held, has nothing to fix; its Live request is kept and no test was made', r.status_code == 200 and is_draft(mk)
              and not await DB.tejas_sets.count_documents({'book_import_id': c}), (r.status_code, mk['state'], mk['issues'], mk.get('publish_hold'), mk.get('set_id')))
        check('C. the book says "Atki hai": which mock, how many pictures, what happens next', bk['state'] == 'matching' and w.get('stuck') and w.get('kind') == 'stuck' and w.get('what') == 'proof'
              and w.get('mock') == label and w.get('mock_id') == mc and (w.get('mocks') or {}).get(mc, {}).get('kind') == 'proof' and w.get('reason') == want and '15 minute' in w.get('next', '')
              and 'Atki hai' in bk['payload'].get('message', '') and 'saabit' in bk['payload'].get('message', ''), (bk['state'], w, bk['payload'].get('message')))
        check('C. every picture was saved once more exactly once (two sends each), and the proof looked twice', set(posts(n, c).values()) == {2} and len(posts(n, c)) == len(recs) and lists(n) == 2, (posts(n, c), lists(n)))
        check('C. its job tries again by itself in 15 minutes and kept all its tries', jb['status'] == 'queued' and jb.get('stuck') is True and jb.get('attempts', 0) == 0 and 800 <= jb['next_run_at'] - time.time() <= 901,
              ({k: jb.get(k) for k in ('status', 'stuck', 'attempts')}, jb['next_run_at'] - time.time()))
        check('C. Supabase is NOT rested for everyone', S.supabase_on() and S.STATE['strikes'] == 0, (S.STATE['down_until'] - time.time(), S.STATE['strikes']))
        up, it = await listed(own, sec, c), await item(own, sec, mc)
        check('C. Uploads: the PDF is listed as stuck with Dobara chalao and says it is about the proof', up.get('state') == 'stuck' and up.get('can_retry') and up.get('active') is False
              and up.get('storage_wait', {}).get('mock') == label and up['storage_wait'].get('what') == 'proof' and up['storage_wait'].get('reason') == want, up)
        check('C. Mocks: its row carries the reason and says it is about the proof; it has no "Pictures" line', it.get('status') == 'publishing' and (it.get('stuck') or {}).get('kind') == 'proof'
              and (it.get('stuck') or {}).get('reason') == want and 'pictures' not in it, it)
        m = J(await own.get('/api/admin/machine/status'))
        check('C. Machine: listed under stuck files with the mock\'s name', [(x['id'], x.get('mock')) for x in m.get('storage_stuck', [])] == [(c, label)] and not m.get('storage_waiting'), (m.get('storage_stuck'), m.get('storage_waiting')))
        h = J(await own.get('/api/admin/storage/health'))
        check('C. Badge: not green; it says the pictures were not proven and does NOT say a file is stuck in Supabase; Supabase itself shows working', h.get('level') == 'yellow' and h['held']['stuck'] == 1
              and any('saabit nahi hui' in x for x in h['reasons']) and not any('Supabase mein atki hai' in x for x in h['reasons']) and h['supabase']['ok'], (h.get('level'), h.get('held'), h.get('reasons')))
        d, md, _ = await book(own, sec, 'gate_next'); r = await live(own, md)
        check('C. another book goes Live meanwhile (the queue is not blocked)', is_live(await BM.find_one({'_id': md})), (await BM.find_one({'_id': md}))['state'])
        r = await retry(own, c)
        bk, mk = await row(c), await BM.find_one({'_id': mc})
        w2 = bk['payload'].get('storage_wait') or {}
        check('C. Dobara chalao while it still happens: stuck again, still Draft, "since" kept, one waiting job', r.status_code == 200 and is_draft(mk) and w2.get('stuck') and w2.get('what') == 'proof' and w2.get('since') == w.get('since')
              and await JOBS_COL.count_documents({'kind': 'book_step', 'payload.book_id': c, 'status': 'queued'}) == 1, (r.status_code, w2, mk['state']))
        sb.vanish = []; n = len(sb.calls)
        r = await retry(own, c)
        bk, mk, recs = await row(c), await BM.find_one({'_id': mc}), await records(c)
        check('C. Supabase keeps the pictures now + Dobara chalao: the mock goes Live, nothing left waiting', r.status_code == 200 and is_live(mk) and 'storage_wait' not in bk['payload'] and 'stuck_round' not in bk['payload'],
              (mk['state'], mk['issues'], bk['payload'].get('storage_wait')))
        check('C. every picture is in Supabase with its noted size and fingerprint; each was sent once in this try', matches(recs) and set(posts(n, c).values()) == {1} and len(posts(n, c)) == len(recs), (len(recs), posts(n, c)))
        up, m, r = await listed(own, sec, c), J(await own.get('/api/admin/machine/status')), J(await own.get(f'{M}/types/{sec}/mocks'))
        check('C. the screens no longer call anything stuck', up.get('state') != 'stuck' and not m.get('storage_stuck') and not any(x.get('stuck') for x in r['items']), (up, m.get('storage_stuck')))

        # ---- D. The records exist, but two files are gone from storage and one is a byte short.
        e, me, _ = await book(own, sec, 'gate_gone')
        s = await tried(own, me); recs = await records(e)
        check('D. setup: "Try as student" saved the Draft\'s pictures and their records; no test was made', s.get('state') == 'ready' and len(recs) >= 6 and matches(recs) and not (await BM.find_one({'_id': me})).get('set_id'), (s, len(recs)))
        gone, short = [inner(f) for f in recs[:2]], inner(recs[2])
        for k in gone:
            del sb.objects[k]
        sb.objects[short] = sb.objects[short][:-1]
        n = len(sb.calls)
        r = await live(own, me)
        mk, after = await BM.find_one({'_id': me}), await records(e)
        names = sorted(k.rsplit('/', 1)[1] for k in gone + [short])
        check('D. Live: only the three bad pictures are saved again, then the mock goes Live', is_live(mk) and sorted(posts(n, e)) == names and set(posts(n, e).values()) == {1} and lists(n) == 2, (mk['state'], mk['issues'], posts(n, e), lists(n)))
        check('D. every picture is in Supabase again with its noted size and fingerprint; no record was added or lost', matches(after) and sorted(f['id'] for f in after) == sorted(f['id'] for f in recs), len(after))

        # ---- E. Supabase cannot give the list (503): nothing can be said, so nothing is called missing.
        f, mf, _ = await book(own, sec, 'gate_away')
        sb.list_code = 503
        r = await live(own, mf)
        bk, mk, jb = await row(f), await BM.find_one({'_id': mf}), await job(f)
        w = bk['payload'].get('storage_wait') or {}
        check('E. the book waits for Supabase; the mock is not held and not called stuck', is_draft(mk) and w and not w.get('stuck') and w.get('kind') == 'away' and jb['status'] == 'queued' and not jb.get('stuck')
              and jb.get('storage_waits') == 1 and jb.get('attempts', 0) == 0, (mk['state'], mk['issues'], w, {k: jb.get(k) for k in ('status', 'stuck', 'storage_waits', 'attempts')}))
        check('E. the proof did not rest Supabase for everyone', S.supabase_on() and S.STATE['strikes'] == 0, S.STATE['strikes'])
        sb.list_code = None; n = len(sb.calls)
        r = await again(own)
        bk, mk = await row(f), await BM.find_one({'_id': mf})
        check('E. Supabase answers again: the waiting mock goes Live by itself, no picture is sent twice', r.get('woke', 0) >= 1 and is_live(mk) and 'storage_wait' not in bk['payload'] and not posts(n, f), (r.get('woke'), mk['state'], posts(n, f)))

        # ---- F. Supabase refuses the list of this folder (400) while it is up: only this mock waits.
        g, mg, glabel = await book(own, sec, 'gate_list')
        sb.list_code = 400
        r = await live(own, mg)
        bk, mk = await row(g), await BM.find_one({'_id': mg})
        w = bk['payload'].get('storage_wait') or {}
        check('F. the mock stays Draft and says the list was refused, with the code', is_draft(mk) and w.get('stuck') and w.get('what') == 'proof' and w.get('mock') == glabel and 'list nahi di (400)' in w.get('reason', '')
              and S.supabase_on(), (mk['state'], w))
        sb.list_code = None
        r = await retry(own, g)
        check('F. the list works again + Dobara chalao: Live', is_live(await BM.find_one({'_id': mg})) and 'storage_wait' not in (await row(g))['payload'], (await BM.find_one({'_id': mg}))['state'])

        # ---- S. Scheduled: the pictures are proven when the mock is scheduled, not when it opens.
        s1, ms1, _ = await book(own, sec, 'gate_sched'); at = time.time() + 86400
        r = await own.post(M + '/status', json={'items': [{'kind': 'book_mock', 'id': ms1}], 'to': 'scheduled', 'at': at}); await pump()
        mk = await BM.find_one({'_id': ms1})
        st, p = await DB.tejas_sets.find_one({'id': mk.get('set_id')}, {'start_at': 1}) or {}, await DB.tejas_picture_proofs.find_one({'_id': mk.get('set_id')}) or {}
        check('S. a healthy mock is Scheduled for tomorrow; its pictures were proven now, not at its opening time', r.status_code == 200 and mk['state'] == 'scheduled' and abs((st.get('start_at') or 0) - at) < 2
              and p.get('ok') is True and p.get('proven') == len(await records(s1)) and 0 < p.get('at', 0) < at - 80000, (r.status_code, mk['state'], st, p))
        s2, ms2, _ = await book(own, sec, 'gate_sched_bad')
        sb.vanish = [f'/books/{s2}/crops/']
        r = await own.post(M + '/status', json={'items': [{'kind': 'book_mock', 'id': ms2}], 'to': 'scheduled', 'at': at}); await pump()
        bk, mk, it = await row(s2), await BM.find_one({'_id': ms2}), await item(own, sec, ms2)
        w = bk['payload'].get('storage_wait') or {}
        check('S. Scheduled while Supabase keeps no picture: no test is made; the mock keeps its chosen time and its row says why', r.status_code == 200 and is_draft(mk) and mk.get('release_at') == at
              and w.get('stuck') and w.get('what') == 'proof' and it.get('status') == 'scheduled' and (it.get('stuck') or {}).get('kind') == 'proof'
              and not await DB.tejas_sets.count_documents({'book_import_id': s2}), (r.status_code, mk['state'], mk.get('release_at'), w, it.get('status'), it.get('stuck')))
        sb.vanish = []
        r = await retry(own, s2)
        mk = await BM.find_one({'_id': ms2})
        st = await DB.tejas_sets.find_one({'id': mk.get('set_id')}, {'start_at': 1}) or {}
        check('S. Supabase keeps the pictures + Dobara chalao: Scheduled for the chosen time', mk['state'] == 'scheduled' and abs((st.get('start_at') or 0) - at) < 2 and 'storage_wait' not in (await row(s2))['payload'],
              (mk['state'], mk['issues'], st))

        # ---- G. One mock, one storage: two of its pictures are in Emergent, the rest in Supabase.
        h, mh, _ = await book(own, sec, 'gate_split')
        await tried(own, mh); recs = await records(h); moved = set()
        for x in recs[:2]:
            key = inner(x).split('/', 1)[1]
            H.STORE[key] = sb.objects[inner(x)]; moved.add(key)
            await DB.tejas_files.update_one({'id': x['id']}, {'$set': {'path': key}})
        n = len(sb.calls)
        r = await live(own, mh)
        bk, mk = await row(h), await BM.find_one({'_id': mh})
        w = bk['payload'].get('storage_wait') or {}
        check('G. pictures split between the stores: the mock is NOT Live and says so; nothing was sent again', is_draft(mk) and w.get('stuck') and w.get('what') == 'proof'
              and w.get('reason') == f'Pictures do storage me bati hain ({len(recs) - 2} Supabase me, 2 Emergent me)' and not posts(n, h) and not await DB.tejas_sets.count_documents({'book_import_id': h}), (mk['state'], w, posts(n, h)))
        check('nothing went to Emergent storage (besides the two pictures this test put there)', {k for k in H.STORE if not k.startswith('jeelive/health/')} == emergent | moved)

        # ---- H. Supabase is not set up at all: every file lives in Emergent, which has no list, so each picture is read back.
        url, real, seen, lose = os.environ.pop('SUPABASE_URL'), S.request, [], []

        def logged(method, path, data=None, content_type=None):
            seen.append((method, path))
            if method == 'PUT' and any(x in path for x in lose):
                return H._Resp(j={'path': path})   # Emergent says yes, the picture is not kept
            return real(method, path, data, content_type)
        S.request = logged
        try:
            i, mi, _ = await book(own, sec, 'gate_em'); n = len(sb.calls); seen.clear()
            r = await live(own, mi)
            mk, recs = await BM.find_one({'_id': mi}), await records(i)
            p, it = await DB.tejas_picture_proofs.find_one({'_id': mk.get('set_id')}) or {}, await item(own, sec, mk.get('set_id'))
            held = bool(recs) and all(not f['path'].startswith(S.SB) and f['path'] in H.STORE and sha(H.STORE[f['path']]) == f['sha256'] and f.get('size') == len(H.STORE[f['path']]) for f in recs)
            check('H. without Supabase: the mock goes Live; every picture is in Emergent with its noted size and fingerprint; Supabase is not asked', is_live(mk) and held and len(sb.calls) == n, (mk['state'], mk['issues'], len(recs), len(sb.calls) - n))
            check('H. ...every picture (the option pieces too) was read back from Emergent; the row says Storage: Emergent', {x for m, x in seen if m == 'GET' and '/crops/' in x} == {f['path'] for f in recs}
                  and p.get('ok') is True and p.get('store') == 'emergent' and p.get('proven') == len(recs) and (it.get('pictures') or {}).get('store') == 'emergent', (p, it.get('pictures')))
            j, mj, _ = await book(own, sec, 'gate_em_gone')
            await tried(own, mj); recs = await records(j)
            gone, changed = recs[0]['path'], recs[1]['path']
            del H.STORE[gone]
            H.STORE[changed] = H.STORE[changed][:-1] + bytes([H.STORE[changed][-1] ^ 1])
            seen.clear()
            r = await live(own, mj)
            mk, after = await BM.find_one({'_id': mj}), await records(j)
            check('H. one picture gone from Emergent and one with other bytes: only those two are saved again, then the mock goes Live', is_live(mk) and sorted(x for m, x in seen if m == 'PUT' and '/crops/' in x) == sorted([gone, changed])
                  and all(f['path'] in H.STORE and sha(H.STORE[f['path']]) == f['sha256'] for f in after), (mk['state'], mk['issues'], [x for m, x in seen if m == 'PUT']))
            k, mk3, klabel = await book(own, sec, 'gate_em_lost')
            lose.append(f'/books/{k}/crops/')
            r = await live(own, mk3)
            bk, mk = await row(k), await BM.find_one({'_id': mk3})
            w, made = bk['payload'].get('storage_wait') or {}, await DB.tejas_files.count_documents({'book_import_id': k})
            check('H. Emergent says yes but keeps no picture: the mock stays Draft and says how many could not be read back', is_draft(mk) and w.get('stuck') and w.get('what') == 'proof' and w.get('mock') == klabel
                  and made > 0 and w.get('reason') == f'{made} pictures storage se wapas padhi nahi ja saki' and not await DB.tejas_sets.count_documents({'book_import_id': k}), (mk['state'], mk['issues'], w, made))
            lose.clear()
            r = await retry(own, k)
            check('H. Emergent keeps the pictures now + Dobara chalao: Live', is_live(await BM.find_one({'_id': mk3})) and 'storage_wait' not in (await row(k))['payload'], (await BM.find_one({'_id': mk3}))['state'])
        finally:
            S.request = real
            os.environ['SUPABASE_URL'] = url
    finally:
        cancel_kicks()
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')


if __name__ == '__main__':
    asyncio.run(main())
