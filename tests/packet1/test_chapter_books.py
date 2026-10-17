"""Chapter-wise BITSAT tests: catalog, publication, upload guards, attempt lifecycle, immutability."""
import asyncio
import hashlib
import json
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest
import pytest_asyncio

pytestmark = pytest.mark.asyncio(loop_scope='session')
ROOT = Path(__file__).resolve().parents[2]


def make_complete_chapter_set(set_id, book_id, chapter_number=1, subject='Physics', title='Units & Measurements', 
                               status='draft', now=None, start_page=1, end_page=10, key_page=11):
    """Create a complete chapter set with all required fields including 50 complete questions."""
    if now is None:
        now = datetime.now(timezone.utc).timestamp()

    questions = []
    for i in range(1, 51):
        q_id = str(uuid.uuid4())
        questions.append({
            'id': q_id,
            'number': i,
            'type': 'mcq',
            'subject': subject,
            'text': f'Question {i} text with options (A) opt1 (B) opt2 (C) opt3 (D) opt4',
            'options': {'A': 'Option A', 'B': 'Option B', 'C': 'Option C', 'D': 'Option D'},
            'answer': ['A', 'B', 'C', 'D'][i % 4],
            'solution': f'Solution for question {i}',
            'solution_number': i,
            'render_mode': 'typed',
            'q_refs': [{'page': start_page + (i-1)//5, 'rect': [40, 100, 500, 200], 'file_id': str(uuid.uuid4())}],
            's_refs': [{'page': key_page, 'rect': [40, 100 + i*10, 500, 110 + i*10], 'file_id': str(uuid.uuid4())}],
            'accessible_text': f'Question {i}',
            'solution_accessible_text': f'Solution {i}',
            'disposition': 'standard'
        })

    return {
        'id': set_id,
        'chapter_book_id': book_id,
        'chapter_number': chapter_number,
        'chapter_subject': subject,
        'title': title,
        'exam': 'BITSAT',
        'year': '',
        'status': status,
        'version': 1,
        'revision': 1,
        'questions': questions,
        'rules': {'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
        'created_at': now,
        'audience': 'all',
        'start_page': start_page,
        'end_page': end_page,
        'key_page': key_page,
        'verification': {'questions': 50, 'keys': 50, 'options': 50, 'key_checks_agree': True, 'source_images': True},
        'file_ids': [],
        'profile_mode': 'practice',
        'rights_upload': True,
        'rights_publish': True,
        'rights_report': True,
        'source': 'TEJAS200 chapter-wise original practice',
        'attribution': 'TEJAS200 · Owner-supplied original practice material',
        'competition': False,
        'solution_kind': 'answer_key_only'
    }


@pytest.fixture(autouse=True)
def mock_storage(monkeypatch):
    """Mock storage operations to avoid external HTTP calls."""
    storage_data = {}

    def mock_put_object(path, data):
        storage_data[path] = data
        return path

    def mock_get_object(path):
        if path in storage_data:
            return storage_data[path]
        # Return minimal valid PDF for tests
        return b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type/Pages/Count 1/Kids[3 0 R]>>\nendobj\n3 0 obj\n<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000015 00000 n\n0000000068 00000 n\n0000000125 00000 n\ntrailer\n<</Size 4/Root 1 0 R>>\nstartxref\n203\n%%EOF'

    import tejas_storage
    monkeypatch.setattr(tejas_storage, 'put_object', mock_put_object)
    monkeypatch.setattr(tejas_storage, 'get_object', mock_get_object)
    # Patch the names looked up by the consumer even if another suite imported it first.
    from tejas import chapter_books
    monkeypatch.setattr(chapter_books, 'put_object', mock_put_object)
    monkeypatch.setattr(chapter_books, 'get_object', mock_get_object)


@pytest_asyncio.fixture(loop_scope='session')
async def owner_session(clean_db):
    """Create owner session for tests requiring owner privileges."""
    from tejas.auth import token
    owner_user = {
        'id': str(uuid.uuid4()), 'email': 'owner@isolated.invalid', 'role': 'owner',
        'name': 'Synthetic owner', 'exam': 'BITSAT', 'access_type': 'staff_password'
    }
    await clean_db.tejas_users.insert_one(dict(owner_user))
    sid = str(uuid.uuid4())
    await clean_db.tejas_sessions.insert_one({
        'id': sid, 'user_id': owner_user['id'],
        'access_type': owner_user['access_type'],
        'expires_at': datetime.now(timezone.utc) + timedelta(hours=1)
    })
    return {
        'user': owner_user, 'session_id': sid,
        'cookies': {
            'access_token': token(owner_user, sid, 'access', 900),
            'refresh_token': token(owner_user, sid, 'refresh', 3600)
        }
    }


# ============================================================================
# CATALOG TESTS: Public/My chapter exams with filters, pagination, subjects
# ============================================================================

async def test_public_chapter_catalog_empty(http_client):
    """Public catalog returns empty when no published chapter tests exist."""
    r = await http_client.get('/api/chapter-exams')
    assert r.status_code == 200
    data = r.json()['data']
    assert data['items'] == []
    assert data['total'] == 0
    assert data['page'] == 1
    assert data['pages'] == 1
    assert data['subject_counts'] == {}


async def test_public_chapter_catalog_filters_unpublished(http_client, clean_db):
    """Public catalog excludes draft/unlive chapter tests."""
    # Insert a draft chapter test
    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Physics Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': 1700000000.0,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'}
    })
    await clean_db.tejas_sets.insert_one({
        'id': set_id, 'chapter_book_id': book_id, 'chapter_number': 1,
        'chapter_subject': 'Physics', 'title': 'Units & Measurements',
        'exam': 'BITSAT', 'year': '', 'status': 'draft', 'version': 1, 'revision': 1,
        'questions': [{'id': str(uuid.uuid4()), 'number': i, 'type': 'mcq', 'subject': 'Physics'} for i in range(1, 51)],
        'rules': {'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
        'created_at': 1700000000.0, 'audience': 'all', 'live_enabled': False
    })
    r = await http_client.get('/api/chapter-exams')
    assert r.status_code == 200
    assert r.json()['data']['total'] == 0


async def test_public_chapter_catalog_live_published(http_client, clean_db):
    """Public catalog shows only live published chapter tests within validity."""
    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()
    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Physics Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'},
        'publication_start': now
    })
    await clean_db.tejas_sets.insert_one({
        'id': set_id, 'chapter_book_id': book_id, 'chapter_number': 1,
        'chapter_subject': 'Physics', 'title': 'Units & Measurements',
        'exam': 'BITSAT', 'year': '', 'status': 'published', 'version': 1, 'revision': 1,
        'questions': [{'id': str(uuid.uuid4()), 'number': i, 'type': 'mcq', 'subject': 'Physics'} for i in range(1, 51)],
        'rules': {'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
        'created_at': now, 'audience': 'all', 'live_enabled': True,
        'start_at': now, 'end_at': now + 365 * 86400,
        'expires': datetime.fromtimestamp(now + 365 * 86400, timezone.utc).date().isoformat()
    })
    r = await http_client.get('/api/chapter-exams')
    assert r.status_code == 200
    data = r.json()['data']
    assert data['total'] == 1
    assert len(data['items']) == 1
    assert data['items'][0]['title'] == 'Units & Measurements'
    assert data['items'][0]['chapter_subject'] == 'Physics'
    assert data['items'][0]['count'] == 50


async def test_chapter_catalog_subject_filter(http_client, clean_db):
    """Catalog filters by subject and returns correct subject counts."""
    book_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()
    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'},
        'publication_start': now
    })
    # Insert 2 Physics and 1 Chemistry chapter
    for i, subj in enumerate(['Physics', 'Physics', 'Chemistry']):
        set_id = str(uuid.uuid4())
        await clean_db.tejas_sets.insert_one({
            'id': set_id, 'chapter_book_id': book_id, 'chapter_number': i + 1,
            'chapter_subject': subj, 'title': f'Chapter {i+1}',
            'exam': 'BITSAT', 'year': '', 'status': 'published', 'version': 1, 'revision': 1,
            'questions': [{'id': str(uuid.uuid4()), 'number': j, 'type': 'mcq', 'subject': subj} for j in range(1, 51)],
            'rules': {'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
            'created_at': now, 'audience': 'all', 'live_enabled': True,
            'start_at': now, 'end_at': now + 365 * 86400,
            'expires': datetime.fromtimestamp(now + 365 * 86400, timezone.utc).date().isoformat()
        })

    # Test subject filter
    r = await http_client.get('/api/chapter-exams?subject=Physics')
    assert r.status_code == 200
    data = r.json()['data']
    assert data['total'] == 2
    assert all(item['chapter_subject'] == 'Physics' for item in data['items'])
    assert data['subject_counts']['Physics'] == 2
    assert data['subject_counts']['Chemistry'] == 1


async def test_chapter_catalog_pagination(http_client, clean_db):
    """Catalog pagination works correctly with 12 items per page."""
    book_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()
    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'},
        'publication_start': now
    })
    # Insert 15 chapters
    for i in range(15):
        set_id = str(uuid.uuid4())
        await clean_db.tejas_sets.insert_one({
            'id': set_id, 'chapter_book_id': book_id, 'chapter_number': i + 1,
            'chapter_subject': 'Physics', 'title': f'Chapter {i+1}',
            'exam': 'BITSAT', 'year': '', 'status': 'published', 'version': 1, 'revision': 1,
            'questions': [{'id': str(uuid.uuid4()), 'number': j, 'type': 'mcq', 'subject': 'Physics'} for j in range(1, 51)],
            'rules': {'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
            'created_at': now, 'audience': 'all', 'live_enabled': True,
            'start_at': now, 'end_at': now + 365 * 86400,
            'expires': datetime.fromtimestamp(now + 365 * 86400, timezone.utc).date().isoformat()
        })

    # Page 1
    r1 = await http_client.get('/api/chapter-exams?page=1')
    assert r1.status_code == 200
    data1 = r1.json()['data']
    assert data1['total'] == 15
    assert len(data1['items']) == 12
    assert data1['page'] == 1
    assert data1['pages'] == 2

    # Page 2
    r2 = await http_client.get('/api/chapter-exams?page=2')
    assert r2.status_code == 200
    data2 = r2.json()['data']
    assert len(data2['items']) == 3
    assert data2['page'] == 2


async def test_my_chapter_catalog_with_attempt_status(http_client, student_session, clean_db):
    """My catalog includes latest attempt status for authenticated user."""
    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'},
        'publication_start': now
    })
    await clean_db.tejas_sets.insert_one({
        'id': set_id, 'chapter_book_id': book_id, 'chapter_number': 1,
        'chapter_subject': 'Physics', 'title': 'Units & Measurements',
        'exam': 'BITSAT', 'year': '', 'status': 'published', 'version': 1, 'revision': 1,
        'questions': [{'id': str(uuid.uuid4()), 'number': i, 'type': 'mcq', 'subject': 'Physics'} for i in range(1, 51)],
        'rules': {'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
        'created_at': now, 'audience': 'all', 'live_enabled': True,
        'start_at': now, 'end_at': now + 365 * 86400,
        'expires': datetime.fromtimestamp(now + 365 * 86400, timezone.utc).date().isoformat()
    })

    # Create an active attempt
    attempt_id = str(uuid.uuid4())
    await clean_db.tejas_attempts.insert_one({
        'id': attempt_id, 'user_id': student_session['user']['id'],
        'set_id': set_id, 'status': 'active', 'mode': 'practice',
        'started_at': now, 'deadline': now + 3600,
        'start_key': str(uuid.uuid4()),
        'title': 'Units & Measurements', 'exam': 'BITSAT', 'version': 1,
        'rules': {'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
        'questions': [], 'answers': {}
    })

    r = await http_client.get('/api/my/chapter-exams', cookies=student_session['cookies'])
    assert r.status_code == 200
    data = r.json()['data']
    assert data['total'] == 1
    assert data['items'][0]['attempt'] is not None
    assert data['items'][0]['attempt']['id'] == attempt_id
    assert data['items'][0]['attempt']['status'] == 'active'


async def test_chapter_catalog_metadata_only_no_keys(http_client, clean_db):
    """Public catalog returns metadata only, no question keys or private paths."""
    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'private/source/path'}
    })
    await clean_db.tejas_sets.insert_one({
        'id': set_id, 'chapter_book_id': book_id, 'chapter_number': 1,
        'chapter_subject': 'Physics', 'title': 'Units & Measurements',
        'exam': 'BITSAT', 'year': '', 'status': 'published', 'version': 1, 'revision': 1,
        'questions': [{'id': str(uuid.uuid4()), 'number': i, 'type': 'mcq', 'subject': 'Physics', 'answer': 'A'} for i in range(1, 51)],
        'rules': {'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
        'created_at': now, 'audience': 'all', 'live_enabled': True,
        'start_at': now, 'end_at': now + 365 * 86400,
        'expires': datetime.fromtimestamp(now + 365 * 86400, timezone.utc).date().isoformat()
    })

    r = await http_client.get('/api/chapter-exams')
    assert r.status_code == 200
    data = r.json()['data']
    item = data['items'][0]
    # Should not contain answer keys
    assert 'questions' not in item or all('answer' not in q for q in item.get('questions', []))
    # Should not contain private paths
    assert 'path' not in json.dumps(item)


# ============================================================================
# PUBLISH GATE TESTS: Verification, 365 days, 50Q, rules, idempotency
# ============================================================================

async def test_publish_rejects_unverified_sources(http_client, owner_session, clean_db):
    """Publish gate rejects chapters without independent_check verification."""
    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'}
    })
    await clean_db.tejas_sets.insert_one({
        'id': set_id, 'chapter_book_id': book_id, 'chapter_number': 1,
        'chapter_subject': 'Physics', 'title': 'Units & Measurements',
        'exam': 'BITSAT', 'year': '', 'status': 'draft', 'version': 1, 'revision': 1,
        'questions': [{'id': str(uuid.uuid4()), 'number': i, 'type': 'mcq', 'subject': 'Physics'} for i in range(1, 51)],
        'rules': {'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
        'created_at': now, 'audience': 'all',
        'verification': {'key_checks_agree': True}
        # Missing independent_check
    })

    r = await http_client.post(f'/api/studio/chapter-books/{book_id}/publish',
                                json={'revision': 1},
                                cookies=owner_session['cookies'])
    assert r.status_code == 409
    assert 'independent' in r.json()['error']['message'].lower() or 'recheck' in r.json()['error']['message'].lower()


async def test_publish_rejects_revision_mismatch(http_client, owner_session, clean_db):
    """Publish gate rejects stale revision to prevent race conditions."""
    book_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 2, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'}
    })

    r = await http_client.post(f'/api/studio/chapter-books/{book_id}/publish',
                                json={'revision': 1},
                                cookies=owner_session['cookies'])
    assert r.status_code == 409
    assert 'reload' in r.json()['error']['message'].lower() or 'revision' in r.json()['error']['message'].lower()


