"""Regression: automatic AI solving is paused (iteration 96).
Synthetic/unit tests run in-process against real MongoDB using TEST_ fixtures (cleaned up) with the
LLM boundary, subprocess launch and dangerous side effects mocked. API tests use the public preview URL.
"""
import asyncio, json, os, re, subprocess, sys, time, uuid
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
from tejas import mock_solutions as ms, ai_solutions as ais, jobs as jb, smart_imports as si, astra
from tejas.db import db

sys.path.insert(0, str(Path(__file__).parent))
import pause_baseline_check as base

LOOP = asyncio.new_event_loop()
asyncio.set_event_loop(LOOP)  # motor binds to the loop at first use; keep one loop for the module
run = LOOP.run_until_complete
TAG = 'TEST_PAUSE_' + uuid.uuid4().hex[:8]


def _boom(*a, **k):
    raise AssertionError('LLM/subprocess boundary must never be reached while paused')


@pytest.fixture(autouse=True)
def no_llm():
    """Hard block on every billable/launch boundary for each test."""
    with mock.patch.object(astra, '_call', _boom), mock.patch.object(ms, '_call', _boom), \
         mock.patch.object(ais, 'solve_and_check', mock.AsyncMock(side_effect=AssertionError('llm'))), \
         mock.patch('subprocess.Popen', side_effect=AssertionError('spawn')) as popen:
        yield popen


async def _cleanup():
    for coll in (db.tejas_question_solutions, db.tejas_ai_solutions, db.tejas_jobs, db.tejas_sets,
                 db.tejas_attempts, db.tejas_smart_imports, db.tejas_smart_papers, db.tejas_ledgers):
        await coll.delete_many({'id': {'$regex': '^' + TAG}})


@pytest.fixture(scope='session', autouse=True)
def baseline_guard():
    before = run(base.snapshot())
    assert all(base.compare(before).values()), f'baseline mismatch BEFORE tests: {base.compare(before)}'
    yield
    run(_cleanup())
    after = run(base.snapshot())
    assert base.compare(after) == {k: True for k in base.QUERIES}, f'baseline mismatch AFTER: {base.compare(after)}'
    assert after['states'] == {'ready': 5939, 'paused': 1161}


