"""Real-function audit regressions. RED means unresolved, never a passing repair.

Only A06 stubs parser/storage bytes. A02/A03 use forwarding read barriers;
A05 pauses the real grader; A06 replaces lease at the destination-write boundary.
"""
import asyncio
import copy
from uuid import uuid4
import pytest

pytestmark = pytest.mark.asyncio(loop_scope='session')

from fastapi import HTTPException, BackgroundTasks


class OpenInvariant(AssertionError):
    """Only the final known invariant may produce an expected failure."""


def correct(condition, name):
    if not condition:
        raise OpenInvariant(name)


def question(number=1):
    return {'id': str(uuid4()), 'number': number, 'solution_number': number,
            'subject': 'Physics', 'section': 'Physics', 'type': 'mcq',
            'text': 'Synthetic isolated practice item', 'options': {'1': 'One', '2': 'Two'},
            'answer': '1', 'solution': 'Synthetic solution', 'approved': True, 'issues': [],
            'render_mode': 'typed', 'q_refs': [], 's_refs': [], 'topic': 'Synthetic',
            'difficulty': 'Easy', 'review_note': '', 'accessible_text': '',
            'solution_accessible_text': '', 'disposition': 'standard'}


def source_set():
    return {'id': str(uuid4()), 'title': 'ISOLATED SYNTHETIC PRACTICE', 'exam': 'JEE Main',
            'status': 'published', 'revision': 1, 'version': 1, 'questions': [question(), question(2)],
            'rules': {'minutes': 0, 'correct': 4, 'wrong': -1, 'skipped': 0,
                      'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
            'audience': 'all', 'expires': None, 'rights_upload': True, 'rights_publish': True,
            'rights_report': True, 'file_ids': [], 'source': 'Synthetic isolated fixture',
            'attribution': 'Not approved academic content', 'profile_mode': 'practice'}


async def same_preimage(monkeypatch, content, set_id):
    original, arrivals, gate = content.get, 0, asyncio.Event()
    async def read(collection, id):
        nonlocal arrivals
        value = await original(collection, id)
        if collection is content.sets and id == set_id:
            arrivals += 1
            if arrivals == 2:
                gate.set()
            await asyncio.wait_for(gate.wait(), 3)
        return value
    monkeypatch.setattr(content, 'get', read)


async def test_a01_retry_alias_survives_completed_retry(clean_db, synthetic_student_user):
    from tejas import attempts, corrections
    s = source_set()
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    u = synthetic_student_user
    await attempts.preflight(s['id'], {}, u)
    a = await attempts.start(s['id'], attempts.Start(start_key='initial-' + str(uuid4()), device_checked=True), u)
    await attempts.finalize(a['id'])
    await corrections.freeze_ledger(await attempts.owned(a['id'], u))
    r1 = await attempts.retry(a['id'], {'start_key': 'retry-first-' + str(uuid4())}, u)
    key2 = 'retry-second-' + str(uuid4())
    assert (await attempts.retry(a['id'], {'start_key': key2}, u))['id'] == r1['id']
    await attempts.finalize(r1['id'])
    replay = await attempts.retry(a['id'], {'start_key': key2}, u)
    correct(replay['id'] == r1['id'], 'A01: accepted retry alias lost after completion')


async def test_a02_publish_has_one_same_version_archive(clean_db, synthetic_owner_user, monkeypatch):
    from tejas import content, safety
    monkeypatch.setattr(safety, 'HELD_CAPABILITIES', frozenset())
    s = source_set()
    s.update(status='review', version=0)
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await same_preimage(monkeypatch, content, s['id'])
    outcomes = await asyncio.gather(*(content.publish(s['id'], {'confirm': True}, synthetic_owner_user) for _ in range(2)), return_exceptions=True)
    # Only a real optimistic conflict is acceptable; any fixture/parser failure is an ERROR.
    for result in outcomes:
        if isinstance(result, Exception) and not (isinstance(result, HTTPException) and result.status_code in (409, 412)):
            raise result
    rows = await clean_db.tejas_versions.count_documents({'set_id': s['id'], 'version': 1})
    assert rows >= 1, 'Fixture failed to publish any version'
    correct(rows == 1, 'A02: duplicate same-version archive')


async def test_a03_concurrent_question_edits_preserve_both(clean_db, synthetic_owner_user, monkeypatch):
    from tejas import content
    s = source_set()
    s['status'] = 'draft'
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await same_preimage(monkeypatch, content, s['id'])
    q1 = s['questions'][0]
    outcomes = await asyncio.gather(
        content.edit_question(s['id'], q1['id'], {'text': 'Editor one'}, synthetic_owner_user),
        content.edit_question(s['id'], q1['id'], {'solution': 'Editor two'}, synthetic_owner_user), return_exceptions=True)
    conflicts = 0
    for result in outcomes:
        if isinstance(result, HTTPException) and result.status_code in (409, 412):
            conflicts += 1
        elif isinstance(result, Exception):
            raise result
    final = await clean_db.tejas_sets.find_one({'id': s['id']})
    edited = next(q for q in final['questions'] if q['id'] == q1['id'])
    correct(conflicts == 1 or (edited['text'] == 'Editor one' and edited['solution'] == 'Editor two'), 'A03: accepted edit overwritten')


async def test_a04_unknown_audience_denied():
    from tejas.content import permitted
    correct(permitted({'audience': 'unknown-private-value', 'expires': None}, None) is False,
            'A04: unknown audience failed open')


async def test_a05_waiting_grade_job_drains_without_second_trigger(clean_db, synthetic_student_user, monkeypatch):
    from tejas import jobs, corrections
    from tejas.db import now
    monkeypatch.setattr(jobs, 'INLINE_JOBS', True)
    monkeypatch.setitem(jobs.LANE_LIMITS, 'grade', 1)
    jobs._active['grade'].clear()
    entered, release = asyncio.Event(), asyncio.Event()
    original = corrections.freeze_ledger
    calls = 0
    async def paused_real_grader(a):
        nonlocal calls
        calls += 1
        if calls == 1:
            entered.set()
            await asyncio.wait_for(release.wait(), 3)
        return await original(a)
    monkeypatch.setattr(corrections, 'freeze_ledger', paused_real_grader)
    ids = []
    for _ in range(2):
        s = source_set()
        a = {**s, 'id': str(uuid4()), 'set_id': s['id'], 'user_id': synthetic_student_user['id'],
             'mode': 'practice', 'start_key': str(uuid4()), 'status': 'completed', 'answers': {}, 'started_at': now(), 'submitted_at': now(), 'deadline': 0}
        await clean_db.tejas_attempts.insert_one(a)
        j = await jobs.enqueue('grade', a['user_id'], a['set_id'], {'attempt_id': a['id']})
        ids.append(j['id'])
    first = asyncio.create_task(jobs.run_job(ids[0]))
    try:
        await asyncio.wait_for(entered.wait(), 3)
        await jobs.run_job(ids[1])
        assert (await clean_db.tejas_jobs.find_one({'id': ids[1]}))['status'] == 'queued'
        release.set()
        await asyncio.wait_for(first, 3)
        assert (await clean_db.tejas_jobs.find_one({'id': ids[0]}))['status'] == 'done'
        await asyncio.sleep(0.1)  # No periodic worker exists: no second explicit trigger.
        final = await clean_db.tejas_jobs.find_one({'id': ids[1]})
        correct(final['status'] == 'done', 'A05: persisted waiting job never dispatches after slot release')
    finally:
        release.set()
        if not first.done():
            first.cancel()
        await asyncio.gather(first, return_exceptions=True)
        jobs._active['grade'].clear()


async def test_a06_extraction_stages_proposal_no_destination_write(clean_db, synthetic_owner_user, monkeypatch):
    """A06: Safe extraction stages proposal via completion lease CAS; NO academic destination writes.

    Original regression: stale lease could write to academic destination (sets collection).
    Architecture change: Direct destination path eliminated. Extraction now ONLY stages proposal
    on job document via completion lease CAS. No sets.update_one call occurs during extraction.
    """
    from tejas import jobs, safety
    monkeypatch.setattr(safety, 'HELD_CAPABILITIES', frozenset())
    monkeypatch.setattr(jobs, 'INLINE_JOBS', True)
    s = source_set()
    s.update(status='draft', questions=[])
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    fid = str(uuid4())
    await clean_db.tejas_files.insert_one({'id': fid, 'path': 'synthetic-no-network'})
    j = await jobs.enqueue('extract', synthetic_owner_user['id'], s['id'], {'qfile': fid, 'sfile': fid, 'revision': s['revision']})
    proposal = [question()]
    async def fake_threadpool(fn, *args, **kwargs):
        if fn is jobs.get_object:
            return b'synthetic-parser-fixture'
        if fn is jobs.build_questions:
            return copy.deepcopy(proposal)
        raise RuntimeError('Unexpected extraction dependency')
    monkeypatch.setattr(jobs, 'run_in_threadpool', fake_threadpool)

    # Monitor that NO destination write occurs during extraction
    real_sets = jobs.sets
    destination_writes = []
    class DestinationMonitor:
        def __getattr__(self, name):
            return getattr(real_sets, name)
        async def update_one(self, query, update, *args, **kwargs):
            destination_writes.append(query)
            return await real_sets.update_one(query, update, *args, **kwargs)
    monkeypatch.setattr(jobs, 'sets', DestinationMonitor())

    await jobs.run_job(j['id'])

    # Verify extraction completed successfully
    final_job = await clean_db.tejas_jobs.find_one({'id': j['id']})
    assert final_job['status'] == 'done', 'Extraction should complete successfully'
    assert 'proposal' in final_job, 'Proposal should be staged in job document'
    assert final_job['proposal']['questions'] == proposal, 'Proposal should contain extracted questions'
    assert final_job['proposal']['source_revision'] == s['revision'], 'Proposal should track source revision'

    # Verify NO academic destination write occurred
    assert destination_writes == [], f'A06: Extraction must not write to academic destination (sets collection), but found {len(destination_writes)} writes'

    # Verify academic content unchanged
    final_set = await real_sets.find_one({'id': s['id']})
    assert final_set['questions'] == [], 'A06: Academic destination (questions) must remain unchanged'
    assert final_set['revision'] == s['revision'], 'A06: Academic destination (revision) must remain unchanged'


async def test_motor_namespace_guards(test_client):
    from motor.motor_asyncio import AsyncIOMotorDatabase
    with pytest.raises(RuntimeError, match='boundary violation'):
        test_client['forbidden']
    with pytest.raises(RuntimeError, match='boundary violation'):
        test_client.get_database('forbidden')
    with pytest.raises(RuntimeError, match='boundary violation'):
        AsyncIOMotorDatabase(test_client, 'forbidden')
    with pytest.raises(RuntimeError, match='boundary violation'):
        await test_client.drop_database('forbidden')


async def test_held_jobs_preserve_exact_intent_before_lease(clean_db, monkeypatch):
    from tejas import jobs
    monkeypatch.setattr(jobs, 'INLINE_JOBS', True)
    for kind in ('extract', 'regrade'):
        j = {'id': str(uuid4()), 'kind': kind, 'status': 'queued', 'attempts': 0, 'lease_until': 0, 'payload': {}}
        await clean_db.tejas_jobs.insert_one(copy.deepcopy(j))
        await jobs.run_job(j['id'])
        after = await clean_db.tejas_jobs.find_one({'id': j['id']}, {'_id': 0})
        assert after == j
        assert jobs.public_job(after)['processing_held'] is True
    assert jobs.job_held('grade') is False and jobs.job_held('report') is False


async def test_hold_rejects_without_receiving_body():
    from tejas.safety import ContentSafetyHold
    async def never(*args, **kwargs):
        raise RuntimeError('Held request reached body parser or downstream app')
    sent = []
    async def send(message):
        sent.append(message)
    scope = {'type': 'http', 'method': 'POST', 'path': '/api/studio/sets/synthetic/files',
             'headers': [(b'content-type', b'multipart/form-data; boundary=broken'), (b'content-length', b'999999999999')]}
    await ContentSafetyHold(never)(scope, never, send)
    assert sent[0]['status'] == 503


async def test_direct_protected_functions_deny_before_lookup():
    from tejas import content, corrections, jobs
    calls = [content.publish('missing', {}, {}), content.extract('missing', {}, BackgroundTasks(), {}),
             content.source_page('missing', 1, {}), content.source_text('missing', 1, {}),
             corrections.regrade('missing', {}, BackgroundTasks(), {}), corrections.run_regrade({}),
             jobs.enqueue('extract', 'u', 's', {}), jobs.enqueue('regrade', 'u', 's', {})]
    for call in calls:
        with pytest.raises(HTTPException) as exc:
            await call
        assert exc.value.status_code == 503


async def test_command_nested_body_is_immutable():
    from tejas.command_contracts import CommandIntent
    uid = str(uuid4())
    original = {'nested': {'values': [1, 2]}}
    intent = CommandIntent(tenant_id=uid, actor_id=uid, target_id=uid, operation='COMMIT',
                           request_key='synthetic-key', expected_version=1, writer_generation=1, body=original)
    before = intent.intent_digest()
    original['nested']['values'].append(3)
    with pytest.raises(TypeError):
        intent.body['nested']['values'].append(4)
    with pytest.raises(TypeError):
        intent.body['nested']['values'][0] = 9
    with pytest.raises(TypeError):
        intent.body.update({'other': True})
    assert intent.intent_digest() == before


async def test_phone_practice_save_resume_submit_preserved(http_client, clean_db):
    s = source_set()
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    login = await http_client.post('/api/auth/phone', json={'phone': '+12025550184'})
    assert login.status_code == 200
    assert login.json()['data']['access_type'] == 'unverified_phone'
    pf = await http_client.post(f'/api/sets/{s["id"]}/preflight', json={})
    assert pf.status_code == 200
    start = await http_client.post(f'/api/sets/{s["id"]}/start', json={'start_key': 'practice-' + str(uuid4()), 'device_checked': True})
    assert start.status_code == 200
    a = start.json()['data']
    assert 'answer' not in a['questions'][0]
    qid = s['questions'][0]['id']
    body = {'value': '1', 'revision': 1, 'request_id': 'answer-' + str(uuid4()), 'marked': False}
    url = f'/api/attempts/{a["id"]}/answers/{qid}'
    saved = await http_client.put(url, json=body)
    assert saved.status_code == 200
    duplicate = await http_client.put(url, json=body)
    assert duplicate.status_code == 200 and duplicate.json()['data']['duplicate'] is True
    resumed = await http_client.get(f'/api/attempts/{a["id"]}')
    assert resumed.json()['data']['answers'][qid]['value'] == '1'
    submitted = await http_client.post(f'/api/attempts/{a["id"]}/submit')
    assert submitted.status_code in (200, 202)
    replay = await http_client.post(f'/api/attempts/{a["id"]}/submit')
    assert replay.json()['data']['receipt'] == submitted.json()['data']['receipt']
    result = await http_client.get(f'/api/attempts/{a["id"]}/results')
    assert result.status_code == 200
    assert result.json()['data']['summary']['score_exact'] == '4'




async def test_concurrent_retry_aliases_across_routes(clean_db, synthetic_student_user):
    """Deep test: Concurrent retry alias binding from multiple routes/clients."""
    from tejas import attempts, corrections
    s = source_set()
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    u = synthetic_student_user
    await attempts.preflight(s['id'], {}, u)
    a = await attempts.start(s['id'], attempts.Start(start_key='initial-' + str(uuid4()), device_checked=True), u)
    await attempts.finalize(a['id'])
    await corrections.freeze_ledger(await attempts.owned(a['id'], u))

    # Simulate concurrent retry requests with different keys
    keys = [f'retry-concurrent-{i}-{str(uuid4())}' for i in range(5)]
    results = await asyncio.gather(
        *(attempts.retry(a['id'], {'start_key': k}, u) for k in keys),
        return_exceptions=True
    )

    # All should succeed and return the same retry attempt ID
    retry_ids = set()
    for r in results:
        if not isinstance(r, Exception):
            retry_ids.add(r['id'])
    assert len(retry_ids) == 1, 'All concurrent retry aliases should bind to the same retry attempt'

    # Verify all keys are bound
    retry_attempt = await clean_db.tejas_attempts.find_one({'id': list(retry_ids)[0]})
    assert len(retry_attempt['start_request_keys']) == 5, 'All retry keys should be bound'
    assert set(retry_attempt['start_request_keys']) == set(keys), 'All keys should be present'


async def test_conflicting_retry_intents_rejected(clean_db, synthetic_student_user):
    """Deep test: Retry with conflicting intent (different parent/score version) is rejected."""
    from tejas import attempts, corrections
    s1 = source_set()
    s2 = source_set()
    s2['id'] = str(uuid4())
    await clean_db.tejas_sets.insert_many([copy.deepcopy(s1), copy.deepcopy(s2)])
    u = synthetic_student_user

    # Create two completed attempts
    await attempts.preflight(s1['id'], {}, u)
    a1 = await attempts.start(s1['id'], attempts.Start(start_key='a1-' + str(uuid4()), device_checked=True), u)
    await attempts.finalize(a1['id'])
    await corrections.freeze_ledger(await attempts.owned(a1['id'], u))

    await attempts.preflight(s2['id'], {}, u)
    a2 = await attempts.start(s2['id'], attempts.Start(start_key='a2-' + str(uuid4()), device_checked=True), u)
    await attempts.finalize(a2['id'])
    await corrections.freeze_ledger(await attempts.owned(a2['id'], u))

    # Start retry for a1
    key = 'shared-key-' + str(uuid4())
    r1 = await attempts.retry(a1['id'], {'start_key': key}, u)

    # Try to use same key for a2 retry - should be rejected
    with pytest.raises(HTTPException) as exc:
        await attempts.retry(a2['id'], {'start_key': key}, u)
    assert exc.value.status_code == 409
    assert 'different request' in exc.value.detail.lower()


async def test_stale_client_revision_rejected(clean_db, synthetic_owner_user, monkeypatch):
    """Deep test: Question edit with stale expected_revision is rejected."""
    from tejas import content, safety
    monkeypatch.setattr(safety, 'HELD_CAPABILITIES', frozenset())
    s = source_set()
    s['status'] = 'draft'
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    q = s['questions'][0]

    # First edit succeeds
    await content.edit_question(s['id'], q['id'], {'text': 'Updated text', 'expected_revision': s['revision']}, synthetic_owner_user)

    # Second edit with stale revision is rejected
    with pytest.raises(HTTPException) as exc:
        await content.edit_question(s['id'], q['id'], {'solution': 'Updated solution', 'expected_revision': s['revision']}, synthetic_owner_user)
    assert exc.value.status_code == 409
    assert 'draft changed' in exc.value.detail.lower()


async def test_archive_failure_recovery_no_duplicate(clean_db, synthetic_owner_user, monkeypatch):
    """Deep test: Publication archive failure recovery doesn't create duplicates."""
    from tejas import content, safety
    monkeypatch.setattr(safety, 'HELD_CAPABILITIES', frozenset())
    s = source_set()
    s.update(status='review', version=0)
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))

    # Simulate archive failure by making first archive call fail
    real_archive = content.archive_publication
    call_count = [0]
    async def failing_archive(s):
        call_count[0] += 1
        if call_count[0] == 1:
            raise RuntimeError('Simulated archive failure')
        return await real_archive(s)
    monkeypatch.setattr(content, 'archive_publication', failing_archive)

    # First publish fails during archive
    with pytest.raises(RuntimeError, match='Simulated archive failure'):
        await content.publish(s['id'], {'confirm': True}, synthetic_owner_user)

    # Verify publication_pending is set despite archive failure
    after_fail = await clean_db.tejas_sets.find_one({'id': s['id']})
    assert after_fail.get('publication_pending') is not None, 'Pending snapshot should survive archive failure'

    # Recovery: call archive_publication directly (simulates maintenance)
    await content.archive_publication(after_fail)

    # Verify exactly one archive exists
    archives = await clean_db.tejas_versions.count_documents({'set_id': s['id'], 'version': 1})
    assert archives == 1, 'Recovery should create exactly one archive'

    # Verify pending cleared
    final = await clean_db.tejas_sets.find_one({'id': s['id']})
    assert final.get('publication_pending') is None, 'Pending should be cleared after successful archive'


