"""TEST-ONLY iteration 145: bounded load + logic + speed exercise against the REAL ASGI app (AdmissionGate and all middleware)
in the EXCLUSIVE isolated DB tejas_isolated_load145 (iso_harness_load145). Synthetic header users (TEST ONLY), storage GET -> local
original PDFs, storage writes + LLM forbidden. 100 logical students, <=30 steady client concurrency, one 100-request burst.
Not a capacity / SLO claim: in-process httpx ASGITransport, co-located Mongo, single process, synthetic auth.
Run (foreground, <=120s): cd /app/backend/tests && timeout 118 python -m pytest test_iter145_load.py -n0 -p no:cacheprovider -s -q
"""
import asyncio, copy, json, resource, statistics, time, uuid
from collections import Counter, defaultdict
from pathlib import Path
import httpx, pymongo, pytest
import iso_harness_load145 as H

LOOP = asyncio.new_event_loop(); asyncio.set_event_loop(LOOP); run = LOOP.run_until_complete
TDB = H.TDB
N_USERS, STEADY, N_SUBMIT = 100, 30, 60
P1, P2 = 'jee-main-pyq-2026-01-22-s1', 'jee-main-pyq-2026-04-02-s2'  # Jan large-page (bonus_all) / April (multiple_accepted)
PAPERS = {s['id']: s for s in H.SETS}
for i in range(N_USERS):
    H.USERS['u%d' % i] = {'id': 'TEST_U145_%03d' % i, 'role': 'student', 'name': 'TEST L%d' % i, 'phone': '+9199145%05d' % i,
                          'access_type': 'unverified_phone', 'exam': 'JEE Main'}
M = defaultdict(lambda: {'first': Counter(), 'final': Counter(), 'retry': Counter(), 'lat_first': [], 'lat_exp': [], 'lat_retry_extra': []})
FAILS, NON_ADMISSION_503, EV, ST = [], [], {}, {}


def hdr(i): return {'x-test-user': 'u%d' % i}
def uid(i): return 'TEST_U145_%03d' % i
def J(r):
    j = r.json(); return j.get('data') if isinstance(j, dict) and 'data' in j and 'meta' in j else j


def client():
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=H.app, raise_app_exceptions=False), base_url='https://api.test.example', timeout=60)


async def call(c, ep, method, url, h, body=None, budget=40.0, max_retries=8, retry=True):
    """Client with honest accounting: first-try status, retry statuses, final status, first and experienced latency."""
    t0 = time.perf_counter(); n = 0
    while True:
        t = time.perf_counter(); r = await c.request(method, url, headers=h, json=body); dt = time.perf_counter() - t
        if n == 0: M[ep]['first'][r.status_code] += 1; M[ep]['lat_first'].append(dt)
        else: M[ep]['retry'][r.status_code] += 1
        if r.status_code >= 500:
            busy = r.status_code == 503 and 'capacity_busy' in r.text
            if not busy:
                (FAILS if r.status_code != 503 else NON_ADMISSION_503).append((ep, r.status_code, r.text[:160]))
        if retry and r.status_code in (429, 503) and 'capacity_busy' in r.text and n < max_retries and time.perf_counter() - t0 < budget:
            await asyncio.sleep(float(r.headers.get('retry-after', '1'))); n += 1; continue
        tot = time.perf_counter() - t0
        M[ep]['final'][r.status_code] += 1; M[ep]['lat_exp'].append(tot)
        if n: M[ep]['lat_retry_extra'].append(tot - dt)
        return r


