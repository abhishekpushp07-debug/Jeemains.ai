"""TEST-ONLY iteration 234, packet C: the owner deletes for good an upload that never reached students.
The app's own routes and the real book worker; Supabase faked at the wire (tests/fake_supabase229.py, which lists and removes the
way the real one was seen to on 24 Nov). Disposable DB, no network.
K. an upload from which a test was made: no Delete (list flag, facts, server 409) and it is never touched by another delete.
A. a read PDF with a Draft mock, fixes, a "Try as student" copy, a day and a replace mark; Supabase away during the delete:
   the row leaves at once, the clean-up stays open, the same PDF can be sent again, and the clean-up finishes when Supabase is back.
B. a big PDF stuck at 0 % ("Atki hai"): deleted, then the same PDF is read afresh under its own first identity.
C. a half-sent upload. D. a mock that became a test in the very moment of the delete: the delete is called off, nothing removed.
E. the Supabase remove functions refuse every path that is not one upload's own folder.
Run: cd /app/backend && python tests/upload_delete234.py
"""
import asyncio, hashlib, sys, time, types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage_book229 import H, J, BM, DB, S, JOBS_COL, RESULTS, check, mkstaff, upload, cut_pdf, big_pdf, cancel_kicks, pump, finish, again, row, listed  # noqa: E402
import httpx  # noqa: E402
from book_publishing_iso170 import build_pdf, q3  # noqa: E402
from tejas import structure, book_delete as BD  # noqa: E402
from fake_supabase229 import FakeSupabase  # noqa: E402

M = '/api/admin/master'
PARTS = ('tejas_book_pages', 'tejas_book_page_history', 'tejas_book_parts', 'tejas_book_mocks', 'tejas_book_allowances', 'tejas_book_supplements', 'tejas_book_cuts')


async def records(bid, jobs=True):
    out = {c: await DB[c].count_documents({'book_id': bid}) for c in PARTS}
    out.update(books=await DB.tejas_books.count_documents({'_id': bid}), files=await DB.tejas_files.count_documents({'book_import_id': bid}),
               previews=await DB.tejas_draft_previews.count_documents({'book_id': bid}), preview_sets=await DB.tejas_sets.count_documents({'draft_preview.book_id': bid}))
    if jobs:
        out['jobs'] = await JOBS_COL.count_documents({'kind': 'book_step', 'payload.book_id': bid})
    return out


async def live(own, mid):
    r = await own.post(M + '/status', json={'items': [{'kind': 'book_mock', 'id': mid}], 'to': 'live'}); await pump()
    return r


async def page(own, sec):
    return J(await own.get(f'{M}/types/{sec}/mocks'))


