import argparse
import concurrent.futures
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse

import fitz
import requests
from bs4 import BeautifulSoup

FOLDER = 'https://drive.google.com/drive/folders/1k1_N_p3yqWKNJK3HyEp1D3w_PAH63S4m'
ROOT = Path('/app/data/jee_pyq/source_audit')
SAMPLES = {'2 april 2025 shift 1.pdf', '21 jan shift 1 2026.pdf', '24 jan shift of 2026.pdf'}


def inventory():
    response = requests.get(FOLDER, timeout=40)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    result = []
    for row in soup.select('tr[data-id][role="row"]'):
        name = row.select_one('strong')
        if name and name.get_text().strip().lower().endswith('.pdf'):
            result.append({'drive_id': row['data-id'], 'filename': name.get_text().strip()})
    if not result:
        raise ValueError('No accessible PDFs in the shared folder')
    return result


def inspect(item):
    path = ROOT / (item['drive_id'] + '.pdf')
    try:
        if not path.exists():
            session = requests.Session()
            response = session.get('https://drive.google.com/uc', params={'export': 'download', 'id': item['drive_id']}, timeout=60)
            response.raise_for_status()
            if not response.content.startswith(b'%PDF-'):
                form = BeautifulSoup(response.text, 'html.parser').find('form', id='download-form')
                if form and urlparse(form.get('action', '')).hostname == 'drive.usercontent.google.com':
                    params = {x['name']: x.get('value', '') for x in form.select('input[name]')}
                    response = session.get(form['action'], params=params, timeout=60)
                    response.raise_for_status()
            if not response.content.startswith(b'%PDF-'):
                raise ValueError('Download did not return a PDF; no access challenge bypassed')
            if len(response.content) > 50 * 1024 * 1024:
                raise ValueError('PDF exceeds the source-audit size limit')
            path.write_bytes(response.content)
        raw = path.read_bytes()
        doc = fitz.open(stream=raw, filetype='pdf')
        pages = [{'page': i + 1, 'chars': len(p.get_text()), 'text': p.get_text()[:2400]} for i, p in enumerate(doc)]
        dates = []
        for page in pages:
            lines = [line.strip() for line in page['text'].splitlines() if re.search(r'202[0-9]|shift|january|april|morning|evening', line, re.I)]
            if lines:
                dates.append({'page': page['page'], 'lines': lines[:12]})
        out = {**item, 'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
               'page_count': len(doc), 'text_chars': sum(p['chars'] for p in pages), 'date_candidates': dates,
               'pages': pages, 'status': 'downloaded_not_mapped'}
        (ROOT / (item['drive_id'] + '.inspection.json')).write_text(json.dumps(out, indent=2))
        return {key: out[key] for key in ('filename', 'drive_id', 'page_count', 'text_chars', 'status', 'date_candidates')}
    except Exception as exc:
        return {**item, 'status': 'blocked', 'reason': type(exc).__name__ + ': ' + str(exc)[:220]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--all', action='store_true')
    args = parser.parse_args()
    ROOT.mkdir(parents=True, exist_ok=True)
    items = inventory()
    (ROOT / 'inventory.json').write_text(json.dumps({'folder_url': FOLDER, 'files': items}, indent=2))
    print(json.dumps({'listed_pdf_count': len(items), 'files': items}), flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(inspect, [item for item in items if args.all or item['filename'] in SAMPLES]))
    (ROOT / ('all_results.json' if args.all else 'sample_results.json')).write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2), flush=True)
