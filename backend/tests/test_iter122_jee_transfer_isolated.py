"""TEST-ONLY iteration 122 (based on 121 + bounded PDF-verifier slot, explicit wrong-owner 409, malformed legacy id 409): owner-only verified JEE transfer importer (tejas/jee_transfer.py) on an ISOLATED DB.
- DB: iso_harness rebinds every tejas Motor handle to `tejas_isolated_iter105_test` (dropped after). MONGO_URL/DB_NAME untouched.
- Auth: X-Test-User header -> synthetic users (TEST-ONLY MOCKED `auth.current`; real staff/owner deps still run).
- Storage: J.storage_request is an in-memory MOCK (GET only). Real PDFs/storage are never contacted.
  Because synthetic bytes cannot match real SHA-256s, J.hashlib is shimmed (TEST-ONLY) so that ONLY the mock-generated
  PDF bytes map to the expected bundle hash; every other hash (record digests, tampered bytes) is computed for real.
  The real verify_pdf() size / %PDF- header / hash comparison code therefore runs unchanged.
Run: cd /app/backend/tests && python -m pytest test_iter121_jee_transfer_isolated.py -p no:asyncio -n0 -v
"""
import asyncio, copy, gzip, hashlib, threading, time, types
import httpx, pytest
import iso_harness as H
import tejas_storage
from tejas import jee_transfer as J
from bson import json_util

LOOP = asyncio.new_event_loop()
asyncio.set_event_loop(LOOP)
run = LOOP.run_until_complete
TDB = H.TDB
REAL_HASHLIB = hashlib
OWNER = {'id': 'TEST_U121_owner', 'role': 'owner', 'name': 'TEST Owner 121', 'email': 'abhishekpushp07@gmail.com', 'access_type': 'password'}
H.USERS.update({
    'owner': OWNER,
    'owner2': {**OWNER, 'id': 'TEST_U121_owner2', 'email': 'test-owner2-121@example.invalid'},
    'reviewer': {'id': 'TEST_U121_rev', 'role': 'reviewer', 'name': 'TEST Rev', 'email': 'rev121@example.invalid', 'access_type': 'password'},
    'student': {'id': 'TEST_U121_student', 'role': 'student', 'name': 'TEST Student', 'phone': '9900000121', 'access_type': 'phone', 'exam': 'JEE Main'},
    'unverified_owner': {**OWNER, 'id': 'TEST_U121_uv', 'access_type': 'unverified_phone'},
})

# ---------------- TEST-ONLY storage + hash shim ----------------
CALLS = []
MODE = {'fail': None, 'delay': 0, 'gate': None, 'gate_fail': None}
HASHMAP = {}
ACTIVE = {'now': 0, 'max': 0}
ALOCK = threading.Lock()


def fake_storage(method, path, data=None, content_type=None):
    CALLS.append((method, path))
    if method != 'GET':
        raise RuntimeError('TEST GUARD: storage write blocked')
    with ALOCK:
        ACTIVE['now'] += 1
        ACTIVE['max'] = max(ACTIVE['max'], ACTIVE['now'])
    try:
        return _fake_storage(path)
    finally:
        with ALOCK:
            ACTIVE['now'] -= 1


def _fake_storage(path):
    if MODE['delay']:
        time.sleep(MODE['delay'])
    gate = MODE['gate']
    if gate is not None:
        assert gate.wait(10), 'TEST gate never released'
    f = BY_PATH[path]
    fail = MODE['gate_fail'] if gate is not None and MODE['gate_fail'] else MODE['fail']
    if fail == 'storage_error':
        raise tejas_storage.StorageError('mock outage')
    size = f['size'] - 1 if fail == 'size' else f['size']
    head = b'%HTML' if fail == 'header' else b'%PDF-'
    raw = head + path.encode()[:size - 5]
    raw = raw + b'\0' * (size - len(raw))
    if fail == 'hash':
        raw = raw[:-1] + b'\1'
    else:
        HASHMAP[REAL_HASHLIB.sha256(raw).hexdigest()] = f['sha256']
    return types.SimpleNamespace(content=raw)


class _Shim:
    @staticmethod
    def sha256(b=b''):
        h = REAL_HASHLIB.sha256(b).hexdigest()
        return types.SimpleNamespace(hexdigest=lambda: HASHMAP.get(h, h))


def blocked_real(*a, **k):
    raise RuntimeError('TEST GUARD: real storage request blocked')


