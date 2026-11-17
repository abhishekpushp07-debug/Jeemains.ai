"""TEST-ONLY iteration 192: owner per-question Override (fix confirmed:true) for held book mocks, problems attaching
solution-page issues to their question, reviewer 403, and Forgot PIN live ranked paper guard (409).
Isolated disposable DB (book_publishing_iso170 harness, storage + AI mocked).
Run: cd /app/backend && timeout 280 python tests/override_guard_iso192.py
"""
import asyncio, sys, time, uuid, secrets
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fitz  # noqa: E402
import book_publishing_iso170 as T  # noqa: E402,F401
from book_publishing_iso170 import H, mkstaff, client, upload, complete, drain, check, RESULTS  # noqa: E402
from tejas import structure  # noqa: E402

DB = H.TDB
BM, PG = DB.tejas_book_mocks, DB.tejas_book_pages


def J(r):
    try: d = r.json()
    except Exception: return {}
    return d if d is not None else {}


def pdf():
    doc = fitz.open(); p = doc.new_page(); p.insert_text((40, 60), 'Physics', fontsize=13); y = 100
    qs = [(1, 'OVR a ball falls 20 m. Find time.', ['1 s', '2 s', '3 s', '4 s']), (2, 'OVR a car speed is', ['1 m/s', '2 m/s', '3 m/s', '4 m/s']),
          (3, 'OVR unit of force is', ['joule', 'newton', 'watt', 'pascal'])]
    for num, text, opts in qs:
        p.insert_text((40, y), f'Q{num}. {text}', fontsize=11); y += 20
        for lab, o in zip('ABCD', opts): p.insert_text((60, y), f'({lab}) {o}', fontsize=11); y += 18
        y += 22
    p = doc.new_page(); p.insert_text((40, 60), 'Answer Key', fontsize=13); y = 100
    for num, ans in [(1, 'B'), (2, 'B'), (3, 'B')]: p.insert_text((40, y), f'Q{num}. ({ans})', fontsize=11); y += 20
    p = doc.new_page(); p.insert_text((40, 60), 'Worked notes page', fontsize=13)
    raw = doc.tobytes(); doc.close(); return raw


