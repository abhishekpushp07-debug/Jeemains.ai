"""TEST-ONLY iteration 187 browser bridge (copy of 185 + owner early JEE paper on 2026-12-15): real app on 127.0.0.1:8770 with a disposable DB and fixtures for
Master Live switch / Edit questions / typed options / series day switch / Library delete / deleted results.
Run: cd /app/backend && python tests/typed_bridge185.py 2400 &   (fixture ids + cookies in /tmp/uibridge/bridge.json, 0600)
"""
import asyncio, json, os, sys, time, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import book_publishing_iso170 as T  # noqa: E402,F401
from book_publishing_iso170 import H, mkstaff, client, upload, complete, drain  # noqa: E402
from structure_iso173 import mkset, start  # noqa: E402
from typed_delete_iso185 import two_opt_pdf, J, M  # noqa: E402
from tejas import structure, live_series  # noqa: E402
import uvicorn  # noqa: E402

OUT = '/tmp/uibridge'
DB = H.TDB; BM = DB.tejas_book_mocks; SETS = DB.tejas_sets


async def book(own, sec, tag, confirm=True, typed=False):
    b = await upload(own, two_opt_pdf(tag), 'TEST_' + tag, section_id=sec); await complete(own, b['id']); await drain()
    m = await BM.find_one({'book_id': b['id']}); base = f"/api/admin/books/{b['id']}/mocks/{m['_id']}"
    if confirm:
        p = J(await own.get(base + '/problems', params={'all': 'true'})); q = next(x for x in p['questions'] if x['number'] == 2)
        body = {'revision': p['revision'], 'question_id': q['id'], 'response_type': 'mcq', 'option_labels': ['A', 'B'], 'answer': 'B', 'complete': True}
        if typed: body.update(option_labels=['A', 'B', 'C', 'D'], answer='C', option_texts={'C': '2\u221a3 m/s', 'D': '4 m/s'})
        await own.post(base + '/fix', json=body); await drain()
    return b['id'], m['_id']


async def main():
    try: await setup_and_serve()
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB); print('dropped', H.TEST_DB, flush=True)


async def setup_and_serve():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    os.makedirs(OUT, exist_ok=True)
    own, _ = await mkstaff('owner', 'ui'); rev, _ = await mkstaff('reviewer', 'ui')
    stu = client(); await stu.post('/api/auth/phone/signup', json={'phone': '91' + str(uuid.uuid4().int)[:8], 'pin': '8261', 'confirm_pin': '8261'})
    r = await own.post('/api/admin/catalog/exams', json={'name': 'NEETX', 'short': 'NX', 'subjects': ['Physics', 'Chemistry', 'Biology'], 'color': 'rose'})
    slug = J(r).get('slug')
    sec = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Mock Tests', 'description': '', 'layout': 'list', 'kind': 'mocks'})).get('id')
    await structure.exams.update_one({'_id': slug}, {'$set': {'shown': True}})
    f = {'slug': slug, 'section': sec}
    f['held'] = await book(own, sec, 'HELD', confirm=False)
    f['draft'] = await book(own, sec, 'DRAFT')
    f['draft2'] = await book(own, sec, 'DRAFTB')
    f['typed'] = await book(own, sec, 'TYPED', typed=True)
    await own.post(M + '/status', json={'items': [{'kind': 'book_mock', 'id': f['typed'][1]}], 'to': 'live'}); await drain()
    f['typed_set'] = (await BM.find_one({'_id': f['typed'][1]}))['set_id']
    await asyncio.sleep(2); await structure.visibility(force=True)
    r = await start(stu, f['typed_set']); print('START', r.status_code, r.text[:300], flush=True); a = J(r); await stu.post(f"/api/attempts/{a['id']}/submit"); f['typed_attempt'] = a['id']
    f['live_set'] = await mkset('LIVE', exam='NEETX', catalog_section_id=sec, test_kind='mock', title='TEST_Live set')
    f['off_set'] = await mkset('OFF', exam='NEETX', catalog_section_id=sec, test_kind='mock', title='TEST_Off set', owner_unlive=True)
    # AITS day with a built paper, open now.
    t = time.time(); w = live_series.window('2026-12-12'); shift = t - w['opens_at'] - 600
    w = {k: (v + shift if isinstance(v, (int, float)) else v) for k, v in w.items()}
    f['day_set'] = await mkset('SDAY', exam='JEE Main', series_id=live_series.SERIES_ID, series_date='2026-12-12', test_kind='mock', series_import=True, series_window=w, live_enabled=True, start_at=0, end_at=4e9)
    await DB.tejas_series.update_one({'_id': live_series.SERIES_ID}, {'$set': {'shown': True}})
    await structure.exams.update_one({'_id': 'jee-main'}, {'$set': {'shown': True}})
    f['series_id'] = live_series.SERIES_ID
    we = live_series.window('2026-12-15')
    f['early_set'] = await mkset('EARLY', exam='JEE Main', series_id=live_series.SERIES_ID, series_date='2026-12-15', test_kind='mock', series_import=True, series_window=we, live_enabled=True, start_at=we['opens_at'], end_at=we['closes_at'], title='TEST_Early paper')
    # Library: archived tests with attempts, archived upload, archived draft mock.
    f['lib1'] = await mkset('LIB1', exam='JEE Main', catalog_section_id='jee-main:mocks', test_kind='mock', title='TEST_Lib one')
    f['lib2'] = await mkset('LIB2', exam='JEE Main', catalog_section_id='jee-main:mocks', test_kind='mock', title='TEST_Lib two')
    f['lib3'] = await mkset('LIB3', exam='JEE Main', catalog_section_id='jee-main:mocks', test_kind='mock', title='TEST_Lib three')
    f['gone'] = await mkset('GONE', exam='JEE Main', catalog_section_id='jee-main:mocks', test_kind='mock', title='TEST_Gone test')
    for k in ('lib1', 'gone'):
        a = J(await start(stu, f[k])); await stu.post(f"/api/attempts/{a['id']}/submit"); f[k + '_attempt'] = a['id']
    await own.post(M + '/status', json={'items': [{'kind': 'set', 'id': f[k]} for k in ('lib1', 'lib2', 'lib3', 'gone')], 'to': 'library'})
    await own.post('/api/admin/library/delete', json={'ids': [f['gone']], 'confirm': 'DELETE'})
    await DB.tejas_imports.insert_one({'id': 'imp-ui185', 'title': 'TEST_Old import', 'archived': True, 'destination': {'section_id': 'jee-main:mocks'}})
    await own.post(M + '/status', json={'items': [{'kind': 'book_mock', 'id': f['draft2'][1]}], 'to': 'library'})
    path = OUT + '/bridge.json'
    with open(path, 'w') as fh:
        json.dump({'owner': dict(own.cookies), 'reviewer': dict(rev.cookies), 'student': dict(stu.cookies), 'f': f}, fh)
    os.chmod(path, 0o600)
    print('READY', H.TEST_DB, json.dumps(f), flush=True)
    server = uvicorn.Server(uvicorn.Config(H.app, host='127.0.0.1', port=8770, log_level='warning', lifespan='off'))
    try:
        await asyncio.wait_for(server.serve(), int(sys.argv[1]) if len(sys.argv) > 1 else 900)
    except asyncio.TimeoutError:
        pass
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
        try: os.unlink(path)
        except OSError: pass
        print('dropped', H.TEST_DB, flush=True)

asyncio.run(main())