async def settle(want=0, tries=80):
    for _ in range(tries):
        if await DB.tejas_books.count_documents({'deleting': {'$exists': True}}) == want:
            return True
        await asyncio.sleep(.1)
    return False


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    sb = FakeSupabase(S.TUS_CHUNK)
    client = httpx.Client(transport=httpx.MockTransport(sb))
    S._client = lambda: client
    S.time = types.SimpleNamespace(time=time.time, sleep=lambda s: None)
    S.STATE.update(down_until=0.0, strikes=0, last_error='', auth=None, bucket=None, failovers=0, last_failover=None, backup_since=None)
    keep_wait = BD.STEP_WAIT
    BD.STEP_WAIT = 1
    folder = lambda bid: sorted(k for k in sb.objects if k.startswith(f'{S.bucket_name()}/jeelive/books/{bid}/'))  # noqa: E731
    removes = lambda: sum(1 for m, _, p in sb.calls if m == 'DELETE')  # noqa: E731
    try:
        own, own_id = await mkstaff('owner', 'del234'); rev, _ = await mkstaff('reviewer', 'del234'); other, _ = await mkstaff('owner', 'del234b')
        slug = J(await own.post('/api/admin/catalog/exams', json={'name': 'DLX', 'short': 'DL', 'subjects': ['Physics'], 'color': 'rose'})).get('slug')
        sec = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Mock Tests', 'description': '', 'layout': 'list', 'kind': 'mocks'})).get('id')
        url = lambda bid: f'{M}/uploads/book/{bid}/delete'  # noqa: E731

        # ---- K. An upload that reached students (one of its two mocks is Live).
        K3 = [(1, 'B'), (2, 'B'), (3, 'C')]
        z = (await upload(own, build_pdf([{'n': 1, 'qs': q3('DZ1'), 'keys': K3}, {'n': 2, 'qs': q3('DZ2'), 'keys': K3}]), 'TEST_del_keep', section_id=sec))['id']; await finish(own, z)
        zm = [m async for m in BM.find({'book_id': z}).sort('order', 1)]
        await live(own, zm[0]['_id'])
        zset = (await BM.find_one({'_id': zm[0]['_id']})).get('set_id')
        check('K. setup: one mock of the two-mock PDF is Live, the other is a Draft', bool(zset) and (await BM.find_one({'_id': zm[1]['_id']}))['state'] == 'ready' and len(folder(z)) > 1, (zset, len(folder(z))))
        zrec, zfiles = await records(z, jobs=False), folder(z)
        p = await page(own, sec)
        draft = next((i for i in p['items'] if i['id'] == zm[1]['_id']), {})
        check('K. its Draft mock does not offer "Is PDF ko delete karo"', draft.get('upload_deletable') is False, draft)
        f = J(await own.get(url(z)))
        check('K. the box says why it cannot be deleted', f.get('allowed') is False and 'students' in f.get('reason', ''), f)
        r = await own.post(url(z), json={'confirm': 'DELETE'})
        check('K. the server refuses (409) and nothing changed', r.status_code == 409 and await records(z, jobs=False) == zrec and folder(z) == zfiles and not (await row(z)).get('deleting'), (r.status_code, r.text[:200]))

        # ---- A. A read PDF that never reached students, with everything that can hang on it.
        rawx = cut_pdf('DLA', long=True)
        x = (await upload(own, rawx, 'TEST_del_x', section_id=sec))['id']; await finish(own, x)
        mk = await BM.find_one({'book_id': x}); mid = mk['_id']
        r = await own.post(f'{M}/preview/{mid}')
        for _ in range(80):
            s = J(await own.get(f'{M}/preview/{mid}'))
            if s.get('state') != 'building':
                break
            await asyncio.sleep(.25)
        check('A. setup: Draft mock, and its "Try as student" copy is built (pictures now in Supabase)', mk['state'] == 'ready' and s.get('state') == 'ready' and len(folder(x)) > 3, (mk['state'], s, len(folder(x))))
        await BM.update_one({'_id': mid}, {'$set': {'confirmed': ['owner-checked'], 'series_date': '2027-01-05'}})
        await DB.tejas_files.insert_one({'id': 'TESTfile-legacy-' + x, 'book_import_id': x, 'path': f'jeelive/books/{x}/crops/legacy.png', 'kind': 'rendered_png', 'set_id': 'none', 'created_at': time.time()})
        await DB.tejas_books.update_one({'_id': x}, {'$set': {'payload.destination.replaces': [zset]}})
        await DB.tejas_sets.update_one({'id': zset}, {'$set': {'replace_pending': 'TEST_del_x'}})
        xrec, xfiles = await records(x), folder(x)
        p = await page(own, sec)
        it = next((i for i in p['items'] if i['id'] == mid), {})
        check('A. the read PDF is not in Uploads; its Draft mock offers "Is PDF ko delete karo"', it.get('upload_deletable') is True and it.get('status') == 'draft' and not [u for u in p['uploads'] if u['id'] == x], (it, p['uploads']))
        f = J(await own.get(url(x)))
        check('A. the box counts what leaves: 1 Draft mock (1 with fixes), pages, original in Supabase, pictures in both stores, 1 day, the replace mark',
              f.get('allowed') and f['mocks'] == 1 and f['fixed'] == 1 and f['pages'] >= 1 and f['original'] == 'supabase' and f['pictures']['supabase'] >= 3 and f['pictures']['emergent'] == 1
              and f['days'] == 1 and f['replaces'] is True and f['title'] == 'TEST_del_x', f)
        codes = [(await rev.get(url(x))).status_code, (await other.get(url(x))).status_code, (await rev.post(url(x), json={'confirm': 'DELETE'})).status_code,
                 (await other.post(url(x), json={'confirm': 'DELETE'})).status_code, (await own.post(url(x), json={'confirm': 'delete'})).status_code, (await own.post(url(x), json={})).status_code]
        check('A. only the owner of the upload, and only with DELETE typed exactly: reviewer 403, another owner 404, wrong word 422, no word 422', codes == [403, 404, 403, 404, 422, 422]
              and await records(x) == xrec and folder(x) == xfiles and not (await row(x)).get('deleting'), codes)
        sb.down = True
        r = await own.post(url(x), json={'confirm': 'DELETE'}); await asyncio.sleep(.3)
        p = await page(own, sec)
        check('A. DELETE typed: 200, and at once the mock and the upload are in no list and cannot be opened', r.status_code == 200 and J(r).get('deleted') is True
              and not [i for i in p['items'] if i.get('book_id') == x] and not [u for u in p['uploads'] if u['id'] == x] and (await own.get(f'/api/admin/books/{x}')).status_code == 404, (r.status_code, r.text[:200]))
        zs = await DB.tejas_sets.find_one({'id': zset})
        check('A. at once: the old mock it was to replace is no longer marked and is still Live; the day it held is free', 'replace_pending' not in zs and zs['status'] == 'published'
              and (await BM.find_one({'_id': mid})).get('series_date') is None, (zs.get('replace_pending'), zs['status']))
        m = J(await own.get('/api/admin/machine/status'))
        d = (await row(x))['deleting']
        check('A. Supabase is away: nothing was removed yet (Supabase first, records after); the clean-up stays open and Machine counts it', folder(x) == xfiles and {k: v for k, v in (await records(x)).items() if k != 'jobs'} == {k: v for k, v in xrec.items() if k != 'jobs'}
              and m['delete_pending']['count'] == 1 and m['delete_pending']['items'][0]['error'] and d['tries'] >= 1 and d['lease_until'] == 0, (m.get('delete_pending'), d))
        sha = hashlib.sha256(rawx).hexdigest()
        x2 = (await upload(own, rawx, 'TEST_del_x', section_id=sec))['id']; await finish(own, x2)
        r3 = J(await own.post('/api/admin/books', json={'filename': 'TEST_del_x.pdf', 'title': 'TEST_del_x', 'sha256': sha, 'size': len(rawx), 'edition': '', 'rights_confirmed': True, 'section_id': sec}))
        check('A. the same PDF sent again while the clean-up is open is a NEW upload; sent a third time it is that same new upload', x2 != x and r3.get('id') == x2 and (await row(x2))['payload'].get('again') is True, (x, x2, r3.get('id')))
        await DB.tejas_books.update_one({'_id': x}, {'$set': {'deleting.at': time.time() - 1000}})
        m = J(await own.get('/api/admin/machine/status'))
        check('A. a clean-up open for more than 15 minutes asks for attention on the badge', m['delete_pending']['late'] is True and m['attention'] is True, m.get('delete_pending'))
        sb.down = False; cancel_kicks()
        await again(own)
        done = await settle()
        check('A. Supabase is back ("Abhi phir try karo"): the clean-up finishes by itself', done and (await records(x)) == {k: 0 for k in xrec}, await records(x))
        check('A. Supabase: the deleted upload\'s own folder is empty', folder(x) == [], folder(x)[:3])
        a = await DB.tejas_audits.find_one({'action': 'Upload deleted for good', 'resource': x})
        check('A. who, when and what is on record', a and a['actor'] == own_id and '1 Draft mocks (1 with owner fixes)' in a['detail'] and f'{len(xfiles)} files removed from Supabase' in a['detail']
              and await DB.tejas_audits.find_one({'action': 'Upload delete requested', 'resource': x}), a and a.get('detail'))
        m = J(await own.get('/api/admin/machine/status'))
        check('A. Machine: no clean-up left', m['delete_pending']['count'] == 0, m.get('delete_pending'))
        b2 = await row(x2); m2 = await BM.find_one({'book_id': x2})
        check('A. the PDF sent again was read afresh in its own folder', b2['payload']['read_pages'] == b2['payload']['pages'] > 0 and m2 and m2['state'] == 'ready' and m2['_id'] != mid
              and f'{S.bucket_name()}/jeelive/books/{x2}/original.pdf' in sb.objects and not m2.get('confirmed'), (b2['state'], b2['payload'].get('read_pages'), m2 and m2['state']))
        await live(own, m2['_id']); m2 = await BM.find_one({'_id': m2['_id']})
        check('A. ...and goes Live like any upload', m2['state'] in ('published', 'scheduled') and m2.get('set_id'), (m2['state'], m2['issues']))
        zs = await DB.tejas_sets.find_one({'id': zset})
        check('A. the other upload was not touched: same records, same Supabase files, its test still Live', await records(z, jobs=False) == zrec and folder(z) == zfiles and zs['status'] == 'published', (await records(z, jobs=False), zrec))

        # ---- B. A big PDF stuck at 0 % (both big-file routes return it): the case seen on Live.
        rawg = big_pdf('DLG')
        sb.tus_down, sb.one_request_code = True, 400
        g = (await upload(own, rawg, 'TEST_del_big', section_id=sec))['id']; await finish(own, g); await again(own); await again(own)
        up = await listed(own, sec, g)
        half = ((await row(g))['payload'].get('transfer') or {}).get('url', '')
        check('B. setup: the big PDF is "Atki hai" at 0 % and its row offers Delete next to Dobara chalao', up.get('state') == 'stuck' and up.get('can_delete') is True and up.get('can_retry') is True, up)
        sb.tus_down, sb.one_request_code = False, None; cancel_kicks()
        r = await own.post(url(g), json={'confirm': 'DELETE'})
        done = await settle()
        check('B. deleted: no record, no job, nothing in Supabase, the half-sent upload ended', r.status_code == 200 and done and (await records(g)) == {k: 0 for k in xrec} and folder(g) == []
              and (not half or half.rsplit('/', 1)[1] not in sb.uploads) and not await listed(own, sec, g), (r.status_code, await records(g), half))
        g2 = (await upload(own, rawg, 'TEST_del_big', section_id=sec))['id']; await finish(own, g2)
        bg, mg = await row(g2), await BM.find_one({'book_id': g2})
        check('B. the same PDF uploaded again takes its first identity and is read afresh', g2 == g and not bg['payload'].get('again') and bg['payload']['read_pages'] == bg['payload']['pages'] > 0
              and mg and mg['state'] == 'ready' and sb.objects.get(f'{S.bucket_name()}/jeelive/books/{g2}/original.pdf') == rawg, (g, g2, bg['state'], bg['payload'].get('message')))

        # ---- C. A half-sent upload (only its first part reached the server).
        h = (await upload(own, big_pdf('DLH'), 'TEST_del_half', parts=[0], section_id=sec))['id']
        up = await listed(own, sec, h)
        check('C. setup: half-sent upload is listed with Delete', up.get('state') == 'uploading' and up.get('can_delete') is True and await DB.tejas_book_parts.count_documents({'book_id': h}) == 1, up)
        r = await own.post(url(h), json={'confirm': 'DELETE'}); done = await settle()
        check('C. deleted: its parts on the server and its record are gone', r.status_code == 200 and done and (await records(h)) == {k: 0 for k in xrec} and not await listed(own, sec, h), await records(h))

        # ---- D. A mock of the upload became a test in the very moment of the delete.
        w = (await upload(own, cut_pdf('DLW', long=True), 'TEST_del_race', section_id=sec))['id']; await finish(own, w)
        wrec = await records(w, jobs=False)
        await JOBS_COL.insert_one({'id': 'TESTjob-' + w, 'kind': 'book_step', 'status': 'running', 'lease': 'test', 'lease_until': time.time() + 300, 'user_id': own_id, 'set_id': w,
                                   'payload': {'book_id': w, 'key': 'TEST-' + w}, 'created_at': time.time(), 'attempts': 1})
        r = await own.post(url(w), json={'confirm': 'DELETE'}); await asyncio.sleep(.3); cancel_kicks()
        d = (await row(w)).get('deleting') or {}
        check('D. a step is still running on the PDF: nothing is removed yet, the clean-up waits', r.status_code == 200 and await records(w, jobs=False) == wrec and 'kadam' in d.get('error', ''), d)
        await DB.tejas_sets.insert_one({'id': 'TESTset-' + w, 'book_import_id': w, 'status': 'draft', 'title': 'TEST race', 'questions': [], 'created_at': time.time()})
        await JOBS_COL.delete_one({'id': 'TESTjob-' + w})
        out = await BD.resume(); await pump()
        bw = await row(w)
        check('D. that step made a test for students: the delete is called off, the upload is back, nothing was removed', out == 1 and bw['removed'] is False and 'deleting' not in bw and not bw['paused']
              and await records(w, jobs=False) == wrec and await DB.tejas_audits.find_one({'action': 'Upload delete called off', 'resource': w}), (out, bw['state'], await records(w, jobs=False), wrec))
        r = await own.post(url(w), json={'confirm': 'DELETE'})
        check('D. and from now on it cannot be deleted (it reached students)', r.status_code == 409, (r.status_code, r.text[:160]))
        await DB.tejas_sets.delete_one({'id': 'TESTset-' + w, 'book_import_id': w})

        # ---- E. The remove functions themselves refuse any path that is not one upload's own folder.
        before, refused = removes(), 0
        for call in (lambda: S.sb_empty('jeelive/written/abc/'), lambda: S.sb_empty('jeelive/books/'), lambda: S.sb_empty(f'jeelive/books/{z}'), lambda: S.sb_empty('jeelive/'), lambda: S.sb_empty(''),
                     lambda: S.sb_empty(f'jeelive/books/{z}/crops/'), lambda: S.sb_remove(f'jeelive/books/{z}/', [f'jeelive/books/{x2}/original.pdf']),
                     lambda: S.sb_remove(f'jeelive/books/{z}/', [f'jeelive/books/{z}/../{x2}/original.pdf']), lambda: S.sb_remove('tejas/reports/', ['tejas/reports/a.pdf'])):
            try:
                call()
            except ValueError:
                refused += 1
        check('E. nine attempts on other paths (another folder, a parent folder, another upload\'s file, "..") are all refused before any request', refused == 9 and removes() == before, (refused, removes() - before))
        check('E. an upload address of another site is never "ended"', S.sb_end_upload('https://example.com/storage/v1/upload/resumable/abc') is False and S.sb_end_upload('') is False and removes() == before)
        check('E. after everything: the kept upload still has every file and record', await records(z, jobs=False) == zrec and folder(z) == zfiles)
    finally:
        cancel_kicks(); BD.STEP_WAIT = keep_wait
        # the disposable test database of this run only (its name is checked first); the app's own database is never touched
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')


if __name__ == '__main__':
    asyncio.run(main())
