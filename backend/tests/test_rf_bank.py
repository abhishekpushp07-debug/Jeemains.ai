"""The Rapid Fire cards a phone keeps for itself (rf_bank.py) and a Solo Sprint played from that copy without the
server (POST /api/rf/sessions/offline), 27 Nov 2026.

What must hold:
  * the list names one part per subject; a part's bytes give its hash, and it holds exactly the cards a sprint deals from;
  * a part asked for with an old hash is refused (the phone then asks for the list again), and nobody without a pass gets it;
  * a round played on the phone is written and closed in one go, with the server's own marking; the same round sent again
    is the same sprint with the same reward; a card that left the bank is left out; a round is never more than 100 cards.

One fixed player (TEST-bank-a, never on a leaderboard: names and ids that begin with TEST are left out there) and fixed
request ids, so a second run adds no row. NOTHING is deleted: the pass ends by its own expiry.
"""
import asyncio
import hashlib
import os
import random
import secrets
import sys
from datetime import datetime, timedelta, timezone

import httpx
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
from rapid_deck import selection_pool  # noqa: E402
from rf_bank import pack  # noqa: E402
from social import remember_identity  # noqa: E402

BASE = "http://localhost:8001/api/rf"
UID = "TEST-bank-a"
ROUND, SHORT, LEFT = "TEST-bank-round-0001", "TEST-bank-round-0004", "TEST-bank-round-0003"  # 0002: the short round before retired cards were left out


