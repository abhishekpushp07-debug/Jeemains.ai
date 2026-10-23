import argparse
import asyncio
import copy
import hashlib
import json
import os
import sys
import uuid
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / '.env')
from tejas.db import db, sets, files, users, now, audit
from tejas.chapter_books import books, publish_book, ChapterAction
from tejas.content import valid_rules
from tejas.sandbox import organise_pdfs
from tejas_storage import put_object, get_object
import fitz

NAMES = {'chemistry': 'Tejas200_JEE_Main_Chemistry_Revised_Complete.pdf',
         'mathematics': 'Tejas200_JEE_Main_Mathematics_Revised_Complete.pdf',
         'physics': 'Tejas200_JEE_Main_Physics_Revised_Complete.pdf'}
MANIFEST = Path('/app/data/jee_chapters/import_manifest.json')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


async def store_file(fid, sid, name, raw, path):
    old = await files.find_one({'id': fid}, {'_id': 0})
    if old:
        if digest(await asyncio.to_thread(get_object, old['path'])) != old['sha256']:
            raise ValueError('Existing immutable source bytes do not match their stored hash.')
        return old
    saved = await asyncio.to_thread(put_object, path, raw)
    if digest(await asyncio.to_thread(get_object, saved)) != digest(raw):
        raise ValueError('Uploaded source read-back hash mismatch.')
    item = {'id': fid, 'set_id': sid, 'name': name, 'path': saved, 'sha256': digest(raw),
            'size': len(raw), 'kind': 'combined', 'created_at': now(), 'is_deleted': False}
    await files.update_one({'id': fid}, {'$setOnInsert': item}, upsert=True)
    return item


async def stage(subject, directory, principal):
    source_path = directory / (subject+'.pdf')
    raw = source_path.read_bytes()
    identity = str(uuid.uuid5(uuid.NAMESPACE_URL, principal['id']+':chapter:'+digest(raw)))
    result = await organise_pdfs(source_path, chapter_book=True)
    result['source_minutes'] = result['minutes']
    result['minutes'] = {'physics': 90, 'mathematics': 120, 'chemistry': 70}[subject]
    for chapter in result['chapters']:
        chapter['minutes'] = result['minutes']
    parsed_sha = digest(json.dumps(result, sort_keys=True).encode())
    (directory/(subject+'.parsed.json')).write_text(json.dumps(result, ensure_ascii=False))
    if result['exam'] != 'JEE Main' or result['subject'].lower() != subject:
        raise ValueError('Subject identity mismatch.')
    doc = fitz.open(stream=raw, filetype='pdf')
    fid = str(uuid.uuid5(uuid.UUID(identity), 'source'))
    source = await store_file(fid, identity, NAMES[subject], raw, f'tejas/chapter-books/{identity}/{fid}.pdf')
    await books.update_one({'id': identity}, {'$setOnInsert': {'id': identity, 'title': NAMES[subject].removesuffix('.pdf').replace('_', ' '),
        'exam': 'JEE Main', 'source': source, 'status': 'ready', 'revision': 1, 'created_at': now(), 'created_by': principal['id'],
        'subject': result['subject'], 'requested_by_email': 'abhishekpushp07@gmail.com', 'minutes': result['minutes'], 'source_minutes': result['source_minutes'], 'pages': result['pages'], 'parsed_sha256': parsed_sha,
        'solution_kind': 'supplied_worked', 'message': f'{len(result["chapters"])} chapters with supplied worked solutions. Private pending independent source verification.'}}, upsert=True)
    manifest = {'id': identity, 'subject': result['subject'], 'source_name': NAMES[subject], 'source_sha256': digest(raw),
                'parsed_sha256': parsed_sha, 'pages': len(doc), 'minutes': result['minutes'], 'chapters': []}
    for chapter in result['chapters']:
        c = copy.deepcopy(chapter)
        sid = str(uuid.uuid5(uuid.UUID(identity), 'chapter:'+str(c['number'])))
        part = fitz.open()
        part.insert_pdf(doc, from_page=c['start_page']-1, to_page=c['end_page']-1)
        part_raw = part.tobytes(garbage=3, deflate=True, no_new_id=True)
        cfid = str(uuid.uuid5(uuid.UUID(sid), 'source'))
        file = await store_file(cfid, sid, f'{result["subject"]} - {c["title"]}.pdf', part_raw, f'tejas/chapter-books/{identity}/{cfid}.pdf')
        for q in c['questions']:
            q['id'] = str(uuid.uuid5(uuid.UUID(sid), str(q['number'])))
            for key in ('q_refs', 's_refs'):
                for ref in q[key]:
                    ref['page'] -= c['start_page']-1
                    ref['file_id'] = cfid
        rules = valid_rules({'minutes': result['minutes'], 'correct': 4, 'wrong': -1, 'skipped': 0})
        rules['numeric_rule'] = 'MCQ and integer responses both score +4 correct, −1 wrong and 0 unanswered. Integer answers are exact. The source’s 10-mark teaching rubric does not change test marks.'
        item = {'id': sid, 'chapter_book_id': identity, 'chapter_number': c['number'], 'chapter_subject': result['subject'],
            'title': c['title'], 'exam': 'JEE Main', 'test_kind': 'chapter', 'year': '', 'source': 'Owner-supplied TEJAS200 JEE Main chapter questions with supplied worked solutions.',
            'attribution': 'TEJAS200 · User-supplied source PDF', 'questions': c['questions'], 'file_ids': [cfid], 'rules': rules,
            'status': 'draft', 'version': 1, 'revision': 1, 'created_at': now(), 'profile_mode': 'practice', 'audience': 'all',
            'rights_upload': True, 'rights_publish': True, 'rights_report': True, 'rights_attested_by': principal['id'],
            'rights_note': 'Requested by abhishekpushp07@gmail.com: user supplied these PDFs and explicitly requested publication under JEE Main chapter practice with original solutions.',
            'competition': False, 'live_enabled': False, 'solution_kind': 'supplied_worked', 'verification': c['verification'],
            'independent_check': None, 'start_page': c['start_page'], 'end_page': c['end_page'], 'key_page': c['key_page'],
            'source_book_sha256': digest(raw), 'parsed_sha256': parsed_sha,
            'source_minutes': result['source_minutes'], 'timer_note': 'Owner-approved online duration overrides the printed PDF timer; original PDF and worked solutions are unchanged.'}
        await sets.update_one({'id': sid}, {'$setOnInsert': item}, upsert=True)
        manifest['chapters'].append({'set_id': sid, 'number': c['number'], 'title': c['title'], 'source_file_id': cfid,
                                    'source_sha256': file['sha256'], 'questions': 50, 'start_page': c['start_page'], 'end_page': c['end_page']})
        print(subject, c['number'], c['title'], 'private', flush=True)
    await audit(principal['id'], 'User-requested JEE chapters staged', identity, f'{len(result["chapters"])} chapters; +4/−1/0; supplied solutions only; no AI')
    return manifest


