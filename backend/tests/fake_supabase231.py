"""TEST-ONLY: the Supabase stand-in of tests/fake_supabase229.py plus one knob: an upload (small file, one-request big file, or a piece
of a resumable upload) whose path contains one of `returned` is answered 400, the way Supabase returns just one file while it is up.
The stand-in's own behaviour is not changed. No network."""
from urllib.parse import unquote
import httpx
from fake_supabase229 import FakeSupabase

SAID = 'TEST: Supabase returns this one file'


class Picky(FakeSupabase):
    def __init__(self, chunk):
        super().__init__(chunk)
        self.returned = []

    def marks(self):
        return self.returned

    def __call__(self, req):
        p = unquote(req.url.path)
        if not self.down and not self.block:
            key = None
            if req.method == 'POST' and p.startswith('/storage/v1/object/') and not p.startswith(('/storage/v1/object/list/', '/storage/v1/object/info/')):
                key = p[len('/storage/v1/object/'):]
            elif req.method == 'PATCH' and p.startswith('/storage/v1/upload/resumable/'):
                key = (self.uploads.get(p.rsplit('/', 1)[1]) or {}).get('key')
            if key and any(x in key for x in self.marks()):
                with self.lock:
                    self.calls.append((req.method, req.url.host, p))
                return httpx.Response(400, json={'statusCode': '400', 'error': 'Bad Request', 'message': SAID})
        return super().__call__(req)
