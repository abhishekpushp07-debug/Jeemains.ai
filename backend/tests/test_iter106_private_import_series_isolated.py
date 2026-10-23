"""Iteration 106: hidden private-import -> All India JEE series publication path (TEST-ONLY ISOLATED).
Run: cd /app/backend && python -m pytest tests/test_iter106_private_import_series_isolated.py -p no:asyncio -n0 -v
Reuses iso_harness (dedicated DB, mocked clock, x-test-user auth). Synthetic ready import fixtures only:
no upload, no storage, no LLM. Configured DB counts are compared at teardown.
"""
import asyncio, copy, uuid
import pytest
import iso_harness as H
from test_iter105_live_series_isolated import ist, at, jee_questions, req, data, run, user, start, RULES  # noqa

W = 'all-india-jee-2026-27'


def imp(**over):
    """Realistic complete ready private import (status ready, revision 0 / no set)."""
    iid = str(uuid.uuid4())
    qs = []
    for q in jee_questions():
        q = {k: q[k] for k in ('number', 'subject', 'type', 'text', 'answer', 'solution', 'render_mode', 'q_refs', 's_refs')}
        q['id'] = str(uuid.uuid5(uuid.UUID(iid), str(q['number'])))
        q['options'] = {'A': '1', 'B': '2', 'C': '3', 'D': '4'} if q['type'] == 'mcq' else {}
        q.update(approved=False, accessible_text=q['text'], solution_accessible_text=q['solution'], issues=[], pairing_evidence='TEST id match')
        qs.append(q)
    r = {'id': iid, 'title': 'TEST Private Import ' + iid[:6], 'format': 'pdf', 'fingerprint': 'TEST', 'sources': [],
         'status': 'ready', 'created_at': H.CLOCK[0], 'created_by': 'TEST_U_owner', 'questions': qs, 'issues': [],
         'rights_attested_at': H.CLOCK[0], 'rights_attested_by': 'TEST_U_owner', 'exam': 'JEE Main', 'duration_minutes': 180,
         'message': 'TEST ready'}
    r.update(over)
    run(H.TDB.tejas_imports.insert_one(copy.deepcopy(r)))
    return r


def assign(sid, day, rev=0, who='owner'):
    return req('POST', '/api/studio/all-india-jee/assign', who, json={'set_id': sid, 'date': day, 'expected_revision': rev})


def sset(sid):
    return run(H.TDB.tejas_sets.find_one({'id': sid}, {'_id': 0}))


def slot(day, who=None):
    path = '/api/studio/all-india-jee' if who == 'owner' else '/api/series/all-india-jee'
    return next(s for s in data(req('GET', path, who))['slots'] if s['date'] == day)


def toggle(sid, live):
    return req('POST', f'/api/studio/imports/{sid}/live', 'owner', json={'live': live, 'revision': sset(sid)['revision']})


async def _real_counts():
    real = H.tdbmod.client[H.REAL_DB]
    return {c: await real[c].estimated_document_count() for c in ('tejas_sets', 'tejas_attempts', 'tejas_imports', 'tejas_audits', 'tejas_files')}


@pytest.fixture(scope='module', autouse=True)
def isolated():
    real_counts = run(_real_counts())
    import tejas.ai_solutions as ai, tejas.imports as im
    orig, orig_proc = getattr(ai, 'process', None), im.process_import

    async def boom(*a, **k):
        raise AssertionError('AI/import processing attempted in isolated test')
    ai.process = boom; im.process_import = boom
    assert H.leftover_real_handles() == []
    assert im.imports.database.name == H.TEST_DB
    run(H.tdbmod.client.drop_database(H.TEST_DB)); run(H.tdbmod.indexes())
    for k, r in [('owner', 'owner'), ('reviewer', 'reviewer'), ('A', 'student'), ('B', 'student'), ('C', 'student'), ('D', 'student')]:
        user(k, r)
    yield
    ai.process = orig; im.process_import = orig_proc
    run(H.tdbmod.client.drop_database(H.TEST_DB))
    assert run(_real_counts()) == real_counts, 'configured DB counts changed!'


S = {}


