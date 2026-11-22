"""Phase 2 (Levels 1-4) live-preview regression: server.py split must keep every API behaving the same.
Covers: health, /api/jl proxy sign-in, RF access grant, catalog, solo sprints, weak lists, All India daily (TEST player),
boards, Practice Rival bot match, and Server-Timing speed on warm calls. Run with: pytest -n0 (one website login per run)."""
import hashlib
import os
import re
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import requests
from dotenv import dotenv_values
from pymongo import MongoClient

FE = dotenv_values("/app/frontend/.env")
BASE_URL = (FE.get("EXPO_PUBLIC_BACKEND_URL") or os.environ["EXPO_BACKEND_URL"]).rstrip("/")
BE = dotenv_values("/app/backend/.env")
PHONE, PIN = "7004186276", "5524"
SLOW: list = []  # (endpoint, ms) warm calls over 20 ms


def timing(r):
    m = re.search(r"app;dur=([\d.]+)", r.headers.get("Server-Timing", ""))
    return float(m.group(1)) if m else None


def call(s, method, path, warm=False, **kw):
    r = s.request(method, f"{BASE_URL}{path}", timeout=40, **kw)
    t = timing(r)
    if warm and t is not None and t > 20:
        SLOW.append((f"{method} {path.split('?')[0]}", t))
    return r


@pytest.fixture(scope="module")
def mongo():
    c = MongoClient(BE["MONGO_URL"])
    yield c[BE["DB_NAME"]]
    c.close()


@pytest.fixture(scope="module")
def qa():
    """QA learner: website sign-in through the proxy, then Rapid Fire grant."""
    s = requests.Session()
    sid = "qa-p2-" + secrets.token_hex(12)
    r = s.post(f"{BASE_URL}/api/jl/auth/phone", json={"phone": PHONE, "pin": PIN}, headers={"X-JL-Sid": sid}, timeout=40)
    if r.status_code != 200:
        pytest.skip(f"QA sign-in failed {r.status_code}: {r.text[:200]}")
    me = s.get(f"{BASE_URL}/api/jl/auth/me", headers={"X-JL-Sid": sid}, timeout=40)
    g = s.post(f"{BASE_URL}/api/rf/access", json={}, headers={"X-JL-Sid": sid}, timeout=40)
    assert g.status_code == 200, g.text
    tok = g.json()["token"]
    rf = requests.Session()
    rf.headers.update({"Authorization": f"Bearer {tok}"})
    return {"s": s, "sid": sid, "me": me, "rf": rf, "uid": g.json()["user_id"]}


@pytest.fixture(scope="module")
def testp(mongo):
    """Local TEST player grant (hidden from real boards)."""
    tok = secrets.token_urlsafe(32)
    uid = "TEST-p2qa-" + secrets.token_hex(4)
    mongo.rf_access.insert_one({"digest": hashlib.sha256(tok.encode()).hexdigest(), "uid": uid, "sid": "",
                                "expires_at": datetime.now(timezone.utc) + timedelta(hours=1)})
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {tok}"})
    return {"rf": s, "uid": uid}


# --- Health
class TestHealth:
    def test_health(self):
        # /api/health never existed (old server.py had only /health + /api/health/load); public /health is routed by ingress
        r = requests.get(BASE_URL + "/api/health", timeout=20)
        print("/api/health ->", r.status_code)
        r = requests.get(BASE_URL + "/health", timeout=20)
        print("/health ->", r.status_code, r.headers.get("content-type"), r.text[:80])
        r = requests.get("http://127.0.0.1:8001/health", timeout=20)
        assert r.status_code == 200 and r.json().get("status") == "ok"

    def test_health_load(self):
        r = requests.get(BASE_URL + "/api/health/load", timeout=20)
        assert r.status_code == 200 and isinstance(r.json(), dict)


# --- Website proxy /api/jl
class TestProxy:
    def test_me_and_catalog(self, qa):
        assert qa["me"].status_code == 200, qa["me"].text[:200]
        body = qa["me"].json()
        data = body.get("data", body)
        assert data.get("id")
        r = qa["s"].get(f"{BASE_URL}/api/jl/catalog/exams", headers={"X-JL-Sid": qa["sid"]}, timeout=40)
        assert r.status_code == 200, r.text[:200]

    def test_bad_and_missing_sid(self):
        r = requests.get(f"{BASE_URL}/api/jl/auth/me", headers={"X-JL-Sid": "bad sid!"}, timeout=20)
        assert r.status_code == 400, r.status_code
        r = requests.get(f"{BASE_URL}/api/jl/auth/me", timeout=20)
        assert r.status_code == 422, r.status_code

    def test_rf_without_token(self):
        r = requests.get(f"{BASE_URL}/api/rf/history?exam=JEE", timeout=20)
        assert r.status_code in (401, 403), r.status_code


