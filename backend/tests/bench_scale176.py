"""TEST-ONLY iteration 176 'everyone at once' exam benchmark against the REAL ASGI app (all middleware + AdmissionGate)
in a disposable isolated DB. REAL cookie/JWT/session auth (sessions + phone profiles inserted directly, no bcrypt per user).
Storage GET -> local original PDFs; storage writes and LLM forbidden. Customer DB never touched; DB dropped at the end.
Single process + in-process httpx client + co-located Mongo: per-request CPU/latency evidence, NOT a fleet capacity claim.
Env: N (students, default 1000), C (client concurrency, default 64), SAVES (per student, default 20), LOGINS (default 40).
"""
import asyncio, copy, json, os, resource, secrets, sys, time, uuid
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault('TEJAS_ISO_DB', 'tejas_isolated_scale176_' + secrets.token_hex(3))
import iso_harness_scale176 as H  # noqa: E402
import httpx  # noqa: E402

N, C = int(os.environ.get('N', 1000)), int(os.environ.get('C', 64))
SAVES, LOGINS = int(os.environ.get('SAVES', 20)), int(os.environ.get('LOGINS', 40))
PID = 'jee-main-pyq-2025-04-02-s1'
TDB = H.TDB
OUT = {'N': N, 'C': C, 'SAVES': SAVES, 'db': H.TEST_DB}


def pct(xs, p):
    if not xs: return None
    xs = sorted(xs); return round(xs[min(len(xs) - 1, int(round(p / 100 * (len(xs) - 1))))] * 1000, 1)


def J(r):
    j = r.json(); return j.get('data') if isinstance(j, dict) and 'data' in j and 'meta' in j else j


async def burst(name, jobs, conc=C, retry=True):
    """Run coroutine factories with bounded concurrency; honest first-try + final status accounting."""
    sem = asyncio.Semaphore(conc); lat, first, final, retried = [], Counter(), Counter(), [0]
    async def one(make):
        async with sem:
            t0 = time.perf_counter(); n = 0
            while True:
                t = time.perf_counter(); r = await make(); dt = time.perf_counter() - t
                if n == 0: first[r.status_code] += 1
                if retry and r.status_code in (429, 503) and n < 30:
                    n += 1; retried[0] += 1; await asyncio.sleep(min(2.0, float(r.headers.get('retry-after', '1'))) * (0.5 + secrets.randbelow(100) / 100)); continue
                final[r.status_code] += 1; lat.append(time.perf_counter() - t0); return r
    cpu, t = time.process_time(), time.perf_counter()
    res = await asyncio.gather(*[one(m) for m in jobs])
    wall, cpu = time.perf_counter() - t, time.process_time() - cpu
    OUT[name] = {'n': len(jobs), 'wall_s': round(wall, 2), 'rps': round(len(jobs) / wall, 1), 'cpu_ms_per_req': round(1000 * cpu / max(1, len(jobs)), 2),
                 'first': dict(first), 'final': dict(final), 'retries': retried[0], 'p50_ms': pct(lat, 50), 'p95_ms': pct(lat, 95), 'p99_ms': pct(lat, 99), 'max_ms': pct(lat, 100)}
    print(name, json.dumps(OUT[name]), flush=True)
    return res


