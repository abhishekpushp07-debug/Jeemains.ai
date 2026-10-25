import argparse
import hashlib
import json
import math
import re
from pathlib import Path

import fitz
from PIL import Image, ImageDraw
from extract_jee_pyq_sources import ROOT, labels, load_pages, position
from repair_jee_pyq_anchors import increasing

OUT = Path('/tmp/jee_pyq_inspect')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file')
    args = parser.parse_args()
    files = json.loads((ROOT / 'inventory.json').read_text())['files']
    rows = []
    for file in files:
        fid = file['drive_id']
        if args.file and fid != args.file:
            continue
        pages = load_pages(fid, 6)
        if not pages or len(pages) != pages[0].get('total_pages'):
            continue
        anchors = labels(pages)[0]
        chain = increasing(anchors)
        ordered = [{'number': 0, 'page': 1, 'column': 0, 'rect': [0, 0, 0, 0]}, *chain,
                   {'number': 76, 'page': pages[-1]['page'], 'column': 1, 'rect': [0, pages[-1]['pdf_height'], 0, 0]}]
        doc = fitz.open(ROOT / (fid + '.pdf'))
        for before, after in zip(ordered, ordered[1:]):
            missing = list(range(before['number'] + 1, after['number']))
            if not missing:
                continue
            for p in pages:
                for c in p['columns']:
                    markers = [r['rect'][0] for r in c['lines'] if re.match(r'^(Ans|Sol)\b', r['text'], re.I)]
                    base = min(markers) if markers else p['pdf_width'] * (.082 if c['index'] == 0 else .512)
                    for line in c['lines']:
                        pos = (p['page'], c['index'], line['rect'][1])
                        if not position(before) < pos < position(after) or line['rect'][0] > base + 6:
                            continue
                        if re.match(r'^(Ans|Sol|SECTION|MATHEMATICS|PHYSICS|CHEMISTRY)', line['text'], re.I):
                            continue
                        rect = fitz.Rect(base - 3, line['rect'][1] - 5, min(c['right'], base + 145), line['rect'][3] + 6)
                        pix = doc[p['page'] - 1].get_pixmap(matrix=fitz.Matrix(2.5, 2.5), clip=rect, alpha=False)
                        image = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
                        rows.append({'id': len(rows), 'file': fid, 'filename': file['filename'], 'missing': missing,
                                     'page': p['page'], 'column': c['index'], 'line': line, 'proof_rect': list(rect), 'image': image})
    OUT.mkdir(parents=True, exist_ok=True)
    for batch in range(math.ceil(len(rows) / 24)):
        subset = rows[batch * 24:(batch + 1) * 24]
        sheet = Image.new('RGB', (1600, 8 * 145), '#eee')
        draw = ImageDraw.Draw(sheet)
        for index, row in enumerate(subset):
            x, y = (index % 4) * 400, (index // 4) * 145
            draw.text((x + 3, y + 2), f'#{row["id"]} missing {row["missing"]} page{row["page"]} col{row["column"]}', fill='black')
            draw.text((x + 3, y + 15), row['filename'][:50], fill='black')
            image = row['image']
            image.thumbnail((390, 108))
            sheet.paste(image, (x + 4, y + 34))
        target = OUT / f'number-review-{batch + 1}.png'
        sheet.save(target)
        print(target)
    serial = [{key: value for key, value in row.items() if key != 'image'} for row in rows]
    (ROOT / 'number_review_candidates.json').write_text(json.dumps(serial, indent=2))
    print('SOURCE NUMBER REGIONS', len(rows))
