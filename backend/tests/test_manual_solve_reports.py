"""Regression (iteration 98): explicit owner manual Solve + student 'Report as wrong'.
In-process tests use isolated TEST_MS_ fixtures with a MOCK model boundary and hold the manual worker
file lock so no real worker can claim synthetic jobs. API tests use the public preview URL.
Run: pytest backend/tests/test_manual_solve_reports.py -p no:asyncio -n0 (serial).
"""
import asyncio, fcntl, hashlib, json, os, re, sys, time, uuid
from pathlib import Path
from unittest import mock

import pytest
import requests

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from dotenv import load_dotenv
load_dotenv(BACKEND / '.env')
load_dotenv(BACKEND.parent / 'frontend' / '.env')
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

from fastapi import HTTPException
from tejas import manual_solutions as M, mock_solutions as ms
from tejas.db import db

LOOP = asyncio.new_event_loop()
asyncio.set_event_loop(LOOP)
run = LOOP.run_until_complete
TAG = 'TEST_MS_' + uuid.uuid4().hex[:8]
STUDENT_PHONE = '9900000196'


def _creds():
    text = (BACKEND.parent / 'memory' / 'test_credentials.md').read_text()
    return re.search(r'Email:\s*(\S+)', text).group(1), re.search(r'Password:\s*(\S+)', text).group(1)


async def _prod_snapshot():
    h, n, ai = hashlib.sha256(), 0, 0
    async for d in db.tejas_sets.find({'id': {'$not': re.compile('^TEST')}}, {'_id': 0}).sort('id', 1):
        h.update(json.dumps(d, sort_keys=True, default=str).encode()); n += 1
        ai += sum(1 for q in d.get('questions', []) if q.get('ai_solution'))
    states = {r['_id']: r['count'] async for r in db.tejas_question_solutions.aggregate([{'$group': {'_id': '$state', 'count': {'$sum': 1}}}])}
    return {'sets': n, 'sha': h.hexdigest(), 'ai_tags': ai, 'states': states}


async def _cleanup():
    for c in (db.tejas_sets, db.tejas_attempts, db.tejas_question_solutions):
        await c.delete_many({'id': {'$regex': '^' + TAG}})
    await db.tejas_question_solutions.delete_many({'set_id': {'$regex': '^' + TAG}, 'trigger': 'owner_solve'})
    await db.tejas_manual_solves.delete_many({'set_id': {'$regex': '^' + TAG}})
    await db.tejas_solution_requests.delete_many({'set_id': {'$regex': '^' + TAG}})
    await db.tejas_question_reports.delete_many({'set_id': {'$regex': '^' + TAG}})


@pytest.fixture(scope='session', autouse=True)
def guard():
    lock = open('/tmp/manual-solution-worker.lock', 'w')
    fcntl.flock(lock, fcntl.LOCK_EX)  # no real worker can drain synthetic jobs while tests run
    before = run(_prod_snapshot())
    print('PRESERVATION BEFORE', before)
    yield before
    run(_cleanup())
    after = run(_prod_snapshot())
    print('PRESERVATION AFTER', after)
    fcntl.flock(lock, fcntl.LOCK_UN); lock.close()
    assert after == before, 'production sets/solutions changed'


def mcq(n, key='B', **kw):
    q = {'id': f'{TAG}-q{n}-{uuid.uuid4().hex[:4]}', 'number': n, 'subject': 'Physics', 'type': 'mcq', 'text': f'TEST {n}: 2+2?',
         'options': {'A': '3', 'B': '4', 'C': '5', 'D': '6'}, 'answer': key, 'q_refs': [], 'render_mode': 'text'}
    q.update(kw); return q


def put_set(questions, **kw):
    sid = f'{TAG}-set-{uuid.uuid4().hex[:6]}'
    doc = {'id': sid, 'title': 'TEST manual solve fixture', 'status': 'draft', 'exam': 'BITSAT', 'full_length': False,
           'revision': 1, 'questions': questions, 'qa_only': True}
    doc.update(kw); run(db.tejas_sets.insert_one(doc)); return sid


