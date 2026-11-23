"""TEST-ONLY iteration 216 (policy updated in 224): Supabase only for new files. When Supabase cannot take a file the write
waits (StorageWaiting) and NOTHING goes to Emergent; old Emergent files still read. Big files carry on from Supabase's own offset.
No network, no real keys, no database. Run: cd /app/backend && python tests/storage_dual216.py
"""
import base64, importlib.util, json, os, sys, threading, time, uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock
from urllib.parse import unquote
import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.update(SUPABASE_URL='https://supabase.com/dashboard/project/abcdefghijklmnopqrst', SUPABASE_SECRET_KEY='sb_secret_test', FRONTEND_URL='https://preview-x.example.com')
spec = importlib.util.spec_from_file_location('dual216', str(ROOT / 'tejas_storage.py'))
S = importlib.util.module_from_spec(spec); spec.loader.exec_module(S)
REAL_CLIENT = S._client
RESULTS = []


def check(name, ok, detail=''):
    RESULTS.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:400]), flush=True)


class FakeSupabase:
    def __init__(self):
        self.objects, self.buckets, self.uploads, self.calls = {}, {}, {}, []
        self.down = False; self.fail_next = 0; self.patch_fail = 0; self.need_bearer = False; self.cut_after = None; self.lock = threading.Lock()

    def __call__(self, req):
        with self.lock:
            self.calls.append((req.method, req.url.host, req.url.path))
        if self.down:
            return httpx.Response(503, text='Service Unavailable')
        if req.headers.get('apikey') != 'sb_secret_test':
            return httpx.Response(401, json={'message': 'Invalid API key'})
        if self.need_bearer and req.headers.get('authorization') != 'Bearer sb_secret_test':
            return httpx.Response(400, json={'statusCode': '403', 'error': 'Unauthorized', 'message': 'headers must have required property authorization'})
        p = unquote(req.url.path)
        if p.startswith('/storage/v1/bucket'):
            if req.method == 'GET':
                name = p.rsplit('/', 1)[1]
                return httpx.Response(200, json=self.buckets[name]) if name in self.buckets else httpx.Response(400, json={'error': 'Bucket not found'})
            b = json.loads(req.content); self.buckets[b['id']] = b
            return httpx.Response(200, json={'name': b['id']})
        if p.startswith('/storage/v1/object/authenticated/'):
            key = p[len('/storage/v1/object/authenticated/'):]
            return httpx.Response(200, content=self.objects[key]) if key in self.objects else httpx.Response(400, json={'error': 'not_found'})
        if p.startswith('/storage/v1/object/') and req.method == 'POST':
            if self.fail_next:
                self.fail_next -= 1; return httpx.Response(500, text='boom')
            key = p[len('/storage/v1/object/'):]
            if key in self.objects and req.headers.get('x-upsert') != 'true':
                return httpx.Response(400, json={'error': 'Duplicate'})
            self.objects[key] = req.content
            return httpx.Response(200, json={'Key': key})
        if p == '/storage/v1/upload/resumable' and req.method == 'POST':
            meta = dict(x.split(' ') for x in req.headers['upload-metadata'].split(','))
            meta = {k: base64.b64decode(v).decode() for k, v in meta.items()}
            uid = uuid.uuid4().hex
            self.uploads[uid] = {'len': int(req.headers['upload-length']), 'key': meta['bucketName'] + '/' + meta['objectName'], 'data': b''}
            return httpx.Response(201, headers={'Location': f'https://{req.url.host}/storage/v1/upload/resumable/{uid}', 'Tus-Resumable': '1.0.0'})
        if p.startswith('/storage/v1/upload/resumable/'):
            u = self.uploads[p.rsplit('/', 1)[1]]
            if req.method == 'HEAD':
                return httpx.Response(200, headers={'Upload-Offset': str(len(u['data'])), 'Upload-Length': str(u['len'])})
            if self.patch_fail:
                self.patch_fail -= 1
                u['data'] += req.content[:1000]   # a piece that broke part way: Supabase kept only some of it
                return httpx.Response(500, text='piece lost')
            if int(req.headers['upload-offset']) != len(u['data']):
                return httpx.Response(409, text='offset mismatch')
            if len(req.content) != min(S.TUS_CHUNK, u['len'] - len(u['data'])):
                return httpx.Response(400, text='wrong piece size')
            u['data'] += req.content
            if self.cut_after is not None:
                self.cut_after -= 1
                self.down = self.cut_after <= 0   # Supabase goes away after this many pieces
            if len(u['data']) == u['len']:
                self.objects[u['key']] = u['data']
            return httpx.Response(204, headers={'Upload-Offset': str(len(u['data']))})
        return httpx.Response(404, text='unknown route ' + p)