def plan_for(i, pid):
    qs = PAPERS[pid]['questions']; std = [q for q in qs if q['disposition'] == 'standard']
    picks = []
    for k in range(12):
        q = std[(i * 7 + k * 5) % len(std)]
        if q not in picks: picks.append(q)
    plan = {}
    for k, q in enumerate(picks):
        if k % 3 == 0 and k:
            plan[q['id']] = next(x for x in 'ABCD' if x != q['answer']) if q['type'] == 'mcq' else str(int(q['answer']) + 1)
        else:
            plan[q['id']] = q['answer']
    if pid == P2:
        mq = next(q for q in qs if q['disposition'] == 'multiple_accepted')
        plan[mq['id']] = 'D' if (i // 2) % 2 == 0 else 'C'
    first = picks[0]  # rev1 deliberately different, rev2 = correct
    rev1 = next(x for x in 'ABCD' if x != first['answer']) if first['type'] == 'mcq' else str(int(first['answer']) + 2)
    return plan, first['id'], rev1


def expected(pid, final):
    total, marks = 0, {}
    for q in PAPERS[pid]['questions']:
        if q['disposition'] == 'bonus_all': m = 4
        elif q['id'] not in final: m = 0
        else: m = 4 if final[q['id']] in (q.get('accepted_answers') or [q['answer']]) else -1
        marks[q['id']] = m; total += m
    return total, marks


def pct(xs, p):
    if not xs: return None
    xs = sorted(xs); return round(xs[min(len(xs) - 1, int(round(p / 100 * (len(xs) - 1))))] * 1000, 1)


def rss_mb():
    for line in open('/proc/self/status'):
        if line.startswith('VmRSS'): return round(int(line.split()[1]) / 1024, 1)


@pytest.fixture(scope='module', autouse=True)
def isolated():
    assert H.TEST_DB == 'tejas_isolated_load145' and not H.leftover_real_handles()
    run(H.tdbmod.client.drop_database(H.TEST_DB)); run(H.tdbmod.indexes())
    for name, rows in H.DATA['collections'].items():
        run(TDB[name].insert_many([copy.deepcopy(r) for r in rows]))
    EV['fixture_counts'] = {n: run(TDB[n].count_documents({})) for n in H.DATA['collections']}
    EV['cpu0'], EV['rss0_mb'] = time.process_time(), rss_mb()
    yield
    EV['metrics'] = {ep: {'n': len(v['lat_first']), 'first_status': dict(v['first']), 'retry_status': dict(v['retry']), 'final_status': dict(v['final']),
                          'first_ms': {p: pct(v['lat_first'], p) for p in (50, 95, 99, 100)},
                          'experienced_ms': {p: pct(v['lat_exp'], p) for p in (50, 95, 99, 100)},
                          'retried_requests': len(v['lat_retry_extra'])} for ep, v in M.items()}
    EV['fails_5xx'] = FAILS[:20]; EV['non_admission_503'] = NON_ADMISSION_503[:20]
    EV['cpu_total_s'] = round(time.process_time() - EV['cpu0'], 2); EV['rss_end_mb'] = rss_mb()
    EV['maxrss_mb'] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)
    EV['storage_puts'], EV['llm_calls'], EV['distinct_gets'], EV['total_gets'] = H.PUTS, H.LLM_CALLS, len(set(H.GETS)), len(H.GETS)
    EV['leftover_handles'] = H.leftover_real_handles()
    run(H.tdbmod.client.drop_database(H.TEST_DB))
    EV['db_dropped'] = H.TEST_DB not in run(H.tdbmod.client.list_database_names())
    Path('/app/test_reports/iter145_load_evidence.json').write_text(json.dumps(EV, indent=1, default=str))
    print(json.dumps({k: EV[k] for k in ('metrics', 'cpu_total_s', 'rss0_mb', 'rss_end_mb', 'maxrss_mb', 'db_dropped', 'storage_puts', 'llm_calls')}, default=str))


# cold source proof once per paper (Jan large PDF once), then warm reuse by another user
def test_cold_proof_once_per_paper():
    async def go():
        out = {}
        async with client() as c:
            for pid in (P1, P2):
                g0 = len(H.GETS); t = time.perf_counter()
                r = await call(c, 'preflight_cold', 'POST', f'/api/sets/{pid}/preflight', hdr(0 if pid == P1 else 1), {'test_response': 'ok'}, retry=False)
                tc = time.perf_counter() - t; g1 = len(H.GETS)
                r2 = await call(c, 'preflight_warm', 'POST', f'/api/sets/{pid}/preflight', hdr(2 if pid == P1 else 3), {'test_response': 'ok'}, retry=False)
                out[pid] = {'cold': (r.status_code, round(tc, 3), g1 - g0), 'warm': (r2.status_code, round(M['preflight_warm']['lat_first'][-1], 4), len(H.GETS) - g1)}
        return out
    o = run(go()); EV['cold_warm'] = o; print('COLD/WARM', o)
    assert all(v['cold'][0] == 200 and v['cold'][2] == 1 and v['warm'][0] == 200 and v['warm'][2] == 0 for v in o.values()), o