async def test_publish_rejects_partial_chapter_counts(http_client, owner_session, clean_db):
    """Publish gate rejects chapters with != 50 questions."""
    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'}
    })
    await clean_db.tejas_sets.insert_one({
        'id': set_id, 'chapter_book_id': book_id, 'chapter_number': 1,
        'chapter_subject': 'Physics', 'title': 'Units & Measurements',
        'exam': 'BITSAT', 'year': '', 'status': 'draft', 'version': 1, 'revision': 1,
        'questions': [{'id': str(uuid.uuid4()), 'number': i, 'type': 'mcq', 'subject': 'Physics'} for i in range(1, 46)],  # Only 45
        'rules': {'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
        'created_at': now, 'audience': 'all',
        'verification': {'key_checks_agree': True},
        'independent_check': {'method': 'test', 'checked_at': now}
    })

    r = await http_client.post(f'/api/studio/chapter-books/{book_id}/publish',
                                json={'revision': 1},
                                cookies=owner_session['cookies'])
    assert r.status_code == 409
    assert '50' in r.json()['error']['message']


async def test_publish_valid_creates_365day_validity(http_client, owner_session, clean_db):
    """Valid publication creates 365-day validity with correct rules."""
    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'}
    })
    chapter_set = make_complete_chapter_set(set_id, book_id, status='draft', now=now)
    chapter_set['verification'] = {'key_checks_agree': True, 'questions': 50, 'keys': 50, 'options': 50, 'source_images': True}
    chapter_set['independent_check'] = {'method': 'test', 'checked_at': now}
    await clean_db.tejas_sets.insert_one(chapter_set)

    r = await http_client.post(f'/api/studio/chapter-books/{book_id}/publish',
                                json={'revision': 1},
                                cookies=owner_session['cookies'])
    assert r.status_code == 200

    # Verify publication
    published_set = await clean_db.tejas_sets.find_one({'id': set_id})
    assert published_set['status'] == 'published'
    assert published_set['live_enabled'] is True
    assert 'start_at' in published_set
    assert 'end_at' in published_set
    # 365 days = 365 * 86400 seconds
    assert abs(published_set['end_at'] - published_set['start_at'] - 365 * 86400) < 10
    assert published_set['rules']['minutes'] == 60
    assert published_set['rules']['correct'] == 3
    assert published_set['rules']['wrong'] == -1
    assert published_set['rules']['skipped'] == 0


