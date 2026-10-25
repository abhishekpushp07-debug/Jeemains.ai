import json
import math
from pathlib import Path

import fitz
from PIL import Image, ImageDraw
from extract_jee_pyq_sources import ROOT, extract

OUT = Path('/tmp/jee_pyq_inspect')
rows = []
for file in json.loads((ROOT / 'inventory.json').read_text())['files']:
    try:
        paper = extract(file['drive_id'])
    except Exception:
        continue
    doc = fitz.open(ROOT / (file['drive_id'] + '.pdf'))
    for q in paper['questions']:
        if 'Supplied solution label needs visual review' not in q['issues'] or not q.get('s_refs'):
            continue
        ref = q['s_refs'][0]
        rect = fitz.Rect(ref['rect'])
        rect.y1 = min(rect.y1, rect.y0 + doc[ref['page'] - 1].rect.height * .18)
        scale = 370 / rect.width
        pix = doc[ref['page'] - 1].get_pixmap(matrix=fitz.Matrix(scale, scale), clip=rect, alpha=False)
        image = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
        rows.append({'id': len(rows), 'file': file['drive_id'], 'source_sha256': paper['source_sha256'], 'filename': file['filename'], 'number': q['number'], 'ref': ref, 'image': image})
for batch in range(math.ceil(len(rows) / 12)):
    sheet = Image.new('RGB', (1600, 900), '#eee')
    draw = ImageDraw.Draw(sheet)
    for i, row in enumerate(rows[batch * 12:(batch + 1) * 12]):
        x, y = (i % 4) * 400, (i // 4) * 300
        draw.text((x + 4, y + 2), f'#{row["id"]} Q{row["number"]} sourcepage{row["ref"]["page"]}', fill='black')
        draw.text((x + 4, y + 16), row['filename'][:50], fill='black')
        row['image'].thumbnail((390, 260))
        sheet.paste(row['image'], (x + 4, y + 34))
    dest = OUT / f'solution-label-review-{batch + 1}.png'
    sheet.save(dest)
    print(dest)
(ROOT / 'solution_label_candidates.json').write_text(json.dumps([{k: v for k, v in r.items() if k != 'image'} for r in rows], indent=2))
print('SOLUTION_LABELS_NEED_VISUAL_PROOF', len(rows))