# ---------- Unit/synthetic: gates ----------
class TestGates:
    def test_flag_and_require(self):
        assert ms.AI_SOLVING_PAUSED is True
        with pytest.raises(HTTPException) as e:
            ms.require_solving_enabled()
        assert e.value.status_code == 409

    def test_enqueue_all_noop(self):
        n = run(db.tejas_question_solutions.count_documents({}))
        assert run(ms.enqueue_all()) == 0
        assert run(db.tejas_question_solutions.count_documents({})) == n

    def test_claim_does_not_take_synthetic_queued(self):
        sid = TAG + '-claim'
        run(db.tejas_question_solutions.insert_one({'id': sid, 'state': 'queued', 'order': -1, 'tries': 0}))
        assert run(ms.claim()) is None
        d = run(db.tejas_question_solutions.find_one({'id': sid}))
        assert d['state'] == 'queued' and d['tries'] == 0

    def test_solve_direct_blocked(self):
        with pytest.raises(HTTPException) as e:
            run(ms.solve({'id': TAG + '-x', 'set_id': 'nope', 'question_id': 'nope'}))
        assert e.value.status_code == 409

    def test_worker_keeper_spawn_noop(self, no_llm):
        assert run(asyncio.wait_for(ms.worker(), 2)) is None
        assert run(asyncio.wait_for(ms.keeper(), 2)) is None
        assert ms.spawn() is None
        no_llm.assert_not_called()

    def test_legacy_ensure_process_blocked(self):
        with pytest.raises(HTTPException):
            run(ais.ensure({'id': TAG + '-q', 'type': 'mcq'}, 'u', 's'))
        with pytest.raises(HTTPException):
            run(ais.process({'id': TAG + '-j', 'payload': {'solution_id': 'x'}}))
        assert run(db.tejas_ai_solutions.count_documents({'question_id': TAG + '-q'})) == 0

    def test_jobs_enqueue_run_drain_retry(self):
        with pytest.raises(HTTPException):
            run(jb.enqueue('ai_solution', 'u', TAG, {'key': TAG + '-k'}))
        assert run(db.tejas_jobs.count_documents({'id': 'ai_solution-' + TAG + '-k'})) == 0
        jid = TAG + '-aijob'
        run(db.tejas_jobs.insert_one({'id': jid, 'kind': 'ai_solution', 'status': 'failed', 'user_id': TAG + 'u',
                                      'payload': {'solution_id': 'x'}, 'attempts': 1, 'next_run_at': 0, 'created_at': 0, 'lease_until': 0}))
        run(jb.run_job(jid))
        run(jb.drain_lane('ai_solution'))
        run(jb.drain_for(TAG))
        bg = mock.MagicMock()
        with pytest.raises(HTTPException) as e:
            run(jb.retry_job(jid, bg, {'id': TAG + 'u', 'role': 'owner'}))
        assert e.value.status_code == 409
        assert run(db.tejas_jobs.find_one({'id': jid}))['status'] == 'failed'

    def test_maintenance_skips_ai_but_runs_other_lanes(self):
        ai_id, rep_id = TAG + '-mq-ai', TAG + '-mq-report'
        for i, k in ((ai_id, 'ai_solution'), (rep_id, 'report')):
            run(db.tejas_jobs.insert_one({'id': i, 'kind': k, 'status': 'queued', 'next_run_at': 0, 'created_at': -1e9,
                                          'lease_until': 0, 'attempts': 0, 'payload': {}}))
        op = run(db.tejas_operations.find_one({'id': 'maintenance'}))
        rj = mock.AsyncMock()
        with mock.patch.object(jb, 'run_job', rj), mock.patch('tejas.attempts.finalize', mock.AsyncMock()), \
             mock.patch('tejas.attempts.ensure_grade', mock.AsyncMock()), mock.patch('tejas.content.archive_publication', mock.AsyncMock()):
            run(jb.maintenance())
        called = [c.args[0] for c in rj.call_args_list]
        assert rep_id in called and ai_id not in called
        if op:
            op.pop('_id', None)
            run(db.tejas_operations.replace_one({'id': 'maintenance'}, op))

    def test_reconcile_stops_at_solving_paused(self):
        iid = TAG + '-imp'
        run(db.tejas_smart_imports.insert_one({'id': iid, 'state': 'solving', 'pages': 1, 'processed_pages': 1, 'owner_id': 'x'}))
        with mock.patch.object(ais, 'ensure', mock.AsyncMock(side_effect=AssertionError('ensure'))):
            run(si.reconcile(iid))
        assert run(db.tejas_smart_imports.find_one({'id': iid}))['state'] == 'solving_paused'
        run(db.tejas_smart_imports.update_one({'id': iid}, {'$set': {'state': 'complete'}}))
        run(si.reconcile(iid))
        assert run(db.tejas_smart_imports.find_one({'id': iid}))['state'] == 'complete'


# ---------- Unit/synthetic: pause_pending + CLI ----------
class TestPausePending:
    def test_idempotent_and_preserving(self):
        S = db.tejas_question_solutions
        payload = {'final_answer': 'A', 'insight': 'keep'}
        for st in ('queued', 'solving', 'failed', 'ready'):
            run(S.insert_one({'id': f'{TAG}-qs-{st}', 'state': st, 'solution': payload, 'lease_until': 5, 'retry_at': 9}))
        for st in ('queued', 'verified'):
            run(db.tejas_ai_solutions.insert_one({'id': f'{TAG}-as-{st}', 'state': st, 'steps': [1]}))
        for kind, st in (('ai_solution', 'running'), ('ai_solution', 'done'), ('report', 'queued')):
            run(db.tejas_jobs.insert_one({'id': f'{TAG}-j-{kind}-{st}', 'kind': kind, 'status': st, 'next_run_at': 0, 'lease': 'L'}))
        c1 = run(ms.pause_pending())
        assert c1['tejas_question_solutions'] >= 3 and c1['tejas_ai_solutions'] >= 1 and c1['tejas_jobs'] >= 1
        for st in ('queued', 'solving', 'failed'):
            d = run(S.find_one({'id': f'{TAG}-qs-{st}'}))
            assert d['state'] == 'paused' and d['paused_from'] == st and d['solution'] == payload
            assert 'lease_until' not in d and 'retry_at' not in d and d['resume_required'] is True
        assert run(S.find_one({'id': f'{TAG}-qs-ready'}))['state'] == 'ready'
        assert run(db.tejas_ai_solutions.find_one({'id': f'{TAG}-as-verified'}))['state'] == 'verified'
        assert run(db.tejas_jobs.find_one({'id': f'{TAG}-j-ai_solution-done'}))['status'] == 'done'
        assert run(db.tejas_jobs.find_one({'id': f'{TAG}-j-report-queued'}))['status'] == 'queued'
        j = run(db.tejas_jobs.find_one({'id': f'{TAG}-j-ai_solution-running'}))
        assert j['status'] == 'paused' and j['paused_from'] == 'running'
        c2 = run(ms.pause_pending())
        assert c2 == {'tejas_question_solutions': 0, 'tejas_ai_solutions': 0, 'tejas_jobs': 0}
        assert run(S.find_one({'id': f'{TAG}-qs-failed'}))['paused_from'] == 'failed'
        # real paused docs keep their original paused_from
        assert run(S.count_documents({'state': 'paused', 'paused_from': 'failed', 'id': {'$not': re.compile('^' + TAG)}})) == 1161

    def test_cli_no_args_and_pause_pending(self):
        before = run(base.snapshot())
        with mock.patch('subprocess.Popen', _real_popen):
            r1 = subprocess.run([sys.executable, str(BACKEND / 'tools' / 'solution_worker.py')], capture_output=True, text=True, timeout=60)
            r2 = subprocess.run([sys.executable, str(BACKEND / 'tools' / 'solution_worker.py'), '--pause-pending'], capture_output=True, text=True, timeout=60)
        assert r1.returncode == 0 and 'paused' in r1.stderr.lower() and r1.stdout.strip() == ''
        assert r2.returncode == 0
        counts = json.loads(r2.stdout.strip().replace("'", '"'))
        assert set(counts) == {'tejas_question_solutions', 'tejas_ai_solutions', 'tejas_jobs'}
        after = run(base.snapshot())
        assert after['tejas_question_solutions'] == before['tejas_question_solutions']
        assert after['states'].get('ready') == before['states'].get('ready')


