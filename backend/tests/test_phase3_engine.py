"""Phase 3 (Levels 5-7): speed engine, live engine, shields and eyes.

- fast_json: orjson answers are the same JSON as FastAPI's old path (dates, int keys, models, sets, huge ints).
- website shield: opens after a burst of website failures, answers at once while shut, lets ONE probe through, closes on
  success, stays shut twice as long on a failed probe; a call the caller abandoned says nothing.
- canonical_request goes through the shield: while shut, nothing is sent to the website.
- Rapid Fire keeps playing while the website is down: a session the website verified earlier gets a grant; a session it
  never verified, a 401 from the website, or an old trust do not.
- limits per player (429 after the burst), background looks wait only when the process is packed.
- redaction: PINs, passwords, tokens, cookies and phone numbers never reach a log line; a 422 never echoes the input.
- rewards: the same match paid from 8 places at once pays once.
- card bank: a file another copy already wrote is not written again (this copy only drops its cached bank).
- App Health data: counts and timings only.

Scratch database only (`<DB_NAME>_phase3_selftest`); nothing live is touched.
Run:  cd /app/backend && python -m pytest tests/test_phase3_engine.py -q
"""
import asyncio
import json
import logging
import os
import shutil
import tempfile
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import aiohttp
import httpx
import pytest
from dotenv import load_dotenv
from fastapi import FastAPI
from multidict import CIMultiDict
from pydantic import BaseModel
from pymongo import AsyncMongoClient

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

import card_bank  # noqa: E402
import health_panel  # noqa: E402
import health_stats  # noqa: E402
import jl_transport  # noqa: E402
import load_guard  # noqa: E402
import log_redact  # noqa: E402
import rf_access  # noqa: E402
import website_shield  # noqa: E402
from database import Collections  # noqa: E402
from fast_json import dumps  # noqa: E402
from fastapi.encoders import jsonable_encoder  # noqa: E402
from gamify import make_router as make_gamify  # noqa: E402
from rf_access import rf_user  # noqa: E402

SCRATCH = os.environ["DB_NAME"] + "_phase3_selftest"


def run(coro):
    return asyncio.run(coro)


def scratch():
    client = AsyncMongoClient(os.environ["MONGO_URL"])
    return client, Collections(client[SCRATCH])


# ---------- Level 5: fast JSON ----------
class Item(BaseModel):
    name: str
    at: datetime


def test_fast_json_is_the_same_json_as_before():
    now = datetime(2026, 6, 1, 10, 30, 5, 123456, tzinfo=timezone.utc)
    samples = [
        {"a": 1, "b": [1, 2.5, None, True], "c": {"d": "é ✓ \u20b9"}, "e": (1, 2)},
        {1: "int key", 2.5: "float key", "nested": {3: [now]}},
        {"model": Item(name="x", at=now), "set": {3}, "when": now, "naive": datetime(2026, 1, 1, 8, 0)},
        {"huge": 2 ** 70, "neg": -1},
        [{"id": str(uuid.uuid4()), "cards": [{"prompt": "x" * 50, "options": ["1", "2"]}] * 30}],
    ]
    for value in samples:
        old = json.loads(json.dumps(jsonable_encoder(value), ensure_ascii=False, separators=(",", ":")))
        assert json.loads(dumps(value)) == old, value


# ---------- Level 7: website shield ----------
def fresh_shield(monkeypatch):
    s = website_shield.Shield()
    monkeypatch.setattr(jl_transport, "shield", s)
    return s


def test_shield_opens_refuses_probes_and_closes(monkeypatch):
    s = fresh_shield(monkeypatch)
    for _ in range(5):
        assert s.allow() is False
        s.record(True, False, 0.05)
    for _ in range(website_shield.MIN_FAILS - 1):
        s.record(False, s.allow(), 0.05)
    assert s.state == "closed"  # 7 failed of 12: not yet enough failures
    s.record(False, s.allow(), 0.05)
    assert s.state == "open" and s.opened == 1
    with pytest.raises(website_shield.WebsiteDown) as down:
        s.allow()
    assert 1 <= down.value.retry_after <= website_shield.OPEN_FIRST
    s.open_until = time.monotonic() - 0.01  # its pause is over
    assert s.allow() is True  # the probe
    with pytest.raises(website_shield.WebsiteDown):
        s.allow()  # only one probe at a time
    s.record(False, True, 0.05)  # the probe failed: shut again, twice as long
    assert s.state == "open" and s.open_for == 2 * website_shield.OPEN_FIRST
    s.open_until = time.monotonic() - 0.01
    probe = s.allow()
    s.record(None, probe, 0.0)  # the caller went away: says nothing about the website
    assert s.state == "half" and not s.probing
    s.record(True, s.allow(), 0.05)
    assert s.state == "closed" and s.open_for == website_shield.OPEN_FIRST
    snap = s.snapshot()
    assert snap["state"] == "closed" and snap["failed"] >= 9 and snap["refused"] >= 2