# --- Catalog + solo sprint end-to-end (QA learner)
class TestSprint:
    def test_catalog(self, qa):
        r = call(qa["rf"], "GET", "/api/rf/catalog?exam=JEE")
        assert r.status_code == 200
        assert r.headers.get("X-Cache") in ("HIT-MEMORY", "MISS", "HIT-STALE"), r.headers.get("X-Cache")
        r = call(qa["rf"], "GET", "/api/rf/catalog?exam=JEE", warm=True)
        assert r.status_code == 200 and r.json()

    def test_sprint_flow_and_weak_lists(self, qa, mongo):
        rf = qa["rf"]
        rev0 = call(rf, "GET", "/api/rf/revision?exam=JEE").json()
        wt0 = call(rf, "GET", "/api/rf/weak-topics?exam=JEE").json()
        rid = uuid.uuid4().hex
        body = {"subject": "Physics", "count": 30, "request_id": rid, "exam": "JEE"}
        r = call(rf, "POST", "/api/rf/sessions", json=body, warm=True)
        assert r.status_code == 200, r.text[:300]
        s = r.json()
        ids = [c["id"] for c in s["cards"]]
        assert len(ids) == 30 and len(set(ids)) == 30 and s["seconds_per_card"] == 20
        # solo cards carry the answer key by design (same as old server.py public_card)
        r2 = call(rf, "POST", "/api/rf/sessions", json=body, warm=True)
        assert r2.json()["id"] == s["id"] and [c["id"] for c in r2.json()["cards"]] == ids
        keys = {d["id"]: d["answer"] for d in mongo.rf_cards.find({"id": {"$in": ids}}, {"id": 1, "answer": 1})}
        res = [{"card_id": ids[i], "outcome": "correct", "choice": keys[ids[i]], "ms": 3000} for i in range(3)]
        wrong = ids[3:8]
        res += [{"card_id": c, "outcome": "incorrect", "choice": (keys[c] + 1) % 4, "ms": 4000} for c in wrong]
        c1 = call(rf, "POST", f"/api/rf/sessions/{s['id']}/complete", json={"results": res}, warm=True)
        assert c1.status_code == 200, c1.text[:300]
        j1 = c1.json()
        assert j1["summary"]["correct"] == 3 and j1["summary"]["incorrect"] == 5 and j1["summary"]["total"] == 30
        assert j1["status"] == "completed" and j1["reward"] is not None
        c2 = call(rf, "POST", f"/api/rf/sessions/{s['id']}/complete", json={"results": []}, warm=True)
        assert c2.status_code == 200 and c2.json()["reward"] == j1["reward"], (j1["reward"], c2.json().get("reward"))
        g = call(rf, "GET", f"/api/rf/sessions/{s['id']}", warm=True)
        assert g.status_code == 200 and g.json()["status"] == "completed" and g.json()["reward"] is not None
        h = call(rf, "GET", "/api/rf/history?exam=JEE", warm=True)
        assert h.status_code == 200 and any(i["id"] == s["id"] for i in h.json()["items"])
        # weak lists must count the missed cards right after the round
        rev1 = call(rf, "GET", "/api/rf/revision?exam=JEE", warm=True)
        assert rev1.status_code == 200
        print("QA revision remaining before/after:", rev0.get("remaining"), rev1.json().get("remaining"))
        assert rev1.json()["remaining"] > rev0["remaining"], "revision count did not update after the round"
        wt1 = call(rf, "GET", "/api/rf/weak-topics?exam=JEE", warm=True)
        assert wt1.status_code == 200
        print("QA weak-topics cards before/after:", wt0.get("cards"), wt1.json().get("cards"), len(wt1.json()["topics"]))

    def test_weak_lists_exact_test_player(self, testp, mongo):
        """Fresh TEST player: 0 -> 5 missed after a sprint; replaying them with 2 right clears exactly 2 (incremental marks)."""
        rf = testp["rf"]
        assert call(rf, "GET", "/api/rf/revision?exam=JEE").json()["remaining"] == 0
        assert call(rf, "GET", "/api/rf/weak-topics?exam=JEE").json()["cards"] == 0
        s = call(rf, "POST", "/api/rf/sessions", json={"subject": "Chemistry", "count": 30, "request_id": uuid.uuid4().hex, "exam": "JEE"}).json()
        ids = [c["id"] for c in s["cards"]]
        keys = {d["id"]: d["answer"] for d in mongo.rf_cards.find({"id": {"$in": ids}}, {"id": 1, "answer": 1})}
        wrong = ids[:5]
        res = [{"card_id": c, "outcome": "incorrect", "choice": (keys[c] + 1) % 4, "ms": 3000} for c in wrong]
        assert call(rf, "POST", f"/api/rf/sessions/{s['id']}/complete", json={"results": res}).status_code == 200
        rev = call(rf, "GET", "/api/rf/revision?exam=JEE", warm=True).json()
        assert rev["remaining"] == 5, rev
        wt = call(rf, "GET", "/api/rf/weak-topics?exam=JEE", warm=True).json()
        assert wt["cards"] >= 5 and sum(t["missed"] for t in wt["topics"]) == 5, wt
        r2 = call(rf, "POST", "/api/rf/sessions", json={"subject": "Chemistry", "card_ids": wrong, "count": 5, "request_id": uuid.uuid4().hex, "exam": "JEE"})
        assert r2.status_code == 200 and r2.json()["mode"] == "repeat_missed", r2.text[:200]
        res2 = [{"card_id": c, "outcome": "correct", "choice": keys[c], "ms": 2000} for c in wrong[:2]]
        assert call(rf, "POST", f"/api/rf/sessions/{r2.json()['id']}/complete", json={"results": res2}).status_code == 200
        rev2 = call(rf, "GET", "/api/rf/revision?exam=JEE", warm=True).json()
        assert rev2["remaining"] == 3, rev2
        rs = call(rf, "POST", "/api/rf/sessions", json={"subject": "Chemistry", "count": 30, "request_id": uuid.uuid4().hex, "exam": "JEE", "revision": True})
        assert rs.status_code == 200 and {c["id"] for c in rs.json()["cards"]} <= set(wrong[2:]), rs.text[:200]

    @pytest.mark.parametrize("count", [50, 100])
    def test_pcm_picks(self, qa, count):
        picks = [{"subject": x, "chapter": None} for x in ("Physics", "Chemistry", "Mathematics")]
        r = call(qa["rf"], "POST", "/api/rf/sessions", json={"picks": picks, "count": count, "request_id": uuid.uuid4().hex, "exam": "JEE"}, warm=True)
        assert r.status_code == 200, r.text[:300]
        ids = [c["id"] for c in r.json()["cards"]]
        assert len(ids) == count and len(set(ids)) == count
        assert {c["subject"] for c in r.json()["cards"]} == {"Physics", "Chemistry", "Mathematics"}

    def test_diagram_410(self, qa):
        r = call(qa["rf"], "POST", "/api/rf/sessions", json={"subject": "Physics", "count": 30, "request_id": uuid.uuid4().hex, "exam": "JEE", "diagram_only": True})
        assert r.status_code == 410

    @pytest.mark.parametrize("flag", ["revision", "weak_topics"])
    def test_revision_weak(self, qa, flag):
        r = call(qa["rf"], "POST", "/api/rf/sessions", json={"subject": "Physics", "count": 30, "request_id": uuid.uuid4().hex, "exam": "JEE", flag: True})
        assert r.status_code in (200, 404), r.text[:200]
        if r.status_code == 404:
            assert isinstance(r.json().get("detail"), str)
        else:
            assert r.json()["cards"]


