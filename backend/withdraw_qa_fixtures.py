"""Safely withdraw positively identified test sets. Dry-run by default.
Preserves attempts, files, ledgers, report objects and the original source paper.
Run only in an explicitly authorized environment after testing.
"""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / 'backend' / '.env')
load_dotenv(ROOT / 'frontend' / '.env')
KNOWN_TEST_SOURCES = [
    'QA test fixture for V5 architecture testing',
    'QA test fixture for cross-set testing',
    'QA fault injection testing',
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    db = MongoClient(os.environ['MONGO_URL'])[os.environ['DB_NAME']]
    original = db.tejas_sets.find_one({'id': 'tejas-paper-01'}, {'_id': 0})
    original_hash = hashlib.sha256(json.dumps(original, sort_keys=True, default=str).encode()).hexdigest()
    query = {'id': {'$ne': 'tejas-paper-01'}, '$or': [{'qa_only': True}, {'source': {'$in': KNOWN_TEST_SOURCES}}]}
    candidates = list(db.tejas_sets.find(query, {'_id': 0, 'id': 1, 'title': 1, 'status': 1, 'qa_only': 1, 'source': 1}))
    if not args.apply:
        print(json.dumps({'dry_run': True, 'count': len(candidates), 'sets': candidates}, indent=2))
        return
    session = requests.Session()
    base = os.environ['REACT_APP_BACKEND_URL'].rstrip('/') + '/api'
    auth = session.post(base + '/auth/login', json={'email': os.environ['ADMIN_EMAIL'], 'password': os.environ['ADMIN_PASSWORD']}, timeout=30)
    auth.raise_for_status()
    rows = []
    for entry in candidates:
        if entry['status'] != 'withdrawn':
            response = session.post(base + '/studio/sets/' + entry['id'] + '/withdraw', json={'reason': 'Controlled QA complete. Withdraw fixture only; preserve original source and historical evidence.'}, timeout=30)
            response.raise_for_status()
        db.tejas_sets.update_one({'id': entry['id'], 'status': 'withdrawn'}, {'$set': {'qa_only': True}})
        after = db.tejas_sets.find_one({'id': entry['id']}, {'status': 1})
        rows.append({'id': entry['id'], 'title': entry['title'], 'before': entry['status'], 'after': after['status']})
    original_after = db.tejas_sets.find_one({'id': 'tejas-paper-01'}, {'_id': 0})
    unchanged = hashlib.sha256(json.dumps(original_after, sort_keys=True, default=str).encode()).hexdigest() == original_hash
    if not unchanged:
        raise RuntimeError('Original source changed during cleanup; investigate immediately.')
    report = {'recorded_at': datetime.now(timezone.utc).isoformat(), 'operation': 'QA soft withdrawal, no deletions', 'original_unchanged': unchanged, 'original_status': original_after['status'], 'original_question_count': len(original_after.get('questions', [])), 'count': len(rows), 'sets': rows}
    target = ROOT / 'test_reports' / 'qa_withdrawal.json'
    target.write_text(json.dumps(report, indent=2))
    print(json.dumps({'report': str(target), 'withdrawn_or_confirmed': len(rows), 'original_unchanged': unchanged, 'original_status': original_after['status']}))


if __name__ == '__main__':
    main()
