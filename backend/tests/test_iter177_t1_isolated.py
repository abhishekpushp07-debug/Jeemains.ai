"""TEST-ONLY iteration 177 (T1 testing agent): independent gap regression for the scale/integrity change against the REAL
ASGI app + REAL cookie auth in a disposable isolated DB (dropped at the end). Customer DB never touched.
Covers: native envelope, attempt_view leak, shared pack per revision, PIN change/owner reset cache eviction, owner
integrity endpoints (shape/409/403/401), report-only checks untouched, waiting/failed regrade, second run clean,
leaderboard ties 100,90,90,80 + no private data, security headers + origin_denied, run_job return value.
Run: python test_iter177_t1_isolated.py"""
import asyncio, copy, os, secrets, sys, time, uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ['TEJAS_ISO_DB'] = 'tejas_isolated_t1iter177_' + secrets.token_hex(3)
import iso_harness_scale176 as H  # noqa: E402
import httpx  # noqa: E402

TDB, PID = H.TDB, 'jee-main-pyq-2025-04-02-s1'
RESULTS = []
LEAK = {'answer', 'correct', 'correct_option', 'solution', 'ai_solution', 'explanation', 's_refs', 'answer_key', 'key'}


def check(name, ok, info=''):
    RESULTS.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(info)[:400]), flush=True)


def env(r):
    j = r.json(); return isinstance(j, dict) and {'data', 'error', 'meta'} <= set(j)


