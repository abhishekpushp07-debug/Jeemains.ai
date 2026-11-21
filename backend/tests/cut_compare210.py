"""TEST-ONLY iteration 210: compare two cut_scan209 output folders question by question.
Run: python tests/cut_compare210.py <before_dir> <after_dir>
"""
import glob, json, sys


def load(folder):
    rows = {}
    for f in glob.glob(folder + '/Chapter_*.json'):
        for r in json.load(open(f))['rows']:
            rows[(r['chapter'], r['n'])] = r
    return rows


def near(a, b, tol):
    return len(a) == len(b) and all(abs(x - y) <= tol for x, y in zip(a, b))


a, b = load(sys.argv[1]), load(sys.argv[2])
gone, new = sorted(set(a) - set(b)), sorted(set(b) - set(a))
status, region, parts, same = [], [], [], 0
for k in sorted(set(a) & set(b)):
    x, y = a[k], b[k]
    if (x['status'], x['type'], x['key']) != (y['status'], y['type'], y['key']):
        status.append((k, x['status'], y['status'], x['type'], y['type'], x['key'], y['key'], y['reason'][:70]))
    elif len(x['parts']) != len(y['parts']) or any(p['part'] != q['part'] or p['page'] != q['page'] or not near(p['rect'], q['rect'], .0012) for p, q in zip(x['parts'], y['parts'])):
        parts.append(k)
    elif len(x['regions']) != len(y['regions']) or any(not near(p['rect'], q['rect'], .0005) for p, q in zip(x['regions'], y['regions'])):
        region.append(k)
    else:
        same += 1
print(f'before {len(a)} after {len(b)} same {same} | gone {len(gone)} new {len(new)} | status/type/key changed {len(status)} | pieces moved {len(parts)} | only region moved {len(region)}')
print(' gone', gone[:12]); print(' new', new[:12])
for s in status[:25]: print(' changed', s)
print(' pieces moved', parts[:25]); print(' region moved', region[:12])
held = [(k, r['reason'][:90]) for k, r in sorted(b.items()) if r['status'] == 'held']
odd = [(k, r['type'], r['status'], r['arrangement'], r['key']) for k, r in sorted(b.items()) if r['type'] == 'unresolved' or len(r['key']) != 1 or not r['checked']]
print(' held now', held[:20]); print(' odd now', odd[:20])
