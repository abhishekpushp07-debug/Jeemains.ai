"""TEST-ONLY iteration 134: isolated fault reproduction + small canonical baseline (INITIAL AUDIT, no app code changed).
- DB: iso_harness_iter134 rebinds ALL tejas/server Motor handles to `tejas_isolated_iter134` (dropped before/after).
  MONGO_URL / DB_NAME untouched. No lifespan (no seed/worker/AI). No real auth login; synthetic ephemeral actors only.
- Clock: app `now()` = real + OFFSET; Mongo $$NOW is real (skew injection).
- Grade dispatch from submit is replaced by a recorder (no job/AI run).
- Tests that assert the DESIRED invariant but currently FAIL are marked xfail(strict=True) = reproduced FAULT.
  After the fix they XPASS -> strict failure -> remove the marker.
Run: cd /app/backend/tests && python -m pytest test_iter134_canonical_faults_isolated.py -n0 -p no:cacheprovider -v -s
"""
import asyncio, copy, hashlib, json, time, types, uuid
import httpx, pytest
import iso_harness_iter134 as H
from pymongo.errors import DuplicateKeyError
from tejas import attempts as AT, answers as AN, packs as PK, derivatives as DV, phone as PH, auth as AU
import tejas_core, tejas_storage

LOOP = asyncio.new_event_loop()
asyncio.set_event_loop(LOOP)
run = LOOP.run_until_complete
TDB = H.TDB
EVIDENCE = {}
STUDENT = {'id': 'TEST_U134_student', 'role': 'student', 'name': 'TEST Student 134', 'phone': '+919900000134', 'access_type': 'unverified_phone', 'exam': 'JEE Main'}
OTHER = {'id': 'TEST_U134_other', 'role': 'student', 'name': 'TEST Other 134', 'phone': '+919900000135', 'access_type': 'unverified_phone', 'exam': 'JEE Main'}
H.USERS.update({'s': STUDENT, 'o': OTHER})
GRADE_CALLS = []


async def _no_grade(a, bg=None):  # TEST-ONLY: record, never enqueue/run grade jobs
    GRADE_CALLS.append(a.get('id'))
    return None


@pytest.fixture(scope='module', autouse=True)
def isolated():
    assert H.TEST_DB != H.REAL_DB and H.TEST_DB == 'tejas_isolated_iter134'
    assert H.PATCHED and not H.leftover_real_handles(), H.leftover_real_handles()
    run(H.tdbmod.client.drop_database(H.TEST_DB))
    orig = AT.ensure_grade
    AT.ensure_grade = _no_grade
    yield
    AT.ensure_grade = orig
    H.OFFSET[0] = 0
    run(H.tdbmod.client.drop_database(H.TEST_DB))
    assert H.TEST_DB not in run(H.tdbmod.client.list_database_names())
    with open('/app/test_reports/iter134_evidence.json', 'w') as f:
        json.dump(EVIDENCE, f, indent=2, default=str)


@pytest.fixture(autouse=True)
def reset_clock():
    H.OFFSET[0] = 0
    yield
    H.OFFSET[0] = 0


def questions(n=4, bonus=0):
    qs = []
    for i in range(n + bonus):
        qs.append({'id': str(uuid.uuid4()), 'number': i + 1, 'type': 'mcq', 'subject': 'Physics', 'section': 'A',
                   'options': {'A': 'a', 'B': 'b', 'C': 'c', 'D': 'd'}, 'answer': 'A',
                   'text': f'TEST_134 synthetic question {i} ' + 'x' * 600, 'solution': 'TEST solution ' + 'y' * 400,
                   **({'bonus': True} if i >= n else {})})
    return qs


async def make_attempt(user=STUDENT, deadline_in=600.0, n=4, bonus=0, rules=None):
    a = {'id': 'TEST_A134_' + uuid.uuid4().hex, 'user_id': user['id'], 'set_id': 'TEST_S134', 'title': 'TEST 134',
         'exam': 'JEE Main', 'mode': 'practice', 'version': 1, 'rules': rules or {'minutes': 10}, 'status': 'active',
         'answers': {}, 'first_answers': {}, 'server_seq': 0, 'command_count': 0, 'visited': [], 'test_kind': 'mock',
         'profile': {}, 'started_at': time.time(), 'deadline': (time.time() + deadline_in) if deadline_in is not None else 0,
         'questions': questions(n, bonus), 'parent_attempt': None, 'start_key': 'TEST_K134_' + uuid.uuid4().hex}
    qs = copy.deepcopy(a['questions'])
    await PK.insert_attempt(a)
    return a['id'], qs


