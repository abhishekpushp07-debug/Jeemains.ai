"""Immutable, idempotent learning events. Queries are scoped to one learner + exam."""
import random
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


async def weak_chapters(db, uid, exam):
    rows = await (await db.rf_learning_events.aggregate([
        {"$match": {"uid": uid, "exam": exam}},
        {"$sort": {"completed_at": 1, "ref": 1}},
        {"$unwind": "$results"},
        {"$group": {"_id": "$results.card_id", "subject": {"$last": "$results.subject"},
                    "chapter": {"$last": "$results.chapter"}, "latest": {"$last": "$results.outcome"},
                    "misses": {"$sum": {"$cond": [{"$in": ["$results.outcome", ["incorrect", "timed_out"]]}, 1, 0]}}}},
        {"$match": {"latest": {"$ne": "correct"}, "misses": {"$gt": 0}}},
        {"$lookup": {"from": "rf_cards", "localField": "_id", "foreignField": "id", "as": "card"}},
        {"$match": {"card": {"$elemMatch": {"exam": exam, "retired": {"$ne": True}}}}},
        {"$sort": {"misses": -1, "_id": 1}},
        {"$group": {"_id": {"subject": "$subject", "chapter": "$chapter"},
                    "misses": {"$sum": "$misses"}, "card_ids": {"$push": "$_id"}}},
        {"$sort": {"misses": -1, "_id.subject": 1, "_id.chapter": 1}},
        {"$project": {"_id": 0, "subject": "$_id.subject", "chapter": "$_id.chapter", "misses": 1,
                      "remaining": {"$size": "$card_ids"}, "card_ids": {"$slice": ["$card_ids", 30]}}},
    ])).to_list(150)
    return rows


# Weak Topic Sprint: the subtopics a student keeps missing (wrong or timed out), and a sprint dealt only from them.
MIN_MISSES, MAX_TOPICS = 2, 8


async def weak_topics(db, uid, exam):
    """Subtopics ranked by misses (then miss rate). "Frequently missed" = missed at least twice; when fewer than three
    subtopics reach that, the next most-missed ones fill in so a new student still gets a sprint."""
    rows = await (await db.rf_learning_events.aggregate([
        {"$match": {"uid": uid, "exam": exam}},
        {"$sort": {"completed_at": 1, "ref": 1}},
        {"$unwind": "$results"},
        {"$group": {"_id": "$results.card_id", "latest": {"$last": "$results.outcome"}, "tries": {"$sum": 1},
                    "misses": {"$sum": {"$cond": [{"$in": ["$results.outcome", ["incorrect", "timed_out"]]}, 1, 0]}}}},
    ])).to_list(20000)
    by_card = {r["_id"]: r for r in rows}
    topics = {}
    async for c in db.rf_cards.find({"id": {"$in": list(by_card)}, "exam": exam, "retired": {"$ne": True}}, {"_id": 0, "id": 1, "subject": 1, "chapter": 1, "topic": 1}):
        r, key = by_card[c["id"]], (c["subject"], c["chapter"], c.get("topic") or c["chapter"])
        t = topics.setdefault(key, {"subject": key[0], "chapter": key[1], "topic": key[2], "misses": 0, "tries": 0, "weak_ids": []})
        t["misses"] += r["misses"]
        t["tries"] += r["tries"]
        if r["misses"] and r["latest"] != "correct":
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
        exam = require_active_exam(exam)
        rows = await weak_chapters(db, rf_user(x_rf_user), exam)
        return {"exam": exam, "items": [{k: v for k, v in row.items() if k != "card_ids"} for row in rows],
                "remaining": sum(row["remaining"] for row in rows),
                "rule": "Wrong and timed-out cards from completed sprints and duels. Correct replays clear a card; skipped cards do not count."}

    @router.get("/weak-topics")
    async def weak_topic_list(exam: Exam = "JEE", x_rf_user: Optional[str] = Header(None)):
        exam = require_active_exam(exam)
        deck, topics = await weak_topic_deck(db, rf_user(x_rf_user), exam, 100, set())  # what a round can really deal (max 100)
        return {"exam": exam, "cards": len(deck), "seconds": CARD_SECONDS,
                "topics": [{k: v for k, v in t.items() if k != "weak_ids"} | {"missed": len(t["weak_ids"])} for t in topics],
                "rule": f"Subtopics you got wrong or ran out of time on at least {MIN_MISSES} times, most missed first. Only these subtopics are dealt."}

    return router