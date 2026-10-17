"""Build traceable metric definitions from the user's already-extracted authoritative guide."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
source = ROOT / 'docs/source_guides/04_Results_60_Analyses_and_Question_Insights.pdf.txt'
text = source.read_text()
blocks = re.findall(r'^A(\d{2}) / ([^\n]+)\n(.*?)(?=^A\d{2} / |^ACCEPTANCE / PRECAUTIONS|\Z)', text, re.M | re.S)
metrics = []
for n, title, body in blocks:
    body = ' '.join(body.split())
    fields = {}
    for label, stop in [('Inputs','Formula'),('Formula','Evidence'),('Evidence','Action'),('Action','Limit')]:
        part = re.search(label + r':\s*(.*?)\s*' + stop + ':', body)
        if not part: raise ValueError(f'Missing {label} in A{n}')
        fields[label.lower()] = part.group(1)
    fields['limitation'] = body.split('Limit:',1)[1].strip()
    metrics.append({'metric_id':'A'+n, 'name':title, **fields})
assert len(metrics) == 60 and [m['metric_id'] for m in metrics] == [f'A{n:02d}' for n in range(1,61)]
target = ROOT / 'backend/tejas/analytics_registry.json'
target.write_text(json.dumps({'registry_version':'guide04-v1.0', 'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'metrics':metrics},ensure_ascii=False,indent=2)+'\n')
print('Generated 60 guide-aligned definitions; source hash retained.')