async def db_attempt(id):
    return await TDB.tejas_attempts.find_one({'id': id}, {'_id': 0})


def client():
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=H.app, raise_app_exceptions=False), base_url='https://api.test.example', timeout=60)


def J(r):
    j = r.json()
    return j.get('data') if isinstance(j, dict) and 'data' in j and 'meta' in j else j


def body(rev=1, rid=None, value='A'):
    return {'value': value, 'revision': rev, 'request_id': rid or ('TEST_R134_' + uuid.uuid4().hex)}


# ---------- 0. isolation proof ----------
def test_isolation_all_handles_rebound():
    assert not H.leftover_real_handles()
    assert 'tejas.db.attempts' in H.PATCHED and 'tejas.packs.db' in H.PATCHED and 'tejas.phone.db' in H.PATCHED
    assert AT.attempts.database.name == AN.attempts.database.name == PK.db.name == PH.db.name == H.TEST_DB
    EVIDENCE['isolation'] = {'test_db': H.TEST_DB, 'patched_handles': len(H.PATCHED), 'clock_patched': H.CLOCK_PATCHED}


# ---------- 1. owned() scopes user BEFORE hydrate (rule-out) ----------
def test_owned_scopes_user_before_hydrate():
    calls = []
    orig = AT.hydrate

    async def spy(a):
        calls.append(a.get('user_id'))
        return await orig(a)

    async def go():
        id, qs = await make_attempt()
        AT.hydrate = spy
        try:
            async with client() as c:
                foreign = [await c.get(f'/api/attempts/{id}', headers={'x-test-user': 'o'}),
                           await c.get(f'/api/attempts/{id}/results', headers={'x-test-user': 'o'}),
                           await c.get(f'/api/attempts/{id}/questions/{qs[0]["id"]}/asset/question/0', headers={'x-test-user': 'o'}),
                           await c.put(f'/api/attempts/{id}/answers/{qs[0]["id"]}', json=body(), headers={'x-test-user': 'o'}),
                           await c.post(f'/api/attempts/{id}/visit', json={'question_id': qs[0]['id']}, headers={'x-test-user': 'o'}),
                           await c.post(f'/api/attempts/{id}/submit', headers={'x-test-user': 'o'})]
                n_foreign = len(calls)
                own = await c.get(f'/api/attempts/{id}', headers={'x-test-user': 's'})
            return id, [r.status_code for r in foreign], n_foreign, own.status_code, await db_attempt(id)
        finally:
            AT.hydrate = orig
    id, codes, n_foreign, own, doc = run(go())
    EVIDENCE['owned_before_hydrate'] = {'foreign_codes': codes, 'hydrate_calls_for_foreign': n_foreign, 'own_read': own}
    assert codes == [404] * 6 and n_foreign == 0 and own == 200
    assert doc['status'] == 'active' and doc['answers'] == {} and doc['server_seq'] == 0


# ---------- 2. clock skew: app AHEAD, DB deadline still future ----------
SKEW_OPS = ['answer', 'visit', 'bonus', 'read_expire', 'history']


async def skew_case(op, offset, deadline_in):
    rules = {'minutes': 10, 'bonus_rule': True} if op == 'bonus' else None
    id, qs = await make_attempt(deadline_in=deadline_in, n=2, bonus=1 if op == 'bonus' else 0, rules=rules)
    if op == 'bonus':  # answer all main questions at true time first
        async with client() as c:
            for q in qs[:2]:
                assert (await c.put(f'/api/attempts/{id}/answers/{q["id"]}', json=body(), headers={'x-test-user': 's'})).status_code == 200
    H.OFFSET[0] = offset
    h = {'x-test-user': 's'}
    async with client() as c:
        if op == 'answer':
            r = await c.put(f'/api/attempts/{id}/answers/{qs[0]["id"]}', json=body(), headers=h)
        elif op == 'visit':
            r = await c.post(f'/api/attempts/{id}/visit', json={'question_id': qs[0]['id']}, headers=h)
        elif op == 'bonus':
            r = await c.post(f'/api/attempts/{id}/bonus', headers=h)
        elif op == 'read_expire':
            r = await c.get(f'/api/attempts/{id}', headers=h)
        else:
            r = await c.get('/api/attempts', headers=h)
    H.OFFSET[0] = 0
    d = await db_attempt(id)
    real_left = d['deadline'] - time.time()
    return {'op': op, 'http': r.status_code, 'detail': (r.json().get('error') if r.headers.get('content-type', '').startswith('application/json') else r.text)
            if r.status_code >= 400 else None, 'db_status': d['status'], 'db_reason': d.get('reason'),
            'real_seconds_left_at_check': round(real_left, 1), 'submitted_before_deadline_by_s':
            round(d['deadline'] - d['submitted_at'], 1) if d.get('submitted_at') else None}


