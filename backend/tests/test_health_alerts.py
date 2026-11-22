"""App Health email alerts (health_alerts.py): what counts as a problem, when an email goes, and the owner routes.

No real email is sent: a fake sender records what would go. Scratch database only (`<DB_NAME>_alerts_selftest`).
Run:  cd /app/backend && python -m pytest tests/test_health_alerts.py -q
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
from dotenv import load_dotenv
from fastapi import FastAPI
from pymongo import AsyncMongoClient

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

import health_alerts  # noqa: E402
import owner_mail  # noqa: E402

SCRATCH = os.environ["DB_NAME"] + "_alerts_selftest"


def run(coro):
    return asyncio.run(coro)


def scratch():
    """A database of its own for each test (the tests may run side by side)."""
    client = AsyncMongoClient(os.environ["MONGO_URL"])
    return client, client[SCRATCH + "_" + uuid.uuid4().hex[:8]]


def data(**over):
    d = {"at": time.time(), "students": {"signed_in": 3, "playing_live_now": 2, "live_matches": 1},
         "speed": [{"id": "all", "count": 100, "errors": 0, "p95_ms": 50}, {"id": "answers", "count": 30, "errors": 0, "p95_ms": 20}],
         "website": {"state": "closed", "calls": 10, "failed": 0}, "routes": [],
         "jobs": [{"id": "cup_night_tick", "label": "Cup Night clock", "every_s": 3, "last_s_ago": 2, "late_s": 1, "ok": True},
                  {"id": "sweep", "label": "Closing old matches", "every_s": 330, "last_s_ago": 100, "late_s": 100, "ok": True}],
         "copies": [{"id": "abc123", "up_s": 4000, "lag_ms": 3, "busy": False}]}
    d.update(over)
    return d


class Sender:
    def __init__(self):
        self.sent = []

    async def __call__(self, *, to, subject, html):
        owner_mail._assert_safe_email(subject, html)  # every alert passes the email guard
        self.sent.append((to, subject, html))
        return "id"


def test_a_healthy_app_has_no_problems():
    assert health_alerts.problems(data(), None) == {}


def test_each_kind_of_problem_is_found():
    assert "did not answer" in health_alerts.problems(data(), "did not answer within 10 seconds")["website"]
    assert "paused" in health_alerts.problems(data(website={"state": "open", "calls": 40, "failed": 30}), None)["website"]
    errors = data(speed=[{"id": "all", "count": 200, "errors": 20, "p95_ms": 50}])
    assert "20 of 200" in health_alerts.problems(errors, None)["errors"]
    website_only = data(speed=[{"id": "all", "count": 200, "errors": 20}, {"id": "website", "count": 150, "errors": 20}])
    assert "errors" not in health_alerts.problems(website_only, None), "website failures are the website alert, not app errors"
    assert "packed" in health_alerts.problems(data(copies=[{"id": "a", "up_s": 50, "lag_ms": 3, "busy": True}]), None)["packed"]
    assert "behind" in health_alerts.problems(data(copies=[{"id": "a", "up_s": 50, "lag_ms": 450, "busy": False}]), None)["packed"]
    slow = data(speed=[{"id": "all", "count": 100, "errors": 0}, {"id": "answers", "count": 40, "errors": 0, "p95_ms": 1000}])
    assert "slow" in health_alerts.problems(slow, None)["packed"]
    late = data(jobs=[{"id": "sweep", "label": "Closing old matches", "every_s": 330, "last_s_ago": 2000, "late_s": 2000, "ok": True}])
    assert "Closing old matches has not run" in health_alerts.problems(late, None)["jobs"]
    fresh = data(jobs=late["jobs"], copies=[{"id": "a", "up_s": 120, "lag_ms": 3, "busy": False}])
    assert "jobs" not in health_alerts.problems(fresh, None), "a copy that just started has not had the job's turn yet"
    failed = data(jobs=[{"id": "card_sync", "label": "Question bank check", "every_s": 60, "last_s_ago": 5, "late_s": 5, "ok": False}])
    assert "failed" in health_alerts.problems(failed, None)["jobs"]


def test_one_email_when_it_starts_and_one_when_it_is_fixed():
    async def main():
        client, db = scratch()
        send, now, d = Sender(), time.time(), data()
        try:
            down = {"website": "The website did not answer within 10 seconds."}
            await health_alerts.step(db, down, d, now, send)
            assert send.sent == [], "seen once: could be a blip"
            await health_alerts.step(db, down, d, now + 30, send)
            assert len(send.sent) == 1 and "alert: jeelive.ai website is down" in send.sent[0][1]
            assert send.sent[0][0] == health_alerts.TO and "did not answer" in send.sent[0][2]
            for i in range(2, 6):
                await health_alerts.step(db, down, d, now + 30 * i, send)
            assert len(send.sent) == 1, "still down: no repeat emails"
            for i in range(6, 9):
                await health_alerts.step(db, {}, d, now + 30 * i, send)
            assert len(send.sent) == 1, "fixed only after 2 quiet minutes"
            await health_alerts.step(db, {}, d, now + 30 * 9, send)
            assert len(send.sent) == 2 and "Fixed: jeelive.ai website is answering again" in send.sent[1][1]
            # back again 2 minutes later: held while inside the 10-minute gap, then emailed because it is still on
            for i in range(10, 21):
                await health_alerts.step(db, down, d, now + 30 * i, send)
            assert len(send.sent) == 2 and (await db.rf_meta.find_one({"_id": "alert:website"}))["active"] is True
            await health_alerts.step(db, down, d, now + 30 * 21, send)
            assert len(send.sent) == 3 and "alert: jeelive.ai website is down" in send.sent[2][1], "a repeat outage is never left unreported"
            for i in range(22, 26):
                await health_alerts.step(db, {}, d, now + 30 * i, send)
            assert len(send.sent) == 4 and "Fixed:" in send.sent[3][1]
            # back for less than the 10-minute gap: never emailed, so no 'Fixed' either
            for i in range(26, 28):
                await health_alerts.step(db, down, d, now + 30 * i, send)
            for i in range(28, 32):
                await health_alerts.step(db, {}, d, now + 30 * i, send)
            assert len(send.sent) == 4
        finally:
            await client.drop_database(db.name)
            await client.close()
    run(main())


def test_the_daily_cap_stops_a_flood():
    async def main():
        client, db = scratch()
        send = Sender()
        try:
            results = [await health_alerts.mail(db, "JEELIVE.AI alert: x", "<p>x</p>", send) for _ in range(health_alerts.DAILY_CAP + 3)]
            assert results.count("sent") == health_alerts.DAILY_CAP and results[-3:] == ["cap"] * 3 and len(send.sent) == health_alerts.DAILY_CAP
        finally:
            await client.drop_database(db.name)
            await client.close()
    run(main())


def test_email_link_uses_the_host_the_owner_opened_and_marks_preview():
    async def main():
        client, db = scratch()
        try:
            assert await health_alerts.page_link(db) == ("", "")
            await db.rf_meta.insert_one({"_id": "alert:host", "host": "abc.preview.emergentagent.com"})
            link, prefix = await health_alerts.page_link(db)
            assert link == "https://abc.preview.emergentagent.com/api/owner/health" and prefix == "[Preview] "
            html = health_alerts.email_html("t", ["a <b>"], data(), link, "bad")
            owner_mail._assert_safe_email("t", html)
            assert "a &lt;b&gt;" in html
        finally:
            await client.drop_database(db.name)
            await client.close()
    run(main())


def test_owner_routes_need_the_owner_and_the_test_email_is_rate_limited(monkeypatch):
    async def main():
        client, db = scratch()
        send = Sender()
        monkeypatch.setattr(health_alerts, "send_email", send)
        app = FastAPI()
        app.include_router(health_alerts.make_router(db), prefix="/api")
        token = secrets.token_urlsafe(32)
        try:
            await db.owner_sessions.insert_one({"digest": hashlib.sha256(token.encode()).hexdigest(), "who": "ow***@test",
                                                "expires_at": datetime.now(timezone.utc) + timedelta(hours=1)})
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="https://owner.example.org") as http:
                assert (await http.get("/api/owner/health/alerts")).status_code == 401
                assert (await http.post("/api/owner/health/alerts/test", headers={"X-Owner-Panel": "1"})).status_code == 401
                ck = {"Cookie": "jl_owner=" + token}
                st = (await http.get("/api/owner/health/alerts", headers=ck)).json()
                assert st["to"].endswith("@billpe.com") and "***" in st["to"] and [k["id"] for k in st["kinds"]] == list(health_alerts.KINDS)
                assert (await http.post("/api/owner/health/alerts/test", headers=ck)).status_code == 403, "needs the owner panel header"
                r = await http.post("/api/owner/health/alerts/test", headers={**ck, "X-Owner-Panel": "1"})
                assert r.status_code == 200 and r.json()["sent"] is True and len(send.sent) == 1
                assert "https://owner.example.org/api/owner/health" in send.sent[0][2]
                again = await http.post("/api/owner/health/alerts/test", headers={**ck, "X-Owner-Panel": "1"})
                assert again.status_code == 429 and len(send.sent) == 1
        finally:
            await client.drop_database(db.name)
            await client.close()
    run(main())


def test_a_failed_send_is_tried_again_later_and_not_counted():
    async def main():
        client, db = scratch()
        good, now, d = Sender(), time.time(), data()

        async def broken(**_):
            raise RuntimeError("email service down")
        try:
            jobs = {"jobs": "Question bank check failed on its last run."}
            for i in range(3):
                await health_alerts.step(db, jobs, d, now + 30 * i, broken)
            day = await db.rf_meta.find_one({"_id": {"$regex": "^alert:day:"}})
            assert not day, "failed sends do not use up the day's emails"
            for i in range(3, 11):  # tried again only after RETRY_EVERY (300 s) since the last try
                await health_alerts.step(db, jobs, d, now + 30 * i, good)
            assert len(good.sent) == 0
            await health_alerts.step(db, jobs, d, now + 30 * 11, good)
            assert len(good.sent) == 1 and "A background job stopped" in good.sent[0][1]
        finally:
            await client.drop_database(db.name)
            await client.close()
    run(main())
