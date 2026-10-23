"""TEST-ONLY iteration 123: operational driver tools/run_jee_transfer.py exercised with a FAKE requests.Session.
NEVER contacts live/preview. Non-auth calls are forwarded ONLY to the isolated bridge iso_bridge_iter122.py
(127.0.0.1:8768, isolated DB, mocked storage). Login is faked with FAKE env creds; crop asset bytes are faked PNGs.
Run (bridge must be running and freshly seeded): cd /app/backend/tests && python -m pytest test_iter123_driver_isolated.py -p no:asyncio -n0 -v
"""
import io, json, os, socket, stat, sys, contextlib
from pathlib import Path
from urllib.parse import urlsplit
import pytest
import requests
from dotenv import dotenv_values

FAKE_EMAIL, FAKE_PW = 'fake-owner-123@example.invalid', 'FAKE-pw-123-DoNotLog!'
os.environ['ADMIN_EMAIL'], os.environ['ADMIN_PASSWORD'] = FAKE_EMAIL, FAKE_PW  # before import: load_dotenv won't override
sys.path.insert(0, '/app/backend')
from tools import run_jee_transfer as D  # noqa: E402

REAL = {k: v for k, v in dotenv_values('/app/backend/.env').items() if k in ('ADMIN_EMAIL', 'ADMIN_PASSWORD') and v}
BRIDGE = 'http://127.0.0.1:8768'
TARGET = 'https://prod-target.example.invalid'
REAL_SESSION = requests.Session
PNG = b'\x89PNG\r\n\x1a\n' + b'0' * 20


class Resp:
    def __init__(self, code, payload=None, content=b''):
        self.status_code, self._p, self.content = code, payload, content

    def json(self):
        return self._p


class FakeSession:
    LOG = []
    MODE = {}

    def __init__(self):
        self.headers = {}
        self.logged_in = False
        self.closed = False
        self._fwd = REAL_SESSION()
        FakeSession.INSTANCE = self

    def request(self, method, url, json=None, timeout=None, allow_redirects=True):
        u = urlsplit(url)
        assert f'{u.scheme}://{u.netloc}' == TARGET, url
        path = u.path + ('?' + u.query if u.query else '')
        FakeSession.LOG.append((method, path, dict(self.headers), json))
        if path == '/api/auth/login':
            if self.MODE.get('login') == 401:
                return Resp(401, {'detail': 'bad'})
            self.logged_in = True
            return Resp(200, {'data': {'ok': True}, 'meta': {'api_version': '1'}})
        if '/asset/' in path:
            return Resp(200, content=PNG)
        if self.MODE.get('fail_step_at') and path.endswith('/jee-transfer/step'):
            n = sum(1 for x in FakeSession.LOG if x[1].endswith('/step'))
            if n == self.MODE['fail_step_at']:
                return Resp(409, {'detail': 'conflict'})
        if self.MODE.get('probe') and path == '/api/studio/jee-transfer' and not self.logged_in:
            return Resp(self.MODE['probe'], {})
        h = {'x-test-user': 'owner'} if self.logged_in else {}
        r = self._fwd.request(method, BRIDGE + path, json=json, headers=h, timeout=60, allow_redirects=False)
        try:
            payload = r.json()
        except ValueError:
            payload = None
        return Resp(r.status_code, payload, r.content)

    def get(self, url, timeout=None, allow_redirects=True):
        return self.request('GET', url, timeout=timeout, allow_redirects=allow_redirects)

    def close(self):
        self.closed = True
        self._fwd.close()


@pytest.fixture(autouse=True)
def fake(monkeypatch):
    FakeSession.LOG, FakeSession.MODE = [], {}
    monkeypatch.setattr(D.requests, 'Session', FakeSession)
    orig = socket.create_connection

    def guarded(addr, *a, **k):  # any socket other than the local bridge is blocked
        assert addr[0] in ('127.0.0.1', 'localhost') and addr[1] == 8768, addr
        return orig(addr, *a, **k)
    monkeypatch.setattr(socket, 'create_connection', guarded)
    yield


