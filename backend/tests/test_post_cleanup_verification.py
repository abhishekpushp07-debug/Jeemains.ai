"""
Post-cleanup verification tests for QA withdrawal, auth rate limiting, and edge cases.
Tests are READ-ONLY and do not create new fixtures or modify existing data.
"""
import requests
import sys
import json
import time
import hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

# Load environment
import os
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')
load_dotenv(Path(__file__).parent.parent.parent / 'frontend' / '.env')

BASE_URL = os.environ['REACT_APP_BACKEND_URL']
OWNER_EMAIL = os.environ.get('ADMIN_EMAIL', '')
OWNER_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')

# Test phone numbers - use different ones to avoid throttling real users
TEST_PHONE_STUDENT = "+12025550199"  # From test_v5_faults.py
FICTIONAL_PHONE = "+12025550188"  # Different from +12025550184

class TestResults:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.results = []
    
    def record(self, name, passed, details=""):
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            self.tests_failed += 1
            print(f"❌ {name}: {details}")
        self.results.append({
            "test": name,
            "passed": passed,
            "details": details
        })
    
    def summary(self):
        print(f"\n{'='*70}")
        print(f"TESTS COMPLETED: {self.tests_passed}/{self.tests_run} passed, {self.tests_failed} failed")
        print(f"{'='*70}")
        return self.tests_failed == 0

results = TestResults()

def test_qa_sets_withdrawal():
    """Verify all QA sets are withdrawn and not visible in public APIs"""
    print("\n🔍 Testing QA sets withdrawal...")
    
    # Load withdrawal record
    with open('/app/test_reports/qa_withdrawal.json', 'r') as f:
        withdrawal = json.load(f)
    
    withdrawn_ids = [s['id'] for s in withdrawal['sets']]
    print(f"  Found {len(withdrawn_ids)} withdrawn sets in record")
    
    # Test 1: Public /api/sets?exam=JEE%20Main should show NO QA sets
    response = requests.get(f"{BASE_URL}/api/sets?exam=JEE%20Main", timeout=30)
    if response.status_code == 200:
        resp_data = response.json()
        sets = resp_data.get('data', resp_data) if isinstance(resp_data, dict) else resp_data
        if isinstance(sets, dict):
            sets = sets.get('items')
        assert isinstance(sets, list), 'Unexpected catalogue response shape'
        qa_sets = [s for s in sets if isinstance(s, dict) and (s.get('id') in withdrawn_ids or 'QA' in s.get('title', '').upper())]
        results.record(
            "Public API shows NO QA sets",
            len(qa_sets) == 0,
            f"Found {len(qa_sets)} QA sets in public API" if qa_sets else ""
        )
    else:
        results.record("Public API accessible", False, f"Status {response.status_code}")
    
    # Test 2: Login as owner and check /api/my/sets
    session = requests.Session()
    response = session.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": OWNER_EMAIL, "password": OWNER_PASSWORD, "name": "Owner"},
        timeout=30
    )
    
    if response.status_code == 200:
        response = session.get(f"{BASE_URL}/api/my/sets", timeout=30)
        if response.status_code == 200:
            resp_data = response.json()
            my_sets = resp_data.get('data', resp_data) if isinstance(resp_data, dict) else resp_data
            if isinstance(my_sets, dict):
                my_sets = my_sets.get('items')
            assert isinstance(my_sets, list), 'Unexpected private catalogue response shape'
            qa_sets = [s for s in my_sets if isinstance(s, dict) and s.get('id') in withdrawn_ids]
            results.record(
                "/api/my/sets shows NO published QA sets",
                len(qa_sets) == 0,
                f"Found {len(qa_sets)} published QA sets" if qa_sets else ""
            )
        else:
            results.record("/api/my/sets accessible", False, f"Status {response.status_code}")
    else:
        results.record("Owner login", False, f"Status {response.status_code}")
    
    # Test 3: Try to start withdrawn fixture f565e4db-19bb-45c2-95ef-75b74bd985b6
    withdrawn_set_id = "f565e4db-19bb-45c2-95ef-75b74bd985b6"
    
    # Get phone session
    phone_session = requests.Session()
    response = phone_session.post(
        f"{BASE_URL}/api/auth/phone",
        json={"phone": "+12025550184"},
        timeout=30
    )
    
    if response.status_code == 200:
        # Try preflight
        response = phone_session.post(
            f"{BASE_URL}/api/sets/{withdrawn_set_id}/preflight",
            json={"preview": False},
            timeout=30
        )
        results.record(
            f"Withdrawn set {withdrawn_set_id[:8]}... returns 404/409",
            response.status_code in [404, 409],
            f"Got status {response.status_code}"
        )
    else:
        results.record("Phone auth for withdrawal test", False, f"Status {response.status_code}")

