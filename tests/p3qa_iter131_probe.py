"""Iteration131 probe (App Health fixes): route privacy, Cup Night late_s, logout trust removal.
Creates a TEST-p3qa grant, an owner session, a scratch jl_jars + rf_trust row; deletes each by exact key afterwards.
Usage: python p3qa_iter131_probe.py [routes|jobs|logout|copies|all]"""
import hashlib
import secrets
import sys
import time
from datetime import datetime, timedelta, timezone

import requests
from dotenv import dotenv_values
from pymongo import MongoClient

BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
BE = dotenv_values("/app/backend/.env")
db = MongoClient(BE["MONGO_URL"])[BE["DB_NAME"]]
what = sys.argv[1] if len(sys.argv) > 1 else "all"
tok, otok = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
uid = "TEST-p3qa-" + secrets.token_hex(4)
dg, odg = hashlib.sha256(tok.encode()).hexdigest(), hashlib.sha256(otok.encode()).hexdigest()
now = datetime.now(timezone.utc)
db.rf_access.insert_one({"digest": dg, "uid": uid, "sid": "", "expires_at": now + timedelta(minutes=5)})
db.owner_sessions.insert_one({"digest": odg, "who": "qa***@test", "expires_at": now + timedelta(minutes=30)})
R = {"pass": 0, "fail": 0}


def check(name, ok, info=""):
    R["pass" if ok else "fail"] += 1
    print(("PASS " if ok else "FAIL ") + name, info)


def data():
    r = requests.get(f"{BASE}/api/owner/health/data", cookies={"jl_owner": otok}, timeout=20)
    assert r.status_code == 200, r.status_code
    return r


try:
    if what in ("routes", "all"):
        code = "QAZWSXED"
        A = {"Authorization": f"Bearer {tok}"}
        st = [requests.get(f"{BASE}/api/rf/friends/code/{code}", headers=A, timeout=20).status_code for _ in range(30)]
        st2 = [requests.get(f"{BASE}/api/rf/friends/code/{code}", timeout=20).status_code for _ in range(30)]
        print("with grant:", set(st), "without grant:", set(st2))
        check("no-grant -> 401", set(st2) == {401})
        p = requests.get(f"{BASE}/api/rf/profile", headers={**A, "X-RF-User": "spoofed-user-123"}, timeout=20)
        check("profile with grant (guard injects player)", p.status_code == 200, p.status_code)
        for _ in range(20):
            requests.post(f"{BASE}/api/rf/duels/{secrets.token_hex(8)}/answer", headers=A, json={"index": 0, "choice": 0, "outcome": "answer", "ms": 900}, timeout=20)
            requests.get(f"{BASE}/api/rf/sessions/{secrets.token_hex(8)}", headers=A, timeout=20)
            requests.get(f"{BASE}/api/jl/auth/me", headers={"X-JL-Sid": "p3qa-" + secrets.token_hex(10)}, timeout=20)
        time.sleep(7)
        d = data()
        routes = [x["route"] for x in d.json()["routes"]]
        print("routes:", routes)
        check("no raw code in data JSON", code not in d.text)
        check("routed pattern {code} present", "/api/rf/friends/code/{code}" in routes)
        check("guard-rejected folded {id} present", "/api/rf/friends/code/{id}" in routes)
        check("duel answer pattern", any(r.startswith("/api/rf/duels/{") and r.endswith("}/answer") for r in routes))
        check("sessions pattern", any(r.startswith("/api/rf/sessions/{") for r in routes))
        check("/api/jl/auth/me kept", "/api/jl/auth/me" in routes)
        raw = [n for n in db.rf_health_nodes.find({}) if any(code in k for k in (n.get("routes") or {}))]
        check("no raw code in any rf_health_nodes doc (all routes, not just top 15)", not raw)
        anyhex = [k for n in db.rf_health_nodes.find({}) for k in (n.get("routes") or {}) if any(len(p) >= 12 and not p.startswith("{") for p in k.split("/"))]
        print("suspicious long path parts:", anyhex[:10])
    if what in ("jobs", "all"):
        for i in range(7):
            j = {x["id"]: x for x in data().json()["jobs"]}
            c = j.get("cup_night_tick", {})
            print(i, {k: (v["label"], v["last_s_ago"], v["late_s"], v["ok"]) for k, v in j.items()})
            check(f"sample {i} cup_night late_s<=6", c.get("late_s", 99) <= 6, c)
            time.sleep(2)
        labels = {x["id"]: x["label"] for x in data().json()["jobs"]}
        check("labels", labels.get("warm_up") == "Warm-up after start" and labels.get("sweep") == "Closing old matches", labels)
    if what in ("copies", "all"):
        cs = data().json()["copies"]
        print("copies:", cs)
        check("copies length 1", len(cs) == 1, len(cs))
    if what in ("logout", "all"):
        sid = "p3qa-" + secrets.token_hex(12)
        key = hashlib.sha256(("sid:" + sid).encode()).hexdigest()
        db.jl_jars.insert_one({"sid": sid, "cookies": {}, "uid": uid, "seen_at": now})
        db.rf_trust.insert_one({"_id": key, "uid": uid, "verified_at": now, "until": now + timedelta(minutes=10)})
        try:
            r = requests.post(f"{BASE}/api/jl/auth/logout", headers={"X-JL-Sid": sid}, json={}, timeout=30)
            print("logout:", r.status_code, r.text[:160])
            gone_t, gone_j = db.rf_trust.count_documents({"_id": key}) == 0, db.jl_jars.count_documents({"sid": sid}) == 0
            if 200 <= r.status_code < 300:
                check("logout 2xx removes rf_trust + jl_jars", gone_t and gone_j, (gone_t, gone_j))
            else:
                check("logout non-2xx keeps rows (branch not taken)", not gone_t and not gone_j, (r.status_code, gone_t, gone_j))
        finally:
            print("scratch cleanup", db.rf_trust.delete_many({"_id": key}).deleted_count, db.jl_jars.delete_many({"sid": sid}).deleted_count)
finally:
    print("cleanup", db.rf_access.delete_many({"digest": dg}).deleted_count, db.owner_sessions.delete_many({"digest": odg}).deleted_count,
          db.rf_profiles.delete_many({"uid": uid}).deleted_count, db.rf_profiles.delete_many({"_id": uid}).deleted_count)
    print("RESULT", R)
