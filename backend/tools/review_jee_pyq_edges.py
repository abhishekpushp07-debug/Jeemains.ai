import json
import math
from pathlib import Path

import fitz
from PIL import Image, ImageDraw
from extract_jee_pyq_sources import ROOT

OUT = Path('/tmp/jee_pyq_inspect')
rows = []
files = json.loads((ROOT / 'inventory.json').read_text())['files']
for file in files:
    path = ROOT / (file['drive_id'] + '.crop_edge_checks.json')
    if not path.exists():
        continue
    doc = fitz.open(ROOT / (file['drive_id'] + '.pdf'))
    for issue in json.loads(path.read_text()):
        if issue['top_ink'] <= 8:
            continue
        rect = fitz.Rect(issue['rect'])
        page = doc[issue['page'] - 1]
        top = max(0, rect.y0 - page.rect.height * .04)
        bottom = min(page.rect.height, rect.y0 + page.rect.height * .04)
        proof = fitz.Rect(rect.x0, top, rect.x1, bottom)
        scale = 375 / proof.width
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=proof, alpha=False)
        image = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
        image_draw = ImageDraw.Draw(image)
        marker = int((rect.y0 - top) * scale)
        image_draw.line([(0, marker), (image.width, marker)], fill='#de0000', width=2)
        rows.append({'id': len(rows), 'file': file['drive_id'], 'filename': file['filename'], 'issue': issue, 'proof_rect': list(proof), 'image': image})
for batch in range(math.ceil(len(rows) / 12)):
    sheet = Image.new('RGB', (1600, 900), '#eee')
    draw = ImageDraw.Draw(sheet)
    for i, row in enumerate(rows[batch * 12:(batch + 1) * 12]):
        x, y = i % 4 * 400, i // 4 * 300
        issue = row['issue']
        draw.text((x + 4, y + 2), f'#{row["id"]} Q{issue["question"]} {issue["kind"]} p{issue["page"]}', fill='black')
        draw.text((x + 4, y + 16), row['filename'][:50], fill='black')
        row['image'].thumbnail((390, 255))
        sheet.paste(row['image'], (x + 4, y + 35))
    path = OUT / f'crop-boundary-review-{batch + 1}.png'
    sheet.save(path)
    print(path)
(ROOT / 'crop_boundary_candidates.json').write_text(json.dumps([{k: v for k, v in row.items() if k != 'image'} for row in rows], indent=2))
print('SOURCE_CROP_TOP_BOUNDARIES', len(rows))
