"""TEST-ONLY iteration 135: new hardening features (status header, packs fail-closed, assets, ledger, admission,
jobs/cron, index plans, capacity/contracts). Isolated DB via iso_harness_iter134 (all handles rebound, no lifespan).
AI / storage / crop / manual dispatch are MOCKED. Shares the event loop + helpers with the iter135 regression module.
Run: cd /app/backend/tests && python -m pytest test_iter135_canonical_regression_isolated.py test_iter135_hardening_isolated.py -n0 -p no:cacheprovider -v
"""
import asyncio, hashlib, json, time, uuid, zlib
import httpx, pytest
import iso_harness_iter134 as H
import test_iter135_canonical_regression_isolated as R
from tejas import attempts as AT, packs as PK, jobs as JB, corrections as CO, canonical as CN, admission as AD
import tejas_core, tejas_storage, server

run, client, J, body, db_attempt, TDB = R.run, R.client, R.J, R.body, R.db_attempt, R.TDB


async def make_attempt(user=R.STUDENT, deadline_in=600.0, n=4, bonus=0, rules=None):
    # unique set_id per attempt: production indexes() enforce one active attempt per (user,set,mode)
    a = {'id': 'TEST_A135_' + uuid.uuid4().hex, 'user_id': user['id'], 'set_id': 'TEST_S135_' + uuid.uuid4().hex[:8], 'title': 'TEST 135',
         'exam': 'JEE Main', 'mode': 'practice', 'version': 1, 'rules': rules or {'minutes': 10, 'correct': 4, 'wrong': -1, 'skipped': 0}, 'status': 'active',
         'answers': {}, 'first_answers': {}, 'server_seq': 0, 'command_count': 0, 'visited': [], 'test_kind': 'mock',
         'profile': {}, 'started_at': time.time(), 'deadline': time.time() + deadline_in, 'questions': R.questions(n, bonus),
         'parent_attempt': None, 'start_key': 'TEST_K135_' + uuid.uuid4().hex}
    qs = [dict(q) for q in a['questions']]
    await PK.insert_attempt(a)
    return a['id'], qs
EV = {}
OWNER = {'id': 'TEST_U135_owner', 'role': 'owner', 'name': 'TEST Owner 135', 'email': 'test135-owner@example.invalid', 'access_type': 'password'}
H.USERS.update({'s': R.STUDENT, 'o': R.OTHER, 'w': OWNER})
S, O = {'x-test-user': 's'}, {'x-test-user': 'o'}


@pytest.fixture(scope='module', autouse=True)
def isolated():
    assert H.TEST_DB != H.REAL_DB and not H.leftover_real_handles()
    run(H.tdbmod.client.drop_database(H.TEST_DB))
    run(H.tdbmod.indexes())  # production index set, isolated DB only, AFTER all handles rebound
    orig = AT.ensure_grade
    AT.ensure_grade = R._no_grade
    yield
    AT.ensure_grade = orig
    H.OFFSET[0] = 0
    run(H.tdbmod.client.drop_database(H.TEST_DB))
    assert H.TEST_DB not in run(H.tdbmod.client.list_database_names())
    with open('/app/test_reports/iter135_hardening_evidence.json', 'w') as f:
        json.dump(EV, f, indent=2, default=str)


@pytest.fixture(autouse=True)
def clock():
    H.OFFSET[0] = 0
    yield
    H.OFFSET[0] = 0


# ---------- status header endpoint ----------
def test_status_header_contract_auth_and_no_hydration():
    calls = []
    oe = PK.entry_for

    async def spy(*a, **k):
        calls.append(a[0]); return await oe(*a, **k)

    async def go():
        id, _ = await make_attempt()
        PK.entry_for = spy
        try:
            async with client() as c:
                own = await c.get(f'/api/attempts/{id}/status', headers=S)
                foreign = await c.get(f'/api/attempts/{id}/status', headers=O)
                anon = await c.get(f'/api/attempts/{id}/status')
                H.OFFSET[0] = 3600
                ahead = await c.get(f'/api/attempts/{id}/status', headers=S)
                H.OFFSET[0] = 0
        finally:
            PK.entry_for = oe
        return own, foreign, anon, ahead, await db_attempt(id)
    own, foreign, anon, ahead, d = run(go())
    j = J(own)
    EV['status_header'] = {'keys': sorted(j), 'bytes': len(own.content), 'foreign': foreign.status_code, 'anon': anon.status_code,
                           'ahead_status': J(ahead)['status'], 'server_now_minus_real': round(J(ahead)['server_now'] - time.time(), 2), 'pack_loads': len(calls)}
    assert own.status_code == 200 and set(j) == {'id', 'status', 'deadline', 'server_now', 'receipt', 'submitted_at', 'grading_status', 'sealed_seq'}
    assert not any(k in own.text for k in ('"questions"', '"answers"', 'pack_id', 'rules', 'TEST solution'))
    assert foreign.status_code == 404 and anon.status_code == 401 and calls == []
    assert J(ahead)['status'] == 'active' and abs(J(ahead)['server_now'] - time.time()) < 5 and d['status'] == 'active'


