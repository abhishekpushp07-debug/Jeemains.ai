"""TEST-ONLY bridge (iteration 161) for Owner Reset PIN UI. Real app routes with REAL auth, lifespan off,
random isolated DB tejas_isolated_iter161_<hex> (dropped on start/stop). Seeds synthetic owner/reviewer (random pw),
2 synthetic PIN students (random PIN) + 1 legacy v0 profile. Creds -> /tmp/iter161_creds.json (0600, deleted on stop).
Port 8796. Run: cd /app/backend/tests && timeout 900 python iso_bridge_iter161.py > /tmp/iter161_bridge.log 2>&1 &
"""
import asyncio, json, os, secrets, uuid
import uvicorn
import iso_harness_iter161 as H
from tejas import auth

CREDS = '/tmp/iter161_creds.json'
C = {'owner_email': 'test161-owner@example.com', 'owner_pw': 'T161-' + secrets.token_urlsafe(14),
     'rev_email': 'test161-rev@example.com', 'rev_pw': 'T161-' + secrets.token_urlsafe(14), 'origin': H.ORIGIN,
     'students': []}


async def wrapper(scope, receive, send):
    if scope['type'] == 'http' and scope['path'] == '/__test/state':
        profs = await H.TDB.tejas_phone_profiles.find({}, {'_id': 0, 'pin_hash': 0}).to_list(None)
        body = json.dumps({'db': H.TEST_DB, 'profiles': profs, 'leftover': H.leftover_real_handles(),
                           'student_sessions': await H.TDB.tejas_sessions.count_documents({'access_type': 'unverified_phone'})}).encode()
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
    for i, legacy in enumerate([False, False, True]):
        sid, ph, p = str(uuid.uuid4()), f'+9199161{i:05d}', f'{secrets.randbelow(10000):04d}'
        doc = {'_id': sid, 'id': sid, 'phone': ph, 'name': 'TEST Learner', 'created_at': 1.0}
        if not legacy:
            doc.update({'role': 'student', 'access_type': 'unverified_phone', 'pin_hash': auth.hashpw(p), 'pin_version': 1})
        await H.TDB.tejas_phone_profiles.insert_one(doc)
        C['students'].append({'id': sid, 'phone': ph, 'pin': None if legacy else p, 'legacy': legacy})
    fd = os.open(CREDS, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as f:
        json.dump(C, f)
    print('READY', H.TEST_DB, flush=True)


if __name__ == '__main__':
    loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(setup())
        loop.run_until_complete(uvicorn.Server(uvicorn.Config(wrapper, host='127.0.0.1', port=8796, log_level='warning', lifespan='off')).serve())
    finally:
        loop.run_until_complete(H.tdbmod.client.drop_database(H.TEST_DB))
        if os.path.exists(CREDS):
            os.remove(CREDS)
        print('DROPPED', H.TEST_DB not in loop.run_until_complete(H.tdbmod.client.list_database_names()), flush=True)
