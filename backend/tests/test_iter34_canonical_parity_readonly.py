# Iteration 34: canonical direct-vs-proxy read-only parity (identity, catalogues, completed history, result signatures)
import os
import uuid
import hashlib

import pytest
import requests
from dotenv import load_dotenv


load_dotenv("/app/frontend/.env")

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "").rstrip("/")
JEELIVE_API = os.environ.get("EXPO_PUBLIC_JEELIVE_API", "").rstrip("/")
PHONE = "9000000001"
EXPECTED_UID = "db0c62b8-eeaf-41be-b8b1-05f5f34ac1d8"


def _must_have_env():
    if not BASE_URL or not JEELIVE_API:
        pytest.skip("Required public env vars are missing for iteration 34 live parity tests.")


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


def _question_ref_signature_list(result_payload: dict) -> list[str]:
    questions = result_payload.get("questions") or []
    sigs = []
    for q in questions:
        qid = q.get("id") or q.get("question_id") or ""
        solution_ref = q.get("solution_ref") or q.get("solution_asset") or q.get("solution") or q.get("solution_url")
        question_ref = q.get("question_ref") or q.get("question_asset") or q.get("asset") or q.get("source")
        # Do not store content; keep only stable identity/reference fields.
        stable = {
            "id": qid,
            "qref": str(question_ref) if question_ref is not None else None,
            "sref": str(solution_ref) if solution_ref is not None else None,
        }
        sigs.append(hashlib.sha256(str(stable).encode("utf-8")).hexdigest())
    return sigs


@pytest.fixture(scope="module")
def direct_session():
    return requests.Session()


@pytest.fixture(scope="module")
def proxy_session():
    return requests.Session()


@pytest.fixture(scope="module")
def proxy_sid() -> str:
    return "TESTSID" + uuid.uuid4().hex[:20]


def _login_direct(s: requests.Session) -> dict:
    r = s.post(f"{JEELIVE_API}/auth/phone", json={"phone": PHONE}, timeout=30)
    assert r.status_code == 200, r.text[:400]
    me = s.get(f"{JEELIVE_API}/auth/me", timeout=30)
    assert me.status_code == 200, me.text[:400]
    return _unwrap(me.json())


def _login_proxy(s: requests.Session, sid: str) -> dict:
    r = s.post(
        f"{BASE_URL}/api/jl/auth/phone",
        json={"phone": PHONE},
        headers={"X-JL-Sid": sid},
        timeout=30,
    )
    assert r.status_code == 200, r.text[:400]
    me = s.get(f"{BASE_URL}/api/jl/auth/me", headers={"X-JL-Sid": sid}, timeout=30)
    assert me.status_code == 200, me.text[:400]
    return _unwrap(me.json())


# Canonical identity parity: approved phone should map to same canonical UID on direct and app-proxy paths
def test_identity_direct_and_proxy_same_uid(direct_session: requests.Session, proxy_session: requests.Session, proxy_sid: str):
    _must_have_env()
    direct_me = _login_direct(direct_session)
    proxy_me = _login_proxy(proxy_session, proxy_sid)

    assert direct_me.get("id") == EXPECTED_UID
    assert proxy_me.get("id") == EXPECTED_UID
    assert direct_me.get("id") == proxy_me.get("id")


# Canonical PYQ catalogue parity: IDs and stable metadata should match across direct and proxy
def test_pyq_catalogue_parity_direct_vs_proxy(direct_session: requests.Session, proxy_session: requests.Session, proxy_sid: str):
    _must_have_env()
    _login_direct(direct_session)
    _login_proxy(proxy_session, proxy_sid)

    d_res = direct_session.get(f"{JEELIVE_API}/pyq/jee-main", timeout=30)
    p_res = proxy_session.get(f"{BASE_URL}/api/jl/pyq/jee-main", headers={"X-JL-Sid": proxy_sid}, timeout=30)
    assert d_res.status_code == 200, d_res.text[:400]
    assert p_res.status_code == 200, p_res.text[:400]

    direct = _unwrap(d_res.json())
    proxy = _unwrap(p_res.json())

    assert direct.get("total") == proxy.get("total")
    assert direct.get("years") == proxy.get("years")

    d_items = sorted([_stable_meta(i) for i in direct.get("items", [])], key=lambda x: str(x.get("id")))
    p_items = sorted([_stable_meta(i) for i in proxy.get("items", [])], key=lambda x: str(x.get("id")))
    assert d_items == p_items