def test_status_seals_expired_and_full_vs_status_bytes():
    async def go():
        id, _ = await make_attempt(deadline_in=-3)
        async with client() as c:
            H.OFFSET[0] = -3600  # app clock behind; DB clock must still seal
            st = await c.get(f'/api/attempts/{id}/status', headers=S)
            H.OFFSET[0] = 0
            full = await c.get(f'/api/attempts/{id}', headers=S)
        return st, full, await db_attempt(id)
    st, full, d = run(go())
    j = J(st)
    EV['status_expired'] = {'status': j['status'], 'submitted_eq_deadline': j['submitted_at'] == j['deadline'], 'status_bytes': len(st.content), 'full_bytes': len(full.content)}
    assert j['status'] == 'completed' and d['reason'] == 'time_limit' and j['submitted_at'] == d['deadline'] and j['receipt'] == d['id']
    assert len(st.content) * 10 < len(full.content)


def test_finalize_time_limit_refuses_future_then_explicit_submit_seals():
    async def go():
        id, _ = await make_attempt(deadline_in=600)
        a = await AT.finalize(id, 'time_limit')
        async with client() as c:
            s = await c.post(f'/api/attempts/{id}/submit', headers=S)
        return a, s, await db_attempt(id)
    a, s, d = run(go())
    assert a['status'] == 'active' and s.status_code in (200, 202)
    assert d['status'] == 'completed' and d['reason'] == 'submitted' and d['submitted_at'] < d['deadline']


def test_history_and_submit_projection_contract():
    async def go():
        id, qs = await make_attempt()
        async with client() as c:
            await c.put(f'/api/attempts/{id}/answers/{qs[0]["id"]}', json=body(), headers=S)
            s = await c.post(f'/api/attempts/{id}/submit', headers=S)
            h = await c.get('/api/attempts', headers=S)
        return id, s, h
    id, s, h = run(go())
    item = next(i for i in J(h)['items'] if i['id'] == id)
    EV['submit_contract_keys'] = sorted(J(s)); EV['history_item_keys'] = sorted(item)
    assert J(s)['status'] == 'completed' and J(s).get('receipt') == id
    assert 'questions' not in item and 'answers' not in item and item['status'] == 'completed' and 'server_now' in item


# ---------- packs fail-closed via actual API ----------
@pytest.mark.parametrize('mode', ['trailing', 'missing', 'oversize', 'wrong_hash', 'truncated'])
def test_pack_corruption_fails_closed_503_then_recovers(mode):
    async def go():
        id, _ = await make_attempt()
        pid = (await db_attempt(id))['pack_id']
        orig = await TDB.tejas_packs.find_one({'_id': pid})
        if mode == 'missing':
            await TDB.tejas_packs.delete_one({'_id': pid})
        else:
            raw = zlib.decompress(orig['payload'])
            ch = {'trailing': {'payload': orig['payload'] + b'JUNK'}, 'oversize': {'bytes': 64 * 1024 * 1024},
                  'wrong_hash': {'payload': zlib.compress(raw.replace(b'TEST_134', b'TEST_XXX', 1))},
                  'truncated': {'payload': orig['payload'][:-6]}}[mode]
            await TDB.tejas_packs.update_one({'_id': pid}, {'$set': ch})
        PK._cache.clear(); PK._cache_bytes = 0
        async with client() as c:
            bad = await c.get(f'/api/attempts/{id}', headers=S)
            await TDB.tejas_packs.replace_one({'_id': pid}, orig, upsert=True)
            good = await c.get(f'/api/attempts/{id}', headers=S)
        return bad, good, await db_attempt(id)
    bad, good, d = run(go())
    EV.setdefault('pack_corruption', {})[mode] = [bad.status_code, bad.json().get('error') if bad.status_code != 200 else None, good.status_code]
    assert bad.status_code == 503 and 'TEST solution' not in bad.text and good.status_code == 200
    assert d['status'] == 'active' and d['answers'] == {} and PK._loading == {}


