# Result analysis (cohort stats) + gpt-6-astra AI solutions + owner password + PDF AI text
import os
import time
import uuid
import pytest
import requests

pytest.skip('Retired customer-database fixture: use the isolated auth and exam harnesses.', allow_module_level=True)

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
API = BASE_URL + '/api'
HDR = {'Origin': BASE_URL, 'Content-Type': 'application/json'}
PHONE = '99000003' + str(int(time.time()) % 90 + 10)


def unwrap(r):
    j = r.json()
    return j['data'] if isinstance(j, dict) and 'data' in j and 'error' in j else j


def sess(phone=PHONE):
    s = requests.Session()
    s.headers.update(HDR)
    r = s.post(API + '/auth/phone', json={'phone': phone})
    assert r.status_code == 200, r.text
    return s


@pytest.fixture(scope='module')
def student():
    return sess()


@pytest.fixture(scope='module')
def mock1(student):
    d = unwrap(student.get(API + '/exam-navigation/bitsat/catalogue', params={'kind': 'mocks'}))
    m = d['items'][0]
    assert m['title'] == 'BITSAT Full Mock 01'
    return m


@pytest.fixture(scope='module')
def active(student, mock1):
    student.post(API + f"/sets/{mock1['id']}/preflight", json={})
    r = student.post(API + f"/sets/{mock1['id']}/start", json={'start_key': str(uuid.uuid4()), 'device_checked': True})
    assert r.status_code == 200, r.text
    return unwrap(r)


def put(s, aid, qid, val='A', rev=1):
    return s.put(API + f'/attempts/{aid}/answers/{qid}', json={'value': val, 'revision': rev, 'request_id': str(uuid.uuid4())})


class TestOwner:
    def test_new_password_works(self):
        s = requests.Session(); s.headers.update(HDR)
        r = s.post(API + '/auth/login', json={'email': os.environ['ADMIN_EMAIL'], 'password': os.environ['ADMIN_PASSWORD']})
        assert r.status_code == 200, r.text
        d = unwrap(s.get(API + '/studio/mock-books'))
        p = d['items'][0]['ai_solutions']
        print('progress', p)
        assert p['total'] == 7100 and p['ready'] >= 142

    def test_old_password_rejected(self):
        r = requests.post(API + '/auth/login', headers=HDR, json={'email': os.environ['ADMIN_EMAIL'], 'password': uuid.uuid4().hex})
        assert r.status_code == 401, r.text


class TestActiveAndSubmit:
    def test_ai_solutions_409_while_active(self, student, active):
        r = student.get(API + f"/attempts/{active['id']}/ai-solutions")
        assert r.status_code == 409, r.text
        assert student.get(API + f"/attempts/{active['id']}/cohort").status_code == 409

    def test_other_user_cannot_read(self, active):
        other = sess('9900000399')
        r = other.get(API + f"/attempts/{active['id']}/ai-solutions")
        assert r.status_code in (403, 404), r.text

    def test_submit(self, student, active):
        aid = active['id']
        main = [q for q in active['questions'] if not q.get('bonus')]
        for q in main[:20]:
            assert put(student, aid, q['id'], 'B').status_code == 200
        r = student.post(API + f'/attempts/{aid}/submit', json={})
        assert r.status_code in (200, 202), r.text
        for _ in range(20):
            r = student.get(API + f'/attempts/{aid}/results')
            if r.status_code == 200:
                break
            time.sleep(1.5)
        assert r.status_code == 200, r.text

    def test_ai_solutions_ready(self, student, active):
        r = student.get(API + f"/attempts/{active['id']}/ai-solutions")
        assert r.status_code == 200, r.text
        d = unwrap(r)
        print('ready', d['ready'], d['total'])
        assert d['total'] == 142 and d['ready'] == 142
        it = d['items'][0]
        assert it['label'] == 'AI generated' and it['model'] == 'gpt-6-astra'
        s = it['solution']
        for k in ('concept', 'given', 'steps', 'final_answer', 'insight', 'shortcut', 'common_mistakes', 'time_tip', 'difficulty'):
            assert k in s
        assert len(s['steps']) >= 3

    def test_cohort_available(self, student, active):
        d = None
        for _ in range(10):
            d = unwrap(student.get(API + f"/attempts/{active['id']}/cohort"))
            if d['state'] == 'available':
                break
            time.sleep(2.5)
        print({k: d.get(k) for k in ('state', 'rank', 'percentile', 'average', 'median', 'top', 'sample_size', 'sections')})
        assert d['state'] == 'available', d
        assert isinstance(d['rank'], int) and d['rank'] >= 1
        assert d['sample_size'] >= 2
        for k in ('percentile', 'average', 'median', 'top'):
            assert d[k] is not None
        assert len(d['sections']) == 5
        assert len(d['questions']) >= 130
        q = d['questions'][0]
        assert q['correct'] + q['incorrect'] + q['skipped'] + q.get('bonus', 0) + q.get('dropped', 0) <= q['denominator'] == d['sample_size']

    def test_pdf_has_ai_text(self, student, active):
        aid = active['id']
        r = student.post(API + f'/attempts/{aid}/report', json={'score_version': 'original'})
        assert r.status_code == 200, r.text
        j = unwrap(r)
        for _ in range(90):
            if j['status'] in ('done', 'failed'):
                break
            time.sleep(2)
            j = unwrap(student.get(API + f"/jobs/{j['id']}"))
        assert j['status'] == 'done', j
        r = student.get(API + f"/jobs/{j['id']}/download")
        assert r.status_code == 200 and r.content[:4] == b'%PDF'
        import fitz
        doc = fitz.open(stream=r.content, filetype='pdf')
        txt = ''.join(p.get_text() for p in doc)
        print('pages', len(doc), 'ai blocks', txt.count('AI generated step-by-step solution (gpt-6-astra)'))
        assert 'AI generated step-by-step solution (gpt-6-astra)' in txt


class TestPeerAttempt:
    def test_seeded_peer_attempt(self):
        s = sess('9900000200')
        aid = '845518e3-d954-4bb9-80b3-dcdf0d27196f'
        d = unwrap(s.get(API + f'/attempts/{aid}/ai-solutions'))
        assert d['ready'] == d['total'] == 142
        c = unwrap(s.get(API + f'/attempts/{aid}/cohort'))
        assert c['state'] in ('available', 'preparing'), c
