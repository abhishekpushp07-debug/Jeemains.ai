"""
Independent verification tests for chapter book parser.
This script re-extracts answer keys independently and verifies all structural requirements.
"""
import json
import hashlib
import re
import sys
from pathlib import Path
import fitz  # PyMuPDF

# Test configuration
DATA_DIR = Path('/app/data/chapter50')
REPORT_DIR = Path('/app/test_reports')
SUBJECTS = ['physics', 'chemistry', 'mathematics']
EXPECTED_COUNTS = {'physics': 30, 'chemistry': 32, 'mathematics': 32}


def compute_sha256(file_path):
    """Compute SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def independent_key_extraction(pdf_path, chapter_info):
    """
    Independently extract answer keys from PDF without using parser methods.
    Uses a completely different algorithm to verify parser correctness.
    """
    doc = fitz.open(pdf_path)
    key_page_num = chapter_info['key_page'] - 1  # Convert to 0-indexed
    
    if key_page_num >= len(doc):
        return None, f"Key page {chapter_info['key_page']} exceeds PDF length"
    
    page = doc[key_page_num]
    text = page.get_text()
    
    # Verify chapter title appears on key page
    if chapter_info['title'] not in text:
        return None, f"Chapter title '{chapter_info['title']}' not found on key page"
    
    # Independent extraction: find all two-digit numbers followed by A/B/C/D
    # Using word-level extraction for geometric verification
    words = page.get_text('words')
    
    keys = {}
    for i, word in enumerate(words):
        # word format: (x0, y0, x1, y1, text, block_no, line_no, word_no)
        text = word[4]
        
        # Look for question numbers (01-50)
        if re.fullmatch(r'\d{2}', text):
            qnum = int(text)
            if not 1 <= qnum <= 50:
                continue
            
            # Look for answer letter nearby (within 65 pixels horizontally, 2 pixels vertically)
            x0, y0, x1, y1 = word[0], word[1], word[2], word[3]
            
            # Find candidate answer letters
            candidates = []
            for j, other in enumerate(words):
                if i == j:
                    continue
                other_text = other[4]
                if other_text in ('A', 'B', 'C', 'D'):
                    ox0, oy0, ox1, oy1 = other[0], other[1], other[2], other[3]
                    # Check if it's to the right and on same line
                    if 0 < ox0 - x1 < 65 and abs(oy0 - y0) < 2:
                        candidates.append((ox0 - x1, other_text))
            
            # Take the closest candidate
            if len(candidates) == 1:
                keys[qnum] = candidates[0][1]
            elif len(candidates) > 1:
                # Take the closest one
                candidates.sort()
                keys[qnum] = candidates[0][1]
    
    doc.close()
    
    # Verify we got all 50 keys
    if sorted(keys.keys()) != list(range(1, 51)):
        missing = set(range(1, 51)) - set(keys.keys())
        return None, f"Missing keys for questions: {sorted(missing)}"
    
    return keys, None


def verify_question_regions(pdf_path, question, chapter_info):
    """
    Verify question regions don't include key pages and have proper boundaries.
    """
    issues = []
    key_page = chapter_info['key_page']
    
    for ref in question.get('q_refs', []):
        ref_page = ref['page']
        
        # Check if question region includes key page
        if ref_page == key_page:
            issues.append(f"Q{question['number']} includes key page {key_page}")
        
        # Check if page is beyond key page
        if ref_page > key_page:
            issues.append(f"Q{question['number']} page {ref_page} is beyond key page {key_page}")
    
    # Verify options are present
    text = question.get('text', '')
    options_found = set(re.findall(r'\(([A-D])\)', text))
    
    if options_found != {'A', 'B', 'C', 'D'}:
        missing = {'A', 'B', 'C', 'D'} - options_found
        issues.append(f"Q{question['number']} missing options: {sorted(missing)}")
    
    return issues


def render_question_sample(pdf_path, question, output_dir):
    """
    Render a low-res sample of question region to verify formulas aren't clipped.
    Returns True if region is non-empty, False otherwise.
    """
    try:
        doc = fitz.open(pdf_path)
        
        # Render first region only for sampling
        if not question.get('q_refs'):
            doc.close()
            return False
        
        ref = question['q_refs'][0]
        page_num = ref['page'] - 1
        rect = ref['rect']
        
        if page_num >= len(doc):
            doc.close()
            return False
        
        page = doc[page_num]
        clip_rect = fitz.Rect(rect)
        
        # Render at low resolution (72 DPI)
        pix = page.get_pixmap(clip=clip_rect, matrix=fitz.Matrix(1, 1))
        
        # Check if region is non-empty (has some dark pixels)
        samples = pix.samples
        dark_pixels = sum(1 for b in samples if b < 230)
        
        doc.close()
        
        # Region should have at least some content
        return dark_pixels > 100
        
    except Exception as e:
        return False


def verify_chapter(subject, chapter_data, pdf_path):
    """
    Comprehensive verification of a single chapter.
    Returns a detailed test result dictionary.
    """
    result = {
        'subject': subject,
        'chapter_number': chapter_data['number'],
        'title': chapter_data['title'],
        'question_count': len(chapter_data['questions']),
        'key_count': 0,
        'matched_keys': 0,
        'regions_checked': 0,
        'issues': [],
        'status': 'PASS',
        'source_sha256': '',
        'parsed_sha256': ''
    }
    
    # Verify question count
    if result['question_count'] != 50:
        result['issues'].append(f"Expected 50 questions, found {result['question_count']}")
        result['status'] = 'FAIL'
    
    # Independent key extraction
    independent_keys, error = independent_key_extraction(pdf_path, chapter_data)
    
    if error:
        result['issues'].append(f"Independent key extraction failed: {error}")
        result['status'] = 'FAIL'
        return result
    
    result['key_count'] = len(independent_keys)
    
    # Compare with parsed keys
    matched = 0
    key_mismatches = []
    
    for question in chapter_data['questions']:
        qnum = question['number']
        parsed_answer = question.get('answer')
        
        if qnum in independent_keys:
            if independent_keys[qnum] == parsed_answer:
                matched += 1
            else:
                key_mismatches.append(
                    f"Q{qnum}: parsed={parsed_answer}, independent={independent_keys[qnum]}"
                )
        
        # Verify question regions
        region_issues = verify_question_regions(pdf_path, question, chapter_data)
        result['issues'].extend(region_issues)
        
        result['regions_checked'] += 1
    
    result['matched_keys'] = matched
    
    if key_mismatches:
        result['issues'].extend(key_mismatches)
        result['status'] = 'FAIL'
    
    # Sample rendering check (first, middle, last, random questions)
    sample_indices = [0, 24, 49]
    if len(chapter_data['questions']) >= 50:
        sample_indices.append(17)  # Random middle question
    
    empty_renders = []
    for idx in sample_indices:
        if idx < len(chapter_data['questions']):
            question = chapter_data['questions'][idx]
            if not render_question_sample(pdf_path, question, REPORT_DIR):
                empty_renders.append(f"Q{question['number']}")
    
    if empty_renders:
        result['issues'].append(f"Empty/invalid renders: {', '.join(empty_renders)}")
        result['status'] = 'FAIL'
    
    # Final status
    if result['issues']:
        result['status'] = 'FAIL'
    
    return result


def run_all_tests():
    """
    Run comprehensive tests on all 94 chapters.
    """
    print("=" * 80)
    print("CHAPTER BOOK INDEPENDENT VERIFICATION")
    print("=" * 80)
    
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    
    all_results = []
    total_chapters = 0
    passed_chapters = 0
    
    for subject in SUBJECTS:
        print(f"\n{'=' * 80}")
        print(f"Testing {subject.upper()}")
        print(f"{'=' * 80}")
        
        pdf_path = DATA_DIR / f'{subject}.pdf'
        json_path = DATA_DIR / f'{subject}.parsed.json'
        
        # Compute hashes
        source_hash = compute_sha256(pdf_path)
        parsed_hash = compute_sha256(json_path)
        
        print(f"Source SHA256: {source_hash}")
        print(f"Parsed SHA256: {parsed_hash}")
        
        # Load parsed data
        with open(json_path, 'r') as f:
            parsed_data = json.load(f)
        
        chapters = parsed_data.get('chapters', [])
        expected_count = EXPECTED_COUNTS[subject]
        
        print(f"\nExpected chapters: {expected_count}")
        print(f"Found chapters: {len(chapters)}")
        
        if len(chapters) != expected_count:
            print(f"❌ FAIL: Chapter count mismatch!")
        
        # Verify each chapter
        for i, chapter in enumerate(chapters, 1):
            print(f"\n[{i}/{len(chapters)}] Chapter {chapter['number']}: {chapter['title']}")
            
            result = verify_chapter(subject, chapter, pdf_path)
            result['source_sha256'] = source_hash
            result['parsed_sha256'] = parsed_hash
            
            all_results.append(result)
            total_chapters += 1
            
            if result['status'] == 'PASS':
                passed_chapters += 1
                print(f"  ✅ PASS - {result['matched_keys']}/50 keys matched, {result['regions_checked']} regions checked")
            else:
                print(f"  ❌ FAIL - Issues found:")
                for issue in result['issues'][:5]:  # Show first 5 issues
                    print(f"    - {issue}")
                if len(result['issues']) > 5:
                    print(f"    ... and {len(result['issues']) - 5} more issues")
    
    # Save detailed report
    report_path = REPORT_DIR / 'chapter50_recheck.json'
    with open(report_path, 'w') as f:
        json.dump({
            'test_type': 'chapter_book_independent_verification',
            'total_chapters': total_chapters,
            'passed_chapters': passed_chapters,
            'failed_chapters': total_chapters - passed_chapters,
            'success_rate': f"{(passed_chapters / total_chapters * 100):.1f}%",
            'chapters': all_results
        }, f, indent=2)
    
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total chapters tested: {total_chapters}")
    print(f"Passed: {passed_chapters}")
    print(f"Failed: {total_chapters - passed_chapters}")
    print(f"Success rate: {(passed_chapters / total_chapters * 100):.1f}%")
    print(f"\nDetailed report saved to: {report_path}")
    
    # Return exit code
    return 0 if passed_chapters == total_chapters else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
