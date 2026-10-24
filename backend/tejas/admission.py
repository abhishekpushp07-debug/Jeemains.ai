import time
from .contracts import error_response
from .runtime import INFLIGHT_LIMITS

BUCKETS = (0.005, 0.025, 0.1, 0.3, 1.0, 3.0, 10.0)


def workload(path, method):
    if path == '/api/health' and method == 'GET':
        return None
    if path == '/api/ready':
        return 'probe'
    if path in ('/api/auth/login', '/api/auth/phone', '/api/auth/register'):
        return 'auth'
    if '/asset/' in path or path.endswith('/download') or '/source/' in path:
        return 'asset'
    if path.startswith(('/api/studio/', '/api/internal/', '/api/cron/')):
        return 'control'
    if path.startswith('/api/attempts/') and path.endswith('/status'):
        return 'live'
    if path.startswith('/api/auth/') or path.startswith('/api/attempts/') and method != 'GET' or path.endswith('/start'):
        return 'live'
    return 'read'


class AdmissionGate:
    def __init__(self, app, owner):
        self.app = app
        self.started = time.monotonic()
        self.lanes = {name: {'limit': limit, 'in_flight': 0, 'peak': 0, 'admitted': 0,
                            'rejected': 0, 'completed': 0, 'failed': 0,
                            'response_bytes': 0, 'duration_buckets': [0] * (len(BUCKETS) + 1)}
                      for name, limit in INFLIGHT_LIMITS.items()}
        owner.state.admission = self

    def snapshot(self):
        return {'scope': 'THIS_PROCESS_ONLY', 'capacity_qualified': False,
                'uptime_seconds': round(time.monotonic() - self.started, 3),
                'duration_bucket_upper_seconds': list(BUCKETS) + [None],
                'lanes': {key: {**value, 'duration_buckets': list(value['duration_buckets'])}
                          for key, value in self.lanes.items()}}

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or not scope.get('path', '').startswith('/api/') or scope['method'] == 'OPTIONS':
            return await self.app(scope, receive, send)
        name = workload(scope['path'], scope['method'])
        if name is None:
            return await self.app(scope, receive, send)
        lane = self.lanes[name]
        if lane['in_flight'] >= lane['limit']:
            lane['rejected'] += 1
            response = error_response('This service is busy. Your saved work is safe; retry shortly.', 503, 'capacity_busy')
            response.headers['Retry-After'] = '2'
            return await response(scope, receive, send)
        lane['in_flight'] += 1
        lane['admitted'] += 1
        lane['peak'] = max(lane['peak'], lane['in_flight'])
        started = time.monotonic()
        status = 500
        finished = None
        released = False

        def release():
            nonlocal released
            if released:
                return
            released = True
            lane['in_flight'] -= 1
            lane['completed'] += 1
            lane['failed'] += int(status >= 500)
            elapsed = (finished or time.monotonic()) - started
            bucket = next((i for i, upper in enumerate(BUCKETS) if elapsed <= upper), len(BUCKETS))
            lane['duration_buckets'][bucket] += 1

        async def measured_send(message):
            nonlocal status, finished
            if message['type'] == 'http.response.start':
                status = message['status']
            elif message['type'] == 'http.response.body':
                lane['response_bytes'] += len(message.get('body', b''))
                if not message.get('more_body', False):
                    finished = time.monotonic()
            await send(message)
            if finished is not None:
                release()

        try:
            await self.app(scope, receive, measured_send)
        finally:
            release()
