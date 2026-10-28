"""Iteration 53: public launch media delivery, range semantics, and media integrity checks."""

import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from statistics import mean

import pytest
import requests
from dotenv import load_dotenv
from PIL import Image


load_dotenv("/app/frontend/.env")
BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "").rstrip("/")
MANIFEST_PATH = Path("/app/backend/marketing_manifest.json")


def _require_base_url():
    if not BASE_URL:
        pytest.skip("EXPO_PUBLIC_BACKEND_URL is not configured")


def _ffprobe(path: Path, *, count_frames: bool = False) -> dict:
    cmd = ["ffprobe", "-v", "error"]
    if count_frames:
        cmd.append("-count_frames")
    cmd.extend(["-show_streams", "-show_format", "-of", "json", str(path)])
    out = subprocess.check_output(cmd, text=True)
    return json.loads(out)


def _download(url: str, target: Path) -> bytes:
    response = requests.get(url, timeout=180)
    assert response.status_code == 200, f"Failed download {url}: {response.status_code}"
    target.write_bytes(response.content)
    return response.content


def _top_level_atoms(path: Path) -> list[tuple[str, int]]:
    atoms = []
    with path.open("rb") as handle:
        size = path.stat().st_size
        pos = 0
        while pos + 8 <= size:
            handle.seek(pos)
            raw = handle.read(8)
            if len(raw) < 8:
                break
            atom_size = int.from_bytes(raw[:4], "big")
            atom_name = raw[4:8].decode("latin1")
            if atom_size == 0:
                atom_size = size - pos
            if atom_size < 8:
                break
            atoms.append((atom_name, pos))
            pos += atom_size
    return atoms


@pytest.fixture(scope="session")
def manifest() -> dict:
    data = json.loads(MANIFEST_PATH.read_text())
    assert "assets" in data
    return data["assets"]


@pytest.fixture(scope="session")
def api_client() -> requests.Session:
    session = requests.Session()
    session.headers.update({"Accept": "*/*"})
    return session


@pytest.fixture(scope="session")
def media_workspace(manifest: dict) -> dict:
    _require_base_url()
    tmp = Path(tempfile.mkdtemp(prefix="iter53_media_"))
    files = {}
    for name in ["vertical.mp4", "landscape.mp4", "vertical.webm", "landscape.webm", "poster-vertical.jpg", "poster-landscape.jpg"]:
        files[name] = tmp / name
        _download(f"{BASE_URL}/api/marketing/launch/{name}", files[name])
    return files


def _asset_url(name: str) -> str:
    return f"{BASE_URL}/api/marketing/launch/{name}"


# Public endpoint read-only smoke
def test_public_asset_smoke_head(api_client: requests.Session):
    _require_base_url()
    response = api_client.head(_asset_url("vertical.mp4"), timeout=30)
    assert response.status_code == 200


# Manifest and allowlist integrity
def test_manifest_exposes_exact_public_allowlist(manifest: dict):
    expected = {"vertical.mp4", "landscape.mp4", "vertical.webm", "landscape.webm", "poster-vertical.jpg", "poster-landscape.jpg"}
    assert set(manifest.keys()) == expected


@pytest.mark.parametrize("name", ["vertical.mp4", "landscape.mp4", "vertical.webm", "landscape.webm", "poster-vertical.jpg", "poster-landscape.jpg"])
def test_head_returns_metadata_for_each_public_asset(api_client: requests.Session, manifest: dict, name: str):
    _require_base_url()
    response = api_client.head(_asset_url(name), timeout=60)
    record = manifest[name]
    assert response.status_code == 200
    assert response.headers.get("Content-Type", "").startswith(record["content_type"])
    assert int(response.headers.get("Content-Length", "0")) == record["bytes"]
    assert response.headers.get("Accept-Ranges") == "bytes"
    assert response.headers.get("ETag") == f'"{record["sha256"]}"'
    assert f'filename="{record["filename"]}"' in response.headers.get("Content-Disposition", "")


def test_head_body_is_empty(api_client: requests.Session):
    _require_base_url()
    response = api_client.head(_asset_url("vertical.mp4"), timeout=60)
    assert response.status_code == 200
    assert response.content == b""


def test_head_ignores_range_per_rfc(api_client: requests.Session, manifest: dict):
    _require_base_url()
    response = api_client.head(_asset_url("vertical.mp4"), headers={"Range": "bytes=0-9"}, timeout=60)
    assert response.status_code == 200
    assert response.headers.get("Content-Range") is None
    assert int(response.headers.get("Content-Length", "0")) == manifest["vertical.mp4"]["bytes"]


@pytest.mark.parametrize("name", ["vertical.mp4", "landscape.mp4", "vertical.webm", "landscape.webm", "poster-vertical.jpg", "poster-landscape.jpg"])
def test_get_full_asset_matches_manifest_sha_and_length(api_client: requests.Session, manifest: dict, name: str):
    _require_base_url()
    response = api_client.get(_asset_url(name), timeout=180)
    digest = hashlib.sha256(response.content).hexdigest()
    record = manifest[name]
    assert response.status_code == 200
    assert response.headers.get("Content-Type", "").startswith(record["content_type"])
    assert len(response.content) == record["bytes"]
    assert digest == record["sha256"]


