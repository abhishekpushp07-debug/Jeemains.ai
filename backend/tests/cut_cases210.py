"""TEST-ONLY iteration 210: the cutter on made-up pages, straight on the PDF. No database, no storage, no AI.
Run: cd /app/backend && python tests/cut_cases210.py [folder for pictures]
"""
import os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tejas')]
import fitz  # noqa: E402
from book_cutter import cut_region, cut_boxes  # noqa: E402

RESULT = []
ABCD = ['A', 'B', 'C', 'D']
INK = (0, 0, 0)


def say(name, ok, detail=''):
    RESULT.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:600]), flush=True)


def words(page, cut, key):
    w, h = page.rect.width, page.rect.height; r = cut['pieces'][key]['rect']
    text = page.get_text(clip=fitz.Rect(r[0] * w, r[1] * h, r[2] * w, r[3] * h))
    return ' '.join(text.split())


def region(page, y0, y1):
    return [.02, y0 / page.rect.height, .98, y1 / page.rect.height]


def statements(page, y, small=True):
    page.insert_text((40, y), 'Q16. Consider the following statements about motion in a plane:', fontsize=11); y += 18
    for s, t in zip('abcde' if small else 'ABCDE', ['Speed is a scalar.', 'Velocity is a vector.', 'Distance can be negative.', 'Acceleration is a vector.', 'Time is a vector.']):
        page.insert_text((56, y), f'({s}) {t}', fontsize=11); y += 16
    page.insert_text((40, y), 'Choose the correct answer from the options given below:', fontsize=11)
    return y + 22


def unboxed(doc):
    """Statements (a) to (e) inside the question, options (A) to (D) whose own text is made of the same small letters."""
    p = doc.new_page(); y = statements(p, 80)
    for lab, t in zip(ABCD, ['(a), (b) and (c) only', '(b), (c) and (d) only', '(a), (b) and (d) only', '(c), (d) and (e) only']):
        p.insert_text((56, y), f'({lab})', fontsize=11); p.insert_text((80, y), t, fontsize=11); y += 18
    cut = cut_region(p, region(p, 62, y), ABCD)
    got = {k: words(p, cut, k) for k in cut['pieces']}
    say('small a-e in the question, capital A-D options: cut cleanly', cut['status'] == 'ok' and cut['arrangement'] == 'column', (cut['status'], cut['reason']))
    say('  every option holds exactly its own line', [got.get(k) for k in ABCD] == ['(a), (b) and (c) only', '(b), (c) and (d) only', '(a), (b) and (d) only', '(c), (d) and (e) only'], got)
    say('  the question keeps all five statements', all(f'({s})' in got.get('q', '') for s in 'abcde') and 'only' not in got.get('q', ''), got.get('q'))
    # Boxes drawn by hand: running over a neighbour on blank paper is fine, sharing anything printed is not.
    h = p.rect.height; area = region(p, 62, y)
    hand = {k: [v['rect'][0], v['rect'][1] - 1.5 / h, v['rect'][2], v['rect'][3] + 1.5 / h] for k, v in cut['pieces'].items()}
    fixed = cut_boxes(p, area, hand, ABCD)
    lap = sum(hand[a][3] > hand[b][1] for a, b in zip(['q', *ABCD], ABCD))
    say('boxes drawn by hand that overlap only on blank paper: accepted', lap >= 3 and fixed['status'] == 'manual' and not fixed['outside'] and len(fixed['pieces']) == 5, (lap, fixed['status'], fixed['reason'], fixed['outside']))
    say('  every option still holds exactly its own line', [words(p, fixed, k) for k in ABCD] == [got[k] for k in ABCD], {k: words(p, fixed, k) for k in fixed['pieces']})
    over = {**hand, 'A': [hand['A'][0], hand['A'][1], hand['A'][2], (hand['B'][1] + hand['B'][3]) / 2]}
    fixed = cut_boxes(p, area, over, ABCD)
    say('a box drawn by hand over a neighbour\'s print: refused with the reason', fixed['status'] == 'held' and 'chadh' in fixed['reason'] and not fixed['pieces'], (fixed['status'], fixed['reason']))
    # Options two per line, each one starting with a small letter.
    p = doc.new_page(); y = statements(p, 80)
    for row in ((('A', '(a) and (b) only'), ('B', '(b) and (c) only')), (('C', '(c) and (d) only'), ('D', '(d) and (e) only'))):
        for x, (lab, t) in zip((56, 300), row):
            p.insert_text((x, y), f'({lab})', fontsize=11); p.insert_text((x + 24, y), t, fontsize=11)
        y += 18
    cut = cut_region(p, region(p, 62, y), ABCD)
    got = {k: words(p, cut, k) for k in cut['pieces']}
    say('options two per line that start with small letters: cut cleanly', cut['status'] == 'ok' and cut['arrangement'] == 'grid', (cut['status'], cut['reason']))
    say('  every option holds exactly its own text', [got.get(k) for k in ABCD] == ['(a) and (b) only', '(b) and (c) only', '(c) and (d) only', '(d) and (e) only'], got)
    # Capital statements in the question, small-letter options below: the lower set is the options.
    p = doc.new_page(); y = statements(p, 80, small=False)
    for lab, t in zip('abcd', ['A and B only', 'B and C only', 'A, B and D only', 'C, D and E only']):
        p.insert_text((56, y), f'({lab}) {t}', fontsize=11); y += 18
    cut = cut_region(p, region(p, 62, y), ABCD)
    got = {k: words(p, cut, k) for k in cut['pieces']}
    say('capital statements, small-letter options: the lower set is cut as the options', cut['status'] == 'ok' and [got.get(k) for k in ABCD] == ['A and B only', 'B and C only', 'A, B and D only', 'C, D and E only'], (cut['status'], cut['reason'], got))
    # A held cut never offers boxes that mix capital and small labels.
    p = doc.new_page(); y = statements(p, 80)
    p.insert_text((56, y), '(A)', fontsize=11); p.insert_text((80, y), '(a) and (b) only', fontsize=11); p.insert_text((300, y), '(B)', fontsize=11); p.insert_text((324, y), '(b) and (c) only', fontsize=11); y += 18
    p.insert_text((96, y), '(C)', fontsize=11); p.insert_text((120, y), '(c) and (d) only', fontsize=11); p.insert_text((300, y), '(D)', fontsize=11); p.insert_text((324, y), '(d) and (e) only', fontsize=11); y += 18
    cut = cut_region(p, region(p, 62, y), ABCD)
    w, h = p.rect.width, p.rect.height
    draft = {k: ' '.join(p.get_text(clip=fitz.Rect(r[0] * w, r[1] * h, r[2] * w, r[3] * h)).split()) for k, r in (cut.get('draft') or {}).items()}
    say('labels not lined up: held, never guessed', cut['status'] == 'held' and not cut['pieces'], (cut['status'], cut['reason']))
    say('  starting boxes sit on the capital labels, not on small letters', [draft.get(k, '')[:3] for k in ABCD] == ['(A)', '(B)', '(C)', '(D)'], draft)


