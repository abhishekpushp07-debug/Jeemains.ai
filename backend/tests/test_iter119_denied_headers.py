"""TEST-ONLY iteration 119: denied-origin 403 now carries security headers + matching request id (isolated ASGI, real auth).
Run: cd /app/backend/tests && FRONTEND_URL=... CORS_ORIGINS=... python -m pytest test_iter119_denied_headers.py -p no:asyncio -n0
"""
import pytest
import test_iter118_auth_cors_isolated as T  # reuses isolated harness, client helpers and module fixture
from test_iter118_auth_cors_isolated import isolated_db  # noqa: F401  (autouse seed/drop of isolated DB)

A, H, req, err, run, CANON = T.A, T.H, T.req, T.err, T.run, T.CANON
SEC = {'x-content-type-options': 'nosniff', 'x-frame-options': 'DENY', 'cache-control': 'private, no-store',
       'referrer-policy': 'same-origin', 'permissions-policy': 'camera=(), microphone=(), geolocation=()'}


def _sec(r):
    for k, v in SEC.items():
        assert r.headers.get(k) == v, (k, r.headers.get(k))
    rid = r.headers.get('x-request-id')
    assert rid and len(rid) == 36
    assert r.headers.get('server-timing', '').startswith('app;dur=')
    return rid


# denied origin: 403 origin_denied + all security headers + header/body request id match, no ACAO
@pytest.mark.parametrize('origin', ['https://evil.example', 'null', CANON + '.evil.example', 'https://jeelive.ai:0443'])
@pytest.mark.parametrize('method,path', [('POST', '/api/auth/phone'), ('POST', '/api/auth/login'), ('DELETE', '/api/studio/sets/x')])
def test_denied_403_has_security_headers(origin, method, path):
    r = req(method, path, origin, json={'phone': '9900000151'}) if method != 'DELETE' else req(method, path, origin)
    assert r.status_code == 403 and err(r).get('code') == 'origin_denied'
    rid = _sec(r)
    assert r.json()['meta']['request_id'] == rid
    assert r.headers.get('access-control-allow-origin') is None
    assert r.headers.get('access-control-allow-credentials') is None
    assert not r.headers.get_list('set-cookie')


def test_denied_requests_unique_request_ids_and_no_db_rows():
    ids = {req('POST', '/api/auth/phone', 'https://evil.example', json={'phone': '9900000152'}).headers['x-request-id'] for _ in range(3)}
    assert len(ids) == 3
    for c in ('tejas_phone_limits', 'tejas_phone_profiles', 'tejas_login_limits'):
        assert run(H.TDB[c].count_documents({})) == 0, c


def test_denied_with_real_staff_cookie_not_honoured():
    r = req('POST', '/api/auth/login', CANON, json={'email': A.OWNER_EMAIL, 'password': A.OWNER_PW})
    assert r.status_code == 200
    ck = T.jar(r)
    r = req('POST', '/api/auth/logout', 'https://evil.example', cookies=ck)
    assert r.status_code == 403 and not r.headers.get_list('set-cookie')
    _sec(r)
    assert req('GET', '/api/auth/me', CANON, cookies=ck).status_code == 200  # session survived denied logout


def test_host_spoof_denied_with_headers():
    host = 'evil.example'
    r = req('POST', '/api/auth/phone', 'https://' + host, json={'phone': '0000000000'},
            headers={'Host': host, 'X-Forwarded-Host': host, 'Referer': CANON + '/login'})
    assert r.status_code == 403 and err(r).get('code') == 'origin_denied'
    assert r.json()['meta']['request_id'] == _sec(r)


# allowed origin: errors still enveloped with matching request id + headers
def test_allowed_validation_errors_headers_match():
    r = req('POST', '/api/auth/phone', CANON, json={'phone': '0000000000'})
    assert r.status_code == 422 and r.headers['access-control-allow-origin'] == CANON
    assert r.json()['meta']['request_id'] == _sec(r)
    r = req('POST', '/api/auth/login', CANON, json={})
    assert r.status_code == 422 and err(r).get('code') == 'validation_error'
    assert r.json()['meta']['request_id'] == _sec(r)
    assert r.headers['access-control-allow-credentials'] == 'true'


def test_preflight_allowed_exact_acao():
    r = req('OPTIONS', '/api/auth/login', CANON, headers={'Access-Control-Request-Method': 'POST', 'Access-Control-Request-Headers': 'content-type'})
    assert r.status_code == 200 and r.headers['access-control-allow-origin'] == CANON
    assert r.headers['access-control-allow-credentials'] == 'true'


def test_phone_success_session_flow():
    r = req('POST', '/api/auth/phone', CANON, json={'phone': '9900000153'})
    assert r.status_code == 200, r.text[:200]
    ck = T.jar(r)
    s = req('GET', '/api/auth/session', CANON, cookies=ck).json()['data']['user']
    assert s and s.get('role') not in ('owner', 'reviewer')
    assert req('GET', '/api/studio/sets', CANON, cookies=ck).status_code in (401, 403)