@pytest.fixture(scope='module', autouse=True)
def isolated():
    saved = (J.storage_request, J.hashlib, tejas_storage.request)
    J.storage_request, J.hashlib, tejas_storage.request = fake_storage, _Shim, blocked_real
    run(H.tdbmod.client.drop_database(H.TEST_DB))
    run(H.tdbmod.indexes())
    yield
    run(H.tdbmod.client.drop_database(H.TEST_DB))
    J.storage_request, J.hashlib, tejas_storage.request = saved


DATA = J.load_bundle()
BY_PATH = {f['path']: f for f in DATA['tejas_files']}
TARGET = J.target_records(DATA, OWNER)
IDS = {n: [d['id'] for d in TARGET[n]] for n in J.COLLECTIONS}
OTHER = ('tejas_users', 'tejas_attempts', 'tejas_sessions')


def req(method, path, who='owner', **kw):
    async def go():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=H.app), base_url='https://api.test.example', timeout=120) as c:
            h = dict(kw.pop('headers', {}) or {})
            if who:
                h['x-test-user'] = who
            return await c.request(method, path, headers=h, **kw)
    return run(go())


def body(r):
    j = r.json()
    return j['data'] if isinstance(j, dict) and 'data' in j else j


def step(who='owner', **kw):
    return req('POST', '/api/studio/jee-transfer/step', who, **kw)


def receipt():
    return run(TDB.tejas_content_transfers.find_one({'_id': J.TRANSFER_ID}))


def target_counts():
    return {n: run(TDB[n].count_documents({'id': {'$in': IDS[n]}})) for n in J.COLLECTIONS}


def snapshot():
    async def go():
        out = {}
        for n in await TDB.list_collection_names():
            out[n] = sorted(json_util.dumps(d, sort_keys=True) for d in await TDB[n].find({}).to_list(None))
        return out
    return run(go())


def non_target_snapshot():
    s = snapshot()
    s.pop('tejas_content_transfers', None)
    for n in J.COLLECTIONS:
        ids = set(IDS[n])
        s[n] = [d for d in s.get(n, []) if json_util.loads(d)['id'] not in ids]
    return s


# ---------------- 1. bundle integrity ----------------
def test_isolation_guards():
    assert H.TEST_DB != H.REAL_DB and not H.leftover_real_handles()
    assert J.db.name == H.TEST_DB


def test_bundle_integrity_and_scope():
    raw = gzip.decompress(J.BUNDLE_PATH.read_bytes())
    assert REAL_HASHLIB.sha256(raw).hexdigest() == J.BUNDLE_SHA == '3551e344ef2d33f765bfd0015836ebdaec83c918d32830ca9521f62d688191b2'
    b = json_util.loads(raw)
    assert b['independent_audit']['status'] == 'PASS'
    assert {n: len(DATA[n]) for n in J.COLLECTIONS} == {'tejas_files': 81, 'tejas_chapter_books': 3, 'tejas_sets': 78}
    qs = [q for s in DATA['tejas_sets'] for q in s['questions']]
    assert len(qs) == 3900 and len({q['id'] for q in qs}) == 3900
    assert all(q['solution_kind'] == 'supplied_worked' and q['solution'] and q['s_refs'] and q['q_refs'] for q in qs)
    by_subj = {}
    for s in DATA['tejas_sets']:
        by_subj[s['chapter_subject']] = by_subj.get(s['chapter_subject'], 0) + 1
        assert s['status'] == 'published' and s['rules']['minutes'] == J.TIMINGS[s['chapter_subject']]
        assert (s['rules']['correct'], s['rules']['wrong'], s['rules']['skipped']) == (4, -1, 0)
        assert set(s['file_ids']) <= set(f['id'] for f in DATA['tejas_files'])
        assert s['chapter_book_id'] in IDS['tejas_chapter_books']
    assert by_subj == {'Physics': 29, 'Mathematics': 26, 'Chemistry': 23}
    assert len(BY_PATH) == 81 and all(f['size'] > 0 and len(f['sha256']) == 64 for f in DATA['tejas_files'])
    for n in J.COLLECTIONS:
        assert {d['id']: J.digest(d) for d in DATA[n]} == b['record_sha256'][n]


