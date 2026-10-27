"""Iteration 50: public legal/branding surface and safe deletion messaging checks.

Modules covered: legal public pages, legal method guardrails, native launch brand assets.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest
import requests


def _env_base_url() -> str | None:
    direct = os.environ.get("EXPO_PUBLIC_BACKEND_URL")
    if direct:
        return direct.rstrip("/")
    env_file = Path("/app/frontend/.env")
    if not env_file.exists():
        return None
    for line in env_file.read_text().splitlines():
        if line.startswith("EXPO_PUBLIC_BACKEND_URL="):
            return line.split("=", 1)[1].strip().rstrip("/")
    return None


BASE_URL = _env_base_url()


@pytest.fixture(scope="session")
def api_client() -> requests.Session:
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


def _png_dimensions(content: bytes) -> tuple[int, int]:
    if len(content) < 24 or content[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Not a PNG payload")
    width = int.from_bytes(content[16:20], "big")
    height = int.from_bytes(content[20:24], "big")
    return width, height


def test_iter50_base_url_available():
    """Config module: public preview URL is present."""
    assert BASE_URL, "EXPO_PUBLIC_BACKEND_URL is missing; cannot run public endpoint tests."


def test_iter50_legal_privacy_html_headers_and_content(api_client: requests.Session):
    """Legal module: privacy page is public, static, and hardened."""
    response = api_client.get(f"{BASE_URL}/api/legal/privacy", timeout=20)
    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("text/html")
    assert "default-src 'none'" in (response.headers.get("content-security-policy") or "")
    assert response.headers.get("x-frame-options") == "DENY"
    assert "no-store" in (response.headers.get("cache-control") or "")
    assert response.headers.get("referrer-policy") == "no-referrer"
    html = response.text
    assert "Abhishek@billpe.com" in html
    assert html.count("data-testid=\"public-privacy-heading-") == 8
    assert "<script" not in html.lower()
    assert "<form" not in html.lower()


def test_iter50_legal_delete_account_unavailable_without_pin_ui(api_client: requests.Session):
    """Legal module: deletion page does not claim working deletion flow."""
    response = api_client.get(f"{BASE_URL}/api/legal/delete-account", timeout=20)
    assert response.status_code == 200
    html = response.text
    assert "Direct deletion is not available yet" in html
    assert "No PIN is collected here" in html
    assert "Delete button" in html
    assert "input" not in html.lower()
    assert "data-testid=\"public-account-deletion-page\"" in html


def test_iter50_legal_information_json_shape(api_client: requests.Session):
    """Legal module: JSON source aligns with expected public policy contract."""
    response = api_client.get(f"{BASE_URL}/api/legal/information", timeout=20)
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("version") == "2026-10-27"
    assert payload.get("supportEmail") == "Abhishek@billpe.com"
    assert isinstance(payload.get("sections"), list) and len(payload["sections"]) == 8
    deletion = payload.get("deletion") or {}
    assert deletion.get("enabled") is False
    assert deletion.get("mode") == "pin_confirmed_direct"
    assert deletion.get("status") == "Direct deletion is not available yet"


@pytest.mark.parametrize("method,path", [("post", "privacy"), ("delete", "privacy"), ("post", "delete-account"), ("delete", "delete-account"), ("post", "information"), ("delete", "information")])
def test_iter50_legal_methods_not_allowed(api_client: requests.Session, method: str, path: str):
    """Legal module: no mutating legal API methods are exposed."""
    response = getattr(api_client, method)(f"{BASE_URL}/api/legal/{path}", data=json.dumps({}), timeout=20)
    assert response.status_code == 405


def test_iter50_native_launch_unknown_kind_404(api_client: requests.Session):
    """Brand module: arbitrary/private launch proxying is blocked."""
    response = api_client.get(f"{BASE_URL}/api/brand/launch/unknownkind.png", timeout=20)
    assert response.status_code == 404


@pytest.mark.parametrize(
    "kind,expected_size",
    [
        ("icon", (1024, 1024)),
        ("adaptive", (1024, 1024)),
        ("monochrome", (1024, 1024)),
        ("splash", (1132, 452)),
        ("favicon", (64, 64)),
    ],
)
def test_iter50_native_launch_known_assets(kind: str, expected_size: tuple[int, int], api_client: requests.Session):
    """Brand module: native launch endpoints serve expected PNG dimensions and hashes."""
    manifest = Path("/app/backend/native_brand_manifest.json")
    assert manifest.exists(), "native_brand_manifest.json missing"
    expected = json.loads(manifest.read_text())["assets"][kind]["sha256"]

    response = api_client.get(f"{BASE_URL}/api/brand/launch/{kind}.png", timeout=30)
    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("image/png")
    assert hashlib.sha256(response.content).hexdigest() == expected
    assert _png_dimensions(response.content) == expected_size
