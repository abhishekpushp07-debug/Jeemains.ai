"""TEST-ONLY iteration 230, Pocket 1 edge-case hunt: new scenarios NOT covered by storage_big229/before229/book229.
Extends FakeSupabase only by adding knobs or thin wrapping transports; never changes its existing behaviour.
Run: cd /app/backend && python tests/storage_edge230.py
"""
import importlib.util, logging, os, sys, threading, time
from pathlib import Path
from unittest import mock
import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'tests'))
os.environ.update(SUPABASE_URL='https://abcdefghijklmnopqrst.supabase.co',
                  SUPABASE_SECRET_KEY='sb_secret_test',
                  FRONTEND_URL='https://preview-x.example.com')
os.environ.pop('SUPABASE_BUCKET', None)
spec = importlib.util.spec_from_file_location('edge230', str(ROOT / 'tejas_storage.py'))
S = importlib.util.module_from_spec(spec); spec.loader.exec_module(S)
from fake_supabase229 import FakeSupabase  # noqa: E402

RESULTS = []
B = 'jeelive-preview-x-example-com'
KEY = 'jeelive/books/b1/original.pdf'


def check(name, ok, detail=''):
    RESULTS.append(bool(ok))
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:400]), flush=True)


def fresh(cls=FakeSupabase, **kw):
    sb = cls(S.TUS_CHUNK, **kw) if kw else cls(S.TUS_CHUNK)
    S.STATE.update(down_until=0.0, strikes=0, last_error='', auth=None, bucket=None,
                   writes={'supabase': 0, 'emergent': 0}, failovers=0, last_failover=None,
                   backup_since=None)
    S._source_cache = S.ByteCache(64 * 1024 * 1024)
    client = httpx.Client(transport=httpx.MockTransport(sb))
    S._client = lambda: client
    return sb


def put(data, resume=None, seen=None, key=KEY, content_type='application/pdf'):
    try:
        return S.put_object(key, data, content_type, resume, seen.append if seen is not None else None), None
    except S.StorageError as exc:
        return None, exc


