"""TEST-ONLY iteration 154: REAL student PIN signup/login/change + owner student directory + staff regression.
Real HTTP boundary (httpx ASGITransport over the real FastAPI app, real JWT cookies, NO auth.current override),
isolated DB tejas_isolated_iter154 (dropped before/after). Synthetic random credentials only.
Run (foreground): cd /app/backend/tests && python -m pytest test_iter154_pin_auth_isolated.py -p no:cacheprovider -q
"""
import asyncio, secrets, time, uuid
import httpx, pytest, bcrypt
import iso_harness_iter154 as H
from tejas import auth, phone as PH

LOOP = asyncio.new_event_loop()
asyncio.set_event_loop(LOOP)
run = LOOP.run_until_complete
TDB = H.TDB
OWNER_PW = 'T154-' + secrets.token_urlsafe(14)
REV_PW = 'T154-' + secrets.token_urlsafe(14)
OWNER = {'id': str(uuid.uuid4()), 'email': 'test154-owner@example.com', 'role': 'owner'}
REV = {'id': str(uuid.uuid4()), 'email': 'test154-rev@example.com', 'role': 'reviewer'}
CTX = {}


def pin():
    return f'{secrets.randbelow(10000):04d}'


_n = [0]


def num():
    _n[0] += 1
    return f'99015{_n[0]:05d}'


def fresh_window():
    H.OFFSET[0] += 1800  # move app clock into an unused 15-minute limiter window


def client(peer=('127.0.0.1', 123)):
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=H.app, raise_app_exceptions=False, client=peer),
                             base_url='https://api.test.example', headers={'Origin': H.ORIGIN}, timeout=60)


def J(r):
    j = r.json()
    return j.get('data') if isinstance(j, dict) and 'data' in j and 'meta' in j else j


async def signup(c, phone, p):
    return await c.post('/api/auth/phone/signup', json={'phone': phone, 'pin': p, 'confirm_pin': p})


@pytest.fixture(scope='module', autouse=True)
def isolated():
    assert H.TEST_DB != H.REAL_DB and not H.leftover_real_handles() and not H.app.dependency_overrides
    run(H.tdbmod.client.drop_database(H.TEST_DB))
    run(H.tdbmod.indexes())
    for u, pw in [(OWNER, OWNER_PW), (REV, REV_PW)]:
        run(TDB.tejas_users.insert_one({**u, 'name': 'TEST ' + u['role'], 'exam': 'JEE Main', 'access_type': 'staff_password',
                                        'password_hash': auth.hashpw(pw), 'created_at': 0}))
    yield
    run(H.tdbmod.client.drop_database(H.TEST_DB))
    assert H.TEST_DB not in run(H.tdbmod.client.list_database_names())


# ---------- signup ----------
def test_signup_normalizes_bcrypt_no_leak_and_cookies():
    async def go():
        fresh_window()
        async with client() as c:
            p = pin(); raw = '0' + num()
            r = await signup(c, raw, p)
            assert r.status_code == 200, r.text
            u = J(r)
            assert set(u) <= {'id', 'name', 'phone', 'role', 'exam', 'access_type', 'pin_configured'}, u
            assert u['phone'] == '+91' + raw[1:] and u['role'] == 'student' and u['pin_configured'] is True
            assert 'pin' not in r.text.replace('pin_configured', '') and p not in r.text
            sc = r.headers.get_list('set-cookie')
            assert any(s.startswith('access_token=') and 'HttpOnly' in s and 'Secure' in s for s in sc)
            doc = await TDB.tejas_phone_profiles.find_one({'phone': u['phone']})
            assert doc['pin_hash'].startswith('$2b$') and doc['id'] == u['id'] and doc['pin_version'] == 1
            me = J(await c.get('/api/auth/me'))
            assert me['id'] == u['id'] and me['phone'] == u['phone']
            CTX['s1'] = (u['phone'], p, u['id'])
    run(go())