def D(r):
    return r.json()['data']


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.client.drop_database(H.TEST_DB); await H.tdbmod.indexes()
    for name, rows in H.DATA['collections'].items():
        await TDB[name].insert_many([copy.deepcopy(r) for r in rows])
    from tejas import auth, integrity, jobs as J_
    opw = secrets.token_urlsafe(16); oemail = f'test_owner_{secrets.token_hex(3)}@example.com'
    await TDB.tejas_users.insert_one({'id': 'TEST_OWNER177', 'email': oemail, 'name': 'TEST owner', 'role': 'owner',
                                      'password_hash': auth.hashpw(opw), 'created_at': time.time()})
    T = httpx.ASGITransport(app=H.app, raise_app_exceptions=False)
    origin = os.environ['FRONTEND_URL'].rstrip('/')
    async with httpx.AsyncClient(transport=T, base_url='https://api.test.example', timeout=120, headers={'Origin': origin}) as c:
        # --- native contract: signup / login / me envelope
        phones = ['+9199177%05d' % k for k in range(4)]
        jars = []
        for p in phones:
            r = await c.post('/api/auth/phone/signup', json={'phone': p, 'pin': '2468', 'confirm_pin': '2468'})
            jars.append(dict(r.cookies)); c.cookies.clear()
        check('signup envelope + cookie', r.status_code == 200 and env(r) and 'access_token' in jars[-1], r.text[:200])
        r = await c.post('/api/auth/phone', json={'phone': phones[0], 'pin': '2468'}); jar0 = dict(r.cookies); c.cookies.clear()
        check('phone login envelope', r.status_code == 200 and env(r) and 'access_token' in jar0, r.text[:200])
        r = await c.post('/api/auth/phone', json={'phone': phones[0], 'pin': '0000'}); c.cookies.clear()
        check('wrong pin rejected with envelope', r.status_code in (400, 401, 403) and env(r) and r.json()['error'], r.status_code)
        r = await c.get('/api/auth/me', cookies=jar0)
        me = D(r)
        check('/auth/me envelope + no hashes', r.status_code == 200 and env(r) and 'pin_hash' not in me and 'password_hash' not in me, r.text[:200])
        # --- preflight/start/attempt_view
        r = await c.post(f'/api/sets/{PID}/preflight', json={'test_response': 'ok'}, cookies=jars[0])
        check('preflight envelope ok', r.status_code == 200 and env(r) and D(r)['ok'] is True, r.text[:200])
        r = await c.post(f'/api/sets/{PID}/start', json={'start_key': str(uuid.uuid4()), 'device_checked': True}, cookies=jars[0])
        A = D(r); aid = A['id']
        qkeys = set().union(*[set(q) for q in A['questions']])
        check('start envelope + 75 questions + no answer/solution fields', r.status_code == 200 and env(r) and len(A['questions']) == 75 and not (qkeys & LEAK) and 'pack_id' not in A and 'response_schema' not in A, sorted(qkeys))
        await c.post(f'/api/sets/{PID}/preflight', json={'test_response': 'ok'}, cookies=jars[1])
        r2 = await c.post(f'/api/sets/{PID}/start', json={'start_key': str(uuid.uuid4()), 'device_checked': True}, cookies=jars[1])
        a1 = await TDB.tejas_attempts.find_one({'id': aid}); a2 = await TDB.tejas_attempts.find_one({'id': D(r2)['id']})
        check('same revision -> same pack_id for two students, identical public questions', a1['pack_id'] == a2['pack_id'] and D(r2)['questions'] == A['questions'])
        # bad source ref after revision change must be rejected by preflight
        good = await TDB.tejas_sets.find_one({'id': PID}, {'questions': {'$slice': 1}, 'revision': 1})
        await TDB.tejas_sets.update_one({'id': PID}, {'$set': {'questions.0.q_refs.0.file_id': 'TEST_bogus_file'}, '$inc': {'revision': 1}})
        r = await c.post(f'/api/sets/{PID}/preflight', json={'test_response': 'ok'}, cookies=jars[2])
        check('preflight rejects bad source ref after edit (400)', r.status_code == 400 and env(r), (r.status_code, r.text[:200]))
        await TDB.tejas_sets.update_one({'id': PID}, {'$set': {'questions.0.q_refs': good['questions'][0]['q_refs']}, '$inc': {'revision': 1}})
        r = await c.post(f'/api/sets/{PID}/preflight', json={'test_response': 'ok'}, cookies=jars[2])
        check('preflight ok again after restoring refs', r.status_code == 200, r.text[:200])
        # --- save / submit / result envelope
        mcq = [q for q in A['questions'] if q['type'] == 'mcq']
        r = await c.put(f'/api/attempts/{aid}/answers/{mcq[0]["id"]}', json={'value': sorted(mcq[0]['options'])[0], 'revision': 1, 'request_id': str(uuid.uuid4())}, cookies=jars[0])
        check('answer save envelope + accepted receipt', r.status_code == 200 and env(r) and D(r)['accepted']['revision'] == 1, r.text[:200])
        r = await c.put(f'/api/attempts/{aid}/answers/{mcq[0]["id"]}', json={'value': sorted(mcq[0]['options'])[1], 'revision': 1, 'request_id': str(uuid.uuid4())}, cookies=jars[0])
        check('stale revision save -> 409 envelope', r.status_code == 409 and env(r), r.status_code)
        r = await c.put(f'/api/attempts/{aid}/answers/{mcq[0]["id"]}', json={'value': 'A', 'revision': 2, 'request_id': str(uuid.uuid4())}, cookies=jars[1])
        check('other student cannot save into my attempt', r.status_code in (403, 404), r.status_code)
        r = await c.post(f'/api/attempts/{aid}/submit', cookies=jars[0])
        check('submit envelope + receipt', r.status_code in (200, 202) and env(r) and D(r).get('receipt'), r.text[:200])
        await J_.drain_lane('grade')
        r = await c.get(f'/api/attempts/{aid}/results', cookies=jars[0])
        check('results envelope + summary', r.status_code == 200 and env(r) and 'summary' in str(D(r))[:5000], r.text[:200])
        r = await c.get(f'/api/attempts/{aid}/results', cookies=jars[1])
        check('other student cannot read my results', r.status_code in (403, 404), r.status_code)
        # --- PIN change evicts cache immediately
        cookie = jars[2]
        assert (await c.get('/api/auth/me', cookies=cookie)).status_code == 200
        r = await c.post('/api/auth/pin', json={'phone': phones[2], 'new_pin': '1357', 'confirm_pin': '1357'}, cookies=cookie); new2 = dict(r.cookies); c.cookies.clear()
        old = await c.get('/api/auth/me', cookies=cookie)
        check('PIN change -> old cookie 401 immediately, new cookie works', r.status_code == 200 and old.status_code == 401 and (await c.get('/api/auth/me', cookies=new2)).status_code == 200, (r.status_code, old.status_code))
        # --- owner login + owner PIN reset evicts cache
        r = await c.post('/api/auth/login', json={'email': oemail, 'password': opw}); ojar = dict(r.cookies); c.cookies.clear()
        check('isolated owner login', r.status_code == 200 and 'access_token' in ojar, r.text[:200])
        cookie = jars[3]
        assert (await c.get('/api/auth/me', cookies=cookie)).status_code == 200
        prof = await TDB.tejas_phone_profiles.find_one({'phone': phones[3]})
        r = await c.post('/api/auth/owner/student-pin-reset', json={'phone': phones[3], 'new_pin': '9753', 'confirm_pin': '9753', 'expected_pin_version': prof.get('pin_version', 0)}, cookies=ojar)
        old = await c.get('/api/auth/me', cookies=cookie)
        check('owner PIN reset -> student old cookie 401 immediately', r.status_code == 200 and old.status_code == 401, (r.status_code, r.text[:200], old.status_code))
        # --- integrity endpoints
        r = await c.get('/api/admin/integrity', cookies=ojar)
        g = D(r) if r.status_code == 200 else {}
        check('owner GET integrity shape {report,running,schedule}', r.status_code == 200 and env(r) and set(g) >= {'report', 'running', 'schedule'} and g['running'] is False, r.text[:200])
        r = await c.post('/api/admin/integrity/run', cookies=jars[0])
        check('student POST run -> 403', r.status_code == 403, r.status_code)
        c.cookies.clear()
        r = await c.post('/api/admin/integrity/run')
        check('anonymous POST run -> 401', r.status_code == 401, r.status_code)
        await TDB.tejas_operations.update_one({'_id': 'integrity-lock'}, {'$set': {'until': time.time() + 60}}, upsert=True)
        r = await c.post('/api/admin/integrity/run', cookies=ojar)
        g = D(await c.get('/api/admin/integrity', cookies=ojar))
        check('POST run while running -> 409 and GET running=true', r.status_code == 409 and g['running'] is True, (r.status_code, g.get('running')))
        r = await c.post('/api/admin/integrity/run', cookies=ojar)
        run_lock = await TDB.tejas_operations.find_one({'_id': 'integrity-lock'})
        await TDB.tejas_operations.update_one({'_id': 'integrity-lock'}, {'$set': {'until': 0}})
        # seed waiting / failed / report-only problems
        a2id = a2['id']
        await c.post(f'/api/attempts/{a2id}/submit', cookies=jars[1]); await J_.drain_lane('grade')
        await TDB.tejas_attempts.update_one({'id': aid}, {'$set': {'grading_status': 'failed'}})
        await TDB.tejas_attempts.update_one({'id': a2id}, {'$set': {'grading_status': 'queued'}})
        await TDB.tejas_jobs.update_one({'id': 'grade-' + aid}, {'$set': {'status': 'failed', 'attempts': 3}})
        bad = {'id': 'TEST_before_start', 'user_id': me['id'], 'set_id': PID, 'mode': 'retry', 'start_key': 'TEST_bs', 'status': 'completed',
               'grading_status': 'ready', 'started_at': 2000, 'submitted_at': 1000, 'deadline': 0, 'summary': {'score_exact': '0'}}
        await TDB.tejas_attempts.insert_one(dict(bad)); await TDB.tejas_ledgers.insert_one({'id': 'TEST_before_start', 'summary': {'score_exact': '0'}})
        before_bad = await TDB.tejas_attempts.find_one({'id': 'TEST_before_start'}, {'_id': 0})
        rep = await integrity.run('test')
        by = {x['key']: x for x in rep['checks']}
        check('score_failed found and fixed', by['score_failed']['found'] == 1 and by['score_failed']['fixed'] == 1, by['score_failed'])
        check('waiting_for_score found and regraded', by['waiting_for_score']['found'] >= 1 and by['waiting_for_score']['fixed'] >= 1, by['waiting_for_score'])
        check('submitted_before_start reported, record untouched', by['submitted_before_start']['found'] == 1 and by['submitted_before_start']['state'] == 'needs_attention'
              and await TDB.tejas_attempts.find_one({'id': 'TEST_before_start'}, {'_id': 0}) == before_bad, by['submitted_before_start'])
        check('report counts only (no ids/phones in report)', 'TEST_before_start' not in str(rep) and phones[0] not in str(rep) and me['id'] not in str(rep))
        await J_.drain_lane('grade')
        x1 = await TDB.tejas_attempts.find_one({'id': aid}); x2 = await TDB.tejas_attempts.find_one({'id': a2id})
        check('both regraded attempts end ready', x1['grading_status'] == 'ready' and x2['grading_status'] == 'ready', (x1['grading_status'], x2['grading_status']))
        rep2 = await integrity.run('test')
        check('second run: nothing left to repair', all(x['found'] == 0 for x in rep2['checks'] if x['action'] == 'repair') and rep2['fixed'] == 0, [x for x in rep2['checks'] if x['found'] and x['action'] == 'repair'])
        g = D(await c.get('/api/admin/integrity', cookies=ojar))
        check('GET returns persisted last report', g['report'] and g['report']['last_run'] == rep2['last_run'] and g['running'] is False)
        # --- leaderboard 100,90,90,80 + no private data
        CID = 'TEST_COMP177'
        await TDB.tejas_sets.insert_one({'id': CID, 'title': 'TEST comp', 'exam': 'JEE Main', 'competition': True, 'questions': [{'id': 'x'}], 'rules': {'minutes': 60},
                                         'start_at': time.time() - 7200, 'end_at': time.time() - 60, 'live_enabled': True})
        uids = [(await TDB.tejas_phone_profiles.find_one({'phone': p}))['id'] for p in phones]
        scores = [100, 90, 90, 80]
        await TDB.tejas_attempts.insert_many([{'id': f'TEST_LB_{k}', 'user_id': uids[k], 'set_id': CID, 'mode': 'practice', 'competition_ranked': True, 'competition_end': 1,
                                               'status': 'completed', 'grading_status': 'ready', 'summary': {'score': v, 'score_exact': str(v), 'accuracy': 50}, 'start_key': 'lb%d' % k} for k, v in enumerate(scores)])
        r = await c.get(f'/api/competitions/{CID}', cookies=jars[2] if False else new2)
        lb = D(r)
        check('leaderboard ranks 1,2,2,4 and you=rank 2 (caller scored 90)', [x['rank'] for x in lb['rows']] == [1, 2, 2, 4] and lb['you']['rank'] == 2, lb)
        check('leaderboard rows carry no phone/user ids', not any(p in str(lb) for p in phones) and not any(u in str(lb['rows']) for u in uids), lb['rows'][:2])
        r = await c.get(f'/api/competitions/{CID}', cookies=jar0)
        check('cached leaderboard gives each caller their own you row', D(r)['you']['rank'] == 1, D(r).get('you'))
        # --- security headers + origin guard
        need = {'x-request-id', 'x-content-type-options', 'referrer-policy', 'x-frame-options', 'permissions-policy', 'cache-control', 'server-timing'}
        for path in ('/api/health', '/api/nope-404', '/api/auth/me'):
            r = await c.get(path)
            check(f'security headers on {path} ({r.status_code})', need <= set(r.headers) and r.headers['x-frame-options'] == 'DENY' and r.headers['x-content-type-options'] == 'nosniff'
                  and r.headers['referrer-policy'] == 'same-origin' and 'no-store' in r.headers['cache-control'], sorted(need - set(r.headers)))
        r = await c.post('/api/auth/phone', json={'phone': phones[0], 'pin': '2468'}, headers={'Origin': 'https://evil.example'})
        j = r.json()
        check('cross-origin POST -> 403 origin_denied, request id matches', r.status_code == 403 and j['error']['code'] == 'origin_denied'
              and r.headers.get('x-request-id') and r.headers['x-request-id'] in str(j), (r.status_code, j, r.headers.get('x-request-id')))
        r = await c.request('DELETE', '/api/auth/logout', headers={'Origin': 'https://evil.example'})
        check('cross-origin DELETE -> 403', r.status_code == 403, r.status_code)
        r = await c.get('/api/health', headers={'Origin': 'https://evil.example'})
        check('cross-origin GET not blocked', r.status_code == 200)
        r = await c.post('/api/auth/phone', json={'phone': phones[0], 'pin': '2468'}, headers={'Origin': origin}); c.cookies.clear()
        check('allowed-origin POST passes', r.status_code == 200, r.status_code)
        # --- run_job return value
        check('run_job unknown id -> not True', await J_.run_job('TEST_nope') is not True)
        await TDB.tejas_jobs.insert_one({'id': 'TEST_done_job', 'kind': 'grade', 'status': 'done', 'user_id': 'x', 'set_id': PID, 'payload': {'attempt_id': aid}, 'attempts': 1, 'created_at': time.time()})
        check('run_job already-done job -> not True', await J_.run_job('TEST_done_job') is not True)
        await TDB.tejas_attempts.update_one({'id': aid}, {'$set': {'grading_status': 'queued'}})
        await TDB.tejas_jobs.update_one({'id': 'grade-' + aid}, {'$set': {'status': 'queued', 'attempts': 0, 'next_run_at': 0}})
        res = await J_.run_job('grade-' + aid)
        check('run_job queued grade job -> True', res is True, res)
    for t in list(integrity._tasks):
        await t
    check('no storage writes / LLM calls', not H.PUTS and not H.LLM_CALLS, (H.PUTS[:3], H.LLM_CALLS[:3]))
    await H.tdbmod.client.drop_database(H.TEST_DB)
    check('isolated database dropped', H.TEST_DB not in await H.tdbmod.client.list_database_names())
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        import pymongo
        from dotenv import dotenv_values
        cl = pymongo.MongoClient(dotenv_values(H.BACKEND / '.env')['MONGO_URL'])
        if H.TEST_DB in cl.list_database_names():
            cl.drop_database(H.TEST_DB); print('cleanup: dropped', H.TEST_DB)
