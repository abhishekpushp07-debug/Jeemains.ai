"""TEST-ONLY iteration 255 browser bridge (pocket C1a, "Jod: ek sawaal, ek record"): the real app on 127.0.0.1:8781 bound to a
disposable isolated DB (storage mocked, no AI, no network). Seeds Mock 06 and 07 of the owner's AITS book in the built-in JEE series
and chapter 8 of the owner's chemistry book in Chapter-wise, both as Drafts. Nothing is joined yet.
The file /tmp/uibridge255/break gives the chapter copy of Mock 06 / Q65 another answer (as a fix in the Draft would);
/tmp/uibridge255/fix puts it back. Writes /tmp/uibridge255/bridge.json (owner cookies, 0600).
Run: cd /app/backend && python tests/links_bridge255.py 900 &
"""
import asyncio, json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from question_records_iso254 import H, mkstaff, upload, drain, aits_slice, drafts, edit  # noqa: E402
from book_speed211 import chapter8, run_book  # noqa: E402
import uvicorn  # noqa: E402
from tejas import structure  # noqa: E402

OUT, PORT = '/tmp/uibridge255', 8781


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    os.makedirs(OUT, exist_ok=True)
    for name in ('break', 'fix'):
        Path(f'{OUT}/{name}').unlink(missing_ok=True)
    own, _ = await mkstaff('owner', 'ui255')
    b = await upload(own, aits_slice(), 'TEST_AITS_06_07', section_id='jee-main:aits')
    await own.post(f"/api/admin/books/{b['id']}/complete"); await drain(100000)
    chem, _, _, _ = await run_book(own, 'jee-main:chapters', chapter8(), 'TEST_CHEM_CH08')
    P, C = await drafts(b['id']), await drafts(chem)
    both = set(P) & set(C)
    assert len(P) == 150 and (6, 65) in both, (len(P), sorted(both))
    (_, pq), (cm, cq) = P[(6, 65)], C[(6, 65)]
    other = next(x for x in 'ABCD' if x != cq['answer'])

    async def watcher():
        while True:
            for name, answer in (('break', other), ('fix', cq['answer'])):
                if os.path.exists(f'{OUT}/{name}'):
                    await edit(cm, cq, answer=answer)
                    os.unlink(f'{OUT}/{name}')
            await asyncio.sleep(.3)
    watch = asyncio.create_task(watcher())
    path = OUT + '/bridge.json'
    with open(path, 'w') as f:
        json.dump({'owner': dict(own.cookies), 'type': '/super-admin/exam/jee-main/jee-main:aits',
                   'counts': {'records': len(set(P) | set(C)), 'linked': len(both), 'paper': 150 - len(both), 'chapter': len(C) - len(both)},
                   'per_mock': {str(n): sum(1 for k in both if k[0] == n) for n in (6, 7)}, 'named': len(both),
                   'answers': [pq['answer'], other], 'where': f"Chapter-wise · TEST_CHEM_CH08 · {cm['chapter']['title']} · Q{cq['original_number']}"}, f)
    os.chmod(path, 0o600)
    print('READY', H.TEST_DB, len(P), len(C), flush=True)
    server = uvicorn.Server(uvicorn.Config(H.app, host='127.0.0.1', port=PORT, log_level='warning', lifespan='off'))
    try:
        await asyncio.wait_for(server.serve(), int(sys.argv[1]) if len(sys.argv) > 1 else 900)
    except asyncio.TimeoutError:
        pass
    finally:
        watch.cancel()
        # the disposable test database of this run only (its name is checked first); the app's own database is never touched
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        for name in ('bridge.json', 'break', 'fix'):
            Path(f'{OUT}/{name}').unlink(missing_ok=True)
        print('dropped', H.TEST_DB, flush=True)

asyncio.run(main())
