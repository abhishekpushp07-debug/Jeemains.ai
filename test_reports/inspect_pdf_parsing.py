#!/usr/bin/env python3
"""Detailed inspection of PDF parsing to understand where the worker breaks."""
import re
import fitz

ANCHOR = re.compile(r'^(?:(?:Q(?:uestion)?\.?\s*)(\d{1,3})\s*[.:)\-]?\s*|(\d{1,3})\s*[.)]\s+)(.*)$', re.I)

def inspect_questions_pdf():
    """Inspect the questions PDF to see what the parser sees."""
    pdf_path = '/app/test_reports/fixtures/real_tejas200_questions.pdf'
    doc = fitz.open(pdf_path)
    
    print("=" * 80)
    print("DETAILED PDF PARSING INSPECTION - QUESTIONS")
    print("=" * 80)
    print()
    
    # Analyze first 3 pages in detail
    for pi in range(min(3, len(doc))):
        page = doc[pi]
        print(f"\n{'=' * 80}")
        print(f"PAGE {pi + 1}")
        print(f"{'=' * 80}")
        print(f"Page size: {page.rect.width:.1f} x {page.rect.height:.1f}")
        print(f"Left 27% boundary: {page.rect.width * 0.27:.1f}")
        print(f"Middle column: {page.rect.width * 0.46:.1f} to {page.rect.width * 0.68:.1f}")
        print()
        
        # Extract text with positions
        lines = []
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines', []):
                text = ''.join(span['text'] for span in line['spans']).strip()
                if text:
                    lines.append((line['bbox'], text))
        
        print(f"Total text lines: {len(lines)}")
        print()
        
        # Check each line for ANCHOR match
        matches = []
        for box, text in lines:
            m = ANCHOR.match(text)
            x_pos = box[0]
            in_left = x_pos < page.rect.width * 0.27
            in_middle = page.rect.width * 0.46 < x_pos < page.rect.width * 0.68
            in_valid_column = in_left or in_middle
            
            if m:
                q_num = int(m[1] or m[2])
                matches.append({
                    'text': text[:80],
                    'number': q_num,
                    'x': x_pos,
                    'y': box[1],
                    'in_valid_column': in_valid_column,
                    'in_left': in_left,
                    'in_middle': in_middle
                })
        
        if matches:
            print(f"✓ Found {len(matches)} ANCHOR matches:")
            for i, match in enumerate(matches, 1):
                status = "✓ VALID" if match['in_valid_column'] else "✗ INVALID (wrong column)"
                print(f"\n  {i}. Q{match['number']} at x={match['x']:.1f}, y={match['y']:.1f} - {status}")
                print(f"     Text: {match['text']}")
                print(f"     Position: left={match['in_left']}, middle={match['in_middle']}")
        else:
            print("✗ NO ANCHOR matches found!")
            print("\nShowing first 30 lines to debug:")
            for i, (box, text) in enumerate(lines[:30], 1):
                x_pos = box[0]
                # Try to match manually
                if 'Q' in text[:5] or text[:3].isdigit():
                    print(f"\n  {i}. x={x_pos:.1f}, y={box[1]:.1f}")
                    print(f"     Text: {text[:100]}")
                    print(f"     ANCHOR match: {bool(ANCHOR.match(text))}")
                    # Try different variations
                    if not ANCHOR.match(text):
                        # Check if it's a continuation
                        if text.startswith('Q'):
                            print(f"     Starts with Q but doesn't match ANCHOR regex")
                            print(f"     First 20 chars: {repr(text[:20])}")
    
    doc.close()


def inspect_solutions_pdf():
    """Inspect the solutions PDF to see what the parser sees."""
    pdf_path = '/app/test_reports/fixtures/real_tejas200_solutions.pdf'
    doc = fitz.open(pdf_path)
    
    print("\n\n")
    print("=" * 80)
    print("DETAILED PDF PARSING INSPECTION - SOLUTIONS")
    print("=" * 80)
    print()
    
    # Analyze first 3 pages in detail
    for pi in range(min(3, len(doc))):
        page = doc[pi]
        print(f"\n{'=' * 80}")
        print(f"PAGE {pi + 1}")
        print(f"{'=' * 80}")
        print(f"Page size: {page.rect.width:.1f} x {page.rect.height:.1f}")
        print()
        
        # Extract text with positions
        lines = []
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines', []):
                text = ''.join(span['text'] for span in line['spans']).strip()
                if text:
                    lines.append((line['bbox'], text))
        
        print(f"Total text lines: {len(lines)}")
        print()
        
        # Check each line for ANCHOR match
        matches = []
        for box, text in lines:
            m = ANCHOR.match(text)
            x_pos = box[0]
            in_left = x_pos < page.rect.width * 0.27
            in_middle = page.rect.width * 0.46 < x_pos < page.rect.width * 0.68
            in_valid_column = in_left or in_middle
            
            if m:
                q_num = int(m[1] or m[2])
                matches.append({
                    'text': text[:80],
                    'number': q_num,
                    'x': x_pos,
                    'y': box[1],
                    'in_valid_column': in_valid_column
                })
        
        if matches:
            print(f"✓ Found {len(matches)} ANCHOR matches:")
            for i, match in enumerate(matches, 1):
                status = "✓ VALID" if match['in_valid_column'] else "✗ INVALID (wrong column)"
                print(f"  {i}. Q{match['number']} at x={match['x']:.1f}, y={match['y']:.1f} - {status}")
                print(f"     Text: {match['text']}")
        else:
            print("✗ NO ANCHOR matches found!")
            print("\nShowing first 30 lines to debug:")
            for i, (box, text) in enumerate(lines[:30], 1):
                x_pos = box[0]
                if 'Q' in text[:10] or 'Answer' in text[:20]:
                    print(f"\n  {i}. x={x_pos:.1f}, y={box[1]:.1f}")
                    print(f"     Text: {text[:100]}")
                    print(f"     ANCHOR match: {bool(ANCHOR.match(text))}")
    
    doc.close()


def test_anchor_regex():
    """Test the ANCHOR regex with sample lines from the PDF."""
    print("\n\n")
    print("=" * 80)
    print("ANCHOR REGEX TESTING")
    print("=" * 80)
    print()
    
    test_cases = [
        "Q1. Let the foci of a hyperbola H be S(−1, 3) and S′(−1, −1), and let H pass thr",
        "Q8. For a natural number n, let D(n) =",
        "Q20. Let T1 be the equilateral triangle with one vertex at A(1, 1) and the oppos",
        "Q2. Answer: (4)",
        "1. n-th term: Tn = 13 + 23 + · · · + n3",
        "Q",
        "Ans",
        "1",
        "(2)",
        "16",
        "(4)",
        "31",
    ]
    
    for test in test_cases:
        m = ANCHOR.match(test)
        if m:
            q_num = m[1] or m[2]
            header = m[3]
            print(f"✓ MATCH: Q{q_num}")
            print(f"  Input: {test}")
            print(f"  Header: {header[:50]}")
        else:
            print(f"✗ NO MATCH: {test}")
        print()


if __name__ == '__main__':
    inspect_questions_pdf()
    inspect_solutions_pdf()
    test_anchor_regex()
