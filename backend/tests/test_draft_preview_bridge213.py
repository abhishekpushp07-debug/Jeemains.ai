# Draft preview API (Try as student) via the disposable bridge :8772 — owner/reviewer on Live vs Draft mocks
import json, os, time
import pytest, requests

BRIDGE = 'http://127.0.0.1:8772'
ORIGIN = 'https://jlive-ceo-inspect--0x57uoje.preview.emergentagent.com'
B = json.load(open('/tmp/uibridge210/bridge.json')) if os.path.exists('/tmp/uibridge210/bridge.json') else None
pytestmark = pytest.mark.skipif(B is None, reason='bridge not running')


def sess(role):
    s = requests.Session()
    s.headers.update({'Origin': ORIGIN, 'Cookie': '; '.join(f'{k}={v}' for k, v in B[role].items())})
    return s


def data(r):
    return r.json().get('data')


# Published (Live) boxed mock: owner gets the real Live set
def test_owner_live_mock_ready_with_live_set():
    mid = B['f']['boxed'][1]
    r = sess('owner').post(f'{BRIDGE}/api/admin/master/preview/{mid}', timeout=20)
    assert r.status_code == 200, r.text
    d = data(r)
    assert d['state'] == 'ready' and d['set_id'] == B['f']['live_set'] and d['left_out'] == []
    g = sess('owner').get(f'{BRIDGE}/api/admin/master/preview/{mid}', timeout=20)
    assert g.status_code == 200 and data(g)['set_id'] == B['f']['live_set']


# Reviewer may not try a published mock
def test_reviewer_live_mock_404():
    mid = B['f']['boxed'][1]
    for m in ('post', 'get'):
        r = getattr(sess('reviewer'), m)(f'{BRIDGE}/api/admin/master/preview/{mid}', timeout=20)
        assert r.status_code == 404, (m, r.status_code, r.text)


# Student cannot call the staff endpoint at all
def test_student_forbidden():
    mid = B['f']['boxed_small'][1]
    r = sess('student').post(f'{BRIDGE}/api/admin/master/preview/{mid}', timeout=20)
    assert r.status_code in (401, 403), r.status_code


# Draft mock: owner -> building/ready quickly, ready eventually, set is private preview
@pytest.mark.parametrize('role', ['owner', 'reviewer'])
def test_draft_mock_preview_builds(role):
    mid = B['f']['boxed_small'][1]
    s = sess(role)
    t = time.time()
    r = s.post(f'{BRIDGE}/api/admin/master/preview/{mid}', timeout=20)
    assert r.status_code == 200, r.text
    assert time.time() - t < 3
    d = data(r)
    assert d['state'] in ('building', 'ready')
    for _ in range(60):
        if d['state'] != 'building':
            break
        time.sleep(0.5)
        d = data(s.get(f'{BRIDGE}/api/admin/master/preview/{mid}', timeout=20))
    assert d['state'] == 'ready', d
    assert d['set_id'] and d['set_id'] != B['f']['live_set']
    st = s.get(f'{BRIDGE}/api/studio/sets/{d["set_id"]}', timeout=20)
    assert st.status_code == 200, st.text


# Unknown mock id -> 404
def test_unknown_mock_404():
    r = sess('owner').post(f'{BRIDGE}/api/admin/master/preview/does-not-exist', timeout=20)
    assert r.status_code == 404
