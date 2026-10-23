"""Iteration 109: Personal 62-day live-series streak (TEST-ONLY ISOLATED, dedicated test DB).
Run: cd /app/backend && python -m pytest tests/test_iter109_series_streak_isolated.py -p no:asyncio -n0 -v
Uses iso_harness: every tejas Mongo handle re-bound to tejas_isolated_iter105_test, clock patched,
auth = synthetic X-Test-User. Synthetic attempt docs only. No AI / storage / lifespan.
"""
import asyncio, uuid, json
from datetime import date, timedelta
import httpx, pytest
import iso_harness as H
from test_iter105_live_series_isolated import ist  # noqa

LOOP = asyncio.get_event_loop() if not asyncio.get_event_loop().is_closed() else asyncio.new_event_loop()
asyncio.set_event_loop(LOOP); run = LOOP.run_until_complete
FIRST = date(2026, 12, 1)
COL = H.TDB.tejas_attempts
SID = 'all-india-jee-2026-27'


def d(i):  # day index 0..61 -> iso date
    return (FIRST + timedelta(days=i)).isoformat()


def att(user, day, h=12, **over):
    a = {'id': 'TEST_A_' + uuid.uuid4().hex[:12], 'user_id': user, 'series_id': SID, 'series_date': day,
         'mode': 'series_live', 'status': 'completed', 'submitted_at': ist(day, h), 'parent_attempt': None,
         'reason': 'submitted', 'deadline': ist(day, 23, 59), 'score': 123, 'answers': {'q': 'B'}}
    a.update(over)
    return a


async def _req(path, who):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=H.app), base_url='http://iso') as c:
        return await c.get(path, headers={'x-test-user': who} if who else {})


def streak(who, clock):
    H.CLOCK[0] = clock
    r = run(_req('/api/series/all-india-jee/streak', who))
    r.j = (r.json().get('data') if r.status_code == 200 else r.json())
    return r


def seed(user, docs):
    run(COL.delete_many({'user_id': user}))
    if docs:
        run(COL.insert_many(docs))
    H.USERS[user] = {'id': user, 'role': 'student', 'name': user, 'phone': '9900000109', 'access_type': 'unverified_phone'}


@pytest.fixture(scope='module', autouse=True)
def isolation():
    assert H.TEST_DB != H.REAL_DB and not H.leftover_real_handles()
    import tejas.series_streak as SS
    assert SS.attempts.database.name == H.TEST_DB and SS.now is H.fake_now
    run(H.tdbmod.client.drop_database(H.TEST_DB))
    yield
    run(H.tdbmod.client.drop_database(H.TEST_DB))  # exact dedicated DB only


# --- auth / isolation
def test_unauth_401():
    assert streak(None, ist('2026-12-05', 10)).status_code == 401


def test_prelaunch_zeros():
    seed('TEST_U_pre', [])
    r = streak('TEST_U_pre', ist('2026-11-20', 10)); j = r.j
    assert r.status_code == 200 and j['user_id'] == 'TEST_U_pre' and j['stage'] == 'prelaunch'
    assert (j['completed_count'], j['current_streak'], j['best_streak']) == (0, 0, 0)
    assert len(j['days']) == 62 and all(x['state'] == 'upcoming' for x in j['days']) and j['today_state'] is None
    assert not any(m['earned'] for m in j['milestones']) and j['next_milestone']['days'] == 7


def test_first_day_and_today_grace():
    seed('TEST_U_first', [att('TEST_U_first', d(0), 11)])
    j = streak('TEST_U_first', ist(d(0), 12)).j
    assert (j['completed_count'], j['current_streak'], j['today_state']) == (1, 1, 'completed')
    j = streak('TEST_U_first', ist(d(1), 22)).j  # day 2 not done yet: grace keeps yesterday
    assert j['current_streak'] == 1 and j['today_state'] == 'today'
    j = streak('TEST_U_first', ist(d(2), 0, 30)).j  # day 2 missed -> broken
    assert j['current_streak'] == 0 and j['days'][1]['state'] == 'missed' and j['best_streak'] == 1


@pytest.mark.parametrize('n', [7, 15, 30, 45, 62])
def test_consecutive_cups(n):
    u = f'TEST_U_c{n}'
    seed(u, [att(u, d(i)) for i in range(n)])
    j = streak(u, ist('2027-02-05', 10) if n == 62 else ist(d(n - 1), 20)).j
    assert j['completed_count'] == n and j['best_streak'] == n and j['current_streak'] == n
    earned = {m['days']: m for m in j['milestones'] if m['earned']}
    assert set(earned) == {k for k in (7, 15, 30, 45, 62) if k <= n}
    assert earned[n]['earned_date'] == d(n - 1)


def test_scattered_total_does_not_earn_cup():
    u = 'TEST_U_scatter'
    seed(u, [att(u, d(i)) for i in range(0, 62, 2)])  # 31 alternate days
    j = streak(u, ist('2027-02-02', 10)).j
    assert j['completed_count'] == 31 and j['best_streak'] == 1 and not any(m['earned'] for m in j['milestones'])
    assert j['stage'] == 'finished'


