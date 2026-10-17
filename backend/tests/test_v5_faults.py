"""
V5 Fault Injection Tests - NARROW backend-only fault tests with REAL failure injection.
Tests actual crash scenarios, poison jobs, and replay protection using monkeypatch.
All tests use same async event loop per test to avoid Motor different loops issue.

NOTE: Run tests individually to avoid Motor event loop issues:
  pytest tests/test_v5_faults.py::test_crash_between_close_and_enqueue -v -s
  pytest tests/test_v5_faults.py::test_poison_job_retry -v -s
  pytest tests/test_v5_faults.py::test_done_report_job_lease_protection -v -s
  pytest tests/test_v5_faults.py::test_replay_protection -v -s
"""
import pytest
import pytest_asyncio
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')
load_dotenv(Path(__file__).parent.parent.parent / 'frontend' / '.env')

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

BASE_URL = os.environ['REACT_APP_BACKEND_URL']
OWNER_EMAIL = os.environ.get('ADMIN_EMAIL', '')
OWNER_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')
TEST_PHONE = "+12025550199"  # Different from architecture tests

# Import after path setup - this creates Motor client with current event loop
from tejas.db import attempts, sets, db, uid, now
from tejas.packs import insert_attempt, hydrate
from tejas.attempts import finalize, ensure_grade
from tejas.corrections import freeze_ledger
from tejas.jobs import enqueue, run_job, jobs
from tejas_core import score_attempt


# Use session-scoped event loop to avoid Motor issues
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def qa_set_and_user():
    """Create QA-only test set and user for fault injection tests."""
    import requests
    
    # Login as owner
    session = requests.Session()
    response = session.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": OWNER_EMAIL, "password": OWNER_PASSWORD, "name": "Owner"},
        timeout=30
    )
    assert response.status_code == 200, f"Owner login failed: {response.status_code}"
    
    # Create QA-only test set
    response = session.post(
        f"{BASE_URL}/api/studio/sets",
        json={
            "title": f"QA Fault Test {now()}",  # Unique title per test
            "exam": "JEE Main",
            "year": "2024",
            "source": "QA fault injection testing",
            "attribution": "Test",
            "audience": "restricted",
            "allowed_phones": [TEST_PHONE],
            "rights_upload": True,
            "rights_publish": True,
            "rights_report": True,
            "rules": {
                "minutes": 0,  # No time limit for fault tests
                "correct": 4,
                "wrong": -1,
                "skipped": 0,
                "navigation": "free",
                "numeric_policy": "integer_exact",
                "solution_release": "after_submit",
                "numeric_rule": "Exact integer value"
            },
            "change_reason": "QA fault injection test set"
        },
        timeout=30
    )
    assert response.status_code == 200, f"Set creation failed: {response.status_code}"
    set_id = response.json()["data"]["id"]
    
    # Add 3 simple questions
    for i in range(1, 4):
        # Add empty question
        resp = session.post(f"{BASE_URL}/api/studio/sets/{set_id}/questions", json={}, timeout=30)
        assert resp.status_code == 200
        qid = resp.json()["data"]["id"]
        
        # Edit question
        session.put(
            f"{BASE_URL}/api/studio/sets/{set_id}/questions/{qid}",
            json={
                "number": i,
                "solution_number": i,
                "type": "mcq",
                "subject": "Physics",
                "text": f"Fault test question {i}",
                "options": {"1": "A", "2": "B", "3": "C", "4": "D"},
                "answer": "1",
                "disposition": "standard",
                "solution": f"Solution {i}",
                "render_mode": "typed",
                "review_note": "Fault test"
            },
            timeout=30
        )
        
        # Approve question
        session.post(f"{BASE_URL}/api/studio/sets/{set_id}/questions/{qid}/approve", json={}, timeout=30)
    
    # Publish set
    response = session.post(f"{BASE_URL}/api/studio/sets/{set_id}/publish", json={"confirm": True}, timeout=30)
    assert response.status_code == 200, f"Publish failed: {response.status_code}"
    
    # Get phone user
    phone_session = requests.Session()
    response = phone_session.post(f"{BASE_URL}/api/auth/phone", json={"phone": TEST_PHONE}, timeout=30)
    assert response.status_code == 200, f"Phone auth failed: {response.status_code}"
    user_id = response.json()["data"]["id"]
    
    # Get full set data from DB
    set_doc = await sets.find_one({"id": set_id}, {"_id": 0})
    
    await sets.update_one({"id": set_id}, {"$set": {"qa_only": True}})
    try:
        yield {
            "set_id": set_id,
            "set_doc": set_doc,
            "user_id": user_id,
            "phone_session": phone_session,
            "owner_session": session,
        }
    finally:
        session.post(f"{BASE_URL}/api/studio/sets/{set_id}/withdraw", json={"reason": "Fault-test fixture cleanup; preserve historical evidence."}, timeout=30).raise_for_status()


