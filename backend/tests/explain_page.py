"""TEST-ONLY: explain one page's reader issues (crossing boxes, option text) for a PDF page."""
import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tejas.book_pdf import inspect  # noqa: E402
from tejas.book_reader import read_page, TOP, BOTTOM, band  # noqa: E402

src, page = sys.argv[1], int(sys.argv[2])
prev = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
d = inspect(src, 'text', page)
m, ctx = read_page(d['lines'], prev, d.get('geometry', []), d.get('images', []))
print('ISSUES', m.issues)
body = [x for x in d['lines'] if not band(x)]
for r in m.regions:
    print('REGION', r.role, r.number, r.subject, r.response_type, r.option_labels, r.checked, [round(v, 3) for v in r.rect])
    if r.role in ('question', 'solution'):
        for box in [x['rect'] for x in body] + [g for g in d.get('geometry', []) if TOP < g[3] and g[1] < BOTTOM]:
            rect = r.rect
            inter = min(rect[2], box[2]) - max(rect[0], box[0]) > .002 and min(rect[3], box[3]) - max(rect[1], box[1]) > .002
            inside = rect[0] - .002 <= box[0] and rect[1] - .002 <= box[1] and box[2] <= rect[2] + .002 and box[3] <= rect[3] + .002
            if inter and not inside:
                print('   CROSS', [round(v, 3) for v in box], next((x['text'][:40] for x in body if x['rect'] == box), 'geometry'))
        if not r.option_labels: print('   TEXT', repr(r.text[-300:]))
print('CTX', {k: v for k, v in ctx.items() if k != 'last'})
