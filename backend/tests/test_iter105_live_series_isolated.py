"""Iteration 105: All India JEE live series + historical rank (TEST-ONLY ISOLATED, dedicated test DB).
Run: cd /app/backend && python -m pytest tests/test_iter105_live_series_isolated.py -p no:asyncio -n0 -v
Never touches configured DB (handles re-bound in iso_harness). Clock mocked. No AI/provider calls.
"""
import asyncio, copy, uuid
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import httpx, pytest
import iso_harness as H

IST = ZoneInfo('Asia/Kolkata')
LOOP = asyncio.new_event_loop(); asyncio.set_event_loop(LOOP); run = LOOP.run_until_complete
RULES = {'minutes': 180, 'correct': 4, 'wrong': -1, 'skipped': 0, 'navigation': 'free',
         'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'}


def ist(d, h=0, m=0, s=0):
    return datetime.combine(date.fromisoformat(d), datetime.min.time().replace(hour=h, minute=m, second=s), IST).timestamp()


def at(d, h=0, m=0, s=0):
    H.CLOCK[0] = ist(d, h, m, s)


def jee_questions():
    qs, n = [], 0
    for subj in ('Physics', 'Chemistry', 'Mathematics'):
        for kind, cnt in (('mcq', 20), ('integer', 5)):
            for _ in range(cnt):
                n += 1
                q = {'id': str(uuid.uuid4()), 'number': n, 'subject': subj, 'section': subj, 'type': kind,
                     'text': f'TEST_Q {n} $x^{2}$', 'q_refs': [], 's_refs': [], 'render_mode': 'text',
                     'solution': f'TEST supplied solution {n}', 'status': 'approved'}
                q.update({'answer': 'B', 'options': {'A': '1', 'B': '2', 'C': '3', 'D': '4'}} if kind == 'mcq' else {'answer': '7'})
                qs.append(q)
    return qs


def paper(**over):
    s = {'id': 'TEST_P_' + uuid.uuid4().hex[:10], 'title': 'TEST Live paper ' + uuid.uuid4().hex[:4], 'exam': 'JEE Main',
         'version': 1, 'revision': 1, 'status': 'published', 'audience': 'all', 'questions': jee_questions(),
         'rules': dict(RULES), 'attribution': 'TEST', 'created_at': 0}
    s.update(over)
    run(H.TDB.tejas_sets.insert_one(copy.deepcopy(s)))
    return s


def user(key, role='student'):
    u = {'id': 'TEST_U_' + key, 'role': role, 'name': key}
    if role == 'student':
        u.update(access_type='unverified_phone', phone='99000001' + str(abs(hash(key)) % 100).zfill(2))
    else:
        u.update(email=f'{key}@test.invalid', access_type='staff_password')
    H.USERS[key] = u
    return u


async def _req(method, path, who=None, **kw):
    headers = {'x-test-user': who} if who else {}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=H.app), base_url='http://iso') as c:
        r = await c.request(method, path, headers=headers, **kw)
    return r


def req(method, path, who=None, **kw):
    return run(_req(method, path, who, **kw))


def data(r):
    j = r.json(); return j.get('data', j) if isinstance(j, dict) else j


def assign(set_id, day, rev=1, who='owner'):
    return req('POST', '/api/studio/all-india-jee/assign', who, json={'set_id': set_id, 'date': day, 'expected_revision': rev})


def start(set_id, who, key=None):
    pf = req('POST', f'/api/sets/{set_id}/preflight', who, json={'test_response': 'ok'})
    if pf.status_code != 200:
        return pf
    return req('POST', f'/api/sets/{set_id}/start', who, json={'start_key': key or uuid.uuid4().hex, 'device_checked': True})


@pytest.fixture(scope='module', autouse=True)
def isolated():
    real_counts = run(_real_counts())
    import tejas.ai_solutions as ai
    orig = getattr(ai, 'process', None)

    async def no_ai(*a, **k):
        raise AssertionError('AI call attempted in isolated test')
    ai.process = no_ai
    assert H.leftover_real_handles() == []
    run(H.tdbmod.client.drop_database(H.TEST_DB))
    run(H.tdbmod.indexes())
    for k, r in [('owner', 'owner'), ('reviewer', 'reviewer'), ('A', 'student'), ('B', 'student'), ('C', 'student'), ('D', 'student'), ('E', 'student')]:
        user(k, r)
    yield
    ai.process = orig
    run(H.tdbmod.client.drop_database(H.TEST_DB))  # exact dedicated DB only
    assert run(_real_counts()) == real_counts, 'configured DB counts changed!'


