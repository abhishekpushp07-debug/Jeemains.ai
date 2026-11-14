"""Cup Champion Showcase: crown {won, real} on player cards and profile `cups` block (public URL).

Requires the seeded social fixture (python /app/tests/rf_social_fixture.py seed). Uses one TEST viewer with a hashed
short-lived grant and temporary friend rows to the fixture friends; removes exactly what it created.
"""
import hashlib
import os
import secrets
import sys
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import requests
from dotenv import dotenv_values, load_dotenv
from pymongo import MongoClient

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
from social import make_pid  # noqa: E402

FE = dotenv_values("/app/frontend/.env")
BASE = (FE.get("EXPO_BACKEND_URL") or FE["EXPO_PUBLIC_BACKEND_URL"]).rstrip("/") + "/api/rf"
DIYA, AARAV, KABIR = "PE5941BE1", "P3299BB0E", "P78C578D5"


@pytest.fixture(scope="module")
def ctx():
    db = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    fx = {p["pid"]: p for p in db.rf_profiles.find({"pid": {"$in": [DIYA, AARAV, KABIR]}}, {"_id": 0, "uid": 1, "pid": 1})}
    if len(fx) < 3:
        pytest.skip("social fixture not seeded")
    uid = f"TEST-crown-{uuid.uuid4().hex[:6]}"
    token = secrets.token_urlsafe(24)
    db.rf_access.insert_one({"digest": hashlib.sha256(token.encode()).hexdigest(), "uid": uid, "sid": "", "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10)})
    rows = [r for p in fx.values() for r in ({"uid": uid, "fid": p["uid"], "ts": 0}, {"uid": p["uid"], "fid": uid, "ts": 0})]
    db.rf_friends.insert_many(rows)
    db.rf_profiles.insert_one({"uid": uid, "pid": make_pid(uid), "name": "TESTCROWN", "display_name": "TESTCROWN"})
    s = requests.Session()
    s.headers["Authorization"] = "Bearer " + token
    yield {"s": s, "uid": uid, "pid": make_pid(uid)}
    db.rf_access.delete_many({"uid": uid})
    db.rf_friends.delete_many({"$or": [{"uid": uid}, {"fid": uid}]})
    db.rf_profiles.delete_many({"uid": uid})
    db.rf_notices.delete_many({"$or": [{"uid": uid}, {"from_uid": uid}]})


def get(ctx, path):
    r = ctx["s"].get(BASE + path, timeout=30)
    assert r.status_code == 200, r.text
    assert '"_id"' not in r.text
    return r.json()


# Profile: gold crown x3, 2 vs real players, latest wins newest first
def test_diya_profile(ctx):
    p = get(ctx, f"/players/{DIYA}")
    assert p["crown"] == {"won": 3, "real": 2}
    c = p["cups"]
    assert (c["won"], c["real"], c["played"]) == (3, 2, 3)
    assert [w["label"] for w in c["recent"]] == ["PCM Mixed", "Mixed Physics", "Mixed Chemistry"]
    assert [w["humans"] for w in c["recent"]] == [2, 2, 1]
    assert [w["size"] for w in c["recent"]] == [8, 4, 4]
    assert all(set(w) == {"id", "label", "size", "kind", "humans", "finished_at"} for w in c["recent"])
    assert p["is_me"] is False


# Profile: silver crown (practice only)
def test_aarav_profile(ctx):
    p = get(ctx, f"/players/{AARAV}")
    assert p["crown"] == {"won": 1, "real": 0}
    assert (p["cups"]["won"], p["cups"]["real"], p["cups"]["played"]) == (1, 0, 1)
    assert p["cups"]["recent"][0]["humans"] == 1


# Profile: no crown, but cups played counted
def test_kabir_profile(ctx):
    p = get(ctx, f"/players/{KABIR}")
    assert p["crown"] is None
    assert (p["cups"]["won"], p["cups"]["real"], p["cups"]["recent"]) == (0, 0, [])
    assert p["cups"]["played"] == 2


# Own profile: zero cups
def test_own_profile(ctx):
    p = get(ctx, f"/players/{ctx['pid']}")
    assert p["is_me"] is True and p["crown"] is None
    assert p["cups"] == {"won": 0, "real": 0, "played": 0, "recent": []}


# Friends list cards carry crown
def test_friends_list_crowns(ctx):
    d = get(ctx, "/friends")
    items = d["items"] if isinstance(d, dict) else d
    by = {f["pid"]: f for f in items}
    assert by[DIYA]["crown"] == {"won": 3, "real": 2}
    assert by[AARAV]["crown"] == {"won": 1, "real": 0}
    assert by[KABIR]["crown"] is None


# Friends League rows carry crown
def test_friends_league_crowns(ctx):
    d = get(ctx, "/league/friends")
    by = {x["pid"]: x for x in d["items"]}
    assert by[DIYA]["crown"] == {"won": 3, "real": 2}
    assert by[AARAV]["crown"] == {"won": 1, "real": 0}
    assert by[KABIR]["crown"] is None
    assert all("crown" in x for x in d["items"])
    for key in ("last", "all_time"):
        v = d.get(key)
        rows = (v or {}).get("items", []) if isinstance(v, dict) else (v or [])
        assert all("crown" in x for x in rows), key


# All India leaderboard + Gang War board carry crown key
@pytest.mark.parametrize("path", ["/leaderboard", "/league/gangwar"])
def test_boards_have_crown(ctx, path):
    d = get(ctx, path)
    items = d["items"] if isinstance(d, dict) else d
    assert all("crown" in x for x in items)
    for x in items:
        assert x["crown"] is None or (x["crown"]["won"] >= 1 and 0 <= x["crown"]["real"] <= x["crown"]["won"])


# Auth required
def test_profile_needs_auth():
    assert requests.get(f"{BASE}/players/{DIYA}", timeout=30).status_code in (401, 403)
