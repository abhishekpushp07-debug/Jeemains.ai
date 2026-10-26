"""Iteration 36: verify public brand assets match bundled/source originals exactly."""

import hashlib
import os
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv


load_dotenv("/app/frontend/.env")

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "").rstrip("/")


def _must_have_env():
    if not BASE_URL:
        pytest.skip("EXPO_PUBLIC_BACKEND_URL missing; cannot validate brand endpoints")


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


# Home artwork parity: API-managed public images must be byte-identical to bundled offline fallback.
@pytest.mark.parametrize(
    "kind,local_file",
    [
        ("jee", "/app/frontend/assets/images/tile-jee.jpg"),
        ("live", "/app/frontend/assets/images/tile-live.jpg"),
        ("bitsat", "/app/frontend/assets/images/tile-bitsat.jpg"),
        ("comedk", "/app/frontend/assets/images/tile-comedk.jpg"),
    ],
)
def test_iter36_brand_card_matches_bundled_artwork(kind: str, local_file: str):
    _must_have_env()
    local_path = Path(local_file)
    assert local_path.exists(), f"Missing bundled fallback: {local_file}"

    local_bytes = local_path.read_bytes()
    response = requests.get(f"{BASE_URL}/api/brand/cards/{kind}.jpg", timeout=30)

    assert response.status_code == 200, f"{kind} card HTTP {response.status_code}"
    assert response.headers.get("content-type", "").startswith("image/jpeg")
    assert _sha256(response.content) == _sha256(local_bytes)
    assert response.content == local_bytes


# Logo parity: API logo should remain byte-identical to owner-supplied vector file.
def test_iter36_brand_logo_matches_owner_source_svg():
    _must_have_env()
    owner_logo = Path("/app/reference/integration-2026-10-26/assets/brand/jeelive-vector.svg")
    assert owner_logo.exists(), "Missing owner source logo SVG"

    source_bytes = owner_logo.read_bytes()
    response = requests.get(f"{BASE_URL}/api/brand/logo.svg", timeout=30)

    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("image/svg")
    assert _sha256(response.content) == _sha256(source_bytes)
    assert response.content == source_bytes
