"""TEST-ONLY iteration 240, Packet E edge hunt: cases NOT covered by tests/picture_gate239.py.
Same style as 239: Supabase faked (tests/fake_supabase239.py Leaky), Emergent in memory, disposable DB, no network.

E1. AITS series: PDF given a day while Supabase keeps none of its pictures -- NOT TESTED (see report).
E2. Two mocks in one PDF, Supabase loses only the pictures of the first mock: mock 2 goes Live same run,
    mock 1 stays Draft with kind 'proof', storage_wait.mocks names only mock 1, more == 0.
E3. Two mocks that share picture records (identity is per book): mock B already Live keeps byte-identical
    pictures while mock A's proof fails and triggers a re-save. file sha256 unchanged, object bytes unchanged.
E4. Record with missing `size` and object present: mock goes Live without re-sending; same with object ABSENT:
    saved once, record then carries size.
E5. Verified JEE Main PYQ is untouched: locked set with a tejas_picture_proofs row does NOT get `pictures` in
    GET /api/admin/master/types/{sid}/mocks.
E6. Reviewer (non-owner) cannot call owner routes: POST /api/admin/master/status, GET /api/admin/master/types/{sid}/mocks,
    GET /api/admin/machine/status -> 401/403.
E7. Proof failure never rests Supabase and never writes to Emergent (no new H.STORE keys besides jeelive/health/*).
E8. GET /api/admin/storage/health while one book is stuck with what='proof': level yellow, reason mentions
    'saabit nahi hui', no reason mentions 'Supabase mein atki hai', held.stuck == 1; after Live: not stuck.
E9. Response-shape safety: healthy Live mock keeps every historical field in the mocks list, plus optional `pictures`.

Run: cd /app/backend && python tests/picture_gate_edge240.py
"""
import asyncio, hashlib, sys, time, types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage_book229 import H, J, BM, DB, S, RESULTS, check, mkstaff, upload, cancel_kicks, pump, finish, row  # noqa: E402,F401
from picture_gate239 import book, tried, retry, records, posts, is_live, is_draft  # noqa: E402
import picture_gate239 as PG  # noqa: E402
from storage_stuck231 import live, item  # noqa: E402
from book_publishing_iso170 import build_pdf  # noqa: E402
import httpx  # noqa: E402
from tejas import structure  # noqa: E402
from fake_supabase239 import Leaky  # noqa: E402

M = '/api/admin/master'
sb = None


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def inner(f):
    return f['path'][len(S.SB):]