@pytest.mark.parametrize('payload,code', [
    ({'pin': '12a4', 'confirm_pin': '12a4'}, 422), ({'pin': '123', 'confirm_pin': '123'}, 422),
    ({'pin': '12345', 'confirm_pin': '12345'}, 422), ({'pin': '1234', 'confirm_pin': '1235'}, 422),
    ({'pin': '١٢٣٤', 'confirm_pin': '١٢٣٤'}, 422), ({'pin': '1234\n', 'confirm_pin': '1234\n'}, 422),
    ({'pin': 1234, 'confirm_pin': 1234}, 422), ({'pin': '1234', 'confirm_pin': '1234', 'role': 'owner'}, 422),
    ({'pin': '1234', 'confirm_pin': '1234', 'pin_version': 9}, 422), ({'pin': '1234'}, 422),
])
def test_signup_invalid_inputs_rejected(payload, code):
    async def go():
        async with client() as c:
            phone = num()
            r = await c.post('/api/auth/phone/signup', json={'phone': phone, **payload})
            assert r.status_code == code, r.text
            assert await TDB.tejas_phone_profiles.count_documents({'phone': '+91' + phone}) == 0
    run(go())


def test_leading_zero_pin_and_duplicate_and_legacy_not_claimable():
    async def go():
        fresh_window()
        async with client() as c:
            phone = num()
            assert (await signup(c, phone, '0007')).status_code == 200
        async with client() as c:
            assert (await c.post('/api/auth/phone', json={'phone': phone, 'pin': '0007'})).status_code == 200
            assert (await c.post('/api/auth/phone', json={'phone': phone, 'pin': '7'})).status_code == 422
            d = await signup(c, '+91 ' + phone, '1111')
            assert d.status_code == 409
            # legacy (pre-PIN) profile
            legacy = num(); lid = str(uuid.uuid4())
            await TDB.tejas_phone_profiles.insert_one({'_id': lid, 'id': lid, 'phone': '+91' + legacy, 'name': 'Learner',
                                                       'role': 'student', 'access_type': 'unverified_phone', 'created_at': 0})
            assert (await signup(c, legacy, '2222')).status_code == 409
            r = await c.post('/api/auth/phone', json={'phone': legacy, 'pin': '2222'})
            assert r.status_code == 401
            doc = await TDB.tejas_phone_profiles.find_one({'id': lid})
            assert 'pin_hash' not in doc
            CTX['legacy'] = (legacy, lid)
    run(go())


def test_login_wrong_pin_and_correct_pin():
    phone, p, sid = CTX['s1']
    async def go():
        fresh_window()
        async with client() as c:
            bad = '9999' if p != '9999' else '8888'
            assert (await c.post('/api/auth/phone', json={'phone': phone, 'pin': bad})).status_code == 401
            assert (await c.post('/api/auth/phone', json={'phone': phone})).status_code == 422
            r = await c.post('/api/auth/phone', json={'phone': phone, 'pin': p, 'role': 'owner'})
            assert r.status_code == 422
            r = await c.post('/api/auth/phone', json={'phone': phone, 'pin': p})
            assert r.status_code == 200 and J(r)['id'] == sid and J(r)['role'] == 'student'
    run(go())


def test_account_rate_limit_429_retry_after():
    async def go():
        fresh_window()
        async with client() as c:
            phone = num()
            codes = [(await c.post('/api/auth/phone', json={'phone': phone, 'pin': '1234'})) for _ in range(6)]
            assert [r.status_code for r in codes[:5]] == [401] * 5
            assert codes[5].status_code == 429 and int(codes[5].headers['retry-after']) >= 1
            fresh_window()
            assert (await c.post('/api/auth/phone', json={'phone': phone, 'pin': '1234'})).status_code == 401
    run(go())


def test_successful_logins_reset_account_limit():
    """iter155: success resets the per-number key, so repeated successful logins are never 429."""
    phone, p, _ = CTX['s1']
    async def go():
        fresh_window()
        async with client() as c:
            codes = [(await c.post('/api/auth/phone', json={'phone': phone, 'pin': p})).status_code for _ in range(6)]
            CTX['success_limit_codes'] = codes
            print('6 successful logins ->', codes)
            assert codes == [200] * 6, codes
    run(go())


