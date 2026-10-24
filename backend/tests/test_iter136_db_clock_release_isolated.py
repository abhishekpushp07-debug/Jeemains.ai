"""TEST-ONLY iteration 136: DB-clock embargo/label gates across satellite APIs, jobs $literal, FIFO index,
outbox starvation, cron envelope, score_version/legacy asset lookups, source-commitment fail-closed, marking.
Isolated DB via iso_harness_iter134 (all handles rebound, no lifespan, synthetic X-Test-User actors).
App clock skew = H.OFFSET (+7200 / -7200); Mongo $$NOW / hello.localTime stay real (the release authority).
Storage/crop/grade dispatch are MOCKED. Shares the event loop with the iter135 modules.
Run: cd /app/backend/tests && python -m pytest test_iter135_canonical_regression_isolated.py test_iter135_hardening_isolated.py test_iter136_db_clock_release_isolated.py -n0 -p no:cacheprovider -v
"""
import asyncio, json, time, uuid
import pytest
import iso_harness_iter134 as H
import test_iter135_canonical_regression_isolated as R
from tejas import attempts as AT, packs as PK, jobs as JB, corrections as CO, cohorts as CH, live_series as LS

run, client, J, TDB = R.run, R.client, R.J, R.TDB
EV = {}
S, O = {'x-test-user': 's'}, {'x-test-user': 'o'}
H.USERS.update({'s': R.STUDENT, 'o': R.OTHER})
JEE = {'minutes': 10, 'correct': 4, 'wrong': -1, 'skipped': 0}
BITSAT = {'minutes': 10, 'correct': 3, 'wrong': -1, 'skipped': 0}
FILE_ID = 'TEST_F136_file'


@pytest.fixture(scope='module', autouse=True)
def isolated():
    assert H.TEST_DB != H.REAL_DB and not H.leftover_real_handles()
    run(H.tdbmod.client.drop_database(H.TEST_DB))
    run(H.tdbmod.indexes())
    run(TDB.tejas_files.insert_one({'id': FILE_ID, 'path': 'TEST/none.png', 'kind': 'image', 'sha256': ''}))
    orig = AT.ensure_grade
    AT.ensure_grade = R._no_grade
    yield
    AT.ensure_grade = orig
    H.OFFSET[0] = 0
    run(H.tdbmod.client.drop_database(H.TEST_DB))
    assert H.TEST_DB not in run(H.tdbmod.client.list_database_names())
    with open('/app/test_reports/iter136_evidence.json', 'w') as f:
        json.dump(EV, f, indent=2, default=str)


@pytest.fixture(autouse=True)
def clock():
    H.OFFSET[0] = 0
    yield
    H.OFFSET[0] = 0


def qs(n=4, refs=False):
    return [{'id': str(uuid.uuid4()), 'number': i + 1, 'type': 'mcq', 'subject': 'Physics', 'section': 'A',
             'options': {'A': 'a', 'B': 'b', 'C': 'c', 'D': 'd'}, 'answer': 'A', 'text': f'TEST_136 q{i}', 'solution': 'TEST_136 secret solution',
             **({'q_refs': [{'file_id': FILE_ID, 'page': 1, 'box': [0, 0, 1, 1]}], 's_refs': [{'file_id': FILE_ID, 'page': 1, 'box': [0, 0, 1, 1]}]} if refs else {})}
            for i in range(n)]


async def make(user=R.STUDENT, deadline_in=600.0, rules=None, exam='JEE Main', extra=None, refs=False, set_id=None, legacy=False):
    a = {'id': 'TEST_A136_' + uuid.uuid4().hex, 'user_id': user['id'], 'set_id': set_id or ('TEST_S136_' + uuid.uuid4().hex[:8]), 'title': 'TEST 136',
         'exam': exam, 'mode': 'practice', 'version': 1, 'rules': rules or dict(JEE), 'status': 'active', 'answers': {}, 'first_answers': {},
         'server_seq': 0, 'command_count': 0, 'visited': [], 'test_kind': 'mock', 'profile': {}, 'started_at': time.time(),
         'deadline': time.time() + deadline_in, 'questions': qs(refs=refs), 'parent_attempt': None, 'start_key': 'TEST_K136_' + uuid.uuid4().hex, **(extra or {})}
    q = [dict(x) for x in a['questions']]
    if legacy:
        await TDB.tejas_attempts.insert_one(dict(a))
    else:
        await PK.insert_attempt(a)
    return a['id'], q


