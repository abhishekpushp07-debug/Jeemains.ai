"""
A06 AUDIT: Extraction destination fencing gap
SCOPE: Isolated test with simulated lease replacement
RULE: jobs.py extraction should fence destination writes with lease check

HYPOTHESIS: require_lease() checks job lease, then sets.update_one() writes.
            If lease is replaced between check and write, stale worker can
            still modify sets collection even though job CAS would fail.
            
ISOLATION: Uses audit_jobs_a06 and audit_sets_a06 temporary collections
"""
import asyncio
import sys
import os
sys.path.insert(0, '/app/backend')

# Load environment variables
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

from motor.motor_asyncio import AsyncIOMotorClient
from tejas.db import uid, now

TEMP_JOBS = "audit_jobs_a06"
TEMP_SETS = "audit_sets_a06"

async def test_extraction_fencing():
    """Test if stale worker can write to sets after lease replacement"""
    
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client.get_database(os.environ["DB_NAME"])
    temp_jobs = db[TEMP_JOBS]
    temp_sets = db[TEMP_SETS]
    
    try:
        # Setup: Create a set and extraction job
        set_id = "audit-set-a06"
        job_id = "extract-audit-a06"
        
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
        await temp_sets.insert_one(test_set)
        print(f"✓ Created set: {set_id} at revision {test_set['revision']}")
        
        # Create extraction job with lease
        worker1_lease = uid()
        extraction_job = {
            "id": job_id,
            "kind": "extract",
            "user_id": "audit-user-a06",
            "set_id": set_id,
            "payload": {
                "qfile": "file-1",
                "sfile": "file-2",
                "revision": 5,
            },
            "status": "running",
            "progress": 50,
            "created_at": now(),
            "lease_until": now() + 300,
            "lease": worker1_lease,
            "error": "",
            "attempts": 1,
        }
        await temp_jobs.insert_one(extraction_job)
        print(f"✓ Created extraction job: {job_id}")
        print(f"✓ Worker 1 lease: {worker1_lease}")
        
        # Simulate extraction processing (lines 84-94)
        print(f"\n--- Worker 1: Processing extraction ---")
        
        # Worker 1: Extract questions (simulated)
        extracted_questions = [
            {
                "id": uid(),
                "number": 1,
                "type": "mcq",
                "text": "Extracted question 1",
                "options": {"1": "A", "2": "B"},
                "answer": "1",
                "solution": "Solution 1",
                "subject": "Physics",
            }
        ]
        print(f"✓ Worker 1: Extracted {len(extracted_questions)} questions")
        
        # Worker 1: Call require_lease() before destination write (line 89)
        print(f"\n--- Worker 1: Checking lease before destination write ---")
        
        # Simulate require_lease() check (lines 45-47)
        lease_check = await temp_jobs.find_one({
            "id": job_id,
            "lease": worker1_lease,
            "status": "running",
            "lease_until": {"$gt": now()}
        }, {"_id": 1})
        
        if lease_check:
            print(f"✓ Worker 1: Lease valid at line 89 (before destination write)")
        else:
            print(f"✗ Worker 1: Lease check failed")
            return False
        
        # CRITICAL WINDOW: Between lease check and destination write
        print(f"\n--- CRITICAL WINDOW: Lease replacement occurs ---")
        
        # Simulate lease replacement (e.g., worker timeout, retry)
        worker2_lease = uid()
        await temp_jobs.update_one(
            {"id": job_id},
            {"$set": {
                "lease": worker2_lease,
                "lease_until": now() + 300,
                "attempts": 2,
            }}
        )
        print(f"✓ Worker 2 acquired lease: {worker2_lease}")
        print(f"✓ Worker 1 lease {worker1_lease} is now STALE")
        
        # Worker 1: Proceed with destination write (line 91)
        # This happens AFTER lease check but BEFORE final job CAS
        print(f"\n--- Worker 1: Writing to destination (sets collection) ---")
        
        guard = {"id": set_id, "revision": extraction_job["payload"]["revision"]}
        
        # This is the VULNERABILITY: sets.update_one has NO lease guard
        updated = await temp_sets.update_one(
            guard,
            {"$set": {
                "questions": extracted_questions,
                "status": "review"
            }, "$inc": {"revision": 1}}
        )
        
        if updated.modified_count:
            print(f"✓ Worker 1: Destination write SUCCEEDED (stale worker wrote to sets)")
            print(f"  - Worker 1 lease is stale: {worker1_lease}")
            print(f"  - Current lease is: {worker2_lease}")
            print(f"  - sets.update_one() has NO lease guard")
        else:
            print(f"✗ Worker 1: Destination write failed")
            return False
        
        # Worker 1: Try to complete job with CAS (lines 120)
        print(f"\n--- Worker 1: Attempting job completion CAS ---")
        
        completed = await temp_jobs.update_one(
            {
                "id": job_id,
                "lease": worker1_lease,  # Stale lease
                "status": "running",
                "lease_until": {"$gt": now()}
            },
            {"$set": {
                "status": "done",
                "progress": 100,
                "message": "Extraction completed",
                "finished_at": now(),
            }}
        )
        
        if completed.modified_count:
            print(f"✗ Worker 1: Job CAS succeeded (unexpected)")
            return False
        else:
            print(f"✓ Worker 1: Job CAS FAILED (lease guard worked)")
            print(f"  - Job status remains 'running'")
            print(f"  - But destination (sets) was already modified!")
        
        # Verify final state
        final_set = await temp_sets.find_one({"id": set_id})
        final_job = await temp_jobs.find_one({"id": job_id})
        
        print(f"\n--- Final State ---")
        print(f"✓ Set revision: {final_set['revision']} (incremented)")
        print(f"✓ Set questions: {len(final_set['questions'])} (modified by stale worker)")
        print(f"✓ Job status: {final_job['status']} (still running)")
        print(f"✓ Job lease: {final_job['lease']} (Worker 2's lease)")
        
        # VULNERABILITY confirmed
        print(f"\n⚠ VULNERABILITY CONFIRMED:")
        print(f"  - Worker 1 checked lease at line 89 (valid)")
        print(f"  - Lease replaced between check and destination write")
        print(f"  - Worker 1 wrote to sets collection (line 91) with stale lease")
        print(f"  - Worker 1's job CAS failed (line 120) but damage done")
        print(f"  - sets.update_one() has NO lease guard, only revision guard")
        print(f"\n✓ AUDIT FINDING: jobs.py lines 89-91 (extraction destination write)")
        print(f"  require_lease() check at line 89 is NOT atomic with sets.update_one() at line 91")
        print(f"  Stale worker can modify destination even if job CAS fails")
        print(f"  Destination write should include lease guard or use fenced token")
        
        # Check if Worker 2 would overwrite
        print(f"\n--- Worker 2: Would overwrite Worker 1's changes ---")
        print(f"  - Worker 2 has valid lease: {worker2_lease}")
        print(f"  - Worker 2 would extract different questions")
        print(f"  - Worker 2's destination write would succeed (revision guard)")
        print(f"  - Worker 2's job CAS would succeed (lease guard)")
        print(f"  - Result: Worker 1's extraction lost, Worker 2's wins")
        print(f"  - But Worker 1 already modified sets (race condition)")
        
        return True
            
    finally:
        # Cleanup
        await temp_jobs.drop()
        await temp_sets.drop()
        print(f"\n✓ Cleaned up temporary collections")

async def main():
    print("=" * 80)
    print("A06 AUDIT: Extraction Destination Fencing Gap")
    print("=" * 80)
    print("Testing: jobs.py lines 84-94 (extraction destination write)")
    print("Isolation: Temporary collections audit_jobs_a06, audit_sets_a06")
    print("=" * 80)
    print()
    
    result = await test_extraction_fencing()
    
    print("\n" + "=" * 80)
    if result:
        print("RESULT: CONFIRMED - Stale worker can write to destination")
        print("IMPACT: Lease check not atomic with destination write")
        print("LOCATION: jobs.py lines 89-91 (require_lease before sets.update_one)")
    else:
        print("RESULT: NOT REPRODUCED or TEST ERROR")
    print("=" * 80)
    
    return 0 if result else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
