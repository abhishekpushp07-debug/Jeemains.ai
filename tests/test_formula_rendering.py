"""
Visual verification test for formula rendering and boundary detection.
Creates contact sheets for sample questions to verify formulas aren't clipped.
"""
import json
import sys
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import io

DATA_DIR = Path('/app/data/chapter50')
REPORT_DIR = Path('/app/test_reports')
SUBJECTS = ['physics', 'chemistry', 'mathematics']


def create_contact_sheet(pdf_path, chapter_data, sample_indices, output_path):
    """
    Create a contact sheet of sample question renderings.
    Returns list of issues found.
    """
    issues = []
    doc = fitz.open(pdf_path)
    images = []
    
    for idx in sample_indices:
        if idx >= len(chapter_data['questions']):
            continue
        
        question = chapter_data['questions'][idx]
        qnum = question['number']
        
        # Render first region of this question
        if not question.get('q_refs'):
            issues.append(f"Q{qnum}: No q_refs found")
            continue
        
        ref = question['q_refs'][0]
        page_num = ref['page'] - 1
        rect = ref['rect']
        
        if page_num >= len(doc):
            issues.append(f"Q{qnum}: Page {ref['page']} exceeds PDF length")
            continue
        
        try:
            page = doc[page_num]
            clip_rect = fitz.Rect(rect)
            
            # Render at 150 DPI for better quality
            mat = fitz.Matrix(150/72, 150/72)
            pix = page.get_pixmap(clip=clip_rect, matrix=mat)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Check if image has content
            extrema = img.convert('L').getextrema()
            if extrema[0] == extrema[1]:  # All pixels same color
                issues.append(f"Q{qnum}: Rendered region appears empty")
            
            images.append((qnum, img))
            
        except Exception as e:
            issues.append(f"Q{qnum}: Rendering failed - {str(e)}")
    
    doc.close()
    
    # Create contact sheet if we have images
    if images:
        # Calculate grid layout
        cols = min(2, len(images))
        rows = (len(images) + cols - 1) // cols
        
        # Get max dimensions
        max_width = max(img.width for _, img in images)
        max_height = max(img.height for _, img in images)
        
        # Create contact sheet
        sheet_width = max_width * cols + 20 * (cols + 1)
        sheet_height = max_height * rows + 20 * (rows + 1) + 30 * rows  # Extra for labels
        
        sheet = Image.new('RGB', (sheet_width, sheet_height), 'white')
        
        for i, (qnum, img) in enumerate(images):
            row = i // cols
            col = i % cols
            
            x = 20 + col * (max_width + 20)
            y = 20 + row * (max_height + 50)
            
            sheet.paste(img, (x, y))
        
        # Save contact sheet
        sheet.save(output_path, 'PNG', optimize=True, quality=85)
    
    return issues


def verify_formula_boundaries(pdf_path, chapter_data):
    """
    Verify that question boundaries properly include elevated fractions/radicals.
    Checks for potential clipping at boundaries.
    """
    issues = []
    doc = fitz.open(pdf_path)
    
    for question in chapter_data['questions']:
        qnum = question['number']
        text = question.get('text', '')
        
        # Check for mathematical symbols that might indicate formulas
        has_formulas = any(symbol in text for symbol in ['√', '∫', '∑', '∏', '∂', 'π', 'θ', '≤', '≥', '≠', '±'])
        
        if has_formulas:
            # Verify regions have reasonable height (formulas need vertical space)
            for ref in question.get('q_refs', []):
                rect = ref['rect']
                height = rect[3] - rect[1]  # y1 - y0
                
                # If height is too small for formulas, flag it
                if height < 30:
                    issues.append(f"Q{qnum}: Region height {height:.1f} may clip formulas")
        
        # Check for cross-page questions
        if len(question.get('q_refs', [])) > 1:
            pages = [ref['page'] for ref in question['q_refs']]
            if max(pages) - min(pages) > 1:
                issues.append(f"Q{qnum}: Spans {len(pages)} pages (may have boundary issues)")
    
    doc.close()
    return issues


def test_sample_chapters():
    """
    Test sample chapters with detailed visual verification.
    """
    print("=" * 80)
    print("FORMULA RENDERING AND BOUNDARY VERIFICATION")
    print("=" * 80)
    
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    
    all_issues = []
    
    # Test one chapter from each subject
    test_cases = [
        ('physics', 1, 'Units & Measurements'),
        ('chemistry', 1, 'Mole Concept'),
        ('mathematics', 13, 'Continuity & Differentiability')  # Math-heavy chapter
    ]
    
    for subject, chapter_num, expected_title in test_cases:
        print(f"\n{'=' * 80}")
        print(f"Testing {subject.upper()} - Chapter {chapter_num}")
        print(f"{'=' * 80}")
        
        pdf_path = DATA_DIR / f'{subject}.pdf'
        json_path = DATA_DIR / f'{subject}.parsed.json'
        
        with open(json_path, 'r') as f:
            parsed_data = json.load(f)
        
        # Find the chapter
        chapter = None
        for ch in parsed_data['chapters']:
            if ch['number'] == chapter_num:
                chapter = ch
                break
        
        if not chapter:
            print(f"❌ Chapter {chapter_num} not found!")
            continue
        
        print(f"Chapter title: {chapter['title']}")
        
        # Sample questions: first, middle, last, and some randoms
        sample_indices = [0, 12, 24, 36, 49]
        
        # Create contact sheet
        output_path = REPORT_DIR / f'contact_sheet_{subject}_ch{chapter_num}.png'
        print(f"\nCreating contact sheet with questions: {[chapter['questions'][i]['number'] for i in sample_indices if i < len(chapter['questions'])]}")
        
        sheet_issues = create_contact_sheet(pdf_path, chapter, sample_indices, output_path)
        
        if sheet_issues:
            print(f"❌ Contact sheet issues:")
            for issue in sheet_issues:
                print(f"  - {issue}")
            all_issues.extend(sheet_issues)
        else:
            print(f"✅ Contact sheet created: {output_path}")
        
        # Verify formula boundaries
        print(f"\nVerifying formula boundaries...")
        boundary_issues = verify_formula_boundaries(pdf_path, chapter)
        
        if boundary_issues:
            print(f"⚠️  Boundary warnings:")
            for issue in boundary_issues[:5]:
                print(f"  - {issue}")
            if len(boundary_issues) > 5:
                print(f"  ... and {len(boundary_issues) - 5} more")
            all_issues.extend(boundary_issues)
        else:
            print(f"✅ No boundary issues detected")
    
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total issues found: {len(all_issues)}")
    
    if all_issues:
        print("\nAll issues:")
        for issue in all_issues[:20]:
            print(f"  - {issue}")
        if len(all_issues) > 20:
            print(f"  ... and {len(all_issues) - 20} more")
        raise AssertionError('; '.join(all_issues))
    else:
        print("✅ All visual verification tests passed!")
        return None


if __name__ == '__main__':
    sys.exit(test_sample_chapters())
