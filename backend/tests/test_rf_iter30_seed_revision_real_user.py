# Iteration 30 helper: seed deterministic NEET Biology misses for the real pilot user to validate arena revision CTA.
import os
import uuid

import requests
import pytest

pytestmark = pytest.mark.skipif(os.environ.get("RF_SEED_PILOT") != "1", reason="Pilot UI fixture requires explicit RF_SEED_PILOT=1; never mutate pilot history in ordinary regression runs.")


API = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/") + "/api/rf"
UID = "db0c62b8-eeaf-41be-b8b1-05f5f34ac1d8"


def test_seed_revision_for_real_user():
    req = "rf30-seed-" + uuid.uuid4().hex[:12]
    s = requests.post(
        f"{API}/sessions",
        headers={"X-RF-User": UID, "Content-Type": "application/json"},
        json={"exam": "NEET", "subject": "Biology", "chapter": "Human Reproduction", "count": 3, "request_id": req},
        timeout=30,
    )
    assert s.status_code == 200, s.text
    cards = s.json()["cards"]
    body = {
        "results": [
            {"card_id": cards[0]["id"], "outcome": "incorrect", "choice": (cards[0]["answer"] + 1) % 4, "ms": 12000},
            {"card_id": cards[1]["id"], "outcome": "timed_out", "choice": None, "ms": 20000},
            {"card_id": cards[2]["id"], "outcome": "skipped", "choice": None, "ms": 0},
        ]
    }
    c = requests.post(
        f"{API}/sessions/{s.json()['id']}/complete",
        headers={"X-RF-User": UID, "Content-Type": "application/json"},
        json=body,
        timeout=30,
    )
    assert c.status_code == 200, c.text

    rev = requests.get(f"{API}/revision", headers={"X-RF-User": UID}, params={"exam": "NEET"}, timeout=30)
    assert rev.status_code == 200
    assert any(x["subject"] == "Biology" for x in rev.json()["items"])


def test_clear_seeded_revision_for_real_user():
    req = "rf30-clear-" + uuid.uuid4().hex[:12]
    s = requests.post(
        f"{API}/sessions",
        headers={"X-RF-User": UID, "Content-Type": "application/json"},
        json={"exam": "NEET", "subject": "Biology", "chapter": "Human Reproduction", "revision": True, "count": 30, "request_id": req},
        timeout=30,
    )
    if s.status_code == 404:
        return
    assert s.status_code == 200, s.text
    data = s.json()
    results = [{"card_id": c["id"], "outcome": "correct", "choice": c["answer"], "ms": 4000} for c in data["cards"]]
    c = requests.post(
        f"{API}/sessions/{data['id']}/complete",
        headers={"X-RF-User": UID, "Content-Type": "application/json"},
        json={"results": results},
        timeout=30,
    )
    assert c.status_code == 200, c.text