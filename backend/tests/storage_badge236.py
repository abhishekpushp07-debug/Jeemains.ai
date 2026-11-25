"""TEST-ONLY iteration 236, packet D (the storage badge that tells the truth). The app's own routes and storage code, Supabase faked
at the wire (tests/fake_supabase231.py), disposable DB, no network, no real keys.
A. the check itself: a new file name every time, removed after; never "Read back different bytes"; only its own files can be removed
B. ONE record in the database: another server's finding is shown here, and its good check ends this server's rest
C. colours: green / yellow / red, each with its reason        D. the last 20 failures and the last 20 timings
E. the big-file test runs by itself when it is due            F. when a wait began is kept
Run: cd /app/backend && python tests/storage_badge236.py
"""
import asyncio, hashlib, json, os, sys, time, types, uuid
from pathlib import Path
from urllib.parse import unquote
sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage_book229 import H, J, BM, DB, S, RESULTS, JOBS_COL, check, mkstaff, upload, cut_pdf, big_pdf, finish, again, pump, row, job, cancel_kicks  # noqa: E402
import httpx  # noqa: E402
from tejas import structure, jobs as JOBS, storage_health as SH  # noqa: E402
from fake_supabase231 import Picky  # noqa: E402

COL = DB.tejas_storage_state
M = '/api/admin/master'
HEALTH, RETRY, BIG, MACHINE = '/api/admin/storage/health', '/api/admin/storage/retry', '/api/admin/storage/big-test', '/api/admin/machine/status'


class Lagging(Picky):
    """One more knob: with stale=True a path that was written twice gives back its FIRST bytes, the way an overwritten file can be read stale."""
    def __init__(self, chunk):
        super().__init__(chunk)
        self.stale, self.first = False, {}

    def __call__(self, req):
        p = unquote(req.url.path)
        if self.stale and not self.down and not self.block:
            if req.method == 'POST' and p.startswith('/storage/v1/object/') and not p.startswith(('/storage/v1/object/list/', '/storage/v1/object/info/')):
                self.first.setdefault(p[len('/storage/v1/object/'):], bytes(req.content))
            if req.method == 'GET' and p.startswith('/storage/v1/object/authenticated/'):
                key = p[len('/storage/v1/object/authenticated/'):]
                if key in self.first and key in self.objects:
                    return httpx.Response(200, content=self.first[key])
        return super().__call__(req)


def health_files(sb):
    return sorted(k.split('/', 1)[1] for k in sb.objects if k.split('/', 1)[1].startswith('health/'))


def check_posts(sb):
    start = f'/storage/v1/object/{S.bucket_name()}/'
    return [p[len(start):] for m, _, p in sb.calls if m == 'POST' and p.startswith(start + 'health/')]


def deletes(sb):
    return sum(1 for m, _, p in sb.calls if m == 'DELETE')


async def health(own, fresh=False):
    return J(await own.get(HEALTH + ('?fresh=true' if fresh else '')))


async def rec():
    return await COL.find_one({'_id': 'state'})


async def put(change):
    """What another server would leave in the shared record."""
    await COL.update_one({'_id': 'state'}, {'$set': change, '$inc': {'rev': 1}})


async def live(own, mid):
    r = await own.post(M + '/status', json={'items': [{'kind': 'book_mock', 'id': mid}], 'to': 'live'}); await pump()
    return r


async def shown(own, sec, tag, title, wait, state='received', transfer=False):
    """A row that only shows a wait: no job runs for it."""
    raw = cut_pdf(tag, long=True)
    bid = (await upload(own, raw, title, section_id=sec))['id']
    change = {'state': state, 'payload.storage_wait': {'at': time.time(), 'error': '', **wait}}
    if transfer:
        change['payload.transfer'] = {'url': '', 'path': f'jeelive/books/{bid}/original.pdf', 'size': len(raw), 'sent': 0, 'started': time.time()}
    await DB.tejas_books.update_one({'_id': bid}, {'$set': change})
    return bid


