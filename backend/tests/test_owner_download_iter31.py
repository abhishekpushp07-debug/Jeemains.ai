# Iteration 31: owner ZIP grant capability validations + NEET catalog smoke regression.
import hashlib
import json
import os
import subprocess
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import pytest
import requests
from dotenv import dotenv_values
from pymongo import MongoClient


ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ENV = dotenv_values(ROOT / "frontend" / ".env")
BACKEND_ENV = dotenv_values(ROOT / "backend" / ".env")

BASE_URL = (os.environ.get("EXPO_PUBLIC_BACKEND_URL") or FRONTEND_ENV.get("EXPO_PUBLIC_BACKEND_URL") or "").rstrip("/")
MONGO_URL = os.environ.get("MONGO_URL") or BACKEND_ENV.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME") or BACKEND_ENV.get("DB_NAME")

API_OWNER = f"{BASE_URL}/api/owner-downloads"
API_RF = f"{BASE_URL}/api/rf"
ZIP_PATH = ROOT / "neetlive" / "exports" / "neetlive-content.zip"


def _token_from_url(url: str) -> str:
    return urlparse(url).path.rstrip("/").split("/")[-1]


def _req(method: str, url: str, **kwargs) -> requests.Response:
    # single retry for intermittent network edge
    r = requests.request(method, url, timeout=45, **kwargs)
    if r.status_code >= 500:
        r = requests.request(method, url, timeout=45, **kwargs)
    return r


@pytest.fixture(scope="module")
def env_ready():
    if not BASE_URL:
        pytest.skip("EXPO_PUBLIC_BACKEND_URL missing")
    if not MONGO_URL or not DB_NAME:
        pytest.skip("backend DB env missing")
    if not ZIP_PATH.exists():
        pytest.skip("neet zip not found")


@pytest.fixture(scope="module")
def db(env_ready):
    return MongoClient(MONGO_URL)[DB_NAME]


