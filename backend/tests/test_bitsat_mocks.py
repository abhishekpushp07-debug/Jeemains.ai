# BITSAT full mocks: catalogue, chapter tests unchanged, bonus gating, scoring sections, PDF report, studio mock-book
import os
import time
import uuid
import io
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
API = BASE_URL + '/api'
HDR = {'Origin': BASE_URL, 'Content-Type': 'application/json'}
PHONE = '99000001' + str(int(time.time()) % 90 + 10)


def unwrap(r):
    j = r.json()
    return j['data'] if isinstance(j, dict) and 'data' in j and 'error' in j else j


@pytest.fixture(scope='module')
def student():
    s = requests.Session()
    s.headers.update(HDR)
    r = s.post(API + '/auth/phone', json={'phone': PHONE})
    assert r.status_code == 200, r.text
    assert unwrap(r)['role'] == 'student'
    return s


@pytest.fixture(scope='module')
def mocks(student):
    items = []
    for p in (1, 2, 3, 4, 5):
        r = student.get(API + '/exam-navigation/bitsat/catalogue', params={'kind': 'mocks', 'page': p})
        assert r.status_code == 200, r.text
        d = unwrap(r)
        items += d['items']
        if p >= d['pages']:
            break
    return items


@pytest.fixture(scope='module')
def attempt(student, mocks):
    # start mock 50 (least likely used by others)
    m = mocks[-1]
    r = student.post(API + f"/sets/{m['id']}/preflight", json={'test_response': 'A'})
    assert r.status_code == 200, r.text
    r = student.post(API + f"/sets/{m['id']}/start", json={'start_key': str(uuid.uuid4()), 'device_checked': True})
    assert r.status_code == 200, r.text
    return unwrap(r)


def put(student, aid, qid, val='A', rev=1):
    return student.put(API + f'/attempts/{aid}/answers/{qid}', json={'value': val, 'revision': rev, 'request_id': str(uuid.uuid4())})


class TestCatalogue:
    def test_health(self):
        r = requests.get(API + '/health')
        assert r.status_code == 200 and unwrap(r)['status'] == 'ok'

    def test_50_mocks_in_order(self, student, mocks):
        r = student.get(API + '/exam-navigation/bitsat/catalogue', params={'kind': 'mocks'})
        d = unwrap(r)
        assert d['total'] == 50 and d['pages'] == 5 and len(d['items']) == 12
        titles = [m['title'] for m in mocks]
        assert titles == [f'BITSAT Full Mock {i:02d}' for i in range(1, 51)], titles[:5]

    def test_chapter_counts_unchanged(self, student):
        d = unwrap(student.get(API + '/exam-navigation/bitsat/catalogue', params={'kind': 'chapters'}))
        assert d['total'] == 94
        assert d['subject_counts'].get('Physics') == 30
        assert d['subject_counts'].get('Chemistry') == 32
        assert d['subject_counts'].get('Mathematics') == 32

    def test_chapter_test_rules(self, student):
        d = unwrap(student.get(API + '/exam-navigation/bitsat/catalogue', params={'kind': 'chapters'}))
        s = unwrap(student.get(API + f"/my/sets/{d['items'][0]['id']}"))
        print(s.get('rules'), s.get('count'), s.get('question_count'))
        assert s['rules']['minutes'] == 60
        assert (s.get('count') or s.get('question_count')) == 50


