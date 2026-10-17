"""
Backend Testing - Preview Mode Practice Flow
Tests practice flow using owner preview mode (for unpublished sets)
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

class PreviewFlowTester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.issues = []
        self.owner_session = requests.Session()
        
        # Store IDs for cross-test usage
        self.owner_id = None
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
    
    def test_get_draft_set(self):
        """Get a draft/review set for preview testing"""
        print("\n🔍 Finding draft/review set for preview testing...")
        
        response = self.make_request('GET', '/api/studio/sets', session=self.owner_session)
        
        if not response or response.status_code != 200:
            self.log_fail("Find draft set", "Could not fetch sets")
            return False
        
        data = response.json()
        if 'data' in data and len(data['data']) > 0:
            # Find a set with questions
            for item in data['data']:
                if item.get('count', 0) > 0:
                    self.test_set_id = item['id']
                    self.log_pass("Find draft set", f"Set ID: {self.test_set_id}, Title: {item.get('title')}, Questions: {item.get('count')}, Status: {item.get('status')}")
                    return True
            
            self.log_fail("Find draft set", "No sets with questions found")
            return False
        else:
            self.log_fail("Find draft set", "No sets available")
            return False
    
    def test_preflight_preview(self):
        """Test preflight check with preview mode"""
        print("\n🔍 Testing preflight check (preview mode)...")
        
        if not self.test_set_id:
            self.log_fail("Preflight preview", "No test set ID available")
            return False
        
        response = self.make_request(
            'POST',
            f'/api/sets/{self.test_set_id}/preflight',
            session=self.owner_session,
            json={'test_response': 'preview_test', 'preview': True}
        )
        
        if not response:
            self.log_fail("Preflight preview", "No response")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'].get('ok'):
                self.log_pass("Preflight preview", "Connection verified")
                return True
            else:
                self.log_fail("Preflight preview", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("Preflight preview", f"Status {response.status_code}: {response.text}")
            return False
    
    def test_start_preview_attempt(self):
        """Test starting a preview attempt"""
        print("\n🔍 Testing start preview attempt...")
        
        if not self.test_set_id:
            self.log_fail("Start preview attempt", "No test set ID available")
            return False
        
        start_key = str(uuid.uuid4())
        
        response = self.make_request(
            'POST',
            f'/api/sets/{self.test_set_id}/start',
            session=self.owner_session,
            json={
                'start_key': start_key,
                'device_checked': True,
                'preview': True
            }
        )
        
        if not response:
            self.log_fail("Start preview attempt", "No response")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'].get('id'):
                self.test_attempt_id = data['data']['id']
                questions = data['data'].get('questions', [])
                self.test_question_ids = [q['id'] for q in questions]
                question_count = len(questions)
                mode = data['data'].get('mode')
                self.log_pass("Start preview attempt", f"Attempt ID: {self.test_attempt_id}, Mode: {mode}, Questions: {question_count}")
                return True
            else:
                self.log_fail("Start preview attempt", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("Start preview attempt", f"Status {response.status_code}: {response.text}")
            return False
    
    def test_get_preview_attempt(self):
        """Test getting preview attempt details"""
        print("\n🔍 Testing GET preview attempt...")
        
        if not self.test_attempt_id:
            self.log_fail("GET preview attempt", "No test attempt ID available")
            return False
        
        response = self.make_request(
            'GET',
            f'/api/attempts/{self.test_attempt_id}',
            session=self.owner_session
        )
        
        if not response:
            self.log_fail("GET preview attempt", "No response")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'].get('id') == self.test_attempt_id:
                status = data['data'].get('status')
                mode = data['data'].get('mode')
                question_count = len(data['data'].get('questions', []))
                self.log_pass("GET preview attempt", f"Status: {status}, Mode: {mode}, Questions: {question_count}")
                return True
            else:
                self.log_fail("GET preview attempt", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("GET preview attempt", f"Status {response.status_code}")
            return False
    
    def test_visit_questions_preview(self):
        """Test visiting multiple questions in preview"""
        print("\n🔍 Testing visit questions (preview)...")
        
        if not self.test_attempt_id or not self.test_question_ids:
            self.log_fail("Visit questions preview", "No test attempt or question IDs available")
            return False
        
        # Visit first 3 questions
        visited_count = 0
        for i in range(min(3, len(self.test_question_ids))):
            question_id = self.test_question_ids[i]
            
            response = self.make_request(
                'POST',
                f'/api/attempts/{self.test_attempt_id}/visit',
                session=self.owner_session,
                json={'question_id': question_id}
            )
            
            if response and response.status_code == 200:
                visited_count += 1
        
        if visited_count > 0:
            self.log_pass("Visit questions preview", f"Visited {visited_count} questions")
            return True
        else:
            self.log_fail("Visit questions preview", "Could not visit any questions")
            return False
    
    def test_save_multiple_answers(self):
        """Test saving answers to multiple questions"""
        print("\n🔍 Testing save multiple answers...")
        
        if not self.test_attempt_id or not self.test_question_ids:
            self.log_fail("Save multiple answers", "No test attempt or question IDs available")
            return False
        
        # Get attempt details to check question types
        response = self.make_request(
            'GET',
            f'/api/attempts/{self.test_attempt_id}',
            session=self.owner_session
        )
        
        if not response or response.status_code != 200:
            self.log_fail("Save multiple answers", "Could not fetch attempt details")
            return False
        
        data = response.json()
        questions = data['data'].get('questions', [])
        
        saved_count = 0
        # Save answers to first 5 questions
        for i in range(min(5, len(questions))):
            q = questions[i]
            qid = q['id']
            qtype = q['type']
            
            # Determine answer based on question type
            if qtype == 'mcq':
                # Get first option key
                options = q.get('options', {})
                answer_value = list(options.keys())[0] if options else '1'
            else:  # integer
                answer_value = '42'
            
            response = self.make_request(
                'PUT',
                f'/api/attempts/{self.test_attempt_id}/answers/{qid}',
                session=self.owner_session,
                json={
                    'value': answer_value,
                    'marked': False,
                    'revision': 1,
                    'request_id': str(uuid.uuid4())
                }
            )
            
            if response and response.status_code == 200:
                saved_count += 1
        
        if saved_count > 0:
            self.log_pass("Save multiple answers", f"Saved {saved_count} answers")
            return True
        else:
            self.log_fail("Save multiple answers", "Could not save any answers")
            return False
    
    def test_update_answer(self):
        """Test updating an existing answer"""
        print("\n🔍 Testing update answer (revision)...")
        
        if not self.test_attempt_id or not self.test_question_ids:
            self.log_fail("Update answer", "No test attempt or question IDs available")
            return False
        
        question_id = self.test_question_ids[0]
        
        # Update the answer (revision 2)
        response = self.make_request(
            'PUT',
            f'/api/attempts/{self.test_attempt_id}/answers/{question_id}',
            session=self.owner_session,
            json={
                'value': '2',
                'marked': True,
                'revision': 2,
                'request_id': str(uuid.uuid4())
            }
        )
        
        if not response:
            self.log_fail("Update answer", "No response")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'accepted' in data['data']:
                accepted = data['data']['accepted']
                value = accepted.get('value')
                marked = accepted.get('marked')
                revision = accepted.get('revision')
                self.log_pass("Update answer", f"Updated to value: {value}, marked: {marked}, revision: {revision}")
                return True
            else:
                self.log_fail("Update answer", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("Update answer", f"Status {response.status_code}: {response.text}")
            return False
    
    def test_submit_preview_attempt(self):
        """Test submitting preview attempt"""
        print("\n🔍 Testing submit preview attempt...")
        
        if not self.test_attempt_id:
            self.log_fail("Submit preview attempt", "No test attempt ID available")
            return False
        
        response = self.make_request(
            'POST',
            f'/api/attempts/{self.test_attempt_id}/submit',
            session=self.owner_session
        )
        
        if not response:
            self.log_fail("Submit preview attempt", "No response")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'].get('status') == 'completed':
                receipt = data['data'].get('receipt')
                self.log_pass("Submit preview attempt", f"Receipt: {receipt}")
                return True
            else:
                self.log_fail("Submit preview attempt", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("Submit preview attempt", f"Status {response.status_code}")
            return False
    
    def test_get_preview_results(self):
        """Test getting results for preview attempt"""
        print("\n🔍 Testing GET preview results...")
        
        if not self.test_attempt_id:
            self.log_fail("GET preview results", "No test attempt ID available")
            return False
        
        response = self.make_request(
            'GET',
            f'/api/attempts/{self.test_attempt_id}/results',
            session=self.owner_session
        )
        
        if not response:
            self.log_fail("GET preview results", "No response")
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
                accuracy = summary.get('accuracy')
                
                # Get detailed question results
                questions = data['data'].get('questions', [])
                outcomes = {}
                for q in questions:
                    outcome = q.get('outcome', 'unknown')
                    outcomes[outcome] = outcomes.get(outcome, 0) + 1
                
                self.log_pass("GET preview results", 
                    f"Score: {score}/{maximum}, Correct: {correct}, Incorrect: {incorrect}, Skipped: {skipped}, Accuracy: {accuracy}%, Outcomes: {outcomes}")
                return True
            else:
                self.log_fail("GET preview results", f"Invalid response: {data}")
                return False
        else:
            self.log_fail("GET preview results", f"Status {response.status_code}")
            return False
    
    def test_get_question_asset(self):
        """Test getting question asset"""
        print("\n🔍 Testing GET question asset...")
        
        if not self.test_attempt_id or not self.test_question_ids:
            self.log_fail("GET question asset", "No test attempt or question IDs available")
            return False
        
        # Get attempt details to find a question with assets
        response = self.make_request(
            'GET',
            f'/api/attempts/{self.test_attempt_id}/results',
            session=self.owner_session
        )
        
        if not response or response.status_code != 200:
            self.log_fail("GET question asset", "Could not fetch results")
            return False
        
        data = response.json()
        questions = data['data'].get('questions', [])
        
        # Find a question with assets
        for q in questions:
            if q.get('asset_count', 0) > 0:
                qid = q['id']
                
                # Try to get the first question asset
                asset_response = self.make_request(
                    'GET',
                    f'/api/attempts/{self.test_attempt_id}/questions/{qid}/asset/question/0',
                    session=self.owner_session
                )
                
                if asset_response and asset_response.status_code == 200:
                    content_type = asset_response.headers.get('content-type', '')
                    content_length = len(asset_response.content)
                    self.log_pass("GET question asset", f"Asset retrieved: {content_type}, Size: {content_length} bytes")
                    return True
        
        # If no questions with assets, that's okay
        self.log_pass("GET question asset", "No questions with assets (typed questions)")
        return True
    
    def test_retry_attempt(self):
        """Test creating a retry attempt for incorrect questions"""
        print("\n🔍 Testing retry attempt creation...")
        
        if not self.test_attempt_id:
            self.log_fail("Retry attempt", "No test attempt ID available")
            return False
        
        retry_key = str(uuid.uuid4())
        
        response = self.make_request(
            'POST',
            f'/api/attempts/{self.test_attempt_id}/retry',
            session=self.owner_session,
            json={'start_key': retry_key}
        )
        
        if not response:
            self.log_fail("Retry attempt", "No response")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'].get('id'):
                retry_id = data['data']['id']
                self.log_pass("Retry attempt", f"Retry attempt created: {retry_id}")
                return True
            else:
                self.log_fail("Retry attempt", f"Invalid response: {data}")
                return False
        elif response.status_code == 400:
            # This is okay if there are no incorrect questions
            error_msg = response.json().get('error', {}).get('message', '')
            if 'no incorrect or skipped questions' in error_msg.lower():
                self.log_pass("Retry attempt", "No incorrect questions to retry (all correct)")
                return True
            else:
                self.log_fail("Retry attempt", f"Status {response.status_code}: {error_msg}")
                return False
        else:
            self.log_fail("Retry attempt", f"Status {response.status_code}: {response.text}")
            return False
    
    def run_all_tests(self):
        """Run all preview flow tests"""
        print("=" * 80)
        print("BACKEND TESTING - PREVIEW MODE PRACTICE FLOW")
        print("=" * 80)
        print(f"Base URL: {BASE_URL}")
        print(f"Owner Email: {OWNER_EMAIL}")
        print("=" * 80)
        
        # Phase 1: Setup
        print("\n" + "=" * 80)
        print("PHASE 1: AUTHENTICATION & SETUP")
        print("=" * 80)
        
        if not self.test_owner_login():
            print("\n⚠️  Owner login failed - cannot continue")
            return False
        
        if not self.test_get_draft_set():
            print("\n⚠️  No draft sets available - cannot continue")
            return False
        
        # Phase 2: Practice Flow
        print("\n" + "=" * 80)
        print("PHASE 2: PREVIEW PRACTICE FLOW")
        print("=" * 80)
        
        self.test_preflight_preview()
        
        if self.test_start_preview_attempt():
            self.test_get_preview_attempt()
            self.test_visit_questions_preview()
            self.test_save_multiple_answers()
            self.test_update_answer()
            self.test_submit_preview_attempt()
            self.test_get_preview_results()
            self.test_get_question_asset()
            self.test_retry_attempt()
        
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
    tester = PreviewFlowTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