_real_popen = subprocess.Popen


# ---------- Unit/synthetic: lifecycle ----------
class TestLifespan:
    def test_lifespan_no_spawn_no_keeper(self, no_llm):
        import server
        fake = mock.MagicMock(); fake.create_index = mock.AsyncMock()
        tasks_before = len(asyncio.all_tasks(LOOP)) if LOOP.is_running() else 0
        created = []
        orig_ct = asyncio.create_task
        async def go():
            with mock.patch.object(server, 'indexes', mock.AsyncMock()), mock.patch.object(server.auth, 'seed_owner', mock.AsyncMock()), \
                 mock.patch.object(server, 'client', mock.MagicMock()), mock.patch.object(ms, 'solutions', fake), \
                 mock.patch.object(ms, 'keeper', mock.AsyncMock(side_effect=AssertionError('keeper'))), \
                 mock.patch.object(ms, 'spawn', side_effect=AssertionError('spawn')), \
                 mock.patch('asyncio.create_task', side_effect=lambda c, **k: created.append(c) or orig_ct(c, **k)):
                async with server.lifespan(server.app):
                    await asyncio.sleep(0.2)
        run(go())
        assert created == [] and fake.create_index.await_count == 3
        no_llm.assert_not_called()


# ---------- API/integration (public URL) ----------
def _owner_creds():
    text = (BACKEND.parent / 'memory' / 'test_credentials.md').read_text()
    email = re.search(r'Email:\s*(\S+)', text).group(1)
    pw = re.search(r'Password:\s*(\S+)', text).group(1)
    return email, pw


@pytest.fixture(scope='module')
def owner():
    s = requests.Session()
    e, p = _owner_creds()
    r = s.post(f'{BASE_URL}/api/auth/login', json={'email': e, 'password': p})
    if r.status_code != 200:
        pytest.skip(f'owner login failed {r.status_code}')
    return s


@pytest.fixture(scope='module')
def student():
    s = requests.Session()
    r = s.post(f'{BASE_URL}/api/auth/phone', json={'phone': '9900000196'})
    assert r.status_code == 200, r.text
    me = s.get(f'{BASE_URL}/api/auth/me').json()
    me = me.get('data', me)
    s.uid = (me.get('user') or me)['id']
    return s


def _data(r):
    j = r.json()
    return j.get('data', j) if isinstance(j, dict) else j


def _q(qid, n, key, agrees, sid):
    return {'id': qid, 'number': n, 'subject': 'Physics', 'type': 'mcq', 'answer': key, 'options': {'A': 'a', 'B': 'b', 'C': 'c', 'D': 'd'},
            'q_refs': [], 'ai_solution': {'solution_id': sid, 'key': key, 'agrees': agrees, 'label': 'AI generated', 'generated_at': 1.0,
            'solution': {'final_answer': 'B' if not agrees else key, 'insight': 'TEST insight', 'steps': [{'title': 's', 'work': 'w'}],
                         'key_agrees': agrees}}}


