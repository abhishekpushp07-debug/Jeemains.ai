"""TEST-ONLY MOCKED/ISOLATED browser bridge (iteration 113) for BITSAT branch matches UI. NOT production evidence.
DB `tejas_isolated_iter105_test` (dedicated, dropped by tester after use), port 8765. Auth via x-test-user header.
Seeds a full 130+12 BITSAT set + completed practice attempts (310 main + 9 bonus = 319; 200 main; chapter incompatible).
Run: cd /app/backend/tests && python iso_bridge_bitsat_iter113.py &
"""
import asyncio, copy
import uvicorn
import iso_harness as H
from test_iter113_bitsat_branches_isolated import bitsat_attempt, RULES

SEED = {}


async def seed():
    await H.tdbmod.client.drop_database(H.TEST_DB)
    await H.tdbmod.indexes()
    for k in ('student', 'other'):
        H.USERS[k] = {'id': 'TEST_U_' + k, 'role': 'student', 'name': 'Test ' + k, 'phone': '99000001' + str(len(k)).zfill(2),
                      'access_type': 'unverified_phone'}
    good = bitsat_attempt('student', set_id='TEST_S_BITSAT', title='TEST BITSAT Full Mock')
    s = {'id': 'TEST_S_BITSAT', 'title': 'TEST BITSAT Full Mock', 'exam': 'BITSAT', 'version': 1, 'revision': 1, 'status': 'published',
         'audience': 'all', 'test_kind': 'mock', 'questions': [{k: v for k, v in q.items()} for q in good['questions']],
         'rules': dict(RULES), 'attribution': 'TEST', 'created_at': 0}
    await H.TDB.tejas_sets.insert_one(copy.deepcopy(s))
    low = bitsat_attempt('student', n_correct=70, n_wrong=10, set_id='TEST_S_BITSAT', title='TEST BITSAT Low')
    chap = bitsat_attempt('student', test_kind='chapter', set_id='TEST_S_BITSAT', title='TEST BITSAT Chapter')
    other = bitsat_attempt('other', set_id='TEST_S_BITSAT', title='TEST BITSAT Other')
    for i, a in enumerate((good, low, chap, other)):
        a['start_key'] = 'TEST_K' + str(i); a['submitted_at'] = H.CLOCK[0] - 3600 * (i + 1); a['started_at'] = a['submitted_at'] - 3 * 3600
        await H.TDB.tejas_attempts.insert_one(copy.deepcopy(a))
    SEED.update(good=good['id'], low=low['id'], chap=chap['id'], other=other['id'])
    print('SEED113', SEED, good['summary']['score'], low['summary']['main_block']['score'], flush=True)


if __name__ == '__main__':
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(seed())
    loop.run_until_complete(uvicorn.Server(uvicorn.Config(H.app, host='127.0.0.1', port=8765, log_level='warning', lifespan='off')).serve())