def run(body):
    async def go():
        db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
        token = secrets.token_urlsafe(24)
        await db.rf_access.insert_one({"digest": hashlib.sha256(token.encode()).hexdigest(), "uid": UID, "sid": "", "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10)})
        await remember_identity(db, UID, {"name": "TESTBANK", "phone": ""})
        async with httpx.AsyncClient(base_url=BASE, timeout=60, headers={"Authorization": "Bearer " + token}) as s:
            await body(db, s)
    asyncio.run(go())


def test_the_same_cards_give_the_same_bytes_whatever_order_they_came_in():
    cards = [{"id": f"c{k:02d}", "chapter": ["Waves", "Optics", "Extra"][k % 3], "topic": "", "prompt": f"q{k}", "formula": "", "options": ["a", "b", "c", "d"], "answer": k % 4, "explain": ""} for k in range(12)]
    first = pack("JEE", "Physics", cards, ["Optics", "Waves", "Heat"])
    mixed = cards[:]
    random.shuffle(mixed)
    again = pack("JEE", "Physics", mixed, ["Optics", "Waves", "Heat"])
    assert first["hash"] == again["hash"] and first["gz"] == again["gz"] and first["cards"] == 12
    # the chapters as the picker lists them: the book's order, a chapter without cards too, one the book does not know last
    assert first["chapters"] == [{"name": "Optics", "count": 4}, {"name": "Waves", "count": 4}, {"name": "Heat", "count": 0}, {"name": "Extra", "count": 4}]
    assert pack("JEE", "Physics", cards[:-1], ["Optics", "Waves", "Heat"])["hash"] != first["hash"]


def test_the_list_and_its_parts():
    async def body(db, s):
        assert (await httpx.AsyncClient(base_url=BASE, timeout=30).get("/bank?exam=JEE")).status_code == 401  # no pass, no cards
        listed = await s.get("/bank?exam=JEE")
        assert listed.status_code == 200, listed.text
        data = listed.json()
        assert data["exam"] == "JEE" and data["seconds_per_card"] == 20 and data["counts"] == [30, 50, 100]
        parts = {p["subject"]: p for p in data["parts"]}
        assert list(parts) == ["Physics", "Chemistry", "Mathematics", "English", "Logical Reasoning"]
        for subject, p in parts.items():
            pool = await selection_pool(db, "JEE", subject)
            assert p["cards"] == sum(len(rows) for rows in pool.values()) > 0, subject
            assert {c["name"]: c["count"] for c in p["chapters"] if c["count"]} == {chapter: len(rows) for chapter, rows in pool.items()}, subject
        p = parts["Logical Reasoning"]  # the smallest part
        got = await s.get("/bank/part", params={"exam": "JEE", "subject": p["subject"], "h": p["hash"]})
        assert got.status_code == 200 and got.headers["content-encoding"] == "gzip" and got.headers["cache-control"] == "no-store"
        assert hashlib.sha256(got.content).hexdigest()[:20] == p["hash"] and len(got.content) == p["bytes"]
        body = got.json()
        pool = await selection_pool(db, "JEE", p["subject"])
        assert body["exam"] == "JEE" and body["subject"] == p["subject"] and len(body["cards"]) == p["cards"]
        assert {c["id"] for c in body["cards"]} == {row[0] for rows in pool.values() for row in rows}  # exactly what a sprint deals from
        for c in body["cards"][:50]:
            assert set(c) - {"diagram"} == {"id", "chapter", "topic", "prompt", "formula", "options", "answer", "explain"} and 0 <= c["answer"] < len(c["options"])
        assert (await s.get("/bank/part", params={"exam": "JEE", "subject": p["subject"], "h": "0" * 20})).status_code == 409
        assert (await s.get("/bank/part", params={"exam": "JEE", "subject": "Biology", "h": p["hash"]})).status_code == 404
    run(body)


def test_a_round_played_on_the_phone_is_written_marked_and_paid_once():
    async def body(db, s):
        cards = await db.rf_cards.find({"exam": "JEE", "subject": "Physics", "retired": {"$ne": True}, "diagram": None}, {"_id": 0, "id": 1, "answer": 1}).sort("id", 1).limit(30).to_list(30)
        assert len(cards) == 30
        wrong = lambda c: (c["answer"] + 1) % 4  # noqa: E731
        results = ([{"card_id": c["id"], "outcome": "correct", "choice": c["answer"], "ms": 4000} for c in cards[:19]]
                   + [{"card_id": cards[19]["id"], "outcome": "incorrect", "choice": cards[19]["answer"], "ms": 3000}]  # the phone said wrong, the key says right
                   + [{"card_id": cards[20]["id"], "outcome": "correct", "choice": wrong(cards[20]), "ms": 3000}]      # the phone said right, the key says wrong
                   + [{"card_id": c["id"], "outcome": "incorrect", "choice": wrong(c), "ms": 9000} for c in cards[21:25]]
                   + [{"card_id": c["id"], "outcome": "skipped", "choice": None, "ms": 2000} for c in cards[25:28]]
                   + [{"card_id": c["id"], "outcome": "timed_out", "choice": None, "ms": 20000} for c in cards[28:]])
        sent = {"request_id": ROUND, "exam": "JEE", "picks": [{"subject": "Physics", "chapter": None}], "card_ids": [c["id"] for c in cards], "results": results, "played_at": "2026-11-27T10:00:00.000Z"}
        first = await s.post("/sessions/offline", json=sent)
        assert first.status_code == 200, first.text
        done = first.json()
        assert done["status"] == "completed" and done["mode"] == "fresh" and done["label"] == "Mixed Physics" and done["subject"] == "Physics" and done["exam"] == "JEE"
        assert {k: done["summary"][k] for k in ("total", "correct", "incorrect", "skipped", "timed_out", "answered", "score")} == {"total": 30, "correct": 20, "incorrect": 5, "skipped": 3, "timed_out": 2, "answered": 25, "score": 20}
        assert isinstance(done["reward"], dict) and done["card_ids"] == sent["card_ids"]
        kept = await db.rf_sessions.find_one({"user_id": UID, "request_id": ROUND}, {"_id": 0, "offline": 1, "played_at": 1, "id": 1})
        assert kept == {"offline": True, "played_at": "2026-11-27T10:00:00.000Z", "id": done["id"]}
        # the same round again (the phone did not hear the answer), even with other answers: the same sprint, the same pay
        again = (await s.post("/sessions/offline", json={**sent, "results": []})).json()
        assert again["id"] == done["id"] and again["summary"] == done["summary"] and again["reward"] == done["reward"]
        assert await db.rf_sessions.count_documents({"user_id": UID, "request_id": ROUND}) == 1
        assert await db.rf_awards.count_documents({"uid": UID, "ref": "solo:" + done["id"]}) == 1
        assert done["id"] in [row["id"] for row in (await s.get("/history?exam=JEE")).json()["items"]]
        assert (await s.get(f"/sessions/{done['id']}")).json()["status"] == "completed"  # opens like any finished sprint
    run(body)


def test_a_card_that_left_the_bank_is_left_out_and_a_round_has_its_limits():
    async def body(db, s):
        cards = await db.rf_cards.find({"exam": "JEE", "subject": "Chemistry", "retired": {"$ne": True}, "diagram": None}, {"_id": 0, "id": 1, "answer": 1}).sort("id", 1).limit(3).to_list(3)
        # a card that is not in the bank, and one that was retired after the phone fetched it (read only: nothing is retired here)
        retired = await db.rf_cards.find_one({"exam": "JEE", "retired": True}, {"_id": 0, "id": 1})
        ids = ["no-such-card", *([retired["id"]] if retired else []), *[c["id"] for c in cards]]
        short = await s.post("/sessions/offline", json={"request_id": SHORT, "card_ids": ids, "repeat": True,
                                                        "results": [{"card_id": "no-such-card", "outcome": "correct", "choice": 0, "ms": 100}, {"card_id": cards[0]["id"], "outcome": "correct", "choice": cards[0]["answer"], "ms": 100}]})
        assert short.status_code == 200, short.text
        done = short.json()
        assert done["card_ids"] == [c["id"] for c in cards] and done["mode"] == "repeat_missed" and done["subject"] == "Chemistry" and done["label"] is None
        assert done["summary"]["total"] == 3 and done["summary"]["correct"] == 1 and done["summary"]["skipped"] == 2  # cards without an answer count as skipped
        assert (await s.post("/sessions/offline", json={"request_id": LEFT, "card_ids": ["no-such-card"], "results": []})).status_code == 404
        assert await db.rf_sessions.count_documents({"user_id": UID, "request_id": LEFT}) == 0
        assert (await s.post("/sessions/offline", json={"request_id": LEFT, "card_ids": [f"x{k}" for k in range(101)], "results": []})).status_code == 422
        assert (await s.post("/sessions/offline", json={"request_id": LEFT, "card_ids": [], "results": []})).status_code == 422
        assert (await s.post("/sessions/offline", json={"request_id": LEFT, "card_ids": ids, "results": [], "coins": 999})).status_code == 422
        assert (await httpx.AsyncClient(base_url=BASE, timeout=30).post("/sessions/offline", json={"request_id": LEFT, "card_ids": ids, "results": []})).status_code == 401
    run(body)
