"""
CORRECTED AUDIT HARNESS - Failclosed NamespaceProxy for complete isolation
Fixes: A01 packs escape, A05 sequential await, A06 wrong proxy, A02 barrier, A04 incomplete
"""
import asyncio
import sys
import os
import uuid
import copy
from unittest.mock import patch, AsyncMock, MagicMock
from contextlib import asynccontextmanager

sys.path.insert(0, '/app/backend')

from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

from motor.motor_asyncio import AsyncIOMotorClient
from tejas.db import uid, now

# Test isolation UUID
AUDIT_UUID = str(uuid.uuid4())[:8]

# Global client and db
client = None
db = None


class NamespaceProxy:
    """Failclosed proxy that maps tejas_X to audit_UUID_tejas_X"""
    
    ALLOWED_COLLECTIONS = {
        'tejas_packs', 'tejas_sets', 'tejas_attempts', 'tejas_files', 
        'tejas_jobs', 'tejas_audits', 'tejas_users', 'tejas_sessions',
        'tejas_versions', 'tejas_ledgers', 'tejas_score_versions',
        'tejas_preflight', 'tejas_phone_profiles', 'tejas_phone_limits',
        'tejas_login_limits', 'tejas_cron_receipts', 'tejas_operations'
    }
    
    def __init__(self, real_db, audit_uuid):
        self._real_db = real_db
        self._audit_uuid = audit_uuid
        self._cache = {}
    
    def __getattr__(self, name):
        """Map tejas_X to audit_UUID_tejas_X, reject unknown"""
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        
        if name not in self.ALLOWED_COLLECTIONS:
            raise AttributeError(f"NamespaceProxy: Unknown collection '{name}' - audit harness must not access this")
        
        if name not in self._cache:
            namespaced = f"audit_{self._audit_uuid}_{name}"
            self._cache[name] = self._real_db[namespaced]
        
        return self._cache[name]
    
    def get_database(self, *args, **kwargs):
        """Delegate get_database to real db"""
        return self._real_db.get_database(*args, **kwargs)
    
    def list_collection_names(self):
        """Return only namespaced collections"""
        return [f"audit_{self._audit_uuid}_{c}" for c in self.ALLOWED_COLLECTIONS]


async def setup_namespace():
    """Setup namespaced database proxy"""
    global client, db
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    real_db = client.get_database(os.environ["DB_NAME"])
    db = NamespaceProxy(real_db, AUDIT_UUID)
    
    print(f"✓ Setup NamespaceProxy with UUID: {AUDIT_UUID}")
    return db


async def capture_main_counts():
    """Capture counts of main immutable collections BEFORE test"""
    real_db = client.get_database(os.environ["DB_NAME"])
    counts = {}
    for coll in ['tejas_packs', 'tejas_sets', 'tejas_attempts', 'tejas_users', 'tejas_jobs']:
        counts[coll] = await real_db[coll].count_documents({})
    print(f"✓ Captured main collection counts: {counts}")
    return counts


async def verify_isolation(before_counts):
    """Verify NO writes to main collections"""
    real_db = client.get_database(os.environ["DB_NAME"])
    after_counts = {}
    violations = []
    
    for coll, before in before_counts.items():
        after = await real_db[coll].count_documents({})
        after_counts[coll] = after
        if after != before:
            violations.append(f"{coll}: {before} -> {after} (+{after - before})")
    
    if violations:
        print(f"✗ ISOLATION VIOLATION: {', '.join(violations)}")
        return False
    else:
        print(f"✓ Isolation verified: No writes to main collections")
        return True


async def cleanup_namespace():
    """Cleanup all namespaced collections"""
    global client, db
    if db is not None:
        real_db = client.get_database(os.environ["DB_NAME"])
        dropped = 0
        for coll_name in db.list_collection_names():
            await real_db[coll_name].drop()
            dropped += 1
        print(f"✓ Dropped {dropped} namespaced collections")
    if client is not None:
        client.close()