def test_mostly_working_website_never_opens(monkeypatch):
    s = fresh_shield(monkeypatch)
    for k in range(200):
        s.record(k % 4 != 0, s.allow(), 0.05)  # 25% failures (one student's bad calls, a flaky picture)
    assert s.state == "closed"


class FakeResponse:
    def __init__(self, status, body=b"{}"):
        self.status, self.headers, self.body = status, CIMultiDict({"content-type": "application/json"}), body

    async def read(self):
        return self.body

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class FakeWebsite:
    """Stands in for the aiohttp session: `mode` is "down" (connection refused), "slow", "520" or a (status, body)."""
    def __init__(self, mode="down"):
        self.mode, self.calls = mode, 0

    def request(self, method, url, **kw):
        self.calls += 1
        if self.mode == "down":
            raise aiohttp.ClientConnectionError("refused")
        if self.mode == "520":
            return FakeResponse(520, b"<html>origin</html>")
        status, body = self.mode
        return FakeResponse(status, json.dumps(body).encode())


def test_canonical_request_stops_calling_a_down_website(monkeypatch):
    s = fresh_shield(monkeypatch)
    site = FakeWebsite("520")

    async def main():
        for _ in range(website_shield.MIN_FAILS):
            r = await jl_transport.canonical_request(site, "POST", "https://x/attempts/a/answers/q", path="attempts/a/answers/q", params=None, body=b"{}", headers={})
            assert r.status_code == 520
        sent = site.calls
        for _ in range(50):
            with pytest.raises(jl_transport.UpstreamError):  # WebsiteDown is an UpstreamError: every caller handles it
                await jl_transport.canonical_request(site, "GET", "https://x/papers", path="papers", params=None, body=None, headers={})
        return sent
    sent = run(main())
    assert site.calls == sent, "nothing is sent to the website while the shield is shut"
    assert s.state == "open"


# ---------- Rapid Fire keeps playing while the website is down ----------
def access_app(db, site):
    app = FastAPI()
    app.include_router(rf_access.make_access_router(db, lambda: site))
    return app


def test_trusted_session_keeps_rapid_fire_playing_while_the_website_is_down(monkeypatch):
    fresh_shield(monkeypatch)

    async def main():
        client, db = scratch()
        uid, sid, other = f"TEST-p3-{uuid.uuid4().hex[:8]}", uuid.uuid4().hex, uuid.uuid4().hex
        site = FakeWebsite("down")
        try:
            await db.jl_jars.insert_one({"sid": sid, "cookies": {"access_token": "cookie-" + sid}})
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=access_app(db, site)), base_url="http://t") as c:
                h = {"X-JL-Sid": sid}
                r = await c.post("/rf/access", json={}, headers=h)
                assert r.status_code == 503, "never verified: no grant while the website is down"
                site.mode = (200, {"data": {"id": uid, "name": "Test Player"}, "meta": {"api_version": "1"}})
                r = await c.post("/rf/access", json={}, headers=h)
                assert r.status_code == 200 and r.json()["user_id"] == uid
                trust = await db.rf_trust.find_one({"_id": rf_access.trust_key(sid, "cookie-" + sid)})
                assert trust["uid"] == uid and trust["until"].replace(tzinfo=timezone.utc) > datetime.now(timezone.utc) + timedelta(hours=5)
                site.mode = "down"
                r = await c.post("/rf/access", json={}, headers=h)
                assert r.status_code == 200 and r.json()["user_id"] == uid, r.text
                grant = await db.rf_access.find_one({"digest": rf_access.token_digest(r.json()["token"])})
                assert grant["trusted"] is True and grant["uid"] == uid
                site.mode = "520"
                assert (await c.post("/rf/access", json={}, headers=h)).status_code == 200  # its error page counts as down too
                site.mode = (401, {"error": {"message": "expired"}})
                assert (await c.post("/rf/access", json={}, headers=h)).status_code == 401, "the website said no: no grant"
                await db.rf_trust.update_one({"_id": trust["_id"]}, {"$set": {"until": datetime.now(timezone.utc) - timedelta(seconds=1)}})
                site.mode = "down"
                assert (await c.post("/rf/access", json={}, headers=h)).status_code == 503, "an old trust is not used"
                # Another device handle never borrows this trust.
                await db.jl_jars.insert_one({"sid": other, "cookies": {"access_token": "cookie-" + sid}})
                assert (await c.post("/rf/access", json={}, headers={"X-JL-Sid": other})).status_code == 503
        finally:
            await db.jl_jars.delete_many({"sid": {"$in": [sid, other]}})
            await db.rf_trust.delete_many({"uid": uid})
            await db.rf_access.delete_many({"uid": uid})
            await client.close()
    run(main())


