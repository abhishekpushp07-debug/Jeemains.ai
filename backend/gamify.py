"""Rapid Fire game layer: XP, levels, coins, daily streak and badges (practice only — never touches exam marks)."""
import math
import time
import asyncio
import logging
from bisect import bisect_right
from itertools import accumulate
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import JSONResponse
from metadata_cache import metadata_cache
import hashlib
import json
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from shop import AVATAR_BY_ID, AVATAR_ITEMS, BUYABLE, GEM_SHOP, QUESTS, SHOP, SHOP_BY_ID, equipped_of, owned_of, safe_avatar
from exam_groups import ACTIVE_EXAMS, Exam, require_active_exam

IST = timezone(timedelta(hours=5, minutes=30))
logger = logging.getLogger("jeelive")
LADDER_SECONDS = 30  # the least time between two passes over the XP index (see build_ladder)
LADDER_QUICK = 0.05  # a pass this fast (seconds) is waited for; a slower one runs in the background
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
    "cup_champion": ("Cup Champion", "Won a knockout cup"),
}


# Phoenix streak: correct answers in a row inside one match. Passing a milestone wins one diamond of that colour.
MILESTONES = ((3, "red"), (5, "blue"), (10, "emerald"), (15, "gold"), (20, "kohinoor"))
DIAMONDS = tuple(c for _, c in MILESTONES)


def phoenix(outcomes: list) -> tuple:
    """Diamonds won and the longest streak for one match. Wrong, timed-out and skipped cards restart the count."""
    won, streak, best = {}, 0, 0
    for o in outcomes:
        streak = streak + 1 if o == "correct" else 0
        best = max(best, streak)
        for at, colour in MILESTONES:
            if streak == at:
                won[colour] = won.get(colour, 0) + 1
    return won, best


def vault_of(p: dict) -> dict:
    """Diamonds in hand (the Store spends these)."""
    have = p.get("diamonds") or {}
    return {c: int(have.get(c, 0)) for c in DIAMONDS}


def vault_total(p: dict) -> dict:
    """Every diamond ever collected, including the ones already spent in the Store."""
    spent = p.get("diamonds_spent") or {}
    return {c: n + int(spent.get(c, 0)) for c, n in vault_of(p).items()}


# Diamond Rush: the diamonds won today move a daily track; each milestone opens a chest. Resets at midnight IST.
RUSH = ((1, "Bronze", 25, None), (3, "Silver", 50, None), (6, "Gold", 80, "freeze"), (10, "Royal", 120, "blue"), (15, "Phoenix", 200, "gold"))


def rush_of(p: dict) -> dict:
    ds = p.get("day_stats") or {}
    stats = ds if ds.get("day") == ist_day() else {}
    points, opened = stats.get("gems", 0), stats.get("rush", [])
    return {"points": points, "steps": [{"at": at, "chest": name, "coins": coins, "bonus": bonus, "done": points >= at, "claimed": at in opened} for at, name, coins, bonus in RUSH]}


def crown_of(p: dict) -> Optional[dict]:
    """The champion's crown next to a player's name: every Knockout Cup they won, and how many of those beat real players."""
    won = p.get("cups_won", 0)
    return {"won": won, "real": min(p.get("cups_real", 0), won)} if won else None



def level_of(xp: int) -> int:
    return int(math.sqrt(max(0, xp) / 100)) + 1


def level_floor(level: int) -> int:
    return (level - 1) ** 2 * 100


def ist_day(ts: Optional[float] = None) -> str:
    return datetime.fromtimestamp(ts or time.time(), IST).strftime("%Y-%m-%d")


def ist_week(ts: Optional[float] = None) -> str:
    """The league week (Monday to Sunday, IST) a moment falls in."""
    year, week, _ = datetime.fromtimestamp(ts or time.time(), IST).isocalendar()
    return f"{year}-W{week:02d}"