@pytest.mark.parametrize('op', SKEW_OPS)
@pytest.mark.xfail(strict=True, reason='FAULT: app-clock precheck now()>=deadline calls finalize() -> premature seal while DB deadline is future')
def test_app_clock_ahead_does_not_seal_valid_attempt(op):
    res = run(skew_case(op, offset=+3600, deadline_in=600))
    EVIDENCE.setdefault('clock_ahead_3600s_deadline_future_600s', []).append(res)
    print('AHEAD', res)
    assert res['db_status'] == 'active', res
    assert res['http'] == 200, res


@pytest.mark.parametrize('op', ['answer', 'visit', 'read_expire'])
def test_app_clock_behind_valid_future_deadline_accepts(op):
    res = run(skew_case(op, offset=-3600, deadline_in=600))
    EVIDENCE.setdefault('clock_behind_3600s_deadline_future', []).append(res)
    assert res['http'] == 200 and res['db_status'] == 'active', res


def test_app_clock_behind_db_deadline_passed_rejects_late_write_no_score():
    async def go():
        id, qs = await make_attempt(deadline_in=-2)
        H.OFFSET[0] = -3600
        async with client() as c:
            r = await c.put(f'/api/attempts/{id}/answers/{qs[0]["id"]}', json=body(), headers={'x-test-user': 's'})
            v = await c.post(f'/api/attempts/{id}/visit', json={'question_id': qs[0]['id']}, headers={'x-test-user': 's'})
            g = await c.get(f'/api/attempts/{id}', headers={'x-test-user': 's'})
        H.OFFSET[0] = 0
        return r.status_code, v.status_code, J(g).get('status'), await db_attempt(id)
    r, v, read_status, d = run(go())
    EVIDENCE['clock_behind_deadline_passed'] = {'answer': r, 'visit': v, 'read_status_reported': read_status, 'db_status': d['status'], 'answers': d['answers']}
    assert r == 409 and v == 409 and d['answers'] == {}  # DB $$NOW guard holds
    # NOTE (recorded, not asserted): read reports 'active' past deadline because expire() uses app clock -> no seal until DB-clock path


def test_finalize_uses_db_clock_only():
    async def go():
        id1, _ = await make_attempt(deadline_in=600)
        id2, _ = await make_attempt(deadline_in=-5)
        H.OFFSET[0] = +3600
        a1 = await AT.finalize(id1, 'submitted')
        a2 = await AT.finalize(id2, 'submitted')
        H.OFFSET[0] = 0
        return a1, a2
    a1, a2 = run(go())
    EVIDENCE['finalize_direct'] = {'future': [a1['reason'], round(a1['deadline'] - a1['submitted_at'], 1)], 'expired': [a2['reason'], a2['submitted_at'] == a2['deadline']]}
    assert a1['reason'] == 'submitted' and a1['submitted_at'] < a1['deadline']
    assert a2['reason'] == 'time_limit' and a2['submitted_at'] == a2['deadline']


@pytest.mark.xfail(strict=True, reason='FAULT: finalize(reason="time_limit") on a NOT-expired attempt stores reason=time_limit + submitted_at<deadline (caller reason trusted)')
def test_finalize_time_limit_reason_requires_db_expiry():
    async def go():
        id, _ = await make_attempt(deadline_in=600)
        return await AT.finalize(id, 'time_limit')
    a = run(go())
    EVIDENCE['finalize_time_limit_on_future'] = {'status': a['status'], 'reason': a['reason'], 'seconds_early': round(a['deadline'] - a['submitted_at'], 1)}
    assert a['status'] == 'active' or a['reason'] != 'time_limit'