def box(page, rect, radius=0):
    if radius:
        page.draw_rect(rect, color=(.6, .7, .8), width=.8, radius=radius / min(rect.width, rect.height))
    else:
        page.draw_rect(rect, color=(.6, .7, .8), width=.8)


def boxed(doc, name, cells, radius=0, extra=None, labels='ABCD', inner=True):
    """One question in a ruled box and each option in its own ruled box. cells: the option boxes in the order they are drawn."""
    p = doc.new_page()
    p.insert_text((36, 44), 'Question 7', fontsize=14); p.insert_text((36, 58), 'CH 02 / Kinematics', fontsize=8)
    q = fitz.Rect(32, 66, 563, 200); box(p, q, radius)
    y = 84
    p.insert_text((44, y), 'Consider the following statements:', fontsize=11); y += 16
    for s in 'abcd':
        p.insert_text((52, y), f'({s}) Statement {s} about the particle.', fontsize=11); y += 15
    p.insert_text((44, y), 'The correct statements are:', fontsize=11)
    texts = ['(a) and (b) only', '(b) and (c) only', '(a), (c) and (d) only', '(a), (b), (c) and (d)']
    for (lab, t), r in zip(zip(labels, texts), cells):
        box(p, r, radius)
        if inner:
            p.insert_text((r.x0 + 10, r.y0 + 24), f'({lab})', fontsize=11, fontname='hebo')
        p.insert_text((r.x0 + (34 if inner else 10), r.y0 + 24), t, fontsize=11)
    if extra:
        extra(p)
    bottom = max(r.y1 for r in cells) + 6
    cut = cut_region(p, region(p, 30, bottom), ABCD)
    got = {k: words(p, cut, k) for k in cut['pieces']}
    return p, cut, got, texts, bottom