# steady phase: 100 logical students, <=30 concurrent flows; idempotent start/save, out-of-order, submit 60 + results
def test_steady_100_users_30_concurrency():
    sem = asyncio.Semaphore(STEADY); deadline = time.perf_counter() + 70; active = [0]; peak = [0]

    async def flow(c, i):
        async with sem:
            active[0] += 1; peak[0] = max(peak[0], active[0])
            try:
                if time.perf_counter() > deadline: return {'i': i, 'stage': 'not_started_budget'}
                h, pid = hdr(i), (P1 if i % 2 == 0 else P2); s = {'i': i, 'pid': pid, 'acked': {}, 'errors': []}
                r = await call(c, 'catalogue', 'GET', '/api/pyq/jee-main', h); s['cat'] = r.status_code
                r = await call(c, 'preflight', 'POST', f'/api/sets/{pid}/preflight', h, {'test_response': 'ok'})
                if r.status_code != 200: s['errors'].append(('preflight', r.status_code, r.text[:120])); return s
                key = str(uuid.uuid4())
                a, b = await asyncio.gather(*[call(c, 'start', 'POST', f'/api/sets/{pid}/start', h, {'start_key': key, 'device_checked': True}) for _ in range(2)])
                if a.status_code != 200 or b.status_code != 200: s['errors'].append(('start', a.status_code, b.status_code, a.text[:100])); return s
                A, B = J(a), J(b); s['aid'] = A['id']; s['same_start'] = A['id'] == B['id']; s['deadline'] = A['deadline']; s['started_at'] = A['started_at']
                r = await call(c, 'start_resume', 'POST', f'/api/sets/{pid}/start', h, {'start_key': str(uuid.uuid4()), 'device_checked': True})
                s['resume_same'] = r.status_code == 200 and J(r)['id'] == A['id'] and J(r)['deadline'] == A['deadline']
                aid = A['id']; qs = A['questions']; s['n_q'] = len(qs)
                r = await call(c, 'attempt_get', 'GET', f'/api/attempts/{aid}', h); s['get'] = r.status_code
                r = await call(c, 'asset_question', 'GET', f'/api/attempts/{aid}/questions/{qs[i % 10]["id"]}/asset/question/0', h)
                s['asset'] = (r.status_code, r.headers.get('content-type'), len(r.content))
                plan, q0, rev1 = plan_for(i, pid); s['plan'] = dict(plan)
                rid0 = str(uuid.uuid4()); body0 = {'value': rev1, 'revision': 1, 'request_id': rid0}
                r = await call(c, 'save', 'PUT', f'/api/attempts/{aid}/answers/{q0}', h, body0)
                if r.status_code == 200: s['acked'][q0] = (1, rev1)
                else: s['errors'].append(('save0', r.status_code, r.text[:100]))
                for qid, val in plan.items():
                    if qid == q0: continue
                    r = await call(c, 'save', 'PUT', f'/api/attempts/{aid}/answers/{qid}', h, {'value': val, 'revision': 1, 'request_id': str(uuid.uuid4())})
                    if r.status_code == 200: s['acked'][qid] = (1, val)
                    else: s['errors'].append(('save', qid, r.status_code, r.text[:100]))
                r = await call(c, 'save_retry_same', 'PUT', f'/api/attempts/{aid}/answers/{q0}', h, body0)  # same-save replay
                s['dup_same'] = (r.status_code, r.status_code == 200 and J(r).get('duplicate'))
                body2 = {'value': plan[q0], 'revision': 2, 'request_id': str(uuid.uuid4())}
                x, y = await asyncio.gather(*[call(c, 'save_concurrent_same', 'PUT', f'/api/attempts/{aid}/answers/{q0}', h, body2) for _ in range(2)])
                s['conc_same'] = (x.status_code, y.status_code, sorted([bool(J(x).get('duplicate')), bool(J(y).get('duplicate'))]) if x.status_code == y.status_code == 200 else None)
                if 200 in (x.status_code, y.status_code): s['acked'][q0] = (2, plan[q0])
                q1 = next(q for q in plan if q != q0)
                r = await call(c, 'save_out_of_order', 'PUT', f'/api/attempts/{aid}/answers/{q1}', h, {'value': plan[q1], 'revision': 3, 'request_id': str(uuid.uuid4())})
                s['ooo'] = r.status_code
                r = await call(c, 'save_reused_rid', 'PUT', f'/api/attempts/{aid}/answers/{q0}', h, {**body0, 'value': plan[q0] if plan[q0] != rev1 else 'A'})
                s['reuse_rid'] = r.status_code
                if i < N_SUBMIT:
                    r1 = await call(c, 'submit', 'POST', f'/api/attempts/{aid}/submit', h)
                    r2 = await call(c, 'submit_repeat', 'POST', f'/api/attempts/{aid}/submit', h)
                    s['submit'] = (r1.status_code, r2.status_code, (J(r1) or {}).get('receipt') == (J(r2) or {}).get('receipt'))
                    t = time.perf_counter()
                    while time.perf_counter() - t < 30:
                        r = await call(c, 'results', 'GET', f'/api/attempts/{aid}/results', h)
                        if r.status_code != 202: break
                        await asyncio.sleep(float(r.headers.get('retry-after', '1')))
                    s['results_wait_s'] = round(time.perf_counter() - t, 3); s['results'] = r.status_code
                    if r.status_code == 200:
                        R = J(r); s['score'] = R['summary']['score']; s['marks'] = {q['id']: q.get('marks') for q in R['questions']}
                s['stage'] = 'done'; return s
            except Exception as e:
                return {'i': i, 'stage': 'exception', 'exc': repr(e)[:200]}
            finally:
                active[0] -= 1

    async def go():
        async with client() as c:
            t = time.perf_counter(); res = await asyncio.gather(*[flow(c, i) for i in range(N_USERS)])
            return res, round(time.perf_counter() - t, 2), H.app.state.admission.snapshot()
    cpu = time.process_time(); res, wall, snap = run(go()); cpu = round(time.process_time() - cpu, 2)
    ST['flows'] = {s['i']: s for s in res}
    done = [s for s in res if s.get('stage') == 'done']
    EV['steady'] = {'wall_s': wall, 'cpu_s': cpu, 'client_peak_flows': peak[0], 'done': len(done), 'stages': Counter(s.get('stage') for s in res),
                    'flows_per_s': round(len(done) / wall, 2), 'exceptions': [s for s in res if s.get('stage') == 'exception'][:3],
                    'errors': [(s['i'], s['errors'][:3]) for s in res if s.get('errors')][:10],
                    'lanes': {k: {x: v[x] for x in ('limit', 'peak', 'admitted', 'rejected', 'failed', 'in_flight')} for k, v in snap['lanes'].items()},
                    'results_wait_p95_ms': pct([s['results_wait_s'] for s in done if 'results_wait_s' in s], 95)}
    print('STEADY', json.dumps(EV['steady'], default=str))
    assert len(done) == N_USERS, EV['steady']['stages']
    bad = [(s['i'], k) for s in done for k, ok in (('same_start', s['same_start']), ('resume', s['resume_same']), ('n75', s['n_q'] == 75),
           ('asset', s['asset'][0] == 200 and s['asset'][1] == 'image/png'), ('dup', s['dup_same'] == (200, True)), ('ooo', s['ooo'] == 409),
           ('reuse', s['reuse_rid'] == 409), ('conc', s['conc_same'] in ((200, 200, [False, True]), )), ('errors', not s['errors'])) if not ok]
    EV['steady_logic_bad'] = bad[:30]
    assert not bad, bad
    assert not FAILS, FAILS[:5]