# ---- studio candidates ----
def test_studio_lists_ready_private_import_rev0():
    at('2026-11-20', 10)
    good = imp(); S['good'] = good
    blocked = imp(status='blocked', issues=[{'message': 'x'}]); qa = imp(qa_only=True); short = imp(questions=good['questions'][:74])
    issued = imp(issues=[{'message': 'pending'}]); bitsat = imp(exam='BITSAT')
    d = data(req('GET', '/api/studio/all-india-jee', 'owner'))
    rows = {p['id']: p for p in d['papers']}
    assert rows[good['id']] == {'id': good['id'], 'title': good['title'], 'revision': 0, 'kind': 'private_import'}
    for bad in (blocked, qa, short, issued, bitsat):
        assert bad['id'] not in rows
    assert d['papers'][0]['kind'] == 'private_import'  # prioritised
    assert 'questions' not in str(d['papers'])
    for who in ('A', 'reviewer', None):
        assert req('GET', '/api/studio/all-india-jee', who).status_code in (401, 403)


def test_assign_roles_and_validation_no_partial_sets():
    g = S['good']['id']
    assert assign(g, '2026-12-05', who='A').status_code == 403
    assert assign(g, '2026-12-05', who='reviewer').status_code == 403
    assert assign(g, '2026-12-05', who=None).status_code == 401
    assert assign(g, '2026-11-30').status_code == 422
    assert assign(g, '2027-02-01').status_code == 422
    assert assign(g, '2026-12-05', rev=1).status_code == 409  # stale revision for rev0 import
    assert assign('TEST_missing', '2026-12-05').status_code == 404
    for kw in ({'status': 'blocked', 'issues': [{'message': 'x'}]}, {'qa_only': True}, {'questions': S['good']['questions'][:74]},
               {'issues': [{'message': 'y'}]}, {'exam': 'BITSAT'}, {'duration_minutes': 120}):
        b = imp(**kw)
        assert assign(b['id'], '2026-12-05').status_code in (409, 422), kw
        assert sset(b['id']) is None, kw
    assert sset(g) is None
    assert run(H.TDB.tejas_sets.count_documents({})) == 0


def test_assign_private_import_creates_hidden_series_set():
    g = S['good']['id']
    r = assign(g, '2026-12-05'); assert r.status_code == 200, r.text
    s = sset(g)
    assert s['series_import'] is True and s['competition'] is False and s['series_id'] == W and s['series_date'] == '2026-12-05'
    assert s['status'] == 'published' and s['live_enabled'] and s['revision'] == 1 and s['import_id'] == g
    assert s['start_at'] == ist('2026-12-05', 0, 1) and s['end_at'] == ist('2026-12-05', 23, 59)
    assert s['rights_attested_by'] == 'TEST_U_owner' and len(s['questions']) == 75 and s['rules']['minutes'] == 180
    # import view series fields
    v = data(req('GET', f'/api/studio/imports/{g}', 'owner'))
    assert v['series_import'] and v['series_date'] == '2026-12-05' and v['status'] == 'scheduled' and v['set_id'] == g
    # second assign of same import -> blocked, no duplicate
    assert assign(g, '2026-12-06').status_code == 409  # rev0 stale now that set exists
    assert sset(g)['series_date'] == '2026-12-05' and sset(g)['revision'] == 1


def test_hidden_before_opening():
    g = S['good']['id']
    for t in (('2026-11-20', 10), ('2026-12-04', 23, 59, 59), ('2026-12-05', 0, 0, 59)):
        at(*t)
        sl = slot('2026-12-05')
        assert sl['set_id'] is None and sl['title'] == 'All India JEE Mains · Test 05' and not sl['can_start'], t
        assert req('GET', f'/api/sets/{g}', 'A').status_code in (403, 404), t
        assert g not in str(data(req('GET', '/api/sets', 'A')))
        assert g not in str(data(req('GET', '/api/sets')))
        r = start(g, 'A'); assert r.status_code in (403, 404, 409), (t, r.status_code)
    assert run(H.TDB.tejas_attempts.count_documents({'set_id': g})) == 0
    # studio candidate list must no longer show the import as a fresh private import
    at('2026-11-20', 10)
    kinds = [(p['id'], p['kind']) for p in data(req('GET', '/api/studio/all-india-jee', 'owner'))['papers'] if p['id'] == g]
    assert kinds == [(g, 'paper')]  # still unopened -> may be moved; not duplicated as private_import


