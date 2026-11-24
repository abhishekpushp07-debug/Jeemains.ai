"""TEST-ONLY iteration 231 browser bridge (Pocket 2): the real app on 127.0.0.1:8775 bound to a disposable isolated DB, Supabase faked at the wire.
An upload whose path contains a line of /tmp/uibridge231/returned.txt is returned by "Supabase" with 400 (that file only; empty the file = Supabase
takes it). Supabase is DOWN while /tmp/uibridge231/supabase_down exists. Seeds, in a new exam > Mock Tests:
  ok       a Live mock (made Live while the others were stuck)
  pic      a mock whose pictures are returned at Live: "Atki hai", 22 minutes old (the 15-minute alert shows)
  big      a 7 MB PDF returned on both big-file routes: "Atki hai", fresh (no alert yet)
  two      a PDF with two mocks, a picture of each returned at Live: its row names the first mock and counts the other
  file / blocked   display-only rows: "this file only, machine retries" (423) and "project blocked" (402)
Writes /tmp/uibridge231/bridge.json (owner + reviewer cookies, 0600). Run: cd /app/backend && python tests/storage_stuck_bridge231.py 2400 &
"""
import asyncio, json, os, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage_book229 import H, J, BM, DB, S, mkstaff, upload, cut_pdf, big_pdf, finish, again, pump  # noqa: E402
import httpx, uvicorn  # noqa: E402
from book_publishing_iso170 import build_pdf, q3  # noqa: E402
from tejas import structure  # noqa: E402
from fake_supabase231 import Picky  # noqa: E402

OUT = '/tmp/uibridge231'
FLAG, MARKS = OUT + '/supabase_down', OUT + '/returned.txt'


class Switched(Picky):
    def marks(self):
        try:
            return [x.strip() for x in Path(MARKS).read_text().split('\n') if x.strip()]
        except OSError:
            return []

    @property
    def down(self):
        return os.path.exists(FLAG)

    @down.setter
    def down(self, value):
        pass


async def shown(bid, raw, wait):
    """A row that only shows a wait: no job runs for it."""
    t = time.time()
    await DB.tejas_books.update_one({'_id': bid}, {'$set': {'state': 'received', 'payload.transfer': {'url': '', 'path': f'jeelive/books/{bid}/original.pdf', 'size': len(raw), 'sent': 0, 'started': t},
                                                            'payload.storage_wait': {'since': t - 120, 'at': t, 'error': '', **wait}}})


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    os.makedirs(OUT, exist_ok=True)
    for f in (FLAG, MARKS):
        try: os.unlink(f)
        except OSError: pass
    sb = Switched(S.TUS_CHUNK)
    client = httpx.Client(transport=httpx.MockTransport(sb))
    S._client = lambda: client
    S.STATE.update(down_until=0.0, strikes=0, last_error='', auth=None, bucket=None, failovers=0, last_failover=None, backup_since=None)
    own, _ = await mkstaff('owner', 'ui231'); rev, _ = await mkstaff('reviewer', 'ui231')
    slug = J(await own.post('/api/admin/catalog/exams', json={'name': 'STKX', 'short': 'ST', 'subjects': ['Physics'], 'color': 'rose'})).get('slug')
    sec = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Mock Tests', 'description': '', 'layout': 'list', 'kind': 'mocks'})).get('id')
    await structure.exams.update_one({'_id': slug}, {'$set': {'shown': True}})

    async def live(mid):
        await own.post('/api/admin/master/status', json={'items': [{'kind': 'book_mock', 'id': mid}], 'to': 'live'}); await pump()
    pic = (await upload(own, cut_pdf('UIPIC', long=True), 'TEST_PICTURE_ATKI', section_id=sec))['id']; await finish(own, pic)
    raw = big_pdf('UIBIG')
    big = (await upload(own, raw, 'TEST_BADI_PDF_ATKI', section_id=sec))['id']
    K = [(1, 'B'), (2, 'B'), (3, 'C')]
    two = (await upload(own, build_pdf([{'n': 1, 'qs': q3('UI1'), 'keys': K}, {'n': 2, 'qs': q3('UI2'), 'keys': K}]), 'TEST_DO_MOCK_ATKE', section_id=sec))['id']; await finish(own, two)
    pair = [m async for m in BM.find({'book_id': two}).sort('order', 1)]
    Path(MARKS).write_text(f'/books/{pic}/crops/\n/books/{big}/original.pdf\n/books/{two}/crops/\n')
    mk = await BM.find_one({'book_id': pic}); await live(mk['_id'])
    await own.post('/api/admin/master/status', json={'items': [{'kind': 'book_mock', 'id': m['_id']} for m in pair], 'to': 'live'}); await pump()
    await finish(own, big); await again(own); await again(own)
    await DB.tejas_books.update_one({'_id': pic}, {'$set': {'payload.storage_wait.since': time.time() - 22 * 60}})
    ok = (await upload(own, cut_pdf('UIOK', long=True), 'TEST_THEEK_PDF', section_id=sec))['id']; await finish(own, ok)
    mo = await BM.find_one({'book_id': ok}); await live(mo['_id'])
    small = cut_pdf('UIF', long=True)
    one = (await upload(own, small, 'TEST_SIRF_YEH_FILE', section_id=sec))['id']
    await shown(one, small, {'kind': 'file', 'code': 423, 'reason': 'Supabase me isi file ka ek aur upload abhi khula hai (423)', 'next': 'Kuch nahi karna: machine khud phir koshish kar rahi hai.'})
    rok = (await upload(own, cut_pdf('UIB', long=True), 'TEST_PROJECT_ROK', section_id=sec))['id']
    await shown(rok, small, {'kind': 'blocked', 'code': 402, 'reason': 'Supabase project par billing ya usage ki rok hai (402)', 'next': 'Supabase dashboard me Billing aur Usage dekhiye. Rok hatte hi kaam apne aap aage chalega.'})
    state = {b['payload']['title']: (b['state'], (b['payload'].get('storage_wait') or {}).get('kind')) async for b in DB.tejas_books.find({}, {'state': 1, 'payload.title': 1, 'payload.storage_wait': 1})}
    path = OUT + '/bridge.json'
    with open(path, 'w') as f:
        json.dump({'owner': dict(own.cookies), 'reviewer': dict(rev.cookies), 'type': f'/super-admin/exam/{slug}/{sec}', 'pic': {'book': pic, 'mock': mk['_id'], 'label': mk['label']},
                   'big': big, 'ok': {'book': ok, 'mock': mo['_id']}, 'file': one, 'blocked': rok,
                   'two': {'book': two, 'mocks': [m['_id'] for m in pair], 'first': pair[0]['label']}}, f)
    os.chmod(path, 0o600)
    print('READY', H.TEST_DB, json.dumps(state), flush=True)
    server = uvicorn.Server(uvicorn.Config(H.app, host='127.0.0.1', port=8775, log_level='warning', lifespan='off'))
    try:
        await asyncio.wait_for(server.serve(), int(sys.argv[1]) if len(sys.argv) > 1 else 900)
    except asyncio.TimeoutError:
        pass
    finally:
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        for name in ('bridge.json', 'returned.txt', 'supabase_down'):
            try: os.unlink(OUT + '/' + name)
            except OSError: pass
        print('dropped', H.TEST_DB, flush=True)

asyncio.run(main())
