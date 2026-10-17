# Owner-side AI solution tags (worker), student read-only path, disagreement gating, Studio AI Answer Review API
# Run with -n0 (tests share state via pytest.m10_*): pytest tests/test_ai_tags_review.py -n0 -v
import os
import time
import uuid
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
API = BASE_URL + '/api'
HDR = {'Origin': BASE_URL, 'Content-Type': 'application/json'}
PHONE = '99000003' + str(int(time.time()) % 90 + 10)
M10 = '1a43cf59-11b0-5ced-9f5e-5244bf041c46'
M11 = 'e4b4bf76-002f-5b9d-9caf-50e075fa0c01'


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
def owner():
    s = requests.Session(); s.headers.update(HDR)
    r = s.post(API + '/auth/login', json={'email': 'abhishek@billpe.com', 'password': '55241878'})
    assert r.status_code == 200, r.text
    return s


def mocks(student):
    return unwrap(student.get(API + '/exam-navigation/bitsat/catalogue', params={'kind': 'mocks'}))['items']


def take(student, set_id, n=5):
    student.post(API + f"/sets/{set_id}/preflight", json={})
    r = student.post(API + f"/sets/{set_id}/start", json={'start_key': str(uuid.uuid4()), 'device_checked': True})
    assert r.status_code == 200, r.text
    a = unwrap(r)
    for q in [q for q in a['questions'] if not q.get('bonus')][:n]:
        student.put(API + f"/attempts/{a['id']}/answers/{q['id']}", json={'value': 'A', 'revision': 1, 'request_id': str(uuid.uuid4())})
    r = student.post(API + f"/attempts/{a['id']}/submit", json={})
    assert r.status_code in (200, 202), r.text
    for _ in range(20):
        if student.get(API + f"/attempts/{a['id']}/results").status_code == 200:
            break
        time.sleep(1.5)
    return a


def sol_map(student, aid):
    t = time.time()
    r = student.get(API + f'/attempts/{aid}/ai-solutions')
    dt = time.time() - t
    assert r.status_code == 200, r.text
    return unwrap(r), dt


class TestStudentReadOnly:
    def test_mock01_ready_fast(self, student):
        m1 = [m for m in mocks(student) if m['title'] == 'BITSAT Full Mock 01'][0]
        a = take(student, m1['id'])
        d, dt = sol_map(student, a['id'])
        print('mock01 ready', d['ready'], d['total'], 'time', round(dt, 2))
        assert dt < 2.0
        assert d['total'] == 142 and d['ready'] == 142
        s = d['items'][0]['solution']
        assert d['items'][0]['label'] == 'AI generated' and len(s['steps']) >= 3

    def test_mock10_q105_under_review(self, student):
        a = take(student, M10, 2)
        d, dt = sol_map(student, a['id'])
        qnum = {q['id']: q['number'] for q in a['questions']}
        by = {qnum[x['question_id']]: x for x in d['items']}
        print('mock10 ready', d['ready'], 'q105', by[105]['state'], 'time', round(dt, 2))
        assert by[105]['state'] == 'under_review' and by[105]['solution'] is None
        pytest.m10_attempt = a['id']
        pytest.m10_qid = [k for k, v in qnum.items() if v == 105][0]


class TestReviewApi:
    def test_student_forbidden(self, student):
        assert student.get(API + '/studio/ai-review').status_code in (401, 403)
        assert student.post(API + f'/studio/ai-review/{M10}/x', json={'action': 'reopen'}).status_code in (401, 403)

    def test_list_open(self, owner):
        d = unwrap(owner.get(API + '/studio/ai-review', params={'state': 'open'}))
        print('counts', d['counts'], 'progress', d['progress'])
        keys = {(x['set_id'], x['number']) for x in d['items']}
        # M11 Q136 was key_confirmed + re-solved (now agrees) in iteration 95, so it left the list
        assert (M10, 105) in keys and (M11, 113) in keys
        x = [i for i in d['items'] if i['set_id'] == M10 and i['number'] == 105][0]
        assert x['key'] == 'A' and x['ai_answer'] == 'C' and x['image_count'] >= 1 and x['insight']
        assert d['progress']['total'] == 11800
        r = owner.get(API + f"/studio/sets/{M10}/questions/{x['question_id']}/asset/question/0")
        assert r.status_code == 200 and r.headers['content-type'].startswith('image'), r.status_code

    def test_invalid_action(self, owner):
        r = owner.post(API + f'/studio/ai-review/{M10}/{pytest.m10_qid}', json={'action': 'bogus'})
        assert r.status_code in (400, 422), r.text

    def test_not_found(self, owner):
        r = owner.post(API + f'/studio/ai-review/{M10}/nope', json={'action': 'reopen'})
        assert r.status_code == 404, r.text

    def test_key_wrong_then_student_sees_flag(self, owner, student):
        r = owner.post(API + f'/studio/ai-review/{M10}/{pytest.m10_qid}', json={'action': 'key_wrong', 'note': 'TEST_note'})
        assert r.status_code == 200, r.text
        assert unwrap(r)['review']['status'] == 'key_wrong'
        d = unwrap(owner.get(API + '/studio/ai-review', params={'state': 'key_wrong'}))
        assert any(i['question_id'] == pytest.m10_qid for i in d['items'])
        d, _ = sol_map(student, pytest.m10_attempt)
        x = [i for i in d['items'] if i['question_id'] == pytest.m10_qid][0]
        assert x['state'] == 'ready' and x['solution'] and x['flag']

    def test_reopen(self, owner, student):
        r = owner.post(API + f'/studio/ai-review/{M10}/{pytest.m10_qid}', json={'action': 'reopen'})
        assert r.status_code == 200 and unwrap(r)['review'] is None
        d = unwrap(owner.get(API + '/studio/ai-review', params={'state': 'open'}))
        assert any(i['question_id'] == pytest.m10_qid for i in d['items'])
        d, _ = sol_map(student, pytest.m10_attempt)
        x = [i for i in d['items'] if i['question_id'] == pytest.m10_qid][0]
        assert x['state'] == 'under_review'


class TestRegression:
    def test_chapters_94(self, student):
        d = unwrap(student.get(API + '/exam-navigation/bitsat/catalogue', params={'kind': 'chapters'}))
        n = d.get('total', len(d['items']))
        print('chapters', n)
        assert n == 94

    def test_mock_book_50_live(self, owner):
        d = unwrap(owner.get(API + '/studio/mock-books'))
        b = d['items'][0]
        print({k: v for k, v in b.items() if k in ('live', 'live_count', 'ai_solutions', 'count')})
        assert b['ai_solutions']['total'] == 7100