def test_tampered_bundle_blocked(tmp_path, monkeypatch):
    raw = bytearray(gzip.decompress(J.BUNDLE_PATH.read_bytes()))
    raw[raw.index(b'"minutes"') + 12] ^= 1
    p = tmp_path / 'b.json.gz'
    p.write_bytes(gzip.compress(bytes(raw)))
    monkeypatch.setattr(J, 'BUNDLE_PATH', p)
    J.load_bundle.cache_clear()
    try:
        with pytest.raises(J.HTTPException) as e:
            J.load_bundle()
        assert e.value.status_code == 503
    finally:
        monkeypatch.undo()
        J.load_bundle.cache_clear()
        J.load_bundle()


def test_bundle_not_publicly_routed():
    paths = [getattr(r, 'path', '') for r in H.app.routes]
    assert not any('resources' in p or p.endswith('.gz') for p in paths)
    for p in ('/resources/jee_chapters.json.gz', '/api/resources/jee_chapters.json.gz', '/jee_chapters.json.gz'):
        r = req('GET', p, None)
        assert r.status_code in (404, 405) and b'record_sha256' not in r.content and not r.content.startswith(b'\x1f\x8b')


# ---------------- 2. auth / payload / read-only ----------------
@pytest.mark.parametrize('who,code', [(None, 401), ('student', 403), ('reviewer', 403), ('unverified_owner', 403)])
def test_role_matrix_denied(who, code):
    assert req('GET', '/api/studio/jee-transfer', who).status_code == code
    assert step(who).status_code == code
    assert receipt() is None and sum(target_counts().values()) == 0 and not CALLS


@pytest.mark.parametrize('payload', [{'collections': {'tejas_sets': []}}, {'owner_id': 'x'}, [], 'x', 1])
def test_strict_empty_payload_rejects_data(payload):
    r = step(json=payload)
    assert r.status_code == 422, (r.status_code, r.text[:200])
    assert receipt() is None and not CALLS


def test_oversized_body_rejected():
    r = step(content=b'{"a":"' + b'x' * 9000 + b'"}', headers={'content-type': 'application/json'})
    assert r.status_code in (413, 422) and receipt() is None


def seed_fixtures():
    async def go():
        await TDB.tejas_files.insert_one({'id': 'TEST_F121', 'path': 'tejas/x', 'size': 1, 'sha256': 'a' * 64, 'note': None})
        await TDB.tejas_chapter_books.insert_one({'id': 'TEST_B121', 'title': 'TEST Book', 'created_by': 'someone', 'meta': {'n': None, 'l': [1, 2]}})
        await TDB.tejas_sets.insert_many([{'id': f'TEST_S121_{i}', 'exam': 'BITSAT', 'status': 'draft', 'title': f'TEST {i}', 'questions': [{'id': 'q', 'answer': 'A'}]} for i in range(3)])
        await TDB.tejas_users.insert_one({'id': 'TEST_U121_real', 'role': 'student', 'phone': '9900000129'})
        await TDB.tejas_attempts.insert_one({'id': 'TEST_A121', 'user_id': 'TEST_U121_real', 'set_id': 'TEST_S121_0', 'score': 7})
        await TDB.tejas_sessions.insert_one({'id': 'TEST_SS121', 'user_id': 'TEST_U121_real'})
        # pre-existing IDENTICAL target records (should be skipped, not duplicated)
        await TDB.tejas_files.insert_one(copy.deepcopy(TARGET['tejas_files'][5]))
        await TDB.tejas_sets.insert_one(copy.deepcopy(TARGET['tejas_sets'][10]))
    run(go())


def test_get_status_no_writes():
    seed_fixtures()
    before = snapshot()
    for _ in range(3):
        r = req('GET', '/api/studio/jee-transfer')
        assert r.status_code == 200
        d = body(r)
        assert d['phase'] == 'not_started' and d['verified_files'] == 0 and d['chapter_tests'] == 1
        assert d['timings'] == {'Physics': 90, 'Mathematics': 120, 'Chemistry': 70}
        assert d['marking'] == {'correct': 4, 'wrong': -1, 'skipped': 0}
    assert snapshot() == before and not CALLS


# ---------------- 3. verification phase ----------------
BASE = {}


@pytest.mark.parametrize('fail,code', [('size', 409), ('header', 409), ('hash', 409), ('storage_error', 503)])
def test_storage_failures_block_without_inserts(fail, code):
    if not BASE:
        BASE['non_target'] = non_target_snapshot()
        BASE['targets'] = target_counts()
    MODE['fail'] = fail
    try:
        r = step()
    finally:
        MODE['fail'] = None
    assert r.status_code == code, r.text[:300]
    rc = receipt()
    assert rc['verified_files'] == 0 and rc['phase'] == 'verifying' and rc['lease_until'] == 0
    assert target_counts() == BASE['targets']
    assert not J.SOURCE_SLOT.locked(), 'slot must be released after a failed PDF check'