# ---------- 3. PDF source SHA not checked by render_crop ----------
def test_render_crop_png_checks_sha_baseline():
    src = {'kind': 'rendered_png', 'path': 'TEST/134/a.png', 'sha256': hashlib.sha256(b'EXPECTED').hexdigest()}
    og = tejas_storage.get_object
    tejas_storage.get_object = lambda p: b'TAMPERED'
    try:
        with pytest.raises(ValueError):
            DV.render_crop(src, {'page': 1, 'rect': [0, 0, 1, 1]})
    finally:
        tejas_storage.get_object = og


@pytest.mark.xfail(strict=True, reason='FAULT: render_crop(PDF) never compares source bytes with source.sha256; crop_png renders tampered bytes')
def test_render_crop_pdf_rejects_sha_mismatch():
    calls = []
    src = {'kind': 'pdf', 'path': 'TEST/134/' + uuid.uuid4().hex + '.pdf', 'sha256': hashlib.sha256(b'%PDF-EXPECTED').hexdigest()}
    og, oc = tejas_storage.get_object, tejas_core.crop_png
    tejas_storage.get_object = lambda p: b'%PDF-TAMPERED'
    tejas_core.crop_png = lambda data, ref, scale=2: calls.append(hashlib.sha256(data).hexdigest()) or b'\x89PNG-TEST'
    try:
        err = None
        try:
            out = DV.render_crop(src, {'page': 1, 'rect': [0, 0, 1, 1]})
        except ValueError as e:
            err, out = str(e), None
    finally:
        tejas_storage.get_object, tejas_core.crop_png = og, oc
    EVIDENCE['pdf_sha_mismatch'] = {'expected': 'ValueError integrity failure, no crop_png call', 'raised': err, 'crop_png_calls': len(calls),
                                    'rendered_from_sha': calls[:1], 'declared_sha': src['sha256'], 'returned': bool(out)}
    print('PDF', EVIDENCE['pdf_sha_mismatch'])
    assert err and not calls


# ---------- 4. packs.unpack decode + cold-read amplification (bounded 32 x 100q, isolated DB) ----------
def test_unpack_cold_concurrency_baseline():
    counts = {'find_one': 0, 'loads': 0, 'decompress': 0}
    real_json, real_zlib, real_db = PK.json, PK.zlib, PK.db

    class Coll:
        def __init__(self, c): self.c = c
        async def find_one(self, *a, **k):
            counts['find_one'] += 1
            await asyncio.sleep(0.01)  # widen the cold window deterministically
            return await self.c.find_one(*a, **k)
        def __getattr__(self, n): return getattr(self.c, n)

    class DB:
        def __getattr__(self, n): return Coll(real_db[n]) if n == 'tejas_packs' else getattr(real_db, n)

    def loads(raw):
        counts['loads'] += 1
        return real_json.loads(raw)

    def decompress(b):
        counts['decompress'] += 1
        return real_zlib.decompress(b)

    async def go():
        key = await PK.seal(questions(100))
        raw_len = len(PK._cache[key])
        PK._cache.clear(); PK._cache_bytes = 0
        PK.db = DB()
        PK.json = types.SimpleNamespace(loads=loads, dumps=real_json.dumps)
        PK.zlib = types.SimpleNamespace(decompress=decompress, compress=real_zlib.compress)
        try:
            t0 = time.perf_counter()
            cold = await asyncio.gather(*[PK.unpack(key) for _ in range(32)])
            cold_ms = (time.perf_counter() - t0) * 1000
            cold_counts = dict(counts)
            for k in counts: counts[k] = 0
            t1 = time.perf_counter()
            warm = await asyncio.gather(*[PK.unpack(key) for _ in range(32)])
            warm_ms = (time.perf_counter() - t1) * 1000
            warm_counts = dict(counts)
            t2 = time.perf_counter()
            for _ in range(32): real_json.loads(PK._cache[key])
            decode_ms = (time.perf_counter() - t2) * 1000 / 32
        finally:
            PK.db, PK.json, PK.zlib = real_db, real_json, real_zlib
        cold[0][0]['text'] = 'MUTATED'
        again = await PK.unpack(key)
        return dict(raw_bytes=raw_len, cold=cold_counts, cold_ms=round(cold_ms, 1), warm=warm_counts, warm_ms=round(warm_ms, 1),
                    json_decode_ms_per_call=round(decode_ms, 3), mutation_isolated=again[0]['text'] != 'MUTATED',
                    cache_type='raw bytes only (OrderedDict, 32MiB byte bound); every hit re-decodes JSON',
                    db='real isolated Mongo tejas_isolated_iter134 (not fake)')
    res = run(go())
    EVIDENCE['unpack_baseline_32x100q'] = res
    print('UNPACK', res)
    assert res['mutation_isolated']
    assert res['cold']['find_one'] == 32 and res['cold']['decompress'] == 32  # baseline: NO cold coalescing (amplification x32)
    assert res['cold']['loads'] == 32 and res['warm']['loads'] == 32 and res['warm']['find_one'] == 0  # decode per hit


