"""TEST-ONLY iteration 211: after the rollback, compare a fresh scan with the scan made by the lost engine (21 Nov, 09:20 UTC).
Run: python tests/cut_compare_restore211.py <new_dir> <old_dir>   (both made by tests/cut_scan209.py scan)
"""
import json, sys
from pathlib import Path


def rows(folder):
    out = {}
    for f in Path(folder).glob('Chapter_*.json'):
        for r in json.load(open(f))['rows']:
            out[(r['chapter'], r['n'])] = r
    return out


def same(a, b):
    keep = lambda r: (r['status'], r['type'], r['labels'], r['key'], r['arrangement'], r['reason'], [(p['part'], p['page'], p['rect'], p.get('erase')) for p in r['parts']], r['draft'])
    return keep(a) == keep(b)


new, old = rows(sys.argv[1]), rows(sys.argv[2])
diff = [k for k in sorted(set(new) | set(old)) if k not in new or k not in old or not same(new[k], old[k])]
print('questions new', len(new), 'old', len(old), 'different', len(diff), diff[:10])
