"""TEST-ONLY iteration 118: reproduce the original production misconfiguration (FRONTEND_URL=https://www.jeelive.ai, CORS_ORIGINS='*')
in-process on an ISOLATED DB: canonical https://jeelive.ai writes are 403 origin_denied BEFORE credentials (legacy '*' grants nothing).
Also verifies invalid explicit config fails closed at import without echoing the configured value. Env set only in subprocesses."""
import os, subprocess, sys
from pathlib import Path
import pytest

HERE = Path(__file__).resolve().parent


def test_misconfigured_canonical_origin_is_403_before_credentials():
    if os.environ.get('FRONTEND_URL') != 'https://www.jeelive.ai':
        pytest.skip('run with FRONTEND_URL=https://www.jeelive.ai CORS_ORIGINS=*')
    import test_iter118_auth_cors_isolated as T  # noqa: F401  (seeds/drops isolated DB through its fixture only when collected)
    import asyncio
    T.run(T.A.seed())
    try:
        assert T.ALLOWED == ['https://www.jeelive.ai']
        for path, body in [('/api/auth/phone', {'phone': '0000000000'}), ('/api/auth/login', {})]:
            r = T.req('POST', path, 'https://jeelive.ai', json=body)
            assert r.status_code == 403 and T.err(r)['code'] == 'origin_denied', r.text[:200]
            r = T.req('POST', path, 'https://www.jeelive.ai', json=body)
            assert r.status_code == 422, r.text[:200]
        r = T.req('OPTIONS', '/api/auth/phone', 'https://jeelive.ai', headers={'Access-Control-Request-Method': 'POST'})
        assert r.status_code == 400
    finally:
        T.run(T.A.drop())


@pytest.mark.parametrize('fe,extra', [('https://jeelive.ai', 'https://*.jeelive.ai'), ('https://jeelive.ai/app', ''),
                                      ('https://ops:Sup3rSecretValue@jeelive.ai', ''), ('', '')])
def test_invalid_explicit_config_fails_closed(fe, extra):
    env = dict(os.environ, FRONTEND_URL=fe, CORS_ORIGINS=extra)
    p = subprocess.run([sys.executable, '-c', 'import server'], cwd=HERE.parent, env=env, capture_output=True, text=True, timeout=90)
    assert p.returncode != 0
    out = p.stdout + p.stderr
    assert 'RuntimeError' in out
    assert 'Sup3rSecretValue' not in out and '*.jeelive.ai' not in out


def test_legacy_star_does_not_crash_and_is_ignored():
    env = dict(os.environ, FRONTEND_URL='https://campus-search-debug.preview.emergentagent.com', CORS_ORIGINS='*')
    p = subprocess.run([sys.executable, '-c', 'import server; print("ORIGINS", server.origins)'], cwd=HERE.parent, env=env,
                       capture_output=True, text=True, timeout=90)
    assert p.returncode == 0, p.stderr[-500:]
    assert "ORIGINS ['https://campus-search-debug.preview.emergentagent.com']" in p.stdout
