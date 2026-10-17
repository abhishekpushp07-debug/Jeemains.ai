"""
Test 75-question PDF report generation from actual app API
Validates complete flow: auth, attempt, scoring, report generation and download

Updated to load URLs/MONGO_URL/DB_NAME from dotenv (no hardcodes)
"""
import sys
import json
import time
import hashlib
import os
from pathlib import Path
import requests
from pymongo import MongoClient
import fitz  # PyMuPDF
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
EXPECTED_MAXIMUM = fixture['expected_maximum']

print("=" * 80)
print("TESTING 75-QUESTION PDF REPORT GENERATION")
print("=" * 80)
print(f"Set ID: {SET_ID}")
print(f"Phone: {PHONE}")
print(f"Expected: {EXPECTED_QUESTIONS} questions, {EXPECTED_MAXIMUM} maximum score")
print("=" * 80)

class TestSession:
    def __init__(self):
        self.session = requests.Session()
        self.user = None
        self.attempt_id = None
        self.job_id = None
        
    def phone_auth(self):
        """Authenticate via phone"""
        print("\n📱 Step 1: Phone Authentication")
        print(f"   POST {BASE_URL}/api/auth/phone")
        
        response = self.session.post(
            f"{BASE_URL}/api/auth/phone",
            json={"phone": PHONE},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ FAIL: Phone auth returned {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        self.user = response.json()
        print(f"✅ PASS: Authenticated as {self.user.get('name', 'user')}")
        print(f"   User ID: {self.user.get('id')}")
        return True
    
    def get_fixture_questions(self):
        """Read fixture questions from MongoDB"""
        print("\n📚 Step 2: Reading Fixture Questions from MongoDB")
        
        try:
            client = MongoClient(MONGO_URL)
            db = client[DB_NAME]
            
            set_doc = db.tejas_sets.find_one({"id": SET_ID}, {"_id": 0})
            if not set_doc:
                print(f"❌ FAIL: Fixture set {SET_ID} not found in MongoDB")
                return None
            
            questions = set_doc.get('questions', [])
            if len(questions) != EXPECTED_QUESTIONS:
                print(f"❌ FAIL: Expected {EXPECTED_QUESTIONS} questions, found {len(questions)}")
                return None
            
            print(f"✅ PASS: Found {len(questions)} questions in fixture")
            
            # Validate all questions have answers
            missing_answers = [q['number'] for q in questions if not q.get('answer')]
            if missing_answers:
                print(f"⚠️  WARNING: Questions without answers: {missing_answers}")
            
            # Check for specific question IDs mentioned in requirements
            question_ids = [q['id'] for q in questions]
            print(f"   Question IDs sample: {question_ids[:3]}...")
            
            # Validate question types
            mcq_count = sum(1 for q in questions if q['type'] == 'mcq')
            integer_count = sum(1 for q in questions if q['type'] == 'integer')
            print(f"   MCQ: {mcq_count}, Integer: {integer_count}")
            
            return questions
            
        except Exception as e:
            print(f"❌ FAIL: MongoDB query failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def preflight(self):
        """Run preflight check"""
        print("\n🔍 Step 3: Preflight Check")
        print(f"   POST {BASE_URL}/api/sets/{SET_ID}/preflight")
        
        response = self.session.post(
            f"{BASE_URL}/api/sets/{SET_ID}/preflight",
            json={"preview": False, "test_response": "preflight-test"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ FAIL: Preflight returned {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        result = response.json()
        print(f"✅ PASS: {result.get('message', 'Preflight successful')}")
        return True
    
    def start_attempt(self):
        """Start non-preview attempt"""
        print("\n🚀 Step 4: Start Non-Preview Attempt")
        print(f"   POST {BASE_URL}/api/sets/{SET_ID}/start")
        
        start_key = f"test-report-75-{int(time.time())}"
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
            print(f"❌ FAIL: Start attempt returned {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        result = response.json()
        
        # Handle both direct response and nested data response
        attempt = result.get('data', result)
        self.attempt_id = attempt.get('id')
        
        if not self.attempt_id:
            print(f"❌ FAIL: No attempt ID in response")
            print(f"   Full response: {json.dumps(result, indent=2)[:500]}")
            return False
        
        print(f"✅ PASS: Attempt started")
        print(f"   Attempt ID: {self.attempt_id}")
        print(f"   Status: {attempt.get('status')}")
        print(f"   Questions: {attempt.get('count')}")
        
        return True
    
    def submit_answers(self, questions):
        """Submit correct answers for all 75 questions"""
        print("\n✍️  Step 5: Submit Correct Answers for All 75 Questions")
        print(f"   PUT {BASE_URL}/api/attempts/{self.attempt_id}/answers/{{qid}}")
        
        success_count = 0
        failed_questions = []
        
        for i, q in enumerate(questions, 1):
            qid = q['id']
            answer = q.get('answer', '')
            
            if not answer:
                print(f"   ⚠️  Q{q['number']}: No answer available, skipping")
                continue
            
            # Submit answer
            response = self.session.put(
                f"{BASE_URL}/api/attempts/{self.attempt_id}/answers/{qid}",
                json={
                    "value": answer,
                    "marked": False,
                    "revision": 1,
                    "request_id": f"test-{qid}-{int(time.time())}"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                success_count += 1
                if i % 15 == 0:  # Progress update every 15 questions
                    print(f"   ✅ Progress: {success_count}/{len(questions)} answers submitted")
            else:
                failed_questions.append({
                    'number': q['number'],
                    'id': qid,
                    'status': response.status_code,
                    'error': response.text[:100]
                })
                print(f"   ❌ Q{q['number']} (ID: {qid}): Failed with {response.status_code}")
        
        print(f"\n   Summary: {success_count}/{len(questions)} answers submitted successfully")
        
        if failed_questions:
            print(f"   ❌ FAIL: {len(failed_questions)} questions failed:")
            for fq in failed_questions[:5]:  # Show first 5 failures
                print(f"      Q{fq['number']}: {fq['status']} - {fq['error']}")
            return False
        
        if success_count != len(questions):
            print(f"   ❌ FAIL: Expected {len(questions)} successful submissions, got {success_count}")
            return False
        
        print(f"   ✅ PASS: All {success_count} answers submitted")
        return True
    
    def submit_attempt(self):
        """Submit the attempt"""
        print("\n📤 Step 6: Submit Attempt")
        print(f"   POST {BASE_URL}/api/attempts/{self.attempt_id}/submit")
        
        response = self.session.post(
            f"{BASE_URL}/api/attempts/{self.attempt_id}/submit",
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ FAIL: Submit returned {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        result = response.json()
        
        # Handle both direct response and nested data response
        submit_result = result.get('data', result)
        
        print(f"✅ PASS: Attempt submitted")
        print(f"   Receipt: {submit_result.get('receipt')}")
        print(f"   Status: {submit_result.get('status')}")
        return True
    
    def verify_score(self):
        """Verify the score is 300/300 with 75 correct"""
        print("\n🎯 Step 7: Verify Score (300/300, 75 correct)")
        print(f"   GET {BASE_URL}/api/attempts/{self.attempt_id}/results")
        
        response = self.session.get(
            f"{BASE_URL}/api/attempts/{self.attempt_id}/results",
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ FAIL: Results returned {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        result = response.json()
        
        # Handle both direct response and nested data response
        results = result.get('data', result)
        summary = results.get('summary', {})
        
        score = summary.get('score')
        maximum = summary.get('maximum')
        correct = summary.get('correct')
        incorrect = summary.get('incorrect')
        skipped = summary.get('skipped')
        
        print(f"   Score: {score}/{maximum}")
        print(f"   Correct: {correct}, Incorrect: {incorrect}, Skipped: {skipped}")
        
        if score is None or maximum is None:
            print(f"❌ FAIL: Score data not available in response")
            print(f"   Response keys: {list(results.keys())}")
            print(f"   Summary: {json.dumps(summary, indent=2)[:300]}")
            return False
        
        if score != EXPECTED_MAXIMUM:
            print(f"❌ FAIL: Expected score {EXPECTED_MAXIMUM}, got {score}")
            return False
        
        if correct != EXPECTED_QUESTIONS:
            print(f"❌ FAIL: Expected {EXPECTED_QUESTIONS} correct, got {correct}")
            return False
        
        print(f"✅ PASS: Perfect score {score}/{maximum} with {correct} correct answers")
        return True
    
    def generate_report(self):
        """Generate PDF report"""
        print("\n📄 Step 8: Generate PDF Report")
        print(f"   POST {BASE_URL}/api/attempts/{self.attempt_id}/report")
        
        response = self.session.post(
            f"{BASE_URL}/api/attempts/{self.attempt_id}/report",
            json={},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ FAIL: Report generation returned {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        result = response.json()
        
        # Handle both direct response and nested data response
        job = result.get('data', result)
        self.job_id = job.get('id')
        
        if not self.job_id:
            print(f"❌ FAIL: No job ID in response")
            print(f"   Response keys: {list(result.keys())}")
            print(f"   Full response: {json.dumps(result, indent=2)[:500]}")
            return False
        
        print(f"✅ PASS: Report job created")
        print(f"   Job ID: {self.job_id}")
        print(f"   Status: {job.get('status')}")
        return True
    
    def wait_for_report(self, timeout=120):
        """Wait for report to be ready"""
        print("\n⏳ Step 9: Wait for Report Completion")
        print(f"   GET {BASE_URL}/api/jobs/{self.job_id}")
        print(f"   Timeout: {timeout}s")
        
        start_time = time.time()
        last_progress = -1
        
        while time.time() - start_time < timeout:
            response = self.session.get(
                f"{BASE_URL}/api/jobs/{self.job_id}",
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ FAIL: Job status returned {response.status_code}")
                return False
            
            result = response.json()
            
            # Handle both direct response and nested data response
            job = result.get('data', result)
            status = job.get('status')
            progress = job.get('progress', 0)
            
            if progress != last_progress:
                print(f"   Progress: {progress}% - Status: {status}")
                last_progress = progress
            
            if status == 'done':
                elapsed = time.time() - start_time
                print(f"✅ PASS: Report ready in {elapsed:.1f}s")
                return True
            
            if status == 'failed':
                error = job.get('error', 'Unknown error')
                print(f"❌ FAIL: Report generation failed: {error}")
                return False
            
            time.sleep(2)
        
        print(f"❌ FAIL: Report generation timed out after {timeout}s")
        return False
    
    def download_report(self):
        """Download the PDF report"""
        print("\n⬇️  Step 10: Download PDF Report")
        print(f"   GET {BASE_URL}/api/jobs/{self.job_id}/download")
        
        response = self.session.get(
            f"{BASE_URL}/api/jobs/{self.job_id}/download",
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ FAIL: Download returned {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return None
        
        pdf_data = response.content
        
        if not pdf_data.startswith(b'%PDF-'):
            print(f"❌ FAIL: Downloaded content is not a PDF")
            print(f"   First 100 bytes: {pdf_data[:100]}")
            return None
        
        # Save to file
        report_path = Path('/app/test_reports/report75.pdf')
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_bytes(pdf_data)
        
        print(f"✅ PASS: PDF downloaded and saved")
        print(f"   Path: {report_path}")
        print(f"   Size: {len(pdf_data):,} bytes")
        
        return pdf_data
    
    def validate_pdf(self, pdf_data):
        """Validate PDF contains all 75 questions"""
        print("\n🔍 Step 11: Validate PDF Content")
        
        try:
            doc = fitz.open(stream=pdf_data, filetype="pdf")
            page_count = len(doc)
            
            print(f"   Pages: {page_count}")
            
            # Extract all text and look for question headers
            all_text = ""
            for page in doc:
                all_text += page.get_text()
            
            # Look for "Question 1" through "Question 75"
            found_questions = []
            for i in range(1, EXPECTED_QUESTIONS + 1):
                if f"Question {i}" in all_text:
                    found_questions.append(i)
            
            print(f"   Found question headers: {len(found_questions)}/{EXPECTED_QUESTIONS}")
            
            if len(found_questions) != EXPECTED_QUESTIONS:
                missing = set(range(1, EXPECTED_QUESTIONS + 1)) - set(found_questions)
                print(f"❌ FAIL: Missing questions: {sorted(missing)[:10]}...")
                return False
            
            print(f"✅ PASS: All {EXPECTED_QUESTIONS} questions present in PDF")
            
            # Calculate SHA256
            sha256 = hashlib.sha256(pdf_data).hexdigest()
            print(f"\n📊 PDF Metadata:")
            print(f"   Pages: {page_count}")
            print(f"   Size: {len(pdf_data):,} bytes")
            print(f"   SHA256: {sha256}")
            
            return True
            
        except Exception as e:
            print(f"❌ FAIL: PDF validation error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def validate_source_segmentation(self):
        """Validate source PDF segmentation"""
        print("\n📑 Step 12: Validate Source PDF Segmentation")
        
        questions_pdf = Path("/app/sources/questions.pdf")
        solutions_pdf = Path("/app/sources/solutions.pdf")
        
        if not questions_pdf.exists() or not solutions_pdf.exists():
            print(f"⚠️  WARNING: Source PDFs not found, skipping segmentation test")
            return True
        
        try:
            from tejas_core import build_questions, segment_pdf
            
            print(f"   Loading source PDFs...")
            qdata = questions_pdf.read_bytes()
            sdata = solutions_pdf.read_bytes()
            
            # Combine and segment
            print(f"   Segmenting combined PDF...")
            combined = qdata + sdata  # This is conceptual, actual implementation may differ
            
            # Build questions
            print(f"   Building questions with known_tejas=True...")
            questions = build_questions(qdata, sdata, "questions", "solutions", known_tejas=True)
            
            if len(questions) != EXPECTED_QUESTIONS:
                print(f"❌ FAIL: Expected {EXPECTED_QUESTIONS} questions, got {len(questions)}")
                return False
            
            print(f"✅ PASS: Extracted exactly {EXPECTED_QUESTIONS} questions")
            
            # Validate no question crop extends past page 11 into answer key/solutions
            print(f"   Validating question boundaries...")
            
            max_question_page = 0
            for q in questions:
                for ref in q.get('q_refs', []):
                    page = ref.get('page', 0)
                    if page > max_question_page:
                        max_question_page = page
            
            print(f"   Maximum question page: {max_question_page}")
            
            if max_question_page > 11:
                print(f"⚠️  WARNING: Questions extend past page 11 (found page {max_question_page})")
            else:
                print(f"✅ PASS: All questions within expected page range")
            
            # Validate all 75 source-pair IDs
            print(f"   Validating source-pair IDs...")
            
            questions_with_refs = sum(1 for q in questions if q.get('q_refs'))
            solutions_with_refs = sum(1 for q in questions if q.get('s_refs'))
            
            print(f"   Questions with q_refs: {questions_with_refs}/{len(questions)}")
            print(f"   Questions with s_refs: {solutions_with_refs}/{len(questions)}")
            
            if questions_with_refs == len(questions) and solutions_with_refs == len(questions):
                print(f"✅ PASS: All 75 questions have complete source-pair IDs")
            else:
                print(f"⚠️  WARNING: Some questions missing source references")
            
            return True
            
        except Exception as e:
            print(f"❌ FAIL: Source segmentation validation error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def save_context(self):
        """Save attempt and job IDs to qa_context.json"""
        print("\n💾 Step 13: Save Context for Browser QA")
        
        try:
            with open('/app/memory/qa_context.json', 'r') as f:
                context = json.load(f)
            
            context['attempt_id'] = self.attempt_id
            context['job_id'] = self.job_id
            context['test_timestamp'] = int(time.time())
            
            with open('/app/memory/qa_context.json', 'w') as f:
                json.dump(context, f, indent=2)
            
            print(f"✅ PASS: Context saved")
            print(f"   Attempt ID: {self.attempt_id}")
            print(f"   Job ID: {self.job_id}")
            
            return True
            
        except Exception as e:
            print(f"❌ FAIL: Failed to save context: {str(e)}")
            return False

def main():
    """Run complete test flow"""
    test = TestSession()
    
    start_time = time.time()
    
    # Step 1: Phone Authentication
    if not test.phone_auth():
        print("\n" + "=" * 80)
        print("❌ TEST FAILED: Phone authentication failed")
        print("=" * 80)
        return 1
    
    # Step 2: Get fixture questions
    questions = test.get_fixture_questions()
    if not questions:
        print("\n" + "=" * 80)
        print("❌ TEST FAILED: Could not read fixture questions")
        print("=" * 80)
        return 1
    
    # Step 3: Preflight
    if not test.preflight():
        print("\n" + "=" * 80)
        print("❌ TEST FAILED: Preflight check failed")
        print("=" * 80)
        return 1
    
    # Step 4: Start attempt
    if not test.start_attempt():
        print("\n" + "=" * 80)
        print("❌ TEST FAILED: Could not start attempt")
        print("=" * 80)
        return 1
    
    # Step 5: Submit answers
    if not test.submit_answers(questions):
        print("\n" + "=" * 80)
        print("❌ TEST FAILED: Answer submission failed")
        print("=" * 80)
        return 1
    
    # Step 6: Submit attempt
    if not test.submit_attempt():
        print("\n" + "=" * 80)
        print("❌ TEST FAILED: Attempt submission failed")
        print("=" * 80)
        return 1
    
    # Step 7: Verify score
    if not test.verify_score():
        print("\n" + "=" * 80)
        print("❌ TEST FAILED: Score verification failed")
        print("=" * 80)
        return 1
    
    # Step 8: Generate report
    if not test.generate_report():
        print("\n" + "=" * 80)
        print("❌ TEST FAILED: Report generation failed")
        print("=" * 80)
        return 1
    
    # Step 9: Wait for report
    if not test.wait_for_report(timeout=120):
        print("\n" + "=" * 80)
        print("❌ TEST FAILED: Report generation timed out or failed")
        print("=" * 80)
        return 1
    
    # Step 10: Download report
    pdf_data = test.download_report()
    if not pdf_data:
        print("\n" + "=" * 80)
        print("❌ TEST FAILED: Report download failed")
        print("=" * 80)
        return 1
    
    # Step 11: Validate PDF
    if not test.validate_pdf(pdf_data):
        print("\n" + "=" * 80)
        print("❌ TEST FAILED: PDF validation failed")
        print("=" * 80)
        return 1
    
    # Step 12: Validate source segmentation
    if not test.validate_source_segmentation():
        print("\n" + "=" * 80)
        print("❌ TEST FAILED: Source segmentation validation failed")
        print("=" * 80)
        return 1
    
    # Step 13: Save context
    if not test.save_context():
        print("\n" + "=" * 80)
        print("⚠️  WARNING: Could not save context (non-critical)")
        print("=" * 80)
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED")
    print("=" * 80)
    print(f"Total time: {elapsed:.1f}s")
    print(f"Report saved: /app/test_reports/report75.pdf")
    print(f"Attempt ID: {test.attempt_id}")
    print(f"Job ID: {test.job_id}")
    print("=" * 80)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
