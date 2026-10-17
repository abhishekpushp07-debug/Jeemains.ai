"""Real behavioral tests for staff credential generation fencing.

Tests actual rotation primitive, bcrypt verification, atomic CAS, session revocation,
concurrent rotation conflicts, cleanup failures, and boundary violations.
No app code or dependency edits. Uses isolated test DB from conftest.
"""
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import pytest
import pytest_asyncio
from pymongo.errors import PyMongoError

pytestmark = pytest.mark.asyncio(loop_scope='session')


@pytest_asyncio.fixture(loop_scope='session')
async def staff_account_with_password(clean_db):
    """Create a synthetic staff account with known password and generation 0."""
    from tejas.db import users
    from tejas.auth import hashpw
    
    account_id = str(uuid.uuid4())
    password = 'InitialStaffPassword123!'
    hashed = await asyncio.get_event_loop().run_in_executor(None, hashpw, password)
    
    await users.insert_one({
        'id': account_id,
        'email': 'staff-rotation-test@isolated.invalid',
        'name': 'Rotation Test Staff',
        'role': 'reviewer',
        'exam': 'JEE Main',
        'access_type': 'staff_password',
        'password_hash': hashed,
        'credential_generation': 0,
        'created_at': datetime.now(timezone.utc),
    })
    
    return {'id': account_id, 'password': password, 'generation': 0, 'hash': hashed}


@pytest_asyncio.fixture(loop_scope='session')
async def owner_account_with_password(clean_db):
    """Create a synthetic owner account with known password and generation 0."""
    from tejas.db import users
    from tejas.auth import hashpw
    
    account_id = str(uuid.uuid4())
    password = 'OwnerInitialPassword456!'
    hashed = await asyncio.get_event_loop().run_in_executor(None, hashpw, password)
    
    await users.insert_one({
        'id': account_id,
        'email': 'owner-rotation-test@isolated.invalid',
        'name': 'Rotation Test Owner',
        'role': 'owner',
        'exam': 'JEE Main',
        'access_type': 'staff_password',
        'password_hash': hashed,
        'credential_generation': 0,
        'created_at': datetime.now(timezone.utc),
    })
    
    return {'id': account_id, 'password': password, 'generation': 0, 'hash': hashed}


async def test_basic_rotation_gen0_to_gen1(staff_account_with_password, clean_db):
    """Test basic rotation from generation 0 to 1 with real bcrypt verification."""
    from tejas.staff_credentials import rotate_staff_credential
    from tejas.db import users
    
    account = staff_account_with_password
    new_password = 'NewRotatedPassword789!'
    operation_id = str(uuid.uuid4())
    
    # Perform rotation
    receipt = await rotate_staff_credential(
        account['id'], 
        account['generation'], 
        new_password, 
        operation_id
    )
    
    # Verify receipt structure
    assert receipt.operation_id == operation_id
    assert receipt.account_id == account['id']
    assert receipt.prior_generation == 0
    assert receipt.new_generation == 1
    assert receipt.logical_session_revocation == 'COMMITTED'
    assert receipt.physical_cleanup == 'COMPLETE'
    assert type(receipt.deleted_session_count) is int
    
    # Verify no secrets in receipt
    receipt_dict = receipt.model_dump()
    receipt_json = receipt.model_dump_json()
    assert new_password not in receipt_json
    assert 'password' not in receipt_dict
    assert 'hash' not in receipt_dict
    assert 'token' not in receipt_dict
    assert 'email' not in receipt_dict
    
    # Verify database state
    updated = await users.find_one({'id': account['id']})
    assert updated['credential_generation'] == 1
    assert updated['password_hash'] != account['hash']
    assert updated['password_hash'].startswith('$2b$')
    
    # Verify new password works with bcrypt
    verify_result = await asyncio.get_event_loop().run_in_executor(
        None, 
        bcrypt.checkpw, 
        new_password.encode('utf-8'), 
        updated['password_hash'].encode('utf-8')
    )
    assert verify_result is True
    
    # Verify old password no longer works
    old_verify = await asyncio.get_event_loop().run_in_executor(
        None, 
        bcrypt.checkpw, 
        account['password'].encode('utf-8'), 
        updated['password_hash'].encode('utf-8')
    )
    assert old_verify is False
    
    print(f"✓ Basic rotation gen0->gen1 with real bcrypt verification passed")