async def completed(user=R.STUDENT, comp_delta=None, rules=None, exam='JEE Main', extra=None, refs=False, hdr=S):
    ex = dict(extra or {})
    if comp_delta is not None:
        ex['competition_end'] = time.time() + comp_delta
    id, q = await make(user, rules=rules, exam=exam, extra=ex, refs=refs)
    async with client() as c:
        r1 = await c.put(f'/api/attempts/{id}/answers/{q[0]["id"]}', json=R.body(value='A'), headers=hdr)
        r2 = await c.put(f'/api/attempts/{id}/answers/{q[1]["id"]}', json=R.body(value='B'), headers=hdr)
        r3 = await c.post(f'/api/attempts/{id}/submit', headers=hdr)
    assert r1.status_code == 200 and r2.status_code == 200 and r3.status_code in (200, 202), (r1.text, r2.text, r3.text)
    led = await CO.freeze_ledger(dict(await AT.owned(id, user)))
    await TDB.tejas_attempts.update_one({'id': id}, {'$set': {'summary': led['summary'], 'grading_status': 'ready'}})
    return id, q, led


# ---------- 1. parameterized actual-API embargo with app clock +/-7200 ----------
CASES = [(off, rel) for off in (7200, -7200) for rel in (False, True)]


@pytest.mark.parametrize('offset,released', CASES, ids=[f'app{o:+d}-{"released" if r else "embargoed"}' for o, r in CASES])
def test_satellite_embargo_db_clock(offset, released, monkeypatch):
    monkeypatch.setattr(JB, 'get_object', lambda path: b'%PDF-TEST136')
    async def go():
        id, q, led = await completed(comp_delta=(-3600 if released else 3600))
        jid = 'TEST_J136_' + uuid.uuid4().hex
        await TDB.tejas_jobs.insert_one({'id': jid, 'kind': 'report', 'user_id': R.STUDENT['id'], 'set_id': 'x', 'status': 'done', 'path': 'TEST/r.pdf',
                                         'payload': {'attempt_id': id}, 'created_at': time.time(), 'attempts': 1})
        H.OFFSET[0] = offset
        out = {}
        async with client() as c:
            hist = await c.get('/api/exam-navigation/jee-main/history', headers=S)
            mt = await c.get('/api/my/tests?tab=completed', headers=S)
            res = await c.get(f'/api/attempts/{id}/results', headers=S)
            out['results'] = res
            out['ai_solutions'] = await c.get(f'/api/attempts/{id}/ai-solutions', headers=S)
            out['worked_solution'] = await c.get(f'/api/attempts/{id}/solutions/{q[0]["id"]}', headers=S)
            out['cohort'] = await c.get(f'/api/attempts/{id}/cohort', headers=S)
            out['air'] = await c.post(f'/api/attempts/{id}/air-scenario', json={'percentile_low': 90.0, 'percentile_high': 95.0}, headers=S)
            out['journey'] = await c.get(f'/api/attempts/{id}/journey', headers=S)
            out['ev'] = await c.post(f'/api/attempts/{id}/expected-value', json={'probability': 0.5}, headers=S)
            out['report_key'] = await c.post(f'/api/attempts/{id}/questions/{q[0]["id"]}/report-wrong', json={'category': 'key', 'context': 'results', 'note': 'TEST'}, headers=S)
            out['solution_asset'] = await c.get(f'/api/attempts/{id}/questions/{q[0]["id"]}/asset/solution/0', headers=S)
            out['download'] = await c.get(f'/api/jobs/{jid}/download', headers=S)
            foreign = {k: (await c.get(u, headers=O)).status_code for k, u in
                       [('results', f'/api/attempts/{id}/results'), ('cohort', f'/api/attempts/{id}/cohort'), ('journey', f'/api/attempts/{id}/journey'),
                        ('ai_solutions', f'/api/attempts/{id}/ai-solutions'), ('download', f'/api/jobs/{jid}/download')]}
        H.OFFSET[0] = 0
        return id, hist, mt, out, foreign
    id, hist, mt, out, foreign = run(go())
    hi = {i['id']: i for i in J(hist)['items']}[id]
    mi = {i['id']: i for i in J(mt)['items']}[id]
    codes = {k: v.status_code for k, v in out.items()}
    rj = J(out['results'])
    EV[f'embargo_{offset}_{released}'] = {'history_summary': hi.get('summary'), 'mytests_status': mi['status'], 'mytests_summary': mi.get('summary'),
                                          'results_status': rj.get('status'), 'codes': codes, 'foreign': foreign}
    print('EMB', offset, released, EV[f'embargo_{offset}_{released}'])
    leaks = [k for k, v in out.items() if '_database_now' in v.text] + (['history'] if '_database_now' in hist.text else [])
    assert not leaks, leaks
    assert all(v == 404 for v in foreign.values()), foreign
    if released:
        assert hi['summary'] and hi['summary']['score'] == 3 and mi['status'] == 'completed' and mi['summary']['score'] == 3
        assert codes['results'] == 200 and rj.get('status') != 'embargoed' and rj['summary']['score'] == 3
        for k in ('ai_solutions', 'cohort', 'air', 'journey', 'ev', 'report_key', 'solution_asset', 'download', 'worked_solution'):
            assert codes[k] != 403, (k, codes[k], out[k].text[:200])
        assert codes['download'] == 200 and codes['report_key'] == 200 and codes['ev'] == 200 and codes['journey'] == 200
    else:
        assert hi['summary'] is None and mi['status'] == 'embargoed' and mi.get('summary') is None
        assert codes['results'] == 200 and rj['status'] == 'embargoed' and 'summary' not in rj and 'questions' not in rj
        for k in ('ai_solutions', 'cohort', 'air', 'journey', 'ev', 'report_key', 'solution_asset', 'download', 'worked_solution'):
            assert codes[k] == 403, (k, codes[k], out[k].text[:200])
        assert 'secret solution' not in ''.join(v.text for v in out.values())


