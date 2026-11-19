"""All India Rapid: the same 45 PCM cards (15 Physics, 15 Chemistry, 15 Maths, 20 s each) for every student each day (IST),
with one All India board.

The server deals one card at a time and keeps the clock, so the board is fair: the answer key never reaches the phone
before a card is answered, a card can never be read before its turn, and the time on the board is the server's time.
Cards used on an earlier day never come back (the bank lasts well over a year of days)."""
import asyncio
import hashlib
import random
import time
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from exam_groups import Exam, require_active_exam
from gamify import IST, crown_of, ist_day, level_of, phoenix
from load_guard import arena_gate
from rapid_deck import fingerprint
from revision import record_learning
from scope import CARD_SECONDS
from shop import equipped_of, safe_avatar

SUBJECTS = ("Physics", "Chemistry", "Mathematics")
PER_SUBJECT = 15  # 45 cards a day
TOTAL = PER_SUBJECT * len(SUBJECTS)
GRACE = 2.5  # seconds for the network, both ways
START_IN = 3.0  # the 3-2-1 before the first card
REVEAL = {"correct": 1.0, "incorrect": 2.4, "timed_out": 2.4, "skipped": 0.3}  # the next card shows after this


class Answer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    exam: Optional[Exam] = None
    i: int = Field(ge=0, lt=TOTAL)
    choice: Optional[int] = Field(default=None, ge=0, le=3)
    skip: bool = False


class Start(BaseModel):
    model_config = ConfigDict(extra="forbid")
    exam: Optional[Exam] = None


def day_ends(day: str) -> float:
    start = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=IST)
    return (start + timedelta(days=1)).timestamp()


def public(card: dict, i: int) -> dict:
    """What the phone may see before answering: no id, no key, no explanation."""
    return {"i": i, "subject": card["subject"], "chapter": card["chapter"], "prompt": card["prompt"], "options": card["options"]}