async def override_tests(own, rev, sec):
    b = await upload(own, pdf(), 'TEST_Override192', section_id=sec); await complete(own, b['id']); await drain()
    bid = b['id']; m = await BM.find_one({'book_id': bid}) or {}; mid = m.get('_id'); base = f'/api/admin/books/{bid}/mocks/{mid}'
    print('initial', m.get('state'), m.get('issues'), [(q['original_number'], q['subject'], q['source_regions']) for q in m.get('questions', [])][:3])
    pages = {p['number']: p for p in await PG.find({'book_id': bid}).to_list(None)}
    print('pages', {n: [(r['role'], r.get('number'), r.get('mock')) for r in p.get('regions', [])] for n, p in pages.items()})
    q1 = next(r for r in pages[1]['regions'] if r['role'] == 'question')
    label, subj, sect = q1['mock'], q1['subject'], q1.get('section', '')
    sol = lambda n, cont, checked, y: {'role': 'solution', 'mock': label, 'subject': subj, 'section': sect, 'number': n, 'rect': [0.05, y, 0.95, y + 0.1],
                                       'text': f'Solution {n}', 'answer': '', 'option_labels': [], 'option_texts': {}, 'response_type': 'unresolved',
                                       'continuation': cont, 'shared_for': [], 'complete': True, 'checked': checked}
    # Production RCA: Q3 solution is a lone continuation (ambiguous start); Q2 solution region on the solution page is unchecked.
    regs = [r for r in pages[3].get('regions', []) if r['role'] != 'ignore'] + [sol(3, True, True, 0.2), sol(2, False, False, 0.5)]
    await PG.update_one({'_id': pages[3]['_id']}, {'$set': {'regions': regs, 'issues': [], 'classification': pages[2].get('classification')}})
    p = J(await own.get(base + '/problems', params={'all': 'true'}))
    q3 = next(x for x in p['questions'] if x['number'] == 3); q2 = next(x for x in p['questions'] if x['number'] == 2)
    fix = lambda q, rv, **x: {'revision': rv, 'question_id': q['id'], 'response_type': 'mcq', 'option_labels': ['A', 'B', 'C', 'D'], 'answer': 'B', 'complete': True, **x}
    # 1. old behaviour (confirmed false) -> rebuild re-adds the same issues (reproduces the loop)
    r = await own.post(base + '/fix', json=fix(q3, p['revision'])); await drain()
    m = await BM.find_one({'_id': mid})
    check('confirmed:false fix 200', r.status_code == 200, r.text[:200])
    amb = [x for x in m['issues'] if 'Q3: ambiguous worked-solution' in x]; rev2 = [x for x in m['issues'] if x.startswith('Page 3, Q2: source region needs review')]
    check('repro: mock held with Q3 ambiguous + Page 3 Q2 unchecked', m['state'] == 'held' and amb and rev2, (m['state'], m['issues']))
    check('confirmed list empty after plain fix', not m.get('confirmed'), m.get('confirmed'))
    # 2. problems attaches the solution-page issue to Q2's card, returns confirmed
    p = J(await own.get(base + '/problems'))
    cards = {x['number']: x for x in p.get('questions', [])}
    check('problems: Q2 card carries Page 3 solution-page issue', any('Page 3, Q2' in x for x in cards.get(2, {}).get('issues', [])), (cards.get(2), p.get('general')))
    check('problems: Page 3 Q2 issue not in general', not any('Page 3, Q2' in x for x in p.get('general', [])), p.get('general'))
    check('problems: Q3 card carries ambiguous issue', any('ambiguous' in x for x in cards.get(3, {}).get('issues', [])), cards.get(3))
    check('problems: confirmed field false per question', all(x.get('confirmed') is False for x in p['questions']), [(x['number'], x.get('confirmed')) for x in p['questions']])
    # 3. reviewer confirmed:true -> 403; reviewer confirmed:false works
    rp = J(await rev.get(base + '/problems'))
    check('reviewer sees held problems', rp.get('state') == 'held', rp.get('state'))
    r = await rev.post(base + '/fix', json=fix(cards[3], p['revision'], confirmed=True))
    check('reviewer confirmed:true -> 403', r.status_code == 403 and 'Only the owner' in r.text, (r.status_code, r.text[:200]))
    m = await BM.find_one({'_id': mid}); check('403 did not touch confirmed', not m.get('confirmed'), m.get('confirmed'))
    r = await rev.post(base + '/fix', json=fix(cards[3], p['revision'], confirmed=False)); await drain()
    check('reviewer confirmed:false -> 200', r.status_code == 200, (r.status_code, r.text[:200]))
    # 4. owner override Q3 -> ambiguous issue gone, Q2 still holds
    p = J(await own.get(base + '/problems')); cards = {x['number']: x for x in p.get('questions', [])}
    r = await own.post(base + '/fix', json=fix(cards[3], p['revision'], confirmed=True)); await drain()
    m = await BM.find_one({'_id': mid})
    check('owner confirmed:true Q3 -> 200', r.status_code == 200, (r.status_code, r.text[:200]))
    check('Q3 coverage key stored in confirmed', any(k.endswith('|3') for k in m.get('confirmed', [])), m.get('confirmed'))
    check('Q3 ambiguous issue dropped after rebuild', not any('Q3: ambiguous' in x for x in m['issues']), m['issues'])
    check('Q2 issue still holds the mock', m['state'] == 'held' and any('Q2' in x for x in m['issues']), (m['state'], m['issues']))
    p = J(await own.get(base + '/problems', params={'all': 'true'}))
    check('problems all=true Q3 confirmed true', next(x for x in p['questions'] if x['number'] == 3).get('confirmed') is True, [(x['number'], x.get('confirmed')) for x in p['questions']])
    # 5. owner override Q2 -> its issue gone; Q1 'original solution expected' (soft, caused by mixed book) remains
    q2 = next(x for x in p['questions'] if x['number'] == 2)
    r = await own.post(base + '/fix', json=fix(q2, p['revision'], confirmed=True)); await drain()
    m = await BM.find_one({'_id': mid})
    check('owner confirmed:true Q2 -> no Q2/Q3 issues left', r.status_code == 200 and not any(('Q2' in x or 'Q3' in x) for x in m['issues']), (r.status_code, m['state'], m['issues']))
    print('after Q2 override', m['state'], m['issues'])
    p = J(await own.get(base + '/problems', params={'all': 'true'})); q1c = next(x for x in p['questions'] if x['number'] == 1)
    r = await own.post(base + '/fix', json=fix(q1c, p['revision'], confirmed=True)); await drain()
    m = await BM.find_one({'_id': mid})
    check('owner confirmed:true Q1 (original solution expected) -> mock ready', r.status_code == 200 and m['state'] == 'ready', (r.status_code, m['state'], m['issues']))
    check('confirmed has 3 keys, no duplicates', len(m.get('confirmed', [])) == len(set(m.get('confirmed', []))) == 3, m.get('confirmed'))
    # 6. hard issue survives override: conflicting key (Q1 key blank + solution with no answer) -> keep 'missing or conflicting supplied key'
    pages = {pp['number']: pp for pp in await PG.find({'book_id': bid}).to_list(None)}
    for r_ in pages[2]['regions']:
        if r_.get('number') == 1 and r_['role'] in ('key', 'solution'): r_['answer'] = ''
    await PG.update_one({'_id': pages[2]['_id']}, {'$set': {'regions': pages[2]['regions']}})
    p = J(await own.get(base + '/problems', params={'all': 'true'}))
    q2 = next(x for x in p['questions'] if x['number'] == 2)
    r = await own.post(base + '/fix', json=fix(q2, p['revision'], confirmed=True)); await drain()  # triggers a rebuild
    m = await BM.find_one({'_id': mid})
    check('hard issue (missing key) kept despite Q1 confirmed', m['state'] == 'held' and any('Q1: missing or conflicting supplied key' in x for x in m['issues']), (m['state'], m['issues']))
    return bid, mid