def test_pack_cancellation_does_not_cancel_shared_fetch_and_eviction_bound():
    async def go():
        key = await PK.seal(R.questions(30))
        PK._cache.clear(); PK._cache_bytes = 0
        t1 = asyncio.ensure_future(PK.unpack(key)); t2 = asyncio.ensure_future(PK.unpack(key))
        await asyncio.sleep(0); t1.cancel()
        r2 = await t2
        old = PK._CACHE_MAX_BYTES
        PK._CACHE_MAX_BYTES = 200_000
        try:
            for i in range(6):
                await PK.seal(R.questions(20 + i))
            bound = (PK._cache_bytes, PK._CACHE_MAX_BYTES, len(PK._cache))
        finally:
            PK._CACHE_MAX_BYTES = old
        return t1.cancelled(), len(r2), bound
    cancelled, n, bound = run(go())
    EV['pack_cancel_evict'] = {'cancelled': cancelled, 'other_waiter_len': n, 'bytes_limit_entries': bound}
    assert cancelled and n == 30 and bound[0] <= bound[1]


# ---------- private assets ----------
def _asset_setup(monkey, src_bytes, sha):
    fid = 'TEST_F135_' + uuid.uuid4().hex
    run(TDB.tejas_files.insert_one({'id': fid, 'kind': 'pdf', 'path': 'TEST/135/' + fid + '.pdf', **({'sha256': sha} if sha else {})}))
    calls = []
    monkey.setattr(tejas_storage, 'get_object', lambda p: src_bytes)
    monkey.setattr(tejas_core, 'crop_png', lambda data, ref, scale=2: calls.append(1) or b'\x89PNG-TEST135')
    return fid, calls


def test_assets_authorization_embargo_bonus_and_integrity(monkeypatch):
    good = b'%PDF-TEST135-' + uuid.uuid4().bytes
    fid, calls = _asset_setup(monkeypatch, good, hashlib.sha256(good).hexdigest())
    bad_fid = 'TEST_F135_bad_' + uuid.uuid4().hex
    run(TDB.tejas_files.insert_one({'id': bad_fid, 'kind': 'pdf', 'path': 'TEST/135/bad.pdf', 'sha256': hashlib.sha256(b'other').hexdigest()}))
    png_fid = 'TEST_F135_png_' + uuid.uuid4().hex
    run(TDB.tejas_files.insert_one({'id': png_fid, 'kind': 'rendered_png', 'path': 'TEST/135/x.png', 'sha256': hashlib.sha256(b'other').hexdigest()}))
    legacy_fid = 'TEST_F135_legacy_' + uuid.uuid4().hex
    run(TDB.tejas_files.insert_one({'id': legacy_fid, 'kind': 'pdf', 'path': 'TEST/135/legacy.pdf'}))
    ref = lambda f: [{'file_id': f, 'page': 1, 'rect': [0, 0, 1, 1]}]

    async def go():
        qs = R.questions(3, bonus=1)
        qs[0].update(q_refs=ref(fid), s_refs=ref(fid)); qs[1].update(q_refs=ref(bad_fid)); qs[2].update(q_refs=ref(png_fid) + ref(legacy_fid)); qs[3].update(q_refs=ref(fid))
        a = {'id': 'TEST_A135_' + uuid.uuid4().hex, 'user_id': R.STUDENT['id'], 'set_id': 'TEST_S135_assets', 'title': 'T', 'exam': 'JEE Main', 'mode': 'practice',
             'version': 1, 'rules': {'minutes': 10, 'bonus_rule': True}, 'status': 'active', 'answers': {}, 'first_answers': {}, 'server_seq': 0, 'command_count': 0,
             'visited': [], 'profile': {}, 'started_at': time.time(), 'deadline': time.time() + 600, 'questions': qs, 'start_key': 'TEST_K135_' + uuid.uuid4().hex}
        await PK.insert_attempt(a)
        id = a['id']; u = lambda q, k='question', i=0, sv='': f'/api/attempts/{id}/questions/{q["id"]}/asset/{k}/{i}' + (f'?score_version={sv}' if sv else '')
        out = {}
        async with client() as c:
            out['own_q'] = (await c.get(u(qs[0]), headers=S)).status_code
            out['foreign_user'] = (await c.get(u(qs[0]), headers=O)).status_code
            out['foreign_qid'] = (await c.get(f'/api/attempts/{id}/questions/{uuid.uuid4()}/asset/question/0', headers=S)).status_code
            out['solution_active'] = (await c.get(u(qs[0], 'solution'), headers=S)).status_code
            out['bonus_locked'] = (await c.get(u(qs[3]), headers=S)).status_code
            n_before = len(calls)
            out['pdf_hash_mismatch'] = (await c.get(u(qs[1]), headers=S)).status_code
            out['crop_calls_on_mismatch'] = len(calls) - n_before
            out['png_hash_mismatch'] = (await c.get(u(qs[2]), headers=S)).status_code
            out['legacy_nohash'] = (await c.get(u(qs[2], i=1), headers=S)).status_code
            # complete with competition embargo in the future by DB clock; app clock ahead must not release
            await TDB.tejas_attempts.update_one({'id': id}, {'$set': {'competition_end': time.time() + 600}})
            await c.post(f'/api/attempts/{id}/submit', headers=S)
            H.OFFSET[0] = 7200
            out['solution_embargo_skew'] = (await c.get(u(qs[0], 'solution'), headers=S)).status_code
            st = await c.get(f'/api/attempts/{id}/status', headers=S)
            H.OFFSET[0] = 0
            await TDB.tejas_attempts.update_one({'id': id}, {'$set': {'competition_end': 0}})
            out['solution_released'] = (await c.get(u(qs[0], 'solution'), headers=S)).status_code
            await TDB.tejas_score_versions.insert_one({'id': 'TEST_SV135_foreign', 'attempt_id': id, 'user_id': R.OTHER['id'], 'pack_id': 'x'})
            out['foreign_score_version'] = (await c.get(u(qs[0], sv='TEST_SV135_foreign'), headers=S)).status_code
            leak = st.text
        return out, leak
    out, leak = run(go())
    EV['assets'] = out
    print('ASSETS', out)
    assert out['own_q'] == 200 and out['foreign_user'] == 404 and out['foreign_qid'] == 404 and out['solution_active'] == 403
    assert out['bonus_locked'] == 404 and out['pdf_hash_mismatch'] == 503 and out['crop_calls_on_mismatch'] == 0
    assert out['png_hash_mismatch'] == 503 and out['legacy_nohash'] == 200
    assert out['solution_embargo_skew'] == 403 and out['solution_released'] == 200 and out['foreign_score_version'] == 404
    assert '"answer"' not in leak and 'solution' not in leak