# ---------- Eligibility / preservation (pure) ----------
class TestEligibility:
    def test_rules(self):
        k = 'B'
        boiler = mcq(1, solution_kind='answer_key_only', solution=f'Supplied answer key: {k}. This book does not contain a worked solution.',
                     s_refs=[{'file_id': 'x'}], solution_accessible_text=f'Supplied key {k}; no worked solution provided.')
        custom = mcq(2, solution_kind='answer_key_only', solution='My own worked text')
        assert M.eligible(mcq(3)) and M.eligible(boiler)
        assert M.preserved(custom) == 'owner' and not M.eligible(custom)
        assert M.preserved(mcq(4, ai_solution={'x': 1})) == 'ai' and M.preserved(mcq(5, ai_solution_id='s')) == 'ai'
        assert M.preserved(mcq(6, solution='typed')) == 'owner' and M.preserved(mcq(7, s_refs=[{'f': 1}])) == 'owner'
        assert M.preserved(mcq(8, solution_accessible_text='alt')) == 'owner'
        assert not M.eligible(mcq(9, key='Z')) and not M.eligible(mcq(10, answer=''))
        assert not M.eligible(mcq(11, type='subjective'))
        assert M.eligible(mcq(12, type='integer', answer='7', options={}))
        assert not M.eligible(mcq(13, render_mode='source', q_refs=[])) and M.eligible(mcq(14, render_mode='source', q_refs=[{'file_id': 'f'}]))

    def test_none_solution_does_not_crash(self):
        # legacy docs may carry solution: None
        try:
            M.preserved(mcq(1, solution=None))
        except AttributeError as e:
            pytest.fail(f'preserved() crashes on solution=None: {e}')


# ---------- In-process request + worker with MOCK model ----------
@pytest.fixture(scope='module')
def owner_user():
    e, _ = _creds()
    u = run(db.tejas_users.find_one({'email': e}, {'_id': 0, 'password_hash': 0}))
    assert u and u['role'] == 'owner'
    return u


class BG:
    def __init__(self): self.tasks = []
    def add_task(self, f, *a): self.tasks.append(f)


CALLS = []


def fake_call(prompt, text, images, model, *a):
    CALLS.append(json.loads(text)['number'])
    time.sleep(0.05)
    v = M.ManualTenMark(concept='TEST', given=[], steps=[{'title': f's{i}', 'explanation': 'w'} for i in range(3)],
                        final_answer=json.loads(text)['answer'], key_agrees=True, insight='TEST insight', shortcut='', common_mistakes=[],
                        time_tip='', difficulty='Easy').model_dump()
    return v, {'model': 'mock'}


def _solution_ok(value):
    try:
        M.ManualTenMark(**value); return value
    except Exception:
        return None


@pytest.fixture
def mocked():
    CALLS.clear()
    with mock.patch.object(M, '_call', side_effect=fake_call) as c, mock.patch.object(M, 'reserve_call', mock.AsyncMock()), \
         mock.patch('subprocess.Popen', side_effect=AssertionError('spawn')):
        yield c


def _fill(value):
    # adapt fake output to ManualTenMark schema fields when stricter
    return value