class FakeEmergent:
    def __init__(self):
        self.objects, self.down, self.calls = {}, False, 0

    def request(self, method, path, data=None, content_type=None, tries=4):
        self.calls += 1
        if self.down:
            raise S.StorageError('Private storage unavailable (500). Retry later or check account storage permissions and quota.')
        if method == 'PUT':
            self.objects[path] = data
            return type('R', (), {'json': lambda self_: {'path': path}})()
        if path not in self.objects:
            raise S.StorageError('Private storage unavailable (404).')
        return type('R', (), {'content': self.objects[path]})()


def reset(fake_sb, fake_em):
    S.STATE.update(down_until=0.0, strikes=0, last_error='', auth=None, bucket=None, writes={'supabase': 0, 'emergent': 0}, failovers=0, last_failover=None)
    S._source_cache = S.ByteCache(64 * 1024 * 1024)
    client = httpx.Client(transport=httpx.MockTransport(fake_sb))
    S._client = lambda: client   # every worker thread talks to the fake


def main():
    sb, em = FakeSupabase(), FakeEmergent()
    with mock.patch.object(S, 'request', em.request):
        reset(sb, em)
        check('dashboard link accepted as project URL', S.project_url() == 'https://abcdefghijklmnopqrst.supabase.co', S.project_url())
        check('bucket named after this app (preview and live never share)', S.bucket_name() == 'jeelive-preview-x-example-com', S.bucket_name())
        # 1. Normal: small file to Supabase, read back exact.
        png = os.urandom(70_000)
        t = time.time(); ref = S.put_object('jeelive/books/b1/crops/f1.png', png, 'image/png'); took = time.time() - t
        check('new file goes to Supabase first (ref names the store)', ref == 'sb://jeelive-preview-x-example-com/jeelive/books/b1/crops/f1.png', ref)
        check('bucket made private on first use', sb.buckets.get('jeelive-preview-x-example-com', {}).get('public') is False, sb.buckets)
        check('Emergent not touched when Supabase is fine', em.calls == 0, em.calls)
        S._source_cache = S.ByteCache(64 * 1024 * 1024)
        check('read back from Supabase: bytes exact', S.get_object(ref) == png)
        check('small write is quick on a healthy store', took < 0.5, took)
        # 2. Big file: resumable 6 MB pieces, one piece breaks part way and is resumed from where Supabase stands.
        big = os.urandom(20 * 1024 * 1024 + 12345)
        sb.patch_fail = 1
        ref2 = S.put_object('jeelive/books/b1/original.pdf', big, 'application/pdf')
        S._source_cache = S.ByteCache(64 * 1024 * 1024)
        check('20 MB PDF saved in Supabase in resumable pieces, a broken piece resumed', ref2.startswith('sb://') and S.get_object(ref2) == big, (ref2, len(sb.objects.get('jeelive-preview-x-example-com/jeelive/books/b1/original.pdf', b''))))
        check('big file used the fast storage host', any(h == 'abcdefghijklmnopqrst.storage.supabase.co' for _, h, _ in sb.calls))
        # 3. A Supabase hiccup (one 500) is retried, still Supabase.
        sb.fail_next = 1
        ref3 = S.put_object('jeelive/books/b1/crops/f2.png', png, 'image/png')
        check('one 500 from Supabase: retried, file still in Supabase', ref3.startswith('sb://'), ref3)
        # 4. Supabase down: the file WAITS (StorageWaiting), Emergent is never written; next writes skip Supabase while it rests.
        sb.down = True; e0 = em.calls
        t = time.time()
        try:
            S.put_object('jeelive/books/b1/crops/f3.png', png, 'image/png'); waited = False
        except S.StorageWaiting as exc:
            waited = 'Supabase' in str(exc)
        took = time.time() - t
        check('Supabase down: the file waits (StorageWaiting), clear Hinglish reason', waited)
        check('Supabase down: NOTHING written to Emergent', em.calls == e0 and not em.objects, (em.calls, list(em.objects)))
        check('wait decided within 1.5 s', took < 1.5, took)
        n1 = len(sb.calls); waits = 0
        t = time.time()
        for i in range(20):
            try:
                S.put_object(f'jeelive/books/b1/crops/g{i}.png', png, 'image/png')
            except S.StorageWaiting:
                waits += 1
        took = time.time() - t
        check('while Supabase rests, 20 files wait at once (no Supabase call, no Emergent)', waits == 20 and len(sb.calls) == n1 and em.calls == e0 and took < 0.5, (waits, len(sb.calls) - n1, em.calls - e0, took))
        check('wait recorded for the badge', S.STATE['failovers'] >= 1 and S.STATE['last_failover'] and 'Supabase' in S.STATE['last_failover']['reason'], S.STATE['last_failover'])
        check('a wait is still a StorageError (old callers keep working)', issubclass(S.StorageWaiting, S.StorageError))
        S._source_cache = S.ByteCache(64 * 1024 * 1024)
        try:
            S.get_object(ref); read_wait = False
        except S.StorageWaiting:
            read_wait = True
        check('Supabase down: reading a Supabase file also waits (never searches Emergent)', read_wait and em.calls == e0)
        # 5. Supabase back: after its rest, new files go to Supabase again.
        sb.down = False; S.STATE['down_until'] = 0.0
        ref5 = S.put_object('jeelive/books/b1/crops/f4.png', png, 'image/png')
        check('Supabase back: new files go to Supabase again', ref5.startswith('sb://'), ref5)
        # 6. Both down: still a wait for Supabase (Emergent is not even asked).
        sb.down = True; em.down = True; S.STATE['down_until'] = 0.0; e0 = em.calls
        try:
            S.put_object('jeelive/books/b1/crops/f5.png', png, 'image/png'); ok = False
        except S.StorageWaiting as exc:
            ok = 'supabase' in str(exc).lower()
        check('both stores down: the file waits for Supabase, Emergent not asked', ok and em.calls == e0)
        sb.down = False; em.down = False; S.STATE['down_until'] = 0.0
        # 7. Old files (saved before Supabase) read from Emergent only.
        em.objects['tejas/sources/old/x.pdf'] = b'%PDF-old'; n = len(sb.calls)
        check('old plain path: read from Emergent, Supabase not asked', S.get_object('tejas/sources/old/x.pdf') == b'%PDF-old' and len(sb.calls) == n)
        # 8. Not set up: everything goes to Emergent.
        with mock.patch.dict(os.environ, {'SUPABASE_SECRET_KEY': 'https://supabase.com/dashboard/project/abcdefghijklmnopqrst'}):
            check('a link saved as the key counts as not set up', not S.configured())
            check('not set up: Emergent takes new files', not S.put_object('jeelive/x/y.png', png, 'image/png').startswith('sb://'))
        # 9. A new secret key that Supabase wants in Authorization too: found once, then used.
        reset(sb, em); sb.need_bearer = True
        ref9 = S.put_object('jeelive/books/b2/crops/a.png', png, 'image/png')
        check('key style found automatically (Authorization added once asked)', ref9.startswith('sb://') and S.STATE['auth'] == 'bearer', (ref9, S.STATE['auth']))
        sb.need_bearer = False
        # 10. Many at once: 300 pictures from 16 threads, every one saved once and readable.
        reset(sb, em); pics = {f'jeelive/books/b3/crops/p{i}.png': os.urandom(3000 + i) for i in range(300)}
        t = time.time()
        with ThreadPoolExecutor(16) as ex:
            out = dict(zip(pics, ex.map(lambda k: S.put_object(k, pics[k], 'image/png'), pics)))
        took = time.time() - t
        S._source_cache = S.ByteCache(64 * 1024 * 1024)
        check('300 pictures from 16 threads: all in Supabase, all exact', all(r.startswith('sb://') for r in out.values()) and all(S.get_object(r) == pics[k] for k, r in out.items()), took)
        # 11. Health check.
        reset(sb, em); h = S.probe()
        check('health: both stores write+read ok with times', h['supabase']['ok'] and h['emergent']['ok'] and 'write_ms' in h['supabase'], h)
        sb.down = True; h = S.probe()
        check('health: Supabase down shows its reason and rests it', not h['supabase']['ok'] and h['emergent']['ok'] and not S.supabase_on(), h)
        check('health: a failed check alone is not counted as a file handed to Emergent', S.STATE['failovers'] == 0 and S.STATE['last_failover'] is None, S.STATE['failovers'])
        sb.down = False
        # 12. Supabase accepts the connection then hangs: no retry of the write, the file waits at once (nothing in Emergent).
        reset(sb, em); S.STATE['bucket'] = S.bucket_name(); hangs = {'n': 0}; e0 = em.calls

        def hang(req):
            hangs['n'] += 1
            raise httpx.ReadTimeout('silent', request=req)
        hung = httpx.Client(transport=httpx.MockTransport(hang)); S._client = lambda: hung
        t = time.time()
        try:
            S.put_object('jeelive/books/b9/crops/h.png', png, 'image/png'); waited = False
        except S.StorageWaiting:
            waited = True
        took = time.time() - t
        check('hanging Supabase: one try only, the file waits, counted, Emergent untouched', waited and hangs['n'] == 1 and took < 1 and S.STATE['failovers'] == 1 and em.calls == e0, (waited, hangs, took))
        S._local.sb = None
        check('20 s read limit on real Supabase calls', REAL_CLIENT().timeout.read == 20.0, REAL_CLIENT().timeout)
        # 13. A big PDF cut off part way by Supabase carries on from Supabase's own offset when it is back (no restart from 0).
        reset(sb, em); big = os.urandom(20 * 1024 * 1024 + 12345); key = 'jeelive/books/b7/original.pdf'; seen = []
        sb.cut_after = 2; e0, k0 = em.calls, set(em.objects)
        with mock.patch.object(S.time, 'sleep', lambda s: None):
            try:
                S.put_object(key, big, 'application/pdf', None, seen.append); waited = False
            except S.StorageWaiting:
                waited = True
        saved = seen[-1] if seen else {}
        check('Supabase gone after 2 pieces: the PDF waits, its place is reported for saving', waited and saved.get('sent') == 2 * S.TUS_CHUNK and saved.get('url'), saved)
        check('cut-off PDF: nothing written to Emergent', em.calls == e0 and set(em.objects) == k0, em.calls - e0)
        sb.down = False; sb.cut_after = None; S.STATE['down_until'] = 0.0
        starts = sum(1 for m, _, p in sb.calls if m == 'POST' and p.endswith('/upload/resumable')); patches = sum(1 for m, _, _ in sb.calls if m == 'PATCH')
        again = []
        ref13 = S.put_object(key, big, 'application/pdf', saved, again.append)
        S._source_cache = S.ByteCache(64 * 1024 * 1024)
        new_starts = sum(1 for m, _, p in sb.calls if m == 'POST' and p.endswith('/upload/resumable')) - starts
        new_patches = sum(1 for m, _, _ in sb.calls if m == 'PATCH') - patches
        check('Supabase back: the PDF carries on from piece 3 (same upload, only the 2 missing pieces sent)', again and again[0]['sent'] == 2 * S.TUS_CHUNK and new_starts == 0 and new_patches == 2, (again[:1], new_starts, new_patches))
        check('carried-on PDF is byte-exact in Supabase', ref13.startswith('sb://') and S.get_object(ref13) == big)
        old = {**saved, 'started': time.time() - 21 * 3600}
        n0 = sum(1 for m, _, p in sb.calls if m == 'POST' and p.endswith('/upload/resumable'))
        S.put_object(key, big, 'application/pdf', old, None)
        check('a saved place older than 20 h is not trusted: a fresh upload starts', sum(1 for m, _, p in sb.calls if m == 'POST' and p.endswith('/upload/resumable')) == n0 + 1)
        S.STATE.update(down_until=0.0, strikes=0)
        with mock.patch.dict(os.environ, {'SUPABASE_SECRET_KEY': ''}):
            check('Supabase not set up at all: Emergent still takes new files (unchanged)', not S.configured() and not S.put_object('jeelive/x/z.png', png, 'image/png').startswith('sb://'))
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')


if __name__ == '__main__':
    main()