def test_break_restart_best_persists():
    u = 'TEST_U_break'
    seed(u, [att(u, d(i)) for i in range(8)] + [att(u, d(i)) for i in range(10, 13)])
    j = streak(u, ist(d(12), 21)).j
    assert (j['completed_count'], j['current_streak'], j['best_streak']) == (11, 3, 8)
    assert [m['days'] for m in j['milestones'] if m['earned']] == [7]


def test_month_boundaries_and_end_preserved():
    u = 'TEST_U_bound'
    seed(u, [att(u, x) for x in ('2026-12-30', '2026-12-31', '2027-01-01', '2027-01-02')])
    j = streak(u, ist('2027-01-02', 15)).j
    assert j['current_streak'] == 4
    u2 = 'TEST_U_end'
    seed(u2, [att(u2, x) for x in ('2027-01-29', '2027-01-30', '2027-01-31')])
    j = streak(u2, ist('2027-02-01', 0, 5)).j
    assert j['stage'] == 'finished' and j['current_streak'] == 3 and j['best_streak'] == 3
    j = streak(u2, ist('2027-03-15', 9)).j
    assert j['current_streak'] == 3


def test_exclusions_and_dedup():
    u = 'TEST_U_excl'
    docs = [att(u, d(0), 10), att(u, d(0), 14),  # duplicate same date -> 1
            att(u, d(1), mode='practice'), att(u, d(2), mode='retry', parent_attempt='X'),
            att(u, d(3), mode='preview'), att(u, d(4), parent_attempt='TEST_parent'),
            att(u, d(5), submitted_at=ist(d(5), 0, 0, 30)),  # before 00:01
            att(u, d(6), submitted_at=ist(d(7), 0, 10)),  # after close (archive)
            att(u, '2026-11-30'), att(u, '2027-02-01'), att(u, d(11), series_date='2026-12-1'), att(u, d(11), series_date='garbage'),
            att(u, d(8), series_id='other-series'), att('TEST_U_other', d(9)),
            att(u, d(10), status='abandoned')]
    seed(u, docs); H.USERS['TEST_U_other'] = dict(H.USERS[u], id='TEST_U_other')
    j = streak(u, ist(d(12), 10)).j
    assert j['completed_count'] == 1 and j['days'][0]['state'] == 'completed', [x for x in j['days'] if x['state'] == 'completed']
    assert j['days'][9]['state'] == 'missed'  # other user's finish not visible
    assert j['days'][0]['attempt_id'] == docs[0]['id']  # earliest submission chosen
    run(COL.delete_many({'user_id': 'TEST_U_other'}))


def test_future_submission_not_counted():
    u = 'TEST_U_future'
    seed(u, [att(u, d(3), 18)])
    j = streak(u, ist(d(3), 12)).j  # submitted_at in future relative to clock
    assert j['completed_count'] == 0 and j['days'][3]['state'] == 'today'


def test_time_limit_pending_in_progress():
    u = 'TEST_U_tl'
    seed(u, [att(u, d(0), reason='time_limit', submitted_at=ist(d(0), 23, 59)),
             att(u, d(1), status='active', submitted_at=None, deadline=ist(d(1), 13)),
             att(u, d(2), status='active', submitted_at=None, deadline=ist(d(2), 23, 0))])
    j = streak(u, ist(d(2), 15)).j
    assert j['days'][0]['state'] == 'completed'
    assert j['days'][1]['state'] == 'pending' and j['days'][1]['attempt_id']
    assert j['days'][2]['state'] == 'in_progress' and j['today_state'] == 'in_progress' and j['days'][2]['attempt_id']
    assert j['completed_count'] == 1 and j['current_streak'] == 0  # pending day 2 does not count yet
    # seal pending (time_limit) -> counts
    run(COL.update_one({'user_id': u, 'series_date': d(1)}, {'$set': {'status': 'completed', 'submitted_at': ist(d(1), 13), 'reason': 'time_limit'}}))
    j = streak(u, ist(d(2), 15)).j
    assert j['completed_count'] == 2 and j['current_streak'] == 2


def test_no_scores_and_no_writes_and_embargo_safe():
    u = 'TEST_U_c7'
    seed(u, [att(u, d(i), score=999, answer_key={'k': 'A'}) for i in range(7)])
    before = run(COL.find({}, {'_id': 0}).sort('id', 1).to_list(1000))
    cols_before = sorted(run(H.TDB.list_collection_names()))
    for _ in range(3):
        r = streak(u, ist(d(6), 20))
    after = run(COL.find({}, {'_id': 0}).sort('id', 1).to_list(1000))
    assert before == after and sorted(run(H.TDB.list_collection_names())) == cols_before
    data = r.j; data.pop('policy')
    body = json.dumps(data).lower()
    for bad in ('score', 'answer', '999', 'marks', 'rank', 'correct', 'key'):
        assert bad not in body, bad
    assert set(r.j['days'][0]) == {'day', 'date', 'state', 'attempt_id'}
