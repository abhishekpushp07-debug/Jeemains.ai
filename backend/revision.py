"""Immutable, idempotent learning events. Queries are scoped to one learner + exam."""
import random
import sys
import time
from collections import OrderedDict, namedtuple
from typing import Optional

from fastapi import APIRouter, Header

from exam_groups import Exam, require_active_exam
from scope import CARD_SECONDS


async def record_learning(db, uid, ref, exam, rows, cards, completed_at):
    by_id = {c["id"]: c for c in cards}
    results = []
    for row in rows:
        card = by_id.get(row.get("card_id"))
        if card and row["outcome"] in ("correct", "incorrect", "timed_out"):
            results.append({"card_id": card["id"], "subject": card["subject"],
                            "chapter": card["chapter"], "outcome": row["outcome"]})
    if results:
        await db.rf_learning_events.update_one({"uid": uid, "ref": ref}, {"$setOnInsert": {
            "exam": exam, "results": results, "completed_at": completed_at}}, upsert=True)


MEMO_SECONDS, MEMO_SIZE = 60, 5000
_memo: OrderedDict = OrderedDict()  # (what, uid, exam) -> (learning events, read_at, value)


async def remembered(db, what, uid, exam, load, empty):
    """A student's weak lists change only when they finish another round (one more learning event) or the bank changes.
    So the pass over their whole history runs once per finished round (and at most a minute later for a bank change);
    every other look - each time the lobby opens - costs one count read from the index. No finished round: no pass at all."""
    events = await db.rf_learning_events.count_documents({"uid": uid, "exam": exam})
    if not events:
        return empty
    key = (what, uid, exam)
    hit = _memo.get(key)
    if hit and hit[0] == events and time.monotonic() - hit[1] < MEMO_SECONDS:
        _memo.move_to_end(key)
        return hit[2]
    value = await load()
    _memo[key] = (events, time.monotonic(), value)
    _memo.move_to_end(key)
    while len(_memo) > MEMO_SIZE:
        _memo.popitem(last=False)
    return value


Mark = namedtuple("Mark", "card subject chapter latest tries misses")
MARKS_SIZE = 300
_marks: OrderedDict = OrderedDict()  # (uid, exam) -> (learning events, every card the student has answered)


async def card_marks(db, uid, exam) -> list:
    """Every card this student has answered: where it belongs, the latest outcome, tries and misses.
    Learning events are never changed once written, so this pass over the student's whole history is made once per
    finished round and then serves both weak lists (the lobby asks for both, and again a minute later for bank changes).
    Before, each list made its own pass every time, and one of them looked every missed card up one at a time."""
    events = await db.rf_learning_events.count_documents({"uid": uid, "exam": exam})
    hit = _marks.get((uid, exam))
    if hit and hit[0] == events:
        _marks.move_to_end((uid, exam))
        return hit[1]
    rows = await (await db.rf_learning_events.aggregate([
        {"$match": {"uid": uid, "exam": exam}},
        {"$sort": {"completed_at": 1, "ref": 1}},
        {"$unwind": "$results"},
        {"$group": {"_id": "$results.card_id", "subject": {"$last": "$results.subject"}, "chapter": {"$last": "$results.chapter"},
                    "latest": {"$last": "$results.outcome"}, "tries": {"$sum": 1},
                    "misses": {"$sum": {"$cond": [{"$in": ["$results.outcome", ["incorrect", "timed_out"]]}, 1, 0]}}}},
    ])).to_list(None)
    marks = [Mark(r["_id"], sys.intern(r["subject"]), sys.intern(r["chapter"]), sys.intern(r["latest"]), r["tries"], r["misses"]) for r in rows]
    _marks[(uid, exam)] = (events, marks)
    _marks.move_to_end((uid, exam))
    while len(_marks) > MARKS_SIZE:
        _marks.popitem(last=False)
    return marks


async def weak_chapters(db, uid, exam):
    """Chapters with cards still missed (wrong or timed out, and not answered right since), most missed first."""
    missed = [m for m in await card_marks(db, uid, exam) if m.latest != "correct" and m.misses > 0]
    live = {c["id"] async for c in db.rf_cards.find({"id": {"$in": [m.card for m in missed]}, "exam": exam, "retired": {"$ne": True}}, {"_id": 0, "id": 1})} if missed else set()
    chapters = {}
    for m in sorted((m for m in missed if m.card in live), key=lambda m: (-m.misses, m.card)):
        row = chapters.setdefault((m.subject, m.chapter), {"subject": m.subject, "chapter": m.chapter, "misses": 0, "card_ids": []})
        row["misses"] += m.misses
        row["card_ids"].append(m.card)
    rows = sorted(chapters.values(), key=lambda row: (-row["misses"], row["subject"], row["chapter"]))[:150]
    return [{**row, "remaining": len(row["card_ids"]), "card_ids": row["card_ids"][:30]} for row in rows]