def test_ip_rate_limit_60():
    """iter155: IP guard applies only to a direct GLOBAL ASGI peer (1.1.1.1); private/loopback peers are not IP-bucketed."""
    async def go():
        fresh_window()
        async with client(('1.1.1.1', 4444)) as c:
            codes = []
            for i in range(61):
                codes.append((await c.post('/api/auth/phone', json={'phone': num(), 'pin': '1234'})).status_code)
            assert codes[:60] == [401] * 60 and codes[60] == 429, codes[-3:]
    run(go())


# ---------- PIN change ----------
def test_pin_change_permissions():
    phone, p, _ = CTX['s1']
    async def go():
        fresh_window()
        async with client() as c:
            body = {'phone': phone, 'new_pin': '4321', 'confirm_pin': '4321'}
            assert (await c.post('/api/auth/pin', json=body)).status_code == 401
            c.cookies.set('access_token', 'not.a.jwt', domain='api.test.example')
            assert (await c.post('/api/auth/pin', json=body)).status_code == 401
        async with client() as c:  # other student
            other = num(); assert (await signup(c, other, '1212')).status_code == 200
            assert (await c.post('/api/auth/pin', json=body)).status_code == 403
            r = await c.post('/api/auth/pin', json={**body, 'pin_version': 0})
            assert r.status_code == 422
            r = await c.post('/api/auth/pin', json={'phone': other, 'new_pin': '1234', 'confirm_pin': '4321'})
            assert r.status_code == 422
        for email, pw in [(OWNER['email'], OWNER_PW), (REV['email'], REV_PW)]:
            async with client() as c:
                assert (await c.post('/api/auth/login', json={'email': email, 'password': pw})).status_code == 200
                assert (await c.post('/api/auth/pin', json=body)).status_code == 403
        doc = await TDB.tejas_phone_profiles.find_one({'phone': phone})
        assert doc['pin_version'] == 1 and bcrypt.checkpw(p.encode(), doc['pin_hash'].encode())
    run(go())


def test_pin_change_revokes_old_sessions_and_new_cookie_works():
    phone, p, sid = CTX['s1']
    async def go():
        fresh_window()
        a, b = client(), client()
        async with a, b:
            assert (await a.post('/api/auth/phone', json={'phone': phone, 'pin': p})).status_code == 200
            assert (await b.post('/api/auth/phone', json={'phone': phone, 'pin': p})).status_code == 200
            old_b = dict(b.cookies)
            new = '0420' if p != '0420' else '0421'
            r = await a.post('/api/auth/pin', json={'phone': phone, 'new_pin': new, 'confirm_pin': new})
            assert r.status_code == 200, r.text
            assert J(r)['id'] == sid and J(r)['pin_configured'] is True and 'pin_hash' not in r.text
            assert (await a.get('/api/auth/me')).status_code == 200  # new issued cookie
            assert (await b.get('/api/auth/me')).status_code == 401
            assert (await b.post('/api/auth/refresh')).status_code == 401
            assert J(await b.get('/api/auth/session'))['user'] is None
        async with client() as c:
            for k, v in old_b.items():
                c.cookies.set(k, v, domain='api.test.example')
            assert (await c.post('/api/auth/refresh')).status_code == 401
            assert (await c.post('/api/auth/phone', json={'phone': phone, 'pin': p})).status_code == 401
            assert (await c.post('/api/auth/phone', json={'phone': phone, 'pin': new})).status_code == 200
        CTX['s1'] = (phone, new, sid)
    run(go())


def test_concurrent_pin_changes_cas():
    async def go():
        fresh_window()
        async with client() as c:
            phone = num(); assert (await signup(c, phone, '1357')).status_code == 200
            rs = await asyncio.gather(*[c.post('/api/auth/pin', json={'phone': phone, 'new_pin': x, 'confirm_pin': x})
                                        for x in ('1111', '2222', '3333')])
            codes = sorted(r.status_code for r in rs)
            doc = await TDB.tejas_phone_profiles.find_one({'phone': '+91' + phone})
            print('concurrent codes', codes, 'version', doc['pin_version'])
            assert codes.count(200) == 1 and doc['pin_version'] == 2
            winner = [x for x, r in zip(('1111', '2222', '3333'), rs) if r.status_code == 200][0]
            assert bcrypt.checkpw(winner.encode(), doc['pin_hash'].encode())
    run(go())


