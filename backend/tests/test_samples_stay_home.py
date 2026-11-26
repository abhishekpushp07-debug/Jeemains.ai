"""Made-up samples never leave the workspace (27 Nov 2026).

On 26 Nov 2026 a Publish made from a copy of the workspace pointed production at a copy of the preview's database: the
preview's three made-up Matched shifts and the "on" of Home's card were served to students. Since then a sample is shown
only by a server whose MongoDB is the workspace's own (workspace.py), whatever the database holds.
Nothing is written by this file: the database is only read."""
import asyncio
import os
import sys
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matched
import workspace

SAMPLE = {"_id": "2027-01-22-s1", "published": True, "sample": True, "paper_id": "sample-paper-01",
          "items": [{"n": 1, "subject": "Physics", "jee": {"text": "A made-up JEE question"},
                     "ours": [{"text": "A made-up question of ours", "question_id": "sample-q-0001"}]}]}
REAL = {**SAMPLE, "_id": "2027-01-23-s1", "paper_id": "real-paper-0001"}
del REAL["sample"]


def test_only_a_mongo_on_the_same_machine_is_the_workspace():
    for url in ("mongodb://localhost:27017", "mongodb://localhost", "mongodb://127.0.0.1:27017/", "mongodb://[::1]:27017",
                "mongodb://localhost:27017/test_database?retryWrites=true"):
        assert workspace.own(url), url
    # A managed cluster, a password, another machine, a list of machines, a look-alike name, or nothing at all: production.
    for url in ("", "mongodb+srv://someone:word@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority", "mongodb://someone:word@localhost:27017",
                "mongodb://10.0.0.5:27017", "mongodb://db.internal:27017/app", "mongodb://localhost:27017,other.example:27017/app",
                "mongodb://localhost.evil.example:27017", "mongodb://localhost:27017/?x=someone@elsewhere", "https://localhost:27017"):
        assert not workspace.own(url), url
    assert workspace.own() is True  # this test runs on the preview: its own database is the one on this machine


class _Shifts:
    """A stand-in for the collection that answers like Mongo for the two things asked here: equality and {"$ne": True}."""
    def __init__(self, docs):
        self.docs = docs

    def _hits(self, query):
        def hit(doc):
            return all(doc.get(k) is not True if v == {"$ne": True} else doc.get(k) == v for k, v in query.items())
        return [d for d in self.docs if hit(d)]

    def find(self, query, *_):
        self.rows = sorted(self._hits(query), key=lambda d: d["_id"], reverse=True)
        return self

    def sort(self, *_):
        return self

    async def to_list(self, _):
        return self.rows

    async def find_one(self, query, *_, **__):
        rows = self._hits(query)
        return rows[0] if rows else None


class _Meta:
    def __init__(self, row):
        self.row = row

    async def find_one(self, *_):
        return self.row


def served(monkeypatch, own, shifts=(SAMPLE, REAL), card=None, code="auto"):
    """What a server gives out: the ids of the list, the sample shift, the sample's paper, and whether Home's card is on."""
    monkeypatch.setattr(workspace, "own", lambda url=None: own)
    monkeypatch.setattr(matched, "_owner", {"value": None, "read": float("-inf")})
    monkeypatch.setattr(matched, "cache", matched.MetadataCache())
    monkeypatch.setattr(matched, "_series", {"last": "2027-01-27", "loaded": True})
    monkeypatch.setattr(matched, "ist_day", lambda: "2026-11-27")  # before the series: only a shift or a word turns the card on
    db = type("Db", (), {"matched_shifts": _Shifts(list(shifts)), "rf_meta": _Meta(card)})()

    async def run():
        index = await matched.load_index(db)
        return ([s["id"] for s in index["shifts"]], await matched.load_shift(db, SAMPLE["_id"]),
                await matched.load_paper(db, SAMPLE["paper_id"]), await matched.card_on(db, code))
    return asyncio.run(run())


def test_the_workspace_shows_its_samples_and_production_never_does(monkeypatch):
    ids, shift, paper, card = served(monkeypatch, own=True)
    assert ids == [REAL["_id"], SAMPLE["_id"]] and shift["matched"] == 1 and paper["id"] == SAMPLE["_id"] and card is True
    ids, shift, paper, card = served(monkeypatch, own=False)
    assert ids == [REAL["_id"]] and shift is None and paper is None and card is True  # the real shift alone turns the card on
    # A database that holds nothing but samples (production on 26 Nov 2026): no list, no page, no paper, no card.
    assert served(monkeypatch, own=False, shifts=(SAMPLE,)) == ([], None, None, False)
    # A real shift is never mistaken for a sample: `sample` missing, false or anything that is not true.
    for mark in (False, None, "true", 1):
        ids, *_ = served(monkeypatch, own=False, shifts=({**REAL, "sample": mark},))
        assert ids == [REAL["_id"]], mark


