import argparse
import concurrent.futures
import csv
import io
import json
import os
import subprocess
from pathlib import Path

import fitz
from PIL import Image

ROOT = Path('/app/data/jee_pyq/source_audit')
CACHE = ROOT / 'ocr'


def recognise(image, psm=3):
    data = io.BytesIO()
    image.save(data, format='PNG')
    run = subprocess.run(['tesseract', 'stdin', 'stdout', '--psm', str(psm), '-l', 'eng', 'tsv'],
                         input=data.getvalue(), capture_output=True, timeout=65,
                         env={**os.environ, 'OMP_THREAD_LIMIT': '1'})
    if run.returncode:
        raise RuntimeError('OCR process failed')
    groups = {}
    for row in csv.DictReader(io.StringIO(run.stdout.decode()), delimiter='\t', quoting=csv.QUOTE_NONE):
        if row['level'] != '5' or not row['text'].strip():
            continue
        key = tuple(row[k] for k in ('block_num', 'par_num', 'line_num'))
        word = {'text': row['text'], 'box': [int(row['left']), int(row['top']), int(row['left']) + int(row['width']), int(row['top']) + int(row['height'])], 'confidence': float(row['conf'])}
        groups.setdefault(key, []).append(word)
    lines = []
    for words in groups.values():
        words.sort(key=lambda x: x['box'][0])
        box = [min(w['box'][0] for w in words), min(w['box'][1] for w in words), max(w['box'][2] for w in words), max(w['box'][3] for w in words)]
        lines.append({'text': ' '.join(w['text'] for w in words), 'box': box, 'words': words})
    return sorted(lines, key=lambda x: (x['box'][1], x['box'][0]))


def page_job(task):
    fid, number, psm = task
    dest = CACHE / fid / f'{number:03d}-psm{psm}.json'
    if dest.exists():
        cached = json.loads(dest.read_text())
        if cached.get('schema') == 3 or number != 1 and cached.get('schema') == 2:
            return str(dest)
    doc = fitz.open(ROOT / (fid + '.pdf'))
    page = doc[number - 1]
    scale = 2000 / page.rect.width
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    image = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
    result = {'schema': 3, 'page': number, 'total_pages': len(doc), 'pdf_width': page.rect.width, 'pdf_height': page.rect.height, 'scale': scale, 'columns': []}
    boundaries = [(int(pix.width * .035), int(pix.width * .50)), (int(pix.width * .50), int(pix.width * .965))]
    if number == 1:
        result['cover_lines'] = recognise(image.crop((int(pix.width * .04), 0, int(pix.width * .96), pix.height)), 6)
        result['has_cover'] = any('IMPORTANT INSTRUCTIONS' in line['text'].upper() for line in result['cover_lines'])
        if result['has_cover']:
            boundaries = []
    for ci, (left, right) in enumerate(boundaries):
        lines = recognise(image.crop((left, 0, right, pix.height)), psm)
        for line in lines:
            for item in [line, *line['words']]:
                x0, y0, x1, y1 = item['box']
                item['rect'] = [round((x0 + left) / scale, 3), round(y0 / scale, 3), round((x1 + left) / scale, 3), round(y1 / scale, 3)]
        result['columns'].append({'index': ci, 'left': left / scale, 'right': right / scale, 'lines': lines})
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result))
    print('OCR', fid, number, flush=True)
    return str(dest)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file')
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--headers', action='store_true')
    parser.add_argument('--pages', default='')
    parser.add_argument('--psm', type=int, default=3)
    args = parser.parse_args()
    if not args.file and not args.all:
        parser.error('--file or --all is required')
    ids = [row['drive_id'] for row in json.loads((ROOT / 'inventory.json').read_text())['files']] if args.all else [args.file]
    tasks = []
    for fid in ids:
        doc = fitz.open(ROOT / (fid + '.pdf'))
        pages = [1] if args.headers else [int(p) for p in args.pages.split(',')] if args.pages else list(range(1, len(doc) + 1))
        tasks.extend((fid, number, args.psm) for number in pages)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(page_job, tasks))