def test_delayed_old_login_session_rejected():
    phone, p, sid = CTX['s1']
    async def go():
        doc = await TDB.tejas_phone_profiles.find_one({'id': sid}, {'_id': 0})
        stale = {**doc, 'pin_version': doc['pin_version'] - 1}
        resp = httpx.Response(200)
        from fastapi import Response, HTTPException
        before = await TDB.tejas_sessions.count_documents({'user_id': sid})
        CTX['stale_rows_after_change'] = await TDB.tejas_sessions.count_documents({'user_id': sid, 'pin_version': {'$lt': doc['pin_version']}})
        print('old-version session rows physically retained after change:', CTX['stale_rows_after_change'])
        with pytest.raises(HTTPException) as e:
            await auth.new_session(stale, Response())
        assert e.value.status_code == 401
        assert await TDB.tejas_sessions.count_documents({'user_id': sid}) == before
        # delayed physical insertion of an old-version session after change: unusable
        old_sid = str(uuid.uuid4())
        from datetime import datetime, timezone, timedelta
        await TDB.tejas_sessions.insert_one({'id': old_sid, 'user_id': sid, 'access_type': 'unverified_phone',
                                             'pin_version': doc['pin_version'] - 1, 'expires_at': datetime.now(timezone.utc) + timedelta(days=1)})
        async with client() as c:
            u = {'id': sid, 'access_type': 'unverified_phone'}
            c.cookies.set('access_token', auth.token(u, old_sid, 'access', 600), domain='api.test.example')
            c.cookies.set('refresh_token', auth.token(u, old_sid, 'refresh', 600), domain='api.test.example')
            assert (await c.get('/api/auth/me')).status_code == 401
            assert (await c.post('/api/auth/refresh')).status_code == 401
    run(go())


def test_legacy_session_enrolls_pin_without_id_change():
    legacy, lid = CTX['legacy']
    async def go():
        fresh_window()
        from datetime import datetime, timezone, timedelta
        await TDB.tejas_attempts.insert_one({'_id': 'TEST154_att', 'id': 'TEST154_att', 'user_id': lid, 'status': 'completed'})
        old_sid = str(uuid.uuid4())
        await TDB.tejas_sessions.insert_one({'id': old_sid, 'user_id': lid, 'access_type': 'unverified_phone',
                                             'expires_at': datetime.now(timezone.utc) + timedelta(days=1)})
        async with client() as c:
            u = {'id': lid, 'access_type': 'unverified_phone'}
            c.cookies.set('access_token', auth.token(u, old_sid, 'access', 600), domain='api.test.example')
            me = await c.get('/api/auth/me')
            assert me.status_code == 200 and J(me)['pin_configured'] is False and J(me)['role'] == 'student'
            r = await c.post('/api/auth/pin', json={'phone': legacy, 'new_pin': '0550', 'confirm_pin': '0550'})
            assert r.status_code == 200 and J(r)['id'] == lid and J(r)['pin_configured'] is True
        async with client() as c:
            r = await c.post('/api/auth/phone', json={'phone': legacy, 'pin': '0550'})
            assert r.status_code == 200 and J(r)['id'] == lid
        assert await TDB.tejas_attempts.count_documents({'user_id': lid}) == 1
    run(go())


def test_student_role_forced_even_if_profile_field_tampered():
    phone, p, sid = CTX['s1']
    async def go():
        fresh_window()
        await TDB.tejas_phone_profiles.update_one({'id': sid}, {'$set': {'role': 'owner'}})
        try:
            async with client() as c:
                r = await c.post('/api/auth/phone', json={'phone': phone, 'pin': p})
                assert r.status_code == 200 and J(r)['role'] == 'student', r.text
                assert (await c.get('/api/admin/students')).status_code == 403
                assert (await c.get('/api/studio/sets')).status_code in (403, 404)
        finally:
            await TDB.tejas_phone_profiles.update_one({'id': sid}, {'$set': {'role': 'student', 'access_type': 'unverified_phone'}})
        # access_type tamper must fail closed (never staff)
        await TDB.tejas_phone_profiles.update_one({'id': sid}, {'$set': {'access_type': 'staff_password'}})
        try:
            async with client() as c:
                r = await c.post('/api/auth/phone', json={'phone': phone, 'pin': p})
                print('access_type tamper login ->', r.status_code)
                assert r.status_code in (200, 401) and (r.status_code == 401 or J(r)['role'] == 'student')
        finally:
            await TDB.tejas_phone_profiles.update_one({'id': sid}, {'$set': {'access_type': 'unverified_phone'}})
    run(go())


