"""TEST-ONLY iteration 194 browser bridge (copy of library_bridge183 with own port/out): real app on 127.0.0.1:8772 with a disposable DB after the fresh start
(JEE Main PYQ kept, BITSAT/JEE/COMEDK tests, series papers and uploads in the Library). Cookies in /tmp/uibridge194/bridge.json (0600).
Run: cd /app/backend && python tests/library_bridge194.py 2400 &
"""
import asyncio, json, os, sys, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import book_publishing_iso170 as T  # noqa: E402,F401
from book_publishing_iso170 import H, mkstaff, client  # noqa: E402
from structure_iso173 import mkset  # noqa: E402
from fresh_start_iso183 import seed_content  # noqa: E402
from tejas import structure, library  # noqa: E402
import uvicorn  # noqa: E402

OUT = os.environ.get('BRIDGE_OUT', '/tmp/uibridge194')


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    os.makedirs(OUT, exist_ok=True)
    own, _ = await mkstaff('owner', 'ui'); rev, _ = await mkstaff('reviewer', 'ui')
    stu = client(); await stu.post('/api/auth/phone/signup', json={'phone': '95' + str(uuid.uuid4().int)[:8], 'pin': '8261', 'confirm_pin': '8261'})
    s = await seed_content()
    for subject, n in (('Physics', 4), ('Chemistry', 3), ('Mathematics', 2)):
        for i in range(n):
            await mkset(f'CH{subject[:2]}{i}', exam='BITSAT', test_kind='chapter', chapter_subject=subject, chapter_number=i + 1, title=f'{subject} chapter {i + 1}')
    print('FRESH', await library.fresh_start_once(), flush=True)
    await structure.visibility(force=True)
    path = OUT + '/bridge.json'
    with open(path, 'w') as f:
        json.dump({'owner': dict(own.cookies), 'reviewer': dict(rev.cookies), 'student': dict(stu.cookies), 'sets': s}, f)
    os.chmod(path, 0o600)
    print('READY', H.TEST_DB, flush=True)
    server = uvicorn.Server(uvicorn.Config(H.app, host='127.0.0.1', port=int(os.environ.get('BRIDGE_PORT', '8772')), log_level='warning', lifespan='off'))
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