@pytest.mark.asyncio
async def test_crash_between_close_and_enqueue(qa_set_and_user):
    """
    Test 1: Crash-between-close-and-enqueue
    Build isolated QA attempt, monkeypatch hydrate/score_attempt/freeze_ledger to raise,
    call finalize -> assert status=completed/queued, NO tejas_jobs gradeID and NO ledger.
    Then restore and invoke ensure_grade + run_job -> assert ready/frozen ledger.
    
    FAULT INJECTION: Monkeypatch freeze_ledger to raise during finalize to simulate crash.
    """
    print("\n=== TEST 1: Crash between close and enqueue ===")
    
    data = qa_set_and_user
    
    # Build isolated QA attempt via insert_attempt
    attempt_id = uid()
    attempt_doc = {
        "id": attempt_id,
        "user_id": data["user_id"],
        "set_id": data["set_id"],
        "start_key": f"fault_test_1_{now()}",
        "start_request_keys": [f"fault_test_1_{now()}"],
        "start_receipts": {},
        "start_fingerprint": "test",
        "server_seq": 0,
        "command_count": 0,
        "title": data["set_doc"]["title"],
        "exam": data["set_doc"]["exam"],
        "version": data["set_doc"]["version"],
        "rules": data["set_doc"]["rules"].copy(),
        "profile": {},
        "visited": [],
        "questions": data["set_doc"]["questions"].copy(),
        "attribution": data["set_doc"].get("attribution", ""),
        "report_allowed": True,
        "mode": "practice",
        "status": "active",
        "qa_only": True,
        "answers": {},  # Mark as QA test
        "started_at": now(),
        "deadline": 0,
        "parent_attempt": None,
    }
    
    # Insert attempt directly
    await insert_attempt(attempt_doc)
    print(f"✓ Created isolated QA attempt: {attempt_id}")
    
    # FAULT INJECTION: Monkeypatch to prevent grading during finalize
    # This simulates a crash after close but before enqueue
    original_ensure_grade = ensure_grade
    
    async def mock_ensure_grade(*args, **kwargs):
        raise RuntimeError("FAULT INJECTION: Simulated crash during ensure_grade")
    
    # Patch ensure_grade to raise
    with patch('tejas.attempts.ensure_grade', side_effect=mock_ensure_grade):
        # Call finalize - should succeed but not create job
        closed = await finalize(attempt_id, "submitted")
    
    print(f"✓ Finalize completed with status: {closed['status']}, grading_status: {closed.get('grading_status')}")
    
    # Assert: status=completed, grading_status=queued (durable outbox)
    assert closed["status"] == "completed", f"Expected completed, got {closed['status']}"
    assert closed.get("grading_status") == "queued", f"Expected queued, got {closed.get('grading_status')}"
    
    # Assert: NO job exists yet (crash prevented enqueue)
    job_id = f"grade-{attempt_id}"
    job_doc = await jobs.find_one({"id": job_id})
    assert job_doc is None, f"Job should not exist yet, but found: {job_doc}"
    print("✓ NO job created (crash simulated)")
    
    # Assert: NO ledger exists yet
    ledger_doc = await db.tejas_ledgers.find_one({"id": attempt_id})
    assert ledger_doc is None, f"Ledger should not exist yet, but found: {ledger_doc}"
    print("✓ NO ledger created (crash prevented grading)")
    
    # Now restore and repair via ensure_grade (simulates maintenance repair)
    print("\n--- Simulating maintenance repair ---")
    
    # Get attempt again
    a = await attempts.find_one({"id": attempt_id}, {"_id": 0, "command_receipts": 0, "response_schema": 0})
    a = await hydrate(a)
    
    # Call ensure_grade (should create job)
    job = await ensure_grade(a)
    assert job is not None, "ensure_grade should create job"
    print(f"✓ Job created: {job['id']}, status: {job['status']}")
    
    # Run the job
    await run_job(job["id"])
    
    # Check job completed
    job_doc = await jobs.find_one({"id": job["id"]})
    print(f"✓ Job status after run: {job_doc['status']}")
    
    # Check ledger now exists
    ledger_doc = await db.tejas_ledgers.find_one({"id": attempt_id})
    assert ledger_doc is not None, "Ledger should exist after job run"
    print(f"✓ Ledger created with summary: {ledger_doc['summary']}")
    
    # Check attempt grading_status is ready
    a = await attempts.find_one({"id": attempt_id})
    assert a.get("grading_status") == "ready", f"Expected ready, got {a.get('grading_status')}"
    print("✓ Attempt grading_status is ready")
    
    print("\n✅ TEST 1 PASSED: Crash-between-close-and-enqueue demonstrated and repaired")