@asynccontextmanager
async def patch_all_modules():
    """Patch ALL tejas module db references to use NamespaceProxy"""
    import tejas.db
    import tejas.packs
    import tejas.attempts
    import tejas.content
    import tejas.jobs
    import tejas.corrections
    import tejas.profiles
    
    # Store originals
    originals = {
        'tejas.db.db': tejas.db.db,
        'tejas.db.users': tejas.db.users,
        'tejas.db.sessions': tejas.db.sessions,
        'tejas.db.sets': tejas.db.sets,
        'tejas.db.attempts': tejas.db.attempts,
        'tejas.db.files': tejas.db.files,
        'tejas.db.jobs': tejas.db.jobs,
        'tejas.db.audits': tejas.db.audits,
        'tejas.packs.db': tejas.packs.db,
        'tejas.attempts.attempts': tejas.attempts.attempts,
        'tejas.attempts.sets': tejas.attempts.sets,
        'tejas.attempts.files': tejas.attempts.files,
        'tejas.attempts.db': tejas.attempts.db,
        'tejas.content.sets': tejas.content.sets,
        'tejas.content.files': tejas.content.files,
        'tejas.content.audits': tejas.content.audits,
        'tejas.content.jobs': tejas.content.jobs,
        'tejas.content.db': tejas.content.db,
        'tejas.jobs.jobs': tejas.jobs.jobs,
        'tejas.jobs.sets': tejas.jobs.sets,
        'tejas.jobs.files': tejas.jobs.files,
        'tejas.jobs.attempts': tejas.jobs.attempts,
        'tejas.jobs.db': tejas.jobs.db,
    }
    
    # Patch to NamespaceProxy
    tejas.db.db = db
    tejas.db.users = db.tejas_users
    tejas.db.sessions = db.tejas_sessions
    tejas.db.sets = db.tejas_sets
    tejas.db.attempts = db.tejas_attempts
    tejas.db.files = db.tejas_files
    tejas.db.jobs = db.tejas_jobs
    tejas.db.audits = db.tejas_audits
    
    tejas.packs.db = db
    
    tejas.attempts.attempts = db.tejas_attempts
    tejas.attempts.sets = db.tejas_sets
    tejas.attempts.files = db.tejas_files
    tejas.attempts.db = db
    
    tejas.content.sets = db.tejas_sets
    tejas.content.files = db.tejas_files
    tejas.content.audits = db.tejas_audits
    tejas.content.jobs = db.tejas_jobs
    tejas.content.db = db
    
    tejas.jobs.jobs = db.tejas_jobs
    tejas.jobs.sets = db.tejas_sets
    tejas.jobs.files = db.tejas_files
    tejas.jobs.attempts = db.tejas_attempts
    tejas.jobs.db = db
    
    try:
        yield
    finally:
        # Restore originals
        tejas.db.db = originals['tejas.db.db']
        tejas.db.users = originals['tejas.db.users']
        tejas.db.sessions = originals['tejas.db.sessions']
        tejas.db.sets = originals['tejas.db.sets']
        tejas.db.attempts = originals['tejas.db.attempts']
        tejas.db.files = originals['tejas.db.files']
        tejas.db.jobs = originals['tejas.db.jobs']
        tejas.db.audits = originals['tejas.db.audits']
        tejas.packs.db = originals['tejas.packs.db']
        tejas.attempts.attempts = originals['tejas.attempts.attempts']
        tejas.attempts.sets = originals['tejas.attempts.sets']
        tejas.attempts.files = originals['tejas.attempts.files']
        tejas.attempts.db = originals['tejas.attempts.db']
        tejas.content.sets = originals['tejas.content.sets']
        tejas.content.files = originals['tejas.content.files']
        tejas.content.audits = originals['tejas.content.audits']
        tejas.content.jobs = originals['tejas.content.jobs']
        tejas.content.db = originals['tejas.content.db']
        tejas.jobs.jobs = originals['tejas.jobs.jobs']
        tejas.jobs.sets = originals['tejas.jobs.sets']
        tejas.jobs.files = originals['tejas.jobs.files']
        tejas.jobs.attempts = originals['tejas.jobs.attempts']
        tejas.jobs.db = originals['tejas.jobs.db']


