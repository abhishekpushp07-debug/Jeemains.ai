# Iteration 19: soft-retire of verifier-removed cards (no delete_many) + httpx dependency pin
import asyncio
import json
import os
import pathlib
import re
import shutil
import sys
import tempfile
import time
import uuid

import pytest
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv("/app/frontend/.env")
load_dotenv("/app/backend/.env")
BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL").rstrip("/")
UID = "db0c62b8-eeaf-41be-b8b1-05f5f34ac1d8"
H = {"X-RF-User": UID}
SUBJ, CHAP = "Chemistry", "p-Block"
mdb = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]


def rid():
    return "TEST_" + uuid.uuid4().hex


def catalog_count(cat, s, c):
    for sub in cat["subjects"]:
        if sub["name"] == s:
            for ch in sub["chapters"]:
                if ch["name"] == c:
                    return ch["count"]
    return None


def wait_catalog(expected, timeout=80):
    v = None
    for _ in range(timeout // 5):
        v = catalog_count(requests.get(f"{BASE_URL}/api/rf/catalog").json(), SUBJ, CHAP)
        if v == expected:
            return v
        time.sleep(5)
    return v


# Static: no delete_many on rf_cards anywhere in backend code
def test_no_delete_many_on_cards():
    for f in ["server.py", "duels.py", "gamify.py", "shop.py"]:
        src = pathlib.Path("/app/backend", f).read_text()
        assert not re.search(r"rf_cards\.(delete_many|delete_one|drop)", src), f


# Dependency pin: httpx and friends pinned and importable
def test_httpx_pinned_and_importable():
    req = pathlib.Path("/app/backend/requirements.txt").read_text()
    for p in ["httpx==", "httpcore==", "anyio==", "certifi==", "idna==", "sniffio==", "h11=="]:
        assert p in req, p
    import httpx
    assert httpx.__version__ == re.search(r"httpx==([\d.]+)", req).group(1)


# Catalog counts equal non-retired DB counts (~11k)
def test_catalog_matches_non_retired():
    cat = requests.get(f"{BASE_URL}/api/rf/catalog").json()
    total = sum(s["total"] for s in cat["subjects"])
    assert total == mdb.rf_cards.count_documents({"retired": {"$ne": True}})
    assert 10000 <= total <= 12000


# Solo sprint returns 30 non-retired cards
def test_solo_sprint_30_non_retired():
    r = requests.post(f"{BASE_URL}/api/rf/sessions", json={"subject": "Physics", "request_id": rid()}, headers=H)
    assert r.status_code == 200
    cards = r.json()["cards"]
    assert len(cards) == 30 and len({c["id"] for c in cards}) == 30
    assert mdb.rf_cards.count_documents({"id": {"$in": [c["id"] for c in cards]}, "retired": True}) == 0


@pytest.fixture(scope="module")
def retired_card():
    s = requests.post(f"{BASE_URL}/api/rf/sessions", json={"subject": SUBJ, "chapter": CHAP, "request_id": rid()}, headers=H).json()
    x = s["cards"][0]["id"]
    base = mdb.rf_cards.count_documents({"subject": SUBJ, "chapter": CHAP, "retired": {"$ne": True}})
    mdb.rf_cards.update_one({"id": x}, {"$set": {"retired": True}})
    yield {"x": x, "old_sid": s["id"], "old_card_ids": s["card_ids"], "base": base}
    mdb.rf_cards.update_one({"id": x}, {"$set": {"retired": False}})


# Retired card never appears in fresh solo sessions (15 samples from a 94-card chapter)
def test_retired_not_in_new_sessions(retired_card):
    x = retired_card["x"]
    for _ in range(15):
        c = requests.post(f"{BASE_URL}/api/rf/sessions", json={"subject": SUBJ, "chapter": CHAP, "request_id": rid()}, headers=H).json()["cards"]
        assert len(c) == 30
        assert x not in [k["id"] for k in c]


# Retired card excluded from repeat-missed
def test_retired_not_in_repeat_missed(retired_card):
    x, ids = retired_card["x"], retired_card["old_card_ids"]
    r = requests.post(f"{BASE_URL}/api/rf/sessions", json={"subject": SUBJ, "card_ids": [x, ids[1]], "request_id": rid()}, headers=H)
    assert r.status_code == 200
    assert [c["id"] for c in r.json()["cards"]] == [ids[1]]
    r = requests.post(f"{BASE_URL}/api/rf/sessions", json={"subject": SUBJ, "card_ids": [x], "request_id": rid()}, headers=H)
    assert r.status_code == 404


# Retired card never picked for duels
def test_retired_not_in_duels(retired_card):
    x = retired_card["x"]
    for _ in range(10):
        d = requests.post(f"{BASE_URL}/api/rf/duels", json={"subject": SUBJ, "chapter": CHAP, "mode": "invite", "name": "TEST_P", "request_id": rid()}, headers=H).json()
        doc = mdb.rf_duels.find_one({"id": d["id"]})
        assert len(doc["card_ids"]) == 30 and x not in doc["card_ids"]
        requests.post(f"{BASE_URL}/api/rf/duels/{d['id']}/cancel", headers=H)


# Retired card excluded from public /rf/cards
def test_retired_not_in_public_cards(retired_card):
    r = requests.get(f"{BASE_URL}/api/rf/cards", params={"subject": SUBJ, "chapter": CHAP, "limit": 200}).json()
    assert r["total"] == retired_card["base"] - 1
    assert retired_card["x"] not in [c["id"] for c in r["items"]]


# Old session containing the retired card still loads (GET) and completes
def test_old_session_still_loads(retired_card):
    s = requests.get(f"{BASE_URL}/api/rf/sessions/{retired_card['old_sid']}", headers=H).json()
    assert len(s["cards"]) == 30 and retired_card["x"] in [c["id"] for c in s["cards"]]
    c = requests.post(f"{BASE_URL}/api/rf/sessions/{retired_card['old_sid']}/complete",
                      json={"results": [{"card_id": retired_card["x"], "outcome": "correct", "choice": 0, "ms": 1000}]}, headers=H)
    assert c.status_code == 200, c.text
    assert c.json()["summary"]["total"] == 30


# Catalog count drops by one after cache refresh (sync loop clears cache every 60s)
def test_catalog_excludes_retired(retired_card):
    assert wait_catalog(retired_card["base"] - 1) == retired_card["base"] - 1


# sync_cards itself: card dropped from a chapter file -> retired (not deleted); re-added -> un-retired
def test_sync_cards_soft_retire_roundtrip():
    sys.path.insert(0, "/app/backend")
    import server
    src = next(f for f in server.CARDS_DIR.glob("*.json") if json.loads(f.read_text())[0]["chapter"] == CHAP)
    cards = json.loads(src.read_text())
    x = cards[-1]["id"]
    total_before = mdb.rf_cards.count_documents({})
    tmp = pathlib.Path(tempfile.mkdtemp())
    try:
        (tmp / src.name).write_text(json.dumps(cards[:-1]))
        server.CARDS_DIR, server.CARD_MTIMES = tmp, {}
        loop = asyncio.new_event_loop()
        loop.run_until_complete(server.sync_cards())
        assert mdb.rf_cards.count_documents({}) == total_before  # nothing deleted
        assert mdb.rf_cards.find_one({"id": x})["retired"] is True
        assert mdb.rf_cards.count_documents({"chapter": CHAP, "retired": True}) == 1
        shutil.copy(src, tmp / src.name)
        server.CARD_MTIMES = {}
        loop.run_until_complete(server.sync_cards())
        assert mdb.rf_cards.find_one({"id": x})["retired"] is False
        loop.close()
    finally:
        mdb.rf_cards.update_one({"id": x}, {"$set": {"retired": False}})
        shutil.rmtree(tmp)
    assert mdb.rf_cards.count_documents({"retired": True}) == 0


# Duel AI Rival quick match: random -> bot -> ready with 4.6s intro and 30 cards
def test_duel_ai_rival_end_to_end():
    d = requests.post(f"{BASE_URL}/api/rf/duels", json={"subject": "Mathematics", "chapter": None, "mode": "random", "name": "TEST_P", "request_id": rid()}, headers=H).json()
    v = requests.post(f"{BASE_URL}/api/rf/duels/{d['id']}/bot", headers=H).json()
    assert v["status"] == "ready" and v["vs_bot"] is True and v["total"] == 30
    assert 4.3 <= v["start_at"] - v["server_now"] <= 4.7
    time.sleep(max(0, v["start_at"] - v["server_now"]) + 0.5)
    g = requests.get(f"{BASE_URL}/api/rf/duels/{d['id']}", headers=H).json()
    assert g["status"] == "ready" and len(g["cards"]) >= 1
    a = requests.post(f"{BASE_URL}/api/rf/duels/{d['id']}/answer", json={"index": 0, "choice": 0, "outcome": "answer", "ms": 3000}, headers=H)
    assert a.status_code == 200, a.text
    requests.post(f"{BASE_URL}/api/rf/duels/{d['id']}/forfeit", headers=H)