@pytest.mark.parametrize('offset', [7200, -7200])
def test_series_history_and_leaderboard_db_clock(offset):
    async def go():
        ids = {}
        for rel in (False, True):
            id, q, led = await completed(comp_delta=(-3600 if rel else 3600), extra={'series_id': LS.SERIES_ID, 'series_date': '2026-10-24'})
            await TDB.tejas_attempts.update_one({'id': id}, {'$set': {'mode': 'series_live'}})
            ids[rel] = id
        comp = {}
        for rel in (False, True):
            cid = 'TEST_C136_' + uuid.uuid4().hex[:10]
            await TDB.tejas_sets.insert_one({'id': cid, 'title': 'TEST 136 comp', 'exam': 'JEE Main', 'competition': True, 'questions': [{'id': 'q1'}], 'rules': {'minutes': 10},
                                             'start_at': time.time() - 7000, 'end_at': time.time() + (-3600 if rel else 3600), 'live_enabled': True, 'status': 'published'})
            comp[rel] = cid
        H.OFFSET[0] = offset
        async with client() as c:
            sh = await c.get('/api/series/all-india-jee/history', headers=S)
            lb = {rel: await c.get(f'/api/competitions/{cid}', headers=S) for rel, cid in comp.items()}
        H.OFFSET[0] = 0
        return ids, sh, lb
    ids, sh, lb = run(go())
    assert sh.status_code == 200, sh.text
    items = {i['id']: i for i in J(sh)['items']}
    lbs = {rel: (r.status_code, J(r).get('status'), J(r).get('competition', {}).get('status')) for rel, r in lb.items()}
    EV[f'series_lb_{offset}'] = {'series_embargoed': (items[ids[False]]['status'], items[ids[False]].get('summary')),
                                 'series_released': (items[ids[True]]['status'], (items[ids[True]].get('summary') or {}).get('score')), 'leaderboard': lbs}
    print('SERIES/LB', offset, EV[f'series_lb_{offset}'])
    assert items[ids[False]]['status'] == 'embargoed' and items[ids[False]].get('summary') is None
    assert items[ids[True]]['status'] == 'completed' and items[ids[True]]['summary']['score'] == 3
    assert lbs[False][0] == 200 and lbs[False][1] == 'embargoed' and lbs[False][2] == 'live'
    assert lbs[True][0] == 200 and lbs[True][1] != 'embargoed' and lbs[True][2] == 'ended'
    assert abs(J(sh).get('server_now', time.time()) - time.time()) < 5 if 'server_now' in J(sh) else True


