"""TEST-ONLY iteration 229, Pocket 1: the big-file route (an original PDF over 6 MB).
The fake answers the way real Supabase was seen to answer (tests/fake_supabase229.py). No network, no real keys, no database.
Run: cd /app/backend && python tests/storage_big229.py
"""
import importlib.util, os, sys, time
from pathlib import Path
from unittest import mock
import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'tests'))
os.environ.update(SUPABASE_URL='https://abcdefghijklmnopqrst.supabase.co', SUPABASE_SECRET_KEY='sb_secret_test', FRONTEND_URL='https://preview-x.example.com')
os.environ.pop('SUPABASE_BUCKET', None)
spec = importlib.util.spec_from_file_location('big229', str(ROOT / 'tejas_storage.py'))
S = importlib.util.module_from_spec(spec); spec.loader.exec_module(S)
from fake_supabase229 import FakeSupabase  # noqa: E402

RESULTS = []
B = 'jeelive-preview-x-example-com'
KEY = 'jeelive/books/b1/original.pdf'


def check(name, ok, detail=''):
    RESULTS.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:400]), flush=True)


def fresh():
    sb = FakeSupabase(S.TUS_CHUNK)
    S.STATE.update(down_until=0.0, strikes=0, last_error='', auth=None, bucket=None, writes={'supabase': 0, 'emergent': 0}, failovers=0, last_failover=None, backup_since=None)
    S._source_cache = S.ByteCache(64 * 1024 * 1024)
    client = httpx.Client(transport=httpx.MockTransport(sb))
    S._client = lambda: client
    return sb


def put(data, resume=None, seen=None, key=KEY):
    """Returns (reference or None, the error or None), the way a caller sees it."""
    try:
        return S.put_object(key, data, 'application/pdf', resume, seen.append if seen is not None else None), None
    except S.StorageError as exc:
        return None, exc