# burst: 100 simultaneous requests (40 active-user saves + 60 submitted-user results), then raw read burst w/o retry; tokens released
def test_burst_100_and_post_burst_recovery():
    F = ST['flows']; act = [i for i in F if i >= N_SUBMIT]; sub = [i for i in F if i < N_SUBMIT]
    for i in act:
        pid = F[i]['pid']; q = next(q for q in PAPERS[pid]['questions'] if q['disposition'] == 'standard' and q['id'] not in F[i]['plan'])
        F[i]['burst_q'] = (q['id'], q['answer'])

    async def save(c, i):
        qid, val = F[i]['burst_q']
        r = await call(c, 'burst_save', 'PUT', f'/api/attempts/{F[i]["aid"]}/answers/{qid}', hdr(i), {'value': val, 'revision': 1, 'request_id': str(uuid.uuid4())})
        if r.status_code == 200: F[i]['acked'][qid] = (1, val); F[i]['plan'][qid] = val
        return r.status_code

    async def res(c, i):
        r = await call(c, 'burst_results', 'GET', f'/api/attempts/{F[i]["aid"]}/results', hdr(i))
        return r.status_code, (J(r)['summary']['score'] if r.status_code == 200 else None)

    async def go():
        async with client() as c:
            adm = H.app.state.admission; rej0 = {k: v['rejected'] for k, v in adm.lanes.items()}
            t = time.perf_counter()
            out = await asyncio.gather(*[save(c, i) for i in act], *[res(c, i) for i in sub])
            wall = round(time.perf_counter() - t, 2)
            rej1 = {k: adm.lanes[k]['rejected'] - rej0[k] for k in rej0}
            # raw burst: 100 concurrent GET attempt (read lane), NO retry -> intentional 503 counts
            t = time.perf_counter()
            raw = await asyncio.gather(*[call(c, 'raw_burst_attempt_get', 'GET', f'/api/attempts/{F[i]["aid"]}', hdr(i), retry=False) for i in F])
            raw_wall = round(time.perf_counter() - t, 2)
            inflight = {k: v['in_flight'] for k, v in adm.lanes.items()}
            t = time.perf_counter(); p1 = await c.get('/api/pyq/jee-main', headers=hdr(0)); p2 = await c.get(f'/api/attempts/{F[70]["aid"]}', headers=hdr(70))
            post = (p1.status_code, p2.status_code, round(time.perf_counter() - t, 4))
            return out, wall, rej1, Counter(r.status_code for r in raw), raw_wall, inflight, post, [r.headers.get('retry-after') for r in raw if r.status_code == 503][:1]
    out, wall, rej, raw, raw_wall, inflight, post, ra = run(go())
    scores_same = all(o[1] == F[i].get('score') for o, i in zip(out[len(act):], sub))
    EV['burst'] = {'mixed_wall_s': wall, 'save_final': Counter(out[:len(act)]), 'results_final': Counter(o[0] for o in out[len(act):]),
                   'lane_rejections_during_mixed_burst': rej, 'results_scores_unchanged': scores_same,
                   'raw_read_burst_codes': raw, 'raw_wall_s': raw_wall, 'retry_after': ra, 'in_flight_after': inflight, 'post_burst_first_try': post}
    print('BURST', json.dumps(EV['burst'], default=str))
    assert set(out[:len(act)]) == {200} and all(o[0] == 200 for o in out[len(act):]) and scores_same
    assert set(raw) <= {200, 503} and not FAILS, (raw, FAILS[:3])
    assert all(v == 0 for v in inflight.values()) and post[:2] == (200, 200)


