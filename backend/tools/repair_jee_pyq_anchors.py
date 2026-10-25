import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

import fitz
from extract_jee_pyq_sources import ROOT, labels, load_pages, position


def increasing(anchors):
    chains = []
    for anchor in anchors:
        choices = [chain for chain in chains if chain[-1]['number'] < anchor['number']]
        chain = max(choices, key=len, default=[]) + [anchor]
        chains.append(chain)
    return max(chains, key=len, default=[])


def crop_number(task):
    fid, line, page, col, base, allowed = task
    doc = fitz.open(ROOT / (fid + '.pdf'))
    y0, y1 = line['rect'][1], line['rect'][3]
    rect = fitz.Rect(base - 2, y0 - 3, base + 21, y1 + 3)
    pix = doc[page - 1].get_pixmap(matrix=fitz.Matrix(7, 7), clip=rect, alpha=False)
    readings = []
    for mode in (8, 10):
        run = subprocess.run(['tesseract', 'stdin', 'stdout', '--psm', str(mode), '-l', 'eng', '-c', 'tessedit_char_whitelist=0123456789.'],
                             input=pix.tobytes('png'), capture_output=True, timeout=20, env={**os.environ, 'OMP_THREAD_LIMIT': '1'})
        text = re.sub(r'[^0-9]', '', run.stdout.decode())
        readings.append(int(text) if text and len(text) <= 2 else None)
    if readings[0] == readings[1] and readings[0] in allowed:
        return {'number': readings[0], 'page': page, 'column': col, 'rect': line['rect'],
                'text': line['text'], 'original_text': line['text'], 'proof_rect': list(rect),
                'ocr_modes': [8, 10], 'method': 'two-pass isolated number glyph consensus'}
    return None


def repair(fid):
    pages = load_pages(fid, 6)
    if not pages or len(pages) != pages[0].get('total_pages'):
        raise ValueError('Complete OCR required')
    anchors, _, _, _ = labels(pages)
    chain = increasing(anchors)
    ordered = [{'number': 0, 'page': 1, 'column': 0, 'rect': [0, 0, 0, 0]}, *chain,
               {'number': 76, 'page': pages[-1]['page'], 'column': 1, 'rect': [0, pages[-1]['pdf_height'], 0, 0]}]
    tasks = []
    for before, after in zip(ordered, ordered[1:]):
        allowed = list(range(before['number'] + 1, after['number']))
        if not allowed:
            continue
        for p in pages:
            for c in p['columns']:
                bases = [r['rect'][0] for r in c['lines'] if re.match(r'^(Ans|Sol)\b', r['text'], re.I)]
                base = min(bases) if bases else p['pdf_width'] * (.082 if c['index'] == 0 else .512)
                for line in c['lines']:
                    pos = (p['page'], c['index'], line['rect'][1])
                    if not position(before) < pos < position(after):
                        continue
                    if line['rect'][0] > base + 42 or re.match(r'^(Ans|Sol|SECTION|MATHEMATICS|PHYSICS|CHEMISTRY)', line['text'], re.I):
                        continue
                    tasks.append((fid, line, p['page'], c['index'], base, allowed))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        found = [r for r in pool.map(crop_number, tasks) if r]
    grouped = {}
    for row in found:
        grouped.setdefault(row['number'], []).append(row)
    unique = []
    ambiguous = []
    for number, rows in grouped.items():
        distinct = []
        for row in sorted(rows, key=position):
            if not any(position(row)[:2] == position(old)[:2] and abs(row['rect'][1] - old['rect'][1]) < 4 for old in distinct):
                distinct.append(row)
        if len(distinct) == 1:
            unique.append(distinct[0])
        else:
            ambiguous.append({'number': number, 'candidates': distinct})
    output = {'source_sha256': hashlib.sha256((ROOT / (fid + '.pdf')).read_bytes()).hexdigest(), 'repairs': unique, 'ambiguous': ambiguous}
    (ROOT / (fid + '.anchor_repairs.json')).write_text(json.dumps(output, indent=2))
    print(json.dumps({'file': fid, 'targeted_regions': len(tasks), 'recovered': [r['number'] for r in unique], 'ambiguous': [r['number'] for r in ambiguous]}, indent=2), flush=True)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', required=True)
    args = parser.parse_args()
    repair(args.file)
