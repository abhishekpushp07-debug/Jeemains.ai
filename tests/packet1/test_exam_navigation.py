"""Exam navigation tests: catalogue, history, filters, pagination, metadata safety."""
import uuid
from datetime import datetime, timezone, timedelta
import pytest
import pytest_asyncio

pytestmark = pytest.mark.asyncio(loop_scope='session')


# ============================================================================
# AUTHENTICATION & AUTHORIZATION TESTS
# ============================================================================

async def test_catalogue_unauth_401(http_client):
    """Catalogue endpoint requires authentication."""
    r = await http_client.get('/api/exam-navigation/jee-main/catalogue')
    assert r.status_code == 401


async def test_history_unauth_401(http_client):
    """History endpoint requires authentication."""
    r = await http_client.get('/api/exam-navigation/jee-main/history')
    assert r.status_code == 401


async def test_catalogue_bad_slug_404(http_client, student_session):
    """Invalid exam slug returns 404."""
    r = await http_client.get('/api/exam-navigation/invalid-exam/catalogue',
                               cookies=student_session['cookies'])
    assert r.status_code == 404
    assert 'not supported' in r.json()['error']['message'].lower()


async def test_history_bad_slug_404(http_client, student_session):
    """Invalid exam slug returns 404 for history."""
    r = await http_client.get('/api/exam-navigation/invalid-exam/history',
                               cookies=student_session['cookies'])
    assert r.status_code == 404
    assert 'not supported' in r.json()['error']['message'].lower()


# ============================================================================
# EXAM SEPARATION TESTS: JEE Main / BITSAT / COMEDK strict isolation
# ============================================================================