def boxes(doc):
    stack = [fitz.Rect(32, 214 + 60 * i, 563, 264 + 60 * i) for i in range(4)]
    grid = [fitz.Rect(32 + 270 * (i % 2), 214 + 60 * (i // 2), 292 + 270 * (i % 2), 264 + 60 * (i // 2)) for i in range(4)]
    row = [fitz.Rect(32 + 134 * i, 214, 158 + 134 * i, 264) for i in range(4)]
    for name, cells, radius in (('boxes one below another', stack, 0), ('boxes two in a line', grid, 0), ('boxes four in a line', row, 0), ('rounded boxes one below another', stack, 6), ('rounded boxes two in a line', grid, 6)):
        cells = cells if 'four' not in name else row
        p, cut, got, texts, _ = boxed(doc, name, cells, radius)
        if 'four' in name:
            texts = None
        say(f'{name}: cut along the printed boxes', cut['status'] == 'ok' and cut['arrangement'] == 'boxes', (cut['status'], cut['arrangement'], cut['reason']))
        say('  five printed boxes offered to the fix tool', len(cut['frames']) == 5, cut['frames'])
        if texts:
            say('  each option is its own box, label left out of the picture', [got.get(k) for k in ABCD] == texts or [got.get(k, '').split(') ', 1)[-1] for k in ABCD] == [t.split(') ', 1)[-1] for t in texts], got)
        say('  the question keeps its statements and loses its heading', 'Statement d' in got.get('q', '') and 'Question 7' not in got.get('q', '') and 'CH 02' not in got.get('q', ''), got.get('q'))
        w, h = p.rect.width, p.rect.height
        gap = all(cut['pieces'][k]['rect'][1] * h >= c.y0 and cut['pieces'][k]['rect'][3] * h <= c.y1 and cut['pieces'][k]['rect'][0] * w >= c.x0 and cut['pieces'][k]['rect'][2] * w <= c.x1 for k, c in zip(ABCD, cells)) if cut['pieces'] else False
        say('  every piece lies inside its printed box', gap, {k: [round(v * (w if i % 2 == 0 else h), 1) for i, v in enumerate(cut['pieces'][k]['rect'])] for k in cut['pieces']})
    # Boxes drawn in the order A, C, B, D still go by the label printed inside.
    p, cut, got, texts, _ = boxed(doc, 'shuffled', [grid[0], grid[2], grid[1], grid[3]])
    say('boxes two in a line read down the columns: named by the label inside', cut['status'] == 'ok' and [got.get(k) for k in ABCD] == texts, (cut['status'], cut['reason'], got))
    # Something printed outside every box is not guessed about.
    p, cut, got, texts, bottom = boxed(doc, 'stray', [fitz.Rect(32, 214 + 60 * i, 563, 264 + 60 * i) for i in range(4)], extra=lambda p: p.insert_text((44, 205), 'Note: take g = 10', fontsize=7))
    say('something printed between the boxes: held with the boxes ready', cut['status'] == 'held' and len(cut.get('draft') or {}) == 5 and 'bahar' in cut['reason'], (cut['status'], cut['reason'], cut.get('draft')))
    fixed = cut_boxes(p, region(p, 30, bottom), cut['draft'], ABCD)
    say('  the printed boxes taken by hand: pieces made, the stray mark reported', fixed['status'] == 'manual' and fixed['outside'] and len(fixed['pieces']) == 5, (fixed['status'], fixed['reason'], fixed['outside']))
    # An option box with no label printed in it.
    p, cut, got, texts, bottom = boxed(doc, 'nolabel', [fitz.Rect(32, 214 + 60 * i, 563, 264 + 60 * i) for i in range(4)], inner=False)
    say('option boxes without labels: held, the five boxes offered', cut['status'] == 'held' and len(cut.get('draft') or {}) == 5 and len(cut['frames']) == 5, (cut['status'], cut['reason'], cut.get('draft')))
    fixed = cut_boxes(p, region(p, 30, bottom), cut['draft'], ABCD)
    say('  the printed boxes taken by hand pass every check', fixed['status'] == 'manual' and not fixed['outside'] and not fixed['reason'], (fixed['status'], fixed['reason'], fixed['outside']))
    # Small boxes drawn by hand around small printed boxes.
    p, cut, got, texts, bottom = boxed(doc, 'grid by hand', grid)
    w, h = p.rect.width, p.rect.height
    hand = {'q': [30 / w, 62 / h, 566 / w, 204 / h], **{k: [(c.x0 - 3) / w, (c.y0 - 3) / h, (c.x1 + 3) / w, (c.y1 + 3) / h] for k, c in zip(ABCD, grid)}}
    fixed = cut_boxes(p, region(p, 30, bottom), hand, ABCD)
    say('boxes drawn by hand a little outside the printed boxes: nothing left outside', fixed['status'] == 'manual' and not fixed['outside'], (fixed['status'], fixed['reason'], fixed['outside']))


def main():
    doc = fitz.open()
    unboxed(doc); boxes(doc)
    if len(sys.argv) > 1:
        os.makedirs(sys.argv[1], exist_ok=True)
        for i, page in enumerate(doc):
            page.get_pixmap(matrix=fitz.Matrix(1.2, 1.2), clip=fitz.Rect(0, 0, page.rect.width, 480)).save(f'{sys.argv[1]}/case_{i}.png')
        doc.save(sys.argv[1] + '/cases.pdf')
    print('TOTAL', len(RESULT), 'PASS', sum(RESULT), 'FAIL', len(RESULT) - sum(RESULT))


if __name__ == '__main__':
    main()
