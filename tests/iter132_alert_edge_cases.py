"""Iteration132 scratch-DB edge cases for health_alerts.step()/mail() with a fake sender (no real email, no live DB writes).
Run: cd /app/tests && PYTHONDONTWRITEBYTECODE=1 python -m pytest iter132_alert_edge_cases.py -q -p no:randomly -p no:cacheprovider"""
import asyncio
import os
import sys
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv
from pymongo import AsyncMongoClient

sys.path.insert(0, "/app/backend")
load_dotenv(Path("/app/backend/.env"))
import health_alerts as ha  # noqa: E402
import owner_mail  # noqa: E402

DOWN = {"website": "The website did not answer within 10 seconds."}


def data():
    return {"students": {"signed_in": 3, "playing_live_now": 2, "live_matches": 1},
            "speed": [{"id": "all", "count": 100, "errors": 0}, {"id": "answers", "count": 30, "errors": 0, "p95_ms": 20}],
            "website": {"state": "closed", "calls": 10, "failed": 0}, "jobs": [],
            "copies": [{"id": "abc123", "up_s": 4000, "lag_ms": 3, "busy": False}]}


class Sender:
    def __init__(self, fail=False):
        self.sent, self.fail = [], fail

    async def __call__(self, *, to, subject, html):
        owner_mail._assert_safe_email(subject, html)
        if self.fail:
            raise RuntimeError("provider down")
        self.sent.append((to, subject, html))


def with_db(fn):
    async def main():
        client = AsyncMongoClient(os.environ["MONGO_URL"])
        db = client[os.environ["DB_NAME"] + "_it132_" + uuid.uuid4().hex[:8]]
        try:
            await fn(db)
        finally:
            await client.drop_database(db.name)
            await client.close()
    asyncio.run(main())


# Two kinds at once: one email each, independent state
def test_two_kinds_at_once():
    async def t(db):
        s, now = Sender(), time.time()
        both = {**DOWN, "packed": "1 of 1 server copies are packed, so new players are asked to wait."}
        await ha.step(db, both, data(), now, s)
        await ha.step(db, both, data(), now + 30, s)
        assert sorted(x[1] for x in s.sent) == ["JEELIVE.AI alert: The server is packed or slow", "JEELIVE.AI alert: jeelive.ai website is down"]
        for i in range(2, 6):
            await ha.step(db, DOWN, data(), now + 30 * i, s)  # packed clears, website stays
        assert s.sent[-1][1] == "Fixed: The server is back to normal speed" and len(s.sent) == 3
    with_db(t)


# Cooldown ends: a new outage >10 min after the last problem email is emailed again
def test_new_outage_after_cooldown_is_emailed():
    async def t(db):
        s, now = Sender(), time.time()
        for i in range(2):
            await ha.step(db, DOWN, data(), now + 30 * i, s)
        for i in range(2, 6):
            await ha.step(db, {}, data(), now + 30 * i, s)
        later = now + 700
        for i in range(2):
            await ha.step(db, DOWN, data(), later + 30 * i, s)
        assert [x[1].split(":")[0] for x in s.sent] == ["JEELIVE.AI alert", "Fixed", "JEELIVE.AI alert"]
    with_db(t)


# GAP: re-outage inside the cooldown that then lasts an hour never emails (owner last got 'Fixed')
def test_long_reoutage_inside_cooldown_is_eventually_emailed():
    async def t(db):
        s, now = Sender(), time.time()
        for i in range(2):
            await ha.step(db, DOWN, data(), now + 30 * i, s)
        for i in range(2, 6):
            await ha.step(db, {}, data(), now + 30 * i, s)
        for i in range(6, 126):  # down again 1 hour
            await ha.step(db, DOWN, data(), now + 30 * i, s)
        assert len(s.sent) >= 3, f"owner got {[x[1] for x in s.sent]} and nothing about the 1-hour re-outage"
    with_db(t)


# GAP: a failed send is never retried while the problem stays active
def test_failed_problem_email_is_retried():
    async def t(db):
        bad, now = Sender(fail=True), time.time()
        for i in range(2):
            await ha.step(db, DOWN, data(), now + 30 * i, bad)
        good = Sender()
        for i in range(2, 60):
            await ha.step(db, DOWN, data(), now + 30 * i, good)
        assert good.sent, "provider came back but the ongoing outage was never emailed"
    with_db(t)


# Missing OWNER_ALERT_EMAIL: nothing sent, state still tracked, no crash
def test_missing_owner_email():
    async def t(db):
        old, ha.TO = ha.TO, ""
        try:
            s, now = Sender(), time.time()
            for i in range(3):
                await ha.step(db, DOWN, data(), now + 30 * i, s)
            st = await db.rf_meta.find_one({"_id": "alert:website"})
            assert s.sent == [] and st["active"] is True and st["mailed"] is False
            assert await db.rf_meta.find_one({"_id": {"$regex": "^alert:day:"}}) is None
        finally:
            ha.TO = old
    with_db(t)


# Flapping every other check never alerts (needs 2 in a row) - documents behaviour
def test_flapping_every_other_check():
    async def t(db):
        s, now = Sender(), time.time()
        for i in range(20):
            await ha.step(db, DOWN if i % 2 else {}, data(), now + 30 * i, s)
        print("flapping emails:", len(s.sent))
    with_db(t)


# Email content: no student names/ids; problem email passes the guard and has exactly one https link
def test_email_content():
    async def t(db):
        await db.rf_meta.insert_one({"_id": "alert:host", "host": "abc.preview.emergentagent.com"})
        s, now = Sender(), time.time()
        for i in range(2):
            await ha.step(db, {"jobs": "Closing old <script> failed on its last run."}, data(), now + 30 * i, s)
        to, subj, html = s.sent[0]
        assert subj.startswith("[Preview] ") and "<script>" not in html and "&lt;script&gt;" in html
        assert html.count("href=") == 1 and 'href="https://jeelive-feature-book--3o05z2vs.preview.emergentagent.com/api/owner/health"' in html
        assert "<form" not in html and to == ha.TO
    with_db(t)
