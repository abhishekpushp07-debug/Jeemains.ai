"""TEST-ONLY iteration 176: race-condition + integrity-repair regression suite against the REAL ASGI app and REAL cookie
auth in a disposable isolated DB (dropped at the end). Customer DB never touched. Run: python test_integrity176_isolated.py"""
import asyncio, copy, os, secrets, sys, time, uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ['TEJAS_ISO_DB'] = 'tejas_isolated_integrity176_' + secrets.token_hex(3)
import iso_harness_scale176 as H  # noqa: E402
import httpx  # noqa: E402

TDB, PID = H.TDB, 'jee-main-pyq-2025-04-02-s1'
RESULTS = []


def check(name, ok, info=''):
    RESULTS.append(ok); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(info)[:300]), flush=True)


def J(r):
    j = r.json(); return j.get('data') if isinstance(j, dict) and 'data' in j and 'meta' in j else j


async def student(i, pin_hash):
    from tejas import auth
    uid = 'TEST_U176I_%04d' % i; stamp = time.time()
    u = {'_id': uid, 'id': uid, 'phone': '+91991%07d' % i, 'name': 'TEST', 'role': 'student', 'exam': 'JEE Main', 'access_type': 'unverified_phone',
         'pin_hash': pin_hash, 'pin_version': 1, 'created_at': stamp, 'consent_at': stamp, 'last_seen_at': stamp}
    sid = str(uuid.uuid4())
    await TDB.tejas_phone_profiles.insert_one(u)
    await TDB.tejas_sessions.insert_one({'id': sid, 'user_id': uid, 'access_type': 'unverified_phone', 'pin_version': 1, 'expires_at': datetime.now(timezone.utc) + timedelta(days=1)})
    return uid, {'access_token': auth.token(u, sid, 'access', 3600)}


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.client.drop_database(H.TEST_DB); await H.tdbmod.indexes()
    for name, rows in H.DATA['collections'].items():
        await TDB[name].insert_many([copy.deepcopy(r) for r in rows])
    from tejas import auth, integrity, jobs as J_
    pin = auth.hashpw('1234')
    S = [await student(i, pin) for i in range(12)]
    T = httpx.ASGITransport(app=H.app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=T, base_url='https://api.test.example', timeout=120) as c:
        def go(i, method, url, body=None):
            return c.request(method, url, json=body, cookies=S[i][1])
        assert (await go(0, 'POST', f'/api/sets/{PID}/preflight', {'test_response': 'ok'})).status_code == 200
        # T1/T2 start races
        rs = await asyncio.gather(*[go(0, 'POST', f'/api/sets/{PID}/start', {'start_key': str(uuid.uuid4()), 'device_checked': True}) for _ in range(20)])
        ids = {J(r)['id'] for r in rs if r.status_code == 200}
        check('20 concurrent starts by one student -> one open attempt', len(ids) == 1 and await TDB.tejas_attempts.count_documents({'user_id': S[0][0], 'status': 'active'}) == 1, [r.status_code for r in rs])
        key = str(uuid.uuid4()); await go(1, 'POST', f'/api/sets/{PID}/preflight', {'test_response': 'ok'})
        rs = await asyncio.gather(*[go(1, 'POST', f'/api/sets/{PID}/start', {'start_key': key, 'device_checked': True}) for _ in range(10)])
        check('10 concurrent identical start retries -> same attempt', len({J(r)['id'] for r in rs if r.status_code == 200}) == 1 and all(r.status_code == 200 for r in rs), [r.status_code for r in rs])
        A = J(rs[0]); aid = A['id']
        full = await TDB.tejas_attempts.find_one({'id': aid})
        check('started attempt stores the shared frozen pack and full answer schema', bool(full.get('pack_id')) and len(full['response_schema']) == len(A['questions']) == 75 and await TDB.tejas_packs.count_documents({'_id': full['pack_id']}) == 1)
        mcq = [q for q in A['questions'] if q['type'] == 'mcq']
        q0 = mcq[0]['id']; opts = sorted(mcq[0]['options'])
        # T3 different saves racing on the same revision
        rs = await asyncio.gather(*[go(1, 'PUT', f'/api/attempts/{aid}/answers/{q0}', {'value': opts[k % len(opts)], 'revision': 1, 'request_id': str(uuid.uuid4())}) for k in range(20)])
        ok = [r for r in rs if r.status_code == 200]
        stored = (await TDB.tejas_attempts.find_one({'id': aid}, {'answers': 1}))['answers'][q0]
        check('20 racing first saves of one question -> exactly one accepted, rest rejected', len(ok) == 1 and all(r.status_code == 409 for r in rs if r.status_code != 200) and stored['revision'] == 1 and stored['value'] == J(ok[0])['accepted']['value'], [r.status_code for r in rs])
        body = {'value': opts[0], 'revision': 2, 'request_id': str(uuid.uuid4())}
        rs = await asyncio.gather(*[go(1, 'PUT', f'/api/attempts/{aid}/answers/{q0}', body) for _ in range(10)])
        accepted = {J(r)['accepted']['server_seq'] for r in rs if r.status_code == 200}
        check('10 identical save retries -> one stored change, same receipt for all', all(r.status_code == 200 for r in rs) and len(accepted) == 1 and sum(not J(r)['duplicate'] for r in rs) == 1, [r.status_code for r in rs])
        for q in mcq[1:6]:
            await go(1, 'PUT', f'/api/attempts/{aid}/answers/{q["id"]}', {'value': sorted(q['options'])[0], 'revision': 1, 'request_id': str(uuid.uuid4())})
        # T5 submit race + grading
        rs = await asyncio.gather(*[go(1, 'POST', f'/api/attempts/{aid}/submit') for _ in range(10)])
        check('10 racing submits -> one sealed receipt and one scoring job', len({J(r)['receipt'] for r in rs if r.status_code in (200, 202)}) == 1 and await TDB.tejas_jobs.count_documents({'kind': 'grade', 'payload.attempt_id': aid}) == 1, [r.status_code for r in rs])
        await J_.drain_lane('grade')
        a = await TDB.tejas_attempts.find_one({'id': aid}); led = await TDB.tejas_ledgers.find_one({'id': aid})
        check('graded score equals the frozen ledger', a['grading_status'] == 'ready' and led and a['summary']['score_exact'] == led['summary']['score_exact'])
        # T6 signup race on one number
        rs = await asyncio.gather(*[c.post('/api/auth/phone/signup', json={'phone': '+919912345670', 'pin': '4321', 'confirm_pin': '4321'}) for _ in range(8)])
        check('8 racing sign-ups for one number -> exactly one account', sum(r.status_code == 200 for r in rs) == 1 and await TDB.tejas_phone_profiles.count_documents({'phone': '+919912345670'}) == 1, [r.status_code for r in rs])
        # T7 paper cache never serves edited questions
        await TDB.tejas_sets.update_one({'id': PID}, {'$set': {'questions.0.text': 'TEST edited text'}, '$inc': {'revision': 1}})
        await go(2, 'POST', f'/api/sets/{PID}/preflight', {'test_response': 'ok'})
        r = await go(2, 'POST', f'/api/sets/{PID}/start', {'start_key': str(uuid.uuid4()), 'device_checked': True})
        b = await TDB.tejas_attempts.find_one({'id': J(r)['id']})
        check('after a question edit, a new start freezes the new content', r.status_code == 200 and b['pack_id'] != full['pack_id'], r.text[:200])
        # T8 auth cache invalidation
        cookie = S[3][1]
        first = await c.get('/api/auth/me', cookies=cookie)
        await c.post('/api/auth/logout', cookies=cookie)
        check('logout takes effect immediately on this server', first.status_code == 200 and (await c.get('/api/auth/me', cookies=cookie)).status_code == 401)
        auth.STUDENT_SESSION_SECONDS = 0.3
        cookie = S[4][1]; await c.get('/api/auth/me', cookies=cookie)
        await TDB.tejas_sessions.delete_many({'user_id': S[4][0]}); await asyncio.sleep(0.4)
        check('a session revoked elsewhere stops working within the cache window', (await c.get('/api/auth/me', cookies=cookie)).status_code == 401)
        auth.STUDENT_SESSION_SECONDS = 10
        # T9 leaderboard ranks with ties
        CID = 'TEST_COMP176'
        await TDB.tejas_sets.insert_one({'id': CID, 'title': 'TEST comp', 'exam': 'JEE Main', 'competition': True, 'questions': [{'id': 'x'}], 'rules': {'minutes': 60},
                                         'start_at': time.time() - 7200, 'end_at': time.time() - 60, 'live_enabled': True})
        scores = [100, 90, 90, 80, 70, 70, 70, 10]
        await TDB.tejas_attempts.insert_many([{'id': f'TEST_LA_{k}', 'user_id': S[k][0], 'set_id': CID, 'mode': 'practice', 'competition_ranked': True, 'competition_end': 1,
                                               'status': 'completed', 'grading_status': 'ready', 'summary': {'score': v, 'score_exact': str(v), 'accuracy': 50}, 'start_key': 'k%d' % k} for k, v in enumerate(scores)])
        await TDB.tejas_ledgers.insert_many([{'id': f'TEST_LA_{k}', 'summary': {'score': v, 'score_exact': str(v)}} for k, v in enumerate(scores)])
        r = J(await go(5, 'GET', f'/api/competitions/{CID}'))
        check('leaderboard shares ranks on ties (1,2,2,4,5,5,5,8) and ranks you', [x['rank'] for x in r['rows']] == [1, 2, 2, 4, 5, 5, 5, 8] and r['you']['rank'] == 5 and r['participants'] == 8, r)
        # T10 integrity repairs on seeded broken data
        await go(6, 'POST', f'/api/sets/{PID}/preflight', {'test_response': 'ok'})
        e = J(await go(6, 'POST', f'/api/sets/{PID}/start', {'start_key': str(uuid.uuid4()), 'device_checked': True}))
        await TDB.tejas_attempts.update_one({'id': e['id']}, {'$set': {'deadline': time.time() - 30}})
        await TDB.tejas_attempts.update_one({'id': aid}, {'$set': {'summary.score_exact': '999', 'summary.score': 999}})
        wrong_entry = await TDB.tejas_cohort_entries.find_one({'attempt_id': aid})
        await TDB.tejas_cohort_entries.update_one({'attempt_id': aid}, {'$set': {'score_exact': '777', 'score': 777}})
        await TDB.tejas_cohort_entries.insert_one({'id': 'TEST_orphan_entry', 'cohort_id': 'TEST_C176', 'user_id': 'nobody', 'attempt_id': 'TEST_missing', 'score': 50, 'score_exact': '50'})
        await TDB.tejas_cohorts.insert_one({'id': 'TEST_C176', 'dirty': False})
        await TDB.tejas_ledgers.insert_one({'id': 'TEST_orphan_ledger', 'summary': {'score': 1, 'score_exact': '1'}})
        await TDB.tejas_sessions.insert_one({'id': 'TEST_orphan_session', 'user_id': 'TEST_nobody', 'expires_at': datetime.now(timezone.utc) + timedelta(days=1)})
        await TDB.tejas_jobs.insert_one({'id': 'report-TEST', 'kind': 'report', 'status': 'failed', 'user_id': 'x', 'set_id': PID, 'payload': {'attempt_id': aid}, 'attempts': 3, 'created_at': time.time()})
        await TDB.tejas_attempts.insert_one({'id': 'TEST_no_test', 'user_id': S[7][0], 'set_id': 'TEST_missing_set', 'status': 'completed', 'grading_status': 'ready', 'mode': 'retry', 'start_key': 'zz',
                                             'summary': {'score_exact': '0'}})
        await TDB.tejas_ledgers.insert_one({'id': 'TEST_no_test', 'summary': {'score_exact': '0'}})
        rep = await integrity.run('test')
        by = {x['key']: x for x in rep['checks']}
        for k in ('open_after_time', 'score_differs', 'peer_score_differs', 'peer_entry_orphan', 'score_record_orphan', 'session_orphan', 'job_stopped'):
            check(f'repair {k}: found then fixed', by[k]['found'] and by[k]['left'] == 0 and by[k]['state'] == 'fixed', by[k])
        check('report-only problem is shown, never changed', by['attempt_without_test']['found'] == 1 and by['attempt_without_test']['state'] == 'needs_attention' and await TDB.tejas_attempts.count_documents({'id': 'TEST_no_test'}) == 1, by['attempt_without_test'])
        a = await TDB.tejas_attempts.find_one({'id': aid}); entry = await TDB.tejas_cohort_entries.find_one({'attempt_id': aid})
        check('wrong shown score restored from the frozen ledger', a['summary']['score_exact'] == led['summary']['score_exact'])
        check('wrong ranking entry restored from the frozen ledger', entry['score_exact'] == wrong_entry['score_exact'] and (await TDB.tejas_cohorts.find_one({'id': entry['cohort_id']}))['dirty'] is True)
        check('orphans archived before removal (reversible)', await TDB.tejas_integrity_archive.count_documents({'_id': {'$in': ['cohort_entry:' + str(x) for x in []]}}) == 0 and await TDB.tejas_integrity_archive.count_documents({'kind': {'$in': ['cohort_entry', 'ledger']}}) == 2 and (await TDB.tejas_cohorts.find_one({'id': 'TEST_C176'}))['dirty'] is True)
        await J_.drain_lane('grade')
        ex = await TDB.tejas_attempts.find_one({'id': e['id']})
        check('timed-out attempt closed at its deadline and scored', ex['status'] == 'completed' and ex['reason'] == 'time_limit' and ex['grading_status'] == 'ready', {k: ex.get(k) for k in ('status', 'reason', 'grading_status')} | {'job': await TDB.tejas_jobs.find_one({'id': 'grade-' + e['id']}, {'_id': 0, 'status': 1, 'error': 1, 'attempts': 1, 'next_run_at': 1})})
        await TDB.tejas_ledgers.delete_one({'id': e['id']})
        rep2 = await integrity.run('test')
        by2 = {x['key']: x for x in rep2['checks']}
        await J_.drain_lane('grade')
        relaid = await TDB.tejas_ledgers.find_one({'id': e['id']}); ex = await TDB.tejas_attempts.find_one({'id': e['id']})
        check('score shown without a frozen record is re-scored from sealed answers', by2['score_without_record']['found'] == 1 and relaid and relaid['summary']['score_exact'] == ex['summary']['score_exact'], by2['score_without_record'])
        rep3 = await integrity.run('test')
        check('third run: every repairable check is clean', all(x['found'] == 0 for x in rep3['checks'] if x['action'] == 'repair'), [x for x in rep3['checks'] if x['found']])
        check('no missing database safeguards', rep3['missing_safeguards'] == [], rep3['missing_safeguards'])
        check('lock is released after each run', (await TDB.tejas_operations.find_one({'_id': 'integrity-lock'}))['until'] == 0)
        r = await go(8, 'GET', '/api/admin/integrity')
        check('students cannot read the data report', r.status_code == 403, r.status_code)
        check('signed-out visitors cannot read the data report', (await c.get('/api/admin/integrity')).status_code == 401)
        # maintenance: whole backlog, single flight
        for i in (9, 10, 11):
            await go(i, 'POST', f'/api/sets/{PID}/preflight', {'test_response': 'ok'})
            x = J(await go(i, 'POST', f'/api/sets/{PID}/start', {'start_key': str(uuid.uuid4()), 'device_checked': True}))
            await TDB.tejas_attempts.update_one({'id': x['id']}, {'$set': {'deadline': time.time() - 5}})
        await asyncio.gather(J_.maintenance(), J_.maintenance())
        check('maintenance closes and scores every timed-out attempt, one run at a time', await TDB.tejas_attempts.count_documents({'status': 'active', 'deadline': {'$lt': time.time()}, 'deadline_test': {'$exists': False}, 'user_id': {'$in': [S[i][0] for i in (9, 10, 11)]}}) == 0
              and await TDB.tejas_attempts.count_documents({'user_id': {'$in': [S[i][0] for i in (9, 10, 11)]}, 'grading_status': 'ready'}) == 3)
    for t in list(integrity._tasks):
        await t
    await H.tdbmod.client.drop_database(H.TEST_DB)
    check('isolated database dropped', H.TEST_DB not in await H.tdbmod.client.list_database_names())
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')


if __name__ == '__main__':
    asyncio.run(main())