async def publish(report, principal):
    evidence = json.loads(report.read_text())
    manifest = json.loads(MANIFEST.read_text())
    if evidence.get('status') != 'PASS': raise ValueError('Independent source audit has not passed.')
    for book in manifest['books']:
        rows = [e for e in evidence['chapters'] if e.get('book_id') == book['id']]
        if len(rows) != len(book['chapters']): raise ValueError('Independent report does not cover every chapter.')
        for c in book['chapters']:
            row = next((r for r in rows if r['set_id'] == c['set_id']), None)
            if not row or row.get('status') != 'PASS' or row.get('keys_checked') != 50 or row.get('solutions_checked') != 50 or row.get('issues'):
                raise ValueError('A chapter failed independent source verification.')
            if row['source_book_sha256'] != book['source_sha256'] or row['parsed_sha256'] != book['parsed_sha256'] or row['chapter_source_sha256'] != c['source_sha256']:
                raise ValueError('Independent evidence belongs to different immutable bytes.')
        for c in book['chapters']:
            row = next(r for r in rows if r['set_id'] == c['set_id'])
            await sets.update_one({'id': c['set_id'], 'source_book_sha256': book['source_sha256'], 'parsed_sha256': book['parsed_sha256'], 'independent_check': None},
                {'$set': {'independent_check': {'method': 'Independent source/region audit', 'scope': '50 source keys and supplied solution pairings; not academic certification',
                    'source_sha256': book['source_sha256'], 'parsed_sha256': book['parsed_sha256'], 'chapter_source_sha256': c['source_sha256'],
                    'checked_at': now(), 'report': str(report), 'keys_checked': 50, 'solutions_checked': 50}}})
        r = await books.find_one({'id': book['id']}, {'_id': 0})
        await publish_book(book['id'], ChapterAction(revision=r['revision']), principal)
        await books.update_one({'id': book['id']}, {'$set': {'message': f'{len(book["chapters"])} JEE Main chapter tests published with independently checked supplied questions and solutions. No AI generation.'}})
        print('Published', book['subject'], len(book['chapters']), flush=True)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', default='/tmp/jee_chapter_import')
    parser.add_argument('--publish-report')
    args = parser.parse_args()
    principal = await users.find_one({'email': 'abhishekpushp07@gmail.com', 'role': 'owner'}, {'_id': 0, 'id': 1, 'email': 1, 'role': 1})
    if not principal:
        principal = await users.find_one({'email': os.environ['ADMIN_EMAIL'].lower(), 'role': 'owner'}, {'_id': 0, 'id': 1, 'email': 1, 'role': 1})
    if not principal: raise ValueError('No existing authorized owner account was found; credentials are unchanged.')
    if args.publish_report:
        await publish(Path(args.publish_report), principal)
        return
    before = {name: await db[name].count_documents({}) for name in ('tejas_sets', 'tejas_attempts', 'tejas_ai_solutions', 'tejas_manual_solves')}
    results = []
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    for subject in NAMES:
        results.append(await stage(subject, Path(args.directory), principal))
        MANIFEST.write_text(json.dumps({'books': results, 'baseline_counts': before, 'updated_at': now()}, indent=2))
    print('STAGED', sum(len(b['chapters']) for b in results), 'chapters; no tests published yet.', flush=True)


if __name__ == '__main__':
    asyncio.run(main())
