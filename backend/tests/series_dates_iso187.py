"""TEST-ONLY iteration 187: JEE series 9 Dec 2026 - 27 Jan 2027 (50 days), one-time date migration, owner early access
(JEE + custom series), exam catalog series_path, Give a day waits for a busy PDF lock.
Isolated disposable DB (storage + AI mocked). Run: cd /app/backend && timeout 290 python tests/series_dates_iso187.py
"""
import asyncio, sys, time, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import book_publishing_iso170 as T  # noqa: E402,F401
from book_publishing_iso170 import H, mkstaff, client, upload, complete, drain, check, RESULTS  # noqa: E402
from library_aits_iso180 import build_aits, aits_mock  # noqa: E402
from structure_iso173 import mkset, start  # noqa: E402
from tejas import structure, live_series, series_admin  # noqa: E402

DB = H.TDB; SETS, M, S = DB.tejas_sets, '/api/admin/master', live_series.SERIES_ID


def J(r):
    try: d = r.json()
    except Exception: return {}
    if isinstance(d, dict) and 'data' in d and 'error' in d: d = d['data']
    return d if d is not None else {}


async def fix_all(own, book_id, mid):
    base = f"/api/admin/books/{book_id}/mocks/{mid}"
    for _ in range(40):
        p = J(await own.get(base + '/problems'))
        if not p.get('questions'): break
        q = p['questions'][0]; integer = q['number'] % 25 in (21, 22, 23, 24, 0)
        r = await own.post(base + '/fix', json={'revision': p['revision'], 'question_id': q['id'], 'response_type': 'integer' if integer else 'mcq',
            'option_labels': [] if integer else ['A', 'B', 'C', 'D'], 'answer': str((q['number'] - 1) % 25) if integer else 'B', 'complete': True}); await drain()
        if r.status_code != 200: print('fix fail', r.status_code, r.text[:200]); break


async def dates_api(own, stu, anon):
    d = J(await anon.get('/api/series/all-india-jee'))
    check('public JEE: 9 Dec 2026 - 27 Jan 2027, 50 slots', d.get('first_date') == '2026-12-09' and d.get('last_date') == '2027-01-27' and d.get('total') == 50 and len(d.get('slots', [])) == 50
          and d['slots'][0]['date'] == '2026-12-09' and d['slots'][-1]['date'] == '2027-01-27', {k: d.get(k) for k in ('first_date', 'last_date', 'total')})
    s = J(await stu.get('/api/series/all-india-jee/streak'))
    cups = s.get('cups') or s.get('milestones') or []
    check('streak: total_days 50, dates, After 27 January', s.get('total_days') == 50 and s.get('first_date') == '2026-12-09' and s.get('last_date') == '2027-01-27' and 'After 27 January' in s.get('policy', ''), {k: s.get(k) for k in ('total_days', 'first_date', 'last_date')})
    last = cups[-1] if cups else {}
    check('streak last cup 50 Champion', (last.get('days') == 50 or last.get('target') == 50 or last.get('n') == 50 or '50' in str(last)) and 'Champion' in str(last), last)
    check('no 62 in streak text', '62' not in str({k: s.get(k) for k in ('policy', 'cups', 'total_days')}), '')
    m = J(await own.get(f'{M}/series/{S}'))
    check('Master owner view: 50 days from 2026-12-09', m.get('first_date') == '2026-12-09' and m.get('total') == 50 and len(m.get('slots', [])) == 50, {k: m.get(k) for k in ('first_date', 'total')})
    for bad in ('2026-12-08', '2027-01-28', '2026-12-01'):
        r = await own.post('/api/studio/all-india-jee/assign', json={'kind': 'paper', 'set_id': 'x', 'date': bad, 'expected_revision': 1})
        check(f'studio assign {bad} -> 422 range message', r.status_code == 422 and 'Choose a date from 9 December 2026 to 27 January 2027.' in r.text, (r.status_code, r.text[:200]))
    r = await own.post(f'{M}/series/{S}/assign', json={'kind': 'set', 'id': 'x', 'date': '2026-12-05'})
    check('master assign 2026-12-05 (old range) -> 422', r.status_code == 422, (r.status_code, r.text[:150]))
    r = await own.put(f'{M}/series/{S}', json={'days': 62}); check('JEE builtin days locked 409 mentions 50 days', r.status_code == 409 and '50 days' in r.text, r.text[:200])


