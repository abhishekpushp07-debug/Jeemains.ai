"""TEST-ONLY MOCKED/ISOLATED browser bridge (iteration 109) for the 62-day streak UI. NOT production evidence.
DB `tejas_isolated_iter105_test` (dedicated, dropped by the tester after use), port 8765.
Each synthetic user has its own frozen IST clock (set per request from the x-test-user header).
Synthetic completed/active series_live attempt docs only. No lifespan, no AI, no storage.
Run: cd /app/backend/tests && python iso_bridge_streak_iter109.py &
"""
import asyncio, uuid
from datetime import date, timedelta
import uvicorn
import iso_harness as H
from test_iter105_live_series_isolated import ist  # noqa

FIRST = date(2026, 12, 1)
SID = 'all-india-jee-2026-27'
d = lambda i: (FIRST + timedelta(days=i)).isoformat()


def att(user, day, h=12, **over):
    a = {'id': f'TEST_A_{user}_{day}', 'user_id': user, 'series_id': SID, 'series_date': day, 'mode': 'series_live',
         'status': 'completed', 'submitted_at': ist(day, h), 'parent_attempt': None, 'reason': 'submitted',
         'deadline': ist(day, 23, 59)}
    a.update(over)
    return a


CLOCKS = {'pre': ist('2026-11-20', 10), 'seven': ist(d(6), 20), 'missed': ist(d(13), 15),
          'full': ist('2027-02-02', 10), 'fresh': ist(d(2), 10)}
DOCS = ([att('seven', d(i)) for i in range(7)]
        + [att('missed', d(i)) for i in list(range(8)) + [10, 11]]
        + [att('missed', d(12), status='active', submitted_at=None, deadline=ist(d(12), 15)),
           att('missed', d(13), status='active', submitted_at=None, deadline=ist(d(13), 18))]
        + [att('full', d(i)) for i in range(62)])


async def seed():
    await H.tdbmod.client.drop_database(H.TEST_DB)
    await H.TDB.tejas_attempts.insert_many(DOCS)
    for k in CLOCKS:
        H.USERS[k] = {'id': 'TEST_U_' + k, 'role': 'student', 'name': 'Test ' + k, 'phone': '99000001' + str(len(k)).zfill(2),
                      'access_type': 'unverified_phone'}
    # attempt docs use short ids; rewrite to the synthetic user ids
    for k in CLOCKS:
        await H.TDB.tejas_attempts.update_many({'user_id': k}, {'$set': {'user_id': 'TEST_U_' + k}})
    print('SEED109 ok', await H.TDB.tejas_attempts.count_documents({}), flush=True)


async def app(scope, receive, send):
    if scope['type'] == 'http':
        who = dict(scope['headers']).get(b'x-test-user', b'').decode()
        H.CLOCK[0] = CLOCKS.get(who, ist(d(2), 10))
    await H.app(scope, receive, send)


if __name__ == '__main__':
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(seed())
    loop.run_until_complete(uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=8765, log_level='warning', lifespan='off')).serve())
