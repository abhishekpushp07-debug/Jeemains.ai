import argparse
import json
from pathlib import Path

from extract_jee_pyq_sources import ROOT, extract


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh', action='store_true')
    args = parser.parse_args()
    files = json.loads((ROOT / 'inventory.json').read_text())['files']
    summary = []
    for file in files:
        try:
            data = extract(file['drive_id'])
            (ROOT / (file['drive_id'] + '.candidates.json')).write_text(json.dumps(data, indent=2))
            summary.append({'file': file, 'metadata': {k: data['metadata'].get(k) for k in ('exam_date', 'year', 'shift')}, 'counts': data['counts'], 'issues': data['issues']})
            print(file['filename'], data['counts'], 'ISSUES', len(data['issues']), flush=True)
        except Exception as exc:
            summary.append({'file': file, 'error': str(exc)})
            print(file['filename'], 'BLOCKED', str(exc), flush=True)
    (ROOT / 'extraction_summary.json').write_text(json.dumps(summary, indent=2))
    print('PAPERS', len(summary), 'UNRESOLVED', sum(bool(r.get('issues') or r.get('error')) for r in summary))