# Canonical JEE chapter catalogue parity through direct and proxy
def test_chapter_catalogue_parity_direct_vs_proxy(direct_session: requests.Session, proxy_session: requests.Session, proxy_sid: str):
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


# Completed My Tests parity and one completed result signature parity (identity/score/question refs) across both paths
def test_completed_history_and_result_signature_parity(
    direct_session: requests.Session,
    proxy_session: requests.Session,
    proxy_sid: str,
):
    _must_have_env()
    _login_direct(direct_session)
    _login_proxy(proxy_session, proxy_sid)

    query = "tab=completed&page=1&q=&status=all&exam="
    d_res = direct_session.get(f"{JEELIVE_API}/my/tests?{query}", timeout=30)
    p_res = proxy_session.get(f"{BASE_URL}/api/jl/my/tests?{query}", headers={"X-JL-Sid": proxy_sid}, timeout=30)
    assert d_res.status_code == 200, d_res.text[:400]
    assert p_res.status_code == 200, p_res.text[:400]

    direct = _unwrap(d_res.json())
    proxy = _unwrap(p_res.json())
    assert direct.get("counts") == proxy.get("counts")

    d_items = direct.get("items", [])
    p_items = proxy.get("items", [])
    d_ids = [x.get("id") for x in d_items]
    p_ids = [x.get("id") for x in p_items]
    assert d_ids == p_ids

    completed = [x for x in d_items if x.get("id") and x.get("status") == "completed"]
    if not completed:
        pytest.skip("No completed attempts available for the approved pilot on page 1.")

    selected = completed[0]
    attempt_id = selected["id"]

    d_result_res = direct_session.get(f"{JEELIVE_API}/attempts/{attempt_id}/results?score_version=original", timeout=40)
    p_result_res = proxy_session.get(
        f"{BASE_URL}/api/jl/attempts/{attempt_id}/results?score_version=original",
        headers={"X-JL-Sid": proxy_sid},
        timeout=40,
    )
    assert d_result_res.status_code in (200, 202), d_result_res.text[:400]
    assert p_result_res.status_code in (200, 202), p_result_res.text[:400]

    if d_result_res.status_code == 202 or p_result_res.status_code == 202:
        pytest.skip("Selected completed result is still grading/sealed right now.")

    direct_result = _unwrap(d_result_res.json())
    proxy_result = _unwrap(p_result_res.json())

    # Stable identity and score signatures only (no full answer/user content dump).
    assert direct_result.get("id") == proxy_result.get("id") == attempt_id
    d_summary = direct_result.get("summary") or {}
    p_summary = proxy_result.get("summary") or {}
    assert d_summary.get("score") == p_summary.get("score")
    assert d_summary.get("maximum") == p_summary.get("maximum")

    d_q_sigs = _question_ref_signature_list(direct_result)
    p_q_sigs = _question_ref_signature_list(proxy_result)
    assert d_q_sigs == p_q_sigs


# Remaining known gaps: canonical RF catalogue 404, companion RF catalogue exists, protected PYQ import status locked
def test_known_remaining_gaps_record(direct_session: requests.Session, proxy_session: requests.Session, proxy_sid: str):
    _must_have_env()

    # Canonical RF on jeelive.ai is still missing.
    rf_direct = direct_session.get(f"{JEELIVE_API}/rf/catalog", timeout=30)
    rf_proxy = proxy_session.get(f"{BASE_URL}/api/jl/rf/catalog", headers={"X-JL-Sid": proxy_sid}, timeout=30)
    assert rf_direct.status_code == 404
    assert rf_proxy.status_code == 404

    # Companion RF remains available from app backend service.
    rf_companion = proxy_session.get(f"{BASE_URL}/api/rf/catalog", timeout=30)
    assert rf_companion.status_code == 200
    assert isinstance(rf_companion.json().get("subjects"), list)

    # Protected canonical PYQ import status should not be available anonymously/learner.
    anon = requests.Session()
    studio_anon = anon.get(f"{JEELIVE_API}/studio/pyq-import/status", timeout=30)
    assert studio_anon.status_code == 401

    learner = requests.Session()
    _login_direct(learner)
    studio_learner = learner.get(f"{JEELIVE_API}/studio/pyq-import/status", timeout=30)
    assert studio_learner.status_code == 403
