"""TEST-ONLY: writes paper PDFs + combined xlsx into /tmp/uibridge173 for the wizard browser regression (no DB access)."""
import io
import fitz
from openpyxl import Workbook

OUT = '/tmp/uibridge173'


def page(lines):
    d = fitz.open(); p = d.new_page(); y = 60
    for line in lines:
        p.insert_text((50, y), line, fontsize=11); y += 18
    return d.tobytes()


q = ['BITSAT Practice Paper', 'Duration: 180 minutes', 'Physics']
s = ['Physics']
for i in range(1, 4):
    q += [f'Q{i}. TEST_UI question {i} about force?', '(A) Newton', '(B) Joule', '(C) Watt', '(D) Pascal', '']
    s += [f'Q{i}. Answer: A', f'TEST_UI solution {i}.', '']
open(OUT + '/TEST_UI_paper_q.pdf', 'wb').write(page(q))
open(OUT + '/TEST_UI_paper_s.pdf', 'wb').write(page(s))
head = ['question_id', 'question_no', 'subject', 'question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option', 'type', 'topic', 'difficulty', 'exam', 'duration_minutes', 'solution_text']
wb = Workbook(); ws = wb.active; ws.title = 'Questions'; ws.append(head)
for i in range(1, 4):
    ws.append([f'TEST-u{i}', i, 'Physics', f'TEST_UI excel q{i}?', 'Newton', 'Joule', 'Watt', 'Pascal', 'A', 'mcq', 'Units', 'Easy', 'BITSAT', 180, 'Newtons.'])
b = io.BytesIO(); wb.save(b); open(OUT + '/TEST_UI_excel.xlsx', 'wb').write(b.getvalue())
print('ok')
