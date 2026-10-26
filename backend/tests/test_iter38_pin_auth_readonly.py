"""Iteration 38: live PIN auth read-only verification for canonical + web proxy.

No account mutation tests are executed here.
"""

import hashlib
import os
import uuid

import pytest
import requests
from dotenv import load_dotenv


load_dotenv("/app/frontend/.env")
load_dotenv("/app/backend/.env")

BASE_URL = (os.environ.get("EXPO_PUBLIC_BACKEND_URL") or "").rstrip("/")
JEELIVE_API = (os.environ.get("EXPO_PUBLIC_JEELIVE_API") or "").rstrip("/")
PHONE = os.environ.get("JEELIVE_TEST_PHONE") or ""
PIN = os.environ.get("JEELIVE_TEST_PIN") or ""


def _unwrap(payload):
    return payload.get("data", payload) if isinstance(payload, dict) else payload


def _id_hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _require_env():
    if not BASE_URL or not JEELIVE_API:
        pytest.skip("Missing EXPO_PUBLIC_BACKEND_URL or EXPO_PUBLIC_JEELIVE_API")
    if not PHONE or not PIN:
        pytest.skip("Missing JEELIVE_TEST_PHONE / JEELIVE_TEST_PIN in backend env")


# Auth/session fixtures (single login per requests session)
@pytest.fixture(scope="module")
def direct_session():
    _require_env()
    with requests.Session() as s:
        r = s.post(f"{JEELIVE_API}/auth/phone", json={"phone": PHONE, "pin": PIN}, timeout=30)
        if r.status_code in (401, 429):
            pytest.skip(f"Credential flow blocked with HTTP {r.status_code}; stop requested by scope")
        assert r.status_code == 200, f"Direct login failed: HTTP {r.status_code}"
        yield s


@pytest.fixture(scope="module")
def proxy_sid() -> str:
    return "TESTSID" + uuid.uuid4().hex[:20]


@pytest.fixture(scope="module")
def proxy_session(proxy_sid: str):
    _require_env()
    with requests.Session() as s:
        headers = {"X-JL-Sid": proxy_sid}
        r = s.post(f"{BASE_URL}/api/jl/auth/phone", json={"phone": PHONE, "pin": PIN}, headers=headers, timeout=30)
        if r.status_code in (401, 429):
            pytest.skip(f"Proxy credential flow blocked with HTTP {r.status_code}; stop requested by scope")
        assert r.status_code == 200, f"Proxy login failed: HTTP {r.status_code}"
        yield s


# Identity parity checks (read-only)
def test_auth_me_direct_ok(direct_session: requests.Session):
    res = direct_session.get(f"{JEELIVE_API}/auth/me", timeout=30)
    assert res.status_code == 200
    me = _unwrap(res.json())
    assert isinstance(me.get("id"), str) and len(me["id"]) >= 8
    assert isinstance(me.get("role"), str)


def test_auth_me_proxy_ok(proxy_session: requests.Session, proxy_sid: str):
    res = proxy_session.get(f"{BASE_URL}/api/jl/auth/me", headers={"X-JL-Sid": proxy_sid}, timeout=30)
    assert res.status_code == 200
    me = _unwrap(res.json())
    assert isinstance(me.get("id"), str) and len(me["id"]) >= 8
    assert isinstance(me.get("role"), str)


def test_direct_proxy_identity_match(direct_session: requests.Session, proxy_session: requests.Session, proxy_sid: str):
    d = _unwrap(direct_session.get(f"{JEELIVE_API}/auth/me", timeout=30).json())
    p = _unwrap(proxy_session.get(f"{BASE_URL}/api/jl/auth/me", headers={"X-JL-Sid": proxy_sid}, timeout=30).json())
    assert d.get("id") == p.get("id"), f"identity_hash_mismatch direct={_id_hash(str(d.get('id')))} proxy={_id_hash(str(p.get('id')))}"


# Canonical academic read-only checks
def test_pyq_jee_main_catalog_count_30_and_questions_2250(direct_session: requests.Session):
    res = direct_session.get(f"{JEELIVE_API}/pyq/jee-main", timeout=30)
    assert res.status_code == 200
    payload = _unwrap(res.json())
    items = payload.get("items") or []
    assert payload.get("total") == 30
    q_sum = sum(int((row.get("count") or 0)) for row in items)
    assert q_sum == 2250


def test_attempts_readonly_fingerprint_stable_same_session(direct_session: requests.Session):
    r1 = direct_session.get(f"{JEELIVE_API}/attempts?page=1", timeout=30)
    r2 = direct_session.get(f"{JEELIVE_API}/attempts?page=1", timeout=30)
    assert r1.status_code == 200
    assert r2.status_code == 200
    p1 = _unwrap(r1.json())
    p2 = _unwrap(r2.json())
    ids1 = [str(x.get("id")) for x in (p1.get("items") or []) if x.get("id")]
    ids2 = [str(x.get("id")) for x in (p2.get("items") or []) if x.get("id")]
    assert ids1 == ids2


def test_change_pin_rejects_invalid_payload_without_mutation(direct_session: requests.Session):
    """PIN endpoint contract validation check only (invalid payload)."""
    res = direct_session.post(
        f"{JEELIVE_API}/auth/pin",
        json={"phone": PHONE, "new_pin": "12", "confirm_pin": "34"},
        timeout=30,
    )
    assert res.status_code in (400, 422)


def test_signup_rejects_pin_mismatch(direct_session: requests.Session):
    """Signup contract check only (mismatch payload)."""
    payload = {
        "phone": PHONE,
        "pin": "1234",
        "confirm_pin": "0000",
    }
    res = direct_session.post(f"{JEELIVE_API}/auth/phone/signup", json=payload, timeout=30)
    assert res.status_code in (400, 409, 422)
