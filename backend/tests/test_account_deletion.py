"""Account deletion (account_deletion.py, owner_panel.py, legal_pages.py).

Part A talks to the running preview backend and never deletes anything: page/CSP checks, validation, a wrong PIN on a
number that is not a real Indian mobile (1000000001) and owner-panel access rules.
Part B runs the real routes in-process against a SCRATCH database (<DB_NAME>_deletion_selftest, reused, never dropped)
with throwaway TEST-del-* players; the website PIN check is replaced by a stub, so no real account is touched.
"""
import asyncio
import hashlib
import os
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
load_dotenv(ROOT.parent / "frontend" / ".env")
BASE = (os.environ.get("EXPO_PUBLIC_BACKEND_URL") or "").rstrip("/")

import account_deletion  # noqa: E402
import owner_panel  # noqa: E402


# ---------- Part A: live preview backend, read-only ----------
class TestPublicSurface:
    def test_public_page_has_a_working_form(self):
        r = requests.get(f"{BASE}/api/legal/delete-account", timeout=20)
        assert r.status_code == 200
        html, csp = r.text, r.headers["content-security-policy"]
        for tid in ("public-deletion-form", "public-deletion-phone", "public-deletion-pin", "public-deletion-confirm", "public-deletion-agree", "public-deletion-submit"):
            assert f'data-testid="{tid}"' in html
        assert "script-src 'nonce-" in csp and "connect-src 'self'" in csp and "frame-ancestors 'none'" in csp
        assert "/api/account/delete-request" in html

    def test_privacy_page_stays_script_free(self):
        r = requests.get(f"{BASE}/api/legal/privacy", timeout=20)
        # The edge may add its own bot-check script; our page carries none of its own and no form.
        assert r.status_code == 200 and "<script nonce" not in r.text.lower() and "<form" not in r.text.lower()
        assert "Deleting your account" in r.text

    def test_validation_never_echoes_the_pin(self):
        for body, words in (({"phone": "7004186276", "pin": "12", "confirm": "DELETE"}, "4 digits"),
                            ({"phone": "7004186276", "pin": "9137", "confirm": "nope"}, "DELETE"),
                            ({"phone": "abc", "pin": "9137", "confirm": "DELETE"}, "mobile number")):
            r = requests.post(f"{BASE}/api/account/delete-request", json=body, timeout=20)
            assert r.status_code == 422 and words in r.json()["detail"]
            assert body["pin"] not in r.text

    def test_wrong_pin_deletes_nothing(self):
        r = requests.post(f"{BASE}/api/account/delete-request", json={"phone": "1000000001", "pin": "0000", "confirm": "DELETE"}, timeout=40)
        assert r.status_code in (401, 422, 429), r.text
        if r.status_code == 401:
            assert "Nothing was deleted" in r.json()["detail"]

    def test_status_lookup(self):
        assert requests.get(f"{BASE}/api/account/delete-request/DEL-AAAA-AAAA", timeout=20).status_code == 404
        assert requests.get(f"{BASE}/api/account/delete-request/not-a-code", timeout=20).status_code == 404

    def test_owner_panel_is_closed(self):
        page = requests.get(f"{BASE}/api/owner/deletions", timeout=20)
        assert page.status_code == 200 and 'data-testid="owner-login"' in page.text
        assert "script-src 'nonce-" in page.headers["content-security-policy"] and "noindex" in page.headers["x-robots-tag"]
        assert requests.get(f"{BASE}/api/owner/deletion-requests", timeout=20).status_code == 401
        assert requests.post(f"{BASE}/api/owner/deletion-requests/DEL-AAAA-AAAA/complete", json={}, timeout=20).status_code == 403
        assert requests.post(f"{BASE}/api/owner/deletion-requests/DEL-AAAA-AAAA/complete", json={}, headers={"X-Owner-Panel": "1"}, timeout=20).status_code == 401
        r = requests.get(f"{BASE}/api/owner/deletion-requests", cookies={"jl_owner": secrets.token_urlsafe(32)}, timeout=20)
        assert r.status_code == 401


# ---------- Part B: in-process, scratch database ----------
def run(coro):
    return asyncio.run(coro)


async def scratch():
    from pymongo import AsyncMongoClient
    from fastapi import FastAPI
    client = AsyncMongoClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"] + "_deletion_selftest"]
    await account_deletion.ensure_indexes(db)
    await owner_panel.ensure_indexes(db)
    app = FastAPI()
    app.include_router(account_deletion.make_router(db, lambda: None), prefix="/api")
    app.include_router(owner_panel.make_router(db, lambda: None), prefix="/api")
    http = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="https://test")
    return client, db, http


