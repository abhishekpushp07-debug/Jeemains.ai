"""Iteration 116: ISOLATED end-to-end JEE chapter attempt flow against the TEST-ONLY bridge (iso_bridge_jee_iter116.py, port 8765).
Bridge DB = tejas_isolated_iter105_test (dedicated); auth = X-Test-User header (TEST-ONLY MOCKED). Never touches customer DB.
Run (bridge must be up): cd /app/backend && python -m pytest tests/test_iter116_jee_attempt_flow_isolated.py -p no:asyncio -n0 -v
"""
import json, time, uuid
import pytest, requests

B = 'http://127.0.0.1:8765'
CH1 = {'Physics': 90, 'Mathematics': 120, 'Chemistry': 70}
STATE = {}


def call(method, path, who='student', **kw):
    r = requests.request(method, B + path, headers={'x-test-user': who} if who else {}, timeout=120, **kw)
    try:
        j = r.json(); body = j['data'] if isinstance(j, dict) and 'data' in j else j
    except ValueError:
        body = None
    return r, body


def chapter1(subject):
    _, b = call('GET', f'/api/exam-navigation/jee-main/catalogue', params={'kind': 'chapters', 'subject': subject})
    return next(i for i in b['items'] if i.get('chapter_number', 1) == 1)


@pytest.mark.parametrize('subject', list(CH1))
def test_preflight_start_deadline_resume(subject):
    s = chapter1(subject)
    assert s['rules']['minutes'] == CH1[subject] and s['rules']['correct'] == 4 and s['rules']['wrong'] == -1
    r, d = call('POST', f"/api/sets/{s['id']}/preflight", json={'test_response': 'ok'})
    assert r.status_code == 200 and d['ok'], r.text
    key = 'TEST116-' + uuid.uuid4().hex
    r, a = call('POST', f"/api/sets/{s['id']}/start", json={'start_key': key, 'device_checked': True})
    assert r.status_code == 200, r.text
    assert abs(a['deadline'] - a['started_at'] - CH1[subject] * 60) < 1
    assert len(a['questions']) == 50 and a['test_kind'] == 'chapter'
    blob = json.dumps(a['questions'])
    assert '"answer"' not in blob and 's_refs' not in blob and '10-mark solution' not in blob, 'key/solution leak in active attempt'
    r2, a2 = call('POST', f"/api/sets/{s['id']}/start", json={'start_key': key, 'device_checked': True})
    assert a2['id'] == a['id'] and a2['deadline'] == a['deadline']
    r3, a3 = call('GET', f"/api/attempts/{a['id']}")
    assert r3.status_code == 200 and a3['deadline'] == a['deadline']
    r4, a4 = call('POST', f"/api/sets/{s['id']}/start", json={'start_key': 'TEST116-' + uuid.uuid4().hex, 'device_checked': True})
    assert a4['id'] == a['id'] and a4['deadline'] == a['deadline'], 'resume of active attempt must keep deadline'
    STATE[subject] = (s, a)


def test_no_solution_before_submit_and_ownership():
    s, a = STATE['Chemistry']
    q = a['questions'][0]
    r, _ = call('GET', f"/api/attempts/{a['id']}/results")
    assert r.status_code == 403
    r, _ = call('GET', f"/api/attempts/{a['id']}/questions/{q['id']}/asset/solution/0")
    assert r.status_code in (403, 404), r.status_code
    r, _ = call('GET', f"/api/attempts/{a['id']}/questions/{q['id']}/asset/question/0")
    assert r.status_code == 200 and r.content[:4] == b'\x89PNG'
    r, _ = call('GET', f"/api/attempts/{a['id']}", who='other')
    assert r.status_code == 404
    r, d = call('GET', f"/api/sets/{s['id']}")
    assert r.status_code == 200 and '"answer"' not in r.text and 's_refs' not in r.text
    for path in ('/api/studio/chapter-books', f"/api/studio/chapter-books/{s['chapter_book_id']}/chapters/{s['id']}",
                 f"/api/studio/chapter-books/{s['chapter_book_id']}/chapters/{s['id']}/questions/{q['id']}/asset/solution/0"):
        r, _ = call('GET', path)
        assert r.status_code == 403, (path, r.status_code)


def put_answer(a, qid, value, rev=1):
    return call('PUT', f"/api/attempts/{a['id']}/answers/{qid}", json={'value': value, 'revision': rev, 'request_id': 'TEST116-' + uuid.uuid4().hex})


