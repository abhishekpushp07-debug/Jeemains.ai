"""TEST-ONLY iteration 164: tejas_storage source-cache singleflight / byte-bound eviction / PUT invalidation.
Storage boundary (tejas_storage.request) is MOCKED in-process; no network, no real object-store writes.
"""
import sys, threading, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tejas_storage as S  # noqa: E402
from tejas.cache import ByteCache  # noqa: E402


class R:
    def __init__(self, c): self.content = c
    def json(self): return {'path': 'p'}


@pytest.fixture
def fake(monkeypatch):
    calls = {'GET': [], 'PUT': []}; state = {'fail_get': False, 'fail_put': False, 'blob': b'A' * 1000}
    def req(method, path, data=None, content_type=None):
        calls[method].append(path); time.sleep(0.05)
        if method == 'GET':
            if state['fail_get']: raise S.StorageError('boom')
            return R(state['blob'] + path.encode())
        if state['fail_put']: raise S.StorageError('put boom')
        return R(b'')
    monkeypatch.setattr(S, 'request', req)
    monkeypatch.setattr(S, '_source_cache', ByteCache(64 * 1024 * 1024))
    return calls, state


def test_singleflight_same_path(fake):
    calls, _ = fake
    with ThreadPoolExecutor(10) as ex:
        out = list(ex.map(lambda _: S.get_object('x.pdf'), range(10)))
    assert len(calls['GET']) == 1 and len(set(out)) == 1


def test_distinct_paths_each_fetched_once(fake):
    calls, _ = fake
    with ThreadPoolExecutor(10) as ex:
        list(ex.map(lambda i: S.get_object(f'p{i % 3}.pdf'), range(30)))
    assert sorted(calls['GET']) == ['p0.pdf', 'p1.pdf', 'p2.pdf']


def test_failure_not_cached(fake):
    calls, state = fake
    state['fail_get'] = True
    for _ in range(2):
        with pytest.raises(S.StorageError):
            S.get_object('f.pdf')
    state['fail_get'] = False
    assert S.get_object('f.pdf').endswith(b'f.pdf') and len(calls['GET']) == 3


def test_put_invalidates_only_on_success(fake):
    calls, state = fake
    S.get_object('k.pdf'); state['blob'] = b'B' * 1000
    state['fail_put'] = True
    with pytest.raises(S.StorageError):
        S.put_object('k.pdf', b'new')
    assert S.get_object('k.pdf').startswith(b'A')  # failed PUT keeps cache
    state['fail_put'] = False
    S.put_object('k.pdf', b'new')
    assert S.get_object('k.pdf').startswith(b'B') and len(calls['GET']) == 2


def test_byte_bound_eviction():
    c = ByteCache(3000)
    for i in range(5):
        c.put(str(i), b'x' * 1000)
    assert c.size <= 3000 and c.get('0') is None and c.get('4') is not None
    c.remove('4'); c.remove('4'); c.remove('missing')
    assert c.size == sum(len(v) for v in c.data.values())
