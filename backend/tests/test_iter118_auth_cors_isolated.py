"""TEST-ONLY iteration 118: CORS + unsafe-write origin fence + REAL auth integration on an ISOLATED DB via in-process ASGI.
Run (env only in the subprocess; .env untouched):
  cd /app/backend/tests && ITER118_EXPECTED='<csv>' FRONTEND_URL=... CORS_ORIGINS=... python -m pytest test_iter118_auth_cors_isolated.py -p no:asyncio -n0
"""
import asyncio, os, re, time, uuid
import httpx, jwt, pytest
import iso_auth_harness_iter118 as A
import server

H = A.H
LOOP = asyncio.new_event_loop()
asyncio.set_event_loop(LOOP)
run = LOOP.run_until_complete
EXPECTED = [o for o in os.environ.get('ITER118_EXPECTED', '').split(',') if o]
ALLOWED = list(server.origins)
CANON = ALLOWED[0]
EVIL = ['https://evil.example', 'https://jeelive.ai.evil.example', 'https://evil-jeelive.ai', 'null', '',
        'https://evil.example/' + CANON, CANON + '.evil.example', CANON + '@evil.example']
EVIL = [o for o in EVIL if o not in ALLOWED and o.rstrip('/') not in ALLOWED]


@pytest.fixture(scope='module', autouse=True)
def isolated_db():
    run(A.seed())
    yield
    run(A.drop())


def client():
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=H.app), base_url='https://api.test.example')


def req(method, path, origin=None, cookies=None, **kw):
    async def go():
        async with client() as c:
            if cookies:
                c.cookies.update(cookies)
            headers = dict(kw.pop('headers', {}) or {})
            if origin is not None:
                headers['Origin'] = origin
            return await c.request(method, path, headers=headers, **kw)
    return run(go())


def set_cookies(r):
    return r.headers.get_list('set-cookie')


def jar(r):
    out = {}
    for sc in set_cookies(r):
        name, val = sc.split(';', 1)[0].split('=', 1)
        out[name] = val.strip('"')
    return out


def err(r):
    return r.json().get('error', {})


# --- config ---
def test_configured_allowlist_matches_expected():
    assert '*' not in ALLOWED
    if EXPECTED:
        assert ALLOWED == EXPECTED, ALLOWED


def test_no_real_db_handles_left():
    assert not H.leftover_real_handles()


# --- unsafe-write fence ---
@pytest.mark.parametrize('origin', EVIL)
@pytest.mark.parametrize('method,path,body', [('POST', '/api/auth/phone', {'phone': '0000000000'}), ('POST', '/api/auth/login', {}),
                                              ('POST', '/api/auth/logout', {}), ('PATCH', '/api/auth/preferences', {'exam': 'BITSAT'}),
                                              ('PUT', '/api/studio/sets/x', {}), ('DELETE', '/api/studio/sets/x', None)])
def test_unrelated_origin_unsafe_403(origin, method, path, body):
    r = req(method, path, origin, json=body) if body is not None else req(method, path, origin)
    assert r.status_code == 403, (origin, r.status_code, r.text[:200])
    assert err(r).get('code') == 'origin_denied'
    assert r.headers.get('access-control-allow-origin') is None


def test_host_forwarded_referer_spoofing_adds_no_trust():
    host = 'evil.example'
    r = req('POST', '/api/auth/phone', 'https://' + host, json={'phone': '0000000000'},
            headers={'Host': host, 'X-Forwarded-Host': host, 'X-Forwarded-Proto': 'https', 'Referer': CANON + '/login', 'Forwarded': 'host=' + host})
    assert r.status_code == 403 and err(r).get('code') == 'origin_denied'


def test_denied_write_creates_no_rows():
    req('POST', '/api/auth/phone', 'https://evil.example', json={'phone': '9900000150'})
    assert run(H.TDB.tejas_phone_limits.count_documents({})) == 0
    assert run(H.TDB.tejas_phone_profiles.count_documents({})) == 0


