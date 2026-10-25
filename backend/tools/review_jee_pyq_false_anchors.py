import json
import math
from pathlib import Path

import fitz
from PIL import Image, ImageDraw
from extract_jee_pyq_sources import ROOT, extract, position

OUT = Path('/tmp/jee_pyq_inspect')
files = json.loads((ROOT / 'inventory.json').read_text())['files']
rows = []
for file in files:
    try:
        paper = extract(file['drive_id'])
    except Exception:
        continue
    qs = paper['questions']
    seen = set()
    previous = 0
    doc = fitz.open(ROOT / (file['drive_id'] + '.pdf'))
    for q in qs:
        number = q['number']
        if number in seen or number < previous:
            a = q['anchor']
            width = doc[a['page'] - 1].rect.width
            left = width * (.075 if a['column'] == 0 else .505)
            rect = fitz.Rect(left - 4, max(0, a['rect'][1] - 8), left + 150, a['rect'][3] + 10)
            pix = doc[a['page'] - 1].get_pixmap(matrix=fitz.Matrix(2.5, 2.5), clip=rect, alpha=False)
            image = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
            rows.append({'id': len(rows), 'file': file['drive_id'], 'filename': file['filename'], 'number': number, 'anchor': a, 'proof_rect': list(rect), 'image': image})
        else:
            previous = number
        seen.add(number)
for batch in range(math.ceil(len(rows) / 24)):
    sheet = Image.new('RGB', (1600, 1160), '#eee')
    draw = ImageDraw.Draw(sheet)
    for i, row in enumerate(rows[batch * 24:(batch + 1) * 24]):
        x, y = (i % 4) * 400, (i // 4) * 145
        draw.text((x + 3, y + 2), f'#{row["id"]} parsedQ{row["number"]} page{row["anchor"]["page"]}', fill='black')
        draw.text((x + 3, y + 15), row['filename'][:50], fill='black')
        row['image'].thumbnail((390, 108))
        sheet.paste(row['image'], (x + 4, y + 34))
    path = OUT / f'false-anchor-review-{batch + 1}.png'
    sheet.save(path)
    print(path)
(ROOT / 'false_anchor_candidates.json').write_text(json.dumps([{k: v for k, v in row.items() if k != 'image'} for row in rows], indent=2))
print('OUT_OF_SEQUENCE_REGIONS', len(rows))
