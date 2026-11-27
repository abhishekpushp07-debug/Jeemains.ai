# CEO API (iter157): test profiles left out + stable student order. READ ONLY (Mongo is only read, never written).
import os
import re
import subprocess
from datetime import datetime, timedelta, timezone

import pytest
import requests
from pymongo import MongoClient


def _env(path, key):
    for line in open(path):
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip().strip('"')


BASE = _env("/app/frontend/.env", "EXPO_PUBLIC_BACKEND_URL").rstrip("/")
MONGO_URL, DB_NAME = _env("/app/backend/.env", "MONGO_URL"), _env("/app/backend/.env", "DB_NAME")


def _token():
    t = os.environ.get("CEO_API_TOKEN") or _env("/app/backend/.env", "CEO_API_TOKEN")
    if t:
        return t
    pid = subprocess.run("pgrep -f 'uvicorn server:app'", shell=True, capture_output=True, text=True).stdout.split()[0]
    env = subprocess.run(["sudo", "cat", f"/proc/{pid}/environ"], capture_output=True).stdout.split(b"\0")
    for e in env:
        if e.startswith(b"CEO_API_TOKEN="):
            return e.split(b"=", 1)[1].decode()
    pytest.skip("CEO_API_TOKEN not found")


TOKEN = _token()
H = {"Authorization": f"Bearer {TOKEN}"}
UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
REAL = {"uid": {"$regex": UUID.pattern, "$options": "i"}, "name": {"$not": {"$regex": "^TEST"}}}
IST = timezone(timedelta(hours=5, minutes=30))


def day(n):
    return (datetime.now(IST) - timedelta(days=n)).strftime("%Y-%m-%d")


@pytest.fixture(scope="module")
def db():
    c = MongoClient(MONGO_URL)
    yield c[DB_NAME]
    c.close()


@pytest.fixture(scope="module")
def ov():
    r = requests.get(f"{BASE}/api/ceo/overview", headers=H, timeout=30)
    assert r.status_code == 200
    return r.json()


def get_users(**params):
    r = requests.get(f"{BASE}/api/ceo/users", headers=H, params=params, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()


# --- auth
def test_overview_no_token_401():
    assert requests.get(f"{BASE}/api/ceo/overview", timeout=30).status_code == 401


def test_overview_wrong_token_401():
    assert requests.get(f"{BASE}/api/ceo/overview", headers={"Authorization": "Bearer nope"}, timeout=30).status_code == 401


def test_users_no_and_wrong_token_401():
    assert requests.get(f"{BASE}/api/ceo/users", timeout=30).status_code == 401
    assert requests.get(f"{BASE}/api/ceo/users", headers={"Authorization": "Bearer x"}, timeout=30).status_code == 401


# --- overview counts vs direct Mongo read
def test_overview_counts_match_mongo(db, ov):
    p = db.rf_profiles
    real = p.count_documents(REAL)
    assert ov["app_users"] == real
    assert ov["test_profiles_left_out"] == p.count_documents({}) - real
    assert ov["active"]["today"] == p.count_documents({**REAL, "last_day": day(0)})
    assert ov["active"]["last_7_days"] == p.count_documents({**REAL, "last_day": {"$gte": day(6)}})
    assert ov["active"]["last_30_days"] == p.count_documents({**REAL, "last_day": {"$gte": day(29)}})
    assert ov["on_streak"] == p.count_documents({**REAL, "streak": {"$gt": 0}})
    assert ov["rapid_fire_players"] == p.count_documents(
        {**REAL, "$or": [{"sessions": {"$gt": 0}}, {"duels": {"$gt": 0}}, {"rival_games": {"$gt": 0}}]})
    best = max([d.get("best_streak") or 0 for d in p.find(REAL, {"best_streak": 1})] or [0])
    assert ov["best_streak_seen"] == best


def test_overview_python_side_real_filter(db, ov):
    # independent check: python-side filter (UUID case-insensitive + not name startswith TEST)
    n = sum(1 for d in db.rf_profiles.find({}, {"uid": 1, "name": 1})
            if isinstance(d.get("uid"), str) and UUID.match(d["uid"]) and not str(d.get("name") or "").startswith("TEST"))
    assert ov["app_users"] == n


# --- users list
def test_users_total_matches_overview(ov):
    d = get_users()
    assert d["total"] == ov["app_users"]
    assert all(UUID.match(i["uid"]) and not (i["name"] or "").startswith("TEST") for i in d["items"])
    assert "_id" not in str(d)


def _order_ok(items):
    keys = [(i["last_active"] or "", i["uid"]) for i in items]
    for a, b in zip(keys, keys[1:]):
        assert a[0] > b[0] or (a[0] == b[0] and a[1] < b[1]), (a, b)


def test_users_order_rule():
    _order_ok(get_users(limit=500)["items"])


@pytest.mark.parametrize("limit", [1, 2])
def test_users_paging_no_repeat_no_gap(limit, db):
    first = get_users(limit=limit)
    seen = []
    for page in range(1, first["pages"] + 1):
        seen += [i["uid"] for i in get_users(limit=limit, page=page)["items"]]
    assert len(seen) == len(set(seen)) == first["total"]
    expected = {d["uid"] for d in db.rf_profiles.find(REAL, {"uid": 1})}
    assert set(seen) == expected


def test_users_q_test_zero():
    assert get_users(q="TEST")["total"] == 0


def test_users_q_and_active_since(db):
    items = get_users(limit=500)["items"]
    if not items:
        pytest.skip("no real profiles")
    name = items[0]["name"] or items[0]["player_code"]
    d = get_users(q=name[:4])
    assert d["total"] >= 1 and all(UUID.match(i["uid"]) for i in d["items"])
    since = day(29)
    d2 = get_users(active_since=since)
    assert d2["total"] == db.rf_profiles.count_documents({**REAL, "last_day": {"$gte": since}})
    assert all((i["last_active"] or "") >= since for i in d2["items"])
    # far future -> 0
    assert get_users(active_since="2999-01-01")["total"] == 0


def test_index_exists(db):
    keys = [list(ix["key"].items()) for ix in db.rf_profiles.list_indexes()]
    assert [("last_day", -1), ("uid", 1)] in keys