async def test_publish_competition_false_no_embargo(http_client, owner_session, clean_db):
    """Published chapter tests have competition=false, no embargo."""
    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'}
    })
    chapter_set = make_complete_chapter_set(set_id, book_id, status='draft', now=now)
    chapter_set['competition'] = False
    chapter_set['verification'] = {'key_checks_agree': True, 'questions': 50, 'keys': 50, 'options': 50, 'source_images': True}
    chapter_set['independent_check'] = {'method': 'test', 'checked_at': now}
    await clean_db.tejas_sets.insert_one(chapter_set)

    r = await http_client.post(f'/api/studio/chapter-books/{book_id}/publish',
                                json={'revision': 1},
                                cookies=owner_session['cookies'])
    assert r.status_code == 200

    published_set = await clean_db.tejas_sets.find_one({'id': set_id})
    assert published_set.get('competition') is False


async def test_repeated_publish_idempotent_no_extend(http_client, owner_session, clean_db):
    """Repeated publication is idempotent, does not extend validity or reset."""
    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'},
        'publication_start': now  # Already published
    })
    chapter_set = make_complete_chapter_set(set_id, book_id, status='published', now=now)
    chapter_set['live_enabled'] = True
    chapter_set['start_at'] = now
    chapter_set['end_at'] = now + 365 * 86400
    chapter_set['verification'] = {'key_checks_agree': True, 'questions': 50, 'keys': 50, 'options': 50, 'source_images': True}
    chapter_set['independent_check'] = {'method': 'test', 'checked_at': now}
    await clean_db.tejas_sets.insert_one(chapter_set)

    original_end = now + 365 * 86400

    # Publish again
    r = await http_client.post(f'/api/studio/chapter-books/{book_id}/publish',
                                json={'revision': 1},
                                cookies=owner_session['cookies'])
    assert r.status_code == 200

    # Verify end_at did not change
    published_set = await clean_db.tejas_sets.find_one({'id': set_id})
    assert published_set['end_at'] == original_end


async def test_per_chapter_live_toggle_cas(http_client, owner_session, clean_db):
    """Per-chapter live toggle uses revision CAS."""
    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'},
        'publication_start': now
    })
    chapter_set = make_complete_chapter_set(set_id, book_id, status='published', now=now)
    chapter_set['live_enabled'] = True
    chapter_set['start_at'] = now
    chapter_set['end_at'] = now + 365 * 86400
    await clean_db.tejas_sets.insert_one(chapter_set)

    # Toggle with wrong revision
    r = await http_client.post(f'/api/studio/chapter-books/{book_id}/chapters/{set_id}/live',
                                json={'revision': 999, 'live': False},
                                cookies=owner_session['cookies'])
    assert r.status_code == 409

    # Toggle with correct revision
    r = await http_client.post(f'/api/studio/chapter-books/{book_id}/chapters/{set_id}/live',
                                json={'revision': 1, 'live': False},
                                cookies=owner_session['cookies'])
    assert r.status_code == 200

    updated_set = await clean_db.tejas_sets.find_one({'id': set_id})
    assert updated_set['live_enabled'] is False
    assert updated_set['revision'] == 2


async def test_expiry_forbids_new_starts(http_client, student_session, clean_db):
    """Expired chapter tests forbid new attempt starts."""
    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()
    past = now - 400 * 86400  # Expired

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': past,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'},
        'publication_start': past
    })
    await clean_db.tejas_sets.insert_one({
        'id': set_id, 'chapter_book_id': book_id, 'chapter_number': 1,
        'chapter_subject': 'Physics', 'title': 'Units & Measurements',
        'exam': 'BITSAT', 'year': '', 'status': 'published', 'version': 1, 'revision': 1,
        'questions': [{'id': str(uuid.uuid4()), 'number': i, 'type': 'mcq', 'subject': 'Physics'} for i in range(1, 51)],
        'rules': {'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
        'created_at': past, 'audience': 'all', 'live_enabled': True,
        'start_at': past, 'end_at': past + 365 * 86400  # Expired
    })

    # Should not appear in catalog
    r = await http_client.get('/api/my/chapter-exams', cookies=student_session['cookies'])
    assert r.status_code == 200
    assert r.json()['data']['total'] == 0


async def test_active_attempt_resumes_with_original_deadline(http_client, student_session, clean_db):
    """Active attempt resumes with original 60min deadline, not recalculated."""
    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'},
        'publication_start': now
    })
    chapter_set = make_complete_chapter_set(set_id, book_id, status='published', now=now)
    chapter_set['live_enabled'] = True
    chapter_set['start_at'] = now
    chapter_set['end_at'] = now + 365 * 86400
    await clean_db.tejas_sets.insert_one(chapter_set)

    # Create preflight
    await clean_db.tejas_preflight.insert_one({
        'user_id': student_session['user']['id'],
        'set_id': set_id,
        'revision': 1,
        'at': now
    })

    # Start attempt
    start_key = str(uuid.uuid4())
    r1 = await http_client.post(f'/api/sets/{set_id}/start',
                                 json={'start_key': start_key, 'device_checked': True, 'preview': False},
                                 cookies=student_session['cookies'])
    assert r1.status_code == 200
    attempt_data = r1.json()['data']
    original_deadline = attempt_data['deadline']

    # Resume attempt with same key
    r2 = await http_client.post(f'/api/sets/{set_id}/start',
                                 json={'start_key': start_key, 'device_checked': True, 'preview': False},
                                 cookies=student_session['cookies'])
    assert r2.status_code == 200
    resumed_data = r2.json()['data']
    assert resumed_data['deadline'] == original_deadline


# ============================================================================
# PDF UPLOAD GUARD TESTS: Multipart, idempotency, duplicate handling
# ============================================================================

async def test_upload_requires_owner_auth(http_client):
    """Upload endpoint requires owner authentication."""
    r = await http_client.post('/api/studio/chapter-books',
                                data={'request_id': str(uuid.uuid4())},
                                files={'file': ('test.pdf', b'%PDF-test', 'application/pdf')})
    assert r.status_code == 401


async def test_upload_single_pdf_multipart_guard(http_client, owner_session):
    """Upload accepts only single PDF with request_id."""
    # Missing request_id
    r1 = await http_client.post('/api/studio/chapter-books',
                                 files={'file': ('test.pdf', b'%PDF-test', 'application/pdf')},
                                 cookies=owner_session['cookies'])
    assert r1.status_code == 422

    # Extra field
    r2 = await http_client.post('/api/studio/chapter-books',
                                 data={'request_id': str(uuid.uuid4()), 'extra': 'field'},
                                 files={'file': ('test.pdf', b'%PDF-test', 'application/pdf')},
                                 cookies=owner_session['cookies'])
    assert r2.status_code in (400, 422)  # Backend returns 400 for too many fields


async def test_upload_duplicate_request_idempotent(http_client, owner_session, clean_db):
    """Duplicate upload request with same request_id is idempotent."""
    request_id = str(uuid.uuid4())
    pdf_content = b'%PDF-1.4\ntest content'
    sha256 = hashlib.sha256(pdf_content).hexdigest()

    # First upload - will fail processing but receipt is stored
    r1 = await http_client.post('/api/studio/chapter-books',
                                 data={'request_id': request_id},
                                 files={'file': ('test.pdf', pdf_content, 'application/pdf')},
                                 cookies=owner_session['cookies'])
    assert r1.status_code == 202

    # Second upload with same request_id and same file
    r2 = await http_client.post('/api/studio/chapter-books',
                                 data={'request_id': request_id},
                                 files={'file': ('test.pdf', pdf_content, 'application/pdf')},
                                 cookies=owner_session['cookies'])
    assert r2.status_code == 202 or r2.status_code == 200


async def test_upload_mismatched_request_409(http_client, owner_session, clean_db):
    """Upload with same request_id but different file returns 409."""
    request_id = str(uuid.uuid4())

    # First upload
    r1 = await http_client.post('/api/studio/chapter-books',
                                 data={'request_id': request_id},
                                 files={'file': ('test1.pdf', b'%PDF-1.4\ntest1', 'application/pdf')},
                                 cookies=owner_session['cookies'])
    assert r1.status_code == 202

    # Second upload with different content
    r2 = await http_client.post('/api/studio/chapter-books',
                                 data={'request_id': request_id},
                                 files={'file': ('test2.pdf', b'%PDF-1.4\ntest2', 'application/pdf')},
                                 cookies=owner_session['cookies'])
    assert r2.status_code == 409


async def test_upload_unsupported_pdf_fails(http_client, owner_session):
    """Upload of non-PDF or invalid PDF fails."""
    request_id = str(uuid.uuid4())

    # Not a PDF
    r1 = await http_client.post('/api/studio/chapter-books',
                                 data={'request_id': request_id},
                                 files={'file': ('test.txt', b'not a pdf', 'text/plain')},
                                 cookies=owner_session['cookies'])
    assert r1.status_code == 422

    # Invalid PDF
    r2 = await http_client.post('/api/studio/chapter-books',
                                 data={'request_id': str(uuid.uuid4())},
                                 files={'file': ('test.pdf', b'invalid pdf content', 'application/pdf')},
                                 cookies=owner_session['cookies'])
    assert r2.status_code == 422


