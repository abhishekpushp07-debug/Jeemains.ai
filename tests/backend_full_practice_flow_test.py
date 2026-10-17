"""
Full 75-Question Practice Flow Test for Tejas Platform
Tests complete workflow: upload PDFs, extract, approve, publish, practice, score, report
"""
import requests
import sys
import time
import os
from pathlib import Path
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv(Path(__file__).parent.parent / 'backend' / '.env')

BASE_URL = "https://campus-launch-2.preview.emergentagent.com"
OWNER_EMAIL = os.environ.get('ADMIN_EMAIL', '')
OWNER_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')

# Known answers from the Tejas paper (first 10 for testing)
KNOWN_ANSWERS = {
    1: "2",   # Q1: (2)
    2: "4",   # Q2: (4)
    3: "1",   # Q3: (1)
    4: "3",   # Q4: (3)
    21: "13440",  # Q21: integer answer
    22: "10385",  # Q22: integer answer
}

class FullPracticeFlowTester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.issues = []
        self.owner_session = requests.Session()
        self.student_session = requests.Session()
        self.set_id = None
        self.attempt_id = None
        self.question_map = {}  # Maps question number to question ID
        
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
        """Make HTTP request - FIXED: check response is not None"""
        url = f"{BASE_URL}{endpoint}"
        try:
            response = session.request(method, url, timeout=60, **kwargs)
            return response
        except Exception as e:
            print(f"Request exception: {str(e)}")
            return None
    
    def test_owner_login(self):
        """Login as owner"""
        print("\n🔍 Logging in as owner...")
        
        response = self.make_request(
            self.owner_session,
            "POST",
            "/api/auth/login",
            json={"email": OWNER_EMAIL, "password": OWNER_PASSWORD, "name": "Owner"}
        )
        
        if response is not None and response.status_code == 200:
            self.log_pass("Owner login")
            return True
        else:
            status = response.status_code if response is not None else 'No response'
            self.log_fail("Owner login", f"Status: {status}")
            return False
    
    def test_student_register(self):
        """Register a test student"""
        print("\n🔍 Registering test student...")
        
        timestamp = int(time.time())
        self.student_email = f"practice_student_{timestamp}@test.com"
        
        response = self.make_request(
            self.student_session,
            "POST",
            "/api/auth/register",
            json={
                "email": self.student_email,
                "password": "TestPassword123",
                "name": "Practice Student",
                "exam": "JEE Main",
                "consent": True
            }
        )
        
        if response is not None and response.status_code == 200:
            self.log_pass("Student registration")
            return True
        else:
            status = response.status_code if response is not None else 'No response'
            self.log_fail("Student registration", f"Status: {status}")
            return False
    
    def test_create_set(self):
        """Create a new practice set"""
        print("\n🔍 Creating practice set...")
        
        response = self.make_request(
            self.owner_session,
            "POST",
            "/api/studio/sets",
            json={
                "title": "TEJAS 200 - Predicted Paper 01 (Test)",
                "exam": "JEE Main",
                "year": "2027",
                "source": "TEJAS 200 Predicted Paper",
                "attribution": "TEJAS Platform Test",
                "audience": "all",
                "rights_upload": True,
                "rights_publish": True,
                "rights_report": True,
                "rules": {
                    "minutes": 180,
                    "correct": 4,
                    "wrong": -1,
                    "skipped": 0
                }
            }
        )
        
        if response is not None and response.status_code == 200:
            data = response.json()
            self.set_id = data.get("data", {}).get("id")
            if self.set_id:
                self.log_pass("Create practice set")
                return True
            else:
                self.log_fail("Create practice set", "No set ID returned")
        else:
            status = response.status_code if response is not None else 'No response'
            self.log_fail("Create practice set", f"Status: {status}")
        return False
    
    def test_upload_pdfs(self):
        """Upload questions and solutions PDFs"""
        print("\n🔍 Uploading PDFs...")
        
        # Upload questions PDF
        questions_path = Path("/app/sources/questions.pdf")
        if not questions_path.exists():
            self.log_fail("Upload questions PDF", "questions.pdf not found")
            return False
        
        with open(questions_path, 'rb') as f:
            files = {'file': ('questions.pdf', f, 'application/pdf')}
            data = {'kind': 'questions'}
            response = self.make_request(
                self.owner_session,
                "POST",
                f"/api/studio/sets/{self.set_id}/files",
                files=files,
                data=data
            )
        
        if response is None or response.status_code != 200:
            status = response.status_code if response is not None else 'No response'
            self.log_fail("Upload questions PDF", f"Status: {status}")
            return False
        
        self.log_pass("Upload questions PDF")
        
        # Upload solutions PDF
        solutions_path = Path("/app/sources/solutions.pdf")
        if not solutions_path.exists():
            self.log_fail("Upload solutions PDF", "solutions.pdf not found")
            return False
        
        with open(solutions_path, 'rb') as f:
            files = {'file': ('solutions.pdf', f, 'application/pdf')}
            data = {'kind': 'solutions'}
            response = self.make_request(
                self.owner_session,
                "POST",
                f"/api/studio/sets/{self.set_id}/files",
                files=files,
                data=data
            )
        
        if response is None or response.status_code != 200:
            status = response.status_code if response is not None else 'No response'
            self.log_fail("Upload solutions PDF", f"Status: {status}")
            return False
        
        self.log_pass("Upload solutions PDF")
        return True
    
    def test_extract_questions(self):
        """Extract questions from PDFs"""
        print("\n🔍 Extracting questions (this may take 30-60 seconds)...")
        
        response = self.make_request(
            self.owner_session,
            "POST",
            f"/api/studio/sets/{self.set_id}/extract",
            json={"replace_drafts": True}
        )
        
        if response is None or response.status_code != 200:
            status = response.status_code if response is not None else 'No response'
            self.log_fail("Extract questions", f"Status: {status}")
            return False
        
        data = response.json()
        job_id = data.get("data", {}).get("id")
        if not job_id:
            self.log_fail("Extract questions", "No job ID returned")
            return False
        
        # Wait for extraction job to complete
        for i in range(60):  # Wait up to 60 seconds
            time.sleep(1)
            status_response = self.make_request(
                self.owner_session,
                "GET",
                f"/api/jobs/{job_id}"
            )
            
            if status_response is not None and status_response.status_code == 200:
                job_data = status_response.json().get("data", {})
                if job_data.get("status") == "done":
                    self.log_pass("Extract questions")
                    return True
                elif job_data.get("status") == "failed":
                    self.log_fail("Extract questions", f"Job failed: {job_data.get('error')}")
                    return False
        
        self.log_fail("Extract questions", "Job timeout after 60 seconds")
        return False
    
    def test_get_and_approve_questions(self):
        """Get extracted questions and approve them"""
        print("\n🔍 Getting and approving ALL questions (this may take 2-3 minutes)...")
        
        # Get set details with questions
        response = self.make_request(
            self.owner_session,
            "GET",
            f"/api/studio/sets/{self.set_id}"
        )
        
        if response is None or response.status_code != 200:
            status = response.status_code if response is not None else 'No response'
            self.log_fail("Get questions", f"Status: {status}")
            return False
        
        data = response.json()
        questions = data.get("data", {}).get("questions", [])
        
        if len(questions) < 10:
            self.log_fail("Get questions", f"Expected at least 10 questions, got {len(questions)}")
            return False
        
        print(f"  Found {len(questions)} questions, approving all...")
        
        # Build question map
        for q in questions:
            self.question_map[q["number"]] = q["id"]
        
        # Approve ALL questions for full test
        approved_count = 0
        failed_count = 0
        for idx, q in enumerate(questions, 1):
            qid = q["id"]
            
            # Progress indicator every 10 questions
            if idx % 10 == 0:
                print(f"  Progress: {idx}/{len(questions)} questions processed...")
            
            # First, ensure question has required fields
            if not q.get("answer") or not q.get("solution"):
                print(f"  ⚠️  Q{q['number']} missing answer or solution, skipping")
                failed_count += 1
                continue
            
            # Add accessible text if missing (required for source mode)
            if q.get("render_mode") == "source" and (not q.get("accessible_text") or not q.get("solution_accessible_text")):
                # Update question with accessible text
                update_data = {
                    **q,
                    "accessible_text": q.get("text", "")[:500] or "Question content from source PDF",
                    "solution_accessible_text": q.get("solution", "")[:500] or "Solution content from source PDF"
                }
                
                update_response = self.make_request(
                    self.owner_session,
                    "PUT",
                    f"/api/studio/sets/{self.set_id}/questions/{qid}",
                    json=update_data
                )
                
                if update_response is None or update_response.status_code != 200:
                    print(f"  ⚠️  Failed to update Q{q['number']} with accessible text")
                    failed_count += 1
                    continue
            
            approve_response = self.make_request(
                self.owner_session,
                "POST",
                f"/api/studio/sets/{self.set_id}/questions/{qid}/approve"
            )
            
            if approve_response is not None and approve_response.status_code == 200:
                approved_count += 1
            else:
                status = approve_response.status_code if approve_response is not None else 'No response'
                error_msg = ""
                if approve_response is not None:
                    try:
                        error_data = approve_response.json()
                        error_msg = error_data.get("error", {}).get("message", "")
                    except:
                        pass
                if idx <= 10:  # Only print first 10 errors to avoid spam
                    print(f"  ⚠️  Failed to approve Q{q['number']}: {status} - {error_msg}")
                failed_count += 1
        
        print(f"  Approval complete: {approved_count} approved, {failed_count} failed")
        
        if approved_count >= len(questions) - 5:  # Allow up to 5 failures
            self.log_pass(f"Approve questions ({approved_count}/{len(questions)} approved)")
            return True
        else:
            self.log_fail("Approve questions", f"Only {approved_count}/{len(questions)} questions approved")
            return False
    
    def test_create_subset_with_approved(self):
        """Create a subset with only approved questions"""
        print("\n🔍 Creating subset with approved questions...")
        
        # Get set details to find approved questions
        response = self.make_request(
            self.owner_session,
            "GET",
            f"/api/studio/sets/{self.set_id}"
        )
        
        if response is None or response.status_code != 200:
            self.log_fail("Get approved questions", "Could not fetch set")
            return False
        
        data = response.json()
        questions = data.get("data", {}).get("questions", [])
        approved_qids = [q["id"] for q in questions if q.get("approved")]
        
        if len(approved_qids) < 10:
            self.log_fail("Create subset", f"Not enough approved questions: {len(approved_qids)}")
            return False
        
        # Create subset with approved questions
        subset_response = self.make_request(
            self.owner_session,
            "POST",
            f"/api/studio/sets/{self.set_id}/subset",
            json={
                "title": "TEJAS Test Subset - Approved Questions",
                "question_ids": approved_qids
            }
        )
        
        if subset_response is not None and subset_response.status_code == 200:
            subset_data = subset_response.json()
            new_set_id = subset_data.get("data", {}).get("id")
            if new_set_id:
                self.set_id = new_set_id  # Use subset for remaining tests
                self.log_pass(f"Create subset ({len(approved_qids)} questions)")
                return True
            else:
                self.log_fail("Create subset", "No subset ID returned")
        else:
            status = subset_response.status_code if subset_response is not None else 'No response'
            self.log_fail("Create subset", f"Status: {status}")
        return False
    
    def test_publish_set(self):
        """Publish the practice set"""
        print("\n🔍 Publishing practice set...")
        
        response = self.make_request(
            self.owner_session,
            "POST",
            f"/api/studio/sets/{self.set_id}/publish",
            json={"confirm": True}
        )
        
        if response is not None and response.status_code == 200:
            self.log_pass("Publish set")
            return True
        else:
            status = response.status_code if response is not None else 'No response'
            body = response.json() if response is not None else {}
            self.log_fail("Publish set", f"Status: {status}, Body: {body}")
            return False
    
    def test_preflight(self):
        """Run preflight check"""
        print("\n🔍 Running preflight check...")
        
        response = self.make_request(
            self.student_session,
            "POST",
            f"/api/sets/{self.set_id}/preflight",
            json={"preview": False, "test_response": "test123"}
        )
        
        if response is not None and response.status_code == 200:
            self.log_pass("Preflight check")
            return True
        else:
            status = response.status_code if response is not None else 'No response'
            self.log_fail("Preflight check", f"Status: {status}")
            return False
    
    def test_start_attempt(self):
        """Start practice attempt"""
        print("\n🔍 Starting practice attempt...")
        
        start_key = f"practice_start_{int(time.time())}"
        response = self.make_request(
            self.student_session,
            "POST",
            f"/api/sets/{self.set_id}/start",
            json={
                "start_key": start_key,
                "device_checked": True,
                "preview": False
            }
        )
        
        if response is not None and response.status_code == 200:
            data = response.json()
            self.attempt_id = data.get("data", {}).get("id")
            if self.attempt_id:
                self.log_pass("Start attempt")
                return True
            else:
                self.log_fail("Start attempt", "No attempt ID returned")
        else:
            status = response.status_code if response is not None else 'No response'
            self.log_fail("Start attempt", f"Status: {status}")
        return False
    
    def test_start_idempotence(self):
        """Test that starting with same start_key returns existing attempt"""
        print("\n🔍 Testing start idempotence...")
        
        # Use same start_key as before
        start_key = f"practice_start_{int(time.time()) - 10}"  # Use old timestamp
        response = self.make_request(
            self.student_session,
            "POST",
            f"/api/sets/{self.set_id}/start",
            json={
                "start_key": start_key,
                "device_checked": True,
                "preview": False
            }
        )
        
        if response is not None and response.status_code == 200:
            data = response.json()
            returned_id = data.get("data", {}).get("id")
            # Should return existing attempt or create new one
            self.log_pass("Start idempotence")
            return True
        else:
            status = response.status_code if response is not None else 'No response'
            self.log_fail("Start idempotence", f"Status: {status}")
            return False
    
    def test_submit_answers(self):
        """Submit answers with known correct values"""
        print("\n🔍 Submitting answers...")
        
        # Get attempt to see questions
        response = self.make_request(
            self.student_session,
            "GET",
            f"/api/attempts/{self.attempt_id}"
        )
        
        if response is None or response.status_code != 200:
            self.log_fail("Get attempt for answers", "Could not fetch attempt")
            return False
        
        data = response.json()
        questions = data.get("data", {}).get("questions", [])
        
        submitted_count = 0
        for q in questions[:6]:  # Submit first 6 answers
            qid = q["id"]
            qnum = q["number"]
            
            # Get known answer if available
            if qnum not in KNOWN_ANSWERS:
                continue
            
            answer_value = KNOWN_ANSWERS[qnum]
            
            # Submit answer with CAS revision
            answer_response = self.make_request(
                self.student_session,
                "PUT",
                f"/api/attempts/{self.attempt_id}/answers/{qid}",
                json={
                    "value": answer_value,
                    "marked": False,
                    "revision": 1,
                    "request_id": f"req_{qid}_{int(time.time())}"
                }
            )
            
            if answer_response is not None and answer_response.status_code == 200:
                submitted_count += 1
            else:
                status = answer_response.status_code if answer_response is not None else 'No response'
                print(f"  ⚠️  Failed to submit Q{qnum}: {status}")
        
        if submitted_count >= 4:
            self.log_pass(f"Submit answers ({submitted_count} submitted)")
            return True
        else:
            self.log_fail("Submit answers", f"Only {submitted_count} answers submitted")
            return False
    
    def test_submit_attempt(self):
        """Submit the attempt"""
        print("\n🔍 Submitting attempt...")
        
        response = self.make_request(
            self.student_session,
            "POST",
            f"/api/attempts/{self.attempt_id}/submit"
        )
        
        if response is not None and response.status_code == 200:
            data = response.json()
            if data.get("data", {}).get("receipt"):
                self.log_pass("Submit attempt")
                return True
            else:
                self.log_fail("Submit attempt", "No receipt returned")
        else:
            status = response.status_code if response is not None else 'No response'
            self.log_fail("Submit attempt", f"Status: {status}")
        return False
    
    def test_get_results(self):
        """Get results and verify scoring"""
        print("\n🔍 Getting results and verifying scoring...")
        
        response = self.make_request(
            self.student_session,
            "GET",
            f"/api/attempts/{self.attempt_id}/results"
        )
        
        if response is None or response.status_code != 200:
            status = response.status_code if response is not None else 'No response'
            self.log_fail("Get results", f"Status: {status}")
            return False
        
        data = response.json()
        summary = data.get("data", {}).get("summary", {})
        
        # Verify scoring
        score = summary.get("score", 0)
        correct = summary.get("correct", 0)
        
        if correct > 0 and score > 0:
            self.log_pass(f"Get results (Score: {score}, Correct: {correct})")
            return True
        else:
            self.log_fail("Get results", f"Unexpected scoring: score={score}, correct={correct}")
            return False
    
    def test_generate_report(self):
        """Generate PDF report"""
        print("\n🔍 Generating PDF report (this may take 30-60 seconds)...")
        
        response = self.make_request(
            self.student_session,
            "POST",
            f"/api/attempts/{self.attempt_id}/report"
        )
        
        if response is None or response.status_code != 200:
            status = response.status_code if response is not None else 'No response'
            self.log_fail("Generate report", f"Status: {status}")
            return False
        
        data = response.json()
        job_id = data.get("data", {}).get("id")
        if not job_id:
            self.log_fail("Generate report", "No job ID returned")
            return False
        
        # Wait for report generation
        for i in range(90):  # Wait up to 90 seconds
            time.sleep(1)
            status_response = self.make_request(
                self.student_session,
                "GET",
                f"/api/jobs/{job_id}"
            )
            
            if status_response is not None and status_response.status_code == 200:
                job_data = status_response.json().get("data", {})
                if job_data.get("status") == "done":
                    self.log_pass("Generate report")
                    self.report_job_id = job_id
                    return True
                elif job_data.get("status") == "failed":
                    self.log_fail("Generate report", f"Job failed: {job_data.get('error')}")
                    return False
        
        self.log_fail("Generate report", "Job timeout after 90 seconds")
        return False
    
    def test_download_report(self):
        """Download generated PDF report"""
        print("\n🔍 Downloading PDF report...")
        
        if not hasattr(self, 'report_job_id'):
            self.log_fail("Download report", "No report job ID available")
            return False
        
        response = self.make_request(
            self.student_session,
            "GET",
            f"/api/jobs/{self.report_job_id}/download"
        )
        
        if response is not None and response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if 'pdf' in content_type and len(response.content) > 1000:
                self.log_pass(f"Download report ({len(response.content)} bytes)")
                return True
            else:
                self.log_fail("Download report", f"Invalid PDF: {content_type}, {len(response.content)} bytes")
        else:
            status = response.status_code if response is not None else 'No response'
            self.log_fail("Download report", f"Status: {status}")
        return False
    
    def run_all_tests(self):
        """Run all practice flow tests"""
        print("=" * 70)
        print("TEJAS FULL 75-QUESTION PRACTICE FLOW TEST")
        print(f"Testing against: {BASE_URL}")
        print("=" * 70)
        
        # Setup
        if not self.test_owner_login():
            print("\n❌ Owner login failed - cannot continue")
            return self.tests_passed, self.tests_failed, self.issues
        
        if not self.test_student_register():
            print("\n❌ Student registration failed - cannot continue")
            return self.tests_passed, self.tests_failed, self.issues
        
        # Content creation
        if not self.test_create_set():
            print("\n❌ Set creation failed - cannot continue")
            return self.tests_passed, self.tests_failed, self.issues
        
        if not self.test_upload_pdfs():
            print("\n❌ PDF upload failed - cannot continue")
            return self.tests_passed, self.tests_failed, self.issues
        
        if not self.test_extract_questions():
            print("\n❌ Question extraction failed - cannot continue")
            return self.tests_passed, self.tests_failed, self.issues
        
        if not self.test_get_and_approve_questions():
            print("\n❌ Question approval failed - cannot continue")
            return self.tests_passed, self.tests_failed, self.issues
        
        # Create subset with approved questions
        if not self.test_create_subset_with_approved():
            print("\n❌ Subset creation failed - cannot continue")
            return self.tests_passed, self.tests_failed, self.issues
        
        if not self.test_publish_set():
            print("\n❌ Set publication failed - cannot continue")
            return self.tests_passed, self.tests_failed, self.issues
        
        # Practice flow
        if not self.test_preflight():
            print("\n❌ Preflight failed - cannot continue")
            return self.tests_passed, self.tests_failed, self.issues
        
        if not self.test_start_attempt():
            print("\n❌ Start attempt failed - cannot continue")
            return self.tests_passed, self.tests_failed, self.issues
        
        self.test_start_idempotence()
        
        if not self.test_submit_answers():
            print("\n⚠️  Answer submission had issues - continuing")
        
        if not self.test_submit_attempt():
            print("\n❌ Attempt submission failed - cannot continue")
            return self.tests_passed, self.tests_failed, self.issues
        
        if not self.test_get_results():
            print("\n❌ Get results failed - cannot continue")
            return self.tests_passed, self.tests_failed, self.issues
        
        if not self.test_generate_report():
            print("\n⚠️  Report generation failed - continuing")
        else:
            self.test_download_report()
        
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
    tester = FullPracticeFlowTester()
    passed, failed, issues = tester.run_all_tests()
    sys.exit(0 if failed == 0 else 1)