def week_ends_in() -> int:
    """Seconds until the leagues reset (next Monday 00:00 IST)."""
    now = datetime.now(IST)
    monday = (now + timedelta(days=7 - now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    return max(0, int((monday - now).total_seconds()))


def public_profile(p: dict) -> dict:
    lvl = level_of(p.get("xp", 0))
    today, yday = ist_day(), ist_day(time.time() - 86400)
    current = p.get("streak", 0) if p.get("last_day") in (today, yday) else 0
    return {"xp": p.get("xp", 0), "level": lvl, "level_floor": level_floor(lvl), "next_level_xp": level_floor(lvl + 1), "coins": p.get("coins", 0),
            "streak": current, "best_streak": p.get("best_streak", 0), "played_today": p.get("last_day") == today,
            "sessions": p.get("sessions", 0), "duels": p.get("duels", 0), "wins": p.get("wins", 0), "cards_correct": p.get("cards_correct", 0),
            "badges": [{"id": b, "title": BADGES[b][0], "body": BADGES[b][1], "earned": b in p.get("badges", [])} for b in BADGES],
            "avatar": safe_avatar(p.get("avatar")), "equipped": equipped_of(p), "owned": owned_of(p), "freezes": p.get("freezes", 0),
            "quests": quests_of(p), "diamonds": vault_of(p), "diamonds_total": vault_total(p), "rush": rush_of(p),
            "best_phoenix": p.get("best_phoenix", 0), "pid": p.get("pid"), "name": p.get("name")}


def quests_of(p: dict) -> list:
    ds = p.get("day_stats") or {}
    today = ist_day()
    stats = ds if ds.get("day") == today else {}
    claimed = stats.get("claimed", [])
    return [{**q, "progress": min(q["goal"], stats.get(q["stat"], 0)), "done": stats.get(q["stat"], 0) >= q["goal"], "claimed": q["id"] in claimed} for q in QUESTS]


AWARD_STALE = 15  # seconds: a reward still unwritten after this was cut off by a server restart; the next call finishes it


async def pay_once(db, uid: str, ref: str, update: dict) -> Optional[dict]:
    """Applies `update` to the player's profile exactly once per `ref` and returns the profile after it, or None if this
    ref was already paid. The ref is recorded in the same atomic write, so a retry after a crash never pays twice."""
    try:
        return await db.rf_profiles.find_one_and_update({"uid": uid, "paid_refs": {"$ne": ref}}, {**update, "$push": {"paid_refs": {"$each": [ref], "$slice": -40}}},
                                                        upsert=True, return_document=ReturnDocument.AFTER)
    except DuplicateKeyError:  # the profile exists and already carries this ref
        return None


def streak_after(p: dict, today: str, yday: str, freeze_ok: bool = True) -> tuple:
    """(streak, uses a freeze) for a played match, from the profile as read."""
    last, streak = p.get("last_day"), p.get("streak", 0)
    if last == today:
        return streak, False
    if last == yday:
        return streak + 1, False
    if freeze_ok and last == ist_day(time.time() - 2 * 86400) and p.get("freezes", 0) > 0:
        return streak + 1, True  # a Streak Freeze covers exactly one missed day
    return 1, False


def make_router(db, rf_user):
    r = APIRouter(prefix="/rf")
    board_cache = {}
    rank_cache = {}  # (exam, uid) -> (when, xp, rank)
    board_locks = {exam: asyncio.Lock() for exam in ACTIVE_EXAMS}
    ladders = {}  # exam -> (XP values in rising order, players at or above each value, QA players as (xp, uid))
    ladder_due = {}  # exam -> when the next pass over the XP index may start (monotonic clock)
    ladder_wait = {}  # exam -> from when a rank waits for the pass in progress instead of reading the ladder already there
    ladder_tasks = {}  # exam -> the pass running now

    async def build_ladder(exam: str):
        """How many players stand at each XP: one pass over the XP index answers "how many are above me?" for everybody.
        Before, each student's own rank made the database walk every player above them (half of all players on
        average) whenever their lobby opened. QA players (TEST…) are a handful, read through their own indexes and left out."""
        began, field = time.monotonic(), f"exam_stats.{exam}.xp"
        try:
            # Two lists come back (XP values in rising order, players on each) instead of one small document per value.
            doc = await (await db.rf_profiles.aggregate([{"$match": {field: {"$gt": 0}}}, {"$group": {"_id": "$" + field, "n": {"$sum": 1}}}, {"$sort": {"_id": 1}},
                                                         {"$group": {"_id": None, "xp": {"$push": "$_id"}, "n": {"$push": "$n"}}}])).to_list(1)
            values, counts = (doc[0]["xp"], doc[0]["n"]) if doc else ([], [])
            qa = [(p.get("exam_stats", {}).get(exam, {}).get("xp", 0), p["uid"]) for p in await db.rf_profiles.find(
                {"$or": [{"uid": {"$regex": "^TEST"}}, {"name": {"$regex": "^TEST"}}], field: {"$gt": 0}}, {"_id": 0, "uid": 1, field: 1}).to_list(None)]
            if qa:
                where = {xp: i for i, xp in enumerate(values)}
                for xp, _ in qa:
                    if xp in where:
                        counts[where[xp]] -= 1
            ladders[exam] = (values, list(accumulate(reversed(counts)))[::-1] + [0], qa)
            # A pass starts only when somebody asks for a rank, so after a quiet spell the ladder can be hours old.
            # A quick pass (a small crowd) is therefore simply waited for whenever it is due. A long pass (a huge crowd,
            # where somebody is always asking) runs in the background; its ladder answers until it is two gaps old.
            took = time.monotonic() - began
            gap = max(LADDER_SECONDS, 100 * took)
            ladder_wait[exam] = time.monotonic() + (gap if took < LADDER_QUICK else 2 * gap)
        except Exception:  # noqa: BLE001 - a failed pass keeps the ladder already there; ranks never fail because of it
            logger.exception("XP ladder pass failed")
        finally:
            # The pass reads the whole XP index, so it runs at most every 30 s and never takes more than about 1% of
            # the time (with a million players it comes every few minutes; a rank that deep does not move faster).
            ladder_due[exam] = time.monotonic() + max(LADDER_SECONDS, 100 * (time.monotonic() - began))
            ladder_tasks.pop(exam, None)

    async def ladder(exam: str) -> Optional[tuple]:
        """The ladder this server has now. A new pass starts when one is due. While players keep asking, nobody waits for
        a long pass (the ladder there is at most two gaps old); a quick pass, the very first one and a pass after a quiet
        spell are waited for (2 s at most), so a rank is never read from a ladder older than that. None only when the
        first pass of a huge crowd is still running."""
        task = ladder_tasks.get(exam)
        if not task and time.monotonic() >= ladder_due.get(exam, 0):
            task = ladder_tasks[exam] = asyncio.create_task(build_ladder(exam))
        if task and time.monotonic() >= ladder_wait.get(exam, 0):
            await asyncio.wait([task], timeout=2)
        return ladders.get(exam)

    async def award(uid: str, ref: str, kind: str, correct: int, total: int, answered: int, won: Optional[bool] = None, exam: str = "JEE",
                    diamonds: Optional[dict] = None, phoenix_streak: int = 0, meta: Optional[dict] = None) -> dict:
        """Idempotent per (uid, ref): replays return the original reward. `meta` describes the match for the friend feed.
        Every counter moves with $inc on its own field, so a quest claim, a chest or another match landing at the same
        moment is never overwritten; the profile write records `ref`, so a crash half-way never pays twice or loses it."""
        require_active_exam(exam)
        try:
            await db.rf_awards.insert_one({"uid": uid, "ref": ref, "exam": exam, "ts": time.time()})
        except DuplicateKeyError:
            for _ in range(20):  # first call may still be writing the reward
                prev = await db.rf_awards.find_one({"uid": uid, "ref": ref}, {"_id": 0})
                if prev and prev.get("reward"):
                    return prev["reward"]
                await asyncio.sleep(0.1)
            # Still no reward: the first call stopped half-way (server restart). Once that is clearly stale, finish it here.
            if not await db.rf_awards.find_one_and_update({"uid": uid, "ref": ref, "reward": {"$exists": False}, "ts": {"$lt": time.time() - AWARD_STALE}},
                                                          {"$set": {"ts": time.time()}}):
                return {}
        p = await db.rf_profiles.find_one({"uid": uid}) or {}
        acc = correct / answered if answered else 0
        perfect = total >= 10 and correct == total
        # A win only pays (and counts) with real effort: at least 5 correct answers. Skip/tap-farming earns nothing extra.
        if won and correct < 5:
            won = False
        xp = correct * 10 + (25 if acc >= 0.8 and answered >= 10 else 0) + (50 if perfect else 0) + (60 if won else 20 if kind == "duel" and answered else 10 if kind == "bot" else 0)
        coins = (correct * 2 if kind != "bot" else correct) + (50 if won else 0) + (30 if perfect else 0)
        today, yday = ist_day(), ist_day(time.time() - 86400)
        played = answered > 0  # an all-skip run earns nothing and never keeps a streak alive
        used_freeze = False
        if played:
            streak, used_freeze = streak_after(p, today, yday)
            if used_freeze:  # spend the freeze only if no other match spent it a moment ago
                spent = await db.rf_profiles.update_one({"uid": uid, "freezes": {"$gt": 0}, "last_day": p.get("last_day")}, {"$inc": {"freezes": -1}, "$set": {"last_day": yday}})
                if not spent.modified_count:
                    used_freeze = False
                    p = await db.rf_profiles.find_one({"uid": uid}) or {}
                    streak, _ = streak_after(p, today, yday, freeze_ok=False)
        else:
            streak = p.get("streak", 0) if p.get("last_day") in (today, yday) else 0
        diamonds = {c: n for c, n in (diamonds or {}).items() if c in DIAMONDS and n > 0}
        # A new day / league week starts the day's and week's totals from zero, once (whichever match comes first).
        if (p.get("day_stats") or {}).get("day") != today:
            try:
                await db.rf_profiles.update_one({"uid": uid, "day_stats.day": {"$ne": today}},
                                                {"$set": {"day_stats": {"day": today, "sprints": 0, "correct": 0, "wins": 0, "claimed": [], "gems": 0, "rush": []}}}, upsert=True)
            except DuplicateKeyError:
                pass  # another match of this player started today's totals first
        week = ist_week()
        if (p.get("week_stats") or {}).get("week") != week:  # last week's totals move to `last_week` (prizes are paid from there)
            await db.rf_profiles.update_one({"uid": uid, "week_stats.week": {"$ne": week}}, [{"$set": {
                "last_week": {"$cond": [{"$gt": ["$week_stats.week", None]}, "$week_stats", {"$ifNull": ["$last_week", "$$REMOVE"]}]},
                "week_stats": {"$literal": {"week": week, "xp": 0, "wins": 0, "correct": 0, "matches": 0}}}}])
        inc = {"xp": xp, "coins": coins, "cards_correct": correct}
        inc[f"exam_stats.{exam}.xp"] = xp
        inc[f"exam_stats.{exam}.wins"] = 1 if won else 0
        inc[f"exam_stats.{exam}.cards_correct"] = correct
        for colour, n in diamonds.items():
            inc[f"diamonds.{colour}"] = n
        if kind == "solo":
            if played:
                inc["sessions"] = 1
        elif kind == "bot":
            inc["rival_games"] = 1
        else:
            if played:
                inc["duels"] = 1
            inc["wins"] = 1 if won else 0
        inc.update({"day_stats.sprints": 1 if kind == "solo" and played else 0, "day_stats.correct": correct, "day_stats.wins": 1 if won else 0,
                    "day_stats.gems": sum(diamonds.values()), "week_stats.xp": xp, "week_stats.wins": 1 if won else 0, "week_stats.correct": correct,
                    "week_stats.matches": 1 if played and kind == "duel" else 0})
        sets = {"streak": streak, "last_day": today} if played and p.get("last_day") != today else {}
        # Wins in a row across matches (for the friend feed). Solo sprints never touch it.
        if played and kind != "solo":
            if won:
                inc["win_run"] = 1
            else:
                sets["win_run"] = 0
        update = {"$inc": inc, "$max": {"best_streak": streak, "best_phoenix": phoenix_streak}, **({"$set": sets} if sets else {})}
        fresh = await pay_once(db, uid, ref, update)
        p = fresh or await db.rf_profiles.find_one({"uid": uid}) or {"uid": uid, "xp": xp, "coins": coins}
        win_run = p.get("win_run", 0)
        before = level_of(p.get("xp", 0) - xp)
        have = set(p.get("badges", []))
        rules = {"first_sprint": p.get("sessions", 0) >= 1, "first_win": p.get("wins", 0) >= 1, "streak_3": streak >= 3, "streak_7": streak >= 7, "streak_30": streak >= 30,
                 "sharpshooter": answered >= 25 and acc >= 0.9, "perfect": perfect, "duelist_10": p.get("duels", 0) >= 10, "champion_10": p.get("wins", 0) >= 10}
        new = [b for b, ok in rules.items() if ok and b not in have]
        if new:
            await db.rf_profiles.update_one({"uid": uid}, {"$addToSet": {"badges": {"$each": new}}})
        after = level_of(p.get("xp", 0))
        reward = {"exam": exam, "exam_xp_total": p.get("exam_stats", {}).get(exam, {}).get("xp", 0), "xp": xp, "coins": coins, "streak": streak, "freeze_used": used_freeze, "level_before": before, "level_after": after, "level_up": after > before,
                  "xp_total": p.get("xp", 0), "coins_total": p.get("coins", 0), "level_floor": level_floor(after), "next_level_xp": level_floor(after + 1), "played": played,
                  "quest_ready": any(q["done"] and not q["claimed"] for q in quests_of(p)) or any(s["done"] and not s["claimed"] for s in rush_of(p)["steps"]),
                  "diamonds": diamonds, "phoenix_streak": phoenix_streak, "vault": vault_of(p),
                  "new_badges": [{"id": b, "title": BADGES[b][0], "body": BADGES[b][1]} for b in new]}
        await db.rf_awards.update_one({"uid": uid, "ref": ref}, {"$set": {"reward": reward}})
        # Friend feed: the moments worth telling friends about.
        events = []
        if kind == "duel" and won and meta and not meta.get("bot"):
            events.append(("win", meta))
        if kind == "duel" and won and win_run in (3, 5, 10):
            events.append(("run", {"n": win_run}))
        events += [("gem", {"colour": c}) for c in ("emerald", "gold", "kohinoor") if diamonds.get(c)]
        if after > before:
            events.append(("level", {"level": after}))
        events += [("badge", {"title": BADGES[b][0]}) for b in new]
        if events and fresh and not uid.startswith("TEST"):  # only the call that paid tells friends (never twice)
            now = datetime.now(timezone.utc)
            await db.rf_feed.insert_many([{"id": f"{ref}:{k}", "uid": uid, "kind": kind_, "data": data, "ts": time.time(), "at": now} for k, (kind_, data) in enumerate(events)])
        # The leaderboard is NOT reset here: with thousands of matches ending every second it would never stay cached.
        # It refreshes every 15 seconds, and each player's own row is always read fresh.
        return reward

    @r.get("/profile")
    async def profile(x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        return public_profile(await db.rf_profiles.find_one({"uid": uid}) or {})

    @r.get("/leaderboard")
    async def leaderboard(exam: Exam = "JEE", x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        exam = require_active_exam(exam)
        field = f"exam_stats.{exam}.xp"
        query = {field: {"$gt": 0}, "name": {"$not": {"$regex": "^TEST"}}, "uid": {"$not": {"$regex": "^TEST"}}}
        async with board_locks[exam]:
            cached = board_cache.get(exam, {})
            if time.time() - cached.get("ts", 0) > 15:
                rows = await db.rf_profiles.find(query, {"_id": 0, "uid": 1, "name": 1, "exam_stats": 1, "pid": 1, "avatar": 1, "equipped": 1, "cups_won": 1, "cups_real": 1}).sort([(field, -1), ("uid", 1)]).limit(20).to_list(20)
                cached = {"ts": time.time(), "rows": rows}
                board_cache[exam] = cached
        items = []
        for i, row in enumerate(cached["rows"]):
            stats = row.get("exam_stats", {}).get(exam, {})
            items.append({"rank": i + 1, "name": row.get("name") or f"{exam} Aspirant", "you": row["uid"] == uid, "pid": row.get("pid"),
                          "avatar": safe_avatar(row.get("avatar")), "frame": equipped_of(row).get("frame"),
                          "xp": stats.get("xp", 0), "level": level_of(stats.get("xp", 0)), "wins": stats.get("wins", 0), "crown": crown_of(row)})
        mine = await db.rf_profiles.find_one({"uid": uid}, {"_id": 0, "exam_stats": 1, "name": 1}) or {}
        xp = mine.get("exam_stats", {}).get(exam, {}).get("xp", 0)
        rank = next((item["rank"] for item in items if item["you"]), None)  # on the list: the place shown there, so both always agree
        if not rank and xp > 0 and not uid.startswith("TEST") and not mine.get("name", "").startswith("TEST"):
            hit = rank_cache.get((exam, uid))
            if hit and hit[1] == xp and time.time() - hit[0] < 30:
                rank = hit[2]
            else:
                # Above you: everyone with more XP (read off the shared ladder), then the players level with you whose
                # id sorts first (a short read of the index: only the players on exactly your XP, never everyone above).
                steps = await ladder(exam)
                if steps:
                    values, at_or_above, qa = steps
                    level = await db.rf_profiles.count_documents({field: xp, "uid": {"$lt": uid}})
                    rank = 1 + at_or_above[bisect_right(values, xp)] + max(0, level - sum(1 for x, u in qa if x == xp and u < uid))
                else:  # this server's first moments, before its ladder is ready: the full count (QA players taken off)
                    above = {"$or": [{field: {"$gt": xp}}, {field: xp, "uid": {"$lt": uid}}]}
                    everyone, qa_above = await asyncio.gather(db.rf_profiles.count_documents(above), db.rf_profiles.count_documents(
                        {"$and": [above, {"$or": [{"uid": {"$regex": "^TEST"}}, {"name": {"$regex": "^TEST"}}]}]}))
                    rank = 1 + everyone - qa_above
                if len(rank_cache) > 100_000:
                    rank_cache.clear()
                rank_cache[(exam, uid)] = (time.time(), xp, rank)
        return {"exam": exam, "items": items, "you": {"rank": rank, "xp": xp, "level": level_of(xp)},
                "note": "Exam-only practice XP. Wallet, streak and overall level remain shared."}

    @r.post("/profile/name")
    async def set_name(data: dict, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        name = str(data.get("name", "")).strip()[:24]
        if not name:
            raise HTTPException(400, "Name required.")
        await db.rf_profiles.update_one({"uid": uid}, {"$set": {"name": name}}, upsert=True)
        board_cache.clear()
        return {"ok": True}

    # Public read API so the JEELIVE.AI website (or any client) can use the same Rapid Fire bank.
    @r.get("/cards")
    async def cards(subject: Optional[str] = None, chapter: Optional[str] = None, exam: Optional[Exam] = None, page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=200)):
        exam = require_active_exam(exam or ("NEET" if subject == "Biology" else "JEE"))
        scope = {"exam": exam}
        q = {**scope, **{k: v for k, v in (("subject", subject), ("chapter", chapter)) if v}, "retired": {"$ne": True}}
        async def load():
            total = await db.rf_cards.count_documents(q)
            # NO answers, explanations or answer-side formulae in Redis/public pages.
            items = await db.rf_cards.find(q, {"_id": 0, "answer": 0, "explain": 0, "formula": 0}).sort([("subject", 1), ("chapter", 1), ("id", 1)]).skip((page - 1) * limit).limit(limit).to_list(limit)
            return {"items": items, "total": total, "page": page, "pages": max(1, math.ceil(total / limit)), "review_status": "quick_recall_reviewed_v1"}
        variant = hashlib.sha256(json.dumps([exam, subject, chapter, page, limit]).encode()).hexdigest()
        data, state = await metadata_cache.get_or_load(f'{db.name}:cards:{variant}', load, ttl=60)
        return JSONResponse(data, headers={'X-Cache': state, 'Cache-Control': 'no-cache'})

    @r.get("/shop")
    async def shop(x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        p = await db.rf_profiles.find_one({"uid": uid}) or {}
        return {"items": SHOP + GEM_SHOP, "avatars": [{k: a.get(k) for k in ("id", "title", "rarity", "price", "gems")} for a in AVATAR_ITEMS], "coins": p.get("coins", 0), "diamonds": vault_of(p),
                "owned": owned_of(p), "equipped": equipped_of(p), "freezes": p.get("freezes", 0), "avatar": safe_avatar(p.get("avatar"))}

    @r.post("/shop/buy")
    async def buy(data: dict, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        item = BUYABLE.get(str(data.get("item_id")))
        if not item:
            raise HTTPException(404, "Item not found.")
        gems = item.get("gems")
        if not item["price"] and not gems:
            raise HTTPException(409, "You already own this. It is free for everyone.")
        if gems:  # diamond specials: every colour in the price must be in the Vault
            q = {"uid": uid, "owned": {"$ne": item["id"]}, **{f"diamonds.{c}": {"$gte": n} for c, n in gems.items()}}
            upd = {"$inc": {k: v for c, n in gems.items() for k, v in ((f"diamonds.{c}", -n), (f"diamonds_spent.{c}", n))}, "$addToSet": {"owned": item["id"]}}
        else:
            q = {"uid": uid, "coins": {"$gte": item["price"]}}
            upd = {"$inc": {"coins": -item["price"], **({"freezes": 1} if item.get("consumable") else {})}}
            if not item.get("consumable"):
                q["owned"] = {"$ne": item["id"]}
                upd["$addToSet"] = {"owned": item["id"]}
        p = await db.rf_profiles.find_one_and_update(q, upd, return_document=True)
        if not p:
            have = await db.rf_profiles.find_one({"uid": uid}) or {}
            need = ", ".join(f"{n} {c.title()}" for c, n in (gems or {}).items())
            raise HTTPException(409, "You already own this." if item["id"] in have.get("owned", []) else f"Not enough diamonds. You need {need}. Win them with Phoenix streaks." if gems
                                else f"Not enough coins — you need {item['price']}. Earn more in sprints and duels.")
        return {"coins": p.get("coins", 0), "owned": p.get("owned", []), "freezes": p.get("freezes", 0), "diamonds": vault_of(p)}

    @r.post("/rush/claim")
    async def rush_claim(data: dict, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        step = next((s for s in RUSH if s[0] == data.get("at")), None)
        if not step:
            raise HTTPException(404, "Chest not found.")
        at, name, coins, bonus = step
        inc = {"coins": coins, **({"freezes": 1} if bonus == "freeze" else {f"diamonds.{bonus}": 1} if bonus else {})}
        p = await db.rf_profiles.find_one_and_update({"uid": uid, "day_stats.day": ist_day(), "day_stats.gems": {"$gte": at}, "day_stats.rush": {"$ne": at}},
                                                     {"$inc": inc, "$addToSet": {"day_stats.rush": at}}, return_document=True)
        if not p:
            raise HTTPException(409, "This chest is not ready yet, or you already opened it.")
        return {"chest": name, "coins": coins, "bonus": bonus, "coins_total": p["coins"], "rush": rush_of(p)}

    @r.post("/shop/equip")
    async def equip(data: dict, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        slot, item_id = str(data.get("slot")), data.get("item_id")
        if slot not in ("frame", "entry", "theme"):
            raise HTTPException(400, "Unknown slot.")
        if item_id is not None:
            p = await db.rf_profiles.find_one({"uid": uid}) or {}
            if item_id not in owned_of(p) or SHOP_BY_ID.get(item_id, {}).get("slot") != slot:
                raise HTTPException(403, "Buy this item first.")
        await db.rf_profiles.update_one({"uid": uid}, {"$set": {f"equipped.{slot}": item_id}}, upsert=True)
        return {"ok": True}

    @r.post("/profile/avatar")
    async def avatar(data: dict, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        a = AVATAR_BY_ID.get(data.get("avatar"))
        if not a:
            raise HTTPException(400, "Unknown avatar.")
        if (a["price"] or a.get("gems")) and a["id"] not in ((await db.rf_profiles.find_one({"uid": uid}) or {}).get("owned", [])):
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
