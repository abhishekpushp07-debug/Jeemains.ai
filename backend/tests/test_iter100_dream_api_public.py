"""Dream College API (/api/rf/dream*) via the PUBLIC URL with local TEST grants (no website writes)."""
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
UIDS = [f"TEST-it100-{RUN}-a", f"TEST-it100-{RUN}-b"]
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


D = {"id": "jee-1", "exam": "jee", "college": "TEST_NIT", "branch": "CSE", "need": 180, "range": [170, 195], "note": "R5 closing", "at": 1}
M = {"id": "m1", "exam": "jee", "score": 120, "max": 300, "raw": 120, "rawMax": 300, "title": "TEST_Mock", "at": 1000}


@pytest.fixture(scope="module")
def ha():
    return grant(UIDS[0])


@pytest.fixture(scope="module")
def hb():
    return grant(UIDS[1])


# Auth
def test_no_bearer_401():
    assert requests.get(f"{BASE}/rf/dream", timeout=15).status_code == 401
    assert requests.put(f"{BASE}/rf/dream/dreams", json={"dreams": [], "base": []}, timeout=15).status_code == 401
    assert requests.post(f"{BASE}/rf/dream/mocks", json={"mocks": [M]}, timeout=15).status_code == 401


def test_bad_bearer_401():
    assert requests.get(f"{BASE}/rf/dream", headers={"Authorization": "Bearer nope"}, timeout=15).status_code == 401


# Dreams
def test_empty_then_save(ha):
    assert requests.get(f"{BASE}/rf/dream", headers=ha, timeout=15).json() == {"dreams": [], "mocks": [], "cheered": []}
    r = requests.put(f"{BASE}/rf/dream/dreams", headers=ha, json={"dreams": [D], "base": []}, timeout=15)
    assert r.status_code == 200 and r.json()["dreams"][0]["college"] == "TEST_NIT"
    got = requests.get(f"{BASE}/rf/dream", headers=ha, timeout=15).json()
    assert got["dreams"][0]["note"] == "R5 closing" and got["dreams"][0]["range"] == [170, 195]


def test_six_per_exam_400_five_ok(ha):
    five = [{**D, "id": f"jee-{i}"} for i in range(5)]
    five_b = [{**D, "id": f"bit-{i}", "exam": "bitsat"} for i in range(5)]
    assert requests.put(f"{BASE}/rf/dream/dreams", headers=ha, json={"dreams": five + five_b, "base": ["jee-1"]}, timeout=15).status_code == 200
    six = [{**D, "id": f"jee-{i}"} for i in range(6)]
    r = requests.put(f"{BASE}/rf/dream/dreams", headers=ha, json={"dreams": six, "base": []}, timeout=15)
    assert r.status_code == 400
    got = requests.get(f"{BASE}/rf/dream", headers=ha, timeout=15).json()
    assert len(got["dreams"]) == 10  # unchanged after rejected PUT


def test_duplicate_ids_400(ha):
    assert requests.put(f"{BASE}/rf/dream/dreams", headers=ha, json={"dreams": [D, D], "base": []}, timeout=15).status_code == 400


def test_invalid_exam_422(ha):
    assert requests.put(f"{BASE}/rf/dream/dreams", headers=ha, json={"dreams": [{**D, "exam": "neet"}], "base": []}, timeout=15).status_code == 422


def test_missing_base_only_adds(ha):
    ids = [d["id"] for d in requests.get(f"{BASE}/rf/dream", headers=ha, timeout=15).json()["dreams"]]
    requests.put(f"{BASE}/rf/dream/dreams", headers=ha, json={"dreams": [D], "base": ids}, timeout=15)
    r = requests.put(f"{BASE}/rf/dream/dreams", headers=ha, json={"dreams": [{**D, "id": "older-build"}]}, timeout=15)
    assert r.status_code == 200 and [d["id"] for d in r.json()["dreams"]] == ["jee-1", "older-build"]


