"""TEST-ONLY iteration 188 browser bridge: real app on 127.0.0.1:8770 with a disposable DB.
Fixtures: picture book-mock practice set, plain practice set, open series day paper (series_live), closed series attempt for rank.
Run: cd /app/backend && python tests/ui_bridge188.py 1500 &   (ids + cookies in /tmp/uibridge/bridge.json, 0600)
"""
import asyncio, json, os, sys, time, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import book_publishing_iso170 as T  # noqa: E402,F401
from book_publishing_iso170 import H, mkstaff, client, upload, complete, drain  # noqa: E402
from structure_iso173 import mkset  # noqa: E402
from typed_delete_iso185 import two_opt_pdf, J, M  # noqa: E402
from tejas import structure, live_series  # noqa: E402
import uvicorn  # noqa: E402

OUT = '/tmp/uibridge'
DB = H.TDB; BM = DB.tejas_book_mocks; SETS = DB.tejas_sets


async def main():
    try: await setup_and_serve()
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB); print('dropped', H.TEST_DB, flush=True)


async def setup_and_serve():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    os.makedirs(OUT, exist_ok=True)
    own, _ = await mkstaff('owner', 'ui')
    stu = client(); await stu.post('/api/auth/phone/signup', json={'phone': '91' + str(uuid.uuid4().int)[:8], 'pin': '8261', 'confirm_pin': '8261'})
    await structure.exams.update_one({'_id': 'jee-main'}, {'$set': {'shown': True}})
    f = {}
    b = await upload(own, two_opt_pdf('PIC'), 'TEST_PIC', section_id='jee-main:mocks'); await complete(own, b['id']); await drain()
    m = await BM.find_one({'book_id': b['id']}); base = f"/api/admin/books/{b['id']}/mocks/{m['_id']}"
    for _ in range(5):
        p = J(await own.get(base + '/problems'))
        if not p.get('questions'): break
        q = p['questions'][0]
        await own.post(base + '/fix', json={'revision': p['revision'], 'question_id': q['id'], 'response_type': 'mcq', 'option_labels': ['A', 'B'], 'answer': 'B', 'complete': True}); await drain()
    await own.post(M + '/status', json={'items': [{'kind': 'book_mock', 'id': m['_id']}], 'to': 'live'}); await drain()
    f['pic_set'] = (await BM.find_one({'_id': m['_id']})).get('set_id')
    await SETS.update_one({'id': f['pic_set']}, {'$set': {'rules.minutes': 180}})
    f['prac_set'] = await mkset('PRAC', exam='JEE Main', catalog_section_id='jee-main:mocks', test_kind='mock', title='TEST_Practice paper')
    t = time.time(); w = live_series.window('2026-12-12'); shift = t - w['opens_at'] - 600
    w = {k: (v + shift if isinstance(v, (int, float)) else v) for k, v in w.items()}
    f['day_set'] = await mkset('SDAY', exam='JEE Main', series_id=live_series.SERIES_ID, series_date='2026-12-12', test_kind='mock', series_import=True, series_window=w, live_enabled=True, start_at=0, end_at=4e9, title='TEST_Series day paper')
    sd = await SETS.find_one({'id': f['day_set']}); await SETS.update_one({'id': f['day_set']}, {'$set': {'series_pattern': live_series.paper_pattern(sd)}})
    f['day_set2'] = await mkset('SDAY2', exam='JEE Main', series_id=live_series.SERIES_ID, series_date='2026-12-13', test_kind='mock', series_import=True, series_window=w, live_enabled=True, start_at=0, end_at=4e9, title='TEST_Series closed paper')
    sd = await SETS.find_one({'id': f['day_set2']}); await SETS.update_one({'id': f['day_set2']}, {'$set': {'series_pattern': live_series.paper_pattern(sd)}})
    await DB.tejas_series.update_one({'_id': live_series.SERIES_ID}, {'$set': {'shown': True}})
    await asyncio.sleep(2); await structure.visibility(force=True)
    # A finished series attempt whose day has closed (rank ready).
    r = await stu.post(f"/api/sets/{f['day_set2']}/start", json={'preview': False, 'start_key': 'b188-' + uuid.uuid4().hex[:10], 'get_ready': True}); a = J(r)
    print('START2', r.status_code, r.text[:200], flush=True)
    await stu.post(f"/api/attempts/{a['id']}/begin")
    await stu.put(f"/api/attempts/{a['id']}/answers/{a['questions'][0]['id']}", json={'value': 'A', 'revision': 1, 'request_id': str(uuid.uuid4())})
    await stu.post(f"/api/attempts/{a['id']}/submit"); f['closed_attempt'] = a['id']
    for _ in range(20):
        if (J(await stu.get(f"/api/attempts/{a['id']}/results")) or {}).get('summary'): break
        await asyncio.sleep(0.5)
    await DB.tejas_attempts.update_one({'id': a['id']}, {'$set': {'competition_end': time.time() - 5}})
    path = OUT + '/bridge.json'
    with open(path, 'w') as fh:
        json.dump({'owner': dict(own.cookies), 'student': dict(stu.cookies), 'f': f}, fh)
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