@pytest.fixture(scope="module")
def zip_meta(env_ready):
    payload = ZIP_PATH.read_bytes()
    return {
        "bytes": payload,
        "size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


@pytest.fixture(scope="module")
def grants(db):
    coll = db.owner_download_grants
    created_ids: list[str] = []
    yield coll, created_ids
    if created_ids:
        coll.delete_many({"id": {"$in": created_ids}})


def _issue_grant(hours: int = 1) -> dict:
    cmd = [
        "python",
        "/app/backend/tools/owner_download.py",
        "issue",
        "--hours",
        str(hours),
        "--base-url",
        BASE_URL,
    ]
    out = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return json.loads(out.stdout.strip())


def _revoke_grant(grant_id: str) -> dict:
    cmd = ["python", "/app/backend/tools/owner_download.py", "revoke", "--grant-id", grant_id]
    out = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return json.loads(out.stdout.strip())


# --- Owner grant issue/redeem/revoke happy path and storage assertions ---
class TestOwnerGrantHappyPath:
    def test_valid_grant_returns_exact_zip_and_private_headers(self, grants, zip_meta):
        coll, created_ids = grants
        issued = _issue_grant(hours=1)
        created_ids.append(issued["grant_id"])

        token = _token_from_url(issued["download_url"])
        r = _req("GET", f"{API_OWNER}/{token}")

        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("application/zip")
        assert r.headers.get("content-disposition") == 'attachment; filename="neetlive-content.zip"'
        # The preview ingress normalizes Cache-Control to
        # "no-store, no-cache, must-revalidate". RFC no-store forbids storage by
        # BOTH private and shared caches; require its semantics, not byte order.
        directives = {part.strip().lower() for part in r.headers.get("cache-control", "").split(",")}
        assert "no-store" in directives
        assert "public" not in directives
        assert not any(part.startswith(("s-maxage=", "max-age=")) for part in directives)
        assert r.headers.get("pragma") == "no-cache"
        assert r.headers.get("referrer-policy") == "no-referrer"
        assert r.headers.get("x-content-type-options") == "nosniff"
        assert len(r.content) == zip_meta["size"]
        assert hashlib.sha256(r.content).hexdigest() == zip_meta["sha256"]

        grant_doc = coll.find_one({"id": issued["grant_id"]}, {"_id": 0})
        assert grant_doc is not None
        assert grant_doc["artifact_type"] == "neetlive-content-zip"
        assert "token" not in grant_doc and "raw_token" not in grant_doc
        assert token.isalnum() and len(token) == 64
        assert grant_doc["token_sha256"] == hashlib.sha256(bytes.fromhex(token)).hexdigest()

    def test_cli_revoke_grant_invalidates_existing_token(self, grants):
        _, created_ids = grants
        issued = _issue_grant(hours=1)
        created_ids.append(issued["grant_id"])
        token = _token_from_url(issued["download_url"])

        revoked = _revoke_grant(issued["grant_id"])
        assert revoked["revoked"] is True

        r = _req("GET", f"{API_OWNER}/{token}")
        assert r.status_code == 404
        assert r.headers.get("content-type", "").startswith("application/json")


# --- Invalid/malformed/missing/expired/revoked/type/hash grants must deny ---
class TestOwnerGrantDenials:
    def test_random_or_malformed_or_missing_grants_return_404_no_zip(self):
        candidates = [
            "abcd",
            "g" * 64,
            "0" * 63,
            "f" * 64,
            uuid.uuid4().hex + uuid.uuid4().hex,
        ]
        for token in candidates:
            r = _req("GET", f"{API_OWNER}/{token}")
            assert r.status_code == 404
            assert not r.headers.get("content-type", "").startswith("application/zip")
            assert b"PK\x03\x04" not in r.content[:4]

    def test_wrong_x_rf_user_header_cannot_authorize_missing_or_invalid_grant(self):
        bad = "f" * 64
        r = _req("GET", f"{API_OWNER}/{bad}", headers={"X-RF-User": "db0c62b8-eeaf-41be-b8b1-05f5f34ac1d8"})
        assert r.status_code == 404
        assert not r.headers.get("content-type", "").startswith("application/zip")

    def test_expired_grant_denied_even_before_ttl_cleanup(self, grants, zip_meta):
        coll, created_ids = grants
        raw = os.urandom(32)
        token = raw.hex()
        grant_id = f"TEST_iter31_expired_{uuid.uuid4().hex[:12]}"
        created_ids.append(grant_id)
        coll.insert_one(
            {
                "id": grant_id,
                "token_sha256": hashlib.sha256(raw).hexdigest(),
                "artifact_type": "neetlive-content-zip",
                "artifact_sha256": zip_meta["sha256"],
                "created_at": datetime.now(timezone.utc) - timedelta(hours=2),
                "expires_at": datetime.now(timezone.utc) - timedelta(minutes=1),
                "revoked_at": None,
                "issued_for": "TEST_iter31",
            }
        )
        r = _req("GET", f"{API_OWNER}/{token}")
        assert r.status_code == 404

    def test_wrong_artifact_type_and_hash_denied(self, grants, zip_meta):
        coll, created_ids = grants

        raw_type = os.urandom(32)
        token_type = raw_type.hex()
        gid_type = f"TEST_iter31_type_{uuid.uuid4().hex[:12]}"
        created_ids.append(gid_type)
        coll.insert_one(
            {
                "id": gid_type,
                "token_sha256": hashlib.sha256(raw_type).hexdigest(),
                "artifact_type": "wrong-artifact",
                "artifact_sha256": zip_meta["sha256"],
                "created_at": datetime.now(timezone.utc),
                "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
                "revoked_at": None,
                "issued_for": "TEST_iter31",
            }
        )
        r1 = _req("GET", f"{API_OWNER}/{token_type}")
        assert r1.status_code == 404

        raw_hash = os.urandom(32)
        token_hash = raw_hash.hex()
        gid_hash = f"TEST_iter31_hash_{uuid.uuid4().hex[:12]}"
        created_ids.append(gid_hash)
        coll.insert_one(
            {
                "id": gid_hash,
                "token_sha256": hashlib.sha256(raw_hash).hexdigest(),
                "artifact_type": "neetlive-content-zip",
                "artifact_sha256": "0" * 64,
                "created_at": datetime.now(timezone.utc),
                "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
                "revoked_at": None,
                "issued_for": "TEST_iter31",
            }
        )
        r2 = _req("GET", f"{API_OWNER}/{token_hash}")
        assert r2.status_code == 404


# --- Endpoint method constraints, TTL index, and redacted access logs ---
class TestOwnerGrantInfraAndLogs:
    def test_no_http_mint_endpoint_and_post_download_is_405(self):
        post_existing_shape = _req("POST", f"{API_OWNER}/{'f' * 64}")
        assert post_existing_shape.status_code == 405

        post_collection = _req("POST", API_OWNER)
        assert post_collection.status_code in (404, 405)

    def test_ttl_index_expires_at_exists_and_expire_after_zero(self, db, grants):
        # Ensure CLI bootstraps indexes in this worker before assertion.
        _, created_ids = grants
        issued = _issue_grant(hours=1)
        created_ids.append(issued["grant_id"])
        info = db.owner_download_grants.index_information()
        ttl_idx = [v for v in info.values() if v.get("key") == [("expires_at", 1)] and v.get("expireAfterSeconds") == 0]
        assert len(ttl_idx) >= 1

    def test_access_log_redaction_hides_tokens_for_valid_and_invalid_requests(self, grants):
        _, created_ids = grants
        issued = _issue_grant(hours=1)
        created_ids.append(issued["grant_id"])
        token_valid = _token_from_url(issued["download_url"])
        token_invalid = "e" * 64

        _req("GET", f"{API_OWNER}/{token_valid}")
        _req("GET", f"{API_OWNER}/{token_invalid}")

        log_out = Path("/var/log/supervisor/backend.out.log")
        log_err = Path("/var/log/supervisor/backend.err.log")
        out_tail = "\n".join(log_out.read_text(errors="ignore").splitlines()[-400:]) if log_out.exists() else ""
        err_tail = "\n".join(log_err.read_text(errors="ignore").splitlines()[-400:]) if log_err.exists() else ""
        tail_text = out_tail + "\n" + err_tail

        assert token_valid not in tail_text
        assert token_invalid not in tail_text
        assert "/api/owner-downloads/[REDACTED]" in tail_text


# --- Regression smoke for NEET catalog totals/diagrams ---
class TestNeetSmoke:
    def test_neet_catalog_totals_and_diagrams_unchanged(self):
        r = _req("GET", f"{API_RF}/catalog", params={"exam": "NEET"})
        assert r.status_code == 200
        body = r.json()

        total = sum(s["total"] for s in body["subjects"])
        assert total == 7585
        assert body["diagram_count"] == 18