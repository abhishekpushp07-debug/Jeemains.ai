"""Matched: the copy of the website's shifts (matched.sync_site), the one part of Matched that WRITES.

Run against an in-memory stand-in for the two collections and a stand-in for the website's doors, so nothing is read
from the website and nothing is written to any real collection. What is not covered here: the real request to the
website (`matched._site`); the website has no Matched doors yet, so that is first exercised when they exist."""
import asyncio
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matched  # noqa: E402

S1, S2 = "2027-01-25-s1", "2027-01-25-s2"
HAND = {"_id": "2027-01-20-s1", "published": True, "updated_at": 3, "items": []}                  # written by hand: no source
SAMPLE = {"_id": "2027-01-22-s1", "published": True, "sample": True, "updated_at": 3, "items": []}  # the preview's sample


class Coll:
    def __init__(self, docs=()):
        self.docs = {d["_id"]: copy.deepcopy(d) for d in docs}

    @staticmethod
    def _hit(doc, query):
        return all(doc.get(k) in v["$in"] if isinstance(v, dict) and "$in" in v else doc.get(k) == v for k, v in query.items())

    @staticmethod
    def _apply(doc, change):
        doc.update(copy.deepcopy(change.get("$set", {})))
        for key in change.get("$unset", {}):
            doc.pop(key, None)

    def find(self, query, fields=None):
        rows = [copy.deepcopy(d) for d in self.docs.values() if self._hit(d, query)]

        async def each():
            for row in rows:
                yield row
        return each()

    async def update_one(self, query, change, upsert=False):
        for doc in self.docs.values():
            if self._hit(doc, query):
                return self._apply(doc, change)
        if upsert:
            doc = {k: v for k, v in query.items() if not isinstance(v, dict)}
            self._apply(doc, change)
            self.docs[doc["_id"]] = doc

    async def update_many(self, query, change):
        for doc in self.docs.values():
            if self._hit(doc, query):
                self._apply(doc, change)


class Db:
    def __init__(self, shifts=()):
        self.matched_shifts, self.rf_meta = Coll(shifts), Coll()


def shift(sid, stamp, **more):
    ours = {"text": "Ours", "options": ["a", "b"], "correct": 1, "source": "AITS Day 12 · Q 7", "question_id": "q-000001"}
    return {"id": sid, "asked": 75, "updated_at": stamp, "paper_id": "paper-0001", "secret": "never kept",
            "items": [{"n": 1, "subject": "Physics", "jee": {"text": "JEE"}, "ours": [ours]}], **more}


def website(monkeypatch, answers):
    """The website's doors answer from `answers` ({path: answer}); returns the list of paths that were asked."""
    asked = []

    async def door(client, path):
        asked.append(path)
        return copy.deepcopy(answers.get(path))
    monkeypatch.setattr(matched, "_site", door)
    return asked


def one_pass(db):
    return asyncio.run(matched.sync_site(db, None))


def test_nothing_changes_while_the_website_has_no_doors_or_answers_something_else(monkeypatch):
    db = Db([HAND, SAMPLE, {"_id": S1, "published": True, "source": "website", "updated_at": 5, "items": []}])
    before = copy.deepcopy(db.matched_shifts.docs)
    for answer in (None, [], "x", {}, {"shifts": "x"}, {"shifts": None}, {"error": "boom"}):
        website(monkeypatch, {"matched": answer})
        assert one_pass(db) is False
    # Above all: a website that is down or answers nonsense must not take a published shift away from students.
    assert db.matched_shifts.docs == before and db.rf_meta.docs == {}


def test_a_shift_is_copied_and_read_again_only_when_the_website_changed_it(monkeypatch):
    answers = {"matched": {"shifts": [{"id": S1, "updated_at": 5}, {"id": S2, "updated_at": 5}, {"id": "not-a-shift"}]},
               f"matched/{S1}": shift(S1, 5)}  # S2 is listed, but its own door does not answer
    asked = website(monkeypatch, answers)
    db = Db([{"_id": S1, "published": True, "sample": True, "updated_at": 1, "items": []}])  # a preview sample with the same id
    assert one_pass(db) is True
    doc = db.matched_shifts.docs[S1]
    assert doc["source"] == "website" and doc["published"] is True and "sample" not in doc
    assert (doc["asked"], doc["updated_at"], doc["paper_id"], len(doc["items"])) == (75, 5, "paper-0001", 1)
    assert set(doc) == {"_id", "asked", "updated_at", "paper_id", "items", "published", "source", "synced_at"}  # nothing else is kept
    assert S2 not in db.matched_shifts.docs and "not-a-shift" not in db.matched_shifts.docs
    assert matched.shape_shift(doc)["paper_questions"] == 1  # what students then get: the paper, with one of ours in it

    asked.clear()
    assert one_pass(db) is True
    assert asked == ["matched", f"matched/{S2}"]  # S1 has not changed: not read again; S2 is still wanted

    answers["matched"]["shifts"][0]["updated_at"] = 6
    answers[f"matched/{S1}"] = shift(S1, 6, asked=90)
    asked.clear()
    assert one_pass(db) is True
    assert f"matched/{S1}" in asked and db.matched_shifts.docs[S1]["asked"] == 90 and db.matched_shifts.docs[S1]["updated_at"] == 6


def test_a_shift_the_website_takes_back_is_hidden_never_deleted_and_others_are_left_alone(monkeypatch):
    db = Db([HAND, SAMPLE, {"_id": S1, "published": True, "source": "website", "updated_at": 5, "synced_at": 1, "items": []}])
    website(monkeypatch, {"matched": {"shifts": []}})
    assert one_pass(db) is True
    assert db.matched_shifts.docs[S1]["published"] is False
    assert set(db.matched_shifts.docs) == {HAND["_id"], SAMPLE["_id"], S1}
    assert db.matched_shifts.docs[HAND["_id"]] == HAND and db.matched_shifts.docs[SAMPLE["_id"]] == SAMPLE

    # Published again on the website: it comes back.
    website(monkeypatch, {"matched": {"shifts": [{"id": S1, "updated_at": 5}]}, f"matched/{S1}": shift(S1, 5)})
    assert one_pass(db) is True and db.matched_shifts.docs[S1]["published"] is True


def test_only_the_three_words_switch_homes_card(monkeypatch):
    db = Db()
    website(monkeypatch, {"matched": {"shifts": []}})
    assert one_pass(db) is True and db.rf_meta.docs == {}  # no word from the website: the switch is not touched
    for word, kept in (("off", "off"), ("banana", "off"), (None, "off"), (True, "off"), ("on", "on"), ("auto", "auto")):
        website(monkeypatch, {"matched": {"shifts": [], "card": word}})
        assert one_pass(db) is True
        assert db.rf_meta.docs[matched.CARD_META]["value"] == kept


def test_at_most_twenty_shifts_are_read_in_one_pass(monkeypatch):
    ids = [f"2027-01-{day:02d}-s{n}" for day in range(10, 25) for n in (1, 2)]  # 30 shifts
    asked = website(monkeypatch, {"matched": {"shifts": [{"id": i, "updated_at": 1} for i in ids]}, **{f"matched/{i}": shift(i, 1) for i in ids}})
    db = Db()
    assert one_pass(db) is True
    assert len(asked) == 1 + matched.SITE_BATCH == 21 and len(db.matched_shifts.docs) == 20
    assert one_pass(db) is True and len(db.matched_shifts.docs) == 30
