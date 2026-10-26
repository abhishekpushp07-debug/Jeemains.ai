# Iteration 33: real PYQ cross-environment validation (live app backend vs source-project backend)
import os
import uuid

import pytest
import requests
from dotenv import load_dotenv


load_dotenv("/app/frontend/.env")

APP_BASE = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "").rstrip("/")
LIVE_API = os.environ.get("EXPO_PUBLIC_JEELIVE_API", "").rstrip("/")
SOURCE_API = os.environ.get("PYQ_SOURCE_API", "").rstrip("/")
PHONE = "9000000001"

# This historical investigation asserts a data-source mismatch and creates pilot
# attempts. Never run it as an ordinary regression or against an unintended host.
pytestmark = pytest.mark.skipif(
    os.environ.get("PYQ_RUN_SOURCE_INVESTIGATION") != "1",
    reason="Explicit PYQ_RUN_SOURCE_INVESTIGATION=1 and PYQ_SOURCE_API required; creates pilot practice attempts.",
)


def _unwrap(payload):
    return payload.get("data", payload) if isinstance(payload, dict) else payload


def _must_have_env():
    if not APP_BASE or not LIVE_API or not SOURCE_API:
        pytest.skip("Required public env vars are missing for iteration 33 live integration tests.")


def _login(session: requests.Session, base: str):
    response = session.post(f"{base}/auth/phone", json={"phone": PHONE}, timeout=30)
    assert response.status_code == 200, response.text[:400]
    me = session.get(f"{base}/auth/me", timeout=30)
    assert me.status_code == 200, me.text[:400]
    return _unwrap(me.json())


@pytest.fixture(scope="module")
def live_session():
    return requests.Session()


@pytest.fixture(scope="module")
def source_session():
    return requests.Session()


# Auth and catalogue divergence proof with separate cookie jars and account IDs
def test_live_vs_source_catalogue_and_uid_proof(live_session: requests.Session, source_session: requests.Session):
    _must_have_env()

    live_me = _login(live_session, LIVE_API)
    source_me = _login(source_session, SOURCE_API)

    assert live_me.get("id")
    assert source_me.get("id")
    assert live_me["id"] != source_me["id"]

    live_cat_res = live_session.get(f"{LIVE_API}/pyq/jee-main", timeout=30)
    source_cat_res = source_session.get(f"{SOURCE_API}/pyq/jee-main", timeout=30)
    assert live_cat_res.status_code == 200, live_cat_res.text[:400]
    assert source_cat_res.status_code == 200, source_cat_res.text[:400]

    live_cat = _unwrap(live_cat_res.json())
    source_cat = _unwrap(source_cat_res.json())

    assert isinstance(live_cat.get("items"), list)
    assert isinstance(source_cat.get("items"), list)
    assert live_cat.get("total") == len(live_cat.get("items", []))
    assert source_cat.get("total") == len(source_cat.get("items", []))

    assert live_cat.get("total") == 0
    assert source_cat.get("total") == 30
    assert 2026 in source_cat.get("years", [])
    assert 2025 in source_cat.get("years", [])


# Current live environment should reject known source paper IDs under /my/sets
def test_live_rejects_known_source_bundle_ids(live_session: requests.Session, source_session: requests.Session):
    _must_have_env()
    _login(live_session, LIVE_API)
    _login(source_session, SOURCE_API)

    source_cat = _unwrap(source_session.get(f"{SOURCE_API}/pyq/jee-main", timeout=30).json())
    ids = [row.get("id") for row in source_cat.get("items", [])[:2] if row.get("id")]
    assert len(ids) >= 2

    for paper_id in ids:
        r = live_session.get(f"{LIVE_API}/my/sets/{paper_id}", timeout=30)
        assert r.status_code == 404, f"expected 404 for {paper_id}, got {r.status_code}"


