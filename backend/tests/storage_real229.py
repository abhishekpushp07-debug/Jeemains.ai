"""TEST-ONLY Pocket 1 on the REAL Supabase, preview bucket only, TEST_p229/ paths only (removed afterwards). Changes no app data.
Run: cd /app/backend && python tests/storage_real229.py
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
import tejas_storage as S

assert 'preview' in S.bucket_name(), 'preview bucket only'
P = 'TEST_p229/real_big.pdf'
RESULTS, CALLS = [], []
_real = S._call


def counted(method, url, headers=None, tries=3, **kw):
    r = _real(method, url, headers, tries, **kw)
    CALLS.append((method, url.split('/storage/v1/')[1].split('/')[0:2], r.status_code))
    return r


S._call = counted


def check(name, ok, detail=''):
    RESULTS.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:300]), flush=True)


def pieces():
    return sum(1 for m, _, _ in CALLS if m == 'PATCH')


def stored():
    return S.sb_get(S.bucket_name(), P)


try:
    a, b = os.urandom(7 * 1024 * 1024), os.urandom(7 * 1024 * 1024)
    t = time.time(); ref = S.put_object(P, a)
    check('1. new 7 MB file saved in pieces and read back exactly', ref.endswith(P) and stored() == a and pieces() == 2, (ref, pieces()))
    print(f'   took {time.time() - t:.1f}s', flush=True)
    n = pieces(); t = time.time(); S.put_object(P, a)
    check('2. the SAME file to the same path again: recognised, not one piece sent', pieces() == n, pieces() - n)
    print(f'   took {time.time() - t:.1f}s', flush=True)
    n = pieces(); S.put_object(P, b)
    check('3. a DIFFERENT file to the same path (the live fault): replaced, byte for byte', stored() == b and pieces() - n == 2, [c for c in CALLS[-6:]])
    # 4. The answer to the last piece is lost on the way back.
    c = os.urandom(7 * 1024 * 1024); lost = {'n': 0}

    def lose_last(method, url, headers=None, tries=3, **kw):
        r = counted(method, url, headers, tries, **kw)
        if method == 'PATCH' and r.status_code == 204 and int(r.headers.get('Upload-Offset', 0)) == len(c) and not lost['n']:
            lost['n'] += 1
            raise S.StorageError('Supabase connection failed: ReadTimeout')
        return r
    S._call = lose_last
    n = pieces(); seen = []
    try:
        ref = S.put_object(P, c, 'application/pdf', None, seen.append); err = None
    except S.StorageError as exc:
        ref, err = None, exc
    S._call = counted
    check('4. last piece saved, its answer lost: accepted as saved, no wait', lost['n'] == 1 and ref and err is None and stored() == c, (lost, err, seen[-1:]))
    # 5. The second route: the whole file in one request.
    t = time.time(); S._one_request(S.bucket_name(), P, a, 'application/pdf')
    check('5. one-request route saves a 7 MB file over the old one', stored() == a and S.sb_size(S.bucket_name(), P) == len(a))
    print(f'   took {time.time() - t:.1f}s', flush=True)
    check('6. a path with no file reads as "nothing there"', S.sb_size(S.bucket_name(), 'TEST_p229/none.pdf') is None)
finally:
    r = _real('DELETE', f'{S.project_url()}/storage/v1/object/{S.bucket_name()}', {'Content-Type': 'application/json'}, json={'prefixes': [P]})
    left = _real('POST', f'{S.project_url()}/storage/v1/object/list/{S.bucket_name()}', {'Content-Type': 'application/json'}, json={'prefix': 'TEST_p229/', 'limit': 100})
    print('cleanup', r.status_code, 'left in TEST_p229/:', len(left.json()) if left.status_code == 200 else left.text[:120], flush=True)
print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')
