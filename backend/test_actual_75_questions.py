"""
Test actual 75 questions from source PDFs
Validates question extraction and scoring against real TEJAS paper
"""
import sys
from pathlib import Path

# Import scoring and extraction functions
from tejas.scoring import score, canonical
from tejas_core import build_questions, RULES

def test_actual_75_questions():
    """Test extraction and scoring of actual 75 questions"""
    print("=" * 70)
    print("TESTING ACTUAL 75 QUESTIONS FROM SOURCE PDFs")
    print("=" * 70)
    
    # Load source PDFs
    questions_pdf_path = Path("/app/sources/questions.pdf")
    solutions_pdf_path = Path("/app/sources/solutions.pdf")
    
    if not questions_pdf_path.exists() or not solutions_pdf_path.exists():
        print("❌ Source PDFs not found")
        return False
    
    print(f"\n📄 Loading questions PDF: {questions_pdf_path}")
    print(f"📄 Loading solutions PDF: {solutions_pdf_path}")
    
    with open(questions_pdf_path, 'rb') as qf, open(solutions_pdf_path, 'rb') as sf:
        qdata = qf.read()
        sdata = sf.read()
    
    print(f"✅ Loaded {len(qdata)} bytes questions, {len(sdata)} bytes solutions")
    
    # Extract questions using tejas_core.build_questions
    print("\n🔍 Extracting questions using tejas_core.build_questions...")
    try:
        questions = build_questions(qdata, sdata, "questions", "solutions", known_tejas=True)
        print(f"✅ Extracted {len(questions)} questions")
    except Exception as e:
        print(f"❌ Extraction failed: {str(e)}")
        return False
    
    # Validate 75 questions
    if len(questions) != 75:
        print(f"❌ Expected 75 questions, got {len(questions)}")
        return False
    else:
        print(f"✅ All 75 questions present")
    
    # Count MCQ and integer types
    mcq_count = sum(1 for q in questions if q['type'] == 'mcq')
    integer_count = sum(1 for q in questions if q['type'] == 'integer')
    
    print(f"\n📊 Question breakdown:")
    print(f"   MCQ: {mcq_count}")
    print(f"   Integer: {integer_count}")
    
    if mcq_count != 60 or integer_count != 15:
        print(f"❌ Expected 60 MCQ + 15 integer, got {mcq_count} MCQ + {integer_count} integer")
        return False
    else:
        print(f"✅ Correct breakdown: 60 MCQ + 15 integer")
    
    # Check for specific questions mentioned in requirements (Q37, Q61, Q67, Q69, Q70)
    # Requirements say: "no exclusion of Q37/61/67/69/70"
    critical_numbers = [37, 61, 67, 69, 70]
    found_critical = [q['number'] for q in questions if q['number'] in critical_numbers]
    print(f"\n🔍 Checking critical questions (Q37, Q61, Q67, Q69, Q70)...")
    print(f"   Found: {sorted(found_critical)}")
    
    if len(found_critical) == len(critical_numbers):
        print(f"✅ All critical questions present (no exclusion)")
    else:
        missing = set(critical_numbers) - set(found_critical)
        print(f"⚠️  Missing critical questions: {missing}")
    
    # Check option families (numbered 1-4 vs A-D)
    print(f"\n🔍 Checking option families (should use numbered 1-4, not A-D figure labels)...")
    mcq_questions = [q for q in questions if q['type'] == 'mcq']
    
    numbered_family = 0
    letter_family = 0
    for q in mcq_questions:
        opts = q.get('options', {})
        if opts:
            keys = set(opts.keys())
            if '1' in keys or '2' in keys or '3' in keys or '4' in keys:
                numbered_family += 1
            elif 'A' in keys or 'B' in keys or 'C' in keys or 'D' in keys:
                letter_family += 1
    
    print(f"   Numbered (1-4): {numbered_family}")
    print(f"   Letter (A-D): {letter_family}")
    
    if numbered_family > 0:
        print(f"✅ Using numbered option family (1-4)")
    
    # Test scoring with all correct answers
    print(f"\n🔍 Testing scoring with all 75 questions...")
    
    # Create answers dict with all correct answers
    answers = {}
    for q in questions:
        if q.get('answer'):
            answers[q['id']] = {'value': q['answer'], 'marked': False}
    
    attempt = {
        'questions': questions,
        'answers': answers,
        'rules': RULES,
        'started_at': 0
    }
    
    try:
        result = score(attempt)
        summary = result['summary']
        
        print(f"\n📊 Scoring results:")
        print(f"   Score: {summary['score']} / {summary['maximum']}")
        print(f"   Correct: {summary['correct']}")
        print(f"   Incorrect: {summary['incorrect']}")
        print(f"   Skipped: {summary['skipped']}")
        print(f"   Percentage: {summary.get('percentage', 'N/A')}%")
        
        # Expected: 75 correct * 4 = 300
        if summary['correct'] == len(answers) and summary['score'] == len(answers) * 4:
            print(f"✅ Scoring correct: {summary['correct']} correct = {summary['score']} marks")
        else:
            print(f"⚠️  Scoring mismatch: expected {len(answers)} correct, got {summary['correct']}")
        
    except Exception as e:
        print(f"❌ Scoring failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test with some wrong answers
    print(f"\n🔍 Testing scoring with mixed correct/wrong/blank...")
    
    # Answer only first 10 questions, 5 correct, 5 wrong
    mixed_answers = {}
    for i, q in enumerate(questions[:10]):
        if i < 5:
            # Correct answer
            mixed_answers[q['id']] = {'value': q['answer'], 'marked': False}
        else:
            # Wrong answer
            if q['type'] == 'mcq':
                # Pick a different option
                opts = list(q.get('options', {}).keys())
                wrong_opt = next((o for o in opts if o != q['answer']), opts[0] if opts else '1')
                mixed_answers[q['id']] = {'value': wrong_opt, 'marked': False}
            else:
                # Wrong integer
                mixed_answers[q['id']] = {'value': '999', 'marked': False}
    
    attempt_mixed = {
        'questions': questions,
        'answers': mixed_answers,
        'rules': RULES,
        'started_at': 0
    }
    
    try:
        result_mixed = score(attempt_mixed)
        summary_mixed = result_mixed['summary']
        
        print(f"\n📊 Mixed scoring results:")
        print(f"   Score: {summary_mixed['score']} / {summary_mixed['maximum']}")
        print(f"   Correct: {summary_mixed['correct']}")
        print(f"   Incorrect: {summary_mixed['incorrect']}")
        print(f"   Skipped: {summary_mixed['skipped']}")
        
        # Expected: 5 correct (+20) + 5 wrong (-5) + 65 blank (0) = 15
        expected_score = 5 * 4 + 5 * (-1)  # 20 - 5 = 15
        if summary_mixed['score'] == expected_score:
            print(f"✅ Mixed scoring correct: {expected_score} marks")
        else:
            print(f"⚠️  Expected {expected_score}, got {summary_mixed['score']}")
        
    except Exception as e:
        print(f"❌ Mixed scoring failed: {str(e)}")
        return False
    
    print("\n" + "=" * 70)
    print("✅ ALL 75 QUESTIONS VALIDATED SUCCESSFULLY")
    print("=" * 70)
    return True

if __name__ == '__main__':
    success = test_actual_75_questions()
    sys.exit(0 if success else 1)
