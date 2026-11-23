"""TEST-ONLY iteration 183: fresh start (only JEE Main PYQ kept, Rapid Fire untouched), series days freed with dates kept,
Library segments + recycle-bin restore (series day back if free), and the clean student source line.
Isolated disposable DB (storage + AI mocked). Run: cd /app/backend && python tests/fresh_start_iso183.py
"""
import asyncio, io, sys, time, uuid, zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import book_publishing_iso170 as T  # noqa: E402,F401
from book_publishing_iso170 import H, mkstaff, client, check, RESULTS  # noqa: E402
from structure_iso173 import mkset, start  # noqa: E402
from tejas import structure, library, live_series  # noqa: E402

DB = H.TDB
SETS = DB.tejas_sets
JEE = live_series.SERIES_ID


def env(r):
    try: return r.json()
    except Exception: return {}


async def nav(stu, slug, section):
    r = await stu.get(f'/api/exam-navigation/{slug}/catalogue', params={'section': section})
    return [x['id'] for x in env(r).get('items', [])]


async def seed_content():
    s = {}
    s['pyq'] = await mkset('PYQ', exam='JEE Main', test_kind='pyq', pyq_year=2025, pyq_date='2025-01-22', import_id='imp-jee-pyq', live_enabled=True, start_at=0, end_at=4e9)
    s['mpyq'] = await mkset('MPYQ', exam='JEE Main', catalog_section_id='jee-main:pyq', test_kind='pyq', master_pyq=True, pyq_year=2024)
    s['bpyq'] = await mkset('BPYQ', exam='BITSAT', test_kind='pyq', pyq_year=2023)
    s['bmock'] = await mkset('BMOCK', exam='BITSAT', catalog_section_id='bitsat:mocks', test_kind='mock', source='Owner-uploaded secret_file_name.pdf')
    s['jch'] = await mkset('JCH', exam='JEE Main', test_kind='chapter', chapter_subject='Physics', chapter_number=3, source='Owner-supplied TEJAS200 JEE Main chapter folder')
    s['jmock'] = await mkset('JMOCK', exam='JEE Main', catalog_section_id='jee-main:mocks', test_kind='mock', start_at=time.time() + 86400 * 30)
    s['draft'] = await mkset('DRAFT', exam='JEE Main', catalog_section_id='jee-main:mocks', status='draft', written=True)
    s['comedk'] = await mkset('COMEDK', exam='COMEDK', catalog_section_id='comedk:mocks', test_kind='mock')
    s['past'] = await mkset('SPAST', exam='JEE Main', series_id=JEE, series_date='2026-11-02', test_kind='mock', series_import=True, series_window=live_series.window('2026-11-02'))
    s['future'] = await mkset('SFUT', exam='JEE Main', series_id=JEE, series_date='2026-12-13', test_kind='mock', series_import=True, series_window=live_series.window('2026-12-13'))
    s['rapid'] = await mkset('RAPID', exam='Rapid Fire', test_kind='rapid_fire')
    s['qa'] = await mkset('QA', exam='BITSAT', catalog_section_id='bitsat:mocks', status='draft', qa_only=True, audience='restricted')
    t = time.time()
    await DB.tejas_imports.insert_many([{'id': 'imp-jee-pyq', 'title': 'JEE PYQ folder', 'destination': {}}, {'id': 'imp-bitsat', 'title': 'BITSAT paper', 'destination': {'section_id': 'bitsat:mocks'}}])
    await DB.tejas_chapter_books.insert_one({'id': 'cb-1', 'title': 'Old chapter book', 'destination': {'section_id': 'bitsat:chapters'}})
    for bid, dest in (('bk-ch', {'section_id': 'bitsat:chapters'}), ('bk-ser', {'section_id': 'jee-main:aits', 'series': True, 'series_id': JEE})):
        await DB.tejas_books.insert_one({'_id': bid, 'removed': False, 'paused': False, 'state': 'ready', 'created_at': t, 'payload': {'title': bid, 'destination': dest}})
    await DB.tejas_book_mocks.insert_many([
        {'_id': 'bm-sched', 'book_id': 'bk-ch', 'label': 'Chapter 1', 'set_id': None, 'state': 'ready', 'publish_requested': True, 'release_at': t + 3600, 'order': 1, 'questions': []},
        {'_id': 'bm-day', 'book_id': 'bk-ser', 'label': 'Mock 1', 'set_id': None, 'state': 'ready', 'series_date': '2026-12-20', 'series_id': JEE, 'publish_requested': True, 'release_at': t + 9999, 'order': 1, 'questions': []}])
    return s