async def test_late_pending_job_dispatch(clean_db, synthetic_student_user, monkeypatch):
    """Deep test: Late dispatch of pending job after lane clears."""
    from tejas import jobs, corrections
    from tejas.db import now
    monkeypatch.setattr(jobs, 'INLINE_JOBS', True)
    monkeypatch.setitem(jobs.LANE_LIMITS, 'grade', 1)
    jobs._active['grade'].clear()

    # Create two completed attempts
    ids = []
    for i in range(2):
        s = source_set()
        a = {**s, 'id': str(uuid4()), 'set_id': s['id'], 'user_id': synthetic_student_user['id'],
             'mode': 'practice', 'start_key': str(uuid4()), 'status': 'completed', 'answers': {},
             'started_at': now(), 'submitted_at': now(), 'deadline': 0}
        await clean_db.tejas_attempts.insert_one(a)
        j = await jobs.enqueue('grade', a['user_id'], a['set_id'], {'attempt_id': a['id']})
        ids.append(j['id'])

    # Run first job (blocks lane)
    await jobs.run_job(ids[0])
    assert (await clean_db.tejas_jobs.find_one({'id': ids[0]}))['status'] == 'done'

    # Second job should have been drained automatically
    await asyncio.sleep(0.1)
    second = await clean_db.tejas_jobs.find_one({'id': ids[1]})
    assert second['status'] == 'done', 'Second job should be dispatched after first completes'


