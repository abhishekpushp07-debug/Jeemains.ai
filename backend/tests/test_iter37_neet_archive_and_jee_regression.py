# Iteration 37: NEET archive preservation/guards + JEE-only regression (Rapid Fire APIs).
import hashlib
import json
import os
import time
import uuid
import zipfile
from pathlib import Path

import pytest
import requests
from pymongo import MongoClient
from dotenv import load_dotenv


load_dotenv("/app/backend/.env")
load_dotenv("/app/frontend/.env")
BASE_URL = (os.environ.get("EXPO_BACKEND_URL") or os.environ["EXPO_PUBLIC_BACKEND_URL"]).rstrip("/")
API = f"{BASE_URL}/api/rf"
DB = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
BASELINE = json.loads(Path("/app/test_reports/iter37_archive_baseline.json").read_text())


def hdr(uid: str):
    return {"X-RF-User": uid, "Content-Type": "application/json"}


def rid(prefix: str = "TEST37"):
    return f"{prefix}-{uuid.uuid4().hex[:16]}"


def _doc_hash(doc: dict) -> str:
    blob = json.dumps(doc, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()


def _fingerprint(col: str, query: dict, projection: dict | None = None, sort_field: str | None = None):
    cur = DB[col].find(query, projection or {"_id": 0})
    if sort_field:
        cur = cur.sort(sort_field, 1)
    docs = list(cur)
    per = sorted(_doc_hash(d) for d in docs)
    joined = "".join(per)
    return len(docs), hashlib.sha256(joined.encode()).hexdigest()


@pytest.fixture(scope="module")
def run_ctx():
    users = {
        "solo": f"TEST37-{uuid.uuid4().hex[:18]}",
        "duel_a": f"TEST37A-{uuid.uuid4().hex[:18]}",
        "duel_b": f"TEST37B-{uuid.uuid4().hex[:18]}",
        "cancel": f"TEST37C-{uuid.uuid4().hex[:18]}",
    }
    created = {"sessions": [], "duels": [], "users": users}
    yield created
    DB.rf_learning_events.delete_many({"uid": {"$in": list(users.values())}})
    DB.rf_awards.delete_many({"uid": {"$in": list(users.values())}})
    DB.rf_sessions.delete_many({"id": {"$in": created["sessions"]}})
    DB.rf_duels.delete_many({"id": {"$in": created["duels"]}})
    DB.rf_profiles.delete_many({"uid": {"$in": list(users.values())}})


@pytest.fixture(scope="module")
def archived_refs():
    sess = DB.rf_sessions.find_one({"exam": "NEET"}, {"_id": 0, "id": 1, "user_id": 1, "request_id": 1, "subject": 1})
    duel = DB.rf_duels.find_one({"exam": "NEET", "players.0.uid": {"$exists": True}}, {"_id": 0, "id": 1, "code": 1, "subject": 1, "players": 1})
    if not sess or not duel:
        pytest.skip("Archived NEET fixtures unavailable in DB; cannot validate runtime archive guards.")
    return {
        "session": sess,
        "duel": {
            "id": duel["id"],
            "code": duel.get("code"),
            "subject": duel.get("subject", "Physics"),
            "owner_uid": duel["players"][0]["uid"],
        },
    }


# Preservation checks: exact archived NEET counts/hashes + ZIP immutability.
class TestArchivePreservation:
    def test_exact_archive_fingerprints_match_baseline(self):
        mapping = {
            "rf_cards": "rf_cards",
            "rf_sessions": "rf_sessions",
            "rf_duels": "rf_duels",
            "rf_awards": "rf_awards",
            "rf_learning_events": "rf_learning_events",
        }
        for key, col in mapping.items():
            count, digest = _fingerprint(col, {"exam": "NEET"}, {"_id": 0})
            assert count == BASELINE["collections"][key]["count"], f"{col} count drifted"
            assert digest == BASELINE["collections"][key]["sha256"], f"{col} hash drifted"

        pcount, pdigest = _fingerprint(
            "rf_profiles",
            {"exam_stats.NEET": {"$exists": True}},
            {"_id": 0, "uid": 1, "exam_stats.NEET": 1},
            sort_field="uid",
        )
        rows = list(DB.rf_profiles.find({"exam_stats.NEET": {"$exists": True}}, {"_id": 0, "uid": 1, "exam_stats.NEET": 1}).sort("uid", 1))
        pdigest = hashlib.sha256(json.dumps(rows, sort_keys=True, default=str).encode()).hexdigest()
        assert pcount == BASELINE["neet_profile_segments"]["count"]
        assert pdigest == BASELINE["neet_profile_segments"]["sha256"]

    def test_neet_zip_bytes_and_hash_unchanged(self):
        zip_path = Path(BASELINE["zip"]["path"])
        payload = zip_path.read_bytes()
        assert len(payload) == BASELINE["zip"]["bytes"]
        assert hashlib.sha256(payload).hexdigest() == BASELINE["zip"]["sha256"]
        with zipfile.ZipFile(zip_path, "r") as zf:
            assert zf.testzip() is None


# JEE-only public boundary checks and legacy Biology implicit behavior.
class TestJeeOnlyBoundary:
    def test_new_archived_play_cannot_create_records(self):
        uid = rid()
        for exam, subject in [("NEET", "Physics"), (None, "Biology")]:
            body = {"subject": subject, "request_id": rid()}
            if exam:
                body["exam"] = exam
            solo = requests.post(f"{API}/sessions", headers=hdr(uid), json=body, timeout=30)
            duel = requests.post(f"{API}/duels", headers=hdr(uid), json={**body, "mode": "invite", "name": "TEST37_ARCHIVE"}, timeout=30)
            assert solo.status_code == duel.status_code == 410
        assert DB.rf_sessions.count_documents({"user_id": uid}) == 0
        assert DB.rf_duels.count_documents({"players.uid": uid}) == 0
        assert DB.rf_profiles.count_documents({"uid": uid}) == 0

    def test_catalog_default_is_jee_only_with_expected_totals(self):
        r = requests.get(f"{API}/catalog", timeout=30)
        assert r.status_code == 200
        data = r.json()
        names = [s["name"] for s in data["subjects"]]
        totals = {s["name"]: s["total"] for s in data["subjects"]}
        assert data["exam"] == "JEE"
        assert names == ["Physics", "Chemistry", "Mathematics"]
        assert sum(totals.values()) == 7045

    def test_explicit_neet_catalog_returns_410_archived(self):
        r = requests.get(f"{API}/catalog", params={"exam": "NEET"}, timeout=30)
        assert r.status_code == 410

    def test_cards_without_exam_do_not_leak_biology_or_neet(self):
        r = requests.get(f"{API}/cards", params={"page": 1, "limit": 200}, timeout=30)
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 7045
        subjects = {item["subject"] for item in body["items"]}
        assert "Biology" not in subjects

    def test_implicit_legacy_biology_request_rejected(self):
        r = requests.get(f"{API}/cards", params={"subject": "Biology"}, timeout=30)
        assert r.status_code == 410

    def test_history_duels_revision_leaderboard_reject_neet_exam(self):
        uid = f"TEST37-READ-{uuid.uuid4().hex[:16]}"
        for route in ("history", "duels", "revision", "leaderboard"):
            r = requests.get(f"{API}/{route}", headers=hdr(uid), params={"exam": "NEET"}, timeout=30)
            assert r.status_code == 410


# Archive runtime guards must reject old NEET session/duel access before mutation side effects.
class TestArchiveRuntimeGuards:
    def test_default_history_hides_archived_activity(self, archived_refs):
        uid = archived_refs["session"]["user_id"]
        for route in ("history", "duels"):
            response = requests.get(f"{API}/{route}", headers=hdr(uid), timeout=30)
            assert response.status_code == 200
            assert all(item["exam"] == "JEE" for item in response.json()["items"])

    def test_old_request_id_replay_to_jee_is_blocked(self, archived_refs):
        s = archived_refs["session"]
        before = DB.rf_sessions.find_one({"id": s["id"]}, {"_id": 0})
        r = requests.post(
            f"{API}/sessions",
            headers=hdr(s["user_id"]),
            json={"exam": "JEE", "subject": "Physics", "request_id": s["request_id"]},
            timeout=30,
        )
        assert r.status_code == 410
        after = DB.rf_sessions.find_one({"id": s["id"]}, {"_id": 0})
        assert _doc_hash(before) == _doc_hash(after)

    def test_old_neet_session_get_and_complete_are_blocked(self, archived_refs):
        s = archived_refs["session"]
        before = DB.rf_sessions.find_one({"id": s["id"]}, {"_id": 0})
        g = requests.get(f"{API}/sessions/{s['id']}", headers=hdr(s["user_id"]), timeout=30)
        c = requests.post(f"{API}/sessions/{s['id']}/complete", headers=hdr(s["user_id"]), json={"results": []}, timeout=30)
        assert g.status_code == 410
        assert c.status_code == 410
        after = DB.rf_sessions.find_one({"id": s["id"]}, {"_id": 0})
        assert _doc_hash(before) == _doc_hash(after)

    def test_old_neet_duel_get_answer_cancel_forfeit_bot_blocked(self, archived_refs):
        d = archived_refs["duel"]
        did, uid = d["id"], d["owner_uid"]
        before = DB.rf_duels.find_one({"id": did}, {"_id": 0})
        calls = [
            requests.get(f"{API}/duels/{did}", headers=hdr(uid), timeout=30),
            requests.post(f"{API}/duels/{did}/answer", headers=hdr(uid), json={"index": 0, "choice": 0, "outcome": "answer", "ms": 1}, timeout=30),
            requests.post(f"{API}/duels/{did}/cancel", headers=hdr(uid), json={}, timeout=30),
            requests.post(f"{API}/duels/{did}/forfeit", headers=hdr(uid), json={}, timeout=30),
            requests.post(f"{API}/duels/{did}/bot", headers=hdr(uid), json={}, timeout=30),
        ]
        assert all(r.status_code == 410 for r in calls)
        after = DB.rf_duels.find_one({"id": did}, {"_id": 0})
        assert _doc_hash(before) == _doc_hash(after)

    def test_old_neet_invite_join_code_blocked(self, archived_refs):
        code = archived_refs["duel"]["code"]
        assert code
        r = requests.post(
            f"{API}/duels/join",
            headers=hdr(f"TEST37JOIN-{uuid.uuid4().hex[:16]}"),
            json={"code": code, "name": "TEST37_JOIN", "exam": "JEE"},
            timeout=30,
        )
        assert r.status_code == 410

    def test_old_neet_duel_websocket_refused(self, archived_refs):
        ws = pytest.importorskip("websocket")
        d = archived_refs["duel"]
        uid = d["owner_uid"]
        ws_base = BASE_URL.replace("https://", "wss://").replace("http://", "ws://")
        url = f"{ws_base}/api/rf/duels/{d['id']}/ws?u={uid}"
        conn = ws.create_connection(url, timeout=5)
        try:
            closed = False
            try:
                msg = conn.recv()
                closed = (msg in (None, ""))
            except Exception:
                closed = True
            assert closed
        finally:
            conn.close()


# JEE regression using transient TEST37 users only; cleanup handled by fixture.
class TestJeeRegression:
    def test_solo_create_complete_history_revision_and_idempotent_reward(self, run_ctx):
        uid = run_ctx["users"]["solo"]
        created = requests.post(
            f"{API}/sessions",
            headers=hdr(uid),
            json={"exam": "JEE", "subject": "Physics", "count": 30, "request_id": rid()},
            timeout=30,
        )
        assert created.status_code == 200
        sess = created.json()
        run_ctx["sessions"].append(sess["id"])
        assert sess["exam"] == "JEE"
        assert len(sess["cards"]) == 30

        results = [{"card_id": c["id"], "outcome": "skipped", "choice": None, "ms": 0} for c in sess["cards"]]
        c1 = requests.post(f"{API}/sessions/{sess['id']}/complete", headers=hdr(uid), json={"results": results}, timeout=30)
        c2 = requests.post(f"{API}/sessions/{sess['id']}/complete", headers=hdr(uid), json={"results": results}, timeout=30)
        assert c1.status_code == c2.status_code == 200
        assert c1.json()["reward"] == c2.json()["reward"]

        hist = requests.get(f"{API}/history", headers=hdr(uid), params={"exam": "JEE"}, timeout=30)
        rev = requests.get(f"{API}/revision", headers=hdr(uid), params={"exam": "JEE"}, timeout=30)
        board = requests.get(f"{API}/leaderboard", headers=hdr(uid), params={"exam": "JEE"}, timeout=30)
        assert hist.status_code == rev.status_code == board.status_code == 200
        assert hist.json()["totals"]["sessions"] >= 1
        assert rev.json()["exam"] == "JEE"
        assert board.json()["exam"] == "JEE"

    def test_duel_invite_join_get_answer_and_waiting_cancel(self, run_ctx):
        a = run_ctx["users"]["duel_a"]
        b = run_ctx["users"]["duel_b"]

        created = requests.post(
            f"{API}/duels",
            headers=hdr(a),
            json={"exam": "JEE", "subject": "Physics", "mode": "invite", "name": "TEST37_A", "request_id": rid()},
            timeout=30,
        )
        assert created.status_code == 200
        d = created.json()
        run_ctx["duels"].append(d["id"])

        joined = requests.post(
            f"{API}/duels/join",
            headers=hdr(b),
            json={"code": d["code"], "name": "TEST37_B", "exam": "JEE"},
            timeout=30,
        )
        assert joined.status_code == 200

        # Wait briefly for countdown to unlock answers.
        for _ in range(16):
            g = requests.get(f"{API}/duels/{d['id']}", headers=hdr(a), timeout=30)
            assert g.status_code == 200
            body = g.json()
            if body.get("status") == "ready" and body.get("start_at", 0) <= body.get("server_now", 0):
                break
            time.sleep(0.5)

        ans = requests.post(
            f"{API}/duels/{d['id']}/answer",
            headers=hdr(a),
            json={"index": 0, "choice": 0, "outcome": "answer", "ms": 1},
            timeout=30,
        )
        assert ans.status_code == 200, "JEE answer should save once the countdown has elapsed"

        # Feasible cancel flow on a separate waiting invite.
        c_uid = run_ctx["users"]["cancel"]
        c = requests.post(
            f"{API}/duels",
            headers=hdr(c_uid),
            json={"exam": "JEE", "subject": "Chemistry", "mode": "invite", "name": "TEST37_C", "request_id": rid()},
            timeout=30,
        )
        assert c.status_code == 200
        run_ctx["duels"].append(c.json()["id"])
        cancelled = requests.post(f"{API}/duels/{c.json()['id']}/cancel", headers=hdr(c_uid), json={}, timeout=30)
        assert cancelled.status_code == 200


def test_final_archive_and_zip_still_match_after_all_requests():
    checks = TestArchivePreservation()
    checks.test_exact_archive_fingerprints_match_baseline()
    checks.test_neet_zip_bytes_and_hash_unchanged()
