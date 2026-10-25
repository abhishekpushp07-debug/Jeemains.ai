import argparse
import json
import math
from pathlib import Path

import fitz
from PIL import Image, ImageDraw
from extract_jee_pyq_sources import ROOT

OUT = Path('/tmp/jee_pyq_inspect')
parser = argparse.ArgumentParser()
parser.add_argument('--per-paper', type=int, default=3)
args = parser.parse_args()
rows = []
for entry in json.loads((ROOT / 'extraction_summary.json').read_text()):
    if entry.get('issues') or entry.get('error'):
        continue
    fid = entry['file']['drive_id']
    data = json.loads((ROOT / (fid + '.candidates.json')).read_text())
    doc = fitz.open(ROOT / (fid + '.pdf'))
    for number in [1, 26, 51][:args.per_paper]:
        q = next(q for q in data['questions'] if q['number'] == number)
        images = []
        for ref in q['q_refs']:
            rect = fitz.Rect(ref['rect'])
            scale = 370 / rect.width
            pix = doc[ref['page'] - 1].get_pixmap(matrix=fitz.Matrix(scale, scale), clip=rect, alpha=False)
            images.append(Image.frombytes('RGB', [pix.width, pix.height], pix.samples))
        image = Image.new('RGB', (370, sum(i.height for i in images) + len(images) * 6), 'white')
        y = 0
        for i in images:
            image.paste(i, (0, y))
            y += i.height + 6
        rows.append({'filename': entry['file']['filename'], 'question': number, 'image': image})
for batch in range(math.ceil(len(rows) / 12)):
    sheet = Image.new('RGB', (1600, 1200), '#eee')
    draw = ImageDraw.Draw(sheet)
    for i, row in enumerate(rows[batch * 12:(batch + 1) * 12]):
        x, y = i % 4 * 400, i // 4 * 400
        draw.text((x + 4, y + 2), f'Q{row["question"]} {row["filename"]}', fill='black')
        row['image'].thumbnail((390, 370))
        sheet.paste(row['image'], (x + 4, y + 24))
    dest = OUT / f'paper-sample-proof-{batch + 1}.png'
    sheet.save(dest)
    print(dest)
