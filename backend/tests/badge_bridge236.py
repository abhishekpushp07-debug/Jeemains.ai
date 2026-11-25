"""TEST-ONLY iteration 236 browser bridge (packet D, the storage badge): the real app on 127.0.0.1:8777 bound to a disposable isolated DB,
Supabase faked at the wire. Switches (files in /tmp/uibridge236): supabase_down = Supabase answers nothing; tus_down = only the big-file
piece route is broken; returned.txt = paths Supabase returns (one per line). Seeds, in a new exam > Mock Tests:
  pic  a PDF whose mock's pictures are returned by Supabase: "Atki hai"      ok  a PDF whose mock is Live
The storage watch runs as on a started server. Writes /tmp/uibridge236/bridge.json (owner cookies, 0600).
Run: cd /app/backend && python tests/badge_bridge236.py 2400 &
"""
import asyncio, json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage_book229 import H, J, BM, DB, S, mkstaff, upload, cut_pdf, finish, pump  # noqa: E402
import httpx, uvicorn  # noqa: E402
from tejas import structure, storage_health as SH  # noqa: E402
from fake_supabase231 import Picky  # noqa: E402

OUT = '/tmp/uibridge236'
DOWN, TUS, MARKS = OUT + '/supabase_down', OUT + '/tus_down', OUT + '/returned.txt'


class Switched(Picky):
    down = property(lambda self: os.path.exists(DOWN), lambda self, value: None)
    tus_down = property(lambda self: os.path.exists(TUS), lambda self, value: None)

    def marks(self):
        try:
            return [x.strip() for x in Path(MARKS).read_text().split('\n') if x.strip()]
        except OSError:
            return []


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    os.makedirs(OUT, exist_ok=True)
    for f in (DOWN, TUS, MARKS):
        try: os.unlink(f)
        except OSError: pass
    sb = Switched(S.TUS_CHUNK)
    client = httpx.Client(transport=httpx.MockTransport(sb))
    S._client = lambda: client
    S.STATE.update(down_until=0.0, strikes=0, last_error='', auth=None, bucket=None, failovers=0, last_failover=None, backup_since=None, last_ok=0.0, struck_at=0.0)
    S.EVENTS.clear(); S._recent.clear()
    own, _ = await mkstaff('owner', 'ui236')
    slug = J(await own.post('/api/admin/catalog/exams', json={'name': 'BDGX', 'short': 'BG', 'subjects': ['Physics'], 'color': 'rose'})).get('slug')
    sec = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Mock Tests', 'description': '', 'layout': 'list', 'kind': 'mocks'})).get('id')
    await structure.exams.update_one({'_id': slug}, {'$set': {'shown': True}})

    async def live(mid):
        await own.post('/api/admin/master/status', json={'items': [{'kind': 'book_mock', 'id': mid}], 'to': 'live'}); await pump()
    ok = (await upload(own, cut_pdf('UIOK', long=True), 'TEST_THEEK_PDF', section_id=sec))['id']; await finish(own, ok)
    mo = await BM.find_one({'book_id': ok}); await live(mo['_id'])
    pic = (await upload(own, cut_pdf('UIPIC', long=True), 'TEST_PICTURE_ATKI', section_id=sec))['id']; await finish(own, pic)
    mk = await BM.find_one({'book_id': pic})
    Path(MARKS).write_text(f'/books/{pic}/crops/\n')
    await live(mk['_id'])
    watch = asyncio.create_task(SH.watch())
    await asyncio.sleep(.1); await SH.flush()
    state = {b['payload']['title']: (b['state'], (b['payload'].get('storage_wait') or {}).get('kind')) async for b in DB.tejas_books.find({}, {'state': 1, 'payload.title': 1, 'payload.storage_wait': 1})}
    path = OUT + '/bridge.json'
    with open(path, 'w') as f:
        json.dump({'owner': dict(own.cookies), 'type': f'/super-admin/exam/{slug}/{sec}', 'pic': {'book': pic, 'mock': mk['_id'], 'label': mk['label']}, 'ok': {'book': ok, 'mock': mo['_id']}}, f)
    os.chmod(path, 0o600)
    print('READY', H.TEST_DB, json.dumps(state), flush=True)
    server = uvicorn.Server(uvicorn.Config(H.app, host='127.0.0.1', port=8777, log_level='warning', lifespan='off'))
    try:
        await asyncio.wait_for(server.serve(), int(sys.argv[1]) if len(sys.argv) > 1 else 900)
    except asyncio.TimeoutError:
        pass
    finally:
        watch.cancel(); SH._mem['loop'] = None
        late = SH._running['flush']
        if late and not late.done():
            await asyncio.gather(late, return_exceptions=True)
        # the disposable test database of this run only (its name is checked first); the app's own database is never touched
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        for name in ('bridge.json', 'returned.txt', 'supabase_down', 'tus_down'):
            try: os.unlink(OUT + '/' + name)
            except OSError: pass
        print('dropped', H.TEST_DB, flush=True)

asyncio.run(main())
