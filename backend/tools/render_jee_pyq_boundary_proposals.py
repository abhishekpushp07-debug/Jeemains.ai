import json
import math
from pathlib import Path

import fitz
from PIL import Image, ImageDraw
from extract_jee_pyq_sources import ROOT

OUT = Path('/tmp/jee_pyq_inspect')
rows = json.loads((ROOT / 'boundary_proposals.json').read_text())
for batch in range(math.ceil(len(rows) / 12)):
    sheet = Image.new('RGB', (1600, 1000), '#eee')
    draw = ImageDraw.Draw(sheet)
    for i, row in enumerate(rows[batch * 12:(batch + 1) * 12]):
        if row['proposed_top'] is None:
            continue
        doc = fitz.open(ROOT / (row['file']['drive_id'] + '.pdf'))
        page = doc[row['page'] - 1]
        rect = fitz.Rect(row['old'])
        top = max(0, row['proposed_top'] - page.rect.height * .018)
        proof = fitz.Rect(rect.x0, top, rect.x1, min(page.rect.height, rect.y0 + page.rect.height * .045))
        scale = 375 / proof.width
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=proof, alpha=False)
        image = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
        pen = ImageDraw.Draw(image)
        for boundary, color in ((rect.y0, '#d90000'), (row['proposed_top'], '#009447')):
            y = int((boundary - top) * scale)
            pen.line([(0, y), (image.width, y)], fill=color, width=2)
        x, y = i % 4 * 400, i // 4 * 330
        draw.text((x + 4, y + 2), f'#{batch * 12 + i} Q{row["question"]} page{row["page"]}', fill='black')
        draw.text((x + 4, y + 16), row['file']['filename'][:50], fill='black')
        image.thumbnail((390, 290))
        sheet.paste(image, (x + 4, y + 35))
    path = OUT / f'proposed-boundary-proof-{batch + 1}.png'
    sheet.save(path)
    print(path)