def test_empty_list_clears(ha):
    ids = [d["id"] for d in requests.get(f"{BASE}/rf/dream", headers=ha, timeout=15).json()["dreams"]]
    assert requests.put(f"{BASE}/rf/dream/dreams", headers=ha, json={"dreams": [], "base": ids}, timeout=15).status_code == 200
    assert requests.get(f"{BASE}/rf/dream", headers=ha, timeout=15).json()["dreams"] == []


# Merge: a phone's changes never wipe the account's own dreams or another device's
def put(h, dreams, base):
    r = requests.put(f"{BASE}/rf/dream/dreams", headers=h, json={"dreams": dreams, "base": base}, timeout=15)
    assert r.status_code == 200, r.text
    return [d["id"] for d in r.json()["dreams"]]


def test_two_devices_both_adds_kept(ha):
    put(ha, [], [d["id"] for d in requests.get(f"{BASE}/rf/dream", headers=ha, timeout=15).json()["dreams"]])
    assert put(ha, [{**D, "id": "x"}], []) == ["x"]           # phone A adds x
    assert put(ha, [{**D, "id": "y"}], []) == ["x", "y"]      # phone B (never saw x) adds y: x stays


def test_removal_only_of_what_phone_removed(ha):
    assert put(ha, [{**D, "id": "y"}], ["x", "y"]) == ["y"]   # removed x, kept y
    assert put(ha, [{**D, "id": "z"}], ["x"]) == ["y", "z"]   # stale phone: x already gone, y (unknown to it) stays


def test_old_phone_dreams_fill_free_slots_only(ha):
    put(ha, [], ["y", "z"])
    five = [{**D, "id": f"acc-{i}"} for i in range(5)]
    put(ha, five, [])
    legacy = [{**D, "id": "old-jee"}, {**D, "id": "old-comedk", "exam": "comedk"}]
    got = put(ha, legacy, [])
    assert got == [f"acc-{i}" for i in range(5)] + ["old-comedk"]  # JEE full: the account's 5 stay, old JEE dropped


def test_parallel_saves_both_land(ha):
    from concurrent.futures import ThreadPoolExecutor
    put(ha, [], [d["id"] for d in requests.get(f"{BASE}/rf/dream", headers=ha, timeout=15).json()["dreams"]])
    with ThreadPoolExecutor(6) as pool:
        list(pool.map(lambda i: put(ha, [{**D, "id": f"p{i}", "exam": "bitsat" if i % 2 else "comedk"}], []), range(6)))
    got = {d["id"] for d in requests.get(f"{BASE}/rf/dream", headers=ha, timeout=15).json()["dreams"]}
    assert got == {f"p{i}" for i in range(6)}


# Mocks
def test_mocks_replace_newest_first(ha):
    assert requests.post(f"{BASE}/rf/dream/mocks", headers=ha, json={"mocks": [M, {**M, "id": "m2", "at": 2000}]}, timeout=15).status_code == 200
    assert requests.post(f"{BASE}/rf/dream/mocks", headers=ha, json={"mocks": [{**M, "score": 140}]}, timeout=15).status_code == 200
    got = requests.get(f"{BASE}/rf/dream", headers=ha, timeout=15).json()["mocks"]
    assert [(m["id"], m["score"]) for m in got] == [("m2", 120), ("m1", 140)]


def test_mocks_max_30(ha):
    batch = [{**M, "id": f"x{i}", "at": 5000 + i} for i in range(30)]
    assert requests.post(f"{BASE}/rf/dream/mocks", headers=ha, json={"mocks": batch}, timeout=15).status_code == 200
    got = requests.get(f"{BASE}/rf/dream", headers=ha, timeout=15).json()["mocks"]
    assert len(got) == 30 and got[0]["id"] == "x29" and "m1" not in [m["id"] for m in got]


