import argparse
import json
import math
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont

ROOT = Path('/app/data/jee_pyq/source_audit')
OUT = Path('/tmp/jee_pyq_inspect')


def page_crop(doc, ref, width=440):
    rect = fitz.Rect(ref['rect'])
    scale = width / rect.width
    pix = doc[ref['page'] - 1].get_pixmap(matrix=fitz.Matrix(scale, scale), clip=rect, alpha=False)
    return Image.frombytes('RGB', [pix.width, pix.height], pix.samples)


def stack(doc, refs, width=440):
    imgs = [page_crop(doc, ref, width) for ref in refs]
    out = Image.new('RGB', (width, sum(i.height for i in imgs) + max(0, len(imgs) - 1) * 8), 'white')
    top = 0
    for image in imgs:
        out.paste(image, (0, top))
        top += image.height + 8
    return out


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', required=True)
    args = parser.parse_args()
    data = json.loads((ROOT / (args.file + '.candidates.json')).read_text())
    doc = fitz.open(ROOT / (args.file + '.pdf'))
    OUT.mkdir(parents=True, exist_ok=True)
    proofs = []
    for q in data['questions']:
        if not q.get('q_refs') or not q.get('s_refs'):
            continue
        number = q['number']
        question = stack(doc, q['q_refs'])
        solution = stack(doc, q['s_refs'])
        question.save(OUT / f'{args.file}-q{number}.png')
        solution.save(OUT / f'{args.file}-s{number}.png')
        label = q['s_refs'][0].copy()
        label['rect'] = [*label['rect'][:3], min(label['rect'][3], label['rect'][1] + 20)]
        image = page_crop(doc, label, 260)
        tile = Image.new('RGB', (300, 90), 'white')
        draw = ImageDraw.Draw(tile)
        draw.text((5, 3), f'Q{number} | extracted {q["answer"]}', fill='black')
        tile.paste(image, (5, 25))
        proofs.append(tile)
    sheet = Image.new('RGB', (1500, math.ceil(len(proofs) / 5) * 90), '#ddd')
    for i, tile in enumerate(proofs):
        sheet.paste(tile, ((i % 5) * 300, (i // 5) * 90))
    path = OUT / (args.file + '-key-proof.png')
    sheet.save(path)
    print(path)
    print('Saved paired source crops:', len(proofs))
