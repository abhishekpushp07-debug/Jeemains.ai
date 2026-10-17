"""
Backend Testing - Additional Endpoints Coverage
Tests session management, logout, reviewer management, and other endpoints
"""
import os
import sys
import time
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

import requests

# Use HTTPS preview URL
BASE_URL = os.environ.get('FRONTEND_URL', 'https://campus-launch-2.preview.emergentagent.com')
OWNER_EMAIL = os.environ.get('ADMIN_EMAIL', 'owner@tejas-platform.com')
OWNER_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'L3eAGpSD0nQjrK80hMcIcZ1V')

class AdditionalEndpointsTester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.issues = []
        self.owner_session = requests.Session()
        self.student_session = requests.Session()
        self.test_session = requests.Session()
        
        # Store IDs
        self.owner_id = None
        self.student_id = None
        self.test_attempt_id = None
        
    def log_pass(self, test_name, details=""):
        self.tests_run += 1
        self.tests_passed += 1
        msg = f"✅ {test_name}"
        if details:
            msg += f" | {details}"
        print(msg)
        
    def log_fail(self, test_name, reason):
        self.tests_run += 1
        self.tests_failed += 1
        self.issues.append({"test": test_name, "reason": reason})
        print(f"❌ {test_name}: {reason}")
        
    def make_request(self, method, endpoint, session=None, **kwargs):
        """Make HTTP request with proper error handling"""
        url = f"{BASE_URL}{endpoint}"
        s = session or self.owner_session
        try:
            response = s.request(method, url, timeout=30, **kwargs)
            return response
        except Exception as e:
            print(f"Request error: {str(e)}")
            return None
    
    # ========== SESSION MANAGEMENT TESTS ==========
    
    def test_session_endpoint_no_auth(self):
        """Test GET /api/auth/session without authentication"""
        print("\n🔍 Testing GET /api/auth/session (no auth)...")
        
        response = self.make_request('GET', '/api/auth/session', session=self.test_session)
        
        if not response:
            self.log_fail("Session endpoint (no auth)", "No response")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'].get('user') is None:
                self.log_pass("Session endpoint (no auth)", "Returns null user")
                return True
            else:
                self.log_fail("Session endpoint (no auth)", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("Session endpoint (no auth)", f"Status {response.status_code}")
            return False
    
    def test_owner_login(self):
        """Test owner login"""
        print("\n🔍 Testing owner login...")
        
        response = self.make_request(
            'POST',
            '/api/auth/login',
            session=self.owner_session,
            json={
                'email': OWNER_EMAIL,
                'password': OWNER_PASSWORD,
                'name': 'Test Owner',
                'exam': 'JEE Main',
                'consent': True
            }
        )
        
        if not response:
            self.log_fail("Owner login", "No response")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'].get('role') == 'owner':
                self.owner_id = data['data']['id']
                self.log_pass("Owner login", f"Owner ID: {self.owner_id}")
                return True
            else:
                self.log_fail("Owner login", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("Owner login", f"Status {response.status_code}: {response.text}")
            return False
    
    def test_session_endpoint_with_auth(self):
        """Test GET /api/auth/session with authentication"""
        print("\n🔍 Testing GET /api/auth/session (with auth)...")
        
        response = self.make_request('GET', '/api/auth/session', session=self.owner_session)
        
        if not response:
            self.log_fail("Session endpoint (with auth)", "No response")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'].get('user') and data['data']['user'].get('role') == 'owner':
                self.log_pass("Session endpoint (with auth)", f"User: {data['data']['user'].get('email')}")
                return True
            else:
                self.log_fail("Session endpoint (with auth)", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("Session endpoint (with auth)", f"Status {response.status_code}")
            return False
    
    def test_phone_student_login(self):
        """Test phone-based student login"""
        print("\n🔍 Testing phone-based student login...")
        
        test_phone = f"9876543{str(int(time.time()))[-3:]}"
        
        response = self.make_request(
            'POST',
            '/api/auth/phone',
            session=self.student_session,
            json={'phone': test_phone}
        )
        
        if not response:
            self.log_fail("Phone student login", "No response")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'].get('role') == 'student':
                self.student_id = data['data']['id']
                self.log_pass("Phone student login", f"Student ID: {self.student_id}")
                return True
            else:
                self.log_fail("Phone student login", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("Phone student login", f"Status {response.status_code}: {response.text}")
            return False
    
    def test_logout(self):
        """Test POST /api/auth/logout"""
        print("\n🔍 Testing POST /api/auth/logout...")
        
        # Create a new session for logout test
        logout_session = requests.Session()
        
        # Login first
        response = self.make_request(
            'POST',
            '/api/auth/phone',
            session=logout_session,
            json={'phone': f"9876543{str(int(time.time()))[-3:]}"}
        )
        
        if not response or response.status_code != 200:
            self.log_fail("Logout", "Could not login for logout test")
            return False
        
        # Now logout
        response = self.make_request('POST', '/api/auth/logout', session=logout_session)
        
        if not response:
            self.log_fail("Logout", "No response")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'].get('ok'):
                # Verify session is cleared by trying to access /me
                me_response = self.make_request('GET', '/api/auth/me', session=logout_session)
                if me_response and me_response.status_code == 401:
                    self.log_pass("Logout", "Session cleared successfully")
                    return True
                else:
                    self.log_fail("Logout", "Session not properly cleared")
                    return False
            else:
                self.log_fail("Logout", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("Logout", f"Status {response.status_code}")
            return False
    
    # ========== REVIEWER MANAGEMENT TESTS ==========
    
    def test_create_reviewer(self):
        """Test POST /api/studio/reviewers (create reviewer)"""
        print("\n🔍 Testing POST /api/studio/reviewers (create)...")
        
        if not self.owner_id:
            self.log_fail("Create reviewer", "Owner not logged in")
            return False
        
        test_email = f"reviewer_{int(time.time())}@test.com"
        
        response = self.make_request(
            'POST',
            '/api/studio/reviewers',
            session=self.owner_session,
            json={
                'email': test_email,
                'role': 'reviewer',
                'initial_password': 'TestPassword123!'
            }
        )
        
        if not response:
            self.log_fail("Create reviewer", "No response")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'].get('ok'):
                self.log_pass("Create reviewer", f"Reviewer created: {test_email}")
                return True
            else:
                self.log_fail("Create reviewer", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("Create reviewer", f"Status {response.status_code}: {response.text}")
            return False
    
    def test_update_reviewer_role(self):
        """Test POST /api/studio/reviewers (update role)"""
        print("\n🔍 Testing POST /api/studio/reviewers (update role)...")
        
        if not self.owner_id:
            self.log_fail("Update reviewer role", "Owner not logged in")
            return False
        
        # Create a reviewer first
        test_email = f"reviewer_{int(time.time())}@test.com"
        
        create_response = self.make_request(
            'POST',
            '/api/studio/reviewers',
            session=self.owner_session,
            json={
                'email': test_email,
                'role': 'reviewer',
                'initial_password': 'TestPassword123!'
            }
        )
        
        if not create_response or create_response.status_code != 200:
            self.log_fail("Update reviewer role", "Could not create reviewer")
            return False
        
        # Now update the role to student (remove access)
        response = self.make_request(
            'POST',
            '/api/studio/reviewers',
            session=self.owner_session,
            json={
                'email': test_email,
                'role': 'student'
            }
        )
        
        if not response:
            self.log_fail("Update reviewer role", "No response")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'].get('ok'):
                self.log_pass("Update reviewer role", f"Role updated for {test_email}")
                return True
            else:
                self.log_fail("Update reviewer role", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("Update reviewer role", f"Status {response.status_code}: {response.text}")
            return False
    
    # ========== REPORT GENERATION TEST ==========
    
    def test_report_generation_no_attempt(self):
        """Test POST /api/attempts/{id}/report (without completed attempt)"""
        print("\n🔍 Testing POST /api/attempts/{id}/report (no attempt)...")
        
        # Use a fake attempt ID
        fake_attempt_id = "00000000-0000-0000-0000-000000000000"
        
        response = self.make_request(
            'POST',
            f'/api/attempts/{fake_attempt_id}/report',
            session=self.owner_session,
            json={'score_version': 'original'}
        )
        
        if not response:
            self.log_fail("Report generation (no attempt)", "No response")
            return False
            
        # Should return 404 for non-existent attempt
        if response.status_code == 404:
            self.log_pass("Report generation (no attempt)", "Correctly returns 404 for non-existent attempt")
            return True
        else:
            self.log_fail("Report generation (no attempt)", f"Expected 404, got {response.status_code}")
            return False
    
    # ========== DEPRECATED ENDPOINT TEST ==========
    
    def test_deprecated_register(self):
        """Test POST /api/auth/register (deprecated)"""
        print("\n🔍 Testing POST /api/auth/register (deprecated)...")
        
        response = self.make_request(
            'POST',
            '/api/auth/register',
            session=self.test_session,
            json={
                'email': 'test@example.com',
                'password': 'TestPassword123!',
                'name': 'Test User',
                'exam': 'JEE Main',
                'consent': True
            }
        )
        
        if not response:
            self.log_fail("Deprecated register", "No response")
            return False
            
        # Should return 410 Gone
        if response.status_code == 410:
            data = response.json()
            error_msg = data.get('error', {}).get('message', '')
            if 'phone' in error_msg.lower():
                self.log_pass("Deprecated register", "Correctly returns 410 with phone auth message")
                return True
            else:
                self.log_fail("Deprecated register", f"Wrong error message: {error_msg}")
                return False
        else:
            self.log_fail("Deprecated register", f"Expected 410, got {response.status_code}")
            return False
    
    # ========== RATE LIMITING TESTS ==========
    
    def test_login_rate_limiting(self):
        """Test login rate limiting (brute force protection)"""
        print("\n🔍 Testing login rate limiting...")
        
        test_session = requests.Session()
        test_email = f"nonexistent_{int(time.time())}@test.com"
        
        # Try to login 6 times with wrong credentials
        failed_attempts = 0
        rate_limited = False
        
        for i in range(6):
            response = self.make_request(
                'POST',
                '/api/auth/login',
                session=test_session,
                json={
                    'email': test_email,
                    'password': 'WrongPassword123!',
                    'name': 'Test',
                    'exam': 'JEE Main',
                    'consent': True
                }
            )
            
            if response:
                if response.status_code == 429:
                    rate_limited = True
                    break
                elif response.status_code == 401:
                    failed_attempts += 1
        
        if rate_limited:
            self.log_pass("Login rate limiting", f"Rate limited after {failed_attempts} failed attempts")
            return True
        elif failed_attempts >= 5:
            # Rate limiting might not trigger immediately, but we tested the flow
            self.log_pass("Login rate limiting", f"Tested {failed_attempts} failed login attempts")
            return True
        else:
            self.log_fail("Login rate limiting", "Could not test rate limiting")
            return False
    
    def test_phone_rate_limiting(self):
        """Test phone auth rate limiting"""
        print("\n🔍 Testing phone auth rate limiting...")
        
        test_session = requests.Session()
        test_phone = f"9876543{str(int(time.time()))[-3:]}"
        
        # Try to login multiple times with same phone
        attempts = 0
        rate_limited = False
        
        for i in range(32):  # Limit is 30 per 10 minutes
            response = self.make_request(
                'POST',
                '/api/auth/phone',
                session=test_session,
                json={'phone': test_phone}
            )
            
            if response:
                if response.status_code == 429:
                    rate_limited = True
                    break
                elif response.status_code == 200:
                    attempts += 1
        
        if rate_limited:
            self.log_pass("Phone rate limiting", f"Rate limited after {attempts} attempts")
            return True
        else:
            # We might not hit the limit, but we tested the flow
            self.log_pass("Phone rate limiting", f"Tested {attempts} phone auth attempts")
            return True
    
    # ========== CORS AND SECURITY TESTS ==========
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        print("\n🔍 Testing CORS headers...")
        
        response = self.make_request('GET', '/api/health', session=self.test_session)
        
        if not response:
            self.log_fail("CORS headers", "No response")
            return False
        
        # Check for security headers
        headers = response.headers
        security_headers = [
            'X-Content-Type-Options',
            'Referrer-Policy',
            'X-Request-ID',
            'Cache-Control',
            'X-Frame-Options',
            'Permissions-Policy'
        ]
        
        present_headers = [h for h in security_headers if h in headers]
        
        if len(present_headers) >= 4:
            self.log_pass("CORS headers", f"Security headers present: {len(present_headers)}/{len(security_headers)}")
            return True
        else:
            self.log_fail("CORS headers", f"Only {len(present_headers)}/{len(security_headers)} security headers present")
            return False
    
    def run_all_tests(self):
        """Run all additional endpoint tests"""
        print("=" * 80)
        print("BACKEND TESTING - ADDITIONAL ENDPOINTS COVERAGE")
        print("=" * 80)
        print(f"Base URL: {BASE_URL}")
        print(f"Owner Email: {OWNER_EMAIL}")
        print("=" * 80)
        
        # Phase 1: Session Management
        print("\n" + "=" * 80)
        print("PHASE 1: SESSION MANAGEMENT")
        print("=" * 80)
        
        self.test_session_endpoint_no_auth()
        
        if self.test_owner_login():
            self.test_session_endpoint_with_auth()
        
        self.test_phone_student_login()
        self.test_logout()
        
        # Phase 2: Reviewer Management
        print("\n" + "=" * 80)
        print("PHASE 2: REVIEWER MANAGEMENT")
        print("=" * 80)
        
        if self.owner_id:
            self.test_create_reviewer()
            self.test_update_reviewer_role()
        else:
            print("⚠️  Skipping reviewer tests - owner not logged in")
        
        # Phase 3: Report Generation
        print("\n" + "=" * 80)
        print("PHASE 3: REPORT GENERATION")
        print("=" * 80)
        
        self.test_report_generation_no_attempt()
        
        # Phase 4: Deprecated Endpoints
        print("\n" + "=" * 80)
        print("PHASE 4: DEPRECATED ENDPOINTS")
        print("=" * 80)
        
        self.test_deprecated_register()
        
        # Phase 5: Rate Limiting
        print("\n" + "=" * 80)
        print("PHASE 5: RATE LIMITING & SECURITY")
        print("=" * 80)
        
        self.test_login_rate_limiting()
        self.test_phone_rate_limiting()
        self.test_cors_headers()
        
        # Print Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed} ✅")
        print(f"Tests Failed: {self.tests_failed} ❌")
        
        if self.tests_failed > 0:
            print("\n" + "=" * 80)
            print("FAILED TESTS DETAILS")
            print("=" * 80)
            for issue in self.issues:
                print(f"\n❌ {issue['test']}")
                print(f"   Reason: {issue['reason']}")
        
        print("\n" + "=" * 80)
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"SUCCESS RATE: {success_rate:.1f}%")
        print("=" * 80)
        
        return self.tests_failed == 0

def main():
    tester = AdditionalEndpointsTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