class TestManualWorker:
    def test_request_idempotent_and_preserves(self, owner_user, mocked):
        saved = mcq(2, solution='Owner text')
        ai = mcq(3, ai_solution={'solution_id': 'keep', 'solution': {'insight': 'old'}})
        target = mcq(1)
        sid = put_set([target, saved, ai, mcq(4, type='subjective')])
        rid = 'TEST-req-' + uuid.uuid4().hex
        bg = BG()
        with mock.patch.object(M, 'dispatch_manual', mock.AsyncMock()):
            async def both():
                return await asyncio.gather(M.request_solve(sid, M.SolvePayload(request_id=rid), bg, owner_user),
                                            M.request_solve(sid, M.SolvePayload(request_id=rid), bg, owner_user))
            r1, r2 = run(both())
        assert r1['request_id'] == r2['request_id']
        assert r1['missing'] == 0 and r1['queued'] == 1 and r1['owner_saved'] == 1 and r1['ai_saved'] == 1 and r1['blocked'] == 1
        assert run(db.tejas_manual_solves.count_documents({'set_id': sid})) == 1
        assert run(db.tejas_solution_requests.count_documents({'set_id': sid})) == 1
        job = run(db.tejas_manual_solves.find_one({'set_id': sid}))
        assert job['trigger'] == 'owner_solve' and job['_id'] == M.job_id(sid, target)
        run(M.run_manual())
        assert CALLS == [1], f'model calls {CALLS}'
        s = run(db.tejas_sets.find_one({'id': sid}))
        qs = {q['number']: q for q in s['questions']}
        assert qs[1]['ai_solution']['content_hash'] == M.fingerprint(target)
        assert qs[2].get('ai_solution') is None and qs[2]['solution'] == 'Owner text'
        assert qs[3]['ai_solution']['solution_id'] == 'keep' and qs[1]['answer'] == 'B'
        assert run(db.tejas_manual_solves.find_one({'set_id': sid}))['state'] == 'ready'
        # repeating the same request does not create new model work
        with mock.patch.object(M, 'dispatch_manual', mock.AsyncMock()):
            again = run(M.request_solve(sid, M.SolvePayload(request_id=rid), BG(), owner_user))
        run(M.run_manual())
        assert CALLS == [1] and again['ai_saved'] == 2 and again['missing'] == 0

    def test_failed_requires_new_request(self, owner_user, mocked):
        sid = put_set([mcq(1)])
        rid = 'TEST-fail-' + uuid.uuid4().hex
        mocked.side_effect = RuntimeError('provider down')
        with mock.patch.object(M, 'dispatch_manual', mock.AsyncMock()):
            run(M.request_solve(sid, M.SolvePayload(request_id=rid), BG(), owner_user))
            run(M.run_manual())
            st = run(M.overview(run(M.paper(sid))))
            assert st['failed'] == 1 and st['errors'] and st['queued'] == 0
            assert mocked.call_count == 1, 'provider failure must not auto-retry'
            run(M.request_solve(sid, M.SolvePayload(request_id=rid), BG(), owner_user))  # same id: no retry
            assert run(db.tejas_manual_solves.find_one({'set_id': sid}))['state'] == 'failed'
            time.sleep(0.01)
            mocked.side_effect = fake_call
            run(M.request_solve(sid, M.SolvePayload(request_id=rid + '-new'), BG(), owner_user))
            assert run(db.tejas_manual_solves.find_one({'set_id': sid}))['state'] == 'queued'
            run(M.run_manual())
        assert run(db.tejas_manual_solves.find_one({'set_id': sid}))['state'] == 'ready'

    def test_concurrent_owner_edit_wins(self, owner_user, mocked):
        target = mcq(1)
        sid = put_set([target])
        def edit_during_call(*a):
            r = fake_call(*a)
            from pymongo import MongoClient
            with MongoClient(os.environ['MONGO_URL']) as c:
                c[os.environ['DB_NAME']].tejas_sets.update_one({'id': sid, 'questions.id': target['id']},
                    {'$set': {'questions.$.solution': 'Owner edit mid-flight', 'questions.$.solution_kind': 'owner_provided'}, '$inc': {'revision': 1}})
            return r
        mocked.side_effect = edit_during_call
        with mock.patch.object(M, 'dispatch_manual', mock.AsyncMock()):
            run(M.request_solve(sid, M.SolvePayload(request_id='TEST-edit-' + uuid.uuid4().hex), BG(), owner_user))
        run(M.run_manual())
        q = run(db.tejas_sets.find_one({'id': sid}))['questions'][0]
        assert q['solution'] == 'Owner edit mid-flight' and q.get('ai_solution') is None
        assert run(db.tejas_manual_solves.find_one({'set_id': sid}))['state'] == 'skipped'

    def test_revoked_owner_and_forged_job_rejected(self, owner_user, mocked):
        sid = put_set([mcq(1)])
        with mock.patch.object(M, 'dispatch_manual', mock.AsyncMock()):
            run(M.request_solve(sid, M.SolvePayload(request_id='TEST-rev-' + uuid.uuid4().hex), BG(), owner_user))
        demoted = dict(owner_user, role='student')
        with mock.patch.object(M.users, 'find_one', mock.AsyncMock(return_value=demoted)):
            run(M.run_manual())
        assert mocked.call_count == 0
        assert run(db.tejas_manual_solves.find_one({'set_id': sid}))['state'] == 'failed'
        # forged queue row without persisted request is refused before model
        sid2 = put_set([mcq(1)])
        q = run(db.tejas_sets.find_one({'id': sid2}))['questions'][0]
        forged = M.ManualJob(id=M.job_id(sid2, q), set_id=sid2, question_id=q['id'], number=1, fingerprint=M.fingerprint(q),
                             requested_by=owner_user['id'], request_id='nope', requested_at=M.now())
        run(db.tejas_manual_solves.insert_one(forged.to_mongo()))
        run(M.run_manual())
        assert mocked.call_count == 0 and run(db.tejas_manual_solves.find_one({'set_id': sid2}))['state'] == 'failed'

    def test_stale_lease_cannot_write(self, owner_user, mocked):
        sid = put_set([mcq(1)])
        with mock.patch.object(M, 'dispatch_manual', mock.AsyncMock()):
            run(M.request_solve(sid, M.SolvePayload(request_id='TEST-lease-' + uuid.uuid4().hex), BG(), owner_user))
        j = run(M.claim_manual())
        run(db.tejas_manual_solves.update_one({'_id': j.id}, {'$set': {'lease': 'other'}}))  # another worker took over
        run(M.solve_manual(j))
        assert run(db.tejas_sets.find_one({'id': sid}))['questions'][0].get('ai_solution') is None
        run(db.tejas_manual_solves.update_one({'_id': j.id}, {'$set': {'state': 'skipped'}}))

    def test_cli_default_noop(self):
        import subprocess
        out = subprocess.run([sys.executable, str(BACKEND / 'tools' / 'solution_worker.py')], capture_output=True, text=True, timeout=60)
        assert out.returncode == 0 and 'paus' in (out.stdout + out.stderr).lower()


