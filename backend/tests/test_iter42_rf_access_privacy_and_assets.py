"""Iteration 42: Rapid Fire access/privacy/authz + portrait asset/cleanup integrity.

Modules covered:
- canonical login to SID exchange and /api/rf/access
- RF grant validation (missing/fake/expired)
- owner scoping + spoofed X-RF-User ignored
- websocket first-frame token auth
- public RF/brand/cleanup integrity contracts
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import requests
import websockets
from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv("/app/frontend/.env")
load_dotenv("/app/backend/.env")

BASE_URL = (os.environ.get("EXPO_PUBLIC_BACKEND_URL") or "").rstrip("/")
PHONE = os.environ.get("JEELIVE_TEST_PHONE") or ""
PIN = os.environ.get("JEELIVE_TEST_PIN") or ""
MONGO_URL = (os.environ.get("MONGO_URL") or "").strip().strip('"')
DB_NAME = (os.environ.get("DB_NAME") or "").strip().strip('"')


def _require_env() -> None:
    if not BASE_URL:
        pytest.skip("Missing EXPO_PUBLIC_BACKEND_URL")
    if not PHONE or not PIN:
        pytest.skip("Missing canonical test phone/pin in backend env")
    if not MONGO_URL or not DB_NAME:
        pytest.skip("Missing MONGO_URL/DB_NAME for scoped test cleanup")


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _request_with_retry(method: str, url: str, **kwargs) -> requests.Response:
    tries = 0
    while True:
        tries += 1
        try:
            res = requests.request(method, url, **kwargs)
            if res.status_code not in (502, 503, 520, 522, 524) or tries >= 3:
                return res
        except requests.RequestException:
            if tries >= 3:
                raise
        time.sleep(1.0)


@pytest.fixture(scope="module")
def mongo():
    _require_env()
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    try:
        yield db
    finally:
        client.close()


@pytest.fixture(scope="module")
def scoped_ids():
    run = uuid.uuid4().hex[:8]
    return {
        "sid": f"TESTSID-ITER42-{run}",
        "uid_a": f"TEST-RF-portrait-A-{run}",
        "uid_b": f"TEST-RF-portrait-B-{run}",
        "uid_shop_a": f"TEST-RF-portrait-shopA-{run}",
        "uid_shop_b": f"TEST-RF-portrait-shopB-{run}",
    }


@pytest.fixture(scope="module", autouse=True)
def cleanup(mongo, scoped_ids):
    yield
    owned = {"$in": [value for key, value in scoped_ids.items() if key.startswith('uid_')]}
    mongo.rf_access.delete_many({"uid": owned})
    mongo.rf_sessions.delete_many({"user_id": owned})
    mongo.rf_duels.delete_many({"players.uid": owned})
    mongo.rf_profiles.delete_many({"uid": owned})
    mongo.rf_awards.delete_many({"uid": owned})
    mongo.rf_learning_events.delete_many({"uid": owned})
    mongo.jl_jars.delete_many({"sid": scoped_ids["sid"]})


def _grant_for_uid(mongo, uid: str, minutes: int = 10) -> str:
    token = "t-" + uuid.uuid4().hex + uuid.uuid4().hex
    exp = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    mongo.rf_access.insert_one({"digest": _digest(token), "uid": uid, "sid": "", "expires_at": exp})
    return token


def test_canonical_pin_login_and_rf_access_sid_exchange(scoped_ids):
    """Auth module: canonical PIN login (read-only) + /api/rf/access grant via authenticated SID."""
    _require_env()
    sid = scoped_ids["sid"]
    with requests.Session() as _:
        login = _request_with_retry(
            "POST",
            f"{BASE_URL}/api/jl/auth/phone",
            json={"phone": PHONE, "pin": PIN},
            headers={"X-JL-Sid": sid},
            timeout=30,
        )
        assert login.status_code == 200

        grant = _request_with_retry("POST", f"{BASE_URL}/api/rf/access", json={}, headers={"X-JL-Sid": sid}, timeout=20)
        assert grant.status_code == 200
        body = grant.json()
        assert isinstance(body.get("token"), str) and len(body["token"]) >= 20
        assert isinstance(body.get("user_id"), str) and len(body["user_id"]) >= 8
        assert isinstance(body.get("expires_at"), str) and body["expires_at"].endswith("+00:00")


def test_rf_access_denies_fake_sid_and_private_without_grant(scoped_ids):
    """Access guard module: fake SID denied, missing grant denied on private endpoint."""
    fake = requests.post(
        f"{BASE_URL}/api/rf/access",
        json={},
        headers={"X-JL-Sid": f"{scoped_ids['sid']}-FAKE"},
        timeout=20,
    )
    assert fake.status_code == 401

    no_grant = requests.get(f"{BASE_URL}/api/rf/profile", timeout=20)
    assert no_grant.status_code == 401


def test_expired_grant_rejected(mongo):
    """Access guard module: expired grant is denied."""
    uid = "TEST-RF-portrait-expired-" + uuid.uuid4().hex[:8]
    token = "expired-" + uuid.uuid4().hex
    mongo.rf_access.insert_one(
        {
            "digest": _digest(token),
            "uid": uid,
            "sid": "",
            "expires_at": datetime.now(timezone.utc) - timedelta(minutes=1),
        }
    )
    try:
        res = requests.get(
            f"{BASE_URL}/api/rf/profile",
            headers={"Authorization": f"Bearer {token}"},
            timeout=20,
        )
        assert res.status_code == 401
    finally:
        mongo.rf_access.delete_many({"uid": uid})


def test_owner_scope_enforced_and_spoofed_header_ignored(mongo, scoped_ids):
    """Session module: token owner scope enforced; forged X-RF-User header ignored."""
    a_token = _grant_for_uid(mongo, scoped_ids["uid_a"])
    b_token = _grant_for_uid(mongo, scoped_ids["uid_b"])

    create = requests.post(
        f"{BASE_URL}/api/rf/sessions",
        json={
            "subject": "Physics",
            "chapter": None,
            "count": 30,
            "request_id": "iter42-" + uuid.uuid4().hex,
            "exam": "JEE",
            "revision": False,
        },
        headers={
            "Authorization": f"Bearer {a_token}",
            "X-RF-User": scoped_ids["uid_b"],  # must be ignored/replaced by guard
        },
        timeout=30,
    )
    assert create.status_code == 200
    sid = create.json()["id"]

    owner_get = requests.get(
        f"{BASE_URL}/api/rf/sessions/{sid}",
        headers={
            "Authorization": f"Bearer {a_token}",
            "X-RF-User": "forged-user-should-be-ignored",
        },
        timeout=20,
    )
    assert owner_get.status_code == 200
    owner_payload = owner_get.json()
    assert owner_payload.get("id") == sid
    assert len(owner_payload.get("cards") or []) == 30

    other_get = requests.get(
        f"{BASE_URL}/api/rf/sessions/{sid}",
        headers={"Authorization": f"Bearer {b_token}"},
        timeout=20,
    )
    assert other_get.status_code == 404


def test_duel_websocket_requires_first_frame_token(mongo, scoped_ids):
    """WebSocket module: no UID-only access; first frame token auth is required."""
    token = _grant_for_uid(mongo, scoped_ids["uid_a"])
    create = requests.post(
        f"{BASE_URL}/api/rf/duels",
        json={
            "subject": "Physics",
            "chapter": None,
            "mode": "invite",
            "name": "TEST-RF-portrait-A",
            "request_id": "iter42-duel-" + uuid.uuid4().hex,
            "exam": "JEE",
        },
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    assert create.status_code == 200
    did = create.json()["id"]

    ws_base = BASE_URL.replace("https://", "wss://").replace("http://", "ws://")
    ws_url = f"{ws_base}/api/rf/duels/{did}/ws?u={scoped_ids['uid_b']}"

    async def _run_checks():
        # Invalid token should be rejected quickly.
        bad_closed = False
        try:
            async with websockets.connect(ws_url, open_timeout=8) as ws:
                await ws.send(json.dumps({"token": "invalid-token"}))
                await ws.recv()
        except Exception:
            bad_closed = True
        assert bad_closed

        # Valid token should receive state frame.
        async with websockets.connect(ws_url, open_timeout=8) as ws:
            await ws.send(json.dumps({"token": token}))
            frame = await ws.recv()
            payload = json.loads(frame)
            assert payload.get("id") == did
            assert payload.get("status") in {"waiting", "ready", "finished", "expired", "cancelled"}

    asyncio.run(_run_checks())


def test_public_cards_omit_answer_formula_explain():
    """Public cards module: answer-side fields must not be exposed."""
    res = requests.get(f"{BASE_URL}/api/rf/cards?exam=JEE&subject=Physics&page=1&limit=5", timeout=20)
    assert res.status_code == 200
    items = res.json().get("items") or []
    assert len(items) > 0
    for row in items:
        assert "answer" not in row
        assert "explain" not in row
        assert "formula" not in row


def test_brand_rapid_assets_exist_and_combined_size_near_31kb():
    """Branding module: all four rapid artworks are reachable and lightweight."""
    total = 0
    for kind in ("spark", "friends", "coins", "trophy"):
        r = requests.get(f"{BASE_URL}/api/brand/rapid/{kind}.webp", timeout=20)
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("image/webp")
        total += len(r.content)
    assert 28000 <= total <= 36000


def test_cleanup_report_and_migration_marker_present(mongo):
    """Cleanup module: report values + idempotent completion marker remain intact."""
    report = json.loads(Path("/app/backend/rapidfire/portrait_cleanup_report.json").read_text())
    assert report.get("completed") is True
    assert report.get("reviewed") == 7045
    assert report.get("kept") == 6155
    assert report.get("deleted_active_cards") == 890
    assert report.get("reasons") == {
        "ambiguous": 226,
        "incorrect": 105,
        "calculation": 442,
        "multistep": 85,
        "borderline": 32,
    }
    marker = mongo.rf_migrations.find_one({"name": "rapid_portrait_2026_v1"}, {"_id": 0, "completed": 1}) or {}
    assert marker.get("completed") is True


def test_source_sync_not_resurrecting_deleted_jee_artifacts(mongo):
    """Sync module: rejected JEE cards never come back, and the live bank is exactly the card files
    (6155 after the cleanup; it grows only when new card files are published, e.g. the June 2026 expansion)."""
    bank = Path("/app/backend/rapidfire")
    jee = lambda folder: [c for f in (bank / folder).glob("*.json") if not f.name.startswith("biology") for c in json.loads(f.read_text())]  # noqa: E731
    rejected = [c["id"] for c in jee("rejected")]
    assert rejected and mongo.rf_cards.count_documents({"id": {"$in": rejected}, "retired": {"$ne": True}}) == 0
    active_jee_cards = mongo.rf_cards.count_documents({"exam": "JEE", "retired": {"$ne": True}})
    assert active_jee_cards == len(jee("cards")) >= 6155


def test_shop_purchase_deducts_once_and_repeat_denied(mongo, scoped_ids):
    """Shop module: one real purchase deducts once; duplicate buy of owned cosmetic is denied."""
    uid = scoped_ids['uid_shop_a']
    token = _grant_for_uid(mongo, uid)
    mongo.rf_profiles.update_one(
        {"uid": uid},
        {
            "$set": {
                "uid": uid,
                "name": "TEST RF Shop A",
                "coins": 1000,
                "owned": [],
                "equipped": {"frame": None, "entry": None, "theme": None},
                "avatar": "av_astronaut",
            }
        },
        upsert=True,
    )

    shop = requests.get(f"{BASE_URL}/api/rf/shop", headers={"Authorization": f"Bearer {token}"}, timeout=20)
    assert shop.status_code == 200
    avatars = shop.json().get("avatars") or []
    target = next((a for a in avatars if int(a.get("price") or 0) > 0), None)
    assert target is not None

    before = int(shop.json().get("coins") or 0)
    buy1 = requests.post(
        f"{BASE_URL}/api/rf/shop/buy",
        json={"item_id": target["id"]},
        headers={"Authorization": f"Bearer {token}"},
        timeout=20,
    )
    assert buy1.status_code == 200
    after = int(buy1.json().get("coins") or before)
    assert after == before - int(target["price"])

    buy2 = requests.post(
        f"{BASE_URL}/api/rf/shop/buy",
        json={"item_id": target["id"]},
        headers={"Authorization": f"Bearer {token}"},
        timeout=20,
    )
    assert buy2.status_code == 409


def test_shop_insufficient_coins_denied(mongo, scoped_ids):
    """Shop module: purchase fails with clear insufficient-coins response."""
    uid = scoped_ids['uid_shop_b']
    token = _grant_for_uid(mongo, uid)
    mongo.rf_profiles.update_one(
        {"uid": uid},
        {
            "$set": {
                "uid": uid,
                "name": "TEST RF Shop B",
                "coins": 0,
                "owned": [],
                "equipped": {"frame": None, "entry": None, "theme": None},
                "avatar": "av_astronaut",
            }
        },
        upsert=True,
    )

    shop = requests.get(f"{BASE_URL}/api/rf/shop", headers={"Authorization": f"Bearer {token}"}, timeout=20)
    assert shop.status_code == 200
    avatars = shop.json().get("avatars") or []
    target = next((a for a in avatars if int(a.get("price") or 0) > 0), None)
    assert target is not None

    buy = requests.post(
        f"{BASE_URL}/api/rf/shop/buy",
        json={"item_id": target["id"]},
        headers={"Authorization": f"Bearer {token}"},
        timeout=20,
    )
    assert buy.status_code == 409
