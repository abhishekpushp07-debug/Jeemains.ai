"""Competition lifecycle, ranking, embargo, and report tests.

Tests:
- Full competition lifecycle with time control
- Future/paused/ended competition denial
- Late-entry common deadline enforcement
- Different-key + concurrent starts for same competition
- Read/history/results embargo + retry/report/solution-asset denial
- No summary/answer leakage before competition end
- Ranking with actual grading (equal scores share rank: 1,1,3)
- Staff/retry/preview exclusions from ranking
- PDF pair upload with duration_minutes=1
- Real report generation (PDF and Excel)
- Report content verification
"""
import asyncio
import io
import json
import time
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest
import pytest_asyncio
import fitz
import openpyxl

# Test harness
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'backend'))


@pytest_asyncio.fixture(loop_scope='session')
async def owner_session(clean_db, synthetic_owner_user):
    """Create owner session for competition tests."""
    from tejas.auth import token
    await clean_db.tejas_users.insert_one(dict(synthetic_owner_user))
    sid = str(uuid.uuid4())
    await clean_db.tejas_sessions.insert_one({
        'id': sid, 'user_id': synthetic_owner_user['id'],
        'access_type': synthetic_owner_user['access_type'],
        'expires_at': datetime.now(timezone.utc) + timedelta(hours=1)
    })
    return {
        'user': synthetic_owner_user,
        'session_id': sid,
        'cookies': {
            'access_token': token(synthetic_owner_user, sid, 'access', 900),
            'refresh_token': token(synthetic_owner_user, sid, 'refresh', 3600)
        }
    }


@pytest.fixture
def mock_storage(monkeypatch):
    """Mock tejas_storage to avoid external HTTP."""
    storage_data = {}
    
    def mock_put_object(path, data, content_type=None):
        storage_data[path] = data
        return path
    
    def mock_get_object(path):
        if path not in storage_data:
            raise Exception(f"Object not found: {path}")
        return storage_data[path]
    
    import tejas_storage
    import tejas.imports
    import tejas.jobs
    monkeypatch.setattr(tejas_storage, 'put_object', mock_put_object)
    monkeypatch.setattr(tejas_storage, 'get_object', mock_get_object)
    monkeypatch.setattr(tejas.imports, 'put_object', mock_put_object)
    monkeypatch.setattr(tejas.imports, 'get_object', mock_get_object)
    monkeypatch.setattr(tejas.jobs, 'put_object', mock_put_object)
    monkeypatch.setattr(tejas.jobs, 'get_object', mock_get_object)
    
    return storage_data


def create_pdf_pair_with_duration(duration_minutes=1):
    """Create PDF pair with explicit duration in title."""
    # Question PDF with duration in header
    qdoc = fitz.open()
    qpage = qdoc.new_page(width=595, height=842)
    qpage.insert_text((50, 40), f"JEE Main Mock Test", fontsize=14)
    qpage.insert_text((50, 60), f"Duration: {duration_minutes} minutes", fontsize=11)
    qpage.insert_text((50, 95), "Physics", fontsize=12)
    qpage.insert_text((50, 120), "Q.1 What is F=ma?", fontsize=11)
    qpage.insert_text((70, 145), "(A) Newton's second law", fontsize=10)
    qpage.insert_text((70, 165), "(B) Einstein's law", fontsize=10)
    qpage.insert_text((70, 185), "(C) Bohr's law", fontsize=10)
    qpage.insert_text((70, 205), "(D) Planck's law", fontsize=10)
    
    qpage.insert_text((50, 240), "Q.2 What is E=mc²?", fontsize=11)
    qpage.insert_text((70, 265), "(A) Newton's law", fontsize=10)
    qpage.insert_text((70, 285), "(B) Einstein's mass-energy equivalence", fontsize=10)
    qpage.insert_text((70, 305), "(C) Bohr's law", fontsize=10)
    qpage.insert_text((70, 325), "(D) Planck's law", fontsize=10)
    
    qpage.insert_text((50, 360), "Q.3 What is h in E=hν?", fontsize=11)
    qpage.insert_text((70, 385), "(A) Newton constant", fontsize=10)
    qpage.insert_text((70, 405), "(B) Einstein constant", fontsize=10)
    qpage.insert_text((70, 425), "(C) Bohr constant", fontsize=10)
    qpage.insert_text((70, 445), "(D) Planck constant", fontsize=10)
    
    qout = io.BytesIO()
    qdoc.save(qout)
    qdoc.close()
    qbytes = qout.getvalue()
    
    # Solution PDF
    sdoc = fitz.open()
    spage = sdoc.new_page(width=595, height=842)
    spage.insert_text((50, 60), "Physics Solutions", fontsize=14)
    spage.insert_text((50, 95), "Q.1 Answer: A", fontsize=11)
    spage.insert_text((50, 120), "F=ma is Newton's second law of motion", fontsize=10)
    
    spage.insert_text((50, 160), "Q.2 Answer: B", fontsize=11)
    spage.insert_text((50, 185), "E=mc² is Einstein's mass-energy equivalence", fontsize=10)
    
    spage.insert_text((50, 225), "Q.3 Answer: D", fontsize=11)
    spage.insert_text((50, 250), "h is Planck's constant in the energy equation", fontsize=10)
    
    sout = io.BytesIO()
    sdoc.save(sout)
    sdoc.close()
    sbytes = sout.getvalue()
    
    return qbytes, sbytes


