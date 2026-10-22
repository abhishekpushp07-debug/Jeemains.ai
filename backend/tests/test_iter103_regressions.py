"""Iteration 103 regressions: (1) legacy completed attempt lacking receipt -> results 202 not 500,
(2) discovery catalogue returns batched per-user `saved` flags, (3) report-group detail parser:
invalid version/shape 404, legacy null/missing source_hash, exact predicate.
Run: cd /app/backend && python -m pytest tests/test_iter103_regressions.py -n0 -p no:asyncio -v
Run AFTER `seed_ui_journey.py cleanup` (shares student 9900000196). Synthetic TEST_R103_ fixtures only, no AI calls.
"""
import asyncio, os, re, sys, time, uuid
from pathlib import Path
import pytest, requests

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from dotenv import load_dotenv
load_dotenv(BACKEND / '.env'); load_dotenv(BACKEND.parent / 'frontend' / '.env')
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
from tejas.db import db
from tejas.packs import insert_attempt

LOOP = asyncio.new_event_loop(); asyncio.set_event_loop(LOOP); run = LOOP.run_until_complete
TAG = 'TEST_R103_' + uuid.uuid4().hex[:8]
PHONE, OTHER_PHONE = '9900000196', '9900000197'
PACKS, ATT = set(), []
RULES = {'minutes': 180, 'correct': 4, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'}


def body(r):
    j = r.json(); return j.get('data', j) if isinstance(j, dict) else j


def login_phone(phone):
    s = requests.Session()
    assert s.post(f'{BASE_URL}/api/auth/phone', json={'phone': phone}).status_code == 200
    me = body(s.get(f'{BASE_URL}/api/auth/me')); s.uid = (me.get('user') or me)['id']; return s


def _creds():
    text = (BACKEND.parent / 'memory' / 'test_credentials.md').read_text()
    return re.search(r'Email:\s*(\S+)', text).group(1), re.search(r'Password:\s*(\S+)', text).group(1)


def qs(n=10):
    return [{'id': str(uuid.uuid4()), 'number': i + 1, 'subject': 'Physics', 'section': 'Physics', 'type': 'mcq', 'text': f'TEST {i}',
             'answer': 'B', 'options': {'A': '1', 'B': '2', 'C': '3', 'D': '4'}, 'q_refs': [], 's_refs': [], 'render_mode': 'text'} for i in range(n)]


async def _cleanup():
    await db.tejas_attempts.delete_many({'$or': [{'id': {'$regex': '^' + TAG}}, {'set_id': {'$regex': '^' + TAG}}]})
    await db.tejas_sets.delete_many({'id': {'$regex': '^' + TAG}})
    await db.tejas_saved_tests.delete_many({'set_id': {'$regex': '^' + TAG}})
    await db.tejas_question_reports.delete_many({'set_id': {'$regex': '^' + TAG}})
    await db.tejas_ledgers.delete_many({'id': {'$regex': '^' + TAG}})
    await db.tejas_jobs.delete_many({'$or': [{'set_id': {'$regex': '^' + TAG}}, {'payload.attempt_id': {'$regex': '^' + TAG}}]})
    if PACKS:
        await db.tejas_packs.delete_many({'_id': {'$in': list(PACKS)}})


@pytest.fixture(scope='session', autouse=True)
def guard():
    n0 = run(db.tejas_sets.count_documents({'id': {'$not': re.compile('^TEST')}}))
    yield
    run(_cleanup())
    assert run(db.tejas_sets.count_documents({'id': {'$not': re.compile('^TEST')}})) == n0
    assert run(db.tejas_attempts.count_documents({'id': {'$regex': '^' + TAG}})) == 0


@pytest.fixture(scope='session')
def student(): return login_phone(PHONE)


@pytest.fixture(scope='session')
def other(): return login_phone(OTHER_PHONE)


@pytest.fixture(scope='session')
def owner():
    s = requests.Session(); e, p = _creds()
    if s.post(f'{BASE_URL}/api/auth/login', json={'email': e, 'password': p}).status_code != 200:
        pytest.skip('owner login failed')
    return s


# ---------- (1) results grading branch: missing receipt ----------
class TestReceipt:
    def test_legacy_completed_without_receipt_returns_202(self, student):
        a = {'id': f'{TAG}-att-{uuid.uuid4().hex[:8]}', 'user_id': student.uid, 'set_id': f'{TAG}-legacy', 'title': f'{TAG} legacy',
             'exam': 'JEE Main', 'version': 1, 'rules': RULES, 'questions': qs(), 'mode': 'practice', 'status': 'completed',
             'answers': {}, 'test_kind': 'mock', 'parent_attempt': None, 'started_at': time.time() - 4000, 'deadline': 0,
             'submitted_at': time.time() - 100, 'competition_end': 0, 'start_key': uuid.uuid4().hex, 'key_version': 1, 'summary': None}
        run(insert_attempt(a)); PACKS.add(a['pack_id']); ATT.append(a['id'])
        run(db.tejas_attempts.update_one({'id': a['id']}, {'$unset': {'receipt': '', 'grading_status': ''}}))
        assert 'receipt' not in run(db.tejas_attempts.find_one({'id': a['id']}))
        r = student.get(f'{BASE_URL}/api/attempts/{a["id"]}/results')
        assert r.status_code in (200, 202), (r.status_code, r.text[:300])
        if r.status_code == 202:
            d = body(r); assert d['status'] == 'grading' and d['receipt'] is None and r.headers.get('Retry-After') == '2'

    def test_foreign_and_missing_attempt_404(self, other):
        if ATT:
            assert other.get(f'{BASE_URL}/api/attempts/{ATT[0]}/results').status_code == 404
        assert other.get(f'{BASE_URL}/api/attempts/{TAG}-nope/results').status_code == 404


# ---------- (2) batched saved flags on catalogue ----------
@pytest.fixture(scope='session')
def two_sets(student):
    ids = []
    for k in range(2):
        sid = f'{TAG}-cat{k}'
        run(db.tejas_sets.insert_one({'id': sid, 'title': f'{TAG} catalogue {k}', 'exam': 'JEE Main', 'status': 'published',
            'audience': 'restricted', 'allowed_phones': ['+91' + PHONE, '+91' + OTHER_PHONE], 'revision': 1, 'version': 1, 'rules': RULES,
            'questions': qs(75), 'test_kind': 'mock', 'full_length': True, 'competition': False, 'created_at': time.time(), 'published_at': time.time()}))
        ids.append(sid)
    return ids


class TestCatalogueSaved:
    C = '/api/exam-navigation/jee-main/catalogue?kind=mocks&q='

    def _items(self, s):
        r = s.get(BASE_URL + self.C + TAG); assert r.status_code == 200, r.text[:300]
        return {i['id']: i for i in body(r)['items']}

    def test_saved_flags_scoped_per_user(self, student, other, two_sets):
        it = self._items(student)
        assert set(two_sets) <= set(it), list(it)
        assert all(isinstance(it[s]['saved'], bool) and it[s]['saved'] is False for s in two_sets)
        assert body(student.post(f'{BASE_URL}/api/my/tests/saved/{two_sets[0]}', json={}))['saved'] is True
        it = self._items(student)
        assert it[two_sets[0]]['saved'] is True and it[two_sets[1]]['saved'] is False
        io = self._items(other)
        assert io[two_sets[0]]['saved'] is False and io[two_sets[1]]['saved'] is False  # isolation
        assert body(student.delete(f'{BASE_URL}/api/my/tests/saved/{two_sets[0]}'))['saved'] is False
        assert self._items(student)[two_sets[0]]['saved'] is False

    def test_real_catalogue_has_saved_bool(self, student):
        r = student.get(f'{BASE_URL}/api/exam-navigation/jee-main/catalogue?kind=mocks')
        assert r.status_code == 200
        items = body(r)['items']; assert len(items) <= 12
        assert all(isinstance(i.get('saved'), bool) for i in items)


# ---------- (3) report group detail parser ----------
def rep(set_id, qid, uid, version=1, source_hash='h1', unset_hash=False):
    doc = {'_id': f'{TAG}-rep-{uuid.uuid4().hex[:10]}', 'set_id': set_id, 'version': version, 'question_id': qid, 'number': 1, 'title': 'T',
           'exam': 'JEE Main', 'user_id': uid, 'attempt_id': f'{TAG}-a', 'category': 'key', 'context': 'results', 'note': 'TEST', 'status': 'open',
           'created_at': time.time(), 'source_hash': source_hash}
    if unset_hash: doc.pop('source_hash')
    run(db.tejas_question_reports.insert_one(doc)); return doc['_id']


class TestReportGroup:
    G = '/api/studio/question-report-group?group_id='

    def g(self, owner, gid):
        return owner.get(BASE_URL + self.G + requests.utils.quote(gid, safe=''))

    def test_parser_and_legacy(self, owner):
        S = f'{TAG}-rset'
        rep(S, 'qN', 'u2', unset_hash=True); rep(S, 'qN', 'u3', source_hash='')
        rep(S, 'qH', 'u1'); rep(S, 'qH', 'u2', version=2)
        d = self.g(owner, f'{S}|1|qN|'); assert d.status_code == 200, d.text[:200]
        assert body(d)['total'] == 2  # missing and blank grouped as legacy
        assert body(self.g(owner, f'{S}|1|qH|h1'))['total'] == 1  # exact version predicate
        assert body(self.g(owner, f'{S}|2|qH|h1'))['total'] == 1
        for bad in (f'{S}|x|qH|h1', f'{S}|-1|qH|h1', f'{S}|1|qH', f'{S}|1|qH|h1|extra', f'{S}|99999999999|qH|h1', f'{S}|3|qH|h1', f'{S}|1|qH|nohash', 'nope', '|||'):
            assert self.g(owner, bad).status_code == 404, bad
        # priorities group_id round-trips for legacy groups
        pr = body(owner.get(f'{BASE_URL}/api/studio/question-report-priorities?status=open'))
        while True:
            mine = [i for i in pr['items'] if i['set_id'] == S]
            if mine or pr['page'] >= pr['pages']: break
            pr = body(owner.get(f'{BASE_URL}/api/studio/question-report-priorities?status=open&page={pr["page"] + 1}'))
        assert mine
        for i in mine:
            assert self.g(owner, i['group_id']).status_code == 200, i['group_id']

    def test_explicit_null_source_hash_legacy(self, owner):
        S = f'{TAG}-rnull'
        rep(S, 'qZ', 'u1', source_hash=None)
        r = self.g(owner, f'{S}|1|qZ|')
        assert r.status_code == 200 and body(r)['total'] == 1, (r.status_code, r.text[:200])

    def test_student_forbidden(self, student):
        assert student.get(BASE_URL + self.G + 'a|1|b|c').status_code == 403