class TestBonusFlow:
    def test_attempt_shape(self, attempt):
        qs = attempt['questions']
        assert len(qs) == 142
        assert attempt['rules']['minutes'] == 180
        assert attempt['rules']['bonus_rule']['main_count'] == 130
        assert abs(attempt['deadline'] - attempt['started_at'] - 10800) < 2
        bonus = [q for q in qs if q.get('bonus')]
        assert len(bonus) == 12
        from collections import Counter
        sec = Counter(q.get('section') for q in qs if not q.get('bonus'))
        print(sec)
        assert sec == {'Physics': 30, 'Chemistry': 30, 'English Proficiency': 10, 'Logical Reasoning': 20, 'Mathematics': 40}
        # no answer key leak
        assert all('answer' not in q and 'accepted_answers' not in q for q in qs)

    def test_bonus_locked_early(self, student, attempt):
        aid = attempt['id']
        r = student.post(API + f'/attempts/{aid}/bonus', json={})
        assert r.status_code == 409, r.text
        b = next(q for q in attempt['questions'] if q.get('bonus'))
        assert put(student, aid, b['id']).status_code == 409

    def test_answer_129_then_bonus_still_locked(self, student, attempt):
        aid = attempt['id']
        main = [q for q in attempt['questions'] if not q.get('bonus')]
        for q in main[:129]:
            r = put(student, aid, q['id'], 'A')
            assert r.status_code == 200, r.text
        r = student.post(API + f'/attempts/{aid}/bonus', json={})
        assert r.status_code == 409 and '1 still unanswered' in r.text, r.text
        # visiting does not count
        r = student.post(API + f'/attempts/{aid}/visit', json={'question_id': main[129]['id']})
        assert r.status_code == 200
        assert student.post(API + f'/attempts/{aid}/bonus', json={}).status_code == 409

    def test_unlock_and_lock_main(self, student, attempt):
        aid = attempt['id']
        main = [q for q in attempt['questions'] if not q.get('bonus')]
        last = main[129]
        assert put(student, aid, last['id'], 'B').status_code == 200
        r = student.post(API + f'/attempts/{aid}/bonus', json={})
        assert r.status_code == 200, r.text
        assert unwrap(r)['bonus_unlocked_at'] > 0
        # idempotent
        assert student.post(API + f'/attempts/{aid}/bonus', json={}).status_code == 200
        r = put(student, aid, main[0]['id'], 'B', rev=2)
        assert r.status_code == 409 and 'locked' in r.text
        bonus = [q for q in attempt['questions'] if q.get('bonus')]
        for q in bonus[:5]:
            assert put(student, aid, q['id'], 'A').status_code == 200

    def test_submit_and_results(self, student, attempt):
        aid = attempt['id']
        r = student.post(API + f'/attempts/{aid}/submit', json={})
        assert r.status_code in (200, 202), r.text
        for _ in range(20):
            r = student.get(API + f'/attempts/{aid}/results')
            if r.status_code == 200:
                break
            time.sleep(1.5)
        assert r.status_code == 200, r.text
        d = unwrap(r)
        s = d['summary']
        assert s['maximum'] == 426
        names = [x['name'] for x in s['sections']]
        assert names == ['Physics', 'Chemistry', 'English Proficiency', 'Logical Reasoning', 'Mathematics'], names
        assert s['main_block']['count'] == 130 if 'count' in s['main_block'] else True
        bb = s['bonus_block']
        assert bb['entered'] is True
        assert bb['correct'] + bb['incorrect'] == 5 and bb['skipped'] == 7
        mb = s['main_block']
        assert mb['skipped'] == 0 and mb['correct'] + mb['incorrect'] == 130
        assert s['score'] == sum(x['score'] for x in s['sections']) + bb['score']
        assert s['score'] == 3 * (mb['correct'] + bb['correct']) - (mb['incorrect'] + bb['incorrect'])
        q = d['questions'][0]
        assert 'response' in q and q['accepted_answers']
        pytest.attempt_id = aid

    def test_pdf_report(self, student, attempt):
        aid = attempt['id']
        r = None
        for _ in range(5):
            r = student.post(API + f'/attempts/{aid}/report', json={'score_version': 'original'})
            if r.status_code == 200:
                break
            time.sleep(2)
        assert r.status_code == 200, r.text
        j = unwrap(r)
        for _ in range(60):
            if j['status'] in ('ready', 'completed', 'done', 'failed'):
                break
            time.sleep(2)
            j = unwrap(student.get(API + f"/jobs/{j['id']}"))
        assert j['status'] != 'failed', j
        r = student.get(API + f"/jobs/{j['id']}/download")
        assert r.status_code == 200 and r.content[:4] == b'%PDF'
        import fitz
        doc = fitz.open(stream=r.content, filetype='pdf')
        txt = ''.join(doc[i].get_text() for i in range(min(3, len(doc))))
        print('pages', len(doc), txt[:1500])
        assert 'Physics' in txt and 'Bonus' in txt and 'Logical Reasoning' in txt


class TestBonusNotEntered:
    def test_submit_without_bonus(self, student, mocks):
        m = mocks[-2]
        student.post(API + f"/sets/{m['id']}/preflight", json={'test_response': 'A'})
        a = unwrap(student.post(API + f"/sets/{m['id']}/start", json={'start_key': str(uuid.uuid4()), 'device_checked': True}))
        main = [q for q in a['questions'] if not q.get('bonus')]
        assert put(student, a['id'], main[0]['id'], 'A').status_code == 200
        student.post(API + f"/attempts/{a['id']}/submit", json={})
        for _ in range(20):
            r = student.get(API + f"/attempts/{a['id']}/results")
            if r.status_code == 200:
                break
            time.sleep(1.5)
        s = unwrap(r)['summary']
        assert s['bonus_block']['entered'] is False
        assert s['main_block']['skipped'] == 129


class TestStudio:
    def test_mock_book(self):
        s = requests.Session()
        s.headers.update(HDR)
        r = s.post(API + '/auth/login', json={'email': 'abhishek@billpe.com', 'password': '55241878'})
        if r.status_code != 200:
            pytest.skip('owner login ' + r.text)
        d = unwrap(s.get(API + '/studio/mock-books'))
        b = d['items'][0]
        assert b['live'] == 50 and b['held'] == 0 and len(b['mocks']) == 50
        assert all(m['main_count'] == 130 and m['bonus_count'] == 12 and m['keys'] == 142 for m in b['mocks'])
        # student must be forbidden
        st = requests.Session()
        st.headers.update(HDR)
        st.post(API + '/auth/phone', json={'phone': PHONE})
        assert st.get(API + '/studio/mock-books').status_code in (401, 403)
