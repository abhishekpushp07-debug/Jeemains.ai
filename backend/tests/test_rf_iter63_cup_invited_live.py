"""Iter63 live check: Friends Cup host sees invited_players; friends league shows each fixture friend once. Needs RF_TEST_SID + seeded rf_social_fixture."""
import os
import pytest
import requests

BASE = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "").rstrip("/") + "/api"
SID = os.environ.get("RF_TEST_SID")
pytestmark = pytest.mark.skipif(not SID or BASE == "/api", reason="RF_TEST_SID not set")
FRIENDS = ["PB9DF02EC", "P0E830E12", "PEA5C6FE7"]


@pytest.fixture(scope="module")
def h():
    r = requests.post(f"{BASE}/rf/access", headers={"X-JL-Sid": SID}, json={}, timeout=20)
    if r.status_code != 200:
        pytest.skip(f"rf/access {r.status_code}")
    return {"Authorization": "Bearer " + r.json()["token"]}


# Friends Cup: invited_players for host, then cancel (leave) the cup
def test_private_cup_invited_players(h):
    pids = [p for p in os.environ.get("RF_FIXTURE_PIDS", ",".join(FRIENDS)).split(",") if p]
    r = requests.post(f"{BASE}/rf/cups", headers=h, json={"kind": "private", "size": 4, "pids": pids}, timeout=20)
    assert r.status_code == 200, r.text
    cid = r.json().get("id") or r.json().get("cup", {}).get("id")
    try:
        g = requests.get(f"{BASE}/rf/cups/{cid}", headers=h, timeout=20)
        assert g.status_code == 200
        d = g.json()
        assert d["is_host"] is True and d["kind"] == "private"
        inv = d["invited_players"]
        print("invited", [(p.get("pid"), p.get("name"), p.get("joined")) for p in inv])
        got = [p.get("pid") for p in inv]
        assert len(got) == len(set(got)), "duplicate invited rows"
        for p in pids:
            assert p in got
        assert all(p["joined"] is False for p in inv if p.get("pid") in pids)
    finally:
        lv = requests.post(f"{BASE}/rf/cups/{cid}/leave", headers=h, json={}, timeout=20)
        print("leave", lv.status_code, lv.text[:200])
        assert lv.status_code == 200


# Friends league: no duplicate fixture friend
def test_friends_league_unique(h):
    r = requests.get(f"{BASE}/rf/league/friends", headers=h, timeout=20)
    assert r.status_code == 200
    rows = r.json().get("rows") or r.json().get("items") or r.json().get("board") or []
    names = [x.get("name") for x in rows]
    print("league names", names)
    for n in ("Aarav Sharma", "Diya Patel", "Kabir Singh"):
        assert names.count(n) <= 1, f"{n} duplicated"