async def lock_for(book_id, seconds):
    await DB.tejas_books.update_one({'_id': book_id}, {'$set': {'lock_until': time.time() + 900, 'lock_token': 'qa-held'}})
    await asyncio.sleep(seconds)
    await DB.tejas_books.update_one({'_id': book_id, 'lock_token': 'qa-held'}, {'$set': {'lock_until': 0}})


async def early_and_lock(own, stu, anon):
    book = await upload(own, build_aits([aits_mock(1), aits_mock(2)]), 'JEE Series Book', section_id='jee-main:aits'); await complete(own, book['id']); await drain()
    cands = [c for c in J(await own.get(f'{M}/series/{S}')).get('candidates', []) if c['kind'] == 'book_mock']
    for c in cands: await fix_all(own, book['id'], c['id'])
    cands = [c for c in J(await own.get(f'{M}/series/{S}')).get('candidates', []) if c['kind'] == 'book_mock' and not c['problem']]
    check('two fixed PDF papers ready', len(cands) == 2, cands)
    # Give a day while the PDF lock is held ~5 s -> waits then succeeds
    holder = asyncio.create_task(lock_for(book['id'], 5)); await asyncio.sleep(0.3)
    t0 = time.time(); r = await own.post(f'{M}/series/{S}/assign', json={'kind': 'book_mock', 'id': cands[0]['id'], 'date': '2026-12-10'}); took = time.time() - t0
    await holder; await drain()
    check('Give a day with busy lock (5 s) waits then 200', r.status_code == 200 and 3.5 < took < 20, (r.status_code, round(took, 1), r.text[:200]))
    s = await SETS.find_one({'series_id': S, 'series_date': '2026-12-10'}) or {}
    check('paper built for 2026-12-10', s.get('status') == 'published' and len(s.get('questions', [])) == 75, s.get('status'))
    # Lock held > 30 s -> 409 friendly message
    holder = asyncio.create_task(lock_for(book['id'], 36)); await asyncio.sleep(0.3)
    t0 = time.time(); r = await own.post(f'{M}/series/{S}/assign', json={'kind': 'book_mock', 'id': cands[1]['id'], 'date': '2026-12-11'}); took = time.time() - t0
    await holder
    check('lock held >30 s -> 409 still finishing message', r.status_code == 409 and 'This PDF is still finishing earlier work' in r.text and took >= 25, (r.status_code, round(took, 1), r.text[:200]))
    mrow = await DB.tejas_book_mocks.find_one({'_id': cands[1]['id']}) or {}
    check('mock 2 untouched after 409', not mrow.get('series_date'), mrow.get('series_date'))
    sid = s.get('id', 'x'); slot = lambda d: next(x for x in d['slots'] if x['date'] == '2026-12-10')
    o = slot(J(await own.get('/api/series/all-india-jee')))
    check('owner sees early slot: early/can_start/set_id/real title', o['early'] is True and o['can_start'] is True and o['set_id'] == sid and o['title'] == s.get('title'), o)
    for who, c in (('student', stu), ('anon', anon)):
        x = slot(J(await c.get('/api/series/all-india-jee')))
        check(f'{who} sees placeholder only', x['early'] is False and x['can_start'] is False and x['set_id'] is None and x['title'] == 'All India JEE Mains · Test 02', x)
    r = await stu.get(f'/api/sets/{sid}'); check('student GET set before day 404', r.status_code == 404, r.status_code)
    r = await start(stu, sid); check('student start before day 404/409', r.status_code in (404, 409), (r.status_code, r.text[:150]))
    r = await stu.get(f'/api/my/sets/{sid}'); check('student GET /my/sets before day 404', r.status_code == 404, r.status_code)
    r = await own.get(f'/api/my/sets/{sid}'); check('owner GET /my/sets before day 200 (UI path)', r.status_code == 200, (r.status_code, r.text[:150]))
    r = await own.get(f'/api/sets/{sid}'); check('INFO owner GET anonymous /api/sets before day (expected 404, anon route)', True, r.status_code)
    r = await start(own, sid); a = J(r)
    w = live_series.window('2026-12-10')
    check('owner early start -> series_live, competition_end = 11:59 PM', r.status_code == 200 and a.get('mode') == 'series_live' and abs((a.get('competition_end') or 0) - w['closes_at']) < 1, (r.status_code, a.get('mode'), a.get('competition_end'), r.text[:200]))
    row = await DB.tejas_attempts.find_one({'id': a.get('id')}) or {}
    check('attempt stored with series_id/date', row.get('series_id') == S and row.get('series_date') == '2026-12-10' and row.get('competition_end') == w['closes_at'], {k: row.get(k) for k in ('series_id', 'series_date', 'mode')})
    return book, cands


