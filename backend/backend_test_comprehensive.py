"""
Comprehensive Backend Testing - Full MVP Coverage
Tests ALL backend endpoints including practice, progress, and content management flows
This test covers endpoints NOT tested in iteration 7
"""
import os
import sys
import time
import json
import uuid
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

import requests

# Use HTTPS preview URL
BASE_URL = os.environ.get('FRONTEND_URL', 'https://campus-launch-2.preview.emergentagent.com')
OWNER_EMAIL = os.environ.get('ADMIN_EMAIL', 'owner@tejas-platform.com')
OWNER_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'L3eAGpSD0nQjrK80hMcIcZ1V')

class ComprehensiveBackendTester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.issues = []
        self.owner_session = requests.Session()
        self.student_session = requests.Session()
        self.reviewer_session = requests.Session()
        
        # Store IDs for cross-test usage
        self.owner_id = None
        self.student_id = None
        self.student_phone = None
        self.test_set_id = None
        self.test_attempt_id = None
        self.test_question_ids = []
        
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
    
    # ========== AUTHENTICATION TESTS ==========
    
    def test_owner_login(self):
        """Test owner login with password"""
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
    
    def test_phone_student_login(self):
        """Test phone-based student login"""
        print("\n🔍 Testing phone-based student login...")
        
        # Use a unique test phone number
        test_phone = f"9876543{str(int(time.time()))[-3:]}"
        self.student_phone = test_phone
        
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
                self.log_pass("Phone student login", f"Student ID: {self.student_id}, Phone: {test_phone}")
                return True
            else:
                self.log_fail("Phone student login", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("Phone student login", f"Status {response.status_code}: {response.text}")
            return False
    
    def test_get_current_user_owner(self):
        """Test GET /api/auth/me for owner"""
        print("\n🔍 Testing GET /api/auth/me (owner)...")
        
        response = self.make_request('GET', '/api/auth/me', session=self.owner_session)
        
        if not response:
            self.log_fail("GET /me (owner)", "No response")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'].get('role') == 'owner':
                self.log_pass("GET /me (owner)", f"Role: {data['data']['role']}")
                return True
            else:
                self.log_fail("GET /me (owner)", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("GET /me (owner)", f"Status {response.status_code}")
            return False
    
    def test_get_current_user_student(self):
        """Test GET /api/auth/me for student"""
        print("\n🔍 Testing GET /api/auth/me (student)...")
        
        response = self.make_request('GET', '/api/auth/me', session=self.student_session)
        
        if not response:
            self.log_fail("GET /me (student)", "No response")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'].get('role') == 'student':
                self.log_pass("GET /me (student)", f"Role: {data['data']['role']}")
                return True
            else:
                self.log_fail("GET /me (student)", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("GET /me (student)", f"Status {response.status_code}")
            return False
    
    # ========== CONTENT MANAGEMENT TESTS (OWNER) ==========
    
    def test_get_studio_sets(self):
        """Test GET /api/studio/sets (owner view)"""
        print("\n🔍 Testing GET /api/studio/sets...")
        
        response = self.make_request('GET', '/api/studio/sets', session=self.owner_session)
        
        if not response:
            self.log_fail("GET /studio/sets", "No response")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and isinstance(data['data'], list):
                count = len(data['data'])
                self.log_pass("GET /studio/sets", f"Found {count} sets")
                return True
            else:
                self.log_fail("GET /studio/sets", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("GET /studio/sets", f"Status {response.status_code}")
            return False
    
    def test_get_existing_set_detail(self):
        """Test GET /api/studio/sets/{id} for existing set"""
        print("\n🔍 Testing GET /api/studio/sets/{id} for existing set...")
        
        # First get the list of sets
        response = self.make_request('GET', '/api/studio/sets', session=self.owner_session)
        
        if not response or response.status_code != 200:
            self.log_fail("GET existing set detail", "Could not fetch sets list")
            return False
        
        data = response.json()
        if 'data' in data and len(data['data']) > 0:
            # Get the first set's ID
            set_id = data['data'][0]['id']
            
            # Now get the set detail
            response = self.make_request('GET', f'/api/studio/sets/{set_id}', session=self.owner_session)
            
            if not response:
                self.log_fail("GET existing set detail", "No response")
                return False
                
            if response.status_code == 200:
                detail = response.json()
                if 'data' in detail and detail['data'].get('id') == set_id:
                    title = detail['data'].get('title', 'Unknown')
                    question_count = len(detail['data'].get('questions', []))
                    self.log_pass("GET existing set detail", f"Set: {title}, Questions: {question_count}")
                    return True
                else:
                    self.log_fail("GET existing set detail", f"Invalid response: {detail}")
                    return False
            else:
                self.log_fail("GET existing set detail", f"Status {response.status_code}")
                return False
        else:
            self.log_fail("GET existing set detail", "No sets available")
            return False
    
    # ========== PUBLIC CATALOG TESTS ==========
    
    def test_get_public_sets(self):
        """Test GET /api/sets (public catalog)"""
        print("\n🔍 Testing GET /api/sets (public catalog)...")
        
        response = self.make_request('GET', '/api/sets', session=self.student_session)
        
        if not response:
            self.log_fail("GET /sets (public)", "No response")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'items' in data['data']:
                count = len(data['data']['items'])
                self.log_pass("GET /sets (public)", f"Found {count} published sets")
                return True
            else:
                self.log_fail("GET /sets (public)", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("GET /sets (public)", f"Status {response.status_code}")
            return False
    
    def test_get_my_sets_student(self):
        """Test GET /api/my/sets (student's available sets)"""
        print("\n🔍 Testing GET /api/my/sets (student)...")
        
        response = self.make_request('GET', '/api/my/sets', session=self.student_session)
        
        if not response:
            self.log_fail("GET /my/sets", "No response")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'items' in data['data']:
                count = len(data['data']['items'])
                self.log_pass("GET /my/sets", f"Student has access to {count} sets")
                return True
            else:
                self.log_fail("GET /my/sets", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("GET /my/sets", f"Status {response.status_code}")
            return False
    
    # ========== PRACTICE ATTEMPT FLOW TESTS ==========
    
    def test_get_published_set_for_practice(self):
        """Find a published set to use for practice testing"""
        print("\n🔍 Finding published set for practice testing...")
        
        response = self.make_request('GET', '/api/my/sets', session=self.student_session)
        
        if not response or response.status_code != 200:
            self.log_fail("Find published set", "Could not fetch sets")
            return False
        
        data = response.json()
        if 'data' in data and 'items' in data['data'] and len(data['data']['items']) > 0:
            # Find a set with questions
            for item in data['data']['items']:
                if item.get('count', 0) > 0:
                    self.test_set_id = item['id']
                    self.log_pass("Find published set", f"Set ID: {self.test_set_id}, Title: {item.get('title')}, Questions: {item.get('count')}")
                    return True
            
            self.log_fail("Find published set", "No sets with questions found")
            return False
        else:
            self.log_fail("Find published set", "No published sets available")
            return False
    
    def test_preflight_check(self):
        """Test POST /api/sets/{id}/preflight"""
        print("\n🔍 Testing POST /api/sets/{id}/preflight...")
        
        if not self.test_set_id:
            self.log_fail("Preflight check", "No test set ID available")
            return False
        
        response = self.make_request(
            'POST',
            f'/api/sets/{self.test_set_id}/preflight',
            session=self.student_session,
            json={'test_response': 'test123'}
        )
        
        if not response:
            self.log_fail("Preflight check", "No response")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'].get('ok'):
                self.log_pass("Preflight check", "Connection verified")
                return True
            else:
                self.log_fail("Preflight check", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("Preflight check", f"Status {response.status_code}: {response.text}")
            return False
    
    def test_start_practice_attempt(self):
        """Test POST /api/sets/{id}/start"""
        print("\n🔍 Testing POST /api/sets/{id}/start...")
        
        if not self.test_set_id:
            self.log_fail("Start practice attempt", "No test set ID available")
            return False
        
        start_key = str(uuid.uuid4())
        
        response = self.make_request(
            'POST',
            f'/api/sets/{self.test_set_id}/start',
            session=self.student_session,
            json={
                'start_key': start_key,
                'device_checked': True,
                'preview': False
            }
        )
        
        if not response:
            self.log_fail("Start practice attempt", "No response")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'].get('id'):
                self.test_attempt_id = data['data']['id']
                questions = data['data'].get('questions', [])
                self.test_question_ids = [q['id'] for q in questions]
                question_count = len(questions)
                self.log_pass("Start practice attempt", f"Attempt ID: {self.test_attempt_id}, Questions: {question_count}")
                return True
            else:
                self.log_fail("Start practice attempt", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("Start practice attempt", f"Status {response.status_code}: {response.text}")
            return False
    
    def test_get_attempt_detail(self):
        """Test GET /api/attempts/{id}"""
        print("\n🔍 Testing GET /api/attempts/{id}...")
        
        if not self.test_attempt_id:
            self.log_fail("GET attempt detail", "No test attempt ID available")
            return False
        
        response = self.make_request(
            'GET',
            f'/api/attempts/{self.test_attempt_id}',
            session=self.student_session
        )
        
        if not response:
            self.log_fail("GET attempt detail", "No response")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'].get('id') == self.test_attempt_id:
                status = data['data'].get('status')
                question_count = len(data['data'].get('questions', []))
                self.log_pass("GET attempt detail", f"Status: {status}, Questions: {question_count}")
                return True
            else:
                self.log_fail("GET attempt detail", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("GET attempt detail", f"Status {response.status_code}")
            return False
    
    def test_visit_question(self):
        """Test POST /api/attempts/{id}/visit"""
        print("\n🔍 Testing POST /api/attempts/{id}/visit...")
        
        if not self.test_attempt_id or not self.test_question_ids:
            self.log_fail("Visit question", "No test attempt or question IDs available")
            return False
        
        question_id = self.test_question_ids[0]
        
        response = self.make_request(
            'POST',
            f'/api/attempts/{self.test_attempt_id}/visit',
            session=self.student_session,
            json={'question_id': question_id}
        )
        
        if not response:
            self.log_fail("Visit question", "No response")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'visited' in data['data']:
                visited_count = len(data['data']['visited'])
                self.log_pass("Visit question", f"Visited questions: {visited_count}")
                return True
            else:
                self.log_fail("Visit question", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("Visit question", f"Status {response.status_code}")
            return False
    
    def test_save_answer(self):
        """Test PUT /api/attempts/{id}/answers/{qid}"""
        print("\n🔍 Testing PUT /api/attempts/{id}/answers/{qid}...")
        
        if not self.test_attempt_id or not self.test_question_ids:
            self.log_fail("Save answer", "No test attempt or question IDs available")
            return False
        
        question_id = self.test_question_ids[0]
        
        response = self.make_request(
            'PUT',
            f'/api/attempts/{self.test_attempt_id}/answers/{question_id}',
            session=self.student_session,
            json={
                'value': '1',
                'marked': False,
                'revision': 1,
                'request_id': str(uuid.uuid4())
            }
        )
        
        if not response:
            self.log_fail("Save answer", "No response")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'accepted' in data['data']:
                accepted_value = data['data']['accepted'].get('value')
                self.log_pass("Save answer", f"Answer saved: {accepted_value}")
                return True
            else:
                self.log_fail("Save answer", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("Save answer", f"Status {response.status_code}: {response.text}")
            return False
    
    def test_submit_attempt(self):
        """Test POST /api/attempts/{id}/submit"""
        print("\n🔍 Testing POST /api/attempts/{id}/submit...")
        
        if not self.test_attempt_id:
            self.log_fail("Submit attempt", "No test attempt ID available")
            return False
        
        response = self.make_request(
            'POST',
            f'/api/attempts/{self.test_attempt_id}/submit',
            session=self.student_session
        )
        
        if not response:
            self.log_fail("Submit attempt", "No response")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'].get('status') == 'completed':
                receipt = data['data'].get('receipt')
                self.log_pass("Submit attempt", f"Receipt: {receipt}")
                return True
            else:
                self.log_fail("Submit attempt", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("Submit attempt", f"Status {response.status_code}")
            return False
    
    def test_get_results(self):
        """Test GET /api/attempts/{id}/results"""
        print("\n🔍 Testing GET /api/attempts/{id}/results...")
        
        if not self.test_attempt_id:
            self.log_fail("GET results", "No test attempt ID available")
            return False
        
        response = self.make_request(
            'GET',
            f'/api/attempts/{self.test_attempt_id}/results',
            session=self.student_session
        )
        
        if not response:
            self.log_fail("GET results", "No response")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'summary' in data['data']:
                summary = data['data']['summary']
                score = summary.get('score', 0)
                maximum = summary.get('maximum', 0)
                correct = summary.get('correct', 0)
                incorrect = summary.get('incorrect', 0)
                skipped = summary.get('skipped', 0)
                self.log_pass("GET results", f"Score: {score}/{maximum}, Correct: {correct}, Incorrect: {incorrect}, Skipped: {skipped}")
                return True
            else:
                self.log_fail("GET results", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("GET results", f"Status {response.status_code}")
            return False
    
    def test_get_attempt_history(self):
        """Test GET /api/attempts (history)"""
        print("\n🔍 Testing GET /api/attempts (history)...")
        
        response = self.make_request('GET', '/api/attempts', session=self.student_session)
        
        if not response:
            self.log_fail("GET attempt history", "No response")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'items' in data['data']:
                count = len(data['data']['items'])
                self.log_pass("GET attempt history", f"Found {count} attempts")
                return True
            else:
                self.log_fail("GET attempt history", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("GET attempt history", f"Status {response.status_code}")
            return False
    
    # ========== HEALTH CHECK ==========
    
    def test_health_endpoint(self):
        """Test GET /api/health"""
        print("\n🔍 Testing GET /api/health...")
        
        response = self.make_request('GET', '/api/health', session=None)
        
        if not response:
            self.log_fail("Health check", "No response")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'].get('status') == 'ok':
                service = data['data'].get('service', 'Unknown')
                version = data['data'].get('version', 'Unknown')
                self.log_pass("Health check", f"Service: {service}, Version: {version}")
                return True
            else:
                self.log_fail("Health check", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("Health check", f"Status {response.status_code}")
            return False
    
    # ========== PREFERENCES TEST ==========
    
    def test_update_preferences(self):
        """Test PATCH /api/auth/preferences"""
        print("\n🔍 Testing PATCH /api/auth/preferences...")
        
        response = self.make_request(
            'PATCH',
            '/api/auth/preferences',
            session=self.student_session,
            json={'exam': 'BITSAT'}
        )
        
        if not response:
            self.log_fail("Update preferences", "No response")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'].get('exam') == 'BITSAT':
                self.log_pass("Update preferences", "Exam preference updated to BITSAT")
                return True
            else:
                self.log_fail("Update preferences", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("Update preferences", f"Status {response.status_code}")
            return False
    
    # ========== PROFILES TEST ==========
    
    def test_get_profiles(self):
        """Test GET /api/studio/profiles"""
        print("\n🔍 Testing GET /api/studio/profiles...")
        
        response = self.make_request('GET', '/api/studio/profiles', session=self.owner_session)
        
        if not response:
            self.log_fail("GET profiles", "No response")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and isinstance(data['data'], list):
                count = len(data['data'])
                self.log_pass("GET profiles", f"Found {count} exam profiles")
                return True
            else:
                self.log_fail("GET profiles", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("GET profiles", f"Status {response.status_code}")
            return False
    
    # ========== RUN ALL TESTS ==========
    
    def run_all_tests(self):
        """Run all comprehensive backend tests"""
        print("=" * 80)
        print("COMPREHENSIVE BACKEND TESTING - FULL MVP COVERAGE")
        print("=" * 80)
        print(f"Base URL: {BASE_URL}")
        print(f"Owner Email: {OWNER_EMAIL}")
        print("=" * 80)
        
        # Phase 1: Authentication
        print("\n" + "=" * 80)
        print("PHASE 1: AUTHENTICATION TESTS")
        print("=" * 80)
        
        if not self.test_owner_login():
            print("\n⚠️  Owner login failed - some tests will be skipped")
        
        if not self.test_phone_student_login():
            print("\n⚠️  Student login failed - some tests will be skipped")
        
        if self.owner_id:
            self.test_get_current_user_owner()
        
        if self.student_id:
            self.test_get_current_user_student()
        
        # Phase 2: Content Management (Owner)
        print("\n" + "=" * 80)
        print("PHASE 2: CONTENT MANAGEMENT TESTS (OWNER)")
        print("=" * 80)
        
        if self.owner_id:
            self.test_get_studio_sets()
            self.test_get_existing_set_detail()
            self.test_get_profiles()
        else:
            print("⚠️  Skipping content management tests - owner not logged in")
        
        # Phase 3: Public Catalog
        print("\n" + "=" * 80)
        print("PHASE 3: PUBLIC CATALOG TESTS")
        print("=" * 80)
        
        self.test_get_public_sets()
        
        if self.student_id:
            self.test_get_my_sets_student()
        
        # Phase 4: Practice Attempt Flow
        print("\n" + "=" * 80)
        print("PHASE 4: PRACTICE ATTEMPT FLOW TESTS")
        print("=" * 80)
        
        if self.student_id:
            if self.test_get_published_set_for_practice():
                self.test_preflight_check()
                if self.test_start_practice_attempt():
                    self.test_get_attempt_detail()
                    self.test_visit_question()
                    self.test_save_answer()
                    self.test_submit_attempt()
                    self.test_get_results()
                    self.test_get_attempt_history()
            else:
                print("⚠️  No published sets available - skipping practice flow tests")
        else:
            print("⚠️  Skipping practice flow tests - student not logged in")
        
        # Phase 5: Preferences
        print("\n" + "=" * 80)
        print("PHASE 5: PREFERENCES TESTS")
        print("=" * 80)
        
        if self.student_id:
            self.test_update_preferences()
        
        # Phase 6: Health Check
        print("\n" + "=" * 80)
        print("PHASE 6: SYSTEM HEALTH")
        print("=" * 80)
        
        self.test_health_endpoint()
        
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
    tester = ComprehensiveBackendTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
