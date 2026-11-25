"""TEST-ONLY packet C on the REAL Supabase, preview bucket only. No app data, no database.
A folder shaped exactly like one upload's own folder (jeelive/books/<a fresh random id>/) is filled with TEST_ files, then emptied
by the app's own remove functions: listed, removed, listed again. A half-sent big upload is ended. A neighbour folder is untouched.
Everything this test made is removed at the end. Run: cd /app/backend && python tests/storage_delete_real234.py
"""
import base64, os, sys, uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
import tejas_storage as S

assert 'preview' in S.bucket_name(), 'preview bucket only'
RESULTS = []
A, N = f'jeelive/books/{uuid.uuid4()}/', f'jeelive/books/{uuid.uuid4()}/'
B = S._bucket()


def check(name, ok, detail=''):
    RESULTS.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:300]), flush=True)


def tree(folder):
    files, inner = S.sb_list(folder)
    return sorted(n for n, _ in files) + sorted(f'{d}/{n}' for d in inner for n, _ in S.sb_list(folder + d + '/')[0])


try:
    for name in ('TEST_original.pdf', 'crops/TEST_a.png', 'crops/TEST_b.png', 'crops/TEST_c.png'):
        S.sb_put(A + name, os.urandom(3000), 'application/octet-stream')
    S.sb_put(N + 'TEST_keep.png', b'keep me', 'application/octet-stream')
    check('1. setup: the upload folder holds 1 PDF + 3 pictures in a sub-folder; the neighbour holds 1 file', len(tree(A)) == 4 and tree(N) == ['TEST_keep.png'], (tree(A), tree(N)))
    meta = ','.join(f'{k} {base64.b64encode(v.encode()).decode()}' for k, v in {'bucketName': B, 'objectName': A + 'TEST_half.pdf', 'contentType': 'application/pdf', 'cacheControl': '3600'}.items())
    r = S._call('POST', S._tus_endpoint(), {'Tus-Resumable': '1.0.0', 'Upload-Length': str(13 * 1024 * 1024), 'Upload-Metadata': meta, 'x-upsert': 'true'})
    half = r.headers.get('Location', '')
    S._call('PATCH', half, {'Tus-Resumable': '1.0.0', 'Upload-Offset': '0', 'Content-Type': 'application/offset+octet-stream', 'x-upsert': 'true'}, tries=1, content=os.urandom(S.TUS_CHUNK))
    check('2. setup: a big upload of that folder is half-sent (6 of 13 MB)', S._call('HEAD', half, {'Tus-Resumable': '1.0.0'}).headers.get('Upload-Offset') == str(S.TUS_CHUNK), half[:60])
    check('3. the half-sent upload is ended: Supabase no longer knows its address', S.sb_end_upload(half) is True and S._call('HEAD', half, {'Tus-Resumable': '1.0.0'}).status_code == 404)
    refused = 0
    for bad in (lambda: S.sb_empty('jeelive/books/'), lambda: S.sb_empty(A + 'crops/'), lambda: S.sb_remove(A, [N + 'TEST_keep.png']), lambda: S.sb_empty('jeelive/')):
        try:
            bad()
        except ValueError:
            refused += 1
    check('4. other paths are refused before anything is asked of Supabase; both folders unchanged', refused == 4 and len(tree(A)) == 4 and tree(N) == ['TEST_keep.png'], refused)
    n = S.sb_empty(A)
    files, inner = S.sb_list(A)
    check('5. the upload folder is emptied: 4 files removed, and Supabase lists nothing there (no file, no sub-folder)', n == 4 and not files and not inner, (n, files, inner))
    check('6. every removed file is really gone (asked one by one)', all(S.sb_size(B, A + x) is None for x in ('TEST_original.pdf', 'crops/TEST_a.png', 'crops/TEST_b.png', 'crops/TEST_c.png')))
    check('7. the neighbour folder still has its file, byte for byte', tree(N) == ['TEST_keep.png'] and S.sb_get(B, N + 'TEST_keep.png') == b'keep me', tree(N))
    check('8. emptying an already empty folder is harmless (0 removed)', S.sb_empty(A) == 0)
    check('9. Supabase was never rested by any of this', S.supabase_on() and S.STATE['strikes'] == 0, S.STATE['strikes'])
finally:
    for folder in (A, N):
        try:
            S.sb_empty(folder)
        except Exception as exc:  # noqa: BLE001
            print('cleanup problem', folder, exc)
    print('cleanup: left in the two test folders:', len(tree(A)) + len(tree(N)), flush=True)
print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')