# ---------- limits per player, crowd order ----------
def test_player_limit_allows_a_phone_and_stops_a_script(monkeypatch):
    monkeypatch.setattr(load_guard, "_buckets", load_guard.OrderedDict())
    uid = "TEST-p3-limit"
    allowed = sum(load_guard.player_allowed(uid) for _ in range(500))  # 500 calls in the same instant
    assert load_guard.PLAYER_BURST - 2 <= allowed <= load_guard.PLAYER_BURST + 2
    assert all(load_guard.player_allowed("TEST-p3-other") for _ in range(30)), "another player is never affected"
    b = load_guard._buckets[uid]
    b[1] -= 1.0  # one second later: RATE more calls
    assert sum(load_guard.player_allowed(uid) for _ in range(100)) in range(int(load_guard.PLAYER_RATE) - 1, int(load_guard.PLAYER_RATE) + 2)


def test_background_looks_wait_only_when_the_process_is_packed(monkeypatch):
    for path in ("/api/rf/leaderboard", "/api/rf/duels/live", "/api/rf/feed", "/api/rf/players/PF1234567", "/api/rf/players/PF1234567/h2h", "/api/rf/duels"):
        assert load_guard.background_look("GET", path), path
    for method, path in (("POST", "/api/rf/duels/x/answer"), ("GET", "/api/rf/duels/abc-123"), ("POST", "/api/rf/duels"), ("GET", "/api/rf/inbox"), ("GET", "/api/rf/profile")):
        assert not load_guard.background_look(method, path), path
    monkeypatch.setattr(load_guard.load, "background", 100)
    monkeypatch.setattr(load_guard, "busy", lambda: False)
    assert not load_guard.shed_background()
    monkeypatch.setattr(load_guard, "busy", lambda: True)
    assert load_guard.shed_background()
    monkeypatch.setattr(load_guard.load, "background", 0)
    assert not load_guard.shed_background()


def test_website_calls_do_not_make_rapid_fire_busy(monkeypatch):
    monkeypatch.setattr(load_guard.load, "sustained", 0.0)
    monkeypatch.setattr(load_guard.load, "inflight", load_guard.INFLIGHT_LIMIT + 2000)
    monkeypatch.setattr(load_guard.load, "inflight_web", 2000)
    assert not load_guard.busy()
    monkeypatch.setattr(load_guard.load, "inflight_web", 0)
    assert load_guard.busy()


# ---------- no secret in a log line or an error answer ----------
def test_logs_never_show_pins_passwords_tokens_or_numbers():
    lines = ['body {"phone": "9876543210", "pin": "5524"}', "login password=hunter2 ok", "Authorization: Bearer abc.def-123",
             "cookie access_token=eyJhbGciOi; refresh_token=zzz", "new_pin='1234' confirm_pin=1234", "+91 9876543210 called", "token=AbC123xyz"]
    for line in lines:
        out = log_redact.redact(line)
        for secret in ("9876543210", "5524", "hunter2", "abc.def-123", "eyJhbGciOi", "zzz", "1234", "AbC123xyz"):
            assert secret not in out, (line, out)
    assert log_redact.redact("ts=1764000000 took 12 ms, 2026-06-01") == "ts=1764000000 took 12 ms, 2026-06-01"
    record = logging.LogRecord("t", logging.WARNING, __file__, 1, "sign-in failed for %s pin=%s", ("9876543210", "5524"), None)
    try:
        raise ValueError('bad body {"pin": "5524"}')
    except ValueError:
        import sys
        record.exc_info = sys.exc_info()
    log_redact.Redact().filter(record)
    text = logging.Formatter().format(record)
    assert "5524" not in text and "9876543210" not in text


def test_validation_error_never_echoes_the_input():
    import server

    async def main():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=server.app), base_url="http://t") as c:
            r = await c.post("/api/account/forgot-pin", json={"phone": "9876543210", "new_pin": "12a4", "confirm_pin": "12a4"})
            return r
    r = run(main())
    assert r.status_code == 422
    assert "12a4" not in r.text and "9876543210" not in r.text
    assert r.json()["detail"][0]["loc"] == ["body", "new_pin"]


