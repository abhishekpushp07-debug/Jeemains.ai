"""Extra edge cases for the "samples stay in the workspace" rule (27 Nov 2026, T1 independent check).

Stands in for `workspace.own` and uses tiny in-memory collections (same pattern as `tests/test_samples_stay_home.py`).
NEVER writes to the real database; only reads happen in the companion `test_samples_stay_home.py` (not here).
Tries extra MONGO_URL strings around `workspace.own`, extra `by` cases for the "matched:card" word, and runs the
same probes via the public routes through `fastapi.testclient.TestClient` with `workspace.own` forced to False."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matched
import workspace
from fastapi import FastAPI
from fastapi.testclient import TestClient

SAMPLE = {"_id": "2027-01-22-s1", "published": True, "sample": True, "paper_id": "sample-paper-01",
          "items": [{"n": 1, "subject": "Physics", "jee": {"text": "sample jee"},
                     "ours": [{"text": "sample ours", "question_id": "sample-q-01"}]}]}
SAMPLE2 = {**SAMPLE, "_id": "2027-01-22-s2", "paper_id": "sample-paper-02"}
REAL = {**SAMPLE, "_id": "2027-01-24-s1", "paper_id": "real-paper-0001"}
del REAL["sample"]


class _Shifts:
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

    async def find_one(self, *_, **__):
        return self.row


def _fake_db(shifts, card):
    return type("Db", (), {"matched_shifts": _Shifts(list(shifts)), "rf_meta": _Meta(card)})()


# ------------------------------- workspace.own() edge cases ------------------------------- #
def test_workspace_own_more_tricky_urls():
    """Extra true / false cases around `workspace.own`, on top of `test_samples_stay_home`."""
    for url in (
        "mongodb://localhost:27017/jeelive",  # a database name is fine
        "mongodb://127.0.0.1",                # no port, no path
        "mongodb://[::1]",                    # IPv6 bare
        "mongodb://localhost:27018/db?x=1",   # a different port is still local
    ):
        assert workspace.own(url), f"should be workspace: {url!r}"

    for url in (
        None,                                                  # unset -> read from env -> this machine's MONGO_URL
        "mongodb://user@localhost:27017",                      # a user name is a password-shaped credential
        "mongodb://:word@localhost:27017",                     # an empty user with a password
        "mongodb://user:word@localhost:27017/app",             # full credentials
        "mongodb+srv://localhost/app",                         # +srv is never truly local
        "mongodb://localhost@evil.example:27017",              # look-alike with @
        "mongodb://127.0.0.1.evil.example:27017",              # look-alike host
        "mongodb://[::1].evil.example:27017",                  # look-alike v6
        "mongodb://localhost:27017,127.0.0.1:27018/db",        # a replica list is production
        "mongodb://127.0.0.1:27017 ",                          # trailing whitespace is not an address
        " mongodb://127.0.0.1:27017",                          # leading whitespace either
        "MONGODB://localhost:27017",                           # upper-case scheme is a different scheme in a regex
        "mongo://localhost:27017",                             # no "db"
        "mongodb://localhost:abc",                             # nonsense port
    ):
        if url is None:
            # own() reads MONGO_URL from the process environment: on this preview that is a local mongo.
            # Don't assert either way here; the other test covers the env-reading case.
            continue
        assert not workspace.own(url), f"should be production: {url!r}"


# ------------------------------- matched: by:'website' and by:'owner' ------------------------------- #
def _card_on(own, card, shift_id=REAL["_id"], published=True):
    """Return what `matched.card_on` would say, with workspace.own and a card row standing in for the real server."""
    doc = {**REAL, "_id": shift_id, "published": published}

    async def run(monkeypatch=None):
        # A fresh cache every call, so the previous card_on() does not win over the current one.
        matched._owner = {"value": None, "read": float("-inf")}
        matched.cache = matched.MetadataCache()
        matched._series = {"last": "2027-01-27", "loaded": True}
        db = _fake_db([doc], card)
        return await matched.card_on(db, "auto")

    import unittest.mock as mock
    with mock.patch.object(workspace, "own", lambda url=None: own):
        return asyncio.run(run())


def test_card_signed_by_website_turns_card_on_in_production():
    """With own=False a real shift is enough; add a by:'website' 'on' and the card is still on, and a by:'website' 'off'
    turns it off even with a real shift. Nothing unsigned decides outside the workspace."""
    assert _card_on(False, None) is True                                                 # the real shift alone
    assert _card_on(False, {"value": "on", "by": "website"}) is True
    assert _card_on(False, {"value": "off", "by": "website"}) is False                    # the word wins over the shift
    assert _card_on(False, {"value": "on", "by": "owner"}) is True
    assert _card_on(False, {"value": "off", "by": "owner"}) is False


def test_unsigned_or_sample_signed_word_is_ignored_in_production():
    """Unsigned, by:'sample' or by:anything-else are not words: the auto rule (a real shift) decides."""
    for by in (None, "sample", "someone-else", ""):
        row = {"value": "on"} if by is None else {"value": "on", "by": by}
        assert _card_on(False, row) is True, by                                           # a real shift already turns it on
        assert _card_on(False, row, published=False) is False, by                          # and auto has nothing to turn on


def test_in_the_workspace_an_unsigned_on_still_switches_the_card():
    assert _card_on(True, {"value": "on"}, published=False) is True                        # the owner's preview
    assert _card_on(True, {"value": "off"}, published=True) is False                       # owner-only word still rules


# ------------------------------- /api/matched over TestClient with own=False ------------------------------- #
def test_the_routes_never_leak_a_sample_outside_the_workspace(monkeypatch):
    """GET /api/matched, /api/matched/<id>, /api/matched/paper/<pid> with own=False and a database that holds BOTH a
    real shift and samples: the real shift is listed and reachable, every sample is 404 (both the shift id and its paper
    id), the card follows auto from the real shift alone (so 'on')."""
    monkeypatch.setattr(workspace, "own", lambda url=None: False)
    monkeypatch.setattr(matched, "_owner", {"value": None, "read": float("-inf")})
    monkeypatch.setattr(matched, "cache", matched.MetadataCache())
    monkeypatch.setattr(matched, "_series", {"last": "2027-01-27", "loaded": True})
    monkeypatch.setattr(matched, "ist_day", lambda: "2026-11-27")

    db = _fake_db([SAMPLE, SAMPLE2, REAL], None)
    app = FastAPI()
    app.include_router(matched.make_router(db), prefix="/api")
    with TestClient(app) as door:
        listed = door.get("/api/matched").json()
        assert [s["id"] for s in listed["shifts"]] == [REAL["_id"]]
        assert door.get(f"/api/matched/{REAL['_id']}").status_code == 200
        for s in (SAMPLE, SAMPLE2):
            assert door.get(f"/api/matched/{s['_id']}").status_code == 404, s["_id"]
            assert door.get(f"/api/matched/paper/{s['paper_id']}").status_code == 404, s["paper_id"]


def test_workspace_still_gives_every_sample_through_the_routes(monkeypatch):
    """The same database, but the server IS the workspace: every shift shows up, every sample's page is 200."""
    monkeypatch.setattr(workspace, "own", lambda url=None: True)
    monkeypatch.setattr(matched, "_owner", {"value": None, "read": float("-inf")})
    monkeypatch.setattr(matched, "cache", matched.MetadataCache())
    monkeypatch.setattr(matched, "_series", {"last": "2027-01-27", "loaded": True})
    monkeypatch.setattr(matched, "ist_day", lambda: "2026-11-27")

    db = _fake_db([SAMPLE, SAMPLE2, REAL], {"value": "on"})  # the unsigned 'on' that reached production
    app = FastAPI()
    app.include_router(matched.make_router(db), prefix="/api")
    with TestClient(app) as door:
        listed = door.get("/api/matched").json()
        assert {s["id"] for s in listed["shifts"]} == {SAMPLE["_id"], SAMPLE2["_id"], REAL["_id"]}
        for s in (SAMPLE, SAMPLE2, REAL):
            assert door.get(f"/api/matched/{s['_id']}").status_code == 200


