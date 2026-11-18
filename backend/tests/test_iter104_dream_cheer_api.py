"""Dream Unlocked celebration API: /api/rf/dream/cheered + cheer track /api/rf/art/dream_cheer.m4a (PUBLIC URL, local TEST grants)."""
import hashlib
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv("/app/backend/.env")
load_dotenv("/app/frontend/.env")
BASE = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/") + "/api"
mdb = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
RUN = uuid.uuid4().hex[:8]
UIDS = [f"TEST-it104-{RUN}-a", f"TEST-it103-{RUN}-b"]
DIGESTS = []


@pytest.fixture(autouse=True, scope="module")
def cleanup():
    yield
    mdb.rf_dreams.delete_many({"uid": {"$in": UIDS}})
    mdb.rf_access.delete_many({"digest": {"$in": DIGESTS}})


def grant(uid):
    token = secrets.token_urlsafe(24)
    d = hashlib.sha256(token.encode()).hexdigest()
    DIGESTS.append(d)
    mdb.rf_access.insert_one({"digest": d, "uid": uid, "sid": "", "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10)})
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def ha():
    return grant(UIDS[0])


@pytest.fixture(scope="module")
def hb():
    return grant(UIDS[1])


# Cheer track (public asset)
def test_track_public_audio():
    r = requests.get(f"{BASE}/rf/art/dream_cheer.m4a", timeout=30)
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("audio/mp4")
    assert 250_000 < len(r.content) < 450_000
    assert r.content[4:8] == b"ftyp"


def test_track_range_request():
    r = requests.get(f"{BASE}/rf/art/dream_cheer.m4a", headers={"Range": "bytes=0-99"}, timeout=30)
    assert r.status_code in (200, 206)


# Auth
def test_cheered_no_auth_401():
    assert requests.post(f"{BASE}/rf/dream/cheered", json={"ids": ["x"]}, timeout=15).status_code == 401


def test_cheered_bad_bearer_401():
    r = requests.post(f"{BASE}/rf/dream/cheered", json={"ids": ["x"]}, headers={"Authorization": "Bearer nope"}, timeout=15)
    assert r.status_code == 401


# Validation
@pytest.mark.parametrize("body", [{"ids": []}, {"ids": ["x"], "extra": 1}, {}, {"ids": [""]}, {"ids": ["a" * 81]}, {"ids": [f"i{k}" for k in range(16)]}, {"ids": "x"}])
def test_cheered_validation_422(ha, body):
    assert requests.post(f"{BASE}/rf/dream/cheered", json=body, headers=ha, timeout=15).status_code == 422


# Behaviour
def test_cheered_upsert_dedupe_and_get(ha):
    # GET on empty account -> shape {dreams, mocks, cheered}
    g = requests.get(f"{BASE}/rf/dream", headers=ha, timeout=15).json()
    assert g == {"dreams": [], "mocks": [], "cheered": []}
    r = requests.post(f"{BASE}/rf/dream/cheered", json={"ids": ["jee-1", "jee-1", "jee-2"]}, headers=ha, timeout=15)
    assert r.status_code == 200 and r.json() == {"ok": True}
    r = requests.post(f"{BASE}/rf/dream/cheered", json={"ids": ["jee-2", "jee-3"]}, headers=ha, timeout=15)
    assert r.status_code == 200
    g = requests.get(f"{BASE}/rf/dream", headers=ha, timeout=15).json()
    assert g["cheered"] == ["jee-1", "jee-2", "jee-3"]


def test_cheered_keeps_dreams_and_mocks(ha):
    d = {"id": "jee-9", "exam": "jee", "college": "TEST_NIT", "branch": "CSE", "need": 180, "at": 1}
    m = {"id": "m9", "exam": "jee", "score": 190, "max": 300, "raw": 190, "rawMax": 300, "title": "TEST_Mock", "at": 1000}
    assert requests.put(f"{BASE}/rf/dream/dreams", json={"dreams": [d], "base": []}, headers=ha, timeout=15).status_code == 200
    assert requests.post(f"{BASE}/rf/dream/mocks", json={"mocks": [m]}, headers=ha, timeout=15).status_code == 200
    assert requests.post(f"{BASE}/rf/dream/cheered", json={"ids": ["jee-9"]}, headers=ha, timeout=15).status_code == 200
    g = requests.get(f"{BASE}/rf/dream", headers=ha, timeout=15).json()
    assert [x["id"] for x in g["dreams"]] == ["jee-9"] and [x["id"] for x in g["mocks"]] == ["m9"] and "jee-9" in g["cheered"]
    assert "_id" not in g


def test_cheered_isolated_per_account(ha, hb):
    g = requests.get(f"{BASE}/rf/dream", headers=hb, timeout=15).json()
    assert g["cheered"] == []


def test_cheered_parallel_first_write(hb):
    import concurrent.futures as cf
    with cf.ThreadPoolExecutor(4) as ex:
        codes = list(ex.map(lambda i: requests.post(f"{BASE}/rf/dream/cheered", json={"ids": [f"p{i}"]}, headers=hb, timeout=15).status_code, range(4)))
    assert codes == [200] * 4
    g = requests.get(f"{BASE}/rf/dream", headers=hb, timeout=15).json()
    assert sorted(g["cheered"]) == ["p0", "p1", "p2", "p3"]
    assert mdb.rf_dreams.count_documents({"uid": UIDS[1]}) == 1
