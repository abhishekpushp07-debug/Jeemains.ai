#!/usr/bin/env python3
"""
Comprehensive regression verification for PDF organizer fix (iteration 60 → 61).

ISSUE FIXED: Solutions PDF with 338 anchors (limit: 300) due to ANCHOR regex 
             matching solution step numbers (1., 2., 3.) as question numbers.

FIX APPLIED: Modified ANCHOR matching logic to distinguish Q-prefixed headers 
             from bare numerals. When Q-prefixed headers exist, only accept 
             Q-prefixed anchors, rejecting bare solution step numbers.

VERIFICATION:
1. PDF processing succeeds (was failing with "No reliable numbered questions found")
2. Exactly 75 questions extracted (not 338 false positives)
3. All render_mode = "source" (no guessed math conversions)
4. All subjects, types, and answers correctly extracted
5. No issues reported
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, '/app/backend')

from tejas.sandbox import organise_pdfs


async def verify_regression_fix():
    """Comprehensive verification of the PDF organizer fix."""
    
    questions_path = Path('/app/test_reports/fixtures/real_tejas200_questions.pdf')
    solutions_path = Path('/app/test_reports/fixtures/real_tejas200_solutions.pdf')
    
    print("=" * 80)
    print("ITERATION 61: PDF ORGANIZER REGRESSION VERIFICATION")
    print("=" * 80)
    print()
    print("Issue: Solutions PDF rejected due to 338 anchors (limit: 300)")
    print("Root cause: ANCHOR regex matched solution steps (1., 2., 3.) as questions")
    print("Fix: Distinguish Q-prefixed headers from bare numerals")
    print()
    print("=" * 80)
    print()
    
    # Verify files exist
    if not questions_path.exists() or not solutions_path.exists():
        print("❌ FAIL: Test fixture PDFs not found")
        return False
    
    print(f"✓ Questions PDF: {questions_path.stat().st_size:,} bytes")
    print(f"✓ Solutions PDF: {solutions_path.stat().st_size:,} bytes")
    print()
    
    # Test 1: PDF processing succeeds
    print("TEST 1: PDF Processing Success")
    print("-" * 80)
    try:
        result = await organise_pdfs(
            questions_path=str(questions_path),
            solutions_path=str(solutions_path),
            format='pdf'
        )
        print("✅ PASS: PDF processing succeeded")
    except ValueError as e:
        print(f"❌ FAIL: PDF processing failed with error: {e}")
        return False
    except Exception as e:
        print(f"❌ FAIL: Unexpected error: {e}")
        return False
    print()
    
    # Test 2: Exactly 75 questions extracted
    print("TEST 2: Question Count")
    print("-" * 80)
    questions = result.get('questions', [])
    if len(questions) == 75:
        print(f"✅ PASS: Extracted exactly 75 questions (not 338 false positives)")
    else:
        print(f"❌ FAIL: Expected 75 questions, got {len(questions)}")
        return False
    print()
    
    # Test 3: No issues reported
    print("TEST 3: Issue Count")
    print("-" * 80)
    issues = result.get('issues', [])
    if len(issues) == 0:
        print(f"✅ PASS: No issues reported")
    else:
        print(f"❌ FAIL: {len(issues)} issues reported")
        for i, issue in enumerate(issues[:5], 1):
            print(f"  {i}. Q{issue.get('question', 'N/A')}: {issue.get('message', 'No message')}")
        return False
    print()
    
    # Test 4: All render_mode = "source" (no guessed conversions)
    print("TEST 4: Math Preservation (render_mode = 'source')")
    print("-" * 80)
    render_modes = [q.get('render_mode', 'N/A') for q in questions]
    source_count = sum(1 for mode in render_modes if mode == 'source')
    if source_count == 75:
        print(f"✅ PASS: All 75 questions use render_mode='source'")
        print(f"         (No guessed math conversions)")
    else:
        print(f"❌ FAIL: Only {source_count}/75 questions use render_mode='source'")
        non_source = [q['number'] for q in questions if q.get('render_mode') != 'source']
        print(f"  Non-source questions: {non_source[:10]}")
        return False
    print()
    
    # Test 5: Subject distribution
    print("TEST 5: Subject Distribution")
    print("-" * 80)
    subject_counts = {}
    for q in questions:
        subject = q.get('subject', 'Unknown')
        subject_counts[subject] = subject_counts.get(subject, 0) + 1
    
    expected = {'Mathematics': 25, 'Physics': 25, 'Chemistry': 25}
    if subject_counts == expected:
        print(f"✅ PASS: Correct subject distribution")
        for subject, count in sorted(subject_counts.items()):
            print(f"         {subject}: {count}")
    else:
        print(f"❌ FAIL: Incorrect subject distribution")
        print(f"  Expected: {expected}")
        print(f"  Got: {subject_counts}")
        return False
    print()
    
    # Test 6: Question type distribution
    print("TEST 6: Question Type Distribution")
    print("-" * 80)
    type_counts = {}
    for q in questions:
        qtype = q.get('type', 'unknown')
        type_counts[qtype] = type_counts.get(qtype, 0) + 1
    
    expected_types = {'mcq': 60, 'integer': 15}
    if type_counts == expected_types:
        print(f"✅ PASS: Correct type distribution")
        for qtype, count in sorted(type_counts.items()):
            print(f"         {qtype}: {count}")
    else:
        print(f"❌ FAIL: Incorrect type distribution")
        print(f"  Expected: {expected_types}")
        print(f"  Got: {type_counts}")
        return False
    print()
    
    # Test 7: All questions have answers
    print("TEST 7: Answer Extraction")
    print("-" * 80)
    questions_with_answers = sum(1 for q in questions if q.get('answer'))
    if questions_with_answers == 75:
        print(f"✅ PASS: All 75 questions have answers extracted")
    else:
        print(f"❌ FAIL: Only {questions_with_answers}/75 questions have answers")
        missing = [q['number'] for q in questions if not q.get('answer')]
        print(f"  Missing answers: {missing[:10]}")
        return False
    print()
    
    # Test 8: Asset counts
    print("TEST 8: Asset Preservation")
    print("-" * 80)
    total_q_assets = sum(len(q['assets']['question']) for q in questions)
    total_s_assets = sum(len(q['assets']['solution']) for q in questions)
    
    if total_q_assets > 0 and total_s_assets > 0:
        print(f"✅ PASS: Assets preserved")
        print(f"         Question assets: {total_q_assets}")
        print(f"         Solution assets: {total_s_assets}")
        print(f"         Total: {total_q_assets + total_s_assets}")
    else:
        print(f"❌ FAIL: Missing assets")
        print(f"  Question assets: {total_q_assets}")
        print(f"  Solution assets: {total_s_assets}")
        return False
    print()
    
    # Test 9: Unmatched solutions
    print("TEST 9: Solution Matching")
    print("-" * 80)
    unmatched = result.get('unmatched_solutions', 0)
    if unmatched == 0:
        print(f"✅ PASS: All solutions matched to questions")
    else:
        print(f"❌ FAIL: {unmatched} unmatched solutions")
        return False
    print()
    
    # Test 10: Processing metadata
    print("TEST 10: Processing Metadata")
    print("-" * 80)
    exam = result.get('exam', 'Unknown')
    duration = result.get('duration_minutes', 0)
    sandbox = result.get('sandbox', 'Unknown')
    source_pages = result.get('source_pages', {})
    
    print(f"  Exam type: {exam}")
    print(f"  Duration: {duration} minutes")
    print(f"  Sandbox: {sandbox}")
    print(f"  Source pages: Q={source_pages.get('questions', 0)}, S={source_pages.get('solutions', 0)}")
    
    if exam and duration > 0 and sandbox and source_pages:
        print(f"✅ PASS: Metadata extracted correctly")
    else:
        print(f"❌ FAIL: Missing or incorrect metadata")
        return False
    print()
    
    return True


async def main():
    """Run comprehensive regression verification."""
    print()
    success = await verify_regression_fix()
    print()
    print("=" * 80)
    if success:
        print("✅ ALL TESTS PASSED - Regression fix verified")
        print()
        print("Summary:")
        print("  • PDF processing succeeds (was failing)")
        print("  • 75 questions extracted (not 338 false positives)")
        print("  • All math preserved as source (no guessed conversions)")
        print("  • All subjects, types, answers correctly extracted")
        print("  • No issues reported")
        print("  • All solutions matched")
    else:
        print("❌ TESTS FAILED - Regression fix incomplete")
    print("=" * 80)
    print()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
