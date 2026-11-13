"""Phase 3 live-API regression over the public URL, as the approved QA learner (needs RF_TEST_SID = web X-JL-Sid; skipped otherwise).
Requires `python tests/rf_social_fixture.py seed` first (Aarav = first friend with a lost match). Creates one Badla challenge and cancels it."""
import os
import pytest
import requests

BASE = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "").rstrip("/") + "/api"
SID = os.environ.get("RF_TEST_SID")
pytestmark = pytest.mark.skipif(not SID or BASE == "/api", reason="RF_TEST_SID / EXPO_PUBLIC_BACKEND_URL not set")


@pytest.fixture(scope="module")
def h():
    r = requests.post(f"{BASE}/rf/access", headers={"X-JL-Sid": SID}, json={}, timeout=20)
    if r.status_code != 200:
        pytest.skip(f"rf/access {r.status_code}")
    return {"Authorization": "Bearer " + r.json()["token"]}


@pytest.fixture(scope="module")
def lost(h):
    """The fixture friend + their lost 1 v 1 match (from the h2h list)."""
    friends = requests.get(f"{BASE}/rf/friends", headers=h, timeout=20)
    items = friends.json().get("items", friends.json().get("friends", [])) if friends.status_code == 200 else []
    for f in items:
        pid = f.get("pid")
        rows = requests.get(f"{BASE}/rf/players/{pid}/h2h", headers=h, timeout=20).json().get("items", [])
        for m in rows:
            if not m["won"] and not m["tie"]:
                return pid, m
    pytest.skip("No lost h2h match — seed the fixture first")


# Head to head: items carry picks; profile head_to_head.last carries picks
def test_h2h_items_have_picks(lost):
    _, m = lost
    assert isinstance(m["picks"], list) and m["picks"] and "subject" in m["picks"][0]


def test_profile_last_has_picks(h, lost):
    pid, _ = lost
    p = requests.get(f"{BASE}/rf/players/{pid}", headers=h, timeout=20).json()
    last = p["head_to_head"]["last"]
    assert last and isinstance(last.get("picks"), list) and last["picks"]


# Badla lo: new picks change the label; revenge + single; then cancel (cleanup)
def test_badla_with_new_picks_then_cancel(h, lost):
    pid, m = lost
    new = [{"subject": "Mathematics", "chapter": None}] if m["picks"][0]["subject"] != "Mathematics" else [{"subject": "Physics", "chapter": None}]
    r = requests.post(f"{BASE}/rf/challenges", headers=h, json={"rematch_of": m["id"], "picks": new}, timeout=20)
    assert r.status_code == 200, r.text
    room = r.json()
    try:
        assert room["revenge"] is True and room["single"] is True and room["rematch_of"] == m["id"]
        assert room["picks"] == new and room["label"] == f"Mixed {'Maths' if new[0]['subject'] == 'Mathematics' else 'Physics'}"
        got = requests.get(f"{BASE}/rf/challenges/{room['id']}", headers=h, timeout=20).json()
        assert got["label"] == room["label"] and got["status"] == "open"
    finally:
        c = requests.post(f"{BASE}/rf/challenges/{room['id']}/cancel", headers=h, json={}, timeout=20)
        assert c.status_code == 200 and c.json()["status"] == "cancelled"


# Cup watch-by-code: unknown code is a clean 404 with a message
def test_cup_watch_bad_code(h):
    r = requests.post(f"{BASE}/rf/cups/watch", headers=h, json={"code": "ZZZZZZ"}, timeout=20)
    assert r.status_code == 404 and "No cup has this code" in r.json()["detail"]


# Leagues: friends weekly league + gang war board respond with lists
def test_friends_league(h):
    r = requests.get(f"{BASE}/rf/league/friends", headers=h, timeout=20)
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), dict)


def test_gangwar_board(h):
    r = requests.get(f"{BASE}/rf/league/gangwar", headers=h, timeout=20)
    assert r.status_code == 200, r.text