# ---- 122: bounded single verifier on timeout (real threads, controlled Event, shortened wait_for) ----
class _ShortWait:
    """Proxy for the real asyncio module: identical except wait_for uses a 0.2s timeout (future-shaped API kept)."""
    def __getattr__(self, name):
        return getattr(asyncio, name)

    @staticmethod
    def wait_for(aw, timeout):
        return asyncio.wait_for(aw, 0.2)


def wait_slot_free(limit=5):
    end = time.time() + limit
    while J.SOURCE_SLOT.locked() and time.time() < end:
        run(asyncio.sleep(0.02))
    return not J.SOURCE_SLOT.locked()


def verifier_threads_unused():
    return None


@pytest.mark.parametrize('gate_fail', [None, 'storage_error'])
def test_timeout_keeps_single_bounded_verifier(monkeypatch, gate_fail):
    monkeypatch.setattr(J, 'asyncio', _ShortWait())
    gate = threading.Event()
    MODE['gate'], MODE['gate_fail'] = gate, gate_fail
    ACTIVE['max'] = 0
    CALLS.clear()
    try:
        r = step()
        assert r.status_code == 503 and 'timed out' in r.text, r.text[:300]
        rc = receipt()
        assert rc['verified_files'] == 0 and rc['lease_until'] == 0 and rc['lease_token'] == ''
        assert J.SOURCE_SLOT.locked() and ACTIVE['now'] == 1, 'thread must still own the slot after timeout'
        for _ in range(4):  # repeated resumes: 429, no new storage GET, no stacked thread, lease released
            r = step()
            assert r.status_code == 429, r.text[:300]
            assert r.headers.get('retry-after') == '30' and 'still finishing' in r.text
            assert len(CALLS) == 1 and ACTIVE['now'] == 1 and ACTIVE['max'] == 1
            assert receipt()['lease_until'] == 0 and receipt()['verified_files'] == 0
        assert target_counts() == BASE['targets']
    finally:
        gate.set()
    assert wait_slot_free(), 'slot must be released once the background verifier finishes'
    MODE['gate'], MODE['gate_fail'] = None, None
    assert ACTIVE['now'] == 0 and ACTIVE['max'] == 1
    assert receipt()['verified_files'] == 0  # orphaned result is never counted


def test_next_step_works_after_background_completion():
    CALLS.clear()
    r = step()
    assert r.status_code == 200 and body(r)['verified_files'] == 1, r.text[:300]
    assert CALLS == [('GET', DATA['tejas_files'][0]['path'])] and not J.SOURCE_SLOT.locked()
    run(TDB.tejas_content_transfers.update_one({'_id': J.TRANSFER_ID}, {'$set': {'verified_files': 0}}))


def test_verify_all_81_before_any_insert():
    CALLS.clear()
    for i in range(40):
        r = step()
        assert r.status_code == 200, r.text[:300]
        assert body(r)['verified_files'] == i + 1 and body(r)['phase'] == 'verifying'
        assert target_counts() == BASE['targets']
    # interruption: just stop; status reflects resume point
    d = body(req('GET', '/api/studio/jee-transfer'))
    assert d['phase'] == 'verifying' and d['verified_files'] == 40
    assert CALLS == [('GET', f['path']) for f in DATA['tejas_files'][:40]]


def test_concurrent_steps_single_lease():
    MODE['delay'] = 0.5

    async def both():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=H.app), base_url='https://x.test', timeout=60) as c:
            h = {'x-test-user': 'owner'}
            return await asyncio.gather(c.post('/api/studio/jee-transfer/step', headers=h), c.post('/api/studio/jee-transfer/step', headers=h))
    try:
        a, b = run(both())
    finally:
        MODE['delay'] = 0
    assert sorted([a.status_code, b.status_code]) == [200, 409], (a.status_code, b.status_code)
    assert receipt()['verified_files'] == 41


def test_stale_lease_blocks_until_expiry():
    run(TDB.tejas_content_transfers.update_one({'_id': J.TRANSFER_ID}, {'$set': {'lease_token': 'crashed', 'lease_until': H.CLOCK[0] + 300}}))
    assert step().status_code == 409
    H.CLOCK[0] += 301
    r = step()
    assert r.status_code == 200 and body(r)['verified_files'] == 42


