"""TEST-ONLY iteration 193: owner 'Override whole mock' (POST .../confirm-all), solution-page problems fields, and live ranked
paper guard on BOTH Forgot PIN and signed-in Change PIN (409). Isolated disposable DB (book_publishing_iso170 harness, storage + AI mocked).
Run: cd /app/backend && timeout 280 python tests/override_all_iso193.py
"""
import asyncio, sys, time, uuid, secrets
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import book_publishing_iso170 as T  # noqa: E402,F401
from book_publishing_iso170 import H, mkstaff, client, upload, complete, drain, check, RESULTS  # noqa: E402
from override_guard_iso192 import pdf, J  # noqa: E402
from tejas import structure  # noqa: E402

DB = H.TDB
BM, PG = DB.tejas_book_mocks, DB.tejas_book_pages


async def held(own, sec, tag):
    # Same production reproduction as iteration 192: Q3 ambiguous solution start, Q2 unchecked solution region on page 3.
    raw = pdf().replace(b'OVR', tag.encode()[:3].ljust(3, b'X'))
    b = await upload(own, raw + b'\n%' + uuid.uuid4().hex.encode(), 'TEST_' + tag, section_id=sec); await complete(own, b['id']); await drain()
    bid = b['id']; m = await BM.find_one({'book_id': bid}); mid = m['_id']; base = f'/api/admin/books/{bid}/mocks/{mid}'
    pages = {p['number']: p for p in await PG.find({'book_id': bid}).to_list(None)}
    q1 = next(r for r in pages[1]['regions'] if r['role'] == 'question')
    sol = lambda n, cont, checked, y: {'role': 'solution', 'mock': q1['mock'], 'subject': q1['subject'], 'section': q1.get('section', ''), 'number': n, 'rect': [0.05, y, 0.95, y + 0.1],
                                       'text': f'Solution {n}', 'answer': '', 'option_labels': [], 'option_texts': {}, 'response_type': 'unresolved',
                                       'continuation': cont, 'shared_for': [], 'complete': True, 'checked': checked}
    await PG.update_one({'_id': pages[3]['_id']}, {'$set': {'regions': [sol(3, True, True, 0.2), sol(2, False, False, 0.5)], 'issues': [], 'classification': pages[2].get('classification')}})
    p = J(await own.get(base + '/problems', params={'all': 'true'})); q3 = next(x for x in p['questions'] if x['number'] == 3)
    await own.post(base + '/fix', json={'revision': p['revision'], 'question_id': q3['id'], 'response_type': 'mcq', 'option_labels': ['A', 'B', 'C', 'D'], 'answer': 'B', 'complete': True})
    await drain()
    return bid, mid, base