# ---------- frozen ledger ----------
def test_ledger_once_concurrent_grade_and_tamper_fail_closed():
    async def go():
        id, qs = await make_attempt()
        async with client() as c:
            await c.put(f'/api/attempts/{id}/answers/{qs[0]["id"]}', json=body(value='A'), headers=S)
            await c.post(f'/api/attempts/{id}/submit', headers=S)
        a = await AT.owned(id, R.STUDENT)
        ledgers = await asyncio.gather(*[CO.freeze_ledger(dict(a)) for _ in range(10)])
        n = await TDB.tejas_ledgers.count_documents({'id': id})
        led = await TDB.tejas_ledgers.find_one({'id': id})
        async with client() as c:
            ok = await c.get(f'/api/attempts/{id}/results', headers=S)
            await TDB.tejas_attempts.update_one({'id': id}, {'$set': {f'answers.{qs[1]["id"]}': {'value': 'A', 'revision': 1, 'server_seq': 2}}})
            tampered = await c.get(f'/api/attempts/{id}/results', headers=S)
            await TDB.tejas_attempts.update_one({'id': id}, {'$unset': {f'answers.{qs[1]["id"]}': 1}, '$set': {'rules.minutes': 99}})
            rules_t = await c.get(f'/api/attempts/{id}/results', headers=S)
        return ledgers, n, led, ok, tampered, rules_t
    ledgers, n, led, ok, tampered, rules_t = run(go())
    EV['ledger'] = {'docs': n, 'fields': sorted(k for k in led if k != 'rows'), '_id_eq_id': led['_id'] == led['id'], 'distinct_created': len({l['created_at'] for l in ledgers}),
                    'results': ok.status_code, 'answers_tampered': tampered.status_code, 'rules_tampered': rules_t.status_code, 'score': J(ok).get('summary', {}).get('score') if ok.status_code == 200 else None}
    print('LEDGER', EV['ledger'])
    assert n == 1 and led['_id'] == led['id'] and led['source_commitment'] and led['sealed_seq'] == 1 and led['user_id'] == R.STUDENT['id'] and led['source_pack_id']
    assert len({l['created_at'] for l in ledgers}) == 1 and ok.status_code == 200
    assert tampered.status_code == 503 and rules_t.status_code == 503


def test_legacy_ledger_without_proof_readable_unchanged():
    async def go():
        id, qs = await make_attempt()
        await AT.finalize(id, 'submitted')
        a = await AT.owned(id, R.STUDENT)
        res = CO.score_attempt(a) if hasattr(CO, 'score_attempt') else AT.score_attempt(a)
        legacy = {'_id': id, 'id': id, 'attempt_id': id, 'user_id': a['user_id'], 'summary': res['summary'], 'engine_version': 1, 'created_at': 1.0,
                  'rows': [{k: q.get(k) for k in ('id', 'response', 'normalized_response', 'accepted_answers', 'outcome', 'disposition', 'marks', 'marks_exact', 'reason_code')} for q in res['questions']]}
        await TDB.tejas_ledgers.insert_one(dict(legacy))
        before = await TDB.tejas_ledgers.find_one({'id': id})
        async with client() as c:
            r = await c.get(f'/api/attempts/{id}/results', headers=S)
        again = await CO.freeze_ledger(await AT.owned(id, R.STUDENT))
        after = await TDB.tejas_ledgers.find_one({'id': id})
        return r, before, after, again
    r, before, after, again = run(go())
    EV['legacy_ledger'] = {'results': r.status_code, 'unchanged': before == after}
    assert r.status_code == 200 and before == after and 'source_commitment' not in after