@pytest.mark.parametrize('offset', [7200, -7200])
def test_active_labels_catalogues_and_mytests_db_clock(offset):
    """+7200: DB deadline future -> active everywhere, never sealed. -7200: DB deadline passed -> completed/expired label."""
    async def go():
        set_nav = 'TEST_SN136_' + uuid.uuid4().hex[:8]
        set_ch = 'TEST_SC136_' + uuid.uuid4().hex[:8]
        base = {'status': 'published', 'audience': 'all', 'title': 'TEST 136 chapter', 'questions': qs(), 'rules': dict(JEE), 'created_at': time.time(), 'revision': 1}
        await TDB.tejas_sets.insert_one({**base, 'id': set_nav, 'exam': 'JEE Main', 'test_kind': 'chapter'})
        await TDB.tejas_sets.insert_one({**base, 'id': set_ch, 'exam': 'BITSAT', 'chapter_book_id': 'TEST_B136', 'chapter_subject': 'Physics', 'chapter_number': 1,
                                         'live_enabled': True, 'start_at': time.time() - 30000, 'end_at': time.time() + 30000})
        din = 600 if offset > 0 else -60
        a_nav, _ = await make(set_id=set_nav, deadline_in=din)
        a_ch, _ = await make(set_id=set_ch, deadline_in=din, exam='BITSAT', rules=dict(BITSAT))
        H.OFFSET[0] = offset
        async with client() as c:
            nav = await c.get('/api/exam-navigation/jee-main/catalogue?kind=chapters', headers=S)
            ch = await c.get('/api/my/chapter-exams', headers=S)
            prog = await c.get('/api/my/tests?tab=progress', headers=S)
            comp = await c.get('/api/my/tests?tab=completed', headers=S)
        H.OFFSET[0] = 0
        return a_nav, a_ch, set_nav, set_ch, nav, ch, prog, comp, await R.db_attempt(a_nav), await R.db_attempt(a_ch)
    a_nav, a_ch, set_nav, set_ch, nav, ch, prog, comp, dn, dc = run(go())
    assert nav.status_code == 200 and ch.status_code == 200, (nav.text[:300], ch.text[:300])
    nav_lbl = next((i.get('attempt') or {}).get('status') for i in J(nav)['items'] if i['id'] == set_nav)
    ch_lbl = next((i.get('attempt') or {}).get('status') for i in J(ch)['items'] if i['id'] == set_ch)
    prog_ids = {i['id']: i['status'] for i in J(prog)['items']}
    comp_ids = {i['id']: i['status'] for i in J(comp)['items']}
    EV[f'labels_{offset}'] = {'nav': nav_lbl, 'chapter': ch_lbl, 'progress': prog_ids, 'completed': comp_ids, 'db': (dn['status'], dc['status'])}
    print('LABELS', offset, EV[f'labels_{offset}'])
    if offset > 0:
        assert nav_lbl == 'active' and ch_lbl == 'active' and prog_ids.get(a_nav) == 'active' and prog_ids.get(a_ch) == 'active'
        assert a_nav not in comp_ids and dn['status'] == 'active' and dc['status'] == 'active' and not dn.get('submitted_at')
    else:
        assert nav_lbl == 'completed' and ch_lbl == 'completed' and a_nav not in prog_ids and comp_ids.get(a_nav) == 'expired'


