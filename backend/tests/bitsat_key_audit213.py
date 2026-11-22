"""TEST-ONLY: compare harness AUDIT answers against the printed 'Q01 A' key pages (via bookmarks), crop heights, solution regions."""
import json, re, sys
from collections import defaultdict, Counter
import fitz
pdf, audit = sys.argv[1], sys.argv[2]
doc = fitz.open(pdf)
toc = doc.get_toc()
rows = json.load(open(audit))
by = defaultdict(dict)
for r in rows: by[r['mock']][r['n']] = r
# key pages from bookmarks
keypages = [(t, p) for lvl, t, p in toc if re.search(r'answer\s*key', t, re.I)]
print('toc sample', toc[:4], 'key bookmarks', len(keypages))
chapters = sorted(by, key=lambda s: int(re.sub(r'\D', '', s) or 0))
mism = 0; checked = 0; nosol = 0; short = Counter()
for i, ch in enumerate(chapters):
    printed = {}
    if i < len(keypages):
        txt = doc[keypages[i][1] - 1].get_text()
        for q, a in re.findall(r'Q\.?\s*(\d{1,3})\s+\(?([A-D])\)?\b', txt): printed[int(q)] = a
    got = {n: r['answer'] for n, r in by[ch].items()}
    bad = [(n, printed.get(n), got.get(n)) for n in sorted(got) if printed.get(n) != (got.get(n) if not isinstance(got.get(n), list) else ''.join(got.get(n)))]
    checked += len(got); mism += len(bad)
    for n, r in by[ch].items():
        if not r['s']: nosol += 1
        h = max(g['rect'][3] - g['rect'][1] for g in r['q'])
        if h < .15: short[ch] += 1
    print(ch, 'questions', len(got), 'printed keys', len(printed), 'mismatches', len(bad), bad[:5], 'types', Counter(r['type'] for r in by[ch].values()))
print('TOTAL checked', checked, 'mismatch', mism, 'no solution region', nosol, 'short crops(<.15)', dict(short))
for ch in sys.argv[3:]:
    print(ch, 'first 5', [(n, by[ch][n]['answer'], round(max(g['rect'][3]-g['rect'][1] for g in by[ch][n]['q']), 3)) for n in sorted(by[ch])[:5]])