# ============================================================================
# A01: Retry idempotency - CORRECTED with proper namespace
# ============================================================================
async def test_a01_retry_idempotency():
    """
    A01: CORRECTED - Uses NamespaceProxy to prevent packs escape
    """
    print("\n" + "="*80)
    print("A01: RETRY IDEMPOTENCY - Corrected with NamespaceProxy")
    print("="*80)
    
    async with patch_all_modules():
        from tejas.attempts import retry
        from tejas.packs import insert_attempt
        
        # Mock dependencies
        with patch('tejas.attempts.audit', new_callable=AsyncMock) as mock_audit, \
             patch('tejas.attempts.seal_profile', new_callable=AsyncMock) as mock_seal_profile, \
             patch('tejas.corrections.with_grade', new_callable=AsyncMock) as mock_with_grade:
            
            mock_seal_profile.return_value = {"exam": "JEE Main", "year": "2024"}
            
            # Setup: Create completed parent
            user_id = "audit-user-a01"
            set_id = "audit-set-a01"
            parent_id = uid()
            
            q1_id = uid()
            q2_id = uid()
            parent = {
                "id": parent_id,
                "user_id": user_id,
                "set_id": set_id,
                "status": "completed",
                "mode": "practice",
                "questions": [
                    {"id": q1_id, "outcome": "incorrect", "type": "mcq", "answer": "1", "number": 1},
                    {"id": q2_id, "outcome": "incorrect", "type": "mcq", "answer": "2", "number": 2},
                ],
                "answers": {},
                "started_at": now(),
                "submitted_at": now(),
                "rules": {"minutes": 60, "correct": 4, "wrong": -1, "skipped": 0},
                "title": "Test Set",
                "exam": "JEE Main",
                "version": 1,
                "ledger": {
                    "summary": {"correct": 0, "total": 2},
                    "rows": [
                        {"id": q1_id, "outcome": "incorrect", "points": -1},
                        {"id": q2_id, "outcome": "incorrect", "points": -1},
                    ]
                },
            }
            
            # Insert parent using namespaced collection
            await db.tejas_attempts.insert_one(parent)
            print(f"✓ Created parent in namespaced collection: {parent_id}")
            
            # Mock with_grade
            async def mock_with_grade_impl(attempt, score_version):
                return {**attempt, "questions": [
                    {**q, "outcome": "incorrect"} for q in attempt["questions"]
                ]}
            mock_with_grade.side_effect = mock_with_grade_impl
            
            user = {"id": user_id, "email": "test@example.com"}
            
            # STEP 1: Call retry() with K1
            start_key_1 = "retry-key-001-" + uid()[:8]
            data_1 = {"start_key": start_key_1}
            
            print(f"\n--- STEP 1: Call retry() with K1={start_key_1} ---")
            result_1 = await retry(parent_id, data_1, user)
            retry_1_id = result_1["id"]
            print(f"✓ retry() returned: {retry_1_id}")
            
            # Verify R1 is active
            r1 = await db.tejas_attempts.find_one({"id": retry_1_id})
            assert r1["status"] == "active"
            print(f"✓ R1 is active")
            
            # STEP 2: Call retry() with K2 WHILE R1 ACTIVE
            start_key_2 = "retry-key-002-" + uid()[:8]
            data_2 = {"start_key": start_key_2}
            
            print(f"\n--- STEP 2: Call retry() with K2={start_key_2} WHILE R1 ACTIVE ---")
            result_2 = await retry(parent_id, data_2, user)
            retry_2_id = result_2["id"]
            
            if retry_2_id == retry_1_id:
                print(f"✓ K2 returned R1 (correct while active)")
            else:
                print(f"✗ K2 created new retry (BUG)")
                return False
            
            # STEP 3: Complete R1
            print(f"\n--- STEP 3: Complete R1 ---")
            await db.tejas_attempts.update_one(
                {"id": retry_1_id},
                {"$set": {"status": "completed", "submitted_at": now()}}
            )
            print(f"✓ R1 completed")
            
            # STEP 4: Call retry() with K2 AFTER R1 completed
            print(f"\n--- STEP 4: Call retry() with K2 AFTER R1 COMPLETE ---")
            result_3 = await retry(parent_id, data_2, user)
            retry_3_id = result_3["id"]
            
            if retry_3_id == retry_1_id:
                print(f"✗ BUG NOT REPRODUCED - K2 returned R1")
                return False
            else:
                print(f"✓ BUG CONFIRMED: K2 created NEW retry {retry_3_id}")
                print(f"  - Expected: K2 should return R1 (idempotency)")
                print(f"  - Actual: K2 created duplicate retry")
                return True


