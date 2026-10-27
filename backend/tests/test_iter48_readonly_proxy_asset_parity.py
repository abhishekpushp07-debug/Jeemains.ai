"""Iteration 48 read-only canonical/proxy parity for auth, catalogue and source images.

This suite performs no academic attempt mutations.
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
JEELIVE_API = (os.environ.get("JEELIVE_API") or os.environ.get("EXPO_PUBLIC_JEELIVE_API") or "").rstrip("/")
PHONE = (os.environ.get("JEELIVE_TEST_PHONE") or "").strip()
PIN = (os.environ.get("JEELIVE_TEST_PIN") or "").strip()

def _unwrap(payload):
    return payload.get("data", payload) if isinstance(payload, dict) else payload


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _completed_attempt_ids(session: requests.Session, base: str, headers: dict | None = None) -> list[str]:
    query = "tab=completed&page=1&q=&status=all&exam="
    response = session.get(f"{base}/my/tests?{query}", headers=headers or {}, timeout=40)
    if response.status_code != 200:
        return []
    payload = _unwrap(response.json())
    items = payload.get("items") or []
    return [x.get("id") for x in items if x.get("id") and x.get("status") == "completed"]


def _require_env():
    if not BASE_URL or not JEELIVE_API:
        pytest.skip("Missing EXPO_PUBLIC_BACKEND_URL or JEELIVE_API/EXPO_PUBLIC_JEELIVE_API")
    if not PHONE or not PIN:
        pytest.skip("Missing JEELIVE_TEST_PHONE / JEELIVE_TEST_PIN")


# Auth/session fixtures for read-only parity (single login per channel)
@pytest.fixture(scope="module")
def direct_session():
    _require_env()
    with requests.Session() as s:
        try:
            r = s.post(f"{JEELIVE_API}/auth/phone", json={"phone": PHONE, "pin": PIN}, timeout=30)
        except requests.RequestException as exc:
            pytest.skip(f"Direct canonical auth unavailable: {type(exc).__name__}")
        if r.status_code in (401, 429):
            pytest.skip(f"Direct login blocked with HTTP {r.status_code}")
        assert r.status_code == 200, f"Direct login failed: {r.status_code}"
        yield s


@pytest.fixture(scope="module")
def proxy_sid() -> str:
    return "TESTSID" + uuid.uuid4().hex[:20]


@pytest.fixture(scope="module")
def proxy_session(proxy_sid: str):
    _require_env()
    with requests.Session() as s:
        try:
            r = s.post(
                f"{BASE_URL}/api/jl/auth/phone",
                json={"phone": PHONE, "pin": PIN},
                headers={"X-JL-Sid": proxy_sid},
                timeout=30,
            )
        except requests.RequestException as exc:
            pytest.skip(f"Proxy auth unavailable: {type(exc).__name__}")
        if r.status_code in (401, 429):
            pytest.skip(f"Proxy login blocked with HTTP {r.status_code}")
        assert r.status_code == 200, f"Proxy login failed: {r.status_code}"
        yield s


# Identity and catalogue read-only checks
def test_identity_direct_and_proxy_same(direct_session: requests.Session, proxy_session: requests.Session, proxy_sid: str):
    d = _unwrap(direct_session.get(f"{JEELIVE_API}/auth/me", timeout=30).json())
    p = _unwrap(proxy_session.get(f"{BASE_URL}/api/jl/auth/me", headers={"X-JL-Sid": proxy_sid}, timeout=30).json())
    assert isinstance(d.get("id"), str) and len(d["id"]) >= 8
    assert d.get("id") == p.get("id")


def test_pyq_catalogue_count_and_years(direct_session: requests.Session, proxy_session: requests.Session, proxy_sid: str):
    d_res = direct_session.get(f"{JEELIVE_API}/pyq/jee-main", timeout=30)
    p_res = proxy_session.get(f"{BASE_URL}/api/jl/pyq/jee-main", headers={"X-JL-Sid": proxy_sid}, timeout=30)
    assert d_res.status_code == 200
    assert p_res.status_code == 200
    d = _unwrap(d_res.json())
    p = _unwrap(p_res.json())
    assert d.get("total") == p.get("total") == 30
    assert sorted(d.get("years") or [], reverse=True) == [2026, 2025]


# Source image parity: compare one question image and one solution image SHA via direct vs proxy
def test_completed_attempt_question_and_solution_image_sha_match(
    direct_session: requests.Session,
    proxy_session: requests.Session,
    proxy_sid: str,
):
    direct_ids = _completed_attempt_ids(direct_session, JEELIVE_API)
    proxy_ids = _completed_attempt_ids(proxy_session, f"{BASE_URL}/api/jl", {"X-JL-Sid": proxy_sid})
    candidate_ids = [x for x in direct_ids if x in set(proxy_ids)]

    if not candidate_ids:
        pytest.skip("No completed attempts available for this approved account on page 1")

    chosen = None
    result_d = None
    result_p = None
    for attempt_id in candidate_ids:
        d_res = direct_session.get(f"{JEELIVE_API}/attempts/{attempt_id}/results?score_version=original", timeout=40)
        p_res = proxy_session.get(
            f"{BASE_URL}/api/jl/attempts/{attempt_id}/results?score_version=original",
            headers={"X-JL-Sid": proxy_sid},
            timeout=40,
        )
        if d_res.status_code == 200 and p_res.status_code == 200:
            chosen = attempt_id
            result_d = _unwrap(d_res.json())
            result_p = _unwrap(p_res.json())
            break

    if not chosen:
        pytest.skip("No approved completed attempt currently released for this account")

    assert result_d.get("summary") == result_p.get("summary")
    questions = result_d.get("questions") or []
    assert len(questions) >= 1

    for kind, count_field in [("question", "asset_count"), ("solution", "solution_asset_count")]:
        q = next((x for x in questions if int(x.get(count_field) or 0) > 0), None)
        assert q, f"No {kind} image available on chosen completed attempt"
        qid = q["id"]
        path = f"/attempts/{chosen}/questions/{qid}/asset/{kind}/0"

        d_asset = direct_session.get(f"{JEELIVE_API}{path}", timeout=40)
        p_asset = proxy_session.get(f"{BASE_URL}/api/jl{path}", headers={"X-JL-Sid": proxy_sid}, timeout=40)
        assert d_asset.status_code == p_asset.status_code == 200
        assert d_asset.headers.get("content-type", "").startswith("image/")
        assert _sha(d_asset.content) == _sha(p_asset.content)
