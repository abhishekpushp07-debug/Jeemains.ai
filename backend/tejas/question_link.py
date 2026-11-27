"""One question, one record (pocket C1): where a question was printed from ('AITS Mock 04 / Q68'), its own words without the heading
lines, and the locks that prove two printed copies are the same question: same kind, same answer, words alike.
Plain reading of the words the PDF reader already took; no AI, no database."""
import re, unicodedata
from decimal import Decimal, InvalidOperation
from tejas_core import _SOURCE_LINE, printed_address

WORDS_OK, RUN = 0.80, 5   # two copies under one address: the share of 5-letter runs they must have in common
KIND = {'mcq': 'MCQ', 'integer': 'numerical'}
_ADDRESS = re.compile(r'(?P<series>.*?[^\s\d])[ \t]*0*(?P<mock>\d{1,3})[ \t]*/[ \t]*Q[ \t.]*0*(?P<q>\d{1,3})', re.I)
_NUMBER = re.compile(r'\s*(?:q(?:uestion)?\.?\s*)?\(?\d{1,3}\)?\s*[.):-]?\s*', re.I)
_LEAD = re.compile(r'^\s*(?:q(?:uestion)?\.?\s*)?\(?\d{1,3}\)?\s*[.):-]\s*', re.I)
_PLACE = re.compile(r'\s*[A-Za-z]{2,12}\.?\s*\d{1,3}\s*/\s*\S.*')
_CHAPTER = re.compile(r'\s*ch(?:apter)?\.?\s*\d{1,3}\s*/\s*(\S.*?)\s*', re.I)
_MOCK = re.compile(r'(\d{1,3})\s*$')
_OPTION = re.compile(r'(?m)^[ \t]*\(([A-D])\)[ \t]*')
_DASH = re.compile('[\u2212\u2013\u2014\u2010\u2011]')


def letters(text):
    """Letters and digits only, so line breaks, spacing and punctuation never make two copies look different."""
    return re.sub(r'[^a-z0-9]+', '', unicodedata.normalize('NFKC', text or '').lower())


def value(text):
    """An answer or an option as printed, without spacing; every kind of minus sign is one sign."""
    return re.sub(r'\s+', '', _DASH.sub('-', unicodedata.normalize('NFKC', str(text or '')).lower()))


def address(text):
    """(series, mock, question, as printed) from a question's heading lines, or None. 'AITS Mock 04 / Q68' -> ('aitsmock', 4, 68, …)."""
    line = printed_address(text)
    m = _ADDRESS.fullmatch(line) if line else None
    return (letters(m['series']), int(m['mock']), int(m['q']), line) if m else None


def mock_number(label):
    """The number a paper's own heading gives it ('Mock 04' -> 4), or None."""
    m = _MOCK.search(label or '')
    return int(m[1]) if m else None


def _at(lines):
    return next((i for i, line in enumerate(lines[:4]) if _SOURCE_LINE.fullmatch(line)), None)


def body(text):
    """A question's own words: without its printed number, its address line and the place line under it ('CH 01 / …', 'MOCK 26 / …')."""
    lines = text.split('\n') if isinstance(text, str) else []
    at = _at(lines)
    if at is None:
        # No address line: a printed number on a line of its own, and a place line right under it, are headings too.
        if len(lines) > 1 and _NUMBER.fullmatch(lines[0]):
            return '\n'.join(lines[2:] if len(lines) > 2 and _PLACE.fullmatch(lines[1]) else lines[1:])
        return _LEAD.sub('', text or '', count=1)
    drop = {at} | {i for i in range(at) if _NUMBER.fullmatch(lines[i])}
    if at + 1 < len(lines) and _PLACE.fullmatch(lines[at + 1]):
        drop.add(at + 1)
    return '\n'.join(line for i, line in enumerate(lines) if i not in drop)


def chapter_name(text):
    """The chapter a chapter-wise page prints under the address ('CH 01 / Mole Concept and Stoichiometry'), or ''."""
    lines = text.split('\n') if isinstance(text, str) else []
    at = _at(lines)
    m = _CHAPTER.fullmatch(lines[at + 1]) if at is not None and at + 1 < len(lines) else None
    return m[1][:120] if m else ''