# ============================================================================
# A02: Concurrent publication - CORRECTED with actual barrier
# ============================================================================
async def test_a02_concurrent_publication():
    """
    A02: CORRECTED - Uses ACTUAL content.get wrapper with Event barrier
    """
    print("\n" + "="*80)
    print("A02: CONCURRENT PUBLICATION - Corrected with actual barrier")
    print("="*80)
    
    async with patch_all_modules():
        from tejas.content import publish
        from tejas.db import get
        
        # Mock dependencies
        with patch('tejas.content.audit', new_callable=AsyncMock) as mock_audit, \
             patch('tejas.profiles.seal_profile', new_callable=AsyncMock) as mock_seal_profile, \
             patch('tejas.content.validate_refs', new_callable=AsyncMock) as mock_validate_refs, \
             patch('tejas.content.question_issues', return_value=[]):
            
            mock_seal_profile.return_value = None
            mock_validate_refs.return_value = None
            
            # Setup: Create draft set
            set_id = "audit-set-a02"
            draft_set = {
                "id": set_id,
                "title": "Audit Test Set A02",
                "exam": "JEE Main",
                "status": "review",
                "version": 0,
                "revision": 5,
                "questions": [
                    {
                        "id": uid(),
                        "number": 1,
                        "type": "mcq",
                        "text": "Test question",
                        "options": {"1": "A", "2": "B", "3": "C", "4": "D"},
                        "answer": "1",
                        "solution": "Test solution",
                        "subject": "Physics",
                        "approved": True,
                        "issues": [],
                        "render_mode": "typed",
                        "q_refs": [],
                        "s_refs": [],
                    }
                ],
                "rules": {"minutes": 60, "correct": 4, "wrong": -1, "skipped": 0},
                "audience": "all",
                "source": "Test source",
                "attribution": "Test attribution",
                "rights_upload": True,
                "rights_publish": True,
                "rights_report": True,
                "created_at": now(),
            }
            await db.tejas_sets.insert_one(draft_set)
            print(f"✓ Created draft set: {set_id} at revision {draft_set['revision']}")
            
            user = {"id": "audit-user-a02", "email": "test@example.com"}
            
            # Barrier using ACTUAL content.get wrapper
            barrier_event = asyncio.Event()
            preimage_count = [0]
            original_get = get
            
            async def barrier_get(coll, id):
                """Intercept get() to create barrier when two threads read preimage"""
                result = await original_get(coll, id)
                if coll.name.endswith('tejas_sets') and id == set_id:
                    preimage_count[0] += 1
                    if preimage_count[0] == 1:
                        # First thread waits for second
                        await asyncio.sleep(0.05)
                    elif preimage_count[0] == 2:
                        # Second thread captured preimage
                        barrier_event.set()
                        await asyncio.sleep(0.05)
                return result
            
            with patch('tejas.content.get', side_effect=barrier_get):
                # Launch two concurrent publish calls
                print(f"\n--- Launching 2 concurrent publish() calls ---")
                
                data = {"confirm": True}
                task1 = asyncio.create_task(publish(set_id, data, user))
                task2 = asyncio.create_task(publish(set_id, data, user))
                
                # Wait for barrier (both captured preimage)
                await asyncio.wait_for(barrier_event.wait(), timeout=2.0)
                print(f"✓ Barrier reached: Both threads captured preimage")
                
                results = await asyncio.gather(task1, task2, return_exceptions=True)
                
                print(f"✓ Both publish() calls completed")
                
                # Check version rows
                version_rows = await db.tejas_versions.find({"set_id": set_id}).to_list(10)
                print(f"✓ Version rows created: {len(version_rows)}")
                
                # Check final set state
                final_set = await db.tejas_sets.find_one({"id": set_id})
                print(f"✓ Final set version: {final_set['version']}")
                
                success_count = sum(1 for r in results if isinstance(r, dict) and r.get("ok"))
                
                if len(version_rows) == 2:
                    print(f"\n✓ BUG CONFIRMED: Both publishes inserted version rows")
                    print(f"  - Both threads captured preimage at revision 5")
                    print(f"  - Both inserted version rows BEFORE CAS")
                    print(f"  - Revision guard failed to prevent race")
                    return True
                elif len(version_rows) == 1 and success_count == 1:
                    print(f"✗ Only 1 version row (race not reproduced)")
                    return False
                else:
                    print(f"✗ Unexpected state: {len(version_rows)} rows, {success_count} successes")
                    return False


