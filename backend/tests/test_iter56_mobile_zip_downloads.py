"""Iteration56: public mobile ZIP delivery, extracted media, standalone page and offline packaging."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

from dotenv import load_dotenv
import pytest
import requests

load_dotenv('/app/frontend/.env')
BASE = os.environ['EXPO_PUBLIC_BACKEND_URL'].rstrip('/')
ASSETS = json.loads(Path('/app/backend/marketing_manifest.json').read_text())['assets']
ZIP_SHA = '8672f7bb38fcc47146c58ea01b4dfc8cc2de168cf465b84b3543a80cd3ff8c84'
ZIP_SIZE = 13403359
ROUTES = ['/api/marketing/launch/launch-mobile-pack.zip', '/api/marketing/videos.zip']


@pytest.fixture(scope='module')
def zip_body():
    response = requests.get(BASE + ROUTES[0], timeout=120, allow_redirects=False)
    assert response.status_code == 200
    return response.content


# Public GET/HEAD/conditional/range contract; all real requests, no authentication.
@pytest.mark.parametrize('route', ROUTES)
def test_zip_delivery_contract(route, zip_body):
    response = requests.get(BASE + route, timeout=120, allow_redirects=False)
    assert response.status_code == 200 and not response.history
    assert response.content == zip_body
    assert len(response.content) == ZIP_SIZE
    assert hashlib.sha256(response.content).hexdigest() == ZIP_SHA
    assert response.headers['Content-Type'] == 'application/zip'
    assert response.headers['Content-Disposition'] == 'attachment; filename="JEELIVE-Mobile-Videos-45s.zip"'
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    assert response.headers['Accept-Ranges'] == 'bytes'
    etag = f'"{ZIP_SHA}"'
    assert response.headers['ETag'] == etag
    head = requests.head(BASE + route, timeout=30, allow_redirects=False)
    assert head.status_code == 200 and head.content == b''
    assert int(head.headers['Content-Length']) == ZIP_SIZE
    # The public edge may stream GET via chunked transfer and omit Content-Length.
    if 'Content-Length' in response.headers:
        assert int(response.headers['Content-Length']) == ZIP_SIZE
    for key in ['Content-Type', 'Content-Disposition', 'ETag', 'Accept-Ranges', 'X-Content-Type-Options']:
        assert head.headers[key] == response.headers[key]
    conditional = requests.get(BASE + route, headers={'If-None-Match': etag}, timeout=30, allow_redirects=False)
    assert conditional.status_code == 304 and conditional.content == b''
    for range_value, start, end in [('bytes=0-31', 0, 31), ('bytes=-64', ZIP_SIZE - 64, ZIP_SIZE - 1), (f'bytes={ZIP_SIZE-32}-', ZIP_SIZE-32, ZIP_SIZE-1)]:
        part = requests.get(BASE + route, headers={'Range': range_value}, timeout=30, allow_redirects=False)
        assert part.status_code == 206
        assert part.content == zip_body[start:end+1]
        assert part.headers['Content-Range'] == f'bytes {start}-{end}/{ZIP_SIZE}'
    invalid = requests.get(BASE + route, headers={'Range': f'bytes={ZIP_SIZE}-'}, timeout=30)
    assert invalid.status_code == 416 and invalid.headers['Content-Range'] == f'bytes */{ZIP_SIZE}'
    assert invalid.json()['detail'] == 'Requested range not satisfiable'


# Ordinary root-level, non-encrypted ZIP_STORED and exact verified member hashes.
def test_archive_integrity(zip_body):
    assert zip_body.startswith(b'PK\x03\x04')
    with zipfile.ZipFile(io.BytesIO(zip_body)) as archive:
        assert archive.testzip() is None
        assert archive.namelist() == ['JEELIVE-Mobile-Vertical-45s.mp4', 'JEELIVE-Mobile-Landscape-45s.mp4']
        for mode, info in zip(('vertical', 'landscape'), archive.infolist()):
            assert info.filename.isascii() and '/' not in info.filename and '\\' not in info.filename
            assert info.compress_type == zipfile.ZIP_STORED and not (info.flag_bits & 1)
            raw = archive.read(info)
            assert len(raw) == ASSETS[f'{mode}-mobile.mp4']['bytes']
            assert hashlib.sha256(raw).hexdigest() == ASSETS[f'{mode}-mobile.mp4']['sha256']
            assert raw[4:8] == b'ftyp'


# Decode downloaded/extracted members, not merely matching local source videos.
@pytest.mark.parametrize('mode,dimensions', [('vertical', (720, 1280)), ('landscape', (1280, 720))])
def test_extracted_mobile_media_full_decode(mode, dimensions, zip_body, tmp_path):
    path = tmp_path / f'{mode}.mp4'
    with zipfile.ZipFile(io.BytesIO(zip_body)) as archive:
        path.write_bytes(archive.read(ASSETS[f'{mode}-mobile.mp4']['filename']))
    info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)], timeout=30))
    video = next(s for s in info['streams'] if s['codec_type'] == 'video')
    audio = next(s for s in info['streams'] if s['codec_type'] == 'audio')
    assert (video['codec_name'], video['profile'], video['level'], video['pix_fmt'], video['nb_frames']) == ('h264', 'Constrained Baseline', 31, 'yuv420p', '1350')
    assert (video['width'], video['height']) == dimensions
    assert video['r_frame_rate'] == '30/1' and float(info['format']['duration']) == 45
    assert (audio['codec_name'], audio['profile'], audio['sample_rate'], audio['channels']) == ('aac', 'LC', '44100', 2)
    decoded = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'null', '-'], capture_output=True, timeout=90)
    assert decoded.returncode == 0 and decoded.stderr == b''


# Original nine records (including paths/hashes) must remain unchanged; exact ten allowlist.
def test_original_manifest_preservation():
    # Pin the pre-change snapshot: HEAD advances after a normal workspace save.
    original = json.loads(subprocess.check_output(['git', 'show', '9a22b91:backend/marketing_manifest.json'], cwd='/app'))['assets']
    assert len(original) == 9 and len(ASSETS) == 10
    assert {k: ASSETS[k] for k in original} == original
    assert set(ASSETS) - set(original) == {'launch-mobile-pack.zip'}
    assert ASSETS['launch-mobile-pack.zip']['sha256'] == ZIP_SHA
    spec = importlib.util.spec_from_file_location('iter56_media', '/app/backend/marketing_media.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.ALLOWED == set(ASSETS)


def test_readonly_and_unknown_assets():
    missing = requests.get(BASE + '/api/marketing/launch/TEST_unknown.mp4', timeout=30, allow_redirects=False)
    assert missing.status_code == 404 and missing.json()['detail'] == 'Campaign asset not found'
    for route in ROUTES + ['/api/marketing/downloads']:
        for method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            response = requests.request(method, BASE + route, timeout=30, allow_redirects=False)
            assert response.status_code == 405 and response.json()['detail'] == 'Method Not Allowed'


# Public document: native form/no Expo routing or login; edge may inject blocked Cloudflare scripts.
def test_standalone_html():
    response = requests.get(BASE + '/api/marketing/downloads', timeout=30, allow_redirects=False)
    assert response.status_code == 200 and response.headers['Content-Type'].startswith('text/html')
    assert 'no-store' in response.headers['Cache-Control']
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    assert "default-src 'none'" in response.headers['Content-Security-Policy']
    assert '<form action="/api/marketing/videos.zip" method="get">' in response.text
    assert 'data-testid="download-mobile-zip"' in response.text
    assert 'Extract / Unzip' in response.text and '13.4 MB' in response.text
    assert '__ZIP_SIZE__' not in response.text
    for forbidden in ['_expo', 'entry.bundle', 'expo-router', '/login', '/auth/']:
        assert forbidden not in response.text
    source = Path('/app/backend/launch_download.html').read_text()
    assert '<script' not in source


# Offline deterministic packaging and publisher early-return; guard forbids any cloud call.
def test_packaging_idempotence_and_master_preservation(tmp_path, monkeypatch, capsys):
    spec = importlib.util.spec_from_file_location('iter56_pack', '/app/marketing/launch45/download_pack.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    output = tmp_path / 'marketing' / 'launch45' / 'output'
    output.mkdir(parents=True)
    for key in ['vertical.mp4', 'landscape.mp4', 'vertical-mobile.mp4', 'landscape-mobile.mp4']:
        shutil.copyfile(Path('/app/marketing/launch45/output') / ASSETS[key]['filename'], output / ASSETS[key]['filename'])
    master = module.make_pack(output, ASSETS)
    master_bytes = master.read_bytes()
    assert hashlib.sha256(master_bytes).hexdigest() == 'aceeaa6329a41e32109521acb6f9da1118c81b0816b1c27ab33577dbec339822'
    mobile = module.make_pack(output, ASSETS, mobile=True)
    mobile_bytes = mobile.read_bytes()
    assert len(mobile_bytes) == ZIP_SIZE and hashlib.sha256(mobile_bytes).hexdigest() == ZIP_SHA
    assert module.make_pack(output, ASSETS, mobile=True).read_bytes() == mobile_bytes
    assert master.read_bytes() == master_bytes
    backend = tmp_path / 'backend'
    backend.mkdir()
    manifest_path = backend / 'marketing_manifest.json'
    manifest_path.write_text(json.dumps({'assets': ASSETS}))
    before = manifest_path.read_bytes()
    monkeypatch.setattr(module, 'ROOT', output.parent)
    monkeypatch.setattr(module, 'APP', tmp_path)
    def forbid_network(*args, **kwargs):
        pytest.fail('Idempotent publication attempted network IO')
    monkeypatch.setattr(module.httpx, 'Client', forbid_network)
    module.publish_pack(mobile=True)
    result = json.loads(capsys.readouterr().out)
    assert result == {'already_published': True, 'bytes': ZIP_SIZE, 'sha256': ZIP_SHA}
    assert manifest_path.read_bytes() == before and master.read_bytes() == master_bytes