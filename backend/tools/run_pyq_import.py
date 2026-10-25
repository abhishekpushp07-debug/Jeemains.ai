import argparse
import json
import os
import time
from pathlib import Path

import requests
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--target', choices=['preview', 'production'], required=True)
parser.add_argument('--url')
args = parser.parse_args()
backend = dotenv_values(ROOT / 'backend' / '.env')
frontend = dotenv_values(ROOT / 'frontend' / '.env')
if args.target == 'production' and not args.url:
    parser.error('Production URL must be explicitly provided after deployment verification')
base = args.url or frontend['REACT_APP_BACKEND_URL']
base = base.rstrip('/')
session = requests.Session()
session.headers.update({'Origin': base, 'Content-Type': 'application/json'})
try:
    response = session.post(base + '/api/auth/login', json={'email': backend['ADMIN_EMAIL'], 'password': backend['ADMIN_PASSWORD']}, timeout=45)
    response.raise_for_status()
    print('OWNER_AUTHORIZED', args.target, flush=True)
    for step in range(100):
        reply = session.post(base + '/api/studio/pyq-import/step', json={}, timeout=110)
        if reply.status_code in (409, 503):
            print('IMPORT_RETRY', reply.status_code, flush=True)
            time.sleep(5)
            continue
        reply.raise_for_status()
        envelope = reply.json()
        state = envelope.get('data', envelope)
        print(json.dumps({k: state[k] for k in ('phase', 'verified_files', 'total_files', 'inserted_records', 'total_records', 'published_papers', 'total_papers', 'questions')}), flush=True)
        if state['phase'] == 'complete':
            break
    else:
        raise RuntimeError('Import did not complete within the bounded step budget')
finally:
    if session.cookies:
        session.post(base + '/api/auth/logout', json={}, timeout=20)
    session.close()
