"""Owner email and password update with 8-character exception.

Tests atomic CAS email+hash+generation, role restrictions, session revocation,
duplicate email collision, byte budget, and CAS race conditions.
Uses SYNTHETIC 8-character passwords only. No live secrets.
"""
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import pytest
import pytest_asyncio

pytestmark = pytest.mark.asyncio(loop_scope='session')


def generate_synthetic_8char_password():
    """Generate a random 8-character password for testing."""
    return str(uuid.uuid4())[:8].replace('-', 'A')


@pytest_asyncio.fixture(loop_scope='session')
async def owner_account_for_identity_update(clean_db):
    """Create a synthetic owner account for identity update tests."""
    from tejas.db import users
    from tejas.auth import hashpw
    
    account_id = str(uuid.uuid4())
    initial_email = f'owner-identity-{account_id[:8]}@example.com'
    password = 'InitialOwnerPassword123!'
    hashed = await asyncio.get_event_loop().run_in_executor(None, hashpw, password)
    
    await users.insert_one({
        'id': account_id,
        'email': initial_email,
        'name': 'Owner Identity Test',
        'role': 'owner',
        'exam': 'JEE Main',
        'access_type': 'staff_password',
        'password_hash': hashed,
        'credential_generation': 0,
        'created_at': datetime.now(timezone.utc),
    })
    
    return {
        'id': account_id,
        'email': initial_email,
        'password': password,
        'generation': 0,
        'hash': hashed
    }


@pytest_asyncio.fixture(loop_scope='session')
async def reviewer_account_for_identity_update(clean_db):
    """Create a synthetic reviewer account to test role restrictions."""
    from tejas.db import users
    from tejas.auth import hashpw
    
    account_id = str(uuid.uuid4())
    email = f'reviewer-identity-{account_id[:8]}@example.com'
    password = 'ReviewerPassword123!'
    hashed = await asyncio.get_event_loop().run_in_executor(None, hashpw, password)
    
    await users.insert_one({
        'id': account_id,
        'email': email,
        'name': 'Reviewer Identity Test',
        'role': 'reviewer',
        'exam': 'JEE Main',
        'access_type': 'staff_password',
        'password_hash': hashed,
        'credential_generation': 0,
        'created_at': datetime.now(timezone.utc),
    })
    
    return {
        'id': account_id,
        'email': email,
        'password': password,
        'generation': 0,
        'hash': hashed
    }


async def test_owner_email_and_password_update_with_8char(owner_account_for_identity_update, clean_db, http_client):
    """Test owner can update email and use 8-character password with owner_selected_password=True."""
    from tejas.staff_credentials import rotate_staff_credential
    from tejas.db import users
    
    account = owner_account_for_identity_update
    new_email = f'new-owner-{uuid.uuid4().hex[:8]}@example.com'
    new_password = generate_synthetic_8char_password()
    operation_id = str(uuid.uuid4())
    
    # Perform rotation with email replacement and 8-char password
    receipt = await rotate_staff_credential(
        account['id'],
        account['generation'],
        new_password,
        operation_id,
        replacement_email=new_email,
        owner_selected_password=True
    )
    
    # Verify receipt
    assert receipt.operation_id == operation_id
    assert receipt.account_id == account['id']
    assert receipt.prior_generation == 0
    assert receipt.new_generation == 1
    assert receipt.logical_session_revocation == 'COMMITTED'
    
    # Verify no secrets in receipt
    receipt_json = receipt.model_dump_json()
    assert new_password not in receipt_json
    assert new_email not in receipt_json
    
    # Verify database state
    updated = await users.find_one({'id': account['id']})
    assert updated['credential_generation'] == 1
    assert updated['email'] == new_email.lower()
    assert updated['password_hash'] != account['hash']
    assert updated['password_hash'].startswith('$2b$')
    assert updated['owner_selected_password_exception'] is True
    assert updated['id'] == account['id']  # UUID preserved
    
    # Verify new password works
    verify_result = await asyncio.get_event_loop().run_in_executor(
        None,
        bcrypt.checkpw,
        new_password.encode('utf-8'),
        updated['password_hash'].encode('utf-8')
    )
    assert verify_result is True
    
    # Test login with NEW email returns 200
    response = await http_client.post('/api/auth/login', json={
        'email': new_email,
        'password': new_password,
        'name': 'Test Owner',
        'exam': 'JEE Main',
        'consent': True,
    })
    assert response.status_code == 200
    data = response.json()['data']
    assert data['role'] == 'owner'
    assert data['email'] == new_email.lower()
    
    # Test login with OLD email returns 401
    response = await http_client.post('/api/auth/login', json={
        'email': account['email'],
        'password': new_password,
        'name': 'Test Owner',
        'exam': 'JEE Main',
        'consent': True,
    })
    assert response.status_code == 401
    
    print(f"✓ Owner email+password update with 8-char password successful")


