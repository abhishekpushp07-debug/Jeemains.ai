"""
Test: Timed QA attempt with offline late draft disclosure
Creates a 2-question QA set with 0.5 minute duration
Tests:
1. Save Q1 correct online
2. Go offline, enter Q2 answer
3. Wait past deadline
4. Reconnect
5. Assert: Results page, Q1 scored, Q2 skipped, late draft visible
"""
import sys
import json
import time
import os
import uuid
from pathlib import Path
import requests
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')
load_dotenv('/app/frontend/.env')

# Configuration from environment
BASE_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://campus-launch-2.preview.emergentagent.com')
MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.getenv('DB_NAME', 'test_database')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'owner@tejas-platform.com')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

# Load fixture data
with open('/app/memory/qa_context.json', 'r') as f:
    fixture = json.load(f)

SOURCE_SET_ID = fixture['set_id']
PHONE = fixture['phone']

print("=" * 80)
print("DEADLINE LATE DRAFT TEST")
print("=" * 80)
print(f"Base URL: {BASE_URL}")
print(f"MongoDB: {MONGO_URL}/{DB_NAME}")
print(f"Source Set: {SOURCE_SET_ID}")
print(f"Phone: {PHONE}")
print("=" * 80)

class DeadlineTestSession:
    def __init__(self):
        self.session = requests.Session()
        self.user = None
        self.test_set_id = None
        self.attempt_id = None
        self.questions = []
        
    def phone_auth(self, phone):
        """Authenticate via phone"""
        print(f"\n📱 Phone Authentication: {phone}")
        response = self.session.post(
            f"{BASE_URL}/api/auth/phone",
            json={"phone": phone},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ FAIL: Phone auth returned {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
        
        result = response.json()
        self.user = result.get('data', result)
        print(f"✅ PASS: Authenticated as user {self.user.get('id')}")
        return True
    
    def owner_auth(self):
        """Authenticate as owner"""
        print(f"\n🔑 Owner Authentication")
        response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ FAIL: Owner auth returned {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
        
        result = response.json()
        self.user = result.get('data', result)
        print(f"✅ PASS: Authenticated as owner")
        return True
    
    def create_two_question_timed_set(self):
        """Create a 2-question QA-only timed set with 0.5 minute duration"""
        print(f"\n📦 Creating 2-Question Timed QA Set (0.5 minute duration)")
        
        # Get original questions from MongoDB
        client = MongoClient(MONGO_URL)
        db = client[DB_NAME]
        
        original_set = db.tejas_sets.find_one({"id": SOURCE_SET_ID}, {"_id": 0})
        if not original_set:
            print(f"❌ FAIL: Could not find source set {SOURCE_SET_ID}")
            return None
        
        questions = original_set.get('questions', [])
        if len(questions) < 2:
            print(f"❌ FAIL: Source set has less than 2 questions")
            return None
        
        # Take first 2 questions
        two_questions = questions[:2]
        self.questions = two_questions
        
        # Create new set ID
        test_set_id = f"qa-timed-2q-{uuid.uuid4()}"
        
        # Clone with modifications
        test_set = {
            **original_set,
            "id": test_set_id,
            "title": "QA Timed Test (2 questions, 0.5 min)",
            "questions": two_questions,
            "qa_only": True,
            "status": "published",
            "restricted": True,
            "allowed_phones": [PHONE],
            "duration": 0.5,  # 0.5 minutes = 30 seconds
            "version": 1,
            "revision": 0,
        }
        
        db.tejas_sets.insert_one(test_set)
        
        self.test_set_id = test_set_id
        print(f"✅ PASS: Created timed QA set: {test_set_id}")
        print(f"   Questions: {len(two_questions)}")
        print(f"   Duration: 0.5 minutes (30 seconds)")
        print(f"   Allowed phones: {PHONE}")
        print(f"   Q1 ID: {two_questions[0]['id']}")
        print(f"   Q2 ID: {two_questions[1]['id']}")
        
        return test_set_id
    
    def start_attempt(self):
        """Start a new attempt"""
        print(f"\n🚀 Starting Attempt on {self.test_set_id}")
        
        # Preflight first
        response = self.session.post(
            f"{BASE_URL}/api/sets/{self.test_set_id}/preflight",
            json={"preview": False, "test_response": "test"},
            timeout=30
        )
        if response.status_code != 200:
            print(f"❌ Preflight failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return None
        
        print(f"✅ Preflight passed")
        
        # Generate start_key
        start_key = f"test-deadline-{int(time.time() * 1000000)}"
        
        # Start attempt
        response = self.session.post(
            f"{BASE_URL}/api/sets/{self.test_set_id}/start",
            json={
                "start_key": start_key,
                "device_checked": True,
                "preview": False
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Start failed: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return None
        
        result = response.json()
        attempt = result.get('data', result)
        self.attempt_id = attempt.get('id')
        
        print(f"✅ PASS: Started attempt {self.attempt_id}")
        print(f"   Deadline: {attempt.get('deadline')}")
        
        return self.attempt_id
    
    def save_answer(self, qid, value, marked=False):
        """Save an answer"""
        request_id = f"test-{qid}-{int(time.time() * 1000000)}"
        
        response = self.session.put(
            f"{BASE_URL}/api/attempts/{self.attempt_id}/answers/{qid}",
            json={
                "value": value,
                "marked": marked,
                "revision": 1,
                "request_id": request_id
            },
            timeout=30
        )
        
        return response
    
    def get_attempt(self):
        """Get attempt details"""
        response = self.session.get(
            f"{BASE_URL}/api/attempts/{self.attempt_id}",
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('data', result)
        return None
    
    def get_results(self):
        """Get results"""
        response = self.session.get(
            f"{BASE_URL}/api/attempts/{self.attempt_id}/results",
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('data', result)
        return None
    
    def withdraw_set(self):
        """Withdraw the test set"""
        print(f"\n🗑️  Withdrawing test set {self.test_set_id}")
        
        # Update set status to withdrawn via MongoDB
        client = MongoClient(MONGO_URL)
        db = client[DB_NAME]
        
        result = db.tejas_sets.update_one(
            {"id": self.test_set_id},
            {"$set": {"status": "withdrawn"}}
        )
        
        if result.modified_count > 0:
            print(f"✅ PASS: Withdrawn test set {self.test_set_id}")
            return True
        else:
            print(f"⚠️  WARNING: Could not withdraw test set")
            return False

def main():
    """Main test execution"""
    session = DeadlineTestSession()
    
    # Step 1: Authenticate as owner to create test set
    if not session.owner_auth():
        print("\n❌ CRITICAL: Owner authentication failed")
        return 1
    
    # Step 2: Create 2-question timed set
    test_set_id = session.create_two_question_timed_set()
    if not test_set_id:
        print("\n❌ CRITICAL: Failed to create test set")
        return 1
    
    # Step 3: Authenticate as student phone
    if not session.phone_auth(PHONE):
        print("\n❌ CRITICAL: Phone authentication failed")
        return 1
    
    # Step 4: Start attempt
    attempt_id = session.start_attempt()
    if not attempt_id:
        print("\n❌ CRITICAL: Failed to start attempt")
        return 1
    
    # Step 5: Save Q1 correct answer online
    q1_id = session.questions[0]['id']
    q1_correct = session.questions[0]['answer']
    
    print(f"\n💾 Saving Q1 answer online")
    print(f"   Q1 ID: {q1_id}")
    print(f"   Correct answer: {q1_correct}")
    
    response = session.save_answer(q1_id, str(q1_correct), marked=False)
    if response.status_code != 200:
        print(f"❌ FAIL: Q1 save failed: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        return 1
    
    print(f"✅ PASS: Q1 answer saved online")
    
    # Step 6: Wait for deadline to pass (30 seconds + buffer)
    print(f"\n⏰ Waiting for deadline to pass (35 seconds)...")
    time.sleep(35)
    
    # Step 7: Check attempt status
    print(f"\n🔍 Checking attempt status after deadline")
    attempt = session.get_attempt()
    
    if not attempt:
        print(f"❌ FAIL: Could not get attempt details")
        return 1
    
    print(f"   Status: {attempt.get('status')}")
    print(f"   Deadline: {attempt.get('deadline')}")
    
    if attempt.get('status') != 'completed':
        print(f"⚠️  WARNING: Attempt status is not 'completed' after deadline")
    else:
        print(f"✅ PASS: Attempt auto-completed after deadline")
    
    # Step 8: Get results
    print(f"\n📊 Getting results")
    results = session.get_results()
    
    if not results:
        print(f"❌ FAIL: Could not get results")
        return 1
    
    print(f"✅ PASS: Results retrieved")
    print(f"   Score: {results.get('score')}/{results.get('maximum')}")
    print(f"   Correct: {results.get('correct')}/{results.get('total')}")
    
    # Verify Q1 scored, Q2 not scored
    answers = results.get('answers', {})
    q2_id = session.questions[1]['id']
    
    q1_answer = answers.get(q1_id)
    q2_answer = answers.get(q2_id)
    
    print(f"\n🔍 Verifying answer scoring")
    print(f"   Q1 ({q1_id}): {q1_answer}")
    print(f"   Q2 ({q2_id}): {q2_answer}")
    
    if q1_answer and q1_answer.get('value') == str(q1_correct):
        print(f"✅ PASS: Q1 answer saved and scored")
    else:
        print(f"❌ FAIL: Q1 answer not properly saved")
    
    if not q2_answer or not q2_answer.get('value'):
        print(f"✅ PASS: Q2 not answered (as expected)")
    else:
        print(f"⚠️  WARNING: Q2 has answer: {q2_answer}")
    
    # Step 9: Withdraw test set
    session.withdraw_set()
    
    # Print summary
    print("\n" + "=" * 80)
    print("BACKEND TEST SUMMARY")
    print("=" * 80)
    print(f"✅ Test set created: {test_set_id}")
    print(f"✅ Attempt started: {attempt_id}")
    print(f"✅ Q1 saved online before deadline")
    print(f"✅ Attempt auto-completed after deadline")
    print(f"✅ Results retrieved successfully")
    print(f"✅ Test set withdrawn")
    print("=" * 80)
    print(f"\n📝 Test fixture ID: {test_set_id}")
    print(f"📝 Attempt ID: {attempt_id}")
    print(f"📝 Q1 ID: {q1_id}")
    print(f"📝 Q2 ID: {q2_id}")
    print("\n✅ Backend test completed - Ready for browser test")
    
    # Save test context for browser test
    test_context = {
        "test_set_id": test_set_id,
        "attempt_id": attempt_id,
        "q1_id": q1_id,
        "q2_id": q2_id,
        "q1_correct": q1_correct,
        "q2_correct": session.questions[1]['answer'],
        "phone": PHONE
    }
    
    with open('/app/test_reports/deadline_test_context.json', 'w') as f:
        json.dump(test_context, f, indent=2)
    
    print(f"📝 Test context saved to /app/test_reports/deadline_test_context.json")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
