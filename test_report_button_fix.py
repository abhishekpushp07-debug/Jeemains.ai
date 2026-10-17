#!/usr/bin/env python3
"""
Test ReportButton fix: Inject failed report job and verify retry flow
"""
import asyncio
import sys
import os

# Set environment variables before importing tejas modules
os.environ['MONGO_URL'] = 'mongodb://localhost:27017'
os.environ['DB_NAME'] = 'test_database'

sys.path.insert(0, '/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient
from tejas.db import uid, now

async def setup_failed_report_test():
    """Create a QA attempt and inject a failed report job"""
    
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client.test_database
    
    print("=== Setting up ReportButton fix test ===")
    
    # Get user ID for phone +12025550184
    phone_profile = await db.tejas_phone_profiles.find_one({'phone': '+12025550184'})
    if not phone_profile:
        print("❌ Phone profile not found for +12025550184")
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
    
    # Create a fresh QA attempt (finalized, no existing report)
    attempt_id = uid()
    print(f"✓ Creating QA attempt: {attempt_id}")
    
    # Create minimal finalized attempt
    attempt = {
        'id': attempt_id,
        'user_id': user_id,
        'set_id': set_id,
        'title': s['title'] + ' - QA Report Test',
        'exam': s['exam'],
        'version': s['version'],
        'rules': s['rules'],
        'mode': 'practice',
        'status': 'completed',
        'qa_only': True,  # Mark as QA test
        'questions': s['questions'][:3],  # Just first 3 questions
        'answers': {s['questions'][0]['id']: {'value': s['questions'][0]['answer'], 'at': now() - 400}},  # One correct answer
        'started_at': now() - 600,
        'submitted_at': now() - 300,
        'sealed_at': now() - 300,
        'sealed_seq': 1,
        'receipt': attempt_id,
        'reason': 'submitted',
        'grading_status': 'ready',
        'report_allowed': True,
        'attribution': s.get('attribution', ''),
        'visited': [s['questions'][0]['id']],
        'server_seq': 1,
        'command_count': 1,
        'profile': {'exam': s['exam'], 'year': '2024'},
        'deadline': 0,
        'parent_attempt': None,
    }
    
    # Insert attempt
    await db.tejas_attempts.insert_one(attempt)
    print(f"✓ Created finalized attempt: {attempt_id}")
    
    # Create a simple ledger so grading is "ready"
    from tejas_core import score_attempt
    ledger = score_attempt(attempt)
    await db.tejas_ledgers.insert_one({'id': attempt_id, **ledger})
    print(f"✓ Created ledger with score: {ledger['summary']['score']}/{ledger['summary']['maximum']}")
    
    # Now inject a FAILED report job
    job_id = f"report-{attempt_id}-original"
    failed_job = {
        'id': job_id,
        'kind': 'report',
        'user_id': user_id,
        'set_id': set_id,
        'payload': {
            'attempt_id': attempt_id,
            'score_version': 'original'
        },
        'status': 'failed',
        'progress': 0,
        'created_at': now() - 200,
        'lease_until': 0,
        'error': 'Simulated failure for testing retry flow',
        'attempts': 3,  # Max attempts reached
        'next_run_at': 0,
        'finished_at': now() - 100,
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
    
    return attempt_id

if __name__ == '__main__':
    attempt_id = asyncio.run(setup_failed_report_test())
    if attempt_id:
        print(f"\n✓ Test setup successful")
        print(f"Next: Open browser to results page and click Download button")
        print(f"Expected: ReportButton should call POST /jobs/{{id}}/retry, then download PDF")
    else:
        print("\n❌ Test setup failed")
        sys.exit(1)
