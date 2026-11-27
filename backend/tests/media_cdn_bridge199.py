"""Spot checks of signed CDN picture links against the iteration-188 bridge (127.0.0.1:8770, disposable DB).
Run while `python tests/ui_bridge188.py` is up: pytest tests/media_cdn_bridge199.py -p no:xdist -q"""
import json, uuid, pytest, requests

B = 'http://127.0.0.1:8770'
CFG = json.load(open('/tmp/uibridge/bridge.json'))
F = CFG['f']
ORIGIN = 'https://jlive-ceo-inspect--0x57uoje.preview.emergentagent.com'


def sess(cookies=None):
    s = requests.Session()
    s.headers['Origin'] = ORIGIN
    if cookies:
        s.headers['Cookie'] = '; '.join(f'{k}={v}' for k, v in cookies.items())
    return s


def data(r):
    j = r.json()
    return j.get('data', j) if isinstance(j, dict) else j


def start(s, set_id):
    r = s.post(f"{B}/api/sets/{set_id}/start", json={'preview': False, 'start_key': 'T199-' + uuid.uuid4().hex[:10], 'get_ready': True})
    assert r.status_code == 200, r.text[:300]
    return data(r)


@pytest.fixture(scope='module')
def stu():
    return sess(CFG['student'])


@pytest.fixture(scope='module')
def stu2():
    s = sess()
    s.headers['Origin'] = ORIGIN
    r = s.post(f"{B}/api/auth/phone/signup", json={'phone': '91' + str(uuid.uuid4().int)[:8], 'pin': '8261', 'confirm_pin': '8261'})
    assert r.status_code in (200, 201), r.text[:200]
    # Session cookies are Secure; requests will not resend them over http, so copy them onto a plain cookie header.
    s.headers['Cookie'] = '; '.join(f'{c.name}={c.value}' for c in r.cookies)
    s.cookies.clear()
    return s


@pytest.fixture(scope='module')
def att(stu):
    return start(stu, F['pic_set'])


# Links for the attempt owner
def test_links_owner(stu, att):
    r = stu.get(f"{B}/api/attempts/{att['id']}/assets/links")
    assert r.status_code == 200, r.text
    d = data(r)
    assert d['limit'] == 12 and d['cdn'] is False and d['total'] > 0
    assert len(d['parts']) == (d['total'] + 11) // 12
    assert all(p.startswith('/api/media/pack/') for p in d['parts'])
    pytest.links = d


# Non-owner gets 404, signed-out 401
def test_links_other_and_anon(stu2, att):
    assert stu2.get(f"{B}/api/attempts/{att['id']}/assets/links").status_code == 404
    assert sess().get(f"{B}/api/attempts/{att['id']}/assets/links").status_code == 401


# Same paper -> identical links for two students
def test_links_identical_two_students(stu2):
    a2 = start(stu2, F['pic_set'])
    d2 = data(stu2.get(f"{B}/api/attempts/{a2['id']}/assets/links"))
    assert d2['parts'] == pytest.links['parts']


# Public part: cache headers, CORS, no cookie, byte-identical with private pack
def test_media_public_part(stu, att):
    link = pytest.links['parts'][0]
    r = requests.get(B + link, headers={'Origin': 'https://evil.example'})
    assert r.status_code == 200
    assert r.headers['Content-Type'].startswith('application/octet-stream')
    cc = r.headers['Cache-Control']
    assert cc.startswith('public') and 'max-age=' in cc and 's-maxage=' in cc and 'immutable' in cc, cc
    assert r.headers.get('Access-Control-Allow-Origin') == '*'
    assert 'set-cookie' not in {k.lower() for k in r.headers}
    p = stu.get(f"{B}/api/attempts/{att['id']}/assets/pack?offset=0&limit=12")
    assert p.status_code == 200 and p.content == r.content


# Tampered links -> 404 no-store
@pytest.mark.parametrize('mut', ['sig', 'offset', 'bonus', 'pack', 'exp'])
def test_media_tampered(mut):
    link = pytest.links['parts'][0]
    base, name = link.rsplit('/', 1)
    o, l, b, e, s = name[:-4].split('-', 4)
    if mut == 'sig': s = ('A' if s[0] != 'A' else 'B') + s[1:]
    if mut == 'offset': o = '12'
    if mut == 'bonus': b = '1' if b == '0' else '0'
    if mut == 'exp': e = str(int(e) - 86400 * 5)
    if mut == 'pack': base = base[:-1] + ('0' if base[-1] != '0' else '1')
    r = requests.get(f"{B}{base}/{o}-{l}-{b}-{e}-{s}.bin")
    assert r.status_code == 404
    assert 'no-store' in r.headers.get('Cache-Control', '')


# After submit -> 409
def test_links_after_submit(stu2):
    a = start(stu2, F['prac_set'])
    stu2.post(f"{B}/api/attempts/{a['id']}/begin")
    r = stu2.post(f"{B}/api/attempts/{a['id']}/submit")
    assert r.status_code in (200, 202), (r.status_code, r.text[:200])
    assert stu2.get(f"{B}/api/attempts/{a['id']}/assets/links").status_code == 409
