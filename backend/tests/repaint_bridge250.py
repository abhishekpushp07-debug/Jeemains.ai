"""TEST-ONLY iteration 250 browser bridge (pocket S1b, "Line hatao"): the real app on 127.0.0.1:8779 bound to a disposable isolated DB,
Supabase faked at the wire. Seeds one Live chapter test whose whole-question and solution pictures are as they were saved before the
printed 'Source' line was hidden. One of them is marked as cut from another PDF (it cannot be proven) until the file
/tmp/uibridge250/fix appears. Writes /tmp/uibridge250/bridge.json (owner cookies, 0600).
Run: cd /app/backend && python tests/repaint_bridge250.py 900 &
"""
import asyncio, json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import source_repaint250 as T  # noqa: E402
from source_repaint250 import H, S, J, mkstaff, paper, age, Bent  # noqa: E402
import httpx, uvicorn  # noqa: E402
from tejas import structure, storage_health as SH, source_repaint as SR  # noqa: E402

OUT, PORT = '/tmp/uibridge250', 8779
FIX = OUT + '/fix'


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    os.makedirs(OUT, exist_ok=True)
    Path(FIX).unlink(missing_ok=True)
    T.sb = Bent(S.TUS_CHUNK)
    wire = httpx.Client(transport=httpx.MockTransport(T.sb))
    S._client = lambda: wire   # nothing leaves this process
    S.STATE.update(down_until=0.0, strikes=0, last_error='', auth=None, bucket=None, failovers=0, last_failover=None, backup_since=None, last_ok=0.0, struck_at=0.0)
    S.EVENTS.clear(); S._recent.clear()
    own, _ = await mkstaff('owner', 'ui250')
    slug = J(await own.post('/api/admin/catalog/exams', json={'name': 'RPUX', 'short': 'RU', 'subjects': ['Chemistry'], 'color': 'rose'})).get('slug')
    chap = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Chapter-wise', 'description': '', 'layout': 'chapters', 'kind': 'chapters'})).get('id')
    await structure.exams.update_one({'_id': slug}, {'$set': {'shown': True}})
    bid, sid, pdf = await paper(own, chap, 'ui')
    s, old = await age(sid, pdf)
    odd = next(i for i, o in old.items() if o['line'])
    await T.FILES.update_one({'id': odd}, {'$set': {'source_sha256': 'f' * 64}})

    async def fixer():
        while True:
            if os.path.exists(FIX):
                await T.FILES.update_one({'id': odd}, {'$set': {'source_sha256': old[odd]['source_sha256']}})
                os.unlink(FIX)
            await asyncio.sleep(.3)
    fix, watch = asyncio.create_task(fixer()), asyncio.create_task(SH.watch())
    await asyncio.sleep(.1); await SH.flush()
    path = OUT + '/bridge.json'
    with open(path, 'w') as f:
        json.dump({'owner': dict(own.cookies), 'type': f'/super-admin/exam/{slug}/{chap}', 'pictures': len(old), 'with_line': sum(1 for o in old.values() if o['line']), 'odd': old[odd]['at']}, f)
    os.chmod(path, 0o600)
    print('READY', H.TEST_DB, len(old), flush=True)
    server = uvicorn.Server(uvicorn.Config(H.app, host='127.0.0.1', port=PORT, log_level='warning', lifespan='off'))
    try:
        await asyncio.wait_for(server.serve(), int(sys.argv[1]) if len(sys.argv) > 1 else 900)
    except asyncio.TimeoutError:
        pass
    finally:
        fix.cancel(); watch.cancel(); SH._mem['loop'] = None
        for t in list(SR._tasks):
            t.cancel()
        late = SH._running['flush']
        if late and not late.done():
            await asyncio.gather(late, return_exceptions=True)
        # the disposable test database of this run only (its name is checked first); the app's own database is never touched
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        for name in ('bridge.json', 'fix'):
            Path(OUT + '/' + name).unlink(missing_ok=True)
        print('dropped', H.TEST_DB, flush=True)

asyncio.run(main())