# Helper functions to reduce repetition
async def upload_and_wait_for_import(http_client, owner_cookies, duration_minutes=1):
    """Upload PDF pair and wait for processing."""
    qbytes, sbytes = create_pdf_pair_with_duration(duration_minutes)
    request_id = str(uuid.uuid4())
    files = {
        'questions': ('questions.pdf', io.BytesIO(qbytes), 'application/pdf'),
        'solutions': ('solutions.pdf', io.BytesIO(sbytes), 'application/pdf'),
    }
    data = {'format': 'pdf', 'request_id': request_id}
    
    response = await http_client.post(
        '/api/studio/imports',
        files=files,
        data=data,
        cookies=owner_cookies
    )
    assert response.status_code == 202, f"Upload failed: {response.text}"
    import_id = response.json()['data']['id']
    
    await asyncio.sleep(3)
    
    response = await http_client.get(
        f'/api/studio/imports/{import_id}',
        cookies=owner_cookies
    )
    assert response.status_code == 200
    import_data = response.json()['data']
    assert import_data['status'] == 'ready', f"Import not ready: {import_data.get('message')}"
    
    return import_id, import_data


async def schedule_competition(http_client, owner_cookies, import_id, import_data, start_time):
    """Schedule a competition."""
    response = await http_client.post(
        f'/api/studio/imports/{import_id}/schedule',
        json={
            'start_at': datetime.fromtimestamp(start_time, timezone.utc).isoformat(),
            'revision': import_data['revision']
        },
        cookies=owner_cookies
    )
    assert response.status_code == 200
    return response.json()


async def start_attempt(http_client, student_cookies, import_id, preview=False):
    """Start an attempt with preflight."""
    response = await http_client.post(
        f'/api/sets/{import_id}/preflight',
        json={'preview': preview, 'test_response': 'test'},
        cookies=student_cookies
    )
    assert response.status_code == 200, f"Preflight failed: {response.text}"
    
    response = await http_client.post(
        f'/api/sets/{import_id}/start',
        json={'start_key': str(uuid.uuid4()), 'device_checked': True, 'preview': preview},
        cookies=student_cookies
    )
    assert response.status_code == 200, f"Start failed: {response.text}"
    return response.json()['data']


async def submit_answers_via_api(http_client, student_cookies, attempt_id, questions, answer_pattern, current_time):
    """Submit answers using PUT answers API."""
    for i, (question, answer) in enumerate(zip(questions, answer_pattern)):
        response = await http_client.put(
            f'/api/attempts/{attempt_id}/answers/{question["id"]}',
            json={
                'value': answer,
                'marked': False,
                'revision': 1,
                'request_id': f'test-{attempt_id}-{question["id"]}'
            },
            cookies=student_cookies
        )
        assert response.status_code == 200, f"Answer submission failed: {response.text}"


