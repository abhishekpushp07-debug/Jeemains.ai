# Rank tools (public), Dream/Mission (auth) endpoints - iteration 199
import json
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    for line in open('/app/frontend/.env'):
        if line.startswith('REACT_APP_BACKEND_URL='):
            BASE_URL = line.split('=', 1)[1].strip().rstrip('/')
BRIDGE = 'http://127.0.0.1:8773'
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'}


@pytest.fixture(scope='module')
def s():
    x = requests.Session()
    x.headers.update(UA)
    return x


def J(r):
    d = r.json()
    return d['data'] if isinstance(d, dict) and set(d) == {'data', 'error', 'meta'} else d


def post(s, path, body):
    return s.post(f'{BASE_URL}/api/rank{path}', json=body, timeout=60)


# --- Rank: meta / estimate / percentile
def test_meta(s):
    r = s.get(f'{BASE_URL}/api/rank/meta', timeout=30)
    assert r.status_code == 200 and isinstance(J(r), dict)


def test_estimate_jee(s):
    r = post(s, '/estimate', {'marks': 180})
    assert r.status_code == 200
    d = J(r)
    assert d['exam'] == 'jee' and len(d['levels']) == 3
    p = d['result']['percentile']; p = p if isinstance(p, list) else [p]
    assert all(90 < float(v) <= 100 for v in p)


def test_estimate_invalid(s):
    assert post(s, '/estimate', {'marks': 400}).status_code == 422
    assert post(s, '/estimate', {'exam': 'comedk', 'marks': 190}).status_code == 422


def test_estimate_comedk(s):
    r = post(s, '/estimate', {'exam': 'comedk', 'marks': 120})
    assert r.status_code == 200, r.text


def test_percentile(s):
    r = post(s, '/percentile', {'percentile': 97.5, 'category': 'OBC-NCL'})
    assert r.status_code == 200
    d = J(r)
    assert len(d['marks']) == 3 and d['result']
    assert post(s, '/percentile', {'percentile': 101}).status_code == 422


# --- College predictor JEE / BITSAT / COMEDK
def test_predict_jee_and_college(s):
    r = post(s, '/predict', {'marks': 180, 'category': 'GEN'})
    assert r.status_code == 200, r.text
    d = J(r)
    txt = json.dumps(d)
    assert 'inst' in txt
    assert post(s, '/predict', {}).status_code == 422
    assert post(s, '/predict', {'marks': 180, 'state': 'Atlantis'}).status_code == 422
    r2 = post(s, '/college', {'marks': 180, 'inst': 0})
    assert r2.status_code in (200, 404), r2.text
    assert post(s, '/college', {'marks': 180, 'inst': -1}).status_code == 422


def test_bitsat(s):
    r = post(s, '/bitsat', {'score': 280})
    assert r.status_code == 200, r.text
    assert post(s, '/bitsat', {'score': 999}).status_code == 422
    assert post(s, '/bitsat', {'score': 280, 'campus': 'Mars'}).status_code == 422


def test_comedk(s):
    r = post(s, '/comedk', {'marks': 110})
    assert r.status_code == 200, r.text
    assert post(s, '/comedk', {'marks': 200}).status_code == 422
    assert post(s, '/comedk', {'rank': 5000}).status_code == 200
    assert post(s, '/comedk/college', {'marks': 110, 'code': 'NOPE'}).status_code == 404


# --- Colleges list, Target marks
def test_colleges_and_targets(s):
    r = s.get(f'{BASE_URL}/api/rank/colleges', timeout=30)
    assert r.status_code == 200
    d = J(r)
    assert d['jee'] and d['comedk'] and d['bitsat']
    inst = d['jee'][0]['inst']
    code = d['comedk'][0]['code']
    tj = post(s, '/target/jee', {'inst': inst})
    assert tj.status_code == 200, tj.text
    assert post(s, '/target/jee', {'inst': 99999}).status_code == 404
    tc = post(s, '/target/comedk', {'code': code})
    assert tc.status_code == 200, tc.text
    assert post(s, '/target/comedk', {'code': 'XX'}).status_code == 404
    tb = s.get(f'{BASE_URL}/api/rank/target/bitsat', timeout=30)
    assert tb.status_code == 200 and J(tb)['rows']
    # compare colleges
    cc = post(s, '/compare/colleges', {'items': [{'exam': 'jee', 'id': str(inst)}, {'exam': 'comedk', 'id': code},
                                                  {'exam': 'bitsat', 'id': 'Pilani'}]})
    assert cc.status_code == 200, cc.text
    assert post(s, '/compare/colleges', {'items': []}).status_code == 422
    assert post(s, '/compare', {'items': []}).status_code == 422


