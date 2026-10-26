# Iteration 36: canonical read-only parity and safe opt-in PYQ write flow checks
import json
import os
import uuid
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv


# Shared environment + canonical evidence for academic API checks
load_dotenv("/app/frontend/.env")

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "").rstrip("/")
JEELIVE_API = os.environ.get("EXPO_PUBLIC_JEELIVE_API", "").rstrip("/")
PHONE = "9000000001"
WRITE_OPTIN = os.environ.get("ITER36_RUN_PILOT_WRITE", "0") == "1"
EVIDENCE_PATH = Path("/app/reference/integration-2026-10-26/evidence/canonical-pyq.json")


def _must_have_env():
    if not BASE_URL or not JEELIVE_API:
        pytest.skip("Required frontend env vars missing for iteration 36 checks")


def _unwrap(payload):
    if isinstance(payload, dict) and payload.get("meta", {}).get("api_version") and "data" in payload:
        return payload["data"]
    return payload


def _canonical_expected():
    data = json.loads(EVIDENCE_PATH.read_text())
    rows = data.get("papers", [])
    return {
        "total": int(data.get("total", 0)),
        "questions": int(data.get("questions", 0)),
        "ids": [r.get("id") for r in rows],
        "counts": {r.get("id"): int(r.get("count", 0)) for r in rows},
    }


def _login_direct(session: requests.Session):
    if getattr(session, "iter36_ok", False):
        return
    r = session.post(f"{JEELIVE_API}/auth/phone", json={"phone": PHONE}, timeout=30)
    assert r.status_code == 200, f"Auth failed ({r.status_code}) Retry-After={r.headers.get('Retry-After')}"
    me = session.get(f"{JEELIVE_API}/auth/me", timeout=30)
    assert me.status_code == 200, me.text[:300]
    session.iter36_ok = True


def _login_proxy(session: requests.Session, sid: str):
    if getattr(session, "iter36_ok", False):
        return
    r = session.post(
        f"{BASE_URL}/api/jl/auth/phone",
        json={"phone": PHONE},
        headers={"X-JL-Sid": sid},
        timeout=30,
    )
    assert r.status_code == 200, f"Auth failed ({r.status_code}) Retry-After={r.headers.get('Retry-After')}"
    me = session.get(f"{BASE_URL}/api/jl/auth/me", headers={"X-JL-Sid": sid}, timeout=30)
    assert me.status_code == 200, me.text[:300]
    session.iter36_ok = True


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


# Read-only canonical catalogue parity with package evidence (30 papers / 2250 questions)
def test_iter36_pyq_catalogue_matches_canonical_evidence_and_proxy(
    direct_session: requests.Session,
    proxy_session: requests.Session,
    proxy_sid: str,
):
    expected = _canonical_expected()
    d_res = direct_session.get(f"{JEELIVE_API}/pyq/jee-main", timeout=30)
    p_res = proxy_session.get(f"{BASE_URL}/api/jl/pyq/jee-main", headers={"X-JL-Sid": proxy_sid}, timeout=30)
    assert d_res.status_code == 200, d_res.text[:300]
    assert p_res.status_code == 200, p_res.text[:300]
    direct = _unwrap(d_res.json())
    proxy = _unwrap(p_res.json())

    assert direct.get("total") == expected["total"] == 30
    assert proxy.get("total") == direct.get("total")

    d_items = direct.get("items", [])
    p_items = proxy.get("items", [])
    assert len(d_items) == len(p_items) == expected["total"]

    d_ids = [x.get("id") for x in d_items]
    p_ids = [x.get("id") for x in p_items]
    assert sorted(d_ids) == sorted(p_ids)
    assert sorted(d_ids) == sorted(expected["ids"])

    d_total_q = sum(int(x.get("count", 0)) for x in d_items)
    p_total_q = sum(int(x.get("count", 0)) for x in p_items)
    assert d_total_q == p_total_q == expected["questions"] == 2250

    for item in d_items:
        pid = item.get("id")
        assert int(item.get("count", 0)) == expected["counts"][pid]


# Read-only learner history parity (no opening active attempt in test)
def test_iter36_attempt_history_readonly_parity(
    direct_session: requests.Session,
    proxy_session: requests.Session,
    proxy_sid: str,
):
    path = "/attempts?page=1"
    d_res = direct_session.get(f"{JEELIVE_API}{path}", timeout=30)
    p_res = proxy_session.get(f"{BASE_URL}/api/jl{path}", headers={"X-JL-Sid": proxy_sid}, timeout=30)
    assert d_res.status_code == 200, d_res.text[:300]
    assert p_res.status_code == 200, p_res.text[:300]

    direct = _unwrap(d_res.json())
    proxy = _unwrap(p_res.json())

    assert direct.get("page") == proxy.get("page")
    assert direct.get("pages") == proxy.get("pages")
    assert direct.get("count") == proxy.get("count")
    assert [x.get("id") for x in direct.get("items", [])] == [x.get("id") for x in proxy.get("items", [])]


# Public brand endpoint integrity: official SVG bytes are non-empty and stable via ETag
def test_iter36_public_brand_logo_headers():
    _must_have_env()
    r = requests.get(f"{BASE_URL}/api/brand/logo.svg", timeout=30)
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("image/svg")
    assert "Cache-Control" in r.headers
    assert "ETag" in r.headers
    assert len(r.content) > 200


# Safe opt-in only: one new pilot write check for pre-submit source-solution lock (403/404)
def test_iter36_optin_solution_locked_before_submit(direct_session: requests.Session):
    if not WRITE_OPTIN:
        pytest.skip("Opt-in only: set ITER36_RUN_PILOT_WRITE=1 to run live write checks")

    cat = _unwrap(direct_session.get(f"{JEELIVE_API}/pyq/jee-main", timeout=30).json())
    target = next((x for x in cat.get("items", []) if int(x.get("attempt_count", 0)) == 0), None)
    if not target:
        pytest.skip("No attempt_count=0 paper available for safe new write test")

    set_id = target["id"]
    pre = direct_session.post(f"{JEELIVE_API}/sets/{set_id}/preflight", json={"test_response": "A", "preview": False}, timeout=30)
    assert pre.status_code == 200, pre.text[:300]

    start = direct_session.post(
        f"{JEELIVE_API}/sets/{set_id}/start",
        json={"start_key": str(uuid.uuid4()), "device_checked": True, "preview": False},
        timeout=40,
    )
    assert start.status_code == 200, start.text[:300]
    attempt = _unwrap(start.json())
    attempt_id = attempt.get("id")
    questions = attempt.get("questions", [])
    q = next((row for row in questions if int(row.get("solution_asset_count", 0)) > 0), None)
    if not q:
        pytest.skip("No question with supplied solution asset found in selected paper")

    qid = q["id"]
    lock = direct_session.get(
        f"{JEELIVE_API}/attempts/{attempt_id}/questions/{qid}/asset/solution/0",
        timeout=30,
    )
    assert lock.status_code in (403, 404)