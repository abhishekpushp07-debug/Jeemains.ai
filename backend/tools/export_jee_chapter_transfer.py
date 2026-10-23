import argparse
import asyncio
import gzip
import hashlib
import json
import os
import sys
import tarfile
from pathlib import Path
from dotenv import load_dotenv
from bson import json_util

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / '.env')
from tejas.db import db
from tejas_storage import get_object


def canonical(value):
    return json_util.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default=str(ROOT.parent / 'data' / 'private_transfers' / 'jee_chapters'))
    args = parser.parse_args()
    folder = Path(args.output)
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(folder, 0o700)
    (folder/'pdfs').mkdir(exist_ok=True, mode=0o700)
    manifest = json.loads(Path('/app/data/jee_chapters/import_manifest.json').read_text())
    audit = json.loads(Path('/app/test_reports/jee_chapter_source_audit.json').read_text())
    if audit.get('status') != 'PASS' or len(manifest['books']) != 3:
        raise ValueError('Expected the independently verified three-book manifest.')
    book_ids = [b['id'] for b in manifest['books']]
    set_ids = [c['set_id'] for b in manifest['books'] for c in b['chapters']]
    sets = await db.tejas_sets.find({'id': {'$in': set_ids}}, {'_id': 0}).sort('id', 1).to_list(79)
    books = await db.tejas_chapter_books.find({'id': {'$in': book_ids}}, {'_id': 0}).sort('id', 1).to_list(4)
    if len(sets) != 78 or len(books) != 3 or {s['id'] for s in sets} != set(set_ids):
        raise ValueError('Scoped source records are incomplete or ambiguous.')
    timings = {'Physics': 90, 'Mathematics': 120, 'Chemistry': 70}
    for s in sets:
        proof = next((c for c in audit['chapters'] if c['set_id'] == s['id']), None)
        rules = s['rules']
        if not proof or proof['status'] != 'PASS' or proof['parsed_sha256'] != s['parsed_sha256'] or proof['source_book_sha256'] != s['source_book_sha256']:
            raise ValueError('Source verification proof no longer matches a chapter.')
        if s['exam'] != 'JEE Main' or s.get('test_kind') != 'chapter' or s['status'] != 'published' or not s['live_enabled'] or s.get('series_id'):
            raise ValueError('Only the approved published JEE chapter sets may be transferred.')
        if len(s['questions']) != 50 or [rules.get(k) for k in ('minutes', 'correct', 'wrong', 'skipped')] != [timings[s['chapter_subject']], 4, -1, 0]:
            raise ValueError('Timer or scoring differs from the user-approved configuration.')
        if any(q['solution_kind'] != 'supplied_worked' or not q['approved'] or not q['q_refs'] or not q['s_refs'] for q in s['questions']):
            raise ValueError('Only approved original question/solution pairs may be transferred.')
    file_ids = {f for s in sets for f in s['file_ids']} | {b['source']['id'] for b in books}
    refs = {r['file_id'] for s in sets for q in s['questions'] for k in ('q_refs', 's_refs') for r in q[k]}
    if not refs.issubset(file_ids) or len(file_ids) != 81:
        raise ValueError('Unexpected source file dependencies.')
    files = await db.tejas_files.find({'id': {'$in': list(file_ids)}}, {'_id': 0}).sort('id', 1).to_list(82)
    if len(files) != 81 or any(f.get('is_deleted') or f['set_id'] not in set_ids+book_ids for f in files):
        raise ValueError('Referenced PDF metadata is missing or belongs to unrelated content.')
    expected_pdf_hashes = {b['source']['id']: next(m['source_sha256'] for m in manifest['books'] if m['id'] == b['id']) for b in books}
    expected_pdf_hashes.update({c['source_file_id']: c['source_sha256'] for b in manifest['books'] for c in b['chapters']})
    semaphore = asyncio.Semaphore(4)
    async def export_pdf(f):
        async with semaphore:
            raw = await asyncio.to_thread(get_object, f['path'])
            if not raw.startswith(b'%PDF-') or digest(raw) != f['sha256'] or f['sha256'] != expected_pdf_hashes[f['id']]:
                raise ValueError('Stored source bytes failed hash verification.')
            target = folder/'pdfs'/(f['id']+'.pdf')
            target.write_bytes(raw)
            os.chmod(target, 0o600)
            print('Verified source', f['id'], len(raw), flush=True)
            return len(raw)
    sizes = await asyncio.gather(*(export_pdf(f) for f in files))
    collections = {'tejas_sets': sets, 'tejas_chapter_books': books, 'tejas_files': files}
    hashes = {name: {d['id']: digest(canonical(d)) for d in docs} for name, docs in collections.items()}
    for name, docs in collections.items():
        fresh = await db[name].find({'id': {'$in': [d['id'] for d in docs]}}, {'_id': 0}).to_list(len(docs)+1)
        if {d['id']: digest(canonical(d)) for d in fresh} != hashes[name]:
            raise ValueError('Source content changed during export; do not transfer this snapshot.')
    payload = {'schema': 'jeelive-scoped-jee-content-v1', 'collections': collections, 'record_sha256': hashes,
               'source_manifest': manifest, 'independent_audit': audit,
               'scope': {'books': 3, 'sets': 78, 'questions': 3900, 'solutions': 3900, 'pdfs': 81,
                         'timings': timings, 'correct': 4, 'wrong': -1, 'skipped': 0},
               'target_policy': 'Append only these records. Different existing IDs/hashes must stop the import; identical records may be skipped. Never copy users, sessions, attempts, keys, encrypted vaults, AI records or unrelated data. Stage private, verify every PDF through production storage, then publish only these sets. Preserve existing production data.'}
    metadata = folder/'metadata.json'
    metadata.write_bytes(canonical(payload))
    os.chmod(metadata, 0o600)
    archive = folder/'jee-chapters-transfer.tar.gz'
    with tarfile.open(archive, 'w:gz') as out:
        out.add(metadata, arcname='metadata.json', recursive=False)
        for f in files:
            out.add(folder/'pdfs'/(f['id']+'.pdf'), arcname='pdfs/'+f['id']+'.pdf', recursive=False)
    os.chmod(archive, 0o600)
    summary = {'archive': str(archive), 'sha256': digest(archive.read_bytes()), 'archive_bytes': archive.stat().st_size,
               'pdf_bytes': sum(sizes), 'collections': {name: len(docs) for name, docs in collections.items()}, 'scope': payload['scope'],
               'customer_database_writes': False, 'secret_fields_exported': False}
    (folder/'summary.json').write_text(json.dumps(summary, indent=2))
    os.chmod(folder/'summary.json', 0o600)
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    asyncio.run(main())
