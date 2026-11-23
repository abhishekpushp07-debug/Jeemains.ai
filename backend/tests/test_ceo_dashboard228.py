# CEO dashboard API (/api/ceo/v1/*), student contacts API, usage events and signup source - against the isolated bridge only.
import json, os, uuid, random
import pytest, requests

BRIDGE_OUT = os.environ.get('BRIDGE_OUT', '/tmp/ceobridge228')
API = 'http://127.0.0.1:' + os.environ.get('BRIDGE_PORT', '8776')
B = json.load(open(f'{BRIDGE_OUT}/bridge.json'))
E = B['expect']
ORIGIN = [l.split('=', 1)[1].strip() for l in open('/app/frontend/.env') if l.startswith('REACT_APP_BACKEND_URL')][0].rstrip('/')
KEY = {'X-CEO-Key': B['ceo_key']}
HIDDEN_PHONE = '+919811100005'


def ceo(path, **params):
    r = requests.get(f'{API}/api/ceo/v1/{path}', headers=KEY, params=params, timeout=30)
    return r


def body(r):
    j = r.json()
    return j.get('data', j) if isinstance(j, dict) else j


def dig(d, dotted):
    for k in dotted.split('.'):
        d = d[k] if isinstance(d, dict) else d
    return d


def student_session(role, origin=True):
    s = requests.Session()
    for k, v in B[role].items():
        s.cookies.set(k, v)
    if origin:
        s.headers['Origin'] = ORIGIN
    return s


# --- CEO auth & headers
class TestCeoAuth:
    def test_no_key_401(self):
        r = requests.get(f'{API}/api/ceo/v1/summary', timeout=20)
        assert r.status_code == 401, r.text

    def test_wrong_key_401(self):
        r = requests.get(f'{API}/api/ceo/v1/summary', headers={'X-CEO-Key': 'nope' * 8}, timeout=20)
        assert r.status_code == 401

    def test_all_endpoints_200_no_store_envelope(self):
        for p in ['summary', 'daily', 'funnel', 'retention', 'aits', 'content', 'health', 'alerts', 'students', f"students/{B['ids']['arjun']}", 'contacts', 'events']:
            r = ceo(p)
            assert r.status_code == 200, (p, r.status_code, r.text[:200])
            assert 'no-store' in r.headers.get('cache-control', ''), p
            j = r.json()
            assert {'data', 'error', 'meta'} <= set(j), (p, list(j))

    @pytest.mark.parametrize('params', [{'from': '2026-12-10', 'to': '2026-12-01'}, {'from': '2025-01-01', 'to': '2026-12-01'}, {'from': '2026-1-1'}, {'to': '14-12-2026'}])
    def test_bad_dates_422(self, params):
        for p in ('daily', 'funnel', 'events'):
            assert ceo(p, **params).status_code == 422, (p, params)

    def test_unknown_student_404(self):
        assert ceo('students/does-not-exist').status_code == 404