# ---------- admission gate (pure ASGI, no DB) ----------
def test_admission_lanes_release_and_cancellation():
    events = {'downstream': 0}
    gate_box = {}

    async def inner(scope, receive, send):
        events['downstream'] += 1
        if scope['path'].endswith('/slow/asset/x'):
            await asyncio.sleep(0.2)
        if scope['path'] == '/api/boom':
            raise RuntimeError('TEST boom')
        await send({'type': 'http.response.start', 'status': 200, 'headers': []})
        await send({'type': 'http.response.body', 'body': b'ok', 'more_body': False})
        lane = AD.workload(scope['path'], scope['method'])
        if lane:
            events.setdefault('in_flight_after_body', []).append((lane, gate_box['g'].lanes[lane]['in_flight']))
        await asyncio.sleep(0.05)  # background-task phase

    class Owner: state = type('S', (), {})()
    g = AD.AdmissionGate(inner, Owner); gate_box['g'] = g
    g.lanes['asset']['limit'] = 2
    c = httpx.AsyncClient(transport=httpx.ASGITransport(app=g, raise_app_exceptions=False), base_url='http://t')

    async def go():
        slow = [asyncio.ensure_future(c.get('/api/attempts/a/questions/q/slow/asset/x')) for _ in range(2)]
        await asyncio.sleep(0.05)
        d0 = events['downstream']
        over = await c.get('/api/attempts/a/questions/q/slow/asset/x')
        d1 = events['downstream']
        live = await c.put('/api/attempts/a/answers/q')
        await asyncio.gather(*slow)
        boom = await c.get('/api/boom')
        t = asyncio.ensure_future(c.get('/api/attempts/a/questions/q/slow/asset/x'))
        await asyncio.sleep(0.05); t.cancel()
        await asyncio.sleep(0.05)
        health = await c.get('/api/health')
        return over, d0 == d1, live, boom
    over, no_downstream, live, boom = run(go())
    snap = g.snapshot()
    EV['admission'] = {'over': over.status_code, 'retry_after': over.headers.get('retry-after'), 'no_downstream': no_downstream, 'live': live.status_code,
                       'in_flight_after_final_body': events.get('in_flight_after_body'), 'lanes': {k: {x: v[x] for x in ('in_flight', 'peak', 'rejected', 'failed')} for k, v in snap['lanes'].items()}}
    print('ADMISSION', EV['admission'])
    assert over.status_code == 503 and over.headers.get('retry-after') == '2' and no_downstream and live.status_code == 200
    assert all(v['in_flight'] == 0 for v in snap['lanes'].values())
    # a request's own slot is released after its final body (before the background phase); the concurrent asset sibling may still hold 1
    assert [x for l, x in events['in_flight_after_body'] if l == 'live'] == [0] and all(x <= 1 for l, x in events['in_flight_after_body'])
    assert snap['lanes']['read']['failed'] >= 1 and 'health' not in json.dumps(snap)
    assert not any(k in json.dumps(snap) for k in ('/api/', 'phone', 'user'))


def test_admission_real_app_overload_envelope_headers_and_probes():
    gate = server.app.state.admission
    origin = server.origins[0] if server.origins else 'https://x'

    async def go():
        async with client() as c:
            await c.get('/api/health')  # build middleware stack
            old = gate.lanes['read']['limit']; gate.lanes['read']['limit'] = 0
            try:
                r = await c.get('/api/sets', headers={**S, 'origin': origin})
            finally:
                gate.lanes['read']['limit'] = old
            h = await c.get('/api/health')
            rd = await c.get('/api/ready')
            oc = server.client
            class Bad:
                class admin:
                    @staticmethod
                    async def command(*a, **k):
                        from pymongo.errors import ServerSelectionTimeoutError
                        raise ServerSelectionTimeoutError('TEST ping fail')
            server.client = Bad
            try:
                rf = await c.get('/api/ready')
            finally:
                server.client = oc
            rt = {u: (await c.get('/api/internal/runtime/status', headers={'x-test-user': u} if u else {})).status_code for u in ('', 's', 'w')}
            rt_body = (await c.get('/api/internal/runtime/status', headers={'x-test-user': 'w'})).text
        return r, h, rd, rf, rt, rt_body
    r, h, rd, rf, rt, rt_body = run(go())
    EV['real_gate'] = {'overload': r.status_code, 'body': r.json(), 'headers': {k: r.headers.get(k) for k in ('retry-after', 'x-content-type-options', 'x-request-id', 'access-control-allow-origin', 'access-control-allow-credentials')},
                       'health': h.status_code, 'ready': rd.status_code, 'ready_fail': rf.status_code, 'runtime_status': rt, 'runtime_bytes': len(rt_body)}
    print('GATE', EV['real_gate'])
    assert r.status_code == 503 and r.headers.get('retry-after') == '2' and r.headers.get('x-content-type-options') == 'nosniff' and r.headers.get('x-request-id')
    assert r.headers.get('access-control-allow-origin') == origin
    assert h.status_code == 200 and rd.status_code == 200 and rf.status_code == 503
    assert rt[''] == 401 and rt['s'] == 403 and rt['w'] == 200 and '+91' not in rt_body


