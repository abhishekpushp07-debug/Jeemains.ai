"""Immutable, idempotent learning events. Queries are scoped to one learner + exam."""
import random
import sys
import time
from collections import OrderedDict, namedtuple
from typing import Optional

from fastapi import APIRouter, Header

from exam_groups import SUBJECTS, Exam, require_active_exam
from metadata_cache import metadata_cache
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
_marks: OrderedDict = OrderedDict()  # (uid, exam) -> (learning events, newest (completed_at, ref) read, {card: Mark})


def _apply(marks: dict, results: list):
    """One more round, in play order: the same sums the full pass makes ($last subject/chapter/outcome, tries, misses)."""
    for r in results:
        m = marks.get(r["card_id"])
        marks[r["card_id"]] = Mark(r["card_id"], sys.intern(r["subject"]), sys.intern(r["chapter"]), sys.intern(r["outcome"]),
                                   (m.tries if m else 0) + 1, (m.misses if m else 0) + (r["outcome"] in ("incorrect", "timed_out")))


async def card_marks(db, uid, exam) -> list:
    """Every card this student has answered: where it belongs, the latest outcome, tries and misses.
    Learning events are never changed once written, so the pass over the student's whole history is made once; after
    each finished round only the rounds that came after it are read and added (one or two rows instead of thousands).
    A round recorded late (it sorts before rounds already read) makes a full pass again, so the answer is always the same."""
    events = await db.rf_learning_events.count_documents({"uid": uid, "exam": exam})
    key = (uid, exam)
    hit = _marks.get(key)
    if hit and hit[0] == events:
        _marks.move_to_end(key)
        return list(hit[2].values())
    marks = last = None
    if hit and hit[1] and events > hit[0]:
        newer = await db.rf_learning_events.find({"uid": uid, "exam": exam, "completed_at": {"$gte": hit[1][0]}},
                                                 {"_id": 0, "completed_at": 1, "ref": 1, "results": 1}).sort([("completed_at", 1), ("ref", 1)]).to_list(None)
        fresh = [e for e in newer if (e["completed_at"], e["ref"]) > hit[1]]
        if len(fresh) == events - hit[0]:
            marks = dict(hit[2])
            for e in fresh:
                _apply(marks, e.get("results") or [])
            last = (fresh[-1]["completed_at"], fresh[-1]["ref"])
    if marks is None:
        rows = await (await db.rf_learning_events.aggregate([
            {"$match": {"uid": uid, "exam": exam}},
            {"$sort": {"completed_at": 1, "ref": 1}},
            {"$unwind": "$results"},
            {"$group": {"_id": "$results.card_id", "subject": {"$last": "$results.subject"}, "chapter": {"$last": "$results.chapter"},
                        "latest": {"$last": "$results.outcome"}, "tries": {"$sum": 1},
                        "misses": {"$sum": {"$cond": [{"$in": ["$results.outcome", ["incorrect", "timed_out"]]}, 1, 0]}}}},
        ])).to_list(None)
        marks = {r["_id"]: Mark(r["_id"], sys.intern(r["subject"]), sys.intern(r["chapter"]), sys.intern(r["latest"]), r["tries"], r["misses"]) for r in rows}
        newest = await db.rf_learning_events.find_one({"uid": uid, "exam": exam}, {"_id": 0, "completed_at": 1, "ref": 1}, sort=[("completed_at", -1), ("ref", -1)])
        last = (newest["completed_at"], newest["ref"]) if newest and isinstance(newest.get("completed_at"), str) else None
    _marks[key] = (events, last, marks)
    _marks.move_to_end(key)
    while len(_marks) > MARKS_SIZE:
        _marks.popitem(last=False)
    return list(marks.values())


_live: dict = {}  # exam -> (the subject maps it was made from, one map of them all)


async def live_cards(db, exam) -> dict:
    """card id -> [subject, chapter, subtopic] of every card that can be dealt now, kept like the deal pools (one map per
    subject, 2 minutes, then reloaded behind the scenes). Weak lists look their cards up here instead of in the database:
    a long history used to read thousands of cards on every lobby open."""
    maps = []
    for subject in SUBJECTS[exam]:
        async def load(subject=subject):
            return {c["id"]: [c["subject"], c["chapter"], c.get("topic") or ""] async for c in db.rf_cards.find(
                {"exam": exam, "subject": subject, "retired": {"$ne": True}}, {"_id": 0, "id": 1, "subject": 1, "chapter": 1, "topic": 1}).batch_size(2000)}
        maps.append((await metadata_cache.get_or_load(f"{db.name}:live:{exam}:{subject}", load, ttl=120))[0])
    hit = _live.get(exam)
    if hit and len(hit[0]) == len(maps) and all(a is b for a, b in zip(hit[0], maps)):
        return hit[1]
    merged = {}
    for m in maps:
        merged.update(m)
    _live[exam] = (maps, merged)
    return merged


async def weak_chapters(db, uid, exam):
    """Chapters with cards still missed (wrong or timed out, and not answered right since), most missed first."""
    missed = [m for m in await card_marks(db, uid, exam) if m.latest != "correct" and m.misses > 0]
    live = await live_cards(db, exam) if missed else {}
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
    live = await live_cards(db, exam) if by_card else {}
    topics = {}
    for cid, m in by_card.items():
        card = live.get(cid)
        if not card:
            continue
        key = (card[0], card[1], card[2] or card[1])
        t = topics.setdefault(key, {"subject": key[0], "chapter": key[1], "topic": key[2], "misses": 0, "tries": 0, "weak_ids": []})
        t["misses"] += m.misses
        t["tries"] += m.tries
        if m.misses and m.latest != "correct":
            t["weak_ids"].append(cid)
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