def test_other_owner_cannot_drive_receipt():
    before = receipt()
    CALLS.clear()
    r = step('owner2')
    assert r.status_code == 409 and receipt()['verified_files'] == 42
    msg = r.json()['error']['message']
    assert 'different owner' in msg and 'original owner' in msg and 'Another owner import step is running' not in msg, msg
    after = receipt()
    assert after == before and after['owner_id'] == OWNER['id'] and not CALLS  # no takeover / lease grab
    assert req('GET', '/api/studio/jee-transfer', 'owner2').status_code == 200  # status still readable
    r = step()
    assert r.status_code == 200 and body(r)['verified_files'] == 43  # original owner continues
    run(TDB.tejas_content_transfers.update_one({'_id': J.TRANSFER_ID}, {'$set': {'verified_files': 42}}))


def test_baseline_change_blocks_phase_switch():
    while receipt()['verified_files'] < 80:
        assert step().status_code == 200
    run(TDB.tejas_sets.update_one({'id': 'TEST_S121_1'}, {'$set': {'title': 'TEST edited by someone'}}))
    r = step()
    assert r.status_code == 409 and receipt()['verified_files'] == 80 and receipt()['phase'] == 'verifying'
    run(TDB.tejas_sets.update_one({'id': 'TEST_S121_1'}, {'$set': {'title': 'TEST 1'}}))
    r = step()
    assert r.status_code == 200 and body(r)['phase'] == 'importing' and body(r)['verified_files'] == 81
    assert target_counts() == BASE['targets']
    assert [c[1] for c in CALLS if c[0] == 'GET'][-1] == DATA['tejas_files'][80]['path']


# ---------------- 4. import phase ----------------
ORDERED = [(n, d) for n in J.COLLECTIONS for d in TARGET[n]]


def test_first_batch_and_crash_retry_dedupe():
    r = step()
    assert r.status_code == 200 and body(r)['processed_records'] == 8
    # simulate crash after inserting next batch but before receipt update
    for n, d in ORDERED[8:16]:
        if not run(TDB[n].find_one({'id': d['id']})):
            run(TDB[n].insert_one(J.ContentRecord.from_mongo({'_id': J.TRANSFER_ID + ':' + d['id'], **copy.deepcopy(d)}).to_mongo()))
    r = step()
    assert r.status_code == 200 and body(r)['processed_records'] == 16
    for n in J.COLLECTIONS:
        ids = [x['id'] for x in run(TDB[n].find({}, {'id': 1}).to_list(None))]
        assert len(ids) == len(set(ids))


def test_race_different_record_conflict_409_no_overwrite():
    while receipt()['cursor'] < 88:
        assert step().status_code == 200
    n, d = ORDERED[100]
    alien = {'id': d['id'], 'title': 'TEST conflicting', 'exam': 'BITSAT', 'status': 'draft'}
    run(TDB[n].insert_one(dict(alien)))
    cur = receipt()['cursor']
    while receipt()['cursor'] < 96:
        assert step().status_code == 200
    r = step()  # batch 96..103 includes index 100
    assert r.status_code == 409 and 'without overwriting' in r.text
    got = run(TDB[n].find_one({'id': d['id']}, {'_id': 0}))
    assert got == alien and receipt()['cursor'] == 96 and receipt()['lease_until'] == 0
    run(TDB[n].delete_one({'id': d['id'], 'title': 'TEST conflicting'}))  # owner resolves conflict
    assert cur >= 88


def test_complete_import():
    steps = 0
    while receipt()['phase'] != 'complete':
        r = step()
        assert r.status_code == 200, r.text[:300]
        steps += 1
        assert steps < 30
    d = body(r)
    assert d['phase'] == 'complete' and d['processed_records'] == 162 and d['chapter_tests'] == 78 and d['existing_content_unchanged'] is True