# Source-project end-to-end: false live_enabled paper should still start/continue/re-attempt via real server permissions
def test_source_false_live_flag_start_resume_submit_and_reattempt(source_session: requests.Session):
    _must_have_env()
    _login(source_session, SOURCE_API)

    cat = _unwrap(source_session.get(f"{SOURCE_API}/pyq/jee-main", timeout=30).json())
    seed = [p for p in cat.get("items", []) if p.get("count", 0) > 0 and p.get("id")]
    assert seed, "No startable source papers found"

    paper_id = None
    detail = None
    for row in seed[:8]:
        r = source_session.get(f"{SOURCE_API}/my/sets/{row['id']}", timeout=30)
        if r.status_code != 200:
            continue
        d = _unwrap(r.json())
        # source contract: live_enabled=false is expected for ordinary PYQ practice
        if isinstance(d, dict) and d.get("live_enabled") is False:
            paper_id = row["id"]
            detail = d
            break
    assert paper_id, "Could not find a /my/sets paper detail with live_enabled=false"
    assert isinstance(detail, dict)

    preflight = source_session.post(
        f"{SOURCE_API}/sets/{paper_id}/preflight",
        json={"preview": False, "test_response": "25"},
        timeout=30,
    )
    assert preflight.status_code == 200, preflight.text[:400]

    same_key = "iter33-" + uuid.uuid4().hex
    start_1 = _unwrap(source_session.post(
        f"{SOURCE_API}/sets/{paper_id}/start",
        json={"start_key": same_key, "device_checked": True, "preview": False},
        timeout=30,
    ).json())
    assert start_1.get("id")
    attempt_id = start_1["id"]
    print(f"ITER33_SOURCE_ATTEMPT_ID={attempt_id}")

    # Same key should be idempotent per server contract
    start_2_res = source_session.post(
        f"{SOURCE_API}/sets/{paper_id}/start",
        json={"start_key": same_key, "device_checked": True, "preview": False},
        timeout=30,
    )
    assert start_2_res.status_code == 200, start_2_res.text[:400]
    start_2 = _unwrap(start_2_res.json())
    assert start_2.get("id") == attempt_id

    attempt = _unwrap(source_session.get(f"{SOURCE_API}/attempts/{attempt_id}", timeout=30).json())
    assert isinstance(attempt.get("questions"), list)
    assert len(attempt["questions"]) == 75

    first_q = attempt["questions"][0]
    qid = first_q["id"]

    # Question source image should be available during attempt
    q_image = source_session.get(
        f"{SOURCE_API}/attempts/{attempt_id}/questions/{qid}/asset/question/0",
        timeout=30,
    )
    assert q_image.status_code == 200

    # Supplied solution asset should be inaccessible before submit
    s_image = source_session.get(
        f"{SOURCE_API}/attempts/{attempt_id}/questions/{qid}/asset/solution/0",
        timeout=30,
    )
    assert s_image.status_code in (403, 404)

    # Autosave one answer and verify resume on same attempt id
    answer_payload = {
        "value": "A",
        "marked": False,
        "revision": 1,
        "request_id": "iter33-ans-" + uuid.uuid4().hex,
    }
    put_answer = source_session.put(
        f"{SOURCE_API}/attempts/{attempt_id}/answers/{qid}",
        json=answer_payload,
        timeout=30,
    )
    assert put_answer.status_code == 200, put_answer.text[:400]

    resumed = _unwrap(source_session.get(f"{SOURCE_API}/attempts/{attempt_id}", timeout=30).json())
    assert resumed.get("id") == attempt_id
    assert isinstance(resumed.get("answers"), dict)
    assert qid in resumed["answers"]

    submit = source_session.post(f"{SOURCE_API}/attempts/{attempt_id}/submit", json={}, timeout=30)
    assert submit.status_code in (200, 202), submit.text[:400]

    result = source_session.get(f"{SOURCE_API}/attempts/{attempt_id}/results?score_version=original", timeout=40)
    assert result.status_code in (200, 202), result.text[:400]
    print(f"ITER33_RESULT_ENDPOINT_ID={attempt_id};status={result.status_code}")

    # Re-attempt should generate a new attempt id and not overwrite older result id
    preflight_2 = source_session.post(
        f"{SOURCE_API}/sets/{paper_id}/preflight",
        json={"preview": False, "test_response": "25"},
        timeout=30,
    )
    assert preflight_2.status_code == 200, preflight_2.text[:400]

    start_3_res = source_session.post(
        f"{SOURCE_API}/sets/{paper_id}/start",
        json={"start_key": "iter33-reattempt-" + uuid.uuid4().hex, "device_checked": True, "preview": False},
        timeout=30,
    )
    assert start_3_res.status_code == 200, start_3_res.text[:400]
    start_3 = _unwrap(start_3_res.json())
    assert start_3.get("id")
    assert start_3["id"] != attempt_id
    print(f"ITER33_SOURCE_REATTEMPT_ID={start_3['id']}")