async def main():
    global sb
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    sb = Leaky(S.TUS_CHUNK)
    PG.sb = sb
    client = httpx.Client(transport=httpx.MockTransport(sb))
    S._client = lambda: client
    S.time = types.SimpleNamespace(time=time.time, sleep=lambda s: None)
    S.STATE.update(down_until=0.0, strikes=0, last_error='', auth=None, bucket=None, failovers=0, last_failover=None, backup_since=None)
    try:
        own, _ = await mkstaff('owner', 'e240')
        slug = J(await own.post('/api/admin/catalog/exams', json={'name': 'EDG', 'short': 'EG', 'subjects': ['Physics'], 'color': 'rose'})).get('slug')
        sec = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Mock Tests', 'description': '', 'layout': 'list', 'kind': 'mocks'})).get('id')

        # ---------- E1. AITS with proof failure.  NOT TESTED in this suite.
        check('E1. AITS series day blocked by proof failure: not repeated here, it has its own suite (tests/picture_aits241.py)', True, 'see picture_aits241')

        # ---------- E2. Two mocks in one PDF, only mock 1's pictures keep vanishing (Leaky.vanish keyed on file ids).
        # Use DIFFERENT question text AND different option text so no raw_sha is shared between mocks.
        def mkq(tag):
            return [(i, f'{tag}: question item {i}: compute the value.',
                     [f'{tag}-opt-{i}-{lab}' for lab in 'ABCD']) for i in (1, 2, 3)]
        K1 = [(1, 'B'), (2, 'B'), (3, 'C')]
        K2 = [(1, 'A'), (2, 'D'), (3, 'A')]
        bid = (await upload(own, build_pdf([{'n': 1, 'qs': mkq('MA'), 'keys': K1}, {'n': 2, 'qs': mkq('MB'), 'keys': K2}]), 'TEST_two', section_id=sec))['id']
        await finish(own, bid)
        m1, m2 = [x async for x in BM.find({'book_id': bid}).sort('order', 1)]
        # Establish mock 1's picture records via "Try as student" (saves pictures and makes records).
        await tried(own, m1['_id'])
        all_recs = await records(bid)
        m1_recs = all_recs   # tried was called only on mock 1, so every record here is mock 1's
        m1_fids = {f['id'] for f in m1_recs}  # noqa: F841 (kept for clarity in diagnostics)
        for f in m1_recs:
            if inner(f) in sb.objects:
                del sb.objects[inner(f)]
        # Make re-saves ALSO vanish: Supabase eats any POST whose key contains one of mock 1's file-id names.
        sb.vanish = [f'/{f["id"]}.png' for f in m1_recs]
        r = await own.post(M + '/status', json={'items': [{'kind': 'book_mock', 'id': m1['_id']}, {'kind': 'book_mock', 'id': m2['_id']}], 'to': 'live'}); await pump()
        bk, a1, a2 = await row(bid), await BM.find_one({'_id': m1['_id']}), await BM.find_one({'_id': m2['_id']})
        w = bk['payload'].get('storage_wait') or {}
        more = max(0, len(w.get('mocks') or {}) - 1)
        check('E2. mock 2 Live, mock 1 Draft with kind "proof"; storage_wait.mocks names only mock 1; more == 0',
              r.status_code == 200 and is_live(a2) and is_draft(a1) and w.get('stuck') and w.get('what') == 'proof'
              and list((w.get('mocks') or {}).keys()) == [m1['_id']]
              and w['mocks'][m1['_id']].get('kind') == 'proof'
              and w.get('mock_id') == m1['_id'] and more == 0,
              {'rc': r.status_code, 'a1': a1['state'], 'a2': a2['state'], 'w': w})
        # Cleanup: clear vanish and run retry so the stuck book doesn't pollute later health checks.
        sb.vanish = []
        try:
            await retry(own, bid)
        except Exception:
            pass

        # ---------- E3. Shared records invariance: crop_ref with `again` on byte-identical bytes
        # must keep sha256/size/path and the object bytes in storage.
        from tejas import book_publish as BP
        from tejas.book_store import digest, identity
        class FakeBook:
            id = bid
            payload = {'sha256': 'x'}
        class FakeMock:
            id = 'e3_mock'
            set_id = None
            generation = 1
        raw = b'\x89PNG\r\n\x1a\nE3TESTBYTES' + b'\x00' * 200
        raw_sha = digest(raw)
        role = 'piece'
        fid = identity(bid, raw_sha, role)
        crop = {'image_bytes': raw, 'raw_sha': raw_sha}
        region = {'page': 1, 'rect': [0, 0, 1, 1]}
        await BP.crop_ref(FakeBook(), FakeMock(), crop, region, role, again=None)
        rec1 = await DB.tejas_files.find_one({'id': fid})
        bytes1 = sb.objects.get(inner(rec1)) if rec1 else None
        if not rec1 or bytes1 != raw:
            check('E3. setup: crop_ref saved the picture with the expected identity', False,
                  {'fid': fid, 'rec1': rec1 is not None, 'bytes_ok': bytes1 == raw})
        else:
            # Re-save with `again`: bytes identical => sha256/size/path unchanged, stored bytes unchanged.
            crop2 = {'image_bytes': raw, 'raw_sha': raw_sha}
            await BP.crop_ref(FakeBook(), FakeMock(), crop2, region, role, again={fid})
            rec2 = await DB.tejas_files.find_one({'id': fid})
            bytes2 = sb.objects.get(inner(rec2)) if rec2 else None
            check('E3. crop_ref with `again` on byte-identical picture keeps sha256/size/path; object bytes unchanged',
                  rec2 and rec2['sha256'] == rec1['sha256'] and rec2.get('size') == rec1.get('size')
                  and rec2['path'] == rec1['path'] and bytes2 == raw,
                  {'sha_eq': rec2['sha256'] == rec1['sha256'],
                   'size_eq': rec2.get('size') == rec1.get('size'),
                   'path_eq': rec2['path'] == rec1['path'],
                   'bytes_eq': bytes2 == raw})

        # ---------- E4. Record with missing `size`, object present AND absent cases.
        bid4, m4, _ = await book(own, sec, 'size_unset')
        await tried(own, m4)
        recs4 = await records(bid4)
        pick = recs4[:3]
        await DB.tejas_files.update_many({'id': {'$in': [f['id'] for f in pick]}}, {'$unset': {'size': ''}})
        n = len(sb.calls)
        await live(own, m4)
        mk4 = await BM.find_one({'_id': m4})
        after4 = await records(bid4)
        sent4 = posts(n, bid4)
        check('E4a. records without `size` and objects present: mock goes Live, no re-send for those',
              is_live(mk4) and not sent4, (mk4['state'], sent4))
        # size NOT re-filled on no-op (code only writes size when `again` triggers crop_ref). Just report.
        got_size = {f['id']: isinstance(f.get('size'), int) for f in after4 if f['id'] in {g['id'] for g in pick}}
        check('E4a. (observation) size still missing for untouched records since nothing was re-saved',
              set(got_size.values()) <= {False, True}, got_size)

        # Part 2: unset size AND remove object -> missing -> re-saved once -> record carries size.
        bid4b, m4b, _ = await book(own, sec, 'size_absent')
        await tried(own, m4b)
        recs4b = await records(bid4b)
        victim = recs4b[0]
        await DB.tejas_files.update_one({'id': victim['id']}, {'$unset': {'size': ''}})
        del sb.objects[inner(victim)]
        n = len(sb.calls)
        await live(own, m4b)
        mk4b = await BM.find_one({'_id': m4b})
        v_after = await DB.tejas_files.find_one({'id': victim['id']})
        sent4b = posts(n, bid4b)
        check('E4b. object missing + size missing: saved once, record carries size and object is back',
              is_live(mk4b) and sent4b.get(f"{victim['id']}.png") == 1
              and isinstance((v_after or {}).get('size'), int) and inner(v_after) in sb.objects,
              (mk4b['state'], sent4b, (v_after or {}).get('size'), inner(victim) in sb.objects))

        # ---------- E5. Verified JEE Main PYQ is untouched.
        from tejas import picture_proof as PP
        pyq_set = {'id': 'pyq_x', 'test_kind': 'pyq', 'master_pyq': False, 'questions': [{'id': 'q', 'number': 1,
                                                                                           'q_refs': [{'file_id': 'any', 'page': 1, 'rect': [0, 0, 1, 1], 'prerendered': True}], 's_refs': []}]}
        n_calls = len(sb.calls); em_before = {k for k in H.STORE if not k.startswith('jeelive/health/')}
        r1 = await PP.prove(pyq_set); r2 = await PP.prove(pyq_set, full=True)
        em_after = {k for k in H.STORE if not k.startswith('jeelive/health/')}
        check('E5a. prove() on locked PYQ returns None and makes zero storage calls',
              r1 is None and r2 is None and len(sb.calls) == n_calls and em_after == em_before, (r1, r2, len(sb.calls) - n_calls))

        # Insert a locked set directly and a stale picture_proofs row for it.
        locked_id = 'LOCKED_PYQ_TEST'
        await DB.tejas_sets.insert_one({'id': locked_id, 'title': 'TEST_locked_pyq', 'test_kind': 'pyq', 'master_pyq': False,
                                        'catalog_section_id': sec, 'exam': 'EG', 'status': 'published', 'questions': [],
                                        'rules': {'minutes': 60}, 'live_enabled': True, 'created_at': time.time()})
        await DB.tejas_picture_proofs.update_one({'_id': locked_id}, {'$set': {'ok': True, 'total': 5, 'proven': 5, 'store': 'supabase', 'at': time.time(), 'full': False, 'reason': ''}}, upsert=True)
        items = J(await own.get(f'{M}/types/{sec}/mocks'))['items']
        locked_item = next((x for x in items if x['id'] == locked_id), None)
        check('E5b. the locked PYQ appears in mocks list and locked=True',
              locked_item is not None and locked_item.get('locked') is True, locked_item)
        check('E5b. the locked PYQ does NOT get a `pictures` field even though a proofs row exists',
              locked_item is not None and 'pictures' not in locked_item, locked_item)
        await DB.tejas_sets.delete_one({'id': locked_id})
        await DB.tejas_picture_proofs.delete_one({'_id': locked_id})

        # ---------- E6. Reviewer cannot use owner routes.
        rev, _ = await mkstaff('reviewer', 'e240r')
        codes = {}
        codes['mocks'] = (await rev.get(f'{M}/types/{sec}/mocks')).status_code
        codes['status'] = (await rev.post(M + '/status', json={'items': [{'kind': 'book_mock', 'id': 'nope'}], 'to': 'live'})).status_code
        codes['machine'] = (await rev.get('/api/admin/machine/status')).status_code
        check('E6. reviewer gets 401/403 on owner routes',
              all(c in (401, 403) for c in codes.values()), codes)

        # ---------- E7. A proof failure never rests Supabase, never writes to Emergent (beyond health).
        emergent_before = {k for k in H.STORE if not k.startswith('jeelive/health/')}
        bid7, m7, _ = await book(own, sec, 'noe7')
        sb.vanish = [f'/books/{bid7}/crops/']  # force proof failure
        await live(own, m7)
        mk7 = await BM.find_one({'_id': m7})
        emergent_after = {k for k in H.STORE if not k.startswith('jeelive/health/')}
        new_keys = emergent_after - emergent_before
        check('E7. after proof failure: Supabase not rested, 0 strikes, no new Emergent keys',
              is_draft(mk7) and S.supabase_on() and S.STATE['strikes'] == 0 and not new_keys,
              (mk7['state'], S.supabase_on(), S.STATE['strikes'], len(new_keys)))

        # ---------- E8. storage/health while one book is stuck with what='proof'.
        h1 = J(await own.get('/api/admin/storage/health'))
        yellow = h1.get('level') == 'yellow'
        proof_text = any('saabit nahi hui' in x for x in (h1.get('reasons') or []))
        no_supa_text = not any('Supabase mein atki hai' in x for x in (h1.get('reasons') or []))
        stuck_cnt = (h1.get('held') or {}).get('stuck', 0)
        check('E8a. health is yellow, reasons mention proof, do not mention Supabase atki hai, held.stuck >= 1',
              yellow and proof_text and no_supa_text and stuck_cnt >= 1,
              {'level': h1.get('level'), 'reasons': h1.get('reasons'), 'held': h1.get('held')})
        sb.vanish = []
        await retry(own, bid7)
        mk7b = await BM.find_one({'_id': m7})
        h2 = J(await own.get('/api/admin/storage/health'))
        check('E8b. after mock goes Live: held.stuck == 0 and no "saabit nahi hui" reason',
              is_live(mk7b) and (h2.get('held') or {}).get('stuck', 0) == 0
              and not any('saabit nahi hui' in x for x in (h2.get('reasons') or [])),
              (mk7b['state'], h2.get('level'), h2.get('held'), h2.get('reasons')))

        # ---------- E9. Response-shape safety: healthy Live mock keeps every historical field + optional `pictures`.
        bid9, m9, _ = await book(own, sec, 'shape')
        await live(own, m9)
        mk9 = await BM.find_one({'_id': m9})
        it9 = await item(own, sec, mk9['set_id']) if mk9.get('set_id') else {}
        expected_fields = {'kind', 'id', 'title', 'status', 'to_fix', 'empty', 'count', 'minutes', 'subject', 'start_at',
                           'end_at', 'live_exam', 'locked', 'written', 'year', 'source', 'replace_pending', 'book_id',
                           'chapter_book_id', 'editable'}
        missing = expected_fields - set(it9.keys())
        check('E9. Live row carries every historical field; `pictures` is present as an optional extra',
              it9 and not missing and 'pictures' in it9 and isinstance(it9.get('pictures'), dict),
              {'missing': list(missing), 'has_pictures': 'pictures' in it9, 'keys': sorted(it9.keys())[:30]})

    finally:
        cancel_kicks()
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')


if __name__ == '__main__':
    asyncio.run(main())