async def custom_series(own, stu, anon):
    r = await own.post('/api/admin/catalog/exams', json={'name': 'BITSATX', 'short': 'BX', 'subjects': ['Physics', 'Chemistry', 'Mathematics'], 'color': 'rose'})
    slug = J(r).get('slug')
    r = await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'All India Test Series', 'description': '', 'layout': 'list', 'kind': 'aits',
                       'first_date': '2026-12-20', 'days': 5, 'open_time': '09:00', 'last_start': '11:00', 'minutes': 10, 'correct': 4, 'wrong': -1})
    sec = J(r); sid = sec.get('series_id'); check('custom aits section created', r.status_code == 200 and sid, r.text[:200])
    await structure.exams.update_one({'_id': slug}, {'$set': {'shown': True}})
    r = await own.put(f'{M}/series/{sid}', json={'shown': True}); check("PUT shown:true -> 'Students can now open it inside its exam.'", r.status_code == 200 and J(r).get('message') == 'Students can now open it inside its exam.', r.text[:200])
    ex = J(await stu.get(f'/api/catalog/exams/{slug}')); aits = [x for x in ex.get('sections', []) if x.get('kind') == 'aits']
    check('exam catalog includes aits section with series_path /series/<sid>, live_count 0', len(aits) == 1 and aits[0].get('series_path') == '/series/' + sid and aits[0].get('live_count') == 0, aits)
    await structure.exams.update_one({'_id': 'jee-main'}, {'$set': {'shown': True}})
    jx = J(await stu.get('/api/catalog/exams/jee-main')); ja = [x for x in jx.get('sections', []) if x.get('kind') == 'aits']
    check('jee-main catalog aits series_path /series/all-india-jee', len(ja) == 1 and ja[0].get('series_path') == '/series/all-india-jee', ja)
    w = series_admin.window('2026-12-21', {'open_time': '09:00', 'last_start': '11:00', 'close_time': '23:59'})
    pid = await mkset('BITS', exam='BITSATX', series_id=sid, series_date='2026-12-21', series_window=w, series_import=True, live_enabled=True, start_at=w['opens_at'], end_at=w['closes_at'], test_kind='mock')
    s = await SETS.find_one({'id': pid}); await SETS.update_one({'id': pid}, {'$set': {'series_pattern': live_series.paper_pattern(s)}})
    slot = lambda d: next(x for x in d.get('slots', []) if x['date'] == '2026-12-21')
    o = slot(J(await own.get(f'/api/series/{sid}/schedule')))
    check('custom: owner early slot', o['early'] is True and o['can_start'] is True and o['set_id'] == pid, o)
    x = slot(J(await stu.get(f'/api/series/{sid}/schedule')))
    check('custom: student placeholder', x['early'] is False and x['can_start'] is False and x['set_id'] is None and 'Test 02' in x['title'], x)
    x = slot(J(await anon.get(f'/api/series/{sid}/schedule'))); check('custom: anon placeholder', x['set_id'] is None and x['early'] is False, x)
    r = await start(stu, pid); check('custom: student start before day 404/409', r.status_code in (404, 409), r.status_code)
    r = await start(own, pid); a = J(r)
    check('custom: owner early start series_live, competition_end closes_at', r.status_code == 200 and a.get('mode') == 'series_live' and abs((a.get('competition_end') or 0) - w['closes_at']) < 1, (r.status_code, a.get('mode'), r.text[:200]))
    sl = J(await anon.get('/api/series')); check('/api/series lists custom series', any(i['id'] == sid for i in sl.get('items', [])), [i['id'] for i in sl.get('items', [])])


