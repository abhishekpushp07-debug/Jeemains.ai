import hashlib
import json
import math
from pathlib import Path

import fitz
from PIL import Image, ImageDraw
from extract_jee_pyq_sources import ROOT

OUT = Path('/tmp/jee_pyq_inspect')
files = json.loads((ROOT / 'inventory.json').read_text())['files']
rows = []
for file in files:
    data_path = ROOT / (file['drive_id'] + '.candidates.json')
    if not data_path.exists():
        continue
    data = json.loads(data_path.read_text())
    if data['issues']:
        continue
    for q in data['questions']:
        if len(q.get('q_refs', [])) > 1 or len(q.get('s_refs', [])) > 1:
            rows.append({'file': file, 'number': q['number'], 'q_segments': len(q['q_refs']), 's_segments': len(q['s_refs'])})
(ROOT / 'continuation_manifest.json').write_text(json.dumps(rows, indent=2))
print('MULTI_SEGMENT_QUESTIONS', len(rows), 'PAPERS', len({r['file']['drive_id'] for r in rows}))