@pytest.mark.parametrize("name", ["vertical.mp4", "landscape.mp4", "vertical.webm", "landscape.webm", "poster-vertical.jpg", "poster-landscape.jpg"])
def test_download_query_forces_attachment_disposition(api_client: requests.Session, manifest: dict, name: str):
    _require_base_url()
    response = api_client.get(_asset_url(name) + "?download=1", timeout=180)
    assert response.status_code == 200
    assert response.headers.get("Content-Disposition", "").startswith("attachment;")
    assert manifest[name]["filename"] in response.headers.get("Content-Disposition", "")


@pytest.mark.parametrize("name", ["source-rapid-stage.jpg", "source-series-stage.jpg", "private.mp4", "does-not-exist.mp4", "..%2F..%2Fetc%2Fpasswd"])
def test_unknown_private_or_traversal_names_are_404(api_client: requests.Session, name: str):
    _require_base_url()
    response = api_client.get(_asset_url(name), timeout=60)
    assert response.status_code == 404


def test_post_not_allowed_on_public_media(api_client: requests.Session):
    _require_base_url()
    response = api_client.post(_asset_url("vertical.mp4"), timeout=60)
    assert response.status_code == 405


# Explicit Range contract checks for Starlette 0.37.2 compatibility
def test_closed_range_returns_exact_bytes_and_content_range(api_client: requests.Session, manifest: dict):
    _require_base_url()
    response = api_client.get(_asset_url("vertical.mp4"), headers={"Range": "bytes=0-99"}, timeout=60)
    size = manifest["vertical.mp4"]["bytes"]
    assert response.status_code == 206
    assert len(response.content) == 100
    assert response.headers.get("Content-Range") == f"bytes 0-99/{size}"


def test_open_range_returns_from_start_to_end(api_client: requests.Session, manifest: dict):
    _require_base_url()
    start = 100
    response = api_client.get(_asset_url("vertical.mp4"), headers={"Range": f"bytes={start}-"}, timeout=60)
    size = manifest["vertical.mp4"]["bytes"]
    assert response.status_code == 206
    assert len(response.content) == size - start
    assert response.headers.get("Content-Range") == f"bytes {start}-{size - 1}/{size}"


def test_suffix_range_returns_tail_bytes(api_client: requests.Session, manifest: dict):
    _require_base_url()
    suffix = 128
    response = api_client.get(_asset_url("vertical.mp4"), headers={"Range": f"bytes=-{suffix}"}, timeout=60)
    size = manifest["vertical.mp4"]["bytes"]
    start = size - suffix
    assert response.status_code == 206
    assert len(response.content) == suffix
    assert response.headers.get("Content-Range") == f"bytes {start}-{size - 1}/{size}"


def test_oversized_end_is_clamped(api_client: requests.Session, manifest: dict):
    _require_base_url()
    start = 1024
    response = api_client.get(_asset_url("vertical.mp4"), headers={"Range": f"bytes={start}-999999999"}, timeout=60)
    size = manifest["vertical.mp4"]["bytes"]
    assert response.status_code == 206
    assert len(response.content) == size - start
    assert response.headers.get("Content-Range") == f"bytes {start}-{size - 1}/{size}"


@pytest.mark.parametrize(
    "range_value",
    [
        "bytes=abc-def",
        "bytes=10-1",
        "bytes=-0",
        "bytes=99999999-",
        "bytes=0-10,20-30",
        "items=0-10",
        "bytes=-",
        "bytes=",
        "bytes=0-5" + "0" * 130,
    ],
)
def test_invalid_or_multirange_requests_return_416(api_client: requests.Session, manifest: dict, range_value: str):
    _require_base_url()
    response = api_client.get(_asset_url("vertical.mp4"), headers={"Range": range_value}, timeout=60)
    size = manifest["vertical.mp4"]["bytes"]
    assert response.status_code == 416
    assert response.headers.get("Accept-Ranges") == "bytes"
    assert response.headers.get("Content-Range") == f"bytes */{size}"


def test_if_range_match_allows_206(api_client: requests.Session, manifest: dict):
    _require_base_url()
    etag = f'"{manifest["vertical.mp4"]["sha256"]}"'
    response = api_client.get(
        _asset_url("vertical.mp4"),
        headers={"Range": "bytes=0-63", "If-Range": etag},
        timeout=60,
    )
    assert response.status_code == 206
    assert len(response.content) == 64


def test_if_range_mismatch_falls_back_to_200(api_client: requests.Session, manifest: dict):
    _require_base_url()
    response = api_client.get(
        _asset_url("vertical.mp4"),
        headers={"Range": "bytes=0-63", "If-Range": '"mismatch-etag"'},
        timeout=120,
    )
    assert response.status_code == 200
    assert len(response.content) == manifest["vertical.mp4"]["bytes"]


