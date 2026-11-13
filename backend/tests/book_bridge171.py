"""TEST-ONLY iteration 171 browser bridge: REAL app on 127.0.0.1:8770 bound to a disposable isolated DB (storage+AI MOCKED,
real sealed PDF worker). Seeds a >1000-page / 60-mock auto-published book. Writes /tmp/book170/bridge.json (0600).
Also writes a large multi-MB upload fixture /tmp/book171/upload_large.pdf for the browser chunked-upload test.
Run: cd /app/backend && timeout 1700 python tests/book_bridge171.py 1600 &
"""
import asyncio, json, os, sys, time, uuid
import book_publishing_iso170 as T
from book_publishing_iso170 import H, J, mkstaff, client, upload, OUT
from book_scale_iso171 import big_pdf
import uvicorn

TTL = int(sys.argv[1]) if len(sys.argv) > 1 else 900


async def pump():
    while True:
        try: await T.drain(20)
        except Exception as e: print('drain err', e)
        await asyncio.sleep(0.5)


async def main():
    assert not H.leftover_real_handles()
    big = '/tmp/book171/upload_large.pdf'
    if not os.path.exists(big): open(big, 'wb').write(big_pdf(range(1, 13), 8, images=True))
    print('upload fixture MB', os.path.getsize(big) / 1048576, flush=True)
    own, _ = await mkstaff('owner', 'owner')
    t = time.time(); b1 = await upload(own, big_pdf(range(1, 61), 17), 'TEST_QA171 Browser 60 mocks')
    await own.post(f"/api/admin/books/{b1['id']}/complete"); await T.drain(5000)
    print('seed processed %.0fs' % (time.time() - t), flush=True)
    stu = client(); await stu.post('/api/auth/phone/signup', json={'phone': '93' + str(uuid.uuid4().int)[:8], 'pin': '8261', 'confirm_pin': '8261'})
    info = {'db': H.TEST_DB, 'books': [b1['id']], 'owner_cookies': dict(own.cookies), 'student_cookies': dict(stu.cookies)}
    p = OUT / 'bridge.json'; p.write_text(json.dumps(info)); os.chmod(p, 0o600); print('BRIDGE READY', json.dumps({k: v for k, v in info.items() if 'cookie' not in k}), flush=True)
    server = uvicorn.Server(uvicorn.Config(H.app, host='127.0.0.1', port=8770, log_level='warning', lifespan='off'))
    task = asyncio.create_task(pump())
    try: await asyncio.wait_for(server.serve(), TTL)
    except asyncio.TimeoutError: pass
    finally:
        task.cancel(); await H.tdbmod.client.drop_database(H.TEST_DB); p.unlink(missing_ok=True)
        print('BRIDGE dropped', H.TEST_DB, flush=True)

asyncio.run(main())
