"""
Pytest-compatible test suite for chapter book parser verification.
Run with: pytest tests/test_chapter_book_validation.py -v
"""
import json
import hashlib
import re
from pathlib import Path
import pytest
import fitz

DATA_DIR = Path('/app/data/chapter50')
SUBJECTS = ['physics', 'chemistry', 'mathematics']
EXPECTED_COUNTS = {'physics': 30, 'chemistry': 32, 'mathematics': 32}


@pytest.fixture(scope='module')
def parsed_data():
    """Load all parsed data once for all tests."""
    data = {}
    for subject in SUBJECTS:
        json_path = DATA_DIR / f'{subject}.parsed.json'
        with open(json_path, 'r') as f:
            data[subject] = json.load(f)
    return data


@pytest.fixture(scope='module')
def pdf_docs():
    """Open all PDF documents once for all tests."""
    docs = {}
    for subject in SUBJECTS:
        pdf_path = DATA_DIR / f'{subject}.pdf'
        docs[subject] = fitz.open(pdf_path)
    yield docs
    # Cleanup
    for doc in docs.values():
        doc.close()


class TestChapterCounts:
    """Test chapter counts and structure."""
    
    def test_total_chapter_count(self, parsed_data):
        """Verify total chapter count is 94."""
        total = sum(len(data['chapters']) for data in parsed_data.values())
        assert total == 94, f"Expected 94 chapters, found {total}"
    
    @pytest.mark.parametrize('subject', SUBJECTS)
    def test_subject_chapter_count(self, parsed_data, subject):
        """Verify each subject has correct chapter count."""
        expected = EXPECTED_COUNTS[subject]
        actual = len(parsed_data[subject]['chapters'])
        assert actual == expected, f"{subject}: expected {expected} chapters, found {actual}"
    
    @pytest.mark.parametrize('subject', SUBJECTS)
    def test_chapter_numbering(self, parsed_data, subject):
        """Verify chapters are numbered sequentially from 1."""
        chapters = parsed_data[subject]['chapters']
        numbers = [ch['number'] for ch in chapters]
        expected = list(range(1, len(chapters) + 1))
        assert numbers == expected, f"{subject}: chapter numbering is not sequential"


class TestQuestionCounts:
    """Test question counts and structure."""
    
    def test_total_question_count(self, parsed_data):
        """Verify total question count is 4700."""
        total = sum(data['count'] for data in parsed_data.values())
        assert total == 4700, f"Expected 4700 questions, found {total}"
    
    @pytest.mark.parametrize('subject', SUBJECTS)
    def test_all_chapters_have_50_questions(self, parsed_data, subject):
        """Verify every chapter has exactly 50 questions."""
        chapters = parsed_data[subject]['chapters']
        for chapter in chapters:
            qcount = len(chapter['questions'])
            assert qcount == 50, f"{subject} Ch{chapter['number']}: expected 50 questions, found {qcount}"
    
    @pytest.mark.parametrize('subject', SUBJECTS)
    def test_question_numbering(self, parsed_data, subject):
        """Verify questions in each chapter are numbered 1-50."""
        chapters = parsed_data[subject]['chapters']
        for chapter in chapters:
            numbers = [q['number'] for q in chapter['questions']]
            expected = list(range(1, 51))
            assert numbers == expected, f"{subject} Ch{chapter['number']}: question numbering incorrect"


class TestAnswerKeys:
    """Test answer key integrity."""
    
    @pytest.mark.parametrize('subject', SUBJECTS)
    def test_all_questions_have_answers(self, parsed_data, subject):
        """Verify every question has an answer key."""
        chapters = parsed_data[subject]['chapters']
        for chapter in chapters:
            for question in chapter['questions']:
                answer = question.get('answer')
                assert answer in ('A', 'B', 'C', 'D'), \
                    f"{subject} Ch{chapter['number']} Q{question['number']}: invalid answer '{answer}'"
    
    @pytest.mark.parametrize('subject', SUBJECTS)
    def test_answer_key_distribution(self, parsed_data, subject):
        """Verify answer keys have reasonable distribution (not all same)."""
        chapters = parsed_data[subject]['chapters']
        for chapter in chapters:
            answers = [q['answer'] for q in chapter['questions']]
            unique_answers = set(answers)
            # At least 2 different answers in a chapter (very conservative check)
            assert len(unique_answers) >= 2, \
                f"{subject} Ch{chapter['number']}: all answers are '{answers[0]}' (suspicious)"


class TestQuestionRegions:
    """Test question region references."""
    
    @pytest.mark.parametrize('subject', SUBJECTS)
    def test_all_questions_have_regions(self, parsed_data, subject):
        """Verify every question has at least one region reference."""
        chapters = parsed_data[subject]['chapters']
        for chapter in chapters:
            for question in chapter['questions']:
                q_refs = question.get('q_refs', [])
                assert len(q_refs) >= 1, \
                    f"{subject} Ch{chapter['number']} Q{question['number']}: no q_refs"
    
    @pytest.mark.parametrize('subject', SUBJECTS)
    def test_regions_dont_include_key_page(self, parsed_data, subject):
        """Verify question regions never include the answer key page."""
        chapters = parsed_data[subject]['chapters']
        for chapter in chapters:
            key_page = chapter['key_page']
            for question in chapter['questions']:
                q_refs = question.get('q_refs', [])
                for ref in q_refs:
                    assert ref['page'] != key_page, \
                        f"{subject} Ch{chapter['number']} Q{question['number']}: includes key page {key_page}"
    
    @pytest.mark.parametrize('subject', SUBJECTS)
    def test_regions_before_key_page(self, parsed_data, subject):
        """Verify all question regions are before the key page."""
        chapters = parsed_data[subject]['chapters']
        for chapter in chapters:
            key_page = chapter['key_page']
            for question in chapter['questions']:
                q_refs = question.get('q_refs', [])
                for ref in q_refs:
                    assert ref['page'] < key_page, \
                        f"{subject} Ch{chapter['number']} Q{question['number']}: page {ref['page']} >= key page {key_page}"