def main():
    big, other = os.urandom(20 * 1024 * 1024 + 321), os.urandom(20 * 1024 * 1024 + 321)
    with mock.patch.object(S.time, 'sleep', lambda s: None):
        # 1. The live fault: the path already holds a file. The same PDF again is recognised, not sent again.
        sb = fresh(); sb.objects[B + '/' + KEY] = big
        ref, err = put(big)
        check('same PDF already in Supabase at that path: accepted without sending one piece', ref == f'sb://{B}/{KEY}' and not err and sb.starts() == 0 and sb.pieces() == 0, (ref, err, sb.starts(), sb.pieces()))
        # 2. The path holds a DIFFERENT file: the new one replaces it (permission to overwrite travels with every piece).
        sb = fresh(); sb.objects[B + '/' + KEY] = other
        ref, err = put(big)
        check('a different file at that path: replaced by the new PDF, byte for byte', ref and sb.objects[B + '/' + KEY] == big and sb.pieces() == 4, (err, sb.pieces()))
        check('...and it is read back exactly', S.get_object(ref) == big)
        # 3. Same size, different bytes at that path: the fingerprint decides, so it is sent.
        sb = fresh(); sb.objects[B + '/' + KEY] = other
        ref, err = put(big)
        check('same size but different bytes: not mistaken for the same file', ref and sb.objects[B + '/' + KEY] == big)
        # 4. The last piece arrived but its answer was lost: found already saved, nothing is sent again, no wait.
        sb = fresh(); sb.lose_last_answer = True; seen = []
        ref, err = put(big, None, seen)
        check('last piece saved but its answer lost: recognised as saved, no wait', ref and not err and sb.objects[B + '/' + KEY] == big and sb.starts() == 1, (err, sb.starts(), sb.pieces()))
        # 5. A half upload that never moves: two tries, then it is dropped for a fresh upload and the one-request route.
        sb = fresh(); sb.tus_down = True; seen = []
        ref, err = put(big, None, seen)
        place = seen[-1]
        check('piece route broken, try 1: the file waits, one stall remembered with its upload address', err and isinstance(err, S.StorageWaiting) and place.get('stalls') == 1 and place.get('url'), (err, place))
        S.STATE['down_until'] = 0.0
        ref, err = put(big, place, seen)
        check('try 2: second stall, so the same PDF goes in ONE request and is saved', ref and not err and sb.objects[B + '/' + KEY] == big and sb.count('POST', '/' + KEY) == 1, (err, seen[-1]))
        check('...the second try carried on with the same upload address first (not a new one)', sb.starts() == 1, sb.starts())
        # 6. Both routes fail: after two stalls the old half upload is NOT used again.
        sb = fresh(); sb.tus_down = True; sb.one_request_code = 500; seen = []
        put(big, None, seen); S.STATE['down_until'] = 0.0
        put(big, seen[-1], seen); S.STATE['down_until'] = 0.0
        check('two stalls remembered when both routes fail', seen[-1].get('stalls') == 2 and sb.starts() == 1, (seen[-1], sb.starts()))
        ref, err = put(big, seen[-1], seen)
        check('try 3: the old half upload is dropped, a fresh upload starts', sb.starts() == 2 and err and seen[-1].get('stalls') == 3, (sb.starts(), seen[-1]))
        sb.tus_down = False; S.STATE['down_until'] = 0.0
        ref, err = put(big, seen[-1], seen)
        check('route back: saved; the stall count is gone from its place', ref and sb.objects[B + '/' + KEY] == big and 'stalls' not in seen[-1], (err, seen[-1]))
        # 7. Pieces that move are never counted as a stall (a slow line is not a stuck file).
        sb = fresh(); seen = []
        real = sb.__call__
        state = {'n': 0}

        def two_then_dead(req):
            if req.method == 'PATCH':
                state['n'] += 1
                if state['n'] > 2:
                    return httpx.Response(500, text='gone')
            return real(req)
        client = httpx.Client(transport=httpx.MockTransport(two_then_dead)); S._client = lambda: client
        ref, err = put(big, None, seen)
        check('2 pieces across, then the route breaks: waits with NO stall counted', err and seen[-1].get('stalls') == 0 and seen[-1]['sent'] == 2 * S.TUS_CHUNK, (err, seen[-1]))
        client = httpx.Client(transport=httpx.MockTransport(sb)); S._client = lambda: client; S.STATE['down_until'] = 0.0
        n = sb.pieces()
        ref, err = put(big, seen[-1], seen)
        check('...and it carries on from piece 3 on the same upload', ref and sb.starts() == 1 and sb.pieces() - n == 2, (err, sb.starts(), sb.pieces() - n))
        # 8. Supabase's lock (423) is waited out, not treated as a failure.
        sb = fresh(); sb.locked = 2
        ref, err = put(big)
        check('423 lock for a moment: asked again, the PDF is saved', ref and not err and sb.objects[B + '/' + KEY] == big, err)
        sb = fresh(); sb.locked = 99; seen = []
        ref, err = put(big, None, seen)
        check('423 lock that stays: the file waits; it is not a stall and no second route is forced', isinstance(err, S.StorageWaiting) and '423' in str(err) and not any(x.get('stalls') for x in seen) and sb.count('POST', '/' + KEY) == 0, (err, seen[-1:]))
        # 9. Supabase itself away: a wait, no stall counted against the file.
        sb = fresh(); seen = []
        sb.down = True
        S.STATE['bucket'] = B
        ref, err = put(big, None, seen)
        check('Supabase away: StorageWaiting, no stall counted, nothing half-claimed', isinstance(err, S.StorageWaiting) and not any(x.get('stalls') for x in seen), (err, seen))
        # 10. The size is checked after every big save.
        sb = fresh(); sb.short_save = True
        ref, err = put(big)
        check('Supabase stored a different size: NOT accepted as saved, the reason names the size', ref is None and isinstance(err, S.StorageWaiting) and 'size' in err.reason and S.supabase_on(), (ref, err, getattr(err, 'reason', '')))
        # 11. A caller that cannot remember the place (a chapter book sent inside one request): both tries and the second route in one call.
        sb = fresh(); sb.tus_down = True
        ref = S.put_object('tejas/chapter-books/c1/s.pdf', big)
        check('no memory between tries: fresh try, then one request, all in one call', ref and sb.objects[B + '/tejas/chapter-books/c1/s.pdf'] == big and sb.starts() == 2, sb.starts())
        # 12. Over Supabase's size limit stays an immediate, clear stop.
        sb = fresh(); sb.tus_start_fail = 413
        ref, err = put(big)
        check('over the size limit: SupabaseRefused at once (no wait, no second route)', isinstance(err, S.SupabaseRefused) and sb.count('POST', '/' + KEY) == 0, err)
        # 13. Small files (pictures) are untouched by all this.
        sb = fresh(); png = os.urandom(70_000)
        ref = S.put_object('jeelive/books/b1/crops/p.png', png, 'image/png')
        check('a picture still goes in one small request', ref and sb.starts() == 0 and S.get_object(ref) == png and sb.count('GET', '/crops/p.png') == 1, sb.calls[-3:])
        # 14. A healthy big upload costs one check before and one after, nothing more.
        sb = fresh(); t = time.time()
        ref, err = put(big)
        infos = sum(1 for m, _, p in sb.calls if '/object/info/' in p)
        check('healthy 20 MB upload: 1 start, 4 pieces, 2 size checks', ref and sb.starts() == 1 and sb.pieces() == 4 and infos == 2, (sb.starts(), sb.pieces(), infos))
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')


if __name__ == '__main__':
    main()