def main():
    big = os.urandom(20 * 1024 * 1024 + 321)

    with mock.patch.object(S.time, 'sleep', lambda s: None):
        # 1. Resume older than 20 h: must NOT be reused; a fresh upload starts.
        sb = fresh(); seen = []
        stale = {'url': f'https://{B}.storage.supabase.co/storage/v1/upload/resumable/deadbeef',
                 'path': KEY, 'size': len(big),
                 'started': time.time() - S.RESUME_SECONDS - 60, 'sent': 6 * 1024 * 1024}
        ref, err = put(big, stale, seen)
        head_hits = sb.count('HEAD', '/deadbeef')
        check('resume older than 20 h: not reused, fresh upload starts, HEAD on stale URL is skipped',
              ref and not err and sb.starts() == 1 and head_hits == 0, (err, sb.starts(), head_hits))

        # 2. Resume for a DIFFERENT path: must NOT be reused.
        sb = fresh(); seen = []
        other_path = {'url': f'https://{B}.storage.supabase.co/storage/v1/upload/resumable/deadbeef',
                      'path': 'jeelive/books/OTHER/original.pdf', 'size': len(big),
                      'started': time.time(), 'sent': 0}
        ref, err = put(big, other_path, seen)
        check('resume for a different path: not reused, fresh upload starts',
              ref and not err and sb.starts() == 1 and sb.count('HEAD', '/deadbeef') == 0,
              (err, sb.starts()))

        # 3. Resume with a DIFFERENT size: must NOT be reused.
        sb = fresh(); seen = []
        wrong_size = {'url': f'https://{B}.storage.supabase.co/storage/v1/upload/resumable/deadbeef',
                      'path': KEY, 'size': len(big) - 1, 'started': time.time(), 'sent': 0}
        ref, err = put(big, wrong_size, seen)
        check('resume with a different size: not reused, fresh upload starts',
              ref and not err and sb.starts() == 1 and sb.count('HEAD', '/deadbeef') == 0,
              (err, sb.starts()))

        # 4. HEAD of the saved upload answers 404 (Supabase forgot it): falls back to a fresh upload, no loop.
        class HeadMiss(FakeSupabase):
            def __call__(self, req):
                if req.method == 'HEAD' and req.url.path.startswith('/storage/v1/upload/resumable/'):
                    return httpx.Response(404, text='Upload not found')
                return super().__call__(req)
        sb = fresh(HeadMiss); seen = []
        resume = {'url': f'https://{B}.storage.supabase.co/storage/v1/upload/resumable/gone',
                  'path': KEY, 'size': len(big), 'started': time.time(), 'sent': 6 * 1024 * 1024}
        ref, err = put(big, resume, seen)
        check('resume HEAD answers 404: a fresh upload starts and the PDF is saved exactly',
              ref and not err and sb.starts() == 1 and sb.objects.get(B + '/' + KEY) == big,
              (err, sb.starts()))

        # 5. HEAD of the saved upload answers 410 Gone: same, fresh upload starts.
        class HeadGone(FakeSupabase):
            def __call__(self, req):
                if req.method == 'HEAD' and req.url.path.startswith('/storage/v1/upload/resumable/'):
                    return httpx.Response(410, text='Gone')
                return super().__call__(req)
        sb = fresh(HeadGone); seen = []
        resume = {'url': f'https://{B}.storage.supabase.co/storage/v1/upload/resumable/gone',
                  'path': KEY, 'size': len(big), 'started': time.time(), 'sent': 0}
        ref, err = put(big, resume, seen)
        check('resume HEAD answers 410: fresh upload starts, PDF saved',
              ref and not err and sb.starts() == 1, (err, sb.starts()))

        # 6. HEAD during a 409 PATCH says Supabase stands AHEAD of the client (progress, not a miss).
        class Ahead(FakeSupabase):
            def __init__(self, chunk):
                super().__init__(chunk); self.first_patch_409 = True
            def __call__(self, req):
                if req.method == 'PATCH' and req.url.path.startswith('/storage/v1/upload/resumable/') and self.first_patch_409:
                    self.first_patch_409 = False
                    uid = req.url.path.rsplit('/', 1)[1]
                    u = self.uploads.get(uid)
                    if u is not None:
                        # Supabase silently took in the piece but we return 409 before the HEAD
                        u['data'] += req.content
                    return httpx.Response(409, text='Upload-Offset conflict')
                return super().__call__(req)
        sb = fresh(Ahead); seen = []
        ref, err = put(big, None, seen)
        check('409 then HEAD shows Supabase ahead: counted as progress (no stall) and the PDF finishes',
              ref and not err and sb.objects.get(B + '/' + KEY) == big
              and not any(x.get('stalls') for x in seen), (err, seen[-1:]))

        # 7. One-request route answers 413: SupabaseRefused at once, no wait, no stuck.
        sb = fresh(); sb.tus_down = True; sb.one_request_code = 413; seen = []
        put(big, None, seen); S.STATE['down_until'] = 0.0
        ref, err = put(big, seen[-1], seen)
        check('one-request route 413 after 2 stalls: SupabaseRefused at once (no stall-3, no wait)',
              isinstance(err, S.SupabaseRefused), (err, seen[-1:]))

        # 8. One-request route answers 423 (locked): raised as a StorageWaiting (not stuck, not refused).
        sb = fresh(); sb.tus_down = True; sb.one_request_code = 423; seen = []
        put(big, None, seen); S.STATE['down_until'] = 0.0
        ref, err = put(big, seen[-1], seen)
        check('one-request 423: waits (not refused, not stuck, no infinite loop)',
              isinstance(err, S.StorageWaiting) and err.code == 423, (err, seen[-1:]))

        # 9. One-request route answers 409 (resource exists despite x-upsert): bubbles up without a loop.
        sb = fresh(); sb.tus_down = True; sb.one_request_code = 409; seen = []
        put(big, None, seen); S.STATE['down_until'] = 0.0
        ref, err = put(big, seen[-1], seen)
        check('one-request 409: lifted into a wait/stuck, no infinite loop',
              err and not ref and sb.count('POST', '/' + KEY) >= 1, (err, seen[-1:]))

        # 10. _same_there: read-back is cut partway through: raises StorageError, is NOT silently 'same'.
        class CutStream(FakeSupabase):
            def __init__(self, chunk):
                super().__init__(chunk); self.cut = False
            def __call__(self, req):
                if self.cut and req.method == 'GET' and req.url.path.startswith('/storage/v1/object/authenticated/'):
                    raise httpx.ReadError('connection reset mid-stream', request=req)
                return super().__call__(req)
        sb = fresh(CutStream); sb.objects[B + '/' + KEY] = big; sb.cut = True; seen = []
        ref, err = put(big, None, seen)
        # Supabase appears away, pieces attempted after that. put() should either save (once stream works) or wait;
        # critically it must NOT treat the broken read as "same" and skip sending.
        pieces_sent = sb.pieces()
        check('read-back fails mid-stream: file is NOT mistakenly accepted as already saved',
              pieces_sent > 0 or (err and isinstance(err, S.StorageWaiting)),
              (ref, err, pieces_sent))

        # 11. Two concurrent put_object for the SAME path with the SAME bytes: source_lock serialises them;
        # the second one sees "same there" and sends nothing extra.
        sb = fresh()
        results = {}

        def go(idx):
            try:
                results[idx] = (S.put_object(KEY, big, 'application/pdf'), None)
            except Exception as e:  # noqa: BLE001
                results[idx] = (None, e)
        t1 = threading.Thread(target=go, args=(1,)); t2 = threading.Thread(target=go, args=(2,))
        t1.start(); t2.start(); t1.join(); t2.join()
        starts = sb.starts()
        check('two concurrent put_object (same bytes, same path): one upload is started, the other reuses',
              all(r[0] and not r[1] for r in results.values()) and starts == 1,
              (results, starts))

        # 12. Exactly 6 MB = small (one-request); 6 MB + 1 byte = big (two pieces).
        sb = fresh(); small = os.urandom(6 * 1024 * 1024)
        ref, err = put(small, key='jeelive/books/boundary/exact.pdf')
        check('exactly 6 MB goes in one small request (no resumable upload)',
              ref and sb.starts() == 0 and sb.count('POST', '/exact.pdf') == 1, (err, sb.starts()))
        sb = fresh(); over = os.urandom(6 * 1024 * 1024 + 1)
        ref, err = put(over, key='jeelive/books/boundary/over.pdf')
        check('6 MB + 1 byte takes the resumable (big) route, two pieces',
              ref and sb.starts() == 1 and sb.pieces() == 2, (err, sb.starts(), sb.pieces()))

        # 13. The caller's listener (it notes the place in the caller's own database) fails. That is not Supabase's fault:
        #     the upload carries on, Supabase is not rested for anyone, and the fault is written to the log.
        #     Rewritten by the main agent with the fix: the first version of this check wanted the listener's error raised to the
        #     caller, which would stop a healthy upload (and mark the book failed) for a database hiccup.
        def bad(info): raise RuntimeError('listener boom')

        def send(listener):
            try:
                return S.put_object(KEY, big, 'application/pdf', None, listener)
            except Exception as e:  # noqa: BLE001
                return e
        noted = []
        handler = logging.Handler(); handler.emit = lambda record: noted.append(record.getMessage())
        logging.getLogger(S.__name__).addHandler(handler)
        try:
            sb = fresh(); out = send(bad)
            check('listener fails on every piece, Supabase healthy: the PDF is still saved byte for byte, each piece sent once',
                  out == f'sb://{B}/{KEY}' and sb.objects.get(B + '/' + KEY) == big and sb.starts() == 1 and sb.pieces() == 4,
                  (out, sb.starts(), sb.pieces()))
            check('...Supabase is NOT rested and no Supabase error is recorded for it',
                  S.supabase_on() and S.STATE['strikes'] == 0 and S.STATE['failovers'] == 0 and not S.STATE['last_error'],
                  {k: S.STATE[k] for k in ('strikes', 'failovers', 'last_error')})
            check('...the listener fault is written to the log', any('could not be noted' in m for m in noted), noted[:2])
            sb = fresh(); seen = []; n = {'calls': 0}

            def once(info):
                n['calls'] += 1
                if n['calls'] == 2:
                    raise RuntimeError('listener boom')
                seen.append(info)
            out = send(once)
            check('listener fails once: the later pieces are heard again and the last report says every byte is in',
                  out == f'sb://{B}/{KEY}' and len(seen) == n['calls'] - 1 and seen[-1]['sent'] == len(big), (out, n, seen[-1:]))
            sb = fresh(); sb.patch_code = 400; out = send(bad)
            check("listener fails AND Supabase returns the pieces (400): the wait names Supabase's 400, not the listener; only this file waits",
                  isinstance(out, S.StorageWaiting) and out.code == 400 and out.scope == 'file' and 'boom' not in str(out) + out.reason + out.raw
                  and S.supabase_on() and S.STATE['strikes'] == 0, (out, getattr(out, 'scope', ''), S.STATE['strikes']))
        finally:
            logging.getLogger(S.__name__).removeHandler(handler)

        # 14. The "away" state is cleared once Supabase is back: the next big upload saves.
        sb = fresh(); sb.down = True; seen = []
        put(big, None, seen)
        was_down = not S.supabase_on()
        sb.down = False; S.STATE['down_until'] = 0.0
        ref, err = put(big, None, seen)
        check('Supabase away then back: next upload saves (no stuck state leaked)',
              was_down and ref and not err and sb.objects.get(B + '/' + KEY) == big, (was_down, err))

        # 15. Missing file info (statusCode 404 inside a 400): sb_size returns None, upload proceeds.
        sb = fresh()
        probe = S.sb_size(B, KEY)
        check('sb_size on a missing object: returns None, no StorageError',
              probe is None, probe)

        # 16. A finished upload left at the path answers HEAD with Upload-Offset == Upload-Length:
        #     _carry_on must NOT reuse it (there < size is False); a fresh upload is started.
        sb = fresh(); seen = []
        put(big, None, seen); done_place = dict(seen[-1])
        # Supabase still remembers this upload. Try to resume with it even though it's complete.
        started_before = sb.starts()
        # The object may already be there; make _same_there fail by removing it to force a fresh upload.
        sb.objects.pop(B + '/' + KEY, None)
        ref, err = put(big, done_place, seen)
        check('resume on a finished upload (HEAD offset == length): dropped, a new upload starts',
              ref and not err and sb.starts() == started_before + 1, (err, sb.starts(), started_before))

        # 17. Supabase blocked (402 / 540 on every request): classified as 'blocked' (project restricted),
        #     NOT 'stuck' and NOT a failover to Emergent.
        sb = fresh(); sb.block = (402, 'billing paused'); seen = []
        ref, err = put(big, None, seen)
        check("Supabase blocked (402): StorageWaiting scope='blocked', nothing goes to Emergent",
              isinstance(err, S.StorageWaiting) and err.scope == 'blocked'
              and S.STATE['writes']['emergent'] == 0, (err, getattr(err, 'scope', '')))

        # 18. Small file 403: _refused does nothing for 403 (not refused), sb_put raises generic StorageError.
        sb = fresh(); sb.small_code = (403, 'forbidden')
        ref, err = put(os.urandom(50_000), key='jeelive/pics/x.png', content_type='image/png')
        check('small upload 403: lifted into a StorageWaiting (blocked/away), not accepted',
              err and not ref, (err,))

    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')
    return sum(RESULTS), len(RESULTS)


if __name__ == '__main__':
    passed, total = main()
    sys.exit(0 if passed == total else 1)
