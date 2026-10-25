# Iteration 30: exam-scoped catalog/cards, leaderboard isolation, duels exam separation, revision idempotency, diagram cards, and NEET portability artifacts.
import json
import os
import time
import uuid
import zipfile
from pathlib import Path

import pytest
import requests
from pymongo import MongoClient


BASE = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
API = f"{BASE}/api/rf"
DB = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]


def uid(prefix="qa30"):
    return f"{prefix}-{uuid.uuid4().hex[:20]}"


def rid():
    return f"rf30-{uuid.uuid4().hex[:16]}"


def h(user_id: str):
    return {"X-RF-User": user_id, "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def ctx():
    users = {
        "lb_je": uid("qa30je"),
        "lb_ne": uid("qa30ne"),
        "rev": uid("qa30rev"),
        "a": uid("qa30a"),
        "b": uid("qa30b"),
        "other": uid("qa30other"),
    }
    refs = []
    sessions = []
    duels = []
    yield {"users": users, "refs": refs, "sessions": sessions, "duels": duels}
    DB.rf_learning_events.delete_many({"uid": {"$in": list(users.values())}})
    DB.rf_awards.delete_many({"uid": {"$in": list(users.values())}})
    DB.rf_sessions.delete_many({"user_id": {"$in": list(users.values())}})
    DB.rf_duels.delete_many({"players.uid": {"$in": list(users.values())}})
    DB.rf_profiles.delete_many({"uid": {"$in": list(users.values())}})


# Catalog and public card scope assertions.
class TestCatalogAndCards:
    def test_exam_scoped_catalog_and_legacy_pool(self):
        neet = requests.get(f"{API}/catalog", params={"exam": "NEET"}, timeout=30)
        jee = requests.get(f"{API}/catalog", params={"exam": "JEE"}, timeout=30)
        legacy = requests.get(f"{API}/catalog", timeout=30)
        assert neet.status_code == jee.status_code == legacy.status_code == 200

        neet_s = [s["name"] for s in neet.json()["subjects"]]
        jee_s = [s["name"] for s in jee.json()["subjects"]]
        legacy_s = [s["name"] for s in legacy.json()["subjects"]]
        assert neet_s == ["Physics", "Chemistry", "Biology"]
        assert jee_s == ["Physics", "Chemistry", "Mathematics"]
        assert legacy_s == ["Physics", "Chemistry", "Mathematics", "Biology"]

    def test_neet_public_cards_and_diagrams_count(self):
        first = requests.get(f"{API}/cards", params={"exam": "NEET", "page": 1, "limit": 200}, timeout=30)
        assert first.status_code == 200
        body = first.json()
        assert body["total"] == 7585
        items = list(body["items"])
        for page in range(2, body["pages"] + 1):
            r = requests.get(f"{API}/cards", params={"exam": "NEET", "page": page, "limit": 200}, timeout=30)
            assert r.status_code == 200
            items.extend(r.json()["items"])
        diagram_ids = [c["id"] for c in items if c.get("diagram")]
        assert len(diagram_ids) == 18
        assert all(c.get("answer") is None and c.get("explain") is None for c in items)

    def test_invalid_exam_subject_combinations_rejected(self):
        u = uid("qa30combo")
        r1 = requests.post(f"{API}/sessions", headers=h(u), json={"exam": "JEE", "subject": "Biology", "request_id": rid()}, timeout=30)
        r2 = requests.post(f"{API}/sessions", headers=h(u), json={"exam": "NEET", "subject": "Mathematics", "request_id": rid()}, timeout=30)
        assert r1.status_code == 422
        assert r2.status_code == 422


# Leaderboard exam isolation, invalidation, and idempotent completion checks.
class TestLeaderboardIsolation:
    def test_exam_xp_isolated_and_award_idempotent(self, ctx):
        je_uid = ctx["users"]["lb_je"]
        ne_uid = ctx["users"]["lb_ne"]

        # JEE Physics session for user A
        s1 = requests.post(
            f"{API}/sessions",
            headers=h(je_uid),
            json={"exam": "JEE", "subject": "Physics", "count": 5, "request_id": rid()},
            timeout=30,
        )
        assert s1.status_code == 200
        sess_je = s1.json()
        ctx["sessions"].append(sess_je["id"])
        results_je = [{"card_id": c["id"], "outcome": "correct", "choice": c["answer"], "ms": 3000} for c in sess_je["cards"]]

        pre_je_neet = requests.get(f"{API}/leaderboard", headers=h(je_uid), params={"exam": "NEET"}, timeout=30).json()["you"]["xp"]
        c1 = requests.post(f"{API}/sessions/{sess_je['id']}/complete", headers=h(je_uid), json={"results": results_je}, timeout=30)
        c1b = requests.post(f"{API}/sessions/{sess_je['id']}/complete", headers=h(je_uid), json={"results": results_je}, timeout=30)
        assert c1.status_code == c1b.status_code == 200
        assert c1.json()["reward"]["xp"] == c1b.json()["reward"]["xp"]

        je_board = requests.get(f"{API}/leaderboard", headers=h(je_uid), params={"exam": "JEE"}, timeout=30).json()
        ne_board = requests.get(f"{API}/leaderboard", headers=h(je_uid), params={"exam": "NEET"}, timeout=30).json()
        assert je_board["you"]["xp"] > 0
        assert ne_board["you"]["xp"] == pre_je_neet

        # NEET Physics session for user B
        s2 = requests.post(
            f"{API}/sessions",
            headers=h(ne_uid),
            json={"exam": "NEET", "subject": "Physics", "count": 5, "request_id": rid()},
            timeout=30,
        )
        assert s2.status_code == 200
        sess_ne = s2.json()
        ctx["sessions"].append(sess_ne["id"])
        results_ne = [{"card_id": c["id"], "outcome": "correct", "choice": c["answer"], "ms": 3000} for c in sess_ne["cards"]]
        c2 = requests.post(f"{API}/sessions/{sess_ne['id']}/complete", headers=h(ne_uid), json={"results": results_ne}, timeout=30)
        assert c2.status_code == 200

        ne_own = requests.get(f"{API}/leaderboard", headers=h(ne_uid), params={"exam": "NEET"}, timeout=30).json()["you"]["xp"]
        je_own = requests.get(f"{API}/leaderboard", headers=h(ne_uid), params={"exam": "JEE"}, timeout=30).json()["you"]["xp"]
        assert ne_own > 0
        assert je_own == 0

    def test_rank_tie_break_by_uid(self, ctx):
        u1 = uid("qa30ranka")
        u2 = uid("qa30rankb")
        # direct profile setup to create deterministic tie without polluting many sessions
        DB.rf_profiles.update_one({"uid": u1}, {"$set": {"uid": u1, "name": "qa30-rank-a", "exam_stats": {"JEE": {"xp": 120, "wins": 0}}}}, upsert=True)
        DB.rf_profiles.update_one({"uid": u2}, {"$set": {"uid": u2, "name": "qa30-rank-b", "exam_stats": {"JEE": {"xp": 120, "wins": 0}}}}, upsert=True)

        b1 = requests.get(f"{API}/leaderboard", headers=h(u1), params={"exam": "JEE"}, timeout=30)
        b2 = requests.get(f"{API}/leaderboard", headers=h(u2), params={"exam": "JEE"}, timeout=30)
        assert b1.status_code == b2.status_code == 200
        r1, r2 = b1.json()["you"]["rank"], b2.json()["you"]["rank"]
        assert r1 is not None and r2 is not None
        assert (r1 < r2) if (u1 < u2) else (r2 < r1)

        DB.rf_profiles.delete_many({"uid": {"$in": [u1, u2]}})


# Duel exam isolation: invite mismatch 409 and matched exam join succeeds.
class TestDuelsExamScoped:
    def test_invite_exam_mismatch_then_match(self, ctx):
        a = ctx["users"]["a"]
        b = ctx["users"]["b"]
        created = requests.post(
            f"{API}/duels",
            headers=h(a),
            json={"exam": "JEE", "subject": "Physics", "mode": "invite", "name": "qa30a", "request_id": rid()},
            timeout=30,
        )
        assert created.status_code == 200
        duel = created.json()
        ctx["duels"].append(duel["id"])
        code = duel["code"]

        bad = requests.post(f"{API}/duels/join", headers=h(b), json={"code": code, "name": "qa30b", "exam": "NEET"}, timeout=30)
        assert bad.status_code == 409

        ok = requests.post(f"{API}/duels/join", headers=h(b), json={"code": code, "name": "qa30b", "exam": "JEE"}, timeout=30)
        assert ok.status_code == 200
        body = ok.json()
        assert body["exam"] == "JEE"
        assert body["status"] in ("ready", "waiting")

        # finish quickly via forfeits so history can include this duel
        requests.post(f"{API}/duels/{duel['id']}/forfeit", headers=h(a), timeout=30)
        requests.post(f"{API}/duels/{duel['id']}/forfeit", headers=h(b), timeout=30)
        for _ in range(6):
            g = requests.get(f"{API}/duels/{duel['id']}", headers=h(a), timeout=30)
            if g.status_code == 200 and g.json().get("status") == "finished":
                break
            time.sleep(0.8)
        hist = requests.get(f"{API}/duels", headers=h(a), params={"exam": "JEE"}, timeout=30)
        assert hist.status_code == 200
        assert any(item["id"] == duel["id"] and item["exam"] == "JEE" for item in hist.json()["items"])


# Revision flow: misses/timed-out included, skip excluded, correct clears, idempotent complete.
class TestRevision:
    def test_revision_rank_and_clear(self, ctx):
        u = ctx["users"]["rev"]
        other = ctx["users"]["other"]

        s = requests.post(
            f"{API}/sessions",
            headers=h(u),
            json={"exam": "NEET", "subject": "Biology", "chapter": "Human Reproduction", "count": 4, "request_id": rid()},
            timeout=30,
        )
        assert s.status_code == 200
        data = s.json()
        ctx["sessions"].append(data["id"])
        cards = data["cards"]
        results = [
            {"card_id": cards[0]["id"], "outcome": "incorrect", "choice": (cards[0]["answer"] + 1) % 4, "ms": 9000},
            {"card_id": cards[1]["id"], "outcome": "timed_out", "choice": None, "ms": 20000},
            {"card_id": cards[2]["id"], "outcome": "correct", "choice": cards[2]["answer"], "ms": 5000},
            {"card_id": cards[3]["id"], "outcome": "skipped", "choice": None, "ms": 0},
        ]
        done = requests.post(f"{API}/sessions/{data['id']}/complete", headers=h(u), json={"results": results}, timeout=30)
        assert done.status_code == 200

        rev = requests.get(f"{API}/revision", headers=h(u), params={"exam": "NEET"}, timeout=30)
        assert rev.status_code == 200
        items = rev.json()["items"]
        row = next((x for x in items if x["subject"] == "Biology" and x["chapter"] == "Human Reproduction"), None)
        assert row is not None
        assert row["remaining"] >= 2

        # other uid cannot see this learner's revision
        rev_other = requests.get(f"{API}/revision", headers=h(other), params={"exam": "NEET"}, timeout=30)
        assert rev_other.status_code == 200
        assert all(not (x["subject"] == "Biology" and x["chapter"] == "Human Reproduction") for x in rev_other.json()["items"])

        rs = requests.post(
            f"{API}/sessions",
            headers=h(u),
            json={"exam": "NEET", "subject": "Biology", "chapter": "Human Reproduction", "revision": True, "count": 30, "request_id": rid()},
            timeout=30,
        )
        assert rs.status_code == 200
        rev_sess = rs.json()
        ctx["sessions"].append(rev_sess["id"])
        assert rev_sess["mode"] == "weak_revision"
        assert len(rev_sess["cards"]) <= 30

        clear_results = [{"card_id": c["id"], "outcome": "correct", "choice": c["answer"], "ms": 4000} for c in rev_sess["cards"]]
        c1 = requests.post(f"{API}/sessions/{rev_sess['id']}/complete", headers=h(u), json={"results": clear_results}, timeout=30)
        c2 = requests.post(f"{API}/sessions/{rev_sess['id']}/complete", headers=h(u), json={"results": clear_results}, timeout=30)
        assert c1.status_code == c2.status_code == 200

        rev2 = requests.get(f"{API}/revision", headers=h(u), params={"exam": "NEET"}, timeout=30).json()
        row2 = next((x for x in rev2["items"] if x["subject"] == "Biology" and x["chapter"] == "Human Reproduction"), None)
        assert (row2 is None) or (row2["remaining"] < row["remaining"])


# Diagram card behavior and NEET-only constraints.
class TestDiagramCards:
    def test_neet_biology_diagram_only_returns_18(self, ctx):
        u = ctx["users"]["other"]
        s = requests.post(
            f"{API}/sessions",
            headers=h(u),
            json={"exam": "NEET", "subject": "Biology", "diagram_only": True, "request_id": rid()},
            timeout=30,
        )
        assert s.status_code == 200
        data = s.json()
        assert data["mode"] == "diagrams"
        assert len(data["cards"]) == 18
        kinds = {c.get("diagram", {}).get("kind") for c in data["cards"]}
        assert kinds == {"heart", "nephron", "flower"}
        for c in data["cards"]:
            assert len(c["options"]) == 4
            assert 0 <= c["answer"] <= 3
            assert c.get("explain")
            assert c.get("diagram", {}).get("target")

    def test_diagram_only_rejects_other_exam_subjects(self):
        u = uid("qa30diagrej")
        r1 = requests.post(f"{API}/sessions", headers=h(u), json={"exam": "JEE", "subject": "Biology", "diagram_only": True, "request_id": rid()}, timeout=30)
        r2 = requests.post(f"{API}/sessions", headers=h(u), json={"exam": "NEET", "subject": "Physics", "diagram_only": True, "request_id": rid()}, timeout=30)
        assert r1.status_code == 422
        assert r2.status_code == 422


# NEET portability artifacts and default bundle hygiene.
class TestNeetPortability:
    def test_source_folder_live_and_bundle_hygiene(self):
        root = Path(__file__).resolve().parents[2] / "neetlive"
        assert (root / "content" / "cards").exists()
        manifest = root / "manifest.json"
        bundle = root / "exports" / "neetlive-content.zip"
        assert manifest.exists()
        assert bundle.exists()

        m = json.loads(manifest.read_text())
        assert m["exam"] == "NEET"
        assert m["card_count"] == 7585
        assert m["subjects"] == {"Physics": 2610, "Chemistry": 2095, "Biology": 2880}
        assert m["diagram_cards"] == 18

        with zipfile.ZipFile(bundle, "r") as z:
            names = [n.lower() for n in z.namelist()]
        forbidden = (".env", "cookie", "learner", "auth", "token", "rf_sessions", "rf_duels", "rf_awards", "rf_learning_events")
        assert not any(any(f in n for f in forbidden) for n in names)