def test_compare_bitsat_items(s):
    tb = J(s.get(f'{BASE_URL}/api/rank/target/bitsat', timeout=30))['rows']
    r = post(s, '/compare', {'items': [{'exam': 'bitsat', 'id': tb[0]['id']}, {'exam': 'bitsat', 'id': tb[1]['id']}]})
    assert r.status_code == 200, r.text


# --- PDFs
@pytest.mark.parametrize('path,body', [
    ('/pdf/jee', {'marks': 180}),
    ('/pdf/comedk', {'marks': 110}),
    ('/pdf/bitsat', {'score': 280}),
    ('/pdf/target/bitsat', {'campus': 'Goa'}),
])
def test_pdfs(s, path, body):
    r = post(s, path, body)
    assert r.status_code == 200, r.text[:300]
    assert r.content[:4] == b'%PDF'


def test_pdf_invalid(s):
    assert post(s, '/pdf/bitsat', {'score': 999}).status_code == 422
    assert post(s, '/pdf/saved', {'items': []}).status_code == 422


# --- Auth-only endpoints (signed out => 401)
@pytest.mark.parametrize('method,path,body', [
    ('get', '/api/dream', None), ('put', '/api/dream/dreams', {'dreams': [], 'base': []}),
    ('post', '/api/dream/cheered', {'ids': ['a']}), ('get', '/api/dream/celebration/abc', None), ('get', '/api/mission/me', None)])
def test_auth_required(s, method, path, body):
    r = getattr(requests, method)(f'{BASE_URL}{path}', json=body, headers=UA, timeout=30)
    assert r.status_code == 401, r.text


# --- Signed in via disposable bridge
@pytest.fixture(scope='module')
def hero():
    try:
        b = json.load(open('/tmp/uibridge196/bridge.json'))
    except Exception:
        pytest.skip('bridge not available')
    x = requests.Session()
    x.cookies.update(b['hero'])
    x.headers.update(UA)
    if x.get(f'{BRIDGE}/api/mission/me', timeout=10).status_code != 200:
        pytest.skip('bridge cookies expired')
    return x, b


def test_mission_me_and_link(hero):
    x, _ = hero
    d = J(x.get(f'{BRIDGE}/api/mission/me'))
    assert d['code'] and 'helped' in d and 'week' in d
    before = d['helped']
    # curl/bot UA never counts
    requests.get(f'{BRIDGE}/api/j/{d["code"]}', headers={'User-Agent': 'curl/8'}, allow_redirects=False)
    import uuid
    ua2 = {'User-Agent': UA['User-Agent'] + ' T' + uuid.uuid4().hex[:6]}
    r = requests.get(f'{BRIDGE}/api/j/{d["code"]}', headers=ua2, allow_redirects=False)
    assert r.status_code == 302 and r.headers['location'] == '/'
    after1 = J(x.get(f'{BRIDGE}/api/mission/me'))['helped']
    assert after1 == before + 1
    # same device again -> no double count
    requests.get(f'{BRIDGE}/api/j/{d["code"]}', headers=ua2, allow_redirects=False)
    assert J(x.get(f'{BRIDGE}/api/mission/me'))['helped'] == after1


def test_celebration(hero):
    x, b = hero
    r = x.get(f'{BRIDGE}/api/dream/celebration/{b["hero_attempt"]}')
    assert r.status_code == 200, r.text
    d = J(r)
    assert {'celebrate', 'good', 'beat_best'} <= set(d)
    assert d['celebrate'] is True and d['good'] is True
    assert x.get(f'{BRIDGE}/api/dream/celebration/nope').status_code == 404


def test_dream_crud(hero):
    x, _ = hero
    g = x.get(f'{BRIDGE}/api/dream')
    assert g.status_code == 200
    base = J(g)['dreams']
    print('dream sample', base[:1])
    cheer = x.post(f'{BRIDGE}/api/dream/cheered', json={'ids': ['TEST_x']})
    assert cheer.status_code == 200
    assert 'TEST_x' in J(x.get(f'{BRIDGE}/api/dream'))['cheered']
