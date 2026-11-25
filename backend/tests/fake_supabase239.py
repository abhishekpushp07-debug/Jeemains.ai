"""TEST-ONLY: the Supabase stand-in of tests/fake_supabase231.py plus two knobs for the picture proof:
`vanish`: a small upload whose path contains one of these is answered 200 but nothing is stored (Supabase says yes, the picture is
not there); `vanish_first` limits it to that many uploads. `list_code`: the folder-list route answers this code. No network."""
from urllib.parse import unquote
import httpx
from fake_supabase231 import Picky

LIST, INFO = '/storage/v1/object/list/', '/storage/v1/object/info/'


class Leaky(Picky):
    def __init__(self, chunk):
        super().__init__(chunk)
        self.vanish, self.vanish_first, self.list_code, self.lost = [], None, None, []

    def __call__(self, req):
        p = unquote(req.url.path)
        if not self.down and not self.block:
            if self.list_code and p.startswith(LIST):
                with self.lock:
                    self.calls.append((req.method, req.url.host, p))
                return httpx.Response(self.list_code, text='list refused')
            if req.method == 'POST' and p.startswith('/storage/v1/object/') and not p.startswith((LIST, INFO)):
                key = p[len('/storage/v1/object/'):]
                if any(x in key for x in self.vanish):
                    with self.lock:
                        hit = self.vanish_first is None or self.vanish_first > 0
                        if hit and self.vanish_first is not None:
                            self.vanish_first -= 1
                        if hit:
                            self.calls.append((req.method, req.url.host, p))
                            self.lost.append(key)
                    if hit:
                        return httpx.Response(200, json={'Key': key})
        return super().__call__(req)
