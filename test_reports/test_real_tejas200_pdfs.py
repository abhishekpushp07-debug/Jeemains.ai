#!/usr/bin/env python3
"""Test real Tejas200 PDFs with actual organise_pdfs function.

This script reproduces the user's reported issue: "By the way pdf se nahi le pa rha direct questions. Ab"
(Cannot extract questions directly from PDF)

Downloads real PDFs and invokes the actual tejas.sandbox.organise_pdfs function.
Reports exact result counts, types, subjects, issues, and timing.
"""
import asyncio
import json
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, '/app/backend')

from tejas.sandbox import organise_pdfs


async def test_real_tejas200_pdfs():
    """Test the actual organise_pdfs function with real Tejas200 PDFs."""
    
    questions_path = Path('/app/test_reports/fixtures/real_tejas200_questions.pdf')
    solutions_path = Path('/app/test_reports/fixtures/real_tejas200_solutions.pdf')
    
    print("=" * 80)
    print("REAL TEJAS200 PDF PROCESSING TEST")
    print("=" * 80)
    print()
    
    # Verify files exist
    if not questions_path.exists():
        print(f"❌ Questions PDF not found: {questions_path}")
        return None
    if not solutions_path.exists():
        print(f"❌ Solutions PDF not found: {solutions_path}")
        return None
    
    print(f"✓ Questions PDF: {questions_path} ({questions_path.stat().st_size:,} bytes)")
    print(f"✓ Solutions PDF: {solutions_path} ({solutions_path.stat().st_size:,} bytes)")
    print()
    
    # Invoke actual organise_pdfs function
    print("Invoking tejas.sandbox.organise_pdfs()...")
    print()
    
    start_time = time.time()
    try:
        result = await organise_pdfs(
            questions_path=str(questions_path),
            solutions_path=str(solutions_path),
            format='pdf'
        )
        elapsed_time = time.time() - start_time
        
        print(f"✅ SUCCESS - Processing completed in {elapsed_time:.2f} seconds")
        print()
        
        # Calculate output size
        output_json = json.dumps(result, ensure_ascii=False)
        output_size = len(output_json.encode('utf-8'))
        
        print("=" * 80)
        print("RESULTS SUMMARY")
        print("=" * 80)
        print()
        print(f"Processing Time: {elapsed_time:.2f} seconds")
        print(f"Output Size: {output_size:,} bytes ({output_size / 1024 / 1024:.2f} MB)")
        print()
        
        # Extract key metrics
        questions = result.get('questions', [])
        issues = result.get('issues', [])
        unmatched_solutions = result.get('unmatched_solutions', 0)
        exam = result.get('exam', 'Unknown')
        duration = result.get('duration_minutes', 0)
        source_pages = result.get('source_pages', {})
        sandbox = result.get('sandbox', 'Unknown')
        
        print(f"Total Questions: {len(questions)}")
        print(f"Total Issues: {len(issues)}")
        print(f"Unmatched Solutions: {unmatched_solutions}")
        print(f"Exam Type: {exam}")
        print(f"Duration: {duration} minutes")
        print(f"Source Pages: Questions={source_pages.get('questions', 0)}, Solutions={source_pages.get('solutions', 0)}")
        print(f"Sandbox Mode: {sandbox}")
        print()
        
        # Count by type
        type_counts = {}
        for q in questions:
            qtype = q.get('type', 'unknown')
            type_counts[qtype] = type_counts.get(qtype, 0) + 1
        
        print("Question Types:")
        for qtype, count in sorted(type_counts.items()):
            print(f"  {qtype}: {count}")
        print()
        
        # Count by subject
        subject_counts = {}
        for q in questions:
            subject = q.get('subject', 'Unknown')
            subject_counts[subject] = subject_counts.get(subject, 0) + 1
        
        print("Questions by Subject:")
        for subject, count in sorted(subject_counts.items()):
            print(f"  {subject}: {count}")
        print()
        
        # Show first 10 issues
        if issues:
            print("=" * 80)
            print("FIRST 10 ISSUES")
            print("=" * 80)
            print()
            for i, issue in enumerate(issues[:10], 1):
                q_num = issue.get('question', 'N/A')
                message = issue.get('message', 'No message')
                print(f"{i}. Question {q_num}: {message}")
            
            if len(issues) > 10:
                print(f"\n... and {len(issues) - 10} more issues")
            print()
        else:
            print("✅ No issues found!")
            print()
        
        # Show sample questions
        print("=" * 80)
        print("SAMPLE QUESTIONS (First 3)")
        print("=" * 80)
        print()
        for i, q in enumerate(questions[:3], 1):
            print(f"Question {i}:")
            print(f"  Number: {q.get('number')} (Source: {q.get('source_number')})")
            print(f"  Subject: {q.get('subject')}")
            print(f"  Type: {q.get('type')}")
            print(f"  Answer: {q.get('answer', 'N/A')}")
            print(f"  Text Preview: {q.get('text', '')[:100]}...")
            print(f"  Options: {len(q.get('options', {}))} options")
            print(f"  Assets: Q={len(q.get('assets', {}).get('question', []))}, S={len(q.get('assets', {}).get('solution', []))}")
            print(f"  Issues: {q.get('issues', [])}")
            print()
        
        return result
        
    except ValueError as e:
        elapsed_time = time.time() - start_time
        print(f"❌ FAILURE - Processing failed after {elapsed_time:.2f} seconds")
        print(f"Error: {str(e)}")
        print()
        return None
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"❌ UNEXPECTED ERROR - Processing failed after {elapsed_time:.2f} seconds")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        return None