async def test_old_session_tokens_rejected_after_rotation(staff_account_with_password, clean_db, http_client):
    """Test that old access and refresh tokens return 401 after rotation."""
    from tejas.staff_credentials import rotate_staff_credential
    from tejas.db import sessions
    from tejas.auth import token
    
    account = staff_account_with_password
    
    # Create old generation session
    old_session_id = str(uuid.uuid4())
    user_dict = {
        'id': account['id'],
        'email': 'staff-rotation-test@isolated.invalid',
        'role': 'reviewer',
        'access_type': 'staff_password',
    }
    
    await sessions.insert_one({
        'id': old_session_id,
        'user_id': account['id'],
        'access_type': 'staff_password',
        'credential_generation': 0,
        'expires_at': datetime.now(timezone.utc) + timedelta(hours=1),
    })
    
    old_access_token = token(user_dict, old_session_id, 'access', 900)
    old_refresh_token = token(user_dict, old_session_id, 'refresh', 3600)
    
    # Verify old tokens work before rotation
    response = await http_client.get('/api/auth/me', cookies={'access_token': old_access_token})
    assert response.status_code == 200
    
    # Perform rotation
    new_password = 'RotatedPasswordForTokenTest!'
    await rotate_staff_credential(account['id'], 0, new_password, str(uuid.uuid4()))
    
    # Verify old access token now returns 401
    response = await http_client.get('/api/auth/me', cookies={'access_token': old_access_token})
    assert response.status_code == 401
    
    # Verify old refresh token now returns 401
    response = await http_client.post('/api/auth/refresh', cookies={'refresh_token': old_refresh_token})
    assert response.status_code == 401
    
    print(f"✓ Old access and refresh tokens rejected after rotation")


async def test_fresh_password_login_after_rotation(clean_db, http_client):
    """Test that fresh password login works after rotation and creates new generation session."""
    from tejas.staff_credentials import rotate_staff_credential
    from tejas.db import users, sessions
    from tejas.auth import hashpw
    
    # Create a fresh account for this test
    account_id = str(uuid.uuid4())
    initial_password = 'InitialPasswordForLogin123!'
    hashed = await asyncio.get_event_loop().run_in_executor(None, hashpw, initial_password)
    
    await users.insert_one({
        'id': account_id,
        'email': 'fresh-login-test@example.com',
        'name': 'Fresh Login Test',
        'role': 'reviewer',
        'exam': 'JEE Main',
        'access_type': 'staff_password',
        'password_hash': hashed,
        'credential_generation': 0,
        'created_at': datetime.now(timezone.utc),
    })
    
    new_password = 'FreshPasswordAfterRotation!'
    
    # Perform rotation
    await rotate_staff_credential(account_id, 0, new_password, str(uuid.uuid4()))
    
    # Login with new password
    response = await http_client.post('/api/auth/login', json={
        'email': 'fresh-login-test@example.com',
        'password': new_password,
        'name': 'Test Staff',
        'exam': 'JEE Main',
        'consent': True,
    })
    
    assert response.status_code == 200
    data = response.json()['data']
    assert data['role'] == 'reviewer'
    
    # Verify new session has generation 1
    user = await users.find_one({'id': account_id})
    assert user['credential_generation'] == 1
    
    # Find the session created by login
    session = await sessions.find_one({'user_id': account_id, 'access_type': 'staff_password'})
    assert session is not None
    assert session['credential_generation'] == 1
    
    print(f"✓ Fresh password login after rotation creates gen1 session")