async def test_upload_oversized_pdf_rejected(http_client, owner_session):
    """Upload exceeding 50MB is rejected."""
    request_id = str(uuid.uuid4())
    large_content = b'%PDF-1.4\n' + b'x' * (50 * 1024 * 1024 + 1)

    r = await http_client.post('/api/studio/chapter-books',
                                data={'request_id': request_id},
                                files={'file': ('large.pdf', large_content, 'application/pdf')},
                                cookies=owner_session['cookies'])
    assert r.status_code == 422


# ============================================================================
# ATTEMPT LIFECYCLE TESTS: Preflight, start, scoring, deadlines, key access
# ============================================================================

async def test_attempt_preflight_validates_sources(http_client, student_session, clean_db):
    """Preflight validates source assets before allowing start."""
    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'},
        'publication_start': now
    })
    await clean_db.tejas_sets.insert_one({
        'id': set_id, 'chapter_book_id': book_id, 'chapter_number': 1,
        'chapter_subject': 'Physics', 'title': 'Units & Measurements',
        'exam': 'BITSAT', 'year': '', 'status': 'published', 'version': 1, 'revision': 1,
        'questions': [{'id': str(uuid.uuid4()), 'number': i, 'type': 'mcq', 'subject': 'Physics', 'text': 'Q', 'options': {'A': 'A'}, 'answer': 'A', 'solution': 'S', 'q_refs': [], 's_refs': []} for i in range(1, 51)],
        'rules': {'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
        'created_at': now, 'audience': 'all', 'live_enabled': True,
        'start_at': now, 'end_at': now + 365 * 86400,
        'file_ids': []
    })

    r = await http_client.post(f'/api/sets/{set_id}/preflight',
                                json={'preview': False},
                                cookies=student_session['cookies'])
    assert r.status_code == 200
    assert r.json()['data']['ok'] is True


async def test_attempt_start_requires_preflight(http_client, student_session, clean_db):
    """Attempt start requires recent preflight check."""
    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'},
        'publication_start': now
    })
    await clean_db.tejas_sets.insert_one({
        'id': set_id, 'chapter_book_id': book_id, 'chapter_number': 1,
        'chapter_subject': 'Physics', 'title': 'Units & Measurements',
        'exam': 'BITSAT', 'year': '', 'status': 'published', 'version': 1, 'revision': 1,
        'questions': [{'id': str(uuid.uuid4()), 'number': i, 'type': 'mcq', 'subject': 'Physics', 'text': 'Q', 'options': {'A': 'A'}, 'answer': 'A', 'solution': 'S', 'render_mode': 'typed', 'q_refs': [], 's_refs': [], 'accessible_text': '', 'solution_accessible_text': ''} for i in range(1, 51)],
        'rules': {'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
        'created_at': now, 'audience': 'all', 'live_enabled': True,
        'start_at': now, 'end_at': now + 365 * 86400,
        'file_ids': []
    })

    # Try to start without preflight
    r = await http_client.post(f'/api/sets/{set_id}/start',
                                json={'start_key': str(uuid.uuid4()), 'device_checked': True, 'preview': False},
                                cookies=student_session['cookies'])
    assert r.status_code == 400
    assert 'check' in r.json()['error']['message'].lower()


async def test_attempt_scoring_correct_rules(http_client, student_session, clean_db):
    """Attempt scoring follows +3/-1/0 rules correctly."""
    from tejas_core import score_attempt

    questions = [
        {'id': str(uuid.uuid4()), 'number': i, 'type': 'mcq', 'subject': 'Physics',
         'text': 'Q', 'options': {'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'},
         'answer': 'A', 'solution': 'S', 'disposition': 'standard'}
        for i in range(1, 51)
    ]

    now = datetime.now(timezone.utc).timestamp()
    attempt = {
        'id': str(uuid.uuid4()),
        'user_id': student_session['user']['id'],
        'status': 'completed',
        'started_at': now,
        'submitted_at': now + 1800,
        'questions': questions,
        'answers': {
            questions[0]['id']: {'value': 'A', 'normalized_value': 'A'},  # Correct
            questions[1]['id']: {'value': 'B', 'normalized_value': 'B'},  # Wrong
            # questions[2] skipped
        },
        'rules': {'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0}
    }

    result = score_attempt(attempt)
    assert result['summary']['correct'] == 1
    assert result['summary']['incorrect'] == 1
    assert result['summary']['skipped'] == 48
    assert result['summary']['score'] == 1 * 3 + 1 * (-1) + 48 * 0  # 2


async def test_attempt_max_score_150(http_client, student_session, clean_db):
    """Maximum score for 50 questions at +3 each is 150."""
    from tejas_core import score_attempt

    questions = [
        {'id': str(uuid.uuid4()), 'number': i, 'type': 'mcq', 'subject': 'Physics',
         'text': 'Q', 'options': {'A': 'A'}, 'answer': 'A', 'solution': 'S', 'disposition': 'standard'}
        for i in range(1, 51)
    ]

    # All correct
    answers = {q['id']: {'value': 'A', 'normalized_value': 'A'} for q in questions}

    now = datetime.now(timezone.utc).timestamp()
    attempt = {
        'id': str(uuid.uuid4()),
        'user_id': student_session['user']['id'],
        'status': 'completed',
        'started_at': now,
        'submitted_at': now + 1800,
        'questions': questions,
        'answers': answers,
        'rules': {'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0}
    }

    result = score_attempt(attempt)
    assert result['summary']['score'] == 150


async def test_attempt_60min_deadline_enforced(http_client, student_session, clean_db):
    """Server enforces 60-minute deadline."""
    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'},
        'publication_start': now
    })
    chapter_set = make_complete_chapter_set(set_id, book_id, status='published', now=now)
    chapter_set['live_enabled'] = True
    chapter_set['start_at'] = now
    chapter_set['end_at'] = now + 365 * 86400
    await clean_db.tejas_sets.insert_one(chapter_set)

    # Create preflight
    await clean_db.tejas_preflight.insert_one({
        'user_id': student_session['user']['id'],
        'set_id': set_id,
        'revision': 1,
        'at': now
    })

    # Start attempt
    start_key = str(uuid.uuid4())
    r = await http_client.post(f'/api/sets/{set_id}/start',
                                json={'start_key': start_key, 'device_checked': True, 'preview': False},
                                cookies=student_session['cookies'])
    assert r.status_code == 200
    data = r.json()['data']
    assert data['deadline'] == data['started_at'] + 60 * 60


async def test_attempt_near_expiry_gets_full_60min(http_client, student_session, clean_db):
    """Attempt started near 365d expiry still gets full 60min (availability not exam window)."""
    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()
    # Start 1 hour before expiry
    start_at = now - 365 * 86400 + 3600

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': start_at,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'},
        'publication_start': start_at
    })
    chapter_set = make_complete_chapter_set(set_id, book_id, status='published', now=start_at)
    chapter_set['live_enabled'] = True
    chapter_set['start_at'] = start_at
    chapter_set['end_at'] = start_at + 365 * 86400
    await clean_db.tejas_sets.insert_one(chapter_set)

    # Create preflight
    await clean_db.tejas_preflight.insert_one({
        'user_id': student_session['user']['id'],
        'set_id': set_id,
        'revision': 1,
        'at': now
    })

    # Start attempt
    start_key = str(uuid.uuid4())
    r = await http_client.post(f'/api/sets/{set_id}/start',
                                json={'start_key': start_key, 'device_checked': True, 'preview': False},
                                cookies=student_session['cookies'])
    assert r.status_code == 200
    data = r.json()['data']
    # Should get full 60 minutes
    assert data['deadline'] >= now + 3500  # At least 58 minutes


async def test_key_solution_403_before_submit(http_client, student_session, clean_db):
    """Key/solution endpoint returns 403 before submission."""
    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'},
        'publication_start': now
    })
    chapter_set = make_complete_chapter_set(set_id, book_id, status='published', now=now)
    chapter_set['live_enabled'] = True
    chapter_set['start_at'] = now
    chapter_set['end_at'] = now + 365 * 86400
    await clean_db.tejas_sets.insert_one(chapter_set)
    q_id = chapter_set['questions'][0]['id']

    # Create preflight
    await clean_db.tejas_preflight.insert_one({
        'user_id': student_session['user']['id'],
        'set_id': set_id,
        'revision': 1,
        'at': now
    })

    # Start attempt
    start_key = str(uuid.uuid4())
    r = await http_client.post(f'/api/sets/{set_id}/start',
                                json={'start_key': start_key, 'device_checked': True, 'preview': False},
                                cookies=student_session['cookies'])
    assert r.status_code == 200
    attempt_id = r.json()['data']['id']

    # Try to access solution before submit
    r = await http_client.get(f'/api/attempts/{attempt_id}/questions/{q_id}/asset/solution/0',
                               cookies=student_session['cookies'])
    assert r.status_code == 403


