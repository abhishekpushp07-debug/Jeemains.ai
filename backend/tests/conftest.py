"""Shared test setup.
1. The preview URL: older suites read EXPO_BACKEND_URL / EXPO_PUBLIC_BACKEND_URL from the shell; fill them from frontend/.env.
2. Older Rapid Fire suites sign in with the retired `X-RF-User: TEST-…` header. Rapid Fire now accepts only a short-lived
   grant (rf_access), so for TEST-* users only, that header is swapped for a real grant written straight into the preview
   database (the same way the newer suites do it). Grants made here are removed when the run ends."""
import hashlib
import os
import secrets
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import requests
from dotenv import dotenv_values, load_dotenv
from pymongo import MongoClient

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / "backend" / ".env")
_front = dotenv_values(ROOT / "frontend" / ".env")
for name in ("EXPO_BACKEND_URL", "EXPO_PUBLIC_BACKEND_URL", "REACT_APP_BACKEND_URL"):
    os.environ.setdefault(name, _front.get("EXPO_PUBLIC_BACKEND_URL") or _front.get("EXPO_BACKEND_URL") or "")

_db = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
_tokens: dict = {}
_RUN = secrets.token_hex(6)  # one tag per test process (xdist workers end at different times)
_send = requests.Session.request


def _grant(uid: str) -> str:
    if uid not in _tokens:
        token = secrets.token_urlsafe(32)
        _db.rf_access.insert_one({"digest": hashlib.sha256(token.encode()).hexdigest(), "uid": uid, "sid": "", "test_shim": _RUN,
                                  "expires_at": datetime.now(timezone.utc) + timedelta(hours=2)})
        _tokens[uid] = token
    return _tokens[uid]


def _request(self, method, url, *args, headers=None, **kw):
    if headers:
        key = next((k for k in headers if k.lower() == "x-rf-user"), None)
        uid = headers.get(key) if key else None
        if isinstance(uid, str) and uid.startswith("TEST") and not any(k.lower() == "authorization" for k in headers):
            headers = {k: v for k, v in headers.items() if k != key}
            headers["Authorization"] = f"Bearer {_grant(uid)}"
    return _send(self, method, url, *args, headers=headers, **kw)


requests.Session.request = _request

# Video checks need ffmpeg/ffprobe (not installed in every pod). Cup Night checks move tonight's real night document, so
# they only make sense before tonight's 8 pm IST start; after it the server is already counting down to tomorrow.
NEEDS_FFMPEG = ("test_media_stream_contract_and_duration", "test_media_decodes_fully_without_ffmpeg_errors", "test_media_frame_count_is_1350",
                "test_audio_is_not_silent", "test_dark_cinematic_background_not_blank_static_black", "test_extracted_mobile_media_full_decode",
                "test_mobile_compatible_mp4_full_decode_and_faststart")
NEEDS_NIGHT_AHEAD = ("test_cup_night", "test_cup_night_split", "test_night_guard_create_and_join", "test_night_lead_in", "test_champions_wall",
                     "test_champions_doors_then_tonight")


def pytest_collection_modifyitems(config, items):
    no_ffmpeg = not (shutil.which("ffmpeg") and shutil.which("ffprobe"))
    hour, minute = (int(x) for x in os.environ.get("RF_CUP_NIGHT_AT", "20:00").split(":"))
    ist = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    night_started = (ist.hour, ist.minute) >= (hour, minute)
    for item in items:
        name = item.name.split("[")[0]
        if no_ffmpeg and name in NEEDS_FFMPEG:
            item.add_marker(pytest.mark.skip(reason="ffmpeg/ffprobe not installed in this pod"))
        if night_started and name in NEEDS_NIGHT_AHEAD:
            item.add_marker(pytest.mark.skip(reason="tonight's Cup Night has already started (IST); run before 8 pm IST"))


@pytest.fixture(scope="session", autouse=True)
def _drop_shim_grants():
    yield
    _db.rf_access.delete_many({"test_shim": _RUN})