def drive(tmp_path, target=TARGET):
    rep = tmp_path / 'r' / 'report.json'
    out = io.StringIO()
    argv = ['run_jee_transfer.py', '--target', target, '--report', str(rep)]
    code = 0
    with contextlib.redirect_stdout(out):
        old = sys.argv
        sys.argv = argv
        try:
            D.main()
        except SystemExit as e:
            code = e.code
        finally:
            sys.argv = old
    return code, out.getvalue(), rep


def no_secrets(*texts):
    for t in texts:
        for s in [FAKE_EMAIL, FAKE_PW, *REAL.values()]:
            assert s not in t, 'credential leaked'
        assert 'password' not in t.lower()


@pytest.mark.parametrize('bad', ['http://x.example', 'https://u:p@x.example', 'https://x.example/api', 'https://x.example?q=1', 'https://x.example/#f', 'x.example'])
def test_target_validation_rejects_before_any_call(tmp_path, bad):
    with pytest.raises(ValueError):
        drive(tmp_path, bad)
    assert FakeSession.LOG == [] and not (tmp_path / 'r').exists()


@pytest.mark.parametrize('probe', [200, 404, 500])
def test_probe_not_401_no_login(tmp_path, probe):
    FakeSession.MODE['probe'] = probe
    code, out, rep = drive(tmp_path)
    r = json.loads(rep.read_text())
    assert code == 1 and r['status'] == 'incomplete' and 'no login' in r['error']
    assert [x[1] for x in FakeSession.LOG] == ['/api/studio/jee-transfer'] and 'operational_session_closed' not in r
    no_secrets(out, rep.read_text())


def test_login_failure_no_logout_no_leak(tmp_path):
    FakeSession.MODE['login'] = 401
    code, out, rep = drive(tmp_path)
    r = json.loads(rep.read_text())
    assert code == 1 and r['error'] == 'Operation stopped: /auth/login returned HTTP 401'
    assert [x[1] for x in FakeSession.LOG] == ['/api/studio/jee-transfer', '/api/auth/login']
    assert FakeSession.LOG[1][3] == {'email': FAKE_EMAIL, 'password': FAKE_PW}  # creds only in login body
    assert FakeSession.INSTANCE.closed
    no_secrets(out, rep.read_text())


def test_mid_run_failure_logs_out(tmp_path):
    FakeSession.MODE['fail_step_at'] = 2
    code, out, rep = drive(tmp_path)
    r = json.loads(rep.read_text())
    assert code == 1 and r['status'] == 'incomplete' and '/studio/jee-transfer/step returned HTTP 409' in r['error']
    assert r['operational_session_closed'] is True and FakeSession.LOG[-1][1] == '/api/auth/logout'
    assert stat.S_IMODE(os.stat(rep).st_mode) == 0o600
    no_secrets(out, rep.read_text())


def test_full_run_against_isolated_bridge(tmp_path):
    code, out, rep = drive(tmp_path)
    text = rep.read_text()
    r = json.loads(text)
    assert code == 0, (r.get('error'), out[-500:])
    assert r['status'] == 'complete_verified' and r['operational_session_closed'] is True
    assert r['after']['phase'] == 'complete' and r['after']['chapter_tests'] == 78
    assert r['catalogue']['total'] == 78 and r['catalogue']['subject_counts'] == {'Physics': 29, 'Mathematics': 26, 'Chemistry': 23}
    assert [s['minutes'] for s in r['samples']] == [90, 120, 70]
    paths = [x[1] for x in FakeSession.LOG]
    assert paths[:3] == ['/api/studio/jee-transfer', '/api/auth/login', '/api/auth/me'] and paths[-1] == '/api/auth/logout'
    assert all(x[2].get('Origin') == TARGET for x in FakeSession.LOG)
    assert stat.S_IMODE(os.stat(rep).st_mode) == 0o600
    assert 'COMPLETE: 78 live chapters' in out
    no_secrets(out, text)


def test_rerun_after_complete_is_noop(tmp_path):
    code, out, rep = drive(tmp_path)
    r = json.loads(rep.read_text())
    assert code == 0 and r['status'] == 'complete_verified'
    assert not any(x[1].endswith('/step') for x in FakeSession.LOG), 'no step POST when already complete'