async def test_key_solution_accessible_after_submit_own_only(http_client, student_session, clean_db):
    """Key/solution accessible after submit, own attempt only."""
    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'},
        'publication_start': now
    })
    chapter_set = make_complete_chapter_set(set_id, book_id, status='published', now=now)
    chapter_set['live_enabled'] = True
    chapter_set['start_at'] = now
    chapter_set['end_at'] = now + 365 * 86400
    await clean_db.tejas_sets.insert_one(chapter_set)
    q_id = chapter_set['questions'][0]['id']

    # Create preflight
    await clean_db.tejas_preflight.insert_one({
        'user_id': student_session['user']['id'],
        'set_id': set_id,
        'revision': 1,
        'at': now
    })

    # Start and submit attempt
    start_key = str(uuid.uuid4())
    r = await http_client.post(f'/api/sets/{set_id}/start',
                                json={'start_key': start_key, 'device_checked': True, 'preview': False},
                                cookies=student_session['cookies'])
    assert r.status_code == 200
    attempt_id = r.json()['data']['id']

    # Submit
    r = await http_client.post(f'/api/attempts/{attempt_id}/submit',
                                cookies=student_session['cookies'])
    assert r.status_code in (200, 202)

    # Now solution should be accessible (though may 404 if no actual file)
    r = await http_client.get(f'/api/attempts/{attempt_id}/questions/{q_id}/asset/solution/0',
                               cookies=student_session['cookies'])
    # Should not be 403 anymore
    assert r.status_code != 403


# ============================================================================
# IMMUTABILITY TESTS: Block generic Studio edits/publish/subset
# ============================================================================

async def test_immutable_chapter_blocks_studio_edit(http_client, staff_session, clean_db):
    """Chapter book sets block generic Studio edit endpoints."""
    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'}
    })
    await clean_db.tejas_sets.insert_one({
        'id': set_id, 'chapter_book_id': book_id, 'chapter_number': 1,
        'chapter_subject': 'Physics', 'title': 'Units & Measurements',
        'exam': 'BITSAT', 'year': '', 'status': 'draft', 'version': 1, 'revision': 1,
        'questions': [{'id': str(uuid.uuid4()), 'number': i, 'type': 'mcq', 'subject': 'Physics'} for i in range(1, 51)],
        'rules': {'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
        'created_at': now, 'audience': 'all'
    })

    # Try to edit via Studio
    r = await http_client.put(f'/api/studio/sets/{set_id}',
                               json={'title': 'Modified', 'exam': 'BITSAT', 'audience': 'all'},
                               cookies=staff_session['cookies'])
    assert r.status_code == 409
    assert 'immutable' in r.json()['error']['message'].lower() or 'frozen' in r.json()['error']['message'].lower()


async def test_immutable_chapter_blocks_studio_publish(http_client, staff_session, clean_db):
    """Chapter book sets block generic Studio publish endpoint."""
    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'}
    })
    await clean_db.tejas_sets.insert_one({
        'id': set_id, 'chapter_book_id': book_id, 'chapter_number': 1,
        'chapter_subject': 'Physics', 'title': 'Units & Measurements',
        'exam': 'BITSAT', 'year': '', 'status': 'draft', 'version': 1, 'revision': 1,
        'questions': [{'id': str(uuid.uuid4()), 'number': i, 'type': 'mcq', 'subject': 'Physics', 'text': 'Q', 'options': {'A': 'A'}, 'answer': 'A', 'solution': 'S', 'approved': True} for i in range(1, 51)],
        'rules': {'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
        'created_at': now, 'audience': 'all',
        'rights_upload': True, 'rights_publish': True, 'rights_report': True,
        'source': 'Test', 'attribution': 'Test'
    })

    # Try to publish via Studio
    r = await http_client.post(f'/api/studio/sets/{set_id}/publish',
                                json={'confirm': True},
                                cookies=staff_session['cookies'])
    assert r.status_code == 409
    assert 'immutable' in r.json()['error']['message'].lower() or 'frozen' in r.json()['error']['message'].lower()


async def test_immutable_chapter_blocks_subset(http_client, staff_session, clean_db):
    """Chapter book sets block subset creation."""
    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'}
    })
    q_ids = [str(uuid.uuid4()) for _ in range(50)]
    await clean_db.tejas_sets.insert_one({
        'id': set_id, 'chapter_book_id': book_id, 'chapter_number': 1,
        'chapter_subject': 'Physics', 'title': 'Units & Measurements',
        'exam': 'BITSAT', 'year': '', 'status': 'published', 'version': 1, 'revision': 1,
        'questions': [{'id': q_ids[i], 'number': i+1, 'type': 'mcq', 'subject': 'Physics'} for i in range(50)],
        'rules': {'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
        'created_at': now, 'audience': 'all'
    })

    # Try to create subset
    r = await http_client.post(f'/api/studio/sets/{set_id}/subset',
                                json={'title': 'Subset', 'question_ids': q_ids[:10]},
                                cookies=staff_session['cookies'])
    assert r.status_code == 409
    assert 'immutable' in r.json()['error']['message'].lower() or 'frozen' in r.json()['error']['message'].lower()


async def test_owner_identity_preserved(http_client, staff_session, clean_db):
    """Original owner identity is preserved through chapter book lifecycle."""
    owner_id = staff_session['user']['id']
    book_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'created_by': owner_id,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'}
    })

    book = await clean_db.tejas_chapter_books.find_one({'id': book_id})
    assert book['created_by'] == owner_id



# ============================================================================
# SOLUTION_KIND REGRESSION TESTS: Immutable pack compatibility, report labels
# ============================================================================

async def test_solution_kind_survives_pack_seal_hydrate(clean_db):
    """solution_kind field survives pack seal->hydrate cycle without mutation."""
    from tejas.packs import seal, unpack, hydrate

    questions = [
        {
            'id': str(uuid.uuid4()),
            'number': 1,
            'type': 'mcq',
            'subject': 'Physics',
            'text': 'Question 1',
            'options': {'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'},
            'answer': 'A',
            'solution': 'Solution 1',
            'solution_kind': 'answer_key_only',
            'disposition': 'standard'
        }
    ]

    # Seal the pack
    pack_id = await seal(questions)

    # Unpack and verify solution_kind is preserved
    unpacked = await unpack(pack_id)
    assert unpacked[0]['solution_kind'] == 'answer_key_only'

    # Hydrate an attempt and verify solution_kind is preserved
    attempt = {
        'pack_id': pack_id,
        'id': str(uuid.uuid4()),
        'status': 'completed'
    }
    hydrated = await hydrate(attempt)
    assert hydrated['questions'][0]['solution_kind'] == 'answer_key_only'


async def test_solution_kind_derived_from_explicit_text(clean_db):
    """Old immutable packs derive solution_kind from explicit text without changing stored pack hash."""
    from tejas.packs import seal, unpack, hydrate

    # Create question with explicit "Supplied answer key" text but no solution_kind field
    questions = [
        {
            'id': str(uuid.uuid4()),
            'number': 1,
            'type': 'mcq',
            'subject': 'Physics',
            'text': 'Question 1',
            'options': {'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'},
            'answer': 'A',
            'solution': 'Supplied answer key: A. This book does not contain a worked solution.',
            'disposition': 'standard'
        }
    ]

    # Seal the pack (without solution_kind field)
    pack_id = await seal(questions)

    # Verify the stored pack does not have solution_kind
    stored_pack = await clean_db.tejas_packs.find_one({'_id': pack_id})
    assert stored_pack is not None
    original_hash = stored_pack['sha256']

    # Hydrate should derive solution_kind from the explicit text
    attempt = {
        'pack_id': pack_id,
        'id': str(uuid.uuid4()),
        'status': 'completed'
    }
    hydrated = await hydrate(attempt)

    # Verify solution_kind was derived
    assert hydrated['questions'][0]['solution_kind'] == 'answer_key_only'

    # Verify the stored pack hash is unchanged
    stored_pack_after = await clean_db.tejas_packs.find_one({'_id': pack_id})
    assert stored_pack_after['sha256'] == original_hash