def test_legacy_profile_without_access_type_field_can_set_pin():
    async def go():
        fresh_window()
        from datetime import datetime, timezone, timedelta
        legacy = num(); lid = str(uuid.uuid4())
        await TDB.tejas_phone_profiles.insert_one({'_id': lid, 'id': lid, 'phone': '+91' + legacy, 'name': 'Learner', 'created_at': 0})
        old_sid = str(uuid.uuid4())
        await TDB.tejas_sessions.insert_one({'id': old_sid, 'user_id': lid, 'access_type': 'unverified_phone',
                                             'expires_at': datetime.now(timezone.utc) + timedelta(days=1)})
        async with client() as c:
            u = {'id': lid, 'access_type': 'unverified_phone'}
            c.cookies.set('access_token', auth.token(u, old_sid, 'access', 600), domain='api.test.example')
            assert (await c.get('/api/auth/me')).status_code == 200
            r = await c.post('/api/auth/pin', json={'phone': legacy, 'new_pin': '0660', 'confirm_pin': '0660'})
            doc = await TDB.tejas_phone_profiles.find_one({'id': lid})
            print('legacy-no-access_type change ->', r.status_code, r.text[:160], 'db pin_version', doc.get('pin_version'))
            CTX['legacy_noat'] = r.status_code
        async with client() as c:
            r2 = await c.post('/api/auth/phone', json={'phone': legacy, 'pin': '0660'})
            print('legacy-no-access_type login ->', r2.status_code, r2.text[:160])
        assert r.status_code == 200 and r2.status_code == 200
    run(go())