async def _real_counts():
    real = H.tdbmod.client[H.REAL_DB]
    return {c: await real[c].estimated_document_count() for c in ('tejas_sets', 'tejas_attempts', 'tejas_sessions', 'tejas_jobs', 'tejas_audits')}


# ---- contracts / schedule ----
def test_routes_registered_with_contracts():
    from tejas.route_contracts import SPEC
    paths = set(H.app.openapi()['paths'])
    for p in ('/api/series/all-india-jee', '/api/series/all-india-jee/history', '/api/studio/all-india-jee',
              '/api/studio/all-india-jee/assign', '/api/studio/all-india-jee/{set_id}'):
        assert p in paths
    for k in ('catalogue', 'history', 'studio_schedule', 'assign', 'unassign'):
        assert 'live_series.' + k in SPEC


def test_schedule_62_slots_before_dec1():
    at('2026-11-30', 23, 59, 59)
    d = data(req('GET', '/api/series/all-india-jee'))
    assert d['total'] == 62 and len(d['slots']) == 62
    assert d['slots'][0]['date'] == '2026-12-01' and d['slots'][-1]['date'] == '2027-01-31'
    assert all(s['state'] == 'upcoming' and not s['can_start'] and s['set_id'] is None for s in d['slots'])
    s0 = d['slots'][0]
    assert s0['opens_at'] == ist('2026-12-01', 0, 1) and s0['last_start_at'] == ist('2026-12-01', 20, 59)
    assert s0['closes_at'] == ist('2026-12-01', 23, 59) and s0['archive_at'] == ist('2026-12-02')
    assert d['today_slot'] is None


# ---- owner assignment ----
STATE = {}


def test_assignment_role_matrix_and_validation():
    at('2026-11-20', 10)
    p = paper(); STATE['p'] = p
    assert assign(p['id'], '2026-12-01', who=None).status_code == 401
    assert assign(p['id'], '2026-12-01', who='A').status_code == 403
    assert assign(p['id'], '2026-12-01', who='reviewer').status_code == 403
    assert req('GET', '/api/studio/all-india-jee', 'A').status_code == 403
    assert assign(p['id'], '2026-11-30').status_code == 422
    assert assign(p['id'], '2027-02-01').status_code == 422
    assert req('POST', '/api/studio/all-india-jee/assign', 'owner', json={'set_id': p['id'], 'date': '2026-12-01', 'expected_revision': 1, 'x': 1}).status_code == 422
    assert assign(p['id'], '2026-12-01', rev=9).status_code == 409
    r = assign(p['id'], '2026-12-01'); assert r.status_code == 200, r.text
    s = run(H.TDB.tejas_sets.find_one({'id': p['id']}))
    assert s['series_date'] == '2026-12-01' and s['revision'] == 2 and s['series_id'] == 'all-india-jee-2026-27'
    # stale CAS after change
    assert assign(p['id'], '2026-12-05', rev=1).status_code == 409
    # duplicate date
    p2 = paper(); STATE['p2'] = p2
    assert assign(p2['id'], '2026-12-01').status_code == 409
    assert run(H.TDB.tejas_sets.find_one({'id': p2['id']})).get('series_date') is None


@pytest.mark.parametrize('kind', ['withdrawn', 'restricted', 'qa', 'competition', 'short', 'minutes', 'marking', 'shape', 'bonus', 'used', 'expires', 'import_window', 'exam'])
def test_invalid_papers_blocked(kind):
    at('2026-11-20', 10)
    qs = jee_questions()
    over = {'withdrawn': {'status': 'withdrawn'}, 'restricted': {'audience': 'restricted'}, 'qa': {'qa_only': True},
            'competition': {'competition': True}, 'short': {'questions': qs[:74]},
            'minutes': {'rules': {**RULES, 'minutes': 170}}, 'marking': {'rules': {**RULES, 'wrong': 0}},
            'exam': {'exam': 'COMEDK'}, 'expires': {'expires': '2026-12-01'},
            'import_window': {'import_id': 'TEST_imp', 'live_enabled': True, 'start_at': ist('2026-11-01'), 'end_at': ist('2026-12-10', 12)}}.get(kind, {})
    if kind == 'shape':
        qs[0]['type'] = 'integer'; over = {'questions': qs}
    if kind == 'bonus':
        qs[0]['bonus'] = True; over = {'questions': qs}
    p = paper(**over)
    if kind == 'used':
        run(H.TDB.tejas_attempts.insert_one({'id': 'TEST_used_' + p['id'], 'user_id': 'x', 'set_id': p['id'], 'mode': 'practice', 'status': 'completed', 'start_key': 'TEST_used_' + p['id']}))
    assert assign(p['id'], '2026-12-10').status_code == 409, kind


