"""TEST-ONLY iteration 154: PYQ catalogue regression via REAL auth over the isolated bridge (iso_bridge_iter154.py, port 8792).
Requires the bridge running. Real student PIN login, real cookies (forwarded manually since bridge is plain http).
"""
import json, re
import httpx, pytest

B = 'http://127.0.0.1:8792'
C = json.load(open('/tmp/iter154_creds.json'))
ORIGIN = __import__('iso_harness_iter154').ORIGIN if False else None


def J(r):
    j = r.json()
    return j.get('data') if isinstance(j, dict) and 'data' in j and 'meta' in j else j


def login(path, body):
    import os
    from dotenv import dotenv_values
    origin = dotenv_values('/app/backend/.env')['FRONTEND_URL'].rstrip('/')
    r = httpx.post(B + path, json=body, headers={'Origin': origin})
    assert r.status_code == 200, r.text
    jar = {k: v for k, v in r.cookies.items()}
    return {'Cookie': '; '.join(f'{k}={v}' for k, v in jar.items()), 'Origin': origin}


@pytest.fixture(scope='module')
def student():
    return login('/api/auth/phone', {'phone': C['student_phone'], 'pin': C['student_pin']})


def test_state_isolated():
    s = httpx.get(B + '/__test/state').json()
    assert s['db'] == 'tejas_isolated_iter154' and s['sets'] == 30 and not s['leftover'] and not s['puts']


def test_catalogue_shape_and_no_secrets(student):
    r = httpx.get(B + '/api/pyq/jee-main', headers=student)
    assert r.status_code == 200 and 'no-store' in r.headers['cache-control']
    d = J(r)
    assert d['total'] == 30 and d['years'] == [2026, 2025]
    assert all(p['count'] == 75 for p in d['items'])
    assert {p['year'] for p in d['items']} == {2025, 2026}
    dates = [p['exam_date'] for p in d['items']]
    assert dates == sorted(dates, reverse=True)
    keys = set(re.findall(r'"([a-z_]+)"\s*:', r.text)) - {'source_note'}
    for leak in ('answer', 'correct', 'source', 'path', 'pdf', 'key', 'questions'):
        assert not [k for k in keys if leak in k], (leak, keys)
    by = {p['id']: p for p in d['items']}
    a, dn = by[C['active_set']], by[C['done_set']]
    assert a['attempt']['status'] == 'active' and a['attempt_count'] == 1
    assert dn['latest_result_id'] == 'TEST154_done' and dn['attempt']['status'] == 'completed'
    others = [p for p in d['items'] if p['id'] not in (C['active_set'], C['done_set'])]
    assert all(p['attempt'] is None and p['attempt_count'] == 0 for p in others)


def test_other_student_and_anon_isolation():
    assert httpx.get(B + '/api/pyq/jee-main').status_code == 401
    h = login('/api/auth/phone/signup', {'phone': '99016%05d' % __import__('secrets').randbelow(99999), 'pin': '4040', 'confirm_pin': '4040'})
    d = J(httpx.get(B + '/api/pyq/jee-main', headers=h))
    assert d['total'] == 30 and all(p['attempt'] is None for p in d['items'])
    assert httpx.get(B + '/api/attempts/TEST154_done/results', headers=h).status_code in (403, 404)


def test_source_access_permissions():
    r = httpx.get(B + '/api/studio/pyq-import/status')
    assert r.status_code == 401
    h = login('/api/auth/login', {'email': C['rev_email'], 'password': C['rev_pw']})
    assert httpx.get(B + '/api/studio/pyq-import/status', headers=h).status_code == 403
    s = login('/api/auth/phone', {'phone': C['student_phone'], 'pin': C['student_pin']})
    assert httpx.get(B + '/api/studio/pyq-import/status', headers=s).status_code == 403
