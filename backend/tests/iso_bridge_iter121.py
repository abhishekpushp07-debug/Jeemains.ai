"""TEST-ONLY bridge (iteration 121) for the JeeTransferPanel UI. NOT production evidence.
Isolated DB tejas_isolated_iter105_test (dropped on start and by tester afterwards). Auth: X-Test-User header (MOCKED).
Storage: in-memory GET mock + TEST-ONLY hash shim (see test_iter121_jee_transfer_isolated.py). Real storage blocked.
Controls (files): /tmp/iter121_fail containing size|hash|storage_error makes PDF checks fail; /tmp/iter121_delay seconds.
Port 8767, lifespan off. Run: cd /app/backend/tests && python iso_bridge_iter121.py &
"""
import asyncio, hashlib, os, time, types
import uvicorn
import iso_harness as H
import tejas_storage
from tejas import jee_transfer as J

REAL = hashlib
MAP = {}
BY_PATH = {f['path']: f for f in J.load_bundle()['tejas_files']}
CALLS = []


def ctl(name, default=''):
    try:
        return open('/tmp/iter121_' + name).read().strip()
    except OSError:
        return default


def fake_storage(method, path, data=None, content_type=None):
    if method != 'GET':
        raise RuntimeError('TEST GUARD')
    CALLS.append(path)
    time.sleep(float(ctl('delay', '0.1') or 0))
    f, fail = BY_PATH[path], ctl('fail')
    if fail == 'storage_error':
        raise tejas_storage.StorageError('mock outage')
    raw = b'%PDF-' + path.encode()
    raw = raw + b'\0' * (f['size'] - len(raw))
    if fail == 'hash':
        raw = raw[:-1] + b'\1'
    else:
        MAP[REAL.sha256(raw).hexdigest()] = f['sha256']
    return types.SimpleNamespace(content=raw)


class Shim:
    @staticmethod
    def sha256(b=b''):
        h = REAL.sha256(b).hexdigest()
        return types.SimpleNamespace(hexdigest=lambda: MAP.get(h, h))


def blocked(*a, **k):
    raise RuntimeError('TEST GUARD: real storage blocked')


J.storage_request, J.hashlib, tejas_storage.request = fake_storage, Shim, blocked
OWNER = {'id': 'TEST_U121_owner', 'role': 'owner', 'name': 'TEST Owner 121', 'email': 'abhishekpushp07@gmail.com', 'access_type': 'password'}
H.USERS.update({'owner': OWNER,
                'reviewer': {'id': 'TEST_U121_rev', 'role': 'reviewer', 'name': 'TEST Reviewer', 'email': 'r121@example.invalid', 'access_type': 'password'},
                'student': {'id': 'TEST_U121_st', 'role': 'student', 'name': 'TEST Student', 'phone': '9900000121', 'access_type': 'phone', 'exam': 'JEE Main'}})


async def seed():
    assert H.TEST_DB != H.REAL_DB and not H.leftover_real_handles()
    await H.tdbmod.client.drop_database(H.TEST_DB)
    await H.tdbmod.indexes()
    print('SEED121 ok', flush=True)


if __name__ == '__main__':
    loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
    loop.run_until_complete(seed())
    loop.run_until_complete(uvicorn.Server(uvicorn.Config(H.app, host='127.0.0.1', port=8767, log_level='warning', lifespan='off')).serve())
