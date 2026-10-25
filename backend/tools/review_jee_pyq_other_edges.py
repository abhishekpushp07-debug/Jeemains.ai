import json
import math
from pathlib import Path

import fitz
from PIL import Image, ImageDraw
from extract_jee_pyq_sources import ROOT

OUT = Path('/tmp/jee_pyq_inspect')
rows = []
for paper in json.loads((ROOT / 'all_crop_edge_summary.json').read_text()):
    if paper.get('error'):
        continue
    fid = paper['file']['drive_id']
    doc = fitz.open(ROOT / (fid + '.pdf'))
    for issue in paper['issues']:
        if issue['kind'] == 'q_refs' and issue['index'] == 0 and issue['top_ink'] > 8:
            continue
        if issue['kind'] == 's_refs' and issue['bottom_ink'] > 8:
            data = json.loads((ROOT / (fid + '.candidates.json')).read_text())
            nextq = next((q for q in data['questions'] if q['number'] == issue['question'] + 1), None)
            if nextq and nextq.get('q_refs') and nextq['q_refs'][0]['page'] == issue['page'] and abs(nextq['q_refs'][0]['rect'][1] - issue['rect'][3]) < 3:
                continue
        rect = fitz.Rect(issue['rect'])
        page = doc[issue['page'] - 1]
        y = rect.y0 if issue['top_ink'] > 8 else rect.y1
        proof = fitz.Rect(rect.x0, max(0, y - page.rect.height * .04), rect.x1, min(page.rect.height, y + page.rect.height * .04))
        scale = 375 / proof.width
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=proof, alpha=False)
        image = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
        pen = ImageDraw.Draw(image)
        boundary = int((y - proof.y0) * scale)
        pen.line([(0, boundary), (image.width, boundary)], fill='#df0000', width=2)
        rows.append({'id': len(rows), 'file': paper['file'], 'issue': issue, 'proof_rect': list(proof), 'image': image})
for batch in range(math.ceil(len(rows) / 12)):
    sheet = Image.new('RGB', (1600, 1000), '#eee')
    draw = ImageDraw.Draw(sheet)
    for i, row in enumerate(rows[batch * 12:(batch + 1) * 12]):
        x, y = i % 4 * 400, i // 4 * 330
        issue = row['issue']
        draw.text((x + 4, y + 2), f'#{row["id"]} Q{issue["question"]} {issue["kind"]} i{issue["index"]} p{issue["page"]}', fill='black')
        draw.text((x + 4, y + 16), row['file']['filename'][:50], fill='black')
        row['image'].thumbnail((390, 290))
        sheet.paste(row['image'], (x + 4, y + 35))
    path = OUT / f'other-edge-proof-{batch + 1}.png'
    sheet.save(path)
    print(path)
(ROOT / 'other_edge_candidates.json').write_text(json.dumps([{k: v for k, v in r.items() if k != 'image'} for r in rows], indent=2))
print('OTHER_CROP_EDGE_CASES', len(rows))