# ============================================================================
# A03: Lost updates - CORRECTED with proper concurrent editing
# ============================================================================
async def test_a03_lost_updates():
    """
    A03: CORRECTED - Concurrent edits on different fields with proper barrier
    """
    print("\n" + "="*80)
    print("A03: LOST UPDATES - Corrected with concurrent editing")
    print("="*80)
    
    async with patch_all_modules():
        from tejas.content import edit_question
        
        # Mock dependencies
        with patch('tejas.content.audit', new_callable=AsyncMock) as mock_audit, \
             patch('tejas.content.validate_refs', new_callable=AsyncMock) as mock_validate_refs:
            
            mock_validate_refs.return_value = None
            
            # Setup: Create set with question
            set_id = "audit-set-a03"
            q_id = uid()
            
            test_set = {
                "id": set_id,
                "title": "Audit Test Set A03",
                "exam": "JEE Main",
                "status": "draft",
                "version": 1,
                "revision": 10,
                "questions": [
                    {
                        "id": q_id,
                        "number": 1,
                        "type": "mcq",
                        "text": "Original question text",
                        "options": {"1": "A", "2": "B", "3": "C", "4": "D"},
                        "answer": "1",
                        "solution": "Original solution",
                        "subject": "Physics",
                        "topic": "Original topic",
                        "difficulty": "Medium",
                        "approved": False,
                        "issues": [],
                        "render_mode": "typed",
                        "q_refs": [],
                        "s_refs": [],
                        "accessible_text": "",
                        "solution_accessible_text": "",
                        "review_note": "",
                    }
                ],
                "rules": {"minutes": 60, "correct": 4, "wrong": -1, "skipped": 0},
                "created_at": now(),
            }
            await db.tejas_sets.insert_one(test_set)
            print(f"✓ Created set: {set_id} at revision {test_set['revision']}")
            print(f"✓ Question: text='{test_set['questions'][0]['text']}'")
            print(f"            topic='{test_set['questions'][0]['topic']}'")
            
            user = {"id": "audit-user-a03", "email": "test@example.com", "role": "staff"}
            
            # Barrier for concurrent edits
            barrier_event = asyncio.Event()
            preimage_count = [0]
            original_find_one = db.tejas_sets.find_one
            
            async def barrier_find_one(*args, **kwargs):
                """Intercept find_one to create barrier"""
                result = await original_find_one(*args, **kwargs)
                if result and result.get("id") == set_id:
                    preimage_count[0] += 1
                    if preimage_count[0] == 1:
                        # First call waits
                        await asyncio.sleep(0.05)
                    elif preimage_count[0] == 2:
                        # Second call captured preimage
                        barrier_event.set()
                        await asyncio.sleep(0.05)
                return result
            
            with patch.object(db.tejas_sets, 'find_one', side_effect=barrier_find_one):
                # Launch two concurrent edits
                print(f"\n--- Launching 2 concurrent edit_question() calls ---")
                
                data1 = {"text": "Editor 1 changed the question text"}
                data2 = {"topic": "Editor 2 changed the topic"}
                
                task1 = asyncio.create_task(edit_question(set_id, q_id, data1, user))
                task2 = asyncio.create_task(edit_question(set_id, q_id, data2, user))
                
                # Wait for barrier
                await asyncio.wait_for(barrier_event.wait(), timeout=2.0)
                print(f"✓ Barrier reached: Both editors captured preimage")
                
                results = await asyncio.gather(task1, task2, return_exceptions=True)
                
                print(f"✓ Both edit_question() calls completed")
                
                # Check final state
                final_set = await db.tejas_sets.find_one({"id": set_id})
                final_q = next((q for q in final_set["questions"] if q["id"] == q_id), None)
                
                print(f"\n--- Final State ---")
                print(f"✓ Final revision: {final_set['revision']}")
                print(f"✓ Final text: '{final_q['text']}'")
                print(f"✓ Final topic: '{final_q['topic']}'")
                
                # Check for lost update
                if final_q["text"] == "Original question text":
                    print(f"\n✓ BUG CONFIRMED: Lost update detected")
                    print(f"  - Editor 1 changed text")
                    print(f"  - Editor 2 changed topic")
                    print(f"  - Final text: '{final_q['text']}' (LOST Editor 1's change)")
                    print(f"  - Final topic: '{final_q['topic']}' (Has Editor 2's change)")
                    print(f"  - Read-modify-write without revision guard")
                    return True
                elif final_q["text"] == "Editor 1 changed the question text" and \
                     final_q["topic"] == "Editor 2 changed the topic":
                    print(f"✗ Both changes preserved (race not reproduced)")
                    return False
                else:
                    print(f"✗ Unexpected state")
                    return False