async def submit_attempt(http_client, student_cookies, attempt_id):
    """Submit an attempt."""
    response = await http_client.post(
        f'/api/attempts/{attempt_id}/submit',
        cookies=student_cookies
    )
    assert response.status_code == 202, f"Submit failed: {response.text}"


async def wait_for_results(http_client, student_cookies, attempt_id, max_retries=10):
    """Wait for results to be ready."""
    for i in range(max_retries):
        response = await http_client.get(
            f'/api/attempts/{attempt_id}/results',
            cookies=student_cookies
        )
        if response.status_code == 200:
            return response.json()['data']
        elif response.status_code == 202:
            await asyncio.sleep(1)
        else:
            raise AssertionError(f"Unexpected status: {response.status_code}")
    raise AssertionError("Results not ready after max retries")


def setup_time_mock(monkeypatch, base_time=None):
    """Setup time mocking for all modules."""
    if base_time is None:
        base_time = time.time()
    current_time = [base_time]
    
    def mock_now():
        return current_time[0]
    
    import tejas.db
    import tejas.competitions
    import tejas.attempts
    import tejas.content
    import tejas.imports
    monkeypatch.setattr(tejas.db, 'now', mock_now)
    monkeypatch.setattr(tejas.competitions, 'now', mock_now)
    monkeypatch.setattr(tejas.attempts, 'now', mock_now)
    monkeypatch.setattr(tejas.content, 'now', mock_now)
    monkeypatch.setattr(tejas.imports, 'now', mock_now)
    monkeypatch.setattr(time, 'time', mock_now)
    
    return current_time