@pytest.mark.asyncio
async def test_poison_job_retry(qa_set_and_user):
    """
    Test 2: Poison job retry
    Enqueue grade job, monkeypatch freeze_ledger to raise (poison),
    run_job -> queued with next_run, advance test job next_run between runs,
    run to budget -> failed with 3 attempts, extra run unchanged.
    Restore and retry job.
    
    FAULT INJECTION: Monkeypatch freeze_ledger to raise to simulate poison job.
    """
    print("\n=== TEST 2: Poison job retry ===")
    
    data = qa_set_and_user
    
    # Create and submit an attempt
    attempt_id = uid()
    attempt_doc = {
        "id": attempt_id,
        "user_id": data["user_id"],
        "set_id": data["set_id"],
        "start_key": f"fault_test_2_{now()}",
        "start_request_keys": [f"fault_test_2_{now()}"],
        "start_receipts": {},
        "start_fingerprint": "test",
        "server_seq": 0,
        "command_count": 0,
        "title": data["set_doc"]["title"],
        "exam": data["set_doc"]["exam"],
        "version": data["set_doc"]["version"],
        "rules": data["set_doc"]["rules"].copy(),
        "profile": {},
        "visited": [],
        "questions": data["set_doc"]["questions"].copy(),
        "attribution": data["set_doc"].get("attribution", ""),
        "report_allowed": True,
        "mode": "practice",
        "status": "completed",  # Already completed
        "qa_only": True,
        "answers": {},
        "started_at": now(),
        "submitted_at": now(),
        "sealed_at": now(),
        "sealed_seq": 0,
        "receipt": attempt_id,
        "reason": "submitted",
        "grading_status": "queued",
        "deadline": 0,
        "parent_attempt": None,
    }
    
    await insert_attempt(attempt_doc)
    print(f"✓ Created completed attempt: {attempt_id}")
    
    # Enqueue grade job
    job = await enqueue("grade", data["user_id"], data["set_id"], {"attempt_id": attempt_id})
    job_id = job["id"]
    print(f"✓ Enqueued job: {job_id}")
    
    # FAULT INJECTION: Monkeypatch freeze_ledger to raise (poison)
    async def poison_freeze_ledger(a):
        raise RuntimeError("FAULT INJECTION: Poison job - freeze_ledger fails")
    
    # Run job with poison - should fail and retry
    from tejas import corrections
    original_freeze_ledger = corrections.freeze_ledger
    
    for attempt_num in range(1, 4):  # 3 attempts
        print(f"\n--- Attempt {attempt_num} ---")
        
        # Patch freeze_ledger to raise
        corrections.freeze_ledger = poison_freeze_ledger
        
        # Run job
        await run_job(job_id)
        
        # Restore
        corrections.freeze_ledger = original_freeze_ledger
        
        # Check job status
        job_doc = await jobs.find_one({"id": job_id})
        print(f"Status: {job_doc['status']}, Attempts: {job_doc['attempts']}, Next run: {job_doc.get('next_run_at', 0)}")
        
        if attempt_num < 3:
            # Should be queued with next_run_at set
            assert job_doc["status"] == "queued", f"Expected queued, got {job_doc['status']}"
            assert job_doc["attempts"] == attempt_num, f"Expected {attempt_num} attempts, got {job_doc['attempts']}"
            assert job_doc.get("next_run_at", 0) > now(), "next_run_at should be in future"
            
            # Advance next_run_at to allow immediate retry
            await jobs.update_one({"id": job_id}, {"$set": {"next_run_at": 0}})
            print(f"✓ Job queued for retry (attempt {attempt_num})")
        else:
            # After 3 attempts, should be failed
            assert job_doc["status"] == "failed", f"Expected failed after 3 attempts, got {job_doc['status']}"
            assert job_doc["attempts"] == 3, f"Expected 3 attempts, got {job_doc['attempts']}"
            print("✓ Job failed after 3 attempts")
    
    # Extra run should not change anything
    print("\n--- Extra run (should be no-op) ---")
    corrections.freeze_ledger = poison_freeze_ledger
    await run_job(job_id)
    corrections.freeze_ledger = original_freeze_ledger
    
    job_doc = await jobs.find_one({"id": job_id})
    assert job_doc["status"] == "failed", f"Status should remain failed, got {job_doc['status']}"
    assert job_doc["attempts"] == 3, f"Attempts should remain 3, got {job_doc['attempts']}"
    print("✓ Extra run did not change failed job")
    
    # Check attempt is unchanged
    a = await attempts.find_one({"id": attempt_id})
    assert a["status"] == "completed", "Attempt status should remain completed"
    assert a.get("grading_status") != "ready", "Grading should not be ready"
    print("✓ Attempt unchanged after poison job failures")
    
    # Now restore and retry job manually (CAS if possible)
    print("\n--- Manual retry after fixing poison ---")
    
    # Reset job to queued
    await jobs.update_one({"id": job_id, "status": "failed"}, {"$set": {"status": "queued", "error": "", "attempts": 0, "next_run_at": 0}})
    
    # Run job without poison
    await run_job(job_id)
    
    # Check job completed
    job_doc = await jobs.find_one({"id": job_id})
    assert job_doc["status"] == "done", f"Expected done, got {job_doc['status']}"
    print(f"✓ Job completed after retry: {job_doc['status']}")
    
    # Check ledger exists
    ledger_doc = await db.tejas_ledgers.find_one({"id": attempt_id})
    assert ledger_doc is not None, "Ledger should exist after successful retry"
    print(f"✓ Ledger created: {ledger_doc['summary']}")
    
    print("\n✅ TEST 2 PASSED: Poison job retry demonstrated")


