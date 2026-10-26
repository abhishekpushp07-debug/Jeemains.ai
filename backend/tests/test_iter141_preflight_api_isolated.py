"""TEST-ONLY iteration 141: API-level PYQ preflight batch validation in the isolated DB (tejas_isolated_iter134).
Reuses iter139 harness (storage GET -> original local PDFs, PUT forbidden; synthetic header users). Real app routes.
Covers per-user authorization before shared immutable proof, per-user preflight records/revision, coalescing,
negative refs/membership/hash/missing-file before any preflight write, and non-PYQ original validate_refs path.
Run (foreground, NOT while iso_bridge_pyq_iter139.py runs): python -m pytest test_iter141_preflight_api_isolated.py -n0 -p no:cacheprovider -v
"""
import asyncio, copy, gzip, json, time, uuid
from pathlib import Path
import pytest
import test_iter139_pyq_isolated as T
from tejas import derivatives
import tejas_core

H, TDB, run = T.H, T.TDB, T.run
PID = 'jee-main-pyq-2026-01-21-s1'
SET = copy.deepcopy(next(s for s in T.SETS if s['id'] == PID))
FID = SET['file_ids'][0]
FILE = copy.deepcopy(next(f for f in T.FILES if f['id'] == FID))
for i in range(1, 7):
    H.USERS['f%d' % i] = {'id': 'TEST_U141_f%d' % i, 'role': 'student', 'name': 'TEST F%d' % i, 'phone': '+91990000141%d' % i,
                          'access_type': 'unverified_phone', 'exam': 'JEE Main'}
F = [{'x-test-user': 'f%d' % i} for i in range(1, 7)]
S, O = T.S, T.O
EV = {}


def reset():
    for c in (derivatives._cache, tejas_core._crop_cache, derivatives._validation_cache):
        with c.lock:
            c.data.clear(); c.size = 0


async def pf(c, h, pid=PID):
    t = time.perf_counter(); r = await c.post(f'/api/sets/{pid}/preflight', headers=h, json={'test_response': 'ok'})
    return r, round(time.perf_counter() - t, 3)


async def rec(uid_, pid=PID):
    return await TDB.tejas_preflight.find_one({'user_id': uid_, 'set_id': pid}, {'_id': 0})


async def patch_set(upd, pid=PID):
    await TDB.tejas_sets.update_one({'id': pid}, upd)


@pytest.fixture(scope='module', autouse=True)
def isolated():
    assert H.TEST_DB != H.REAL_DB and not H.leftover_real_handles()
    run(H.tdbmod.client.drop_database(H.TEST_DB)); run(H.tdbmod.indexes())
    run(TDB.tejas_sets.insert_one(copy.deepcopy(SET))); run(TDB.tejas_files.insert_one(copy.deepcopy(FILE)))
    mock = copy.deepcopy(SET); mock.update(id='TEST_mock141', test_kind='mock', title='TEST mock141')
    run(TDB.tejas_sets.insert_one(mock))
    yield
    run(H.tdbmod.client.drop_database(H.TEST_DB))
    EV['db_dropped'] = H.TEST_DB not in run(H.tdbmod.client.list_database_names()); EV['puts'] = T.PUTS
    Path('/app/test_reports/iter141_preflight_api_evidence.json').write_text(json.dumps(EV, indent=2, default=str))
    assert EV['db_dropped'] and not T.PUTS


@pytest.fixture(autouse=True)
def restore():
    yield
    run(TDB.tejas_sets.replace_one({'id': PID}, copy.deepcopy(SET)))
    run(TDB.tejas_files.replace_one({'id': FID}, copy.deepcopy(FILE), upsert=True))
    T.TAMPER.clear()


# cold then warm across two users; separate per-user records; no answers/solutions leaked
def test_cold_warm_per_user_records_no_leak():
    reset()
    async def go():
        async with T.client() as c:
            g0 = len(T.GETS); a, ta = await pf(c, S); g1 = len(T.GETS); b, tb = await pf(c, O); g2 = len(T.GETS)
            return a, ta, b, tb, g1 - g0, g2 - g1, await rec(S['x-test-user'] and 'TEST_U139_s'), await rec('TEST_U139_o')
    a, ta, b, tb, gc, gw, rs, ro = run(go())
    EV['api_cold_s'], EV['api_warm_other_user_s'], EV['gets_cold'], EV['gets_warm'] = ta, tb, gc, gw
    assert a.status_code == 200 and b.status_code == 200, (a.text, b.text)
    assert gc == 1 and gw == 0
    assert rs and ro and rs['revision'] == ro['revision'] == SET['revision'] and rs['user_id'] != ro['user_id']
    body = a.text.lower()
    for k in ('"answer"', 'accepted_answers', '"solution"', 's_refs', 'q_refs', 'rect', FILE['path'].lower()):
        assert k not in body, k
    assert tb < 0.5


