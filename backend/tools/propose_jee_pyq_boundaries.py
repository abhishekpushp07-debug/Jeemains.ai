import json
from pathlib import Path

import fitz
import numpy as np
from extract_jee_pyq_sources import ROOT

proposals = []
for file in json.loads((ROOT / 'inventory.json').read_text())['files']:
    path = ROOT / (file['drive_id'] + '.crop_edge_checks.json')
    if not path.exists():
        continue
    doc = fitz.open(ROOT / (file['drive_id'] + '.pdf'))
    for issue in json.loads(path.read_text()):
        if issue['top_ink'] <= 8 or issue['kind'] != 'q_refs' or issue['index'] != 0:
            continue
        page = doc[issue['page'] - 1]
        rect = fitz.Rect(issue['rect'])
        scale = min(3, 1200 / rect.width)
        low = max(0, rect.y0 - page.rect.height * .07)
        region = fitz.Rect(rect.x0, low, rect.x1, rect.y0 + page.rect.height * .003)
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=region, colorspace=fitz.csGRAY)
        image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
        white = (image[:, 12:-12] < 170).sum(axis=1) <= 2
        start = min(len(white) - 1, int((rect.y0 - low) * scale))
        run = 0
        minimum = max(3, int(page.rect.height * .003 * scale))
        proposal = None
        for y in range(start, -1, -1):
            run = run + 1 if white[y] else 0
            if run >= minimum:
                proposal = round(low + (y + run / 2) / scale, 3)
                break
        proposals.append({'file': file, 'question': issue['question'], 'page': issue['page'], 'old': issue['rect'], 'proposed_top': proposal,
                          'anchor_top': round(proposal + 2, 3) if proposal is not None else None,
                          'method': 'expand to nearest continuous blank band before the clipped original content; pending visual approval'})
(ROOT / 'boundary_proposals.json').write_text(json.dumps(proposals, indent=2))
print('SOURCE_BOUNDARY_PROPOSALS', len(proposals), 'UNRESOLVED', sum(r['proposed_top'] is None for r in proposals))
print(json.dumps(proposals, indent=2))
