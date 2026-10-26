# Iteration 35: canonical direct-vs-proxy parity, expanded catalogue checks, and completed PYQ result signatures/assets
import hashlib
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
ITER35_COMPLETED_ATTEMPT_ID = os.environ.get("ITER35_COMPLETED_ATTEMPT_ID", "").strip()


def _must_have_env():
    if not BASE_URL or not JEELIVE_API:
        pytest.skip("Required public env vars are missing for iteration 35 parity tests.")


def _unwrap(payload):
    return payload.get("data", payload) if isinstance(payload, dict) else payload


def _stable_meta(item: dict) -> dict:
    return {
        "id": item.get("id"),
        "year": item.get("year"),
        "exam_date": item.get("exam_date"),
        "shift": item.get("shift"),
        "count": item.get("count"),
        "minutes": item.get("minutes"),
        "maximum": item.get("maximum"),
    }


def _normalize(payload):
    if isinstance(payload, dict):
        out = {}
        for k, v in payload.items():
            if k in {"server_now", "generated_at", "fetched_at", "now"}:
                continue
            out[k] = _normalize(v)
        return out
    if isinstance(payload, list):
        return [_normalize(x) for x in payload]
    return payload


def _question_ref_signatures(result_payload: dict) -> list[str]:
    questions = result_payload.get("questions") or []
    sigs = []
    for q in questions:
        stable = {
            "id": q.get("id") or q.get("question_id") or "",
            "qref": str(q.get("question_ref") or q.get("question_asset") or q.get("asset") or q.get("source")),
            "sref": str(q.get("solution_ref") or q.get("solution_asset") or q.get("solution") or q.get("solution_url")),
            "answer": str(q.get("answer") or ""),
            "accepted_answers": [str(x) for x in (q.get("accepted_answers") or [])],
            "solution_kind": q.get("solution_kind"),
            "asset_count": int(q.get("asset_count") or 0),
            "solution_asset_count": int(q.get("solution_asset_count") or 0),
        }
        sigs.append(hashlib.sha256(str(stable).encode("utf-8")).hexdigest())
    return sigs


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


@pytest.fixture(scope="module")
def direct_session():
    _must_have_env()
    with requests.Session() as session:
        _login_direct(session)
        yield session


@pytest.fixture(scope="module")
def proxy_session(proxy_sid):
    _must_have_env()
    with requests.Session() as session:
        _login_proxy(session, proxy_sid)
        yield session


@pytest.fixture(scope="module")
def proxy_sid() -> str:
    return "TESTSID" + uuid.uuid4().hex[:20]


def _login_direct(s: requests.Session) -> dict:
    if hasattr(s, "iter35_identity"):
        return s.iter35_identity
    r = s.post(f"{JEELIVE_API}/auth/phone", json={"phone": PHONE}, timeout=30)
    assert r.status_code == 200, f"Auth setup stopped: HTTP{r.status_code}; Retry-After={r.headers.get('Retry-After')}. No automatic retry."
    me = s.get(f"{JEELIVE_API}/auth/me", timeout=30)
    assert me.status_code == 200, me.text[:400]
    s.iter35_identity = _unwrap(me.json())
    return s.iter35_identity


def _login_proxy(s: requests.Session, sid: str) -> dict:
    if hasattr(s, "iter35_identity"):
        return s.iter35_identity
    r = s.post(
        f"{BASE_URL}/api/jl/auth/phone",
        json={"phone": PHONE},
        headers={"X-JL-Sid": sid},
        timeout=30,
    )
    assert r.status_code == 200, f"Auth setup stopped: HTTP{r.status_code}; Retry-After={r.headers.get('Retry-After')}. No automatic retry."
    me = s.get(f"{BASE_URL}/api/jl/auth/me", headers={"X-JL-Sid": sid}, timeout=30)
    assert me.status_code == 200, me.text[:400]
    s.iter35_identity = _unwrap(me.json())
    return s.iter35_identity


# Identity parity on canonical learner
def test_identity_direct_and_proxy_same_uid(direct_session: requests.Session, proxy_session: requests.Session, proxy_sid: str):
    _must_have_env()
    direct_me = _login_direct(direct_session)
    proxy_me = _login_proxy(proxy_session, proxy_sid)

    assert direct_me.get("id") == EXPECTED_UID
    assert proxy_me.get("id") == EXPECTED_UID
    assert direct_me.get("id") == proxy_me.get("id")


# PYQ parity for all 30 canonical papers and stable metadata
def test_pyq_catalogue_parity_full_30_metadata(direct_session: requests.Session, proxy_session: requests.Session, proxy_sid: str):
    _must_have_env()
    _login_direct(direct_session)
    _login_proxy(proxy_session, proxy_sid)

    d_res = direct_session.get(f"{JEELIVE_API}/pyq/jee-main", timeout=30)
    p_res = proxy_session.get(f"{BASE_URL}/api/jl/pyq/jee-main", headers={"X-JL-Sid": proxy_sid}, timeout=30)
    assert d_res.status_code == 200, d_res.text[:400]
    assert p_res.status_code == 200, p_res.text[:400]

    direct = _unwrap(d_res.json())
    proxy = _unwrap(p_res.json())

    assert direct.get("total") == 30
    assert proxy.get("total") == 30
    assert direct.get("total") == proxy.get("total")
    assert sorted(direct.get("years", []), reverse=True) == [2026, 2025]
    assert direct.get("years") == proxy.get("years")

    d_items = sorted([_stable_meta(i) for i in direct.get("items", [])], key=lambda x: str(x.get("id")))
    p_items = sorted([_stable_meta(i) for i in proxy.get("items", [])], key=lambda x: str(x.get("id")))
    assert len(d_items) == 30
    assert len(p_items) == 30
    assert d_items == p_items