def test_studio_schedule_lists_only_valid_papers_and_no_keys():
    at('2026-11-20', 10)
    d = data(req('GET', '/api/studio/all-india-jee', 'owner'))
    ids = {x['id'] for x in d['papers']}
    assert STATE['p2']['id'] in ids
    slot = d['slots'][0]
    assert slot['set_id'] == STATE['p']['id'] and slot['revision'] == 2
    pub = req('GET', '/api/series/all-india-jee').text
    assert '"answer"' not in pub and '"questions"' not in pub and 'TEST supplied solution' not in pub


def test_future_paper_hidden_from_public():
    at('2026-11-30', 23, 0)
    pid = STATE['p']['id']
    assert req('GET', f'/api/sets/{pid}').status_code == 404
    assert pid not in req('GET', '/api/sets').text
    assert pid not in req('GET', '/api/my/tests', 'A').text
    assert req('POST', f'/api/sets/{pid}/preflight', 'A', json={}).status_code == 404
    assert req('POST', f'/api/sets/{pid}/start', 'A', json={'start_key': uuid.uuid4().hex, 'device_checked': True}).status_code == 404
    slot = data(req('GET', '/api/series/all-india-jee'))['slots'][0]
    assert slot['set_id'] is None and not slot['can_start']
    STATE['future_title_leak'] = slot['title'] == STATE['p']['title']


def test_future_title_not_leaked():
    # 'Future paper metadata ... not exposed': public schedule should keep generic title until open
    assert not STATE.get('future_title_leak'), 'Public schedule exposes future paper title before 00:01 IST'


# ---- date boundaries ----
def test_midnight_still_closed_then_0001_live():
    pid = STATE['p']['id']
    at('2026-12-01', 0, 0, 0)
    assert data(req('GET', '/api/series/all-india-jee'))['slots'][0]['state'] == 'upcoming'
    assert start(pid, 'A').status_code == 404
    at('2026-12-01', 0, 1, 0)
    slot = data(req('GET', '/api/series/all-india-jee'))['slots'][0]
    assert slot['state'] == 'live' and slot['can_start'] and slot['set_id'] == pid
    r = start(pid, 'A'); assert r.status_code == 200, r.text
    a = data(r)
    assert a['mode'] == 'series_live' and a['series_date'] == '2026-12-01'
    assert a['deadline'] == ist('2026-12-01', 0, 1) + 10800
    assert a['competition_end'] == ist('2026-12-01', 23, 59)
    assert not any('answer' in q for q in a['questions'])
    STATE['liveA'] = a['id']
    # reassign/remove after opening denied
    assert assign(pid, '2026-12-20', rev=2).status_code == 409
    assert req('DELETE', f'/api/studio/all-india-jee/{pid}', 'owner').status_code == 409


def test_concurrent_starts_single_live_attempt():
    pid = STATE['p']['id']
    at('2026-12-01', 10, 0)
    assert req('POST', f'/api/sets/{pid}/preflight', 'D', json={}).status_code == 200

    async def many():
        return await asyncio.gather(*[_req('POST', f'/api/sets/{pid}/start', 'D', json={'start_key': uuid.uuid4().hex, 'device_checked': True}) for _ in range(6)])
    rs = run(many())
    assert all(r.status_code == 200 for r in rs), [r.text for r in rs]
    assert len({data(r)['id'] for r in rs}) == 1
    assert run(H.TDB.tejas_attempts.count_documents({'user_id': 'TEST_U_D', 'set_id': pid})) == 1