# --- All India daily (TEST player only for play)
class TestDaily:
    def test_daily_status_board_qa(self, qa):
        r = call(qa["rf"], "GET", "/api/rf/daily?exam=JEE")
        assert r.status_code == 200 and r.json()["total"] == 45 and r.json()["seconds"] == 20
        call(qa["rf"], "GET", "/api/rf/daily?exam=JEE", warm=True)
        b = call(qa["rf"], "GET", "/api/rf/daily/board?exam=JEE", warm=True)
        assert b.status_code == 200

    def test_daily_play_test_player(self, testp, mongo):
        rf = testp["rf"]
        st = call(rf, "POST", "/api/rf/daily/start", json={"exam": "JEE"}, warm=True)
        assert st.status_code == 200, st.text[:300]
        j = st.json()
        assert j["status"] == "playing" and j["total"] == 45
        subjects = []
        for _ in range(3):
            subjects.append(j["card"].get("subject"))
            time.sleep(j.get("show_in_ms", 0) / 1000 + 0.2)
            a = call(rf, "POST", "/api/rf/daily/answer", json={"exam": "JEE", "i": j["i"], "choice": 0}, warm=True)
            assert a.status_code == 200, a.text[:200]
            j = a.json()
        assert j["i"] == 3
        f = call(rf, "POST", "/api/rf/daily/finish", json={"exam": "JEE"}, warm=True)
        assert f.status_code == 200 and f.json()["status"] == "done"
        d = call(rf, "GET", "/api/rf/daily?exam=JEE", warm=True).json()
        assert d["you"]["status"] in ("done", "finished") or d["you"].get("rank") is not None, d["you"]
        print("daily first card subjects:", subjects, "you:", d["you"])


