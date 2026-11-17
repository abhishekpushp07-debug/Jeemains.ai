"""TEST-ONLY iteration 192 browser bridge: real app on 127.0.0.1:8770 with a disposable DB and two held mocks reproducing
the production case (Q3 ambiguous worked-solution start, Q2 unchecked solution region on a solution page), plus a student
with a live ranked attempt for Forgot PIN 409. Run: cd /app/backend && python tests/override_bridge192.py 2400 &
"""
import asyncio, json, os, sys, time, uuid, secrets
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import book_publishing_iso170 as T  # noqa: E402,F401
from book_publishing_iso170 import H, mkstaff, client, upload, complete, drain  # noqa: E402
from override_guard_iso192 import pdf, J  # noqa: E402
from tejas import structure  # noqa: E402
import uvicorn  # noqa: E402

OUT = '/tmp/uibridge'
DB = H.TDB; BM = DB.tejas_book_mocks; PG = DB.tejas_book_pages


async def held(own, sec, tag):
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
    m = await BM.find_one({'_id': mid}); print('HELD', tag, m['state'], m['issues'], flush=True)
    return bid, mid


async def pump():
    while True:
        try: await drain()
        except Exception as e: print('drain error', e, flush=True)
        await asyncio.sleep(1)


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    os.makedirs(OUT, exist_ok=True); path = OUT + '/bridge.json'
    try:
        own, _ = await mkstaff('owner', 'ui'); rev, _ = await mkstaff('reviewer', 'ui')
        r = await own.post('/api/admin/catalog/exams', json={'name': 'OVRX', 'short': 'OX', 'subjects': ['Physics'], 'color': 'rose'}); slug = J(r).get('slug')
        sec = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Mock Tests', 'description': '', 'layout': 'list', 'kind': 'mocks'})).get('id')
        f = {'desk': await held(own, sec, 'DSK'), 'mob': await held(own, sec, 'MOB'), 'rev': await held(own, sec, 'REV')}
        ph = '95' + f'{secrets.randbelow(10 ** 8):08d}'; stu = client()
        r = await stu.post('/api/auth/phone/signup', json={'phone': ph, 'pin': '1357', 'confirm_pin': '1357'}); t = time.time()
        await DB.tejas_attempts.insert_one({'id': 'TEST_att192ui', 'user_id': J(r)['id'], 'set_id': 'x', 'status': 'active', 'competition_end': t + 7200, 'deadline': 0, 'created_at': t})
        f['live_phone'] = ph[2:] if False else ph
        with open(path, 'w') as fh: json.dump({'owner': dict(own.cookies), 'reviewer': dict(rev.cookies), 'f': f}, fh)
        os.chmod(path, 0o600)
        print('READY', H.TEST_DB, json.dumps(f), flush=True)
        task = asyncio.create_task(pump())
        server = uvicorn.Server(uvicorn.Config(H.app, host='127.0.0.1', port=8770, log_level='warning', lifespan='off'))
        try: await asyncio.wait_for(server.serve(), int(sys.argv[1]) if len(sys.argv) > 1 else 900)
        except asyncio.TimeoutError: pass
        task.cancel()
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
        try: os.unlink(path)
        except OSError: pass
        print('dropped', H.TEST_DB, flush=True)


if __name__ == '__main__':
    asyncio.run(main())
