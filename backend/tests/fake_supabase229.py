"""TEST-ONLY: a Supabase Storage stand-in that answers the way the real one was seen to answer (tests/supabase_probe229.py, 24 Nov):
a piece for a path that already holds a file is returned with 409 "The resource already exists" unless the piece itself carries x-upsert;
a finished upload answers 409 to any further piece; a missing file is a 400 with statusCode "404" inside. No network."""
import base64, json, threading, uuid
from urllib.parse import unquote
import httpx

EXISTS = 'The resource already exists'
KEY = 'sb_secret_test'


class FakeSupabase:
    def __init__(self, chunk):
        self.chunk = chunk
        self.objects, self.buckets, self.uploads, self.calls = {}, {}, {}, []
        self.lock = threading.Lock()
        # knobs a test turns
        self.down = False            # every route: 503
        self.tus_down = False        # only the piece route: 500
        self.tus_start_fail = 0      # the next N upload starts answer this code
        self.patch_code = None       # every piece answers this code (e.g. 400)
        self.locked = 0              # the next N pieces answer 423
        self.lose_last_answer = False  # the last piece is saved, its answer never arrives
        self.short_save = False      # a finished upload is stored one byte short
        self.short_one = False       # the one-request route stores one byte short too
        self.one_request_code = None  # the one-request route answers this code
        self.block = None            # (code, message): the whole project answers this (402, 540 ...)
        self.small_code = None       # every small upload answers (code, message)

    def count(self, method, tail):
        return sum(1 for m, _, p in self.calls if m == method and p.endswith(tail))

    def pieces(self):
        return sum(1 for m, _, p in self.calls if m == 'PATCH')

    def starts(self):
        return self.count('POST', '/upload/resumable')

    def __call__(self, req):
        p = unquote(req.url.path)
        with self.lock:
            self.calls.append((req.method, req.url.host, p))
        if self.down:
            return httpx.Response(503, text='Service Unavailable')
        if self.block:
            return httpx.Response(self.block[0], json={'statusCode': str(self.block[0]), 'error': 'blocked', 'message': self.block[1]})
        if req.headers.get('apikey') != KEY:
            return httpx.Response(401, json={'message': 'Invalid API key'})
        missing = httpx.Response(400, json={'statusCode': '404', 'error': 'not_found', 'message': 'Object not found', 'code': 'NoSuchKey'})
        if p.startswith('/storage/v1/bucket'):
            if req.method == 'GET':
                name = p.rsplit('/', 1)[1]
                return httpx.Response(200, json=self.buckets[name]) if name in self.buckets else httpx.Response(400, json={'error': 'Bucket not found'})
            b = json.loads(req.content); self.buckets[b['id']] = b
            return httpx.Response(200, json={'name': b['id']})
        if p.startswith('/storage/v1/object/info/'):
            key = p[len('/storage/v1/object/info/'):]
            return httpx.Response(200, json={'name': key, 'size': len(self.objects[key])}) if key in self.objects else missing
        if p.startswith('/storage/v1/object/authenticated/'):
            key = p[len('/storage/v1/object/authenticated/'):]
            return httpx.Response(200, content=self.objects[key]) if key in self.objects else missing
        if p.startswith('/storage/v1/object/list/'):
            # As the real one (probe of 24 Nov): a folder is named with or without its last slash; half a name lists nothing;
            # files have an id, sub-folders are listed once with id None.
            body = json.loads(req.content); bucket = p.rsplit('/', 1)[1]; prefix = bucket + '/' + body.get('prefix', '').rstrip('/') + '/'
            inside = sorted(k[len(prefix):] for k in self.objects if k.startswith(prefix))
            rows = [{'name': n, 'id': 'f-' + n, 'metadata': {'size': len(self.objects[prefix + n])}} for n in inside if '/' not in n]
            rows += [{'name': n, 'id': None, 'metadata': None} for n in sorted({n.split('/', 1)[0] for n in inside if '/' in n})]
            rows.sort(key=lambda x: x['name'])
            return httpx.Response(200, json=rows[body.get('offset', 0):body.get('offset', 0) + body.get('limit', 100)])
        if p.startswith('/storage/v1/object/') and req.method == 'DELETE':
            bucket = p.rsplit('/', 1)[1]
            gone = [{'name': name} for name in json.loads(req.content).get('prefixes', []) if self.objects.pop(bucket + '/' + name, None) is not None]
            return httpx.Response(200, json=gone)
        if p.startswith('/storage/v1/object/') and req.method == 'POST':
            key = p[len('/storage/v1/object/'):]
            big = len(req.content) > self.chunk
            if big and self.one_request_code:
                return httpx.Response(self.one_request_code, text='one request refused')
            if not big and self.small_code:
                return httpx.Response(400, json={'statusCode': str(self.small_code[0]), 'error': 'x', 'message': self.small_code[1]})
            if key in self.objects and req.headers.get('x-upsert') != 'true':
                return httpx.Response(400, json={'statusCode': '409', 'error': 'Duplicate', 'message': EXISTS})
            self.objects[key] = req.content[:-1] if big and self.short_one else req.content
            return httpx.Response(200, json={'Key': key})
        if p == '/storage/v1/upload/resumable' and req.method == 'POST':
            if self.tus_start_fail:
                code, self.tus_start_fail = self.tus_start_fail, 0
                return httpx.Response(code, text='start refused')
            meta = {k: base64.b64decode(v).decode() for k, v in (x.split(' ') for x in req.headers['upload-metadata'].split(','))}
            key = meta['bucketName'] + '/' + meta['objectName']
            if key in self.objects and req.headers.get('x-upsert') != 'true':
                return httpx.Response(409, text=EXISTS)
            uid = uuid.uuid4().hex
            self.uploads[uid] = {'len': int(req.headers['upload-length']), 'key': key, 'data': b'', 'done': False}
            return httpx.Response(201, headers={'Location': f'https://{req.url.host}/storage/v1/upload/resumable/{uid}', 'Tus-Resumable': '1.0.0'})
        if p.startswith('/storage/v1/upload/resumable/'):
            u = self.uploads.get(p.rsplit('/', 1)[1])
            if not u:
                return httpx.Response(404, text='Upload not found')
            if req.method == 'HEAD':
                return httpx.Response(200, headers={'Upload-Offset': str(len(u['data'])), 'Upload-Length': str(u['len'])})
            if req.method == 'DELETE':   # a half-sent upload is ended: its address is gone (seen on the real one: 204, then 404)
                del self.uploads[p.rsplit('/', 1)[1]]
                return httpx.Response(204)
            if self.tus_down:
                return httpx.Response(500, text='piece route broken')
            if self.patch_code:
                return httpx.Response(self.patch_code, text='piece refused')
            if self.locked:
                self.locked -= 1
                return httpx.Response(423, text='Resource is locked')
            if u['done'] or (u['key'] in self.objects and req.headers.get('x-upsert') != 'true'):
                return httpx.Response(409, text=EXISTS)
            if int(req.headers['upload-offset']) != len(u['data']):
                return httpx.Response(409, text='Upload-Offset conflict')
            if len(req.content) != min(self.chunk, u['len'] - len(u['data'])):
                return httpx.Response(400, text='wrong piece size')
            u['data'] += req.content
            if len(u['data']) == u['len']:
                u['done'] = True
                self.objects[u['key']] = u['data'][:-1] if self.short_save else u['data']
                if self.lose_last_answer:
                    self.lose_last_answer = False
                    raise httpx.ReadTimeout('answer lost', request=req)
            return httpx.Response(204, headers={'Upload-Offset': str(len(u['data']))})
        return httpx.Response(404, text='unknown route ' + p)