# 4 concurrent cold API preflights (different users) coalesce to one source GET; 4 records
def test_four_concurrent_api_coalesced():
    reset()
    async def go():
        async with T.client() as c:
            g0 = len(T.GETS); t = time.perf_counter()
            rs = await asyncio.gather(*[pf(c, F[i]) for i in range(4)])
            return [r[0].status_code for r in rs], round(time.perf_counter() - t, 3), len(T.GETS) - g0, \
                [await rec('TEST_U141_f%d' % (i + 1)) for i in range(4)]
    codes, wall, gets, recs = run(go())
    EV['api_concurrent4'] = {'codes': codes, 'wall_s': wall, 'gets': gets}
    assert codes == [200] * 4 and gets == 1 and all(recs)


# cached proof never bypasses per-user authorization / audience / availability
def test_authorization_before_cached_proof():
    async def go():
        async with T.client() as c:
            assert (await pf(c, S))[0].status_code == 200  # proof warm
            before = await rec('TEST_U139_o')
            await patch_set({'$set': {'audience': 'restricted', 'allowed_phones': [T.STUDENT['phone']], 'allowed_emails': []}})
            ro, _ = await pf(c, O); rs, _ = await pf(c, S); rn, _ = await pf(c, F[5])
            after = await rec('TEST_U139_o'); newrec = await rec('TEST_U141_f6')
            await patch_set({'$set': {'status': 'draft', 'audience': 'all'}}); rd, _ = await pf(c, S)
            await patch_set({'$set': {'status': 'published', 'expires': '2000-01-01'}}); rx, _ = await pf(c, S)
            return ro.status_code, rs.status_code, rn.status_code, before == after, newrec, rd.status_code, rx.status_code
    o = run(go()); EV['authz'] = o
    assert o[0] == 404 and o[1] == 200 and o[2] == 404 and o[3] and o[4] is None and o[5] == 404 and o[6] == 404, o


# fresh set revision is required at start, proof reuse does not refresh another user's record
def test_revision_requires_fresh_preflight():
    async def go():
        async with T.client() as c:
            assert (await pf(c, F[4]))[0].status_code == 200
            await patch_set({'$inc': {'revision': 1}})
            st = await c.post(f'/api/sets/{PID}/start', headers=F[4], json={'start_key': 'TEST_K141_' + uuid.uuid4().hex, 'device_checked': True})
            r2, t2 = await pf(c, F[4]); r = await rec('TEST_U141_f5')
            st2 = await c.post(f'/api/sets/{PID}/start', headers=F[4], json={'start_key': 'TEST_K141_' + uuid.uuid4().hex, 'device_checked': True})
            return st.status_code, st.text[:120], r2.status_code, r['revision'], st2.status_code, t2
    o = run(go()); EV['revision'] = o
    assert o[0] == 400 and 'check again' in o[1] and o[2] == 200 and o[3] == SET['revision'] + 1 and o[4] == 200, o


def _last(mut):
    s = copy.deepcopy(SET); mut(s['questions'][-1]); return s


# negative LAST-ref cases fail with 400 before any preflight write and are not cached
@pytest.mark.parametrize('name,mut,code,gets', [
    ('foreign_file', lambda q: q['s_refs'].append({'file_id': 'TEST_foreign141', 'page': 1, 'rect': [0, 0, 10, 10]}), 400, 0),
    ('bad_coords', lambda q: q['s_refs'][-1].update(rect=[0, 0, 99999, 99999]), 400, 1),
    ('invalid_page', lambda q: q['s_refs'][-1].update(page=999), 400, 1),
    ('bad_omit', lambda q: q['s_refs'][-1].update(omit_rects=[[-50, -50, -10, -10]]), 400, 1),
    ('missing_page_key', lambda q: q['s_refs'][-1].pop('page'), 400, 1),
])
def test_negative_last_ref_no_write(name, mut, code, gets):
    reset()
    async def go():
        await TDB.tejas_sets.replace_one({'id': PID}, _last(mut))
        async with T.client() as c:
            out = []
            for _ in range(2):
                g0 = len(T.GETS); r, _ = await pf(c, F[5]); out.append((r.status_code, len(T.GETS) - g0, r.text[:100]))
            return out, await rec('TEST_U141_f6')
    out, record = run(go()); EV.setdefault('negatives', {})[name] = out
    assert all(o[0] == code and o[1] == gets for o in out), out
    assert record is None


