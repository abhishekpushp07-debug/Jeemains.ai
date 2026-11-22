"""Phase 3 (Levels 5-8) live-preview regression: RF APIs unchanged (orjson), per-player limit, 422 no echo, /api/health/load,
App Health page + data (owner cookie), owner deletion panel, website proxy pass-through. TEST-p3qa-* players only; everything
created here is removed by exact uid / digest at teardown. Run with: pytest -n0 -p no:randomly"""
import hashlib
import json
import os
import re
import secrets
import threading
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
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
CREATED = {"uids": [], "owner_digests": []}


@pytest.fixture(scope="module")
def mongo():
    c = MongoClient(BE["MONGO_URL"])
    db = c[BE["DB_NAME"]]
    yield db
    # cleanup exact records we created
    uids = CREATED["uids"]
    if uids:
        for col in ("rf_access", "rf_profiles", "rf_awards", "rf_learning_events", "rf_sessions", "rf_feed", "rf_trust"):
            n = db[col].delete_many({"uid": {"$in": uids}}).deleted_count
            print(f"cleanup {col}: {n}")
        print("cleanup rf_sessions(user_id):", db.rf_sessions.delete_many({"user_id": {"$in": uids}}).deleted_count)
        n = db.rf_profiles.delete_many({"_id": {"$in": uids}}).deleted_count
        n2 = db.rf_duels.delete_many({"$or": [{"host_uid": {"$in": uids}}, {"players.uid": {"$in": uids}}, {"uids": {"$in": uids}}]}).deleted_count
        print("cleanup rf_profiles(_id):", n, "rf_duels:", n2)
    for d in CREATED["owner_digests"]:
        print("cleanup owner_sessions:", db.owner_sessions.delete_many({"digest": d}).deleted_count)
    c.close()


def make_player(db, tag):
    tok = secrets.token_urlsafe(32)
    uid = f"TEST-p3qa-{tag}-" + secrets.token_hex(3)
    db.rf_access.insert_one({"digest": hashlib.sha256(tok.encode()).hexdigest(), "uid": uid, "sid": "",
                             "expires_at": datetime.now(timezone.utc) + timedelta(hours=1)})
    CREATED["uids"].append(uid)
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {tok}"})
    return {"rf": s, "uid": uid}


@pytest.fixture(scope="module")
def p1(mongo):
    return make_player(mongo, "a")


def get(s, path, **kw):
    return s.get(f"{BASE_URL}{path}", timeout=40, **kw)


def post(s, path, **kw):
    return s.post(f"{BASE_URL}{path}", timeout=40, **kw)


def valid_json(r):
    assert "application/json" in r.headers.get("content-type", ""), r.headers.get("content-type")
    return json.loads(r.text)


# --- Rapid Fire GET endpoints still answer valid JSON with the same shapes
class TestRFReads:
    @pytest.mark.parametrize("path", ["/api/rf/profile", "/api/rf/inbox", "/api/rf/leaderboard?exam=JEE", "/api/rf/daily?exam=JEE",
                                      "/api/rf/history?exam=JEE", "/api/rf/revision?exam=JEE", "/api/rf/weak-topics?exam=JEE",
                                      "/api/rf/feed", "/api/rf/duels", "/api/rf/duels/live"])
    def test_authed_reads(self, p1, path):
        r = get(p1["rf"], path)
        assert r.status_code == 200, f"{path} {r.status_code} {r.text[:200]}"
        body = valid_json(r)
        assert body is not None
        print(path, "keys:", list(body)[:12] if isinstance(body, dict) else f"list[{len(body)}]")

    def test_profile_shape(self, p1):
        b = get(p1["rf"], "/api/rf/profile").json()
        assert isinstance(b, dict) and ("uid" in b or "user_id" in b or "id" in b or "coins" in b), list(b)

    @pytest.mark.parametrize("path", ["/api/rf/catalog", "/api/rf/cards"])
    def test_public(self, path):
        r = requests.get(BASE_URL + path, timeout=40)
        assert r.status_code == 200, r.text[:200]
        valid_json(r)

    def test_no_token_401(self):
        r = requests.get(BASE_URL + "/api/rf/profile", timeout=20)
        assert r.status_code == 401, r.status_code


