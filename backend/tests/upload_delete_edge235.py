"""TEST-ONLY iteration 235, packet C edges NOT covered by tests/upload_delete234.py.
This file does not repeat the main agent's 31 checks; it adds edges around the Pydantic body, the Supabase refusal gate,
owner isolation + unknown ids, sb_end_upload hostname check, concurrent POST / double sweep, and pending()/machine edges.
Isolated DB, fake Supabase (fake_supabase229.FakeSupabase), the real app routes and the real book worker.
Run: cd /app/backend && python tests/upload_delete_edge235.py
"""
import asyncio, sys, time, types, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage_book229 import H, J, BM, DB, S, JOBS_COL, RESULTS, check, mkstaff, upload, cut_pdf, cancel_kicks, pump, finish, again, row, listed  # noqa: E402
import httpx  # noqa: E402
from tejas import structure, book_delete as BD  # noqa: E402
from fake_supabase229 import FakeSupabase  # noqa: E402


M = '/api/admin/master'


async def records_count(bid):
    return {c: await DB[c].count_documents({'book_id' if c != 'tejas_books' and c != 'tejas_files' else ('_id' if c == 'tejas_books' else 'book_import_id'): bid})
            for c in ('tejas_books', 'tejas_book_pages', 'tejas_book_mocks', 'tejas_book_parts', 'tejas_files')}


