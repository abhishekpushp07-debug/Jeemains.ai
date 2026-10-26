"""Immutable, idempotent learning events. Queries are scoped to one learner + exam."""
from typing import Optional

from fastapi import APIRouter, Header

from exam_groups import Exam, require_active_exam


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
    rows = await db.rf_learning_events.aggregate([
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
    ]).to_list(150)
    return rows


def make_router(db, rf_user):
    router = APIRouter(prefix="/rf")

    @router.get("/revision")
    async def revision(exam: Exam = "JEE", x_rf_user: Optional[str] = Header(None)):
        exam = require_active_exam(exam)
        rows = await weak_chapters(db, rf_user(x_rf_user), exam)
        return {"exam": exam, "items": [{k: v for k, v in row.items() if k != "card_ids"} for row in rows],
                "remaining": sum(row["remaining"] for row in rows),
                "rule": "Wrong and timed-out cards from completed sprints and duels. Correct replays clear a card; skipped cards do not count."}

    return router