def test_last_start_2059_00_allowed_2059_01_denied():
    pid = STATE['p']['id']
    at('2026-12-01', 20, 58)
    assert req('POST', f'/api/sets/{pid}/preflight', 'B', json={}).status_code == 200
    assert req('POST', f'/api/sets/{pid}/preflight', 'C', json={}).status_code == 200
    at('2026-12-01', 20, 59, 0)
    r = req('POST', f'/api/sets/{pid}/start', 'B', json={'start_key': uuid.uuid4().hex, 'device_checked': True})
    assert r.status_code == 200, r.text
    a = data(r); STATE['liveB'] = a['id']
    assert a['deadline'] == ist('2026-12-01', 23, 59)  # capped at close, not start+180
    at('2026-12-01', 20, 59, 1)
    r = req('POST', f'/api/sets/{pid}/start', 'C', json={'start_key': uuid.uuid4().hex, 'device_checked': True})
    assert r.status_code == 409, r.text
    assert data(req('GET', '/api/series/all-india-jee'))['slots'][0]['state'] == 'start_closed'


def test_resume_after_cutoff_keeps_deadline():
    pid = STATE['p']['id']
    at('2026-12-01', 21, 30)
    r = start(pid, 'B'); assert r.status_code == 200, r.text
    a = data(r)
    assert a['id'] == STATE['liveB'] and a['status'] == 'active' and a['deadline'] == ist('2026-12-01', 23, 59)
    assert data(req('GET', f'/api/attempts/{a["id"]}', 'B'))['deadline'] == a['deadline']


def test_embargo_until_2359_then_release():
    aid = STATE['liveA']
    at('2026-12-01', 12, 0)
    r = req('POST', f'/api/attempts/{aid}/submit', 'A'); assert r.status_code in (200, 202), r.text
    res = data(req('GET', f'/api/attempts/{aid}/results', 'A'))
    assert res['status'] == 'embargoed' and res['release_at'] == ist('2026-12-01', 23, 59)
    assert 'questions' not in res and 'summary' not in res
    assert req('GET', f'/api/attempts/{aid}/historical-rank', 'A').status_code == 403
    assert req('GET', f'/api/attempts/{aid}/results', 'B').status_code in (403, 404)
    h = data(req('GET', '/api/series/all-india-jee/history', 'A'))
    assert h['items'][0]['status'] == 'embargoed' and h['items'][0]['summary'] is None and h['latest_result_id'] is None
    at('2026-12-01', 23, 59, 0)
    r = req('GET', f'/api/attempts/{aid}/results', 'A')
    if r.status_code == 202:
        r = req('GET', f'/api/attempts/{aid}/results', 'A')
    assert r.status_code == 200, r.text
    res = data(r)
    assert res['status'] == 'completed' and res['summary'] is not None and len(res['questions']) == 75
    assert any('TEST supplied solution' in str(q.get('solution', '')) for q in res['questions'])
    h = data(req('GET', '/api/series/all-india-jee/history', 'A'))
    assert h['latest_result_id'] == aid and h['items'][0]['status'] == 'completed'


def test_ended_window_then_midnight_archive_separate():
    pid = STATE['p']['id']
    at('2026-12-01', 23, 59, 30)
    assert data(req('GET', '/api/series/all-india-jee'))['slots'][0]['state'] == 'ended'
    assert start(pid, 'E').status_code == 409
    at('2026-12-02', 0, 0, 0)
    d = data(req('GET', '/api/series/all-india-jee'))
    assert d['slots'][0]['state'] == 'archive' and d['slots'][0]['can_start']
    r = start(pid, 'A'); assert r.status_code == 200, r.text
    a = data(r)
    assert a['mode'] == 'series_practice' and a['id'] != STATE['liveA'] and not a.get('competition_end')
    assert a['deadline'] == ist('2026-12-02') + 10800
    h = data(req('GET', '/api/series/all-india-jee/history', 'A'))
    assert {i['mode'] for i in h['items']} == {'series_live', 'series_practice'} and h['total'] == 2
    # stored live score unchanged
    live = run(H.TDB.tejas_attempts.find_one({'id': STATE['liveA']}))
    assert live['mode'] == 'series_live' and live['status'] == 'completed'


def test_jan31_feb1_boundary():
    at('2026-11-25', 9)
    q = paper(); r = assign(q['id'], '2027-01-31'); assert r.status_code == 200, r.text
    at('2027-01-31', 0, 1)
    assert data(req('GET', '/api/series/all-india-jee'))['slots'][-1]['state'] == 'live'
    assert data(start(q['id'], 'C'))['mode'] == 'series_live'
    at('2027-02-01', 0, 0)
    d = data(req('GET', '/api/series/all-india-jee'))
    assert d['slots'][-1]['state'] == 'archive' and d['today_slot'] is None
    assert data(start(q['id'], 'E'))['mode'] == 'series_practice'