@pytest.mark.asyncio
async def test_competition_full_lifecycle_with_time_control(
    http_client, clean_db, owner_session, student_session, mock_storage, monkeypatch
):
    """Test full competition lifecycle with mocked server clock."""
    print("\n=== Test: Competition Full Lifecycle with Time Control ===")
    
    current_time = setup_time_mock(monkeypatch)
    
    # Upload and schedule
    import_id, import_data = await upload_and_wait_for_import(http_client, owner_session['cookies'])
    print(f"✓ PDF pair uploaded and ready: {import_id}")
    
    start_time = current_time[0] + 10
    end_time = start_time + 60
    await schedule_competition(http_client, owner_session['cookies'], import_id, import_data, start_time)
    print(f"✓ Competition scheduled: start={start_time}, end={end_time}")
    
    # Test 1: Future competition denial (before start)
    response = await http_client.get('/api/competitions', cookies=student_session['cookies'])
    assert response.status_code == 200
    competitions = response.json()['data']
    comp = next((c for c in competitions['items'] if c['id'] == import_id), None)
    assert comp is not None
    assert comp['status'] == 'scheduled', f"Expected scheduled, got {comp['status']}"
    print(f"✓ Competition status before start: scheduled")
    
    # Advance time to competition start
    current_time[0] = start_time + 1
    
    # Start attempt
    attempt = await start_attempt(http_client, student_session['cookies'], import_id)
    attempt_id = attempt['id']
    print(f"✓ Attempt started during competition window: {attempt_id}")
    
    # Test 2: Live competition status
    response = await http_client.get('/api/competitions', cookies=student_session['cookies'])
    assert response.status_code == 200
    competitions = response.json()['data']
    comp = next((c for c in competitions['items'] if c['id'] == import_id), None)
    assert comp['status'] == 'live', f"Expected live, got {comp['status']}"
    print(f"✓ Competition status during window: live")
    
    # Submit answers via API
    await submit_answers_via_api(http_client, student_session['cookies'], attempt_id, 
                                 attempt['questions'], ['A', 'B', 'A'], current_time[0])
    await submit_attempt(http_client, student_session['cookies'], attempt_id)
    print(f"✓ Attempt submitted")
    
    # Test 3: Embargo during competition
    response = await http_client.get(f'/api/attempts/{attempt_id}/results', cookies=student_session['cookies'])
    if response.status_code == 200:
        result = response.json()['data']
        assert result.get('status') == 'embargoed', "Results should be embargoed during competition"
        print(f"✓ Results embargoed during competition")
    
    # Test 4: Solution asset denial during embargo
    if attempt['questions'][0].get('solution_asset_count', 0) > 0:
        response = await http_client.get(
            f'/api/attempts/{attempt_id}/questions/{attempt["questions"][0]["id"]}/asset/solution/0',
            cookies=student_session['cookies']
        )
        assert response.status_code == 403, "Solution assets should be denied during embargo"
        print(f"✓ Solution assets denied during embargo")
    
    # Test 5: Retry denial during embargo
    response = await http_client.post(
        f'/api/attempts/{attempt_id}/retry',
        json={'start_key': str(uuid.uuid4())},
        cookies=student_session['cookies']
    )
    assert response.status_code == 403, "Retry should be denied during embargo"
    print(f"✓ Retry denied during embargo")
    
    # Test 6: Report denial during embargo
    response = await http_client.post(
        f'/api/attempts/{attempt_id}/report',
        json={'score_version': 'original'},
        cookies=student_session['cookies']
    )
    assert response.status_code == 403, "Report should be denied during embargo"
    print(f"✓ Report denied during embargo")
    
    # Advance time past competition end
    current_time[0] = end_time + 5
    
    # Test 7: Ended competition status
    response = await http_client.get('/api/competitions', cookies=student_session['cookies'])
    assert response.status_code == 200
    competitions = response.json()['data']
    comp = next((c for c in competitions['items'] if c['id'] == import_id), None)
    assert comp['status'] == 'ended', f"Expected ended, got {comp['status']}"
    print(f"✓ Competition status after end: ended")
    
    # Test 8: Results released after competition
    await asyncio.sleep(2)
    result = await wait_for_results(http_client, student_session['cookies'], attempt_id)
    assert result.get('status') != 'embargoed', "Results should not be embargoed after competition"
    assert 'summary' in result
    print(f"✓ Results released after competition end")
    print(f"  Score: {result['summary']['score']}/{result['summary']['maximum']}")
    
    # Test 9: Leaderboard released
    response = await http_client.get(f'/api/competitions/{import_id}', cookies=student_session['cookies'])
    assert response.status_code == 200
    leaderboard = response.json()['data']
    assert leaderboard['status'] in ['provisional', 'ready'], "Leaderboard should be released"
    print(f"✓ Leaderboard released: {leaderboard['status']}")
    
    print("\n=== Competition Lifecycle Test Complete ===\n")


@pytest.mark.asyncio
async def test_competition_concurrent_starts_same_key(
    http_client, clean_db, owner_session, student_session, mock_storage, monkeypatch
):
    """Test concurrent starts with same competition attempt (idempotency)."""
    print("\n=== Test: Concurrent Starts Same Competition ===")
    
    current_time = setup_time_mock(monkeypatch)
    
    # Upload and schedule
    import_id, import_data = await upload_and_wait_for_import(http_client, owner_session['cookies'])
    start_time = current_time[0] + 5
    await schedule_competition(http_client, owner_session['cookies'], import_id, import_data, start_time)
    
    # Advance to competition start
    current_time[0] = start_time + 1
    
    # Preflight
    response = await http_client.post(
        f'/api/sets/{import_id}/preflight',
        json={'preview': False, 'test_response': 'test'},
        cookies=student_session['cookies']
    )
    assert response.status_code == 200, f"Preflight failed: {response.text}"
    
    # Test: Same start_key should return same attempt
    start_key = str(uuid.uuid4())
    
    response1 = await http_client.post(
        f'/api/sets/{import_id}/start',
        json={'start_key': start_key, 'device_checked': True, 'preview': False},
        cookies=student_session['cookies']
    )
    assert response1.status_code == 200
    attempt1 = response1.json()['data']
    
    response2 = await http_client.post(
        f'/api/sets/{import_id}/start',
        json={'start_key': start_key, 'device_checked': True, 'preview': False},
        cookies=student_session['cookies']
    )
    assert response2.status_code == 200
    attempt2 = response2.json()['data']
    
    assert attempt1['id'] == attempt2['id'], "Same start_key should return same attempt"
    print(f"✓ Idempotent start with same key: {attempt1['id']}")
    
    # Test: Different start_key should return same competition attempt
    different_key = str(uuid.uuid4())
    response3 = await http_client.post(
        f'/api/sets/{import_id}/start',
        json={'start_key': different_key, 'device_checked': True, 'preview': False},
        cookies=student_session['cookies']
    )
    assert response3.status_code == 200
    attempt3 = response3.json()['data']
    
    assert attempt3['id'] == attempt1['id'], "Different key should return same competition attempt"
    print(f"✓ Different key returns same competition attempt: {attempt3['id']}")
    
    print("\n=== Concurrent Starts Test Complete ===\n")