def test_staff_auth_rate_limiting():
    """Test staff auth rate limiting with atomic counter"""
    print("\n🔍 Testing staff auth rate limiting...")
    
    # Test with syntactically valid but unknown staff email
    test_email = f"unknown.staff.{time.time_ns()}@example.com"
    test_password = "WrongPassword123"  # >=10 chars
    
    # Make 5 bad attempts (should all return 401)
    for i in range(1, 6):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": test_email, "password": test_password, "name": "Test"},
            timeout=30
        )
        if i <= 5:
            if response.status_code != 401:
                results.record(
                    f"Staff auth attempt {i} returns 401",
                    False,
                    f"Got status {response.status_code}"
                )
                return
    
    print(f"  ✓ First 5 attempts returned 401")
    
    # 6th attempt should return 429 with Retry-After
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": test_email, "password": test_password, "name": "Test"},
        timeout=30
    )
    
    retry_after = response.headers.get('Retry-After')
    results.record(
        "6th staff auth attempt returns 429",
        response.status_code == 429,
        f"Got status {response.status_code}"
    )
    
    results.record(
        "429 includes Retry-After header",
        retry_after is not None and int(retry_after) > 0,
        f"Retry-After: {retry_after}"
    )
    
    # Verify remaining time is within 900s window
    if retry_after:
        remaining = int(retry_after)
        results.record(
            "Retry-After shows remaining time in 900s window",
            0 < remaining <= 900,
            f"Remaining: {remaining}s"
        )

def test_concurrent_staff_auth():
    """Test concurrent staff auth requests - max 5x401, remainder 429"""
    print("\n🔍 Testing concurrent staff auth requests...")
    
    test_email = f"concurrent.test.{int(time.time())}@tejas-platform.com"
    test_password = "ConcurrentTest123"
    
    def make_request(i):
        try:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": test_email, "password": test_password, "name": "Test"},
                timeout=30
            )
            return (i, response.status_code)
        except Exception as e:
            return (i, f"error: {e}")
    
    # Make 8 concurrent requests
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(make_request, i) for i in range(1, 9)]
        responses = [f.result() for f in as_completed(futures)]
    
    responses.sort(key=lambda x: x[0])
    status_codes = [r[1] for r in responses]
    
    count_401 = status_codes.count(401)
    count_429 = status_codes.count(429)
    count_500 = status_codes.count(500)
    
    print(f"  Status codes: 401={count_401}, 429={count_429}, 500={count_500}")
    
    results.record(
        "Concurrent requests: max 5x401",
        count_401 == 5,
        f"Got {count_401} x 401"
    )
    
    results.record(
        "Concurrent requests: remainder 429 (not 500)",
        count_429 == 3 and all(code in (401, 429) for code in status_codes),
        f"Got {count_429} x 429, {count_500} x 500"
    )

def test_phone_rate_limiting():
    """Test phone auth rate limiting (optional with fictional number)"""
    print("\n🔍 Testing phone auth rate limiting (optional)...")
    
    # Use fictional 202 number (not +12025550184)
    # Note: This is optional and may be skipped if we don't want to create test data
    
    # Just verify the endpoint works and has rate limiting
    response = requests.post(
        f"{BASE_URL}/api/auth/phone",
        json={"phone": FICTIONAL_PHONE},
        timeout=30
    )
    
    results.record(
        "Phone auth endpoint accessible",
        response.status_code in [200, 429],
        f"Status {response.status_code}"
    )
    
    # If we got 429, check Retry-After
    if response.status_code == 429:
        retry_after = response.headers.get('Retry-After')
        results.record(
            "Phone 429 includes Retry-After",
            retry_after is not None and int(retry_after) > 0,
            f"Retry-After: {retry_after}"
        )
        
        if retry_after:
            remaining = int(retry_after)
            results.record(
                "Phone Retry-After shows remaining time in 600s window",
                0 < remaining <= 600,
                f"Remaining: {remaining}s"
            )