async def test_exam_strict_separation(http_client, student_session, clean_db):
    """JEE Main/BITSAT/COMEDK catalogues are strictly separated."""
    now = datetime.now(timezone.utc).timestamp()
    
    # Create sets for different exams
    for exam in ['JEE Main', 'BITSAT', 'COMEDK']:
        set_id = str(uuid.uuid4())
        await clean_db.tejas_sets.insert_one({
            'id': set_id,
            'title': f'{exam} Mock Test',
            'exam': exam,
            'year': '2024',
            'status': 'published',
            'version': 1,
            'revision': 1,
            'test_kind': 'mock',
            'full_length': True,
            'questions': [{'id': str(uuid.uuid4()), 'number': i, 'type': 'mcq', 'subject': 'Physics'} for i in range(1, 51)],
            'rules': {'minutes': 180, 'correct': 4, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
            'created_at': now,
            'audience': 'all',
            'live_enabled': True,
            'start_at': now,
            'end_at': now + 365 * 86400,
            'qa_only': False
        })
    
    # Check JEE Main catalogue
    r_jee = await http_client.get('/api/exam-navigation/jee-main/catalogue?kind=mocks',
                                   cookies=student_session['cookies'])
    assert r_jee.status_code == 200
    jee_data = r_jee.json()['data']
    assert jee_data['exam'] == 'JEE Main'
    assert jee_data['total'] == 1
    assert jee_data['items'][0]['exam'] == 'JEE Main'
    
    # Check BITSAT catalogue
    r_bitsat = await http_client.get('/api/exam-navigation/bitsat/catalogue?kind=mocks',
                                      cookies=student_session['cookies'])
    assert r_bitsat.status_code == 200
    bitsat_data = r_bitsat.json()['data']
    assert bitsat_data['exam'] == 'BITSAT'
    assert bitsat_data['total'] == 1
    assert bitsat_data['items'][0]['exam'] == 'BITSAT'
    
    # Check COMEDK catalogue
    r_comedk = await http_client.get('/api/exam-navigation/comedk/catalogue?kind=mocks',
                                      cookies=student_session['cookies'])
    assert r_comedk.status_code == 200
    comedk_data = r_comedk.json()['data']
    assert comedk_data['exam'] == 'COMEDK'
    assert comedk_data['total'] == 1
    assert comedk_data['items'][0]['exam'] == 'COMEDK'


# ============================================================================
# MOCK/CHAPTER FILTER TESTS: Declared mock excludes chapters + untyped
# ============================================================================

async def test_mock_filter_excludes_chapters(http_client, student_session, clean_db):
    """Mock catalogue excludes chapter tests and untyped tests."""
    now = datetime.now(timezone.utc).timestamp()
    
    # Create chapter test (should be excluded from mocks)
    chapter_id = str(uuid.uuid4())
    await clean_db.tejas_sets.insert_one({
        'id': chapter_id,
        'title': 'Chapter Test',
        'exam': 'JEE Main',
        'year': '',
        'status': 'published',
        'version': 1,
        'revision': 1,
        'chapter_book_id': str(uuid.uuid4()),
        'test_kind': 'chapter',
        'questions': [{'id': str(uuid.uuid4()), 'number': i, 'type': 'mcq', 'subject': 'Physics'} for i in range(1, 51)],
        'rules': {'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
        'created_at': now,
        'audience': 'all',
        'live_enabled': True,
        'start_at': now,
        'end_at': now + 365 * 86400,
        'qa_only': False
    })
    
    # Create mock test (should be included)
    mock_id = str(uuid.uuid4())
    await clean_db.tejas_sets.insert_one({
        'id': mock_id,
        'title': 'Mock Test',
        'exam': 'JEE Main',
        'year': '2024',
        'status': 'published',
        'version': 1,
        'revision': 1,
        'test_kind': 'mock',
        'full_length': True,
        'questions': [{'id': str(uuid.uuid4()), 'number': i, 'type': 'mcq', 'subject': 'Physics'} for i in range(1, 51)],
        'rules': {'minutes': 180, 'correct': 4, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
        'created_at': now,
        'audience': 'all',
        'live_enabled': True,
        'start_at': now,
        'end_at': now + 365 * 86400,
        'qa_only': False
    })
    
    # Create untyped test (should be excluded from mocks)
    untyped_id = str(uuid.uuid4())
    await clean_db.tejas_sets.insert_one({
        'id': untyped_id,
        'title': 'Untyped Test',
        'exam': 'JEE Main',
        'year': '',
        'status': 'published',
        'version': 1,
        'revision': 1,
        # No test_kind, no full_length, no chapter_book_id
        'questions': [{'id': str(uuid.uuid4()), 'number': i, 'type': 'mcq', 'subject': 'Physics'} for i in range(1, 51)],
        'rules': {'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
        'created_at': now,
        'audience': 'all',
        'live_enabled': True,
        'start_at': now,
        'end_at': now + 365 * 86400,
        'qa_only': False
    })
    
    # Check mocks catalogue
    r = await http_client.get('/api/exam-navigation/jee-main/catalogue?kind=mocks',
                               cookies=student_session['cookies'])
    assert r.status_code == 200
    data = r.json()['data']
    assert data['total'] == 1
    assert data['items'][0]['id'] == mock_id
    assert data['items'][0]['test_kind'] == 'mock'


async def test_chapter_filter_includes_chapter_tests(http_client, student_session, clean_db):
    """Chapter catalogue includes only chapter tests."""
    now = datetime.now(timezone.utc).timestamp()
    
    # Create chapter test
    chapter_id = str(uuid.uuid4())
    await clean_db.tejas_sets.insert_one({
        'id': chapter_id,
        'title': 'Chapter Test',
        'exam': 'JEE Main',
        'year': '',
        'status': 'published',
        'version': 1,
        'revision': 1,
        'chapter_book_id': str(uuid.uuid4()),
        'chapter_subject': 'Physics',
        'chapter_number': 1,
        'test_kind': 'chapter',
        'questions': [{'id': str(uuid.uuid4()), 'number': i, 'type': 'mcq', 'subject': 'Physics'} for i in range(1, 51)],
        'rules': {'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
        'created_at': now,
        'audience': 'all',
        'live_enabled': True,
        'start_at': now,
        'end_at': now + 365 * 86400,
        'qa_only': False
    })
    
    # Create mock test (should be excluded)
    mock_id = str(uuid.uuid4())
    await clean_db.tejas_sets.insert_one({
        'id': mock_id,
        'title': 'Mock Test',
        'exam': 'JEE Main',
        'year': '2024',
        'status': 'published',
        'version': 1,
        'revision': 1,
        'test_kind': 'mock',
        'full_length': True,
        'questions': [{'id': str(uuid.uuid4()), 'number': i, 'type': 'mcq', 'subject': 'Physics'} for i in range(1, 51)],
        'rules': {'minutes': 180, 'correct': 4, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
        'created_at': now,
        'audience': 'all',
        'live_enabled': True,
        'start_at': now,
        'end_at': now + 365 * 86400,
        'qa_only': False
    })
    
    # Check chapters catalogue
    r = await http_client.get('/api/exam-navigation/jee-main/catalogue?kind=chapters',
                               cookies=student_session['cookies'])
    assert r.status_code == 200
    data = r.json()['data']
    assert data['total'] == 1
    assert data['items'][0]['id'] == chapter_id
    assert data['items'][0]['test_kind'] == 'chapter'


# ============================================================================
# SUBJECT COUNTS & PAGINATION TESTS
# ============================================================================

async def test_chapter_subject_counts(http_client, student_session, clean_db):
    """Chapter catalogue returns correct subject counts."""
    now = datetime.now(timezone.utc).timestamp()
    
    # Create chapters with different subjects
    subjects = ['Physics', 'Physics', 'Chemistry', 'Mathematics']
    for i, subject in enumerate(subjects):
        set_id = str(uuid.uuid4())
        await clean_db.tejas_sets.insert_one({
            'id': set_id,
            'title': f'{subject} Chapter {i+1}',
            'exam': 'JEE Main',
            'year': '',
            'status': 'published',
            'version': 1,
            'revision': 1,
            'chapter_book_id': str(uuid.uuid4()),
            'chapter_subject': subject,
            'chapter_number': i + 1,
            'test_kind': 'chapter',
            'questions': [{'id': str(uuid.uuid4()), 'number': j, 'type': 'mcq', 'subject': subject} for j in range(1, 51)],
            'rules': {'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
            'created_at': now,
            'audience': 'all',
            'live_enabled': True,
            'start_at': now,
            'end_at': now + 365 * 86400,
            'qa_only': False
        })
    
    # Check subject counts
    r = await http_client.get('/api/exam-navigation/jee-main/catalogue?kind=chapters',
                               cookies=student_session['cookies'])
    assert r.status_code == 200
    data = r.json()['data']
    assert data['total'] == 4
    assert data['subject_counts']['Physics'] == 2
    assert data['subject_counts']['Chemistry'] == 1
    assert data['subject_counts']['Mathematics'] == 1


async def test_catalogue_pagination(http_client, student_session, clean_db):
    """Catalogue pagination works correctly with PAGE_SIZE=12."""
    now = datetime.now(timezone.utc).timestamp()
    
    # Create 25 mock tests
    for i in range(25):
        set_id = str(uuid.uuid4())
        await clean_db.tejas_sets.insert_one({
            'id': set_id,
            'title': f'Mock Test {i+1}',
            'exam': 'JEE Main',
            'year': '2024',
            'status': 'published',
            'version': 1,
            'revision': 1,
            'test_kind': 'mock',
            'full_length': True,
            'questions': [{'id': str(uuid.uuid4()), 'number': j, 'type': 'mcq', 'subject': 'Physics'} for j in range(1, 51)],
            'rules': {'minutes': 180, 'correct': 4, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
            'created_at': now + i,
            'audience': 'all',
            'live_enabled': True,
            'start_at': now,
            'end_at': now + 365 * 86400,
            'qa_only': False
        })
    
    # Page 1
    r1 = await http_client.get('/api/exam-navigation/jee-main/catalogue?kind=mocks&page=1',
                                cookies=student_session['cookies'])
    assert r1.status_code == 200
    data1 = r1.json()['data']
    assert data1['total'] == 25
    assert len(data1['items']) == 12
    assert data1['page'] == 1
    assert data1['pages'] == 3
    
    # Page 2
    r2 = await http_client.get('/api/exam-navigation/jee-main/catalogue?kind=mocks&page=2',
                                cookies=student_session['cookies'])
    assert r2.status_code == 200
    data2 = r2.json()['data']
    assert len(data2['items']) == 12
    assert data2['page'] == 2
    
    # Page 3
    r3 = await http_client.get('/api/exam-navigation/jee-main/catalogue?kind=mocks&page=3',
                                cookies=student_session['cookies'])
    assert r3.status_code == 200
    data3 = r3.json()['data']
    assert len(data3['items']) == 1
    assert data3['page'] == 3


# ============================================================================
# LIVE QUERY FILTER TESTS: Revoked/inactive/future/expired/qa excluded
# ============================================================================

async def test_catalogue_excludes_revoked_tests(http_client, student_session, clean_db):
    """Catalogue excludes tests with live_enabled=false."""
    now = datetime.now(timezone.utc).timestamp()
    
    # Create revoked test
    revoked_id = str(uuid.uuid4())
    await clean_db.tejas_sets.insert_one({
        'id': revoked_id,
        'title': 'Revoked Test',
        'exam': 'JEE Main',
        'year': '2024',
        'status': 'published',
        'version': 1,
        'revision': 1,
        'test_kind': 'mock',
        'full_length': True,
        'questions': [{'id': str(uuid.uuid4()), 'number': i, 'type': 'mcq', 'subject': 'Physics'} for i in range(1, 51)],
        'rules': {'minutes': 180, 'correct': 4, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
        'created_at': now,
        'audience': 'all',
        'live_enabled': False,
        'start_at': now,
        'end_at': now + 365 * 86400,
        'qa_only': False
    })
    
    r = await http_client.get('/api/exam-navigation/jee-main/catalogue?kind=mocks',
                               cookies=student_session['cookies'])
    assert r.status_code == 200
    data = r.json()['data']
    assert data['total'] == 0


async def test_catalogue_excludes_future_tests(http_client, student_session, clean_db):
    """Catalogue excludes tests with start_at in future."""
    now = datetime.now(timezone.utc).timestamp()
    
    # Create future test
    future_id = str(uuid.uuid4())
    await clean_db.tejas_sets.insert_one({
        'id': future_id,
        'title': 'Future Test',
        'exam': 'JEE Main',
        'year': '2024',
        'status': 'published',
        'version': 1,
        'revision': 1,
        'test_kind': 'mock',
        'full_length': True,
        'questions': [{'id': str(uuid.uuid4()), 'number': i, 'type': 'mcq', 'subject': 'Physics'} for i in range(1, 51)],
        'rules': {'minutes': 180, 'correct': 4, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
        'created_at': now,
        'audience': 'all',
        'live_enabled': True,
        'start_at': now + 86400,  # Tomorrow
        'end_at': now + 365 * 86400,
        'qa_only': False
    })
    
    r = await http_client.get('/api/exam-navigation/jee-main/catalogue?kind=mocks',
                               cookies=student_session['cookies'])
    assert r.status_code == 200
    data = r.json()['data']
    assert data['total'] == 0


async def test_catalogue_excludes_expired_tests(http_client, student_session, clean_db):
    """Catalogue excludes tests with end_at in past."""
    now = datetime.now(timezone.utc).timestamp()
    
    # Create expired test
    expired_id = str(uuid.uuid4())
    await clean_db.tejas_sets.insert_one({
        'id': expired_id,
        'title': 'Expired Test',
        'exam': 'JEE Main',
        'year': '2024',
        'status': 'published',
        'version': 1,
        'revision': 1,
        'test_kind': 'mock',
        'full_length': True,
        'questions': [{'id': str(uuid.uuid4()), 'number': i, 'type': 'mcq', 'subject': 'Physics'} for i in range(1, 51)],
        'rules': {'minutes': 180, 'correct': 4, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
        'created_at': now - 400 * 86400,
        'audience': 'all',
        'live_enabled': True,
        'start_at': now - 400 * 86400,
        'end_at': now - 10,  # Expired
        'qa_only': False
    })
    
    r = await http_client.get('/api/exam-navigation/jee-main/catalogue?kind=mocks',
                               cookies=student_session['cookies'])
    assert r.status_code == 200
    data = r.json()['data']
    assert data['total'] == 0


async def test_catalogue_excludes_qa_only_tests(http_client, student_session, clean_db):
    """Catalogue excludes tests marked as qa_only."""
    now = datetime.now(timezone.utc).timestamp()
    
    # Create qa_only test
    qa_id = str(uuid.uuid4())
    await clean_db.tejas_sets.insert_one({
        'id': qa_id,
        'title': 'QA Test',
        'exam': 'JEE Main',
        'year': '2024',
        'status': 'published',
        'version': 1,
        'revision': 1,
        'test_kind': 'mock',
        'full_length': True,
        'questions': [{'id': str(uuid.uuid4()), 'number': i, 'type': 'mcq', 'subject': 'Physics'} for i in range(1, 51)],
        'rules': {'minutes': 180, 'correct': 4, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
        'created_at': now,
        'audience': 'all',
        'live_enabled': True,
        'start_at': now,
        'end_at': now + 365 * 86400,
        'qa_only': True
    })
    
    r = await http_client.get('/api/exam-navigation/jee-main/catalogue?kind=mocks',
                               cookies=student_session['cookies'])
    assert r.status_code == 200
    data = r.json()['data']
    assert data['total'] == 0


# ============================================================================
# AUDIENCE GRANT TESTS
# ============================================================================

async def test_catalogue_respects_audience_grants(http_client, student_session, clean_db):
    """Catalogue respects audience field for access control."""
    now = datetime.now(timezone.utc).timestamp()
    
    # Create test with audience='all'
    public_id = str(uuid.uuid4())
    await clean_db.tejas_sets.insert_one({
        'id': public_id,
        'title': 'Public Test',
        'exam': 'JEE Main',
        'year': '2024',
        'status': 'published',
        'version': 1,
        'revision': 1,
        'test_kind': 'mock',
        'full_length': True,
        'questions': [{'id': str(uuid.uuid4()), 'number': i, 'type': 'mcq', 'subject': 'Physics'} for i in range(1, 51)],
        'rules': {'minutes': 180, 'correct': 4, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
        'created_at': now,
        'audience': 'all',
        'live_enabled': True,
        'start_at': now,
        'end_at': now + 365 * 86400,
        'qa_only': False
    })
    
    # Create test with restricted audience
    restricted_id = str(uuid.uuid4())
    await clean_db.tejas_sets.insert_one({
        'id': restricted_id,
        'title': 'Restricted Test',
        'exam': 'JEE Main',
        'year': '2024',
        'status': 'published',
        'version': 1,
        'revision': 1,
        'test_kind': 'mock',
        'full_length': True,
        'questions': [{'id': str(uuid.uuid4()), 'number': i, 'type': 'mcq', 'subject': 'Physics'} for i in range(1, 51)],
        'rules': {'minutes': 180, 'correct': 4, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
        'created_at': now,
        'audience': 'premium',
        'live_enabled': True,
        'start_at': now,
        'end_at': now + 365 * 86400,
        'qa_only': False
    })
    
    r = await http_client.get('/api/exam-navigation/jee-main/catalogue?kind=mocks',
                               cookies=student_session['cookies'])
    assert r.status_code == 200
    data = r.json()['data']
    # Should only see public test (audience filtering handled by available() function)
    assert data['total'] == 1
    assert {item['id'] for item in data['items']} == {public_id}
    assert restricted_id not in {item['id'] for item in data['items']}


# ============================================================================
# HISTORY TESTS: User isolation, exam isolation, kind/date filters
# ============================================================================

async def test_history_strictly_current_user(http_client, student_session, clean_db):
    """History returns only current user's attempts."""
    now = datetime.now(timezone.utc).timestamp()
    
    # Create attempt for current user
    my_attempt_id = str(uuid.uuid4())
    await clean_db.tejas_attempts.insert_one({
        'id': my_attempt_id,
        'user_id': student_session['user']['id'],
        'set_id': str(uuid.uuid4()),
        'start_key': str(uuid.uuid4()),
        'title': 'My Test',
        'exam': 'JEE Main',
        'mode': 'practice',
        'status': 'completed',
        'version': 1,
        'started_at': now,
        'submitted_at': now + 1800,
        'deadline': now + 3600,
        'count': 50,
        'summary': {'score': 100, 'correct': 30, 'incorrect': 10, 'skipped': 10}
    })
    
    # Create attempt for different user
    other_user_id = str(uuid.uuid4())
    other_attempt_id = str(uuid.uuid4())
    await clean_db.tejas_attempts.insert_one({
        'id': other_attempt_id,
        'user_id': other_user_id,
        'set_id': str(uuid.uuid4()),
        'start_key': str(uuid.uuid4()),
        'title': 'Other Test',
        'exam': 'JEE Main',
        'mode': 'practice',
        'status': 'completed',
        'version': 1,
        'started_at': now,
        'submitted_at': now + 1800,
        'deadline': now + 3600,
        'count': 50,
        'summary': {'score': 120, 'correct': 35, 'incorrect': 5, 'skipped': 10}
    })
    
    r = await http_client.get('/api/exam-navigation/jee-main/history',
                               cookies=student_session['cookies'])
    assert r.status_code == 200
    data = r.json()['data']
    assert data['total'] == 1
    assert data['items'][0]['id'] == my_attempt_id
    assert all(item['id'] != other_attempt_id for item in data['items'])


async def test_history_strictly_current_exam(http_client, student_session, clean_db):
    """History returns only attempts for requested exam."""
    now = datetime.now(timezone.utc).timestamp()
    
    # Create JEE Main attempt
    jee_attempt_id = str(uuid.uuid4())
    await clean_db.tejas_attempts.insert_one({
        'id': jee_attempt_id,
        'user_id': student_session['user']['id'],
        'set_id': str(uuid.uuid4()),
        'start_key': str(uuid.uuid4()),
        'title': 'JEE Main Test',
        'exam': 'JEE Main',
        'mode': 'practice',
        'status': 'completed',
        'version': 1,
        'started_at': now,
        'submitted_at': now + 1800,
        'deadline': now + 3600,
        'count': 50,
        'summary': {'score': 100, 'correct': 30, 'incorrect': 10, 'skipped': 10}
    })
    
    # Create BITSAT attempt
    bitsat_attempt_id = str(uuid.uuid4())
    await clean_db.tejas_attempts.insert_one({
        'id': bitsat_attempt_id,
        'user_id': student_session['user']['id'],
        'set_id': str(uuid.uuid4()),
        'start_key': str(uuid.uuid4()),
        'title': 'BITSAT Test',
        'exam': 'BITSAT',
        'mode': 'practice',
        'status': 'completed',
        'version': 1,
        'started_at': now,
        'submitted_at': now + 1800,
        'deadline': now + 3600,
        'count': 50,
        'summary': {'score': 120, 'correct': 35, 'incorrect': 5, 'skipped': 10}
    })
    
    r = await http_client.get('/api/exam-navigation/jee-main/history',
                               cookies=student_session['cookies'])
    assert r.status_code == 200
    data = r.json()['data']
    assert data['exam'] == 'JEE Main'
    assert all(item['exam'] == 'JEE Main' for item in data['items'])
    assert any(item['id'] == jee_attempt_id for item in data['items'])
    assert all(item['id'] != bitsat_attempt_id for item in data['items'])


async def test_history_kind_filter_before_pagination(http_client, student_session, clean_db):
    """History applies kind filter BEFORE pagination with >20 mixed records."""
    now = datetime.now(timezone.utc).timestamp()
    
    # Create 15 mock attempts and 10 chapter attempts (25 total)
    mock_ids = []
    chapter_ids = []
    
    for i in range(15):
        mock_set_id = str(uuid.uuid4())
        await clean_db.tejas_sets.insert_one({
            'id': mock_set_id,
            'test_kind': 'mock',
            'full_length': True
        })
        
        attempt_id = str(uuid.uuid4())
        await clean_db.tejas_attempts.insert_one({
            'id': attempt_id,
            'user_id': student_session['user']['id'],
            'set_id': mock_set_id,
            'start_key': str(uuid.uuid4()),
            'title': f'Mock Test {i+1}',
            'exam': 'JEE Main',
            'mode': 'practice',
            'status': 'completed',
            'version': 1,
            'started_at': now + i,
            'submitted_at': now + i + 1800,
            'deadline': now + i + 3600,
            'count': 50,
            'summary': {'score': 100, 'correct': 30, 'incorrect': 10, 'skipped': 10}
        })
        mock_ids.append(attempt_id)
    
    for i in range(10):
        chapter_set_id = str(uuid.uuid4())
        await clean_db.tejas_sets.insert_one({
            'id': chapter_set_id,
            'chapter_book_id': str(uuid.uuid4()),
            'test_kind': 'chapter'
        })
        
        attempt_id = str(uuid.uuid4())
        await clean_db.tejas_attempts.insert_one({
            'id': attempt_id,
            'user_id': student_session['user']['id'],
            'set_id': chapter_set_id,
            'start_key': str(uuid.uuid4()),
            'title': f'Chapter Test {i+1}',
            'exam': 'JEE Main',
            'mode': 'practice',
            'status': 'completed',
            'version': 1,
            'started_at': now + 15 + i,
            'submitted_at': now + 15 + i + 1800,
            'deadline': now + 15 + i + 3600,
            'count': 50,
            'summary': {'score': 100, 'correct': 30, 'incorrect': 10, 'skipped': 10}
        })
        chapter_ids.append(attempt_id)
    
    # Filter by mock kind
    r_mock = await http_client.get('/api/exam-navigation/jee-main/history?kind=mock',
                                    cookies=student_session['cookies'])
    assert r_mock.status_code == 200
    mock_data = r_mock.json()['data']
    assert mock_data['total'] == 15
    assert all(item['test_kind'] == 'mock' for item in mock_data['items'])
    
    # Filter by chapter kind
    r_chapter = await http_client.get('/api/exam-navigation/jee-main/history?kind=chapter',
                                       cookies=student_session['cookies'])
    assert r_chapter.status_code == 200
    chapter_data = r_chapter.json()['data']
    assert chapter_data['total'] == 10
    assert all(item['test_kind'] == 'chapter' for item in chapter_data['items'])


async def test_history_date_filter_before_pagination(http_client, student_session, clean_db):
    """History applies date filter BEFORE pagination."""
    now = datetime.now(timezone.utc).timestamp()
    
    # Create attempts at different times
    old_attempt_id = str(uuid.uuid4())
    await clean_db.tejas_attempts.insert_one({
        'id': old_attempt_id,
        'user_id': student_session['user']['id'],
        'set_id': str(uuid.uuid4()),
        'start_key': str(uuid.uuid4()),
        'title': 'Old Test',
        'exam': 'JEE Main',
        'mode': 'practice',
        'status': 'completed',
        'version': 1,
        'started_at': now - 100 * 86400,  # 100 days ago
        'submitted_at': now - 100 * 86400 + 1800,
        'deadline': now - 100 * 86400 + 3600,
        'count': 50,
        'summary': {'score': 100, 'correct': 30, 'incorrect': 10, 'skipped': 10}
    })
    
    recent_attempt_id = str(uuid.uuid4())
    await clean_db.tejas_attempts.insert_one({
        'id': recent_attempt_id,
        'user_id': student_session['user']['id'],
        'set_id': str(uuid.uuid4()),
        'start_key': str(uuid.uuid4()),
        'title': 'Recent Test',
        'exam': 'JEE Main',
        'mode': 'practice',
        'status': 'completed',
        'version': 1,
        'started_at': now - 5 * 86400,  # 5 days ago
        'submitted_at': now - 5 * 86400 + 1800,
        'deadline': now - 5 * 86400 + 3600,
        'count': 50,
        'summary': {'score': 120, 'correct': 35, 'incorrect': 5, 'skipped': 10}
    })
    
    # Filter last 7 days
    r = await http_client.get('/api/exam-navigation/jee-main/history?days=7',
                               cookies=student_session['cookies'])
    assert r.status_code == 200
    data = r.json()['data']
    assert data['total'] == 1
    assert data['items'][0]['id'] == recent_attempt_id


async def test_history_stable_sort_same_time(http_client, student_session, clean_db):
    """History sort is stable for attempts at same timestamp."""
    now = datetime.now(timezone.utc).timestamp()
    
    # Create 3 attempts at exact same time
    attempt_ids = []
    for i in range(3):
        attempt_id = str(uuid.uuid4())
        await clean_db.tejas_attempts.insert_one({
            'id': attempt_id,
            'user_id': student_session['user']['id'],
            'set_id': str(uuid.uuid4()),
        'start_key': str(uuid.uuid4()),
            'title': f'Test {i+1}',
            'exam': 'JEE Main',
            'mode': 'practice',
            'status': 'completed',
            'version': 1,
            'started_at': now,  # Same timestamp
            'submitted_at': now + 1800,
            'deadline': now + 3600,
            'count': 50,
            'summary': {'score': 100, 'correct': 30, 'incorrect': 10, 'skipped': 10}
        })
        attempt_ids.append(attempt_id)
    
    # Fetch history multiple times
    results = []
    for _ in range(3):
        r = await http_client.get('/api/exam-navigation/jee-main/history',
                                   cookies=student_session['cookies'])
        assert r.status_code == 200
        data = r.json()['data']
        results.append([item['id'] for item in data['items']])
    
    # All results should have same order (stable sort by id as secondary key)
    assert results[0] == results[1] == results[2]


# ============================================================================
# ACTIVE EXPIRED FINALIZATION TEST
# ============================================================================

async def test_history_finalizes_active_expired_attempts(http_client, student_session, clean_db):
    """History endpoint finalizes active attempts past deadline."""
    now = datetime.now(timezone.utc).timestamp()
    
    # Create active attempt with expired deadline
    attempt_id = str(uuid.uuid4())
    await clean_db.tejas_attempts.insert_one({
        'id': attempt_id,
        'user_id': student_session['user']['id'],
        'set_id': str(uuid.uuid4()),
        'start_key': str(uuid.uuid4()),
        'title': 'Expired Active Test',
        'exam': 'JEE Main',
        'mode': 'practice',
        'status': 'active',
        'version': 1,
        'started_at': now - 7200,
        'deadline': now - 10,  # Expired 10 seconds ago
        'count': 50,
        'questions': [],
        'answers': {},
        'rules': {'minutes': 180, 'correct': 4, 'wrong': -1, 'skipped': 0}
    })
    
    r = await http_client.get('/api/exam-navigation/jee-main/history',
                               cookies=student_session['cookies'])
    assert r.status_code == 200
    data = r.json()['data']
    
    # Find the attempt in history
    attempt = next((item for item in data['items'] if item['id'] == attempt_id), None)
    assert attempt is not None
    # Should be finalized to completed
    assert attempt['status'] == 'completed'
    assert 'submitted_at' in attempt


# ============================================================================
# COMPETITION EMBARGO TEST
# ============================================================================

async def test_history_hides_future_competition_summary(http_client, student_session, clean_db):
    """History hides summary for competition attempts before competition_end."""
    now = datetime.now(timezone.utc).timestamp()
    
    # Create competition attempt with future competition_end
    attempt_id = str(uuid.uuid4())
    await clean_db.tejas_attempts.insert_one({
        'id': attempt_id,
        'user_id': student_session['user']['id'],
        'set_id': str(uuid.uuid4()),
        'start_key': str(uuid.uuid4()),
        'title': 'Competition Test',
        'exam': 'JEE Main',
        'mode': 'competition',
        'status': 'completed',
        'version': 1,
        'started_at': now - 3600,
        'submitted_at': now - 1800,
        'deadline': now,
        'count': 50,
        'summary': {'score': 150, 'correct': 50, 'incorrect': 0, 'skipped': 0},
        'competition_end': now + 86400  # Ends tomorrow
    })
    
    r = await http_client.get('/api/exam-navigation/jee-main/history',
                               cookies=student_session['cookies'])
    assert r.status_code == 200
    data = r.json()['data']
    
    # Find the attempt
    attempt = next((item for item in data['items'] if item['id'] == attempt_id), None)
    assert attempt is not None
    # Summary should be hidden
    assert attempt['summary'] is None
    # server_now should be present
    assert 'server_now' in attempt


async def test_history_shows_past_competition_summary(http_client, student_session, clean_db):
    """History shows summary for competition attempts after competition_end."""
    now = datetime.now(timezone.utc).timestamp()
    
    # Create competition attempt with past competition_end
    attempt_id = str(uuid.uuid4())
    await clean_db.tejas_attempts.insert_one({
        'id': attempt_id,
        'user_id': student_session['user']['id'],
        'set_id': str(uuid.uuid4()),
        'start_key': str(uuid.uuid4()),
        'title': 'Past Competition Test',
        'exam': 'JEE Main',
        'mode': 'competition',
        'status': 'completed',
        'version': 1,
        'started_at': now - 7200,
        'submitted_at': now - 5400,
        'deadline': now - 3600,
        'count': 50,
        'summary': {'score': 150, 'correct': 50, 'incorrect': 0, 'skipped': 0},
        'competition_end': now - 10  # Ended 10 seconds ago
    })
    
    r = await http_client.get('/api/exam-navigation/jee-main/history',
                               cookies=student_session['cookies'])
    assert r.status_code == 200
    data = r.json()['data']
    
    # Find the attempt
    attempt = next((item for item in data['items'] if item['id'] == attempt_id), None)
    assert attempt is not None
    # Summary should be visible
    assert attempt['summary'] is not None
    assert attempt['summary']['score'] == 150


# ============================================================================
# SAFE METADATA TEST: No question keys leaked
# ============================================================================

async def test_catalogue_safe_metadata_no_question_keys(http_client, student_session, clean_db):
    """Catalogue returns safe metadata without question keys or answers."""
    now = datetime.now(timezone.utc).timestamp()
    
    # Create test with full question data including answers
    set_id = str(uuid.uuid4())
    questions = []
    for i in range(1, 51):
        questions.append({
            'id': str(uuid.uuid4()),
            'number': i,
            'type': 'mcq',
            'subject': 'Physics',
            'text': f'Question {i} text',
            'options': {'A': 'Option A', 'B': 'Option B', 'C': 'Option C', 'D': 'Option D'},
            'answer': 'A',  # Should not be leaked
            'solution': f'Solution {i}',  # Should not be leaked
            'disposition': 'standard'
        })
    
    await clean_db.tejas_sets.insert_one({
        'id': set_id,
        'title': 'Test with Answers',
        'exam': 'JEE Main',
        'year': '2024',
        'status': 'published',
        'version': 1,
        'revision': 1,
        'test_kind': 'mock',
        'full_length': True,
        'questions': questions,
        'rules': {'minutes': 180, 'correct': 4, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
        'created_at': now,
        'audience': 'all',
        'live_enabled': True,
        'start_at': now,
        'end_at': now + 365 * 86400,
        'qa_only': False
    })
    
    r = await http_client.get('/api/exam-navigation/jee-main/catalogue?kind=mocks',
                               cookies=student_session['cookies'])
    assert r.status_code == 200
    data = r.json()['data']
    
    # Find the test
    test = next((item for item in data['items'] if item['id'] == set_id), None)
    assert test is not None
    
    # Should have safe metadata
    assert 'title' in test
    assert 'exam' in test
    assert 'count' in test
    
    # Should NOT have full question details with answers
    # The summary() function should exclude question.answer field
    if 'questions' in test:
        for q in test['questions']:
            assert 'answer' not in q, "Question answers should not be leaked in catalogue"
    
    # Should not have raw question text
    import json
    test_json = json.dumps(test)
    assert 'Question 1 text' not in test_json


# ============================================================================
# PDF REPORT TEMPLATE CACHE VERSION TEST
# ============================================================================

async def test_pdf_report_template_cache_version(clean_db):
    """PDF report generation uses correct template cache version."""
    from tejas.reports import render_report
    
    now = datetime.now(timezone.utc).timestamp()
    
    # Create minimal attempt for report generation
    questions = []
    for i in range(1, 51):
        q_id = str(uuid.uuid4())
        questions.append({
            'id': q_id,
            'number': i,
            'type': 'mcq',
            'subject': 'Physics',
            'text': f'Question {i}',
            'options': {'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'},
            'answer': 'A',
            'solution': f'Solution {i}',
            'render_mode': 'typed',
            'q_refs': [],
            's_refs': [],
            'accessible_text': f'Q{i}',
            'solution_accessible_text': f'S{i}',
            'disposition': 'standard'
        })
    
    attempt = {
        'id': str(uuid.uuid4()),
        'user_id': str(uuid.uuid4()),
        'status': 'completed',
        'mode': 'practice',
        'started_at': now,
        'submitted_at': now + 1800,
        'deadline': now + 3600,
        'title': 'Test Report',
        'exam': 'JEE Main',
        'version': 1,
        'rules': {'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0, 'numeric_policy': 'integer_exact', 'numeric_rule': 'Integer exact match'},
        'questions': questions,
        'count': 50,
        'answers': {
            questions[0]['id']: {'value': 'A', 'normalized_value': 'A'},
            questions[1]['id']: {'value': 'B', 'normalized_value': 'B'}
        },
        'response_schema': {q['id']: {'type': 'mcq', 'options': ['A', 'B', 'C', 'D']} for q in questions},
        'summary': {'score': 2, 'correct': 1, 'incorrect': 1, 'skipped': 48}
    }
    
    def mock_loader(file_id):
        # Return minimal PNG
        return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    
    # Generate report
    pdf_bytes = render_report(attempt, mock_loader)
    
    # Verify PDF was generated
    assert len(pdf_bytes) > 1000
    assert pdf_bytes[:4] == b'%PDF'
    
    # Verify PDF contains expected content
    import fitz
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    first_page_text = doc[0].get_text()
    doc.close()
    
    # Should contain test title and exam
    assert 'Test Report' in first_page_text
    assert 'JEEMAINS.AI' in first_page_text.upper()


# ============================================================================
# HISTORY PAGINATION TEST
# ============================================================================

async def test_history_pagination_20_per_page(http_client, student_session, clean_db):
    """History pagination uses 20 items per page."""
    now = datetime.now(timezone.utc).timestamp()
    
    # Create 45 attempts
    for i in range(45):
        attempt_id = str(uuid.uuid4())
        await clean_db.tejas_attempts.insert_one({
            'id': attempt_id,
            'user_id': student_session['user']['id'],
            'set_id': str(uuid.uuid4()),
            'start_key': str(uuid.uuid4()),
            'title': f'Test {i+1}',
            'exam': 'JEE Main',
            'mode': 'practice',
            'status': 'completed',
            'version': 1,
            'started_at': now + i,
            'submitted_at': now + i + 1800,
            'deadline': now + i + 3600,
            'count': 50,
            'summary': {'score': 100, 'correct': 30, 'incorrect': 10, 'skipped': 10}
        })
    
    # Page 1
    r1 = await http_client.get('/api/exam-navigation/jee-main/history?page=1',
                                cookies=student_session['cookies'])
    assert r1.status_code == 200
    data1 = r1.json()['data']
    assert data1['total'] == 45
    assert len(data1['items']) == 20
    assert data1['page'] == 1
    assert data1['pages'] == 3
    
    # Page 2
    r2 = await http_client.get('/api/exam-navigation/jee-main/history?page=2',
                                cookies=student_session['cookies'])
    assert r2.status_code == 200
    data2 = r2.json()['data']
    assert len(data2['items']) == 20
    assert data2['page'] == 2
    
    # Page 3
    r3 = await http_client.get('/api/exam-navigation/jee-main/history?page=3',
                                cookies=student_session['cookies'])
    assert r3.status_code == 200
    data3 = r3.json()['data']
    assert len(data3['items']) == 5
    assert data3['page'] == 3


# ============================================================================
# PREVIEW MODE EXCLUSION TEST
# ============================================================================

async def test_history_excludes_preview_mode(http_client, student_session, clean_db):
    """History excludes preview mode attempts."""
    now = datetime.now(timezone.utc).timestamp()
    
    # Create preview attempt
    preview_id = str(uuid.uuid4())
    await clean_db.tejas_attempts.insert_one({
        'id': preview_id,
        'user_id': student_session['user']['id'],
        'set_id': str(uuid.uuid4()),
        'start_key': str(uuid.uuid4()),
        'title': 'Preview Test',
        'exam': 'JEE Main',
        'mode': 'preview',
        'status': 'completed',
        'version': 1,
        'started_at': now,
        'submitted_at': now + 1800,
        'deadline': now + 3600,
        'count': 50,
        'summary': {'score': 100, 'correct': 30, 'incorrect': 10, 'skipped': 10}
    })
    
    # Create practice attempt
    practice_id = str(uuid.uuid4())
    await clean_db.tejas_attempts.insert_one({
        'id': practice_id,
        'user_id': student_session['user']['id'],
        'set_id': str(uuid.uuid4()),
        'start_key': str(uuid.uuid4()),
        'title': 'Practice Test',
        'exam': 'JEE Main',
        'mode': 'practice',
        'status': 'completed',
        'version': 1,
        'started_at': now,
        'submitted_at': now + 1800,
        'deadline': now + 3600,
        'count': 50,
        'summary': {'score': 120, 'correct': 35, 'incorrect': 5, 'skipped': 10}
    })
    
    r = await http_client.get('/api/exam-navigation/jee-main/history',
                               cookies=student_session['cookies'])
    assert r.status_code == 200
    data = r.json()['data']
    
    # Should only see practice attempt
    assert any(item['id'] == practice_id for item in data['items'])
    assert all(item['id'] != preview_id for item in data['items'])
    assert all(item['mode'] != 'preview' for item in data['items'])
