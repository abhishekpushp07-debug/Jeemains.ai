"""TEST-ONLY Pocket 0 probe: what the REAL Supabase (preview bucket only) answers when a big file goes to the same path twice,
and when the answer to the last piece is lost. Only TEST_p229/ paths; removes them afterwards. Changes no app data.
Run: cd /app/backend && python tests/supabase_probe229.py
"""
import base64, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
import tejas_storage as S

assert 'preview' in S.bucket_name(), 'preview bucket only'
TUS = {'Tus-Resumable': '1.0.0'}
PREFIX = 'TEST_p229/'
made = set()


def say(*a):
    print(*a, flush=True)


def start(path, size, upsert=True):
    meta = ','.join(f"{k} {base64.b64encode(v.encode()).decode()}" for k, v in (('bucketName', S._bucket()), ('objectName', path), ('contentType', 'application/pdf'), ('cacheControl', '3600')))
    r = S._call('POST', S._tus_endpoint(), {**TUS, 'Upload-Length': str(size), 'Upload-Metadata': meta, **({'x-upsert': 'true'} if upsert else {})})
    return r


def patch(where, data, offset, upsert=False):
    return S._call('PATCH', where, {**TUS, 'Upload-Offset': str(offset), 'Content-Type': 'application/offset+octet-stream', **({'x-upsert': 'true'} if upsert else {})}, tries=1, content=data[offset:offset + S.TUS_CHUNK])


def show(tag, r):
    say(f'  {tag}: {r.status_code} offset={r.headers.get("Upload-Offset")} body={r.text[:160]!r}')
    return r


def send_all(path, data, upsert_start=True, upsert_patch=False):
    r = show('start', start(path, len(data), upsert_start))
    if r.status_code != 201:
        return r
    where, offset = r.headers['Location'], 0
    while offset < len(data):
        r = show(f'patch@{offset}', patch(where, data, offset, upsert_patch))
        if r.status_code != 204:
            return r
        offset = int(r.headers['Upload-Offset'])
    made.add(path)
    return r


def info(path):
    r = S._call('GET', f"{S.project_url()}/storage/v1/object/info/{S._bucket()}/{path}")
    say(f'  info: {r.status_code} {r.text[:200]!r}')
    return r


try:
    a, b = os.urandom(7 * 1024 * 1024), os.urandom(7 * 1024 * 1024)
    say('1. first big file to a new path (upsert in the first request only, as the app does today)')
    t = time.time(); send_all(PREFIX + 'same.pdf', a); say(f'  took {time.time() - t:.1f}s'); info(PREFIX + 'same.pdf')

    say('2. the SAME path again, different bytes, upsert in the first request only (today)')
    r = send_all(PREFIX + 'same.pdf', b)
    say('  => today the second upload', 'WORKS' if r.status_code == 204 else f'IS REFUSED ({r.status_code})')
    got = S.sb_get(S._bucket(), PREFIX + 'same.pdf'); say('  stored bytes are', 'second' if got == b else 'first' if got == a else 'other')

    say('3. the SAME path again, upsert sent with every piece too')
    r = send_all(PREFIX + 'same.pdf', b, True, True)
    got = S.sb_get(S._bucket(), PREFIX + 'same.pdf'); say('  stored bytes are', 'second' if got == b else 'first' if got == a else 'other')

    say('4. the SAME path again with no upsert at all')
    send_all(PREFIX + 'same.pdf', a, False, False)

    say('5. last piece sent, its answer "lost": what does the upload address say afterwards?')
    c = os.urandom(7 * 1024 * 1024)
    r = show('start', start(PREFIX + 'lost.pdf', len(c)))
    where = r.headers['Location']
    show('patch@0', patch(where, c, 0))
    show('patch@last (answer thrown away)', patch(where, c, S.TUS_CHUNK)); made.add(PREFIX + 'lost.pdf')
    show('HEAD after finish', S._call('HEAD', where, TUS))
    show('PATCH again at last offset', patch(where, c, S.TUS_CHUNK))
    show('PATCH again at end', patch(where, c, len(c)))
    info(PREFIX + 'lost.pdf')

    say('6. a half-sent upload: HEAD, then a second start for the same path while the first is open')
    d = os.urandom(13 * 1024 * 1024)
    r = show('start A', start(PREFIX + 'half.pdf', len(d)))
    wa = r.headers['Location']
    show('A patch@0', patch(wa, d, 0))
    show('A HEAD', S._call('HEAD', wa, TUS))
    r = show('start B (same path)', start(PREFIX + 'half.pdf', len(d)))
    if r.status_code == 201:
        wb = r.headers['Location']
        show('B patch@0', patch(wb, d, 0))
        show('A patch@6MB while B open', patch(wa, d, S.TUS_CHUNK))
        show('A patch@12MB (finishes A)', patch(wa, d, 2 * S.TUS_CHUNK)); made.add(PREFIX + 'half.pdf')
        show('B patch@6MB after A finished', patch(wb, d, S.TUS_CHUNK))
        show('B HEAD', S._call('HEAD', wb, TUS))
        show('B DELETE (drop the half upload)', S._call('DELETE', wb, TUS))

    say('7. one request for a big file (no pieces): 7 MB POST with upsert')
    t = time.time()
    r = S._call('POST', S._object_url(S._bucket(), PREFIX + 'one.pdf'), {'Content-Type': 'application/pdf', 'x-upsert': 'true', 'Cache-Control': '3600'}, content=a)
    say(f'  one POST: {r.status_code} {r.text[:120]!r} {time.time() - t:.1f}s'); made.add(PREFIX + 'one.pdf')
    info(PREFIX + 'one.pdf')
    r = S._call('HEAD', S._object_url(S._bucket(), PREFIX + 'one.pdf', 'authenticated'))
    say(f'  HEAD object: {r.status_code} length={r.headers.get("content-length")} etag={r.headers.get("etag")}')
    r = S._call('HEAD', S._object_url(S._bucket(), PREFIX + 'nothing-here.pdf', 'authenticated'))
    say(f'  HEAD missing object: {r.status_code}')
    r = S._call('GET', f"{S.project_url()}/storage/v1/bucket/{S._bucket()}")
    say('  bucket:', r.status_code, {k: r.json().get(k) for k in ('public', 'file_size_limit', 'allowed_mime_types')} if r.status_code == 200 else r.text[:120])
finally:
    r = S._call('DELETE', f'{S.project_url()}/storage/v1/object/{S._bucket()}', {'Content-Type': 'application/json'}, json={'prefixes': sorted(made)})
    say('cleanup', r.status_code)
    r = S._call('POST', f'{S.project_url()}/storage/v1/object/list/{S._bucket()}', {'Content-Type': 'application/json'}, json={'prefix': PREFIX, 'limit': 100})
    say('left in TEST_p229/:', len(r.json()) if r.status_code == 200 else r.text[:120])
