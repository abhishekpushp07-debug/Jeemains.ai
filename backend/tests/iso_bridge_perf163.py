"""TEST-ONLY perf163 bridge: isolated DB + PYQ import (local original PDFs) + 1 synthetic PIN student.
Serves the REAL app on 127.0.0.1:8797 for browser waterfall inspection (Playwright proxies /api/** here).
Creds -> /tmp/perf163_creds.json (0600, deleted on stop). Stop with: pkill -INT -f iso_bridge_perf163.py (drops DB).
GET /__test/counters returns harness counters (storage/pdf/crop/db) for the run.
"""
import asyncio, json, os, secrets, uuid
import httpx, uvicorn
import iso_harness_perf163 as H
from tejas import auth

CREDS = '/tmp/perf163_creds.json'
OWNER = {'email': 'perf163b-owner@example.com', 'pw': 'P163B-' + secrets.token_urlsafe(14)}


async def wrapper(scope, receive, send):
    if scope['type'] == 'http' and scope['path'] == '/__test/counters':
        body = json.dumps({'db': H.TEST_DB, **H.snap(), 'rss': H.rss_mb(), 'leftover': H.leftover_real_handles()}).encode()
        await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-type', b'application/json')]})
        return await send({'type': 'http.response.body', 'body': body})
    return await H.app(scope, receive, send)


async def setup():
    assert H.TEST_DB != H.REAL_DB and not H.leftover_real_handles() and not H.app.dependency_overrides
    await H.MCLIENT.drop_database(H.TEST_DB)
    await H.tdbmod.indexes()
    await H.TDB.tejas_users.insert_one({'id': str(uuid.uuid4()), 'email': OWNER['email'], 'name': 'TEST owner', 'role': 'owner',
                                        'exam': 'JEE Main', 'access_type': 'staff_password', 'password_hash': auth.hashpw(OWNER['pw']), 'created_at': 0})
    t = httpx.ASGITransport(app=H.app, client=('127.0.0.1', 9))
    async with httpx.AsyncClient(transport=t, base_url='https://api.test.example', headers={'Origin': H.ORIGIN}, timeout=600) as o:
        assert (await o.post('/api/auth/login', json={'email': OWNER['email'], 'password': OWNER['pw']})).status_code == 200
        for _ in range(200):
            v = (await o.post('/api/studio/pyq-import/step', json={})).json()
            v = v.get('data', v)
            if v.get('phase') == 'complete':
                break
        assert v.get('phase') == 'complete'
        await o.post('/api/auth/logout')
    phone, p = f'99165{secrets.randbelow(10**5):05d}', f'{secrets.randbelow(10000):04d}'
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=H.app, client=('10.9.9.9', 9)), base_url='https://api.test.example', headers={'Origin': H.ORIGIN}) as c:
        assert (await c.post('/api/auth/phone/signup', json={'phone': phone, 'pin': p, 'confirm_pin': p})).status_code == 200
    H.reset_process_caches()
    fd = os.open(CREDS, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as f:
        json.dump({'phone': phone, 'pin': p, 'origin': H.ORIGIN, 'db': H.TEST_DB}, f)
    print('READY', H.TEST_DB, flush=True)


if __name__ == '__main__':
    loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(setup())
        loop.run_until_complete(uvicorn.Server(uvicorn.Config(wrapper, host='127.0.0.1', port=8797, log_level='warning', lifespan='off')).serve())
    finally:
        loop.run_until_complete(H.MCLIENT.drop_database(H.TEST_DB))
        if os.path.exists(CREDS):
            os.remove(CREDS)
        print('DROPPED', H.TEST_DB not in loop.run_until_complete(H.MCLIENT.list_database_names()), flush=True)