async def test_student_sessions_unchanged_by_staff_rotation(staff_account_with_password, clean_db, http_client):
    """Test that student phone sessions remain unchanged when staff credentials rotate."""
    from tejas.staff_credentials import rotate_staff_credential
    from tejas.db import sessions
    from tejas import db
    
    account = staff_account_with_password
    
    # Create a student phone session
    student_id = str(uuid.uuid4())
    student_session_id = str(uuid.uuid4())
    
    await db.db.tejas_phone_profiles.insert_one({
        'id': student_id,
        'phone': '+12025550199',
        'name': 'Test Student',
        'exam': 'JEE Main',
        'access_type': 'unverified_phone',
    })
    
    await sessions.insert_one({
        'id': student_session_id,
        'user_id': student_id,
        'access_type': 'unverified_phone',
        'expires_at': datetime.now(timezone.utc) + timedelta(hours=1),
    })
    
    before = await sessions.find_one({'id': student_session_id})
    # Perform staff rotation
    await rotate_staff_credential(account['id'], 0, 'NewStaffPassword!', str(uuid.uuid4()))

    # The exact student session and actual authenticated access survive unchanged.
    student_session = await sessions.find_one({'id': student_session_id})
    assert student_session == before
    from tejas.auth import token
    profile = await db.db.tejas_phone_profiles.find_one({'id': student_id})
    response = await http_client.get('/api/auth/me', cookies={'access_token': token(profile, student_session_id, 'access', 900)})
    assert response.status_code == 200
    assert response.json()['data']['role'] == 'student'
    
    print(f"✓ Student sessions unchanged by staff rotation")


async def test_concurrent_rotations_one_winner(owner_account_with_password, clean_db):
    """Test that concurrent rotations on same generation result in exactly one winner."""
    from tejas.staff_credentials import rotate_staff_credential, RotationConflict
    from tejas.db import users
    
    account = owner_account_with_password
    
    # Attempt two concurrent rotations
    password1 = 'ConcurrentPassword1!'
    password2 = 'ConcurrentPassword2!'
    op1 = str(uuid.uuid4())
    op2 = str(uuid.uuid4())
    
    results = await asyncio.gather(
        rotate_staff_credential(account['id'], 0, password1, op1),
        rotate_staff_credential(account['id'], 0, password2, op2),
        return_exceptions=True
    )
    
    # Exactly one should succeed, one should fail with RotationConflict
    successes = [r for r in results if not isinstance(r, Exception)]
    conflicts = [r for r in results if isinstance(r, RotationConflict)]
    
    assert len(successes) == 1
    assert len(conflicts) == 1
    
    winner = successes[0]
    assert winner.new_generation == 1
    
    # Verify stored hash matches winning password
    updated = await users.find_one({'id': account['id']})
    assert updated['credential_generation'] == 1
    
    # Determine which password won
    password1_matches = await asyncio.get_event_loop().run_in_executor(
        None, bcrypt.checkpw, password1.encode('utf-8'), updated['password_hash'].encode('utf-8')
    )
    password2_matches = await asyncio.get_event_loop().run_in_executor(
        None, bcrypt.checkpw, password2.encode('utf-8'), updated['password_hash'].encode('utf-8')
    )
    
    # Exactly one should match
    assert (winner.operation_id == op1 and password1_matches and not password2_matches) or (winner.operation_id == op2 and password2_matches and not password1_matches)
    
    print(f"✓ Concurrent rotations: exactly one winner, one RotationConflict")