# ---------- Super Admin directory ----------
def test_admin_students_access_matrix_and_allowlist():
    async def go():
        fresh_window()
        base = await TDB.tejas_phone_profiles.count_documents({})
        for i in range(55 - base if base < 55 else 0):
            sid = str(uuid.uuid4())
            await TDB.tejas_phone_profiles.insert_one({'_id': sid, 'id': sid, 'phone': f'+9198154{i:05d}', 'name': 'SECRET NAME',
                                                       'email': 'secret@example.invalid', 'pin_hash': '$2b$12$xxxx', 'pin_version': 1,
                                                       'role': 'student', 'access_type': 'unverified_phone'})
        total = await TDB.tejas_phone_profiles.count_documents({})
        async with client() as c:
            assert (await c.get('/api/admin/students')).status_code == 401
        async with client() as c:
            assert (await signup(c, num(), '1234')).status_code == 200
            total += 1
            r = await c.get('/api/admin/students', headers={'X-Role': 'owner', 'X-Test-User': 'w'})
            assert r.status_code == 403
        async with client() as c:
            assert (await c.post('/api/auth/login', json={'email': REV['email'], 'password': REV_PW})).status_code == 200
            assert (await c.get('/api/admin/students')).status_code == 403
        async with client() as c:
            assert (await c.post('/api/auth/login', json={'email': OWNER['email'], 'password': OWNER_PW})).status_code == 200
            r = await c.get('/api/admin/students')
            assert r.status_code == 200 and 'no-store' in r.headers.get('cache-control', '')
            d = J(r)
            assert d['total'] == total and d['pages'] == -(-total // 50) and len(d['items']) == 50
            assert all(set(x) == {'id', 'phone'} for x in d['items'])
            for leak in ('SECRET', 'secret@', '$2b$', 'pin_hash', '"_id"', 'name', 'email'):
                assert leak not in r.text
            p2 = J(await c.get('/api/admin/students?page=2'))
            assert len(p2['items']) == total - 50 and not {x['id'] for x in p2['items']} & {x['id'] for x in d['items']}
            s = J(await c.get('/api/admin/students', params={'q': '98154 00003'}))
            assert s['total'] == 1 and s['items'][0]['phone'] == '+919815400003'
            assert J(await c.get('/api/admin/students', params={'q': '+0000000000'}))['total'] == 0
            for bad in ['.*', 'abc', '1' * 33, '$ne', '[0-9]']:
                assert (await c.get('/api/admin/students', params={'q': bad})).status_code == 422, bad
            for bad in ['0', '-1', 'x', '10001']:
                assert (await c.get('/api/admin/students', params={'page': bad})).status_code == 422, bad
            assert (await c.get('/api/admin/students?page=999')).status_code == 200
            assert await TDB.tejas_audits.count_documents({'action': 'student_directory_read'}) >= 1
            # immediate role revocation
            await TDB.tejas_users.update_one({'id': OWNER['id']}, {'$set': {'role': 'reviewer'}})
            assert (await c.get('/api/admin/students')).status_code == 403
            await TDB.tejas_users.update_one({'id': OWNER['id']}, {'$set': {'role': 'owner'}})
            assert (await c.get('/api/admin/students')).status_code == 200
            # owner session cannot enter student PIN plane, cannot login as a student
            assert (await c.post('/api/auth/phone', json={'phone': 'test154-owner@example.com', 'pin': '1234'})).status_code == 422
    run(go())


# ---------- staff / CORS / contracts regression ----------
def test_staff_login_cors_and_contracts():
    async def go():
        fresh_window()
        async with client() as c:
            r = await c.post('/api/auth/login', json={'email': OWNER['email'], 'password': OWNER_PW})
            assert r.status_code == 200 and J(r)['role'] == 'owner' and 'password_hash' not in r.text and OWNER_PW not in r.text
            assert r.headers.get('access-control-allow-origin') == H.ORIGIN
            assert r.headers.get('access-control-allow-credentials') == 'true'
            bad = await c.post('/api/auth/phone', json={'phone': num(), 'pin': '1234'}, headers={'Origin': 'https://evil.example'})
            assert bad.status_code == 403
            assert (await c.post('/api/auth/register', json={})).status_code == 410
            assert (await c.post('/api/auth/login', json={'email': OWNER['email'], 'password': 'wrong-pass-1'})).status_code == 401
        keys = {c.key for c in H.app.state.route_contracts} if hasattr(H.app.state, 'route_contracts') else None
        if keys is None:
            from tejas import route_contracts as RC
            keys = {c.key for c in RC.build(H.app)} if hasattr(RC, 'build') else set()
        print('contract keys present:', {'phone.access', 'phone.signup', 'phone.change_pin', 'students.list_students'} <= keys)
        spec = H.app.openapi()
        for path in ['/api/auth/phone', '/api/auth/phone/signup', '/api/auth/pin', '/api/admin/students']:
            assert path in spec['paths'], path
            op = next(iter(spec['paths'][path].values()))
            assert 'x-owner-policy' in op, path
    run(go())


def test_zz_no_real_handles_and_no_puts():
    assert not H.leftover_real_handles() and not H.PUTS and not H.app.dependency_overrides


def test_staff_rotation_gate_still_works_and_student_unaffected():
    from tejas.staff_credentials import rotate_staff_credential
    phone, p, sid = CTX['s1']
    async def go():
        fresh_window()
        async with client() as rv, client() as st:
            assert (await rv.post('/api/auth/login', json={'email': REV['email'], 'password': REV_PW})).status_code == 200
            assert (await st.post('/api/auth/phone', json={'phone': phone, 'pin': p})).status_code == 200
            newpw = 'T154R-' + secrets.token_urlsafe(16)
            rc = await rotate_staff_credential(REV['id'], 0, newpw, str(uuid.uuid4()))
            assert rc.new_generation == 1 and rc.physical_cleanup == 'COMPLETE'
            assert (await rv.get('/api/auth/me')).status_code == 401
            assert (await st.get('/api/auth/me')).status_code == 200
            async with client() as c2:
                assert (await c2.post('/api/auth/login', json={'email': REV['email'], 'password': REV_PW})).status_code == 401
                assert (await c2.post('/api/auth/login', json={'email': REV['email'], 'password': newpw})).status_code == 200
                assert (await c2.get('/api/auth/me')).status_code == 200
    run(go())