def test_withdrawn_assigned_paper_fails_closed():
    at('2026-11-25', 9)
    w = paper(); assert assign(w['id'], '2026-12-15').status_code == 200
    run(H.TDB.tejas_sets.update_one({'id': w['id']}, {'$set': {'status': 'withdrawn'}}))
    at('2026-12-15', 10)
    slot = [s for s in data(req('GET', '/api/series/all-india-jee'))['slots'] if s['date'] == '2026-12-15'][0]
    assert not slot['ready'] and not slot['can_start'] and slot['set_id'] is None
    assert start(w['id'], 'E').status_code == 404


def test_unassign_future_day():
    at('2026-11-25', 9)
    u = paper(); assert assign(u['id'], '2026-12-20').status_code == 200
    assert req('DELETE', f'/api/studio/all-india-jee/{u["id"]}', 'A').status_code == 403
    assert req('DELETE', f'/api/studio/all-india-jee/{u["id"]}', 'owner').status_code == 200
    assert 'series_date' not in run(H.TDB.tejas_sets.find_one({'id': u['id']}))


def test_history_pagination_and_privacy():
    t = ist('2026-12-20', 12)
    docs = [{'id': f'TEST_H_{i}', 'user_id': 'TEST_U_E', 'set_id': 'x', 'title': 't', 'exam': 'JEE Main', 'version': 1,
             'mode': 'series_practice', 'series_id': 'all-india-jee-2026-27', 'series_date': '2026-12-01', 'started_at': t - i,
             'submitted_at': t - i + 1, 'deadline': t + 10800, 'status': 'completed', 'count': 75, 'summary': {'score': i, 'maximum': 300}, 'answers': {}}
            for i in range(25)]
    for d_ in docs: d_['start_key'] = d_['id']
    docs.append({**docs[0], 'id': 'TEST_H_other', 'start_key': 'TEST_H_other', 'user_id': 'TEST_U_D'})
    docs.append({**docs[0], 'id': 'TEST_H_plain', 'start_key': 'TEST_H_plain', 'mode': 'practice', 'series_id': None})
    run(H.TDB.tejas_attempts.insert_many(docs))
    at('2026-12-21')
    p1 = data(req('GET', '/api/series/all-india-jee/history', 'E'))
    p2 = data(req('GET', '/api/series/all-india-jee/history?page=2', 'E'))
    ids = [i['id'] for i in p1['items'] + p2['items']]
    assert 'TEST_H_other' not in ids and 'TEST_H_plain' not in ids
    assert len(p1['items']) == 20 and p1['total'] >= 25 and len(set(ids)) == len(ids)
    assert req('GET', '/api/series/all-india-jee/history').status_code == 401
    assert req('GET', '/api/series/all-india-jee/history?page=0', 'E').status_code == 422


# ---- historical rank ----
def _completed(exam='JEE Main', score=150, maximum=300, **over):
    if exam == 'JEE Main':
        qs, rules = jee_questions(), dict(RULES)
    elif exam == 'COMEDK':
        qs = [{'id': f'c{i}', 'subject': s, 'section': s, 'type': 'mcq', 'answer': 'A'} for s in ('Physics', 'Chemistry', 'Mathematics') for i in range(60)]
        rules = {**RULES, 'correct': 1, 'wrong': 0}
    else:
        qs = [{'id': f'b{i}', 'subject': 'Physics', 'section': 'Physics', 'type': 'mcq', 'answer': 'A', 'bonus': i >= 130} for i in range(142)]
        rules = {**RULES, 'correct': 3, 'wrong': -1}
    a = {'id': 'TEST_R_' + uuid.uuid4().hex[:8], 'user_id': 'TEST_U_C', 'set_id': 'TEST_rank', 'title': 't', 'exam': exam,
         'version': 1, 'mode': 'practice', 'test_kind': 'mock', 'status': 'completed', 'rules': rules, 'questions': qs,
         'answers': {}, 'started_at': 1, 'submitted_at': 2, 'deadline': 3, 'parent_attempt': None,
         'summary': {'score': score, 'maximum': maximum}}
    a['start_key'] = a['id']
    a.update(over)
    run(H.TDB.tejas_attempts.insert_one(copy.deepcopy(a)))
    return a['id']