def make_router(db, rf_user, award):
    r = APIRouter(prefix="/rf/daily")
    boards: dict = {}  # (exam, day, test) -> (ts, players, rows)
    locks: dict = {}

    async def deck(exam: str, day: str) -> list:
        """Today's 45 card ids: 15 per subject, 15 different chapters each, never a card from an earlier day.
        A day keeps the deck it was first played with; a shorter deck from before the 45-card rule that nobody has played yet is dealt again."""
        key = f"{exam}:{day}"
        have = await db.rf_daily.find_one({"_id": key})
        if have and (len(have["card_ids"]) >= TOTAL or await db.rf_daily_plays.find_one({"exam": exam, "day": day}, {"_id": 1})):
            return have["card_ids"]
        used = set(await db.rf_daily.distinct("card_ids", {"exam": exam, "_id": {"$ne": key}}))
        rng = random.Random(hashlib.sha256(key.encode()).hexdigest())
        lanes, prompts = [], set()
        for subject in SUBJECTS:
            rows = await db.rf_cards.find({"exam": exam, "subject": subject, "retired": {"$ne": True}, "diagram": None},
                                          {"_id": 0, "id": 1, "chapter": 1, "prompt": 1}).to_list(20000)
            rows.sort(key=lambda c: c["id"])  # same order on every server before the seeded shuffle
            rng.shuffle(rows)
            fresh = [c for c in rows if c["id"] not in used] or rows
            by_chapter: dict = {}
            for c in fresh:
                by_chapter.setdefault(c["chapter"], []).append(c)
            chapters = sorted(by_chapter)
            rng.shuffle(chapters)
            picked = []
            while len(picked) < PER_SUBJECT and any(by_chapter.values()):
                for ch in chapters:
                    while by_chapter[ch] and len(picked) < PER_SUBJECT:
                        c = by_chapter[ch].pop()
                        if fingerprint(c["prompt"]) not in prompts:
                            prompts.add(fingerprint(c["prompt"]))
                            picked.append(c["id"])
                            break
            lanes.append(picked)
        ids = [lane[k] for k in range(PER_SUBJECT) for lane in lanes if k < len(lane)]  # Physics, Chemistry, Maths, ...
        doc = {"_id": key, "exam": exam, "day": day, "card_ids": ids, "ts": time.time()}
        if have:  # the unplayed short deck: replaced in place (the same seed gives every server the same new deck)
            await db.rf_daily.replace_one({"_id": key}, doc)
            return ids
        try:
            await db.rf_daily.insert_one(doc)
        except DuplicateKeyError:  # another server made today's deck at the same moment: everyone plays that one
            return (await db.rf_daily.find_one({"_id": key}))["card_ids"]
        return ids

    async def cards_of(ids: list) -> list:
        docs = {c["id"]: c for c in await db.rf_cards.find({"id": {"$in": ids}}, {"_id": 0}).to_list(len(ids))}
        return [docs[i] for i in ids if i in docs]

    def rank_query(p: dict) -> dict:
        return {"exam": p["exam"], "day": p["day"], "test": p.get("test", False), "status": "done",
                "$or": [{"correct": {"$gt": p["correct"]}}, {"correct": p["correct"], "ms": {"$lt": p["ms"]}},
                        {"correct": p["correct"], "ms": p["ms"], "finished_ts": {"$lt": p["finished_ts"]}}]}

    async def rank_of(p: dict) -> Optional[int]:
        return 1 + await db.rf_daily_plays.count_documents(rank_query(p)) if p and p.get("status") == "done" else None

    async def board(exam: str, day: str, test: bool, limit: int = 100) -> tuple:
        """(players, top rows) for a day, kept 15 s: the lobby of every student asks for it."""
        k = (exam, day, test)
        lock = locks.setdefault(k, asyncio.Lock())
        async with lock:
            hit = boards.get(k)
            if hit and time.time() - hit[0] < 15:
                return hit[1], hit[2]
            q = {"exam": exam, "day": day, "test": test, "status": "done"}
            players = await db.rf_daily_plays.count_documents(q)
            plays = await db.rf_daily_plays.find(q, {"_id": 0, "uid": 1, "correct": 1, "ms": 1}).sort([("correct", -1), ("ms", 1), ("finished_ts", 1)]).limit(100).to_list(100)
            profs = {x["uid"]: x for x in await db.rf_profiles.find({"uid": {"$in": [x["uid"] for x in plays]}},
                     {"_id": 0, "uid": 1, "name": 1, "pid": 1, "avatar": 1, "equipped": 1, "xp": 1, "cups_won": 1, "cups_real": 1}).to_list(100)}
            rows = []
            for n, x in enumerate(plays):
                pr = profs.get(x["uid"], {})
                rows.append({"rank": n + 1, "uid": x["uid"], "name": pr.get("name") or "JEE Aspirant", "pid": pr.get("pid"), "avatar": safe_avatar(pr.get("avatar")),
                             "frame": equipped_of(pr).get("frame"), "level": level_of(pr.get("xp", 0)), "crown": crown_of(pr), "correct": x["correct"], "ms": x["ms"]})
            if len(boards) > 64:
                boards.clear()
            boards[k] = (time.time(), players, rows)
            return players, rows

    def shown(rows: list, uid: str, limit: int) -> list:
        return [{k: v for k, v in row.items() if k != "uid"} | {"you": row["uid"] == uid} for row in rows[:limit]]

    async def play_of(uid: str, exam: str, day: str) -> Optional[dict]:
        return await db.rf_daily_plays.find_one({"exam": exam, "day": day, "uid": uid}, {"_id": 0})

    async def result(p: dict, uid: str) -> dict:
        players, _ = await board(p["exam"], p["day"], p.get("test", False))
        award_row = await db.rf_awards.find_one({"uid": uid, "ref": ref_of(p)}, {"_id": 0, "reward": 1}) or {}
        return {"correct": p["correct"], "total": len(p.get("rows") or []) or TOTAL, "ms": p["ms"], "rank": await rank_of(p), "players": max(players, 1),
                "reward": award_row.get("reward"), "day": p["day"]}

    def ref_of(p: dict) -> str:
        return f"daily:{p['exam']}:{p['day']}"

    async def settle(p: dict, uid: str) -> dict:
        """Last card done: pay the reward once and record the misses for Weak cards."""
        boards.pop((p["exam"], p["day"], p.get("test", False)), None)
        cards = await cards_of([x["card_id"] for x in p["rows"]])
        await record_learning(db, uid, ref_of(p), p["exam"], p["rows"], cards, datetime.fromtimestamp(p["finished_ts"], IST).isoformat())
        answered = sum(x["outcome"] in ("correct", "incorrect") for x in p["rows"])
        gems, best = phoenix([x["outcome"] for x in p["rows"]])
        await award(uid, ref_of(p), "solo", p["correct"], len(p["rows"]), answered, exam=p["exam"], diamonds=gems, phoenix_streak=best)
        return await result(p, uid)

    async def current(p: dict, uid: str) -> dict:
        """The card on screen now. A card left past its time (the app was closed) counts as timed out, then the next is dealt."""
        while p["status"] == "playing":
            now = time.time()
            ids = (await db.rf_daily.find_one({"_id": f"{p['exam']}:{p['day']}"}))["card_ids"]
            if p.get("served_ts") is None:
                p = await db.rf_daily_plays.find_one_and_update({"exam": p["exam"], "day": p["day"], "uid": uid, "i": p["i"], "served_ts": None},
                                                                {"$set": {"served_ts": now + START_IN}}, projection={"_id": 0}, return_document=ReturnDocument.AFTER) or await play_of(uid, p["exam"], p["day"])
                continue
            if now <= p["served_ts"] + CARD_SECONDS + GRACE:
                card = (await cards_of([ids[p["i"]]]))[0]
                return {"status": "playing", "i": p["i"], "total": len(ids), "seconds": CARD_SECONDS, "correct": p["correct"], "card": public(card, p["i"]),
                        "show_in_ms": max(0, round((p["served_ts"] - now) * 1000)), "left_ms": round(min(CARD_SECONDS, p["served_ts"] + CARD_SECONDS - now) * 1000)}
            p = await move(p, uid, ids, None, "timed_out", CARD_SECONDS * 1000, now) or await play_of(uid, p["exam"], p["day"])
        return {"status": "done", "result": await result(p, uid)}

    async def move(p: dict, uid: str, ids: list, choice: Optional[int], outcome: str, ms: int, now: float) -> Optional[dict]:
        """Record card i once (the filter on i makes a double tap or a retry harmless) and deal the next one."""
        last = p["i"] + 1 >= len(ids)
        row = {"card_id": ids[p["i"]], "outcome": outcome, "choice": choice, "ms": ms}
        update = {"$push": {"rows": row}, "$inc": {"correct": int(outcome == "correct"), "ms": ms, "i": 1},
                  "$set": {"served_ts": None if last else now + REVEAL[outcome], **({"status": "done", "finished_ts": now} if last else {})}}
        after = await db.rf_daily_plays.find_one_and_update({"exam": p["exam"], "day": p["day"], "uid": uid, "i": p["i"], "status": "playing"}, update,
                                                            projection={"_id": 0}, return_document=ReturnDocument.AFTER)
        if after and after["status"] == "done":
            await settle(after, uid)
        return after

    @r.get("")
    async def status(exam: Exam = "JEE", x_rf_user: Optional[str] = Header(None)):
        """The lobby card and the pop-up: today's state, how many have played, the top three, and yesterday's champions."""
        uid = rf_user(x_rf_user)
        exam = require_active_exam(exam)
        test, day = uid.startswith("TEST"), ist_day()
        yday = ist_day(time.time() - 86400)
        p = await play_of(uid, exam, day)
        players, rows = await board(exam, day, test)
        _, yrows = await board(exam, yday, test)
        you = {"status": "new"}
        if p:
            you = {"status": p["status"], "i": p["i"], "correct": p["correct"], "ms": p["ms"], "rank": await rank_of(p)}
        return {"exam": exam, "day": day, "total": len(await deck(exam, day)) or TOTAL, "seconds": CARD_SECONDS, "ends_in": max(0, round(day_ends(day) - time.time())),
                "players": players, "top": shown(rows, uid, 3), "yesterday": shown(yrows, uid, 3), "you": you}

    @r.post("/start", dependencies=[Depends(arena_gate)])
    async def start(data: Start, x_rf_user: Optional[str] = Header(None)):
        """One try a day. Opening it again carries on from the card on screen (its clock kept running)."""
        uid = rf_user(x_rf_user)
        exam = require_active_exam(data.exam or "JEE")
        day = ist_day()
        ids = await deck(exam, day)
        if not ids:
            raise HTTPException(404, "Today's All India Rapid is not ready yet. Please try again in a minute.")
        try:
            await db.rf_daily_plays.insert_one({"exam": exam, "day": day, "uid": uid, "test": uid.startswith("TEST"), "status": "playing", "i": 0, "served_ts": None,
                                                "rows": [], "correct": 0, "ms": 0, "started_ts": time.time()})
        except DuplicateKeyError:
            pass
        return await current(await play_of(uid, exam, day), uid)

    @r.post("/answer")
    async def answer(data: Answer, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        exam = require_active_exam(data.exam or "JEE")
        day = ist_day()
        p = await play_of(uid, exam, day) or await play_of(uid, exam, ist_day(time.time() - 600))  # a run that crossed midnight
        if not p:
            raise HTTPException(404, "Start today's All India Rapid first.")
        if p["status"] == "done":
            return {"status": "done", "result": await result(p, uid)}
        if data.i != p["i"] or p.get("served_ts") is None:
            return await current(p, uid)  # a retry of a card already counted: show where the run really is
        ids = (await db.rf_daily.find_one({"_id": f"{p['exam']}:{p['day']}"}))["card_ids"]
        now = time.time()
        if now < p["served_ts"]:  # an answer before the card is even on screen does not count: show where the run really is
            return await current(p, uid)
        card = (await cards_of([ids[p["i"]]]))[0]
        took = max(0.0, now - p["served_ts"])
        if took > CARD_SECONDS + GRACE or (data.choice is None and not data.skip):
            outcome, ms = "timed_out", CARD_SECONDS * 1000
        elif data.choice is None:
            outcome, ms = "skipped", min(CARD_SECONDS * 1000, round(took * 1000))
        else:
            outcome, ms = ("correct" if data.choice == card["answer"] else "incorrect"), min(CARD_SECONDS * 1000, round(took * 1000))
        after = await move(p, uid, ids, data.choice if outcome in ("correct", "incorrect") else None, outcome, ms, now)
        if not after:  # the same card arrived twice at once: the first one counted
            return await current(await play_of(uid, p["exam"], p["day"]), uid)
        out = {"outcome": outcome, "answer": card["answer"], "explain": card.get("explain", ""), "formula": card.get("formula", ""), "ms": ms, "correct": after["correct"]}
        if after["status"] == "done":
            return {**out, "status": "done", "result": await result(after, uid)}
        nxt = (await cards_of([ids[after["i"]]]))[0]
        return {**out, "status": "playing", "i": after["i"], "total": len(ids), "seconds": CARD_SECONDS, "card": public(nxt, after["i"]),
                "show_in_ms": round(REVEAL[outcome] * 1000), "left_ms": CARD_SECONDS * 1000}

    @r.post("/finish")
    async def finish(data: Start, x_rf_user: Optional[str] = Header(None)):
        """Leave early: the cards not answered count as skipped, and the score goes on the board."""
        uid = rf_user(x_rf_user)
        exam = require_active_exam(data.exam or "JEE")
        p = await play_of(uid, exam, ist_day())
        if not p:
            raise HTTPException(404, "Start today's All India Rapid first.")
        if p["status"] == "playing":
            ids = (await db.rf_daily.find_one({"_id": f"{p['exam']}:{p['day']}"}))["card_ids"]
            now = time.time()
            rows = [{"card_id": ids[k], "outcome": "skipped", "choice": None, "ms": 0} for k in range(p["i"], len(ids))]
            after = await db.rf_daily_plays.find_one_and_update({"exam": exam, "day": p["day"], "uid": uid, "status": "playing"},
                                                                {"$push": {"rows": {"$each": rows}}, "$set": {"i": len(ids), "status": "done", "finished_ts": now, "served_ts": None}},
                                                                projection={"_id": 0}, return_document=ReturnDocument.AFTER)
            if after:
                return {"status": "done", "result": await settle(after, uid)}
            p = await play_of(uid, exam, p["day"])
        return {"status": "done", "result": await result(p, uid)}

    @r.get("/board")
    async def leaderboard(exam: Exam = "JEE", day: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"), x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        exam = require_active_exam(exam)
        day = day or ist_day()
        players, rows = await board(exam, day, uid.startswith("TEST"))
        p = await play_of(uid, exam, day)
        you = {"status": p["status"], "correct": p["correct"], "ms": p["ms"], "rank": await rank_of(p)} if p else {"status": "new"}
        d = await db.rf_daily.find_one({"_id": f"{exam}:{day}"}, {"card_ids": 1})
        return {"exam": exam, "day": day, "total": len(d["card_ids"]) if d else TOTAL, "players": players, "items": shown(rows, uid, 100), "you": you}

    return r


async def ensure_indexes(db):
    await db.rf_daily.create_index("exam")
    await db.rf_daily_plays.create_index([("exam", 1), ("day", 1), ("uid", 1)], unique=True)
    await db.rf_daily_plays.create_index([("exam", 1), ("day", 1), ("test", 1), ("status", 1), ("correct", -1), ("ms", 1), ("finished_ts", 1)])