# logic/durability/privacy verification after drain
def test_verify_grades_ownership_durability_privacy():
    F = ST['flows']
    sync = pymongo.MongoClient(H.os.environ['MONGO_URL'])[H.TEST_DB]  # fresh object reopen
    bad = defaultdict(list)
    ids = set()
    for i, s in F.items():
        docs = list(sync.tejas_attempts.find({'user_id': uid(i)}, {'_id': 0, 'id': 1, 'set_id': 1, 'answers': 1, 'status': 1, 'deadline': 1, 'started_at': 1,
                                                                    'command_count': 1, 'ledger': 1, 'user_id': 1}))
        if len(docs) != 1: bad['attempt_count'].append((i, len(docs))); continue
        d = docs[0]; ids.add(d['id'])
        if d['id'] != s['aid'] or d['set_id'] != s['pid']: bad['ownership'].append(i)
        if d['deadline'] != s['deadline'] or abs(d['deadline'] - d['started_at'] - 10800) > 2: bad['timer'].append((i, d['deadline'] - d['started_at']))
        persisted = {q: (v.get('revision'), v.get('normalized_value')) for q, v in (d.get('answers') or {}).items()}
        if persisted != s['acked']: bad['acked_vs_persisted'].append((i, len(persisted), len(s['acked'])))
        if {q: v[1] for q, v in persisted.items()} != s['plan']: bad['final_vs_expected'].append(i)
        if d.get('command_count') != len(s['acked']) + 1: bad['command_count'].append((i, d.get('command_count'), len(s['acked']) + 1))
        if i < N_SUBMIT:
            led = list(sync.tejas_ledgers.find({'id': d['id']}, {'_id': 0}))
            if d['status'] != 'completed' or len(led) != 1: bad['submitted_state'].append((i, d['status'], len(led)))
            elif (led[0].get('summary') or {}).get('score') != s.get('score'): bad['ledger_vs_results'].append((i, (led[0].get('summary') or {}).get('score'), s.get('score')))
            exp, marks = expected(s['pid'], {q: v for q, v in s['plan'].items() if q != F[i].get('burst_q', [None])[0]})
            if s.get('score') != exp: bad['score'].append((i, s.get('score'), exp))
            if s.get('marks') != marks: bad['per_question_marks'].append(i)
        elif d['status'] != 'active': bad['active_state'].append((i, d['status']))
    if len(ids) != N_USERS: bad['distinct_attempts'].append(len(ids))
    jobs = list(sync.tejas_jobs.find({}, {'_id': 0, 'kind': 1, 'status': 1, 'payload': 1}))
    grade = [j for j in jobs if j.get('kind') == 'grade']
    EV['jobs'] = {'total': len(jobs), 'grade': len(grade), 'grade_status': Counter(j.get('status') for j in grade),
                  'distinct_grade_attempts': len({(j.get('payload') or {}).get('attempt_id') for j in grade})}
    EV['score_versions'] = sync.tejas_score_versions.count_documents({}); EV['ledgers'] = sync.tejas_ledgers.count_documents({})

    async def privacy():
        out = Counter(); hist = []
        async with client() as c:
            sem = asyncio.Semaphore(10)
            async def one(i):
                async with sem:
                    j = (i + 1) % N_USERS; s, o = F[i], hdr(j); aid = s['aid']; qid = next(iter(s['plan']))
                    for ep, m, url, body in (('x_get', 'GET', f'/api/attempts/{aid}', None), ('x_results', 'GET', f'/api/attempts/{aid}/results', None),
                                             ('x_save', 'PUT', f'/api/attempts/{aid}/answers/{qid}', {'value': 'A', 'revision': 9, 'request_id': str(uuid.uuid4())}),
                                             ('x_solution', 'GET', f'/api/attempts/{aid}/questions/{qid}/asset/solution/0', None)):
                        r = await call(c, 'privacy_' + ep, m, url, o, body); out[(ep, r.status_code)] += 1
                    if i >= N_SUBMIT:
                        r = await call(c, 'own_active_results', 'GET', f'/api/attempts/{aid}/results', hdr(i)); out[('own_active_results', r.status_code)] += 1
                        r = await call(c, 'own_active_solution', 'GET', f'/api/attempts/{aid}/questions/{qid}/asset/solution/0', hdr(i)); out[('own_active_solution', r.status_code)] += 1
                        r = await call(c, 'own_active_get', 'GET', f'/api/attempts/{aid}', hdr(i))
                        txt = r.text
                        out[('active_answer_leak', any(k in txt for k in ('accepted_answers', 's_refs', '"solution"')))] += 1
                    r = await call(c, 'history', 'GET', '/api/attempts?page=1', hdr(i)); items = J(r)['items']
                    hist.append((len(items), all(x['id'] == aid for x in items)))
                    r = await call(c, 'catalogue_after', 'GET', '/api/pyq/jee-main', hdr(i)); rows = J(r)['items']
                    mine = [p['id'] for p in rows if p.get('attempt') or p.get('attempt_count')]
                    if mine != [s['pid']]: out[('catalogue_privacy_bad', i)] += 1
                    r2 = await call(c, 'history_page_big', 'GET', '/api/attempts?page=99999999', hdr(i)); out[('hist_big', r2.status_code, len(J(r2).get('items', [])) if r2.status_code == 200 else -1)] += 1
            await asyncio.gather(*[one(i) for i in F])
            # immutable ledger/results re-read
            again = [J(await c.get(f'/api/attempts/{F[i]["aid"]}/results', headers=hdr(i)))['summary']['score'] == F[i]['score'] for i in range(0, N_SUBMIT, 6)]
        return out, hist, again
    out, hist, again = run(privacy())
    EV['verify'] = {'bad': dict(bad), 'privacy': {str(k): v for k, v in out.items()}, 'history_ok': {str(k): v for k, v in Counter(hist).items()}, 'results_reread_equal': all(again)}
    print('VERIFY', json.dumps(EV['verify'], default=str), json.dumps(EV['jobs'], default=str))
    assert not bad, dict(bad)
    assert out[('x_get', 404)] == out[('x_results', 404)] == out[('x_save', 404)] == out[('x_solution', 404)] == N_USERS, out
    assert out[('own_active_results', 403)] == out[('own_active_solution', 403)] == N_USERS - N_SUBMIT and out[('active_answer_leak', False)] == N_USERS - N_SUBMIT
    assert hist and all(h == (1, True) for h in hist) and all(again) and not [k for k in out if k[0] == 'catalogue_privacy_bad']
    assert EV['jobs']['grade'] == EV['jobs']['distinct_grade_attempts'] == N_SUBMIT and set(EV['jobs']['grade_status']) == {'done'}
    assert H.PUTS == [] and H.LLM_CALLS == [] and not FAILS


