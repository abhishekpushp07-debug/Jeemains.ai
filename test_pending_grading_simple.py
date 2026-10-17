#!/usr/bin/env python3
"""
Test pending grading UI: Use existing attempt and inject delayed grade job
"""
import asyncio
import sys
import os
import time

os.environ['MONGO_URL'] = 'mongodb://localhost:27017'
os.environ['DB_NAME'] = 'test_database'

from motor.motor_asyncio import AsyncIOMotorClient

async def setup_pending_grading_simple():
    """Use existing completed attempt and inject delayed grade job"""
    
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client.test_database
    
    print("=== Setting up pending grading UI test (simple) ===")
    
    # Use the existing attempt from Test 1
    attempt_id = '273f767b-efe3-47b2-9f0f-b14d7ed837be'
    
    # Get attempt
    attempt = await db.tejas_attempts.find_one({'id': attempt_id})
    if not attempt:
        print(f"❌ Attempt not found: {attempt_id}")
        return None
    
    print(f"✓ Found attempt: {attempt_id}")
    print(f"  User: {attempt['user_id']}")
    print(f"  Status: {attempt['status']}")
    
    now_ts = int(time.time())
    
    # Delete existing ledger to simulate pending grading
    ledger_result = await db.tejas_ledgers.delete_one({'id': attempt_id})
    if ledger_result.deleted_count > 0:
        print(f"✓ Deleted existing ledger")
    
    # Update attempt to set grading_status to queued
    await db.tejas_attempts.update_one(
        {'id': attempt_id},
        {'$set': {'grading_status': 'queued'}}
    )
    print(f"✓ Updated attempt grading_status to 'queued'")
    
    # Delete any existing grade job
    job_id = f"grade-{attempt_id}"
    await db.tejas_jobs.delete_one({'id': job_id})
    
    # Create grade job with delay
    grade_job = {
        'id': job_id,
        'kind': 'grade',
        'user_id': attempt['user_id'],
        'set_id': attempt['set_id'],
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
    attempt_id = asyncio.run(setup_pending_grading_simple())
    if attempt_id:
        print(f"\n✓ Test setup successful")
    else:
        print("\n❌ Test setup failed")
        sys.exit(1)