async def inspect_pdf_structure():
    """Inspect PDF structure to understand where parsing might break."""
    print()
    print("=" * 80)
    print("PDF STRUCTURE INSPECTION")
    print("=" * 80)
    print()
    
    try:
        import fitz
        
        questions_path = Path('/app/test_reports/fixtures/real_tejas200_questions.pdf')
        solutions_path = Path('/app/test_reports/fixtures/real_tejas200_solutions.pdf')
        
        for pdf_path, label in [(questions_path, 'QUESTIONS'), (solutions_path, 'SOLUTIONS')]:
            print(f"\n{label} PDF: {pdf_path.name}")
            print("-" * 80)
            
            doc = fitz.open(pdf_path)
            print(f"Pages: {len(doc)}")
            print(f"Encrypted: {doc.is_encrypted}")
            print(f"Metadata: {doc.metadata}")
            print()
            
            # Analyze first 3 pages
            for page_num in range(min(3, len(doc))):
                page = doc[page_num]
                print(f"\nPage {page_num + 1}:")
                print(f"  Size: {page.rect.width:.1f} x {page.rect.height:.1f}")
                
                # Extract text blocks
                text_dict = page.get_text('dict')
                blocks = text_dict.get('blocks', [])
                print(f"  Text Blocks: {len(blocks)}")
                
                # Look for question numbers
                text = page.get_text()
                lines = text.split('\n')[:20]  # First 20 lines
                print(f"  First 20 lines:")
                for i, line in enumerate(lines, 1):
                    if line.strip():
                        print(f"    {i}: {line.strip()[:80]}")
            
            doc.close()
            print()
    
    except Exception as e:
        print(f"Error inspecting PDFs: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test execution."""
    # Test the actual organise_pdfs function
    result = await test_real_tejas200_pdfs()
    
    # Inspect PDF structure
    await inspect_pdf_structure()
    
    # Save detailed results
    if result:
        output_path = Path('/app/test_reports/real_tejas200_detailed_results.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n✓ Detailed results saved to: {output_path}")
        print(f"  Size: {output_path.stat().st_size:,} bytes")
    
    print()
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    asyncio.run(main())
