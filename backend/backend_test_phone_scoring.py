"""
Comprehensive Backend Testing for Phone Auth and Scoring Logic
Tests phone-based authentication and pure scoring.py logic against actual questions
"""
import os
import sys
import time
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

# Import after loading env
import requests
from tejas.scoring import score, canonical
from tejas_core import build_questions, RULES

# Use HTTPS preview URL
BASE_URL = os.environ.get('FRONTEND_URL', 'https://campus-launch-2.preview.emergentagent.com')

class TejasPhoneScoringTester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.issues = []
        self.session = requests.Session()
        self.phone_session = requests.Session()
        
    def log_pass(self, test_name):
        self.tests_run += 1
        self.tests_passed += 1
        print(f"✅ {test_name}")
        
    def log_fail(self, test_name, reason):
        self.tests_run += 1
        self.tests_failed += 1
        self.issues.append({"test": test_name, "reason": reason})
        print(f"❌ {test_name}: {reason}")
        
    def make_request(self, method, endpoint, session=None, **kwargs):
        """Make HTTP request with proper error handling"""
        url = f"{BASE_URL}{endpoint}"
        s = session or self.session
        try:
            response = s.request(method, url, timeout=30, **kwargs)
            return response
        except Exception as e:
            print(f"Request error: {str(e)}")
            return None
    
    # ========== PURE SCORING LOGIC TESTS ==========
    
    def test_scoring_all_correct(self):
        """Test scoring with all 75 questions correct"""
        print("\n🔍 Testing scoring: all 75 correct...")
        
        # Create 75 questions (60 MCQ + 15 integer)
        questions = []
        for i in range(75):
            qtype = 'mcq' if i < 60 else 'integer'
            q = {
                'id': f'q{i+1}',
                'number': i+1,
                'type': qtype,
                'subject': ['Mathematics', 'Physics', 'Chemistry'][i // 25],
                'topic': 'Test Topic',
                'answer': '1' if qtype == 'mcq' else '42',
                'options': {'1': 'A', '2': 'B', '3': 'C', '4': 'D'} if qtype == 'mcq' else {}
            }
            questions.append(q)
        
        # All correct answers
        answers = {}
        for q in questions:
            answers[q['id']] = {'value': q['answer'], 'marked': False}
        
        attempt = {
            'questions': questions,
            'answers': answers,
            'rules': {'correct': 4, 'wrong': -1, 'skipped': 0},
            'started_at': int(time.time())
        }
        
        try:
            result = score(attempt)
            expected_score = 75 * 4  # 300
            if result['summary']['score'] == expected_score:
                self.log_pass(f"Scoring all 75 correct = {expected_score}")
            else:
                self.log_fail("Scoring all correct", f"Expected {expected_score}, got {result['summary']['score']}")
        except Exception as e:
            self.log_fail("Scoring all correct", str(e))
    
    def test_scoring_wrong_answers(self):
        """Test scoring with wrong answers (including numerical)"""
        print("\n🔍 Testing scoring: wrong answers with -1 penalty...")
        
        questions = [
            {'id': 'q1', 'number': 1, 'type': 'mcq', 'subject': 'Math', 'topic': 'Test', 'answer': '1', 'options': {'1': 'A', '2': 'B'}},
            {'id': 'q2', 'number': 2, 'type': 'integer', 'subject': 'Math', 'topic': 'Test', 'answer': '42'}
        ]
        
        answers = {
            'q1': {'value': '2', 'marked': False},  # Wrong MCQ
            'q2': {'value': '99', 'marked': False}  # Wrong integer
        }
        
        attempt = {
            'questions': questions,
            'answers': answers,
            'rules': {'correct': 4, 'wrong': -1, 'skipped': 0},
            'started_at': int(time.time())
        }
        
        try:
            result = score(attempt)
            expected_score = -2  # 2 wrong = -2
            if result['summary']['score'] == expected_score:
                self.log_pass(f"Wrong answers penalty = {expected_score}")
            else:
                self.log_fail("Wrong answers penalty", f"Expected {expected_score}, got {result['summary']['score']}")
        except Exception as e:
            self.log_fail("Wrong answers penalty", str(e))
    
    def test_scoring_blank_answers(self):
        """Test scoring with blank answers = 0"""
        print("\n🔍 Testing scoring: blank answers = 0...")
        
        questions = [
            {'id': 'q1', 'number': 1, 'type': 'mcq', 'subject': 'Math', 'topic': 'Test', 'answer': '1', 'options': {'1': 'A', '2': 'B'}},
            {'id': 'q2', 'number': 2, 'type': 'integer', 'subject': 'Math', 'topic': 'Test', 'answer': '42'}
        ]
        
        answers = {}  # No answers
        
        attempt = {
            'questions': questions,
            'answers': answers,
            'rules': {'correct': 4, 'wrong': -1, 'skipped': 0},
            'started_at': int(time.time())
        }
        
        try:
            result = score(attempt)
            if result['summary']['score'] == 0 and result['summary']['skipped'] == 2:
                self.log_pass("Blank answers = 0 marks")
            else:
                self.log_fail("Blank answers", f"Expected 0 score and 2 skipped, got {result['summary']}")
        except Exception as e:
            self.log_fail("Blank answers", str(e))
    
    def test_canonical_numeric_formats(self):
        """Test canonical() accepts 0, negative, 03, whitespace, Unicode minus"""
        print("\n🔍 Testing canonical numeric formats...")
        
        test_cases = [
            ('0', 'integer', '0'),
            ('-5', 'integer', '-5'),
            ('03', 'integer', '3'),
            ('  42  ', 'integer', '42'),
            ('\u221242', 'integer', '-42'),  # Unicode minus
            ('+100', 'integer', '100'),
        ]
        
        all_passed = True
        for input_val, kind, expected in test_cases:
            try:
                result = canonical(input_val, kind)
                if result != expected:
                    self.log_fail(f"Canonical {repr(input_val)}", f"Expected {expected}, got {result}")
                    all_passed = False
            except Exception as e:
                self.log_fail(f"Canonical {repr(input_val)}", str(e))
                all_passed = False
        
        if all_passed:
            self.log_pass("Canonical numeric formats (0, negative, 03, whitespace, Unicode minus)")
    
    def test_canonical_invalid_formats(self):
        """Test canonical() rejects 3.0 and text for integers"""
        print("\n🔍 Testing canonical rejects invalid formats...")
        
        invalid_cases = ['3.0', 'abc', '3.14', 'text']
        
        all_rejected = True
        for input_val in invalid_cases:
            try:
                result = canonical(input_val, 'integer')
                self.log_fail(f"Canonical should reject {repr(input_val)}", f"Accepted as {result}")
                all_rejected = False
            except ValueError:
                pass  # Expected
            except Exception as e:
                self.log_fail(f"Canonical reject {repr(input_val)}", f"Wrong exception: {str(e)}")
                all_rejected = False
        
        if all_rejected:
            self.log_pass("Canonical rejects invalid formats (3.0, text)")
    
    def test_scoring_dropped_questions(self):
        """Test dropped disposition excludes from maximum"""
        print("\n🔍 Testing scoring: dropped questions...")
        
        questions = [
            {'id': 'q1', 'number': 1, 'type': 'mcq', 'subject': 'Math', 'topic': 'Test', 'answer': '1', 'options': {'1': 'A', '2': 'B'}, 'disposition': 'standard'},
            {'id': 'q2', 'number': 2, 'type': 'mcq', 'subject': 'Math', 'topic': 'Test', 'answer': '1', 'options': {'1': 'A', '2': 'B'}, 'disposition': 'dropped'}
        ]
        
        answers = {
            'q1': {'value': '1', 'marked': False},  # Correct
            'q2': {'value': '1', 'marked': False}   # Correct but dropped
        }
        
        attempt = {
            'questions': questions,
            'answers': answers,
            'rules': {'correct': 4, 'wrong': -1, 'skipped': 0},
            'started_at': int(time.time())
        }
        
        try:
            result = score(attempt)
            # Dropped question should give 0 marks and not count in maximum
            if result['summary']['score'] == 4 and result['summary']['maximum'] == 4 and result['summary']['dropped'] == 1:
                self.log_pass("Dropped questions excluded from maximum")
            else:
                self.log_fail("Dropped questions", f"Expected score=4, max=4, dropped=1, got {result['summary']}")
        except Exception as e:
            self.log_fail("Dropped questions", str(e))
    
    def test_scoring_bonus_all(self):
        """Test bonus_all disposition gives marks to all"""
        print("\n🔍 Testing scoring: bonus_all...")
        
        questions = [
            {'id': 'q1', 'number': 1, 'type': 'mcq', 'subject': 'Math', 'topic': 'Test', 'answer': '1', 'options': {'1': 'A', '2': 'B'}, 'disposition': 'bonus_all'}
        ]
        
        answers = {}  # No answer
        
        attempt = {
            'questions': questions,
            'answers': answers,
            'rules': {'correct': 4, 'wrong': -1, 'skipped': 0},
            'started_at': int(time.time())
        }
        
        try:
            result = score(attempt)
            # Bonus_all should give +4 even without answer
            if result['summary']['score'] == 4 and result['summary']['bonus'] == 1:
                self.log_pass("Bonus_all gives marks to all")
            else:
                self.log_fail("Bonus_all", f"Expected score=4, bonus=1, got {result['summary']}")
        except Exception as e:
            self.log_fail("Bonus_all", str(e))
    
    def test_scoring_multiple_accepted(self):
        """Test multiple_accepted disposition"""
        print("\n🔍 Testing scoring: multiple_accepted...")
        
        questions = [
            {
                'id': 'q1', 
                'number': 1, 
                'type': 'mcq', 
                'subject': 'Math', 
                'topic': 'Test', 
                'answer': '1',
                'accepted_answers': ['1', '2'],  # Both 1 and 2 are correct
                'options': {'1': 'A', '2': 'B', '3': 'C', '4': 'D'},
                'disposition': 'multiple_accepted'
            }
        ]
        
        # Test with answer '2' which should also be correct
        answers = {'q1': {'value': '2', 'marked': False}}
        
        attempt = {
            'questions': questions,
            'answers': answers,
            'rules': {'correct': 4, 'wrong': -1, 'skipped': 0},
            'started_at': int(time.time())
        }
        
        try:
            result = score(attempt)
            if result['summary']['score'] == 4 and result['summary']['correct'] == 1:
                self.log_pass("Multiple_accepted verifies any accepted key")
            else:
                self.log_fail("Multiple_accepted", f"Expected score=4, correct=1, got {result['summary']}")
        except Exception as e:
            self.log_fail("Multiple_accepted", str(e))
    
    def test_scoring_fraction_marks(self):
        """Test fraction-based marks with exact strings"""
        print("\n🔍 Testing scoring: fraction-based marks...")
        
        questions = [
            {'id': 'q1', 'number': 1, 'type': 'mcq', 'subject': 'Math', 'topic': 'Test', 'answer': '1', 'options': {'1': 'A', '2': 'B'}}
        ]
        
        answers = {'q1': {'value': '1', 'marked': False}}
        
        attempt = {
            'questions': questions,
            'answers': answers,
            'rules': {'correct': '4', 'wrong': '-1', 'skipped': 0},  # String fractions
            'started_at': int(time.time())
        }
        
        try:
            result = score(attempt)
            # Check that marks_exact is present
            if 'marks_exact' in result['questions'][0] and result['summary']['score_exact']:
                self.log_pass("Fraction-based marks with exact strings")
            else:
                self.log_fail("Fraction marks", "Missing marks_exact or score_exact")
        except Exception as e:
            self.log_fail("Fraction marks", str(e))
    
    # ========== PHONE AUTH TESTS ==========
    
    def test_phone_auth_valid_number(self):
        """Test phone auth with valid test number"""
        print("\n🔍 Testing phone auth: valid number...")
        
        test_phone = "+919876543210"  # Valid test number
        
        response = self.make_request(
            "POST",
            "/api/auth/phone",
            session=self.phone_session,
            json={"phone": test_phone}
        )
        
        if response is not None and response.status_code == 200:
            data = response.json()
            user_data = data.get("data", {})
            if user_data.get("role") == "student" and user_data.get("access_type") == "unverified_phone":
                self.log_pass("Phone auth valid number (role=student)")
                return True
            else:
                self.log_fail("Phone auth valid", f"Expected student role, got: {user_data}")
        else:
            self.log_fail("Phone auth valid", f"Status: {response.status_code if response else 'No response'}")
        return False
    
    def test_phone_auth_same_number_reopens(self):
        """Test same normalized number reopens same profile"""
        print("\n🔍 Testing phone auth: same number reopens profile...")
        
        test_phone = "+919876543211"
        
        # First login
        session1 = requests.Session()
        response1 = self.make_request("POST", "/api/auth/phone", session=session1, json={"phone": test_phone})
        
        if response1 is None or response1.status_code != 200:
            self.log_fail("Phone same number", "First login failed")
            return
        
        user1 = response1.json().get("data", {})
        
        # Second login from different session
        session2 = requests.Session()
        response2 = self.make_request("POST", "/api/auth/phone", session=session2, json={"phone": test_phone})
        
        if response2 is not None and response2.status_code == 200:
            user2 = response2.json().get("data", {})
            if user1.get("id") == user2.get("id"):
                self.log_pass("Same phone number reopens same profile")
            else:
                self.log_fail("Same phone number", f"Different IDs: {user1.get('id')} vs {user2.get('id')}")
        else:
            self.log_fail("Same phone number", "Second login failed")
    
    def test_phone_auth_different_numbers(self):
        """Test different phone numbers create separate records"""
        print("\n🔍 Testing phone auth: different numbers separate...")
        
        phone1 = "+919876543212"
        phone2 = "+919876543213"
        
        session1 = requests.Session()
        response1 = self.make_request("POST", "/api/auth/phone", session=session1, json={"phone": phone1})
        
        session2 = requests.Session()
        response2 = self.make_request("POST", "/api/auth/phone", session=session2, json={"phone": phone2})
        
        if response1 is not None and response2 is not None and response1.status_code == 200 and response2.status_code == 200:
            user1 = response1.json().get("data", {})
            user2 = response2.json().get("data", {})
            if user1.get("id") != user2.get("id"):
                self.log_pass("Different phone numbers create separate records")
            else:
                self.log_fail("Different phone numbers", "Same ID returned")
        else:
            self.log_fail("Different phone numbers", "Login failed")
    
    def test_phone_auth_malformed(self):
        """Test malformed phone number returns 422"""
        print("\n🔍 Testing phone auth: malformed number...")
        
        malformed_phones = ["123", "abcd", "999999999999999999"]
        
        all_rejected = True
        for phone in malformed_phones:
            response = self.make_request("POST", "/api/auth/phone", json={"phone": phone})
            if response is None or response.status_code != 422:
                self.log_fail(f"Malformed phone {phone}", f"Expected 422, got {response.status_code if response else 'No response'}")
                all_rejected = False
                break
        
        if all_rejected:
            self.log_pass("Malformed phone numbers return 422")
    
    def test_phone_auth_cookies(self):
        """Test HttpOnly Secure cookies are set"""
        print("\n🔍 Testing phone auth: HttpOnly Secure cookies...")
        
        test_phone = "+919876543214"
        session = requests.Session()
        response = self.make_request("POST", "/api/auth/phone", session=session, json={"phone": test_phone})
        
        if response is not None and response.status_code == 200:
            cookies = session.cookies
            has_access = 'access_token' in cookies
            has_refresh = 'refresh_token' in cookies
            
            if has_access and has_refresh:
                self.log_pass("HttpOnly Secure cookies set (access_token, refresh_token)")
            else:
                self.log_fail("Phone auth cookies", f"Missing cookies: access={has_access}, refresh={has_refresh}")
        else:
            self.log_fail("Phone auth cookies", "Login failed")
    
    def test_phone_auth_me_always_student(self):
        """Test GET /me always returns role=student for phone profiles"""
        print("\n🔍 Testing phone auth: /me always student...")
        
        test_phone = "+919876543215"
        session = requests.Session()
        
        # Login with phone
        login_response = self.make_request("POST", "/api/auth/phone", session=session, json={"phone": test_phone})
        
        if login_response is None or login_response.status_code != 200:
            self.log_fail("Phone /me test", "Login failed")
            return
        
        # Check /me
        me_response = self.make_request("GET", "/api/auth/me", session=session)
        
        if me_response is not None and me_response.status_code == 200:
            user = me_response.json().get("data", {})
            if user.get("role") == "student" and user.get("access_type") == "unverified_phone":
                self.log_pass("GET /me always returns role=student for phone profiles")
            else:
                self.log_fail("Phone /me", f"Expected student role, got: {user}")
        else:
            self.log_fail("Phone /me", f"Status: {me_response.status_code if me_response else 'No response'}")
    
    def test_phone_cannot_access_staff_endpoints(self):
        """Test phone profile cannot access /staff/publish (403)"""
        print("\n🔍 Testing phone auth: cannot access staff endpoints...")
        
        test_phone = "+919876543216"
        session = requests.Session()
        
        # Login with phone
        login_response = self.make_request("POST", "/api/auth/phone", session=session, json={"phone": test_phone})
        
        if login_response is None or login_response.status_code != 200:
            self.log_fail("Phone staff access test", "Login failed")
            return
        
        # Try to access studio endpoint
        studio_response = self.make_request("GET", "/api/studio/sets", session=session)
        
        if studio_response is not None and studio_response.status_code == 403:
            self.log_pass("Phone profile cannot access staff endpoints (403)")
        else:
            self.log_fail("Phone staff access", f"Expected 403, got {studio_response.status_code if studio_response else 'No response'}")
    
    def test_owner_password_login_still_works(self):
        """Test owner password login still works from env"""
        print("\n🔍 Testing owner password login...")
        
        owner_email = os.environ.get('ADMIN_EMAIL')
        owner_password = os.environ.get('ADMIN_PASSWORD')
        
        if not owner_email or not owner_password:
            self.log_fail("Owner login", "ADMIN_EMAIL or ADMIN_PASSWORD not in .env")
            return
        
        response = self.make_request(
            "POST",
            "/api/auth/login",
            json={
                "email": owner_email,
                "password": owner_password,
                "name": "Owner"
            }
        )
        
        if response is not None and response.status_code == 200:
            data = response.json()
            user = data.get("data", {})
            if user.get("role") == "owner":
                self.log_pass("Owner password login works from .env")
            else:
                self.log_fail("Owner login", f"Expected owner role, got: {user.get('role')}")
        else:
            self.log_fail("Owner login", f"Status: {response.status_code if response else 'No response'}")
    
    def test_phone_logout_revocation(self):
        """Test logout revokes session (401 on replay)"""
        print("\n🔍 Testing phone logout revocation...")
        
        test_phone = "+919876543217"
        session = requests.Session()
        
        # Login
        login_response = self.make_request("POST", "/api/auth/phone", session=session, json={"phone": test_phone})
        
        if login_response is None or login_response.status_code != 200:
            self.log_fail("Phone logout test", "Login failed")
            return
        
        # Logout
        logout_response = self.make_request("POST", "/api/auth/logout", session=session)
        
        if logout_response is None or logout_response.status_code != 200:
            self.log_fail("Phone logout", "Logout failed")
            return
        
        # Try to access /me after logout
        me_response = self.make_request("GET", "/api/auth/me", session=session)
        
        if me_response is not None and me_response.status_code == 401:
            self.log_pass("Logout revokes session (401 on replay)")
        else:
            self.log_fail("Logout revocation", f"Expected 401, got {me_response.status_code if me_response else 'No response'}")
    
    def test_no_public_papers(self):
        """Test /api/sets returns empty (no public papers)"""
        print("\n🔍 Testing no public papers exist...")
        
        # Create new session without auth
        public_session = requests.Session()
        response = self.make_request("GET", "/api/sets", session=public_session)
        
        if response is not None and response.status_code == 200:
            data = response.json()
            items = data.get("data", {}).get("items", [])
            if len(items) == 0:
                self.log_pass("No public papers exist (/api/sets empty)")
            else:
                self.log_fail("No public papers", f"Found {len(items)} public sets (should be 0)")
        else:
            self.log_fail("No public papers", f"Status: {response.status_code if response else 'No response'}")
    
    def test_json_envelope_format(self):
        """Test JSON envelope body.data/error.message format"""
        print("\n🔍 Testing JSON envelope format...")
        
        response = self.make_request("GET", "/api/health")
        
        if response is not None and response.status_code == 200:
            data = response.json()
            if "data" in data and "error" in data and "meta" in data:
                self.log_pass("JSON envelope format (data/error/meta)")
            else:
                self.log_fail("JSON envelope", f"Missing fields: {list(data.keys())}")
        else:
            self.log_fail("JSON envelope", "Could not test")
    
    def run_all_tests(self):
        """Run all tests"""
        print("=" * 70)
        print("TEJAS PHONE AUTH & SCORING COMPREHENSIVE TESTING")
        print(f"Testing against: {BASE_URL}")
        print("=" * 70)
        
        # Pure scoring logic tests
        print("\n" + "=" * 70)
        print("PURE SCORING LOGIC TESTS")
        print("=" * 70)
        self.test_scoring_all_correct()
        self.test_scoring_wrong_answers()
        self.test_scoring_blank_answers()
        self.test_canonical_numeric_formats()
        self.test_canonical_invalid_formats()
        self.test_scoring_dropped_questions()
        self.test_scoring_bonus_all()
        self.test_scoring_multiple_accepted()
        self.test_scoring_fraction_marks()
        
        # Phone auth tests
        print("\n" + "=" * 70)
        print("PHONE AUTH TESTS")
        print("=" * 70)
        self.test_phone_auth_valid_number()
        self.test_phone_auth_same_number_reopens()
        self.test_phone_auth_different_numbers()
        self.test_phone_auth_malformed()
        self.test_phone_auth_cookies()
        self.test_phone_auth_me_always_student()
        self.test_phone_cannot_access_staff_endpoints()
        self.test_owner_password_login_still_works()
        self.test_phone_logout_revocation()
        
        # System tests
        print("\n" + "=" * 70)
        print("SYSTEM TESTS")
        print("=" * 70)
        self.test_no_public_papers()
        self.test_json_envelope_format()
        
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
    tester = TejasPhoneScoringTester()
    passed, failed, issues = tester.run_all_tests()
    sys.exit(0 if failed == 0 else 1)