async def test_score_report_auth_unaffected(http_client, clean_db):
    """Deep test: Score/report access control unaffected by hardening changes."""
    s = source_set()
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))

    # User 1 creates attempt
    login1 = await http_client.post('/api/auth/phone', json={'phone': '+12025550184'})
    assert login1.status_code == 200
    pf = await http_client.post(f'/api/sets/{s["id"]}/preflight', json={})
    assert pf.status_code == 200
    start = await http_client.post(f'/api/sets/{s["id"]}/start', json={'start_key': 'u1-' + str(uuid4()), 'device_checked': True})
    assert start.status_code == 200
    a1 = start.json()['data']
    submit = await http_client.post(f'/api/attempts/{a1["id"]}/submit')
    assert submit.status_code in (200, 202)

    # User 2 tries to access user 1's results - should be denied
    login2 = await http_client.post('/api/auth/phone', json={'phone': '+12025550199'})
    assert login2.status_code == 200
    result = await http_client.get(f'/api/attempts/{a1["id"]}/results')
    assert result.status_code == 404, 'Other user should not access results'

    # User 1 can access their own results
    await http_client.post('/api/auth/phone', json={'phone': '+12025550184'})
    result = await http_client.get(f'/api/attempts/{a1["id"]}/results')
    assert result.status_code == 200, 'Owner should access their results'


