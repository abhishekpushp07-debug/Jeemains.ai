"""Non-destructive, restart-safe classification of saved pilot activity."""
from datetime import datetime, timezone

from revision import record_learning


async def migrate_exam_data(db):
    for collection in (db.rf_sessions, db.rf_duels):
        await collection.update_many({"exam": {"$exists": False}, "subject": "Biology"}, {"$set": {"exam": "NEET"}})
        await collection.update_many({"exam": {"$exists": False}, "subject": {"$ne": "Biology"}}, {"$set": {"exam": "JEE"}})
    # Legacy XP is rebuilt from persisted rewards, not guessed from the combined wallet.
    async for award in db.rf_awards.find({"exam": {"$exists": False}}, {"_id": 0}):
        kind, _, sid = award["ref"].partition(":")
        source = db.rf_sessions if kind == "solo" else db.rf_duels
        doc = await source.find_one({"id": sid}, {"_id": 0, "exam": 1, "winner": 1})
        if doc:
            await db.rf_awards.update_one({"uid": award["uid"], "ref": award["ref"]}, {"$set": {
                "exam": doc["exam"], "legacy_exam_split": True,
                "exam_win": bool(doc.get("winner") == award["uid"] and award.get("reward", {}).get("coins", 0) >= 50)}})
    async for profile in db.rf_profiles.find({"legacy_exam_split_v1": {"$ne": True}}, {"_id": 0, "uid": 1}):
        rows = await db.rf_awards.aggregate([
            {"$match": {"uid": profile["uid"], "legacy_exam_split": True}},
            {"$group": {"_id": "$exam", "xp": {"$sum": "$reward.xp"}, "wins": {"$sum": {"$cond": ["$exam_win", 1, 0]}}}},
        ]).to_list(2)
        inc = {f"exam_stats.{r['_id']}.{key}": r[key] for r in rows for key in ("xp", "wins") if r["_id"] in ("JEE", "NEET")}
        await db.rf_profiles.update_one({"uid": profile["uid"], "legacy_exam_split_v1": {"$ne": True}},
                                        {"$set": {"legacy_exam_split_v1": True}, **({"$inc": inc} if inc else {})})
    if await db.rf_migrations.find_one({"id": "learning_events_v1"}):
        return
    async for session in db.rf_sessions.find({"status": "completed"}, {"_id": 0}):
        cards = await db.rf_cards.find({"id": {"$in": session["card_ids"]}}, {"_id": 0}).to_list(30)
        await record_learning(db, session["user_id"], "solo:" + session["id"], session["exam"],
                              session.get("results", []), cards, session.get("completed_at") or session["created_at"])
    async for duel in db.rf_duels.find({"status": "finished"}, {"_id": 0}):
        cards = await db.rf_cards.find({"id": {"$in": duel["card_ids"]}}, {"_id": 0}).to_list(30)
        for player in duel["players"]:
            if player.get("bot"):
                continue
            rows = [{**row, "card_id": duel["card_ids"][row["i"]]} for row in player.get("answers", []) if row["i"] < len(duel["card_ids"])]
            await record_learning(db, player["uid"], "duel:" + duel["id"], duel["exam"], rows, cards,
                                  datetime.fromtimestamp(duel["finished_ts"], timezone.utc).isoformat())
    await db.rf_migrations.update_one({"id": "learning_events_v1"}, {"$set": {"done": True}}, upsert=True)