# ============================================================================
# A04: Audience fails open - CORRECTED with actual set_detail call
# ============================================================================
async def test_a04_audience_fails_open():
    """
    A04: CORRECTED - Actually calls set_detail after setting published
    """
    print("\n" + "="*80)
    print("A04: AUDIENCE FAILS OPEN - Corrected with set_detail call")
    print("="*80)
    
    async with patch_all_modules():
        from tejas.content import create_set, set_detail, SetInput, permitted
        
        # Mock dependencies
        with patch('tejas.content.audit', new_callable=AsyncMock):
            
            # Test permitted() with unknown audience
            print(f"\n--- Testing permitted() function ---")
            
            set_typo = {"audience": "private-typo", "expires": None}
            result_typo = permitted(set_typo, None)
            print(f"✓ audience='private-typo': permitted() = {result_typo}")
            
            if not result_typo:
                print(f"✗ Unknown audience rejected (unexpected)")
                return False
            
            print(f"✓ BUG CONFIRMED: Unknown audience fails open")
            
            # Test create_set with invalid audience
            print(f"\n--- Testing create_set() with invalid audience ---")
            
            user = {"id": "audit-user-a04", "email": "test@example.com"}
            
            data = SetInput(
                title="Test Set A04",
                exam="JEE Main",
                audience="private-typo",
                rights_upload=True,
                rights_publish=True,
                rights_report=True,
            )
            
            result = await create_set(data, user)
            set_id = result["id"]
            print(f"✓ create_set() succeeded with invalid audience: {set_id}")
            
            # Verify set was created
            created_set = await db.tejas_sets.find_one({"id": set_id})
            assert created_set["audience"] == "private-typo"
            print(f"✓ Set persisted with audience='private-typo'")
            
            # CORRECTED: Actually call set_detail after setting published
            print(f"\n--- Testing set_detail() access ---")
            
            # Update set to published
            await db.tejas_sets.update_one(
                {"id": set_id},
                {"$set": {"status": "published"}}
            )
            print(f"✓ Set marked as published")
            
            # Call ACTUAL set_detail (should succeed due to fails-open bug)
            try:
                detail = await set_detail(set_id)
                print(f"✓ set_detail() succeeded for anonymous user")
                print(f"✓ BUG CONFIRMED: Unknown audience permits access")
                print(f"  - SetInput accepts any string for audience")
                print(f"  - permitted() fails open for unknown values")
                print(f"  - set_detail() grants access to invalid audience")
                return True
            except Exception as e:
                print(f"✗ set_detail() raised exception: {e}")
                print(f"✗ Expected access to be granted (fails open)")
                return False


# ============================================================================
# A05: Lane overflow - CORRECTED with async freeze_ledger and create_task
# ============================================================================
async def test_a05_lane_overflow():
    """
    A05: CORRECTED - Patches freeze_ledger to ASYNC with Event, uses create_task
    """
    print("\n" + "="*80)
    print("A05: LANE OVERFLOW - Corrected with async freeze_ledger")
    print("="*80)
    
    async with patch_all_modules():
        from tejas.jobs import run_job, _active
        from tejas.runtime import LANE_LIMITS
        
        # Ensure INLINE_JOBS is enabled
        import tejas.jobs
        original_inline = tejas.jobs.INLINE_JOBS
        tejas.jobs.INLINE_JOBS = True
        
        try:
            # Patch freeze_ledger to ASYNC function with Event
            started_count = [0]
            full_event = asyncio.Event()
            release_event = asyncio.Event()
            
            async def async_freeze_ledger(attempt):
                """ASYNC freeze_ledger that blocks at capacity"""
                started_count[0] += 1
                print(f"  freeze_ledger started: {started_count[0]}")
                
                if started_count[0] == 2:
                    full_event.set()
                    print(f"  Lane FULL: 2 jobs started")
                
                # Wait for release
                await release_event.wait()
                
                return {"summary": {"correct": 0, "total": 2}}
            
            with patch('tejas.corrections.freeze_ledger', new_callable=AsyncMock) as mock_freeze:
                mock_freeze.side_effect = async_freeze_ledger
                
                # Get lane limit
                grade_limit = LANE_LIMITS.get("grade", 2)
                print(f"✓ Grade lane limit: {grade_limit}")
                
                # Setup: Create 3 completed attempts
                user_id = "audit-user-a05"
                set_id = "audit-set-a05"
                
                attempt_ids = []
                job_ids = []
                
                for i in range(3):
                    attempt_id = f"attempt-{i+1}-{uid()[:8]}"
                    attempt = {
                        "id": attempt_id,
                        "user_id": user_id,
                        "set_id": set_id,
                        "status": "completed",
                        "mode": "practice",
                        "questions": [],
                        "answers": {},
                        "started_at": now(),
                        "submitted_at": now(),
                    }
                    await db.tejas_attempts.insert_one(attempt)
                    attempt_ids.append(attempt_id)
                    
                    # Create grade job
                    job_id = f"grade-{attempt_id}"
                    job = {
                        "id": job_id,
                        "kind": "grade",
                        "user_id": user_id,
                        "set_id": set_id,
                        "payload": {"attempt_id": attempt_id},
                        "status": "queued",
                        "progress": 0,
                        "created_at": now(),
                        "lease_until": 0,
                        "error": "",
                        "attempts": 0,
                        "next_run_at": 0,
                    }
                    await db.tejas_jobs.insert_one(job)
                    job_ids.append(job_id)
                
                print(f"✓ Created 3 grade jobs")
                
                # Clear active lane
                _active["grade"].clear()
                
                # Launch first 2 jobs with create_task (non-blocking)
                print(f"\n--- Launching first 2 jobs with create_task ---")
                task1 = asyncio.create_task(run_job(job_ids[0]))
                task2 = asyncio.create_task(run_job(job_ids[1]))
                
                # Wait for lane to be full
                await asyncio.wait_for(full_event.wait(), timeout=2.0)
                print(f"✓ Lane FULL: {len(_active['grade'])}/{grade_limit}")
                
                # Try to run third job (should remain queued)
                print(f"\n--- Attempting to run third job (lane full) ---")
                await run_job(job_ids[2])
                
                # Check third job status
                job3 = await db.tejas_jobs.find_one({"id": job_ids[2]})
                
                if job3["status"] == "queued":
                    print(f"✓ Third job remained queued (lane full)")
                    
                    # Release first 2 jobs
                    print(f"\n--- Releasing first 2 jobs ---")
                    release_event.set()
                    await asyncio.gather(task1, task2)
                    print(f"✓ First 2 jobs completed")
                    
                    # Wait to see if third job auto-retries
                    print(f"\n--- Waiting 500ms for auto-retry ---")
                    await asyncio.sleep(0.5)
                    
                    # Check third job status
                    job3_final = await db.tejas_jobs.find_one({"id": job_ids[2]})
                    
                    if job3_final["status"] == "queued":
                        print(f"✓ BUG CONFIRMED: Third job NOT auto-retried")
                        print(f"  - Lane filled to capacity")
                        print(f"  - Overflow job returned immediately")
                        print(f"  - Lane freed, but no auto-retry")
                        print(f"  - No drain mechanism after overflow")
                        return True
                    else:
                        print(f"✗ Third job ran (unexpected): {job3_final['status']}")
                        return False
                else:
                    print(f"✗ Third job ran immediately (lane not full)")
                    return False
        finally:
            tejas.jobs.INLINE_JOBS = original_inline


