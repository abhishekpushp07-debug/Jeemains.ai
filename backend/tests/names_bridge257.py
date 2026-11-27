"""TEST-ONLY iteration 257 browser bridge (pocket C1b, chapter names in the AITS analysis): the real app on 127.0.0.1:8782 bound to a
disposable isolated DB (storage mocked, no AI, no network). Seeds what tests/question_names256.py seeds: Mock 06 of the owner's AITS
book built for a day, chapter 8 of the owner's chemistry book in Chapter-wise, "Jod banao" pressed, and a student who sat the paper
(Mock 06 / Q65 answered wrong, nothing else). The owner's switch is Off.
Writes /tmp/uibridge257/bridge.json (owner and student cookies, 0600).
Run: cd /app/backend && python tests/names_bridge257.py 900 &
"""
import asyncio, json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from question_names256 import H, RESULTS, NAME, mkstaff, setup  # noqa: E402
import uvicorn  # noqa: E402
from tejas import structure  # noqa: E402

OUT, PORT = '/tmp/uibridge257', 8782


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    os.makedirs(OUT, exist_ok=True)
    path = OUT + '/bridge.json'
    try:
        own, _ = await mkstaff('owner', 'ui257')
        got = await setup(own)
        assert got and all(ok for _, ok in RESULTS), [n for n, ok in RESULTS if not ok]
        sid, stu, aid, pm, pq, cm, cq, res = got
        with open(path, 'w') as f:
            json.dump({'owner': dict(own.cookies), 'student': dict(stu.cookies), 'attempt': aid, 'number': pq['number'], 'chapter': NAME,
                       'type': '/super-admin/exam/jee-main/jee-main:aits'}, f)
        os.chmod(path, 0o600)
        print('READY', H.TEST_DB, aid, flush=True)
        server = uvicorn.Server(uvicorn.Config(H.app, host='127.0.0.1', port=PORT, log_level='warning', lifespan='off'))
        try:
            await asyncio.wait_for(server.serve(), int(sys.argv[1]) if len(sys.argv) > 1 else 900)
        except asyncio.TimeoutError:
            pass
    finally:
        # the disposable test database of this run only (its name is checked first); the app's own database is never touched
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        Path(path).unlink(missing_ok=True)
        print('dropped', H.TEST_DB, flush=True)

asyncio.run(main())
