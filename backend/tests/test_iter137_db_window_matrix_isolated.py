"""TEST-ONLY iteration 137: DB-clock start/list window matrix + expiry date + start-key resume + cron auth-first.
Isolated DB via iso_harness_iter134 (all Motor handles rebound, no lifespan, synthetic X-Test-User actors, DB dropped).
App clock skew = H.OFFSET (+/-7200, +/-2 days for date expiry); Mongo $$NOW / hello.localTime stay real (release authority).
Run with the iter135/136 suites (shared loop):
  cd /app/backend/tests && python -m pytest test_iter135_canonical_regression_isolated.py test_iter135_hardening_isolated.py \
     test_iter136_db_clock_release_isolated.py test_iter137_db_window_matrix_isolated.py -n0 -p no:cacheprovider -q
"""
import asyncio, json, os, time, uuid
from datetime import datetime, timezone, timedelta
import pytest
import iso_harness_iter134 as H
import test_iter135_canonical_regression_isolated as R
from tejas import attempts as AT, jobs as JB

run, client, J, TDB = R.run, R.client, R.J, R.TDB
EV = {}
S = {'x-test-user': 's'}
H.USERS.update({'s': R.STUDENT, 'o': R.OTHER})
RULES = {'minutes': 10, 'correct': 4, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'}


@pytest.fixture(scope='module', autouse=True)
def isolated():
    assert H.TEST_DB != H.REAL_DB and not H.leftover_real_handles()
    run(H.tdbmod.client.drop_database(H.TEST_DB))
    run(H.tdbmod.indexes())
    orig = AT.ensure_grade
    AT.ensure_grade = R._no_grade
    yield
    AT.ensure_grade = orig
    H.OFFSET[0] = 0
    run(H.tdbmod.client.drop_database(H.TEST_DB))
    assert H.TEST_DB not in run(H.tdbmod.client.list_database_names())
    with open('/app/test_reports/iter137_evidence.json', 'w') as f:
        json.dump(EV, f, indent=2, default=str)


@pytest.fixture(autouse=True)
def clock():
    H.OFFSET[0] = 0
    yield
    H.OFFSET[0] = 0


def qs(tag, n=3):
    return [{'id': str(uuid.uuid4()), 'number': i + 1, 'type': 'mcq', 'subject': 'Physics', 'section': 'A', 'options': {'A': 'a', 'B': 'b', 'C': 'c', 'D': 'd'},
             'answer': 'A', 'text': f'{tag} private q{i}', 'solution': f'{tag} secret'} for i in range(n)]


def make_set(kind, window, tag):
    t = time.time()
    sid = f'TEST_S137_{kind}_' + uuid.uuid4().hex[:8]
    s = {'id': sid, 'status': 'published', 'audience': 'all', 'title': f'{tag} title', 'version': 1, 'revision': 1, 'created_at': t,
         'questions': qs(tag), 'rules': dict(RULES)}
    if window:
        s.update(start_at=t + window[0], end_at=t + window[1])
    if kind == 'import':
        s.update(exam='JEE Main', import_id='TEST_I137', live_enabled=True, test_kind='mock')
    elif kind == 'chapter':
        s.update(exam='BITSAT', chapter_book_id='TEST_B137', chapter_subject='Physics', chapter_number=1, live_enabled=True, test_kind='chapter')
    elif kind == 'competition':
        s.update(exam='JEE Main', competition=True, test_kind='mock')
    else:  # standard unscheduled published
        s.update(exam='JEE Main', test_kind='mock')
    return s


async def probe(s, offset, tag):
    """All gated reads/writes for set s with app clock offset. Returns codes, listings, leak flags, DB side-effects."""
    await TDB.tejas_sets.insert_one(dict(s))
    sid = s['id']
    H.OFFSET[0] = offset
    out, lists = {}, {}
    async with client() as c:
        nav_kind = 'chapters' if s.get('chapter_book_id') else 'mocks'
        slug = 'bitsat' if s['exam'] == 'BITSAT' else 'jee-main'
        listing = {
            'public_sets': await c.get(f'/api/sets?q={tag}'),
            'my_sets': await c.get(f'/api/my/sets?q={tag}', headers=S),
            'exam_nav': await c.get(f'/api/exam-navigation/{slug}/catalogue?kind={nav_kind}&q={tag}', headers=S),
        }
        if s['exam'] == 'BITSAT':
            listing['chapter_public'] = await c.get(f'/api/chapter-exams?q={tag}')
            listing['chapter_my'] = await c.get(f'/api/my/chapter-exams?q={tag}', headers=S)
        out['set_detail'] = await c.get(f'/api/sets/{sid}')
        out['my_set'] = await c.get(f'/api/my/sets/{sid}', headers=S)
        out['save'] = await c.post(f'/api/my/tests/saved/{sid}', json={}, headers=S)
        out['preflight'] = await c.post(f'/api/sets/{sid}/preflight', json={}, headers=S)
        out['start'] = await c.post(f'/api/sets/{sid}/start', json={'start_key': 'TEST_SK137_' + uuid.uuid4().hex, 'device_checked': True}, headers=S)
        out['saved_unavailable'] = await c.get('/api/my/tests?tab=saved&status=unavailable', headers=S)
    H.OFFSET[0] = 0
    for k, r in listing.items():
        items = J(r).get('items', []) if r.status_code == 200 else None
        lists[k] = (r.status_code, None if items is None else any(i.get('id') == sid for i in items))
    codes = {k: v.status_code for k, v in out.items()}
    leak = [k for k, v in {**out, **listing}.items() if f'{tag} private' in v.text or f'{tag} secret' in v.text]
    n_att = await TDB.tejas_attempts.count_documents({'set_id': sid})
    n_pf = await TDB.tejas_preflight.count_documents({'set_id': sid})
    unavail = [i['set_id'] for i in J(out['saved_unavailable']).get('items', [])] if codes['saved_unavailable'] == 200 else None
    return {'codes': codes, 'lists': lists, 'leak': leak, 'attempts': n_att, 'preflights': n_pf, 'start_body': out['start'].text[:160],
            'saved_unavailable_has': None if unavail is None else sid in unavail, 'start_json': J(out['start']) if codes['start'] == 200 else None}


WINDOWS = {'future': (3600, 3 * 3600), 'open': (-3600, 3600), 'expired': (-9000, -600)}
MATRIX = [(k, w, o) for k in ('import', 'chapter', 'competition') for w in WINDOWS for o in (7200, -7200)]


@pytest.mark.parametrize('kind,win,offset', MATRIX, ids=[f'{k}-{w}-app{o:+d}' for k, w, o in MATRIX])
def test_db_window_matrix(kind, win, offset):
    tag = 'TEST137' + uuid.uuid4().hex[:8]
    s = make_set(kind, WINDOWS[win], tag)
    res = run(probe(s, offset, tag))
    sj = res.pop('start_json')
    EV[f'matrix_{kind}_{win}_{offset}'] = res
    print('MATRIX', kind, win, offset, res['codes'], res['lists'], res['leak'], res['attempts'])
    c, L = res['codes'], res['lists']
    for k, (st, _) in L.items():
        assert st == 200, (k, st)
    if win == 'open':
        assert c['preflight'] == 200 and c['start'] == 200, (c, res['start_body'])
        assert sj['status'] == 'active' and res['attempts'] == 1 and sj['deadline'] > 0
        assert abs(sj['started_at'] - time.time()) < 30, 'started_at must be DB time, not app-skewed'
        assert c['set_detail'] == 200 and c['my_set'] == 200 and c['save'] == 200
        assert all(present for _, present in L.values()), L
        if kind == 'competition':
            assert sj.get('competition_end') == pytest.approx(s['end_at'])
    else:
        assert c['preflight'] == 404 and c['start'] == 404, c
        assert c['set_detail'] == 404 and c['my_set'] == 404 and c['save'] == 404, c
        assert res['attempts'] == 0 and res['preflights'] == 0
        assert not res['leak'], res['leak']
        listed = [k for k, (_, present) in L.items() if present]
        assert not listed, f'{kind}/{win} listed at app {offset:+d} in {listed}'


@pytest.mark.parametrize('offset', [7200, -7200])
def test_standard_unscheduled_set_unchanged(offset):
    tag = 'TEST137' + uuid.uuid4().hex[:8]
    res = run(probe(make_set('standard', None, tag), offset, tag))
    res.pop('start_json')
    EV[f'standard_{offset}'] = res
    c, L = res['codes'], res['lists']
    assert c['preflight'] == 200 and c['start'] == 200 and c['set_detail'] == 200 and c['my_set'] == 200 and c['save'] == 200, c
    assert L['public_sets'][1] and L['my_sets'][1] and L['exam_nav'][1], L
    assert res['attempts'] == 1


@pytest.mark.parametrize('case', ['expired_yesterday_app_minus2d', 'valid_tomorrow_app_plus2d', 'valid_today_app_minus2d'])
def test_expires_date_uses_db_date(case):
    today = datetime.now(timezone.utc).date()
    exp, off = {'expired_yesterday_app_minus2d': (today - timedelta(days=1), -2 * 86400),
                'valid_tomorrow_app_plus2d': (today + timedelta(days=1), 2 * 86400),
                'valid_today_app_minus2d': (today, -2 * 86400)}[case]
    tag = 'TEST137' + uuid.uuid4().hex[:8]
    s = make_set('standard', None, tag)
    s['expires'] = exp.isoformat()
    res = run(probe(s, off, tag))
    res.pop('start_json')
    EV[f'expires_{case}'] = res
    c, L = res['codes'], res['lists']
    print('EXPIRES', case, c, L)
    if case.startswith('expired'):
        assert c['preflight'] == 404 and c['start'] == 404 and c['set_detail'] == 404 and c['my_set'] == 404 and c['save'] == 404, c
        assert not any(p for _, p in L.values()) and res['attempts'] == 0 and not res['leak']
    else:
        assert c['preflight'] == 200 and c['start'] == 200 and c['set_detail'] == 200 and c['save'] == 200, c
        assert L['public_sets'][1] and L['my_sets'][1] and L['exam_nav'][1], L


def test_saved_paper_becomes_unavailable_when_db_window_closes():
    async def go():
        tag = 'TEST137' + uuid.uuid4().hex[:8]
        s = make_set('import', WINDOWS['open'], tag)
        await TDB.tejas_sets.insert_one(dict(s))
        async with client() as c:
            sv = await c.post(f'/api/my/tests/saved/{s["id"]}', json={}, headers=S)
            await TDB.tejas_sets.update_one({'id': s['id']}, {'$set': {'end_at': time.time() - 60}})
            H.OFFSET[0] = -7200  # app thinks it is still open
            av = await c.get('/api/my/tests?tab=saved&status=available', headers=S)
            un = await c.get('/api/my/tests?tab=saved&status=unavailable', headers=S)
            H.OFFSET[0] = 0
        return s['id'], tag, sv, av, un
    sid, tag, sv, av, un = run(go())
    a_ids = [i['set_id'] for i in J(av)['items']]
    u_items = {i['set_id']: i for i in J(un)['items']}
    EV['saved_closed'] = {'save': sv.status_code, 'available': sid in a_ids, 'unavailable': sid in u_items}
    assert sv.status_code == 200 and sid not in a_ids and sid in u_items and u_items[sid]['paper'] is None
    assert f'{tag} private' not in un.text


@pytest.mark.parametrize('kind', ['import', 'competition'])
def test_start_key_retry_and_resume_after_window_closes(kind):
    async def go():
        tag = 'TEST137' + uuid.uuid4().hex[:8]
        s = make_set(kind, WINDOWS['open'], tag)
        await TDB.tejas_sets.insert_one(dict(s))
        key = 'TEST_SK137R_' + uuid.uuid4().hex
        body = {'start_key': key, 'device_checked': True}
        async with client() as c:
            pf = await c.post(f'/api/sets/{s["id"]}/preflight', json={}, headers=S)
            r1 = await c.post(f'/api/sets/{s["id"]}/start', json=body, headers=S)
            H.OFFSET[0] = 7200
            r2 = await c.post(f'/api/sets/{s["id"]}/start', json=body, headers=S)
            await TDB.tejas_sets.update_one({'id': s['id']}, {'$set': {'end_at': time.time() + 30}})
            r3 = await c.post(f'/api/sets/{s["id"]}/start', json=body, headers=S)
            r4 = await c.post(f'/api/sets/{s["id"]}/start', json={'start_key': 'TEST_SK137N_' + uuid.uuid4().hex, 'device_checked': True}, headers=S)
            H.OFFSET[0] = 0
        n = await TDB.tejas_attempts.count_documents({'set_id': s['id']})
        return s, pf, r1, r2, r3, r4, n
    s, pf, r1, r2, r3, r4, n = run(go())
    a1, a2, a3 = J(r1), J(r2), J(r3)
    EV[f'resume_{kind}'] = {'codes': [pf.status_code, r1.status_code, r2.status_code, r3.status_code, r4.status_code],
                            'ids_equal': a1['id'] == a2['id'] == a3['id'], 'deadline': [a1['deadline'], a2['deadline'], a3['deadline']], 'attempts': n}
    print('RESUME', kind, EV[f'resume_{kind}'])
    assert pf.status_code == 200 and r1.status_code == 200 and r2.status_code == 200 and r3.status_code == 200
    assert a1['id'] == a2['id'] == a3['id'] and a1['deadline'] == a2['deadline'] == a3['deadline'] and n == 1
    if kind == 'competition':
        assert a1['deadline'] == pytest.approx(min(a1['started_at'] + 600, s['end_at']))
    # a new key while the attempt is still active resumes the same attempt (no second attempt)
    assert r4.status_code == 200 and J(r4)['id'] == a1['id']


# ---------- cron: auth before parse on the actual app ----------
def test_cron_auth_before_parse_actual_app(monkeypatch):
    sec = 'TEST-cron137-' + uuid.uuid4().hex
    monkeypatch.setenv('WEBHOOK_CRON_SECRET', sec)
    ran = []
    monkeypatch.setattr(JB, 'maintenance', lambda: ran.append(1) or asyncio.sleep(0))
    A = {'authorization': 'Bearer ' + sec}
    async def go():
        before = await TDB.tejas_cron_runs.count_documents({}) if 'tejas_cron_runs' in await TDB.list_collection_names() else 0
        cols_before = set(await TDB.list_collection_names())
        counts_before = {n: await TDB[n].count_documents({}) for n in cols_before}
        wid = 'TEST_wh137_' + uuid.uuid4().hex
        P = '/api/cron/maintenance'
        async with client() as c:
            r = {
                'noauth_valid': await c.post(P, json={'event': 'schedule.triggered', 'run_id': 'TEST_r137'}),
                'noauth_malformed': await c.post(P, json={'event': 'nope'}),
                'noauth_nonjson': await c.post(P, content=b'not json{', headers={'content-type': 'application/json'}),
                'noauth_oversize': await c.post(P, content=b'{"event":"schedule.triggered","x":"' + b'a' * 2_000_000 + b'"}', headers={'content-type': 'application/json'}),
                'noauth_textplain': await c.post(P, content=b'x', headers={'content-type': 'text/plain'}),
                'wrongauth_malformed': await c.post(P, json={'event': 'nope'}, headers={'authorization': 'Bearer wrong'}),
                'dupauth': await c.post(P, json={'event': 'schedule.triggered', 'run_id': 'TEST_r137d'}, headers=[('authorization', 'Bearer ' + sec), ('authorization', 'Bearer ' + sec)]),
            }
            cols_mid = set(await TDB.list_collection_names())
            counts_mid = {n: await TDB[n].count_documents({}) for n in cols_mid}
            r.update({
                'auth_malformed': await c.post(P, json={'event': 'nope'}, headers=A),
                'auth_nonjson': await c.post(P, content=b'not json{', headers={**A, 'content-type': 'application/json'}),
                'auth_header_only': await c.post(P, json={'event': 'schedule.triggered'}, headers={**A, 'x-webhook-id': wid}),
                'auth_header_dup': await c.post(P, json={'event': 'schedule.triggered'}, headers={**A, 'x-webhook-id': wid}),
            })
        return r, counts_before, counts_mid
    r, cb, cm = run(go())
    EV['cron137'] = {k: (v.status_code, v.text[:120]) for k, v in r.items()} | {'ran': len(ran), 'db_unchanged_on_reject': cb == cm}
    print('CRON137', EV['cron137'])
    for k in ('noauth_valid', 'noauth_malformed', 'noauth_nonjson', 'noauth_oversize', 'noauth_textplain', 'wrongauth_malformed', 'dupauth'):
        assert r[k].status_code == 401, (k, r[k].status_code, r[k].text[:200])
    assert cb == cm, 'rejected cron calls wrote to DB'
    assert r['auth_malformed'].status_code == 400 and r['auth_nonjson'].status_code == 400
    assert r['auth_header_only'].status_code == 200 and J(r['auth_header_only']).get('accepted') is True
    assert J(r['auth_header_dup']).get('duplicate') is True and len(ran) == 1


def test_http_limits_general_budgets_unchanged():
    async def go():
        async with client() as c:
            return {
                'nonjson_ct_on_json_route': await c.post('/api/sets/x/preflight', content=b'{}', headers={**S, 'content-type': 'text/plain'}),
                'encoded': await c.post('/api/sets/x/preflight', content=b'{}', headers={**S, 'content-type': 'application/json', 'content-encoding': 'gzip'}),
                'oversize': await c.post('/api/sets/x/preflight', content=b'{"a":"' + b'a' * 3_000_000 + b'"}', headers={**S, 'content-type': 'application/json'}),
                'bad_len': await c.post('/api/sets/x/preflight', content=b'{}', headers={**S, 'content-type': 'application/json', 'content-length': 'abc'}),
            }
    r = run(go())
    EV['http_limits'] = {k: (v.status_code, v.text[:100]) for k, v in r.items()}
    print('LIMITS', EV['http_limits'])
    assert r['nonjson_ct_on_json_route'].status_code == 415 and r['encoded'].status_code == 415
    assert r['oversize'].status_code == 413 and r['bad_len'].status_code == 400