class TestQuestionContent:
    """Test question content and options."""
    
    @pytest.mark.parametrize('subject', SUBJECTS)
    def test_all_questions_have_four_options(self, parsed_data, subject):
        """Verify every question has all four options (A, B, C, D)."""
        chapters = parsed_data[subject]['chapters']
        for chapter in chapters:
            for question in chapter['questions']:
                text = question.get('text', '')
                options = set(re.findall(r'\(([A-D])\)', text))
                assert options == {'A', 'B', 'C', 'D'}, \
                    f"{subject} Ch{chapter['number']} Q{question['number']}: missing options {set(['A','B','C','D']) - options}"
    
    @pytest.mark.parametrize('subject', SUBJECTS)
    def test_questions_have_content(self, parsed_data, subject):
        """Verify questions have non-empty text content."""
        chapters = parsed_data[subject]['chapters']
        for chapter in chapters:
            for question in chapter['questions']:
                text = question.get('text', '').strip()
                assert len(text) > 10, \
                    f"{subject} Ch{chapter['number']} Q{question['number']}: text too short ({len(text)} chars)"


class TestMetadata:
    """Test metadata and verification fields."""
    
    @pytest.mark.parametrize('subject', SUBJECTS)
    def test_parser_version(self, parsed_data, subject):
        """Verify parser version is set."""
        version = parsed_data[subject].get('parser_version')
        assert version == 'chapter50-v1', f"{subject}: unexpected parser version '{version}'"
    
    @pytest.mark.parametrize('subject', SUBJECTS)
    def test_sandbox_flag(self, parsed_data, subject):
        """Verify sandbox isolation flag is set."""
        sandbox = parsed_data[subject].get('sandbox')
        assert sandbox == 'chroot_low_uid_seccomp_resource_limits', \
            f"{subject}: sandbox flag not set correctly"
    
    @pytest.mark.parametrize('subject', SUBJECTS)
    def test_chapter_verification_flags(self, parsed_data, subject):
        """Verify each chapter has verification metadata."""
        chapters = parsed_data[subject]['chapters']
        for chapter in chapters:
            verification = chapter.get('verification', {})
            assert verification.get('questions') == 50
            assert verification.get('keys') == 50
            assert verification.get('options') == 50
            assert verification.get('key_checks_agree') is True
            assert verification.get('source_images') is True


class TestSourceFiles:
    """Test source file integrity."""
    
    @pytest.mark.parametrize('subject', SUBJECTS)
    def test_source_pdf_exists(self, subject):
        """Verify source PDF files exist."""
        pdf_path = DATA_DIR / f'{subject}.pdf'
        assert pdf_path.exists(), f"{subject}.pdf not found"
    
    @pytest.mark.parametrize('subject', SUBJECTS)
    def test_parsed_json_exists(self, subject):
        """Verify parsed JSON files exist."""
        json_path = DATA_DIR / f'{subject}.parsed.json'
        assert json_path.exists(), f"{subject}.parsed.json not found"
    
    @pytest.mark.parametrize('subject', SUBJECTS)
    def test_source_pdf_readable(self, pdf_docs, subject):
        """Verify source PDFs are readable."""
        doc = pdf_docs[subject]
        assert len(doc) > 0, f"{subject}.pdf has no pages"
    
    @pytest.mark.parametrize('subject', SUBJECTS)
    def test_page_count_matches(self, parsed_data, pdf_docs, subject):
        """Verify parsed page count matches actual PDF."""
        expected = len(pdf_docs[subject])
        actual = parsed_data[subject]['pages']
        assert actual == expected, f"{subject}: page count mismatch (parsed={actual}, actual={expected})"


class TestChapterTitles:
    """Test chapter titles and metadata."""
    
    @pytest.mark.parametrize('subject', SUBJECTS)
    def test_all_chapters_have_titles(self, parsed_data, subject):
        """Verify all chapters have non-empty titles."""
        chapters = parsed_data[subject]['chapters']
        for chapter in chapters:
            title = chapter.get('title', '').strip()
            assert len(title) > 0, f"{subject} Ch{chapter['number']}: empty title"
    
    @pytest.mark.parametrize('subject', SUBJECTS)
    def test_chapter_page_ranges(self, parsed_data, subject):
        """Verify chapter page ranges are valid."""
        chapters = parsed_data[subject]['chapters']
        for chapter in chapters:
            start = chapter.get('start_page')
            end = chapter.get('end_page')
            key = chapter.get('key_page')
            
            assert start > 0, f"{subject} Ch{chapter['number']}: invalid start_page"
            assert end >= start, f"{subject} Ch{chapter['number']}: end_page < start_page"
            assert start <= key <= end + 1, f"{subject} Ch{chapter['number']}: key_page out of range"


def test_report_file_exists():
    """Verify the main test report was created."""
    report_path = Path('/app/test_reports/chapter50_recheck.json')
    assert report_path.exists(), "chapter50_recheck.json not found"
    
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    assert report['total_chapters'] == 94
    assert report['passed_chapters'] == 94
    assert report['failed_chapters'] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
