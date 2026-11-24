import os, sys, base64
sys.path.insert(0, '/app/backend')
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')
import tejas_storage as S
assert 'preview' in S.bucket_name()
TUS = {'Tus-Resumable': '1.0.0'}; P = 'TEST_p229/remedy.pdf'; b = S._bucket()
old, new = os.urandom(7 * 1024 * 1024), os.urandom(7 * 1024 * 1024)
try:
    r = S._call('POST', S._object_url(b, P), {'Content-Type': 'application/pdf', 'x-upsert': 'true'}, content=old); print('old file put', r.status_code)
    meta = ','.join(f"{k} {base64.b64encode(v.encode()).decode()}" for k, v in (('bucketName', b), ('objectName', P), ('contentType', 'application/pdf'), ('cacheControl', '3600')))
    r = S._call('POST', S._tus_endpoint(), {**TUS, 'Upload-Length': str(len(new)), 'Upload-Metadata': meta, 'x-upsert': 'true'}); print('tus start', r.status_code); where = r.headers['Location']
    pa = lambda off: S._call('PATCH', where, {**TUS, 'Upload-Offset': str(off), 'Content-Type': 'application/offset+octet-stream'}, tries=1, content=new[off:off + S.TUS_CHUNK])
    r = pa(0); print('patch@0 while old file exists', r.status_code, r.text[:60])
    r = S._call('HEAD', where, TUS); print('HEAD stuck upload', r.status_code, r.headers.get('Upload-Offset'))
    r = S._call('DELETE', f'{S.project_url()}/storage/v1/object/{b}', {'Content-Type': 'application/json'}, json={'prefixes': [P]}); print('old file deleted', r.status_code)
    r = pa(0); print('patch@0 after delete (same stuck upload)', r.status_code, r.headers.get('Upload-Offset'), r.text[:60])
    if r.status_code == 204:
        r = pa(int(r.headers['Upload-Offset'])); print('last piece', r.status_code, r.headers.get('Upload-Offset'))
    print('stored == new bytes:', S.sb_get(b, P) == new)
    r = S._call('HEAD', S._object_url(b, P, 'authenticated')); print('HEAD object', r.status_code, r.headers.get('content-length'))
finally:
    r = S._call('DELETE', f'{S.project_url()}/storage/v1/object/{b}', {'Content-Type': 'application/json'}, json={'prefixes': [P]}); print('cleanup', r.status_code)
    r = S._call('POST', f'{S.project_url()}/storage/v1/object/list/{b}', {'Content-Type': 'application/json'}, json={'prefix': 'TEST_p229/', 'limit': 10}); print('left', len(r.json()) if r.status_code == 200 else r.text[:80])