# ---------- jobs / cron ----------
def test_jobs_grade_lease_retry_exhaust_and_duplicate(monkeypatch):
    async def go():
        out = {}
        id, qs = await make_attempt()
        await AT.finalize(id, 'submitted')
        j = await JB.enqueue('grade', R.STUDENT['id'], 'TEST_S134', {'attempt_id': id})
        j2 = await JB.enqueue('grade', R.STUDENT['id'], 'TEST_S134', {'attempt_id': id})
        out['dup_same_id'] = j['id'] == j2['id']
        H.OFFSET[0] = 7200  # app clock skew must not matter for leases
        await asyncio.gather(JB.run_job(j['id'], drain=False), JB.run_job(j['id'], drain=False))
        H.OFFSET[0] = 0
        jd = await TDB.tejas_jobs.find_one({'id': j['id']}, {'_id': 0})
        out['grade'] = [jd['status'], jd['attempts'], (await db_attempt(id))['grading_status'], await TDB.tejas_ledgers.count_documents({'id': id})]
        # stale worker: lease expired -> require_lease must refuse
        await TDB.tejas_jobs.insert_one({'id': 'TEST_job_stale', 'kind': 'grade', 'status': 'running', 'lease': 'L1', 'lease_until': time.time() - 5, 'attempts': 1})
        try:
            await JB.require_lease({'id': 'TEST_job_stale', 'lease': 'L1'}); out['stale_refused'] = False
        except RuntimeError:
            out['stale_refused'] = True
        # failing grade (attempt not sealed) -> retry queued, then exhausted -> failed
        aid, _ = await make_attempt()
        jf = await JB.enqueue('grade', R.STUDENT['id'], 'TEST_S134', {'attempt_id': aid})
        seen = []
        for _ in range(JB.JOB_ATTEMPTS):
            await TDB.tejas_jobs.update_one({'id': jf['id']}, {'$set': {'next_run_at': 0}})
            await JB.run_job(jf['id'], drain=False)
            seen.append((await TDB.tejas_jobs.find_one({'id': jf['id']}))['status'])
        out['fail_sequence'] = seen
        # crashed worker on last attempt -> maintenance marks failed
        await TDB.tejas_jobs.insert_one({'id': 'TEST_job_crashed', 'kind': 'grade', 'user_id': 'x', 'set_id': 'x', 'payload': {'attempt_id': 'none'}, 'status': 'running', 'lease': 'L2', 'lease_until': time.time() - 5, 'attempts': JB.JOB_ATTEMPTS, 'created_at': 0})
        # seal-enqueue crash: completed attempt with grading_status queued and NO job
        cid, _ = await make_attempt()
        await AT.finalize(cid, 'submitted')
        await TDB.tejas_jobs.delete_many({'payload.attempt_id': cid})
        import tejas.manual_solutions as MS
        monkeypatch.setattr(MS, 'dispatch_manual', lambda: asyncio.sleep(0))
        AT.ensure_grade = _real_ensure_grade
        try:
            await JB.maintenance()
        finally:
            AT.ensure_grade = R._no_grade
        out['crashed_after_maint'] = (await TDB.tejas_jobs.find_one({'id': 'TEST_job_crashed'}))['status']
        cj = await TDB.tejas_jobs.find_one({'payload.attempt_id': cid})
        out['recovered_outbox'] = [cj and cj['status'], (await db_attempt(cid))['grading_status']]
        return out
    out = run(go())
    EV['jobs'] = out
    print('JOBS', out)
    assert out['dup_same_id'] and out['grade'] == ['done', 1, 'ready', 1] and out['stale_refused']
    assert out['fail_sequence'] == ['queued'] * (JB.JOB_ATTEMPTS - 1) + ['failed']
    assert out['crashed_after_maint'] == 'failed' and out['recovered_outbox'] == ['done', 'ready']


from tejas.attempts import ensure_grade as _real_ensure_grade  # captured at import (before module fixture patch)