async def confirm_all_tests(own, rev, sec):
    bid, mid, base = await held(own, sec, 'ALL')
    m = await BM.find_one({'_id': mid}); print('held', m['state'], m['issues'])
    check('setup: mock held with soft issues only', m['state'] == 'held' and m['issues'], m['issues'])
    p = J(await own.get(base + '/problems'))
    check('problems returns total=3', p.get('total') == 3, p.get('total'))
    q2 = next((x for x in p['questions'] if x['number'] == 2), {})
    check('problems Q2 solution_pages contains 3', 3 in q2.get('solution_pages', []), q2)
    rv = p['revision']
    # auth / validation
    r = await client().post(base + '/confirm-all', json={'revision': rv, 'confirm': 'CHECKED'})
    check('anon confirm-all -> 401/403', r.status_code in (401, 403), (r.status_code, r.text[:150]))
    r = await rev.post(base + '/confirm-all', json={'revision': rv, 'confirm': 'CHECKED'})
    check('reviewer confirm-all -> 403', r.status_code == 403, (r.status_code, r.text[:150]))
    r = await own.post(base + '/confirm-all', json={'revision': rv, 'confirm': 'yes'})
    check('wrong confirm -> 422', r.status_code == 422, (r.status_code, r.text[:150]))
    r = await own.post(base + '/confirm-all', json={'revision': rv})
    check('missing confirm -> 422', r.status_code == 422, (r.status_code, r.text[:150]))
    r = await own.post(base + '/confirm-all', json={'revision': rv - 1, 'confirm': 'CHECKED'})
    check('stale revision -> 409', r.status_code == 409 and 'rechecked' in r.text, (r.status_code, r.text[:150]))
    r = await own.post(f'/api/admin/books/{bid}/mocks/nope/confirm-all', json={'revision': rv, 'confirm': 'CHECKED'})
    check('unknown mock -> 404', r.status_code == 404, (r.status_code, r.text[:150]))
    m = await BM.find_one({'_id': mid}); check('rejected calls left confirmed empty', not m.get('confirmed'), m.get('confirmed'))
    # success
    r = await own.post(base + '/confirm-all', json={'revision': rv, 'confirm': 'CHECKED'}); await drain()
    check('owner confirm-all -> 200 + message', r.status_code == 200 and J(r).get('ok') and 'Warnings cleared' in J(r).get('message', ''), (r.status_code, r.text[:200]))
    m = await BM.find_one({'_id': mid})
    keys = [q['coverage_key'] for q in m['questions']]
    check('all 3 coverage keys confirmed, no dupes', sorted(m.get('confirmed', [])) == sorted(keys) and len(set(m['confirmed'])) == 3, (m.get('confirmed'), keys))
    check('soft-only mock becomes ready after recheck', m['state'] == 'ready' and not m['issues'], (m['state'], m['issues']))
    au = await DB.tejas_audit.find_one({'action': 'Book mock owner override'}) if 'tejas_audit' in await DB.list_collection_names() else None
    print('audit row', bool(au))
    # idempotent second call: no duplicate keys
    r = await own.post(base + '/confirm-all', json={'revision': m['revision'], 'confirm': 'CHECKED'}); await drain()
    m = await BM.find_one({'_id': mid})
    check('second confirm-all 200, still 3 keys', r.status_code == 200 and len(m['confirmed']) == 3, (r.status_code, m.get('confirmed')))
    # hard issue survives: blank Q1 key + solution answer
    pages = {pp['number']: pp for pp in await PG.find({'book_id': bid}).to_list(None)}
    for r_ in pages[2]['regions']:
        if r_.get('number') == 1 and r_['role'] in ('key', 'solution'): r_['answer'] = ''
    await PG.update_one({'_id': pages[2]['_id']}, {'$set': {'regions': pages[2]['regions']}})
    m = await BM.find_one({'_id': mid})
    r = await own.post(base + '/confirm-all', json={'revision': m['revision'], 'confirm': 'CHECKED'}); await drain()
    m = await BM.find_one({'_id': mid})
    check('hard issue (missing key) kept after confirm-all', m['state'] == 'held' and any('Q1: missing or conflicting supplied key' in x for x in m['issues']), (m['state'], m['issues']))
    check('only hard issue remains', all('missing or conflicting' in x or 'Q1' in x for x in m['issues']), m['issues'])
    # published mock frozen -> 409
    await BM.update_one({'_id': mid}, {'$set': {'published_generation': m['generation']}})
    m = await BM.find_one({'_id': mid})
    r = await own.post(base + '/confirm-all', json={'revision': m['revision'], 'confirm': 'CHECKED'})
    check('published mock -> 409 frozen', r.status_code == 409 and 'frozen' in r.text, (r.status_code, r.text[:150]))
    # problems: solution-page issue on Q2 card on fresh held mock
    bid2, mid2, base2 = await held(own, sec, 'SOL')
    p = J(await own.get(base2 + '/problems'))
    cards = {x['number']: x for x in p['questions']}
    check('fresh held mock: Q2 card has Page 3 issue + solution_pages [3]', any('Page 3, Q2' in x for x in cards.get(2, {}).get('issues', [])) and 3 in cards.get(2, {}).get('solution_pages', []), cards.get(2))


def num():
    return '95' + f'{secrets.randbelow(10 ** 8):08d}'