def _run(words):
    """The last (A) (B) (C) (D) printed one below another (a Match-the-list question prints the letters twice; its options come last)."""
    hits = list(_OPTION.finditer(words))
    labels = [m[1] for m in hits]
    for i in range(len(hits) - 4, -1, -1):
        if labels[i:i + 4] == ['A', 'B', 'C', 'D']:
            return hits[i:i + 4]
    return []


def options(words):
    """{A: words, …} of the four options, or {} when they are not printed one below another."""
    run = _run(words)
    ends = [h.start() for h in run[1:]] + [len(words)]
    return {m[1]: words[m.end():e].strip() for m, e in zip(run, ends)}


def read(text, kind, answer):
    """What the locks look at for one printed copy."""
    words, answer = body(text), str(answer or '').strip()
    found = options(words) if kind == 'mcq' else {}
    values = [value(v) for v in found.values()]
    # The question above its options, and the four options in one fixed order: the same question with its options printed in another order reads the same.
    stem = letters(words[:_run(words)[0].start()]) if found else ''
    return {'type': kind or '', 'answer': answer, 'words': words, 'letters': letters(words), 'value': value(found.get(answer, '')),
            'distinct': len(values) == 4 and all(values) and len(set(values)) == 4,
            'stem': stem, 'ordered': stem + ''.join(sorted(letters(v) for v in found.values())) if stem else ''}


def alike(a, b):
    """0..1: how much of their 5-letter runs two copies share (1 = the same letters)."""
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0
    x, y = ({s[i:i + RUN] for i in range(max(1, len(s) - RUN + 1))} for s in (a, b))
    return len(x & y) / len(x | y)


def words_alike(a, b):
    """0..1 for two printed copies. When both print their options one below another, the question above the options must be alike
    by itself (many questions share the very same four options, so those prove nothing), and so must the whole, options in one order."""
    if a['letters'] == b['letters']:
        return 1.0
    if a.get('stem') and b.get('stem'):
        return min(alike(a['stem'], b['stem']), alike(a['ordered'], b['ordered']))
    return alike(a['letters'], b['letters'])


def _number(v):
    try:
        n = Decimal(value(v))
    except InvalidOperation:
        return None
    return n if n.is_finite() else None


def _same_answer(a, b):
    if not a['answer'] or not b['answer']:
        return False
    if a['type'] != 'mcq':
        x, y = _number(a['answer']), _number(b['answer'])
        return x == y if x is not None and y is not None else value(a['answer']) == value(b['answer'])
    if a['distinct'] and b['distinct'] and a['value'] and b['value']:
        return a['value'] == b['value']   # the right option's own words: the options may be printed in another order
    return a['answer'] == b['answer'] and (not a['value'] or not b['value'] or a['value'] == b['value'])


def locks(a, b):
    """None when two printed copies are one question; else {'code', 'say'}: the first lock that stays shut, in the owner's words."""
    if a['type'] != b['type']:
        return {'code': 'type', 'say': f"Pata wahi, par ek {KIND.get(a['type'], a['type'] or '?')} hai aur doosra {KIND.get(b['type'], b['type'] or '?')}."}
    if not _same_answer(a, b):
        if not a['answer'] or not b['answer']:
            say = 'Pata wahi, par ek copy ki key mein jawab abhi nahi hai.'
        elif a['type'] == 'mcq' and a['answer'] == b['answer']:
            say = f"Pata wahi, jawab ka akshar wahi ({a['answer']}), par us option ke shabd alag hain."
        else:
            say = f"Pata wahi, jawab alag: {a['answer'][:24]} aur {b['answer'][:24]}."
        return {'code': 'answer', 'say': say}
    share = words_alike(a, b)
    if share < WORDS_OK:
        return {'code': 'words', 'say': f'Pata wahi, par sawaal ke shabd sirf {round(share * 100)}% milte hain.'}
    return None
