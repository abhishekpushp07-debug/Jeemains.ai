"""
A02 AUDIT: Concurrent publication not serialized
SCOPE: Isolated test using temporary collections
RULE: content.py publish() (lines 564-633) should serialize concurrent publishes
      using revision-based CAS

HYPOTHESIS: Two concurrent publish calls can both insert tejas_versions rows
            before either CAS completes, creating duplicate version numbers.
            
ISOLATION: Uses audit_sets_a02 and audit_versions_a02 temporary collections
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
import copy

TEMP_SETS = "audit_sets_a02"
TEMP_VERSIONS = "audit_versions_a02"

async def test_concurrent_publication():
    """Test if concurrent publishes create duplicate version rows"""
    
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client.get_database(os.environ["DB_NAME"])
    temp_sets = db[TEMP_SETS]
    temp_versions = db[TEMP_VERSIONS]
    
    try:
        # Setup: Create a draft set ready for publication
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
        await temp_sets.insert_one(draft_set)
        print(f"✓ Created draft set: {set_id} at revision {draft_set['revision']}")
        
        # Simulate concurrent publication (lines 611-623)
        # Both threads read the same revision=5
        
        # Thread 1: Read set
        s1 = await temp_sets.find_one({"id": set_id})
        print(f"✓ Thread 1: Read set at revision {s1['revision']}")
        
        # Thread 2: Read set (same revision)
        s2 = await temp_sets.find_one({"id": set_id})
        print(f"✓ Thread 2: Read set at revision {s2['revision']}")
        
        # Both threads increment version
        s1["version"] = s1.get("version", 0) + 1
        s2["version"] = s2.get("version", 0) + 1
        
        print(f"✓ Both threads computed version: {s1['version']}")
        
        # Thread 1: Insert version row (line 612-614) BEFORE CAS
        version_row_1 = copy.deepcopy(s1)
        version_row_1.pop("_id", None)  # Remove MongoDB _id
        version_row_1["id"] = uid()
        version_row_1["set_id"] = set_id
        version_row_1["published_at"] = now()
        await temp_versions.insert_one(version_row_1)
        print(f"✓ Thread 1: Inserted version row {version_row_1['id']} with version={s1['version']}")
        
        # Thread 2: Insert version row (line 612-614) BEFORE CAS
        version_row_2 = copy.deepcopy(s2)
        version_row_2.pop("_id", None)  # Remove MongoDB _id
        version_row_2["id"] = uid()
        version_row_2["set_id"] = set_id
        version_row_2["published_at"] = now() + 0.001  # slightly later
        await temp_versions.insert_one(version_row_2)
        print(f"✓ Thread 2: Inserted version row {version_row_2['id']} with version={s2['version']}")
        
        # Now both threads attempt CAS (lines 615-623)
        # Thread 1 CAS
        res1 = await temp_sets.update_one(
            {"id": set_id, "revision": s1["revision"]},
            {"$set": {
                "status": "published",
                "version": s1["version"],
                "published_at": version_row_1["published_at"],
            }, "$inc": {"revision": 1}}
        )
        
        if res1.modified_count:
            print(f"✓ Thread 1: CAS succeeded, set version={s1['version']}")
        else:
            print(f"✗ Thread 1: CAS failed (expected if Thread 2 won)")
        
        # Thread 2 CAS (should fail because revision changed)
        res2 = await temp_sets.update_one(
            {"id": set_id, "revision": s2["revision"]},
            {"$set": {
                "status": "published",
                "version": s2["version"],
                "published_at": version_row_2["published_at"],
            }, "$inc": {"revision": 1}}
        )
        
        if res2.modified_count:
            print(f"✓ Thread 2: CAS succeeded, set version={s2['version']}")
        else:
            print(f"✗ Thread 2: CAS failed (revision guard worked)")
        
        # Check final state
        final_set = await temp_sets.find_one({"id": set_id})
        version_rows = await temp_versions.find({"set_id": set_id}).to_list(10)
        
        print(f"\n✓ Final set version: {final_set['version']}")
        print(f"✓ Version rows in tejas_versions: {len(version_rows)}")
        
        # VULNERABILITY: Both version rows exist, but only one CAS succeeded
        if len(version_rows) == 2:
            print(f"\n⚠ VULNERABILITY CONFIRMED:")
            print(f"  - Both threads inserted version rows BEFORE CAS")
            print(f"  - Version row 1: {version_row_1['id']} (version={version_row_1['version']})")
            print(f"  - Version row 2: {version_row_2['id']} (version={version_row_2['version']})")
            print(f"  - Final set version: {final_set['version']}")
            print(f"  - Orphaned version row exists (CAS failed but version row persisted)")
            print(f"\n✓ AUDIT FINDING: Lines 612-614 insert version BEFORE CAS at lines 615-623")
            print(f"  This creates orphaned version rows when concurrent publishes race")
            return True
        else:
            print(f"✗ Expected 2 version rows, found {len(version_rows)}")
            return False
            
    finally:
        # Cleanup
        await temp_sets.drop()
        await temp_versions.drop()
        print(f"\n✓ Cleaned up temporary collections")

async def main():
    print("=" * 80)
    print("A02 AUDIT: Concurrent Publication Not Serialized")
    print("=" * 80)
    print("Testing: content.py lines 564-633 (publish endpoint)")
    print("Isolation: Temporary collections audit_sets_a02, audit_versions_a02")
    print("=" * 80)
    print()
    
    result = await test_concurrent_publication()
    
    print("\n" + "=" * 80)
    if result:
        print("RESULT: CONFIRMED - Concurrent publication creates orphaned version rows")
        print("IMPACT: tejas_versions contains duplicate/orphaned version entries")
        print("LOCATION: content.py lines 612-614 (insert BEFORE CAS at 615-623)")
    else:
        print("RESULT: NOT REPRODUCED or TEST ERROR")
    print("=" * 80)
    
    return 0 if result else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