async def guard_tests():
    ph = num(); c = client()
    r = await c.post('/api/auth/phone/signup', json={'phone': ph, 'pin': '1357', 'confirm_pin': '1357'}); sid = J(r).get('id')
    check('signup 200', r.status_code == 200, r.text[:200])
    t = time.time(); RES = '/api/auth/pin/reset'; CHG = '/api/auth/pin'
    body = lambda p, x=ph: {'phone': x, 'new_pin': p, 'confirm_pin': p}
    aid = 'TEST_att193_' + uuid.uuid4().hex[:6]
    await DB.tejas_attempts.insert_one({'id': aid, 'user_id': sid, 'set_id': 'x', 'status': 'active', 'competition_end': t + 3600, 'deadline': t + 1800, 'created_at': t})
    r = await client().post(RES, json=body('2468'))
    check('Forgot PIN live -> 409 new message', r.status_code == 409 and 'Forgot PIN works again after that paper ends.' in r.text, (r.status_code, r.text[:200]))
    r = await c.post(CHG, json=body('1122'))
    check('signed-in Change PIN live (deadline future) -> 409', r.status_code == 409 and 'PIN change works again after that paper ends.' in r.text, (r.status_code, r.text[:200]))
    await DB.tejas_attempts.update_one({'id': aid}, {'$set': {'deadline': 0}})
    r = await c.post(CHG, json=body('1122'))
    check('signed-in Change PIN live (deadline 0) -> 409', r.status_code == 409, (r.status_code, r.text[:150]))
    r2 = await client().post('/api/auth/phone', json={'phone': ph, 'pin': '1357'})
    check('old PIN still valid after both 409s', r2.status_code == 200, r2.text[:150])
    me = await c.get('/api/auth/me'); check('session still valid after 409', me.status_code == 200, me.status_code)
    await DB.tejas_attempts.update_one({'id': aid}, {'$set': {'deadline': t - 5}})
    r = await c.post(CHG, json=body('1122')); check('expired deadline -> Change PIN 200', r.status_code == 200, (r.status_code, r.text[:150]))
    await DB.tejas_attempts.update_one({'id': aid}, {'$set': {'deadline': t + 1800, 'competition_end': t - 10}})
    r = await c.post(CHG, json=body('2233')); check('competition ended -> Change PIN 200', r.status_code == 200, (r.status_code, r.text[:150]))
    await DB.tejas_attempts.update_one({'id': aid}, {'$set': {'competition_end': t + 3600, 'status': 'submitted'}})
    r = await c.post(CHG, json=body('3344')); check('submitted attempt -> Change PIN 200', r.status_code == 200, (r.status_code, r.text[:150]))
    r = await client().post(RES, json=body('4455')); check('submitted attempt -> Forgot PIN 200', r.status_code == 200, (r.status_code, r.text[:150]))
    # practice (no competition_end) does not block change
    ph3 = num(); c3 = client(); r = await c3.post('/api/auth/phone/signup', json={'phone': ph3, 'pin': '1357', 'confirm_pin': '1357'})
    await DB.tejas_attempts.update_one({'id': aid}, {'$set': {'status': 'active', 'user_id': J(r).get('id')}, '$unset': {'competition_end': 1}})
    r = await c3.post(CHG, json=body('5791', ph3)); check('practice active -> Change PIN 200', r.status_code == 200, (r.status_code, r.text[:150]))
    # another student's live paper does not block
    ph2 = num(); c2 = client(); await c2.post('/api/auth/phone/signup', json={'phone': ph2, 'pin': '1357', 'confirm_pin': '1357'})
    await DB.tejas_attempts.update_one({'id': aid}, {'$set': {'competition_end': t + 3600, 'deadline': t + 1800}})
    r = await c2.post(CHG, json=body('8642', ph2)); check('other number Change PIN not blocked', r.status_code == 200, (r.status_code, r.text[:150]))


async def main():
    check('no customer DB handles', not H.leftover_real_handles(), H.leftover_real_handles())
    await H.tdbmod.indexes(); await structure.seed()
    own, _ = await mkstaff('owner', 'o'); rev, _ = await mkstaff('reviewer', 'r')
    try:
        r = await own.post('/api/admin/catalog/exams', json={'name': 'OVRY', 'short': 'OY', 'subjects': ['Physics'], 'color': 'rose'})
        slug = J(r).get('slug')
        sec = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Mock Tests', 'description': '', 'layout': 'list', 'kind': 'mocks'})).get('id')
        try: await confirm_all_tests(own, rev, sec)
        except Exception as e: import traceback; traceback.print_exc(); check('confirm-all block crashed', False, repr(e))
        try: await guard_tests()
        except Exception as e: import traceback; traceback.print_exc(); check('guard block crashed', False, repr(e))
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
    failed = [r for r in RESULTS if not r[1]]
    print(f'\nTOTAL {len(RESULTS)} PASS {len(RESULTS) - len(failed)} FAIL {len(failed)}')


if __name__ == '__main__':
    asyncio.run(main())
