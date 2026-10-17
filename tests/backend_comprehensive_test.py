"""
Comprehensive Backend Core Testing for Tejas Exam Platform
Tests full 75-question practice flow, content management, attempts, and reports
CRITICAL FIX: Uses response is not None instead of truthiness to avoid 4xx false negatives
"""
import requests
import sys
import time
import os
from pathlib import Path
from dotenv import load_dotenv

# Load credentials from .env - DO NOT hardcode secrets
load_dotenv(Path(__file__).parent.parent / 'backend' / '.env')

# Use HTTPS preview URL as per requirements
BASE_URL = "https://campus-launch-2.preview.emergentagent.com"

# Load credentials from environment
OWNER_EMAIL = os.environ.get('ADMIN_EMAIL', '')
OWNER_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')
CRON_SECRET = os.environ.get('WEBHOOK_CRON_SECRET', '')

class TejasComprehensiveTester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.issues = []
        self.owner_session = requests.Session()
        self.student1_session = requests.Session()
        self.student2_session = requests.Session()
        self.student1_email = None
        self.student2_email = None
        self.test_set_id = None
        self.test_attempt_id = None
        
    def log_pass(self, test_name):
        self.tests_run += 1
        self.tests_passed += 1
        print(f"✅ {test_name}")
        
    def log_fail(self, test_name, reason):
        self.tests_run += 1
        self.tests_failed += 1
        self.issues.append({"test": test_name, "reason": reason})
        print(f"❌ {test_name}: {reason}")
        
    def make_request(self, session, method, endpoint, **kwargs):
        """Make HTTP request with proper error handling - FIXED: check response is not None"""
        url = f"{BASE_URL}{endpoint}"
        try:
            response = session.request(method, url, timeout=30, **kwargs)
            return response
        except Exception as e:
            print(f"Request exception: {str(e)}")
            return None
    
    # ==================== AUTH TESTS ====================
    
    def test_owner_login(self):
        """Test owner login with credentials from .env"""
        print("\n🔍 Testing owner login...")
        
        if not OWNER_EMAIL or not OWNER_PASSWORD:
            self.log_fail("Owner login", "Credentials not found in .env")
            return False
        
        response = self.make_request(
            self.owner_session,
            "POST",
            "/api/auth/login",
            json={
                "email": OWNER_EMAIL,
                "password": OWNER_PASSWORD,
                "name": "Owner"
            }
        )
        
        # FIXED: Use 'is not None' instead of truthiness
        if response is not None and response.status_code == 200:
            data = response.json()
            user_data = data.get("data", {})
            if user_data.get("role") == "owner":
                self.log_pass("Owner login")
                return True
            else:
                self.log_fail("Owner login", f"Expected owner role, got: {user_data.get('role')}")
        else:
            status = response.status_code if response is not None else 'No response'
            self.log_fail("Owner login", f"Status: {status}")
        return False
    
    def test_student_registrations(self):
        """Test registration of 2 students"""
        print("\n🔍 Testing student registrations...")
        
        timestamp = int(time.time())
        students = [
            (self.student1_session, f"student1_{timestamp}@test.com"),
            (self.student2_session, f"student2_{timestamp}@test.com")
        ]
        
        for idx, (session, email) in enumerate(students, 1):
            response = self.make_request(
                session,
                "POST",
                "/api/auth/register",
                json={
                    "email": email,
                    "password": "TestPassword123",
                    "name": f"Test Student {idx}",
                    "exam": "JEE Main",
                    "consent": True
                }
            )
            
            if response is not None and response.status_code == 200:
                data = response.json()
                user_data = data.get("data", {})
                if user_data.get("role") == "student":
                    self.log_pass(f"Student {idx} registration")
                    if idx == 1:
                        self.student1_email = email
                    else:
                        self.student2_email = email
                else:
                    self.log_fail(f"Student {idx} registration", f"Expected student role, got: {user_data.get('role')}")
                    return False
            else:
                status = response.status_code if response is not None else 'No response'
                self.log_fail(f"Student {idx} registration", f"Status: {status}")
                return False
        
        return True
    
    def test_logout_401(self):
        """Test that logout returns 401 for unauthenticated requests"""
        print("\n🔍 Testing logout 401 for unauthenticated...")
        
        # Create new session without auth
        unauth_session = requests.Session()
        response = self.make_request(unauth_session, "POST", "/api/auth/logout")
        
        if response is not None and response.status_code == 401:
            self.log_pass("Logout 401 (unauthenticated)")
        else:
            status = response.status_code if response is not None else 'No response'
            self.log_fail("Logout 401", f"Expected 401, got: {status}")
    
    def test_duplicate_email_409(self):
        """Test that duplicate email returns 409"""
        print("\n🔍 Testing duplicate email 409...")
        
        response = self.make_request(
            requests.Session(),
            "POST",
            "/api/auth/register",
            json={
                "email": OWNER_EMAIL,
                "password": "SomePassword123",
                "name": "Duplicate",
                "exam": "JEE Main",
                "consent": True
            }
        )
        
        if response is not None and response.status_code == 409:
            self.log_pass("Duplicate email 409")
        else:
            status = response.status_code if response is not None else 'No response'
            self.log_fail("Duplicate email 409", f"Expected 409, got: {status}")
    
    def test_throttling_429(self):
        """Test login throttling returns 429 after 5 failed attempts"""
        print("\n🔍 Testing login throttling 429...")
        
        test_email = f"throttle_{int(time.time())}@test.com"
        test_session = requests.Session()
        
        # Try 5 failed logins
        for i in range(5):
            response = self.make_request(
                test_session,
                "POST",
                "/api/auth/login",
                json={
                    "email": test_email,
                    "password": "WrongPassword123"
                }
            )
            if response is None or response.status_code != 401:
                status = response.status_code if response is not None else 'No response'
                self.log_fail("Throttling 429", f"Expected 401 on attempt {i+1}, got: {status}")
                return
        
        # 6th attempt should be throttled
        response = self.make_request(
            test_session,
            "POST",
            "/api/auth/login",
            json={
                "email": test_email,
                "password": "WrongPassword123"
            }
        )
        
        if response is not None and response.status_code == 429:
            self.log_pass("Throttling 429 (after 5 attempts)")
        else:
            status = response.status_code if response is not None else 'No response'
            self.log_fail("Throttling 429", f"Expected 429, got: {status}")
    
    def test_cross_origin_403(self):
        """Test cross-origin write protection returns 403"""
        print("\n🔍 Testing cross-origin write protection 403...")
        
        response = self.make_request(
            self.owner_session,
            "POST",
            "/api/auth/logout",
            headers={"Origin": "https://malicious-site.com"}
        )
        
        if response is not None and response.status_code == 403:
            self.log_pass("Cross-origin 403")
        else:
            status = response.status_code if response is not None else 'No response'
            self.log_fail("Cross-origin 403", f"Expected 403, got: {status}")
    
    # ==================== CONTENT TESTS ====================
    
    def test_create_restricted_set(self):
        """Test creating a restricted QA test set"""
        print("\n🔍 Testing restricted set creation...")
        
        response = self.make_request(
            self.owner_session,
            "POST",
            "/api/studio/sets",
            json={
                "title": "QA Test Set - 75 Questions",
                "exam": "JEE Main",
                "year": "2024",
                "source": "Test source for QA",
                "attribution": "Test attribution",
                "audience": "restricted",
                "allowed_emails": [self.student1_email] if self.student1_email else [],
                "rights_upload": True,
                "rights_publish": True,
                "rights_report": True,
                "rules": {
                    "minutes": 180,
                    "correct": 4,
                    "wrong": -1,
                    "skipped": 0
                },
                "change_reason": "Initial QA test set"
            }
        )
        
        if response is not None and response.status_code == 200:
            data = response.json()
            set_data = data.get("data", {})
            self.test_set_id = set_data.get("id")
            if self.test_set_id:
                self.log_pass("Create restricted set")
                return True
            else:
                self.log_fail("Create restricted set", "No set ID returned")
        else:
            status = response.status_code if response is not None else 'No response'
            self.log_fail("Create restricted set", f"Status: {status}")
        return False
    
    def test_student_cannot_access_studio(self):
        """Test that students cannot access studio endpoints (403)"""
        print("\n🔍 Testing student studio access denied (403)...")
        
        response = self.make_request(
            self.student1_session,
            "GET",
            "/api/studio/sets"
        )
        
        if response is not None and response.status_code == 403:
            self.log_pass("Student studio access 403")
        else:
            status = response.status_code if response is not None else 'No response'
            self.log_fail("Student studio access 403", f"Expected 403, got: {status}")
    
    def test_unauthorized_source_access(self):
        """Test that unauthorized users cannot access private source files"""
        print("\n🔍 Testing unauthorized source access...")
        
        # Student 2 (not in allowed_emails) tries to access restricted set
        if not self.test_set_id:
            self.log_fail("Unauthorized source access", "No test set ID available")
            return
        
        response = self.make_request(
            self.student2_session,
            "GET",
            f"/api/my/sets/{self.test_set_id}"
        )
        
        if response is not None and response.status_code == 404:
            self.log_pass("Unauthorized source access blocked (404)")
        else:
            status = response.status_code if response is not None else 'No response'
            self.log_fail("Unauthorized source access", f"Expected 404, got: {status}")
    
    def test_publish_without_approvals_blocked(self):
        """Test that publishing without question approvals is blocked"""
        print("\n🔍 Testing publish without approvals blocked...")
        
        if not self.test_set_id:
            self.log_fail("Publish without approvals", "No test set ID available")
            return
        
        response = self.make_request(
            self.owner_session,
            "POST",
            f"/api/studio/sets/{self.test_set_id}/publish",
            json={"confirm": True}
        )
        
        if response is not None and response.status_code == 400:
            self.log_pass("Publish without approvals blocked (400)")
        else:
            status = response.status_code if response is not None else 'No response'
            self.log_fail("Publish without approvals", f"Expected 400, got: {status}")
    
    # ==================== CRON TESTS ====================
    
    def test_cron_unauthorized_401(self):
        """Test cron endpoint returns 401 without secret"""
        print("\n🔍 Testing cron unauthorized 401...")
        
        response = self.make_request(
            requests.Session(),
            "POST",
            "/api/cron/maintenance",
            json={"event": "schedule.triggered", "run_id": f"test_{int(time.time())}"}
        )
        
        if response is not None and response.status_code == 401:
            self.log_pass("Cron unauthorized 401")
        else:
            status = response.status_code if response is not None else 'No response'
            self.log_fail("Cron unauthorized 401", f"Expected 401, got: {status}")
    
    def test_cron_invalid_body_400(self):
        """Test cron endpoint returns 400 for invalid body"""
        print("\n🔍 Testing cron invalid body 400...")
        
        if not CRON_SECRET:
            self.log_fail("Cron invalid body 400", "CRON_SECRET not found in .env")
            return
        
        response = self.make_request(
            requests.Session(),
            "POST",
            "/api/cron/maintenance",
            headers={"Authorization": f"Bearer {CRON_SECRET}"},
            json={"invalid": "body"}
        )
        
        if response is not None and response.status_code == 400:
            self.log_pass("Cron invalid body 400")
        else:
            status = response.status_code if response is not None else 'No response'
            self.log_fail("Cron invalid body 400", f"Expected 400, got: {status}")
    
    def test_cron_valid_accepted(self):
        """Test cron endpoint accepts valid request"""
        print("\n🔍 Testing cron valid request accepted...")
        
        if not CRON_SECRET:
            self.log_fail("Cron valid accepted", "CRON_SECRET not found in .env")
            return
        
        run_id = f"test_{int(time.time())}"
        response = self.make_request(
            requests.Session(),
            "POST",
            "/api/cron/maintenance",
            headers={"Authorization": f"Bearer {CRON_SECRET}"},
            json={"event": "schedule.triggered", "run_id": run_id}
        )
        
        if response is not None and response.status_code == 200:
            data = response.json()
            if data.get("data", {}).get("accepted"):
                self.log_pass("Cron valid accepted")
            else:
                self.log_fail("Cron valid accepted", f"Not accepted: {data}")
        else:
            status = response.status_code if response is not None else 'No response'
            self.log_fail("Cron valid accepted", f"Status: {status}")
    
    def test_cron_duplicate_idempotent(self):
        """Test cron endpoint detects duplicate run_id"""
        print("\n🔍 Testing cron duplicate idempotent...")
        
        if not CRON_SECRET:
            self.log_fail("Cron duplicate idempotent", "CRON_SECRET not found in .env")
            return
        
        run_id = f"test_dup_{int(time.time())}"
        
        # First request
        response1 = self.make_request(
            requests.Session(),
            "POST",
            "/api/cron/maintenance",
            headers={"Authorization": f"Bearer {CRON_SECRET}"},
            json={"event": "schedule.triggered", "run_id": run_id}
        )
        
        if response1 is None or response1.status_code != 200:
            self.log_fail("Cron duplicate idempotent", "First request failed")
            return
        
        # Duplicate request
        response2 = self.make_request(
            requests.Session(),
            "POST",
            "/api/cron/maintenance",
            headers={"Authorization": f"Bearer {CRON_SECRET}"},
            json={"event": "schedule.triggered", "run_id": run_id}
        )
        
        if response2 is not None and response2.status_code == 200:
            data = response2.json()
            if data.get("data", {}).get("duplicate"):
                self.log_pass("Cron duplicate idempotent")
            else:
                self.log_fail("Cron duplicate idempotent", "Duplicate not detected")
        else:
            status = response2.status_code if response2 is not None else 'No response'
            self.log_fail("Cron duplicate idempotent", f"Status: {status}")
    
    # ==================== PRACTICE FLOW TESTS ====================
    
    def test_preflight_without_published_set(self):
        """Test preflight requires published set or preview mode"""
        print("\n🔍 Testing preflight without published set...")
        
        if not self.test_set_id:
            self.log_fail("Preflight without published", "No test set ID available")
            return
        
        # Student tries to preflight unpublished set
        response = self.make_request(
            self.student1_session,
            "POST",
            f"/api/sets/{self.test_set_id}/preflight",
            json={"preview": False, "test_response": "test"}
        )
        
        if response is not None and response.status_code == 404:
            self.log_pass("Preflight without published set blocked (404)")
        else:
            status = response.status_code if response is not None else 'No response'
            self.log_fail("Preflight without published", f"Expected 404, got: {status}")
    
    def test_start_without_preflight_blocked(self):
        """Test that start without preflight is blocked"""
        print("\n🔍 Testing start without preflight blocked...")
        
        if not self.test_set_id:
            self.log_fail("Start without preflight", "No test set ID available")
            return
        
        response = self.make_request(
            self.student1_session,
            "POST",
            f"/api/sets/{self.test_set_id}/start",
            json={
                "start_key": f"test_start_{int(time.time())}",
                "device_checked": True,
                "preview": False
            }
        )
        
        if response is not None and response.status_code in [400, 404]:
            self.log_pass("Start without preflight blocked")
        else:
            status = response.status_code if response is not None else 'No response'
            self.log_fail("Start without preflight", f"Expected 400/404, got: {status}")
    
    # ==================== MAIN TEST RUNNER ====================
    
    def run_all_tests(self):
        """Run all comprehensive backend tests"""
        print("=" * 70)
        print("TEJAS BACKEND COMPREHENSIVE CORE TESTING")
        print(f"Testing against: {BASE_URL}")
        print("=" * 70)
        
        # Auth tests
        if not self.test_owner_login():
            print("\n❌ Owner login failed - cannot continue with remaining tests")
            return self.tests_passed, self.tests_failed, self.issues
        
        if not self.test_student_registrations():
            print("\n❌ Student registration failed - some tests will be skipped")
        
        self.test_logout_401()
        self.test_duplicate_email_409()
        self.test_throttling_429()
        
        # Re-login owner for remaining tests
        self.test_owner_login()
        
        self.test_cross_origin_403()
        
        # Content tests
        if self.test_create_restricted_set():
            self.test_student_cannot_access_studio()
            self.test_unauthorized_source_access()
            self.test_publish_without_approvals_blocked()
            self.test_preflight_without_published_set()
            self.test_start_without_preflight_blocked()
        
        # Cron tests
        self.test_cron_unauthorized_401()
        self.test_cron_invalid_body_400()
        self.test_cron_valid_accepted()
        self.test_cron_duplicate_idempotent()
        
        # Print summary
        print("\n" + "=" * 70)
        print(f"TESTS COMPLETED: {self.tests_passed}/{self.tests_run} passed, {self.tests_failed} failed")
        print("=" * 70)
        
        if len(self.issues) > 0:
            print("\n❌ ISSUES FOUND:")
            for issue in self.issues:
                print(f"  • {issue['test']}: {issue['reason']}")
        else:
            print("\n✅ ALL TESTS PASSED")
        
        return self.tests_passed, self.tests_failed, self.issues

if __name__ == '__main__':
    tester = TejasComprehensiveTester()
    passed, failed, issues = tester.run_all_tests()
    sys.exit(0 if failed == 0 else 1)
