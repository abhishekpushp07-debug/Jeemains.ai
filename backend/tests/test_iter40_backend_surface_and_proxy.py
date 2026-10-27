"""Iteration 40 backend surface checks: health, proxy guardrails, and RF catalog."""

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


def test_base_url_available():
    """Config module: ensure preview/public base URL is available."""
    assert BASE_URL, "EXPO_PUBLIC_BACKEND_URL is missing; cannot run public endpoint tests."


def test_health_ok(api_client: requests.Session):
    """Health module: basic service readiness endpoint."""
    response = api_client.get(f"{BASE_URL}/health", timeout=15)
    assert response.status_code == 200
    if "application/json" not in (response.headers.get("content-type") or ""):
        pytest.skip("Public ingress serves frontend on /health; backend health JSON is not externally routed.")
    data = response.json()
    assert data == {"status": "ok"}


def test_proxy_missing_sid_rejected(api_client: requests.Session):
    """Proxy module: X-JL-Sid is mandatory on /api/jl routes."""
    response = api_client.get(f"{BASE_URL}/api/jl/auth/session", timeout=20)
    assert response.status_code == 422
    data = response.json()
    assert isinstance(data.get("detail"), list)


def test_proxy_invalid_sid_rejected(api_client: requests.Session):
    """Proxy module: malformed X-JL-Sid is rejected with validation error."""
    response = api_client.get(
        f"{BASE_URL}/api/jl/auth/session",
        headers={"X-JL-Sid": "bad"},
        timeout=20,
    )
    assert response.status_code == 400
    assert response.json().get("detail") == "Invalid session handle."


def test_rf_catalog_shape(api_client: requests.Session):
    """Rapid Fire module: catalog is reachable and structurally valid."""
    response = api_client.get(f"{BASE_URL}/api/rf/catalog", timeout=20)
    assert response.status_code == 200
    data = response.json()
    assert data.get("exam") == "JEE"
    subjects = data.get("subjects")
    assert isinstance(subjects, list) and len(subjects) >= 1
    first = subjects[0]
    assert isinstance(first.get("name"), str)
    assert isinstance(first.get("chapters"), list)
