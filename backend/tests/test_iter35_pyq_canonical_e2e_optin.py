# Iteration 35: canonical PYQ live write E2E (opt-in only) for approved pilot
import os
import time
import uuid

import pytest
import requests
from dotenv import load_dotenv


load_dotenv("/app/frontend/.env")

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "").rstrip("/")
JEELIVE_API = os.environ.get("EXPO_PUBLIC_JEELIVE_API", "").rstrip("/")
PHONE = "9000000001"

pytestmark = pytest.mark.skipif(
    os.environ.get("ITER35_RUN_CANONICAL_WRITE") != "1",
    reason="Set ITER35_RUN_CANONICAL_WRITE=1 to run canonical write E2E (creates up to two pilot attempts).",
)


def _unwrap(payload):
    return payload.get("data", payload) if isinstance(payload, dict) else payload


@pytest.fixture(scope="module")
def session():
    return requests.Session()


def _login(s: requests.Session):
    r = s.post(f"{JEELIVE_API}/auth/phone", json={"phone": PHONE}, timeout=30)
    assert r.status_code == 200, r.text[:400]
    me = s.get(f"{JEELIVE_API}/auth/me", timeout=30)
    assert me.status_code == 200, me.text[:400]
    data = _unwrap(me.json())
    assert data.get("id") == "db0c62b8-eeaf-41be-b8b1-05f5f34ac1d8"
    return data


def _pick_untouched_paper(s: requests.Session) -> dict:
    cat_res = s.get(f"{JEELIVE_API}/pyq/jee-main", timeout=30)
    assert cat_res.status_code == 200, cat_res.text[:400]
    cat = _unwrap(cat_res.json())
    items = cat.get("items", [])
    assert len(items) == 30
    # Prefer untouched paper (no attempt history) for safer verification.
    untouched = [p for p in items if int(p.get("attempt_count") or 0) == 0 and not p.get("attempt") and not p.get("latest_result_id")]
    if not untouched:
        pytest.skip("No untouched pilot paper; refuse to change existing attempts.")
    return untouched[0]


# Canonical real-paper E2E: start -> save -> continue same ID -> submit -> result/solutions -> re-attempt new ID
def test_canonical_pyq_real_e2e(session: requests.Session):
    if not BASE_URL or not JEELIVE_API:
        pytest.skip("Required public env vars are missing.")

    me = _login(session)
    paper = _pick_untouched_paper(session)
    paper_id = paper["id"]

    detail = session.get(f"{JEELIVE_API}/my/sets/{paper_id}", timeout=30)
    assert detail.status_code == 200, detail.text[:400]

    preflight = session.post(
        f"{JEELIVE_API}/sets/{paper_id}/preflight",
        json={"preview": False, "test_response": "25"},
        timeout=30,
    )
    assert preflight.status_code == 200, preflight.text[:400]

    start_key = "iter35-" + uuid.uuid4().hex
    start = session.post(
        f"{JEELIVE_API}/sets/{paper_id}/start",
        json={"start_key": start_key, "device_checked": True, "preview": False},
        timeout=30,
    )
    assert start.status_code == 200, start.text[:400]
    started = _unwrap(start.json())
    attempt_id = started.get("id")
    assert attempt_id
    print(f"ITER35_CANONICAL_UID={me.get('id')}")
    print(f"ITER35_CANONICAL_PAPER_ID={paper_id}")
    print(f"ITER35_CANONICAL_ATTEMPT_ID={attempt_id}")

    # continue should not create a new attempt when start key repeats
    repeat = session.post(
        f"{JEELIVE_API}/sets/{paper_id}/start",
        json={"start_key": start_key, "device_checked": True, "preview": False},
        timeout=30,
    )
    assert repeat.status_code == 200, repeat.text[:400]
    repeated = _unwrap(repeat.json())
    assert repeated.get("id") == attempt_id

    attempt = _unwrap(session.get(f"{JEELIVE_API}/attempts/{attempt_id}", timeout=30).json())
    questions = attempt.get("questions") or []
    assert len(questions) == 75
    first_q = questions[0]
    qid = first_q["id"]

    q_image = session.get(f"{JEELIVE_API}/attempts/{attempt_id}/questions/{qid}/asset/question/0", timeout=30)
    assert q_image.status_code == 200

    save = session.put(
        f"{JEELIVE_API}/attempts/{attempt_id}/answers/{qid}",
        json={
            "value": "A",
            "marked": False,
            "revision": 1,
            "request_id": "iter35-ans-" + uuid.uuid4().hex,
        },
        timeout=30,
    )
    assert save.status_code == 200, save.text[:400]

    resumed = _unwrap(session.get(f"{JEELIVE_API}/attempts/{attempt_id}", timeout=30).json())
    assert resumed.get("id") == attempt_id
    assert isinstance(resumed.get("answers"), dict)
    assert qid in resumed["answers"]

    submit = session.post(f"{JEELIVE_API}/attempts/{attempt_id}/submit", json={}, timeout=30)
    assert submit.status_code in (200, 202), submit.text[:400]

    status = None
    result_payload = None
    for _ in range(15):
        result = session.get(f"{JEELIVE_API}/attempts/{attempt_id}/results?score_version=original", timeout=40)
        assert result.status_code in (200, 202), result.text[:400]
        status = result.status_code
        if status == 200:
            result_payload = _unwrap(result.json())
            break
        time.sleep(2)

    assert status == 200, "Result remained pending after polling"
    assert result_payload and result_payload.get("id") == attempt_id
    assert result_payload.get("summary")
    print(f"ITER35_CANONICAL_COMPLETED_ATTEMPT_ID={attempt_id}")

    rows = result_payload.get("questions") or []
    assert len(rows) == 75
    solution_probe = next((q for q in rows if int(q.get("solution_asset_count") or 0) > 0), None)
    if solution_probe:
        sol_asset = session.get(
            f"{JEELIVE_API}/attempts/{attempt_id}/questions/{solution_probe['id']}/asset/solution/0",
            timeout=40,
        )
        assert sol_asset.status_code == 200

    preflight_2 = session.post(
        f"{JEELIVE_API}/sets/{paper_id}/preflight",
        json={"preview": False, "test_response": "25"},
        timeout=30,
    )
    assert preflight_2.status_code == 200, preflight_2.text[:400]

    reattempt = session.post(
        f"{JEELIVE_API}/sets/{paper_id}/start",
        json={"start_key": "iter35-reattempt-" + uuid.uuid4().hex, "device_checked": True, "preview": False},
        timeout=30,
    )
    assert reattempt.status_code == 200, reattempt.text[:400]
    reattempt_data = _unwrap(reattempt.json())
    reattempt_id = reattempt_data.get("id")
    assert reattempt_id
    assert reattempt_id != attempt_id
    print(f"ITER35_CANONICAL_REATTEMPT_ID={reattempt_id}")

    # old result must still exist after new reattempt
    old_result_again = session.get(f"{JEELIVE_API}/attempts/{attempt_id}/results?score_version=original", timeout=40)
    assert old_result_again.status_code == 200, old_result_again.text[:400]
    old_payload = _unwrap(old_result_again.json())
    assert old_payload.get("id") == attempt_id
