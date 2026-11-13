"""TEST-ONLY iteration 172 browser bridge: the real app on 127.0.0.1:8770 bound to a disposable isolated DB.
Storage and AI are MOCKED by iso_harness_book170; the real sandboxed PDF worker runs.
Deliberately NO job pump: processing must continue through the app's own dispatch, as it does in production.
Writes /tmp/uibridge/bridge.json (owner cookies, 0600) and /tmp/uibridge/book.pdf (421 pages / 30 mocks).
Run: cd /app/backend && python tests/book_bridge172.py 900 &   (stop with SIGTERM; it drops its own DB)
"""
import asyncio, json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import book_publishing_iso170 as T  # noqa
from book_publishing_iso170 import H, mkstaff
from book_scale_iso171 import big_pdf
import uvicorn

OUT = '/tmp/uibridge'


async def main():
    assert not H.leftover_real_handles()
    os.makedirs(OUT, exist_ok=True)
    with open(OUT + '/book.pdf', 'wb') as f:
        f.write(big_pdf(range(1, 31), 12))
    own, _ = await mkstaff('owner', 'ui')
    path = OUT + '/bridge.json'
    with open(path, 'w') as f:
        json.dump({'cookies': dict(own.cookies)}, f)
    os.chmod(path, 0o600)
    print('READY', H.TEST_DB, flush=True)
    server = uvicorn.Server(uvicorn.Config(H.app, host='127.0.0.1', port=8770, log_level='warning', lifespan='off'))
    try:
        await asyncio.wait_for(server.serve(), int(sys.argv[1]) if len(sys.argv) > 1 else 900)
    except asyncio.TimeoutError:
        pass
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
        for name in ('bridge.json', 'book.pdf'):
            try: os.unlink(OUT + '/' + name)
            except OSError: pass
        print('dropped', H.TEST_DB, flush=True)

asyncio.run(main())
