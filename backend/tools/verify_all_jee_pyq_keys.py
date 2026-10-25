import argparse
import json
import subprocess
import sys
from pathlib import Path

from extract_jee_pyq_sources import ROOT

parser = argparse.ArgumentParser()
parser.add_argument('--summary-only', action='store_true')
args = parser.parse_args()
results = []
for row in json.loads((ROOT / 'extraction_summary.json').read_text()):
    if row.get('error') or row.get('issues'):
        continue
    fid = row['file']['drive_id']
    print('CHECKING', row['file']['filename'], flush=True)
    checks_path = ROOT / (fid + '.key_checks.json')
    if not args.summary_only:
        run = subprocess.run([sys.executable, str(Path(__file__).with_name('verify_jee_pyq_keys.py')), '--file', fid], capture_output=True, text=True, timeout=240)
        if run.returncode:
            results.append({'file': row['file'], 'error': run.stderr[-300:]})
            continue
    if not checks_path.exists():
        results.append({'file': row['file'], 'error': 'Independent source key checks missing'})
        continue
    checks = json.loads(checks_path.read_text())
    results.append({'file': row['file'], 'checked': len(checks), 'agreement': sum(c['agreement'] for c in checks), 'flagged': [c for c in checks if not c['agreement']]})
    print('RESULT', len(checks), sum(c['agreement'] for c in checks), flush=True)
(ROOT / 'all_key_check_summary.json').write_text(json.dumps(results, indent=2))
print('INDEPENDENT SOURCE KEY PASSES COMPLETE', len(results), flush=True)