# ---------- 2. private scheduled content start window (content.permitted) under app skew ----------
@pytest.mark.parametrize('offset', [7200, -7200, 0])
def test_scheduled_import_start_window_db_clock(offset):
    async def go():
        sid = 'TEST_SI136_' + uuid.uuid4().hex[:8]
        t = time.time()
        win = (t + 3600, t + 3 * 3600) if offset >= 0 else (t - 9000, t - 600)  # DB: not yet open / already closed
        await TDB.tejas_sets.insert_one({'id': sid, 'status': 'published', 'audience': 'all', 'title': 'TEST 136 import', 'exam': 'JEE Main', 'import_id': 'TEST_I136', 'version': 1,
                                         'live_enabled': True, 'start_at': win[0], 'end_at': win[1], 'questions': qs(), 'rules': {**JEE, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'}, 'created_at': t, 'revision': 1})
        H.OFFSET[0] = offset
        async with client() as c:
            pf = await c.post(f'/api/sets/{sid}/preflight', json={}, headers=S)
            EV[f'import_window_preflight_{offset}'] = (pf.status_code, pf.text[:200])
            r = await c.post(f'/api/sets/{sid}/start', json={'start_key': 'TEST_SK136_' + uuid.uuid4().hex, 'device_checked': True}, headers=S)
            EV[f'import_window_text_{offset}'] = r.text[:300]
        H.OFFSET[0] = 0
        return r
    r = run(go())
    print('IMPORTTXT', offset, EV[f'import_window_text_{offset}'])
    EV[f'import_window_{offset}'] = {'status': r.status_code, 'question_text_exposed': 'TEST_136 q0' in r.text}
    print('IMPORTWIN', offset, EV[f'import_window_{offset}'])
    assert r.status_code != 200 and 'TEST_136 q0' not in r.text, f'FAULT: content.permitted uses app now() for import start/end window ({r.status_code})'


# ---------- 3. jobs: $literal message, FIFO index, outbox starvation ----------
def test_job_message_literal_dollar(monkeypatch):
    async def fake_refresh(j):
        return '$danger'
    monkeypatch.setattr(CH, 'refresh', fake_refresh)
    async def go():
        jid = 'TEST_JL136_' + uuid.uuid4().hex
        await TDB.tejas_jobs.insert_one({'id': jid, 'kind': 'cohort', 'user_id': R.STUDENT['id'], 'set_id': 'x', 'status': 'queued', 'payload': {}, 'created_at': time.time(), 'attempts': 0, 'next_run_at': 0})
        await JB.run_job(jid, drain=False)
        return await TDB.tejas_jobs.find_one({'id': jid}, {'_id': 0})
    j = run(go())
    EV['literal_message'] = {'status': j['status'], 'message': j.get('message')}
    assert j['status'] == 'done' and j['message'] == '$danger'


def test_fifo_index_explain_3000_and_no_index_dropped():
    async def go():
        before = sorted(i['name'] for i in await TDB.tejas_jobs.list_indexes().to_list(None))
        await TDB.tejas_jobs.insert_many([{'id': f'TEST_fj_{i}', 'kind': ['grade', 'report', 'cohort'][i % 3], 'status': ['queued', 'done', 'failed', 'running'][i % 4],
                                           'created_at': 10000 - i, 'lease_until': 0, 'attempts': i % 4, 'next_run_at': (time.time() + 999) if i % 7 == 0 else 0} for i in range(3300)])
        Jc = TDB.tejas_jobs
        drain_q = {'kind': 'report', 'status': 'queued', '$and': [{'$expr': {'$lte': [{'$ifNull': ['$next_run_at', 0]}, R.CN.EPOCH_NOW if hasattr(R, 'CN') else {'$divide': [{'$toLong': '$$NOW'}, 1000]}]}},
                   {'$or': [{'attempts': {'$lt': JB.JOB_ATTEMPTS}}, {'attempts': {'$exists': False}}]}]}
        e1 = await Jc.find(drain_q, {'id': 1}).sort('created_at', 1).limit(1).explain()
        now_expr = {'$divide': [{'$toLong': '$$NOW'}, 1000]}
        maint_q = {'kind': 'report', '$and': [{'$or': [{'status': 'queued'}, {'status': 'running', '$expr': {'$lt': ['$lease_until', now_expr]}}]},
                                             {'$expr': {'$lte': [{'$ifNull': ['$next_run_at', 0]}, now_expr]}}]}
        e2 = await Jc.find(maint_q, {'id': 1}).sort('created_at', 1).limit(8).explain()
        first = await Jc.find_one(drain_q, {'id': 1, 'created_at': 1}, sort=[('created_at', 1)])
        return before, e1, e2, first
    before, e1, e2, first = run(go())
    def stages(p):
        p = p['queryPlanner']['winningPlan']; p = p.get('queryPlan', p); out = []
        while p:
            out.append((p.get('stage'), p.get('indexName'))); p = p.get('inputStage') or (p.get('inputStages') or [None])[0]
        return out
    s1, s2 = stages(e1), stages(e2)
    EV['fifo'] = {'indexes': before, 'drain_actual': s1, 'maintenance_recovery': s2, 'first_created_at': first['created_at']}
    print('FIFO', EV['fifo'])
    assert 'job_lane_fifo' in before and 'kind_1_status_1_next_run_at_1_created_at_1' in before
    assert all(st != 'SORT' for st, _ in s1) and any(ix == 'job_lane_fifo' for _, ix in s1)
    expected_min = min(10000 - i for i in range(3300) if i % 3 == 1 and i % 4 == 0 and i % 7 != 0)
    assert first['created_at'] == expected_min


def test_outbox_1200_failed_do_not_starve_new(monkeypatch):
    calls = []
    async def rec(a, bg=None):
        calls.append(a['id'])
    monkeypatch.setattr(AT, 'ensure_grade', rec)
    async def noop(*a, **k):
        return None
    import tejas.manual_solutions as MS
    monkeypatch.setattr(MS, 'dispatch_manual', noop)
    monkeypatch.setattr(JB, 'run_job', noop)
    async def go():
        t = time.time()
        await TDB.tejas_attempts.insert_many([{'id': f'TEST_ob_{i}', 'user_id': 'TEST_obu', 'set_id': f'TEST_obs_{i}', 'mode': 'practice', 'status': 'completed', 'grading_status': 'failed',
                                               'submitted_at': t - 9999 + i, 'started_at': t - 99999, 'start_key': f'TEST_obk_{i}', 'deadline': 0} for i in range(1200)])
        await TDB.tejas_attempts.insert_one({'id': 'TEST_ob_new', 'user_id': 'TEST_obu', 'set_id': 'TEST_obs_new', 'mode': 'practice', 'status': 'completed', 'grading_status': 'queued',
                                             'submitted_at': t, 'started_at': t - 100, 'start_key': 'TEST_obk_new', 'deadline': 0})
        await JB.maintenance()
    run(go())
    EV['outbox'] = {'calls': len(calls), 'new_included': 'TEST_ob_new' in calls, 'failed_included': sum(c.startswith('TEST_ob_') and c != 'TEST_ob_new' for c in calls)}
    assert 'TEST_ob_new' in calls and EV['outbox']['failed_included'] == 0


def test_grade_load_excludes_receipts_and_schema():
    async def go():
        id, q = await make()
        await TDB.tejas_attempts.update_one({'id': id}, {'$set': {'command_receipts': {'x': {'TEST': 1}}, 'response_schema': {'q': 'TEST'}}})
        return await H.tdbmod.get(TDB.tejas_attempts, id)
    d = run(go())
    assert 'command_receipts' not in d and 'response_schema' not in d and '_database_now' in d


# ---------- 4. cron envelope ----------
def test_cron_envelope_header_only_and_malformed(monkeypatch):
    monkeypatch.setenv('WEBHOOK_CRON_SECRET', 'TEST-cron-' + uuid.uuid4().hex)
    sec = __import__('os').environ['WEBHOOK_CRON_SECRET']
    ran = []
    monkeypatch.setattr(JB, 'maintenance', lambda: ran.append(1) or asyncio.sleep(0))
    A = {'authorization': 'Bearer ' + sec}
    async def go():
        wid = 'TEST_wh_' + uuid.uuid4().hex
        async with client() as c:
            r = {
                'malformed_event': await c.post('/api/cron/maintenance', json={'event': 'nope'}, headers=A),
                'missing_id_both': await c.post('/api/cron/maintenance', json={'event': 'schedule.triggered'}, headers=A),
                'non_object': await c.post('/api/cron/maintenance', json=['x'], headers=A),
                'malformed_noauth': await c.post('/api/cron/maintenance', json={'event': 'nope'}),
                'valid_noauth': await c.post('/api/cron/maintenance', json={'event': 'schedule.triggered', 'run_id': 'r'}),
                'header_only': await c.post('/api/cron/maintenance', json={'event': 'schedule.triggered'}, headers={**A, 'x-webhook-id': wid}),
                'header_dup': await c.post('/api/cron/maintenance', json={'event': 'schedule.triggered'}, headers={**A, 'x-webhook-id': wid}),
                'extra_field': await c.post('/api/cron/maintenance', json={'event': 'schedule.triggered', 'run_id': 'TEST_x_' + uuid.uuid4().hex, 'scheduled_at': 'x'}, headers=A),
            }
        return r
    r = run(go())
    EV['cron'] = {k: (v.status_code, v.text[:120]) for k, v in r.items()} | {'ran': len(ran)}
    print('CRON', EV['cron'])
    assert r['malformed_event'].status_code == 400 and r['missing_id_both'].status_code == 400 and r['non_object'].status_code == 400
    assert r['valid_noauth'].status_code == 401 and r['malformed_noauth'].status_code in (400, 401)
    assert r['header_only'].status_code == 200 and J(r['header_only']).get('accepted') is True and not J(r['header_only']).get('duplicate')
    assert J(r['header_dup']).get('duplicate') is True and r['extra_field'].status_code == 200 and len(ran) == 2


# ---------- 5. score_version asset, legacy embedded asset, commitment fail-closed, marking ----------
def test_score_version_and_legacy_asset_lookup(monkeypatch):
    monkeypatch.setattr(AT, 'render_crop', lambda f, ref: b'\x89PNG-TEST136')
    async def go():
        id, q, led = await completed(refs=True)
        a = await TDB.tejas_attempts.find_one({'id': id}, {'_id': 0, 'pack_id': 1})
        alt_id, alt_q = await make(refs=True)
        alt_pack = (await TDB.tejas_attempts.find_one({'id': alt_id}, {'pack_id': 1}))['pack_id']
        pack_before = await TDB.tejas_packs.find_one({'_id': a['pack_id']}) or 'MISSING'
        await TDB.tejas_score_versions.insert_one({'id': 'TEST_SV136_' + id[-6:], 'attempt_id': id, 'user_id': R.STUDENT['id'], 'pack_id': alt_pack})
        await TDB.tejas_score_versions.insert_one({'id': 'TEST_SVF136_' + id[-6:], 'attempt_id': id, 'user_id': R.OTHER['id'], 'pack_id': alt_pack})
        lid, lq = await make(refs=True, legacy=True)
        async with client() as c:
            u = f'/api/attempts/{id}/questions'
            r = {
                'orig_own_q': (await c.get(f'{u}/{q[0]["id"]}/asset/question/0', headers=S)).status_code,
                'corrected_alt_q': (await c.get(f'{u}/{alt_q[0]["id"]}/asset/question/0?score_version=TEST_SV136_{id[-6:]}', headers=S)).status_code,
                'corrected_orig_q_not_in_alt': (await c.get(f'{u}/{q[0]["id"]}/asset/question/0?score_version=TEST_SV136_{id[-6:]}', headers=S)).status_code,
                'foreign_sv': (await c.get(f'{u}/{alt_q[0]["id"]}/asset/question/0?score_version=TEST_SVF136_{id[-6:]}', headers=S)).status_code,
                'missing_sv': (await c.get(f'{u}/{q[0]["id"]}/asset/question/0?score_version=nope', headers=S)).status_code,
                'other_user_orig': (await c.get(f'{u}/{q[0]["id"]}/asset/question/0', headers=O)).status_code,
                'legacy_own': (await c.get(f'/api/attempts/{lid}/questions/{lq[0]["id"]}/asset/question/0', headers=S)).status_code,
                'legacy_foreign_user': (await c.get(f'/api/attempts/{lid}/questions/{lq[0]["id"]}/asset/question/0', headers=O)).status_code,
                'legacy_foreign_qid': (await c.get(f'/api/attempts/{lid}/questions/{q[0]["id"]}/asset/question/0', headers=S)).status_code,
                'legacy_solution_active': (await c.get(f'/api/attempts/{lid}/questions/{lq[0]["id"]}/asset/solution/0', headers=S)).status_code,
            }
        pack_after = await TDB.tejas_packs.find_one({'_id': a['pack_id']}) or 'MISSING'
        return r, pack_before == pack_after
    r, unchanged = run(go())
    EV['assets136'] = {**r, 'orig_pack_unchanged': unchanged}
    print('ASSETS', EV['assets136'])
    assert r['orig_own_q'] == 200 and r['corrected_alt_q'] == 200 and r['corrected_orig_q_not_in_alt'] == 404
    assert r['foreign_sv'] == 404 and r['missing_sv'] == 404 and r['other_user_orig'] == 404 and unchanged
    assert r['legacy_own'] == 200 and r['legacy_foreign_user'] == 404 and r['legacy_foreign_qid'] == 404 and r['legacy_solution_active'] == 403


@pytest.mark.parametrize('field', ['pack_id', 'sealed_seq', 'profile', 'answers', 'rules'])
def test_source_commitment_mutation_fails_closed(field):
    async def go():
        id, q, led = await completed()
        before = await TDB.tejas_ledgers.find_one({'id': id}, {'_id': 0})
        mut = {'pack_id': 'TEST_other_pack', 'sealed_seq': 99, 'profile': {'TEST': 1}, 'answers.' + q[2]['id']: {'value': 'A', 'revision': 1}, 'rules.correct': 5}
        key = next(k for k in mut if k.split('.')[0] == field)
        await TDB.tejas_attempts.update_one({'id': id}, {'$set': {key: mut[key]}})
        async with client() as c:
            r = await c.get(f'/api/attempts/{id}/results', headers=S)
        after = await TDB.tejas_ledgers.find_one({'id': id}, {'_id': 0})
        return r, before == after
    r, unchanged = run(go())
    EV.setdefault('commitment', {})[field] = r.status_code
    assert r.status_code == 503 and 'TEST solution' not in r.text and unchanged, (field, r.status_code, r.text[:200])


def test_marking_jee_and_bitsat_preserved():
    async def go():
        _, _, jl = await completed(rules=dict(JEE))
        _, _, bl = await completed(rules=dict(BITSAT), exam='BITSAT')
        return jl['summary'], bl['summary']
    js, bs = run(go())
    EV['marking'] = {'jee': js.get('score'), 'bitsat': bs.get('score')}
    assert js['score'] == 3 and bs['score'] == 2
