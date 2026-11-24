"""Iteration 197 checks against the ui_bridge188 bridge (127.0.0.1:8770, disposable DB):
picture questions send text '' (start / get / begin / results), text papers keep text, /api/media/probe.bin.
Run while `python tests/ui_bridge188.py` is up: pytest tests/picture_text_bridge200.py -p no:xdist -q"""
import json, time, uuid, pytest, requests

B = 'http://127.0.0.1:8770'
CFG = json.load(open('/tmp/uibridge/bridge.json'))
F = CFG['f']
ORIGIN = 'https://book-pipeline-fix-1--7ttfegq6.preview.emergentagent.com'


def data(r):
    j = r.json()
    return j.get('data', j) if isinstance(j, dict) else j


def new_student():
    s = requests.Session(); s.headers['Origin'] = ORIGIN
    r = s.post(f"{B}/api/auth/phone/signup", json={'phone': '91' + str(uuid.uuid4().int)[:8], 'pin': '8261', 'confirm_pin': '8261'})
    assert r.status_code in (200, 201), r.text[:200]
    s.headers['Cookie'] = '; '.join(f'{c.name}={c.value}' for c in r.cookies); s.cookies.clear()
    return s


def start(s, set_id):
    r = s.post(f"{B}/api/sets/{set_id}/start", json={'preview': False, 'start_key': 'T200-' + uuid.uuid4().hex[:10], 'get_ready': True})
    assert r.status_code == 200, r.text[:300]
    return data(r)


def pics(qs):
    return [q for q in qs if q.get('render_mode') == 'source' and q.get('asset_count')]


@pytest.fixture(scope='module')
def stu():
    return new_student()


@pytest.fixture(scope='module')
def pic(stu):
    return start(stu, F['pic_set'])


# (a) start payload: picture questions text ''
def test_start_pic_text_empty(pic):
    p = pics(pic['questions'])
    assert p, [ (q.get('render_mode'), q.get('asset_count')) for q in pic['questions']]
    assert all(q['text'] == '' for q in p), [q['text'][:60] for q in p]
    pytest.pic_ids = [q['id'] for q in p]


# (a) GET attempt + begin
def test_get_and_begin_text_empty(stu, pic):
    g = stu.get(f"{B}/api/attempts/{pic['id']}"); assert g.status_code == 200
    gp = pics(data(g)['questions']); assert gp and all(q['text'] == '' for q in gp)
    b = stu.post(f"{B}/api/attempts/{pic['id']}/begin"); assert b.status_code == 200, b.text[:200]
    bq = data(b).get('questions')
    if bq:
        bp = pics(bq); assert bp and all(q['text'] == '' for q in bp)


# Options keep their labels
def test_options_present(pic):
    for q in pics(pic['questions']):
        assert q.get('options') or q.get('source_option_labels') or q.get('response_type') != 'mcq'


# (b) results payload text '' for picture questions; solutions/answers still present
def test_results_text_empty(stu, pic):
    a = pic['id']; q0 = pic['questions'][0]
    stu.put(f"{B}/api/attempts/{a}/answers/{q0['id']}", json={'value': 'B', 'revision': 1, 'request_id': str(uuid.uuid4())})
    assert stu.post(f"{B}/api/attempts/{a}/submit").status_code in (200, 202)
    d = None
    for _ in range(30):
        r = stu.get(f"{B}/api/attempts/{a}/results")
        if r.status_code == 200 and data(r).get('questions'):
            d = data(r); break
        time.sleep(0.5)
    assert d, r.text[:300]
    rp = pics(d['questions'])
    assert rp and all(q['text'] == '' for q in rp), [q['text'][:60] for q in rp]
    assert all('correct' in q or 'answer' in q or 'correct_answer' in q for q in rp), list(rp[0].keys())


# No regression: text paper keeps text in player and results
def test_text_paper_keeps_text():
    s = new_student(); a = start(s, F['prac_set'])
    qs = [q for q in a['questions'] if q.get('render_mode') != 'source']
    assert qs and all(q['text'] for q in qs)
    s.post(f"{B}/api/attempts/{a['id']}/begin"); s.post(f"{B}/api/attempts/{a['id']}/submit")
    for _ in range(30):
        r = s.get(f"{B}/api/attempts/{a['id']}/results")
        if r.status_code == 200 and data(r).get('questions'): break
        time.sleep(0.5)
    rq = [q for q in data(r)['questions'] if q.get('render_mode') != 'source']
    assert rq and all(q['text'] for q in rq)


# Public probe
def test_probe():
    r = requests.get(B + '/api/media/probe.bin', headers={'Origin': 'https://evil.example'})
    assert r.status_code == 200
    assert r.content == b'jeelive-media-probe-v1\n'
    assert r.headers['Cache-Control'].startswith('public')
    assert r.headers['Access-Control-Allow-Origin'] == '*'
    assert r.headers['X-Media-CDN'] == 'same-server'
    assert 'set-cookie' not in {k.lower() for k in r.headers}