async def test_old_owner_session_401_after_identity_update(owner_account_for_identity_update, clean_db, http_client):
    """Test that old owner sessions return 401 after email/password rotation."""
    from tejas.staff_credentials import rotate_staff_credential
    from tejas.db import sessions, users
    from tejas.auth import token
    
    # Create a fresh owner for this test
    account_id = str(uuid.uuid4())
    initial_email = f'session-test-owner-{account_id[:8]}@example.com'
    from tejas.auth import hashpw
    hashed = await asyncio.get_event_loop().run_in_executor(None, hashpw, 'InitialPass123!')
    
    await users.insert_one({
        'id': account_id,
        'email': initial_email,
        'name': 'Session Test Owner',
        'role': 'owner',
        'exam': 'JEE Main',
        'access_type': 'staff_password',
        'password_hash': hashed,
        'credential_generation': 0,
        'created_at': datetime.now(timezone.utc),
    })
    
    # Create old generation session
    old_session_id = str(uuid.uuid4())
    user_dict = {
        'id': account_id,
        'email': initial_email,
        'role': 'owner',
        'access_type': 'staff_password',
    }
    
    await sessions.insert_one({
        'id': old_session_id,
        'user_id': account_id,
        'access_type': 'staff_password',
        'credential_generation': 0,
        'expires_at': datetime.now(timezone.utc) + timedelta(hours=1),
    })
    
    old_access_token = token(user_dict, old_session_id, 'access', 900)
    old_refresh_token = token(user_dict, old_session_id, 'refresh', 3600)
    
    # Verify old tokens work before rotation
    response = await http_client.get('/api/auth/me', cookies={'access_token': old_access_token})
    assert response.status_code == 200
    
    # Perform rotation with email change
    new_email = f'rotated-owner-{uuid.uuid4().hex[:8]}@example.com'
    new_password = generate_synthetic_8char_password()
    await rotate_staff_credential(
        account_id,
        0,
        new_password,
        str(uuid.uuid4()),
        replacement_email=new_email,
        owner_selected_password=True
    )
    
    # Verify old access token returns 401
    response = await http_client.get('/api/auth/me', cookies={'access_token': old_access_token})
    assert response.status_code == 401
    
    # Verify old refresh token returns 401
    response = await http_client.post('/api/auth/refresh', cookies={'refresh_token': old_refresh_token})
    assert response.status_code == 401
    
    print(f"✓ Old owner sessions return 401 after identity update")


