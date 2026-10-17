"""
PHASE 1A CORE ISOLATION TEST
Tests tejas_core.py and tejas_storage.py with actual source PDFs.
Load .env before module imports; do not log key.
"""
import os
import sys
from pathlib import Path

# Load .env BEFORE any module imports
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Verify key is loaded (without logging it)
if not os.environ.get('EMERGENT_LLM_KEY'):
    print("❌ CRITICAL: EMERGENT_LLM_KEY not found in environment")
    sys.exit(1)

# Now import modules
import tejas_core
import tejas_storage
import time

class CoreTester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.issues = []
        self.questions = None
        self.q_path = None
        self.s_path = None
        
    def log_pass(self, test_name):
        self.tests_run += 1
        self.tests_passed += 1
        print(f"✅ {test_name}")
        
    def log_fail(self, test_name, reason):
        self.tests_run += 1
        self.issues.append(f"{test_name}: {reason}")
        print(f"❌ {test_name}: {reason}")
        
    def test_storage_roundtrip(self):
        """Test object storage put/get with actual PDFs"""
        print("\n🔍 Testing storage roundtrip with actual PDFs...")
        
        try:
            # Load actual source PDFs
            q_data = open('/app/sources/questions.pdf', 'rb').read()
            s_data = open('/app/sources/solutions.pdf', 'rb').read()
            
            if len(q_data) == 0 or len(s_data) == 0:
                self.log_fail("Storage roundtrip", "Source PDFs are empty")
                return False
                
            print(f"  Loaded questions.pdf: {len(q_data)} bytes")
            print(f"  Loaded solutions.pdf: {len(s_data)} bytes")
            
            # Put objects
            print("  Uploading to private storage...")
            self.q_path = tejas_storage.put_object('test/questions.pdf', q_data, 'application/pdf')
            self.s_path = tejas_storage.put_object('test/solutions.pdf', s_data, 'application/pdf')
            
            print(f"  Questions stored at: {self.q_path}")
            print(f"  Solutions stored at: {self.s_path}")
            
            # Get objects back
            print("  Retrieving from private storage...")
            q_retrieved = tejas_storage.get_object(self.q_path)
            s_retrieved = tejas_storage.get_object(self.s_path)
            
            # Verify roundtrip
            if q_retrieved == q_data and s_retrieved == s_data:
                self.log_pass("Storage roundtrip (put/get)")
                return True
            else:
                self.log_fail("Storage roundtrip", "Retrieved data doesn't match original")
                return False
                
        except Exception as e:
            self.log_fail("Storage roundtrip", str(e))
            return False
            
    def test_build_questions(self):
        """Test build_questions on actual 75 question PDF"""
        print("\n🔍 Testing build_questions with actual PDFs...")
        
        try:
            q_data = open('/app/sources/questions.pdf', 'rb').read()
            s_data = open('/app/sources/solutions.pdf', 'rb').read()
            
            print("  Building questions with known_tejas=True...")
            self.questions = tejas_core.build_questions(
                q_data, s_data, 
                qfile='questions', 
                sfile='solutions', 
                known_tejas=True
            )
            
            print(f"  Built {len(self.questions)} questions")
            
            # Test 1: Exactly 75 unique questions Q1-Q75
            numbers = [q['number'] for q in self.questions]
            unique_numbers = set(numbers)
            
            if len(self.questions) != 75:
                self.log_fail("Question count", f"Expected 75, got {len(self.questions)}")
            elif len(unique_numbers) != 75:
                self.log_fail("Unique questions", f"Expected 75 unique, got {len(unique_numbers)}")
            elif unique_numbers != set(range(1, 76)):
                missing = set(range(1, 76)) - unique_numbers
                extra = unique_numbers - set(range(1, 76))
                self.log_fail("Question numbers", f"Missing: {missing}, Extra: {extra}")
            else:
                self.log_pass("Exactly Q1-Q75 unique questions")
                
            # Test 2: 60 MCQ and 15 integer
            mcq_count = sum(1 for q in self.questions if q['type'] == 'mcq')
            integer_count = sum(1 for q in self.questions if q['type'] == 'integer')
            
            if mcq_count == 60 and integer_count == 15:
                self.log_pass("60 MCQ and 15 integer questions")
            else:
                self.log_fail("Question types", f"Expected 60 MCQ + 15 integer, got {mcq_count} MCQ + {integer_count} integer")
                
            # Test 3: 25 questions per subject
            subjects = {}
            for q in self.questions:
                subj = q.get('subject', 'Unknown')
                subjects[subj] = subjects.get(subj, 0) + 1
                
            print(f"  Subject distribution: {subjects}")
            
            expected_subjects = {'Mathematics': 25, 'Physics': 25, 'Chemistry': 25}
            if subjects == expected_subjects:
                self.log_pass("25 questions per subject (Math, Physics, Chemistry)")
            else:
                self.log_fail("Subject distribution", f"Expected {expected_subjects}, got {subjects}")
                
            # Test 4: Correct answers Q22=13440, Q23=10385
            q22 = next((q for q in self.questions if q['number'] == 22), None)
            q23 = next((q for q in self.questions if q['number'] == 23), None)
            
            if q22 and q22['answer'] == '13440':
                self.log_pass("Q22 answer = 13440")
            else:
                actual = q22['answer'] if q22 else 'NOT FOUND'
                self.log_fail("Q22 answer", f"Expected 13440, got {actual}")
                
            if q23 and q23['answer'] == '10385':
                self.log_pass("Q23 answer = 10385")
            else:
                actual = q23['answer'] if q23 else 'NOT FOUND'
                self.log_fail("Q23 answer", f"Expected 10385, got {actual}")
                
            # Test 5: No key table duplicates (check for duplicate numbers)
            duplicates = [n for n in numbers if numbers.count(n) > 1]
            if len(set(duplicates)) == 0:
                self.log_pass("No duplicate question numbers")
            else:
                self.log_fail("Duplicate questions", f"Found duplicates: {set(duplicates)}")
                
            # Test 6: Solution matching by number
            unmatched = [q for q in self.questions if q['number'] != q.get('solution_number')]
            if len(unmatched) == 0:
                self.log_pass("All solutions matched by number")
            else:
                self.log_fail("Solution matching", f"{len(unmatched)} questions have mismatched solution numbers")
                
            # Test 7: Check for issues field
            questions_with_issues = [q for q in self.questions if q.get('issues')]
            if len(questions_with_issues) > 0:
                print(f"  ⚠️  {len(questions_with_issues)} questions have issues flagged")
                for q in questions_with_issues[:3]:  # Show first 3
                    print(f"      Q{q['number']}: {q['issues']}")
                    
            return True
            
        except Exception as e:
            self.log_fail("build_questions", str(e))
            import traceback
            traceback.print_exc()
            return False
            
    def test_crop_fidelity(self):
        """Test crop fidelity for specific questions"""
        print("\n🔍 Testing crop fidelity for Q7, Q8, Q22, Q23, Q27, Q31, Q41, Q52, Q56, Q67...")
        
        if not self.questions:
            self.log_fail("Crop fidelity", "Questions not built yet")
            return False
            
        try:
            q_data = open('/app/sources/questions.pdf', 'rb').read()
            s_data = open('/app/sources/solutions.pdf', 'rb').read()
            
            test_questions = [7, 8, 22, 23, 27, 31, 41, 52, 56, 67]
            
            for qnum in test_questions:
                q = next((q for q in self.questions if q['number'] == qnum), None)
                if not q:
                    self.log_fail(f"Crop Q{qnum}", "Question not found")
                    continue
                    
                # Test question crop
                if q.get('q_refs'):
                    try:
                        for ref in q['q_refs']:
                            png_data = tejas_core.crop_png(q_data, ref, scale=2)
                            if len(png_data) > 0:
                                pass  # Crop successful
                            else:
                                self.log_fail(f"Crop Q{qnum} question", "Empty PNG data")
                                break
                        else:
                            self.log_pass(f"Crop Q{qnum} question refs")
                    except Exception as e:
                        self.log_fail(f"Crop Q{qnum} question", str(e))
                else:
                    self.log_fail(f"Crop Q{qnum}", "No q_refs found")
                    
                # Test solution crop
                if q.get('s_refs'):
                    try:
                        for ref in q['s_refs']:
                            png_data = tejas_core.crop_png(s_data, ref, scale=2)
                            if len(png_data) > 0:
                                pass  # Crop successful
                            else:
                                self.log_fail(f"Crop Q{qnum} solution", "Empty PNG data")
                                break
                        else:
                            self.log_pass(f"Crop Q{qnum} solution refs")
                    except Exception as e:
                        self.log_fail(f"Crop Q{qnum} solution", str(e))
                        
            return True
            
        except Exception as e:
            self.log_fail("Crop fidelity", str(e))
            return False
            
    def test_score_attempt(self):
        """Test score_attempt with various scenarios"""
        print("\n🔍 Testing score_attempt with various scenarios...")
        
        if not self.questions:
            self.log_fail("score_attempt", "Questions not built yet")
            return False
            
        try:
            # Scenario 1: All correct
            attempt1 = {
                'id': 'test-all-correct',
                'title': 'Test All Correct',
                'exam': 'JEE Main',
                'started_at': time.time(),
                'submitted_at': time.time() + 100,
                'rules': {'correct': 4, 'wrong': -1, 'skipped': 0, 'numeric_rule': 'Exact integer'},
                'questions': self.questions,
                'answers': {q['id']: {'value': q['answer']} for q in self.questions}
            }
            
            result1 = tejas_core.score_attempt(attempt1)
            if result1['summary']['score'] == 300 and result1['summary']['correct'] == 75:
                self.log_pass("score_attempt: all correct = 300")
            else:
                self.log_fail("score_attempt all correct", 
                             f"Expected 300 score, 75 correct; got {result1['summary']['score']} score, {result1['summary']['correct']} correct")
                
            # Scenario 2: All skipped
            attempt2 = {
                'id': 'test-all-skipped',
                'title': 'Test All Skipped',
                'exam': 'JEE Main',
                'started_at': time.time(),
                'rules': {'correct': 4, 'wrong': -1, 'skipped': 0, 'numeric_rule': 'Exact integer'},
                'questions': self.questions,
                'answers': {}
            }
            
            result2 = tejas_core.score_attempt(attempt2)
            if result2['summary']['score'] == 0 and result2['summary']['skipped'] == 75:
                self.log_pass("score_attempt: all skipped = 0")
            else:
                self.log_fail("score_attempt all skipped",
                             f"Expected 0 score, 75 skipped; got {result2['summary']['score']} score, {result2['summary']['skipped']} skipped")
                
            # Check accuracy is null for skipped
            if result2['summary']['accuracy'] is None:
                self.log_pass("score_attempt: skipped accuracy = null")
            else:
                self.log_fail("score_attempt skipped accuracy",
                             f"Expected None, got {result2['summary']['accuracy']}")
                
            # Scenario 3: Mixed correct/incorrect/skipped
            mixed_answers = {}
            for i, q in enumerate(self.questions):
                if i < 25:  # First 25 correct
                    mixed_answers[q['id']] = {'value': q['answer']}
                elif i < 50:  # Next 25 wrong
                    mixed_answers[q['id']] = {'value': '9999'}
                # Last 25 skipped
                
            attempt3 = {
                'id': 'test-mixed',
                'title': 'Test Mixed',
                'exam': 'JEE Main',
                'started_at': time.time(),
                'rules': {'correct': 4, 'wrong': -1, 'skipped': 0, 'numeric_rule': 'Exact integer'},
                'questions': self.questions,
                'answers': mixed_answers
            }
            
            result3 = tejas_core.score_attempt(attempt3)
            expected_score = 25 * 4 + 25 * (-1)  # 100 - 25 = 75
            if result3['summary']['score'] == expected_score:
                self.log_pass(f"score_attempt: mixed = {expected_score} (25 correct, 25 wrong, 25 skipped)")
            else:
                self.log_fail("score_attempt mixed",
                             f"Expected {expected_score}, got {result3['summary']['score']}")
                
            # Check penalties
            if result3['summary']['penalties'] == 25:
                self.log_pass("score_attempt: penalties calculated correctly")
            else:
                self.log_fail("score_attempt penalties",
                             f"Expected 25, got {result3['summary']['penalties']}")
                
            # Scenario 4: Test normalized integer input (leading zeros, signs)
            q_integer = next((q for q in self.questions if q['type'] == 'integer'), None)
            if q_integer:
                test_values = [
                    (q_integer['answer'], True),  # Exact match
                    ('+' + q_integer['answer'], True),  # With plus sign
                    ('0' + q_integer['answer'], True),  # Leading zero
                    (str(int(q_integer['answer']) + 1), False),  # Wrong answer
                ]
                
                for value, should_be_correct in test_values:
                    attempt_test = {
                        'id': 'test-normalize',
                        'title': 'Test Normalize',
                        'exam': 'JEE Main',
                        'started_at': time.time(),
                        'rules': {'correct': 4, 'wrong': -1, 'skipped': 0, 'numeric_rule': 'Exact integer'},
                        'questions': [q_integer],
                        'answers': {q_integer['id']: {'value': value}}
                    }
                    result = tejas_core.score_attempt(attempt_test)
                    is_correct = result['summary']['correct'] == 1
                    
                    if is_correct == should_be_correct:
                        pass  # Correct behavior
                    else:
                        self.log_fail("score_attempt normalize",
                                     f"Value '{value}' should be {'correct' if should_be_correct else 'incorrect'}, but got opposite")
                        break
                else:
                    self.log_pass("score_attempt: normalized integer input (signs, leading zeros)")
                    
            return True
            
        except Exception as e:
            self.log_fail("score_attempt", str(e))
            import traceback
            traceback.print_exc()
            return False
            
    def test_public_question(self):
        """Test that public_question never contains answer/solution"""
        print("\n🔍 Testing public_question never contains answer/solution...")
        
        if not self.questions:
            self.log_fail("public_question", "Questions not built yet")
            return False
            
        try:
            leaked = []
            for q in self.questions:
                pub = tejas_core.public_question(q)
                
                # Check that sensitive fields are not present
                if 'answer' in pub:
                    leaked.append(f"Q{q['number']}: contains 'answer'")
                if 'solution' in pub:
                    leaked.append(f"Q{q['number']}: contains 'solution'")
                if 's_refs' in pub:
                    leaked.append(f"Q{q['number']}: contains 's_refs'")
                    
            if len(leaked) == 0:
                self.log_pass("public_question: no answer/solution leakage")
            else:
                self.log_fail("public_question", f"Leaked data: {leaked[:5]}")
                
            # Verify expected fields are present
            sample_pub = tejas_core.public_question(self.questions[0])
            expected_fields = ['id', 'number', 'subject', 'section', 'type', 'text', 'options', 'topic', 'render_mode', 'accessible_text', 'q_refs']
            missing = [f for f in expected_fields if f not in sample_pub]
            
            if len(missing) == 0:
                self.log_pass("public_question: contains expected fields")
            else:
                self.log_fail("public_question fields", f"Missing fields: {missing}")
                
            return True
            
        except Exception as e:
            self.log_fail("public_question", str(e))
            return False
            
    def test_generate_report(self):
        """Test generate_report creates full 75 question report"""
        print("\n🔍 Testing generate_report with full 75 questions...")
        
        if not self.questions:
            self.log_fail("generate_report", "Questions not built yet")
            return False
            
        try:
            # Create a test attempt
            attempt = {
                'id': 'test-report',
                'title': 'Tejas 200 — Predicted Paper 01',
                'exam': 'JEE Main 2027 Practice',
                'version': 1,
                'started_at': time.time(),
                'submitted_at': time.time() + 10800,  # 3 hours
                'rules': {'correct': 4, 'wrong': -1, 'skipped': 0, 'numeric_rule': 'Exact integer value; signs and leading zeros accepted; up to 20 digits. No rounding.'},
                'questions': self.questions,
                'answers': {q['id']: {'value': q['answer']} for q in self.questions[:50]},  # Answer first 50
                'attribution': 'Tejas 200 — Owner-supplied practice content'
            }
            
            # File loader function
            def file_loader(file_id):
                if file_id == 'questions':
                    return open('/app/sources/questions.pdf', 'rb').read()
                elif file_id == 'solutions':
                    return open('/app/sources/solutions.pdf', 'rb').read()
                else:
                    raise ValueError(f"Unknown file_id: {file_id}")
                    
            print("  Generating PDF report...")
            pdf_data = tejas_core.generate_report(attempt, file_loader)
            
            if len(pdf_data) == 0:
                self.log_fail("generate_report", "Empty PDF data")
                return False
                
            print(f"  Generated PDF: {len(pdf_data)} bytes")
            
            # Save report for inspection
            report_path = '/app/test_reports/core-report.pdf'
            with open(report_path, 'wb') as f:
                f.write(pdf_data)
            print(f"  Saved report to: {report_path}")
            
            # Verify it's a valid PDF
            import fitz
            doc = fitz.open(stream=pdf_data, filetype='pdf')
            page_count = len(doc)
            print(f"  Report has {page_count} pages")
            
            if page_count < 75:  # Should have at least 75 pages (one per question minimum)
                self.log_fail("generate_report", f"Expected at least 75 pages, got {page_count}")
            else:
                self.log_pass(f"generate_report: created {page_count}-page PDF")
                
            # Check first page contains summary
            first_page_text = doc[0].get_text()
            if 'TEJAS / RESULTS & SOLUTIONS' in first_page_text:
                self.log_pass("generate_report: contains header")
            else:
                self.log_fail("generate_report", "Missing expected header")
                
            # Check that questions are present
            question_pages = [p for p in doc if 'Question' in p.get_text()]
            if len(question_pages) >= 75:
                self.log_pass("generate_report: contains all 75 questions")
            else:
                self.log_fail("generate_report", f"Expected 75 question pages, found {len(question_pages)}")
                
            doc.close()
            return True
            
        except Exception as e:
            self.log_fail("generate_report", str(e))
            import traceback
            traceback.print_exc()
            return False
            
    def test_validate_pdf(self):
        """Test validate_pdf rejects invalid inputs"""
        print("\n🔍 Testing validate_pdf rejects invalid/encrypted/oversized...")
        
        try:
            # Test 1: Valid PDF
            valid_data = open('/app/sources/questions.pdf', 'rb').read()
            try:
                doc = tejas_core.validate_pdf(valid_data)
                self.log_pass("validate_pdf: accepts valid PDF")
                doc.close()
            except Exception as e:
                self.log_fail("validate_pdf valid", str(e))
                
            # Test 2: Invalid PDF (not a PDF)
            try:
                tejas_core.validate_pdf(b'This is not a PDF file')
                self.log_fail("validate_pdf invalid", "Should reject non-PDF data")
            except ValueError as e:
                if 'valid PDF' in str(e):
                    self.log_pass("validate_pdf: rejects non-PDF data")
                else:
                    self.log_fail("validate_pdf invalid", f"Wrong error: {e}")
                    
            # Test 3: Oversized PDF (>50MB)
            try:
                huge_data = b'%PDF-1.4\n' + b'x' * (51 * 1024 * 1024)
                tejas_core.validate_pdf(huge_data)
                self.log_fail("validate_pdf oversized", "Should reject >50MB PDF")
            except ValueError as e:
                if '50 MB' in str(e):
                    self.log_pass("validate_pdf: rejects oversized PDF")
                else:
                    self.log_fail("validate_pdf oversized", f"Wrong error: {e}")
                    
            # Test 4: Empty data
            try:
                tejas_core.validate_pdf(b'')
                self.log_fail("validate_pdf empty", "Should reject empty data")
            except ValueError:
                self.log_pass("validate_pdf: rejects empty data")
                
            return True
            
        except Exception as e:
            self.log_fail("validate_pdf", str(e))
            return False
            
    def run_all_tests(self):
        """Run all core isolation tests"""
        print("=" * 70)
        print("PHASE 1A CORE ISOLATION TEST")
        print("Testing tejas_core.py and tejas_storage.py with actual source PDFs")
        print("=" * 70)
        
        # Run tests in order
        self.test_storage_roundtrip()
        self.test_build_questions()
        self.test_crop_fidelity()
        self.test_score_attempt()
        self.test_public_question()
        self.test_generate_report()
        self.test_validate_pdf()
        
        # Print summary
        print("\n" + "=" * 70)
        print(f"TESTS COMPLETED: {self.tests_passed}/{self.tests_run} passed")
        print("=" * 70)
        
        if len(self.issues) > 0:
            print("\n❌ ISSUES FOUND:")
            for issue in self.issues:
                print(f"  • {issue}")
        else:
            print("\n✅ ALL TESTS PASSED")
            
        return self.tests_passed == self.tests_run

if __name__ == '__main__':
    tester = CoreTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
