"""Audit June 2026 fixes: rewards never double-paid or lost (DB1-DB3), cookie jars merge per cookie (DB4),
dream colleges kept with the account. Uses only local TEST-* records (removed at the end); nothing reaches the website."""
import asyncio
import hashlib
import os
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import requests
from dotenv import load_dotenv
from pymongo import AsyncMongoClient, MongoClient

load_dotenv("/app/backend/.env")
BASE = "http://localhost:8001/api"
mdb = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
RUN = uuid.uuid4().hex[:8]
UID = f"TEST-audit-{RUN}"


def run(coro_fn):
    async def go():
        client = AsyncMongoClient(os.environ["MONGO_URL"])
        try:
            return await coro_fn(client[os.environ["DB_NAME"]])
        finally:
            await client.close()
    return asyncio.run(go())


def game(db):
    from gamify import make_router
    return make_router(db, lambda u: u)


@pytest.fixture(autouse=True, scope="module")
def cleanup():
    yield
    for name in ("rf_profiles", "rf_awards", "rf_dreams", "rf_feed", "rf_learning_events"):
        mdb[name].delete_many({"uid": {"$regex": f"^TEST-audit-{RUN}"}})
    mdb.rf_cups.delete_many({"id": {"$regex": f"^TEST-audit-{RUN}"}})
    mdb.jl_jars.delete_many({"sid": {"$regex": f"^TEST-audit-{RUN}"}})
    mdb.rf_access.delete_many({"uid": {"$regex": f"^TEST-audit-{RUN}"}})


def test_parallel_matches_and_claims_keep_every_count():
    """DB1: five matches ending together plus a Diamond Rush chest claim: every gem/XP counted, the chest stays claimed once."""
    uid = UID + "-a"

    async def go(db):
        r, award = game(db)
        await award(uid, "solo:warmup", "solo", 3, 10, 10, diamonds={"red": 1})  # today's totals exist, 1 gem
        rush = next(route.endpoint for route in r.routes if route.path == "/rf/rush/claim")
        results = await asyncio.gather(*[award(uid, f"duel:{i}", "duel", 6, 15, 15, won=True, diamonds={"red": 1}) for i in range(5)],
                                       rush({"at": 1}, x_rf_user=uid), return_exceptions=True)
        assert not [x for x in results[:5] if isinstance(x, Exception)]
        p = await db.rf_profiles.find_one({"uid": uid})
        assert p["day_stats"]["gems"] == 6 and p["day_stats"]["correct"] == 33 and p["day_stats"]["wins"] == 5
        assert p["week_stats"]["matches"] == 5 and p["week_stats"]["xp"] == p["xp"]
        assert p["day_stats"]["rush"] == [1]  # claimed once, not erased by the matches
        with pytest.raises(Exception):
            await rush({"at": 1}, x_rf_user=uid)  # cannot be claimed a second time
        assert p["win_run"] == 5
    run(go)


def test_reward_cut_off_by_a_crash_is_finished_once():
    """DB2: the award marker was written, then the server stopped. A later call pays it; further calls never pay again."""
    uid = UID + "-b"

    async def go(db):
        _, award = game(db)
        await db.rf_awards.insert_one({"uid": uid, "ref": "solo:cut", "exam": "JEE", "ts": time.time() - 60})
        first = await award(uid, "solo:cut", "solo", 8, 10, 10)
        assert first and first["coins"] == 16
        again = await award(uid, "solo:cut", "solo", 8, 10, 10)
        assert again == first
        p = await db.rf_profiles.find_one({"uid": uid})
        assert p["coins"] == 16 and p["paid_refs"] == ["solo:cut"]
    run(go)