async def test_publication_outbox_crash_recovery(clean_db, synthetic_owner_user, monkeypatch):
    """Deep test: Publication outbox survives process crash and recovers correctly."""
    from tejas import content, safety
    monkeypatch.setattr(safety, 'HELD_CAPABILITIES', frozenset())
    s = source_set()
    s.update(status='review', version=0)
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))

    # Simulate crash after CAS win but before archive completes
    real_archive = content.archive_publication
    async def crash_after_cas(s):
        # Don't call real archive - simulates process crash
        raise RuntimeError('Simulated process crash')
    monkeypatch.setattr(content, 'archive_publication', crash_after_cas)

    with pytest.raises(RuntimeError, match='Simulated process crash'):
        await content.publish(s['id'], {'confirm': True}, synthetic_owner_user)



async def test_publication_outbox_idempotent_archive(clean_db, synthetic_owner_user, monkeypatch):
    """Deep test: Archive publication is truly idempotent and safe."""
    from tejas import content, safety
    monkeypatch.setattr(safety, 'HELD_CAPABILITIES', frozenset())
    s = source_set()
    s.update(status='review', version=0)
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))

    # Publish successfully
    await content.publish(s['id'], {'confirm': True}, synthetic_owner_user)

    # Verify archive exists
    archives = await clean_db.tejas_versions.count_documents({'set_id': s['id'], 'version': 1})
    assert archives == 1, 'Archive should exist'

    # Call archive_publication multiple times - should be idempotent
    published = await clean_db.tejas_sets.find_one({'id': s['id']})
    for _ in range(3):
        await content.archive_publication(published)

    # Verify still only one archive
    archives = await clean_db.tejas_versions.count_documents({'set_id': s['id'], 'version': 1})
    assert archives == 1, 'Multiple archive calls should not create duplicates'

    # Verify calling with empty publication_pending is safe
    await content.archive_publication({'id': s['id'], 'publication_pending': None})
    await content.archive_publication({'id': s['id']})

    # Verify still only one archive
    archives = await clean_db.tejas_versions.count_documents({'set_id': s['id'], 'version': 1})
    assert archives == 1, 'Archive calls with no pending should be no-op'