def test_drain_quantum_bounded_and_ai_paused(monkeypatch):
    claimed = []
    async def fake_run(id, drain=True):
        claimed.append(id)
        await TDB.tejas_jobs.update_one({'id': id}, {'$set': {'status': 'done'}})
    async def go():
        await TDB.tejas_jobs.insert_many([{'id': f'TEST_q_{i}', 'kind': 'report', 'status': 'queued', 'attempts': 0, 'next_run_at': 0, 'created_at': i} for i in range(40)])
        monkeypatch.setattr(JB, 'run_job', fake_run)
        await JB.drain_lane('report')
        import tejas.mock_solutions as MS
        return MS.AI_SOLVING_PAUSED
    paused = run(go())
    EV['drain'] = {'claimed': len(claimed), 'quantum': JB.JOB_DRAIN_QUANTUM, 'ai_paused': paused}
    assert len(claimed) == JB.JOB_DRAIN_QUANTUM == 16 and claimed[0] == 'TEST_q_0' and paused is True


def test_cron_auth_malformed_duplicate(monkeypatch):
    monkeypatch.setenv('WEBHOOK_CRON_SECRET', 'TEST-cron-' + uuid.uuid4().hex)
    sec = __import__('os').environ['WEBHOOK_CRON_SECRET']
    ran = []
    monkeypatch.setattr(JB, 'maintenance', lambda: ran.append(1) or asyncio.sleep(0))
    async def go():
        async with client() as c:
            u = await c.post('/api/cron/maintenance', json={'event': 'schedule.triggered', 'run_id': 'r1'})
            w = await c.post('/api/cron/maintenance', json={'event': 'schedule.triggered', 'run_id': 'r1'}, headers={'authorization': 'Bearer wrong'})
            m = await c.post('/api/cron/maintenance', json={'event': 'nope'}, headers={'authorization': 'Bearer ' + sec})
            rid = 'TEST_r_' + uuid.uuid4().hex
            a1 = await c.post('/api/cron/maintenance', json={'event': 'schedule.triggered', 'run_id': rid}, headers={'authorization': 'Bearer ' + sec})
            a2 = await c.post('/api/cron/maintenance', json={'event': 'schedule.triggered', 'run_id': rid}, headers={'authorization': 'Bearer ' + sec})
        return u, w, m, a1, a2
    u, w, m, a1, a2 = run(go())
    EV['cron'] = [u.status_code, w.status_code, m.status_code, a1.status_code, J(a2), len(ran)]
    assert u.status_code == 401 and w.status_code == 401 and m.status_code in (400, 422) and a1.status_code == 200 and J(a2).get('duplicate') is True and len(ran) == 1


# ---------- index query plans (after rebinding; indexes() on isolated DB only) ----------
def _winning(plan):
    p = plan['queryPlanner']['winningPlan']
    p = p.get('queryPlan', p)
    stages, idx = [], None
    while p:
        stages.append(p.get('stage')); idx = idx or p.get('indexName')
        p = p.get('inputStage') or (p.get('inputStages') or [None])[0]
    return {'stages': stages, 'index': idx}


def test_index_query_plans_synthetic_volume():
    assert not H.leftover_real_handles()
    async def go():
        now = time.time()
        await TDB.tejas_attempts.insert_many([{'id': f'TEST_ix_{i}', 'user_id': f'TEST_ixu_{i % 200}', 'set_id': f'TEST_ixs_{i}', 'mode': 'practice', 'status': 'active' if i % 3 else 'completed', 'deadline': now + i,
                                               'grading_status': ['ready', 'queued', 'failed'][i % 3], 'started_at': now - i, 'start_key': f'k{i}', 'submitted_at': now} for i in range(3000)])
        await TDB.tejas_jobs.insert_many([{'id': f'TEST_ixj_{i}', 'kind': ['grade', 'report'][i % 2], 'status': ['queued', 'done', 'failed'][i % 3], 'created_at': i, 'lease_until': 0, 'attempts': 0, 'next_run_at': 0} for i in range(3000)])
        A, Jc = TDB.tejas_attempts, TDB.tejas_jobs
        q = {
            'own_attempt': await A.find({'id': 'TEST_ix_5', 'user_id': 'TEST_ixu_5'}).explain(),
            'user_history': await A.find({'user_id': 'TEST_ixu_7'}).sort('started_at', -1).limit(20).explain(),
            'expiry_sweep': await A.find({'status': 'active', 'deadline': {'$gt': 0}, '$expr': {'$lte': ['$deadline', CN.EPOCH_NOW]}}).sort('deadline', 1).limit(1000).explain(),
            'grade_outbox': await A.find({'status': 'completed', 'grading_status': {'$nin': ['ready', 'failed']}}).limit(1000).explain(),
            'job_drain': await Jc.find({'kind': 'report', 'status': 'queued'}).sort('created_at', 1).limit(1).explain(),
            'job_drain_actual': await Jc.find({'kind': 'report', 'status': 'queued', '$and': [{'$expr': {'$lte': [{'$ifNull': ['$next_run_at', 0]}, CN.EPOCH_NOW]}},
                {'$or': [{'attempts': {'$lt': JB.JOB_ATTEMPTS}}, {'attempts': {'$exists': False}}]}]}, {'id': 1}).sort('created_at', 1).limit(1).explain(),
            'job_by_id': await Jc.find({'id': 'TEST_ixj_9'}).explain(),
        }
        return {k: _winning(v) for k, v in q.items()}
    plans = run(go())
    EV['index_plans'] = plans
    print('PLANS', plans)
    for k in ('own_attempt', 'user_history', 'expiry_sweep', 'grade_outbox', 'job_by_id'):
        assert 'COLLSCAN' not in plans[k]['stages'] and plans[k]['index'], (k, plans[k])
    assert 'SORT' not in plans['user_history']['stages'] and 'SORT' not in plans['expiry_sweep']['stages']


