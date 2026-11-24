"""TEST-ONLY Pocket 2 on the REAL Supabase, preview bucket only, TEST_p231/ paths only (removed afterwards). Changes no app data.
Real Supabase cannot be made to return one file on request, so this test itself answers 409 / 400 for ONE test file's uploads
(every other call goes to the real Supabase). It proves: that file alone becomes "stuck" with its code, Supabase is not rested,
another file is saved for real at the same time, nothing is half-saved, and the stuck file is saved for real on the next try.
Run: cd /app/backend && python tests/storage_stuck_real231.py
"""
import base64, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
import httpx
import tejas_storage as S

assert 'preview' in S.bucket_name(), 'preview bucket only'
BIG, SMALL, OK = 'TEST_p231/stuck_big.pdf', 'TEST_p231/stuck_small.png', 'TEST_p231/healthy.png'
RESULTS, FAULT, HELD = [], {'on': True, 'hits': 0}, set()
_real = S._call


def check(name, ok, detail=''):
    RESULTS.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:300]), flush=True)


def call(method, url, headers=None, tries=3, **kw):
    if FAULT['on']:
        if method == 'PATCH' and url in HELD:
            FAULT['hits'] += 1
            return httpx.Response(409, text='TEST: piece returned', request=httpx.Request(method, url))
        if method == 'POST' and '/storage/v1/object/' in url and url.endswith((BIG, SMALL)):
            FAULT['hits'] += 1
            return httpx.Response(400, json={'statusCode': '409' if url.endswith(BIG) else '400', 'error': 'TEST', 'message': 'TEST: Supabase returns this one file'}, request=httpx.Request(method, url))
    r = _real(method, url, headers, tries, **kw)
    if method == 'POST' and url == S._tus_endpoint() and base64.b64encode(BIG.encode()).decode() in (headers or {}).get('Upload-Metadata', '') and r.status_code == 201:
        HELD.add(r.headers['Location'])
    return r


S._call = call
bucket = S.bucket_name()
big, small, ok = os.urandom(7 * 1024 * 1024 + 231), os.urandom(60_000), os.urandom(61_000)
place, seen = None, []


def send_big():
    global place
    try:
        return S.put_object(BIG, big, 'application/pdf', place, seen.append)
    except S.StorageError as exc:
        return exc
    finally:
        place = seen[-1] if seen else place


def send(path, data):
    try:
        return S.put_object(path, data, 'image/png')
    except S.StorageError as exc:
        return exc


try:
    one, two, three = send_big(), send_big(), send_big()
    check('1. big PDF returned by both routes: tries 1 and 2 wait as "this file only", Supabase not rested', all(isinstance(x, S.StorageWaiting) and x.scope == 'file' for x in (one, two)) and S.supabase_on(), (one, two))
    check('2. try 3: only this PDF is stuck; it says why with Supabase\'s code and what happens next', isinstance(three, S.StorageStuck) and three.code == 409 and '(409)' in three.reason and '15 minute' in three.step, (three, getattr(three, 'reason', '')))
    out = send(SMALL, small)
    check('3. a picture that is returned is stuck at once, with its code', isinstance(out, S.StorageStuck) and out.code == 400 and '(400)' in out.reason, (out, getattr(out, 'reason', '')))
    check('4. Supabase is NOT rested for anyone (no strike, no failover counted)', S.supabase_on() and S.STATE['strikes'] == 0 and S.STATE['failovers'] == 0, {k: S.STATE[k] for k in ('strikes', 'failovers')})
    ref = send(OK, ok)
    check('5. another file sent at that moment is saved in the REAL Supabase and read back exactly', isinstance(ref, str) and ref.endswith(OK) and S.sb_get(bucket, OK) == ok, ref)
    check('6. nothing of the stuck files was half-saved in Supabase', S.sb_size(bucket, BIG) is None and S.sb_size(bucket, SMALL) is None)
    print('   answers this test gave in place of Supabase:', FAULT['hits'], flush=True)
    FAULT['on'] = False
    ref = send_big()
    check('7. Dobara chalao once Supabase takes it: the same PDF is saved for real and read back byte for byte', isinstance(ref, str) and S.sb_get(bucket, BIG) == big and S.sb_size(bucket, BIG) == len(big), ref)
    ref = send(SMALL, small)
    check('8. ...and so is the picture', isinstance(ref, str) and S.sb_get(bucket, SMALL) == small, ref)
finally:
    r = _real('DELETE', f'{S.project_url()}/storage/v1/object/{bucket}', {'Content-Type': 'application/json'}, json={'prefixes': [BIG, SMALL, OK]})
    left = _real('POST', f'{S.project_url()}/storage/v1/object/list/{bucket}', {'Content-Type': 'application/json'}, json={'prefix': 'TEST_p231/', 'limit': 100})
    print('cleanup', r.status_code, 'left in TEST_p231/:', len(left.json()) if left.status_code == 200 else left.text[:120], flush=True)
print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')