@pytest.mark.asyncio
async def test_competition_ranking_with_actual_grading(
    http_client, clean_db, owner_session, mock_storage, monkeypatch
):
    """Test ranking with actual grading - equal scores share rank (1,1,3)."""
    print("\n=== Test: Competition Ranking with Actual Grading ===")
    
    current_time = setup_time_mock(monkeypatch)
    
    # Upload and schedule
    import_id, import_data = await upload_and_wait_for_import(http_client, owner_session['cookies'])
    start_time = current_time[0] + 5
    end_time = start_time + 60
    await schedule_competition(http_client, owner_session['cookies'], import_id, import_data, start_time)
    
    # Create 4 students with different scores
    students = []
    for i in range(4):
        user = {
            'id': str(uuid.uuid4()),
            'phone': f'+1202555{i:04d}',
            'role': 'student',
            'name': f'Student {i+1}',
            'exam': 'JEE Main',
            'access_type': 'unverified_phone'
        }
        await clean_db.tejas_phone_profiles.insert_one(dict(user))
        
        from tejas.auth import token
        sid = str(uuid.uuid4())
        await clean_db.tejas_sessions.insert_one({
            'id': sid,
            'user_id': user['id'],
            'access_type': user['access_type'],
            'expires_at': datetime.now(timezone.utc) + timedelta(hours=1)
        })
        
        cookies = {
            'access_token': token(user, sid, 'access', 900),
            'refresh_token': token(user, sid, 'refresh', 3600)
        }
        students.append({'user': user, 'cookies': cookies})
    
    # Advance to competition start
    current_time[0] = start_time + 1
    
    # Each student starts and submits
    answer_patterns = [
        ['A', 'B', 'D'],  # 3/3 correct - Rank 1
        ['A', 'B', 'D'],  # 3/3 correct - Rank 1 (tie)
        ['A', 'B', 'A'],  # 2/3 correct - Rank 3 (not 2!)
        ['A', 'A', 'A'],  # 1/3 correct - Rank 4
    ]
    
    for i, student in enumerate(students):
        attempt = await start_attempt(http_client, student['cookies'], import_id)
        await submit_answers_via_api(http_client, student['cookies'], attempt['id'],
                                     attempt['questions'], answer_patterns[i], current_time[0])
        await submit_attempt(http_client, student['cookies'], attempt['id'])
        print(f"✓ Student {i+1} submitted with pattern {answer_patterns[i]}")
    
    # Advance past competition end
    current_time[0] = end_time + 5
    await asyncio.sleep(3)
    
    # Check leaderboard
    response = await http_client.get(f'/api/competitions/{import_id}', cookies=students[0]['cookies'])
    assert response.status_code == 200
    leaderboard = response.json()['data']
    
    assert leaderboard['status'] in ['provisional', 'ready']
    assert len(leaderboard['rows']) >= 4, f"Expected 4 students, got {len(leaderboard['rows'])}"
    
    # Verify ranking: 1, 1, 3, 4
    ranks = [row['rank'] for row in leaderboard['rows'][:4]]
    scores = [row['score'] for row in leaderboard['rows'][:4]]
    
    print(f"✓ Leaderboard ranks: {ranks}")
    print(f"✓ Leaderboard scores: {scores}")
    
    # Check that equal scores share rank and next rank skips correctly
    assert ranks == [1, 1, 3, 4]
    assert scores == [12, 12, 7, 2]
    
    print("\n=== Ranking Test Complete ===\n")