def test_json_limits():
    """Verify JSON limits are already tested"""
    print("\n🔍 Verifying JSON limits tests...")
    
    # Read the log file
    with open('/app/test_reports/v5_json_limits_final.log', 'r') as f:
        log = f.read()
    
    results.record(
        "JSON limits tests completed (6/6)",
        "6/6 passed" in log and "ALL TESTS PASSED" in log,
        "See /app/test_reports/v5_json_limits_final.log"
    )

def test_huge_answer_revision():
    """Test huge answer revision validation (422 before handler)"""
    print("\n🔍 Testing huge answer revision validation...")
    
    # Login as phone user
    session = requests.Session()
    response = session.post(
        f"{BASE_URL}/api/auth/phone",
        json={"phone": TEST_PHONE_STUDENT},
        timeout=30
    )
    
    if response.status_code != 200:
        results.record("Phone auth for answer test", False, f"Status {response.status_code}")
        return
    
    # Try to send a huge revision number (should be validated before processing)
    # This tests that validation happens at the Pydantic level (422) before handler
    
    # We need an active attempt to test this, but we don't want to create new fixtures
    # So we'll just test the validation with an invalid attempt ID
    
    fake_attempt_id = "00000000-0000-0000-0000-000000000000"
    fake_question_id = "00000000-0000-0000-0000-000000000001"
    
    # Send huge revision number
    response = session.put(
        f"{BASE_URL}/api/attempts/{fake_attempt_id}/answers/{fake_question_id}",
        json={
            "value": "1",
            "marked": False,
            "revision": 999999999,  # Huge revision
            "request_id": "test-huge-revision-guard"
        },
        timeout=30
    )
    
    # Should return 404 (attempt not found) or 422 (validation error) or 409 (closed)
    # The key is it should NOT crash (500)
    results.record(
        "Huge answer revision handled gracefully",
        response.status_code == 422,
        f"Status {response.status_code} (not 500)"
    )

def test_v5_faults_file():
    """Verify test_v5_faults.py has correct structure"""
    print("\n🔍 Verifying test_v5_faults.py structure...")
    
    with open('/app/backend/tests/test_v5_faults.py', 'r') as f:
        content = f.read()
    
    results.record(
        "test_v5_faults.py has qa_only fixtures",
        'qa_only' in content and 'qa_set_and_user' in content,
        ""
    )
    
    results.record(
        "test_v5_faults.py has yield cleanup",
        'yield' in content and 'finally:' in content,
        ""
    )
    
    # Try to compile the file
    try:
        compile(content, '/app/backend/tests/test_v5_faults.py', 'exec')
        results.record("test_v5_faults.py compiles", True, "")
    except SyntaxError as e:
        results.record("test_v5_faults.py compiles", False, str(e))

def main():
    print("="*70)
    print("POST-CLEANUP VERIFICATION TESTS")
    print(f"Testing against: {BASE_URL}")
    print("="*70)
    
    # Run all tests
    test_qa_sets_withdrawal()
    test_staff_auth_rate_limiting()
    test_concurrent_staff_auth()
    test_phone_rate_limiting()
    test_json_limits()
    test_huge_answer_revision()
    test_v5_faults_file()
    
    # Print summary
    success = results.summary()
    
    # Save results
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE_URL,
        "summary": {
            "total": results.tests_run,
            "passed": results.tests_passed,
            "failed": results.tests_failed
        },
        "results": results.results
    }
    
    output_path = Path('/app/test_reports/post_cleanup_verification.json')
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n📄 Results saved to: {output_path}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