# --- CEO numbers vs hand-counted expect
class TestCeoNumbers:
    def test_summary(self):
        s = body(ceo('summary'))
        x = E['summary']
        assert s['students']['total'] == x['students.total']
        assert s['students']['blocked'] == x['students.blocked']
        assert s['students']['by_signup_channel'] == x['by_signup_channel']
        assert s['signups'] == x['signups']
        assert s['attempts_today'] == x['attempts_today']
        for k, v in x['aits_today'].items():
            assert s['aits_today'][k] == v, k
        assert s['contacts'] == x['contacts']

    def test_aits(self):
        a = body(ceo('aits'))
        x = E['aits']
        days = {d['day']: d for d in a['days']}
        for k, v in x.items():
            head, _, rest = k.partition('.')
            if head.startswith('day') and head[3:].isdigit():
                got = days[int(head[3:])][rest]
            elif head in ('streak_now_at_least', 'best_streak_at_least'):
                got = a[head][rest]
            else:
                got = a[k]
            assert got == v, (k, got, v)

    def test_day6_top_marks_not_staff(self):
        a = body(ceo('aits'))
        d6 = [d for d in a['days'] if d['day'] == 6][0]
        assert d6.get('top_marks') != 299, d6

    def test_funnel_default(self):
        f = body(ceo('funnel'))
        for k, v in E['funnel_default_30d'].items():
            assert f[k] == v, (k, f[k], v)

    def test_student_arjun(self):
        s = body(ceo(f"students/{B['ids']['arjun']}"))
        assert s['aits']['current_streak'] == 5 and s['aits']['best_streak'] == 5
        assert s['contacts_shared'] == 3
        assert s['phone'].startswith('+91') and len(s['phone']) == 13
        assert all(c['phone'].startswith('+91') for c in s['contacts'])

    def test_contacts_list_flags(self):
        c = body(ceo('contacts'))
        assert c['total'] == E['contacts_list']['total']
        by = {i['name']: i for i in c['items']}
        for name, flags in E['contacts_list'].items():
            if name == 'total':
                continue
            for k, v in flags.items():
                assert by[name][k] == v, (name, k)
        assert all(i['phone'].startswith('+91') for i in c['items'])

    def test_alerts(self):
        a = body(ceo('alerts'))
        assert a['level'] == 'red'
        codes = {x['code'] for x in a['alerts']}
        assert {'aits_tomorrow_no_paper', 'grading_failed'} <= codes, codes

    def test_exclusions_and_no_secrets(self):
        blob = ''
        for p in ['summary', 'daily', 'funnel', 'retention', 'aits', 'students', 'contacts', 'events', f"students/{B['ids']['arjun']}", f"students/{B['ids']['riya']}"]:
            blob += ceo(p).text
        assert 'TEST_hidden228' not in blob
        assert HIDDEN_PHONE not in blob and '9811100005' not in blob
        assert B['ids']['test_hidden'] not in blob and B['ids']['staff'] not in blob
        for word in ('pin_hash', 'pin_version', 'access_token', 'refresh_token', '"sid"'):
            assert word not in blob, word
        st = body(ceo('students'))
        assert st['total'] >= E['summary']['students.total']  # signup tests in this file add students
        assert all(i['phone'].startswith('+91') for i in st['items'])

    def test_hidden_student_detail(self):
        # Informational: detail by id of an excluded student
        r = ceo(f"students/{B['ids']['test_hidden']}")
        print('hidden detail status', r.status_code)
        assert r.status_code == 404, 'excluded TEST_ student is reachable via /students/{id}'


# --- Student contacts API
class TestContacts:
    def test_no_session_401(self):
        assert requests.get(f'{API}/api/mission/contacts', timeout=20).status_code == 401
        r = requests.post(f'{API}/api/mission/contacts', json={'contacts': [{'name': 'x', 'tel': ['9822200001']}]}, headers={'Origin': ORIGIN}, timeout=20)
        assert r.status_code == 401

    def test_write_foreign_origin_403(self):
        s = student_session('riya', origin=False)
        r = s.post(f'{API}/api/mission/contacts', json={'contacts': [{'name': 'x', 'tel': ['9822200001']}]}, headers={'Origin': 'https://evil.example'}, timeout=20)
        assert r.status_code == 403, r.text

    def test_save_normalise_skip_ownership(self):
        riya, arjun = student_session('riya'), student_session('arjun')
        n = random.randint(10000000, 99999999)
        a, b = f'098{n:08d}'[:11], f'+91 97{n:08d}'
        r = riya.post(f'{API}/api/mission/contacts', json={'contacts': [
            {'name': 'TEST_A', 'tel': [a]}, {'name': 'TEST_dup', 'tel': [a]}, {'name': 'TEST_bad', 'tel': ['12345']},
            {'name': 'TEST_B', 'tel': ['abc', b]}]}, timeout=20)
        assert r.status_code == 200, r.text
        d = body(r)
        assert d['saved'] == 2 and d['skipped'] == 2, d
        phones = {i['phone']: i for i in d['items']}
        pa, pb = '+91' + a[1:], '+91' + b.replace('+91', '').replace(' ', '')
        assert pa in phones and pb in phones, list(phones)
        cid = phones[pa]['id']
        # Arjun cannot see or delete Riya's row
        al = body(arjun.get(f'{API}/api/mission/contacts', timeout=20))
        assert cid not in [i['id'] for i in al['items']]
        rd = arjun.delete(f'{API}/api/mission/contacts/{cid}', timeout=20)
        assert rd.status_code == 200 and body(rd)['removed'] is True
        assert cid in [i['id'] for i in body(riya.get(f'{API}/api/mission/contacts', timeout=20))['items']]
        # Riya deletes her own
        for i in (cid, phones[pb]['id']):
            assert riya.delete(f'{API}/api/mission/contacts/{i}', timeout=20).status_code == 200
        left = [i['id'] for i in body(riya.get(f'{API}/api/mission/contacts', timeout=20))['items']]
        assert cid not in left and phones[pb]['id'] not in left

    def test_own_number_skipped(self):
        riya = student_session('riya')
        me = body(ceo(f"students/{B['ids']['riya']}"))['phone']
        r = riya.post(f'{API}/api/mission/contacts', json={'contacts': [{'name': 'TEST_me', 'tel': [me]}]}, timeout=20)
        assert r.status_code == 200 and body(r)['saved'] == 0 and body(r)['skipped'] == 1, r.text

    def test_limits_422(self):
        riya = student_session('riya')
        many = [{'name': f'TEST_{i}', 'tel': [f'98{i:08d}']} for i in range(101)]
        assert riya.post(f'{API}/api/mission/contacts', json={'contacts': many}, timeout=20).status_code == 422
        r = riya.post(f'{API}/api/mission/contacts', json={'contacts': [{'name': 'x', 'tel': ['9822200001'] * 7}]}, timeout=20)
        assert r.status_code == 422