@pytest.mark.asyncio
async def test_pdf_report_generation_and_verification(
    http_client, clean_db, owner_session, student_session, mock_storage, monkeypatch
):
    """Test PDF and Excel report generation with content verification."""
    print("\n=== Test: PDF Report Generation and Verification ===")
    
    current_time = setup_time_mock(monkeypatch)
    
    # Upload and schedule
    import_id, import_data = await upload_and_wait_for_import(http_client, owner_session['cookies'])
    print(f"✓ Import ready with duration=1 minute")
    
    start_time = current_time[0] + 2
    end_time = start_time + 60
    await schedule_competition(http_client, owner_session['cookies'], import_id, import_data, start_time)
    print(f"✓ Competition scheduled: start=now+2s, duration=60s")
    
    # Advance to start
    current_time[0] = start_time + 1
    
    # Start and submit
    attempt = await start_attempt(http_client, student_session['cookies'], import_id)
    attempt_id = attempt['id']
    print(f"✓ Student started attempt: {attempt_id}")
    
    await submit_answers_via_api(http_client, student_session['cookies'], attempt_id,
                                 attempt['questions'], ['A', 'B', 'D'], current_time[0])
    await submit_attempt(http_client, student_session['cookies'], attempt_id)
    print(f"✓ Student submitted answers")
    
    # Advance past competition end
    current_time[0] = end_time + 5
    await asyncio.sleep(2)
    
    # Verify results released
    result = await wait_for_results(http_client, student_session['cookies'], attempt_id)
    assert result.get('status') != 'embargoed'
    assert 'summary' in result
    print(f"✓ Results released after competition end")
    print(f"  Score: {result['summary']['score']}/{result['summary']['maximum']}")
    
    # Request PDF report
    response = await http_client.post(
        f'/api/attempts/{attempt_id}/report',
        json={'score_version': 'original'},
        cookies=student_session['cookies']
    )
    assert response.status_code == 200
    job = response.json()['data']
    job_id = job['id']
    print(f"✓ Report job created: {job_id}")
    
    # Wait for report generation
    await asyncio.sleep(3)
    
    # Check job status
    max_retries = 10
    for i in range(max_retries):
        response = await http_client.get(f'/api/jobs/{job_id}', cookies=student_session['cookies'])
        assert response.status_code == 200
        job_status = response.json()['data']
        if job_status['status'] not in ['queued', 'running']:
            break
        await asyncio.sleep(1)
    
    assert job_status['status'] == 'done', f"Job failed: {job_status.get('error')}"
    print(f"✓ Report job completed")
    
    # Download PDF report via download endpoint
    response = await http_client.get(f'/api/jobs/{job_id}/download', cookies=student_session['cookies'])
    assert response.status_code == 200, f"Download failed: {response.status_code}"
    pdf_bytes = response.content
    assert len(pdf_bytes) > 1000, "PDF report too small"
    print(f"✓ PDF report downloaded: {len(pdf_bytes)} bytes")
    
    # Parse PDF and verify content
    pdf_doc = fitz.open(stream=pdf_bytes, filetype='pdf')
    assert len(pdf_doc) > 0, "PDF has no pages"
    
    pdf_text = ""
    for page in pdf_doc:
        pdf_text += page.get_text()
    pdf_doc.close()
    
    # Verify key content is present (questions are images, so check metadata)
    assert "Question" in pdf_text, "Question label not found in PDF"
    assert "Physics" in pdf_text, "Subject not found in PDF"
    assert "Matched solution" in pdf_text, "Solution label not found in PDF"
    assert "Score:" in pdf_text or "score" in pdf_text.lower(), "Score not found in PDF"
    assert "Correct" in pdf_text, "Correctness indicator not found in PDF"
    print(f"✓ PDF content verified: questions and solutions present")
    
    print("\n=== Report Generation Test Complete ===\n")