def test_duplicate_date_and_race_no_partial():
    at('2026-11-20', 10)
    other = imp()
    assert assign(other['id'], '2026-12-05').status_code == 409
    assert sset(other['id']) is None
    a1, a2 = imp(), imp()

    async def race():
        import test_iter105_live_series_isolated as T
        return await asyncio.gather(*[T._req('POST', '/api/studio/all-india-jee/assign', 'owner', json={'set_id': i, 'date': '2026-12-07', 'expected_revision': 0}) for i in (a1['id'], a2['id'], a1['id'])])
    codes = sorted(r.status_code for r in run(race()))
    assert codes == [200, 409, 409], codes
    assert run(H.TDB.tejas_sets.count_documents({'series_date': '2026-12-07'})) == 1
    assert run(H.TDB.tejas_sets.count_documents({'id': {'$in': [a1['id'], a2['id']]}})) == 1


def test_schedule_input_series_date_validation_direct():
    at('2026-11-20', 10)
    x = imp()
    p = f"/api/studio/imports/{x['id']}/schedule"
    for body in ({'start_at': '2026-12-08T00:02:00+05:30', 'revision': 0, 'series_date': '2026-12-08'},
                 {'start_at': '2026-12-08T00:01:00+05:30', 'revision': 0, 'series_date': '2026-12-09'},
                 {'start_at': '2026-11-30T00:01:00+05:30', 'revision': 0, 'series_date': '2026-11-30'},
                 {'start_at': '2026-12-08T00:01:00+05:30', 'revision': 0, 'series_date': '2026-13-08'},
                 {'start_at': '2026-12-08T00:01:00+05:30', 'revision': 0, 'series_date': '08-12-2026'}):
        r = req('POST', p, 'owner', json=body); assert r.status_code == 422, (body, r.text)
    assert req('POST', p, 'A', json={'start_at': '2026-12-08T00:01:00+05:30', 'revision': 0, 'series_date': '2026-12-08'}).status_code == 403
    assert sset(x['id']) is None
    # opened day rejected
    at('2026-12-08', 0, 1)
    assert req('POST', p, 'owner', json={'start_at': '2026-12-08T00:01:00+05:30', 'revision': 0, 'series_date': '2026-12-08'}).status_code == 422
    assert assign(x['id'], '2026-12-08').status_code in (409, 422)
    assert sset(x['id']) is None


def test_plain_importer_regression_and_no_conversion():
    at('2026-11-20', 10)
    x = imp()
    r = req('POST', f"/api/studio/imports/{x['id']}/schedule", 'owner', json={'start_at': '2026-11-21T10:00:00+05:30', 'revision': 0})
    assert r.status_code == 200, r.text
    s = sset(x['id'])
    assert s['competition'] is True and not s.get('series_import') and not s.get('series_id')
    assert s['end_at'] == s['start_at'] + 10800 and s['start_at'] == ist('2026-11-21', 10)
    # ordinary competition cannot convert via importer series_date nor via series assign
    r = req('POST', f"/api/studio/imports/{x['id']}/schedule", 'owner', json={'start_at': '2026-12-10T00:01:00+05:30', 'revision': 1, 'series_date': '2026-12-10'})
    assert r.status_code == 409
    assert assign(x['id'], '2026-12-10', rev=1).status_code == 409
    assert x['id'] not in [p['id'] for p in data(req('GET', '/api/studio/all-india-jee', 'owner'))['papers']]
    # ordinary reschedule still works before start
    r = req('POST', f"/api/studio/imports/{x['id']}/schedule", 'owner', json={'start_at': '2026-11-22T10:00:00+05:30', 'revision': 1})
    assert r.status_code == 200 and sset(x['id'])['start_at'] == ist('2026-11-22', 10)
    # existing series import cannot be rescheduled via ordinary path
    g = S['good']['id']
    for body in ({'start_at': '2026-11-25T10:00:00+05:30', 'revision': 1}, {'start_at': '2026-12-12T00:01:00+05:30', 'revision': 1, 'series_date': '2026-12-12'}):
        assert req('POST', f'/api/studio/imports/{g}/schedule', 'owner', json=body).status_code == 409
    assert sset(g)['series_date'] == '2026-12-05' and sset(g)['revision'] == 1
    # ordinary ended import cannot re-enable
    at('2026-11-23', 10)
    assert toggle(x['id'], False).status_code == 200
    assert toggle(x['id'], True).status_code == 409
    S['ordinary'] = x['id']


def test_studio_candidates_omit_opened_or_used():
    at('2026-11-20', 10)
    ids = [p['id'] for p in data(req('GET', '/api/studio/all-india-jee', 'owner'))['papers']]
    assert S['good']['id'] in ids
    at('2026-12-05', 0, 1)
    ids = [p['id'] for p in data(req('GET', '/api/studio/all-india-jee', 'owner'))['papers']]
    assert S['good']['id'] not in ids