# ---------- capacity + contracts ----------
def test_capacity_profile_and_route_contracts():
    async def go():
        async with client() as c:
            return (await c.get('/api/internal/capacity/profile', headers={'x-test-user': 'w'}), await c.get('/api/internal/capacity/profile', headers=S))
    r, st = run(go())
    p = J(r)
    keys = {c.key for c in server.app.state.route_contracts} if hasattr(server.app.state, 'route_contracts') else set()
    EV['capacity'] = {'status': r.status_code, 'student': st.status_code, 'keys': sorted(p), 'reference_model': p.get('reference_model'),
                      'qualified_active_attempts': p.get('qualified_active_attempts'), 'mounted_runtime_keys': sorted(p.get('mounted_runtime', {}))}
    EV['contracts'] = {'count': len(keys), 'status_route': 'attempt_status.status_attempt' in keys, 'runtime': 'engineering.runtime_status' in keys}
    print('CAP', EV['capacity'], EV['contracts'])
    assert r.status_code == 200 and st.status_code == 403 and p['reference_model'] == 'UNMOUNTED_V5_DESIGN' and p.get('mounted_runtime')
    assert p.get('qualified_active_attempts') is None and 'workload' in p and 'rates' in p
    assert EV['contracts']['status_route'] and EV['contracts']['runtime']


# ---------- remaining app-clock gates (skew probe: app clock +3600s, DB embargo/deadline still future) ----------
def test_exam_navigation_history_embargo_and_status_use_db_clock():
    async def go():
        id, _ = await make_attempt(deadline_in=600)
        cid, _ = await make_attempt(deadline_in=600)
        await AT.finalize(cid, 'submitted')
        await TDB.tejas_attempts.update_one({'id': cid}, {'$set': {'competition_end': time.time() + 1800, 'summary': {'score': 4, 'TEST': 'embargoed'}}})
        H.OFFSET[0] = 3600
        async with client() as c:
            r = await c.get('/api/exam-navigation/jee-main/history', headers=S)
        H.OFFSET[0] = 0
        return id, cid, r, await db_attempt(id)
    id, cid, r, d = run(go())
    items = {i['id']: i for i in J(r).get('items', [])} if r.status_code == 200 else {}
    EV['exam_nav_skew'] = {'http': r.status_code, 'active_reported': items.get(id, {}).get('status'), 'db_status': d['status'],
                           'embargoed_summary_leaked': items.get(cid, {}).get('summary')}
    print('NAVSKEW', EV['exam_nav_skew'])
    assert r.status_code == 200 and d['status'] == 'active'
    assert items[cid].get('summary') is None, 'FAULT: exam_navigation.history uses app now() for competition_end embargo'


def test_perf_status_vs_full_read_100q():
    async def go():
        id, _ = await make_attempt(n=100)
        async with client() as c:
            await c.get(f'/api/attempts/{id}', headers=S)
            out = {}
            for name, url in (('status', f'/api/attempts/{id}/status'), ('full', f'/api/attempts/{id}')):
                t = time.perf_counter()
                rs = await asyncio.gather(*[c.get(url, headers=S) for _ in range(32)])
                out[name] = {'ms_32_concurrent': round((time.perf_counter() - t) * 1000, 1), 'bytes': len(rs[0].content), 'codes': sorted({x.status_code for x in rs}), 'n503': sum(x.status_code == 503 for x in rs),
                             'retry_after': sorted({x.headers.get('retry-after') for x in rs if x.status_code == 503})}
        return out
    out = run(go())
    EV['perf_status_vs_full_100q'] = out
    print('PERF', out)
    # status = live lane (32); full read = read lane (16): excess is shed with 503 Retry-After 2 by design
    assert out['status']['codes'] == [200] and set(out['full']['codes']) <= {200, 503} and out['status']['bytes'] * 50 < out['full']['bytes']