def test_cup_payout_resumes_after_a_crash_and_pays_once():
    """DB3: a finished cup still marked unpaid (its server stopped) is paid by the sweep, exactly once per player."""
    champ, runner, cid = UID + "-c1", UID + "-c2", f"TEST-audit-{RUN}-cup"

    async def go(db):
        from cups import make_router
        cups = make_router(db, lambda u: u, {"hooks": [], "seat": None, "settle": None})
        players = [{"uid": u, "name": u} for u in (champ, runner, UID + "-c3")]
        await db.rf_cups.insert_one({"id": cid, "status": "finished", "payout": "pending", "finished_ts": time.time() - 120, "champion": champ, "label": "TEST",
                                     "players": players, "prizes": {champ: 110, runner: 30}, "gems": {champ: {"red": 3}}, "rounds": []})
        await cups.resume_payouts()
        await cups.resume_payouts()
        await db.rf_cups.update_one({"id": cid}, {"$set": {"payout": "pending"}})  # as if the first payer died after paying
        await cups.resume_payouts()
        c = await db.rf_profiles.find_one({"uid": champ})
        r = await db.rf_profiles.find_one({"uid": runner})
        assert c["coins"] == 110 and c["diamonds"]["red"] == 3 and c["cups_won"] == 1
        assert r["coins"] == 30 and "cups_won" not in r
        assert "payout" not in await db.rf_cups.find_one({"id": cid})
    run(go)


def test_two_servers_renewing_different_cookies_keep_both():
    """DB4: two answers with different Set-Cookie headers saved at the same moment: neither cookie is lost."""
    import server
    sid = f"TEST-audit-{RUN}-jar"

    async def go(db):
        server.db = db
        await asyncio.gather(server.save_cookie_changes(sid, {"access_token": "A2"}, []), server.save_cookie_changes(sid, {"refresh.token": "R2"}, []))
        jar = await server.load_jar(sid)
        assert jar == {"access_token": "A2", "refresh.token": "R2"}
        await server.save_cookie_changes(sid, {}, ["access_token"])
        assert await server.load_jar(sid) == {"refresh.token": "R2"}
        row = await db.jl_jars.find_one({"sid": sid})
        assert isinstance(row["seen_at"], datetime)
    run(go)


def grant(uid):
    token = secrets.token_urlsafe(24)
    mdb.rf_access.insert_one({"digest": hashlib.sha256(token.encode()).hexdigest(), "uid": uid, "sid": "", "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10)})
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def test_dreams_are_kept_with_the_account():
    uid = UID + "-d"
    h, other = grant(uid), grant(UID + "-e")
    dream = {"id": "jee-12", "exam": "jee", "college": "NIT Test", "branch": "CSE", "need": 180, "range": [170, 195], "note": "CSAB 2 closing 14,859 CRL", "at": 1}
    assert requests.get(f"{BASE}/rf/dream", headers=h, timeout=10).json() == {"dreams": [], "mocks": []}
    assert requests.put(f"{BASE}/rf/dream/dreams", headers=h, json={"dreams": [dream], "base": []}, timeout=10).status_code == 200
    six = [{**dream, "id": f"jee-{i}"} for i in range(6)]
    assert requests.put(f"{BASE}/rf/dream/dreams", headers=h, json={"dreams": six, "base": []}, timeout=10).status_code == 400
    mock = {"id": "m1", "exam": "jee", "score": 120, "max": 300, "raw": 120, "rawMax": 300, "title": "Mock 1", "at": 1000}
    assert requests.post(f"{BASE}/rf/dream/mocks", headers=h, json={"mocks": [mock, {**mock, "id": "m2", "at": 2000}]}, timeout=10).status_code == 200
    assert requests.post(f"{BASE}/rf/dream/mocks", headers=h, json={"mocks": [{**mock, "score": 130}]}, timeout=10).status_code == 200
    got = requests.get(f"{BASE}/rf/dream", headers=h, timeout=10).json()
    assert [d["id"] for d in got["dreams"]] == ["jee-12"]
    assert [(m["id"], m["score"]) for m in got["mocks"]] == [("m2", 120), ("m1", 130)]
    assert requests.get(f"{BASE}/rf/dream", headers=other, timeout=10).json() == {"dreams": [], "mocks": []}  # never another account's
    assert requests.get(f"{BASE}/rf/dream", timeout=10).status_code == 401