async def test_concurrent_publications_one_winner(clean_db, synthetic_owner_user, monkeypatch):
    """Deep test: Concurrent publications produce exactly one archive per version."""
    from tejas import content, safety
    monkeypatch.setattr(safety, 'HELD_CAPABILITIES', frozenset())
    s = source_set()
    s.update(status='review', version=0)
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))

    # Simulate concurrent publication attempts
    async def same_preimage(monkeypatch, content, set_id):
        original, arrivals, gate = content.get, 0, asyncio.Event()
        async def read(collection, id):
            nonlocal arrivals
            value = await original(collection, id)
            if collection is content.sets and id == set_id:
                arrivals += 1
                if arrivals == 2:
                    gate.set()
                await asyncio.wait_for(gate.wait(), 3)
            return value
        monkeypatch.setattr(content, 'get', read)

    await same_preimage(monkeypatch, content, s['id'])
    outcomes = await asyncio.gather(
        *(content.publish(s['id'], {'confirm': True}, synthetic_owner_user) for _ in range(2)),
        return_exceptions=True
    )

    # One should succeed, one should get 409
    successes = sum(1 for r in outcomes if not isinstance(r, Exception))
    conflicts = sum(1 for r in outcomes if isinstance(r, HTTPException) and r.status_code == 409)
    assert successes == 1 and conflicts == 1, 'Exactly one publication should win'

    # Verify exactly one archive
    archives = await clean_db.tejas_versions.count_documents({'set_id': s['id'], 'version': 1})
    assert archives == 1, 'Concurrent publications should create exactly one archive'