# ---------- 5. first-upsert limiter race: deterministic DuplicateKeyError fake ----------
class DupOnce:
    def __init__(self, real): self.real, self.n = real, 0
    async def find_one_and_update(self, *a, **k):
        self.n += 1
        if self.n == 1:
            raise DuplicateKeyError('E11000 duplicate key error (TEST fake first-upsert race)')
        return await self.real.find_one_and_update(*a, **k)
    def __getattr__(self, n): return getattr(self.real, n)


@pytest.mark.parametrize('route', ['phone', 'login'])
@pytest.mark.xfail(strict=True, reason='FAULT: limiter find_one_and_update(upsert) DuplicateKeyError is not retried/handled -> HTTP 500')
def test_limiter_first_upsert_duplicate_key_handled(route):
    real_db = PH.db if route == 'phone' else AU.db
    coll = 'tejas_phone_limits' if route == 'phone' else 'tejas_login_limits'
    fake = DupOnce(real_db[coll])

    class DB:
        def __getattr__(self, n): return fake if n == coll else getattr(real_db, n)
        def __getitem__(self, n): return fake if n == coll else real_db[n]
    mod = PH if route == 'phone' else AU
    mod.db = DB()

    async def go():
        async with client() as c:
            if route == 'phone':
                return await c.post('/api/auth/phone', json={'phone': '9900000134'})
            return await c.post('/api/auth/login', json={'email': 'test134-nonexistent@example.com', 'password': 'TEST-not-a-real-password'})
    try:
        r = run(go())
    finally:
        mod.db = real_db
    EVIDENCE.setdefault('limiter_dupkey', {})[route] = {'http': r.status_code, 'fake_calls': fake.n}
    print('LIMIT', route, r.status_code)
    assert r.status_code < 500


def test_limiter_real_concurrent_first_upsert_baseline():
    """Real isolated Mongo 7: 32 concurrent first upserts on same _id. Records whether server-side retry hides the race."""
    async def go():
        key = 'TEST_134_' + uuid.uuid4().hex
        async def one():
            try:
                d = await TDB.tejas_phone_limits.find_one_and_update({'_id': key}, {'$inc': {'count': 1}}, upsert=True, return_document=True)
                return d['count']
            except DuplicateKeyError:
                return 'dup'
        out = await asyncio.gather(*[one() for _ in range(32)])
        return out, (await TDB.tejas_phone_limits.find_one({'_id': key}))['count']
    out, final = run(go())
    dups = out.count('dup')
    EVIDENCE['limiter_real_concurrent'] = {'dup_errors': dups, 'final_count': final, 'note': 'real isolated Mongo; dup errors here would surface as 500 in route'}
    assert final == 32 - dups


