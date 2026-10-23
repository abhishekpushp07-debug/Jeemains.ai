"""Rapid Fire game layer: XP, levels, coins, daily streak and badges (practice only — never touches exam marks)."""
import math
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pymongo.errors import DuplicateKeyError
from shop import AVATAR_BY_ID, AVATAR_ITEMS, BUYABLE, QUESTS, SHOP, SHOP_BY_ID, safe_avatar

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
            "badges": [{"id": b, "title": BADGES[b][0], "body": BADGES[b][1], "earned": b in p.get("badges", [])} for b in BADGES],
            "avatar": safe_avatar(p.get("avatar")), "equipped": p.get("equipped", {}), "owned": p.get("owned", []), "freezes": p.get("freezes", 0),
            "quests": quests_of(p)}


def quests_of(p: dict) -> list:
    ds = p.get("day_stats") or {}
    today = ist_day()
    stats = ds if ds.get("day") == today else {}
    claimed = stats.get("claimed", [])
    return [{**q, "progress": min(q["goal"], stats.get(q["stat"], 0)), "done": stats.get(q["stat"], 0) >= q["goal"], "claimed": q["id"] in claimed} for q in QUESTS]


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
        xp = correct * 10 + (25 if acc >= 0.8 and answered >= 10 else 0) + (50 if perfect else 0) + (60 if won else 20 if kind == "duel" else 10 if kind == "bot" else 0)
        coins = (correct * 2 if kind != "bot" else correct) + (50 if won else 0) + (30 if perfect else 0)
        today, yday = ist_day(), ist_day(time.time() - 86400)
        streak = p.get("streak", 0)
        used_freeze = False
        if p.get("last_day") != today:
            if p.get("last_day") == yday:
                streak += 1
            elif p.get("last_day") == ist_day(time.time() - 2 * 86400) and p.get("freezes", 0) > 0:
                streak += 1  # a Streak Freeze covers exactly one missed day
                used_freeze = True
            else:
                streak = 1
        ds = p.get("day_stats") or {}
        if ds.get("day") != today:
            ds = {"day": today, "sprints": 0, "correct": 0, "wins": 0, "claimed": []}
        ds = {**ds, "sprints": ds.get("sprints", 0) + (1 if kind == "solo" else 0), "correct": ds.get("correct", 0) + correct, "wins": ds.get("wins", 0) + (1 if won else 0)}
        before = level_of(p.get("xp", 0))
        inc = {"xp": xp, "coins": coins, "cards_correct": correct}
        if kind == "solo":
            inc["sessions"] = 1
        elif kind == "bot":
            inc["rival_games"] = 1
        else:
            inc["duels"] = 1
            inc["wins"] = 1 if won else 0
        # Atomic counters so concurrent sprint + duel never lose XP/coins.
        p = await db.rf_profiles.find_one_and_update({"uid": uid}, {"$inc": {**inc, **({"freezes": -1} if used_freeze else {})}, "$set": {"streak": streak, "last_day": today, "day_stats": ds}, "$max": {"best_streak": streak}},
                                                     upsert=True, return_document=True)
        have = set(p.get("badges", []))
        rules = {"first_sprint": p.get("sessions", 0) >= 1, "first_win": p.get("wins", 0) >= 1, "streak_3": streak >= 3, "streak_7": streak >= 7, "streak_30": streak >= 30,
                 "sharpshooter": total >= 30 and acc >= 0.9, "perfect": perfect, "duelist_10": p.get("duels", 0) >= 10, "champion_10": p.get("wins", 0) >= 10}
        new = [b for b, ok in rules.items() if ok and b not in have]
        if new:
            await db.rf_profiles.update_one({"uid": uid}, {"$addToSet": {"badges": {"$each": new}}})
        after = level_of(p["xp"])
        reward = {"xp": xp, "coins": coins, "streak": streak, "freeze_used": used_freeze, "level_before": before, "level_after": after, "level_up": after > before,
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

    @r.get("/shop")
    async def shop(x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        p = await db.rf_profiles.find_one({"uid": uid}) or {}
        return {"items": SHOP, "avatars": [{k: a[k] for k in ("id", "title", "rarity", "price")} for a in AVATAR_ITEMS], "coins": p.get("coins", 0), "owned": p.get("owned", []), "equipped": p.get("equipped", {}), "freezes": p.get("freezes", 0), "avatar": safe_avatar(p.get("avatar"))}

    @r.post("/shop/buy")
    async def buy(data: dict, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        item = BUYABLE.get(str(data.get("item_id")))
        if not item:
            raise HTTPException(404, "Item not found.")
        q = {"uid": uid, "coins": {"$gte": item["price"]}}
        upd = {"$inc": {"coins": -item["price"], **({"freezes": 1} if item.get("consumable") else {})}}
        if not item.get("consumable"):
            q["owned"] = {"$ne": item["id"]}
            upd["$addToSet"] = {"owned": item["id"]}
        p = await db.rf_profiles.find_one_and_update(q, upd, return_document=True)
        if not p:
            have = await db.rf_profiles.find_one({"uid": uid}) or {}
            raise HTTPException(409, "You already own this." if item["id"] in have.get("owned", []) else f"Not enough coins — you need {item['price']}. Earn more in sprints and duels.")
        return {"coins": p["coins"], "owned": p.get("owned", []), "freezes": p.get("freezes", 0)}

    @r.post("/shop/equip")
    async def equip(data: dict, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        slot, item_id = str(data.get("slot")), data.get("item_id")
        if slot not in ("frame", "entry", "theme"):
            raise HTTPException(400, "Unknown slot.")
        if item_id is not None:
            p = await db.rf_profiles.find_one({"uid": uid}) or {}
            if item_id not in p.get("owned", []) or SHOP_BY_ID.get(item_id, {}).get("slot") != slot:
                raise HTTPException(403, "Buy this item first.")
        await db.rf_profiles.update_one({"uid": uid}, {"$set": {f"equipped.{slot}": item_id}}, upsert=True)
        return {"ok": True}

    @r.post("/profile/avatar")
    async def avatar(data: dict, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        a = AVATAR_BY_ID.get(data.get("avatar"))
        if not a:
            raise HTTPException(400, "Unknown avatar.")
        if a["price"] and a["id"] not in ((await db.rf_profiles.find_one({"uid": uid}) or {}).get("owned", [])):
            raise HTTPException(403, "Buy this avatar first.")
        await db.rf_profiles.update_one({"uid": uid}, {"$set": {"avatar": data["avatar"]}}, upsert=True)
        return {"ok": True}

    @r.post("/quests/claim")
    async def claim(data: dict, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        p = await db.rf_profiles.find_one({"uid": uid}) or {}
        q = next((x for x in quests_of(p) if x["id"] == data.get("id")), None)
        if not q or not q["done"] or q["claimed"]:
            raise HTTPException(409, "Quest not ready to claim.")
        res = await db.rf_profiles.update_one({"uid": uid, "day_stats.day": ist_day(), "day_stats.claimed": {"$ne": q["id"]}},
                                              {"$inc": {"coins": q["coins"]}, "$addToSet": {"day_stats.claimed": q["id"]}})
        if not res.modified_count:
            raise HTTPException(409, "Already claimed.")
        return {"coins": q["coins"]}

    return r, award
