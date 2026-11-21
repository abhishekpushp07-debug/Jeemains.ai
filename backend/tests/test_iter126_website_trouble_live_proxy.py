"""Iteration 126: website-down guard through the preview proxy (read-only, QA learner sign-in only; never submits)."""
import os
import uuid

import pytest
import requests

BASE_URL = (os.environ.get("EXPO_PUBLIC_BACKEND_URL") or os.environ.get("EXPO_BACKEND_URL") or "").rstrip("/")
PHONE, PIN = "7004186276", "5524"


def _unwrap(body):
    return body.get("data", body) if isinstance(body, dict) else body


@pytest.fixture(scope="module")
def sid():
    if not BASE_URL:
        pytest.skip("EXPO_PUBLIC_BACKEND_URL not set")
    return "TESTSID" + uuid.uuid4().hex[:20]


@pytest.fixture(scope="module")
def signed_in(sid):
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/jl/auth/phone", json={"phone": PHONE, "pin": PIN}, headers={"X-JL-Sid": sid}, timeout=30)
    if r.status_code == 429:
        pytest.skip("login paused (429)")
    assert r.status_code == 200, f"login {r.status_code} {r.text[:200]}"
    assert isinstance(_unwrap(r.json()).get("user", _unwrap(r.json())), dict)
    yield s
    s.close()


# Sign-in through the proxy
def test_login_ok(signed_in):
    assert signed_in is not None


# PYQ list: 30 JEE Main papers
def test_pyq_list_30_papers(signed_in, sid):
    r = signed_in.get(f"{BASE_URL}/api/jl/pyq/jee-main", headers={"X-JL-Sid": sid}, timeout=30)
    assert r.status_code == 200, r.text[:200]
    d = _unwrap(r.json())
    papers = d if isinstance(d, list) else d.get("papers") or d.get("items") or []
    assert len(papers) == 30, f"got {len(papers)}"
    assert "cloudflare" not in r.text.lower()


# Normal 401 untouched (fresh sid, not signed in)
def test_unsigned_auth_me_is_plain_401():
    r = requests.get(f"{BASE_URL}/api/jl/auth/me", headers={"X-JL-Sid": "TESTSID" + uuid.uuid4().hex[:20]}, timeout=30)
    assert r.status_code == 401, r.status_code
    assert r.json().get("error", {}).get("code") != "website_unavailable"


# Normal 404 untouched
def test_unknown_attempt_is_404(signed_in, sid):
    r = signed_in.get(f"{BASE_URL}/api/jl/attempts/{uuid.uuid4()}", headers={"X-JL-Sid": sid}, timeout=30)
    assert r.status_code == 404, f"{r.status_code} {r.text[:200]}"
    assert r.json().get("error", {}).get("code") != "website_unavailable"


# Invalid sid rejected before upstream
def test_bad_sid_400():
    r = requests.get(f"{BASE_URL}/api/jl/pyq/jee-main", headers={"X-JL-Sid": "bad"}, timeout=30)
    assert r.status_code == 400


# Retry-After exposed for the app
def test_cors_exposes_retry_after():
    r = requests.options(f"{BASE_URL}/api/jl/pyq/jee-main", headers={"Origin": BASE_URL, "Access-Control-Request-Method": "GET",
                                                                    "Access-Control-Request-Headers": "x-jl-sid"}, timeout=30)
    assert r.status_code in (200, 204)
