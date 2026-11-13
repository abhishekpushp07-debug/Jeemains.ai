"""TEST-ONLY iteration 170 browser bridge: serves the REAL app bound to a disposable isolated DB on 127.0.0.1:8770
(storage+AI MOCKED by harness, real sealed PDF worker). Playwright route-forwards /api/** here so uploads/reviews hit real
isolated handlers, never the customer DB. Auto-exits after TTL seconds and drops its DB. Writes /tmp/book170/bridge.json (0600).
Run: cd /app/backend && timeout 900 python tests/book_bridge170.py 840 &
"""
import asyncio, json, os, sys, uuid
import book_publishing_iso170 as T
from book_publishing_iso170 import H, J, build_pdf, q3, mkstaff, client, upload, complete, OUT
import uvicorn

TTL = int(sys.argv[1]) if len(sys.argv) > 1 else 600


async def pump():
    while True:
        try: await T.drain(20)
        except Exception as e: print('drain err', e)
        await asyncio.sleep(0.5)


async def main():
    assert not H.leftover_real_handles()
    own, _ = await mkstaff('owner', 'owner')
    m = lambda n, keys=((1, 'B'), (2, 'B'), (3, 'C')): {'n': n, 'qs': q3(f'BR{n}'), 'keys': list(keys)}
    b1 = await upload(own, build_pdf([m(1), m(2), m(3, ((1, 'B'), (2, 'B'), (2, 'A'), (3, 'C')))]), 'TEST_QA170 Browser Book'); await complete(own, b1['id'])
    b2 = await upload(own, build_pdf([m(1), m(2)]), 'TEST_QA170 Second Series'); await complete(own, b2['id'])
    stu = client(); await stu.post('/api/auth/phone/signup', json={'phone': '93' + str(uuid.uuid4().int)[:8], 'pin': '8261', 'confirm_pin': '8261'})
    info = {'db': H.TEST_DB, 'books': [b1['id'], b2['id']], 'owner_cookies': dict(own.cookies), 'student_cookies': dict(stu.cookies)}
    p = OUT / 'bridge.json'; p.write_text(json.dumps(info)); os.chmod(p, 0o600); print('BRIDGE READY', json.dumps({k: v for k, v in info.items() if 'cookie' not in k}), flush=True)
    server = uvicorn.Server(uvicorn.Config(H.app, host='127.0.0.1', port=8770, log_level='warning', lifespan='off'))
    task = asyncio.create_task(pump())
    try: await asyncio.wait_for(server.serve(), TTL)
    except asyncio.TimeoutError: pass
    finally:
        task.cancel(); await H.tdbmod.client.drop_database(H.TEST_DB); p.unlink(missing_ok=True)
        print('BRIDGE dropped', H.TEST_DB, 'remaining', [n for n in await H.tdbmod.client.list_database_names() if 'book170' in n], flush=True)

asyncio.run(main())
