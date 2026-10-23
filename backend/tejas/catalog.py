"""Bounded, source-free catalogue projections and access filtering before pagination."""

from datetime import datetime, timezone
import re
from .db import sets

PROJECT = {
    "_id": 0,
    'chapter_book_id': 1, 'chapter_number': 1, 'chapter_subject': 1, 'solution_kind': 1,
    'start_at': 1, 'end_at': 1, 'live_enabled': 1,
    "id": 1,
    "title": 1,
    "exam": 1,
    "year": 1,
    "status": 1,
    "rules": 1,
    "version": 1,
    "source": 1,
    "attribution": 1,
    "created_at": 1,
    "audience": 1,
    "allowed_emails": 1,
    "allowed_phones": 1,
    "expires": 1,
    "questions.number": 1,
    "questions.type": 1,
    "questions.subject": 1,
    "questions.approved": 1,
    'questions.scoring': 1,
    'test_kind': 1, 'full_length': 1, 'mock_number': 1,
    "questions.disposition": 1,
}


def available(user=None, exam="", search=""):
    audiences = [{"audience": "all"}]
    if user:
        if user.get("email"):
            audiences.append(
                {"audience": "restricted", "allowed_emails": user["email"]}
            )
        if user.get("phone"):
            audiences.append(
                {"audience": "restricted", "allowed_phones": user["phone"]}
            )
    query = {
        "status": "published",
        "series_id": {"$exists": False},
        "series_import": {"$ne": True},
        "$and": [
            {'$or': [{'$and':[{'import_id': {'$exists': False}}, {'chapter_book_id': {'$exists': False}}]}, {'live_enabled': True, 'start_at': {'$lte': datetime.now(timezone.utc).timestamp()}, 'end_at': {'$gt': datetime.now(timezone.utc).timestamp()}}]},
            {"$or": audiences},
            {
                "$or": [
                    {"expires": {"$exists": False}},
                    {"expires": ""},
                    {
                        "expires": {
                            "$gte": datetime.now(timezone.utc).date().isoformat()
                        }
                    },
                ]
            },
        ],
    }
    if exam:
        query["exam"] = exam
    if search:
        query["title"] = {"$regex": re.escape(search[:100]), "$options": "i"}
    return query


async def page(query, page=1, size=20):
    return (
        await sets.find(query, PROJECT)
        .sort([("created_at", -1), ("id", 1)])
        .skip((max(1, min(page, 10000)) - 1) * size)
        .limit(size)
        .to_list(size)
    )


async def counts(query):
    rows = await sets.aggregate(
        [{"$match": query}, {"$group": {"_id": "$exam", "count": {"$sum": 1}}}]
    ).to_list(10)
    return {r["_id"]: r["count"] for r in rows}