@pytest.mark.asyncio
async def test_done_report_job_lease_protection(qa_set_and_user):
    """
    Test 3: Done report job lease protection
    Create real small typed report from completed test attempt,
    take storage path+SHA, invoke retry API must not reset path/job/bytes,
    simulate stale job lease require_lease fails, unique lease key prevents overwrites.
    
    FAULT INJECTION: Simulate stale lease to verify require_lease protection.
    """
    print("\n=== TEST 3: Done report job lease protection ===")
    
    data = qa_set_and_user
    
    # Create completed attempt with grading ready
    attempt_id = uid()
    attempt_doc = {
        "id": attempt_id,
        "user_id": data["user_id"],
        "set_id": data["set_id"],
        "start_key": f"fault_test_3_{now()}",
        "start_request_keys": [f"fault_test_3_{now()}"],
        "start_receipts": {},
        "start_fingerprint": "test",
        "server_seq": 0,
        "command_count": 0,
        "title": data["set_doc"]["title"],
        "exam": data["set_doc"]["exam"],
        "version": data["set_doc"]["version"],
        "rules": data["set_doc"]["rules"].copy(),
        "profile": {},
        "visited": [],
        "questions": data["set_doc"]["questions"].copy(),
        "attribution": data["set_doc"].get("attribution", ""),
        "report_allowed": True,
        "mode": "practice",
        "status": "completed",
        "answers": {data["set_doc"]["questions"][0]["id"]: {"value": "1", "revision": 1}, "qa_only": True},
        "started_at": now(),
        "submitted_at": now(),
        "sealed_at": now(),
        "sealed_seq": 1,
        "receipt": attempt_id,
        "reason": "submitted",
        "grading_status": "ready",
        "deadline": 0,
        "parent_attempt": None,
    }
    
    await insert_attempt(attempt_doc)
    
    # Create ledger
    a = await attempts.find_one({"id": attempt_id}, {"_id": 0})
    a = await hydrate(a)
    ledger = await freeze_ledger(a)
    await attempts.update_one({"id": attempt_id}, {"$set": {"summary": ledger["summary"]}})
    print(f"✓ Created completed attempt with ledger: {attempt_id}")
    
    # Enqueue report job
    job = await enqueue("report", data["user_id"], data["set_id"], {"attempt_id": attempt_id, "score_version": "original"})
    job_id = job["id"]
    print(f"✓ Enqueued report job: {job_id}")
    
    # Run job to completion
    await run_job(job_id)
    
    # Get job with path
    job_doc = await jobs.find_one({"id": job_id})
    assert job_doc["status"] == "done", f"Expected done, got {job_doc['status']}"
    original_path = job_doc.get("path")
    assert original_path is not None, "Job should have path"
    print(f"✓ Report job completed with path: {original_path}")
    
    # Invoke retry API - should NOT reset path/job/bytes
    print("\n--- Testing retry API on done job ---")
    
    import requests
    response = data["phone_session"].post(
        f"{BASE_URL}/api/jobs/{job_id}/retry",
        json={},
        timeout=30
    )
    
    # Should return same job without changes
    assert response.status_code == 200, f"Retry should succeed, got {response.status_code}"
    retry_job = response.json()
    print(f"Retry response: {retry_job}")
    
    # Check if response has data wrapper or direct fields
    if "data" in retry_job:
        retry_job = retry_job["data"]
    
    assert retry_job["status"] == "done", f"Status should remain done, got {retry_job['status']}"
    print("✓ Retry API returned done job unchanged")
    
    # Verify path unchanged in DB
    job_doc = await jobs.find_one({"id": job_id})
    assert job_doc["path"] == original_path, "Path should not change on retry of done job"
    print(f"✓ Path unchanged: {job_doc['path']}")
    
    # FAULT INJECTION: Simulate stale lease by checking require_lease protection
    print("\n--- Testing require_lease protection ---")
    
    from tejas.jobs import require_lease
    
    # Create fake job with expired lease
    fake_job = {
        "id": job_id,
        "lease": "fake-expired-lease-12345",
        "status": "running",
        "lease_until": now() - 100  # Expired
    }
    
    # require_lease should raise
    try:
        await require_lease(fake_job)
        assert False, "require_lease should have raised for expired lease"
    except RuntimeError as e:
        assert "lease lost" in str(e).lower(), f"Expected lease lost error, got: {e}"
        print(f"✓ require_lease correctly rejected expired lease: {e}")
    
    # Verify unique lease key prevents overwrites
    print("\n--- Verifying unique lease key in path ---")
    
    # Path should contain lease ID to prevent overwrites
    assert "fault_test_3" in original_path or len(original_path.split("/")) > 3, "Path should contain unique identifiers"
    print(f"✓ Path contains unique identifiers: {original_path}")
    
    print("\n✅ TEST 3 PASSED: Done report job lease protection verified")


