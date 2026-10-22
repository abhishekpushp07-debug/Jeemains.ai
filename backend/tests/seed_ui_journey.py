"""Seed/cleanup synthetic TEST_JR_ fixtures for UI testing of My Tests/Results meters/Report priorities.
Usage: python seed_ui_journey.py seed | cleanup   (state saved in /tmp/jr_ui_state.json)."""
import json, sys, time, uuid
sys.argv, MODE = sys.argv[:1], sys.argv[1]
import test_my_tests_journey as T
STATE = '/tmp/jr_ui_state.json'

if MODE == 'seed':
    s = T.login_phone(T.PHONE); o = T.login_phone(T.OTHER_PHONE)
    T.PRE_PROFILES.update(d['_id'] for d in T.run(T.db.tejas_profiles.find({}, {'_id': 1}).to_list(10000)))
    # make fixtures recent so they are not only 30 days old
    J = T.build_journey(s.uid, o.uid)
    sid = f'{T.TAG}-saveset'
    T.run(T.db.tejas_sets.insert_one({'id': sid, 'title': f'QA Saved JEE Paper {T.TAG[-4:]}', 'exam': 'JEE Main', 'status': 'published', 'audience': 'restricted',
        'allowed_phones': ['+91' + T.PHONE], 'revision': 1, 'version': 1, 'rules': T.RULES['JEE Main'], 'questions': T.questions('JEE Main'),
        'test_kind': 'mock', 'full_length': True, 'competition': False, 'created_at': time.time(), 'published_at': time.time()}))
    S = f'{T.TAG}-rset'
    for u in ('u1', 'u2', 'u3'): T.rep(S, 'qA', u, at=1)
    for k in range(3): T.rep(S, 'qB', 'u9', at=50 + k, number=2)
    T.rep(S, 'qC', 'u1', at=2, number=3); T.rep(S, 'qC', 'u2', at=3, number=3)
    json.dump({'tag': T.TAG, 'packs': list(T.PACKS), 'pre_profiles': list(T.PRE_PROFILES), 'J': J, 'saveset': sid}, open(STATE, 'w'))
    print(json.dumps({'tag': T.TAG, 'J': J, 'saveset': sid}))
else:
    st = json.load(open(STATE)); T.TAG = st['tag']; T.PACKS.update(st['packs']); T.PRE_PROFILES.update(st['pre_profiles'])
    real = [a['id'] for a in T.run(T.db.tejas_attempts.find({'set_id': {'$regex': '^' + T.TAG}}, {'id': 1, 'profile': 1, 'pack_id': 1}).to_list(500))]
    T.REAL.extend(real)
    for a in T.run(T.db.tejas_attempts.find({'set_id': {'$regex': '^' + T.TAG}}, {'profile': 1, 'pack_id': 1}).to_list(500)):
        if a.get('profile'): T.PROFILES.add(a['profile']['id'])
        if a.get('pack_id'): T.PACKS.add(a['pack_id'])
    T.run(T.db.tejas_question_reports.delete_many({'set_id': {'$regex': '^' + T.TAG}}))
    T.run(T._cleanup()); print('cleaned', T.TAG, len(real))
