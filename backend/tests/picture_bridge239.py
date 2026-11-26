"""TEST-ONLY iteration 239 browser bridge (Packet E step 2, picture proof at Live): the real app on 127.0.0.1:8778 bound to a disposable
isolated DB, Supabase faked at the wire (tests/fake_supabase239.py). A small upload whose path contains a line of /tmp/uibridge239/vanish.txt
is answered 200 by "Supabase" but not stored (empty the file = Supabase keeps the pictures). Seeds, in a new exam > Mock Tests:
  ok     a Live mock: its row says "Pictures: n / n · Storage: Supabase"
  proof  a mock whose pictures are not in Supabase after two saves: "Atki hai", pictures not proven, 22 minutes old (the 15-minute alert shows)
  two    a PDF with two such mocks: its row names the first mock and counts the other
Packet E, the remaining doors (tests/picture_hold245.py): a stored file whose path contains a line of /tmp/uibridge239/gone.txt is not there
for "Supabase" until the line is removed. Seeds in "Written Tests": an Off test whose photo is gone and that was asked to go Live (stays
Off with the reason), a healthy Off test, a Live test in the Library whose photo is gone, and two display-only rows (proof running,
chosen time passed); in the series: day 3's paper, Off, asked to go Live while its photo is gone.
Writes /tmp/uibridge239/bridge.json (owner cookies, 0600). Run: cd /app/backend && python tests/picture_bridge239.py 2400 &
"""
import asyncio, json, os, sys, threading, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage_book229 import H, J, BM, DB, S, mkstaff, upload, cut_pdf, finish, pump  # noqa: E402
import httpx, uvicorn  # noqa: E402
from book_publishing_iso170 import build_pdf, q3  # noqa: E402
from tejas import structure  # noqa: E402
from fake_supabase239 import Leaky  # noqa: E402

OUT = '/tmp/uibridge239'
MARKS = OUT + '/vanish.txt'
GONE = OUT + '/gone.txt'