async def seed(db, uid, rival):
    now = time.time()
    await db.rf_profiles.insert_many([{"uid": uid, "pid": "PDEL" + uid[-6:], "name": "Riya Test", "display_name": "Riya Test", "phone_last4": "4321",
                                       "phone_hash": "h", "friend_code": "DL" + uid[-6:].upper(), "coins": 50, "xp": 300},
                                      {"uid": rival, "pid": "PRIV" + rival[-6:], "name": "Rival Test", "coins": 10, "xp": 10}])
    await db.rf_friends.insert_many([{"uid": uid, "fid": rival, "ts": now}, {"uid": rival, "fid": uid, "ts": now}])
    await db.rf_notices.insert_one({"id": str(uuid.uuid4()), "uid": rival, "from_uid": uid, "kind": "friend_added", "done": False, "ts": now})
    await db.rf_feed.insert_one({"id": f"x:{uid}", "uid": uid, "kind": "level", "data": {"level": 2}, "ts": now})
    duel = {"id": str(uuid.uuid4()), "status": "finished", "mode": "friend", "finished_ts": now, "winner": rival,
            "players": [{"uid": uid, "name": "Riya Test", "avatar": "av_robo", "frame": "frame_gold", "entry": "entry_spark", "score": 3, "ms": 9000},
                        {"uid": rival, "name": "Rival Test", "avatar": "av_galaxy", "score": 5, "ms": 8000}]}
    waiting = {"id": str(uuid.uuid4()), "status": "waiting", "mode": "random", "created_ts": now, "players": [{"uid": uid, "name": "Riya Test", "score": 0, "ms": 0}]}
    await db.rf_duels.insert_many([duel, waiting])
    await db.rf_feed.insert_one({"id": f"duel:{duel['id']}:0", "uid": rival, "kind": "win", "data": {"vs": "Riya Test", "mine": 5, "theirs": 3}, "ts": now})
    await db.rf_sessions.insert_one({"id": str(uuid.uuid4()), "user_id": uid, "request_id": str(uuid.uuid4()), "status": "completed"})
    await db.rf_learning_events.insert_one({"uid": uid, "ref": "solo:x", "exam": "JEE"})
    await db.rf_awards.insert_one({"uid": uid, "ref": "solo:x", "reward": {}})
    await db.rf_dreams.insert_one({"uid": uid, "dreams": []})
    await db.rf_daily_plays.insert_one({"uid": uid, "exam": "JEE", "day": "2026-11-21", "correct": 9})
    await db.rf_night_seats.insert_one({"uid": uid, "day": "2026-11-21", "group": 1})
    await db.mission_links.insert_one({"uid": uid, "code": "M" + uid[-6:].upper()})
    await db.mission_visits.insert_one({"code": "M" + uid[-6:].upper(), "key": "v1", "ts": now})
    gang = {"id": "G" + uid[-8:].upper(), "name": "Test Gang", "leader_uid": uid, "closed": False,
            "members": [{"uid": uid, "ts": 1}, {"uid": rival, "ts": 2}]}
    await db.rf_gangs.insert_one(gang)
    await db.rf_cups.insert_many([{"id": str(uuid.uuid4()), "status": "open", "host_uid": uid, "players": [{"uid": uid, "name": "Riya Test"}], "invites": [rival]},
                                  {"id": str(uuid.uuid4()), "status": "finished", "host_uid": rival, "players": [{"uid": rival, "name": "Rival Test"}, {"uid": uid, "name": "Riya Test", "avatar": "av_robo"}]}])
    await db.rf_challenges.insert_one({"id": str(uuid.uuid4()), "from_uid": uid, "status": "open", "invites": [{"uid": rival, "status": "sent"}]})
    sid = "TESTSID" + uid[-12:]
    await db.jl_jars.insert_one({"sid": sid, "uid": uid, "cookies": {"access_token": "x"}, "seen_at": datetime.now(timezone.utc)})
    token = secrets.token_urlsafe(32)
    from rf_access import token_digest
    await db.rf_access.insert_one({"digest": token_digest(token), "uid": uid, "sid": sid, "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10)})
    return {"duel": duel["id"], "waiting": waiting["id"], "gang": gang["id"], "sid": sid, "token": token}


@pytest.fixture
def stub_website(monkeypatch):
    """The website PIN check, made local: a 4-digit PIN '2580' is right for any TEST-del number."""
    users = {}

    async def check_pin(db, client, request, phone, pin):
        from fastapi import HTTPException
        if pin != "2580" or phone not in users:
            raise HTTPException(401, "Wrong PIN. Nothing was deleted.")
        return users[phone]

    async def end_session(client, cookie):
        return None

    monkeypatch.setattr(account_deletion, "check_pin", check_pin)
    monkeypatch.setattr(account_deletion, "end_session", end_session)
    return users


def test_full_deletion_flow(stub_website):
    async def main():
        client, db, http = await scratch()
        uid, rival = f"TEST-del-{uuid.uuid4().hex[:10]}", f"TEST-del-{uuid.uuid4().hex[:10]}"
        phone = "9" + str(int(time.time() * 1000))[-9:]
        stub_website[phone] = {"id": uid, "name": "Riya Test", "phone": "+91" + phone}
        ids = await seed(db, uid, rival)
        try:
            body = {"phone": phone, "pin": "2580", "confirm": "delete"}
            bad = await http.post("/api/account/delete-request", json={**body, "pin": "1111"})
            assert bad.status_code == 401 and await db.rf_profiles.count_documents({"uid": uid}) == 1
            # Signed in as someone else in the app: refused, nothing erased.
            other = secrets.token_urlsafe(32)
            from rf_access import token_digest
            await db.rf_access.insert_one({"digest": token_digest(other), "uid": rival, "sid": "", "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10)})
            r = await http.post("/api/account/delete-request", json=body, headers={"Authorization": "Bearer " + other})
            assert r.status_code == 403 and await db.rf_profiles.count_documents({"uid": uid}) == 1

            r = await http.post("/api/account/delete-request", json=body, headers={"Authorization": "Bearer " + ids["token"]})
            assert r.status_code == 200, r.text
            receipt = r.json()
            assert receipt["state"] == "owner_pending" and receipt["rapid_fire_erased"] and receipt["website_account"] == "pending"
            assert account_deletion.RID_RE.match(receipt["request_id"]) and uid not in r.text and phone not in r.text
            due = datetime.fromisoformat(receipt["due_at"]) - datetime.fromisoformat(receipt["requested_at"])
            assert due == timedelta(days=30)

            for name, query in (("rf_profiles", {"uid": uid}), ("rf_friends", {"$or": [{"uid": uid}, {"fid": uid}]}), ("rf_notices", {"from_uid": uid}),
                                ("rf_feed", {"uid": uid}), ("rf_sessions", {"user_id": uid}), ("rf_learning_events", {"uid": uid}), ("rf_awards", {"uid": uid}),
                                ("rf_dreams", {"uid": uid}), ("rf_daily_plays", {"uid": uid}), ("rf_night_seats", {"uid": uid}), ("mission_links", {"uid": uid}),
                                ("rf_access", {"uid": uid}), ("jl_jars", {"sid": ids["sid"]})):
                assert await db[name].count_documents(query) == 0, name
            assert await db.mission_visits.count_documents({"code": "M" + uid[-6:].upper()}) == 0
            assert await db.rf_profiles.count_documents({"uid": rival}) == 1  # the other player is untouched

            duel = await db.rf_duels.find_one({"id": ids["duel"]})
            me = next(p for p in duel["players"] if p["uid"] == uid)
            them = next(p for p in duel["players"] if p["uid"] == rival)
            assert me["name"] == "Deleted player" and me["avatar"] is None and me["frame"] is None and me["entry"] is None and me["deleted"] is True
            assert me["score"] == 3 and them["name"] == "Rival Test" and them["avatar"] == "av_galaxy" and duel["winner"] == rival
            assert (await db.rf_duels.find_one({"id": ids["waiting"]}))["status"] == "archived"
            assert (await db.rf_feed.find_one({"id": f"duel:{ids['duel']}:0"}))["data"]["vs"] == "Deleted player"
            gang = await db.rf_gangs.find_one({"id": ids["gang"]})
            assert [m["uid"] for m in gang["members"]] == [rival] and gang["leader_uid"] == rival and not gang["closed"]
            cups = await db.rf_cups.find({"$or": [{"host_uid": uid}, {"players.uid": uid}]}).to_list(5)
            assert {c["status"] for c in cups} == {"cancelled", "finished"}
            finished = next(c for c in cups if c["status"] == "finished")
            assert next(p for p in finished["players"] if p["uid"] == uid)["name"] == "Deleted player"
            assert (await db.rf_challenges.find_one({"from_uid": uid}))["status"] == "expired"

            # Sign-in is refused while the website account waits; a retry returns the same request.
            assert await account_deletion.pending(db, uid)
            again = await http.post("/api/account/delete-request", json=body)
            assert again.status_code == 200 and again.json()["request_id"] == receipt["request_id"]
            assert await db.account_deletions.count_documents({"uid": uid}) == 1
            status = await http.get(f"/api/account/delete-request/{receipt['request_id']}")
            assert status.status_code == 200 and status.json()["state"] == "owner_pending"

            # A late match payout brings a profile row back: the sweep erases it again.
            await db.rf_profiles.insert_one({"uid": uid, "coins": 5})
            await account_deletion.settle_late(db)
            assert await db.rf_profiles.count_documents({"uid": uid}) == 0

            # Owner panel: list shows number + name, completing removes them and allows nothing twice.
            token = secrets.token_urlsafe(32)
            await db.owner_sessions.insert_one({"digest": hashlib.sha256(token.encode()).hexdigest(), "who": "ow***@test", "expires_at": datetime.now(timezone.utc) + timedelta(hours=1)})
            http.cookies.set("jl_owner", token)
            listed = await http.get("/api/owner/deletion-requests")
            row = next(i for i in listed.json()["items"] if i["id"] == receipt["request_id"])
            assert row["phone"] == "91" + phone and row["name"] == "Riya Test" and row["website_user_id"] == uid and row["days_left"] in (29, 30)
            path = f"/api/owner/deletion-requests/{receipt['request_id']}/complete"
            assert (await http.post(path, json={})).status_code == 403  # no X-Owner-Panel header
            done = await http.post(path, json={"note": "deleted on website"}, headers={"X-Owner-Panel": "1"})
            assert done.status_code == 200 and done.json()["state"] == "owner_completed"
            assert (await http.post(path, json={}, headers={"X-Owner-Panel": "1"})).status_code == 409
            stored = await db.account_deletions.find_one({"id": receipt["request_id"]})
            assert "phone" not in stored and "name" not in stored and "active" not in stored and stored["phone_last4"] == phone[-4:]
            assert [h["event"] for h in stored["history"]] == ["requested", "rapid_fire_erased", "website_account_deleted"]
            assert not await account_deletion.pending(db, uid)
            assert (await http.get(f"/api/account/delete-request/{receipt['request_id']}")).json()["website_account"] == "deleted"
        finally:
            await http.aclose()
            await client.close()
    run(main())


def test_pin_reset_cooldown_blocks_deletion(stub_website):
    """Forgot PIN needs no OTP: right after a reset of that number, deletion waits 72 h (nothing erased, PIN not checked)."""
    async def main():
        client, db, http = await scratch()
        uid = f"TEST-del-{uuid.uuid4().hex[:10]}"
        phone = "7" + str(int(time.time() * 1000))[-9:]
        stub_website[phone] = {"id": uid, "name": "", "phone": phone}
        await db.rf_profiles.insert_one({"uid": uid, "name": "Cool Down", "coins": 3})
        await db.pin_resets.insert_one({"phone": hashlib.sha256(phone.encode()).hexdigest(), "ip": "x", "at": datetime.now(timezone.utc) - timedelta(hours=2), "result": "reset"})
        try:
            r = await http.post("/api/account/delete-request", json={"phone": "+91" + phone, "pin": "2580", "confirm": "DELETE"})
            assert r.status_code == 423 and "3 days after a PIN reset" in r.json()["detail"] and "Nothing was deleted" in r.json()["detail"]
            assert await db.rf_profiles.count_documents({"uid": uid}) == 1 and not await account_deletion.pending(db, uid)
            await db.pin_resets.update_one({"phone": hashlib.sha256(phone.encode()).hexdigest()}, {"$set": {"at": datetime.now(timezone.utc) - timedelta(hours=73)}})
            r = await http.post("/api/account/delete-request", json={"phone": phone, "pin": "2580", "confirm": "DELETE"})
            assert r.status_code == 200 and await db.rf_profiles.count_documents({"uid": uid}) == 0
        finally:
            await http.aclose()
            await client.close()
    run(main())


def test_owner_cancel_lets_the_student_back(stub_website):
    async def main():
        client, db, http = await scratch()
        uid = f"TEST-del-{uuid.uuid4().hex[:10]}"
        phone = "8" + str(int(time.time() * 1000))[-9:]
        stub_website[phone] = {"id": uid, "name": "", "phone": phone}
        try:
            r = await http.post("/api/account/delete-request", json={"phone": phone, "pin": "2580", "confirm": "DELETE"})
            assert r.status_code == 200, r.text
            rid = r.json()["request_id"]
            token = secrets.token_urlsafe(32)
            await db.owner_sessions.insert_one({"digest": hashlib.sha256(token.encode()).hexdigest(), "who": "ow***@test", "expires_at": datetime.now(timezone.utc) + timedelta(hours=1)})
            http.cookies.set("jl_owner", token)
            c = await http.post(f"/api/owner/deletion-requests/{rid}/cancel", json={}, headers={"X-Owner-Panel": "1"})
            assert c.status_code == 200 and c.json()["state"] == "cancelled"
            assert not await account_deletion.pending(db, uid)
            done = await http.get("/api/owner/deletion-requests?view=done")
            assert any(i["id"] == rid and i["state"] == "cancelled" for i in done.json()["items"])
        finally:
            await http.aclose()
            await client.close()
    run(main())