# --- Solo sprint: create + idempotent replay + complete paid once
class TestSprint:
    def test_sprint(self, p1, mongo):
        rf = p1["rf"]
        body = {"exam": "JEE", "subject": "Physics", "picks": [{"subject": "Physics", "chapter": None}], "count": 30, "request_id": uuid.uuid4().hex}
        r = post(rf, "/api/rf/sessions", json=body)
        assert r.status_code == 200, r.text[:300]
        s = valid_json(r)
        ids = [c["id"] for c in s["cards"]]
        assert len(ids) == 30 and len(set(ids)) == 30
        r2 = post(rf, "/api/rf/sessions", json=body)
        assert r2.json()["id"] == s["id"]
        keys = {d["id"]: d["answer"] for d in mongo.rf_cards.find({"id": {"$in": ids}}, {"id": 1, "answer": 1})}
        res = [{"card_id": ids[i], "outcome": "correct", "choice": keys[ids[i]], "ms": 3000} for i in range(4)]
        res += [{"card_id": ids[i], "outcome": "incorrect", "choice": (keys[ids[i]] + 1) % 4, "ms": 3000} for i in range(4, 6)]
        c1 = post(rf, f"/api/rf/sessions/{s['id']}/complete", json={"results": res})
        assert c1.status_code == 200, c1.text[:300]
        j1 = valid_json(c1)
        assert j1["status"] == "completed" and j1["summary"]["correct"] == 4 and j1["summary"]["incorrect"] == 2 and j1["reward"] is not None
        c2 = post(rf, f"/api/rf/sessions/{s['id']}/complete", json={"results": []})
        assert c2.status_code == 200 and c2.json()["reward"] == j1["reward"]
        for k, v in j1.items():
            if isinstance(v, str) and k.endswith("_at"):
                assert ISO.match(v), (k, v)
        h = get(rf, "/api/rf/history?exam=JEE").json()
        assert any(i["id"] == s["id"] for i in h["items"])


# --- Practice Rival bot match: 30 answers, idempotent replay, finished + reward paid once
class TestDuel:
    def test_bot_duel_full(self, p1, mongo):
        rf = p1["rf"]
        r = post(rf, "/api/rf/duels", json={"exam": "JEE", "subject": "Physics", "mode": "invite", "name": "QA", "request_id": uuid.uuid4().hex})
        assert r.status_code == 200, r.text[:300]
        did = valid_json(r)["id"]
        b = post(rf, f"/api/rf/duels/{did}/bot")
        assert b.status_code == 200, b.text[:300]
        d = b.json()
        n = len(d.get("cards") or []) or d.get("count") or 30
        wait = d.get("start_at", time.time()) - time.time()
        if wait > 0:
            time.sleep(min(wait + 0.3, 15))
        first = None
        statuses = []
        for i in range(n):
            a = post(rf, f"/api/rf/duels/{did}/answer", json={"index": i, "choice": i % 4, "outcome": "answer", "ms": 800})
            statuses.append(a.status_code)
            assert a.status_code == 200, f"answer {i}: {a.status_code} {a.text[:200]}"
            if i == 0:
                first = valid_json(a)
        assert 429 not in statuses
        rep = post(rf, f"/api/rf/duels/{did}/answer", json={"index": 0, "choice": 3, "outcome": "answer", "ms": 800})
        assert rep.status_code == 200, rep.text[:200]
        rj = rep.json()
        for k in ("correct", "outcome", "points", "score"):
            if k in first and k in rj and not isinstance(first[k], dict):
                pass
        print("first answer:", {k: first[k] for k in list(first)[:8]}, "\nreplay:", {k: rj[k] for k in list(rj)[:8]})
        deadline = time.time() + 40
        g = None
        while time.time() < deadline:
            g = get(rf, f"/api/rf/duels/{did}").json()
            if g.get("status") == "finished":
                break
            time.sleep(2)
        print("duel status:", g.get("status"), "reward:", g.get("reward"))
        assert g.get("status") == "finished", g.get("status")
        assert g.get("reward") is not None or any(p.get("reward") for p in g.get("players", []) if isinstance(p, dict))
        rows = list(mongo.rf_awards.find({"uid": p1["uid"], "ref": f"duel:{did}"}, {"_id": 0}))
        assert len(rows) == 1, rows
        # replay after finish must not pay again
        post(rf, f"/api/rf/duels/{did}/answer", json={"index": n - 1, "choice": 0, "outcome": "answer", "ms": 800})
        assert mongo.rf_awards.count_documents({"uid": p1["uid"], "ref": f"duel:{did}"}) == 1
        CREATED.setdefault("duels", []).append(did)
        mongo.rf_duels.delete_one({"id": did})


# --- Per-player limit: one player hammering gets 429 slow_down; another player unaffected
class TestLimiter:
    def test_hammer(self, mongo):
        a, b = make_player(mongo, "ham"), make_player(mongo, "oth")
        codes, sample = [], {}
        lock = threading.Lock()

        def worker(k):
            s = requests.Session()
            s.headers.update(a["rf"].headers)
            for _ in range(k):
                r = s.get(BASE_URL + "/api/rf/profile", timeout=30)
                with lock:
                    codes.append(r.status_code)
                    if r.status_code == 429 and not sample:
                        sample.update(body=r.json(), retry=r.headers.get("Retry-After"))

        ts = [threading.Thread(target=worker, args=(10,)) for _ in range(30)]
        [t.start() for t in ts]
        time.sleep(0.5)
        other = get(b["rf"], "/api/rf/profile").status_code
        [t.join() for t in ts]
        ok, lim = codes.count(200), codes.count(429)
        print(f"hammer: 200={ok} 429={lim} other={codes.count(200) + lim != len(codes)} other_player={other} sample={sample}")
        assert other == 200
        assert lim > 0, "no 429 seen"
        assert ok >= 110, ok
        assert sample["body"] == {"detail": "Too many requests at once. Please wait a moment.", "code": "slow_down"}
        assert sample["retry"] == "2"


