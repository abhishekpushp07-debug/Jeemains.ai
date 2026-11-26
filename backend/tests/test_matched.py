"""Matched: GET /api/matched, GET /api/matched/<shift>, and the `matched` switch in GET /api/app/switches.
The shaping is checked on plain dicts. The database path uses ONE fixture shift of the year 2001 (always the same id),
which this file publishes, reads and takes back by setting published to false: nothing is ever deleted."""
import asyncio
import os
import sys
from pathlib import Path

import requests
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matched  # noqa: E402

BASE = os.environ["EXPO_BACKEND_URL"].rstrip("/") + "/api"
FIX = "2001-01-01-s1"


def item(n=None, subject="Physics", **change):
    row = {"n": n, "subject": subject, "chapter": "Kinematics",
           "jee": {"text": "A ball is thrown up at $20\\,m/s$. Time to reach the top is", "options": ["1 s", "2 s", "3 s", "4 s"], "correct": 2,
                   "solution": "At the top $v = 0$, so $t = u/g = 2$ s."},
           "ours": [{"text": "A stone is thrown up at $30\\,m/s$. Time to reach the top is", "options": ["1 s", "2 s", "3 s", "4 s"], "correct": "c",
                     "source": "AITS Day 12 · Q 7", "tag": "Same concept", "solution": "At the top v = 0, so t = u/g.",
                     "solution_images": ["https://cdn.example/s7.png"]}]}
    row.update(change)
    return row


def test_a_question_keeps_only_what_the_app_can_draw():
    good = matched.shape_item({**item(12), "secret": "x", "jee": {**item()["jee"], "internal_id": 99, "images": [
        {"url": "https://cdn.example/q12.png", "w": 800, "h": 300}, "https://cdn.example/plain.png", {"url": "http://cdn.example/not-https.png"},
        {"url": "javascript:alert(1)"}, {"url": "https://cdn.example/half.png", "w": 800}]}})
    assert set(good) == {"n", "subject", "chapter", "jee", "ours"} and good["n"] == 12
    side = {"text", "options", "images", "correct", "answer", "solution", "solution_images"}
    assert set(good["jee"]) == side and set(good["ours"][0]) == side | {"source", "tag", "qid"}
    # The right option is kept as its place from 0, whether it was written as a place from 1 or as a letter.
    assert good["jee"]["correct"] == 1 and good["ours"][0]["correct"] == 2
    assert good["jee"]["solution"].startswith("At the top") and good["ours"][0]["solution_images"] == [{"url": "https://cdn.example/s7.png", "w": None, "h": None}]
    for wrong in (0, 5, "E", "AB", True, None, 1.0, "2"):
        assert matched.shape_item({**item(), "jee": {**item()["jee"], "correct": wrong}})["jee"]["correct"] is None
    # One option without words: no option is shown (a missing one would move the letters), so no option is marked right.
    holed = matched.shape_item({**item(), "jee": {**item()["jee"], "options": ["1 s", "", "3 s"], "answer": "2 s"}})["jee"]
    assert holed["options"] == [] and holed["correct"] is None and holed["answer"] == "2 s"
    assert good["jee"]["images"] == [{"url": "https://cdn.example/q12.png", "w": 800, "h": 300}, {"url": "https://cdn.example/plain.png", "w": None, "h": None},
                                     {"url": "https://cdn.example/half.png", "w": None, "h": None}]
    assert good["ours"][0]["source"] == "AITS Day 12 · Q 7" and good["ours"][0]["tag"] == "Same concept"

    # One of ours given as a single question (not a list) is accepted; a subject the app has no colour for becomes "".
    one = matched.shape_item({**item(subject="Biology"), "ours": item()["ours"][0]})
    assert one["subject"] == "" and len(one["ours"]) == 1 and one["n"] is None
    # A question shown only as a picture is fine; one with neither words nor a picture is not a question.
    assert matched.shape_item({**item(), "jee": {"images": ["https://cdn.example/a.png"]}})["jee"]["text"] == ""
    for bad in (None, "x", {}, {**item(), "jee": {"text": "  "}}, {**item(), "ours": []}, {**item(), "ours": [{"text": ""}]}, {**item(), "jee": None}):
        assert matched.shape_item(bad) is None
    # Sizes are capped, so one runaway row cannot make a screen the phone cannot draw.
    big = matched.shape_item({**item(), "jee": {"text": "x" * 9000, "options": ["o"] * 9, "images": ["https://c.example/%d.png" % i for i in range(9)]},
                              "ours": item()["ours"] * 9})
    assert len(big["jee"]["text"]) == 6000 and len(big["jee"]["options"]) == 6 and len(big["jee"]["images"]) == 6 and len(big["ours"]) == 4


def test_a_shift_counts_only_good_questions_and_reads_day_and_shift_from_its_id():
    doc = {"_id": "2027-01-25-s2", "asked": 75, "published": True, "updated_at": 1800000000.7,
           "items": [item(40, "Chemistry"), {"n": 3}, item(None, "Mathematics"), item(7), item(7, "Physics", chapter="Units")]}
    s = matched.shape_shift(doc)
    assert (s["id"], s["day"], s["shift"], s["asked"], s["matched"], s["updated_at"]) == ("2027-01-25-s2", "2027-01-25", 2, 75, 4, 1800000000)
    assert [i["n"] for i in s["items"]] == [7, 7, 40, None] and [i["chapter"] for i in s["items"][:2]] == ["Kinematics", "Units"]
    assert s["subjects"] == [{"name": "Physics", "n": 2}, {"name": "Chemistry", "n": 1}, {"name": "Mathematics", "n": 1}]
    # "asked" smaller than what matched cannot be true: it is left out rather than shown.
    assert matched.shape_shift({**doc, "asked": 2})["asked"] is None and matched.shape_shift({**doc, "asked": "75"})["asked"] is None
    assert matched.shape_shift({"_id": "2027-01-25-s1"}) == {"id": "2027-01-25-s1", "day": "2027-01-25", "shift": 1, "asked": None, "matched": 0,
                                                          "paper_id": "", "paper_questions": 0, "subjects": [], "updated_at": 0, "items": []}
    for bad in ("2027-13-45-s1", "2027-01-25", "2027-01-25-s0", "x", 5, None):
        assert matched.shape_shift({"_id": bad, "items": [item(1)]}) is None


