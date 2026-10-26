"""TEST-ONLY bridge (iteration 154). Real app routes with REAL auth (no current override), lifespan off,
isolated DB tejas_isolated_iter155 (dropped on start/stop). Storage GET -> local source PDFs, PUT forbidden.
Seeds: synthetic owner/reviewer (random pw), synthetic student (random PIN), 55 synthetic directory numbers,
reviewed PYQ bundle via REAL owner /api/studio/pyq-import/step, own attempt fixtures for the student.
Creds -> /tmp/iter155_creds.json (0600, deleted on stop). Port 8793.
Run: cd /app/backend/tests && timeout 1800 python iso_bridge_iter155.py &
"""
import asyncio, json, os, secrets, uuid
import httpx, uvicorn
import iso_harness_iter155 as H
from tejas import auth

CREDS = '/tmp/iter155_creds.json'
C = {'owner_email': 'test155-owner@example.com', 'owner_pw': 'T155-' + secrets.token_urlsafe(14),
     'rev_email': 'test155-rev@example.com', 'rev_pw': 'T155-' + secrets.token_urlsafe(14),
     'student_phone': '9901700001', 'student_pin': f'{secrets.randbelow(10000):04d}', 'new_pin': f'{secrets.randbelow(10000):04d}'}


def J(r):
    j = r.json()
    return j.get('data') if isinstance(j, dict) and 'data' in j and 'meta' in j else j


async def wrapper(scope, receive, send):
    if scope['type'] == 'http' and scope['path'] == '/__test/state':
        body = json.dumps({'db': H.TEST_DB, 'sets': await H.TDB.tejas_sets.count_documents({'test_kind': 'pyq'}),
                           'students': await H.TDB.tejas_phone_profiles.count_documents({}), 'puts': H.PUTS,
                           'leftover': H.leftover_real_handles()}).encode()
        await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-type', b'application/json')]})
        return await send({'type': 'http.response.body', 'body': body})
    return await H.app(scope, receive, send)


async def setup():
    assert H.TEST_DB != H.REAL_DB and not H.leftover_real_handles() and not H.app.dependency_overrides
    await H.tdbmod.client.drop_database(H.TEST_DB)
    await H.tdbmod.indexes()
    for email, pw, role in [(C['owner_email'], C['owner_pw'], 'owner'), (C['rev_email'], C['rev_pw'], 'reviewer')]:
        await H.TDB.tejas_users.insert_one({'id': str(uuid.uuid4()), 'email': email, 'name': 'TEST ' + role, 'role': role,
            'exam': 'JEE Main', 'access_type': 'staff_password', 'password_hash': auth.hashpw(pw), 'created_at': 0})
    for i in range(55):
        sid = str(uuid.uuid4())
        await H.TDB.tejas_phone_profiles.insert_one({'_id': sid, 'id': sid, 'phone': f'+9198154{i:05d}', 'name': 'Learner',
            'role': 'student', 'access_type': 'unverified_phone', 'pin_hash': '$2b$12$' + 'x' * 53, 'pin_version': 1})
    tr = httpx.ASGITransport(app=H.app)
    async with httpx.AsyncClient(transport=tr, base_url='https://api.test.example', headers={'Origin': H.ORIGIN}, timeout=300) as c:
        assert (await c.post('/api/auth/login', json={'email': C['owner_email'], 'password': C['owner_pw']})).status_code == 200
        for _ in range(120):
            v = J(await c.post('/api/studio/pyq-import/step', json={}))
            if v.get('phase') == 'complete':
                break
        print('IMPORT', {k: v.get(k) for k in ('phase', 'imported', 'sets') if isinstance(v, dict)}, flush=True)
    async with httpx.AsyncClient(transport=tr, base_url='https://api.test.example', headers={'Origin': H.ORIGIN}, timeout=60) as c:
        p = C['student_pin']
        r = await c.post('/api/auth/phone/signup', json={'phone': C['student_phone'], 'pin': p, 'confirm_pin': p})
        assert r.status_code == 200, r.text
        uid_ = J(r)['id']
        cat = J(await c.get('/api/pyq/jee-main'))
        ids = [x['id'] for x in cat['items']]
    now = H.fake_now()
    await H.TDB.tejas_attempts.insert_many([
        {'_id': 'TEST155_active', 'id': 'TEST155_active', 'user_id': uid_, 'set_id': ids[0], 'status': 'active', 'mode': 'exam', 'start_key': 'TEST155-k1',
         'started_at': now - 60, 'deadline': now + 3 * 3600, 'answers': {}},
        {'_id': 'TEST155_done', 'id': 'TEST155_done', 'user_id': uid_, 'set_id': ids[1], 'status': 'completed', 'mode': 'exam', 'start_key': 'TEST155-k2',
         'started_at': now - 7200, 'deadline': now - 3600, 'summary': {'score': 120}, 'answers': {}}])
    C['active_set'], C['done_set'], C['catalogue_total'] = ids[0], ids[1], cat['total']
    fd = os.open(CREDS, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as f:
        json.dump(C, f)
    print('READY total', cat['total'], 'years', cat['years'], flush=True)


if __name__ == '__main__':
    loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(setup())
        loop.run_until_complete(uvicorn.Server(uvicorn.Config(wrapper, host='127.0.0.1', port=8793, log_level='warning', lifespan='off')).serve())
    finally:
        loop.run_until_complete(H.tdbmod.client.drop_database(H.TEST_DB))
        if os.path.exists(CREDS):
            os.remove(CREDS)
        print('DROPPED', H.TEST_DB not in loop.run_until_complete(H.tdbmod.client.list_database_names()), flush=True)