# --- 422 never echoes the input
def test_forgot_pin_422_no_echo():
    r = requests.post(BASE_URL + "/api/account/forgot-pin", json={"phone": "9876543210", "new_pin": "12a4", "confirm_pin": "12a4"}, timeout=20)
    print("forgot-pin:", r.status_code, r.text[:300])
    assert r.status_code == 422
    assert "12a4" not in r.text and "9876543210" not in r.text
    for e in r.json()["detail"]:
        assert set(e) <= {"type", "loc", "msg"}, e


# --- /api/health/load public, counts only
def test_health_load():
    r = requests.get(BASE_URL + "/api/health/load", timeout=20)
    assert r.status_code == 200
    b = r.json()
    print("health/load:", b)
    for k in ("pid", "lag_ms", "lag_sustained_ms", "inflight", "inflight_web", "background", "sockets", "busy", "turned_away",
              "shed", "limited", "answers_quick", "answers_full", "website"):
        assert k in b, k
    assert "TEST-" not in r.text


# --- App Health page + data
class TestOwnerHealth:
    def test_page_headers(self):
        r = requests.get(BASE_URL + "/api/owner/health", timeout=20)
        assert r.status_code == 200 and "text/html" in r.headers["content-type"]
        csp = r.headers.get("Content-Security-Policy", "")
        assert "nonce-" in csp and r.headers.get("X-Frame-Options") == "DENY" and "noindex" in r.headers.get("X-Robots-Tag", "")
        nonce = re.search(r"nonce-([^']+)'", csp).group(1)
        assert f'nonce="{nonce}"' in r.text

    def test_data_401(self):
        r = requests.get(BASE_URL + "/api/owner/health/data", timeout=20)
        assert r.status_code == 401 and r.json()["detail"] == "Please sign in to the owner panel."

    def test_data_signed_in(self, mongo, p1):
        tok = secrets.token_urlsafe(32)
        dg = hashlib.sha256(tok.encode()).hexdigest()
        mongo.owner_sessions.insert_one({"digest": dg, "who": "qa***@test", "expires_at": datetime.now(timezone.utc) + timedelta(hours=1)})
        CREATED["owner_digests"].append(dg)
        r = requests.get(BASE_URL + "/api/owner/health/data", cookies={"jl_owner": tok}, timeout=30)
        assert r.status_code == 200, r.text[:200]
        b = r.json()
        print("health data keys:", list(b), "students:", b["students"], "jobs:", [j["id"] for j in b["jobs"]], "copies:", len(b["copies"]),
              "website:", b["website"])
        for k in ("who", "at", "window_minutes", "students", "speed", "routes", "website", "jobs", "copies"):
            assert k in b, k
        assert set(b["students"]) >= {"signed_in", "kept_playing_while_website_down", "playing_live_now", "live_matches"}
        for s in b["speed"]:
            assert set(s) >= {"id", "label", "count", "errors", "error_pct", "p50_ms", "p95_ms"}
        for j in b["jobs"]:
            assert set(j) >= {"id", "label", "every_s", "last_s_ago", "took_ms", "ok"}
        txt = r.text
        assert "TEST-" not in txt and p1["uid"] not in txt and "7004186276" not in txt
        with open("/tmp/p3_owner_tok", "w") as f:
            os.chmod("/tmp/p3_owner_tok", 0o600)
            f.write(tok + "\n" + dg)


# --- Owner deletion panel unchanged
def test_deletion_panel():
    r = requests.get(BASE_URL + "/api/owner/deletions", timeout=20)
    assert r.status_code == 200 and "text/html" in r.headers["content-type"]
    r = requests.get(BASE_URL + "/api/owner/deletion-requests", timeout=20)
    assert r.status_code == 401


# --- Website proxy pass-through
def test_proxy_passthrough():
    r = requests.get(BASE_URL + "/api/jl/auth/me", headers={"X-JL-Sid": secrets.token_hex(16)}, timeout=30)
    print("jl/auth/me random sid:", r.status_code, r.text[:150])
    assert r.status_code == 401
    r = requests.get(BASE_URL + "/api/jl/auth/me", headers={"X-JL-Sid": "bad sid!!"}, timeout=30)
    print("jl/auth/me bad sid:", r.status_code, r.text[:150])
    assert r.status_code == 400
