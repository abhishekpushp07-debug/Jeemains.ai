"""TEST-ONLY iteration 229 browser bridge (Student Choice): the real app on 127.0.0.1:8783 bound to a disposable isolated DB
(storage in memory, no AI, no network). Seeds the chapter tests of tests/choice_iso229.py (JEE Main, Physics/Chemistry/Maths,
one old-look picture chapter) and turns both Student Choice switches On. Writes /tmp/uibridge229/bridge.json (cookies of the
owner and of the student 'riya', 0600). Stop with SIGINT: its finally drops only its own tejas_isolated_* database.
Run: cd /app/backend && python tests/choice_bridge229.py 1200 &
"""
import asyncio, json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from choice_iso229 import H, seed, staff, student  # noqa: E402
import uvicorn  # noqa: E402
from tejas import choice  # noqa: E402

OUT, PORT = '/tmp/uibridge229', 8783


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes()
    choice.reset()
    await seed()
    os.makedirs(OUT, exist_ok=True)
    owner, riya = await staff('owner'), await student('9811122911')
    r = await owner.put('/api/admin/choice/jee-main', json={'expected_revision': 0, 'pick': True, 'random': True, 'max_questions': 75, 'max_per_subject': None,
                                                           'minutes_per_question': {'Physics': 2.4, 'Chemistry': 1.6, 'Mathematics': 3.2}, 'daily_limit': 5})
    assert r.status_code == 200, r.text
    path = OUT + '/bridge.json'
    with open(path, 'w') as f:
        json.dump({'owner': dict(owner.cookies), 'riya': dict(riya.cookies)}, f)
    os.chmod(path, 0o600)
    print('READY', H.TEST_DB, flush=True)
    server = uvicorn.Server(uvicorn.Config(H.app, host='127.0.0.1', port=PORT, log_level='warning', lifespan='off'))
    try:
        await asyncio.wait_for(server.serve(), int(sys.argv[1]) if len(sys.argv) > 1 else 900)
    except asyncio.TimeoutError:
        pass
    finally:
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)  # this run's throw-away DB only
        Path(path).unlink(missing_ok=True)
        print('dropped', H.TEST_DB, flush=True)

asyncio.run(main())