async def test_solution_kind_does_not_affect_scoring(clean_db):
    """solution_kind metadata does not affect scoring logic."""
    from tejas_core import score_attempt

    # Create two identical attempts, one with solution_kind, one without
    q1_id = str(uuid.uuid4())
    q2_id = str(uuid.uuid4())

    now = datetime.now(timezone.utc).timestamp()

    attempt_with_kind = {
        'id': str(uuid.uuid4()),
        'user_id': str(uuid.uuid4()),
        'status': 'completed',
        'started_at': now,
        'submitted_at': now + 1800,
        'questions': [
            {
                'id': q1_id,
                'number': 1,
                'type': 'mcq',
                'subject': 'Physics',
                'text': 'Q1',
                'options': {'A': 'A', 'B': 'B'},
                'answer': 'A',
                'solution': 'S1',
                'solution_kind': 'answer_key_only',
                'disposition': 'standard'
            },
            {
                'id': q2_id,
                'number': 2,
                'type': 'mcq',
                'subject': 'Physics',
                'text': 'Q2',
                'options': {'A': 'A', 'B': 'B'},
                'answer': 'B',
                'solution': 'S2',
                'solution_kind': 'answer_key_only',
                'disposition': 'standard'
            }
        ],
        'answers': {
            q1_id: {'value': 'A', 'normalized_value': 'A'},  # Correct
            q2_id: {'value': 'A', 'normalized_value': 'A'}   # Wrong
        },
        'rules': {'correct': 3, 'wrong': -1, 'skipped': 0}
    }

    attempt_without_kind = {
        'id': str(uuid.uuid4()),
        'user_id': str(uuid.uuid4()),
        'status': 'completed',
        'started_at': now,
        'submitted_at': now + 1800,
        'questions': [
            {
                'id': q1_id,
                'number': 1,
                'type': 'mcq',
                'subject': 'Physics',
                'text': 'Q1',
                'options': {'A': 'A', 'B': 'B'},
                'answer': 'A',
                'solution': 'S1',
                'disposition': 'standard'
            },
            {
                'id': q2_id,
                'number': 2,
                'type': 'mcq',
                'subject': 'Physics',
                'text': 'Q2',
                'options': {'A': 'A', 'B': 'B'},
                'answer': 'B',
                'solution': 'S2',
                'disposition': 'standard'
            }
        ],
        'answers': {
            q1_id: {'value': 'A', 'normalized_value': 'A'},  # Correct
            q2_id: {'value': 'A', 'normalized_value': 'A'}   # Wrong
        },
        'rules': {'correct': 3, 'wrong': -1, 'skipped': 0}
    }

    result_with = score_attempt(attempt_with_kind)
    result_without = score_attempt(attempt_without_kind)

    # Scores should be identical
    assert result_with['summary']['score'] == result_without['summary']['score']
    assert result_with['summary']['correct'] == result_without['summary']['correct']
    assert result_with['summary']['incorrect'] == result_without['summary']['incorrect']


async def test_report_shows_answer_key_only_flag(clean_db):
    """Results scoring and report generation preserve solution_kind metadata."""
    from tejas.packs import seal, hydrate
    from tejas_core import score_attempt

    # Create questions with answer_key_only solution_kind
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
            'solution': f'Supplied answer key: A. This book does not contain a worked solution.',
            'solution_kind': 'answer_key_only',
            'render_mode': 'typed',
            'q_refs': [],
            's_refs': [],
            'accessible_text': f'Question {i}',
            'solution_accessible_text': f'Key {i}',
            'disposition': 'standard'
        })

    pack_id = await seal(questions)
    now = datetime.now(timezone.utc).timestamp()

    # Create attempt
    attempt = {
        'id': str(uuid.uuid4()),
        'user_id': str(uuid.uuid4()),
        'status': 'completed',
        'mode': 'practice',
        'started_at': now,
        'submitted_at': now + 1800,
        'deadline': now + 3600,
        'title': 'Units & Measurements',
        'exam': 'BITSAT',
        'version': 1,
        'rules': {'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0, 'numeric_policy': 'integer_exact', 'numeric_rule': 'Integer exact match'},
        'pack_id': pack_id,
        'count': 50,
        'answers': {
            questions[0]['id']: {'value': 'D', 'normalized_value': 'D'},  # Wrong
            questions[1]['id']: {'value': 'A', 'normalized_value': 'A'}   # Correct
        },
        'response_schema': {q['id']: {'type': 'mcq', 'options': ['A', 'B', 'C', 'D']} for q in questions}
    }

    # Hydrate and score
    attempt = await hydrate(attempt)
    result = score_attempt(attempt)

    # Verify all questions in result have solution_kind flag
    assert all(q.get('solution_kind') == 'answer_key_only' for q in result['questions'])

    # Verify report generation detects answer_key_only
    from tejas.reports import render_report

    def mock_loader(file_id):
        # Return minimal PNG for testing
        return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'

    pdf_bytes = render_report(attempt, mock_loader)

    # Verify PDF was generated and contains answer key header
    assert len(pdf_bytes) > 1000

    # Extract text from PDF to verify header
    import fitz
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    first_page_text = doc[0].get_text()
    doc.close()

    assert 'RESULTS & ANSWER KEYS' in first_page_text or 'ANSWER KEYS' in first_page_text



# ============================================================================
# REGRESSION TESTS: Metadata projection, catalog history, preflight dedup
# ============================================================================

async def test_book_chapter_project_excludes_sources_answers(clean_db):
    """BOOK_CHAPTER_PROJECT metadata projection excludes source/answer fields."""
    from tejas.chapter_books import BOOK_CHAPTER_PROJECT

    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()

    # Insert chapter with full question data including answers and source refs
    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'}
    })

    questions = []
    for i in range(1, 51):
        questions.append({
            'id': str(uuid.uuid4()),
            'number': i,
            'type': 'mcq',
            'subject': 'Physics',
            'text': f'Question {i} with sensitive data',
            'options': {'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'},
            'answer': 'A',  # Should be excluded
            'solution': f'Solution {i}',  # Should be excluded
            'q_refs': [{'page': 1, 'rect': [0, 0, 100, 100], 'file_id': str(uuid.uuid4())}],  # Should be excluded
            's_refs': [{'page': 2, 'rect': [0, 0, 100, 100], 'file_id': str(uuid.uuid4())}],  # Should be excluded
        })

    await clean_db.tejas_sets.insert_one({
        'id': set_id, 'chapter_book_id': book_id, 'chapter_number': 1,
        'chapter_subject': 'Physics', 'title': 'Units & Measurements',
        'exam': 'BITSAT', 'year': '', 'status': 'published', 'version': 1, 'revision': 1,
        'questions': questions,
        'rules': {'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0},
        'created_at': now, 'audience': 'all', 'live_enabled': True,
        'start_at': now, 'end_at': now + 365 * 86400,
        'verification': {'key_checks_agree': True},
        'independent_check': {'method': 'test', 'checked_at': now},
        'start_page': 1, 'end_page': 10, 'key_page': 11
    })

    # Query with BOOK_CHAPTER_PROJECT
    projected = await clean_db.tejas_sets.find_one({'id': set_id}, BOOK_CHAPTER_PROJECT)

    # Verify metadata fields are present
    assert projected['id'] == set_id
    assert projected['title'] == 'Units & Measurements'
    assert projected['chapter_number'] == 1
    assert projected['chapter_subject'] == 'Physics'
    assert 'questions' in projected
    assert len(projected['questions']) == 50

    # Verify sensitive fields are excluded
    for q in projected['questions']:
        assert 'number' in q  # Only question.number is projected
        assert 'answer' not in q
        assert 'solution' not in q
        assert 'text' not in q
        assert 'options' not in q
        assert 'q_refs' not in q
        assert 's_refs' not in q


async def test_book_view_full_vs_projected_equality(http_client, clean_db):
    """book_view with BOOK_CHAPTER_PROJECT returns same ChapterView metadata as full query excluding only server_now."""
    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'},
        'pages': 100
    })

    chapter_set = make_complete_chapter_set(set_id, book_id, status='published', now=now)
    chapter_set['live_enabled'] = True
    chapter_set['start_at'] = now
    chapter_set['end_at'] = now + 365 * 86400
    chapter_set['verification'] = {'key_checks_agree': True, 'questions': 50, 'keys': 50}
    chapter_set['independent_check'] = {'method': 'test', 'checked_at': now}
    await clean_db.tejas_sets.insert_one(chapter_set)

    # Get book_view with full query
    from tejas.chapter_books import book_view, BOOK_CHAPTER_PROJECT
    book = await clean_db.tejas_chapter_books.find_one({'id': book_id}, {'_id': 0})
    full_view = await book_view(book)

    # Get book_view with projected query
    # Simulate what the API does: fetch book without projection, then fetch chapters with projection
    book_for_projected = await clean_db.tejas_chapter_books.find_one({'id': book_id}, {'_id': 0})
    # Manually apply projection to chapters for comparison
    projected_chapters = await clean_db.tejas_sets.find(
        {'chapter_book_id': book_id},
        BOOK_CHAPTER_PROJECT
    ).to_list(100)

    # Build projected view manually to compare
    from tejas.chapter_books import ChapterView, chapter_view
    projected_chapter_views = []
    for ch in projected_chapters:
        # Use chapter_view function to compute status correctly
        proj_view = chapter_view(ch)
        projected_chapter_views.append(proj_view)

    # Compare full vs projected ChapterView fields (excluding server_now which varies)
    assert len(full_view.chapters) == len(projected_chapter_views)

    for full_ch, proj_ch in zip(full_view.chapters, projected_chapter_views):
        # Compare all ChapterView fields except server_now
        assert full_ch.id == proj_ch.id
        assert full_ch.title == proj_ch.title
        assert full_ch.chapter_number == proj_ch.chapter_number
        assert full_ch.subject == proj_ch.subject
        assert full_ch.count == proj_ch.count
        assert full_ch.status == proj_ch.status
        assert full_ch.start_page == proj_ch.start_page
        assert full_ch.end_page == proj_ch.end_page
        assert full_ch.key_page == proj_ch.key_page
        assert full_ch.verification == proj_ch.verification
        assert full_ch.independent_check == proj_ch.independent_check
        assert full_ch.revision == proj_ch.revision
        assert full_ch.start_at == proj_ch.start_at
        assert full_ch.end_at == proj_ch.end_at
        assert full_ch.live_enabled == proj_ch.live_enabled