class TestApi:
    def test_progress_and_counts(self, owner):
        r = owner.get(f'{BASE_URL}/api/studio/ai-review?state=open')
        assert r.status_code == 200
        p = _data(r)['progress']
        synthetic = run(db.tejas_question_solutions.count_documents({'state': 'paused', 'id': {'$regex': '^' + TAG}}))
        assert p['generation_paused'] is True and p['ready'] == 5939 and p['paused'] == 1161 + synthetic
        r2 = owner.get(f'{BASE_URL}/api/studio/mock-books')
        assert r2.status_code == 200
        assert 'paus' in json.dumps(_data(r2)).lower() or 'generation_paused' in r2.text

    def test_auth_boundaries(self, student):
        assert requests.get(f'{BASE_URL}/api/studio/ai-review').status_code == 401
        assert student.get(f'{BASE_URL}/api/studio/ai-review').status_code == 403
        assert student.post(f'{BASE_URL}/api/studio/ai-review/x/y', json={'action': 'key_confirmed'}).status_code == 403

    def test_review_records_only(self, owner):
        set_id, qid, sid = TAG + '-set', TAG + '-q1', TAG + '-sol1'
        run(db.tejas_sets.insert_one({'id': set_id, 'title': 'TEST pause set', 'status': 'draft', 'exam': 'BITSAT', 'full_length': False,
                                      'questions': [_q(qid, 1, 'A', False, sid)]}))
        run(db.tejas_question_solutions.insert_one({'id': sid, 'state': 'paused', 'paused_from': 'failed', 'set_id': set_id, 'question_id': qid}))
        url = f'{BASE_URL}/api/studio/ai-review/{set_id}/{qid}'
        for action in ('key_confirmed', 'key_wrong', 'reopen'):
            r = owner.post(url, json={'action': action, 'note': 'TEST'})
            assert r.status_code == 200, r.text
            d = run(db.tejas_question_solutions.find_one({'id': sid}))
            assert d['state'] == 'paused' and d['paused_from'] == 'failed'
            rv = run(db.tejas_sets.find_one({'id': set_id}))['questions'][0]['ai_solution']['review']
            assert (rv or {}).get('status') == (None if action == 'reopen' else action)
        run(db.tejas_question_solutions.update_one({'id': sid}, {'$set': {'state': 'ready'}}))
        assert owner.post(url, json={'action': 'key_confirmed'}).status_code == 200
        assert run(db.tejas_question_solutions.find_one({'id': sid}))['state'] == 'ready'
        assert run(db.tejas_question_solutions.count_documents({'state': {'$in': ['queued', 'solving']}})) == 0

    def test_student_reads_saved_never_queues(self, student):
        set_id, aid = TAG + '-sset', TAG + '-att'
        qs = [_q(TAG + '-sq1', 1, 'A', True, TAG + '-ss1'), _q(TAG + '-sq2', 2, 'A', False, TAG + '-ss2'),
              {'id': TAG + '-sq3', 'number': 3, 'type': 'mcq', 'answer': 'C', 'options': {}, 'q_refs': []}]
        run(db.tejas_sets.insert_one({'id': set_id, 'title': 'TEST', 'status': 'published', 'questions': qs}))
        run(db.tejas_attempts.insert_one({'id': aid, 'user_id': student.uid, 'set_id': set_id, 'status': 'completed', 'competition_end': 0,
                                          'questions': [{k: v for k, v in q.items() if k != 'ai_solution'} for q in qs]}))
        r = student.get(f'{BASE_URL}/api/attempts/{aid}/ai-solutions')
        assert r.status_code == 200, r.text
        items = {i['question_id']: i for i in _data(r)['items']}
        assert items[TAG + '-sq1']['state'] == 'ready' and items[TAG + '-sq1']['solution']
        assert items[TAG + '-sq2']['state'] == 'under_review' and items[TAG + '-sq2']['solution'] is None
        assert items[TAG + '-sq3']['state'] == 'pending'
        r2 = student.get(f'{BASE_URL}/api/attempts/{aid}/solutions/{TAG}-sq3')
        assert r2.status_code == 200 and _data(r2)['state'] == 'not_requested'
        r3 = student.post(f'{BASE_URL}/api/attempts/{aid}/solutions/{TAG}-sq3')
        assert r3.status_code == 410
        time.sleep(2)
        assert run(db.tejas_ai_solutions.count_documents({'id': {'$not': re.compile('^' + TAG)}})) == 0
        assert run(db.tejas_jobs.count_documents({'kind': 'ai_solution', 'id': {'$not': re.compile('^' + TAG)}})) == 0
        assert run(db.tejas_question_solutions.count_documents({'state': {'$in': ['queued', 'solving']}, 'id': {'$not': re.compile('^' + TAG)}})) == 0