# --- Usage events
class TestEvents:
    def test_event_ok_and_visible(self):
        s = student_session('arjun')
        r = s.post(f'{API}/api/events', json={'name': 'rank_tool_open', 'props': {'page': 'rank', 'tool': 'testtool_x'}}, timeout=20)
        assert r.status_code == 204, r.text
        anon = requests.post(f'{API}/api/events', json={'name': 'page_open', 'vid': 'abcd1234-ef', 'props': {'page': 'home'}}, headers={'Origin': ORIGIN}, timeout=20)
        assert anon.status_code == 204, anon.text

    def test_event_bad_422(self):
        s = student_session('arjun')
        assert s.post(f'{API}/api/events', json={'name': 'hack'}, timeout=20).status_code == 422
        assert s.post(f'{API}/api/events', json={'name': 'page_open', 'props': {'page': 'Bad Page!'}}, timeout=20).status_code == 422
        assert s.post(f'{API}/api/events', json={'name': 'page_open', 'props': {'x': 1}}, timeout=20).status_code == 422


# --- Signup source
class TestSignupSource:
    def _signup(self, source=None, headers=None):
        phone = '+9197' + str(random.randint(10000000, 99999999))
        payload = {'phone': phone, 'pin': '4826', 'confirm_pin': '4826'}
        if source is not None:
            payload['source'] = source
        r = requests.post(f'{API}/api/auth/phone/signup', json=payload, headers=headers or {}, timeout=20)
        return phone, r

    def test_web_with_source(self):
        phone, r = self._signup({'utm_source': 'insta', 'utm_medium': 'reel', 'utm_campaign': 'aits_dec', 'referrer': 'instagram.com', 'landing': '/series/all-india-jee'},
                                {'Origin': ORIGIN, 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Linux; Android 14) Chrome/120'})
        assert r.status_code in (200, 201), r.text
        items = body(ceo('students', q=phone[3:]))['items']
        assert items, 'new student not in /students'
        p = items[0]
        assert p['signup_channel'] == 'web' and p['signup_device'] == 'android', p
        assert p['signup_source']['utm_source'] == 'insta' and p['signup_source']['landing'] == '/series/all-india-jee'

    def test_app_without_source(self):
        phone, r = self._signup(None, {'User-Agent': 'python-httpx/0.27'})
        assert r.status_code in (200, 201), r.text
        p = body(ceo('students', q=phone[3:]))['items'][0]
        assert p['signup_channel'] == 'app' and p['signup_source'] is None, p

    def test_bad_source_422(self):
        _, r = self._signup({'landing': 'http://evil.com'}, {'Origin': ORIGIN})
        assert r.status_code == 422


# --- Lockout: run LAST (blocks the caller IP for the 10-minute window)
@pytest.mark.skipif(os.environ.get('CEO_LOCKOUT') != '1', reason='set CEO_LOCKOUT=1; blocks CEO key for 10 min')
def test_zz_lockout_429():
    codes = [requests.get(f'{API}/api/ceo/v1/summary', headers={'X-CEO-Key': 'w' * 30}, timeout=20).status_code for _ in range(21)]
    assert codes[:20].count(401) >= 1 and codes[-1] == 429, codes
    assert ceo('summary').status_code == 429  # right key also blocked in the window