def test_a_paper_that_is_no_full_mock_is_taken_out(ha):
    # The app found that a remembered paper is a chapter test (an older version counted long ones): it is removed, and
    # its id is handed out with the list so that every phone takes it out of its own copy.
    requests.post(f"{BASE}/rf/dream/mocks", headers=ha, json={"mocks": [dict(M, id="drop-me", at=9000), dict(M, id="keep-me", at=8000)]}, timeout=30)
    first = requests.get(f"{BASE}/rf/dream", headers=ha, timeout=30).json()
    before = [m["id"] for m in first["mocks"]]
    assert "drop-me" in before and "keep-me" in before and "dropped" not in first
    assert requests.delete(f"{BASE}/rf/dream/mocks/drop-me", headers=ha, timeout=30).json() == {"ok": True}
    got = requests.get(f"{BASE}/rf/dream", headers=ha, timeout=30).json()
    assert [m["id"] for m in got["mocks"]] == [i for i in before if i != "drop-me"] and got["dropped"] == ["drop-me"]
    # Again, or a paper that was never there: the list does not change (the id is remembered once). Without a grant: refused.
    assert requests.delete(f"{BASE}/rf/dream/mocks/drop-me", headers=ha, timeout=30).status_code == 200
    assert requests.delete(f"{BASE}/rf/dream/mocks/never-there", headers=ha, timeout=30).status_code == 200
    got = requests.get(f"{BASE}/rf/dream", headers=ha, timeout=30).json()
    assert [m["id"] for m in got["mocks"]] == [i for i in before if i != "drop-me"] and got["dropped"] == ["drop-me", "never-there"]
    # Sent again (an older app version, or a phone that still holds it): not taken back; a real mock beside it is.
    assert requests.post(f"{BASE}/rf/dream/mocks", headers=ha, json={"mocks": [dict(M, id="drop-me", at=9000)]}, timeout=30).json() == {"ok": True}
    assert requests.post(f"{BASE}/rf/dream/mocks", headers=ha, json={"mocks": [dict(M, id="drop-me", at=9000), dict(M, id="keep-me", at=8000, score=150)]}, timeout=30).status_code == 200
    got = requests.get(f"{BASE}/rf/dream", headers=ha, timeout=30).json()["mocks"]
    assert "drop-me" not in [m["id"] for m in got] and next(m["score"] for m in got if m["id"] == "keep-me") == 150
    assert requests.delete(f"{BASE}/rf/dream/mocks/keep-me", timeout=30).status_code == 401
    assert requests.delete(f"{BASE}/rf/dream/mocks/{'x' * 65}", headers=ha, timeout=30).status_code == 422
    # An account that has nothing yet: the id is still remembered (another phone may hold the paper).
    hc = grant(f"TEST-it100-{RUN}-c")
    UIDS.append(f"TEST-it100-{RUN}-c")
    assert requests.delete(f"{BASE}/rf/dream/mocks/first-thing", headers=hc, timeout=30).status_code == 200
    assert requests.get(f"{BASE}/rf/dream", headers=hc, timeout=30).json() == {"dreams": [], "mocks": [], "cheered": [], "dropped": ["first-thing"]}
    # At most 200 are remembered; the paper is still taken out after that.
    mdb.rf_dreams.update_one({"uid": f"TEST-it100-{RUN}-c"}, {"$set": {"dropped": [f"d{i}" for i in range(200)], "mocks": [dict(M, id="late")]}})
    assert requests.delete(f"{BASE}/rf/dream/mocks/late", headers=hc, timeout=30).status_code == 200
    got = requests.get(f"{BASE}/rf/dream", headers=hc, timeout=30).json()
    assert got["mocks"] == [] and len(got["dropped"]) == 200 and "late" not in got["dropped"]


def test_mocks_empty_or_31_422(ha):
    assert requests.post(f"{BASE}/rf/dream/mocks", headers=ha, json={"mocks": []}, timeout=15).status_code == 422
    assert requests.post(f"{BASE}/rf/dream/mocks", headers=ha, json={"mocks": [{**M, "id": f"y{i}"} for i in range(31)]}, timeout=15).status_code == 422


# Isolation
def test_other_account_isolated(ha, hb):
    requests.put(f"{BASE}/rf/dream/dreams", headers=ha, json={"dreams": [D], "base": []}, timeout=15)
    assert requests.get(f"{BASE}/rf/dream", headers=hb, timeout=15).json() == {"dreams": [], "mocks": [], "cheered": []}
