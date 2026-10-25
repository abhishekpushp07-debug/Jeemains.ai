import argparse
import json
from pathlib import Path

import fitz
import math
import numpy as np

ROOT = Path('/app/data/jee_pyq/source_audit')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', required=True)
    args = parser.parse_args()
    data = json.loads((ROOT / (args.file + '.candidates.json')).read_text())
    doc = fitz.open(ROOT / (args.file + '.pdf'))
    issues = []
    rendered = {}
    for q in data['questions']:
        for kind in ('q_refs', 's_refs'):
            for index, ref in enumerate(q.get(kind, [])):
                rect = fitz.Rect(ref['rect'])
                if ref['page'] not in rendered:
                    page = doc[ref['page'] - 1]
                    scale = min(3, 2000 / page.rect.width)
                    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), colorspace=fitz.csGRAY)
                    rendered[ref['page']] = (np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width).copy(), scale)
                raster, scale = rendered[ref['page']]
                array = raster[max(0, math.floor(rect.y0 * scale)):min(raster.shape[0], math.ceil(rect.y1 * scale)),
                               max(0, math.floor(rect.x0 * scale)):min(raster.shape[1], math.ceil(rect.x1 * scale))].copy()
                for omitted in ref.get('omit_rects', []):
                    cut = fitz.Rect(omitted)
                    if not rect.contains(cut):
                        raise ValueError('Omitted region must be within its source crop')
                    x0, y0 = math.floor(rect.x0 * scale), math.floor(rect.y0 * scale)
                    array[max(0, math.floor(cut.y0 * scale) - y0):math.ceil(cut.y1 * scale) - y0,
                          max(0, math.floor(cut.x0 * scale) - x0):math.ceil(cut.x1 * scale) - x0] = 255
                if array.shape[0] < 2 or array.shape[1] < 25:
                    continue
                body = array[:, 12:-12]
                top = int((body[:2] < 170).sum())
                bottom = int((body[-2:] < 170).sum())
                if top > 8 or bottom > 8:
                    issues.append({'question': q['number'], 'kind': kind, 'index': index, 'page': ref['page'], 'rect': ref['rect'], 'top_ink': top, 'bottom_ink': bottom})
    (ROOT / (args.file + '.crop_edge_checks.json')).write_text(json.dumps(issues, indent=2))
    print(json.dumps({'potential_cut_edges': len(issues), 'items': issues}, indent=2))