async def test_rotation_with_cleanup_failure(staff_account_with_password, clean_db, monkeypatch):
    """Test rotation when session cleanup fails - receipt shows RETRY_REQUIRED but old tokens still 401."""
    from tejas.staff_credentials import rotate_staff_credential
    from tejas.db import sessions, users
    from tejas.auth import token
    
    account = staff_account_with_password
    
    # Create old session
    old_session_id = str(uuid.uuid4())
    user_dict = {
        'id': account['id'],
        'email': 'staff-rotation-test@isolated.invalid',
        'role': 'reviewer',
        'access_type': 'staff_password',
    }
    
    await sessions.insert_one({
        'id': old_session_id,
        'user_id': account['id'],
        'access_type': 'staff_password',
        'credential_generation': 0,
        'expires_at': datetime.now(timezone.utc) + timedelta(hours=1),
    })
    
    old_access_token = token(user_dict, old_session_id, 'access', 900)
    
    # Monkey-patch delete_many to raise PyMongoError
    original_delete_many = sessions.delete_many
    
    async def failing_delete_many(*args, **kwargs):
        raise PyMongoError("Simulated cleanup failure")
    
    monkeypatch.setattr(sessions, 'delete_many', failing_delete_many)
    
    # Perform rotation - should succeed logically but cleanup fails
    receipt = await rotate_staff_credential(account['id'], 0, 'NewPasswordCleanupFail!', str(uuid.uuid4()))
    
    # Restore original
    monkeypatch.setattr(sessions, 'delete_many', original_delete_many)
    
    # Verify receipt shows RETRY_REQUIRED
    assert receipt.logical_session_revocation == 'COMMITTED'
    assert receipt.physical_cleanup == 'RETRY_REQUIRED'
    assert receipt.deleted_session_count is None
    
    # Verify generation was updated
    updated = await users.find_one({'id': account['id']})
    assert updated['credential_generation'] == 1
    
    # Verify old session still exists in DB (cleanup failed)
    old_session = await sessions.find_one({'id': old_session_id})
    assert old_session is not None
    
    # But old token should still be rejected due to generation mismatch
    from tejas.auth import current
    from fastapi import Request, HTTPException
    
    # Create mock request with old token
    class MockRequest:
        def __init__(self):
            self.cookies = {'access_token': old_access_token}
    
    mock_request = MockRequest()
    
    # Should raise 401 due to generation mismatch
    with pytest.raises(HTTPException) as exc_info:
        await current(mock_request)
    assert exc_info.value.status_code == 401
    
    print(f"✓ Cleanup failure: receipt RETRY_REQUIRED, old tokens still 401")


async def test_bad_uuid_rejected(staff_account_with_password, clean_db):
    """Test that malformed UUIDs are rejected without mutation."""
    from tejas.staff_credentials import rotate_staff_credential
    from tejas.db import users
    
    account = staff_account_with_password
    
    # Try with bad account UUID
    with pytest.raises(ValueError, match='badly formed|canonical'):
        await rotate_staff_credential('not-a-uuid', 0, 'ValidPassword123!', str(uuid.uuid4()))
    
    # Try with bad operation UUID
    with pytest.raises(ValueError, match='badly formed|canonical'):
        await rotate_staff_credential(account['id'], 0, 'ValidPassword123!', 'bad-operation-id')
    
    # Verify no mutation occurred
    user = await users.find_one({'id': account['id']})
    assert user['credential_generation'] == 0
    assert user['password_hash'] == account['hash']
    
    print(f"✓ Bad UUIDs rejected without mutation")


async def test_invalid_generation_rejected(staff_account_with_password, clean_db):
    """Test that invalid generation values are rejected without mutation."""
    from tejas.staff_credentials import rotate_staff_credential, MAX_GENERATION
    from tejas.db import users
    
    account = staff_account_with_password
    
    # Negative generation
    with pytest.raises(ValueError, match='Invalid expected generation'):
        await rotate_staff_credential(account['id'], -1, 'ValidPassword123!', str(uuid.uuid4()))
    
    # Generation too large
    with pytest.raises(ValueError, match='Invalid expected generation'):
        await rotate_staff_credential(account['id'], MAX_GENERATION, 'ValidPassword123!', str(uuid.uuid4()))
    
    # Non-integer generation (this would fail at type level, but test boundary)
    with pytest.raises(ValueError, match='Invalid expected generation'):
        await rotate_staff_credential(account['id'], MAX_GENERATION - 1, 'ValidPassword123!', str(uuid.uuid4()))
    
    # Verify no mutation occurred
    user = await users.find_one({'id': account['id']})
    assert user['credential_generation'] == 0
    
    print(f"✓ Invalid generation values rejected without mutation")


