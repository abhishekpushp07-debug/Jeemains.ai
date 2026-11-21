"""Shared test setup.
0. State that every suite shares, kept apart across the two xdist workers with file locks:
   - Tonight's Cup Night is ONE document that several suites move around. Those tests take turns, and a test that writes
     that document straight into the database waits out the 1 s the server keeps it in memory, so the very next API
     call sees the change.
   - One suite switches a live card off for a while. The checks that count the whole card bank wait until that card is
     back on AND the catalogue (kept in memory for up to 2 minutes) shows the whole bank again.
   A request the preview ingress did not even take a connection for (nothing was sent) is asked again, twice at most.
1. The preview URL: older suites read EXPO_BACKEND_URL / EXPO_PUBLIC_BACKEND_URL from the shell; fill them from frontend/.env.
2. Older Rapid Fire suites sign in with the retired `X-RF-User: TEST-…` header. Rapid Fire now accepts only a short-lived
   grant (rf_access), so for TEST-* users only, that header is swapped for a real grant written straight into the preview
   database (the same way the newer suites do it). Grants made here are removed when the run ends."""
import asyncio
import contextlib
import fcntl
import hashlib
import os
import secrets
import shutil
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import requests
from dotenv import dotenv_values, load_dotenv
from motor.motor_asyncio import AsyncIOMotorCollection
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
    for last in (False, False, True):
        try:
            return _send(self, method, url, *args, headers=headers, **kw)
        except requests.exceptions.ConnectTimeout:  # no connection was made, so nothing reached the server: safe to ask again
            if last:
                raise


requests.Session.request = _request

# Video checks need ffmpeg/ffprobe (not installed in every pod). Cup Night checks move tonight's real night document, so
# they only make sense before tonight's 8 pm IST start; after it the server is already counting down to tomorrow.
NEEDS_FFMPEG = ("test_media_stream_contract_and_duration", "test_media_decodes_fully_without_ffmpeg_errors", "test_media_frame_count_is_1350",
                "test_audio_is_not_silent", "test_dark_cinematic_background_not_blank_static_black", "test_extracted_mobile_media_full_decode",
                "test_mobile_compatible_mp4_full_decode_and_faststart")
NEEDS_NIGHT_AHEAD = ("test_cup_night", "test_cup_night_split", "test_night_guard_create_and_join", "test_night_lead_in", "test_champions_wall",
                     "test_champions_doors_then_tonight")
MOVES_TONIGHT = (*NEEDS_NIGHT_AHEAD, "test_cup_night_reminder", "test_cup_night_seat_documents")  # one at a time, across both workers
NIGHT_KEPT = 1.2  # cups.night_doc keeps tonight's document for 1 s in every server process
RETIRES_A_CARD = ("test_rf_iter19_soft_retire",)  # modules that switch a live card off and on again
NEEDS_WHOLE_BANK = ("test_source_sync_not_resurrecting_deleted_jee_artifacts", "test_expanded_bank_is_whole_and_live")  # exact counts of the live bank


@contextlib.contextmanager
def one_at_a_time(name):
    """A lock both xdist workers (separate processes) share."""
    with open(os.path.join(tempfile.gettempdir(), f"jeelive_tests_{name}.lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def _wait_after_night_write(name):
    send = getattr(AsyncIOMotorCollection, name)

    async def write(self, *args, **kw):
        out = await send(self, *args, **kw)
        if self.name == "rf_cup_nights":
            await asyncio.sleep(NIGHT_KEPT)
        return out
    setattr(AsyncIOMotorCollection, name, write)


for _name in ("insert_one", "update_one", "replace_one", "delete_one"):
    _wait_after_night_write(_name)


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


@pytest.fixture(autouse=True)
def _shared_state_in_turns(request):
    name = request.node.name.split("[")[0]
    with contextlib.ExitStack() as held:
        if name in MOVES_TONIGHT:
            held.enter_context(one_at_a_time("cup_night"))
        if name in NEEDS_WHOLE_BANK:
            held.enter_context(one_at_a_time("card_bank"))
        yield


@pytest.fixture(scope="module", autouse=True)
def _card_bank_whole_again(request):
    if request.module.__name__ not in RETIRES_A_CARD:
        yield
        return
    with one_at_a_time("card_bank"):
        yield
        # The module's own fixtures are finished by now (its card is back on). The server still shows the catalogue it
        # read while the card was off, for up to 2 minutes: the bank lock is kept until both agree again.
        url = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/") + "/api/rf/catalog?exam=JEE"
        for _ in range(150):
            if sum(x["total"] for x in requests.get(url, timeout=30).json()["subjects"]) == _db.rf_cards.count_documents({"exam": "JEE", "retired": {"$ne": True}}):
                break
            time.sleep(1)


@pytest.fixture(scope="session", autouse=True)
def _drop_shim_grants():
    yield
    _db.rf_access.delete_many({"test_shim": _RUN})