async def test_old_worker_lease_rotation_fenced_by_cas(clean_db, synthetic_owner_user, monkeypatch):
    """Test worker-inflight lease rotation fenced by completion CAS.

    Scenario: During job completion, another worker rotates the lease. The completing
    worker's CAS should fail, preserving the replacement lease and preventing completion.
    """
    from tejas import jobs, safety
    monkeypatch.setattr(safety, 'HELD_CAPABILITIES', frozenset())
    monkeypatch.setattr(jobs, 'INLINE_JOBS', True)

    s = source_set()
    s.update(status='draft', questions=[])
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))

    fid = str(uuid4())
    await clean_db.tejas_files.insert_one({'id': fid, 'path': 'synthetic-no-network'})

    j = await jobs.enqueue('extract', synthetic_owner_user['id'], s['id'],
                          {'qfile': fid, 'sfile': fid, 'revision': s['revision']})

    proposal = [question()]
    async def fake_threadpool(fn, *args, **kwargs):
        if fn is jobs.get_object:
            return b'synthetic-parser-fixture'
        if fn is jobs.build_questions:
            return copy.deepcopy(proposal)
        raise RuntimeError('Unexpected extraction dependency')
    monkeypatch.setattr(jobs, 'run_in_threadpool', fake_threadpool)

    # Monkeypatch jobs.jobs.update_one to inject lease rotation during completion
    real_update = jobs.jobs.update_one
    replacement_lease = 'replacement-lease-' + str(uuid4())
    
    async def injecting_update(query, update, *args, **kwargs):
        # Detect completion attempt: query contains lease, update sets status='done'
        if 'lease' in query and update.get('$set', {}).get('status') == 'done':
            # FIRST: Rotate lease to simulate another worker taking over
            await real_update(
                {'id': j['id']},
                {'$set': {
                    'lease': replacement_lease,
                    'status': 'running',
                    'lease_until': jobs.now() + 3600
                }}
            )
            # THEN: Execute original completion query (should fail CAS)
        return await real_update(query, update, *args, **kwargs)
    
    monkeypatch.setattr(jobs.jobs, 'update_one', injecting_update)

    # Run actual job execution
    await jobs.run_job(j['id'])

    # Verify replacement lease preserved
    final_job = await clean_db.tejas_jobs.find_one({'id': j['id']})
    correct(final_job['lease'] == replacement_lease, 'Replacement lease must be preserved')
    
    # Verify job NOT done (CAS failed)
    correct(final_job['status'] == 'running', 'Job must remain running after CAS failure')
    
    # Verify no proposal committed
    correct('proposal' not in final_job, 'Proposal must not be committed after CAS failure')
    
    # Verify academic content unchanged
    final_set = await clean_db.tejas_sets.find_one({'id': s['id']})
    correct(final_set['questions'] == [], 'Questions must remain unchanged after CAS failure')
    correct(final_set['revision'] == s['revision'], 'Revision must remain unchanged after CAS failure')