async def test_password_byte_budget_enforced(staff_account_with_password, clean_db):
    """Test that password length constraints are enforced."""
    from tejas.staff_credentials import rotate_staff_credential
    from tejas.db import users
    
    account = staff_account_with_password
    
    # Too short (< 16 chars)
    with pytest.raises(ValueError, match='16–64 character'):
        await rotate_staff_credential(account['id'], 0, 'Short1!', str(uuid.uuid4()))
    
    # Too long (> 64 chars)
    with pytest.raises(ValueError, match='16–64 character'):
        await rotate_staff_credential(account['id'], 0, 'A' * 65 + '!', str(uuid.uuid4()))
    
    # Too many UTF-8 bytes (> 64 bytes)
    # Use multibyte characters to exceed 64 bytes while staying under 64 chars
    multibyte_password = '🔐' * 20  # Each emoji is 4 bytes, 20 * 4 = 80 bytes
    with pytest.raises(ValueError, match='64 UTF-8 bytes'):
        await rotate_staff_credential(account['id'], 0, multibyte_password, str(uuid.uuid4()))
    
    # Verify no mutation occurred
    user = await users.find_one({'id': account['id']})
    assert user['credential_generation'] == 0
    
    print(f"✓ Password byte budget enforced")


async def test_non_staff_account_rejected(clean_db):
    """Test that non-staff accounts cannot be rotated."""
    from tejas.staff_credentials import rotate_staff_credential, RotationConflict
    from tejas.db import users
    from tejas.auth import hashpw
    
    # Create a student account (not staff)
    student_id = str(uuid.uuid4())
    await users.insert_one({
        'id': student_id,
        'email': 'student@isolated.invalid',
        'name': 'Student User',
        'role': 'student',
        'exam': 'JEE Main',
        'access_type': 'staff_password',
        'password_hash': await asyncio.get_event_loop().run_in_executor(None, hashpw, 'StudentPassword123!'),
        'credential_generation': 0,
    })
    
    # Try to rotate - should fail
    with pytest.raises((RotationConflict, ValueError)):
        await rotate_staff_credential(student_id, 0, 'NewPasswordLongEnough123!', str(uuid.uuid4()))
    
    # Verify no mutation
    user = await users.find_one({'id': student_id})
    assert user['credential_generation'] == 0
    
    print(f"✓ Non-staff account rotation rejected")


async def test_malformed_stored_generation_rejects_session(staff_account_with_password, clean_db):
    """Test that malformed credential_generation in user record causes session rejection."""
    from tejas.db import users, sessions
    from tejas.auth import token, current
    from fastapi import Request, HTTPException
    
    account = staff_account_with_password
    
    # Create a valid session
    session_id = str(uuid.uuid4())
    user_dict = {
        'id': account['id'],
        'email': 'staff-rotation-test@isolated.invalid',
        'role': 'reviewer',
        'access_type': 'staff_password',
    }
    
    await sessions.insert_one({
        'id': session_id,
        'user_id': account['id'],
        'access_type': 'staff_password',
        'credential_generation': 0,
        'expires_at': datetime.now(timezone.utc) + timedelta(hours=1),
    })
    
    access_token = token(user_dict, session_id, 'access', 900)
    
    # Corrupt the user's credential_generation
    await users.update_one(
        {'id': account['id']},
        {'$set': {'credential_generation': 'invalid_string'}}
    )
    
    # Try to use the session - should fail
    class MockRequest:
        def __init__(self):
            self.cookies = {'access_token': access_token}
    
    mock_request = MockRequest()
    
    with pytest.raises(HTTPException) as exc_info:
        await current(mock_request)
    assert exc_info.value.status_code == 401
    
    print(f"✓ Malformed stored generation rejects session")


async def test_staff_auth_held_flag_blocks_session(staff_account_with_password, clean_db):
    """Test that staff_auth_held=True blocks new session creation."""
    from tejas.db import users, sessions
    from tejas.auth import new_session
    from fastapi import HTTPException, Response
    
    account = staff_account_with_password
    
    # Set staff_auth_held flag
    await users.update_one(
        {'id': account['id']},
        {'$set': {'staff_auth_held': True}}
    )
    
    # Try to create new session
    user = await users.find_one({'id': account['id']})
    
    class MockResponse:
        def set_cookie(self, *args, **kwargs):
            pass
    
    mock_response = MockResponse()
    
    with pytest.raises(HTTPException) as exc_info:
        await new_session(user, mock_response)
    assert exc_info.value.status_code == 401
    assert 'unavailable' in exc_info.value.detail.lower()
    
    print(f"✓ staff_auth_held flag blocks session creation")


