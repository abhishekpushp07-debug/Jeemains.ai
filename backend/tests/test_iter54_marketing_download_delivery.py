"""Iteration 54: download-delivery contract for launch media ZIP and MP4 attachments."""

import hashlib
import io
import json
import os
import re
import zipfile
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv


load_dotenv("/app/frontend/.env")
BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "").rstrip("/")
MANIFEST_PATH = Path("/app/backend/marketing_manifest.json")

EXPECTED_ZIP_SHA = "aceeaa6329a41e32109521acb6f9da1118c81b0816b1c27ab33577dbec339822"
EXPECTED_VERTICAL_SHA = "c31dbcd1b216662be59c39c1ce8c528b2ae0d15e2db8a4410ea4ced44c172e98"
EXPECTED_LANDSCAPE_SHA = "0d74c017eefd9e92c0f3557abad908d4c9496f937034e272761ac26c6c4a6d21"


def _asset_url(name: str) -> str:
    return f"{BASE_URL}/api/marketing/launch/{name}"


def _require_base_url():
    if not BASE_URL:
        pytest.skip("EXPO_PUBLIC_BACKEND_URL is not configured")


@pytest.fixture(scope="session")
def api_client() -> requests.Session:
    session = requests.Session()
    session.headers.update({"Accept": "*/*"})
    return session


@pytest.fixture(scope="session")
def manifest_assets() -> dict:
    data = json.loads(MANIFEST_PATH.read_text())
    return data["assets"]


@pytest.fixture(scope="session")
def launch_zip_bytes(api_client: requests.Session) -> bytes:
    _require_base_url()
    response = api_client.get(_asset_url("launch-pack.zip"), timeout=180)
    assert response.status_code == 200
    return response.content


# Allowlist and manifest structure
def test_manifest_has_expected_7_public_assets(manifest_assets: dict):
    expected = {
        "vertical.mp4",
        "landscape.mp4",
        "vertical.webm",
        "landscape.webm",
        "poster-vertical.jpg",
        "poster-landscape.jpg",
        "launch-pack.zip",
    }
    assert set(manifest_assets.keys()) == expected


def test_zip_manifest_path_is_uuid_object(manifest_assets: dict):
    path = manifest_assets["launch-pack.zip"]["path"]
    assert re.fullmatch(r"jeelive-ai/uploads/marketing/[0-9a-f\-]{36}\.zip", path)


# Download disposition and MIME contract
@pytest.mark.parametrize("name", ["vertical.mp4", "landscape.mp4"])
def test_mp4_default_is_inline_video_mime(api_client: requests.Session, manifest_assets: dict, name: str):
    _require_base_url()
    response = api_client.get(_asset_url(name), timeout=120)
    assert response.status_code == 200
    assert response.headers.get("Content-Type", "").startswith("video/mp4")
    assert response.headers.get("Content-Disposition", "").startswith("inline;")
    assert manifest_assets[name]["filename"] in response.headers.get("Content-Disposition", "")


@pytest.mark.parametrize("name", ["vertical.mp4", "landscape.mp4"])
def test_mp4_download_query_forces_attachment_octet_stream(api_client: requests.Session, manifest_assets: dict, name: str):
    _require_base_url()
    response = api_client.get(_asset_url(name) + "?download=1", timeout=120)
    assert response.status_code == 200
    assert response.headers.get("Content-Type", "").startswith("application/octet-stream")
    assert response.headers.get("Content-Disposition", "").startswith("attachment;")
    assert manifest_assets[name]["filename"] in response.headers.get("Content-Disposition", "")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"


def test_zip_is_always_attachment_without_query(api_client: requests.Session, manifest_assets: dict):
    _require_base_url()
    response = api_client.get(_asset_url("launch-pack.zip"), timeout=180)
    assert response.status_code == 200
    assert response.headers.get("Content-Type", "").startswith("application/zip")
    assert response.headers.get("Content-Disposition", "").startswith("attachment;")
    assert manifest_assets["launch-pack.zip"]["filename"] in response.headers.get("Content-Disposition", "")


# ZIP integrity: CRC + extraction + exact members + SHA checks
def test_zip_body_sha_and_size_match_manifest_and_expected(launch_zip_bytes: bytes, manifest_assets: dict):
    record = manifest_assets["launch-pack.zip"]
    assert len(launch_zip_bytes) == record["bytes"] == 15097795
    assert hashlib.sha256(launch_zip_bytes).hexdigest() == record["sha256"] == EXPECTED_ZIP_SHA


def test_zip_contains_exact_two_safe_ascii_entries_crc_ok(launch_zip_bytes: bytes):
    expected_names = [
        "JEELIVE-launch-45s-vertical.mp4",
        "JEELIVE-launch-45s-landscape.mp4",
    ]
    with zipfile.ZipFile(io.BytesIO(launch_zip_bytes)) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert names == expected_names
        for name in names:
            assert name.isascii()
            assert ".." not in name
            assert "/" not in name and "\\\\" not in name


def test_zip_extracted_mp4_hashes_match_expected(launch_zip_bytes: bytes):
    with zipfile.ZipFile(io.BytesIO(launch_zip_bytes)) as archive:
        vertical = archive.read("JEELIVE-launch-45s-vertical.mp4")
        landscape = archive.read("JEELIVE-launch-45s-landscape.mp4")
    assert hashlib.sha256(vertical).hexdigest() == EXPECTED_VERTICAL_SHA
    assert hashlib.sha256(landscape).hexdigest() == EXPECTED_LANDSCAPE_SHA


# Range / conditional behavior retained
def test_zip_head_and_range_still_supported(api_client: requests.Session, manifest_assets: dict):
    _require_base_url()
    head = api_client.head(_asset_url("launch-pack.zip"), timeout=60)
    assert head.status_code == 200
    assert int(head.headers.get("Content-Length", "0")) == manifest_assets["launch-pack.zip"]["bytes"]
    assert head.headers.get("Accept-Ranges") == "bytes"

    part = api_client.get(_asset_url("launch-pack.zip"), headers={"Range": "bytes=0-31"}, timeout=60)
    size = manifest_assets["launch-pack.zip"]["bytes"]
    assert part.status_code == 206
    assert len(part.content) == 32
    assert part.headers.get("Content-Range") == f"bytes 0-31/{size}"


def test_zip_etag_if_none_match_returns_304(api_client: requests.Session, manifest_assets: dict):
    _require_base_url()
    etag = f'"{manifest_assets["launch-pack.zip"]["sha256"]}"'
    response = api_client.get(_asset_url("launch-pack.zip"), headers={"If-None-Match": etag}, timeout=60)
    assert response.status_code == 304


# Safety checks
def test_unknown_asset_404_and_write_method_405(api_client: requests.Session):
    _require_base_url()
    missing = api_client.get(_asset_url("unknown-private.mov"), timeout=60)
    assert missing.status_code == 404
    post = api_client.post(_asset_url("launch-pack.zip"), timeout=60)
    assert post.status_code == 405