# ---------- 6. canonical answer invariants (real isolated Mongo, ASGI) ----------
def test_answer_25_replays_single_revision():
    async def go():
        id, qs = await make_attempt()
        b = body()
        async with client() as c:
            rs = await asyncio.gather(*[c.put(f'/api/attempts/{id}/answers/{qs[0]["id"]}', json=b, headers={'x-test-user': 's'}) for _ in range(25)])
            changed = await c.put(f'/api/attempts/{id}/answers/{qs[0]["id"]}', json={**b, 'value': 'B'}, headers={'x-test-user': 's'})
            stale = await c.put(f'/api/attempts/{id}/answers/{qs[0]["id"]}', json=body(rev=1), headers={'x-test-user': 's'})
            foreign = await c.put(f'/api/attempts/{id}/answers/{qs[0]["id"]}', json=body(rev=2), headers={'x-test-user': 'o'})
        return rs, changed, stale, foreign, await db_attempt(id), qs
    rs, changed, stale, foreign, d, qs = run(go())
    codes = [r.status_code for r in rs]
    js = [J(r) for r in rs if r.status_code == 200]
    seqs = {j['accepted']['server_seq'] for j in js}
    applied = sum(not j['duplicate'] for j in js)
    EVIDENCE['replay_25'] = {'codes': sorted(set(codes)), 'applied': applied, 'distinct_seq': list(seqs), 'db_seq': d['server_seq'],
                             'db_command_count': d['command_count'], 'receipts': len(d['command_receipts']), 'changed_body': changed.status_code,
                             'stale_new_rid': stale.status_code, 'foreign': foreign.status_code}
    print('REPLAY', EVIDENCE['replay_25'])
    assert codes == [200] * 25 and applied == 1 and seqs == {1}
    assert d['server_seq'] == 1 and d['command_count'] == 1 and len(d['command_receipts']) == 1 and d['answers'][qs[0]['id']]['revision'] == 1
    assert changed.status_code == 409 and stale.status_code == 409 and foreign.status_code == 404


def test_late_write_after_seal_and_old_replay():
    async def go():
        id, qs = await make_attempt()
        b = body()
        async with client() as c:
            assert (await c.put(f'/api/attempts/{id}/answers/{qs[0]["id"]}', json=b, headers={'x-test-user': 's'})).status_code == 200
            s = await c.post(f'/api/attempts/{id}/submit', headers={'x-test-user': 's'})
            late = await c.put(f'/api/attempts/{id}/answers/{qs[1]["id"]}', json=body(), headers={'x-test-user': 's'})
            replay = await c.put(f'/api/attempts/{id}/answers/{qs[0]["id"]}', json=b, headers={'x-test-user': 's'})
        return s, late, replay, await db_attempt(id), qs
    s, late, replay, d, qs = run(go())
    EVIDENCE['late_write'] = {'submit': s.status_code, 'late_new': late.status_code, 'old_replay': replay.status_code,
                              'old_replay_duplicate': J(replay).get('duplicate') if replay.status_code == 200 else None, 'sealed_seq': d['sealed_seq']}
    assert s.status_code in (200, 202) and late.status_code == 409 and qs[1]['id'] not in d['answers']
    assert replay.status_code == 200 and J(replay)['duplicate'] is True and d['sealed_seq'] == d['server_seq'] == 1


@pytest.mark.parametrize('delay', [0.0, 0.002, 0.004, 0.008, 0.012])
def test_save_vs_seal_race(delay):
    async def go():
        id, qs = await make_attempt(n=20)
        async with client() as c:
            saves = [c.put(f'/api/attempts/{id}/answers/{q["id"]}', json=body(), headers={'x-test-user': 's'}) for q in qs]
            async def sub():
                await asyncio.sleep(delay)  # vary the interleave point of the seal
                return await c.post(f'/api/attempts/{id}/submit', headers={'x-test-user': 's'})
            res = await asyncio.gather(*saves[:10], sub(), *saves[10:])
        return res, await db_attempt(id)
    res, d = run(go())
    ok = [J(r)['accepted']['server_seq'] for r in res if r.request.method == 'PUT' and r.status_code == 200]
    rejected = [r.status_code for r in res if r.request.method == 'PUT' and r.status_code != 200]
    stored = [a['server_seq'] for a in d['answers'].values()]
    EVIDENCE.setdefault('save_vs_seal', []).append({'delay_s': delay, 'acked': len(ok), 'rejected_codes': sorted(set(rejected)), 'rejected': len(rejected), 'sealed_seq': d['sealed_seq'], 'max_acked_seq': max(ok or [0])})
    print('RACE', EVIDENCE['save_vs_seal'][-1])
    assert d['status'] == 'completed' and all(s <= d['sealed_seq'] for s in ok + stored)
    assert len(ok) == len(stored) == d['sealed_seq'] and set(rejected) <= {409}