# --- allowed origins reach validation ---
@pytest.mark.parametrize('idx', range(5))
def test_allowed_origins_reach_validation(idx):
    if idx >= len(ALLOWED):
        pytest.skip('fewer configured origins')
    o = ALLOWED[idx]
    r = req('POST', '/api/auth/phone', o, json={'phone': '0000000000'})
    assert r.status_code == 422, r.text[:200]
    assert 'valid mobile number' in err(r).get('message', '')
    assert r.headers.get('access-control-allow-origin') == o
    assert r.headers.get('access-control-allow-credentials') == 'true'
    r = req('POST', '/api/auth/login', o, json={})
    assert r.status_code == 422 and err(r).get('code') == 'validation_error'


def test_missing_origin_policy_unchanged():
    r = req('POST', '/api/auth/phone', None, json={'phone': '0000000000'})
    assert r.status_code == 422
    assert r.headers.get('access-control-allow-origin') is None


# --- preflight ---
@pytest.mark.parametrize('method', ['POST', 'PUT', 'PATCH', 'DELETE'])
def test_preflight_allowed(method):
    for o in ALLOWED:
        r = req('OPTIONS', '/api/auth/phone', o, headers={'Access-Control-Request-Method': method, 'Access-Control-Request-Headers': 'content-type'})
        assert r.status_code == 200, (o, r.text)
        assert r.headers['access-control-allow-origin'] == o
        assert r.headers['access-control-allow-credentials'] == 'true'
        assert method in r.headers['access-control-allow-methods']


@pytest.mark.parametrize('origin', [o for o in EVIL if o])
def test_preflight_unrelated_400(origin):
    r = req('OPTIONS', '/api/auth/phone', origin, headers={'Access-Control-Request-Method': 'POST', 'Access-Control-Request-Headers': 'content-type'})
    assert r.status_code == 400
    assert r.headers.get('access-control-allow-origin') is None


def test_preflight_disallowed_header_or_method():
    r = req('OPTIONS', '/api/auth/phone', CANON, headers={'Access-Control-Request-Method': 'POST', 'Access-Control-Request-Headers': 'x-evil'})
    assert r.status_code == 400
    r = req('OPTIONS', '/api/auth/phone', CANON, headers={'Access-Control-Request-Method': 'TRACE'})
    assert r.status_code == 400


def test_get_session_unrelated_origin_no_credentials_leak():
    r = req('GET', '/api/auth/session', 'https://evil.example')
    assert r.status_code == 200 and r.json()['data']['user'] is None
    assert r.headers.get('access-control-allow-origin') is None
    r = req('GET', '/api/auth/session', CANON)
    assert r.headers.get('access-control-allow-origin') == CANON
    assert r.headers.get('access-control-allow-origin') != '*'


def test_security_headers_kept():
    r = req('GET', '/api/auth/session', CANON)
    for h in ['x-content-type-options', 'referrer-policy', 'x-request-id', 'cache-control', 'x-frame-options', 'permissions-policy']:
        assert h in r.headers, h


# --- real staff auth ---
def _assert_cookie_flags(r):
    scs = set_cookies(r)
    names = {s.split('=', 1)[0] for s in scs}
    assert {'access_token', 'refresh_token'} <= names, scs
    for s in scs:
        low = s.lower()
        assert 'httponly' in low and 'secure' in low and 'samesite=lax' in low and 'path=/' in low, s


