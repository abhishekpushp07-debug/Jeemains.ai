"""TEST-ONLY iteration 211: the faster PDF reading (letters only, page read once) must give exactly what the old reading gave.
Compares the page reader's input (text, boxes, pictures) on every page, and crop / piece pictures pixel for pixel.
Run: cd /app/backend && python tests/speed_same211.py <pdf> [every_nth_page]
Old code: /root/pdfengine/old (book_cutter_old.py = the 09:20 recovered cutter, worker_old.py = the worker before 2026-11-21 speed work).
"""
import sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tejas'), '/root/pdfengine/old']
import fitz  # noqa: E402
import book_pdf_worker as new  # noqa: E402
import worker_old as old  # noqa: E402


def main(pdf, step):
    doc = fitz.open(pdf); bad = []; n = 0; t_old = t_new = 0
    for p in range(1, len(doc) + 1, step):
        t = time.time(); a = old.handle(doc, {'action': 'text', 'page': p}); t_old += time.time() - t
        t = time.time(); b = new.handle(doc, {'action': 'text', 'page': p}); t_new += time.time() - t
        n += 1
        if a != b:
            bad.append(('text', p))
        for action, extra in (('crop', {}), ('piece', {'scale': 2, 'erase': [[.1, .1, .2, .12]]})):
            item = {'action': action, 'page': p, 'rect': [.05, .1, .95, .6], **extra}
            if old.handle(doc, item)['image'] != new.handle(doc, item)['image']:
                bad.append((action, p))
    print(f'pages {n} different {len(bad)} {bad[:10]} old {t_old:.1f}s new {t_new:.1f}s')


if __name__ == '__main__':
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1)
