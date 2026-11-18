"""TEST-ONLY iteration 196 browser bridge: real app on 127.0.0.1:$BRIDGE_PORT (default 8773) with a disposable DB holding the
analysis fixture of iteration 195 (one 30-question paper, a class of 14 with time records, one old attempt without time).
Run: cd /app/backend && python tests/analysis_bridge196.py 1800 &   (cookies + ids in $BRIDGE_OUT/bridge.json, default /tmp/uibridge196, 0600)
"""
import asyncio, json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis_fixture195 as F  # noqa: E402
from book_publishing_iso170 import H  # noqa: E402
import uvicorn  # noqa: E402

OUT = os.environ.get('BRIDGE_OUT', '/tmp/uibridge196')
PORT = int(os.environ.get('BRIDGE_PORT', '8773'))


async def main():
    path = OUT + '/bridge.json'
    try:
        assert not H.leftover_real_handles()
        os.makedirs(OUT, exist_ok=True)
        f = await F.build()
        await f['hero'].put('/api/profile/display-name', json={'name': 'Arjun'})
        for _, aid in [(f['hero'], f['hero_attempt'])]:
            await F.analysis(f['hero'], aid)
        old, old_attempt = f['old']
        await F.analysis(old, old_attempt)
        data = {'hero': dict(f['hero'].cookies), 'hero_attempt': f['hero_attempt'], 'old': dict(old.cookies), 'old_attempt': old_attempt,
                'set': f['set'], 'friend': dict(f['class'][0][0].cookies), 'friend_attempt': f['class'][0][1]}
        with open(path, 'w') as fh:
            json.dump(data, fh)
        os.chmod(path, 0o600)
        print('READY', H.TEST_DB, flush=True)
        server = uvicorn.Server(uvicorn.Config(H.app, host='127.0.0.1', port=PORT, log_level='warning', lifespan='off'))
        try:
            await asyncio.wait_for(server.serve(), int(sys.argv[1]) if len(sys.argv) > 1 else 900)
        except asyncio.TimeoutError:
            pass
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
        try:
            os.unlink(path)
        except OSError:
            pass
        print('dropped', H.TEST_DB, flush=True)

asyncio.run(main())