# timer expiry release + concurrent double-submit: late save rejected, auto-finalize, exactly one ledger/grade per attempt
def test_timer_expiry_release_and_concurrent_submit():
    F = ST['flows']; e, d = 99, 98

    async def go():
        async with client() as c:
            await TDB.tejas_attempts.update_one({'id': F[e]['aid'], 'user_id': uid(e)}, {'$set': {'deadline': time.time() - 5}})  # TEST-only clock move
            late = await call(c, 'late_save', 'PUT', f'/api/attempts/{F[e]["aid"]}/answers/{next(iter(F[e]["plan"]))}', hdr(e), {'value': 'A', 'revision': 9, 'request_id': str(uuid.uuid4())})
            q = next(q for q in PAPERS[F[e]['pid']]['questions'] if q['disposition'] == 'standard' and q['id'] not in F[e]['plan'])
            late2 = await call(c, 'late_save', 'PUT', f'/api/attempts/{F[e]["aid"]}/answers/{q["id"]}', hdr(e), {'value': q['answer'], 'revision': 1, 'request_id': str(uuid.uuid4())})
            subs = await asyncio.gather(*[call(c, 'submit_concurrent', 'POST', f'/api/attempts/{F[d]["aid"]}/submit', hdr(d)) for _ in range(3)])
            out = {}
            for i in (e, d):
                t = time.perf_counter()
                while time.perf_counter() - t < 30:
                    r = await call(c, 'results', 'GET', f'/api/attempts/{F[i]["aid"]}/results', hdr(i))
                    if r.status_code != 202: break
                    await asyncio.sleep(float(r.headers.get('retry-after', '1')))
                R = J(r); out[i] = (r.status_code, R.get('reason'), R['summary']['score'] if r.status_code == 200 else None,
                                    await TDB.tejas_ledgers.count_documents({'id': F[i]['aid']}), await TDB.tejas_jobs.count_documents({'payload.attempt_id': F[i]['aid']}))
            return late.status_code, late2.status_code, late2.text[:100], [s.status_code for s in subs], len({(J(s) or {}).get('receipt', {}).get('hash') if isinstance((J(s) or {}).get('receipt'), dict) else str((J(s) or {}).get('receipt')) for s in subs}), out
    o = run(go()); EV['timer_release'] = o; print('TIMER', o)
    late, late2, _, subs, receipts, out = o
    assert late == 409 and late2 == 409 and set(subs) <= {200, 202} and receipts == 1, o
    for i in (e, d):
        exp, _ = expected(F[i]['pid'], F[i]['plan'])
        assert out[i][0] == 200 and out[i][2] == exp and out[i][3] == 1 and out[i][4] == 1, (i, out[i], exp)
    assert out[e][1] == 'time_limit'
