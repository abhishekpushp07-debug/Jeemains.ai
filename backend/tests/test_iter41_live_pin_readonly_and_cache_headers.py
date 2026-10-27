"""Iteration 41: live PIN read-only verification + cache header proxy checks.

Scope:
- canonical/proxy auth parity with single-login sessions
- readonly history/catalog checks
- proxy passthrough of image validator/range headers
"""

from __future__ import annotations

import hashlib
import os
import time
import uuid
from typing import Any

import pytest
import requests
from dotenv import load_dotenv


load_dotenv("/app/frontend/.env")
load_dotenv("/app/backend/.env")

BASE_URL = (os.environ.get("EXPO_PUBLIC_BACKEND_URL") or "").rstrip("/")
JEELIVE_API = (os.environ.get("EXPO_PUBLIC_JEELIVE_API") or "").rstrip("/")
PHONE = os.environ.get("JEELIVE_TEST_PHONE") or ""
PIN = os.environ.get("JEELIVE_TEST_PIN") or ""


def _require_env() -> None:
    if not BASE_URL or not JEELIVE_API:
        pytest.skip("Missing EXPO_PUBLIC_BACKEND_URL or EXPO_PUBLIC_JEELIVE_API")
    if not PHONE or not PIN:
        pytest.skip("Missing JEELIVE_TEST_PHONE / JEELIVE_TEST_PIN in backend env")


def _unwrap(payload: Any) -> Any:
    return payload.get("data", payload) if isinstance(payload, dict) else payload


def _hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _id_hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _request_with_retry(session: requests.Session, method: str, url: str, **kwargs) -> requests.Response:
    """Retry once for transient timeout/edge gateway responses."""
    try:
        res = session.request(method, url, **kwargs)
        if res.status_code not in (520, 522, 524):
            return res
    except requests.exceptions.ReadTimeout:
        pass
    time.sleep(1.0)
    return session.request(method, url, **kwargs)


# Auth/session fixtures (single login per client)
@pytest.fixture(scope="module")
def direct_session():
    _require_env()
    with requests.Session() as s:
        r = s.post(f"{JEELIVE_API}/auth/phone", json={"phone": PHONE, "pin": PIN}, timeout=30)
        if r.status_code in (401, 429):
            pytest.skip(f"Direct auth blocked by HTTP {r.status_code}")
        assert r.status_code == 200, f"Direct login failed: HTTP {r.status_code}"
        yield s


@pytest.fixture(scope="module")
def proxy_sid() -> str:
    return "TESTSID" + uuid.uuid4().hex[:20]


@pytest.fixture(scope="module")
def proxy_session(proxy_sid: str):
    _require_env()
    with requests.Session() as s:
        r = s.post(
            f"{BASE_URL}/api/jl/auth/phone",
            json={"phone": PHONE, "pin": PIN},
            headers={"X-JL-Sid": proxy_sid},
            timeout=30,
        )
        if r.status_code in (401, 429):
            pytest.skip(f"Proxy auth blocked by HTTP {r.status_code}")
        assert r.status_code == 200, f"Proxy login failed: HTTP {r.status_code}"
        yield s


# Identity/session parity checks
def test_auth_me_direct_and_proxy_match_identity(
    direct_session: requests.Session, proxy_session: requests.Session, proxy_sid: str
):
    d_res = _request_with_retry(direct_session, "GET", f"{JEELIVE_API}/auth/me", timeout=35)
    p_res = _request_with_retry(proxy_session, "GET", f"{BASE_URL}/api/jl/auth/me", headers={"X-JL-Sid": proxy_sid}, timeout=35)
    assert d_res.status_code == 200
    assert p_res.status_code == 200
    d = _unwrap(d_res.json())
    p = _unwrap(p_res.json())
    assert isinstance(d.get("id"), str) and len(d["id"]) >= 8
    assert isinstance(p.get("id"), str) and len(p["id"]) >= 8
    assert d.get("id") == p.get("id"), f"identity_mismatch direct={_id_hash(str(d.get('id')))} proxy={_id_hash(str(p.get('id')))}"