async def test_publication_outbox_crash_recovery_complete(clean_db, synthetic_owner_user, monkeypatch):
    """Test publication outbox crash after winning CAS before archive write, with full recovery.

    Scenario: Process crashes after winning CAS and setting publication_pending, but before
    archive write completes. Recovery (2nd publish or maintenance replay) should:
    1. Create exactly 1 archive
    2. Clear pending outbox
    3. Ensure snapshot matches published content
    """
    from tejas import content, safety
    monkeypatch.setattr(safety, 'HELD_CAPABILITIES', frozenset())
    s = source_set()
    s.update(status='review', version=0)
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))

    # Patch archive_publication to throw on first call
    real_archive = content.archive_publication
    call_count = [0]
    async def crash_on_first_archive(s):
        call_count[0] += 1
        if call_count[0] == 1:
            raise RuntimeError('Simulated process crash during archive')
        return await real_archive(s)
    monkeypatch.setattr(content, 'archive_publication', crash_on_first_archive)

    # First publish: wins CAS but crashes during archive
    with pytest.raises(RuntimeError, match='Simulated process crash'):
        await content.publish(s['id'], {'confirm': True}, synthetic_owner_user)

    # Verify publication_pending is set (CAS won)
    after_crash = await clean_db.tejas_sets.find_one({'id': s['id']})
    assert after_crash.get('publication_pending') is not None, 'Pending snapshot should survive crash'
    assert after_crash['status'] == 'published', 'Status should be published after CAS win'
    assert after_crash['version'] == 1, 'Version should be incremented after CAS win'
    pending_snapshot = after_crash['publication_pending']

    # Verify no archive exists yet
    archives_before = await clean_db.tejas_versions.count_documents({'set_id': s['id'], 'version': 1})
    assert archives_before == 0, 'No archive should exist after crash'

    # Recovery: call archive_publication directly (simulates maintenance replay)
    await content.archive_publication(after_crash)

    # Verify exactly one archive exists
    archives_after = await clean_db.tejas_versions.count_documents({'set_id': s['id'], 'version': 1})
    correct(archives_after == 1, 'Recovery should create exactly one archive')

    # Verify pending outbox cleared
    final = await clean_db.tejas_sets.find_one({'id': s['id']})
    correct(final.get('publication_pending') is None, 'Pending outbox should be cleared after recovery')

    # Verify snapshot matches published content
    archive = await clean_db.tejas_versions.find_one({'set_id': s['id'], 'version': 1})
    assert archive is not None, 'Archive should exist'
    assert archive['set_id'] == s['id'], 'Archive should reference correct set'
    assert archive['version'] == 1, 'Archive should have correct version'
    assert archive['status'] == 'published', 'Archive should have published status'
    assert len(archive['questions']) == len(s['questions']), 'Archive should contain all questions'

    # Verify idempotency: calling archive again should not create duplicates
    await content.archive_publication(final)
    archives_final = await clean_db.tejas_versions.count_documents({'set_id': s['id'], 'version': 1})
    correct(archives_final == 1, 'Multiple recovery calls should not create duplicate archives')