# ---------- Public API ----------
@pytest.fixture(scope='module')
def owner():
    s = requests.Session(); e, p = _creds()
    r = s.post(f'{BASE_URL}/api/auth/login', json={'email': e, 'password': p})
    if r.status_code != 200: pytest.skip('owner login failed')
    return s


@pytest.fixture(scope='module')
def student():
    s = requests.Session()
    assert s.post(f'{BASE_URL}/api/auth/phone', json={'phone': STUDENT_PHONE}).status_code == 200
    me = s.get(f'{BASE_URL}/api/auth/me').json(); me = me.get('data', me)
    s.uid = (me.get('user') or me)['id']; return s


def body(r):
    j = r.json(); return j.get('data', j) if isinstance(j, dict) else j


class TestSolveApi:
    def test_auth_and_contract(self, owner, student):
        sid = put_set([mcq(1, solution='owner')])
        url = f'{BASE_URL}/api/studio/sets/{sid}/solve'
        assert requests.post(url, json={'request_id': 'x' * 20}).status_code == 401
        assert requests.get(url).status_code == 401
        assert student.post(url, json={'request_id': 'x' * 20}).status_code == 403
        assert student.get(f'{BASE_URL}/api/studio/solve-tests').status_code == 403
        assert owner.post(url, json={'request_id': 'short'}).status_code == 422
        assert owner.post(url, json={'request_id': 'y' * 101}).status_code == 422
        assert owner.post(url, json={'request_id': 'y' * 20, 'all': True}).status_code == 422
        r = owner.post(url, json={'request_id': 'TEST-api-' + uuid.uuid4().hex})
        assert r.status_code == 200, r.text
        d = body(r)
        assert d['owner_saved'] == 1 and d['missing'] == 0 and d['automatic_generation'] is False
        assert owner.get(f'{BASE_URL}/api/studio/sets/missing-{TAG}/solve').status_code == 404
        items = body(owner.get(f'{BASE_URL}/api/studio/solve-tests'))['items']
        assert len(items) >= 144 and all(set(i) == {'id', 'title', 'exam', 'kind'} for i in items)

    def test_import_guard_exemption_exact(self, owner):
        sid = put_set([mcq(1, solution='owner')], chapter_book_id=TAG + '-book')
        assert owner.post(f'{BASE_URL}/api/studio/sets/{sid}/solve', json={'request_id': 'TEST-imp-' + uuid.uuid4().hex}).status_code == 200
        r = owner.post(f'{BASE_URL}/api/studio/sets/{sid}/solve/extra', json={'request_id': 'TEST-imp-' + uuid.uuid4().hex})
        assert r.status_code == 409
        assert owner.put(f'{BASE_URL}/api/studio/sets/{sid}', json={}).status_code == 409


def make_attempt(uid, sid, qs, **kw):
    aid = f'{TAG}-att-{uuid.uuid4().hex[:6]}'
    doc = {'id': aid, 'user_id': uid, 'set_id': sid, 'title': 'TEST report fixture', 'exam': 'BITSAT', 'version': 1,
           'status': 'active', 'competition_end': 0, 'answers': {}, 'questions': qs, 'start_key': aid}
    doc.update(kw); run(db.tejas_attempts.insert_one(doc)); return aid