def test_the_samples_own_on_never_switches_the_card_in_production(monkeypatch):
    legacy = {"_id": matched.CARD_META, "value": "on", "ts": 1795641111.38}  # the very row that reached production
    assert served(monkeypatch, own=True, shifts=(), card=legacy)[3] is True  # the owner's preview: the card is on, as before
    assert served(monkeypatch, own=False, shifts=(), card=legacy)[3] is False
    assert served(monkeypatch, own=False, shifts=(SAMPLE,), card=legacy) == ([], None, None, False)
    assert served(monkeypatch, own=False, shifts=(), card={**legacy, "by": "sample"})[3] is False
    # The website's super admin and the owner still switch it, both ways.
    for by in matched.CARD_BY:
        assert served(monkeypatch, own=False, shifts=(), card={"value": "on", "by": by})[3] is True
        assert served(monkeypatch, own=False, shifts=(REAL,), card={"value": "off", "by": by})[3] is False
    assert served(monkeypatch, own=False, shifts=(REAL,), card={"value": "off"})[3] is True  # an unsigned "off" is not a word either
    assert matched.card_word(None, True) is None and matched.card_word({"value": "auto", "by": "website"}, False) == "auto"


def test_the_filter_reads_this_database_the_same_way_mongo_does():
    """Read only. With the production filter, this database's own samples (if any are published) are left out and every
    other published shift stays; with the workspace's filter nothing published is left out."""
    async def run():
        client = AsyncIOMotorClient(os.environ["MONGO_URL"])
        shifts = client[os.environ["DB_NAME"]].matched_shifts
        docs = await shifts.find({}, {"published": 1, "sample": 1}).to_list(1000)
        every = {d["_id"] for d in docs if d.get("published") is True}
        real = {d["_id"] for d in docs if d.get("published") is True and d.get("sample") is not True}
        outside = {d["_id"] for d in await shifts.find({"published": True, "sample": {"$ne": True}}, {"_id": 1}).to_list(1000)}
        inside = {d["_id"] for d in await shifts.find({"published": True}, {"_id": 1}).to_list(1000)}
        client.close()
        return every, real, outside, inside
    every, real, outside, inside = asyncio.run(run())
    assert outside == real and inside == every


def test_the_filter_is_the_one_each_reader_uses(monkeypatch):
    monkeypatch.setattr(workspace, "own", lambda url=None: False)
    assert matched.shown() == {"published": True, "sample": {"$ne": True}}
    monkeypatch.setattr(workspace, "own", lambda url=None: True)
    assert matched.shown() == {"published": True}


def test_the_real_doors_of_a_production_like_server_on_this_very_database(monkeypatch):
    """The whole way, read only: the app's own doors (GET /api/matched, a shift, a paper, GET /api/app/switches) answered
    by a server that is not the workspace's, from THIS database. While the owner keeps the samples published here, this
    database holds exactly what production's held on 26 Nov 2026: the three samples and the card's unsigned "on"."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from pymongo import MongoClient

    import app_switches
    from database import db

    plain = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    docs = list(plain.matched_shifts.find({"published": True}, {"sample": 1, "paper_id": 1}))
    samples = [d for d in docs if d.get("sample") is True]
    real = sorted((d["_id"] for d in docs if d.get("sample") is not True and matched.re.match(matched.SHIFT_ID, d["_id"])), reverse=True)
    card = plain.rf_meta.find_one({"_id": matched.CARD_META}) or {}
    last = (plain.rf_meta.find_one({"_id": matched.SERIES_META}) or {}).get("value")
    plain.client.close()

    monkeypatch.setattr(workspace, "own", lambda url=None: False)
    monkeypatch.setattr(matched, "_owner", {"value": None, "read": float("-inf")})
    monkeypatch.setattr(matched, "cache", matched.MetadataCache())
    monkeypatch.setattr(matched, "_series", {"last": None, "loaded": False})
    app = FastAPI()
    app.include_router(matched.make_router(db), prefix="/api")
    app.include_router(app_switches.router, prefix="/api")
    with TestClient(app) as door:
        listed = door.get("/api/matched").json()
        assert [s["id"] for s in listed["shifts"]] == real[:matched.MAX_SHIFTS]
        for d in samples:
            assert door.get(f"/api/matched/{d['_id']}").status_code == 404
            if d.get("paper_id"):
                assert door.get(f"/api/matched/paper/{d['paper_id']}").status_code == 404
        switch = door.get("/api/app/switches").json()["matched"]
    print(f"production-like server on this database: {len(samples)} samples kept in, {len(listed['shifts'])} shifts given out, card on = {switch}")  # `pytest -s`
    if card.get("by") not in matched.CARD_BY:  # nobody but the samples switched the card here: "auto" decides
        assert switch is matched.auto_on(bool(listed["shifts"]), last, matched.ist_day())
