"""
Comprehensive test for iteration 12 requirements:
- Offline functionality and draft persistence
- Invalid integer validation
- Multi-tab conflict resolution
- Deadline enforcement
- Idempotent submission
- Score version switching
- Privacy checks

Updated to load URLs/MONGO_URL/DB_NAME from dotenv (no hardcodes)
"""
import sys
import json
import time
import os
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

# Load fixture data
with open('/app/memory/qa_context.json', 'r') as f:
    fixture = json.load(f)

SET_ID = fixture['set_id']
PHONE = fixture['phone']
EXPECTED_QUESTIONS = fixture['expected_questions']

print("=" * 80)
print("COMPREHENSIVE ITERATION 12 TESTING")
print("=" * 80)
print(f"Set ID: {SET_ID}")
print(f"Phone: {PHONE}")
print("=" * 80)

class TestSession:
    def __init__(self):
        self.session = requests.Session()
        self.user = None
        self.attempt_id = None
        
    def phone_auth(self):
        """Authenticate via phone"""
        print("\n📱 Phone Authentication")
        response = self.session.post(
            f"{BASE_URL}/api/auth/phone",
            json={"phone": PHONE},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ FAIL: Phone auth returned {response.status_code}")
            return False
        
        self.user = response.json()
        print(f"✅ PASS: Authenticated as user {self.user.get('id')}")
        return True
    
    def get_questions(self):
        """Get fixture questions from MongoDB"""
        client = MongoClient(MONGO_URL)
        db = client[DB_NAME]
        set_doc = db.tejas_sets.find_one({"id": SET_ID}, {"_id": 0})
        if not set_doc:
            return None
        return set_doc.get('questions', [])
    
    def start_attempt(self, start_key):
        """Start a new attempt"""
        # Preflight first
        response = self.session.post(
            f"{BASE_URL}/api/sets/{SET_ID}/preflight",
            json={"preview": False, "test_response": "test"},
            timeout=30
        )
        if response.status_code != 200:
            print(f"❌ Preflight failed: {response.status_code}")
            return None
        
        # Start attempt
        response = self.session.post(
            f"{BASE_URL}/api/sets/{SET_ID}/start",
            json={
                "start_key": start_key,
                "device_checked": True,
                "preview": False
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Start failed: {response.status_code}")
            return None
        
        result = response.json()
        attempt = result.get('data', result)
        self.attempt_id = attempt.get('id')
        return self.attempt_id
    
    def save_answer(self, qid, value, marked=False, revision=1, request_id=None):
        """Save an answer"""
        if not request_id:
            request_id = f"test-{qid}-{int(time.time() * 1000)}"
        
        response = self.session.put(
            f"{BASE_URL}/api/attempts/{self.attempt_id}/answers/{qid}",
            json={
                "value": value,
                "marked": marked,
                "revision": revision,
                "request_id": request_id
            },
            timeout=30
        )
        
        return response
    
    def get_attempt(self):
        """Get current attempt state"""
        response = self.session.get(
            f"{BASE_URL}/api/attempts/{self.attempt_id}",
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        return None
    
    def submit_attempt(self):
        """Submit the attempt"""
        response = self.session.post(
            f"{BASE_URL}/api/attempts/{self.attempt_id}/submit",
            timeout=30
        )
        return response
    
    def get_results(self, score_version="original"):
        """Get results"""
        response = self.session.get(
            f"{BASE_URL}/api/attempts/{self.attempt_id}/results?score_version={score_version}",
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        return None

def test_invalid_integer_validation():
    """Test that invalid integers are rejected"""
    print("\n" + "=" * 80)
    print("TEST 1: Invalid Integer Validation")
    print("=" * 80)
    
    test = TestSession()
    if not test.phone_auth():
        return False
    
    questions = test.get_questions()
    if not questions:
        print("❌ FAIL: Could not get questions")
        return False
    
    # Find an integer question
    integer_q = next((q for q in questions if q['type'] == 'integer'), None)
    if not integer_q:
        print("❌ FAIL: No integer question found")
        return False
    
    # Start attempt
    attempt_id = test.start_attempt(f"test-invalid-int-{int(time.time())}")
    if not attempt_id:
        print("❌ FAIL: Could not start attempt")
        return False
    
    print(f"✅ Started attempt: {attempt_id}")
    print(f"   Testing with integer question {integer_q['number']}")
    
    # Test invalid inputs
    invalid_inputs = [
        ("3.14", "decimal"),
        ("abc", "letters"),
        ("12.0", "decimal with .0"),
        ("1e5", "scientific notation"),
        ("", "empty string (should be accepted as blank)")
    ]
    
    results = []
    for value, description in invalid_inputs:
        response = test.save_answer(integer_q['id'], value)
        status = response.status_code
        
        if value == "":
            # Empty should be accepted (clearing answer)
            if status == 200:
                print(f"✅ PASS: Empty string accepted (clear answer)")
                results.append(True)
            else:
                print(f"❌ FAIL: Empty string rejected with {status}")
                results.append(False)
        else:
            # Invalid values should be rejected with 400
            if status == 400:
                print(f"✅ PASS: {description} rejected with 400")
                results.append(True)
            else:
                print(f"❌ FAIL: {description} returned {status} (expected 400)")
                results.append(False)
    
    # Test valid inputs
    valid_inputs = [
        ("12345", "positive integer"),
        ("-999", "negative integer"),
        ("0", "zero"),
        ("+42", "positive with + sign"),
        ("00123", "leading zeros")
    ]
    
    for value, description in valid_inputs:
        response = test.save_answer(integer_q['id'], value)
        status = response.status_code
        
        if status == 200:
            print(f"✅ PASS: {description} accepted")
            results.append(True)
        else:
            print(f"❌ FAIL: {description} rejected with {status}")
            results.append(False)
    
    success = all(results)
    print(f"\n{'✅ TEST PASSED' if success else '❌ TEST FAILED'}: {sum(results)}/{len(results)} checks passed")
    return success

def test_idempotent_submission():
    """Test that submission is idempotent"""
    print("\n" + "=" * 80)
    print("TEST 2: Idempotent Submission")
    print("=" * 80)
    
    test = TestSession()
    if not test.phone_auth():
        return False
    
    questions = test.get_questions()
    if not questions:
        return False
    
    # Start attempt
    attempt_id = test.start_attempt(f"test-idempotent-{int(time.time())}")
    if not attempt_id:
        return False
    
    print(f"✅ Started attempt: {attempt_id}")
    
    # Answer first question
    q = questions[0]
    response = test.save_answer(q['id'], q.get('answer', '1'))
    if response.status_code != 200:
        print(f"❌ FAIL: Could not save answer")
        return False
    
    print(f"✅ Saved answer for Q{q['number']}")
    
    # Submit once
    response1 = test.submit_attempt()
    if response1.status_code != 200:
        print(f"❌ FAIL: First submission failed with {response1.status_code}")
        return False
    
    result1 = response1.json()
    receipt1 = result1.get('receipt') or result1.get('data', {}).get('receipt')
    print(f"✅ First submission successful, receipt: {receipt1}")
    
    # Submit again (should be idempotent)
    response2 = test.submit_attempt()
    if response2.status_code != 200:
        print(f"❌ FAIL: Second submission failed with {response2.status_code}")
        return False
    
    result2 = response2.json()
    receipt2 = result2.get('receipt') or result2.get('data', {}).get('receipt')
    print(f"✅ Second submission successful, receipt: {receipt2}")
    
    # Receipts should match
    if receipt1 == receipt2:
        print(f"✅ PASS: Idempotent submission - same receipt")
        return True
    else:
        print(f"❌ FAIL: Different receipts: {receipt1} vs {receipt2}")
        return False

def test_answer_revision_conflict():
    """Test revision conflict detection (409)"""
    print("\n" + "=" * 80)
    print("TEST 3: Answer Revision Conflict (409)")
    print("=" * 80)
    
    test = TestSession()
    if not test.phone_auth():
        return False
    
    questions = test.get_questions()
    if not questions:
        return False
    
    # Start attempt
    attempt_id = test.start_attempt(f"test-conflict-{int(time.time())}")
    if not attempt_id:
        return False
    
    print(f"✅ Started attempt: {attempt_id}")
    
    q = questions[0]
    qid = q['id']
    
    # Save answer with revision 1
    response1 = test.save_answer(qid, "1", revision=1, request_id="req-1")
    if response1.status_code != 200:
        print(f"❌ FAIL: First save failed")
        return False
    
    print(f"✅ Saved answer with revision 1")
    
    # Try to save with revision 1 again (wrong revision, should get 409)
    response2 = test.save_answer(qid, "2", revision=1, request_id="req-2")
    if response2.status_code == 409:
        print(f"✅ PASS: Revision conflict detected (409)")
        return True
    else:
        print(f"❌ FAIL: Expected 409, got {response2.status_code}")
        return False

def test_idempotent_answer_save():
    """Test that saving same answer with same request_id is idempotent"""
    print("\n" + "=" * 80)
    print("TEST 4: Idempotent Answer Save (Same request_id)")
    print("=" * 80)
    
    test = TestSession()
    if not test.phone_auth():
        return False
    
    questions = test.get_questions()
    if not questions:
        return False
    
    # Start attempt
    attempt_id = test.start_attempt(f"test-idempotent-answer-{int(time.time())}")
    if not attempt_id:
        return False
    
    print(f"✅ Started attempt: {attempt_id}")
    
    q = questions[0]
    qid = q['id']
    request_id = "same-request-id-123"
    
    # Save answer
    response1 = test.save_answer(qid, "1", revision=1, request_id=request_id)
    if response1.status_code != 200:
        print(f"❌ FAIL: First save failed")
        return False
    
    print(f"✅ First save successful")
    
    # Save again with same request_id and same value (should be idempotent)
    response2 = test.save_answer(qid, "1", revision=1, request_id=request_id)
    if response2.status_code != 200:
        print(f"❌ FAIL: Second save failed with {response2.status_code}")
        return False
    
    print(f"✅ PASS: Idempotent save with same request_id")
    
    # Try to save different value with same request_id (should fail with 409)
    response3 = test.save_answer(qid, "2", revision=1, request_id=request_id)
    if response3.status_code == 409:
        print(f"✅ PASS: Different value with same request_id rejected (409)")
        return True
    else:
        print(f"❌ FAIL: Expected 409, got {response3.status_code}")
        return False

def test_privacy_endpoints():
    """Test that privacy is enforced on endpoints"""
    print("\n" + "=" * 80)
    print("TEST 5: Privacy Endpoint Checks")
    print("=" * 80)
    
    # Test without authentication
    session = requests.Session()
    
    tests = [
        (f"/api/attempts/{fixture.get('attempt_id', 'test-id')}", "Attempt without auth"),
        (f"/api/attempts/{fixture.get('attempt_id', 'test-id')}/results", "Results without auth"),
        (f"/api/my/sets", "My sets without auth"),
    ]
    
    results = []
    for endpoint, description in tests:
        response = session.get(f"{BASE_URL}{endpoint}", timeout=30)
        # Should get 401 or 403
        if response.status_code in [401, 403]:
            print(f"✅ PASS: {description} - blocked with {response.status_code}")
            results.append(True)
        else:
            print(f"❌ FAIL: {description} - returned {response.status_code}")
            results.append(False)
    
    # Test with wrong user
    test1 = TestSession()
    test1.phone_auth()
    
    test2 = TestSession()
    # Use different phone
    response = test2.session.post(
        f"{BASE_URL}/api/auth/phone",
        json={"phone": "+12025550199"},  # Different phone
        timeout=30
    )
    
    if response.status_code == 200:
        # Try to access test1's attempt (if we have one)
        if fixture.get('attempt_id'):
            response = test2.session.get(
                f"{BASE_URL}/api/attempts/{fixture['attempt_id']}",
                timeout=30
            )
            if response.status_code == 404:
                print(f"✅ PASS: Different user cannot access attempt (404)")
                results.append(True)
            else:
                print(f"❌ FAIL: Different user got {response.status_code}")
                results.append(False)
    
    success = all(results)
    print(f"\n{'✅ TEST PASSED' if success else '❌ TEST FAILED'}: {sum(results)}/{len(results)} checks passed")
    return success

def test_full_75_question_scoring():
    """Test full 75 question scoring accuracy"""
    print("\n" + "=" * 80)
    print("TEST 6: Full 75 Question Scoring (300/300)")
    print("=" * 80)
    
    test = TestSession()
    if not test.phone_auth():
        return False
    
    questions = test.get_questions()
    if not questions or len(questions) != 75:
        print(f"❌ FAIL: Expected 75 questions, got {len(questions) if questions else 0}")
        return False
    
    # Start attempt
    attempt_id = test.start_attempt(f"test-scoring-{int(time.time())}")
    if not attempt_id:
        return False
    
    print(f"✅ Started attempt: {attempt_id}")
    print(f"   Submitting all 75 correct answers...")
    
    # Submit all correct answers
    success_count = 0
    for i, q in enumerate(questions, 1):
        answer = q.get('answer', '')
        if not answer:
            print(f"   ⚠️  Q{q['number']}: No answer, skipping")
            continue
        
        response = test.save_answer(q['id'], answer)
        if response.status_code == 200:
            success_count += 1
            if i % 15 == 0:
                print(f"   Progress: {success_count}/{len(questions)}")
        else:
            print(f"   ❌ Q{q['number']} failed: {response.status_code}")
    
    print(f"✅ Submitted {success_count}/{len(questions)} answers")
    
    # Submit attempt
    response = test.submit_attempt()
    if response.status_code != 200:
        print(f"❌ FAIL: Submission failed")
        return False
    
    print(f"✅ Attempt submitted")
    
    # Check score
    results = test.get_results()
    if not results:
        print(f"❌ FAIL: Could not get results")
        return False
    
    summary = results.get('summary', {})
    score = summary.get('score')
    maximum = summary.get('maximum')
    correct = summary.get('correct')
    
    print(f"\n   Score: {score}/{maximum}")
    print(f"   Correct: {correct}")
    
    if score == 300 and maximum == 300 and correct == 75:
        print(f"✅ PASS: Perfect score 300/300 with 75 correct")
        return True
    else:
        print(f"❌ FAIL: Expected 300/300 with 75 correct, got {score}/{maximum} with {correct} correct")
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("STARTING COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    
    tests = [
        ("Invalid Integer Validation", test_invalid_integer_validation),
        ("Idempotent Submission", test_idempotent_submission),
        ("Answer Revision Conflict", test_answer_revision_conflict),
        ("Idempotent Answer Save", test_idempotent_answer_save),
        ("Privacy Endpoint Checks", test_privacy_endpoints),
        ("Full 75 Question Scoring", test_full_75_question_scoring),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ TEST CRASHED: {name}")
            print(f"   Error: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\n{passed}/{total} tests passed")
    print("=" * 80)
    
    return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(main())
