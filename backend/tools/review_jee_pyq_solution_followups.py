import json
import math
from pathlib import Path

import fitz
from PIL import Image, ImageDraw
from extract_jee_pyq_sources import ROOT, extract

OUT = Path('/tmp/jee_pyq_inspect')
PENDING = {3, 5, 18, 23, 26, 27, 33, 37, 38, 40, 42, 48, 52, 57, 62, 63, 67}
rows = [r for r in json.loads((ROOT / 'solution_label_candidates.json').read_text()) if r['id'] in PENDING]
for batch in range(math.ceil(len(rows) / 8)):
    sheet = Image.new('RGB', (1600, 1000), '#eee')
    draw = ImageDraw.Draw(sheet)
    for index, row in enumerate(rows[batch * 8:(batch + 1) * 8]):
        paper = extract(row['file'])
        q = next(q for q in paper['questions'] if q['number'] == row['number'])
        doc = fitz.open(ROOT / (row['file'] + '.pdf'))
        x, y = (index % 4) * 400, (index // 4) * 500
        draw.text((x + 4, y + 2), f'#{row["id"]} Q{row["number"]} segments{len(q["s_refs"])}', fill='black')
        draw.text((x + 4, y + 16), row['filename'][:50], fill='black')
        images = []
        for ref in q['s_refs']:
            rect = fitz.Rect(ref['rect'])
            rect.y1 = min(rect.y1, rect.y0 + doc[ref['page'] - 1].rect.height * .18)
            scale = 375 / rect.width
            pix = doc[ref['page'] - 1].get_pixmap(matrix=fitz.Matrix(scale, scale), clip=rect, alpha=False)
            images.append(Image.frombytes('RGB', [pix.width, pix.height], pix.samples))
        combined = Image.new('RGB', (375, sum(img.height for img in images) + 8 * len(images)), 'white')
        top = 0
        for img in images:
            combined.paste(img, (0, top))
            top += img.height + 8
        combined.thumbnail((390, 460))
        sheet.paste(combined, (x + 4, y + 34))
    path = OUT / f'solution-followup-{batch + 1}.png'
    sheet.save(path)
    print(path)