async def test_delayed_old_generation_insert_rejected(staff_account_with_password, clean_db, monkeypatch):
    """Test that delayed old-generation session insertion is rejected even after cleanup."""
    from tejas.staff_credentials import rotate_staff_credential
    from tejas.db import sessions, users
    from tejas.auth import token, current
    from fastapi import Request, HTTPException
    import asyncio
    
    account = staff_account_with_password
    
    # Prepare old session data but don't insert yet
    old_session_id = str(uuid.uuid4())
    old_session_data = {
        'id': old_session_id,
        'user_id': account['id'],
        'access_type': 'staff_password',
        'credential_generation': 0,
        'expires_at': datetime.now(timezone.utc) + timedelta(hours=1),
    }
    
    user_dict = {
        'id': account['id'],
        'email': 'staff-rotation-test@isolated.invalid',
        'role': 'reviewer',
        'access_type': 'staff_password',
    }
    
    old_access_token = token(user_dict, old_session_id, 'access', 900)
    
    from tejas import auth
    from fastapi import Response
    original_user = await users.find_one({'id': account['id']})
    entered, release = asyncio.Event(), asyncio.Event()
    real_sessions = auth.sessions
    class DelayedSessions:
        def __getattr__(self, name):
            return getattr(real_sessions, name)
        async def insert_one(self, value, *args, **kwargs):
            entered.set()
            await asyncio.wait_for(release.wait(), 3)
            return await real_sessions.insert_one(value, *args, **kwargs)
    monkeypatch.setattr(auth, 'sessions', DelayedSessions())
    login_response = Response()
    pending = asyncio.create_task(auth.new_session(original_user, login_response))
    try:
        await asyncio.wait_for(entered.wait(), 3)
        # Atomic rotation and cleanup both finish before delayed real insertion.
        await rotate_staff_credential(account['id'], 0, 'NewPasswordDelayed!', str(uuid.uuid4()))
        release.set()
        with pytest.raises(HTTPException) as rejected:
            await asyncio.wait_for(pending, 3)
        assert rejected.value.status_code == 401
        assert not login_response.headers.getlist('set-cookie')
        assert await real_sessions.count_documents({'user_id': account['id']}) == 0
    finally:
        release.set()
        if not pending.done():
            pending.cancel()
        await asyncio.gather(pending, return_exceptions=True)
    # Even a stale insertion from a crashed/legacy worker is rejected on use.
    await sessions.insert_one(old_session_data)
    
    # Verify the session exists in DB
    inserted_session = await sessions.find_one({'id': old_session_id})
    assert inserted_session is not None
    
    # But it should still be rejected due to generation mismatch
    class MockRequest:
        def __init__(self):
            self.cookies = {'access_token': old_access_token}
    
    mock_request = MockRequest()
    
    with pytest.raises(HTTPException) as exc_info:
        await current(mock_request)
    assert exc_info.value.status_code == 401
    
    print(f"✓ Delayed old-generation insert rejected despite DB presence")


async def test_rotation_wrong_expected_generation(staff_account_with_password, clean_db):
    """Test that rotation with wrong expected generation fails."""
    from tejas.staff_credentials import rotate_staff_credential, RotationConflict
    from tejas.db import users
    
    account = staff_account_with_password
    
    # Try to rotate with wrong expected generation
    with pytest.raises(RotationConflict, match='Account state changed'):
        await rotate_staff_credential(account['id'], 1, 'NewPasswordLongEnough123!', str(uuid.uuid4()))
    
    # Verify no mutation
    user = await users.find_one({'id': account['id']})
    assert user['credential_generation'] == 0
    
    print(f"✓ Wrong expected generation causes RotationConflict")
