import argparse
import gzip
import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from bson import json_util
from dotenv import load_dotenv
from pymongo import MongoClient, ReturnDocument

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RECEIPTS = 'tejas_student_resets'
OWNED = ('tejas_sessions', 'tejas_preflight', 'tejas_saved_tests', 'tejas_reviews',
         'tejas_question_reports', 'tejas_score_versions', 'tejas_ledgers', 'tejas_cohort_entries')
CONTENT = ('tejas_sets', 'tejas_versions', 'tejas_files', 'tejas_chapter_books', 'tejas_mock_books',
           'tejas_packs', 'tejas_profiles', 'tejas_question_solutions', 'tejas_ai_solutions',
           'tejas_manual_solves', 'tejas_smart_imports', 'tejas_smart_papers', 'tejas_smart_questions')


def encoded(value):
    return json_util.dumps(value, json_options=json_util.CANONICAL_JSON_OPTIONS, sort_keys=True, separators=(',', ':')).encode()


def backup_encoded(value):
    return json_util.dumps(value, json_options=json_util.CANONICAL_JSON_OPTIONS, sort_keys=False, separators=(',', ':')).encode()


def record_digest(value):
    return hashlib.sha256(backup_encoded(value)).hexdigest()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def require_offline(writers_paused):
    if not writers_paused:
        raise RuntimeError('Pause ALL web, background and scheduled writers before backup or deletion.')


def scope_queries(db, users, attempts, cohorts):
    protected = [row['id'] for name in ('tejas_users', 'tejas_phone_profiles') for row in db[name].find({'role': {'$ne': 'student'}}, {'id': 1})]
    owned = {'$or': [{'user_id': {'$in': users}}, {'attempt_id': {'$in': attempts}, 'user_id': {'$nin': protected}}]}
    scopes = {name: owned for name in OWNED}
    scopes['tejas_ledgers'] = {'$or': owned['$or'] + [{'id': {'$in': attempts}, 'user_id': {'$nin': protected}}]}
    scopes.update({
        'tejas_users': {'id': {'$in': users}, 'role': 'student'},
        'tejas_phone_profiles': {'id': {'$in': users}, 'role': 'student'},
        'tejas_attempts': {'user_id': {'$in': users}},
        'tejas_jobs': {'$or': [{'payload.attempt_id': {'$in': attempts}, 'user_id': {'$nin': protected}, 'kind': {'$in': ['report', 'grade', 'cohort']}},
                               {'user_id': {'$in': users}, 'kind': {'$in': ['report', 'grade', 'cohort']}}]},
        'tejas_audits': {'actor': {'$in': users}},
        'tejas_cohort_snapshots': {'id': {'$in': cohorts}},
    })
    return scopes


def build_plan(db, include_unlinked=False):
    roots = list(db.tejas_users.find({'role': 'student'})) + list(db.tejas_phone_profiles.find({'role': 'student'}))
    account_ids = sorted({row['id'] for row in roots})
    users = set(account_ids)
    known = {row['id'] for name in ('tejas_users', 'tejas_phone_profiles') for row in db[name].find({}, {'id': 1})}
    staff = {row['id'] for row in db.tejas_users.find({'role': {'$ne': 'student'}}, {'id': 1})}
    if include_unlinked:
        for name in ('tejas_attempts',) + OWNED:
            users.update(value for value in db[name].distinct('user_id') if isinstance(value, str) and value and value not in known)
        users.update(value for value in db.tejas_jobs.distinct('user_id', {'kind': {'$in': ['grade', 'report', 'cohort']}}) if isinstance(value, str) and value and value not in known)
    users = sorted(users)
    if staff.intersection(users):
        raise RuntimeError('Student identity overlaps a protected account.')
    attempts = {row['id'] for row in db.tejas_attempts.find({'user_id': {'$in': users}}, {'id': 1})}
    if include_unlinked:
        existing = set(db.tejas_attempts.distinct('id'))
        for name in ('tejas_ledgers', 'tejas_score_versions', 'tejas_reviews', 'tejas_question_reports', 'tejas_cohort_entries'):
            for row in db[name].find({}, {'id': 1, 'attempt_id': 1, 'user_id': 1}):
                aid = row.get('attempt_id') or (row.get('id') if name == 'tejas_ledgers' else None)
                if isinstance(aid, str) and aid and aid not in existing and row.get('user_id') not in staff:
                    attempts.add(aid)
    attempts = sorted(attempts)
    cohorts = set(db.tejas_cohort_entries.distinct('cohort_id', {'$or': [{'user_id': {'$in': users}}, {'attempt_id': {'$in': attempts}}]}))
    if include_unlinked:
        indexed = set(db.tejas_cohort_entries.distinct('cohort_id'))
        cohorts.update(cid for cid in db.tejas_cohort_snapshots.distinct('id') if cid not in indexed)
    cohorts = sorted(cohorts)
    scopes = scope_queries(db, users, attempts, cohorts)
    records = {name: [{'_id': row['_id'], 'sha256': record_digest(row)} for row in db[name].find(query)] for name, query in scopes.items()}
    return {'user_ids': users, 'account_ids': account_ids, 'include_unlinked': include_unlinked, 'attempt_ids': attempts, 'cohort_ids': cohorts, 'records': records}