def test_live_day_full_180_cap_resume():
    g = S['good']['id']
    at('2026-12-05', 0, 1)
    sl = slot('2026-12-05')
    assert sl['set_id'] == g and sl['can_start'] and sl['state'] == 'live'
    r = start(g, 'A'); assert r.status_code == 200, r.text
    a = data(r); S['liveA'] = a['id']
    assert a['mode'] == 'series_live' and a['deadline'] == ist('2026-12-05', 0, 1) + 10800 and a['competition_end'] == ist('2026-12-05', 23, 59)
    assert all('answer' not in q and 'solution' not in q for q in a['questions'])
    at('2026-12-05', 20, 59, 0)
    b = data(start(g, 'B')); S['liveB'] = b['id']
    assert b['deadline'] == ist('2026-12-05', 23, 59)  # capped
    at('2026-12-05', 20, 59, 1)
    assert start(g, 'C').status_code == 409
    at('2026-12-05', 22, 0)
    r = start(g, 'B'); assert r.status_code == 200 and data(r)['id'] == b['id'] and data(r)['deadline'] == b['deadline']


def test_pause_blocks_new_starts_active_attempt_unaffected():
    g = S['good']['id']
    at('2026-12-05', 10)
    c = data(start(g, 'C')); S['liveC'] = c['id']
    before = run(H.TDB.tejas_attempts.find_one({'id': c['id']}, {'_id': 0, 'pack_id': 1, 'deadline': 1, 'started_at': 1, 'mode': 1}))
    assert toggle(g, False).status_code == 200
    assert sset(g)['series_import'] and sset(g)['series_id'] == W
    assert not slot('2026-12-05')['can_start']
    assert start(g, 'D').status_code in (403, 404, 409)
    q = c['questions'][0]
    r = req('PUT', f"/api/attempts/{c['id']}/answers/{q['id']}", 'C', json={'value': 'B', 'revision': 1, 'request_id': uuid.uuid4().hex, 'confidence': 0.5})
    assert r.status_code == 200, r.text
    after = run(H.TDB.tejas_attempts.find_one({'id': c['id']}, {'_id': 0, 'pack_id': 1, 'deadline': 1, 'started_at': 1, 'mode': 1}))
    assert after == before
    # source edit after start: snapshot unchanged
    run(H.TDB.tejas_sets.update_one({'id': g}, {'$set': {'questions.0.text': 'TEST EDITED SOURCE'}}))
    got = data(req('GET', f"/api/attempts/{c['id']}", 'C'))
    assert got['questions'][0]['text'] != 'TEST EDITED SOURCE' and got['deadline'] == before['deadline']
    assert 'pack_id' in before or 'questions' in before
    run(H.TDB.tejas_sets.update_one({'id': g}, {'$set': {'questions.0.text': S['good']['questions'][0]['text']}}))
    # unassign / move opened day blocked
    assert req('DELETE', f'/api/studio/all-india-jee/{g}', 'owner').status_code == 409
    assert assign(g, '2026-12-20', rev=sset(g)['revision']).status_code == 409
    assert req('DELETE', f'/api/studio/all-india-jee/{g}', 'A').status_code == 403
    assert toggle(g, True).status_code == 200 and slot('2026-12-05')['can_start']


def test_next_day_archive_despite_imported_end_at():
    g = S['good']['id']
    at('2026-12-05', 23, 59, 0)
    assert data(req('POST', f"/api/attempts/{S['liveA']}/submit", 'A')) is not None
    at('2026-12-06', 0, 0)
    assert sset(g)['end_at'] < H.CLOCK[0]
    sl = slot('2026-12-05'); assert sl['state'] == 'archive' and sl['can_start']
    r = start(g, 'D'); assert r.status_code == 200, r.text
    d = data(r); S['archD'] = d['id']
    assert d['mode'] == 'series_practice' and d['deadline'] == ist('2026-12-06') + 10800 and not d.get('competition_end')
    assert req('POST', f"/api/attempts/{d['id']}/submit", 'D').status_code in (200, 202)
    r = req('GET', f"/api/attempts/{d['id']}/results", 'D')
    if r.status_code == 202: r = req('GET', f"/api/attempts/{d['id']}/results", 'D')
    assert r.status_code == 200 and data(r)['status'] == 'completed'
    # pause in archive, then reenable after closed day allowed
    assert toggle(g, False).status_code == 200
    assert start(g, 'C').status_code in (403, 404, 409)  # paused: new archive start rejected
    assert toggle(g, True).status_code == 200  # re-enable after closed day allowed for series_import
    r = start(g, 'C'); assert r.status_code == 200, r.text
    assert data(r)['mode'] == 'series_practice' and data(r)['id'] != S['liveC']
    v = data(req('GET', f'/api/studio/imports/{g}', 'owner'))
    S['view_status_after_day'] = v['status']