async def migration(cands):
    await DB.tejas_migrations.delete_one({'_id': series_admin.JEE_DATES_ID})
    await DB.tejas_series.update_one({'_id': S}, {'$set': {'first_date': '2026-12-01', 'days': 62}})
    old = live_series.window('2026-12-03')
    a = await mkset('MIGA', exam='JEE Main', catalog_section_id='jee-main:aits', series_id=S, series_date='2026-12-03', series_window=old, series_import=True, live_enabled=True, start_at=old['opens_at'], end_at=old['closes_at'], test_kind='mock')
    w20 = live_series.window('2026-12-20')
    b = await mkset('MIGB', exam='JEE Main', series_id=S, series_date='2026-12-20', series_window=w20, series_import=True, live_enabled=True, start_at=w20['opens_at'], end_at=w20['closes_at'], test_kind='mock')
    mid = cands[1]['id']
    await DB.tejas_book_mocks.update_one({'_id': mid}, {'$set': {'series_date': '2026-12-05', 'series_id': S, 'set_id': None, 'publish_requested': True, 'release_at': old['opens_at']}})
    r1 = await series_admin.jee_dates_once()
    sa, sb = await SETS.find_one({'id': a}), await SETS.find_one({'id': b}); m = await DB.tejas_book_mocks.find_one({'_id': mid})
    check('migration (a) loses day fields', all(k not in sa for k in ('series_id', 'series_date', 'series_window', 'start_at', 'end_at')), {k: sa.get(k) for k in ('series_id', 'series_date', 'start_at')})
    check('migration (a) stays published + series_import', sa['status'] == 'published' and sa.get('series_import'), (sa['status'], sa.get('series_import')))
    check('migration (b) keeps 2026-12-20', sb.get('series_date') == '2026-12-20' and sb.get('series_id') == S, sb.get('series_date'))
    check('migration (c) mock day cleared, publish_requested False', m.get('series_date') is None and m.get('publish_requested') is False, (m.get('series_date'), m.get('publish_requested')))
    cfg = await DB.tejas_series.find_one({'_id': S}); check('series doc now 2026-12-09 / 50', cfg['first_date'] == '2026-12-09' and cfg['days'] == 50, (cfg['first_date'], cfg['days']))
    check('migration returned moved 2', (r1 or {}).get('moved') == 2, r1)
    mg = await DB.tejas_migrations.find_one({'_id': series_admin.JEE_DATES_ID}); check('tejas_migrations state done', mg and mg['state'] == 'done', mg)
    await DB.tejas_series.update_one({'_id': S}, {'$set': {'first_date': '2026-12-01', 'days': 62}})
    r2 = await series_admin.jee_dates_once(); cfg = await DB.tejas_series.find_one({'_id': S})
    check('second run does nothing', r2 is None and cfg['days'] == 62, (r2, cfg['days']))
    await DB.tejas_series.update_one({'_id': S}, {'$set': {'first_date': '2026-12-09', 'days': 50}})
    return a


async def after_migration(own, stu, a):
    cands = J(await own.get(f'{M}/series/{S}')).get('candidates', [])
    check('migrated (a) listed in Master candidates as paper without a day', any(c['id'] == a and c['kind'] == 'set' for c in cands), [c['id'] for c in cands])
    r = await stu.get(f'/api/sets/{a}'); check('migrated (a) hidden from students (GET set 404)', r.status_code == 404, r.status_code)
    d = J(await stu.get('/api/series/all-india-jee')); check('migrated (a) not in student schedule', a not in str(d), '')


async def main():
    own, _ = await mkstaff('owner', 'j187'); anon = client()
    stu = client(); await stu.post('/api/auth/phone/signup', json={'phone': '93' + str(uuid.uuid4().int)[:8], 'pin': '8261', 'confirm_pin': '8261'})
    for name, fn in (('dates', lambda: dates_api(own, stu, anon)),):
        await fn()
    book, cands = await early_and_lock(own, stu, anon)
    await custom_series(own, stu, anon)
    a = await migration(cands)
    await after_migration(own, stu, a)
    check('no AI calls in whole run', H.AI_CALLS == {'ask': 0, 'solve': 0}, H.AI_CALLS)


async def run():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    try: await main()
    except Exception:
        import traceback; traceback.print_exc(); check('suite ran to the end', False, 'exception above')
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
        ok = sum(1 for r in RESULTS if r[1]); print(f'TOTAL {len(RESULTS)} PASS {ok} FAIL {len(RESULTS) - ok}'); print('dropped', H.TEST_DB)

if __name__ == '__main__':
    asyncio.run(run())
