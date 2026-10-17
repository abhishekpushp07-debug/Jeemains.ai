"""
A03 AUDIT: Lost updates in concurrent editing
SCOPE: Isolated test using temporary collection
RULE: content.py edit_question() (lines 471-519) should use revision guard
      to prevent lost updates

HYPOTHESIS: Two concurrent edits reading same revision can both succeed,
            with last-write-wins causing lost updates.
            
ISOLATION: Uses audit_sets_a03 temporary collection
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

TEMP_SETS = "audit_sets_a03"

async def test_concurrent_edits():
    """Test if concurrent question edits cause lost updates"""
    
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client.get_database(os.environ["DB_NAME"])
    temp_sets = db[TEMP_SETS]
    
    try:
        # Setup: Create a set with a question
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
        await temp_sets.insert_one(test_set)
        print(f"✓ Created set: {set_id} at revision {test_set['revision']}")
        print(f"✓ Question {q_id}: text='{test_set['questions'][0]['text']}'")
        print(f"                    topic='{test_set['questions'][0]['topic']}'")
        
        # Simulate concurrent edits (lines 471-519)
        
        # Editor 1: Read full set (line 473)
        s1 = await temp_sets.find_one({"id": set_id})
        old1 = next((q for q in s1["questions"] if q["id"] == q_id), None)
        print(f"\n✓ Editor 1: Read set at revision {s1['revision']}")
        
        # Editor 2: Read full set (same revision)
        s2 = await temp_sets.find_one({"id": set_id})
        old2 = next((q for q in s2["questions"] if q["id"] == q_id), None)
        print(f"✓ Editor 2: Read set at revision {s2['revision']}")
        
        # Editor 1: Modify question text (lines 498-511)
        data1 = {"text": "Editor 1 changed the question text"}
        q1 = {**old1, **{k: v for k, v in data1.items()}, "approved": False}
        q1["issues"] = []  # Simplified validation
        
        print(f"\n✓ Editor 1: Modified text to '{q1['text']}'")
        
        # Editor 2: Modify question topic (different field)
        data2 = {"topic": "Editor 2 changed the topic"}
        q2 = {**old2, **{k: v for k, v in data2.items()}, "approved": False}
        q2["issues"] = []
        
        print(f"✓ Editor 2: Modified topic to '{q2['topic']}'")
        
        # Editor 1: Update (lines 514-516) - NO revision guard on read
        res1 = await temp_sets.update_one(
            {"id": set_id, "questions.id": q_id},
            {"$set": {"questions.$": q1, "status": "review"}, "$inc": {"revision": 1}}
        )
        
        if res1.modified_count:
            print(f"\n✓ Editor 1: Update succeeded")
        else:
            print(f"✗ Editor 1: Update failed")
            return False
        
        # Check intermediate state
        intermediate = await temp_sets.find_one({"id": set_id})
        intermediate_q = next((q for q in intermediate["questions"] if q["id"] == q_id), None)
        print(f"✓ After Editor 1: revision={intermediate['revision']}")
        print(f"                   text='{intermediate_q['text']}'")
        print(f"                   topic='{intermediate_q['topic']}'")
        
        # Editor 2: Update (lines 514-516) - NO revision guard
        # This uses the OLD revision data (s2) which has original text
        res2 = await temp_sets.update_one(
            {"id": set_id, "questions.id": q_id},
            {"$set": {"questions.$": q2, "status": "review"}, "$inc": {"revision": 1}}
        )
        
        if res2.modified_count:
            print(f"\n✓ Editor 2: Update succeeded")
        else:
            print(f"✗ Editor 2: Update failed")
            return False
        
        # Check final state
        final = await temp_sets.find_one({"id": set_id})
        final_q = next((q for q in final["questions"] if q["id"] == q_id), None)
        
        print(f"\n✓ Final state: revision={final['revision']}")
        print(f"               text='{final_q['text']}'")
        print(f"               topic='{final_q['topic']}'")
        
        # VULNERABILITY: Editor 1's text change is LOST
        if final_q["text"] == "Original question text":
            print(f"\n⚠ VULNERABILITY CONFIRMED:")
            print(f"  - Editor 1 changed text to: 'Editor 1 changed the question text'")
            print(f"  - Editor 2 changed topic to: 'Editor 2 changed the topic'")
            print(f"  - Final text: '{final_q['text']}' (LOST Editor 1's change)")
            print(f"  - Final topic: '{final_q['topic']}' (Has Editor 2's change)")
            print(f"  - Both updates succeeded, but Editor 1's change was overwritten")
            print(f"\n✓ AUDIT FINDING: Lines 473-516 use read-modify-write without revision guard")
            print(f"  edit_question() merges changes into old full question object")
            print(f"  Concurrent edits cause last-write-wins, losing earlier changes")
            return True
        else:
            print(f"✗ Expected original text, found: '{final_q['text']}'")
            return False
            
    finally:
        # Cleanup
        await temp_sets.drop()
        print(f"\n✓ Cleaned up temporary collection")

async def main():
    print("=" * 80)
    print("A03 AUDIT: Lost Updates in Concurrent Editing")
    print("=" * 80)
    print("Testing: content.py lines 471-519 (edit_question endpoint)")
    print("Isolation: Temporary collection audit_sets_a03")
    print("=" * 80)
    print()
    
    result = await test_concurrent_edits()
    
    print("\n" + "=" * 80)
    if result:
        print("RESULT: CONFIRMED - Concurrent edits cause lost updates")
        print("IMPACT: Last-write-wins overwrites earlier changes to different fields")
        print("LOCATION: content.py lines 473-516 (no revision guard on read)")
    else:
        print("RESULT: NOT REPRODUCED or TEST ERROR")
    print("=" * 80)
    
    return 0 if result else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