def test_history_mode_isolation():
    h = data(req('GET', '/api/series/all-india-jee/history', 'A'))
    assert {i['mode'] for i in h['items']} == {'series_live'} and h['latest_result_id'] == S['liveA']
    hd = data(req('GET', '/api/series/all-india-jee/history', 'D'))
    assert [i['mode'] for i in hd['items']] == ['series_practice']


def test_future_unassign_withdrawn_private_and_reassign():
    at('2026-11-20', 10)
    f = imp(); assert assign(f['id'], '2026-12-15').status_code == 200
    assert req('DELETE', f"/api/studio/all-india-jee/{f['id']}", 'owner').status_code == 200
    s = sset(f['id'])
    assert s['status'] == 'withdrawn' and s['live_enabled'] is False and s['series_import'] is True and 'series_date' not in s
    assert req('GET', f"/api/sets/{f['id']}", 'A').status_code in (403, 404)
    assert f['id'] not in str(data(req('GET', '/api/sets', 'A')))
    # re-enable via importer toggle must not expose an unassigned private import
    toggle(f['id'], True)
    assert req('GET', f"/api/sets/{f['id']}", 'A').status_code in (403, 404)
    assert f['id'] not in str(data(req('GET', '/api/sets', 'A')))
    rev = sset(f['id'])['revision']
    cand = [p for p in data(req('GET', '/api/studio/all-india-jee', 'owner'))['papers'] if p['id'] == f['id']]
    assert cand and cand[0]['revision'] == rev
    assert assign(f['id'], '2026-12-16', rev=rev).status_code == 200
    s = sset(f['id'])
    assert s['series_date'] == '2026-12-16' and s['live_enabled'] and s['status'] == 'published' and s['start_at'] == ist('2026-12-16', 0, 1) and s['end_at'] == ist('2026-12-16', 23, 59)
    assert slot('2026-12-16')['set_id'] is None
    at('2026-12-16', 9)
    assert data(start(f['id'], 'A'))['mode'] == 'series_live'


def test_saved_ai_tag_readonly_keys_frozen():
    from tejas.manual_solutions import fingerprint
    g = S['good']['id']
    s = sset(g); q = s['questions'][0]
    tag = {'key': q['answer'], 'agrees': True, 'content_hash': fingerprint(q), 'solution': {'concept': 'TEST concept $E=mc^2$', 'given': ['$m=2$'],
           'steps': [{'title': 'Step', 'explanation': '$K=\\frac{1}{2}mv^2$'}], 'final_answer': q['answer'], 'insight': 'i', 'shortcut': '',
           'common_mistakes': [], 'time_tip': 't'}}
    run(H.TDB.tejas_sets.update_one({'id': g}, {'$set': {'questions.0.ai_solution': tag}}))
    at('2026-12-06', 1)
    r = req('GET', f"/api/attempts/{S['liveA']}/ai-solutions", 'A'); assert r.status_code == 200, r.text
    items = {i['question_id']: i for i in data(r)['items']}
    assert items[q['id']]['state'] == 'ready' and items[q['id']]['solution']['concept'].startswith('TEST')
    assert sum(i['state'] == 'ready' for i in items.values()) == 1
    from tejas.packs import hydrate
    live = run(hydrate(run(H.TDB.tejas_attempts.find_one({'id': S['liveA']}, {'_id': 0}))))
    assert live['questions'][0]['answer'] == q['answer'] and 'ai_solution' not in live['questions'][0]
    assert sset(g)['questions'][0]['answer'] == q['answer']  # original key untouched by read routes
    assert req('GET', f"/api/attempts/{S['liveA']}/ai-solutions", 'B').status_code in (403, 404)


def test_real_db_untouched_mid_run():
    assert H.leftover_real_handles() == []


def test_report_import_view_status_after_day():
    # informational: importer view label for a series import after its day closed (archive)
    print('IMPORT_VIEW_STATUS_AFTER_DAY', S.get('view_status_after_day'))
    assert S.get('view_status_after_day') in ('live', 'scheduled', 'unlive', 'ended', 'archive')
