"""Import the TEJAS200 BITSAT 50 full mocks PDF (idempotent). Valid mocks go live; problem mocks stay private with reasons."""
import asyncio, hashlib, re, subprocess, sys, uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / '.env')
import fitz
from tejas.db import sets, files, indexes, users, now
from tejas.auth import seed_owner
from tejas.content import valid_rules
from tejas.mock_books import mock_books
from tejas.mock_parser import parse_mocks, parse_questions, keys_by_layout, keys_by_position, lines, MAIN, BONUS
from tejas_storage import put_object
import os

SOURCE = Path('/app/data/mocks/mocks.pdf')
KEY_START = 1235
END_AT = datetime(2027, 10, 17, 10, 24, 48, 390757, tzinfo=timezone.utc).timestamp()  # same window as chapter tests
OPTIONS = {k: f'See original option {k}' for k in 'ABCD'}


def check(doc, first, qs, k1, k2, parse_issues):
    reasons = list(parse_issues)
    nums = [q['number'] for q in qs]
    main = [q for q in qs if not q['bonus']]
    bonus = [q for q in qs if q['bonus']]
    if nums != list(range(1, MAIN + BONUS + 1)):
        reasons.append(f'Question numbering is not 1–{MAIN + BONUS} in order (found {len(nums)}).')
    if len(main) != MAIN:
        reasons.append(f'Expected {MAIN} main questions, found {len(main)}.')
    if len(bonus) != BONUS:
        reasons.append(f'Expected {BONUS} bonus questions, found {len(bonus)}.')
    if not k1 or len(k1) != MAIN + BONUS:
        reasons.append(f'Answer key incomplete ({len(k1 or {})} of {MAIN + BONUS} keys).')
    elif k1 != k2:
        diff = sorted(n for n in set(k1) | set(k2) if k1.get(n) != k2.get(n))
        reasons.append('Two independent answer-key readings disagree at Q' + ', Q'.join(map(str, diff[:10])) + '.')
    for q in qs:
        if not q['section']:
            reasons.append(f'Q{q["number"]} has no section heading.')
        if not q['q_refs']:
            reasons.append(f'Q{q["number"]} has no readable source region.')
            continue
        text = ''.join(doc[first + r['page'] - 1].get_textbox(fitz.Rect(r['rect'])) for r in q['q_refs'])
        if not all(f'({c})' in text for c in 'ABCD'):
            reasons.append(f'Q{q["number"]}: options A–D are not all readable in its region.')
        for r in q['q_refs']:
            box = fitz.Rect(r['rect'])
            for line, t in lines(doc[first + r['page'] - 1]):
                m = re.match(r'(\d{1,3})\.(\s|$)', t)
                if m and 'Bold' in line['spans'][0]['font'] and line['bbox'][0] < 62 and int(m.group(1)) != q['number'] and box.intersects(fitz.Rect(line['bbox'])):
                    reasons.append(f'Q{q["number"]} region overlaps Q{m.group(1)}.')
    return reasons