# --- Boards
class TestBoards:
    def test_boards(self, qa):
        lb = call(qa["rf"], "GET", "/api/rf/leaderboard?exam=JEE")
        assert lb.status_code == 200 and "rank" in (lb.json().get("you") or {}), str(lb.json())[:200]
        call(qa["rf"], "GET", "/api/rf/leaderboard?exam=JEE", warm=True)
        for p in ("/api/rf/league/gangwar", "/api/rf/league/friends"):
            call(qa["rf"], "GET", p)
            r = call(qa["rf"], "GET", p, warm=True)
            assert r.status_code == 200, (p, r.text[:200])


# --- Practice Rival (bot) match
class TestRival:
    def test_bot_match(self, qa):
        rf = qa["rf"]
        r = call(rf, "POST", "/api/rf/duels", json={"picks": [{"subject": "Physics", "chapter": None}], "mode": "invite", "name": "QA", "count": 30,
                                                   "request_id": uuid.uuid4().hex, "exam": "JEE"}, warm=True)
        assert r.status_code == 200, r.text[:300]
        did = r.json()["id"]
        b = call(rf, "POST", f"/api/rf/duels/{did}/bot", warm=True)
        assert b.status_code == 200, b.text[:300]
        d = b.json()
        wait = d.get("start_at", time.time()) - time.time()
        if wait > 0:
            time.sleep(min(wait + 0.3, 15))
        for i in range(3):
            a = call(rf, "POST", f"/api/rf/duels/{did}/answer", json={"index": i, "choice": 0, "outcome": "answer", "ms": 2000}, warm=True)
            assert a.status_code == 200, a.text[:200]
        g = call(rf, "GET", f"/api/rf/duels/{did}", warm=True)
        assert g.status_code == 200
        f = call(rf, "POST", f"/api/rf/duels/{did}/forfeit")
        assert f.status_code == 200, f.text[:200]


# --- Error handling unchanged after the split
class TestErrors:
    def test_errors(self, qa, testp):
        rf = qa["rf"]
        assert call(rf, "POST", f"/api/rf/sessions/{uuid.uuid4()}/complete", json={"results": []}).status_code == 404
        assert call(rf, "GET", f"/api/rf/sessions/{uuid.uuid4()}").status_code == 404
        assert call(rf, "POST", "/api/rf/sessions", json={"subject": "Physics", "count": 0, "request_id": uuid.uuid4().hex}).status_code == 422
        assert call(rf, "POST", "/api/rf/sessions", json={"subject": "Physics", "request_id": "short"}).status_code == 422
        assert call(rf, "POST", "/api/rf/sessions", json={"subject": "Physics", "request_id": uuid.uuid4().hex, "bogus": 1}).status_code == 422
        # another player's sprint is not visible
        other = call(testp["rf"], "POST", "/api/rf/sessions", json={"subject": "Physics", "count": 30, "request_id": uuid.uuid4().hex, "exam": "JEE"}).json()["id"]
        assert call(rf, "GET", f"/api/rf/sessions/{other}").status_code == 404
        assert requests.get(f"{BASE_URL}/api/jl/auth/me", headers={"X-JL-Sid": "a" * 15}, timeout=20).status_code == 400
        assert requests.get(f"{BASE_URL}/api/jl/auth/me", headers={"X-JL-Sid": "a" * 65}, timeout=20).status_code == 400
        assert requests.get(f"{BASE_URL}/api/rf/history?exam=JEE", headers={"Authorization": "Bearer nope"}, timeout=20).status_code in (401, 403)


def test_zz_speed_report():
    print("WARM CALLS > 20 ms:", SLOW)
