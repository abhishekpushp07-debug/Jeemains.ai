import json
import math
from pathlib import Path

import fitz
from PIL import Image, ImageDraw
from extract_jee_pyq_sources import ROOT, extract, load_pages, position

OUT = Path('/tmp/jee_pyq_inspect')
rows = []
for file in json.loads((ROOT / 'inventory.json').read_text())['files']:
    try:
        paper = extract(file['drive_id'])
    except Exception:
        continue
    doc = fitz.open(ROOT / (file['drive_id'] + '.pdf'))
    for i, q in enumerate(paper['questions']):
        if not any('key' in issue.lower() for issue in q['issues']):
            continue
        nextq = paper['questions'][i + 1]['anchor'] if i + 1 < len(paper['questions']) else {'page': len(doc), 'column': 1, 'rect': [0, doc[-1].rect.height, 0, 0]}
        key_rows = []
        for page in load_pages(file['drive_id'], 6):
            for c in page['columns']:
                for line in c['lines']:
                    pos = (page['page'], c['index'], line['rect'][1])
                    if position(q['anchor']) < pos < position(nextq) and ('ans' in line['text'].lower() or line['text'].lower().startswith(('sol.', 'so.'))):
                        rect = fitz.Rect(c['left'], line['rect'][1] - 5, c['right'], line['rect'][1] + doc[page['page'] - 1].rect.height * .035)
                        scale = 375 / rect.width
                        pix = doc[page['page'] - 1].get_pixmap(matrix=fitz.Matrix(scale, scale), clip=rect, alpha=False)
                        image = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
                        key_rows.append({'page': page['page'], 'column': c['index'], 'line': line, 'rect': list(rect), 'image': image})
        rows.append({'id': len(rows), 'file': file['drive_id'], 'filename': file['filename'], 'question': q['number'], 'source_sha256': paper['source_sha256'], 'key_rows': key_rows})
for batch in range(math.ceil(len(rows) / 8)):
    sheet = Image.new('RGB', (1600, 1100), '#eee')
    draw = ImageDraw.Draw(sheet)
    for i, row in enumerate(rows[batch * 8:(batch + 1) * 8]):
        x, y = i % 4 * 400, i // 4 * 550
        draw.text((x + 4, y + 2), f'#{row["id"]} Q{row["question"]}', fill='black')
        draw.text((x + 4, y + 16), row['filename'][:50], fill='black')
        top = y + 40
        for source in row['key_rows'][:6]:
            draw.text((x + 4, top), f'p{source["page"]} c{source["column"]}', fill='black')
            top += 14
            image = source['image']
            image.thumbnail((380, 110))
            if top + image.height > y + 545:
                break
            sheet.paste(image, (x + 4, top))
            top += image.height + 8
    dest = OUT / f'key-issue-review-{batch + 1}.png'
    sheet.save(dest)
    print(dest)
for row in rows:
    for source in row['key_rows']:
        source.pop('image')
(ROOT / 'key_issue_candidates.json').write_text(json.dumps(rows, indent=2))
print('FLAGGED_KEY_QUESTIONS', len(rows))
