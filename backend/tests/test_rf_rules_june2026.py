"""Rapid Fire rules (June 2026, /app/memory/RAPID_FIRE_RULES.md): 20 s per card, 30/50/100-card rounds,
BITSAT English + Logical Reasoning subjects, unseen cards first. Uses TEST-* players only (conftest swaps in a grant)."""
import os
import uuid

import requests
from pymongo import MongoClient

BASE = os.environ["EXPO_BACKEND_URL"].rstrip("/") + "/api"
db = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
s = requests.Session()


def user():
    return {"X-RF-User": f"TEST-rules-{uuid.uuid4().hex[:10]}"}


def sprint(h, **body):
    return s.post(f"{BASE}/rf/sessions", headers=h, json={"exam": "JEE", "subject": "Physics", "request_id": uuid.uuid4().hex, **body}, timeout=30)


def cleanup(h):
    uid = h["X-RF-User"]
    db.rf_sessions.delete_many({"user_id": uid})
    db.rf_duels.delete_many({"players.uid": uid})
    db.rf_profiles.delete_many({"uid": uid})


def test_catalog_lists_bitsat_subjects():
    r = s.get(f"{BASE}/rf/catalog?exam=JEE", timeout=30)
    assert r.status_code == 200
    names = [x["name"] for x in r.json()["subjects"]]
    assert names == ["Physics", "Chemistry", "Mathematics", "English", "Logical Reasoning"]
    physics = next(x for x in r.json()["subjects"] if x["name"] == "Physics")
    assert any(c["name"] == "Experimental Skills" for c in physics["chapters"])


def test_solo_counts_and_twenty_seconds():
    h = user()
    try:
        for n in (30, 50, 100):
            r = sprint(h, count=n, picks=[{"subject": "Physics", "chapter": None}])
            assert r.status_code == 200, r.text
            body = r.json()
            assert body["seconds_per_card"] == 20
            assert len(body["cards"]) == n == len(body["card_ids"])
            assert len({c["prompt"].strip().lower() for c in body["cards"]}) == n  # no prompt twice in a round
        assert sprint(h, count=101, picks=[{"subject": "Physics", "chapter": None}]).status_code == 422
    finally:
        cleanup(h)


def test_unseen_cards_come_first():
    h = user()
    try:
        chapter = {"subject": "Mathematics", "chapter": "Area under Curves"}
        pool = db.rf_cards.count_documents({"exam": "JEE", "subject": "Mathematics", "chapter": "Area under Curves", "retired": {"$ne": True}})
        assert pool >= 30
        first = set(sprint(h, count=30, picks=[chapter]).json()["card_ids"])
        second = set(sprint(h, count=30, picks=[chapter]).json()["card_ids"])
        # The second round repeats only what the pool could not fill with unseen cards.
        assert len(first & second) <= max(0, 60 - pool)
    finally:
        cleanup(h)


def test_complete_accepts_a_hundred_results():
    h = user()
    try:
        body = sprint(h, count=100, picks=[{"subject": "Chemistry", "chapter": None}]).json()
        results = [{"card_id": c["id"], "outcome": "correct", "choice": c["answer"], "ms": 19000} for c in body["cards"]]
        r = s.post(f"{BASE}/rf/sessions/{body['id']}/complete", headers=h, json={"results": results}, timeout=30)
        assert r.status_code == 200, r.text
        assert r.json()["summary"]["total"] == 100 and r.json()["summary"]["correct"] == 100
    finally:
        cleanup(h)


def test_practice_rival_fifty_cards():
    h = user()
    try:
        d = s.post(f"{BASE}/rf/duels", headers=h, json={"exam": "JEE", "subject": "Physics", "picks": [{"subject": "Physics", "chapter": None}], "mode": "invite",
                                                        "name": "Rules", "count": 50, "request_id": uuid.uuid4().hex}, timeout=30).json()
        r = s.post(f"{BASE}/rf/duels/{d['id']}/bot", headers=h, json={}, timeout=30)
        assert r.status_code == 200, r.text
        v = r.json()
        assert v["total"] == 50 and v["seconds_per_card"] == 20
        assert v["ends_at"] - v["start_at"] == 50 * (20 + 2) + 30
    finally:
        cleanup(h)


def test_small_pick_deals_the_largest_count_that_fits():
    h = user()
    try:
        pick = [{"subject": "Mathematics", "chapter": "Area under Curves"}]
        pool = db.rf_cards.count_documents({"exam": "JEE", "subject": "Mathematics", "chapter": "Area under Curves", "retired": {"$ne": True}})
        d = s.post(f"{BASE}/rf/duels", headers=h, json={"exam": "JEE", "subject": "Mathematics", "picks": pick, "mode": "invite", "name": "Rules", "count": 100,
                                                        "request_id": uuid.uuid4().hex}, timeout=30)
        assert d.status_code == 200, d.text
        expect = 100 if pool >= 100 else 50 if pool >= 50 else 30
        assert d.json()["total"] == expect
    finally:
        cleanup(h)


def test_bitsat_subjects_play_full_rounds():
    """English and Logical Reasoning now have live cards: a 100-card round of each, no prompt twice, 20 s."""
    h = user()
    try:
        for subject in ("English", "Logical Reasoning"):
            r = sprint(h, subject=subject, count=100, picks=[{"subject": subject, "chapter": None}])
            assert r.status_code == 200, r.text
            body = r.json()
            assert body["seconds_per_card"] == 20 and len(body["cards"]) == 100
            assert {c["subject"] for c in body["cards"]} == {subject}
            assert len({c["prompt"].strip().lower() for c in body["cards"]}) == 100
            assert len({c["chapter"] for c in body["cards"]}) >= 10  # every chapter gets its share
        mixed = sprint(h, subject="English", count=50, picks=[{"subject": "English", "chapter": None}, {"subject": "Logical Reasoning", "chapter": None}])
        assert mixed.status_code == 200, mixed.text
        assert {c["subject"] for c in mixed.json()["cards"]} == {"English", "Logical Reasoning"}
    finally:
        cleanup(h)


def test_expanded_bank_is_whole_and_live():
    """Every card file loads, every card has 4 different options and one key, no id twice, and Mongo serves the same numbers."""
    import json
    from collections import Counter
    from pathlib import Path
    files, per = Path(__file__).parent.parent / "rapidfire" / "cards", Counter()
    ids = Counter()
    for f in files.glob("*.json"):
        for c in json.loads(f.read_text()):
            assert len(c["options"]) == 4 and len(set(c["options"])) == 4 and c["answer"] in (0, 1, 2, 3), (f.name, c["id"])
            assert "\\" not in c["prompt"] and "$" not in c["prompt"], (f.name, c["id"])
            ids[c["id"]] += 1
            per[c["subject"]] += 1
    assert not [i for i, n in ids.items() if n > 1]
    assert per["Physics"] >= 2 * 2383 and per["Chemistry"] >= 2 * 1878 and per["Mathematics"] >= 2 * 1894
    assert per["English"] >= 1000 and per["Logical Reasoning"] >= 800
    live = {x["name"]: x["total"] for x in s.get(f"{BASE}/rf/catalog?exam=JEE", timeout=30).json()["subjects"]}
    assert all(live[k] == per[k] for k in live), (live, per)