def test_matching_if_none_match_returns_304(api_client: requests.Session, manifest: dict):
    _require_base_url()
    etag = f'"{manifest["vertical.mp4"]["sha256"]}"'
    response = api_client.get(_asset_url("vertical.mp4"), headers={"If-None-Match": etag}, timeout=60)
    assert response.status_code == 304
    assert response.content == b""


def test_mismatched_if_none_match_returns_200(api_client: requests.Session):
    _require_base_url()
    response = api_client.get(_asset_url("vertical.mp4"), headers={"If-None-Match": '"wrong"'}, timeout=120)
    assert response.status_code == 200
    assert len(response.content) > 0


# FFmpeg/ffprobe decode and format validation
@pytest.mark.parametrize(
    "name, expected_codec_video, expected_codec_audio, expected_wh",
    [
        ("vertical.mp4", "h264", "aac", (1080, 1920)),
        ("landscape.mp4", "h264", "aac", (1920, 1080)),
        ("vertical.webm", "vp9", "opus", (1080, 1920)),
        ("landscape.webm", "vp9", "opus", (1920, 1080)),
    ],
)
def test_media_stream_contract_and_duration(media_workspace: dict, name: str, expected_codec_video: str, expected_codec_audio: str, expected_wh: tuple[int, int]):
    path = media_workspace[name]
    info = _ffprobe(path)
    streams = info["streams"]
    video = next(row for row in streams if row["codec_type"] == "video")
    audio = next(row for row in streams if row["codec_type"] == "audio")
    duration = float(info["format"].get("duration", 0))
    tol = 0.01 if name.endswith(".mp4") else 0.1
    assert abs(duration - 45.0) <= tol
    assert (video["width"], video["height"]) == expected_wh
    assert video["codec_name"] == expected_codec_video
    assert audio["codec_name"] == expected_codec_audio
    assert video.get("r_frame_rate") == "30/1"
    assert int(audio.get("sample_rate", "0")) == 48000
    assert int(audio.get("channels", 0)) == 2


@pytest.mark.parametrize("name", ["vertical.mp4", "landscape.mp4", "vertical.webm", "landscape.webm"])
def test_media_decodes_fully_without_ffmpeg_errors(media_workspace: dict, name: str):
    path = media_workspace[name]
    result = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"], capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stderr.strip() == ""


@pytest.mark.parametrize("name", ["vertical.mp4", "landscape.mp4", "vertical.webm", "landscape.webm"])
def test_media_frame_count_is_1350(media_workspace: dict, name: str):
    path = media_workspace[name]
    info = _ffprobe(path, count_frames=True)
    video = next(row for row in info["streams"] if row["codec_type"] == "video")
    frames = int(video.get("nb_read_frames") or video.get("nb_frames") or 0)
    assert frames == 1350


@pytest.mark.parametrize("name", ["vertical.mp4", "landscape.mp4", "vertical.webm", "landscape.webm"])
def test_audio_is_not_silent(media_workspace: dict, name: str):
    path = media_workspace[name]
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    payload = result.stderr
    max_match = re.search(r"max_volume:\s*([-0-9.inf]+) dB", payload)
    mean_match = re.search(r"mean_volume:\s*([-0-9.inf]+) dB", payload)
    assert max_match is not None
    assert mean_match is not None
    assert max_match.group(1) != "-inf"
    assert mean_match.group(1) != "-inf"


@pytest.mark.parametrize("name", ["vertical.mp4", "landscape.mp4", "vertical.webm", "landscape.webm"])
def test_dark_cinematic_background_not_blank_static_black(media_workspace: dict, name: str):
    path = media_workspace[name]
    sample_times = [1.0, 11.9, 22.5, 31.5, 43.5]
    frame_hashes = []
    frame_means = []
    with tempfile.TemporaryDirectory(prefix="iter53_frames_") as td:
        frame_dir = Path(td)
        for i, at in enumerate(sample_times):
            frame_path = frame_dir / f"f{i}.png"
            result = subprocess.run(
                ["ffmpeg", "-hide_banner", "-ss", str(at), "-i", str(path), "-frames:v", "1", str(frame_path), "-y"],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
            data = frame_path.read_bytes()
            frame_hashes.append(hashlib.sha256(data).hexdigest())
            with Image.open(frame_path) as img:
                gray = img.convert("L")
                pixels = list(gray.getdata())
                frame_means.append(mean(pixels))
    assert len(set(frame_hashes)) > 1
    assert max(frame_means) > 5


def test_mp4_faststart_moov_precedes_mdat(media_workspace: dict):
    for name in ["vertical.mp4", "landscape.mp4"]:
        atoms = _top_level_atoms(media_workspace[name])
        names = [atom for atom, _ in atoms]
        assert "moov" in names
        assert "mdat" in names
        assert names.index("moov") < names.index("mdat")


# Poster dimension checks
def test_posters_have_expected_dimensions(media_workspace: dict):
    with Image.open(media_workspace["poster-vertical.jpg"]) as img_v:
        assert img_v.size == (1080, 1920)
    with Image.open(media_workspace["poster-landscape.jpg"]) as img_l:
        assert img_l.size == (1920, 1080)
