"""TEST-ONLY iteration 190: bracketed key-table cells '(B)' and a page with key table above + '<Chapter> – Solutions' heading below.
Pure reader checks on synthetic pages (no DB). Run: cd /app/backend && python tests/key_table_split190.py
"""
import sys
sys.path.insert(0, '/app/backend')
import fitz  # noqa: E402
from tejas.book_pdf import inspect  # noqa: E402
from tejas.book_reader import read_page, key_cells  # noqa: E402
from tejas.chapter_reader import named_role, name_heading, find  # noqa: E402

R = []


def check(n, ok, d=''):
    R.append(ok); print(('PASS ' if ok else 'FAIL ') + n + ('' if ok else ' :: ' + str(d)[:300]))


KEYS = 'BDACBDACBDACBDACBDAC'


def page(split=True, bracket=True):
    doc = fitz.open(); p = doc.new_page()
    p.insert_text((40, 60), 'Answer key \u2013 Complex Numbers', fontsize=13)
    y = 95
    for row in range(10):
        for col in range(2):
            n = row + 1 + col * 10
            k = KEYS[n - 1]
            p.insert_text((60 + col * 200, y), str(n), fontsize=11)
            p.insert_text((100 + col * 200, y), f'({k})' if bracket else k, fontsize=11)
        y += 18
    if split:
        y += 20
        p.insert_text((40, y), 'Complex Numbers \u2013 Solutions', fontsize=13); y += 30
        for n in (1, 2):
            p.insert_text((40, y), f'{n}. Answer: ({KEYS[n-1]})', fontsize=11); y += 18
            p.insert_text((40, y), 'Working: compute the modulus and simplify the result step by step.', fontsize=11); y += 30
    path = f'/tmp/key190_{int(split)}{int(bracket)}.pdf'; doc.save(path); doc.close()
    return inspect(path, 'text', 1)


ctx = {'chapters': True, 'plan': False, 'chapter_info': {'Complex Numbers': {'title': 'Complex Numbers'}}, 'mock': 'Complex Numbers', 'role': 'question'}
check('named_role answer key', named_role('Answer key \u2013 Complex Numbers') == ('key', 'Complex Numbers'), named_role('Answer key \u2013 Complex Numbers'))
check('named_role solutions tail', named_role('Complex Numbers \u2013 Solutions') == ('solution', 'Complex Numbers'), named_role('Complex Numbers \u2013 Solutions'))
check('name_heading rejects brackets', name_heading('Differentiability)') == '' and name_heading('(Limits)') == '')
check('name_heading plain name', name_heading('Complex Numbers') == 'Complex Numbers')

d = page(split=False)
pairs = key_cells([x for x in d['lines']])
m = {q: k for q, k, _ in pairs}
check('bracketed key table: 20 pairs', len(pairs) == 20, pairs[:4])
check('bracketed key table: Q->letter, not 1->11', all(m.get(n) == KEYS[n - 1] for n in range(1, 21)), m)
mapped, _ = read_page(d['lines'], ctx, d.get('geometry', []), d.get('images', []))
keys = {r.number: r.answer for r in mapped.regions if r.role == 'key'}
check('key page read as keys', len(keys) == 20 and keys.get(1) == 'B' and keys.get(11) == KEYS[10], keys)

d = page(split=True)
mapped, c2 = read_page(d['lines'], ctx, d.get('geometry', []), d.get('images', []))
keys = {r.number: r.answer for r in mapped.regions if r.role == 'key'}
sols = {r.number: r.answer for r in mapped.regions if r.role == 'solution'}
check('split page: keys above', len(keys) == 20 and keys.get(1) == 'B', keys)
check('split page: solutions 1, 2 below', sorted(sols) == [1, 2] and sols.get(1) == 'B' and sols.get(2) == 'D', [(r.role, r.number, r.answer) for r in mapped.regions])
check('split page: context role solution afterwards', c2.get('role') == 'solution', c2.get('role'))
check('split page: no issues', not mapped.issues, mapped.issues)

d = page(split=False, bracket=False)
check('plain letter key still pairs', len(key_cells(d['lines'])) == 20)
print(f'{sum(R)}/{len(R)} passed'); sys.exit(0 if all(R) else 1)