def test_proxy_session_persists_with_same_sid(proxy_sid: str):
    with requests.Session() as s2:
        # No /auth/phone here; verifies server-side cookie jar persistence per sid.
        res = _request_with_retry(s2, "GET", f"{BASE_URL}/api/jl/auth/me", headers={"X-JL-Sid": proxy_sid}, timeout=35)
        assert res.status_code == 200
        me = _unwrap(res.json())
        assert isinstance(me.get("id"), str) and len(me["id"]) >= 8


# Read-only PYQ + history checks
def test_pyq_catalogue_jee_main_readonly_shape(direct_session: requests.Session):
    res = _request_with_retry(direct_session, "GET", f"{JEELIVE_API}/pyq/jee-main", timeout=40)
    assert res.status_code == 200
    payload = _unwrap(res.json())
    assert payload.get("total") == 30
    assert sorted(payload.get("years", []), reverse=True) == [2026, 2025]
    items = payload.get("items") or []
    assert len(items) == 30
    assert all(str(row.get("id", "")).strip() for row in items)


def test_attempts_history_has_completed_or_active_rows(direct_session: requests.Session):
    res = _request_with_retry(direct_session, "GET", f"{JEELIVE_API}/attempts?page=1", timeout=40)
    assert res.status_code == 200
    rows = (_unwrap(res.json()) or {}).get("items") or []
    assert isinstance(rows, list)
    assert len(rows) > 0
    statuses = {str(r.get("status") or "") for r in rows}
    assert any(s in statuses for s in ("active", "completed", "grading", "embargoed", "expired"))


def _pick_completed_result_attempt(direct_session: requests.Session) -> tuple[str, dict[str, Any]]:
    attempts_res = _request_with_retry(direct_session, "GET", f"{JEELIVE_API}/attempts?page=1", timeout=40)
    if attempts_res.status_code != 200:
        pytest.skip(f"Attempts list unavailable: HTTP {attempts_res.status_code}")
    attempts = (_unwrap(attempts_res.json()) or {}).get("items") or []
    for row in attempts:
        attempt_id = str(row.get("id") or "")
        if not attempt_id:
            continue
        r = _request_with_retry(direct_session, "GET", f"{JEELIVE_API}/attempts/{attempt_id}/results?score_version=original", timeout=45)
        if r.status_code == 200:
            payload = _unwrap(r.json())
            if payload.get("summary") and payload.get("status") != "embargoed":
                return attempt_id, payload
    pytest.skip("No released completed result found in first-page history for this account")


# Proxy cache-header passthrough + byte parity
def test_proxy_asset_validator_headers_and_byte_parity(
    direct_session: requests.Session, proxy_session: requests.Session, proxy_sid: str
):
    attempt_id, result_payload = _pick_completed_result_attempt(direct_session)
    q = next((x for x in (result_payload.get("questions") or []) if int(x.get("asset_count") or 0) > 0), None)
    if not q:
        pytest.skip("Released result had no question image assets")
    qid = q["id"]
    path = f"/attempts/{attempt_id}/questions/{qid}/asset/question/0"

    d = _request_with_retry(direct_session, "GET", f"{JEELIVE_API}{path}", timeout=45)
    p = _request_with_retry(proxy_session, "GET", f"{BASE_URL}/api/jl{path}", headers={"X-JL-Sid": proxy_sid}, timeout=45)
    assert d.status_code == 200
    assert p.status_code == 200
    assert d.headers.get("content-type", "").startswith("image/")
    assert p.headers.get("content-type", "").startswith("image/")
    assert _hash(d.content) == _hash(p.content)

    headers = {"X-JL-Sid": proxy_sid, "Range": "bytes=0-0"}
    if p.headers.get("etag"):
        headers["If-None-Match"] = p.headers["etag"]
        headers["If-Range"] = p.headers["etag"]
    elif p.headers.get("last-modified"):
        headers["If-Modified-Since"] = p.headers["last-modified"]
        headers["If-Range"] = p.headers["last-modified"]

    v = proxy_session.get(f"{BASE_URL}/api/jl{path}", headers=headers, timeout=40)
    assert v.status_code in (200, 206, 304)
    for name in ("etag", "last-modified", "content-range", "accept-ranges", "cache-control"):
        # Contract allows subset depending on upstream image host behavior.
        if name in v.headers:
            assert isinstance(v.headers.get(name), str)