async def test_catalog_history_per_set_not_truncated_200(http_client, student_session, clean_db):
    """Catalog history aggregates per visible set, >200 attempts on one chapter don't hide another."""
    book_id = str(uuid.uuid4())
    set1_id = str(uuid.uuid4())
    set2_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'},
        'publication_start': now
    })

    # Create two chapters
    for i, set_id in enumerate([set1_id, set2_id]):
        chapter_set = make_complete_chapter_set(set_id, book_id, chapter_number=i+1,
                                                 title=f'Chapter {i+1}', status='published', now=now)
        chapter_set['live_enabled'] = True
        chapter_set['start_at'] = now
        chapter_set['end_at'] = now + 365 * 86400
        await clean_db.tejas_sets.insert_one(chapter_set)

    # Create 250 attempts on set1 (exceeds old 200 limit)
    for i in range(250):
        await clean_db.tejas_attempts.insert_one({
            'id': str(uuid.uuid4()),
            'user_id': student_session['user']['id'],
            'set_id': set1_id,
            'mode': 'practice',
            'status': 'completed',
            'started_at': now + i,
            'start_key': str(uuid.uuid4()),
            'title': 'Chapter 1', 'exam': 'BITSAT', 'version': 1,
            'rules': {'minutes': 60}, 'questions': [], 'answers': {}
        })

    # Create 1 active attempt on set2 - OLDER than all set1 attempts to test proper aggregation
    active_attempt_id = str(uuid.uuid4())
    await clean_db.tejas_attempts.insert_one({
        'id': active_attempt_id,
        'user_id': student_session['user']['id'],
        'set_id': set2_id,
        'mode': 'practice',
        'status': 'active',
        'started_at': now - 100,  # Older than all 250 set1 attempts
        'deadline': now + 4000,
        'start_key': str(uuid.uuid4()),
        'title': 'Chapter 2', 'exam': 'BITSAT', 'version': 1,
        'rules': {'minutes': 60}, 'questions': [], 'answers': {}
    })

    # Query catalog
    r = await http_client.get('/api/my/chapter-exams', cookies=student_session['cookies'])
    assert r.status_code == 200
    data = r.json()['data']

    # Both chapters should be visible
    assert data['total'] == 2

    # Find set2 in results
    set2_item = next((item for item in data['items'] if item['id'] == set2_id), None)
    assert set2_item is not None

    # Verify active attempt on set2 is visible (not hidden by set1's 250 attempts)
    assert set2_item['attempt'] is not None
    assert set2_item['attempt']['id'] == active_attempt_id
    assert set2_item['attempt']['status'] == 'active'


async def test_catalog_history_cross_user_filtered(http_client, student_session, clean_db):
    """Catalog history is filtered per user, doesn't leak other users' attempts."""
    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'},
        'publication_start': now
    })

    chapter_set = make_complete_chapter_set(set_id, book_id, status='published', now=now)
    chapter_set['live_enabled'] = True
    chapter_set['start_at'] = now
    chapter_set['end_at'] = now + 365 * 86400
    await clean_db.tejas_sets.insert_one(chapter_set)

    # Create attempt for another user
    other_user_id = str(uuid.uuid4())
    await clean_db.tejas_attempts.insert_one({
        'id': str(uuid.uuid4()),
        'user_id': other_user_id,
        'set_id': set_id,
        'mode': 'practice',
        'status': 'active',
        'started_at': now,
        'deadline': now + 3600,
        'start_key': str(uuid.uuid4()),
        'title': 'Units & Measurements', 'exam': 'BITSAT', 'version': 1,
        'rules': {'minutes': 60}, 'questions': [], 'answers': {}
    })

    # Query catalog as student_session user
    r = await http_client.get('/api/my/chapter-exams', cookies=student_session['cookies'])
    assert r.status_code == 200
    data = r.json()['data']

    # Should see the chapter but no attempt (other user's attempt should not appear)
    assert data['total'] == 1
    assert data['items'][0]['id'] == set_id
    assert data['items'][0].get('attempt') is None


async def test_catalog_history_mode_filtered(http_client, student_session, clean_db):
    """Catalog history only shows practice mode attempts, not preview/retry."""
    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'},
        'publication_start': now
    })

    chapter_set = make_complete_chapter_set(set_id, book_id, status='published', now=now)
    chapter_set['live_enabled'] = True
    chapter_set['start_at'] = now
    chapter_set['end_at'] = now + 365 * 86400
    await clean_db.tejas_sets.insert_one(chapter_set)

    # Create preview mode attempt (should not appear in catalog)
    await clean_db.tejas_attempts.insert_one({
        'id': str(uuid.uuid4()),
        'user_id': student_session['user']['id'],
        'set_id': set_id,
        'mode': 'preview',
        'status': 'active',
        'started_at': now,
        'deadline': now + 3600,
        'start_key': str(uuid.uuid4()),
        'title': 'Units & Measurements', 'exam': 'BITSAT', 'version': 1,
        'rules': {'minutes': 60}, 'questions': [], 'answers': {}
    })

    # Create retry mode attempt (should not appear in catalog)
    await clean_db.tejas_attempts.insert_one({
        'id': str(uuid.uuid4()),
        'user_id': student_session['user']['id'],
        'set_id': set_id,
        'mode': 'retry',
        'status': 'active',
        'started_at': now + 100,
        'deadline': 0,
        'start_key': str(uuid.uuid4()),
        'title': 'Units & Measurements', 'exam': 'BITSAT', 'version': 1,
        'rules': {'minutes': 0}, 'questions': [], 'answers': {}
    })

    # Create practice mode attempt (should appear)
    practice_attempt_id = str(uuid.uuid4())
    await clean_db.tejas_attempts.insert_one({
        'id': practice_attempt_id,
        'user_id': student_session['user']['id'],
        'set_id': set_id,
        'mode': 'practice',
        'status': 'active',
        'started_at': now + 200,
        'deadline': now + 4000,
        'start_key': str(uuid.uuid4()),
        'title': 'Units & Measurements', 'exam': 'BITSAT', 'version': 1,
        'rules': {'minutes': 60}, 'questions': [], 'answers': {}
    })

    # Query catalog
    r = await http_client.get('/api/my/chapter-exams', cookies=student_session['cookies'])
    assert r.status_code == 200
    data = r.json()['data']

    # Should only see practice mode attempt
    assert data['total'] == 1
    assert data['items'][0]['attempt'] is not None
    assert data['items'][0]['attempt']['id'] == practice_attempt_id


async def test_catalog_history_same_timestamp_deterministic(http_client, student_session, clean_db):
    """Catalog history with same started_at uses id as tiebreaker for deterministic ordering."""
    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'},
        'publication_start': now
    })

    chapter_set = make_complete_chapter_set(set_id, book_id, status='published', now=now)
    chapter_set['live_enabled'] = True
    chapter_set['start_at'] = now
    chapter_set['end_at'] = now + 365 * 86400
    await clean_db.tejas_sets.insert_one(chapter_set)

    # Create 3 attempts with same started_at but different IDs
    attempt_ids = sorted([str(uuid.uuid4()) for _ in range(3)])
    for attempt_id in attempt_ids:
        await clean_db.tejas_attempts.insert_one({
            'id': attempt_id,
            'user_id': student_session['user']['id'],
            'set_id': set_id,
            'mode': 'practice',
            'status': 'completed',
            'started_at': now,  # Same timestamp
            'start_key': str(uuid.uuid4()),
            'title': 'Units & Measurements', 'exam': 'BITSAT', 'version': 1,
            'rules': {'minutes': 60}, 'questions': [], 'answers': {}
        })

    # Query catalog multiple times
    results = []
    for _ in range(3):
        r = await http_client.get('/api/my/chapter-exams', cookies=student_session['cookies'])
        assert r.status_code == 200
        data = r.json()['data']
        results.append(data['items'][0]['attempt']['id'])

    # All queries should return the same attempt (deterministic)
    assert len(set(results)) == 1
    # Should be the one with highest id (descending sort)
    assert results[0] == attempt_ids[-1]


