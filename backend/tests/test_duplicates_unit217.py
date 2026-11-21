"""TEST-ONLY (iteration 217): pure unit checks of tejas.duplicates fingerprint/matches. Run: cd /app/backend && python -m pytest tests/test_duplicates_unit217.py -p no:cacheprovider"""
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')  # import only; no database access in these tests
from tejas.duplicates import fingerprint, matches  # noqa: E402

LONG = 'A block of mass 2 kg slides down a rough incline of angle 30 degrees. Find its acceleration.'


def it(i, qs):
    return {'id': i, 'title': i, 'questions': [{'id': f'{i}{n}', 'number': n, 'subject': s, 'text': t} for n, s, t in qs]}


def test_number_and_punctuation_ignored():
    assert fingerprint('Q1. ' + LONG) == fingerprint('12) ' + LONG.upper().replace('.', '')) is not None


def test_short_text_never_counts():
    assert fingerprint('Q1. Find x if x+2=4') is None


def test_same_subject_any_chapter_flagged():
    out = matches([it('a', [(1, 'Physics', LONG)]), it('b', [(4, 'physics ', 'Q4. ' + LONG)])])
    assert set(out) == {'a', 'b'} and out['a'][0]['matches'][0]['id'] == 'b'


def test_different_subject_not_flagged():
    assert matches([it('a', [(1, 'Physics', LONG)]), it('b', [(1, 'Chemistry', LONG)])]) == {}


def test_same_paper_twice_flagged_once_each():
    out = matches([it('a', [(1, 'Physics', LONG), (2, 'Physics', LONG)])])
    assert len(out['a']) == 2


def test_leading_number_in_question_body():
    # A question that itself starts with a number: only the printed number should be stripped, so 100 g vs 200 g must differ
    a = fingerprint('Q5. 100 g of water at 20 degrees is mixed with ice; find the final temperature of the mixture')
    b = fingerprint('Q5. 200 g of water at 20 degrees is mixed with ice; find the final temperature of the mixture')
    assert a != b
