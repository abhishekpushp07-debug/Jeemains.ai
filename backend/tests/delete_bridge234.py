"""TEST-ONLY iteration 234 browser bridge (packets B + C): the real app on 127.0.0.1:8776 bound to a disposable isolated DB, Supabase faked at the wire.
Seeds, in a new exam > Mock Tests:
  keep   a PDF with two mocks, one Live: its Draft mock must NOT offer "Is PDF ko delete karo"
  draft  a read PDF with one Draft mock: its Status menu offers "Is PDF ko delete karo…"
  big    a 7 MB PDF returned on both big-file routes: "Atki hai" at 0 %, its row offers Delete
  hung   a display-only row: the PDF's work went silent three times ("Atki hai", kind hang) + one written-down silent step
  safai  a display-only clean-up of a deleted upload that still waits (Machine: "Delete ki safai baaki: 1")
Writes /tmp/uibridge234/bridge.json (owner cookies, 0600). Run: cd /app/backend && python tests/delete_bridge234.py 2400 &
"""
import asyncio, json, os, sys, time, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage_book229 import H, J, BM, DB, S, mkstaff, upload, cut_pdf, big_pdf, finish, again, pump  # noqa: E402
import httpx, uvicorn  # noqa: E402
from book_publishing_iso170 import build_pdf, q3  # noqa: E402
from tejas import structure  # noqa: E402
from fake_supabase231 import Picky  # noqa: E402

