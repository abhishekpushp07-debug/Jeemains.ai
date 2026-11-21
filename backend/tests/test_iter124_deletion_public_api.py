# Iteration124: account deletion + owner panel closed doors, against the PUBLIC preview URL (read-only / wrong-PIN only)
import os
import re

import pytest
import requests

BASE_URL = (os.environ.get("EXPO_PUBLIC_BACKEND_URL") or os.environ.get("EXPO_BACKEND_URL")).rstrip("/")
DEL = f"{BASE_URL}/api/account/delete-request"
FAKE_PHONE, FAKE_PIN = "1000000001", "0000"  # never the QA learner's PIN


@pytest.fixture
def s():
    x = requests.Session()
    x.headers.update({"Content-Type": "application/json"})
    return x


# --- delete-request validation: 422 with friendly detail, PIN never echoed
@pytest.mark.parametrize("body,msg", [
    ({"phone": "12", "pin": "9137", "confirm": "DELETE"}, "registered mobile number"),
    ({"phone": FAKE_PHONE, "pin": "913", "confirm": "DELETE"}, "exactly 4 digits"),
    ({"phone": FAKE_PHONE, "pin": "9137", "confirm": "nope"}, "Type DELETE"),
])
def test_delete_request_validation(s, body, msg):
    r = s.post(DEL, json=body, timeout=30)
    assert r.status_code == 422
    assert msg in r.json()["detail"]
    assert body["pin"] not in r.text


def test_delete_request_pattern_pin_not_echoed(s):
    # pydantic-level failure (too long / extra field) must also hide the PIN
    r = s.post(DEL, json={"phone": FAKE_PHONE, "pin": "91372468", "confirm": "DELETE", "x": 1}, timeout=30)
    assert r.status_code == 422
    assert "91372468" not in r.text


def test_delete_request_lowercase_delete_accepted_wrong_pin(s):
    # 'delete' in lower case passes validation; the website then rejects the wrong PIN -> 401/422/429, nothing deleted
    r = s.post(DEL, json={"phone": FAKE_PHONE, "pin": FAKE_PIN, "confirm": "delete"}, timeout=60)
    assert r.status_code in (401, 422, 429), r.text
    assert FAKE_PIN not in r.text or r.status_code == 429
    if r.status_code == 401:
        assert "Nothing was deleted" in r.json()["detail"]


def test_delete_status_unknown_404(s):
    r = s.get(f"{DEL}/DEL-AAAA-AAAA", timeout=30)
    assert r.status_code == 404
    assert "No deletion request" in r.json()["detail"]


def test_delete_status_bad_format_404(s):
    assert s.get(f"{DEL}/hello", timeout=30).status_code == 404


# --- public web page
def test_public_page_and_csp(s):
    r = s.get(f"{BASE_URL}/api/legal/delete-account", timeout=30)
    assert r.status_code == 200
    for tid in ("public-deletion-phone", "public-deletion-pin", "public-deletion-confirm", "public-deletion-agree", "public-deletion-submit", "public-deletion-error"):
        assert f'data-testid="{tid}"' in r.text, tid
    csp = r.headers.get("content-security-policy", "")
    assert re.search(r"script-src 'nonce-[^']+'", csp)
    assert "connect-src 'self'" in csp
    nonce = re.search(r"nonce-([^']+)'", csp).group(1)
    assert f'nonce="{nonce}"' in r.text


# --- owner panel closed doors
def test_owner_page_renders(s):
    r = s.get(f"{BASE_URL}/api/owner/deletions", timeout=30)
    assert r.status_code == 200
    assert "owner-login" in r.text


def test_owner_list_requires_session(s):
    assert s.get(f"{BASE_URL}/api/owner/deletion-requests", timeout=30).status_code == 401


def test_owner_complete_needs_header(s):
    assert s.post(f"{BASE_URL}/api/owner/deletion-requests/DEL-AAAA-AAAA/complete", json={}, timeout=30).status_code == 403


def test_owner_complete_header_no_session(s):
    r = s.post(f"{BASE_URL}/api/owner/deletion-requests/DEL-AAAA-AAAA/complete", json={}, headers={"X-Owner-Panel": "1"}, timeout=30)
    assert r.status_code == 401


def test_owner_wrong_login(s):
    r = s.post(f"{BASE_URL}/api/owner/session", json={"email": "nobody@example.com", "password": "wrongpassword1"}, headers={"X-Owner-Panel": "1"}, timeout=60)
    assert r.status_code in (401, 403, 429), r.text
    assert "wrongpassword1" not in r.text
