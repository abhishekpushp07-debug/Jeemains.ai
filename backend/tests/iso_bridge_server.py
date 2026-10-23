"""TEST-ONLY MOCKED/ISOLATED browser bridge (iteration 105). NOT production evidence.
Serves the real FastAPI app re-bound to dedicated DB `tejas_isolated_iter105_test` on 127.0.0.1:8765,
clock frozen at 2 Dec 2026 10:00 IST, auth via x-test-user header (injected by Playwright route).
Run: cd /app/backend/tests && python iso_bridge_server.py &   ; drop DB afterwards (exact name only).
"""
import asyncio, uuid, sys
import httpx, uvicorn
import iso_harness as H
from test_iter105_live_series_isolated import jee_questions, ist, RULES  # noqa

SEED = {}
import tejas.ai_solutions as _ai


async def _no_ai(*a, **k):
    raise RuntimeError('AI call blocked in isolated bridge')
_ai.process = _no_ai


async def call(m, path, who, **kw):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=H.app), base_url='http://iso') as c:
        return await c.request(m, path, headers={'x-test-user': who}, **kw)


def mkpaper(title, **over):
    qs = jee_questions()
    for i, q in enumerate(qs):
        q['text'] = f'TEST Q{i+1}: A block of mass $m=2\\,\\text{{kg}}$ moves with $v=3\\,\\text{{m/s}}$. Find $\\frac{{1}}{{2}}mv^2$.'
        if i % 2:
            q.update(solution_kind='ai_generated', solution=f'1. Kinetic energy\n$K=\\frac{{1}}{{2}}mv^2=\\frac{{1}}{{2}}(2)(3)^2=9\\,\\text{{J}}$ (AI solution {i+1})',
                     ai_steps=[{'title': 'Kinetic energy', 'explanation': '$K=\\frac{1}{2}mv^2=9\\,\\text{J}$'}], ai_provenance={'model': 'TEST-fixture-no-call'})
        else:
            q['solution'] = f'Supplied solution {i+1}: $K = 9\\,\\text{{J}}$'
    s = {'id': 'TEST_P_' + uuid.uuid4().hex[:10], 'title': title, 'exam': 'JEE Main', 'version': 1, 'revision': 1,
         'status': 'published', 'audience': 'all', 'questions': qs, 'rules': dict(RULES), 'attribution': 'TEST', 'created_at': 0}
    s.update(over)
    return s


async def seed():
    await H.tdbmod.client.drop_database(H.TEST_DB)
    await H.tdbmod.indexes()
    H.USERS.update({'student': {'id': 'TEST_U_student', 'role': 'student', 'name': 'Test Student', 'phone': '9900000105', 'access_type': 'unverified_phone'},
                    'owner': {'id': 'TEST_U_owner', 'role': 'owner', 'name': 'Test Owner', 'email': 'owner@test.invalid', 'access_type': 'staff_password'}})
    H.CLOCK[0] = ist('2026-11-20', 10)
    p1, p2, p3, std = mkpaper('TEST Series Day 1'), mkpaper('TEST Series Day 2'), mkpaper('TEST Unassigned Paper'), mkpaper('TEST Standard Mock')
    for p in (p1, p2, p3, std):
        await H.TDB.tejas_sets.insert_one(dict(p))
    for p, d in ((p1, '2026-12-01'), (p2, '2026-12-02')):
        r = await call('POST', '/api/studio/all-india-jee/assign', 'owner', json={'set_id': p['id'], 'date': d, 'expected_revision': 1})
        assert r.status_code == 200, r.text
    H.CLOCK[0] = ist('2026-12-01', 10)
    await call('POST', f"/api/sets/{p1['id']}/preflight", 'student', json={})
    a = (await call('POST', f"/api/sets/{p1['id']}/start", 'student', json={'start_key': uuid.uuid4().hex, 'device_checked': True})).json()
    a = a.get('data', a)
    for i, q in enumerate(a['questions'][:40]):
        val = ('B' if i % 3 else 'A') if q['type'] == 'mcq' else '7'
        r = await call('PUT', f"/api/attempts/{a['id']}/answers/{q['id']}", 'student', json={'value': val, 'revision': 1, 'request_id': uuid.uuid4().hex, 'confidence': 0.7})
        if r.status_code >= 300:
            print('answer failed', r.status_code, r.text[:200]); break
    H.CLOCK[0] = ist('2026-12-01', 12)
    print('submit', (await call('POST', f"/api/attempts/{a['id']}/submit", 'student')).status_code)
    H.CLOCK[0] = ist('2026-12-02', 10)
    for _ in range(3):
        r = await call('GET', f"/api/attempts/{a['id']}/results", 'student')
        if r.status_code == 200: break
    print('results', r.status_code)
    SEED.update(p1=p1['id'], p2=p2['id'], std=std['id'], live=a['id'])
    print('SEED', SEED, flush=True)


if __name__ == '__main__':
    asyncio.set_event_loop(asyncio.new_event_loop())
    config = uvicorn.Config(H.app, host='127.0.0.1', port=8765, log_level='warning', lifespan='off')
    server = uvicorn.Server(config)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(seed())
    loop.run_until_complete(server.serve())