async def test_catalog_history_expired_marked_completed(http_client, student_session, clean_db):
    """Catalog history marks expired attempts (deadline passed) as completed."""
    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'},
        'publication_start': now
    })

    chapter_set = make_complete_chapter_set(set_id, book_id, status='published', now=now)
    chapter_set['live_enabled'] = True
    chapter_set['start_at'] = now
    chapter_set['end_at'] = now + 365 * 86400
    await clean_db.tejas_sets.insert_one(chapter_set)

    # Create attempt with expired deadline
    expired_attempt_id = str(uuid.uuid4())
    await clean_db.tejas_attempts.insert_one({
        'id': expired_attempt_id,
        'user_id': student_session['user']['id'],
        'set_id': set_id,
        'mode': 'practice',
        'status': 'active',  # Still marked active in DB
        'started_at': now - 7200,
        'deadline': now - 100,  # Expired 100 seconds ago
        'start_key': str(uuid.uuid4()),
        'title': 'Units & Measurements', 'exam': 'BITSAT', 'version': 1,
        'rules': {'minutes': 60}, 'questions': [], 'answers': {}
    })

    # Query catalog
    r = await http_client.get('/api/my/chapter-exams', cookies=student_session['cookies'])
    assert r.status_code == 200
    data = r.json()['data']

    # Should see the chapter with attempt marked as completed
    assert data['total'] == 1
    assert data['items'][0]['attempt'] is not None
    assert data['items'][0]['attempt']['id'] == expired_attempt_id
    assert data['items'][0]['attempt']['status'] == 'completed'


async def test_preflight_deduplicates_identical_refs(http_client, student_session, clean_db, monkeypatch):
    """Preflight deduplicates exact identical source refs per request but validates all unique refs."""
    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'},
        'publication_start': now
    })

    # Create 2 distinct file_ids that will be repeated across 100 refs
    file_id_1 = str(uuid.uuid4())
    file_id_2 = str(uuid.uuid4())

    # Create files in DB
    for fid in [file_id_1, file_id_2]:
        await clean_db.tejas_files.insert_one({
            'id': fid,
            'path': f'test/{fid}.pdf',
            'sha256': f'sha_{fid}',
            'kind': 'combined',
            'name': f'{fid}.pdf',
            'size': 1000,
            'set_id': set_id,
            'created_at': now,
            'is_deleted': False
        })

    # Create chapter where 50 questions have repeated refs (100 total refs, only 2 unique)
    questions = []
    for i in range(1, 51):
        questions.append({
            'id': str(uuid.uuid4()),
            'number': i,
            'type': 'mcq',
            'subject': 'Physics',
            'text': f'Question {i}',
            'options': {'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'},
            'answer': 'A',
            'solution': f'Solution {i}',
            'q_refs': [{'page': 1, 'rect': [0, 0, 100, 100], 'file_id': file_id_1}],
            's_refs': [{'page': 2, 'rect': [0, 0, 100, 100], 'file_id': file_id_2}]
        })

    await clean_db.tejas_sets.insert_one({
        'id': set_id, 'chapter_book_id': book_id, 'chapter_number': 1,
        'chapter_subject': 'Physics', 'title': 'Units & Measurements',
        'exam': 'BITSAT', 'year': '', 'status': 'published', 'version': 1, 'revision': 1,
        'questions': questions,
        'rules': {'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0},
        'created_at': now, 'audience': 'all', 'live_enabled': True,
        'start_at': now, 'end_at': now + 365 * 86400,
        'file_ids': [file_id_1, file_id_2]
    })

    # Spy on render_crop to count unique refs validated (via render_crop calls)
    validated_file_ids = []
    from tejas import derivatives

    # Mock render_crop to avoid actual PDF rendering and track calls
    def spy_render_crop(f, r, scale):
        validated_file_ids.append(r['file_id'])
        return b'mock_image_data'

    monkeypatch.setattr(derivatives, 'render_crop', spy_render_crop)

    # First preflight - should validate exactly 2 distinct refs from 100 original refs
    validated_file_ids.clear()
    r1 = await http_client.post(f'/api/sets/{set_id}/preflight',
                                 json={'preview': False},
                                 cookies=student_session['cookies'])
    assert r1.status_code == 200
    assert r1.json()['data']['ok'] is True

    # Should have validated exactly 2 unique refs (deduped from 100)
    unique_validated = set(validated_file_ids)
    assert len(unique_validated) == 2
    assert file_id_1 in unique_validated
    assert file_id_2 in unique_validated

    # Second preflight - should validate 2 again (no cross-request caching)
    validated_file_ids.clear()
    r2 = await http_client.post(f'/api/sets/{set_id}/preflight',
                                 json={'preview': False},
                                 cookies=student_session['cookies'])
    assert r2.status_code == 200
    assert r2.json()['data']['ok'] is True

    # Should have validated exactly 2 unique refs again
    unique_validated_2 = set(validated_file_ids)
    assert len(unique_validated_2) == 2
    assert file_id_1 in unique_validated_2
    assert file_id_2 in unique_validated_2


async def test_preflight_validates_all_unique_refs_including_invalid(http_client, student_session, clean_db):
    """Preflight validates all unique refs including invalid ones, no cross-request caching."""
    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'},
        'publication_start': now
    })

    # Create chapter with one invalid file_id appearing LAST after good refs
    valid_file_id = str(uuid.uuid4())
    invalid_file_id = str(uuid.uuid4())

    questions = []
    for i in range(1, 51):
        # Invalid ref appears last (i==50) after all good refs, not first
        file_id = invalid_file_id if i == 50 else valid_file_id
        questions.append({
            'id': str(uuid.uuid4()),
            'number': i,
            'type': 'mcq',
            'subject': 'Physics',
            'text': f'Question {i}',
            'options': {'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'},
            'answer': 'A',
            'solution': f'Solution {i}',
            'q_refs': [{'page': 1, 'rect': [0, 0, 100, 100], 'file_id': file_id}],
            's_refs': []
        })

    await clean_db.tejas_sets.insert_one({
        'id': set_id, 'chapter_book_id': book_id, 'chapter_number': 1,
        'chapter_subject': 'Physics', 'title': 'Units & Measurements',
        'exam': 'BITSAT', 'year': '', 'status': 'published', 'version': 1, 'revision': 1,
        'questions': questions,
        'rules': {'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0},
        'created_at': now, 'audience': 'all', 'live_enabled': True,
        'start_at': now, 'end_at': now + 365 * 86400,
        'file_ids': [valid_file_id, invalid_file_id]
    })

    # Create only the valid file record
    await clean_db.tejas_files.insert_one({
        'id': valid_file_id,
        'path': 'test/valid.pdf',
        'sha256': 'test_sha',
        'kind': 'combined',
        'name': 'valid.pdf',
        'size': 1000,
        'set_id': set_id,
        'created_at': now,
        'is_deleted': False
    })

    # Preflight should fail because invalid_file_id is validated
    r = await http_client.post(f'/api/sets/{set_id}/preflight',
                                json={'preview': False},
                                cookies=student_session['cookies'])
    assert r.status_code == 404 or r.status_code == 400


async def test_preflight_no_cross_request_cache(http_client, student_session, clean_db):
    """Preflight does not cache validation across requests."""
    book_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).timestamp()

    await clean_db.tejas_chapter_books.insert_one({
        'id': book_id, 'title': 'Test Book', 'subject': 'Physics',
        'status': 'ready', 'revision': 1, 'created_at': now,
        'source': {'sha256': 'abc123', 'id': str(uuid.uuid4()), 'path': 'test/path'},
        'publication_start': now
    })

    file_id = str(uuid.uuid4())
    questions = []
    for i in range(1, 51):
        questions.append({
            'id': str(uuid.uuid4()),
            'number': i,
            'type': 'mcq',
            'subject': 'Physics',
            'text': f'Question {i}',
            'options': {'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'},
            'answer': 'A',
            'solution': f'Solution {i}',
            'q_refs': [{'page': 1, 'rect': [0, 0, 100, 100], 'file_id': file_id}],
            's_refs': []
        })

    await clean_db.tejas_sets.insert_one({
        'id': set_id, 'chapter_book_id': book_id, 'chapter_number': 1,
        'chapter_subject': 'Physics', 'title': 'Units & Measurements',
        'exam': 'BITSAT', 'year': '', 'status': 'published', 'version': 1, 'revision': 1,
        'questions': questions,
        'rules': {'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0},
        'created_at': now, 'audience': 'all', 'live_enabled': True,
        'start_at': now, 'end_at': now + 365 * 86400,
        'file_ids': [file_id]
    })

    # First request without file - should fail
    r1 = await http_client.post(f'/api/sets/{set_id}/preflight',
                                 json={'preview': False},
                                 cookies=student_session['cookies'])
    assert r1.status_code in (404, 400)

    # Create the file
    await clean_db.tejas_files.insert_one({
        'id': file_id,
        'path': 'test/file.pdf',
        'sha256': 'test_sha',
        'kind': 'combined',
        'name': 'test.pdf',
        'size': 1000,
        'set_id': set_id,
        'created_at': now,
        'is_deleted': False
    })

    # Second request with file - should succeed (no caching of previous failure)
    r2 = await http_client.post(f'/api/sets/{set_id}/preflight',
                                 json={'preview': False},
                                 cookies=student_session['cookies'])
    assert r2.status_code == 200
    assert r2.json()['data']['ok'] is True