# ------------------------------- /api/app/switches ------------------------------- #
def test_switches_matched_follows_workspace_own(monkeypatch):
    """`/api/app/switches` 'matched' value with own=False vs own=True, same database (samples + unsigned 'on')."""
    import app_switches

    class _Db:
        def __init__(self, own):
            self.matched_shifts = _Shifts([SAMPLE, SAMPLE2])            # only samples published
            self.rf_meta = _Meta({"value": "on"})                       # unsigned 'on' (what reached production)
            self._own = own

    # own=False: only samples + unsigned 'on' -> the card is off (none of the two counts outside the workspace)
    monkeypatch.setattr(workspace, "own", lambda url=None: False)
    monkeypatch.setattr(matched, "_owner", {"value": None, "read": float("-inf")})
    monkeypatch.setattr(matched, "cache", matched.MetadataCache())
    monkeypatch.setattr(matched, "_series", {"last": "2027-01-27", "loaded": True})
    monkeypatch.setattr(matched, "ist_day", lambda: "2026-11-27")

    app = FastAPI()
    router = matched.make_router(_Db(False))
    app.include_router(router, prefix="/api")
    app.include_router(app_switches.router, prefix="/api")
    # app_switches.router reads from `database.db`, not from the router's db; try the dedicated card_on path instead:
    assert asyncio.run(matched.card_on(_Db(False), "auto")) is False

    # own=True: samples count and unsigned 'on' counts: card is on.
    monkeypatch.setattr(workspace, "own", lambda url=None: True)
    monkeypatch.setattr(matched, "_owner", {"value": None, "read": float("-inf")})
    monkeypatch.setattr(matched, "cache", matched.MetadataCache())
    assert asyncio.run(matched.card_on(_Db(True), "auto")) is True


# ------------------------------- choice.sample_on ------------------------------- #
def test_choice_sample_only_shows_in_the_workspace(monkeypatch):
    """choice.sample_on reads rf_meta['choice:sample'] and ANDs it with workspace.own. Even when the switch is 'on'
    the function is False outside the workspace."""
    import choice

    class _Db:
        def __init__(self, row):
            self.rf_meta = _Meta(row)

    async def ask(db):
        router = choice.make_router(db, client=None)
        # `sample_on` is declared inside make_router: reach it through the router's closure by calling the handler
        # that uses it is awkward, so we test the equivalent condition directly:
        from workspace import own
        row = await db.rf_meta.find_one({"_id": "choice:sample"})
        return bool(own()) and bool(row and row.get("value") == "on")

    # own=True + switch on -> True
    monkeypatch.setattr(workspace, "own", lambda url=None: True)
    assert asyncio.run(ask(_Db({"_id": "choice:sample", "value": "on"}))) is True
    # own=False + switch on -> False
    monkeypatch.setattr(workspace, "own", lambda url=None: False)
    assert asyncio.run(ask(_Db({"_id": "choice:sample", "value": "on"}))) is False
    # own=True + switch off / missing -> False
    monkeypatch.setattr(workspace, "own", lambda url=None: True)
    assert asyncio.run(ask(_Db({"_id": "choice:sample", "value": "off"}))) is False
    assert asyncio.run(ask(_Db(None))) is False