OUT = '/tmp/uibridge234'


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    os.makedirs(OUT, exist_ok=True)
    sb = Picky(S.TUS_CHUNK)
    client = httpx.Client(transport=httpx.MockTransport(sb))
    S._client = lambda: client
    S.STATE.update(down_until=0.0, strikes=0, last_error='', auth=None, bucket=None, failovers=0, last_failover=None, backup_since=None)
    own, _ = await mkstaff('owner', 'ui234'); rev, _ = await mkstaff('reviewer', 'ui234')
    slug = J(await own.post('/api/admin/catalog/exams', json={'name': 'DELX', 'short': 'DE', 'subjects': ['Physics'], 'color': 'rose'})).get('slug')
    sec = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Mock Tests', 'description': '', 'layout': 'list', 'kind': 'mocks'})).get('id')
    await structure.exams.update_one({'_id': slug}, {'$set': {'shown': True}})
    K = [(1, 'B'), (2, 'B'), (3, 'C')]
    keep = (await upload(own, build_pdf([{'n': 1, 'qs': q3('UK1'), 'keys': K}, {'n': 2, 'qs': q3('UK2'), 'keys': K}]), 'TEST_LIVE_WALI_PDF', section_id=sec))['id']; await finish(own, keep)
    pair = [m async for m in BM.find({'book_id': keep}).sort('order', 1)]
    await own.post('/api/admin/master/status', json={'items': [{'kind': 'book_mock', 'id': pair[0]['_id']}], 'to': 'live'}); await pump()
    draft = (await upload(own, cut_pdf('UID', long=True), 'TEST_DRAFT_PDF', section_id=sec))['id']; await finish(own, draft)
    md = await BM.find_one({'book_id': draft})
    big = (await upload(own, big_pdf('UIG'), 'TEST_ATKI_BADI_PDF', section_id=sec))['id']
    sb.returned = [f'/books/{big}/original.pdf']
    await finish(own, big); await again(own); await again(own)
    t = time.time()
    hung = (await upload(own, cut_pdf('UIH', long=True), 'TEST_LATKI_PDF', section_id=sec))['id']; await finish(own, hung)
    mh = await BM.find_one({'book_id': hung})
    where = 'book_worker.py:227 step › book_publish.py:402 publish_ready › book_publish.py:283 source_questions'
    await BM.update_one({'_id': mh['_id']}, {'$set': {'publish_requested': True}})
    await DB.tejas_books.update_one({'_id': hung}, {'$set': {'state': 'matching', 'payload.hang': {'count': 3, 'since': t - 1900, 'at': t, 'where': where},
        'payload.storage_wait': {'since': t - 1900, 'at': t, 'kind': 'hang', 'code': None, 'stuck': True, 'error': 'PDF step silent for 600 s',
                                 'reason': 'kaam 3 baar lagataar 10 minute tak bina harkat ke latka raha', 'next': 'Har ghante apne aap phir koshish hogi. Abhi koshish ke liye "Dobara chalao" dabaiye.'}}})
    await DB.tejas_step_hangs.insert_one({'_id': str(uuid.uuid4()), 'at': t, 'book_id': hung, 'job_id': 'test', 'title': 'TEST_LATKI_PDF', 'silent': 600.0, 'last_beat': 'lock renewed',
                                          'where': where, 'stack': '', 'count': 3, 'freed': True, 'server': 'test'})
    safai = (await upload(own, cut_pdf('UIS', long=True), 'TEST_SAFAI_BAAKI', section_id=sec))['id']
    await DB.tejas_books.update_one({'_id': safai}, {'$set': {'removed': True, 'paused': True, 'state': 'removed', 'deleting': {
        'at': t - 120, 'by': 'test', 'tries': 2, 'lease_until': t + 86400, 'storage_removed': 0, 'facts': {}, 'error': 'Supabase abhi jawab nahi de raha; safai uske lautne par hogi.'}}})
    # An AITS section: one PDF that never reached students (its paper has the dustbin) and one marked display-only as having once been a test (no dustbin).
    aits = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'All India Test Series', 'description': '', 'layout': 'list', 'kind': 'aits',
                            'first_date': '2026-12-20', 'days': 5, 'open_time': '09:00', 'last_start': '11:00', 'minutes': 10, 'correct': 4, 'wrong': -1})).get('id')
    ad = (await upload(own, cut_pdf('UIA', long=True), 'TEST_AITS_DRAFT_PDF', section_id=aits))['id']; await finish(own, ad)
    ak = (await upload(own, cut_pdf('UIB', long=True), 'TEST_AITS_PAHUNCHI_PDF', section_id=aits))['id']; await finish(own, ak)
    ma, mk2 = await BM.find_one({'book_id': ad}), await BM.find_one({'book_id': ak})
    await BM.update_one({'_id': mk2['_id']}, {'$set': {'published_generation': 1}})
    state = {b['payload']['title']: b['state'] async for b in DB.tejas_books.find({}, {'state': 1, 'payload.title': 1})}
    state['aits mocks'] = [ma and ma['state'], mk2 and mk2['state']]
    path = OUT + '/bridge.json'
    with open(path, 'w') as f:
        json.dump({'owner': dict(own.cookies), 'reviewer': dict(rev.cookies), 'type': f'/super-admin/exam/{slug}/{sec}', 'keep': {'book': keep, 'live': (await BM.find_one({'_id': pair[0]['_id']}))['set_id'], 'draft': pair[1]['_id']},
                   'draft': {'book': draft, 'mock': md['_id']}, 'big': big, 'hung': {'book': hung, 'mock': mh['_id']}, 'safai': safai,
                   'aits': {'path': f'/super-admin/exam/{slug}/{aits}', 'draft': ma['_id'], 'kept': mk2['_id']}}, f)
    os.chmod(path, 0o600)
    print('READY', H.TEST_DB, json.dumps(state), flush=True)
    server = uvicorn.Server(uvicorn.Config(H.app, host='127.0.0.1', port=8776, log_level='warning', lifespan='off'))
    try:
        await asyncio.wait_for(server.serve(), int(sys.argv[1]) if len(sys.argv) > 1 else 900)
    except asyncio.TimeoutError:
        pass
    finally:
        # the disposable test database of this run only (its name is checked first); the app's own database is never touched
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        try: os.unlink(path)
        except OSError: pass
        print('dropped', H.TEST_DB, flush=True)

asyncio.run(main())