class TestReportsApi:
    def test_report_flows(self, owner, student):
        q1, q2, qb = mcq(1), mcq(2), mcq(3, bonus=True)
        sid = put_set([q1, q2, qb], status='published')
        active = make_attempt(student.uid, sid, [q1, q2, qb], status='active', competition_end=time.time() + 3600)
        done = make_attempt(student.uid, sid, [q1, q2, qb], status='completed', competition_end=0)
        embargo = make_attempt(student.uid, sid, [q1, q2, qb], status='completed', competition_end=time.time() + 3600)
        foreign = make_attempt(TAG + '-other-user', sid, [q1], status='completed')
        R = lambda a, q: f'{BASE_URL}/api/attempts/{a}/questions/{q}/report-wrong'
        before = run(db.tejas_attempts.find_one({'id': active}, {'_id': 0}))
        assert requests.post(R(active, q1['id']), json={'context': 'attempt'}).status_code == 401
        assert student.post(R(foreign, q1['id']), json={'context': 'results'}).status_code == 404
        assert student.post(R(done, qb['id']), json={'context': 'results'}).status_code == 404
        assert student.post(R(done, 'nope'), json={'context': 'results'}).status_code == 404
        assert student.post(R(active, q1['id']), json={'context': 'attempt', 'category': 'key'}).status_code == 403
        assert student.post(R(active, q1['id']), json={'context': 'results'}).status_code == 403
        assert student.post(R(embargo, q1['id']), json={'context': 'solutions', 'category': 'solution'}).status_code == 403
        assert student.post(R(active, q1['id']), json={'context': 'attempt', 'note': 'x' * 601}).status_code == 422
        assert student.post(R(active, q1['id']), json={'context': 'attempt', 'extra': 1}).status_code == 422
        r = student.post(R(active, q1['id']), json={'context': 'attempt', 'category': 'display', 'note': 'TEST blurry'})
        assert r.status_code == 200, r.text
        rec = body(r)
        assert set(rec) == {'id', 'question_id', 'status', 'category', 'created_at'} and rec['status'] == 'open'
        dup = body(student.post(R(active, q1['id']), json={'context': 'attempt', 'category': 'question'}))
        assert dup['id'] == rec['id'] and dup['category'] == 'display'
        after = run(db.tejas_attempts.find_one({'id': active}, {'_id': 0}))
        assert after == before, 'report mutated the attempt'
        # released results: key/solution allowed, duplicates across views idempotent
        a = body(student.post(R(done, q2['id']), json={'context': 'results', 'category': 'key'}))
        b = body(student.post(R(done, q2['id']), json={'context': 'solutions', 'category': 'solution'}))
        assert a['id'] == b['id']
        mine = body(student.get(f'{BASE_URL}/api/attempts/{done}/question-reports'))
        assert [m['question_id'] for m in mine] == [q2['id']]
        assert student.get(f'{BASE_URL}/api/attempts/{foreign}/question-reports').status_code == 404
        # staff triage
        assert student.get(f'{BASE_URL}/api/studio/question-reports').status_code == 403
        assert student.post(f'{BASE_URL}/api/studio/question-reports/{a["id"]}/review', json={'status': 'resolved'}).status_code == 403
        lst = body(owner.get(f'{BASE_URL}/api/studio/question-reports?status=open&page=1'))
        assert any(i['id'] == a['id'] for i in lst['items']) and all('user_id' not in i for i in lst['items'])
        assert owner.get(f'{BASE_URL}/api/studio/question-reports?status=bogus').status_code == 422
        assert owner.get(f'{BASE_URL}/api/studio/question-reports?page=0').status_code == 422
        rv = owner.post(f'{BASE_URL}/api/studio/question-reports/{a["id"]}/review', json={'status': 'resolved', 'note': 'TEST ok'})
        assert rv.status_code == 200 and body(rv)['status'] == 'resolved'
        assert owner.post(f'{BASE_URL}/api/studio/question-reports/nope/review', json={'status': 'resolved'}).status_code == 404
        assert owner.post(f'{BASE_URL}/api/studio/question-reports/{a["id"]}/review', json={'status': 'closed'}).status_code == 422
        mine = body(student.get(f'{BASE_URL}/api/attempts/{done}/question-reports'))
        assert mine[0]['status'] == 'resolved'
        set_after = run(db.tejas_sets.find_one({'id': sid}))
        assert set_after['questions'][1]['answer'] == 'B'
        assert run(db.tejas_manual_solves.count_documents({'set_id': sid})) == 0