def test_imported_records_exact():
    assert target_counts() == {'tejas_files': 81, 'tejas_chapter_books': 3, 'tejas_sets': 78}
    for n in J.COLLECTIONS:
        rows = {x['id']: x for x in run(TDB[n].find({'id': {'$in': IDS[n]}}).to_list(None))}
        for orig, tgt in zip(DATA[n], TARGET[n]):
            row = rows[orig['id']]
            c = J.content(row)
            assert J.digest(c) == J.digest(tgt)
            diff = {k for k in set(c) | set(orig) if c.get(k, 'MISSING') != orig.get(k, 'MISSING')}
            allowed = {'tejas_chapter_books': {'created_by'}, 'tejas_sets': {'rights_attested_by'}}.get(n, set())
            assert diff <= allowed, (n, orig['id'], diff)
            for k, v in orig.items():
                if v is None:
                    assert k in row and row[k] is None, (n, k)
    for b in run(TDB.tejas_chapter_books.find({'id': {'$in': IDS['tejas_chapter_books']}}).to_list(None)):
        assert b['created_by'] == OWNER['id']
    sets = run(TDB.tejas_sets.find({'id': {'$in': IDS['tejas_sets']}}).to_list(None))
    assert all(s['rights_attested_by'] == OWNER['id'] for s in sets)
    assert sum(len(s['questions']) for s in sets) == 3900
    qh = sorted(J.digest(q) for s in sets for q in s['questions'])
    assert qh == sorted(J.digest(q) for s in DATA['tejas_sets'] for q in s['questions'])


def test_unrelated_data_untouched():
    assert non_target_snapshot() == BASE['non_target']
    for c in OTHER:
        assert run(TDB[c].count_documents({'id': {'$regex': '^TEST_(U|A|SS)121'}})) == 1


def test_repeat_after_complete_is_noop():
    before = snapshot()
    before.pop('tejas_content_transfers')
    CALLS.clear()
    r = step()
    assert r.status_code == 200 and body(r)['phase'] == 'complete'
    after = snapshot()
    after.pop('tejas_content_transfers')
    assert after == before and not CALLS


def test_catalogue_counts_after_import():
    for subj, n, mins in (('Physics', 29, 90), ('Mathematics', 26, 120), ('Chemistry', 23, 70)):
        r = req('GET', '/api/exam-navigation/jee-main/catalogue', 'student', params={'kind': 'chapters', 'subject': subj})
        assert r.status_code == 200, r.text[:300]
        d = body(r)
        items = d['items']
        total = d.get('total', len(items))
        assert total == n, (subj, total)
        assert all(i['rules']['minutes'] == mins for i in items)


# ---------------- 5. pre-existing different record blocks before receipt ----------------
def test_preexisting_conflict_blocks_fresh_start():
    async def reset():
        await TDB.tejas_content_transfers.delete_many({})
        for n in J.COLLECTIONS:
            await TDB[n].delete_many({'id': {'$in': IDS[n]}})
        b = copy.deepcopy(TARGET['tejas_chapter_books'][0]); b['title'] = 'TEST different'
        await TDB.tejas_chapter_books.insert_one(b)
    run(reset())
    CALLS.clear()
    r = step()
    assert r.status_code == 409 and receipt() is None and not CALLS
    assert run(TDB.tejas_chapter_books.find_one({'id': IDS['tejas_chapter_books'][0]}))['title'] == 'TEST different'


# ---------------- 6. (122) malformed legacy record (missing / bad id) -> safe 409 before any write ----------------
@pytest.mark.parametrize('coll,bad', [
    ('tejas_sets', {'title': 'TEST legacy no id', 'exam': 'JEE Main'}),
    ('tejas_files', {'path': 'legacy/x.pdf', 'id': None}),
    ('tejas_chapter_books', {'title': 'TEST legacy int id', 'id': 12345}),
])
def test_malformed_legacy_record_blocks_safely(coll, bad):
    async def reset():
        await TDB.tejas_content_transfers.delete_many({})
        for n in J.COLLECTIONS:
            await TDB[n].delete_many({'id': {'$in': IDS[n]}})
        await TDB[coll].insert_one(dict(bad, _legacy122=True))
    run(reset())
    CALLS.clear()
    before = snapshot()
    assert req('GET', '/api/studio/jee-transfer').status_code == 200  # status unaffected
    r = step()
    assert r.status_code == 409, (r.status_code, r.text[:300])
    assert 'invalid identity' in r.json()['error']['message']
    assert receipt() is None and not CALLS and sum(target_counts().values()) == 0
    assert snapshot() == before
    run(TDB[coll].delete_many({'_legacy122': True}))


def test_fresh_start_works_after_legacy_removed():
    run(TDB.tejas_chapter_books.delete_many({'title': 'TEST different'}))
    CALLS.clear()
    r = step()
    assert r.status_code == 200 and body(r)['verified_files'] == 1 and not J.SOURCE_SLOT.locked(), r.text[:300]