# ---------- every reward exactly once ----------
def test_same_match_paid_from_many_places_pays_once():
    async def main():
        client, db = scratch()
        uid, ref = f"TEST-p3-{uuid.uuid4().hex[:8]}", f"duel:{uuid.uuid4()}"
        try:
            await db.rf_profiles.create_index("uid", unique=True)
            await db.rf_awards.create_index([("uid", 1), ("ref", 1)], unique=True)
            # Two server copies (two game layers on one database), four calls each, all at the same moment.
            awards = [make_gamify(db, rf_user)[1] for _ in range(2)]
            rewards = await asyncio.gather(*(awards[k % 2](uid, ref, "duel", 12, 30, 30, True) for k in range(8)))
            profile = await db.rf_profiles.find_one({"uid": uid})
            assert profile["coins"] == rewards[0]["coins"] == 12 * 2 + 50 and profile["wins"] == 1 and profile["duels"] == 1
            assert all(r == rewards[0] for r in rewards)
            assert await db.rf_awards.count_documents({"uid": uid}) == 1
        finally:
            await db.rf_profiles.delete_many({"uid": uid})
            await db.rf_awards.delete_many({"uid": uid})
            await client.close()
    run(main())


# ---------- the card bank is written once, whichever copy sees a change first ----------
def test_card_file_written_by_another_copy_is_not_written_again(monkeypatch):
    tmp = Path(tempfile.mkdtemp())
    for f in sorted(card_bank.CARDS_DIR.glob("physics__*.json"))[:2]:
        shutil.copy(f, tmp / f.name)
    monkeypatch.setattr(card_bank, "CARDS_DIR", tmp)

    async def main():
        client, db = scratch()
        files = {"$regex": "^JEE:"}
        try:
            await db.rf_cards.delete_many({"source_file": files})
            await db.rf_meta.delete_many({"_id": "card_files"})
            for state in (card_bank.CARD_HASHES, card_bank.CARD_KEYS, card_bank.CARD_STAT):
                state.clear()
            writes = []
            bulk = db.rf_cards.bulk_write

            async def counted(ops, **kw):
                writes.append(len(ops))
                return await bulk(ops, **kw)
            db.rf_cards.bulk_write = counted
            await card_bank.sync_cards(db)  # copy A writes both files
            assert len(writes) == 2
            # Copy B started before that (its memory says something else), and its catalog copy is old.
            for state in (card_bank.CARD_HASHES, card_bank.CARD_STAT):
                state.clear()
            card_bank.CARD_HASHES.update({k: "older" for k in ("JEE:" + f.name for f in tmp.glob("*.json"))})
            dropped = []

            async def invalidate(prefix):
                dropped.append(prefix)
            monkeypatch.setattr(card_bank.metadata_cache, "invalidate_prefix", invalidate)
            await card_bank.sync_cards(db)
            assert len(writes) == 2, "copy B must not write the same cards again"
            assert dropped == [f"{SCRATCH}:"], "copy B drops its cached bank"
            await card_bank.sync_cards(db)  # nothing changed: files are not even re-read
            assert len(writes) == 2 and len(dropped) == 1
        finally:
            await db.rf_cards.delete_many({"source_file": files})
            await db.rf_meta.delete_many({"_id": "card_files"})
            for state in (card_bank.CARD_HASHES, card_bank.CARD_KEYS, card_bank.CARD_STAT):
                state.clear()
            await client.close()
            shutil.rmtree(tmp)
    run(main())


# ---------- App Health: counts and timings only ----------
def test_route_names_fold_ids():
    assert health_stats.route_of(f"/api/rf/duels/{uuid.uuid4()}/answer") == "/api/rf/duels/{id}/answer"
    assert health_stats.route_of("/api/rf/players/PF37CC308/h2h", "/api/rf/players/{code}/h2h") == "/api/rf/players/{code}/h2h"
    assert health_stats.route_of("/api/rf/players/PF37CC308/h2h") == "/api/rf/players/{id}/{id}", "no route answered: only plain words stay"
    assert health_stats.route_of("/api/jl/attempts/6b260c71-c3e5-43c9-8826-bb8e06613c32/answers/q12/extra/more") == "/api/jl/attempts/{id}/answers/{id}"
    assert health_stats.route_of("/api/rf/weak-topics") == "/api/rf/weak-topics"
    # a friend code made only of letters (about 1 in 10) is a code, not a word
    assert health_stats.route_of("/api/rf/friends/code/QAZWSXED") == "/api/rf/friends/code/{id}"
    assert health_stats.route_of("/api/rf/friends/code/QAZWSXED", "/api/rf/friends/code/{code}") == "/api/rf/friends/code/{code}"
    assert health_stats.route_of("/api/jl/auth/me", "/api/jl/{path:path}") == "/api/jl/auth/me", "the website's catch-all keeps the kind of call"