async def main():
    assert not H.leftover_real_handles(), H.leftover_real_handles()
    await H.tdbmod.client.drop_database(H.TEST_DB); await H.tdbmod.indexes()
    for name, rows in H.DATA['collections'].items():
        await TDB[name].insert_many([copy.deepcopy(r) for r in rows])
    from tejas import auth
    pin_hash = auth.hashpw('1234'); stamp = time.time(); exp = datetime.now(timezone.utc) + timedelta(days=1)
    users, sess, cookies = [], [], []
    for i in range(N + LOGINS):
        uid = 'TEST_U176_%06d' % i
        users.append({'_id': uid, 'id': uid, 'phone': '+91990%07d' % i, 'name': 'TEST L%d' % i, 'role': 'student', 'exam': 'JEE Main',
                      'access_type': 'unverified_phone', 'pin_hash': pin_hash, 'pin_version': 1, 'created_at': stamp, 'consent_at': stamp, 'last_seen_at': stamp})
        if i < N:
            sid = str(uuid.uuid4()); sess.append({'id': sid, 'user_id': uid, 'access_type': 'unverified_phone', 'pin_version': 1, 'expires_at': exp})
            cookies.append({'access_token': auth.token(users[-1], sid, 'access', 7200)})
    await TDB.tejas_phone_profiles.insert_many(users); await TDB.tejas_sessions.insert_many(sess)
    limits = httpx.Limits(max_connections=None, max_keepalive_connections=None)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=H.app, raise_app_exceptions=False), base_url='https://api.test.example', timeout=120, limits=limits) as c:
        def req(i, method, url, body=None):
            return lambda: c.request(method, url, json=body, cookies=cookies[i])
        r = await c.post(f'/api/sets/{PID}/preflight', json={'test_response': 'ok'}, cookies=cookies[0]); OUT['cold_preflight'] = r.status_code
        await burst('me', [req(i, 'GET', '/api/auth/me') for i in range(N)])
        await burst('preflight', [req(i, 'POST', f'/api/sets/{PID}/preflight', {'test_response': 'ok'}) for i in range(N)])
        keys = [str(uuid.uuid4()) for _ in range(N)]
        res = await burst('start', [req(i, 'POST', f'/api/sets/{PID}/start', {'start_key': keys[i], 'device_checked': True}) for i in range(N)])
        att = [J(r) if r.status_code == 200 else None for r in res]
        OUT['start_ok'] = sum(a is not None for a in att)
        res = await burst('start_resume_same_key', [req(i, 'POST', f'/api/sets/{PID}/start', {'start_key': keys[i], 'device_checked': True}) for i in range(min(N, 200))])
        OUT['resume_same_attempt'] = sum(r.status_code == 200 and J(r)['id'] == att[i]['id'] for i, r in enumerate(res))
        jobs, expect = [], {}
        for i, a in enumerate(att):
            if not a: continue
            qs = [q for q in a['questions'] if q['type'] == 'mcq'][:SAVES]
            for k, q in enumerate(qs):
                v = sorted(q['options'])[(i + k) % len(q['options'])] if isinstance(q['options'], (list, dict)) else 'A'
                expect.setdefault(a['id'], {})[q['id']] = v
                jobs.append(req(i, 'PUT', f"/api/attempts/{a['id']}/answers/{q['id']}", {'value': v, 'revision': 1, 'request_id': str(uuid.uuid4())}))
        await burst('save', jobs)
        await burst('status_poll', [req(i, 'GET', f"/api/attempts/{a['id']}/status") for i, a in enumerate(att) if a])
        await burst('visit', [req(i, 'POST', f"/api/attempts/{a['id']}/visit", {'question_id': a['questions'][-1]['id']}) for i, a in enumerate(att) if a])
        await burst('submit', [req(i, 'POST', f"/api/attempts/{a['id']}/submit") for i, a in enumerate(att) if a])
        from tejas import jobs as J_
        t, cpu = time.perf_counter(), time.process_time()
        while await TDB.tejas_attempts.count_documents({'status': 'completed', 'grading_status': {'$ne': 'ready'}}):
            await J_.drain_lane('grade')
            if time.perf_counter() - t > 900: break
        g = await TDB.tejas_attempts.count_documents({'grading_status': 'ready'})
        OUT['grade_drain'] = {'graded': g, 'wall_s': round(time.perf_counter() - t, 2), 'cpu_ms_per_grade': round(1000 * (time.process_time() - cpu) / max(1, g), 2)}
        print('grade_drain', OUT['grade_drain'], flush=True)
        wrong = 0
        async for a in TDB.tejas_attempts.find({}, {'_id': 0, 'id': 1, 'answers': 1}):
            got = {q: v.get('normalized_value') for q, v in a.get('answers', {}).items()}
            wrong += got != expect.get(a['id'], {})
        OUT['answers_mismatch_attempts'] = wrong
        # competition-style leaderboard and cohort with N graded attempts
        await TDB.tejas_sets.update_one({'id': PID}, {'$set': {'competition': True, 'start_at': stamp - 7200, 'end_at': time.time() - 1, 'live_enabled': True}})
        await TDB.tejas_attempts.update_many({}, {'$set': {'competition_ranked': True}})
        await burst('leaderboard', [req(i, 'GET', f'/api/competitions/{PID}') for i in range(min(N, 50))], conc=10)
        await burst('results', [req(i, 'GET', f"/api/attempts/{a['id']}/results") for i, a in enumerate(att[:min(N, 50)]) if a], conc=10)
        t = time.perf_counter(); r = await c.get(f"/api/attempts/{att[0]['id']}/cohort", cookies=cookies[0])
        OUT['cohort_first_ms'] = round(1000 * (time.perf_counter() - t), 1)
        t = time.perf_counter()
        from tejas import cohorts
        cid = cohorts.identity(await TDB.tejas_attempts.find_one({'id': att[0]['id']}))
        job = await TDB.tejas_jobs.find_one({'kind': 'cohort'}, sort=[('created_at', -1)])
        try:
            if job: await J_.run_job(job['id'], drain=False)
        except Exception as e:
            OUT['cohort_error'] = repr(e)[:200]
        snap = await TDB.tejas_cohort_snapshots.find_one({'id': cid}, {'_id': 0, 'sample_size': 1})
        OUT['cohort_refresh'] = {'wall_s': round(time.perf_counter() - t, 2), 'sample': (snap or {}).get('sample_size'), 'entries': await TDB.tejas_cohort_entries.count_documents({})}
        print('cohort', OUT['cohort_refresh'], flush=True)
        await burst('login_bcrypt', [lambda i=i: c.post('/api/auth/phone', json={'phone': '+91990%07d' % (N + i), 'pin': '1234'}) for i in range(LOGINS)])
    OUT['attempt_doc_avg_bytes'] = (await TDB.command('collStats', 'tejas_attempts'))['avgObjSize']
    OUT['admission'] = {k: {x: v[x] for x in ('limit', 'peak', 'admitted', 'rejected', 'failed')} for k, v in H.app.state.admission.snapshot()['lanes'].items()}
    OUT['maxrss_mb'] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)
    OUT['storage_puts'], OUT['llm_calls'] = len(H.PUTS), len(H.LLM_CALLS)
    await H.tdbmod.client.drop_database(H.TEST_DB)
    OUT['db_dropped'] = H.TEST_DB not in await H.tdbmod.client.list_database_names()
    tag = os.environ.get('TAG', 'baseline')
    Path(f'/app/test_reports/bench_scale176_{tag}_N{N}.json').write_text(json.dumps(OUT, indent=1, default=str))
    print('DONE', json.dumps({k: OUT[k] for k in ('start_ok', 'resume_same_attempt', 'answers_mismatch_attempts', 'db_dropped')}))


if __name__ == '__main__':
    asyncio.run(main())