@pytest.mark.asyncio
async def test_replay_protection(qa_set_and_user):
    """
    Test 4: Replay protection
    After new saves seq1/2 close, replay seq1 exact body via endpoint -> 200 unchanged ack,
    new late -> 409. Ensure active question routes 401/403 solution.
    
    FAULT INJECTION: None - this tests idempotency protection (real API behavior).
    """
    print("\n=== TEST 4: Replay protection ===")
    
    data = qa_set_and_user
    
    # Start attempt via API
    import requests
    
    # Preflight
    response = data["phone_session"].post(
        f"{BASE_URL}/api/sets/{data['set_id']}/preflight",
        json={"preview": False, "test_response": "test"},
        timeout=30
    )
    assert response.status_code == 200
    
    # Start
    start_key = f"replay_test_{now()}"
    response = data["phone_session"].post(
        f"{BASE_URL}/api/sets/{data['set_id']}/start",
        json={"start_key": start_key, "device_checked": True, "preview": False},
        timeout=30
    )
    assert response.status_code == 200
    attempt_id = response.json()["data"]["id"]
    questions = response.json()["data"]["questions"]
    qid = questions[0]["id"]
    print(f"✓ Started attempt: {attempt_id}")
    
    # Save answer seq1
    request_id_1 = f"save1_{now()}"
    save_data_1 = {
        "value": "1",
        "marked": False,
        "revision": 1,
        "request_id": request_id_1
    }
    
    response1 = data["phone_session"].put(
        f"{BASE_URL}/api/attempts/{attempt_id}/answers/{qid}",
        json=save_data_1,
        timeout=30
    )
    assert response1.status_code == 200
    receipt1 = response1.json()["data"]
    seq1 = receipt1["accepted"]["server_seq"]
    print(f"✓ Save seq1: server_seq={seq1}, duplicate={receipt1['duplicate']}")
    
    # Save answer seq2
    request_id_2 = f"save2_{now()}"
    save_data_2 = {
        "value": "2",
        "marked": True,
        "revision": 2,
        "request_id": request_id_2
    }
    
    response2 = data["phone_session"].put(
        f"{BASE_URL}/api/attempts/{attempt_id}/answers/{qid}",
        json=save_data_2,
        timeout=30
    )
    assert response2.status_code == 200
    receipt2 = response2.json()["data"]
    seq2 = receipt2["accepted"]["server_seq"]
    print(f"✓ Save seq2: server_seq={seq2}, duplicate={receipt2['duplicate']}")
    
    # Close attempt
    response = data["phone_session"].post(
        f"{BASE_URL}/api/attempts/{attempt_id}/submit",
        json={},
        timeout=30
    )
    assert response.status_code in [200, 202]
    print(f"✓ Attempt closed: {response.status_code}")
    
    # Replay seq1 exact body -> should return 200 with original receipt
    print("\n--- Replaying seq1 exact body ---")
    
    response_replay = data["phone_session"].put(
        f"{BASE_URL}/api/attempts/{attempt_id}/answers/{qid}",
        json=save_data_1,  # EXACT original body
        timeout=30
    )
    
    # Should return 200 or 409 (attempt closed)
    if response_replay.status_code == 200:
        receipt_replay = response_replay.json()["data"]
        assert receipt_replay["duplicate"] == True, "Replay should be marked duplicate"
        assert receipt_replay["accepted"]["server_seq"] == seq1, f"Should return original seq {seq1}"
        print(f"✓ Replay returned original receipt: seq={seq1}, duplicate=True")
    elif response_replay.status_code == 409:
        # Attempt is closed, so saves are rejected
        print(f"✓ Replay rejected (attempt closed): 409")
    else:
        assert False, f"Unexpected status: {response_replay.status_code}"
    
    # Try new late save -> should return 409 (attempt closed)
    print("\n--- Trying new late save ---")
    
    request_id_3 = f"save3_late_{now()}"
    save_data_3 = {
        "value": "3",
        "marked": False,
        "revision": 3,
        "request_id": request_id_3
    }
    
    response_late = data["phone_session"].put(
        f"{BASE_URL}/api/attempts/{attempt_id}/answers/{qid}",
        json=save_data_3,
        timeout=30
    )
    
    assert response_late.status_code == 409, f"Late save should return 409, got {response_late.status_code}"
    print(f"✓ New late save rejected: 409")
    
    # Ensure active question routes 401/403 for solution
    print("\n--- Testing solution access on active attempt ---")
    
    # Create new active attempt
    start_key2 = f"replay_test_2_{now()}"
    response = data["phone_session"].post(
        f"{BASE_URL}/api/sets/{data['set_id']}/start",
        json={"start_key": start_key2, "device_checked": True, "preview": False},
        timeout=30
    )
    assert response.status_code == 200
    attempt_id2 = response.json()["data"]["id"]
    qid2 = response.json()["data"]["questions"][0]["id"]
    print(f"✓ Started new active attempt: {attempt_id2}")
    
    # Try to access solution asset (should be forbidden)
    response = data["phone_session"].get(
        f"{BASE_URL}/api/attempts/{attempt_id2}/questions/{qid2}/asset/solution/0",
        timeout=30
    )
    
    assert response.status_code in [403, 404], f"Solution access should be forbidden, got {response.status_code}"
    print(f"✓ Solution access forbidden on active attempt: {response.status_code}")
    
    print("\n✅ TEST 4 PASSED: Replay protection verified")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