def test_staff_wrong_then_correct_full_session_cycle():
    r = req('POST', '/api/auth/login', CANON, json={'email': A.OWNER_EMAIL, 'password': 'WrongPass-118'})
    assert r.status_code == 401 and 'incorrect' in err(r).get('message', '')
    assert not set_cookies(r)
    r = req('POST', '/api/auth/login', CANON, json={'email': A.OWNER_EMAIL.upper(), 'password': A.OWNER_PW})
    assert r.status_code == 200, r.text[:200]
    assert r.json()['data']['role'] == 'owner' and 'password_hash' not in r.text
    _assert_cookie_flags(r)
    ck = jar(r)
    assert run(H.TDB.tejas_login_limits.count_documents({})) == 0  # limiter row cleared on success
    assert req('GET', '/api/studio/all-india-jee', CANON, cookies=ck).status_code == 200
    r = req('GET', '/api/auth/session', CANON, cookies=ck)
    assert r.json()['data']['user']['email'] == A.OWNER_EMAIL
    assert req('GET', '/api/studio/sets', CANON, cookies=ck).status_code == 200
    # bootstrap with refresh only (expired/missing access)
    r = req('GET', '/api/auth/session', CANON, cookies={'refresh_token': ck['refresh_token']})
    assert r.json()['data']['user']['role'] == 'owner'
    _assert_cookie_flags(r)
    r = req('POST', '/api/auth/refresh', CANON, cookies=ck)
    assert r.status_code == 200
    _assert_cookie_flags(r)
    r = req('POST', '/api/auth/logout', CANON, cookies=ck)
    assert r.status_code == 200
    low = ' '.join(set_cookies(r)).lower()
    assert 'access_token=' in low and 'max-age=0' in low or 'expires=' in low
    assert req('GET', '/api/auth/me', CANON, cookies=ck).status_code == 401
    assert req('POST', '/api/auth/refresh', CANON, cookies=ck).status_code == 401
    assert req('GET', '/api/auth/session', CANON, cookies=ck).json()['data']['user'] is None


def test_staff_login_from_each_allowed_origin():
    for o in ALLOWED:
        r = req('POST', '/api/auth/login', o, json={'email': A.OWNER_EMAIL, 'password': A.OWNER_PW})
        assert r.status_code == 200, (o, r.text[:200])
        assert r.headers['access-control-allow-origin'] == o
        req('POST', '/api/auth/logout', o, cookies=jar(r))


def test_reviewer_cannot_owner_route_and_lockout():
    r = req('POST', '/api/auth/login', CANON, json={'email': A.REVIEWER_EMAIL, 'password': A.REVIEWER_PW})
    assert r.status_code == 200 and r.json()['data']['role'] == 'reviewer'
    ck = jar(r)
    r = req('GET', '/api/studio/all-india-jee', CANON, cookies=ck)
    assert r.status_code == 403, r.text[:200]
    assert req('GET', '/api/studio/sets', CANON, cookies=ck).status_code == 200
    req('POST', '/api/auth/logout', CANON, cookies=ck)
    codes = [req('POST', '/api/auth/login', CANON, json={'email': A.REVIEWER_EMAIL, 'password': 'Wrong-118-x'}).status_code for _ in range(5)]
    assert codes == [401] * 5
    r = req('POST', '/api/auth/login', CANON, json={'email': A.REVIEWER_EMAIL, 'password': A.REVIEWER_PW})
    assert r.status_code == 429 and 'retry-after' in r.headers


def test_credential_generation_fencing_and_hold():
    r = req('POST', '/api/auth/login', CANON, json={'email': A.OWNER_EMAIL, 'password': A.OWNER_PW})
    ck = jar(r)
    assert req('GET', '/api/auth/me', CANON, cookies=ck).status_code == 200
    run(H.TDB.tejas_users.update_one({'id': A.OWNER_ID}, {'$set': {'credential_generation': 1}}))
    assert req('GET', '/api/auth/me', CANON, cookies=ck).status_code == 401
    assert req('POST', '/api/auth/refresh', CANON, cookies=ck).status_code == 401
    run(H.TDB.tejas_users.update_one({'id': A.OWNER_ID}, {'$set': {'staff_auth_held': True}}))
    r = req('POST', '/api/auth/login', CANON, json={'email': A.OWNER_EMAIL, 'password': A.OWNER_PW})
    assert r.status_code == 401 and not set_cookies(r)
    run(H.TDB.tejas_users.update_one({'id': A.OWNER_ID}, {'$unset': {'staff_auth_held': 1}}))
    r = req('POST', '/api/auth/login', CANON, json={'email': A.OWNER_EMAIL, 'password': A.OWNER_PW})
    assert r.status_code == 200
    req('POST', '/api/auth/logout', CANON, cookies=jar(r))