async def test_student_sessions_preserved_during_owner_rotation(owner_account_for_identity_update, clean_db, http_client):
    """Test that student phone sessions remain unchanged when owner rotates identity."""
    from tejas.staff_credentials import rotate_staff_credential
    from tejas.db import sessions
    from tejas import db
    from tejas.auth import token
    
    # Create a fresh owner for this test
    account_id = str(uuid.uuid4())
    from tejas.auth import hashpw
    hashed = await asyncio.get_event_loop().run_in_executor(None, hashpw, 'OwnerPass123!')
    
    await db.users.insert_one({
        'id': account_id,
        'email': f'owner-student-test-{account_id[:8]}@example.com',
        'name': 'Owner Student Test',
        'role': 'owner',
        'exam': 'JEE Main',
        'access_type': 'staff_password',
        'password_hash': hashed,
        'credential_generation': 0,
        'created_at': datetime.now(timezone.utc),
    })
    
    # Create a student phone session
    student_id = str(uuid.uuid4())
    student_session_id = str(uuid.uuid4())
    
    await db.db.tejas_phone_profiles.insert_one({
        'id': student_id,
        'phone': '+12025550198',
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
    
    # Perform owner identity rotation
    new_email = f'rotated-{uuid.uuid4().hex[:8]}@example.com'
    await rotate_staff_credential(
        account_id,
        0,
        generate_synthetic_8char_password(),
        str(uuid.uuid4()),
        replacement_email=new_email,
        owner_selected_password=True
    )
    
    # Verify student session unchanged
    student_session = await sessions.find_one({'id': student_session_id})
    assert student_session == before
    
    # Verify student can still authenticate
    profile = await db.db.tejas_phone_profiles.find_one({'id': student_id})
    response = await http_client.get('/api/auth/me', cookies={
        'access_token': token(profile, student_session_id, 'access', 900)
    })
    assert response.status_code == 200
    assert response.json()['data']['role'] == 'student'
    
    print(f"✓ Student sessions preserved during owner identity rotation")


async def test_default_min16_rejects_8char_password(owner_account_for_identity_update, clean_db):
    """Test that default rotation (owner_selected_password=False) rejects 8-character password."""
    from tejas.staff_credentials import rotate_staff_credential
    from tejas.db import users
    
    # Create a fresh owner for this test
    account_id = str(uuid.uuid4())
    from tejas.auth import hashpw
    hashed = await asyncio.get_event_loop().run_in_executor(None, hashpw, 'InitialPass123!')
    
    await users.insert_one({
        'id': account_id,
        'email': f'min16-test-{account_id[:8]}@example.com',
        'name': 'Min16 Test Owner',
        'role': 'owner',
        'exam': 'JEE Main',
        'access_type': 'staff_password',
        'password_hash': hashed,
        'credential_generation': 0,
        'created_at': datetime.now(timezone.utc),
    })
    
    short_password = generate_synthetic_8char_password()
    
    # Try rotation without owner_selected_password flag (default min16)
    with pytest.raises(ValueError, match='16–64 character'):
        await rotate_staff_credential(
            account_id,
            0,
            short_password,
            str(uuid.uuid4()),
            owner_selected_password=False
        )
    
    # Verify no mutation occurred
    user = await users.find_one({'id': account_id})
    assert user['credential_generation'] == 0
    assert user['password_hash'] == hashed
    
    print(f"✓ Default min16 rejects 8-character password")


async def test_reviewer_exception_rejected_without_mutation(reviewer_account_for_identity_update, clean_db):
    """Test that reviewer cannot use owner_selected_password exception or email replacement."""
    from tejas.staff_credentials import rotate_staff_credential, RotationConflict
    from tejas.db import users
    
    account = reviewer_account_for_identity_update
    new_email = f'reviewer-new-{uuid.uuid4().hex[:8]}@example.com'
    short_password = generate_synthetic_8char_password()
    
    # Try email replacement as reviewer (should fail - owner only)
    with pytest.raises(RotationConflict, match='Account state changed|not an eligible'):
        await rotate_staff_credential(
            account['id'],
            0,
            'ValidLongPassword123!',
            str(uuid.uuid4()),
            replacement_email=new_email,
            owner_selected_password=False
        )
    
    # Try 8-char password with owner_selected_password as reviewer (should fail)
    with pytest.raises(RotationConflict, match='Account state changed|not an eligible'):
        await rotate_staff_credential(
            account['id'],
            0,
            short_password,
            str(uuid.uuid4()),
            replacement_email=new_email,
            owner_selected_password=True
        )
    
    # Verify no mutation occurred
    user = await users.find_one({'id': account['id']})
    assert user['credential_generation'] == 0
    assert user['email'] == account['email']
    assert user['password_hash'] == account['hash']
    
    print(f"✓ Reviewer exception rejected without mutation")


async def test_duplicate_email_collision_atomic_unchanged(owner_account_for_identity_update, clean_db):
    """Test that duplicate email collision leaves account atomically unchanged."""
    from tejas.staff_credentials import rotate_staff_credential
    from tejas.db import users
    from pymongo.errors import DuplicateKeyError
    
    # Create first owner
    owner1_id = str(uuid.uuid4())
    owner1_email = f'owner1-{uuid.uuid4().hex[:8]}@example.com'
    from tejas.auth import hashpw
    hashed1 = await asyncio.get_event_loop().run_in_executor(None, hashpw, 'Owner1Pass123!')
    
    await users.insert_one({
        'id': owner1_id,
        'email': owner1_email,
        'name': 'Owner 1',
        'role': 'owner',
        'exam': 'JEE Main',
        'access_type': 'staff_password',
        'password_hash': hashed1,
        'credential_generation': 0,
        'created_at': datetime.now(timezone.utc),
    })
    
    # Create second owner
    owner2_id = str(uuid.uuid4())
    owner2_email = f'owner2-{uuid.uuid4().hex[:8]}@example.com'
    hashed2 = await asyncio.get_event_loop().run_in_executor(None, hashpw, 'Owner2Pass123!')
    
    await users.insert_one({
        'id': owner2_id,
        'email': owner2_email,
        'name': 'Owner 2',
        'role': 'owner',
        'exam': 'JEE Main',
        'access_type': 'staff_password',
        'password_hash': hashed2,
        'credential_generation': 0,
        'created_at': datetime.now(timezone.utc),
    })
    
    # Try to change owner2's email to owner1's email (should fail)
    try:
        await rotate_staff_credential(
            owner2_id,
            0,
            generate_synthetic_8char_password(),
            str(uuid.uuid4()),
            replacement_email=owner1_email,
            owner_selected_password=True
        )
        # If no exception, check that it failed atomically
        owner2 = await users.find_one({'id': owner2_id})
        # Either the operation failed completely, or MongoDB's unique index prevented it
        assert owner2['email'] == owner2_email
        assert owner2['credential_generation'] == 0
    except (DuplicateKeyError, Exception):
        # Expected: duplicate email rejected
        pass
    
    # Verify owner2 unchanged
    owner2 = await users.find_one({'id': owner2_id})
    assert owner2['email'] == owner2_email
    assert owner2['credential_generation'] == 0
    assert owner2['password_hash'] == hashed2
    
    # Verify owner1 unchanged
    owner1 = await users.find_one({'id': owner1_id})
    assert owner1['email'] == owner1_email
    assert owner1['credential_generation'] == 0
    
    print(f"✓ Duplicate email collision leaves account atomically unchanged")


async def test_bad_email_rejected(owner_account_for_identity_update, clean_db):
    """Test that invalid email format is rejected without mutation."""
    from tejas.staff_credentials import rotate_staff_credential
    from tejas.db import users
    
    # Create a fresh owner for this test
    account_id = str(uuid.uuid4())
    from tejas.auth import hashpw
    hashed = await asyncio.get_event_loop().run_in_executor(None, hashpw, 'InitialPass123!')
    
    await users.insert_one({
        'id': account_id,
        'email': f'bad-email-test-{account_id[:8]}@example.com',
        'name': 'Bad Email Test',
        'role': 'owner',
        'exam': 'JEE Main',
        'access_type': 'staff_password',
        'password_hash': hashed,
        'credential_generation': 0,
        'created_at': datetime.now(timezone.utc),
    })
    
    bad_emails = [
        'not-an-email',
        'missing-at-sign.com',
        '@no-local-part.com',
        'no-domain@',
        'spaces in@email.com',
    ]
    
    for bad_email in bad_emails:
        try:
            await rotate_staff_credential(
                account_id,
                0,
                generate_synthetic_8char_password(),
                str(uuid.uuid4()),
                replacement_email=bad_email,
                owner_selected_password=True
            )
            # If it didn't raise, verify no mutation
            user = await users.find_one({'id': account_id})
            assert user['credential_generation'] == 0
        except (ValueError, Exception):
            # Expected: bad email rejected
            pass
    
    # Verify no mutation occurred
    user = await users.find_one({'id': account_id})
    assert user['credential_generation'] == 0
    assert user['password_hash'] == hashed
    
    print(f"✓ Bad email formats rejected without mutation")


async def test_long_byte_budget_password_rejected(owner_account_for_identity_update, clean_db):
    """Test that password exceeding 64 UTF-8 bytes is rejected."""
    from tejas.staff_credentials import rotate_staff_credential
    from tejas.db import users
    
    # Create a fresh owner for this test
    account_id = str(uuid.uuid4())
    from tejas.auth import hashpw
    hashed = await asyncio.get_event_loop().run_in_executor(None, hashpw, 'InitialPass123!')
    
    await users.insert_one({
        'id': account_id,
        'email': f'byte-budget-test-{account_id[:8]}@example.com',
        'name': 'Byte Budget Test',
        'role': 'owner',
        'exam': 'JEE Main',
        'access_type': 'staff_password',
        'password_hash': hashed,
        'credential_generation': 0,
        'created_at': datetime.now(timezone.utc),
    })
    
    # Create password with multibyte characters exceeding 64 bytes
    # Each emoji is 4 bytes, 20 * 4 = 80 bytes
    multibyte_password = '🔐' * 20
    
    with pytest.raises(ValueError, match='64 UTF-8 bytes'):
        await rotate_staff_credential(
            account_id,
            0,
            multibyte_password,
            str(uuid.uuid4()),
            replacement_email=f'new-{uuid.uuid4().hex[:8]}@example.com',
            owner_selected_password=True
        )
    
    # Verify no mutation occurred
    user = await users.find_one({'id': account_id})
    assert user['credential_generation'] == 0
    assert user['password_hash'] == hashed
    
    print(f"✓ Long byte budget password rejected")


async def test_cas_race_condition_one_winner(clean_db):
    """Test that concurrent identity updates result in exactly one winner (CAS race)."""
    from tejas.staff_credentials import rotate_staff_credential, RotationConflict
    from tejas.db import users
    from tejas.auth import hashpw
    
    # Create owner for race test
    account_id = str(uuid.uuid4())
    initial_email = f'race-test-{account_id[:8]}@example.com'
    hashed = await asyncio.get_event_loop().run_in_executor(None, hashpw, 'RaceTestPass123!')
    
    await users.insert_one({
        'id': account_id,
        'email': initial_email,
        'name': 'Race Test Owner',
        'role': 'owner',
        'exam': 'JEE Main',
        'access_type': 'staff_password',
        'password_hash': hashed,
        'credential_generation': 0,
        'created_at': datetime.now(timezone.utc),
    })
    
    # Attempt two concurrent identity updates
    email1 = f'race-winner1-{uuid.uuid4().hex[:8]}@example.com'
    email2 = f'race-winner2-{uuid.uuid4().hex[:8]}@example.com'
    password1 = generate_synthetic_8char_password()
    password2 = generate_synthetic_8char_password()
    op1 = str(uuid.uuid4())
    op2 = str(uuid.uuid4())
    
    results = await asyncio.gather(
        rotate_staff_credential(
            account_id, 0, password1, op1,
            replacement_email=email1, owner_selected_password=True
        ),
        rotate_staff_credential(
            account_id, 0, password2, op2,
            replacement_email=email2, owner_selected_password=True
        ),
        return_exceptions=True
    )
    
    # Exactly one should succeed, one should fail with RotationConflict
    successes = [r for r in results if not isinstance(r, Exception)]
    conflicts = [r for r in results if isinstance(r, RotationConflict)]
    
    assert len(successes) == 1
    assert len(conflicts) == 1
    
    winner = successes[0]
    assert winner.new_generation == 1
    
    # Verify stored state matches winning operation
    updated = await users.find_one({'id': account_id})
    assert updated['credential_generation'] == 1
    
    # Determine which operation won
    if winner.operation_id == op1:
        assert updated['email'] == email1.lower()
        verify_password = password1
    else:
        assert updated['email'] == email2.lower()
        verify_password = password2
    
    # Verify winning password works
    password_matches = await asyncio.get_event_loop().run_in_executor(
        None, bcrypt.checkpw, verify_password.encode('utf-8'), updated['password_hash'].encode('utf-8')
    )
    assert password_matches is True
    
    print(f"✓ CAS race condition: exactly one winner")


async def test_owner_selected_password_requires_email(owner_account_for_identity_update, clean_db):
    """Test that owner_selected_password=True requires replacement_email to be set."""
    from tejas.staff_credentials import rotate_staff_credential
    from tejas.db import users
    
    account = owner_account_for_identity_update
    
    # Try owner_selected_password without replacement_email (should fail)
    with pytest.raises(ValueError, match='Owner-selected exception requires an explicit owner identity update'):
        await rotate_staff_credential(
            account['id'],
            0,
            generate_synthetic_8char_password(),
            str(uuid.uuid4()),
            replacement_email=None,
            owner_selected_password=True
        )
    
    # Verify no mutation occurred
    user = await users.find_one({'id': account['id']})
    assert user['credential_generation'] == 0
    
    print(f"✓ owner_selected_password requires replacement_email")


async def test_uuid_preserved_after_identity_update(owner_account_for_identity_update, clean_db):
    """Test that account UUID is preserved after identity update."""
    from tejas.staff_credentials import rotate_staff_credential
    from tejas.db import users
    
    # Create a fresh owner for this test
    account_id = str(uuid.uuid4())
    initial_email = f'uuid-test-{account_id[:8]}@example.com'
    from tejas.auth import hashpw
    hashed = await asyncio.get_event_loop().run_in_executor(None, hashpw, 'InitialPass123!')
    
    await users.insert_one({
        'id': account_id,
        'email': initial_email,
        'name': 'UUID Test Owner',
        'role': 'owner',
        'exam': 'JEE Main',
        'access_type': 'staff_password',
        'password_hash': hashed,
        'credential_generation': 0,
        'created_at': datetime.now(timezone.utc),
        'custom_field': 'preserved_content',
    })
    
    before = await users.find_one({'id': account_id})
    
    # Perform identity update
    new_email = f'new-uuid-test-{uuid.uuid4().hex[:8]}@example.com'
    await rotate_staff_credential(
        account_id,
        0,
        generate_synthetic_8char_password(),
        str(uuid.uuid4()),
        replacement_email=new_email,
        owner_selected_password=True
    )
    
    # Verify UUID and other fields preserved
    after = await users.find_one({'id': account_id})
    assert after['id'] == account_id
    assert after['id'] == before['id']
    assert after['name'] == before['name']
    assert after['role'] == before['role']
    assert after['exam'] == before['exam']
    assert after['custom_field'] == before['custom_field']
    
    # Only email, password_hash, and generation should change
    assert after['email'] != before['email']
    assert after['password_hash'] != before['password_hash']
    assert after['credential_generation'] != before['credential_generation']
    
    print(f"✓ UUID and content preserved after identity update")
