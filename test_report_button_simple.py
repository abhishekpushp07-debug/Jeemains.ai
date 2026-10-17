#!/usr/bin/env python3
"""
Test ReportButton fix: Inject failed report job for existing attempt
"""
import asyncio
import sys
import os

# Set environment variables
os.environ['MONGO_URL'] = 'mongodb://localhost:27017'
os.environ['DB_NAME'] = 'test_database'

from motor.motor_asyncio import AsyncIOMotorClient

async def inject_failed_job():
    """Inject a failed report job for the existing attempt"""
    
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client.test_database
    
    print("=== Injecting failed report job ===")
    
    # Use the attempt from Test 1
    attempt_id = '273f767b-efe3-47b2-9f0f-b14d7ed837be'
    
    # Get attempt details
    attempt = await db.tejas_attempts.find_one({'id': attempt_id})
    if not attempt:
        print(f"❌ Attempt not found: {attempt_id}")
        return None
    
    print(f"✓ Found attempt: {attempt_id}")
    print(f"  User: {attempt['user_id']}")
    print(f"  Set: {attempt['set_id']}")
    print(f"  Status: {attempt['status']}")
    
    # Delete any existing report job
    job_id = f"report-{attempt_id}-original"
    existing = await db.tejas_jobs.find_one({'id': job_id})
    if existing:
        print(f"  Deleting existing job: {job_id}")
        await db.tejas_jobs.delete_one({'id': job_id})
    
    # Inject a FAILED report job
    import time
    now_ts = int(time.time())
    
    failed_job = {
        'id': job_id,
        'kind': 'report',
        'user_id': attempt['user_id'],
        'set_id': attempt['set_id'],
        'payload': {
            'attempt_id': attempt_id,
            'score_version': 'original'
        },
        'status': 'failed',
        'progress': 0,
        'created_at': now_ts - 200,
        'lease_until': 0,
        'error': 'Simulated failure for testing retry flow',
        'attempts': 3,  # Max attempts reached
        'next_run_at': 0,
        'finished_at': now_ts - 100,
        'message': '',
        # NO 'path' field - this is the key part
    }
    
    await db.tejas_jobs.insert_one(failed_job)
    print(f"✓ Injected failed report job: {job_id}")
    print(f"  - status: failed")
    print(f"  - attempts: 3")
    print(f"  - no path field")
    print(f"  - error: {failed_job['error']}")
    
    print(f"\n=== Setup complete ===")
    print(f"Attempt ID: {attempt_id}")
    print(f"Job ID: {job_id}")
    print(f"Results URL: https://campus-launch-2.preview.emergentagent.com/results/{attempt_id}")
    print(f"\nNext: Open browser to results page and click Download button")
    print(f"Expected: ReportButton should call POST /jobs/{{id}}/retry, then download PDF")
    
    return attempt_id

if __name__ == '__main__':
    attempt_id = asyncio.run(inject_failed_job())
    if attempt_id:
        print(f"\n✓ Test setup successful")
    else:
        print("\n❌ Test setup failed")
        sys.exit(1)
