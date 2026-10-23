"""Parse the TEJAS200 BITSAT 50 full-mock PDF into source-region questions with two independent key extractions."""
import re
import fitz

SECTIONS = {'Physics', 'Chemistry', 'English Proficiency', 'Logical Reasoning', 'Mathematics'}
MAIN, BONUS = 130, 12
X0, X1, TOP, BOTTOM = 45.0, 550.0, 42.0, 796.0


def mock_of(page):
    for b in page.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            t = ''.join(s['text'] for s in l['spans']).strip()
            m = re.fullmatch(r'Mock (\d{2})', t)
            if m and l['bbox'][1] < 40:
                return int(m.group(1))
    return None


def lines(page):
    out = []
    for b in page.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            t = ''.join(s['text'] for s in l['spans']).strip()
            if t and TOP < l['bbox'][1] and l['bbox'][3] < BOTTOM:
                out.append((l, t))
    return out


def content_boxes(page):
    boxes = [fitz.Rect(l['bbox']) for l, _ in lines(page)]
    boxes += [fitz.Rect(b['bbox']) for b in page.get_text('dict')['blocks'] if b['type'] == 1]
    boxes += [d['rect'] for d in page.get_drawings() if d['rect'].y0 > TOP and d['rect'].y1 < BOTTOM]
    return boxes


def markers(page, expected):
    """Ordered (y, kind, value) markers: question starts, section headings, passages, bonus heading."""
    found, floor = [], TOP
    for l, t in sorted(lines(page), key=lambda item: item[0]['bbox'][1]):
        s = l['spans'][0]
        bold = 'Bold' in s['font']
        x, y = l['bbox'][0], l['bbox'][1]
        if bold and s['size'] > 14 and t in SECTIONS:
            found.append((y, 'section', t))
            floor = l['bbox'][3]
        elif bold and s['size'] > 15 and t.lower().startswith('optional bonus'):
            found.append((y, 'bonus', t))
            floor = l['bbox'][3]
        elif bold and t.lower().startswith('read the passage'):
            nums = [int(n) for n in re.findall(r'\d+', t)]
            rng = list(range(nums[0], nums[-1] + 1)) if '–' in t or '-' in t or 'to' in t else nums
            found.append((y, 'passage', rng))
        elif bold and x < 62:
            m = re.match(r'(\d{1,3})\.(\s|$)', t)
            if m and int(m.group(1)) == expected[0]:
                # Superscripts and stacked fractions on the first row sit above the bold number; never cross a heading.
                found.append((max(y - 9, floor + 3), 'question', expected[0]))
                expected[0] += 1
    return sorted(found, key=lambda f: f[0])


def region(page_no, page, y0, y1):
    """Tight region from y0 to y1 limited to real content; None if empty."""
    boxes = [b for b in content_boxes(page) if b.y1 > y0 + 1 and b.y0 < y1 - 1]
    if not boxes:
        return None
    bottom = min(y1, max(b.y1 for b in boxes) + 4)
    top = max(TOP, y0 - 2)
    return {'page': page_no, 'rect': [X0, round(top, 2), X1, round(min(bottom, BOTTOM), 2)]}


def parse_mocks(doc, key_start):
    mocks = {}
    for i in range(1, key_start - 1):
        n = mock_of(doc[i])
        if n:
            mocks.setdefault(n, []).append(i)
    return {n: (pages[0], pages[-1]) for n, pages in mocks.items()}


def parse_questions(doc, first, last):
    """Return ordered question dicts with refs relative to the extracted mock PDF (1-based)."""
    expected = [1]
    questions, passages, current, section, in_bonus = [], [], None, None, False
    for i in range(first, last + 1):
        page, local = doc[i], i - first + 1
        cursor = TOP
        for y, kind, value in markers(page, expected) + [(BOTTOM, 'end', None)]:
            if current is not None:
                ref = region(local, page, cursor, y)
                if ref:
                    current['q_refs'].append(ref)
            if kind == 'end':
                break
            cursor = y
            if kind == 'question':
                current = {'number': value, 'section': section, 'bonus': in_bonus, 'q_refs': []}
                questions.append(current)
            elif kind == 'passage':
                current = {'targets': value, 'q_refs': []}
                passages.append(current)
            else:
                current = None
                if kind == 'section':
                    section = value
                else:
                    in_bonus = True
    issues = []
    by_number = {q['number']: q for q in questions}
    for p in passages:
        for n in p['targets']:
            if n not in by_number:
                issues.append(f'Reading passage for Q{n} has no matching question.')
            else:
                by_number[n]['q_refs'] = p['q_refs'] + by_number[n]['q_refs']
    return questions, issues


def keys_by_layout(text):
    """Extraction 1: plain text Q/Key token pairs per mock."""
    result = {}
    blocks = re.split(r'BITSAT Mock (\d{2})\s+Answer key', text)
    for n, body in zip(blocks[1::2], blocks[2::2]):
        result[int(n)] = {int(q): k for q, k in re.findall(r'(?<!\d)(\d{1,3})\s+([ABCD])(?![A-Za-z])', body)}
    return result


def keys_by_position(doc, key_start):
    """Extraction 2: geometric word pairing (number word followed on the same row by a single A-D word)."""
    result, mock = {}, None
    for i in range(key_start - 1, len(doc)):
        words = doc[i].get_text('words')
        heads = [(w[1], int(re.search(r'\d{2}', w[4]).group())) for j, w in enumerate(words)
                 if j > 0 and words[j - 1][4] == 'Mock' and words[j - 2][4] == 'BITSAT' and re.fullmatch(r'\d{2}', w[4])]
        rows = sorted(words, key=lambda w: (round(w[1]), w[0]))
        for w in rows:
            if heads and any(abs(w[1] - hy) < 2 for hy, _ in heads):
                mock = next(n for hy, n in heads if abs(w[1] - hy) < 2)
                continue
            if w[1] < 40 or w[3] > BOTTOM:
                continue
            if mock is None or not re.fullmatch(r'\d{1,3}', w[4]):
                continue
            same = [v for v in words if abs(v[1] - w[1]) < 3 and v[0] > w[2] and re.fullmatch(r'[ABCD]', v[4])]
            if same:
                nearest = min(same, key=lambda v: v[0])
                nums_between = [v for v in words if abs(v[1] - w[1]) < 3 and w[2] < v[0] < nearest[0] and re.fullmatch(r'\d{1,3}', v[4])]
                if not nums_between:
                    result.setdefault(mock, {})[int(w[4])] = nearest[4]
    return result