def test_the_card_is_on_from_the_day_after_the_series_ends():
    assert not matched.over("2027-01-27", "2027-01-26") and not matched.over("2027-01-27", "2027-01-27")
    assert matched.over("2027-01-27", "2027-01-28") and matched.over("2027-01-27", "2027-04-02")
    assert not matched.over(None, "2027-01-28")  # the series' last day is not known: the All India card stays
    # "auto": with a published shift the card is on while the series still runs; with none, by the series' last day.
    assert matched.auto_on(True, "2027-01-27", "2027-01-21") and matched.auto_on(True, None, "2027-01-21")
    assert not matched.auto_on(False, "2027-01-27", "2027-01-27") and matched.auto_on(False, "2027-01-27", "2027-01-28")
    assert not matched.auto_on(False, None, "2027-01-28")
    # The switch kept in Mongo wins over the one in the code, but only when it is one of the three words.
    assert matched.card_mode("on", "auto") == "on" and matched.card_mode("off", "on") == "off" and matched.card_mode("auto", "on") == "auto"
    assert matched.card_mode(None, "auto") == "auto" and matched.card_mode("yes", "off") == "off" and matched.card_mode(True, "off") == "off"


class _Rows:
    """A stand-in for a Mongo collection: `find().sort().to_list()` gives the documents, `find_one()` the first."""
    def __init__(self, docs):
        self.docs = docs

    def find(self, *_):
        return self

    def sort(self, *_):
        return self

    async def to_list(self, _):
        return self.docs

    async def find_one(self, *_):
        return self.docs[0] if self.docs else None


def test_the_first_published_shift_turns_the_card_on_while_the_series_runs(monkeypatch):
    monkeypatch.setattr(matched, "ist_day", lambda: "2027-01-21")  # a day of the series (it ends on 27 Jan)
    monkeypatch.setattr(matched, "_series", {"last": "2027-01-27", "loaded": True})
    shift = {"_id": "2027-01-21-s1", "published": True, "items": [item(1)]}

    def card(shifts, owner=None, code="auto"):
        # Nothing remembered from the call before: neither the owner's word nor the list of shifts.
        monkeypatch.setattr(matched, "_owner", {"value": None, "read": float("-inf")})
        monkeypatch.setattr(matched, "cache", matched.MetadataCache())
        db = type("Db", (), {"matched_shifts": _Rows(shifts), "rf_meta": _Rows([{"value": owner}] if owner else [])})()
        return asyncio.run(matched.card_on(db, code))

    assert not card([])  # no shift yet: the All India card stays
    assert card([shift])  # the first shift is published: Matched, the same day
    assert not card([{"_id": "not-a-shift", "published": True, "items": [item(1)]}])  # nothing the list can show
    assert not card([shift], owner="off") and not card([shift], code="off")  # "off" still wins
    assert card([], owner="on") and card([], code="on")
    monkeypatch.setattr(matched, "ist_day", lambda: "2027-01-28")  # the series is over: on, also with no shift
    assert card([])


def test_public_routes_answer_without_sign_in():
    r = requests.get(f"{BASE}/matched", timeout=30)
    assert r.status_code == 200  # (its Cache-Control is rewritten by the preview's own gateway, so it is not checked here)
    body = r.json()
    assert set(body) == {"total", "updated_at", "shifts"} and isinstance(body["shifts"], list)
    assert body["total"] == sum(s["matched"] for s in body["shifts"])
    for s in body["shifts"]:
        assert set(s) == {"id", "day", "shift", "asked", "matched", "paper_id", "paper_questions", "subjects", "updated_at"}
    assert requests.get(f"{BASE}/matched/1999-01-01-s1", timeout=30).status_code == 404
    assert requests.get(f"{BASE}/matched/today", timeout=30).status_code == 422
    switches = requests.get(f"{BASE}/app/switches", timeout=30).json()
    assert isinstance(switches["pictures"], int) and isinstance(switches["matched"], bool)


def test_a_published_shift_is_read_and_a_taken_back_one_is_not():
    async def run():
        client = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = client[os.environ["DB_NAME"]]
        try:
            await db.matched_shifts.replace_one({"_id": FIX}, {"_id": FIX, "asked": 75, "published": True, "updated_at": 978307200,
                                                               "items": [item(2), item(1, "Chemistry"), {"jee": {}}]}, upsert=True)
            index = await matched.load_index(db)
            row = next(s for s in index["shifts"] if s["id"] == FIX)
            assert (row["day"], row["shift"], row["asked"], row["matched"]) == ("2001-01-01", 1, 75, 2) and "items" not in row
            assert index["shifts"] == sorted(index["shifts"], key=lambda s: s["id"], reverse=True)
            shift = await matched.load_shift(db, FIX)
            assert [i["n"] for i in shift["items"]] == [1, 2] and shift["items"][0]["ours"][0]["source"] == "AITS Day 12 · Q 7"
        finally:
            await db.matched_shifts.update_one({"_id": FIX}, {"$set": {"published": False}})
        assert FIX not in [s["id"] for s in (await matched.load_index(db))["shifts"]]
        assert await matched.load_shift(db, FIX) is None
        client.close()

    asyncio.run(run())
