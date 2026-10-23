"""Rapid Fire game layer: XP, levels, coins, daily streak and badges (practice only — never touches exam marks)."""
import math
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pymongo.errors import DuplicateKeyError

IST = timezone(timedelta(hours=5, minutes=30))
BADGES = {
    "first_sprint": ("First Sprint", "Finished your first Rapid Fire session"),
    "first_win": ("First Blood", "Won your first duel"),
    "streak_3": ("On Fire", "3-day Rapid Fire streak"),
    "streak_7": ("Unstoppable", "7-day Rapid Fire streak"),
    "streak_30": ("Legend", "30-day Rapid Fire streak"),
    "sharpshooter": ("Sharpshooter", "90%+ accuracy in a 30-card run"),
    "perfect": ("Flawless", "Every card correct in a session of 10+"),
    "duelist_10": ("Duelist", "Played 10 duels"),
    "champion_10": ("Champion", "Won 10 duels"),
}


def level_of(xp: int) -> int:
    return int(math.sqrt(max(0, xp) / 100)) + 1


def level_floor(level: int) -> int:
    return (level - 1) ** 2 * 100


def ist_day(ts: Optional[float] = None) -> str:
    return datetime.fromtimestamp(ts or time.time(), IST).strftime("%Y-%m-%d")


def public_profile(p: dict) -> dict:
    lvl = level_of(p.get("xp", 0))
    today, yday = ist_day(), ist_day(time.time() - 86400)
    current = p.get("streak", 0) if p.get("last_day") in (today, yday) else 0
    return {"xp": p.get("xp", 0), "level": lvl, "level_floor": level_floor(lvl), "next_level_xp": level_floor(lvl + 1), "coins": p.get("coins", 0),
            "streak": current, "best_streak": p.get("best_streak", 0), "played_today": p.get("last_day") == today,
            "sessions": p.get("sessions", 0), "duels": p.get("duels", 0), "wins": p.get("wins", 0), "cards_correct": p.get("cards_correct", 0),
            "badges": [{"id": b, "title": BADGES[b][0], "body": BADGES[b][1], "earned": b in p.get("badges", [])} for b in BADGES]}


def make_router(db, rf_user):
    r = APIRouter(prefix="/rf")

    async def award(uid: str, ref: str, kind: str, correct: int, total: int, answered: int, won: Optional[bool] = None) -> dict:
        """Idempotent per (uid, ref): replays return the original reward."""
        try:
            await db.rf_awards.insert_one({"uid": uid, "ref": ref, "ts": time.time()})
        except DuplicateKeyError:
            import asyncio
            for _ in range(20):  # first call may still be writing the reward
                prev = await db.rf_awards.find_one({"uid": uid, "ref": ref}, {"_id": 0})
                if prev and prev.get("reward"):
                    return prev["reward"]
                await asyncio.sleep(0.1)
            return {}
        p = await db.rf_profiles.find_one({"uid": uid}) or {"uid": uid, "xp": 0, "coins": 0, "streak": 0, "best_streak": 0, "badges": []}
        acc = correct / answered if answered else 0
        perfect = total >= 10 and correct == total
        xp = correct * 10 + (25 if acc >= 0.8 and answered >= 10 else 0) + (50 if perfect else 0) + (60 if won else 20 if kind == "duel" else 0)
        coins = correct * 2 + (50 if won else 0) + (30 if perfect else 0)
        today, yday = ist_day(), ist_day(time.time() - 86400)
        streak = p.get("streak", 0)
        if p.get("last_day") != today:
            streak = streak + 1 if p.get("last_day") == yday else 1
        before = level_of(p.get("xp", 0))
        inc = {"xp": xp, "coins": coins, "cards_correct": correct}
        if kind == "solo":
            inc["sessions"] = 1
        else:
            inc["duels"] = 1
            inc["wins"] = 1 if won else 0
        # Atomic counters so concurrent sprint + duel never lose XP/coins.
        p = await db.rf_profiles.find_one_and_update({"uid": uid}, {"$inc": inc, "$set": {"streak": streak, "last_day": today}, "$max": {"best_streak": streak}},
                                                     upsert=True, return_document=True)
        have = set(p.get("badges", []))
        rules = {"first_sprint": p.get("sessions", 0) >= 1, "first_win": p.get("wins", 0) >= 1, "streak_3": streak >= 3, "streak_7": streak >= 7, "streak_30": streak >= 30,
                 "sharpshooter": total >= 30 and acc >= 0.9, "perfect": perfect, "duelist_10": p.get("duels", 0) >= 10, "champion_10": p.get("wins", 0) >= 10}
        new = [b for b, ok in rules.items() if ok and b not in have]
        if new:
            await db.rf_profiles.update_one({"uid": uid}, {"$addToSet": {"badges": {"$each": new}}})
        after = level_of(p["xp"])
        reward = {"xp": xp, "coins": coins, "streak": streak, "level_before": before, "level_after": after, "level_up": after > before,
                  "new_badges": [{"id": b, "title": BADGES[b][0], "body": BADGES[b][1]} for b in new]}
        await db.rf_awards.update_one({"uid": uid, "ref": ref}, {"$set": {"reward": reward}})
        return reward

    @r.get("/profile")
    async def profile(x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        return public_profile(await db.rf_profiles.find_one({"uid": uid}) or {})

    @r.get("/leaderboard")
    async def leaderboard(x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        top = await db.rf_profiles.find({}, {"_id": 0, "uid": 1, "xp": 1, "name": 1, "wins": 1}).sort("xp", -1).limit(20).to_list(20)
        return {"items": [{"rank": i + 1, "name": t.get("name") or "Player", "you": t["uid"] == uid, "xp": t.get("xp", 0), "level": level_of(t.get("xp", 0)), "wins": t.get("wins", 0)} for i, t in enumerate(top)]}

    @r.post("/profile/name")
    async def set_name(data: dict, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        name = str(data.get("name", "")).strip()[:24]
        if not name:
            raise HTTPException(400, "Name required.")
        await db.rf_profiles.update_one({"uid": uid}, {"$set": {"name": name}}, upsert=True)
        return {"ok": True}

    # Public read API so the JEELIVE.AI website (or any client) can use the same Rapid Fire bank.
    @r.get("/cards")
    async def cards(subject: Optional[str] = None, chapter: Optional[str] = None, page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=200)):
        q = {k: v for k, v in (("subject", subject), ("chapter", chapter)) if v}
        total = await db.rf_cards.count_documents(q)
        items = await db.rf_cards.find(q, {"_id": 0}).sort([("subject", 1), ("chapter", 1), ("id", 1)]).skip((page - 1) * limit).limit(limit).to_list(limit)
        return {"items": items, "total": total, "page": page, "pages": max(1, math.ceil(total / limit)), "review_status": "pilot_review_pending"}

    return r, award
