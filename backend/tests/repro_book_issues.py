"""TEST-ONLY: read a mock-book PDF with the real page reader and count page-level issues (no DB writes)."""
import json, re, sys, time
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tejas.book_pdf import inspect, inspect_many  # noqa: E402
from tejas.book_reader import read_page  # noqa: E402

src, out = sys.argv[1], sys.argv[2]
limit = int(sys.argv[3]) if len(sys.argv) > 3 else 0
pages = inspect(src)['pages']
n = min(pages, limit) if limit else pages
t = time.time(); data = []
for start in range(1, n + 1, 50):
    nums = list(range(start, min(n, start + 49) + 1))
    data.extend(zip(nums, inspect_many(src, [{'action': 'text', 'page': k} for k in nums], 10)))
print('extracted', len(data), 'pages in', round(time.time() - t, 1), 's', flush=True)
context, rows, issues = {}, [], Counter()
for number, d in data:
    if d.get('error'):
        issues['extract error: ' + d['error']] += 1; continue
    mapped, context = read_page(d['lines'], context, d.get('geometry', []))
    rows.append({'number': number, **mapped.model_dump(), 'text': '\n'.join(x['text'] for x in d['lines'])})
    for x in mapped.issues:
        issues[re.sub(r'\d+', '#', x)] += 1
Path(out).write_text(json.dumps(rows))
print('PAGE ISSUES', sum(issues.values()))
for k, v in issues.most_common(30):
    print(v, k)
regions = Counter((r['role'], r['checked']) for p in rows for r in p['regions'])
print('REGIONS', regions.most_common())
