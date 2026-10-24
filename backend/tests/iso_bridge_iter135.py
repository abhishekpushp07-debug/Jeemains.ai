"""TEST-ONLY bridge (iteration 135) for the Player deadline/status UI. NOT production evidence.
Isolated DB tejas_isolated_iter134 (dropped on start and on stop). Auth: X-Test-User header (MOCKED, synthetic).
Grade dispatch replaced by a no-op recorder (no jobs/AI). Lifespan off (no seed_owner/worker).
Controls (outer ASGI wrapper, never part of the app):
  GET /__test/seed?deadline_in=SECONDS -> {"id": ...}   creates a synthetic active attempt for user 's'
  GET /__test/fail_status?n=N         -> next N /status calls return 503 Retry-After:1 (simulated overload)
  GET /__test/calls                   -> counts of /status and full attempt GETs seen
Port 8790. Run: cd /app/backend/tests && python iso_bridge_iter135.py &
"""
import asyncio, json, time, uuid
from urllib.parse import parse_qs
import uvicorn
import iso_harness_iter134 as H
from tejas import attempts as AT, packs as PK

assert H.TEST_DB != H.REAL_DB and not H.leftover_real_handles()
STUDENT = {'id': 'TEST_U135_bridge', 'role': 'student', 'name': 'TEST Bridge 135', 'phone': '+919900000136', 'access_type': 'unverified_phone', 'exam': 'JEE Main'}
H.USERS['s'] = STUDENT
STATE = {'fail': 0, 'status_calls': 0, 'status_503': 0, 'full_gets': 0}


async def _no_grade(a, bg=None):
    return None
AT.ensure_grade = _no_grade


def qs(n=3):
    return [{'id': str(uuid.uuid4()), 'number': i + 1, 'type': 'mcq', 'subject': 'Physics', 'section': 'A',
             'options': {'A': 'alpha', 'B': 'beta', 'C': 'gamma', 'D': 'delta'}, 'answer': 'A',
             'text': f'TEST_135 synthetic question {i + 1}: which option is first?', 'solution': 'TEST solution'} for i in range(n)]


async def seed(deadline_in):
    a = {'id': 'TEST_A135B_' + uuid.uuid4().hex, 'user_id': STUDENT['id'], 'set_id': 'TEST_S135B_' + uuid.uuid4().hex[:8], 'title': 'TEST 135 deadline',
         'exam': 'JEE Main', 'mode': 'practice', 'version': 1, 'rules': {'minutes': 1, 'correct': 4, 'wrong': -1, 'skipped': 0}, 'status': 'active',
         'answers': {}, 'first_answers': {}, 'server_seq': 0, 'command_count': 0, 'visited': [], 'test_kind': 'mock', 'profile': {},
         'started_at': time.time(), 'deadline': time.time() + deadline_in, 'questions': qs(), 'parent_attempt': None,
         'start_key': 'TEST_K135B_' + uuid.uuid4().hex}
    await PK.insert_attempt(a)
    return a['id']


async def send_json(send, obj, status=200, headers=()):
    body = json.dumps(obj).encode()
    await send({'type': 'http.response.start', 'status': status, 'headers': [(b'content-type', b'application/json'), *headers]})
    await send({'type': 'http.response.body', 'body': body})


async def wrapper(scope, receive, send):
    if scope['type'] != 'http':
        return await H.app(scope, receive, send)
    path, q = scope['path'], parse_qs(scope.get('query_string', b'').decode())
    if path == '/__test/seed':
        return await send_json(send, {'id': await seed(float(q.get('deadline_in', ['600'])[0]))})
    if path == '/__test/fail_status':
        STATE['fail'] = int(q.get('n', ['0'])[0]); return await send_json(send, STATE)
    if path == '/__test/calls':
        return await send_json(send, STATE)
    if path.startswith('/api/attempts/') and path.endswith('/status'):
        STATE['status_calls'] += 1
        if STATE['fail'] > 0:
            STATE['fail'] -= 1; STATE['status_503'] += 1
            return await send_json(send, {'data': None, 'error': {'code': 'capacity_busy', 'message': 'TEST simulated busy'}, 'meta': {'api_version': '1'}}, 503, [(b'retry-after', b'1')])
    elif path.startswith('/api/attempts/') and path.count('/') == 3 and scope['method'] == 'GET':
        STATE['full_gets'] += 1
    return await H.app(scope, receive, send)


if __name__ == '__main__':
    loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
    loop.run_until_complete(H.tdbmod.client.drop_database(H.TEST_DB))
    loop.run_until_complete(H.tdbmod.indexes())
    try:
        loop.run_until_complete(uvicorn.Server(uvicorn.Config(wrapper, host='127.0.0.1', port=8790, log_level='warning', lifespan='off')).serve())
    finally:
        loop.run_until_complete(H.tdbmod.client.drop_database(H.TEST_DB))
