"""TEST-ONLY bridge (iteration 139) for the PYQ UI. NOT production evidence.
Real app routes (no lifespan/AI/cron) bound to isolated DB tejas_isolated_iter134 (dropped on start/stop).
MOCKED boundaries only: auth (X-Test-User header -> synthetic users) and object storage (GET -> original local PDFs, PUT forbidden).
On start the reviewed bundle is imported through the REAL owner /api/studio/pyq-import/step endpoint.
Port 8791. Run: cd /app/backend/tests && python iso_bridge_pyq_iter139.py &   Stop: kill the process (DB dropped in finally).
"""
import json
import httpx, uvicorn
import test_iter139_pyq_isolated as T  # applies storage boundary patch + synthetic users
H = T.H


async def send_json(send, obj, status=200):
    await send({'type': 'http.response.start', 'status': status, 'headers': [(b'content-type', b'application/json')]})
    await send({'type': 'http.response.body', 'body': json.dumps(obj).encode()})


async def wrapper(scope, receive, send):
    if scope['type'] == 'http' and scope['path'] == '/__test/state':
        return await send_json(send, {'db': H.TEST_DB, 'sets': await H.TDB.tejas_sets.count_documents({}),
                                      'attempts': await H.TDB.tejas_attempts.count_documents({}), 'puts': T.PUTS})
    if scope['type'] == 'http' and scope['path'] == '/api/auth/session':  # MOCKED auth boundary (cookie session -> synthetic user)
        from tejas.auth import view
        user = H.USERS.get(dict(scope['headers']).get(b'x-test-user', b'').decode())
        return await send_json(send, {'data': {'user': view(user) if user else None}, 'error': None, 'meta': {'api_version': '1'}})
    return await H.app(scope, receive, send)


async def setup():
    assert H.TEST_DB != H.REAL_DB and not H.leftover_real_handles()
    await H.tdbmod.client.drop_database(H.TEST_DB)
    await H.tdbmod.indexes()
    async with T.client() as c:
        for _ in range(80):
            v = T.J(await c.post('/api/studio/pyq-import/step', headers=T.W, json={}))
            if v['phase'] == 'complete':
                break
    print('IMPORT', v, flush=True)


if __name__ == '__main__':
    loop = T.LOOP
    loop.run_until_complete(setup())
    try:
        loop.run_until_complete(uvicorn.Server(uvicorn.Config(wrapper, host='127.0.0.1', port=8791, log_level='warning', lifespan='off')).serve())
    finally:
        loop.run_until_complete(H.tdbmod.client.drop_database(H.TEST_DB))
        print('DROPPED', H.TEST_DB not in loop.run_until_complete(H.tdbmod.client.list_database_names()), flush=True)