def rank(aid, who='C', **params):
    r = req('GET', f'/api/attempts/{aid}/historical-rank', who, params=params)
    return r.status_code, (data(r) if r.status_code == 200 else None)


@pytest.mark.parametrize('score,low,high', [(291, 1, 56), (292, 1, 56), (300, 1, 15), (150, 22156, 28132), (268, 142, 341), (0, 1222184, 1390805)])
def test_jee_exact_rows(score, low, high):
    _, d = rank(_completed(score=score))
    assert d['state'] == 'available' and (d['rank_low'], d['rank_high']) == (low, high)
    assert d['evidence_type'] == 'secondary_published_estimate' and 'Careers360' in d['reference']['title']
    assert 'not an official' in d['reference']['source_scope']


@pytest.mark.parametrize('score', [269, 270, 20, 25, 29, -4, 301])
def test_jee_gaps_malformed_out_of_range_unavailable(score):
    _, d = rank(_completed(score=score))
    assert d['state'] == 'unavailable' and d['rank_low'] is None


def test_comedk_and_bitsat():
    _, d = rank(_completed('COMEDK', 175, 180))
    assert (d['state'], d['rank_low'], d['rank_high']) == ('available', 1, 10) and 'Physics Wallah' in d['reference']['title']
    _, d = rank(_completed('COMEDK', 25, 180)); assert d['state'] == 'unavailable'
    _, d = rank(_completed('BITSAT', 300, 390)); assert d['state'] == 'unavailable' and d['evidence_type'] == 'guidance_only_no_rank_mapping'


@pytest.mark.parametrize('variant', ['retry', 'preview', 'corrected', 'minutes', 'maximum', 'type', 'chapter'])
def test_incompatible_rank_rejected(variant):
    params = {}
    over = {'retry': {'parent_attempt': 'TEST_parent'}, 'preview': {'mode': 'preview'},
            'minutes': {'rules': {**RULES, 'minutes': 120}}, 'maximum': {'summary': {'score': 150, 'maximum': 240}},
            'chapter': {'test_kind': 'chapter'}}.get(variant, {})
    if variant == 'type':
        qs = jee_questions(); qs[0]['type'] = 'integer'; over = {'questions': qs}
    if variant == 'corrected':
        params = {'score_version': 'corrected'}
    _, d = rank(_completed(**over), **params)
    assert d['state'] == 'unavailable', variant


def test_rank_foreign_attempt_denied():
    aid = _completed()
    assert rank(aid, 'D')[0] in (403, 404)
    assert req('GET', f'/api/attempts/{aid}/historical-rank').status_code == 401


# ---- regression: standard practice ----
def test_standard_practice_unchanged():
    at('2026-12-05', 10)
    p = paper()
    assert p['id'] in req('GET', '/api/sets?exam=JEE%20Main').text
    a = data(start(p['id'], 'C'))
    assert a['mode'] == 'practice' and not a.get('series_id') and a['deadline'] == ist('2026-12-05', 10) + 10800


# ---- regression: BITSAT bonus (synthetic 130+12) unaffected by series code ----
def test_bitsat_bonus_unlock_regression():
    at('2026-12-06', 9)
    qs = []
    for i in range(142):
        qs.append({'id': str(uuid.uuid4()), 'number': i + 1, 'subject': 'Physics', 'section': 'Physics', 'type': 'mcq', 'text': f'TEST B{i}',
                   'answer': 'A', 'options': {'A': '1', 'B': '2', 'C': '3', 'D': '4'}, 'q_refs': [], 's_refs': [], 'render_mode': 'text', 'bonus': i >= 130})
    p = paper(exam='BITSAT', questions=qs, rules={**RULES, 'correct': 3, 'wrong': -1, 'bonus_rule': {'main_count': 130, 'bonus_count': 12}})
    a = data(start(p['id'], 'B'))
    assert a['mode'] == 'practice' and not a.get('series_id')
    assert req('POST', f"/api/attempts/{a['id']}/bonus", 'B', json={}).status_code == 409
    for q in a['questions']:
        if not q.get('bonus'):
            r = req('PUT', f"/api/attempts/{a['id']}/answers/{q['id']}", 'B', json={'value': 'A', 'revision': 1, 'request_id': uuid.uuid4().hex})
            assert r.status_code < 300, r.text
    r = req('POST', f"/api/attempts/{a['id']}/bonus", 'B', json={})
    assert r.status_code == 200, r.text
