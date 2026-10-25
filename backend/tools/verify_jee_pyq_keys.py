import argparse
import concurrent.futures
import io
import json
import os
import re
import subprocess
import threading
from pathlib import Path

import fitz

ROOT = Path('/app/data/jee_pyq/source_audit')
_local = threading.local()


def read_key(task):
    fid, q, sha = task
    ref = q['key_ref']
    if getattr(_local, 'fid', None) != fid:
        _local.doc = fitz.open(ROOT / (fid + '.pdf'))
        _local.fid = fid
    doc = _local.doc
    rect = fitz.Rect(ref['rect']) + (-3, -3, 3, 3)
    scale = min(5, 900 / rect.width)
    pix = doc[ref['page'] - 1].get_pixmap(matrix=fitz.Matrix(scale, scale), clip=rect, alpha=False)
    results = []
    for mode in (7, 6):
        run = subprocess.run(['tesseract', 'stdin', 'stdout', '--psm', str(mode), '-l', 'eng'], input=pix.tobytes('png'), capture_output=True,
                             timeout=30, env={**os.environ, 'OMP_THREAD_LIMIT': '1'})
        text = run.stdout.decode().strip()
        match = re.search(r'(?:Ans|Sol)[.,:]?\s*[\[(]?\s*([+-]?\d+(?:\s*,\s*[+-]?\d+)*|Dropped|Bonus)\s*[\])]?', text, re.I)
        if q.get('printed_answer') and '.' in q['printed_answer']:
            match = re.search(r'([+-]?\d+\.\d+)\s*%', text)
        token = match[1].strip().lower().replace(' ', '') if match else None
        if token and re.fullmatch(r'[+-]?\d+(?:,[+-]?\d+)*', token):
            token = ','.join(str(int(value)) for value in token.split(','))
        results.append({'mode': mode, 'text': text, 'answer': token})
    expected = q.get('printed_answer') or (q['source_status'] if q.get('source_status') != 'normal' else ','.join(q.get('accepted_answers', [])))
    accepted = [r['answer'] for r in results if r['answer'] is not None]
    return {'number': q['number'], 'source_sha256': sha, 'page': ref['page'], 'rect': list(rect),
            'candidate_answer': q['answer'], 'expected_printed_answer': expected, 'normalization_evidence': q.get('normalization_evidence'), 'passes': results,
            'agreement': len(accepted) == 2 and len(set(accepted + [expected])) == 1}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', required=True)
    args = parser.parse_args()
    data = json.loads((ROOT / (args.file + '.candidates.json')).read_text())
    tasks = [(args.file, q, data['source_sha256']) for q in data['questions'] if q.get('key_ref')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        result = list(pool.map(read_key, tasks))
    (ROOT / (args.file + '.key_checks.json')).write_text(json.dumps(result, indent=2))
    print('INDEPENDENT_KEY_CHECKS', len(result), 'AGREE', sum(r['agreement'] for r in result))
    print(json.dumps([r for r in result if not r['agreement']], indent=2))