def protected_fingerprint(db, plan):
    h = hashlib.sha256()
    excluded = {name: {backup_encoded(row['_id']) for row in rows} for name, rows in plan['records'].items()}
    for name in sorted(db.list_collection_names()):
        if name == RECEIPTS or name.startswith('system.'):
            continue
        for row in db[name].find({}).sort('_id', 1):
            if backup_encoded(row['_id']) in excluded.get(name, set()):
                continue
            if name == 'tejas_cohorts' and row.get('id') in plan['cohort_ids']:
                row.pop('dirty', None)
                row.pop('generation', None)
            h.update(name.encode() + b'\0' + backup_encoded(row) + b'\n')
    return h.hexdigest()


def upload_verified(data, owner_id, put, fetch):
    uploaded = put(data, owner_id)
    path = uploaded['path']
    if hashlib.sha256(fetch(path)).digest() != hashlib.sha256(data).digest():
        raise RuntimeError('Private backup read-back hash mismatch; no deletion is permitted.')
    return {'path': path, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def prepare(db, binding, owner_email, put, fetch, *, writers_paused=False, include_unlinked=False):
    require_offline(writers_paused)
    owner = db.tejas_users.find_one({'email': owner_email.lower(), 'role': 'owner'})
    if not owner:
        raise RuntimeError('The configured owner account was not found. No data was changed.')
    plan = build_plan(db, include_unlinked)
    before = protected_fingerprint(db, plan)
    reset_id = str(uuid.uuid4())
    parts, collections = [], {}
    for info in sorted(db.list_collections(), key=lambda row: row['name']):
        name = info['name']
        if name == RECEIPTS or name.startswith('system.'):
            continue
        metadata = {'options': info.get('options', {}), 'type': info.get('type', 'collection'),
                    'indexes': list(db[name].list_indexes()), 'records': 0}
        stream_hash = hashlib.sha256()
        buffer, count = bytearray(), 0
        for row in db[name].find({}).sort('_id', 1):
            line = backup_encoded(row) + b'\n'
            buffer.extend(line)
            stream_hash.update(line)
            metadata['records'] += 1
            count += 1
            if len(buffer) >= 8 * 1024 * 1024:
                part = upload_verified(gzip.compress(bytes(buffer), mtime=0), owner['id'], put, fetch)
                parts.append({**part, 'collection': name, 'records': count})
                buffer, count = bytearray(), 0
        if count:
            part = upload_verified(gzip.compress(bytes(buffer), mtime=0), owner['id'], put, fetch)
            parts.append({**part, 'collection': name, 'records': count})
        metadata['sha256'] = stream_hash.hexdigest()
        collections[name] = metadata
    if before != protected_fingerprint(db, plan) or digest(plan) != digest(build_plan(db, include_unlinked)):
        raise RuntimeError('Database changed during backup. Keep writers paused and prepare a fresh snapshot.')
    manifest = {'schema': 1, 'id': reset_id, 'binding': binding, 'database': db.name,
                'created_at': datetime.now(timezone.utc), 'owner_id': owner['id'], 'parts': parts, 'collections': collections, 'plan': plan}
    saved = upload_verified(gzip.compress(backup_encoded(manifest), mtime=0), owner['id'], put, fetch)
    receipt = {'_id': reset_id, 'phase': 'prepared', 'binding': binding, 'owner_id': owner['id'],
               'manifest': saved, 'plan_hash': digest(plan), 'parts_hash': digest(parts), 'collections_hash': record_digest(collections), 'created_at': manifest['created_at'],
               'counts': {name: len(rows) for name, rows in plan['records'].items()}, 'students': len(plan['account_ids']), 'unlinked_profile_ids': len(plan['user_ids']) - len(plan['account_ids'])}
    db[RECEIPTS].insert_one(receipt)
    return receipt


def verified_manifest(receipt, fetch):
    saved = receipt['manifest']
    raw = fetch(saved['path'])
    if hashlib.sha256(raw).hexdigest() != saved['sha256']:
        raise RuntimeError('Backup manifest failed integrity verification.')
    manifest = json_util.loads(gzip.decompress(raw))
    if digest(manifest['plan']) != receipt['plan_hash'] or manifest['id'] != receipt['_id']:
        raise RuntimeError('Backup snapshot does not match the approved receipt.')
    if digest(manifest['parts']) != receipt['parts_hash'] or record_digest(manifest['collections']) != receipt['collections_hash']:
        raise RuntimeError('Backup parts or collection metadata differ from the verified receipt.')
    expected = {name: {backup_encoded(row['_id']): row['sha256'] for row in rows} for name, rows in manifest['plan']['records'].items()}
    covered = {name: set() for name in expected}
    counts = {name: 0 for name in manifest['collections']}
    hashes = {name: hashlib.sha256() for name in counts}
    for part in manifest['parts']:
        name = part['collection']
        raw = fetch(part['path'])
        if hashlib.sha256(raw).hexdigest() != part['sha256']:
            raise RuntimeError('A private backup part failed integrity verification.')
        restored = gzip.decompress(raw)
        rows = [json_util.loads(line) for line in restored.splitlines()]
        if len(rows) != part['records'] or any('_id' not in row for row in rows):
            raise RuntimeError('Backup BSON records cannot be restored faithfully.')
        counts[name] += len(rows)
        hashes[name].update(restored)
        for row in rows:
            key = backup_encoded(row['_id'])
            if key in expected.get(name, {}):
                if key in covered[name] or expected[name][key] != record_digest(row):
                    raise RuntimeError('Backup target records are duplicated or changed.')
                covered[name].add(key)
    if any(covered[name] != set(rows) for name, rows in expected.items()):
        raise RuntimeError('Backup does not cover every record selected for deletion.')
    if any(counts[name] != meta['records'] or hashes[name].hexdigest() != meta['sha256'] for name, meta in manifest['collections'].items()):
        raise RuntimeError('Backup collection totals or content hashes are incomplete.')
    return manifest


def apply(db, binding, owner_email, reset_id, approval_hash, fetch, *, writers_paused=False):
    require_offline(writers_paused)
    owner = db.tejas_users.find_one({'email': owner_email.lower(), 'role': 'owner'})
    receipt = db[RECEIPTS].find_one({'_id': reset_id})
    if not owner or not receipt or receipt['owner_id'] != owner['id'] or receipt['binding'] != binding:
        raise RuntimeError('Reset receipt does not belong to this owner and database binding.')
    if approval_hash != receipt['manifest']['sha256']:
        raise RuntimeError('Exact verified snapshot approval hash is required.')
    if receipt['phase'] == 'complete':
        return receipt
    if receipt['phase'] not in ('prepared', 'applying'):
        raise RuntimeError('This reset snapshot is not in a phase that permits deletion.')
    manifest = verified_manifest(receipt, fetch)
    plan = manifest['plan']
    if manifest['binding'] != binding or manifest['database'] != db.name:
        raise RuntimeError('Backup is for a different database binding.')
    if db.tejas_users.count_documents({'id': {'$in': plan['user_ids']}, 'role': {'$ne': 'student'}}) or db.tejas_phone_profiles.count_documents({'id': {'$in': plan['user_ids']}, 'role': {'$ne': 'student'}}):
        raise RuntimeError('An account is now protected; prepare a new snapshot.')
    scopes = scope_queries(db, plan['user_ids'], plan['attempt_ids'], plan['cohort_ids'])
    for name, rows in plan['records'].items():
        expected = {backup_encoded(row['_id']): row['sha256'] for row in rows}
        for row in db[name].find(scopes[name]):
            if expected.get(backup_encoded(row['_id'])) != record_digest(row):
                raise RuntimeError('Student records changed after backup. Nothing further may be deleted.')
    protection = protected_fingerprint(db, plan) if receipt['phase'] == 'prepared' else receipt.get('protected_sha256')
    token = str(uuid.uuid4())
    clock = {'$divide': [{'$toLong': '$$NOW'}, 1000]}
    receipt = db[RECEIPTS].find_one_and_update({'_id': reset_id, 'phase': receipt['phase'],
        '$expr': {'$lte': [{'$ifNull': ['$lease_until', 0]}, clock]}},
        [{'$set': {'phase': 'applying', 'protected_sha256': {'$literal': protection}, 'lease': token,
                   'lease_until': {'$add': [clock, 300]}}}], return_document=ReturnDocument.AFTER)
    if not receipt:
        raise RuntimeError('Another reset process acquired this snapshot.')
    try:
        if receipt['protected_sha256'] != protected_fingerprint(db, plan):
            raise RuntimeError('Protected data changed during reset. Stop and inspect the private backup.')
        order = ['tejas_sessions', 'tejas_users', 'tejas_phone_profiles', 'tejas_jobs', 'tejas_attempts']
        for name in order + [name for name in plan['records'] if name not in order]:
            ids = [row['_id'] for row in plan['records'][name]]
            for offset in range(0, len(ids), 250):
                if not db[RECEIPTS].find_one({'_id': reset_id, 'lease': token, '$expr': {'$gt': ['$lease_until', clock]}}):
                    raise RuntimeError('Reset lease expired; stop and resume after checking the receipt.')
                db[name].delete_many({'_id': {'$in': ids[offset:offset + 250]}})
        if not db[RECEIPTS].find_one({'_id': reset_id, 'lease': token, '$expr': {'$gt': ['$lease_until', clock]}}):
            raise RuntimeError('Reset lease expired before final verification.')
        db.tejas_cohorts.update_many({'id': {'$in': plan['cohort_ids']}}, {'$set': {'dirty': True, 'generation': 'student-reset-' + reset_id}})
        remaining = {name: db[name].count_documents(query) for name, query in scopes.items()}
        if any(remaining.values()) or receipt['protected_sha256'] != protected_fingerprint(db, plan):
            raise RuntimeError('Reset verification failed; keep writers paused and inspect the receipt.')
        db[RECEIPTS].update_one({'_id': reset_id, 'lease': token}, {'$set': {'phase': 'complete', 'finished_at': datetime.now(timezone.utc), 'remaining': remaining}})
        return db[RECEIPTS].find_one({'_id': reset_id})
    finally:
        db[RECEIPTS].update_one({'_id': reset_id, 'lease': token}, {'$set': {'lease_until': 0}, '$unset': {'lease': ''}})


def public_receipt(row):
    return {'reset_id': row['_id'], 'phase': row['phase'], 'students': row['students'],
            'counts': row['counts'], 'unlinked_profile_ids': row['unlinked_profile_ids'], 'approval_hash': row['manifest']['sha256'],
            'private_backup_verified': True, 'owner_and_papers_retained': row['phase'] == 'complete'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'apply'])
    parser.add_argument('--writers-paused', action='store_true')
    parser.add_argument('--include-unlinked', action='store_true')
    parser.add_argument('--reset-id')
    parser.add_argument('--approval-hash')
    args = parser.parse_args()
    require_offline(args.writers_paused)
    load_dotenv(ROOT / '.env')
    from tejas_storage import put_object, request
    binding = hashlib.sha256((os.environ['MONGO_URL'] + '\0' + os.environ['DB_NAME']).encode()).hexdigest()
    client = MongoClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    put = lambda blob, owner: {'path': put_object('tejas/student-reset-backups/' + owner + '/' + str(uuid.uuid4()) + '.jsonl.gz', blob, 'application/gzip')}
    fetch = lambda path: request('GET', path).content
    try:
        if args.action == 'prepare':
            receipt = prepare(db, binding, os.environ['ADMIN_EMAIL'], put, fetch, writers_paused=True, include_unlinked=args.include_unlinked)
        else:
            receipt = apply(db, binding, os.environ['ADMIN_EMAIL'], args.reset_id, args.approval_hash, fetch, writers_paused=True)
        print(json.dumps(public_receipt(receipt)), flush=True)
    finally:
        client.close()


if __name__ == '__main__':
    main()
