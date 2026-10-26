# Iteration 32: live PYQ proxy parity and Rapid Fire exam-scope regression checks
import os
import uuid

import pytest
import requests
from dotenv import load_dotenv


load_dotenv("/app/frontend/.env")

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "").rstrip("/")
JEELIVE_API = os.environ.get("EXPO_PUBLIC_JEELIVE_API", "").rstrip("/")
PHONE = "9000000001"


@pytest.fixture(scope="module")
def session():
    return requests.Session()


@pytest.fixture(scope="module")
def sid() -> str:
    return "TESTSID" + uuid.uuid4().hex[:20]


def _must_have_env():
    if not BASE_URL or not JEELIVE_API:
        pytest.skip("Required public env vars are missing for live integration tests.")


def _proxy_login_and_get_pyq(s: requests.Session, test_sid: str) -> dict:
    login = s.post(
        f"{BASE_URL}/api/jl/auth/phone",
        json={"phone": PHONE},
        headers={"X-JL-Sid": test_sid},
        timeout=30,
    )
    assert login.status_code == 200, login.text[:400]
    pyq = s.get(
        f"{BASE_URL}/api/jl/pyq/jee-main",
        headers={"X-JL-Sid": test_sid},
        timeout=30,
    )
    assert pyq.status_code == 200, pyq.text[:400]
    payload = pyq.json()
    return payload.get("data", payload)


# Proxy auth/session continuity for pilot login
def test_proxy_auth_me(session: requests.Session, sid: str):
    _must_have_env()
    login = session.post(
        f"{BASE_URL}/api/jl/auth/phone",
        json={"phone": PHONE},
        headers={"X-JL-Sid": sid},
        timeout=30,
    )
    assert login.status_code == 200, login.text[:400]

    me = session.get(
        f"{BASE_URL}/api/jl/auth/me",
        headers={"X-JL-Sid": sid},
        timeout=30,
    )
    assert me.status_code == 200, me.text[:400]
    payload = me.json()
    data = payload.get("data", payload)
    assert data.get("id")
    assert str(data.get("phone", "")).endswith("0001")


# Real PYQ catalogue contract (honest empty/list based on upstream)
def test_proxy_pyq_contract(session: requests.Session, sid: str):
    _must_have_env()
    data = _proxy_login_and_get_pyq(session, sid)

    assert isinstance(data, dict)
    assert "total" in data and "items" in data and "years" in data
    assert isinstance(data["total"], int)
    assert isinstance(data["items"], list)
    assert isinstance(data["years"], list)
    assert data["total"] == len(data["items"])


# Proxy parity with direct jeelive.ai upstream for /pyq/jee-main
def test_proxy_matches_direct_upstream(session: requests.Session, sid: str):
    _must_have_env()
    proxy_data = _proxy_login_and_get_pyq(session, sid)

    direct = requests.Session()
    direct_login = direct.post(
        f"{JEELIVE_API}/auth/phone",
        json={"phone": PHONE},
        timeout=30,
    )
    assert direct_login.status_code == 200, direct_login.text[:400]
    direct_pyq = direct.get(f"{JEELIVE_API}/pyq/jee-main", timeout=30)
    assert direct_pyq.status_code == 200, direct_pyq.text[:400]
    direct_payload = direct_pyq.json()
    direct_data = direct_payload.get("data", direct_payload)

    for key in ["total", "years", "items"]:
        assert key in proxy_data and key in direct_data
    assert proxy_data["total"] == direct_data["total"]
    assert proxy_data["years"] == direct_data["years"]
    assert [x.get("id") for x in proxy_data["items"]] == [x.get("id") for x in direct_data["items"]]


# Rapid Fire exam split sanity: JEE and NEET scoped catalogues both available
def test_rf_catalog_exam_scopes(session: requests.Session):
    _must_have_env()
    jee = session.get(f"{BASE_URL}/api/rf/catalog?exam=JEE", timeout=30)
    neet = session.get(f"{BASE_URL}/api/rf/catalog?exam=NEET", timeout=30)

    assert jee.status_code == 200
    assert neet.status_code == 200

    jee_subjects = [s["name"] for s in jee.json().get("subjects", [])]
    neet_subjects = [s["name"] for s in neet.json().get("subjects", [])]
    assert "Mathematics" in jee_subjects
    assert "Biology" in neet_subjects