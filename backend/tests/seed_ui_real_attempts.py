"""Create 3 REAL start/answer/submit JEE full-mock attempts on synthetic TEST_JR_ restricted sets (UI fixture).
Run after seed_ui_journey.py seed; cleaned up by seed_ui_journey.py cleanup."""
import json, sys, time, uuid
sys.argv = sys.argv[:1]
import test_my_tests_journey as T
st = json.load(open('/tmp/jr_ui_state.json')); TAG = st['tag']
s = T.login_phone(T.PHONE)
B = T.BASE_URL
out = []
for i, (correct, wrong) in enumerate([(20, 20), (35, 10), (45, 5)]):
    sid = f'{TAG}-real{i}'
    T.run(T.db.tejas_sets.insert_one({'id': sid, 'title': f'QA Real JEE Full Mock {i + 1}', 'exam': 'JEE Main', 'status': 'published', 'audience': 'restricted',
        'allowed_phones': ['+91' + T.PHONE], 'revision': 1, 'version': 1, 'rules': T.RULES['JEE Main'], 'questions': T.questions('JEE Main'),
        'test_kind': 'mock', 'full_length': True, 'competition': False, 'created_at': time.time(), 'published_at': time.time(), 'rights_report': True}))
    assert s.post(f'{B}/api/sets/{sid}/preflight', json={'test_response': 'ok'}).status_code == 200
    r = s.post(f'{B}/api/sets/{sid}/start', json={'start_key': 'TESTJR' + uuid.uuid4().hex, 'device_checked': True}); assert r.status_code == 200, r.text
    a = T.body(r); aid = a['id']
    qs = a['questions']
    for n, q in enumerate(qs[:correct + wrong]):
        ok = n < correct
        val = ('B' if ok else 'A') if q['type'] == 'mcq' else ('7' if ok else '8')
        rr = s.put(f'{B}/api/attempts/{aid}/answers/{q["id"]}', json={'value': val, 'revision': 1, 'request_id': 'TESTJR' + uuid.uuid4().hex})
        if rr.status_code != 200: print('answer fail', rr.status_code, rr.text[:200]); break
    print('submit', s.post(f'{B}/api/attempts/{aid}/submit').status_code)
    for _ in range(20):
        if s.get(f'{B}/api/attempts/{aid}/results').status_code == 200: break
        time.sleep(1.5)
    out.append(aid)
st['real'] = out; json.dump(st, open('/tmp/jr_ui_state.json', 'w')); print(out)