# JEE chapter catalogue parity direct vs proxy
def test_jee_chapter_catalogue_parity(direct_session: requests.Session, proxy_session: requests.Session, proxy_sid: str):
    _must_have_env()
    _login_direct(direct_session)
    _login_proxy(proxy_session, proxy_sid)

    path = "/exam-navigation/jee-main/catalogue?kind=chapters&subject=Physics&q=&page=1"
    d_res = direct_session.get(f"{JEELIVE_API}{path}", timeout=30)
    p_res = proxy_session.get(f"{BASE_URL}/api/jl{path}", headers={"X-JL-Sid": proxy_sid}, timeout=30)
    assert d_res.status_code == 200, d_res.text[:400]
    assert p_res.status_code == 200, p_res.text[:400]

    direct = _unwrap(d_res.json())
    proxy = _unwrap(p_res.json())

    assert direct.get("total") == proxy.get("total")
    assert direct.get("pages") == proxy.get("pages")
    assert direct.get("subject_counts") == proxy.get("subject_counts")

    d_rows = [{"id": x.get("id"), "title": x.get("title"), "count": x.get("count"), "maximum": x.get("maximum")} for x in direct.get("items", [])]
    p_rows = [{"id": x.get("id"), "title": x.get("title"), "count": x.get("count"), "maximum": x.get("maximum")} for x in proxy.get("items", [])]
    assert d_rows == p_rows


# BITSAT/COMEDK mocks+chapters and live-series reads should match across direct/proxy sources
@pytest.mark.parametrize(
    "path",
    [
        "/exam-navigation/bitsat/catalogue?kind=mocks&subject=&q=&page=1",
        "/exam-navigation/bitsat/catalogue?kind=chapters&subject=Physics&q=&page=1",
        "/exam-navigation/comedk/catalogue?kind=mocks&subject=&q=&page=1",
        "/exam-navigation/comedk/catalogue?kind=chapters&subject=Physics&q=&page=1",
        "/series/all-india-jee",
    ],
)
def test_bitsat_comedk_and_live_series_parity(
    path: str,
    direct_session: requests.Session,
    proxy_session: requests.Session,
    proxy_sid: str,
):
    _must_have_env()
    _login_direct(direct_session)
    _login_proxy(proxy_session, proxy_sid)

    d_res = direct_session.get(f"{JEELIVE_API}{path}", timeout=30)
    p_res = proxy_session.get(f"{BASE_URL}/api/jl{path}", headers={"X-JL-Sid": proxy_sid}, timeout=30)
    assert d_res.status_code == 200, f"direct {path}: {d_res.status_code} {d_res.text[:240]}"
    assert p_res.status_code == 200, f"proxy {path}: {p_res.status_code} {p_res.text[:240]}"
    assert _normalize(_unwrap(d_res.json())) == _normalize(_unwrap(p_res.json()))


# Completed real canonical PYQ result should have matching signatures and asset hashes across direct/proxy
def test_completed_pyq_result_signature_and_asset_hash_parity(
    direct_session: requests.Session,
    proxy_session: requests.Session,
    proxy_sid: str,
):
    _must_have_env()
    if not ITER35_COMPLETED_ATTEMPT_ID:
        pytest.skip("Set ITER35_COMPLETED_ATTEMPT_ID to the newly completed canonical PYQ attempt id.")

    _login_direct(direct_session)
    _login_proxy(proxy_session, proxy_sid)

    attempt_id = ITER35_COMPLETED_ATTEMPT_ID
    d_result_res = direct_session.get(f"{JEELIVE_API}/attempts/{attempt_id}/results?score_version=original", timeout=40)
    p_result_res = proxy_session.get(
        f"{BASE_URL}/api/jl/attempts/{attempt_id}/results?score_version=original",
        headers={"X-JL-Sid": proxy_sid},
        timeout=40,
    )
    assert d_result_res.status_code == 200, d_result_res.text[:400]
    assert p_result_res.status_code == 200, p_result_res.text[:400]

    direct_result = _unwrap(d_result_res.json())
    proxy_result = _unwrap(p_result_res.json())

    assert direct_result.get("id") == proxy_result.get("id") == attempt_id
    assert direct_result.get("summary") == proxy_result.get("summary")

    d_sigs = _question_ref_signatures(direct_result)
    p_sigs = _question_ref_signatures(proxy_result)
    assert len(d_sigs) == 75
    assert len(p_sigs) == 75
    assert d_sigs == p_sigs

    questions = direct_result.get("questions") or []
    for kind, count_field in [("question", "asset_count"), ("solution", "solution_asset_count")]:
        candidate = next((q for q in questions if int(q.get(count_field) or 0) > 0), None)
        assert candidate, f"Selected paper has no supplied {kind} asset for parity verification"
        qid = candidate["id"]
        path = f"/attempts/{attempt_id}/questions/{qid}/asset/{kind}/0"
        d_asset = direct_session.get(f"{JEELIVE_API}{path}", timeout=40)
        p_asset = proxy_session.get(f"{BASE_URL}/api/jl{path}", headers={"X-JL-Sid": proxy_sid}, timeout=40)
        assert d_asset.status_code == p_asset.status_code == 200
        assert d_asset.headers.get("content-type", "").startswith("image/")
        assert _sha256_bytes(d_asset.content) == _sha256_bytes(p_asset.content)
