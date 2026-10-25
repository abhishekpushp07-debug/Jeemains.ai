import concurrent.futures
import hashlib
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
load_dotenv(BACKEND / '.env')
from tejas_storage import put_object, request as storage_request
from extract_jee_pyq_sources import ROOT

STATE = ROOT / 'private_sources.json'


def upload(item):
    fid = item['file']['drive_id']
    parsed = json.loads((ROOT / (fid + '.candidates.json')).read_text())
    raw = (ROOT / (fid + '.pdf')).read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != parsed['source_sha256']:
        raise ValueError('Original source bytes changed')
    existing = json.loads(STATE.read_text()).get(fid) if STATE.exists() else None
    if existing and existing['sha256'] == sha:
        result = existing
    else:
        remote = put_object('tejas/jee-pyq/originals/' + sha + '.pdf', raw)
        result = {'id': 'jee-pyq-source-' + sha[:24], 'name': item['file']['filename'], 'path': remote,
                  'sha256': sha, 'size': len(raw), 'pages': parsed['ocr_pages'], 'role': 'source', 'status': 'ready',
                  'source_drive_id': fid, 'source_collection': 'jee-pyq-written', 'media_type': 'application/pdf'}
    checked = storage_request('GET', result['path']).content
    if len(checked) != len(raw) or hashlib.sha256(checked).hexdigest() != sha:
        raise ValueError('Private object readback differs from original')
    print('PRIVATE_SOURCE_VERIFIED', item['file']['filename'], len(raw), flush=True)
    return fid, result


if __name__ == '__main__':
    eligible = [item for item in json.loads((ROOT / 'extraction_summary.json').read_text()) if not item.get('error') and not item.get('issues')]
    saved = json.loads(STATE.read_text()) if STATE.exists() else {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for fid, result in pool.map(upload, eligible):
            saved[fid] = result
            STATE.write_text(json.dumps(saved, indent=2))
    print('PRIVATE_OBJECTS_VERIFIED', len(saved), 'NO_DATABASE_WRITES_OR_PUBLICATION', flush=True)
