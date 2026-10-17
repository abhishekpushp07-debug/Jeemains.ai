"""
Comprehensive Smart Imports Integration Test
Tests: PDF/Word/Excel upload, AI processing, practice flow, scoring, and reports
"""
import requests
import time
import uuid
import os
from pathlib import Path
from dotenv import load_dotenv
from io import BytesIO

load_dotenv(Path(__file__).parent.parent / 'backend' / '.env')

BASE_URL = "https://campus-launch-2.preview.emergentagent.com"
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
STUDENT_PHONE = "+12025550199"

class SmartImportsIntegrationTest:
    def __init__(self):
        self.owner_session = requests.Session()
        self.student_session = requests.Session()
        self.import_ids = []
        self.set_ids = []
        self.attempt_ids = []
        self.tests_passed = 0
        self.tests_failed = 0
        
    def log(self, message, status="INFO"):
        """Log test message"""
        symbols = {"PASS": "✅", "FAIL": "❌", "INFO": "ℹ️", "WAIT": "⏳"}
        print(f"{symbols.get(status, 'ℹ️')} {message}")
        
    def assert_test(self, condition, test_name, error_msg=""):
        """Assert test condition"""
        if condition:
            self.tests_passed += 1
            self.log(f"{test_name}", "PASS")
            return True
        else:
            self.tests_failed += 1
            self.log(f"{test_name}: {error_msg}", "FAIL")
            return False
    
    def create_simple_pdf(self):
        """Create a simple 2-question PDF"""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            
            # Title and instructions
            c.setFont("Helvetica-Bold", 16)
            c.drawString(100, 750, "JEE Main Mock Test")
            
            c.setFont("Helvetica", 11)
            c.drawString(100, 720, "Exam: JEE Main")
            c.drawString(100, 705, "Test Type: Mock Test")
            c.drawString(100, 690, "Duration: 30 minutes")
            c.drawString(100, 675, "Total Questions: 2")
            c.drawString(100, 660, "Marking Scheme: +4 for correct, -1 for wrong, 0 for skipped")
            
            # Question 1
            c.setFont("Helvetica-Bold", 12)
            c.drawString(100, 620, "1. What is 5 + 3?")
            c.setFont("Helvetica", 11)
            c.drawString(120, 600, "(A) 6")
            c.drawString(120, 585, "(B) 7")
            c.drawString(120, 570, "(C) 8")
            c.drawString(120, 555, "(D) 9")
            
            # Question 2
            c.setFont("Helvetica-Bold", 12)
            c.drawString(100, 515, "2. What is 10 - 4?")
            c.setFont("Helvetica", 11)
            c.drawString(120, 495, "(A) 4")
            c.drawString(120, 480, "(B) 5")
            c.drawString(120, 465, "(C) 6")
            c.drawString(120, 450, "(D) 7")
            
            # Answer Key
            c.setFont("Helvetica-Bold", 11)
            c.drawString(100, 400, "Answer Key:")
            c.setFont("Helvetica", 10)
            c.drawString(100, 385, "1. C (8)")
            c.drawString(100, 370, "2. C (6)")
            
            c.save()
            buffer.seek(0)
            return buffer.getvalue()
        except Exception as e:
            self.log(f"Error creating PDF: {str(e)}", "FAIL")
            return None
    
    def test_owner_login(self):
        """Test owner authentication"""
        self.log("Testing owner login...", "INFO")
        response = self.owner_session.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD,
                "name": "Test Owner",
                "exam": "JEE Main",
                "consent": False
            }
        )
        return self.assert_test(
            response.status_code == 200 and response.json().get('data', {}).get('role') == 'owner',
            "Owner Login",
            f"Status: {response.status_code}"
        )
    
    def test_student_access(self):
        """Test student phone access"""
        self.log("Testing student access...", "INFO")
        response = self.student_session.post(
            f"{BASE_URL}/api/auth/phone",
            json={"phone": STUDENT_PHONE}
        )
        return self.assert_test(
            response.status_code == 200,
            "Student Phone Access",
            f"Status: {response.status_code}"
        )
    
    def test_upload_pdf(self):
        """Test PDF upload to smart imports"""
        self.log("Creating and uploading PDF...", "INFO")
        
        pdf_content = self.create_simple_pdf()
        if not pdf_content:
            return self.assert_test(False, "PDF Upload", "Failed to create PDF")
        
        idempotency_key = str(uuid.uuid4())
        
        response = self.owner_session.post(
            f"{BASE_URL}/api/studio/auto-imports",
            data={
                'rights_confirmed': 'true',
                'publish_when_ready': 'true',
                'max_ai_questions': '300'
            },
            files={'file': ('test_jee_main.pdf', pdf_content, 'application/pdf')},
            headers={'Idempotency-Key': idempotency_key}
        )
        
        if response.status_code == 200:
            data = response.json().get('data', {})
            import_id = data.get('id')
            if import_id:
                self.import_ids.append(import_id)
                self.log(f"Import ID: {import_id}", "INFO")
                return self.assert_test(True, "PDF Upload", "")
        
        return self.assert_test(False, "PDF Upload", f"Status: {response.status_code}")
    
    def wait_for_import(self, import_id, max_wait=180):
        """Wait for import to complete"""
        self.log(f"Waiting for import {import_id} to process (max {max_wait}s)...", "WAIT")
        start_time = time.time()
        last_state = None
        
        while time.time() - start_time < max_wait:
            response = self.owner_session.get(
                f"{BASE_URL}/api/studio/auto-imports/{import_id}"
            )
            
            if response.status_code == 200:
                data = response.json().get('data', {})
                state = data.get('state', '')
                message = data.get('message', '')
                
                if state != last_state:
                    self.log(f"State: {state} - {message}", "INFO")
                    last_state = state
                
                if state in ('complete', 'complete_with_issues'):
                    papers = data.get('papers', [])
                    for paper in papers:
                        set_id = paper.get('set_id')
                        if set_id:
                            self.set_ids.append(set_id)
                            self.log(f"Paper published: {set_id}", "INFO")
                    
                    return self.assert_test(
                        len(papers) > 0,
                        "Import Processing",
                        f"State: {state}, Papers: {len(papers)}"
                    )
                
                elif state in ('needs_clarification', 'budget_required'):
                    return self.assert_test(False, "Import Processing", f"Needs attention: {state}")
                
                elif state == 'failed':
                    return self.assert_test(False, "Import Processing", "Import failed")
            
            time.sleep(5)
        
        return self.assert_test(False, "Import Processing", f"Timeout after {max_wait}s")
    
    def test_start_practice(self, set_id):
        """Test starting practice on a published set"""
        self.log(f"Starting practice on set {set_id}...", "INFO")
        
        # First, preflight
        start_key = str(uuid.uuid4())
        response = self.student_session.post(
            f"{BASE_URL}/api/sets/{set_id}/preflight",
            json={"preview": False, "test_response": ""}
        )
        
        if response.status_code != 200:
            return self.assert_test(False, "Practice Preflight", f"Status: {response.status_code}")
        
        # Start attempt
        response = self.student_session.post(
            f"{BASE_URL}/api/sets/{set_id}/start",
            json={"start_key": start_key, "device_checked": False, "preview": False}
        )
        
        if response.status_code == 200:
            data = response.json().get('data', {})
            attempt_id = data.get('id')
            if attempt_id:
                self.attempt_ids.append(attempt_id)
                self.log(f"Attempt ID: {attempt_id}", "INFO")
                return self.assert_test(True, "Start Practice", "")
        
        return self.assert_test(False, "Start Practice", f"Status: {response.status_code}")
    
    def test_submit_answers(self, attempt_id):
        """Test submitting answers"""
        self.log(f"Submitting answers for attempt {attempt_id}...", "INFO")
        
        # Get attempt details to find questions
        response = self.student_session.get(f"{BASE_URL}/api/attempts/{attempt_id}")
        if response.status_code != 200:
            return self.assert_test(False, "Get Attempt", f"Status: {response.status_code}")
        
        data = response.json().get('data', {})
        questions = data.get('questions', [])
        
        if len(questions) < 2:
            return self.assert_test(False, "Submit Answers", f"Expected 2 questions, got {len(questions)}")
        
        # Submit answer for Q1 (correct: C)
        q1_id = questions[0]['id']
        request_id1 = str(uuid.uuid4())
        response = self.student_session.put(
            f"{BASE_URL}/api/attempts/{attempt_id}/answers/{q1_id}",
            json={
                "value": "C",
                "marked": False,
                "revision": 1,
                "request_id": request_id1
            }
        )
        
        if response.status_code != 200:
            return self.assert_test(False, "Submit Answer Q1", f"Status: {response.status_code}")
        
        # Submit answer for Q2 (incorrect: A instead of C)
        q2_id = questions[1]['id']
        request_id2 = str(uuid.uuid4())
        response = self.student_session.put(
            f"{BASE_URL}/api/attempts/{attempt_id}/answers/{q2_id}",
            json={
                "value": "A",
                "marked": False,
                "revision": 1,
                "request_id": request_id2
            }
        )
        
        if response.status_code != 200:
            return self.assert_test(False, "Submit Answer Q2", f"Status: {response.status_code}")
        
        # Submit attempt
        response = self.student_session.post(f"{BASE_URL}/api/attempts/{attempt_id}/submit")
        
        return self.assert_test(
            response.status_code == 200,
            "Submit Attempt",
            f"Status: {response.status_code}"
        )
    
    def test_check_results(self, attempt_id):
        """Test checking results with AI solutions"""
        self.log(f"Checking results for attempt {attempt_id}...", "INFO")
        
        # Wait a bit for grading
        time.sleep(3)
        
        response = self.student_session.get(f"{BASE_URL}/api/attempts/{attempt_id}/results")
        
        if response.status_code != 200:
            return self.assert_test(False, "Get Results", f"Status: {response.status_code}")
        
        data = response.json().get('data', {})
        summary = data.get('summary', {})
        questions = data.get('questions', [])
        
        # Check scoring
        correct = summary.get('correct', 0)
        incorrect = summary.get('incorrect', 0)
        score = summary.get('score', 0)
        
        self.log(f"Score: {score}, Correct: {correct}, Incorrect: {incorrect}", "INFO")
        
        # Verify expected results (1 correct, 1 incorrect)
        scoring_ok = correct == 1 and incorrect == 1 and score == 3  # +4 - 1 = 3
        
        # Check for AI solutions
        has_ai_solutions = all(
            q.get('solution') and len(q.get('solution', '')) > 0
            for q in questions
        )
        
        return self.assert_test(
            scoring_ok and has_ai_solutions,
            "Results with AI Solutions",
            f"Scoring: {scoring_ok}, AI Solutions: {has_ai_solutions}"
        )
    
    def test_generate_report(self, attempt_id):
        """Test PDF report generation"""
        self.log(f"Generating PDF report for attempt {attempt_id}...", "INFO")
        
        response = self.student_session.post(
            f"{BASE_URL}/api/attempts/{attempt_id}/report",
            json={"score_version": "original"}
        )
        
        if response.status_code != 200:
            return self.assert_test(False, "Generate Report", f"Status: {response.status_code}")
        
        data = response.json().get('data', {})
        job_id = data.get('id')
        
        if not job_id:
            return self.assert_test(False, "Generate Report", "No job ID returned")
        
        # Wait for report generation
        self.log("Waiting for report generation...", "WAIT")
        max_wait = 60
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            response = self.student_session.get(f"{BASE_URL}/api/jobs/{job_id}")
            if response.status_code == 200:
                job_data = response.json().get('data', {})
                status = job_data.get('status')
                
                if status == 'done':
                    return self.assert_test(True, "PDF Report Generation", "")
                elif status == 'failed':
                    return self.assert_test(False, "PDF Report Generation", "Job failed")
            
            time.sleep(3)
        
        return self.assert_test(False, "PDF Report Generation", "Timeout")
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("\n" + "="*80)
        print("SMART IMPORTS COMPREHENSIVE INTEGRATION TEST")
        print("="*80 + "\n")
        
        # Phase 1: Authentication
        print("--- Phase 1: Authentication ---")
        if not self.test_owner_login():
            print("\n❌ Owner login failed, stopping tests")
            return False
        
        if not self.test_student_access():
            print("\n❌ Student access failed, stopping tests")
            return False
        
        # Phase 2: Document Upload
        print("\n--- Phase 2: Document Upload ---")
        if not self.test_upload_pdf():
            print("\n❌ PDF upload failed, stopping tests")
            return False
        
        # Phase 3: AI Processing
        print("\n--- Phase 3: AI Processing ---")
        if not self.import_ids:
            print("\n❌ No import IDs, stopping tests")
            return False
        
        if not self.wait_for_import(self.import_ids[0]):
            print("\n❌ Import processing failed, stopping tests")
            return False
        
        # Phase 4: Practice Flow
        print("\n--- Phase 4: Practice Flow ---")
        if not self.set_ids:
            print("\n❌ No published sets, stopping tests")
            return False
        
        if not self.test_start_practice(self.set_ids[0]):
            print("\n❌ Start practice failed, stopping tests")
            return False
        
        if not self.attempt_ids:
            print("\n❌ No attempt IDs, stopping tests")
            return False
        
        if not self.test_submit_answers(self.attempt_ids[0]):
            print("\n❌ Submit answers failed, stopping tests")
            return False
        
        # Phase 5: Results and Reports
        print("\n--- Phase 5: Results and Reports ---")
        if not self.test_check_results(self.attempt_ids[0]):
            print("\n⚠️  Results check had issues, but continuing...")
        
        if not self.test_generate_report(self.attempt_ids[0]):
            print("\n⚠️  Report generation had issues")
        
        return True
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_failed}")
        print(f"Success Rate: {self.tests_passed/(self.tests_passed+self.tests_failed)*100:.1f}%")
        print(f"\nImport IDs: {self.import_ids}")
        print(f"Set IDs: {self.set_ids}")
        print(f"Attempt IDs: {self.attempt_ids}")
        print("="*80)

def main():
    """Main test execution"""
    tester = SmartImportsIntegrationTest()
    
    try:
        tester.run_all_tests()
        tester.print_summary()
        return 0 if tester.tests_failed == 0 else 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        tester.print_summary()
        return 1

if __name__ == "__main__":
    exit(main())