async def main():
    await indexes()
    await seed_owner()
    owner = await users.find_one({'email': os.environ['ADMIN_EMAIL'].lower()})
    raw = SOURCE.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    book_id = str(uuid.uuid5(uuid.NAMESPACE_URL, 'tejas200-bitsat-full-mocks:' + sha))
    doc = fitz.open(SOURCE)
    ranges = parse_mocks(doc, KEY_START)
    text = subprocess.run(['pdftotext', '-layout', '-f', str(KEY_START), '-l', str(len(doc)), str(SOURCE), '-'], capture_output=True, text=True, check=True).stdout
    layout_keys, position_keys = keys_by_layout(text), keys_by_position(doc, KEY_START)
    statuses, start = [], now()
    for n in range(1, 51):
        sid = str(uuid.uuid5(uuid.UUID(book_id), f'mock:{n}'))
        title = f'BITSAT Full Mock {n:02d}'
        if n not in ranges:
            statuses.append({'number': n, 'set_id': sid, 'title': title, 'status': 'held', 'reasons': ['Mock pages not found in the PDF.']})
            continue
        first, last = ranges[n]
        qs, issues = parse_questions(doc, first, last)
        k1, k2 = layout_keys.get(n), position_keys.get(n)
        reasons = check(doc, first, qs, k1, k2, issues)
        # Per-mock source PDF keeps crops fast and regions page-local.
        part = fitz.open()
        part.insert_pdf(doc, from_page=first, to_page=last)
        part_raw = part.tobytes(garbage=3, deflate=True)
        fid = str(uuid.uuid5(uuid.UUID(sid), 'source'))
        if not await files.find_one({'id': fid}):
            path = await asyncio.to_thread(put_object, f'tejas/mock-books/{book_id}/{fid}.pdf', part_raw)
            await files.insert_one({'id': fid, 'path': path, 'sha256': hashlib.sha256(part_raw).hexdigest(), 'kind': 'combined',
                'name': f'{title}.pdf', 'size': len(part_raw), 'set_id': sid, 'created_at': now(), 'is_deleted': False})
        questions = []
        for q in qs:
            key = (k1 or {}).get(q['number'], '')
            questions.append({
                'id': str(uuid.uuid5(uuid.UUID(sid), str(q['number']))), 'number': q['number'], 'subject': q['section'] or 'Unlabelled',
                'section': ('Bonus · ' if q['bonus'] else '') + (q['section'] or ''), 'topic': q['section'] or '', 'bonus': q['bonus'],
                'type': 'mcq', 'text': '', 'options': dict(OPTIONS), 'answer': key,
                'solution': f'Supplied answer key: {key}. This book does not contain a worked solution.', 'solution_number': q['number'],
                'render_mode': 'source', 'solution_kind': 'answer_key_only',
                'accessible_text': 'Original PDF question and four options. Formula-safe image; machine text is not a verified accessible transcription.',
                'solution_accessible_text': f'Supplied key {key}; no worked solution provided.',
                'q_refs': [{**r, 'file_id': fid} for r in q['q_refs']], 's_refs': [], 'approved': False, 'issues': []})
        valid = not reasons
        rules = valid_rules({'minutes': 180, 'correct': 3, 'wrong': -1, 'skipped': 0})
        rules['numeric_rule'] = 'Single-correct MCQ: select A, B, C or D. No numeric-entry questions.'
        rules['bonus_rule'] = {'main_count': MAIN, 'bonus_count': BONUS,
            'policy': 'Bonus opens only after all 130 main questions are answered; entering locks every main answer. Same timer and marking.'}
        sections = dict(Counter(q['section'] for q in qs if not q['bonus']))
        s = {'id': sid, 'mock_book_id': book_id, 'mock_number': n, 'title': title, 'exam': 'BITSAT', 'year': '',
             'test_kind': 'mock', 'full_length': True,
             'source': 'TEJAS200 BITSAT full mock (private review edition). Answer keys supplied; no worked solutions.',
             'attribution': 'TEJAS200 · Owner-supplied original practice material', 'questions': questions, 'file_ids': [fid],
             'rules': rules, 'status': 'published' if valid else 'draft', 'version': 1, 'revision': 1, 'created_at': start,
             'profile_mode': 'practice', 'audience': 'all', 'rights_upload': True, 'rights_publish': True, 'rights_report': True,
             'rights_attested_by': owner['id'], 'competition': False, 'live_enabled': valid, 'solution_kind': 'answer_key_only',
             'verification': {'questions': len(qs), 'main': MAIN, 'bonus': BONUS, 'keys': len(k1 or {}), 'key_checks_agree': bool(k1) and k1 == k2,
                              'sections': sections, 'issues': reasons}}
        if valid:
            s.update({'start_at': start, 'end_at': END_AT, 'published_at': start,
                      'expires': datetime.fromtimestamp(END_AT, timezone.utc).date().isoformat()})
        await sets.update_one({'id': sid}, {'$setOnInsert': s}, upsert=True)
        stored = await sets.find_one({'id': sid}, {'status': 1, 'live_enabled': 1})
        statuses.append({'number': n, 'set_id': sid, 'title': title, 'status': 'live' if stored.get('live_enabled') else 'held',
            'reasons': reasons, 'main_count': sum(not q['bonus'] for q in qs), 'bonus_count': sum(q['bonus'] for q in qs),
            'keys': len(k1 or {}), 'sections': sections, 'pages': [first + 1, last + 1]})
    live = sum(x['status'] == 'live' for x in statuses)
    await mock_books.update_one({'id': book_id}, {'$set': {
        'id': book_id, 'title': 'TEJAS200 BITSAT 50 Full Mocks', 'source_name': 'Tejas200_BITSAT_50_Full_Mocks_Combined.pdf',
        'source_sha256': sha, 'pages': len(doc), 'live': live, 'held': len(statuses) - live, 'end_at': END_AT, 'mocks': statuses},
        '$setOnInsert': {'created_at': start}}, upsert=True)
    print('live', live, 'held', len(statuses) - live)
    for x in statuses:
        if x['reasons']:
            print(x['number'], x['reasons'][:3])


asyncio.run(main())