async def gone(bid):
    await DB.tejas_books.delete_one({'_id': bid}); await DB.tejas_book_parts.delete_many({'book_id': bid})


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    sb = Lagging(S.TUS_CHUNK)
    client = httpx.Client(transport=httpx.MockTransport(sb))
    S._client = lambda: client                                               # nothing leaves this process
    S.time = types.SimpleNamespace(time=time.time, sleep=lambda s: None)     # the storage code's own waits only
    S.STATE.update(down_until=0.0, strikes=0, last_error='', auth=None, bucket=None, failovers=0, last_failover=None, backup_since=None, last_ok=0.0, struck_at=0.0)
    S.EVENTS.clear(); S._recent.clear()
    real_request, slow_ms = S.request, SH.SLOW_MS
    try:
        own, owner_id = await mkstaff('owner', 'p3'); rev, _ = await mkstaff('reviewer', 'p3')
        slug = J(await own.post('/api/admin/catalog/exams', json={'name': 'BDX', 'short': 'BD', 'subjects': ['Physics'], 'color': 'rose'})).get('slug')
        sec = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Mock Tests', 'description': '', 'layout': 'list', 'kind': 'mocks'})).get('id')
        b = S.bucket_name()

        # ---- A. The check itself.
        a1 = S.probe(); a2 = S.probe(); names = check_posts(sb)
        check('A. two checks: both stores write and read back, with times', all(x['supabase']['ok'] and x['emergent']['ok'] and 'write_ms' in x['supabase'] and 'read_ms' in x['emergent'] for x in (a1, a2)), (a1, a2))
        check('A. every Supabase check uses a NEW file name (never the old fixed health/check.bin)', len(names) == 2 and names[0] != names[1] and all(S._CHECK.match(n) for n in names), names)
        check('A. the check file is removed after each check: nothing is left in Supabase', health_files(sb) == [] and deletes(sb) == 2, (health_files(sb), deletes(sb)))
        check('A. Emergent keeps ONE check file name (a file cannot be removed there)', sorted(k for k in H.STORE if k.startswith('jeelive/health/')) == ['jeelive/health/check.bin'], sorted(H.STORE)[:5])
        emergent = {k for k in H.STORE if not k.startswith('jeelive/health/')}
        sb.stale = True
        S.sb_put('health/TEST_same_name.bin', b'first', 'application/octet-stream'); S.sb_put('health/TEST_same_name.bin', b'second', 'application/octet-stream')
        got = S.sb_get(b, 'health/TEST_same_name.bin')
        check('A. control: ONE file name written twice can be read back stale (the old "Read back different bytes")', got == b'first', got)
        outs = [S.probe()['supabase'] for _ in range(5)]
        check('A. five checks in a row under that same condition: never "Read back different bytes"', all(o['ok'] and not o['error'] for o in outs), outs)
        sb.stale = False; sb.objects.pop(f'{b}/health/TEST_same_name.bin', None)
        before, refused = deletes(sb), 0
        for bad in (['health/check.bin'], ['jeelive/books/x/original.pdf'], ['health/../jeelive/a.bin'], [f'health/check-{int(time.time())}-zzzzzzzzzzzz.bin'], ['health/big-123-abcdefabcdef.bin'],
                    [names[0], 'tejas/reports/a.pdf'], [], [None], 'health/', [names[0] + '/x']):
            try:
                S._drop_checks(b, bad)
            except ValueError:
                refused += 1
        check('A. the check can remove ONLY its own check files: ten other names are refused before any request', refused == 10 and deletes(sb) == before, (refused, deletes(sb) - before))
        t = int(time.time())
        old = [f'health/check-{t - 7200}-{os.urandom(6).hex()}.bin', f'health/big-{t - 90000}-{os.urandom(6).hex()}.bin']
        new, book_file = f'health/check-{t - 30}-{os.urandom(6).hex()}.bin', f'{b}/jeelive/books/{uuid.uuid4()}/original.pdf'
        for n in old + [new, 'health/check.bin', 'health/TEST_other.txt']:
            sb.objects[f'{b}/{n}'] = b'x'
        sb.objects[book_file] = b'pdf'
        swept = S.sweep_checks()
        check('A. sweep: only check files older than an hour go; a fresh one, the old fixed file and any other file stay', swept == 2 and health_files(sb) == sorted([new, 'health/check.bin', 'health/TEST_other.txt'])
              and sb.objects.get(book_file) == b'pdf', (swept, health_files(sb)))
        for n in (f'{b}/{new}', f'{b}/health/check.bin', f'{b}/health/TEST_other.txt', book_file):
            sb.objects.pop(n, None)

        # ---- B. One record in the database.
        h = await health(own)
        check('B. first look: the small-file route and Emergent are checked and fine', h['mode'] == 'supabase' and h['supabase']['ok'] and h['supabase']['how'] == 'check' and h['emergent']['ok'] and h['checked_at'] > 0, h)
        check('B. the big-file route was never tried: the badge is YELLOW and says so (not green by default)', h['level'] == 'yellow' and h['big']['state'] == 'unknown' and any('jaancha nahi gaya' in x for x in h['reasons']),
              (h['level'], h['reasons']))
        pieces = sb.pieces()
        r = await own.post(BIG); t = J(r)
        check('B. "Badi file ka test": about 7 MB goes by the real piece route in 2 pieces, is read back, then removed', r.status_code == 200 and t['big_test']['ok'] and t['big_test']['size'] == S.BIG_TEST == 7 * 1024 * 1024
              and sb.pieces() - pieces == 2 and health_files(sb) == [], (r.status_code, t.get('big_test'), sb.pieces() - pieces, health_files(sb)))
        check('B. now GREEN, with its one reason line', t['level'] == 'green' and t['reasons'] == [SH.GREEN] and t['big']['state'] == 'ok' and t['big']['how'] == 'test', (t['level'], t['reasons'], t['big']))
        d = await rec()
        check('B. all of it is ONE record in the database (both routes, Emergent, timings, when it was checked)', d['small']['ok'] and d['big']['ok'] and d['emergent']['ok'] and d['checked_at'] and d.get('big_test_at')
              and len(d['readings']['supabase']) >= 1 and len(d['readings']['emergent']) >= 1, {k: d.get(k) for k in ('small', 'big', 'checked_at')})
        codes = [(await rev.get(HEALTH)).status_code, (await rev.post(RETRY)).status_code, (await rev.post(BIG)).status_code]
        check('B. a reviewer cannot read the status, re-check or run the big test', all(c in (401, 403) for c in codes), codes)
        text = json.dumps(t)
        check('B. the answer carries no storage path, upload address or key', not any(x in text for x in ('jeelive/', 'sb://', 'health/', 'sb_secret', 'resumable')), text[:300])
        t0 = time.time()
        await put({'small': {'ok': False, 'at': t0, 'how': 'check', 'error': 'Supabase connection failed: ConnectError', 'code': None, 'scope': 'away', 'said': '', 'bad_since': t0, 'waits': 0}, 'checked_at': t0})
        h = await health(own)
        check('B. another server wrote "Supabase does not answer": THIS server shows the same red, though its own memory says fine', h['mode'] == 'waiting' and h['level'] == 'red' and 'jawab nahi aaya' in h['reasons'][0]
              and S.supabase_on() and S.STATE['strikes'] == 0, (h['mode'], h['level'], h['reasons']))
        check('B. ...and it stays red while this server has no newer proof', await SH.watch_once() is False and (await health(own))['level'] == 'red')
        S.put_object('jeelive/written/TESTp3/a.png', b'\x89PNG a real file', 'image/png')
        woke = await SH.watch_once(); h = await health(own)
        check('B. this server then saves a real file: within one watch round the record is right again', woke is True and h['level'] == 'green' and h['supabase']['ok'] and h['supabase']['how'] == 'file', (woke, h['level'], h['supabase']))
        sb.down = True
        w = (await upload(own, cut_pdf('WAKE', long=True), 'TEST_wakes_by_other_server', section_id=sec))['id']; await finish(own, w)
        jb, bk = await job(w), await row(w)
        check('B. setup: Supabase away, a PDF waits, THIS server rests Supabase, the job notes when its wait began', jb['status'] == 'queued' and jb['next_run_at'] > time.time() and bk['payload'].get('storage_wait')
              and not S.supabase_on() and abs(jb.get('storage_wait_since', 0) - time.time()) < 30, ({k: jb.get(k) for k in ('status', 'storage_wait_since')}, S.supabase_on()))
        sb.down = False; cancel_kicks(); t1 = time.time() + .001
        await put({'small': {'ok': True, 'how': 'check', 'at': t1, 'write_ms': 80, 'read_ms': 40}, 'ok_at': t1, 'checked_at': t1})   # a good check on ANOTHER server
        await JOBS_COL.update_many({'status': 'queued', 'storage_waits': {'$gt': 0}}, {'$set': {'next_run_at': 0}})                 # ...and its wake-up of the waiting jobs
        kicks = len(JOBS._later)
        woke = await SH.watch_once()
        check("B. the other server's good check ends this server's rest and wakes its lane within one watch round (30 s)", woke is True and S.supabase_on() and S.STATE['strikes'] == 0 and len(JOBS._later) > kicks
              and SH.WATCH <= 30, (woke, S.supabase_on(), len(JOBS._later) - kicks))
        await pump(); bk, jb = await row(w), await job(w)
        check('B. ...and the PDF that waited is read; the job forgets its wait', bk['state'] in ('ready', 'attention_needed') and 'storage_wait' not in bk['payload'] and jb['status'] == 'done' and 'storage_wait_since' not in jb,
              (bk['state'], bk['payload'].get('storage_wait'), jb['status'], jb.get('storage_wait_since')))

        # ---- C. Colours and their reasons.
        sb.down = True; r = await again(own)
        check('C. RED: Supabase does not answer', r['level'] == 'red' and r['mode'] == 'waiting' and r['woke'] == 0 and 'Supabase abhi file nahi le raha' in r['reasons'][0] and r['supabase']['error']
              and r['supabase']['state'] == 'bad' and not S.supabase_on(), (r['level'], r['reasons']))
        sb.down = False; sb.block = (402, 'billing'); r = await again(own)
        check('C. RED: the project is blocked (billing): says what and where to look', r['level'] == 'red' and 'rok hai' in r['reasons'][0] and '(402)' in r['reasons'][0] and 'Billing' in r['reasons'][0], r['reasons'])
        sb.block = None; r = await again(own)
        check('C. Supabase back: GREEN again at once', r['level'] == 'green' and r['mode'] == 'supabase' and S.supabase_on(), (r['level'], r['reasons']))
        SH.SLOW_MS = -1; h = await health(own); SH.SLOW_MS = slow_ms
        check('C. YELLOW: Supabase answers slowly', h['level'] == 'yellow' and h['mode'] == 'slow' and 'dheema' in h['reasons'][0], (h['level'], h['reasons']))
        a = (await upload(own, cut_pdf('PICA', long=True), 'TEST_picture_stuck', section_id=sec))['id']; await finish(own, a)
        mk = await BM.find_one({'book_id': a}); mid = mk['_id']
        sb.returned = [f'/books/{a}/crops/']; await live(own, mid)
        h = await health(own)
        check('C. YELLOW: one picture is stuck in Supabase; both routes still show working and Supabase is not rested', h['level'] == 'yellow' and h['mode'] == 'supabase' and h['held']['stuck'] == 1
              and any('atki hai' in x for x in h['reasons']) and h['supabase']['ok'] and h['big']['state'] == 'ok' and S.supabase_on(), (h['level'], h['held'], h['reasons']))
        sb.returned = []
        r = await own.post(f'/api/admin/books/{a}/control', json={'revision': J(await own.get(f'/api/admin/books/{a}'))['revision'], 'action': 'retry'}); await pump()
        mk, h = await BM.find_one({'_id': mid}), await health(own)
        check('C. the picture goes through on Dobara chalao: GREEN again', r.status_code == 200 and mk['state'] in ('published', 'scheduled') and h['level'] == 'green' and h['held'] == {'stuck': 0, 'waiting': 0, 'hung': 0},
              (r.status_code, mk['state'], h['level'], h['held'], h['reasons']))
        q = await shown(own, sec, 'LATE', 'TEST_waits_long', {'since': time.time() - 120, 'kind': 'away', 'code': None, 'reason': 'Supabase se jawab nahi aaya', 'next': ''})
        h2 = await health(own)
        await DB.tejas_books.update_one({'_id': q}, {'$set': {'payload.storage_wait.since': time.time() - 601}})
        h10 = await health(own)
        check('C. a file that waits 2 minutes does not change the colour; from 10 minutes the badge is YELLOW', h2['level'] == 'green' and h2['held']['waiting'] == 0 and h10['level'] == 'yellow' and h10['held']['waiting'] == 1
              and any('10 minute' in x for x in h10['reasons']), (h2['level'], h10['level'], h10['held'], h10['reasons']))
        await gone(q)
        await DB.tejas_imports.insert_one({'id': 'TESTimp236', 'title': 'TEST', 'status': 'queued', 'storage_wait': time.time(), 'storage_wait_since': time.time() - 700, 'storage_waits': 4, 'created_at': time.time()})
        await JOBS_COL.insert_one({'id': 'TESTjob236', 'kind': 'report', 'status': 'queued', 'storage_waits': 5, 'storage_wait_since': time.time() - 700, 'next_run_at': time.time() + 250, 'created_at': time.time(),
                                   'user_id': owner_id, 'set_id': 'x', 'payload': {}})
        h = await health(own)
        await DB.tejas_imports.delete_one({'id': 'TESTimp236'}); await JOBS_COL.delete_one({'id': 'TESTjob236'})
        check('C. a paper import and a report that have waited 10 minutes for storage are counted too', h['held']['waiting'] == 2 and h['level'] == 'yellow', (h['held'], h['level']))
        q = await shown(own, sec, 'HANG', 'TEST_hung_pdf', {'since': time.time() - 60, 'kind': 'hang', 'code': None, 'stuck': True, 'reason': 'kaam 3 baar latak gaya', 'next': 'Har ghante'}, state='reading')
        h = await health(own); await gone(q)
        check('C. YELLOW: a PDF stopped because its own work went silent; said apart, not blamed on storage', h['level'] == 'yellow' and h['held'] == {'stuck': 0, 'waiting': 0, 'hung': 1}
              and any('storage ki galti nahi' in x for x in h['reasons']), (h['held'], h['reasons']))
        sb.tus_down = True; ups = len(sb.uploads)
        r = await own.post(BIG); t = J(r)
        check('C. YELLOW: the big-file test fails while pictures still go: says why in plain words', r.status_code == 200 and t['big_test']['ok'] is False and 'tukde' in t['big_test']['reason'] and t['level'] == 'yellow'
              and t['mode'] == 'supabase' and t['big']['state'] == 'bad' and any('Badi file (PDF) ka raasta' in x for x in t['reasons']), (t.get('big_test'), t['level'], t['reasons']))
        check('C. ...Supabase is NOT rested for anyone, the half upload is ended, no test file is left', S.supabase_on() and S.STATE['strikes'] == 0 and len(sb.uploads) == ups and health_files(sb) == [],
              (S.STATE['strikes'], len(sb.uploads) - ups, health_files(sb)))
        sb.tus_down = False
        g = (await upload(own, big_pdf('PROOF'), 'TEST_real_big_pdf', section_id=sec))['id']; await finish(own, g)
        await SH.flush(); d, h = await rec(), await health(own)
        check('C. a real PDF saved by the piece route is proof too: the big-file line is fine again without a test', d['big']['ok'] and d['big']['how'] == 'pdf' and d['big']['via'] == 'tus' and h['big']['state'] == 'ok'
              and h['level'] == 'green', (d['big'], h['level'], h['reasons']))
        sb.tus_down = True; lump = os.urandom(S.TUS_CHUNK + 1000)
        S.put_object('TEST_p236/one.pdf', lump, 'application/pdf'); await SH.flush(); d = await rec()
        check('C. ...and so is a PDF that went in one request after the piece route failed twice', d['big']['ok'] and d['big']['via'] == 'one' and sb.objects.get(f'{b}/TEST_p236/one.pdf') == lump, d['big'])
        sb.one_request_code = 400; err = None
        try:
            S.put_object('TEST_p236/two.pdf', lump, 'application/pdf')
        except S.StorageError as exc:
            err = exc
        await SH.flush(); d, h = await rec(), await health(own)
        check('C. YELLOW: a real PDF is returned on BOTH big-file routes: the big-file line says fail, Supabase is not rested', isinstance(err, S.StorageStuck) and d['big']['ok'] is False and d['big']['how'] == 'pdf'
              and h['big']['state'] == 'bad' and h['level'] == 'yellow' and h['mode'] == 'supabase' and S.supabase_on(), (type(err).__name__, d['big'], h['level']))
        sb.tus_down = False; sb.one_request_code = None
        t = J(await own.post(BIG))
        check('C. the route works again: one test turns the line back to fine', t['big_test']['ok'] and t['level'] == 'green', (t.get('big_test'), t['level'], t['reasons']))

        def broken(method, path, data=None, content_type=None):
            raise S.StorageError('Private storage unavailable (503). Retry later or check account storage permissions and quota.')
        S.request = broken; r = await again(own); S.request = real_request
        check('C. YELLOW, not red: Emergent (the fallback) does not answer while Supabase works', r['level'] == 'yellow' and r['mode'] == 'supabase' and not r['emergent']['ok']
              and any('Emergent (fallback)' in x for x in r['reasons']), (r['level'], r['reasons']))
        r = await again(own)
        sb.small_code = (400, 'TEST: a bucket rule refuses the check file'); f = await again(own); sb.small_code = None
        check('C. YELLOW: only the check file is returned while Supabase answers: nothing is rested, it is not called "away"', r['level'] == 'green' and f['level'] == 'yellow' and f['mode'] == 'supabase'
              and f['supabase']['state'] == 'warn' and f['backup']['alert'] is False and S.supabase_on() and S.STATE['strikes'] == 0, (r['level'], f['level'], f['reasons']))
        r = await again(own)
        sb.down = True; await again(own)
        await put({'small.bad_since': time.time() - 601})
        h = await health(own)
        sb.down = False; r = await again(own)
        check('C. Supabase away for 10 minutes: the loud alert line is on; off again when it is back', h['backup']['alert'] is True and h['level'] == 'red' and r['backup']['alert'] is False and r['level'] == 'green',
              (h['backup'], r['backup'], r['level']))

        # ---- D. The last 20 failures and the last 20 timings.
        errs = J(await own.get(MACHINE))['storage_errors']
        line = next((e for e in errs if e['file'] == 'TEST_picture_stuck · picture'), None)
        check('D. Machine: the stuck picture is in the list: when, which file, which store, which route, why', bool(line) and line['store'] == 'supabase' and line['route'] == 'small' and '(400)' in line['reason']
              and line['at'] > 0 and line['n'] >= 1, errs[:5])
        big_line = next((e for e in errs if e['file'] == SH.BIG_FILE), None); orig = next((e for e in errs if e['file'] == 'TEST_wakes_by_other_server · original PDF'), None)
        check('D. the failed big-file test and the PDF that had to wait are listed too, each with its route', bool(big_line) and big_line['route'] == 'big' and bool(orig) and orig['route'] == 'small' and '(503)' in orig['reason'],
              [(e['file'], e['route'], e['reason']) for e in errs])
        check('D. the check files that failed are listed as "Jaanch file", for Supabase and for Emergent', {e['store'] for e in errs if e['file'] == SH.CHECK_FILE} == {'supabase', 'emergent'}, [(e['file'], e['store']) for e in errs])
        text = json.dumps(errs)
        check('D. no storage path, id or key in the list', not any(x in text for x in ('jeelive/', 'sb://', 'crops', a, w, 'TEST_p236')) and all('k' not in e for e in errs), text[:300])
        S._recent.clear()
        for i in range(25):
            S._note_error(f'jeelive/written/TEST{i:02d}/a.png', 'supabase', 'small', S._error(f'TEST reason {i:02d}', 400), 400, 'stuck')
        await SH.flush(); errs = await SH.errors()
        check('D. only the last 20 are kept, newest first', len(errs) == 20 and [e['reason'] for e in errs[:3]] == ['TEST reason 24', 'TEST reason 23', 'TEST reason 22'] and errs[-1]['reason'] == 'TEST reason 05'
              and all(e['file'] == 'Likhe hue sawaal ki picture' for e in errs), [(e['file'], e['reason']) for e in errs[:3]])
        for name in ('a', 'b', 'a', 'b', 'a', 'b'):
            S._recent.clear(); S._note_error(f'jeelive/written/TESTsame/{name}.png', 'supabase', 'small', S._error('TEST same', 400), 400, 'stuck')
        await SH.flush(); errs = await SH.errors()
        check('D. the same failure of the files of one upload is ONE line with a count (it cannot push the others out)', errs[0]['reason'] == 'TEST same' and errs[0]['n'] == 6 and len(errs) == 20
              and sum(1 for e in errs if e['reason'] == 'TEST same') == 1, (errs[0], len(errs)))
        S._recent.clear(); n = len(S.EVENTS)
        for _ in range(5):
            S._note_error('jeelive/written/TESTagain/a.png', 'supabase', 'read', S.StorageError('Supabase file unavailable (404). Retry later.'))
        await SH.flush(); e0 = (await SH.errors())[0]
        check('D. one broken file asked for again and again is noted once a minute; a missing file is said plainly', len(S.EVENTS) == 0 and n == 0 and e0['n'] == 1 and e0['route'] == 'read'
              and e0['reason'] == 'Supabase mein yeh file nahi mili (404)', (n, e0))

        async def writer(i):
            S._note('error', path=f'jeelive/written/TESTrace{i:02d}/a.png', store='supabase', route='small', code=400, scope='stuck', reason=f'TEST race {i:02d}', raw='')
            await SH.flush()

        async def other_server():
            for _ in range(60):
                await put({'TEST_bump': time.time()}); await asyncio.sleep(0)
        await asyncio.gather(other_server(), *(writer(i) for i in range(12)))
        for _ in range(6):
            await SH.flush()
        errs = await SH.errors()
        race = sorted(e['reason'] for e in errs if e['reason'].startswith('TEST race'))
        check('D. 12 notes written while another server changes the record 60 times: no line is lost, none is doubled', race == [f'TEST race {i:02d}' for i in range(12)] and len(S.EVENTS) == 0
              and all(e['n'] == 1 for e in errs if e['reason'].startswith('TEST race')) and len(errs) == 20, (race, len(S.EVENTS)))
        for _ in range(23):
            await SH.check()
        d, h = await rec(), await health(own)
        sp = h['speed']
        check('D. the last 20 check timings of each store are kept; the badge gives real numbers for both', len(d['readings']['supabase']) == 20 and len(d['readings']['emergent']) == 20 and sp['supabase']['n'] == 20
              and sp['emergent']['n'] == 20 and sp['supabase']['min_ms'] <= sp['supabase']['median_ms'] <= sp['supabase']['max_ms'], sp)

        # ---- E. The big-file test runs by itself when it is due.
        pieces = sb.pieces(); await SH.routine()
        check('E. outside a started server the scheduled check does nothing', sb.pieces() == pieces and SH._mem['loop'] is None)
        SH._mem['loop'] = asyncio.get_running_loop()
        await put({'big': {}, 'big_test_at': 0})
        await SH.routine(); d = await rec()
        check('E. the big-file route was never proven: the scheduled check tests it by itself', sb.pieces() - pieces == 2 and d['big']['ok'] and d['big']['how'] == 'test' and health_files(sb) == [], (sb.pieces() - pieces, d['big']))
        pieces = sb.pieces(); await SH.routine()
        check('E. ...and not again at the next check while it is proven', sb.pieces() == pieces, sb.pieces() - pieces)
        await put({'big.at': time.time() - 86500}); await SH.routine()
        check('E. proven more than 24 hours ago: tested again (once a day)', sb.pieces() - pieces == 2, sb.pieces() - pieces)
        pieces = sb.pieces()
        await put({'big.ok': False, 'big.scope': 'file', 'big_test_at': time.time() - 100}); await SH.routine(); soon = sb.pieces() - pieces
        await put({'big.ok': False, 'big.scope': 'file', 'big_test_at': time.time() - 901}); await SH.routine(); later = sb.pieces() - pieces
        check('E. the route failed: tested again by itself, at most every 15 minutes', soon == 0 and later == 2 and (await rec())['big']['ok'], (soon, later))
        pieces = sb.pieces()
        q = await shown(own, sec, 'BIGW', 'TEST_pdf_waits_on_big_route', {'since': time.time() - 30, 'kind': 'file', 'code': 500, 'reason': 'x', 'next': ''}, transfer=True)
        await put({'big_test_at': time.time() - 901}); await SH.routine(); await gone(q)
        check('E. a PDF waits on the big-file route: the route is tested by itself', sb.pieces() - pieces == 2, sb.pieces() - pieces)
        pieces = sb.pieces()
        await put({'big': {}, 'big_test_at': 0, 'small.ok': False, 'small.scope': 'away'}); await SH.routine()
        check('E. never while Supabase itself does not answer', sb.pieces() == pieces, sb.pieces() - pieces)
        await put({'checked_at': time.time() - 700}); await SH.routine(); d = await rec()
        check('E. nobody looked for 10 minutes: the scheduled check checks the stores (the record does not go stale)', time.time() - d['checked_at'] < 30 and d['small']['ok'] and d['big'].get('ok'), (d['checked_at'], d['small'], d['big']))
        left = f'health/check-{int(time.time()) - 7200}-{os.urandom(6).hex()}.bin'; sb.objects[f'{b}/{left}'] = b'x'
        await put({'swept_at': time.time() - 90000}); await SH.routine(); d = await rec()
        check('E. once a day check files left behind are swept', health_files(sb) == [] and time.time() - d['swept_at'] < 30, (health_files(sb), d.get('swept_at')))
        await put({'big_lease': time.time() + 100})
        r = await own.post(BIG); h = await health(own)
        await put({'big_lease': 0})
        check('E. a big-file test is already running (on any server): a second one is refused, the badge says it is running', r.status_code == 409 and h['big']['running'] is True, (r.status_code, h['big']))
        url = os.environ.pop('SUPABASE_URL')
        r = await own.post(BIG); h = J(await own.get(HEALTH + '?fresh=true'))
        os.environ['SUPABASE_URL'] = url
        check('E. without Supabase set up: the test is refused plainly; the badge is yellow "Emergent", not red', r.status_code == 409 and h['mode'] == 'emergent' and h['level'] == 'yellow' and h['supabase']['configured'] is False,
              (r.status_code, h['mode'], h['level']))

        # ---- F. When a wait began is kept (so "10 minutes" is counted from the first wait, not the last try).
        from tejas import imports as IMP
        iid, src = str(uuid.uuid4()), cut_pdf('IMP')
        sb.objects[f'{b}/tejas/imports/TESTsrc.pdf'] = src
        await DB.tejas_imports.insert_one({'id': iid, 'title': 'TEST_IMP', 'format': 'pdf', 'fingerprint': 'x', 'status': 'queued', 'created_at': time.time(), 'created_by': 'owner', 'questions': [], 'issues': [],
                                           'sources': [{'id': 's1', 'kind': 'questions', 'name': 'q.pdf', 'sha256': hashlib.sha256(src).hexdigest(), 'size': len(src), 'path': f'sb://{b}/tejas/imports/TESTsrc.pdf'}]})
        sb.down = True; cancel_kicks(); S._source_cache = S.ByteCache(64 * 1024 * 1024)
        await IMP.process_import(iid); first = (await DB.tejas_imports.find_one({'id': iid})).get('storage_wait_since')
        cancel_kicks(); await asyncio.sleep(.05); await IMP.process_import(iid); two = await DB.tejas_imports.find_one({'id': iid})
        check('F. an import that waits for Supabase notes when its wait BEGAN and keeps that time across tries', bool(first) and abs(first - time.time()) < 30 and two.get('storage_wait_since') == first and two.get('storage_waits') == 2
              and two['storage_wait'] > first, (first, {k: two.get(k) for k in ('status', 'storage_wait_since', 'storage_waits')}))
        sb.down = False; cancel_kicks(); await IMP.process_import(iid); three = await DB.tejas_imports.find_one({'id': iid})
        check('F. ...and forgets it once it is through', three['status'] != 'queued' and 'storage_wait_since' not in three, (three['status'], three.get('storage_wait_since')))
        check('nothing at all went to Emergent storage', {k for k in H.STORE if not k.startswith('jeelive/health/')} == emergent, {k for k in H.STORE if not k.startswith('jeelive/health/')} - emergent)
    finally:
        S.request, SH.SLOW_MS, SH._mem['loop'] = real_request, slow_ms, None
        cancel_kicks()
        late = SH._running['flush']
        if late and not late.done():
            await asyncio.gather(late, return_exceptions=True)
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')


if __name__ == '__main__':
    asyncio.run(main())