# iter142: PYQ hash mismatch -> honest 503 (timer not started), retried (not cached), no write/attempt; non-PYQ old 400 unchanged
def test_hash_mismatch_503_no_write():
    reset(); T.TAMPER.add(FILE['path'])
    async def go():
        async with T.client() as c:
            na = await TDB.tejas_attempts.count_documents({})
            g0 = len(T.GETS); a, _ = await pf(c, F[5]); g1 = len(T.GETS); b, _ = await pf(c, F[5]); g2 = len(T.GETS)
            m, _ = await pf(c, F[5], 'TEST_mock141')
            nb = await TDB.tejas_attempts.count_documents({}); assert await rec('TEST_U141_f6') is None
            T.TAMPER.clear(); ok, _ = await pf(c, F[5]); await TDB.tejas_preflight.delete_many({'user_id': 'TEST_U141_f6'})  # recovers once the source verifies (failure was not cached)
            return (a.status_code, str(a.json().get('error')), b.status_code, m.status_code, await rec('TEST_U141_f6', 'TEST_mock141'),
                    g1 - g0, g2 - g1, na == nb, ok.status_code)
    o = run(go()); EV['hash_mismatch'] = o
    assert o[0] == o[2] == 503 and 'could not be verified' in o[1] and 'timer has not started' in o[1], o
    assert 'coordinates' not in o[1] and o[3] == 400 and o[4] is None, o
    assert o[5] == 1 and o[6] == 1 and o[7] and o[8] == 200, o


# iter142: validation locks are distinct from asset render locks -> an asset with colliding stripe renders while validation is pending
def test_validation_lock_distinct_from_asset_lock():
    import threading
    assert derivatives._validation_locks is not derivatives._locks
    assert not any(a is b for a in derivatives._validation_locks for b in derivatives._locks)
    reset()
    src = run(TDB.tejas_files.find_one({'id': FID}, {'_id': 0}))
    refs = [r for q in SET['questions'][:3] for r in q['q_refs']]
    idx = 7; held = derivatives._validation_locks[idx]
    held.acquire()
    try:
        # find an asset ref whose render stripe == idx; render while validation stripe idx is held
        done = {}
        t = threading.Thread(target=lambda: done.setdefault('png', derivatives.render_crop(src, refs[0])))
        t.start(); t.join(30)
        assert done.get('png', b'')[:4] == b'\x89PNG', 'asset render blocked by held validation lock'
    finally:
        held.release()
    # with ALL validation stripes held, asset render still completes; then validation proceeds (no deadlock)
    for lk in derivatives._validation_locks: lk.acquire()
    try:
        done = {}
        t = threading.Thread(target=lambda: done.setdefault('png', derivatives.render_crop(src, refs[1], scale=1)))
        t.start(); t.join(30); assert done.get('png', b'')[:4] == b'\x89PNG'
        v = threading.Thread(target=lambda: (derivatives.validate_source_crops(src, refs), done.setdefault('v', True)))
        v.start(); time.sleep(0.5); assert 'v' not in done  # validation waits on its own lock
    finally:
        for lk in derivatives._validation_locks: lk.release()
    v.join(60); assert done.get('v') is True
    EV['lock_split'] = True


# missing file -> 404 same as old (non-PYQ validate_refs) path; no write
def test_missing_file_404_same_as_old():
    async def go():
        await TDB.tejas_files.delete_one({'id': FID})
        async with T.client() as c:
            a, _ = await pf(c, F[5]); m, _ = await pf(c, F[5], 'TEST_mock141')
            return a.status_code, m.status_code, a.json().get('error'), m.json().get('error'), await rec('TEST_U141_f6')
    o = run(go()); EV['missing_file'] = o
    assert o[0] == 404 and o[1] == 404 and o[2] == o[3] and o[4] is None, o


# non-PYQ set still uses original per-ref validate_refs (one GET per unique ref cold)
def test_non_pyq_uses_original_path():
    reset()
    async def go():
        async with T.client() as c:
            g0 = len(T.GETS); r, t = await pf(c, S, 'TEST_mock141'); return r.status_code, len(T.GETS) - g0, t
    o = run(go()); EV['non_pyq'] = o
    n = len({json.dumps(r, sort_keys=True) for q in SET['questions'] for k in ('q_refs', 's_refs') for r in q[k]})
    assert o[0] == 200 and o[1] == n, (o, n)
