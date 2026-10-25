import argparse
import json
import subprocess
import sys
from pathlib import Path

from extract_jee_pyq_sources import ROOT

parser = argparse.ArgumentParser()
parser.add_argument('--summary-only', action='store_true')
args = parser.parse_args()
out = []
for row in json.loads((ROOT / 'extraction_summary.json').read_text()):
    if row.get('error') or row.get('issues'):
        continue
    fid = row['file']['drive_id']
    path = ROOT / (fid + '.crop_edge_checks.json')
    if not args.summary_only:
        process = subprocess.run([sys.executable, str(Path(__file__).with_name('check_jee_pyq_crop_edges.py')), '--file', fid], capture_output=True, text=True, timeout=60)
        if process.returncode:
            out.append({'file': row['file'], 'error': process.stderr[-300:]})
            continue
    if not path.exists():
        out.append({'file': row['file'], 'error': 'Crop edge checks missing'})
        continue
    flags = json.loads(path.read_text())
    out.append({'file': row['file'], 'issues': flags})
    print(row['file']['filename'], 'CUT_EDGE_FLAGS', len(flags), flush=True)
(ROOT / 'all_crop_edge_summary.json').write_text(json.dumps(out, indent=2))
print('ALL_SOURCE_EDGE_CHECKS_COMPLETE', len(out), flush=True)
