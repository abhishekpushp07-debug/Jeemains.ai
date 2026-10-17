#!/usr/bin/env python3
"""
Isolated regression test for Tejas200 PDF processing failure.

ISSUE: User report "By the way pdf se nahi le pa rha direct questions. Ab"
       (Cannot extract questions directly from PDF)

ROOT CAUSE: The Solutions PDF contains solution steps numbered as "1.", "2.", "3.", etc.
            The ANCHOR regex matches these step numbers as question anchors, causing the
            total anchor count to exceed 300, which triggers the error:
            "No reliable numbered questions found"

EXPECTED: 75 question anchors in Questions PDF, 75 solution anchors in Solutions PDF
ACTUAL: 77 anchors in Questions PDF (includes false positives), 338 anchors in Solutions PDF

The worker rejects PDFs with >300 anchors as a safety measure, but this legitimate
Solutions PDF is being rejected due to overly permissive ANCHOR regex.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, '/app/backend')

from tejas.sandbox import organise_pdfs


async def test_tejas200_pdf_processing():
    """
    Regression test for Tejas200 PDF processing.
    
    This test demonstrates the failure when processing real Tejas200 PDFs
    where the Solutions PDF contains numbered solution steps that are
    incorrectly detected as question anchors.
    """
    questions_path = Path('/app/test_reports/fixtures/real_tejas200_questions.pdf')
    solutions_path = Path('/app/test_reports/fixtures/real_tejas200_solutions.pdf')
    
    print("=" * 80)
    print("REGRESSION TEST: Tejas200 PDF Processing")
    print("=" * 80)
    print()
    print(f"Questions PDF: {questions_path}")
    print(f"  Size: {questions_path.stat().st_size:,} bytes")
    print(f"  SHA256: 6719a47cacdeb941431c9a33099bc1763d487955835d62820c818e288702b2a8")
    print()
    print(f"Solutions PDF: {solutions_path}")
    print(f"  Size: {solutions_path.stat().st_size:,} bytes")
    print(f"  SHA256: 26f67b6d17b5fe4107d2fbf9ce084ca78c33708b9706f3409d0f786135b2607e")
    print()
    
    try:
        result = await organise_pdfs(
            questions_path=str(questions_path),
            solutions_path=str(solutions_path),
            format='pdf'
        )
        
        print("✅ UNEXPECTED SUCCESS")
        print(f"   Questions processed: {len(result.get('questions', []))}")
        print(f"   Issues: {len(result.get('issues', []))}")
        return True
        
    except ValueError as e:
        error_msg = str(e)
        print("❌ EXPECTED FAILURE")
        print(f"   Error: {error_msg}")
        print()
        
        if "No reliable numbered questions found" in error_msg:
            print("✓ Failure matches expected error")
            print()
            print("ROOT CAUSE:")
            print("  The Solutions PDF contains numbered solution steps (1., 2., 3., etc.)")
            print("  that are incorrectly matched by the ANCHOR regex as question numbers.")
            print("  This causes the anchor count to exceed 300, triggering the error.")
            print()
            print("ANCHOR REGEX:")
            print("  r'^(?:(?:Q(?:uestion)?\\.?\\s*)(\\d{1,3})\\s*[.:)\\-]?\\s*|(\\d{1,3})\\s*[.)\\s+)(.*)$'")
            print()
            print("MATCHES:")
            print("  - 'Q1. Let the foci...' → Q1 (correct)")
            print("  - '1. First step...' → Q1 (incorrect - solution step)")
            print("  - '2. Second step...' → Q2 (incorrect - solution step)")
            print()
            print("EXPECTED: ~75 anchors per PDF")
            print("ACTUAL: 77 in Questions, 338 in Solutions (limit: 300)")
            return False
        else:
            print("✗ Failure does NOT match expected error")
            print(f"   Expected: 'No reliable numbered questions found'")
            print(f"   Got: {error_msg}")
            return False


async def main():
    """Run the regression test."""
    success = await test_tejas200_pdf_processing()
    print()
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    return 0 if not success else 1  # Return 0 if failure is reproduced (expected)


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