def test_forged_tokens_rejected():
    forged = jwt.encode({'sub': A.OWNER_ID, 'sid': 'x', 'type': 'access', 'exp': int(time.time()) + 600}, 'not-the-secret', algorithm='HS256')
    assert req('GET', '/api/auth/me', CANON, cookies={'access_token': forged}).status_code == 401
    none_tok = jwt.encode({'sub': A.OWNER_ID, 'sid': 'x', 'type': 'access'}, None, algorithm='none')
    assert req('GET', '/api/studio/sets', CANON, cookies={'access_token': none_tok}).status_code == 401


# --- real student phone auth ---
def test_student_phone_flow_and_isolation():
    r = req('POST', '/api/auth/phone', CANON, json={'phone': '0000000000'})
    assert r.status_code == 422 and not set_cookies(r)
    ra = req('POST', '/api/auth/phone', CANON, json={'phone': '99000 00101'})
    assert ra.status_code == 200, ra.text[:200]
    ua = ra.json()['data']
    assert ua['role'] == 'student' and ua['access_type'] == 'unverified_phone' and ua['phone'] == '+919900000101'
    _assert_cookie_flags(ra)
    cka = jar(ra)
    rb = req('POST', '/api/auth/phone', CANON, json={'phone': '+91 9900000102'})
    ckb, ub = jar(rb), rb.json()['data']
    assert ua['id'] != ub['id']
    # same number again -> same profile
    assert req('POST', '/api/auth/phone', CANON, json={'phone': '9900000101'}).json()['data']['id'] == ua['id']
    # student cannot use staff/owner routes
    assert req('GET', '/api/studio/sets', CANON, cookies=cka).status_code == 403
    assert req('GET', '/api/studio/all-india-jee', CANON, cookies=cka).status_code == 403
    assert req('GET', '/api/studio/sets', CANON).status_code == 401
    # user A attempt not visible to user B
    aid = str(uuid.uuid4())
    run(H.TDB.tejas_attempts.insert_one({'id': aid, 'user_id': ua['id'], 'set_id': 'TEST_set', 'title': 'TEST', 'status': 'submitted',
                                         'deadline': 0, 'started_at': 1, 'questions': [], 'answers': {}}))
    la = req('GET', '/api/attempts', CANON, cookies=cka).json()['data']['items']
    lb = req('GET', '/api/attempts', CANON, cookies=ckb).json()['data']['items']
    assert [x['id'] for x in la] == [aid] and lb == []
    assert req('GET', f'/api/attempts/{aid}', CANON, cookies=ckb).status_code == 404
    assert req('POST', f'/api/attempts/{aid}/submit', CANON, cookies=ckb, json={}).status_code in (404, 422)
    # session persist / refresh / logout
    assert req('GET', '/api/auth/session', CANON, cookies={'refresh_token': cka['refresh_token']}).json()['data']['user']['id'] == ua['id']
    assert req('POST', '/api/auth/logout', CANON, cookies=cka).status_code == 200
    assert req('GET', '/api/auth/me', CANON, cookies=cka).status_code == 401


def test_registration_disabled():
    assert req('POST', '/api/auth/register', CANON).status_code == 410
    r = req('POST', '/api/auth/register', CANON, json={'email': 'x@example.com', 'password': 'whatever123'})
    assert r.status_code in (410, 422)
    assert run(H.TDB.tejas_users.count_documents({'email': 'x@example.com'})) == 0