def test_route_stats_names_rows_by_the_matched_route_through_the_access_guard():
    async def main():
        client, db = scratch()
        token, uid = "tok-" + uuid.uuid4().hex, "TEST-p3route-" + uuid.uuid4().hex[:8]
        app = FastAPI()

        @app.get("/api/rf/friends/code/{code}")
        async def by_code(code: str):
            return {"ok": True}
        app.add_middleware(rf_access.RFAccessGuard, db=db)
        app.add_middleware(health_stats.RouteStats)
        try:
            await db.rf_access.insert_one({"digest": rf_access.token_digest(token), "uid": uid, "sid": "", "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5)})
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as http:
                assert (await http.get("/api/rf/friends/code/QAZWSXED", headers={"Authorization": "Bearer " + token})).status_code == 200
                assert (await http.get("/api/rf/friends/code/ZXCVBNMQ")).status_code == 401  # stopped by the guard, before any route
            rows = health_stats.recent_routes()
            assert rows["/api/rf/friends/code/{code}"][0] >= 1 and rows["/api/rf/friends/code/{id}"][0] >= 1
            assert not [r for r in rows if "QAZWSXED" in r or "ZXCVBNMQ" in r]
        finally:
            await db.rf_access.delete_many({"uid": uid})
            await client.close()
    run(main())


def test_a_stopping_copy_leaves_the_page_at_once():
    async def main():
        client, db = scratch()
        try:
            beating = asyncio.create_task(health_stats.beat(db, lambda: {"sockets": 0}, lambda: {}, lambda: 0))
            for _ in range(50):
                if await db.rf_health_nodes.find_one({"_id": health_stats.NODE}, {"_id": 1}):
                    break
                await asyncio.sleep(0.05)
            assert len((await health_panel.health_data(db))["copies"]) == 1
            await health_stats.leave(db, beating)
            await asyncio.sleep(0)
            assert beating.cancelled() or beating.done()
            assert (await health_panel.health_data(db))["copies"] == []
        finally:
            await db.rf_health_nodes.delete_many({"_id": health_stats.NODE})
            await client.close()
    run(main())


def test_health_data_adds_copies_up_and_shows_no_personal_data():
    async def main():
        client, db = scratch()
        ids = ["node0", "node1", "gone"]
        try:
            await db.rf_health_nodes.delete_many({"_id": {"$in": ids}})
            now = time.time()
            fast = [0] * (len(health_stats.BOUNDS) + 1)
            fast[2] = 100  # 100 answers within 5 ms
            for k in range(2):
                await db.rf_health_nodes.insert_one({"_id": f"node{k}", "started": now - 600, "ts": now, "load": {"sockets": 40, "lag_sustained_ms": 1.0, "busy": False},
                                                     "routes": {"/api/rf/duels/{id}/answer": [100, 1] + fast, "/api/jl/papers": [10, 0] + fast},
                                                     "website": {"state": "open" if k else "closed", "opened": k, "calls": 10, "failed": 5 * k, "refused": 3 * k, "hist": [10, 0, 0, 0, 0, 0, 0, 0, 0]},
                                                     "jobs": {"cup_night_tick": {"ts": now - 7, "took_ms": 1.0, "ok": True}}, "later_pending": 0})
            await db.rf_health_nodes.update_many({"_id": {"$in": ["node0", "node1"]}}, {"$set": {"ts": now - 5}})  # their last report: 5 s ago
            await db.rf_health_nodes.insert_one({"_id": "gone", "started": now - 900, "ts": now - 120, "load": {"sockets": 999}})
            data = await health_panel.health_data(db)
            tick = next(j for j in data["jobs"] if j["id"] == "cup_night_tick")
            assert tick["last_s_ago"] == 7 and tick["late_s"] == 2, "judged at its copy's report, not by the report's age"
            assert data["students"]["playing_live_now"] == 80, "the copy that stopped is not counted"
            answers = next(g for g in data["speed"] if g["id"] == "answers")
            assert answers["count"] == 200 and answers["errors"] == 2 and answers["p95_ms"] == 5
            assert data["website"]["state"] == "open" and data["website"]["refused"] == 3 and len(data["copies"]) == 2
            text = json.dumps(data)
            for word in ('"uid"', '"phone"', '"name"', "TEST-"):
                assert word not in text
        finally:
            await db.rf_health_nodes.delete_many({"_id": {"$in": ids}})
            await client.close()
    run(main())