class Switched(Leaky):
    @property
    def vanish(self):
        try:
            return [x.strip() for x in Path(MARKS).read_text().split('\n') if x.strip()]
        except OSError:
            return []

    @vanish.setter
    def vanish(self, value):
        pass

    def __call__(self, req):
        """A stored file named in gone.txt is put aside (Supabase lists and gives nothing for it) and put back when its line is removed."""
        if not hasattr(self, 'gate'):
            self.gate, self.aside = threading.Lock(), {}
        with self.gate:
            try:
                marks = [x.strip() for x in Path(GONE).read_text().split('\n') if x.strip()]
            except OSError:
                marks = []
            for k in [k for k in self.objects if any(m in k for m in marks)]:
                self.aside[k] = self.objects.pop(k)
            for k in [k for k in self.aside if not any(m in k for m in marks)]:
                self.objects[k] = self.aside.pop(k)
            return super().__call__(req)


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    os.makedirs(OUT, exist_ok=True)
    for old in (MARKS, GONE):
        try: os.unlink(old)
        except OSError: pass
    sb = Switched(S.TUS_CHUNK)
    client = httpx.Client(transport=httpx.MockTransport(sb))
    S._client = lambda: client
    S.STATE.update(down_until=0.0, strikes=0, last_error='', auth=None, bucket=None, failovers=0, last_failover=None, backup_since=None)
    own, _ = await mkstaff('owner', 'ui239')
    slug = J(await own.post('/api/admin/catalog/exams', json={'name': 'PRFX', 'short': 'PF', 'subjects': ['Physics'], 'color': 'rose'})).get('slug')
    sec = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Mock Tests', 'description': '', 'layout': 'list', 'kind': 'mocks'})).get('id')
    await structure.exams.update_one({'_id': slug}, {'$set': {'shown': True}})
    # Written mocks, in a type of their own so the PDF rows keep their counts: one Live with a photo, one Draft whose photo "Supabase" did not keep.
    from written_live244 import written, photo, mcq
    wsec = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Written Tests', 'description': '', 'layout': 'list', 'kind': 'custom'})).get('id')
    assert wsec, 'the written type was not made'
    wok = await written(own, wsec, 'TEST_LIKHA_THEEK', photos=1)
    await own.post('/api/admin/master/status', json={'items': [{'kind': 'set', 'id': wok}], 'to': 'live'})
    wbad = await written(own, wsec, 'TEST_LIKHA_PHOTO_NAHI')
    Path(MARKS).write_text(f'/written/{wbad}/\n')
    await own.put(f'/api/admin/master/written/{wbad}/questions', json=mcq('photo question', image=await photo(own, wbad)))
    Path(MARKS).write_text('')
    # Packet E, the remaining doors: built tests that are switched on again wait for their pictures to be proven.
    from tejas import picture_hold as HOLD

    async def switch(wid, to):
        r = await own.post('/api/admin/master/status', json={'items': [{'kind': 'set', 'id': wid}], 'to': to})
        assert r.status_code == 200, r.text[:300]
    hbad, hok, hlib, hchk, hmiss = [await written(own, wsec, t, photos=1) for t in ('TEST_OFF_PHOTO_GAYAB', 'TEST_OFF_THEEK', 'TEST_LIBRARY_PHOTO_GAYAB', 'TEST_JAANCH_CHAL_RAHI', 'TEST_SAMAY_NIKAL_GAYA_OFF')]
    for wid in (hbad, hok, hlib, hchk, hmiss):
        await switch(wid, 'live')
    for wid in (hbad, hok, hchk, hmiss):
        await switch(wid, 'off')
    await switch(hlib, 'library')
    Path(GONE).write_text(f'/written/{hbad}/\n/written/{hlib}/\n')
    await switch(hbad, 'live')   # its photo is not in storage: it stays Off and its row says why
    # Display only: a proof that "another server" is running, and a test whose chosen time passed while it waited.
    await DB.tejas_sets.update_one({'id': hchk}, {'$set': {'picture_wait': {**HOLD.new_wait('live', 'ui239'), 'lease': time.time() + 86400}}})
    await DB.tejas_sets.update_one({'id': hmiss}, {'$set': {'picture_wait': {**HOLD.new_wait('scheduled', 'ui239', time.time() - 600), 'state': 'missed'}}})

    async def live(*mids):
        await own.post('/api/admin/master/status', json={'items': [{'kind': 'book_mock', 'id': m} for m in mids], 'to': 'live'}); await pump()
    ok = (await upload(own, cut_pdf('UIOK', long=True), 'TEST_THEEK_PDF', section_id=sec))['id']; await finish(own, ok)
    mo = await BM.find_one({'book_id': ok}); await live(mo['_id']); mo = await BM.find_one({'_id': mo['_id']})
    # Packet E step 3: a mock scheduled for a time that went by while its pictures were being saved. It is Draft again and says so.
    from tejas import book_publish as BP
    late = (await upload(own, cut_pdf('UILATE', long=True), 'TEST_SAMAY_NIKAL_GAYA', section_id=sec))['id']; await finish(own, late)
    ml = await BM.find_one({'book_id': late}); real_proven, real_now = BP.proven, BP.database_now

    async def after():
        return await real_now() + 7200

    async def slow(*args, **kw):
        out = await real_proven(*args, **kw)
        BP.database_now = after
        return out
    BP.proven = slow
    try:
        await own.post('/api/admin/master/status', json={'items': [{'kind': 'book_mock', 'id': ml['_id']}], 'to': 'scheduled', 'at': time.time() + 3600}); await pump()
    finally:
        BP.proven, BP.database_now = real_proven, real_now
    ml = await BM.find_one({'_id': ml['_id']})
    proof = (await upload(own, cut_pdf('UIPRF', long=True), 'TEST_PICTURES_SAABIT_NAHI', section_id=sec))['id']; await finish(own, proof)
    K = [(1, 'B'), (2, 'B'), (3, 'C')]
    two = (await upload(own, build_pdf([{'n': 1, 'qs': q3('UI1'), 'keys': K}, {'n': 2, 'qs': q3('UI2'), 'keys': K}]), 'TEST_DO_MOCK_SAABIT_NAHI', section_id=sec))['id']; await finish(own, two)
    pair = [m async for m in BM.find({'book_id': two}).sort('order', 1)]
    Path(MARKS).write_text(f'/books/{proof}/crops/\n/books/{two}/crops/\n')
    mk = await BM.find_one({'book_id': proof}); await live(mk['_id'])
    await live(*[m['_id'] for m in pair])
    # All India Test Series of the same exam: day 1 has its built paper; day 2's paper is not made because its pictures are not proven.
    from datetime import datetime, timedelta
    from tejas.live_series import IST
    first = datetime.now(IST).date() + timedelta(days=2)
    ser = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'All India Test Series', 'description': '', 'layout': 'list', 'kind': 'aits',
            'first_date': first.isoformat(), 'days': 5, 'open_time': '09:00', 'last_start': '11:00', 'minutes': 10, 'correct': 4, 'wrong': -1}))

    async def day(mid, n):
        await own.post(f"/api/admin/master/series/{ser['series_id']}/assign", json={'kind': 'book_mock', 'id': mid, 'date': (first + timedelta(days=n)).isoformat()}); await pump()
    aok = (await upload(own, cut_pdf('UIAOK', long=True), 'TEST_SERIES_THEEK', section_id=ser['id']))['id']; await finish(own, aok)
    abad = (await upload(own, cut_pdf('UIABAD', long=True), 'TEST_SERIES_SAABIT_NAHI', section_id=ser['id']))['id']; await finish(own, abad)
    sok, sbad = await BM.find_one({'book_id': aok}), await BM.find_one({'book_id': abad})
    await day(sok['_id'], 0)
    Path(MARKS).write_text(Path(MARKS).read_text() + f'/books/{abad}/crops/\n')
    await day(sbad['_id'], 1)
    # Day 3: a written paper, switched Off, then asked to go Live while its photo is gone: it stays Off and the day says why.
    wser = await written(own, ser['id'], 'TEST_SERIES_OFF_PHOTO_GAYAB', photos=1, plain=3)
    r = await own.post(f"/api/admin/master/series/{ser['series_id']}/assign", json={'kind': 'written', 'id': wser, 'date': (first + timedelta(days=2)).isoformat()})
    assert r.status_code == 200, r.text[:300]
    await own.post(f"/api/admin/master/series/{ser['series_id']}/live", json={'id': wser, 'live': False})
    Path(GONE).write_text(Path(GONE).read_text() + f'/written/{wser}/\n')
    r = await own.post(f"/api/admin/master/series/{ser['series_id']}/live", json={'id': wser, 'live': True})
    assert r.status_code == 409, r.text[:300]
    waits = {k: ((await DB.tejas_sets.find_one({'id': v}, {'picture_wait': 1}) or {}).get('picture_wait') or {}).get('state') for k, v in (('bad', hbad), ('checking', hchk), ('missed', hmiss), ('series', wser))}
    assert waits == {'bad': 'stuck', 'checking': 'checking', 'missed': 'missed', 'series': 'stuck'}, waits
    await DB.tejas_books.update_one({'_id': proof}, {'$set': {'payload.storage_wait.since': time.time() - 22 * 60}})
    rows = {b['_id']: b async for b in DB.tejas_books.find({}, {'state': 1, 'payload.title': 1, 'payload.storage_wait': 1})}
    state = {b['payload']['title']: (b['state'], (b['payload'].get('storage_wait') or {}).get('what'), (b['payload'].get('storage_wait') or {}).get('reason')) for b in rows.values()}
    path = OUT + '/bridge.json'
    with open(path, 'w') as f:
        json.dump({'owner': dict(own.cookies), 'type': f'/super-admin/exam/{slug}/{sec}', 'ok': {'book': ok, 'mock': mo['_id'], 'set': mo.get('set_id'), 'pictures': await DB.tejas_files.count_documents({'book_import_id': ok})},
                   'proof': {'book': proof, 'mock': mk['_id'], 'label': mk['label'], 'reason': (rows[proof]['payload'].get('storage_wait') or {}).get('reason', ''), 'pictures': await DB.tejas_files.count_documents({'book_import_id': proof})},
                   'two': {'book': two, 'mocks': [m['_id'] for m in pair], 'first': pair[0]['label']},
                   'late': {'book': late, 'mock': ml['_id'], 'state': ml['state'], 'missed_at': ml.get('missed_at'), 'set': ml.get('set_id')},
                   'written': {'type': f'/super-admin/exam/{slug}/{wsec}', 'ok': wok, 'bad': wbad},
                   'hold': {'type': f'/super-admin/exam/{slug}/{wsec}', 'bad': hbad, 'ok': hok, 'lib': hlib, 'checking': hchk, 'missed': hmiss, 'series': wser, 'day': 3},
                   'aits': {'type': f"/super-admin/exam/{slug}/{ser['id']}", 'book': abad, 'mock': sbad['_id'], 'label': sbad['label'], 'pictures': await DB.tejas_files.count_documents({'book_import_id': abad}),
                            'state': [(await BM.find_one({'_id': x['_id']}) or {}).get('state') for x in (sok, sbad)]}}, f)
    os.chmod(path, 0o600)
    print('READY', H.TEST_DB, json.dumps(state), flush=True)
    server = uvicorn.Server(uvicorn.Config(H.app, host='127.0.0.1', port=8778, log_level='warning', lifespan='off'))
    try:
        await asyncio.wait_for(server.serve(), int(sys.argv[1]) if len(sys.argv) > 1 else 900)
    except asyncio.TimeoutError:
        pass


async def run():
    try:
        await main()
    finally:
        # Also when the seed itself fails: the disposable test database of this run only (its name is checked first); the app's own database is never touched.
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        for name in ('bridge.json', 'vanish.txt', 'gone.txt'):
            try: os.unlink(OUT + '/' + name)
            except OSError: pass
        print('dropped', H.TEST_DB, flush=True)

asyncio.run(run())