# Weak Topic Sprint: the subtopics a student keeps missing (wrong or timed out), and a sprint dealt only from them.
MIN_MISSES, MAX_TOPICS = 2, 8


async def weak_topics(db, uid, exam):
    """Subtopics ranked by misses (then miss rate). "Frequently missed" = missed at least twice; when fewer than three
    subtopics reach that, the next most-missed ones fill in so a new student still gets a sprint."""
    by_card = {m.card: m for m in await card_marks(db, uid, exam)}
    topics = {}
    async for c in db.rf_cards.find({"id": {"$in": list(by_card)}, "exam": exam, "retired": {"$ne": True}}, {"_id": 0, "id": 1, "subject": 1, "chapter": 1, "topic": 1}):
        m, key = by_card[c["id"]], (c["subject"], c["chapter"], c.get("topic") or c["chapter"])
        t = topics.setdefault(key, {"subject": key[0], "chapter": key[1], "topic": key[2], "misses": 0, "tries": 0, "weak_ids": []})
        t["misses"] += m.misses
        t["tries"] += m.tries
        if m.misses and m.latest != "correct":
            t["weak_ids"].append(c["id"])
    # A subtopic stays weak while at least one of its missed cards has not been answered right since.
    ranked = sorted((t for t in topics.values() if t["weak_ids"]), key=lambda t: (-t["misses"], -t["misses"] / t["tries"], t["topic"]))
    often = [t for t in ranked if t["misses"] >= MIN_MISSES]
    return (often if len(often) >= 3 else ranked)[:MAX_TOPICS]


def topic_filter(exam, topics):
    # Cards with no subtopic of their own stand under their chapter's name.
    return {"exam": exam, "retired": {"$ne": True}, "$or": [{"subject": t["subject"], "chapter": t["chapter"],
            "topic": t["topic"] if t["topic"] != t["chapter"] else {"$in": ["", None, t["chapter"]]}} for t in topics]}


async def weak_topic_deck(db, uid, exam, count, seen):
    """Up to `count` cards from the weak subtopics only, taken in turn from each subtopic: the student's own still-missed
    cards first, then cards they have not met yet, then the rest. No prompt twice."""
    from rapid_deck import KINDS, fingerprint
    topics = await weak_topics(db, uid, exam)
    if not topics:
        return [], []
    lanes = {(t["subject"], t["chapter"], t["topic"]): [] for t in topics}
    weak = {cid for t in topics for cid in t["weak_ids"]}
    async for c in db.rf_cards.find(topic_filter(exam, topics), {"_id": 0}):
        if c.get("diagram") and c["diagram"].get("kind") not in KINDS:
            continue
        lane = lanes.get((c["subject"], c["chapter"], c.get("topic") or c["chapter"]))
        if lane is not None:
            lane.append(c)
    for lane in lanes.values():
        random.shuffle(lane)
        lane.sort(key=lambda c: (c["id"] not in weak, c["id"] in seen))
    deck, prints = [], set()
    while len(deck) < count and any(lanes.values()):
        for lane in lanes.values():
            while lane and len(deck) < count:
                c = lane.pop(0)
                if fingerprint(c["prompt"]) not in prints:
                    prints.add(fingerprint(c["prompt"]))
                    deck.append(c)
                    break
    return deck, topics


def make_router(db, rf_user):
    router = APIRouter(prefix="/rf")

    @router.get("/revision")
    async def revision(exam: Exam = "JEE", x_rf_user: Optional[str] = Header(None)):
        exam, uid = require_active_exam(exam), rf_user(x_rf_user)

        async def load():
            rows = await weak_chapters(db, uid, exam)
            return {"items": [{k: v for k, v in row.items() if k != "card_ids"} for row in rows], "remaining": sum(row["remaining"] for row in rows)}

        return {"exam": exam, **await remembered(db, "chapters", uid, exam, load, {"items": [], "remaining": 0}),
                "rule": "Wrong and timed-out cards from completed sprints and duels. Correct replays clear a card; skipped cards do not count."}

    @router.get("/weak-topics")
    async def weak_topic_list(exam: Exam = "JEE", x_rf_user: Optional[str] = Header(None)):
        exam, uid = require_active_exam(exam), rf_user(x_rf_user)

        async def load():
            deck, topics = await weak_topic_deck(db, uid, exam, 100, set())  # what a round can really deal (max 100)
            return {"cards": len(deck), "topics": [{k: v for k, v in t.items() if k != "weak_ids"} | {"missed": len(t["weak_ids"])} for t in topics]}

        body = await remembered(db, "topics", uid, exam, load, {"cards": 0, "topics": []})
        return {"exam": exam, "cards": body["cards"], "seconds": CARD_SECONDS, "topics": body["topics"],
                "rule": f"Subtopics you got wrong or ran out of time on at least {MIN_MISSES} times, most missed first. Only these subtopics are dealt."}

    return router