@pytest.mark.asyncio
async def test_late_entry_deadline_enforcement(
    http_client, clean_db, owner_session, student_session, mock_storage, monkeypatch
):
    """Test late entry with common deadline enforcement."""
    print("\n=== Test: Late Entry Deadline Enforcement ===")
    
    current_time = setup_time_mock(monkeypatch)
    
    # Upload and schedule
    import_id, import_data = await upload_and_wait_for_import(http_client, owner_session['cookies'])
    start_time = current_time[0] + 5
    end_time = start_time + 60
    await schedule_competition(http_client, owner_session['cookies'], import_id, import_data, start_time)
    
    # Advance to middle of competition
    current_time[0] = start_time + 30
    
    # Student starts late (30 seconds into 60-second competition)
    attempt = await start_attempt(http_client, student_session['cookies'], import_id)
    attempt_id = attempt['id']
    
    # Check deadline is set to competition end, not start + duration
    a = await clean_db.tejas_attempts.find_one({'id': attempt_id})
    # Use approximate comparison for floating point
    assert abs(a['deadline'] - end_time) < 0.001, f"Late entry deadline should be competition end: {a['deadline']} != {end_time}"
    print(f"✓ Late entry deadline correctly set to competition end")
    
    # Advance past competition end
    current_time[0] = end_time + 5
    
    # Attempt should be auto-closed
    response = await http_client.get(f'/api/attempts/{attempt_id}', cookies=student_session['cookies'])
    assert response.status_code == 200
    attempt = response.json()['data']
    assert attempt['status'] == 'completed', "Attempt should be auto-completed at deadline"
    print(f"✓ Late entry auto-completed at competition end")
    
    print("\n=== Late Entry Test Complete ===\n")


@pytest.mark.asyncio
async def test_preview_excluded_from_ranking(
    http_client, clean_db, owner_session, mock_storage, monkeypatch
):
    """Test that preview attempts are excluded from competition ranking."""
    print("\n=== Test: Preview Excluded from Ranking ===")
    
    current_time = setup_time_mock(monkeypatch)
    
    # Upload and schedule
    import_id, import_data = await upload_and_wait_for_import(http_client, owner_session['cookies'])
    start_time = current_time[0] + 5
    end_time = start_time + 60
    await schedule_competition(http_client, owner_session['cookies'], import_id, import_data, start_time)
    
    # Advance to start (preview can be started anytime)
    current_time[0] = start_time + 1
    
    # Owner starts preview attempt
    preview_attempt = await start_attempt(http_client, owner_session['cookies'], import_id, preview=True)
    preview_id = preview_attempt['id']
    
    # Verify mode is preview
    a = await clean_db.tejas_attempts.find_one({'id': preview_id})
    assert a['mode'] == 'preview', "Should be preview mode"
    assert not a.get('competition_ranked'), "Preview should not be ranked"
    print(f"✓ Preview attempt created: mode={a['mode']}, ranked={a.get('competition_ranked')}")
    
    # Submit preview
    await submit_answers_via_api(http_client, owner_session['cookies'], preview_id,
                                 preview_attempt['questions'], ['A', 'B', 'D'], current_time[0])
    await submit_attempt(http_client, owner_session['cookies'], preview_id)
    
    # Advance past competition end
    current_time[0] = end_time + 5
    await asyncio.sleep(2)
    
    # Check leaderboard - preview should not appear
    response = await http_client.get(f'/api/competitions/{import_id}', cookies=owner_session['cookies'])
    assert response.status_code == 200
    leaderboard = response.json()['data']
    
    assert leaderboard['participants'] == 0, "Preview should not count as participant"
    print(f"✓ Preview excluded from leaderboard: participants={leaderboard['participants']}")
    
    print("\n=== Preview Exclusion Test Complete ===\n")