def test_chem_answers_submit_score():
    s, a = STATE['Chemistry']
    # Answer key from owner preview (isolated owner principal)
    _, prev = call('GET', f"/api/studio/chapter-books/{s['chapter_book_id']}/chapters/{s['id']}", who='owner')
    key = {q['number']: q for q in prev['questions']}
    assert [key[n]['type'] for n in (31, 32, 33, 34)].count('integer') >= 2
    qs = {q['number']: q for q in a['questions']}
    plan = {}
    for n in (1, 2, 3):  # correct MCQ
        plan[n] = key[n]['answer']
    wrong_mcq = next(o for o in 'ABCD' if o != key[4]['answer']); plan[4] = wrong_mcq
    ints = [n for n in (31, 32, 33, 34) if key[n]['type'] == 'integer']
    plan[ints[0]] = key[ints[0]]['answer']  # correct integer
    plan[ints[1]] = str(int(float(key[ints[1]]['answer'])) + 7)  # wrong integer
    for n, v in plan.items():
        r, d = put_answer(a, qs[n]['id'], v)
        assert r.status_code == 200, (n, r.text)
    r, _ = put_answer(a, qs[5]['id'], 'Z')
    print('invalid MCQ value status', r.status_code)
    r, rec = call('POST', f"/api/attempts/{a['id']}/submit")
    assert r.status_code in (200, 202), r.text
    for _ in range(20):
        r, res = call('GET', f"/api/attempts/{a['id']}/results")
        if r.status_code == 200:
            break
        time.sleep(1.5)
    assert r.status_code == 200, r.text
    summ = res['summary']
    print('SUMMARY', json.dumps(summ)[:600])
    assert summ['score'] == 4 * 4 - 1 * 2, summ
    assert summ.get('correct') == 4 and summ.get('incorrect') == 2 and summ['skipped'] == 44 and summ['maximum'] == 200
    rq = {q['number']: q for q in res['questions']}
    assert str(rq[ints[0]]['answer']) == str(key[ints[0]]['answer'])
    assert rq[ints[0]].get('solution_kind') == 'supplied_worked' and '10-mark solution' in rq[ints[0]]['solution']
    r, _ = call('GET', f"/api/attempts/{a['id']}/questions/{qs[31]['id']}/asset/solution/0")
    assert r.status_code == 200 and r.content[:4] == b'\x89PNG'
    r, ai = call('POST', f"/api/attempts/{a['id']}/solutions/{qs[1]['id']}")
    assert r.status_code == 410
    STATE['chem_attempt'] = a['id']; STATE['chem_ints'] = ints


def test_other_subjects_blank_and_wrong():
    for subj in ('Physics', 'Mathematics'):
        s, a = STATE[subj]
        _, prev = call('GET', f"/api/studio/chapter-books/{s['chapter_book_id']}/chapters/{s['id']}", who='owner')
        k = {q['number']: q for q in prev['questions']}
        qs = {q['number']: q for q in a['questions']}
        put_answer(a, qs[1]['id'], k[1]['answer'] if k[1]['type'] == 'mcq' else k[1]['answer'])
        n2 = 2; v = (next(o for o in 'ABCD' if o != k[n2]['answer']) if k[n2]['type'] == 'mcq' else str(int(float(k[n2]['answer'])) + 3))
        put_answer(a, qs[n2]['id'], v)
        call('POST', f"/api/attempts/{a['id']}/submit")
        for _ in range(20):
            r, res = call('GET', f"/api/attempts/{a['id']}/results")
            if r.status_code == 200: break
            time.sleep(1.5)
        assert res['summary']['score'] == 3, (subj, res['summary'])
        STATE[subj + '_attempt'] = a['id']
    print('ATTEMPTS', {k: v for k, v in STATE.items() if k.endswith('attempt')})
    with open('/tmp/iter116_attempts.json', 'w') as f:
        json.dump({k: v for k, v in STATE.items() if k.endswith('attempt') or k == 'chem_ints'}, f)


def test_owner_book_view():
    r, b = call('GET', '/api/studio/chapter-books', who='owner')
    assert r.status_code == 200
    by = {x['subject']: x for x in b['items']}
    assert {k: (v['exam'], v['minutes'], len(v['chapters']), v['count']) for k, v in by.items()} == {
        'Physics': ('JEE Main', 90, 29, 1450), 'Mathematics': ('JEE Main', 120, 26, 1300), 'Chemistry': ('JEE Main', 70, 23, 1150)}
    assert all(v['solution_kind'] == 'supplied_worked' for v in by.values())