async def main():
    check('no customer DB handles', not H.leftover_real_handles(), H.leftover_real_handles())
    await H.tdbmod.indexes(); await structure.seed()
    own, _ = await mkstaff('owner', 'fs'); rev, _ = await mkstaff('reviewer', 'fs')
    stu = client(); await stu.post('/api/auth/phone/signup', json={'phone': '94' + str(uuid.uuid4().int)[:8], 'pin': '8261', 'confirm_pin': '8261'})
    try:
        s = await seed_content()
        await structure.visibility(force=True)
        # Clean source line before the clean-up.
        d = env(await stu.get(f"/api/my/sets/{s['bmock']}"))
        check('source line shows where the test sits, never the file name', d.get('source') == 'BITSAT \u00b7 Mock Tests' and 'secret_file_name' not in str(d), d.get('source'))
        d = env(await stu.get(f"/api/my/sets/{s['jch']}"))
        check('chapter test source line adds its subject', d.get('source') == 'JEE Main \u00b7 Chapter-wise Tests \u00b7 Physics', d.get('source'))
        d = env(await stu.get(f"/api/my/sets/{s['pyq']}"))
        check('PYQ source line adds its year', d.get('source') == 'JEE Main \u00b7 PYQ Papers \u00b7 2025', d.get('source'))
        r = await stu.get('/api/sets', params={'exam': 'BITSAT'})
        check('catalogue never shows back-office source text', r.status_code == 200 and 'Owner-' not in r.text and 'secret_file_name' not in r.text, r.text[:200])
        r = await start(stu, s['bmock']); aid = env(r).get('id')
        check('student attempt before the clean-up', r.status_code == 200 and aid, r.text[:200])
        before_attempts = await DB.tejas_attempts.count_documents({})

        # The one-time fresh start.
        counts = await library.fresh_start_once()
        check('fresh start ran with counts', counts and counts['tests'] == 6 and counts['series']['papers'] == 2 and counts['kept'] == 2 and counts['rapid_fire_kept'] == 1, counts)
        check('fresh start runs once', await library.fresh_start_once() is None)
        st = {k: await SETS.find_one({'id': v}, {'_id': 0, 'archived': 1, 'series_date': 1, 'library_series': 1, 'archived_reason': 1}) for k, v in s.items()}
        check('JEE Main PYQ (verified and Master) kept for students', not st['pyq'].get('archived') and not st['mpyq'].get('archived'), (st['pyq'], st['mpyq']))
        check('Rapid Fire test untouched', not st['rapid'].get('archived'), st['rapid'])
        check('private preview copy untouched', not st['qa'].get('archived'), st['qa'])
        gone = ['bpyq', 'bmock', 'jch', 'jmock', 'draft', 'comedk', 'past', 'future']
        check('everything else moved to the Library', all(st[k].get('archived') for k in gone), {k: bool(st[k].get('archived')) for k in gone})
        check('series papers keep their day in the Library, day freed', all(not st[k].get('series_date') and st[k]['library_series']['series_date'] for k in ('past', 'future')), (st['past'], st['future']))
        check('reason says fresh start', st['bmock']['archived_reason'].startswith('Fresh start'), st['bmock'].get('archived_reason'))
        cfg = await DB.tejas_series.find_one({'_id': JEE})
        check('series dates kept', cfg['first_date'] == '2026-12-09' and cfg['days'] == 50, (cfg['first_date'], cfg['days']))
        sched = env(await own.get(f'/api/admin/master/series/{JEE}'))
        check('series days all free', not any((x.get('paper') or {}).get('id') for x in sched.get('slots', [])), [x for x in sched.get('slots', []) if x.get('paper')][:2])
        check('student attempts untouched', await DB.tejas_attempts.count_documents({}) == before_attempts)
        r = await stu.get(f'/api/attempts/{aid}')
        check('student still opens the old attempt', r.status_code == 200, r.status_code)
        check('student sees JEE Main PYQ only', set(await nav(stu, 'jee-main', 'pyq')) >= {s['pyq'], s['mpyq']} and not await nav(stu, 'bitsat', 'mocks') and not await nav(stu, 'jee-main', 'chapters'), (await nav(stu, 'jee-main', 'pyq')))
        r = await stu.post(f"/api/sets/{s['bmock']}/preflight", json={})
        check('cleared test cannot be started', r.status_code in (403, 404), r.status_code)
        b1 = await DB.tejas_books.find_one({'_id': 'bk-ch'}); m1 = await DB.tejas_book_mocks.find_one({'_id': 'bm-sched'}); m2 = await DB.tejas_book_mocks.find_one({'_id': 'bm-day'})
        check('uploads moved to the Library and paused', b1.get('archived') and b1.get('paused') and (await DB.tejas_books.find_one({'_id': 'bk-ser'})).get('archived'), b1)
        check('waiting go-Live times cancelled', not m1['publish_requested'] and m1['release_at'] is None and not m2.get('series_date') and m2['release_at'] is None, (m1, m2))
        check('JEE PYQ import kept, other imports and chapter books archived', not (await DB.tejas_imports.find_one({'id': 'imp-jee-pyq'})).get('archived')
              and (await DB.tejas_imports.find_one({'id': 'imp-bitsat'})).get('archived') and (await DB.tejas_chapter_books.find_one({'id': 'cb-1'})).get('archived'))

        # Library: segments and facts the page shows.
        lib = env(await own.get('/api/admin/library'))
        items = {x['id']: x for x in lib.get('items', [])}
        check('library lists the 8 cleared tests', set(gone) and all(s[k] in items for k in gone), len(items))
        check('series papers grouped under All India Test Series with their day', items[s['future']]['section_id'] == 'jee-main:aits' and items[s['future']]['section_kind'] == 'aits' and items[s['future']]['series_date'] == '2026-12-13', items.get(s['future']))
        check('chapter test grouped under Chapter-wise with subject', items[s['jch']]['section_kind'] == 'chapters' and items[s['jch']]['subject'] == 'Physics', items.get(s['jch']))
        check('was-state shown (Live / Draft / Scheduled)', items[s['bmock']]['state'] == 'live' and items[s['draft']]['state'] == 'draft' and items[s['jmock']]['state'] == 'scheduled', {k: items[s[k]]['state'] for k in ('bmock', 'draft', 'jmock')})
        check('attempts kept and fresh-start summary', lib['attempts_kept'] >= 1 and lib['fresh_start']['counts']['kept'] == 2 and [e['slug'] for e in lib['exams']][:3] == ['jee-main', 'bitsat', 'comedk'], (lib.get('attempts_kept'), lib.get('fresh_start'), lib.get('exams')))
        check('uploads never Live listed', {u['id'] for u in lib['uploads']} >= {'bk-ch', 'cb-1', 'imp-bitsat'}, [u['id'] for u in lib['uploads']])
        check('uploads say where they go', next(u['place'] for u in lib['uploads'] if u['id'] == 'bk-ch') == 'BITSAT \u203a Chapter-wise Tests', [u['place'] for u in lib['uploads']])
        r = await rev.get('/api/admin/library'); check('reviewer cannot open the Library', r.status_code == 403, r.status_code)
        z = await own.get('/api/admin/library/export', params={'section_id': 'jee-main:aits'})
        names = zipfile.ZipFile(io.BytesIO(z.content)).namelist() if z.status_code == 200 else []
        check('series group ZIP has both papers', len([n for n in names if n.startswith('tests/')]) == 2, (z.status_code, names[:4]))

        # Restore like a recycle bin.
        r = await own.post('/api/admin/library/restore', json={'ids': [s['future']]})
        f = await SETS.find_one({'id': s['future']})
        check('series paper goes back on its free day', r.status_code == 200 and f.get('series_date') == '2026-12-13' and not f.get('archived') and 'library_series' not in f and f.get('series_window'), (r.text[:200], f.get('series_date')))
        await mkset('TAKER', exam='JEE Main', series_id=JEE, series_date='2026-11-02', test_kind='mock', series_import=True)
        r = await own.post('/api/admin/library/restore', json={'ids': [s['past']]})
        p = await SETS.find_one({'id': s['past']})
        check('series paper whose day is taken comes back without a day', r.status_code == 200 and env(r)['without_day'] == 1 and 'without a day' in env(r)['message'] and not p.get('series_date') and not p.get('archived'), (r.text[:250], p.get('series_date')))
        r = await own.post('/api/admin/library/restore', json={'ids': [s['bmock'], s['jch']]})
        check('restore two tests', r.status_code == 200 and env(r)['restored'] == 2, r.text[:200])
        await structure.visibility(force=True)
        check('restored Live test is back for students', s['bmock'] in await nav(stu, 'bitsat', 'mocks'))
        d = env(await stu.get(f"/api/my/sets/{s['jch']}"))
        check('restored chapter keeps the clean line', d.get('source') == 'JEE Main \u00b7 Chapter-wise Tests \u00b7 Physics', d.get('source'))
        r = await own.post('/api/admin/library/restore', json={'uploads': [{'kind': 'book', 'id': 'bk-ch'}]})
        b1 = await DB.tejas_books.find_one({'_id': 'bk-ch'})
        check('upload restore un-pauses as before', r.status_code == 200 and not b1.get('archived') and b1.get('paused') is False, b1)
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
    failed = [r for r in RESULTS if not r[1]]
    print(f'\nTOTAL {len(RESULTS)} PASS {len(RESULTS) - len(failed)} FAIL {len(failed)}')
    sys.exit(1 if failed else 0)

if __name__ == '__main__':
    asyncio.run(main())
