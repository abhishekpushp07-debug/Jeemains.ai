#!/usr/bin/env python3
"""Simulate the worker's PDF processing without sandbox to identify the failure point."""
import fitz
import re
import json

ANCHOR = re.compile(r'^(?:(?:Q(?:uestion)?\.?\s*)(\d{1,3})\s*[.:)\-]?\s*|(\d{1,3})\s*[.)]\s+)(.*)$', re.I)
LIMIT = 50 * 1024 * 1024

def open_pdf(path):
    """Open PDF like the worker does."""
    with open(path, 'rb') as f:
        data = f.read(LIMIT + 1)
    
    if not data.startswith(b'%PDF-') or not 0 < len(data) <= LIMIT:
        raise ValueError('Use valid PDFs of at most50MB each')
    
    doc = fitz.open(stream=data, filetype='pdf')
    
    if doc.is_encrypted or not 1 <= len(doc) <= 300:
        raise ValueError('Use unlocked PDFs of1–300pages')
    
    if any(p.rect.width > 2000 or p.rect.height > 2000 for p in doc):
        raise ValueError('Export standard-size PDF pages')
    
    return doc


def segment(doc):
    """Segment the PDF like the worker does."""
    anchors = []
    headings = []
    columns = {}
    extracted = 0
    
    print(f"Processing {len(doc)} pages...")
    
    for pi, page in enumerate(doc):
        print(f"\nPage {pi + 1}:")
        lines = []
        
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines', []):
                text = ''.join(span['text'] for span in line['spans']).strip()
                if text:
                    lines.append((line['bbox'], text))
                    extracted += len(text)
        
        print(f"  Extracted {len(lines)} lines, {extracted} total chars")
        
        if extracted > 3000000:
            raise ValueError('The PDF has too much text; split the paper')
        
        found = []
        for box, text in lines:
            m = ANCHOR.match(text)
            if m and 1 <= int(m[1] or m[2]) <= 500 and (box[0] < page.rect.width * .27 or page.rect.width * .46 < box[0] < page.rect.width * .68):
                found.append({'number': int(m[1] or m[2]), 'page': pi, 'top': max(12, box[1] - 5), 'x': box[0], 'header': m[3].strip()})
        
        print(f"  Found {len(found)} anchors: {[f['number'] for f in found]}")
        
        two = bool(any(a['x'] < page.rect.width * .3 for a in found) and any(a['x'] > page.rect.width * .46 for a in found))
        columns[pi] = 2 if two else 1
        
        for a in found:
            a['col'] = int(two and a['x'] > page.rect.width * .46)
            anchors.append(a)
    
    print(f"\nTotal anchors found: {len(anchors)}")
    
    anchors.sort(key=lambda a: (a['page'], a['col'], a['top']))
    
    if not anchors or len(anchors) > 300:
        raise ValueError('No reliable numbered questions found. Upload a searchable PDF with numbered questions and solutions')
    
    print(f"Anchors after sorting: {[a['number'] for a in anchors[:10]]}...")
    
    return anchors, columns


def main():
    """Test the worker's logic without sandbox."""
    questions_path = '/app/test_reports/fixtures/real_tejas200_questions.pdf'
    solutions_path = '/app/test_reports/fixtures/real_tejas200_solutions.pdf'
    
    print("=" * 80)
    print("SIMULATING WORKER LOGIC (NO SANDBOX)")
    print("=" * 80)
    print()
    
    try:
        print("Opening Questions PDF...")
        qdoc = open_pdf(questions_path)
        print(f"✓ Questions PDF opened: {len(qdoc)} pages")
        print()
        
        print("Segmenting Questions PDF...")
        q_anchors, q_columns = segment(qdoc)
        print(f"✓ Questions segmented: {len(q_anchors)} anchors")
        print()
        
        print("Opening Solutions PDF...")
        sdoc = open_pdf(solutions_path)
        print(f"✓ Solutions PDF opened: {len(sdoc)} pages")
        print()
        
        print("Segmenting Solutions PDF...")
        s_anchors, s_columns = segment(sdoc)
        print(f"✓ Solutions segmented: {len(s_anchors)} anchors")
        print()
        
        print("=" * 80)
        print("SUCCESS - Worker logic would succeed")
        print("=" * 80)
        print()
        print(f"Questions: {len(q_anchors)} anchors")
        print(f"Solutions: {len(s_anchors)} anchors")
        
        # Show question numbers
        q_numbers = sorted(set(a['number'] for a in q_anchors))
        s_numbers = sorted(set(a['number'] for a in s_anchors))
        
        print(f"\nQuestion numbers: {q_numbers}")
        print(f"Solution numbers: {s_numbers}")
        
        # Check for duplicates
        q_duplicates = [n for n in q_numbers if sum(1 for a in q_anchors if a['number'] == n) > 1]
        s_duplicates = [n for n in s_numbers if sum(1 for a in s_anchors if a['number'] == n) > 1]
        
        if q_duplicates:
            print(f"\n⚠ Duplicate question numbers: {q_duplicates}")
        if s_duplicates:
            print(f"\n⚠ Duplicate solution numbers: {s_duplicates}")
        
    except Exception as e:
        print("=" * 80)
        print("FAILURE - Worker logic would fail")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