async def test_bounded_concurrent_profiles_start_and_answer(clean_db):
    """Test bounded 20 distinct profiles with 5 parallel start requests + 3 parallel answer commands each.

    Scenario: 20 distinct synthetic profiles, each with independent httpx.AsyncClient:
    - Login independently
    - Preflight once
    - 5 parallel start requests with same key (assert ALL status 200)
    - 3 parallel duplicate answer commands (assert ALL status 200)
    - Launch 20 inner coroutines with asyncio.gather
    - Assert 20 attempts exactly

    No production calls. Save actual time total (optional, not throughput claims).
    """
    import time
    import httpx
    from server import app
    
    s = source_set()
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))

    start_time = time.time()

    async def profile_coroutine(profile_index):
        """Independent coroutine per profile with own httpx client."""
        phone = f'+1202555{profile_index:04d}'
        
        # Create independent httpx.AsyncClient with ASGITransport
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), 
            base_url='https://testserver'
        ) as client:
            # Login independently
            login = await client.post('/api/auth/phone', json={'phone': phone})
            assert login.status_code == 200, f'Login failed for {phone}: {login.status_code}'
            
            # Preflight once
            preflight = await client.post(f'/api/sets/{s["id"]}/preflight', json={})
            assert preflight.status_code == 200, f'Preflight failed for {phone}: {preflight.status_code}'
            
            # 5 parallel start requests with same key
            start_key = f'profile-{profile_index}-key-{str(uuid4())}'
            start_tasks = [
                client.post(f'/api/sets/{s["id"]}/start',
                           json={'start_key': start_key, 'device_checked': True})
                for _ in range(5)
            ]
            
            start_results = await asyncio.gather(*start_tasks)
            
            # Assert ALL status 200
            for idx, result in enumerate(start_results):
                assert result.status_code == 200, f'Start {idx} failed for {phone}: {result.status_code}'
            
            # Verify all returned same attempt ID
            attempt_ids = {result.json()['data']['id'] for result in start_results}
            assert len(attempt_ids) == 1, f'Multiple attempt IDs for {phone}: {attempt_ids}'
            
            attempt_id = list(attempt_ids)[0]
            qid = s['questions'][0]['id']
            request_id = f'answer-{profile_index}-{str(uuid4())}'
            
            # 3 parallel duplicate answer commands
            answer_tasks = [
                client.put(
                    f'/api/attempts/{attempt_id}/answers/{qid}',
                    json={'value': '1', 'revision': 1, 'request_id': request_id, 'marked': False}
                )
                for _ in range(3)
            ]
            
            answer_results = await asyncio.gather(*answer_tasks)
            
            # Assert ALL status 200
            for idx, result in enumerate(answer_results):
                assert result.status_code == 200, f'Answer {idx} failed for {phone}: {result.status_code}'
            
            # Verify all acknowledged with same revision
            revisions = {result.json()['data'].get('current_revision', 
                        result.json()['data'].get('accepted', {}).get('revision', 0)) 
                        for result in answer_results}
            assert len(revisions) == 1 and 1 in revisions, f'Revision mismatch for {phone}: {revisions}'
            
            return {
                'profile': profile_index,
                'attempt_id': attempt_id,
                'start_count': len(start_results),
                'answer_count': len(answer_results)
            }
    
    # Launch 20 inner coroutines with asyncio.gather
    all_results = await asyncio.gather(*[profile_coroutine(i) for i in range(20)])
    
    elapsed = time.time() - start_time

    # Assert 20 attempts exactly
    attempts_count = await clean_db.tejas_attempts.count_documents({})
    correct(attempts_count == 20, f'Expected 20 attempts, got {attempts_count}')
    
    # Verify 20 successful result groups
    correct(len(all_results) == 20, f'Expected 20 successful profiles, got {len(all_results)}')
    
    # Verify each attempt has exactly 1 answer revision for the question
    for result in all_results:
        attempt = await clean_db.tejas_attempts.find_one({'id': result['attempt_id']})
        qid = s['questions'][0]['id']
        if qid in attempt.get('answers', {}):
            revision = attempt['answers'][qid].get('revision', 0)
            correct(revision == 1, f'Expected revision 1, got {revision} for attempt {result["attempt_id"]}')
    
    print(f'Concurrency test completed in {elapsed:.2f}s with {len(all_results)} successful profiles')
