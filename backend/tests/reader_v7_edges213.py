"""TEST-ONLY iteration 213 edge probes for READER_VERSION 7 (expected to print OK once fixed)."""
import sys
sys.path.insert(0, '/app/backend')
from tejas.book_reader import read_page


def L(t, y, x=.08):
    return {'text': t, 'rect': [x, y, x + .6, y + .015]}


def page(items):
    return [L(t, .1 + i * .05) for i, t in enumerate(items)]


ctx = {'role': 'solution', 'mock': 'Mock 1', 'last': {'question': 30, 'solution': 0}}
p1 = page(['1. The moles of NaCl are 0.5 so the mass is 29.25 g.', 'Hence option (A).', '2. Solution: a mixture of gases obeys Dalton law.', 'Hence (B).', '3. Using PV = nRT the volume is 22.4 L.', 'Hence (C).'])
p2 = page(['4. Heat released is 57 kJ per mole.', 'Hence (D).', '5. The bond order is 2.5.', 'Hence (A).'])
m1, c1 = read_page(p1, ctx)
m2, c2 = read_page(p2, c1)
s1 = [r.number for r in m1.regions if r.role == 'solution']
s2 = [r.number for r in m2.regions if r.role == 'solution']
print('page1 solutions', s1, 'style', c1.get('solution_style'))
print('page2 solutions', s2, 'issues', m2.issues)
print('RESULT', 'EDGE-BUG: plain solutions dropped' if s1 != [1, 2, 3] or s2 != [4, 5] else 'OK')
# Control: real '1. Answer (A)' style with numbered steps
p3 = page(['1. Answer (A)', '1. First find moles.', '2. Then multiply.', '2. Answer (C)', '1. Balance equation.'])
m3, c3 = read_page(p3, ctx)
print('answer-style solutions', [r.number for r in m3.regions if r.role == 'solution'])

# --- ruled Q01 key tables with fewer than 10 rows per column
from tejas.book_reader import key_cells  # noqa: E402


def table(n):
    body, half = [], (n + 1) // 2
    for i in range(n):
        col, row = divmod(i, half)
        x = .08 + col * .45; y = .15 + row * .03
        body.append({'text': f'Q{i + 1:02d}', 'rect': [x, y, x + .04, y + .012]})
        body.append({'text': 'ABCD'[i % 4], 'rect': [x + .3, y, x + .315, y + .012]})
    return body


for n in (50, 30, 20, 16, 12):
    print(n, 'questions ->', len(key_cells(table(n), 10, ruled='only')), 'pairs read')
