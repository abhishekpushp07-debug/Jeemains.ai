"""Restore the 94 published BITSAT chapter tests from the repository's frozen sources (idempotent)."""
import asyncio, hashlib, json, sys, uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / '.env')
import os
from tejas.db import db, sets, files, users, indexes, now
from tejas.auth import seed_owner
from tejas.content import valid_rules
from tejas.chapter_books import books, independent_evidence
from tejas_storage import put_object

DATA = Path('/app/data/chapter50')
PUB = {p['subject'].lower(): p for p in json.loads(Path('/app/test_reports/chapter50_publication.json').read_text())}


async def restore(subject, identity, owner_id):
    raw = (DATA / f'{subject}.pdf').read_bytes()
    result = json.loads((DATA / f'{subject}.parsed.json').read_text())
    sha = hashlib.sha256(raw).hexdigest()
    parsed_sha = hashlib.sha256(json.dumps(result).encode()).hexdigest()
    start = datetime.fromisoformat(PUB[subject]['start_utc']).timestamp()
    fid = str(uuid.uuid5(uuid.UUID(identity), 'source'))
    if not await files.find_one({'id': fid}):
        path = put_object(f'tejas/chapter-books/{identity}/{fid}.pdf', raw)
        await files.insert_one({'id': fid, 'path': path, 'sha256': sha, 'kind': 'combined', 'name': f'{subject}.pdf', 'size': len(raw),
                                'set_id': identity, 'created_at': now(), 'is_deleted': False})
    source = await files.find_one({'id': fid}, {'_id': 0})
    await books.update_one({'id': identity}, {'$setOnInsert': {
        'id': identity, 'title': f'TEJAS200 BITSAT {subject.title()} chapter-wise', 'source': source, 'status': 'ready', 'revision': 1,
        'created_at': start, 'created_by': owner_id, 'subject': result['subject'], 'pages': result['pages'], 'parsed_sha256': parsed_sha,
        'publication_start': start,
        'message': f'{len(result["chapters"])} chapter tests organised. Original PDF images preserve formulas; worked solutions are not supplied.'}}, upsert=True)
    for c in result['chapters']:
        sid = str(uuid.uuid5(uuid.UUID(identity), 'chapter:' + str(c['number'])))
        for q in c['questions']:
            q['id'] = str(uuid.uuid5(uuid.UUID(sid), str(q['number'])))
            for key in ('q_refs', 's_refs'):
                for ref in q[key]:
                    ref['file_id'] = fid
        rules = valid_rules({'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0})
        rules['numeric_rule'] = 'Single-correct MCQ: select A, B, C or D. No numeric-entry questions.'
        s = {'id': sid, 'chapter_book_id': identity, 'chapter_number': c['number'], 'chapter_subject': result['subject'],
             'title': c['title'], 'exam': 'BITSAT', 'year': '', 'source': 'TEJAS200 chapter-wise original practice. Answer keys supplied; no worked solutions.',
             'attribution': 'TEJAS200 · Owner-supplied original practice material', 'questions': c['questions'], 'file_ids': [fid],
             'rules': rules, 'status': 'published', 'version': 1, 'revision': 2, 'created_at': start, 'profile_mode': 'practice', 'audience': 'all',
             'rights_upload': True, 'rights_publish': True, 'rights_report': True, 'rights_attested_by': owner_id,
             'competition': False, 'live_enabled': True, 'solution_kind': 'answer_key_only', 'verification': c['verification'],
             'independent_check': independent_evidence(sha, parsed_sha, c, result['subject']),
             'start_page': c['start_page'], 'end_page': c['end_page'], 'key_page': c['key_page'],
             'start_at': start, 'end_at': start + 365 * 86400, 'published_at': start,
             'expires': datetime.fromtimestamp(start + 365 * 86400, timezone.utc).date().isoformat()}
        await sets.update_one({'id': sid}, {'$setOnInsert': s}, upsert=True)
    return len(result['chapters'])


async def main():
    await indexes()
    await seed_owner()
    owner = await users.find_one({'email': os.environ['ADMIN_EMAIL'].lower()})
    total = 0
    for b in json.loads((DATA / 'imported_books.json').read_text()):
        total += await restore(b['subject'], b['id'], owner['id'])
    checked = await sets.count_documents({'chapter_book_id': {'$exists': True}, 'independent_check': {'$ne': None}, 'live_enabled': True})
    print('chapters', total, 'live+checked', checked)


asyncio.run(main())