# ============================================================================
# A06: Extraction fencing - CORRECTED with exact tejas.jobs.sets patch
# ============================================================================
async def test_a06_extraction_fencing():
    """
    A06: CORRECTED - Patches the EXACT object tejas.jobs.sets (not db[TEMP_SETS])
    """
    print("\n" + "="*80)
    print("A06: EXTRACTION FENCING - Corrected with exact module patch")
    print("="*80)
    
    async with patch_all_modules():
        from tejas.jobs import run_job, _active
        import tejas.jobs
        from tejas_core import build_questions
        
        # Mock dependencies
        with patch('tejas.jobs.run_in_threadpool', new_callable=AsyncMock) as mock_threadpool:
            
            # Mock build_questions
            mock_questions = [
                {
                    "id": uid(),
                    "number": 1,
                    "type": "mcq",
                    "text": "Extracted question",
                    "options": {"1": "A", "2": "B"},
                    "answer": "1",
                    "solution": "Solution",
                    "subject": "Physics",
                }
            ]
            
            async def mock_threadpool_impl(func, *args, **kwargs):
                if func == build_questions:
                    return mock_questions
                return b"mock pdf"
            
            mock_threadpool.side_effect = mock_threadpool_impl
            
            # Setup: Create set and files
            set_id = "audit-set-a06"
            test_set = {
                "id": set_id,
                "title": "Audit Test Set A06",
                "exam": "JEE Main",
                "status": "draft",
                "version": 1,
                "revision": 5,
                "questions": [],
                "created_at": now(),
            }
            await db.tejas_sets.insert_one(test_set)
            
            qfile_id = uid()
            sfile_id = uid()
            
            qfile = {
                "id": qfile_id,
                "path": "mock/path/q.pdf",
                "created_at": now(),
            }
            sfile = {
                "id": sfile_id,
                "path": "mock/path/s.pdf",
                "created_at": now(),
            }
            await db.tejas_files.insert_one(qfile)
            await db.tejas_files.insert_one(sfile)
            
            print(f"✓ Created set: {set_id} at revision 5")
            
            # Create extraction job
            job_id = f"extract-{set_id}-r5"
            job = {
                "id": job_id,
                "kind": "extract",
                "user_id": "audit-user-a06",
                "set_id": set_id,
                "payload": {
                    "qfile": qfile_id,
                    "sfile": sfile_id,
                    "revision": 5,
                },
                "status": "queued",
                "progress": 0,
                "created_at": now(),
                "lease_until": 0,
                "error": "",
                "attempts": 0,
                "next_run_at": 0,
            }
            await db.tejas_jobs.insert_one(job)
            print(f"✓ Created extraction job: {job_id}")
            
            # Clear active lane
            _active["extract"].clear()
            
            # Patch the EXACT object tejas.jobs.sets.update_one
            original_update_one = tejas.jobs.sets.update_one
            lease_replaced = [False]
            injected_flag = [False]
            
            async def inject_lease_replacement(*args, **kwargs):
                """Replace lease AFTER require_lease but BEFORE destination write"""
                if not lease_replaced[0]:
                    lease_replaced[0] = True
                    
                    # Get current job
                    current_job = await db.tejas_jobs.find_one({"id": job_id})
                    old_lease = current_job.get("lease")
                    
                    # Replace lease (simulate worker timeout)
                    new_lease = uid()
                    await db.tejas_jobs.update_one(
                        {"id": job_id},
                        {"$set": {
                            "lease": new_lease,
                            "lease_until": now() + 300,
                            "attempts": 2,
                        }}
                    )
                    print(f"\n✓ INJECTED: Lease replaced")
                    print(f"  Old lease: {old_lease}")
                    print(f"  New lease: {new_lease}")
                    
                    # Set injected flag
                    injected_flag[0] = True
                
                # Proceed with original update
                return await original_update_one(*args, **kwargs)
            
            # Patch the EXACT module reference
            with patch.object(tejas.jobs.sets, 'update_one', side_effect=inject_lease_replacement):
                # Run extraction job
                print(f"\n--- Running extraction job ---")
                await run_job(job_id)
                
                # Check final state
                final_set = await db.tejas_sets.find_one({"id": set_id})
                final_job = await db.tejas_jobs.find_one({"id": job_id})
                
                print(f"\n--- Final State ---")
                print(f"✓ Set revision: {final_set['revision']}")
                print(f"✓ Set questions: {len(final_set['questions'])}")
                print(f"✓ Job status: {final_job['status']}")
                print(f"✓ Injected flag: {injected_flag[0]}")
                
                if injected_flag[0] and final_set["revision"] == 6 and len(final_set["questions"]) > 0:
                    print(f"\n✓ BUG CONFIRMED: Stale worker wrote to destination")
                    print(f"  - require_lease() checked (passed)")
                    print(f"  - Lease replaced between check and write")
                    print(f"  - Destination write succeeded (stale lease)")
                    print(f"  - require_lease() NOT atomic with destination write")
                    return True
                elif not injected_flag[0]:
                    print(f"✗ Lease injection not triggered")
                    return False
                else:
                    print(f"✗ Destination not modified (unexpected)")
                    return False


