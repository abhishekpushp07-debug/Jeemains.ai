"""TEST-ONLY iteration 170: capture REAL isolated API responses (envelopes + PNG crops) for browser route fulfilment.
Run: cd /app/backend && python tests/book_capture_iso170.py  -> /tmp/book170/fixtures.json
"""
import asyncio, base64, json, uuid
import book_publishing_iso170 as T
from book_publishing_iso170 import H, build_pdf, q3, mkstaff, client, upload, complete, OUT

FX = {}


async def grab(c, path, key=None):
    r = await c.get(path)
    FX[key or path] = {'status': r.status_code, 'ctype': r.headers.get('content-type', ''), 'b64': base64.b64encode(r.content).decode()}
    return r


async def run():
    try:
        own, _ = await mkstaff('owner', 'owner')
        mocks = [{'n': 1, 'qs': q3('M1'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]}, {'n': 2, 'qs': q3('M2'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]}]
        raw = build_pdf(mocks); b = await upload(own, raw, 'TEST_QA170 Browser Book'); _, v = await complete(own, b['id'])
        bid = b['id']
        await grab(own, '/api/auth/session', 'owner:/api/auth/session')
        await grab(own, '/api/admin/books')
        v = (await grab(own, f'/api/admin/books/{bid}')).json()
        await grab(own, f'/api/admin/books/{bid}/pages?page=1')
        await grab(own, f'/api/admin/books/{bid}/pages')
        for n in range(1, v['pages'] + 1):
            await grab(own, f'/api/admin/books/{bid}/pages/{n}'); await grab(own, f'/api/admin/books/{bid}/pages/{n}/image')
        for m in v['mocks']:
            md = (await grab(own, f"/api/admin/books/{bid}/mocks/{m['id']}")).json()
            for q in md['questions']:
                for kind in ('question', 'solution'):
                    await grab(own, f"/api/admin/books/{bid}/mocks/{m['id']}/questions/{q['id']}/asset/{kind}/0")
        stu = client(); await stu.post('/api/auth/phone/signup', json={'phone': '96' + str(uuid.uuid4().int)[:8], 'pin': '6142', 'confirm_pin': '6142'})
        await grab(stu, '/api/auth/session', 'student:/api/auth/session')
        await grab(stu, '/api/book-series', 'student:/api/book-series')
        await grab(stu, f'/api/book-series/{bid}', f'student:/api/book-series/{bid}')
        FX['_meta'] = {'book_id': bid, 'mocks': [(m['id'], m['label'], m['state']) for m in v['mocks']]}
        json.dump(FX, open(OUT / 'fixtures.json', 'w'))
        print('captured', len(FX), FX['_meta'])
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB); print('dropped', H.TEST_DB)

asyncio.run(run())
