"""Iteration 36: read-only checks for approved existing canonical learner records."""

import os
import uuid

import pytest
import requests
from dotenv import load_dotenv


load_dotenv("/app/frontend/.env")

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "").rstrip("/")
JEELIVE_API = os.environ.get("EXPO_PUBLIC_JEELIVE_API", "").rstrip("/")
PHONE = "9000000001"
EXPECTED_UID = "db0c62b8-eeaf-41be-b8b1-05f5f34ac1d8"
COMPLETED_ID = "a1a9bc7f-1d51-48f1-aef5-cbc4d4388e78"
ACTIVE_ID = "185b73e3-b7a7-438d-92e1-e39dc1d7a2f2"


def _must_have_env():
    if not BASE_URL or not JEELIVE_API:
        pytest.skip("Required frontend env vars missing for iteration 36 readonly checks")


def _unwrap(payload):
    if isinstance(payload, dict) and payload.get("meta", {}).get("api_version") and "data" in payload:
        return payload["data"]
    return payload


def _login_direct(session: requests.Session):
    if getattr(session, "iter36_ro_ok", False):
        return
    r = session.post(f"{JEELIVE_API}/auth/phone", json={"phone": PHONE}, timeout=30)
    assert r.status_code == 200, f"Auth failed ({r.status_code}) Retry-After={r.headers.get('Retry-After')}"
    session.iter36_ro_ok = True


def _login_proxy(session: requests.Session, sid: str):
    if getattr(session, "iter36_ro_ok", False):
        return
    r = session.post(
        f"{BASE_URL}/api/jl/auth/phone",
        json={"phone": PHONE},
        headers={"X-JL-Sid": sid},
        timeout=30,
    )
    assert r.status_code == 200, f"Auth failed ({r.status_code}) Retry-After={r.headers.get('Retry-After')}"
    session.iter36_ro_ok = True


@pytest.fixture(scope="module")
def direct_session():
    _must_have_env()
    with requests.Session() as s:
        _login_direct(s)
        yield s


@pytest.fixture(scope="module")
def proxy_sid() -> str:
    return "TESTSID" + uuid.uuid4().hex[:20]


@pytest.fixture(scope="module")
def proxy_session(proxy_sid: str):
    _must_have_env()
    with requests.Session() as s:
        _login_proxy(s, proxy_sid)
        yield s


# Read-only learner identity parity for approved canonical account.
def test_iter36_existing_learner_identity_parity(
    direct_session: requests.Session,
    proxy_session: requests.Session,
    proxy_sid: str,
):
    d_me = direct_session.get(f"{JEELIVE_API}/auth/me", timeout=30)
    p_me = proxy_session.get(f"{BASE_URL}/api/jl/auth/me", headers={"X-JL-Sid": proxy_sid}, timeout=30)
    assert d_me.status_code == 200, d_me.text[:300]
    assert p_me.status_code == 200, p_me.text[:300]

    d_user = _unwrap(d_me.json())
    p_user = _unwrap(p_me.json())
    assert d_user.get("id") == EXPECTED_UID
    assert p_user.get("id") == EXPECTED_UID


# Read-only completed-result parity for historical approved attempt id.
def test_iter36_existing_completed_result_parity(
    direct_session: requests.Session,
    proxy_session: requests.Session,
    proxy_sid: str,
):
    path = f"/attempts/{COMPLETED_ID}/results?score_version=original"
    d_res = direct_session.get(f"{JEELIVE_API}{path}", timeout=40)
    p_res = proxy_session.get(f"{BASE_URL}/api/jl{path}", headers={"X-JL-Sid": proxy_sid}, timeout=40)
    assert d_res.status_code == 200, d_res.text[:300]
    assert p_res.status_code == 200, p_res.text[:300]

    d_result = _unwrap(d_res.json())
    p_result = _unwrap(p_res.json())

    assert d_result.get("id") == COMPLETED_ID
    assert p_result.get("id") == COMPLETED_ID
    assert d_result.get("summary") == p_result.get("summary")
    assert int((d_result.get("summary") or {}).get("maximum") or 0) == 300
    assert len(d_result.get("questions") or []) == 75


# Read-only active-attempt status parity without opening the player route (avoids visit writes).
def test_iter36_existing_active_attempt_status_parity(
    direct_session: requests.Session,
    proxy_session: requests.Session,
    proxy_sid: str,
):
    path = f"/attempts/{ACTIVE_ID}/status"
    d_res = direct_session.get(f"{JEELIVE_API}{path}", timeout=30)
    p_res = proxy_session.get(f"{BASE_URL}/api/jl{path}", headers={"X-JL-Sid": proxy_sid}, timeout=30)
    assert d_res.status_code == 200, d_res.text[:300]
    assert p_res.status_code == 200, p_res.text[:300]

    d_status = _unwrap(d_res.json())
    p_status = _unwrap(p_res.json())

    assert d_status.get("id") == ACTIVE_ID
    assert p_status.get("id") == ACTIVE_ID
    assert d_status.get("status") == p_status.get("status")
    assert d_status.get("deadline") == p_status.get("deadline")