def num():
    return '95' + f'{secrets.randbelow(10 ** 8):08d}'


async def guard_tests():
    ph = num(); c = client()
    r = await c.post('/api/auth/phone/signup', json={'phone': ph, 'pin': '1357', 'confirm_pin': '1357'}); sid = J(r).get('id')
    check('signup 200', r.status_code == 200, r.text[:200])
    t = time.time(); RES = '/api/auth/pin/reset'
    body = lambda p: {'phone': ph, 'new_pin': p, 'confirm_pin': p}
    aid = 'TEST_att192_' + uuid.uuid4().hex[:6]
    await DB.tejas_attempts.insert_one({'id': aid, 'user_id': sid, 'set_id': 'x', 'status': 'active', 'competition_end': t + 3600, 'deadline': t + 1800, 'created_at': t})
    r = await client().post(RES, json=body('2468'))
    check('live paper (deadline future) -> 409 message', r.status_code == 409 and 'A live ranked paper is running on this number' in r.text, (r.status_code, r.text[:200]))
    _, r2 = None, await client().post('/api/auth/phone', json={'phone': ph, 'pin': '1357'})
    check('PIN unchanged after 409', r2.status_code == 200, r2.text[:150])
    await DB.tejas_attempts.update_one({'id': aid}, {'$set': {'deadline': 0}})
    r = await client().post(RES, json=body('2468')); check('live paper deadline 0 -> 409', r.status_code == 409, (r.status_code, r.text[:150]))
    r = await c.post('/api/auth/pin', json={'phone': ph, 'new_pin': '1122', 'confirm_pin': '1122'})
    check('signed-in Change PIN not blocked by live paper', r.status_code == 200, (r.status_code, r.text[:200]))
    await DB.tejas_attempts.update_one({'id': aid}, {'$set': {'deadline': t - 5}})
    r = await client().post(RES, json=body('2468')); check('expired deadline -> reset 200', r.status_code == 200 and J(r).get('id') == sid, (r.status_code, r.text[:150]))
    await DB.tejas_attempts.update_one({'id': aid}, {'$set': {'deadline': t + 1800, 'competition_end': t - 10}})
    r = await client().post(RES, json=body('3579')); check('competition ended -> reset 200', r.status_code == 200, (r.status_code, r.text[:150]))
    await DB.tejas_attempts.update_one({'id': aid}, {'$set': {'competition_end': t + 3600, 'status': 'submitted'}})
    r = await client().post(RES, json=body('4680')); check('submitted attempt -> reset 200', r.status_code == 200, (r.status_code, r.text[:150]))
    ph3 = num(); r = await client().post('/api/auth/phone/signup', json={'phone': ph3, 'pin': '1357', 'confirm_pin': '1357'})
    await DB.tejas_attempts.update_one({'id': aid}, {'$set': {'status': 'active', 'user_id': J(r).get('id')}, '$unset': {'competition_end': 1}})
    r = await client().post(RES, json={'phone': ph3, 'new_pin': '5791', 'confirm_pin': '5791'}); check('practice (no competition_end) active -> reset 200', r.status_code == 200, (r.status_code, r.text[:150]))
    # other student's live paper does not block
    ph2 = num(); r = await client().post('/api/auth/phone/signup', json={'phone': ph2, 'pin': '1357', 'confirm_pin': '1357'})
    await DB.tejas_attempts.update_one({'id': aid}, {'$set': {'competition_end': t + 3600, 'deadline': t + 1800}})
    r = await client().post(RES, json={'phone': ph2, 'new_pin': '8642', 'confirm_pin': '8642'})
    check('other number not blocked by someone else live paper', r.status_code == 200, (r.status_code, r.text[:150]))


async def main():
    check('no customer DB handles', not H.leftover_real_handles(), H.leftover_real_handles())
    await H.tdbmod.indexes(); await structure.seed()
    own, _ = await mkstaff('owner', 'o'); rev, _ = await mkstaff('reviewer', 'r')
    try:
        r = await own.post('/api/admin/catalog/exams', json={'name': 'OVRX', 'short': 'OX', 'subjects': ['Physics'], 'color': 'rose'})
        slug = J(r).get('slug')
        sec = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Mock Tests', 'description': '', 'layout': 'list', 'kind': 'mocks'})).get('id')
        try: await override_tests(own, rev, sec)
        except Exception as e: import traceback; traceback.print_exc(); check('override block crashed', False, repr(e))
        try: await guard_tests()
        except Exception as e: import traceback; traceback.print_exc(); check('guard block crashed', False, repr(e))
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
    failed = [r for r in RESULTS if not r[1]]
    print(f'\nTOTAL {len(RESULTS)} PASS {len(RESULTS) - len(failed)} FAIL {len(failed)}')


if __name__ == '__main__':
    asyncio.run(main())
