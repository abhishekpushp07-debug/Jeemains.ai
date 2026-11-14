"""TEST-ONLY iteration 176 profile of the answer-save hot path (isolated DB, dropped at the end)."""
import asyncio, copy, cProfile, io, os, pstats, secrets, sys, time, uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ['TEJAS_ISO_DB'] = 'tejas_isolated_prof176_' + secrets.token_hex(3)
import iso_harness_scale176 as H  # noqa: E402
import httpx  # noqa: E402

PID, N = 'jee-main-pyq-2025-04-02-s1', 100


async def main():
    TDB = H.TDB
    await H.tdbmod.client.drop_database(H.TEST_DB); await H.tdbmod.indexes()
    for name, rows in H.DATA['collections'].items():
        await TDB[name].insert_many([copy.deepcopy(r) for r in rows])
    from tejas import auth
    exp = datetime.now(timezone.utc) + timedelta(days=1); cookies = []
    for i in range(N):
        uid = 'TEST_P176_%03d' % i; u = {'_id': uid, 'id': uid, 'phone': '+9199300%05d' % i, 'role': 'student', 'access_type': 'unverified_phone', 'pin_version': 1, 'exam': 'JEE Main', 'name': 'T'}
        sid = str(uuid.uuid4()); await TDB.tejas_phone_profiles.insert_one(u)
        await TDB.tejas_sessions.insert_one({'id': sid, 'user_id': uid, 'access_type': 'unverified_phone', 'pin_version': 1, 'expires_at': exp})
        cookies.append({'access_token': auth.token(u, sid, 'access', 3600)})
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=H.app), base_url='https://api.test.example', timeout=60) as c:
        att = []
        for i in range(N):
            await c.post(f'/api/sets/{PID}/preflight', json={'test_response': 'ok'}, cookies=cookies[i])
            r = await c.post(f'/api/sets/{PID}/start', json={'start_key': str(uuid.uuid4()), 'device_checked': True}, cookies=cookies[i])
            att.append(r.json()['data'])
        jobs = [(i, a['id'], q['id'], sorted(q['options'])[0]) for i, a in enumerate(att) for q in a['questions'] if q['type'] == 'mcq'][:2000]
        prof = cProfile.Profile(); t = time.process_time(); prof.enable()
        for k in range(0, len(jobs), 20):
            await asyncio.gather(*[c.put(f'/api/attempts/{aid}/answers/{qid}', json={'value': v, 'revision': 1, 'request_id': str(uuid.uuid4())}, cookies=cookies[i]) for i, aid, qid, v in jobs[k:k + 20]])
        prof.disable(); cpu = time.process_time() - t
    s = io.StringIO(); pstats.Stats(prof, stream=s).sort_stats('tottime').print_stats(30); print(s.getvalue()[:6000])
    s = io.StringIO(); pstats.Stats(prof, stream=s).sort_stats('cumulative').print_stats('tejas|server|starlette|fastapi|pydantic|motor|pymongo|jwt|httpx', 45); print(s.getvalue()[:9000])
    print('cpu_ms_per_save', round(1000 * cpu / len(jobs), 2))
    await H.tdbmod.client.drop_database(H.TEST_DB)


asyncio.run(main())
