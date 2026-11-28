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
from shared_pass import SharedPass
from shop import equipped_of, safe_avatar
from jl_track import track_server

SUBJECTS = ("Physics", "Chemistry", "Mathematics")
PER_SUBJECT = 15  # 45 cards a day
TOTAL = PER_SUBJECT * len(SUBJECTS)
GRACE = 2.5  # seconds for the network, both ways
START_IN = 3.0  # the 3-2-1 before the first card
DECK_SECONDS = 60  # how long a server process keeps the day's cards before reading them again
SLOT_MS = 10_000  # the board counts finished runs by score and by 10 s of time taken (see board())
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
    decks: dict = {}  # "exam:day" -> (read_at, card ids, cards by id) of a deck that can no longer change
    deck_locks: dict = {}  # "exam:day" -> one deal at a time per process (the first minutes of a day: everyone opens the lobby)
    ranks: dict = {}  # (exam, day, uid) -> (ts, rank) of a finished run outside the top 100
    profile_fields = {"_id": 0, "uid": 1, "name": 1, "pid": 1, "avatar": 1, "equipped": 1, "xp": 1, "cups_won": 1, "cups_real": 1}

    async def remember(key: str, ids: list) -> tuple:
        cards = {c["id"]: c for c in await db.rf_cards.find({"id": {"$in": ids}}, {"_id": 0}).to_list(len(ids))}
        if len(decks) > 32:
            decks.clear()
        decks[key] = (time.monotonic(), ids, cards)
        return ids, cards

    async def dealt(exam: str, day: str) -> tuple:
        """(card ids, cards by id) of a day that is being played. Every student plays the same cards, so each server
        process reads them once a minute instead of two or three times on every answer of every student."""
        key = f"{exam}:{day}"
        hit = decks.get(key)
        if hit and time.monotonic() - hit[0] < DECK_SECONDS:
            return hit[1], hit[2]
        return await remember(key, (await db.rf_daily.find_one({"_id": key}))["card_ids"])

    async def deck(exam: str, day: str) -> list:
        """Today's 45 card ids: 15 per subject, 15 different chapters each, never a card from an earlier day.
        A day keeps the deck it was first played with; a shorter deck from before the 45-card rule that nobody has played yet is dealt again."""
        key = f"{exam}:{day}"
        hit = decks.get(key)
        if hit and time.monotonic() - hit[0] < DECK_SECONDS:
            return hit[1]
        async with deck_locks.setdefault(key, asyncio.Lock()):  # the others wait for this one deal, then read it
            hit = decks.get(key)
            if hit and time.monotonic() - hit[0] < DECK_SECONDS:
                return hit[1]
            return await deal(exam, day, key)

    async def deal(exam: str, day: str, key: str) -> list:
        have = await db.rf_daily.find_one({"_id": key})
        if have and (len(have["card_ids"]) >= TOTAL or await db.rf_daily_plays.find_one({"exam": exam, "day": day}, {"_id": 1})):
            return (await remember(key, have["card_ids"]))[0]
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

    def rank_query(p: dict) -> dict:
        return {"exam": p["exam"], "day": p["day"], "test": p.get("test", False), "status": "done",
                "$or": [{"correct": {"$gt": p["correct"]}}, {"correct": p["correct"], "ms": {"$lt": p["ms"]}},
                        {"correct": p["correct"], "ms": p["ms"], "finished_ts": {"$lt": p["finished_ts"]}}]}

    async def rank_of(p: dict, rows: list = ()) -> Optional[int]:
        """A finished run's place. In the top 100 it is the place on the board the student is looking at; below that,
        counting everyone ahead is the costly part, so the count is kept for 15 s (as long as the board itself)."""
        if not p or p.get("status") != "done":
            return None
        on_board = next((row["rank"] for row in rows if row["uid"] == p["uid"]), None)
        if on_board:
            return on_board
        k = (p["exam"], p["day"], p["uid"])
        hit = ranks.get(k)
        if hit and time.time() - hit[0] < 15:
            return hit[1]
        k = (p["exam"], p["day"], p.get("test", False))
        hit = boards.copies.get(k)
        copy = hit[1] if hit else None
        if copy:
            # Runs with more right answers, or as many in an earlier 10 s of time, are added up from the board's small
            # table. Only the runs inside this run's own 10 s are counted from the index: a handful, where the count
            # used to walk past everyone ahead (half of the day's players on average, for every student who looked).
            slot = p["ms"] // SLOT_MS
            ahead = sum(n for (correct, s), n in copy[3].items() if correct > p["correct"] or (correct == p["correct"] and s < slot))
            rank = 1 + ahead + await db.rf_daily_plays.count_documents({
                "exam": p["exam"], "day": p["day"], "test": p.get("test", False), "status": "done", "correct": p["correct"],
                "$or": [{"ms": {"$gte": slot * SLOT_MS, "$lt": p["ms"]}}, {"ms": p["ms"], "finished_ts": {"$lt": p["finished_ts"]}}]})
        else:  # this server has no copy of the board right now: the full count
            rank = 1 + await db.rf_daily_plays.count_documents(rank_query(p))
        if len(ranks) > 200_000:
            ranks.clear()
        ranks[k] = (time.time(), rank)
        return rank

    def row_of(x: dict, pr: dict, rank: int) -> dict:
        return {"rank": rank, "uid": x["uid"], "name": pr.get("name") or "JEE Aspirant", "pid": pr.get("pid"), "avatar": safe_avatar(pr.get("avatar")),
                "frame": equipped_of(pr).get("frame"), "level": level_of(pr.get("xp", 0)), "crown": crown_of(pr), "correct": x["correct"], "ms": x["ms"]}

    async def read_board(k: tuple) -> tuple:
        """(players, top rows, when the read began, finished runs by (score, 10 s of time)) for a day: the lobby of every
        student asks for it. Today's is kept 15 s; a day that is over cannot change any more (only a run that began just
        before midnight may still end), so it is kept 5 minutes."""
        exam, day, test = k
        q, began = {"exam": exam, "day": day, "test": test, "status": "done"}, time.time()
        # One pass over the day's index (the same walk the plain count made) also says how many runs ended on each
        # score in each 10 s of time taken: the number of players is their sum, and rank_of() reads places from it.
        spread = {(g["_id"]["c"] or 0, int(g["_id"]["s"] or 0)): g["n"] for g in await (await db.rf_daily_plays.aggregate(
            [{"$match": q}, {"$group": {"_id": {"c": "$correct", "s": {"$floor": {"$divide": ["$ms", SLOT_MS]}}}, "n": {"$sum": 1}}}])).to_list(None)}
        plays = await db.rf_daily_plays.find(q, {"_id": 0, "uid": 1, "correct": 1, "ms": 1}).sort([("correct", -1), ("ms", 1), ("finished_ts", 1)]).limit(100).to_list(100)
        profs = {x["uid"]: x for x in await db.rf_profiles.find({"uid": {"$in": [x["uid"] for x in plays]}}, profile_fields).to_list(100)}
        return sum(spread.values()), [row_of(x, profs.get(x["uid"], {}), n + 1) for n, x in enumerate(plays)], began, spread

    boards = SharedPass(read_board, keep=lambda k: 15 if k[1] >= ist_day() else 300)

    async def board(exam: str, day: str, test: bool) -> tuple:
        """(players, top rows). With a big crowd the 15 s pass runs in the background while this copy answers."""
        players, rows, _, _ = await boards.get((exam, day, test))
        return players, rows

    async def add_to_board(p: dict, uid: str):
        """A run just finished: the player takes their place on this server's copy of the board, and the count goes up by one.
        The copy used to be thrown away on every finish instead; with a crowd finishing every second it was then never
        kept, and every lobby that opened counted the whole day's runs again."""
        k = (p["exam"], p["day"], p.get("test", False))
        async with boards.lock(k):
            hit = boards.copies.get(k)
            if not hit or any(row["uid"] == uid for row in hit[1][1]):
                return  # no copy here (the next look reads a fresh one), or the copy already shows this run
            ts, (players, rows, began, spread) = hit
            # Same order as the board: more correct first, then less time; a run that ends later stays below its equals.
            at = next((n for n, row in enumerate(rows) if (row["correct"], -row["ms"]) < (p["correct"], -p["ms"])), len(rows))
            if at < 100:
                pr = await db.rf_profiles.find_one({"uid": uid}, profile_fields) or {}
                rows = [{**row, "rank": n + 1} for n, row in enumerate([*rows[:at], row_of(p, pr, 0), *rows[at:]][:100])]
            elif began >= p["finished_ts"]:
                return  # below the top 100, and the copy was read after this run ended: it is already counted
            where = (p["correct"], p["ms"] // SLOT_MS)
            spread[where] = spread.get(where, 0) + 1
            boards.copies[k] = (ts, (players + 1, rows, began, spread))

    def shown(rows: list, uid: str, limit: int) -> list:
        return [{k: v for k, v in row.items() if k != "uid"} | {"you": row["uid"] == uid} for row in rows[:limit]]

    async def play_of(uid: str, exam: str, day: str) -> Optional[dict]:
        return await db.rf_daily_plays.find_one({"exam": exam, "day": day, "uid": uid}, {"_id": 0})

    async def result(p: dict, uid: str) -> dict:
        players, rows = await board(p["exam"], p["day"], p.get("test", False))
        award_row = await db.rf_awards.find_one({"uid": uid, "ref": ref_of(p)}, {"_id": 0, "reward": 1}) or {}
        rank = await rank_of(p, rows)
        return {"correct": p["correct"], "total": len(p.get("rows") or []) or TOTAL, "ms": p["ms"], "rank": rank, "players": max(players, rank or 1),
                "reward": award_row.get("reward"), "day": p["day"]}

    def ref_of(p: dict) -> str:
        return f"daily:{p['exam']}:{p['day']}"

    async def settle(p: dict, uid: str) -> dict:
        """Last card done: pay the reward once and record the misses for Weak cards."""
        await add_to_board(p, uid)
        _, cards = await dealt(p["exam"], p["day"])
        await record_learning(db, uid, ref_of(p), p["exam"], p["rows"], list(cards.values()), datetime.fromtimestamp(p["finished_ts"], IST).isoformat())
        answered = sum(x["outcome"] in ("correct", "incorrect") for x in p["rows"])
        gems, best = phoenix([x["outcome"] for x in p["rows"]])
        await award(uid, ref_of(p), "solo", p["correct"], len(p["rows"]), answered, exam=p["exam"], diamonds=gems, phoenix_streak=best)
        track_server("rapid_fire_match_completed", uid, {"mode": "daily", "exam": str(p["exam"]).lower(), "result": "completed"}, key=ref_of(p))
        return await result(p, uid)

    async def current(p: dict, uid: str) -> dict:
        """The card on screen now. A card left past its time (the app was closed) counts as timed out, then the next is dealt."""
        while p["status"] == "playing":
            now = time.time()
            ids, cards = await dealt(p["exam"], p["day"])
            if p.get("served_ts") is None:
                p = await db.rf_daily_plays.find_one_and_update({"exam": p["exam"], "day": p["day"], "uid": uid, "i": p["i"], "served_ts": None},
                                                                {"$set": {"served_ts": now + START_IN}}, projection={"_id": 0}, return_document=ReturnDocument.AFTER) or await play_of(uid, p["exam"], p["day"])
                continue
            if now <= p["served_ts"] + CARD_SECONDS + GRACE:
                card = cards[ids[p["i"]]]
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
            you = {"status": p["status"], "i": p["i"], "correct": p["correct"], "ms": p["ms"], "rank": await rank_of(p, rows)}
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
        ids, cards = await dealt(p["exam"], p["day"])
        now = time.time()
        if now < p["served_ts"]:  # an answer before the card is even on screen does not count: show where the run really is
            return await current(p, uid)
        card = cards[ids[p["i"]]]
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
        nxt = cards[ids[after["i"]]]
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
            ids, _ = await dealt(exam, p["day"])
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
        you = {"status": p["status"], "correct": p["correct"], "ms": p["ms"], "rank": await rank_of(p, rows)} if p else {"status": "new"}
        d = decks.get(f"{exam}:{day}")  # a deck in memory can no longer change, so its size is right whatever its age
        d = {"card_ids": d[1]} if d else await db.rf_daily.find_one({"_id": f"{exam}:{day}"}, {"card_ids": 1})
        return {"exam": exam, "day": day, "total": len(d["card_ids"]) if d else TOTAL, "players": players, "items": shown(rows, uid, 100), "you": you}

    @r.get("/misses")
    async def misses(exam: Exam = "JEE", day: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"), x_rf_user: Optional[str] = Header(None)):
        """The result screen's Misfires tab: the cards of the student's own finished run that were not answered right,
        each with the answer they gave, the right answer and the explanation.
        Only cards the student was shown. Cards never reached (the round was left early) stay sealed: all of India plays
        the same cards today, so their answers must not leave the server through a student who quits at card 1."""
        uid = rf_user(x_rf_user)
        exam = require_active_exam(exam)
        p = await play_of(uid, exam, day or ist_day())
        if not p or p["status"] != "done":
            raise HTTPException(404, "Finish this All India Rapid round first.")
        _, cards = await dealt(exam, p["day"])
        items, sealed = [], 0
        for i, row in enumerate(p["rows"]):
            if row["outcome"] == "correct":
                continue
            card = cards.get(row["card_id"])
            if not card or (row["outcome"] == "skipped" and not row["ms"]):  # filled in by Finish: it was never on screen
                sealed += 1
                continue
            items.append({**public(card, i), "outcome": row["outcome"], "choice": row["choice"], "answer": card["answer"],
                          "explain": card.get("explain", ""), "formula": card.get("formula", "")})
        return {"day": p["day"], "total": len(p["rows"]), "correct": p["correct"], "items": items, "sealed": sealed}

    return r


async def ensure_indexes(db):
    await db.rf_daily.create_index("exam")
    await db.rf_daily_plays.create_index([("exam", 1), ("day", 1), ("uid", 1)], unique=True)
    await db.rf_daily_plays.create_index([("exam", 1), ("day", 1), ("test", 1), ("status", 1), ("correct", -1), ("ms", 1), ("finished_ts", 1)])