async def settle(want=0, tries=100):
    for _ in range(tries):
        if await DB.tejas_books.count_documents({'deleting': {'$exists': True}}) == want:
            return True
        await asyncio.sleep(.05)
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
    url = lambda bid: f'{M}/uploads/book/{bid}/delete'  # noqa: E731

    try:
        own, own_id = await mkstaff('owner', 'edge235')
        rev, _ = await mkstaff('reviewer', 'edge235')
        other, _ = await mkstaff('owner', 'edge235b')
        slug = J(await own.post('/api/admin/catalog/exams', json={'name': 'ELX', 'short': 'EL', 'subjects': ['Physics'], 'color': 'rose'})).get('slug')
        sec = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Mock Tests', 'description': '', 'layout': 'list', 'kind': 'mocks'})).get('id')

        # --------- section 1: body validation edges on POST ---------
        # Seed one deletable PDF (read fully, never Live).
        raw = cut_pdf('EB1', long=True)
        b = (await upload(own, raw, 'TEST_ed_body', section_id=sec))['id']; await finish(own, b)
        bookfiles = folder(b)
        bookrec = await records_count(b)

        # Every one of these bodies must be refused as 422 and leave the upload untouched (no `deleting` mark).
        bad_bodies = [
            {'confirm': ''},                           # empty string
            {'confirm': ' DELETE'},                    # leading space
            {'confirm': 'DELETE '},                    # trailing space
            {'confirm': 'DELETE\n'},                   # trailing newline
            {'confirm': '\tDELETE'},                   # tab
            {'confirm': 'Delete'},                     # capitalised
            {'confirm': 'DELETEE'},                    # longer
            {'confirm': 'ELETE'},                      # shorter
            {'confirm': 'ＤＥＬＥＴＥ'},                 # full-width unicode
            {'confirm': None},                         # null
            {'confirm': True},                         # bool
            {'confirm': 1},                            # int
            {'confirm': ['DELETE']},                   # list
            {'confirm': 'DELETE', 'extra': 1},         # extra forbid
            {'confirm': 'DELETE', 'id': b},            # extra forbid (id)
            {},                                        # missing
            {'CONFIRM': 'DELETE'},                     # wrong key
        ]
        codes = []
        for body in bad_bodies:
            r = await own.post(url(b), json=body)
            codes.append(r.status_code)
        all_422 = all(c == 422 for c in codes)
        check('1A. every malformed body returns 422', all_422, codes)
        check('1A. upload row is unchanged by 17 bad-body attempts', await records_count(b) == bookrec and folder(b) == bookfiles
              and not (await row(b)).get('deleting'), (await records_count(b), bookrec))

        # Non-JSON bodies / wrong content types
        r = await own.post(url(b), content=b'not json', headers={'content-type': 'application/json'})
        check('1B. non-JSON body is refused with 4xx', 400 <= r.status_code < 500, r.status_code)

        # Exact 'DELETE' with the standard client headers must succeed (and show the body validator is not over-strict either).
        r = await own.post(url(b), json={'confirm': 'DELETE'})
        check('1C. the exact body {"confirm":"DELETE"} is accepted', r.status_code == 200 and J(r).get('deleted') is True, (r.status_code, r.text[:160]))
        await settle()

        # --------- section 2: unknown id / role / other-owner isolation ---------
        unknown = uuid.uuid4().hex
        c1 = (await own.get(url(unknown))).status_code
        c2 = (await own.post(url(unknown), json={'confirm': 'DELETE'})).status_code
        check('2A. an unknown id gives 404 on both GET and POST', c1 == 404 and c2 == 404, (c1, c2))

        # A deletable PDF owned by `other`; the first owner must never see or touch it.
        raw2 = cut_pdf('EOX', long=True)
        other_b = (await upload(other, raw2, 'TEST_ed_other', section_id=sec))['id']; await finish(other, other_b)
        c3 = (await own.get(url(other_b))).status_code
        c4 = (await own.post(url(other_b), json={'confirm': 'DELETE'})).status_code
        c5 = (await rev.get(url(other_b))).status_code
        c6 = (await rev.post(url(other_b), json={'confirm': 'DELETE'})).status_code
        check('2B. another owner sees 404 on GET and POST (no existence leak via 403)', c3 == 404 and c4 == 404, (c3, c4))
        check('2C. a reviewer is refused on GET and POST (401/403), never 200', c5 in (401, 403) and c6 in (401, 403), (c5, c6))
        check('2D. the other owner\'s upload is unchanged', (await row(other_b)) is not None and not (await row(other_b)).get('deleting'),
              (await row(other_b)).get('deleting'))

        # --------- section 3: _removable / sb_remove / sb_empty / sb_end_upload gate ---------
        before = len(sb.calls)
        refused = 0
        good_id = uuid.uuid4().hex  # a valid-shaped uuid we never created
        lower_folder = f'jeelive/books/{good_id}/'
        upper_id = good_id.upper()
        bad_calls = [
            # uppercase UUID folder (regex is [0-9a-f], must refuse)
            lambda: S.sb_empty(f'jeelive/books/{upper_id}/'),
            # no trailing slash
            lambda: S.sb_empty(f'jeelive/books/{good_id}'),
            # double slash in path
            lambda: S.sb_empty(f'jeelive//books/{good_id}/'),
            # outside jeelive
            lambda: S.sb_empty(f'tejas/books/{good_id}/'),
            # extra sub-path on the "folder" value
            lambda: S.sb_empty(f'jeelive/books/{good_id}/crops/'),
            # names referring to another upload
            lambda: S.sb_remove(lower_folder, [f'jeelive/books/{uuid.uuid4().hex}/original.pdf']),
            # ".." in a name
            lambda: S.sb_remove(lower_folder, [f'{lower_folder}../x/original.pdf']),
            # name does not start with folder prefix
            lambda: S.sb_remove(lower_folder, ['other/original.pdf']),
            # name ends with "/" (a sub-folder would be silently dropped)
            lambda: S.sb_remove(lower_folder, [lower_folder + 'sub/']),
            # mixed: one valid + one invalid -> whole call must be refused, nothing removed
            lambda: S.sb_remove(lower_folder, [lower_folder + 'a.pdf', '/etc/passwd']),
            # backslash name
            lambda: S.sb_remove(lower_folder, [lower_folder + '..\\x.pdf']),
            # empty folder string
            lambda: S.sb_remove('', [lower_folder + 'a.pdf']),
            # folder is just the root
            lambda: S.sb_empty('/'),
        ]
        for c in bad_calls:
            try:
                c()
            except ValueError:
                refused += 1
            except Exception as e:  # noqa: BLE001
                check(f'3X. a refused-path call raised {type(e).__name__} instead of ValueError', False, str(e)[:160])
        check(f'3A. all {len(bad_calls)} bad-path attempts raise ValueError before any request', refused == len(bad_calls), refused)
        check('3A. no DELETE/POST reached Supabase during those attempts', len(sb.calls) == before, len(sb.calls) - before)

        # sb_end_upload: wrong scheme, wrong hostname, wrong path, empty — all False, no network call
        ends = [
            S.sb_end_upload('http://' + 'abcdefghijklmnopqrst.supabase.co' + '/storage/v1/upload/resumable/x'),  # http scheme
            S.sb_end_upload('https://evil.example.com/storage/v1/upload/resumable/x'),                           # foreign host
            S.sb_end_upload('https://abcdefghijklmnopqrst.supabase.co/storage/v1/object/public/x'),              # not an upload path
            S.sb_end_upload('https://abcdefghijklmnopqrst.supabase.co/storage/v1/upload/resumable/'),             # empty last segment (still prefix match => should pass prefix test)
            S.sb_end_upload(None),
            S.sb_end_upload(''),
            S.sb_end_upload('not a url'),
        ]
        # Of these, only index 3 may be True/False depending on fake; the first 3 and last 3 MUST be False without any network call.
        check('3B. sb_end_upload refuses http scheme, foreign host, non-upload path, None, empty, garbage',
              ends[0] is False and ends[1] is False and ends[2] is False and ends[4] is False and ends[5] is False and ends[6] is False, ends)

        # --------- section 4: concurrent double POST + idempotent sweep ---------
        raw3 = cut_pdf('EDC', long=True)
        c = (await upload(own, raw3, 'TEST_ed_conc', section_id=sec))['id']; await finish(own, c)

        # Fire two POSTs in the same loop turn; one succeeds, one 404s, nothing crashes.
        r1, r2 = await asyncio.gather(own.post(url(c), json={'confirm': 'DELETE'}),
                                      own.post(url(c), json={'confirm': 'DELETE'}), return_exceptions=True)
        codes = sorted([getattr(r1, 'status_code', 500), getattr(r2, 'status_code', 500)])
        await settle(); cancel_kicks()
        check('4A. concurrent double POST -> one 200 and one 404, no 500', codes == [200, 404], codes)
        check('4A. the upload is fully gone exactly once', (await records_count(c))['tejas_books'] == 0 and folder(c) == [],
              (await records_count(c), folder(c)[:3]))

        # resume() called twice in parallel on an open sweep must not double-process (lease guards it).
        # Seed a stuck clean-up by bringing Supabase down after the row is marked.
        raw4 = cut_pdf('EDS', long=True)
        d = (await upload(own, raw4, 'TEST_ed_resume', section_id=sec))['id']; await finish(own, d)
        sb.down = True
        r = await own.post(url(d), json={'confirm': 'DELETE'}); await asyncio.sleep(.2); cancel_kicks()
        check('4B. setup: clean-up is open with Supabase down', r.status_code == 200 and (await row(d)).get('deleting', {}).get('error'),
              (await row(d)).get('deleting'))
        before_tries = (await row(d))['deleting'].get('tries', 0)
        # Two parallel resume() calls; only one may claim the lease. (The other sees lease_until>now and returns None.)
        out1, out2 = await asyncio.gather(BD.resume(), BD.resume())
        after_tries = (await row(d))['deleting'].get('tries', 0)
        # sweep() returns False on StorageError (resume adds bool->0), and None when the lease blocks it.
        # The correct behaviour is that exactly ONE of the two parallel resume() claimed the lease (tries+=1);
        # the other saw lease_until>now and did nothing. No double-delete, no crash.
        check('4B. two parallel resume() -> exactly one sweep claims the lease, no double-delete',
              after_tries == before_tries + 1 and out1 in (0, None) and out2 in (0, None),
              (out1, out2, before_tries, after_tries))
        # pending() shows the stuck one.
        pend = await BD.pending()
        check('4C. pending() lists the stuck clean-up with its error text', pend['count'] >= 1 and any(it.get('error') for it in pend.get('items', [])),
              pend)
        # Bring Supabase back; a final resume() finishes it.
        sb.down = False
        done = 0
        for _ in range(8):
            done += bool(await BD.resume())
            if (await DB.tejas_books.count_documents({'_id': d})) == 0:
                break
            await asyncio.sleep(.1)
        check('4D. resume() after Supabase is back finishes the open clean-up', (await records_count(d))['tejas_books'] == 0 and folder(d) == [],
              (await records_count(d), folder(d)[:3]))
        pend = await BD.pending()
        check('4D. pending() is empty after finishing', pend['count'] == 0, pend)

        # --------- section 5: GET returns full counted facts and refuses reviewer/unknown ---------
        raw5 = cut_pdf('EGF', long=True)
        e = (await upload(own, raw5, 'TEST_ed_facts', section_id=sec))['id']; await finish(own, e)
        f = J(await own.get(url(e)))
        needed = {'id', 'title', 'allowed', 'reason', 'mocks', 'fixed', 'pages', 'original', 'pictures', 'days', 'replaces', 'supabase'}
        check('5A. GET facts has every counted field', needed <= set(f.keys()) and isinstance(f.get('pictures'), dict)
              and {'supabase', 'emergent'} <= set(f['pictures'].keys()) and f['allowed'] is True, (set(f.keys()), f.get('pictures')))
        check('5B. reviewer is refused on GET facts', (await rev.get(url(e))).status_code in (401, 403))
        check('5B. another owner gets 404 on GET facts (no leak)', (await other.get(url(e))).status_code == 404)

        # Clean up this last one.
        await own.post(url(e), json={'confirm': 'DELETE'}); await settle()

    finally:
        cancel_kicks(); BD.STEP_WAIT = keep_wait
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')


if __name__ == '__main__':
    asyncio.run(main())