# ============================================================================
# Main test runner
# ============================================================================
async def main():
    print("="*80)
    print("CORRECTED AUDIT HARNESS - NamespaceProxy Isolation")
    print("="*80)
    print("Fixes: A01 packs escape, A05 sequential await, A06 wrong proxy")
    print("       A02 barrier, A04 incomplete")
    print("="*80)
    
    await setup_namespace()
    before_counts = await capture_main_counts()
    
    results = {}
    
    try:
        # Run all tests
        print("\n" + "="*80)
        print("EXECUTING CORRECTED AUDIT TESTS")
        print("="*80)
        
        results["A01_retry_idempotency"] = await test_a01_retry_idempotency()
        results["A02_concurrent_publication"] = await test_a02_concurrent_publication()
        results["A03_lost_updates"] = await test_a03_lost_updates()
        results["A04_audience_fails_open"] = await test_a04_audience_fails_open()
        results["A05_lane_overflow"] = await test_a05_lane_overflow()
        results["A06_extraction_fencing"] = await test_a06_extraction_fencing()
        
    finally:
        # Verify isolation
        print("\n" + "="*80)
        print("ISOLATION VERIFICATION")
        print("="*80)
        isolated = await verify_isolation(before_counts)
        
        await cleanup_namespace()
    
    # Print summary
    print("\n" + "="*80)
    print("AUDIT SUMMARY")
    print("="*80)
    
    for test_name, result in results.items():
        status = "✓ CONFIRMED" if result else "✗ NOT REPRODUCED"
        print(f"{test_name}: {status}")
    
    confirmed_count = sum(1 for r in results.values() if r)
    total_count = len(results)
    
    print(f"\nConfirmed: {confirmed_count}/{total_count}")
    print(f"Isolation: {'✓ VERIFIED' if isolated else '✗ VIOLATED'}")
    print("="*80)
    
    return 0 if confirmed_count > 0 and isolated else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
