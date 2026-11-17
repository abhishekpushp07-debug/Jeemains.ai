import asyncio, time
from collections import deque
from .contracts import error_response
from .runtime import INFLIGHT_LIMITS, ADMISSION_WAIT

BUCKETS = (0.005, 0.025, 0.1, 0.3, 1.0, 3.0, 10.0)


def workload(path, method):
    if path == '/api/health' and method == 'GET':
        return None
    if path == '/api/ready':
        return 'probe'
    if path in ('/api/auth/login', '/api/auth/phone', '/api/auth/phone/signup', '/api/auth/pin', '/api/auth/pin/reset', '/api/auth/owner/student-pin-reset', '/api/auth/register'):
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
        self.lanes = {name: {'limit': limit, 'in_flight': 0, 'peak': 0, 'admitted': 0, 'waited': 0,
                            'rejected': 0, 'completed': 0, 'failed': 0,
                            'response_bytes': 0, 'duration_buckets': [0] * (len(BUCKETS) + 1)}
                      for name, limit in INFLIGHT_LIMITS.items()}
        self.waiting = {name: deque() for name in INFLIGHT_LIMITS}
        owner.state.admission = self

    async def wait_slot(self, name, lane):
        """A short, bounded waiting line: a burst of sign-ins waits a few seconds for a free slot instead of being turned away."""
        seconds, queue = ADMISSION_WAIT.get(name, 0), self.waiting[name]
        if not seconds or len(queue) >= lane['limit'] * 64:
            return False
        turn = asyncio.get_running_loop().create_future()
        queue.append(turn)
        try:
            await asyncio.wait_for(turn, seconds)
            return True
        except asyncio.TimeoutError:
            # The slot may have been handed over at the very moment the wait ran out.
            return turn.done() and not turn.cancelled()
        except BaseException:
            if turn.done() and not turn.cancelled():
                self.give_back(name, lane)
            raise
        finally:
            try:
                queue.remove(turn)
            except ValueError:
                pass

    def hand_over(self, name):
        queue = self.waiting[name]
        while queue:
            turn = queue.popleft()
            if not turn.done():
                turn.set_result(True)
                return True
        return False

    def give_back(self, name, lane):
        if not self.hand_over(name):
            lane['in_flight'] -= 1

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
            if not await self.wait_slot(name, lane):
                lane['rejected'] += 1
                response = error_response('This service is busy. Your saved work is safe; retry shortly.', 503, 'capacity_busy')
                response.headers['Retry-After'] = '2'
                return await response(scope, receive, send)
            lane['waited'] += 1
        else:
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
            self.give_back(name, lane)
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
