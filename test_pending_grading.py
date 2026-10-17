#!/usr/bin/env python3
"""
Test pending grading UI: Create finalized attempt with delayed grade job
"""
import asyncio
import sys
import os
import time
import copy

os.environ['MONGO_URL'] = 'mongodb://localhost:27017'
os.environ['DB_NAME'] = 'test_database'

sys.path.insert(0, '/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient

async def setup_pending_grading_test():
    """Create a finalized attempt with delayed grade job"""
    
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client.test_database
    
    print("=== Setting up pending grading UI test ===")
    
    # Get user
    phone_profile = await db.tejas_phone_profiles.find_one({'phone': '+12025550184'})
    if not phone_profile:
        print("❌ Phone profile not found")
        return None
    
    user_id = phone_profile['id']
    print(f"✓ Found user: {user_id}")
    
    # Get set
    set_id = 'f565e4db-19bb-45c2-95ef-75b74bd985b6'
    s = await db.tejas_sets.find_one({'id': set_id})
    if not s:
        print(f"❌ Set not found: {set_id}")
        return None
    
    print(f"✓ Found set: {s['title']}")
    
    # Generate unique attempt ID
    import uuid
    attempt_id = str(uuid.uuid4())
    print(f"✓ Creating attempt: {attempt_id}")
    
    now_ts = int(time.time())
    
    # Create finalized attempt WITHOUT ledger
    attempt = {
        'id': attempt_id,
        'user_id': user_id,
        'set_id': set_id,
        'title': s['title'] + ' - Pending Grading Test',
        'exam': s['exam'],
        'version': s['version'],
        'rules': copy.deepcopy(s['rules']),
        'mode': 'practice',
        'status': 'completed',
        'qa_only': True,  # Mark as QA test
        'questions': copy.deepcopy(s['questions'][:5]),  # First 5 questions
        'answers': {
            s['questions'][0]['id']: {'value': s['questions'][0]['answer'], 'at': now_ts - 400},
            s['questions'][1]['id']: {'value': 'wrong', 'at': now_ts - 350},
        },
        'started_at': now_ts - 600,
        'submitted_at': now_ts - 10,
        'sealed_at': now_ts - 10,
        'sealed_seq': 2,
        'receipt': attempt_id,
        'reason': 'submitted',
        'grading_status': 'queued',  # Queued for grading
        'report_allowed': True,
        'attribution': s.get('attribution', ''),
        'visited': [s['questions'][0]['id'], s['questions'][1]['id']],
        'server_seq': 2,
        'command_count': 2,
        'profile': {'exam': s['exam'], 'year': '2024'},
        'deadline': 0,
        'parent_attempt': None,
    }
    
    # Insert attempt (NO ledger!)
    result = await db.tejas_attempts.insert_one(attempt)
    print(f"✓ Created finalized attempt: {attempt_id}")
    print(f"  - status: completed")
    print(f"  - grading_status: queued")
    print(f"  - NO ledger (grading pending)")
    
    # Create grade job with delay
    job_id = f"grade-{attempt_id}"
    grade_job = {
        'id': job_id,
        'kind': 'grade',
        'user_id': user_id,
        'set_id': set_id,
        'payload': {
            'attempt_id': attempt_id
        },
        'status': 'queued',
        'progress': 0,
        'created_at': now_ts - 5,
        'lease_until': 0,
        'error': '',
        'attempts': 0,
        'next_run_at': now_ts + 15,  # Run in 15 seconds
        'message': '',
    }
    
    await db.tejas_jobs.insert_one(grade_job)
    print(f"✓ Created grade job: {job_id}")
    print(f"  - status: queued")
    print(f"  - next_run_at: now + 15 seconds")
    
    print(f"\n=== Setup complete ===")
    print(f"Attempt ID: {attempt_id}")
    print(f"Job ID: {job_id}")
    print(f"Results URL: https://campus-launch-2.preview.emergentagent.com/results/{attempt_id}")
    print(f"\nNext: Open browser to results page")
    print(f"Expected: GET /api/attempts/{attempt_id}/results returns 202")
    print(f"Expected: UI shows results-grading-pending page with receipt")
    print(f"Expected: After ~15 seconds, grading completes and results appear")
    
    return attempt_id

if __name__ == '__main__':
    attempt_id = asyncio.run(setup_pending_grading_test())
    if attempt_id:
        print(f"\n✓ Test setup successful")
    else:
        print("\n❌ Test setup failed")
        sys.exit(1)
