#!/usr/bin/env python3
"""Test backward compatibility: ensure fix doesn't break PDFs with bare numerals."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, '/app/backend')

from tejas.sandbox import organise_pdfs


async def test_synthetic_pdfs():
    """Test that synthetic PDFs with bare numerals still work."""
    
    questions_path = Path('/app/test_reports/fixtures/synthetic_questions_standard.pdf')
    solutions_path = Path('/app/test_reports/fixtures/synthetic_solutions_standard.pdf')
    
    print("=" * 80)
    print("BACKWARD COMPATIBILITY TEST: Synthetic PDFs with Bare Numerals")
    print("=" * 80)
    print()
    
    if not questions_path.exists() or not solutions_path.exists():
        print("❌ Synthetic PDFs not found")
        return False
    
    print(f"Questions: {questions_path.name} ({questions_path.stat().st_size} bytes)")
    print(f"Solutions: {solutions_path.name} ({solutions_path.stat().st_size} bytes)")
    print()
    
    try:
        result = await organise_pdfs(
            questions_path=str(questions_path),
            solutions_path=str(solutions_path),
            format='pdf'
        )
        
        questions = result.get('questions', [])
        issues = result.get('issues', [])
        
        print(f"✅ SUCCESS")
        print(f"   Questions: {len(questions)}")
        print(f"   Issues: {len(issues)}")
        print()
        
        if questions:
            print("Sample questions:")
            for q in questions[:3]:
                print(f"  Q{q['number']}: {q.get('text', '')[:60]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


async def main():
    success = await test_synthetic_pdfs()
    print()
    print("=" * 80)
    if success:
        print("✅ BACKWARD COMPATIBILITY VERIFIED")
        print("   PDFs with bare numerals (no Q-prefix) still work correctly")
    else:
        print("❌ BACKWARD COMPATIBILITY BROKEN")
        print("   Fix may have broken PDFs with bare numerals")
    print("=" * 80)
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
