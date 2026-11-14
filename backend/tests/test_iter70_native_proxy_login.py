# Iteration 70: phone login through /api/jl proxy (native now uses same path as web) + /api/rf/access with X-JL-Sid.
# Single sign-in per run (rate limits). Credentials read from env JL_QA_PHONE / JL_QA_PIN (see /app/memory/test_credentials.md).
import os
import uuid
import hashlib
import pytest
import requests
from pymongo import MongoClient
from dotenv import dotenv_values

FRONT = dotenv_values("/app/frontend/.env")
BASE_URL = (os.environ.get("EXPO_PUBLIC_BACKEND_URL") or FRONT["EXPO_PUBLIC_BACKEND_URL"]).rstrip("/")
PHONE, PIN = os.environ.get("JL_QA_PHONE"), os.environ.get("JL_QA_PIN")
BACK = dotenv_values("/app/backend/.env")
SID = str(uuid.uuid4())
STATE = {}


def unwrap(body):
    return body["data"] if isinstance(body, dict) and body.get("meta", {}).get("api_version") else body


@pytest.fixture(scope="module", autouse=True)
def cleanup():
    yield
    # Remove only the jar/grant this run created (by exact sid / token digest). No canonical logout.
    db = MongoClient(BACK["MONGO_URL"])[BACK["DB_NAME"]]
    db.jl_jars.delete_one({"sid": SID})
    if STATE.get("token"):
        db.rf_access.delete_one({"digest": hashlib.sha256(STATE["token"].encode()).hexdigest()})


# Proxy header validation: missing / invalid handle must be 4xx, not 500
class TestSidValidation:
    def test_missing_sid(self):
        r = requests.get(f"{BASE_URL}/api/jl/auth/session", timeout=30)
        assert r.status_code in (400, 422), r.status_code

    def test_invalid_sid(self):
        r = requests.get(f"{BASE_URL}/api/jl/auth/session", headers={"X-JL-Sid": "bad;sid"}, timeout=30)
        assert r.status_code in (400, 422), r.status_code

    def test_fresh_sid_session_is_anonymous(self):
        r = requests.get(f"{BASE_URL}/api/jl/auth/session", headers={"X-JL-Sid": str(uuid.uuid4())}, timeout=30)
        assert r.status_code in (200, 401), r.status_code
        if r.status_code == 200:
            assert unwrap(r.json()).get("user") is None

    def test_rf_access_without_sid_or_cookie(self):
        r = requests.post(f"{BASE_URL}/api/rf/access", json={}, timeout=30)
        assert r.status_code == 401, r.status_code

    def test_rf_access_unknown_sid(self):
        r = requests.post(f"{BASE_URL}/api/rf/access", json={}, headers={"X-JL-Sid": str(uuid.uuid4())}, timeout=30)
        assert r.status_code == 401, r.status_code


# Phone + PIN login via proxy, session persistence, RF access grant
class TestProxyLoginFlow:
    def test_1_phone_login(self):
        if not PHONE or not PIN:
            pytest.skip("JL_QA_PHONE/JL_QA_PIN not set")
        r = requests.post(f"{BASE_URL}/api/jl/auth/phone", json={"phone": PHONE, "pin": PIN},
                          headers={"X-JL-Sid": SID}, timeout=40)
        assert r.status_code == 200, (r.status_code, r.text[:200])
        u = unwrap(r.json())
        uid = (u.get("user") or u).get("id") if isinstance(u, dict) else None
        assert isinstance(uid, str) and uid
        STATE["uid"] = uid
        # Ingress may add Cloudflare __cf_bm; canonical auth cookies must never reach the client.
        leaked = [c for c in r.headers.get("set-cookie", "").split(",") if "access_token" in c or "refresh_token" in c]
        assert not leaked, "canonical cookies must stay server-side"

    def test_2_session_persists(self):
        if "uid" not in STATE:
            pytest.skip("login failed")
        r = requests.get(f"{BASE_URL}/api/jl/auth/session", headers={"X-JL-Sid": SID}, timeout=30)
        assert r.status_code == 200
        assert unwrap(r.json())["user"]["id"] == STATE["uid"]

    def test_3_rf_access(self):
        if "uid" not in STATE:
            pytest.skip("login failed")
        r = requests.post(f"{BASE_URL}/api/rf/access", json={}, headers={"X-JL-Sid": SID}, timeout=30)
        assert r.status_code == 200, (r.status_code, r.text[:200])
        d = r.json()
        assert d["user_id"] == STATE["uid"] and d["token"] and d["expires_at"]
        STATE["token"] = d["token"]

    def test_4_rf_bearer_works(self):
        if "token" not in STATE:
            pytest.skip("no grant")
        r = requests.get(f"{BASE_URL}/api/rf/catalog", timeout=30)
        assert r.status_code == 200
        r2 = requests.get(f"{BASE_URL}/api/rf/catalog", headers={"Authorization": "Bearer " + STATE["token"]}, timeout=30)
        assert r2.status_code == 200

    def test_5_lists_load(self):
        if "uid" not in STATE:
            pytest.skip("login failed")
        r = requests.get(f"{BASE_URL}/api/jl/my/tests", headers={"X-JL-Sid": SID}, timeout=40)
        assert r.status_code == 200, (r.status_code, r.text[:200])
