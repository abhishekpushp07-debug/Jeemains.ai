"""Solo Rapid Fire sprints: deal a round (fresh, weak chapter, weak subtopics, missed cards again), finish it, history."""
import time
import uuid
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from card_bank import MAX_ROUND, Card, public_card
from database import BaseDocument, now_iso
from exam_groups import Exam, require_active_exam, resolve_exam
from gamify import phoenix
from load_guard import arena_gate
from rapid_deck import fresh_deck, seen_cards
from revision import record_learning, weak_chapters, weak_topic_deck
from scope import CARD_SECONDS, MAX_PICKS, Pick, normalise, scope_fields


class SessionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject: Literal["Physics", "Chemistry", "Mathematics", "English", "Logical Reasoning", "Biology"] = "Physics"
    chapter: Optional[str] = Field(default=None, max_length=80)
    picks: Optional[List[Pick]] = Field(default=None, max_length=MAX_PICKS)  # whole subjects or chapters for a fresh sprint
    count: int = Field(default=30, ge=1, le=MAX_ROUND)  # a fresh sprint is 30, 50 or 100 cards
    card_ids: Optional[List[str]] = Field(default=None, max_length=MAX_ROUND)
    request_id: str = Field(min_length=8, max_length=64)
    exam: Optional[Exam] = None
    diagram_only: bool = False  # old builds may still send it: diagram sprints answer 410
    revision: bool = False
    weak_topics: bool = False  # Weak Topic Sprint: only the subtopics this student keeps missing


class CardResult(BaseModel):
    card_id: str
    outcome: Literal["correct", "incorrect", "skipped", "timed_out"]
    choice: Optional[int] = Field(default=None, ge=0, le=3)
    ms: int = Field(default=0, ge=0, le=21000)


class SessionComplete(BaseModel):
    model_config = ConfigDict(extra="forbid")
    results: List[CardResult] = Field(max_length=MAX_ROUND)


class OfflineRound(BaseModel):
    """A Solo Sprint dealt and played on the phone from its own copy of the cards, sent up afterwards."""
    model_config = ConfigDict(extra="forbid")
    request_id: str = Field(min_length=8, max_length=64)
    exam: Optional[Exam] = None
    picks: Optional[List[Pick]] = Field(default=None, max_length=MAX_PICKS)
    card_ids: List[str] = Field(min_length=1, max_length=MAX_ROUND)
    results: List[CardResult] = Field(max_length=MAX_ROUND)
    played_at: Optional[str] = Field(default=None, max_length=40)  # when the phone finished it; kept for the record only
    repeat: bool = False  # the missed cards of an earlier round again: no diamonds, as online


class RfSession(BaseDocument):
    id: str
    user_id: str
    request_id: str
    subject: str
    chapter: Optional[str] = None
    picks: Optional[List[dict]] = None
    label: Optional[str] = None
    mode: str = "fresh"
    card_ids: List[str]
    status: str = "active"
    results: List[dict] = []
    summary: Optional[dict] = None
    created_at: str = Field(default_factory=now_iso)
    completed_at: Optional[str] = None
    exam: Optional[Exam] = None


def make_router(db, rf_user, award):
    r = APIRouter(prefix="/rf")
    history_totals: dict = {}  # (player, exam) -> (newest finished sprint, read_at, all-time totals)

    @r.post("/sessions", dependencies=[Depends(arena_gate)])
    async def rf_create(data: SessionCreate, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        scope = None if data.revision or data.card_ids or data.weak_topics else scope_fields(normalise(data.picks, data.subject, data.chapter))
        if scope:
            data.subject, data.chapter = scope["subject"], scope["chapter"]
        exam = resolve_exam(data.exam, data.subject)
        if data.diagram_only:
            raise HTTPException(410, "Diagram sprints are archived in this app.")
        existing = RfSession.from_mongo(await db.rf_sessions.find_one({"user_id": uid, "request_id": data.request_id}))
        if existing:
            resolve_exam(existing.exam, existing.subject)
            cards = [Card.from_mongo(d) for d in await db.rf_cards.find({"id": {"$in": existing.card_ids}}).to_list(MAX_ROUND)]
        else:
            label = None
            if data.weak_topics:
                docs, topics = await weak_topic_deck(db, uid, exam, data.count, await seen_cards(db, uid, exam))
                if not docs:
                    raise HTTPException(404, "No weak subtopics yet. Play a few sprints or matches and your Weak Topic Sprint builds itself.")
                data.subject, data.chapter, label = docs[0]["subject"], None, f"Weak Topic Sprint · {len(topics)} subtopic{'s' if len(topics) > 1 else ''}"
                mode = "weak_topics"
            elif data.revision:
                weak = await weak_chapters(db, uid, exam)
                selected = next((row for row in weak if row["subject"] == data.subject and (not data.chapter or row["chapter"] == data.chapter)), None)
                if not selected:
                    raise HTTPException(404, "No missed cards left here. Play a sprint to build your revision list.")
                docs = await db.rf_cards.find({"id": {"$in": selected["card_ids"]}, "exam": exam, "retired": {"$ne": True}}, {"_id": 0}).to_list(30)
                docs.sort(key=lambda c: selected["card_ids"].index(c["id"]))
                docs = docs[:min(30, data.count)]
                data.chapter = selected["chapter"]
                mode = "weak_revision"
            elif data.card_ids:
                docs = await db.rf_cards.find({"id": {"$in": data.card_ids}, "exam": exam, "subject": data.subject, "retired": {"$ne": True}}, {"_id": 0}).to_list(MAX_ROUND)
                mode = "repeat_missed"
            else:
                docs = await fresh_deck(db, exam, data.subject, data.chapter, data.count, picks=scope["picks"], uid=uid)
                mode = "fresh"
            if not docs:
                raise HTTPException(404, "No reviewed cards are available for this selection yet.")
            cards = [Card.from_mongo(d) for d in docs]
            existing = RfSession(id=str(uuid.uuid4()), user_id=uid, request_id=data.request_id, subject=data.subject,
                                 chapter=data.chapter, exam=exam, mode=mode, card_ids=[c.id for c in cards], **({"picks": scope["picks"], "label": scope["label"]} if scope else {"label": label} if label else {}))
            try:
                await db.rf_sessions.insert_one(existing.to_mongo())
            except DuplicateKeyError:
                return await rf_create(data, x_rf_user)
        by_id = {c.id: c for c in cards}
        return {**existing.model_dump(exclude={"mongo_id", "user_id"}),
                "cards": [public_card(by_id[i]) for i in existing.card_ids if i in by_id], "seconds_per_card": CARD_SECONDS}

    async def finish(uid: str, s: RfSession, results: List[CardResult]):
        """Closes a sprint with the student's answers and pays it once. A sprint already closed answers as it did then."""
        sid = s.id
        if s.status == "completed":
            sm = s.summary or {}
            docs = await db.rf_cards.find({"id": {"$in": s.card_ids}}, {"_id": 0}).to_list(MAX_ROUND)
            await record_learning(db, uid, "solo:" + sid, s.exam, s.results, docs, s.completed_at)
            return {**s.model_dump(exclude={"mongo_id", "user_id"}), "reward": await award(uid, "solo:" + sid, "solo", sm.get("correct", 0), sm.get("total", 0), sm.get("answered", 0), exam=s.exam)}
        cards = {c["id"]: c for c in await db.rf_cards.find({"id": {"$in": s.card_ids}}, {"_id": 0}).to_list(MAX_ROUND)}
        seen, rows = set(), []
        for res in results:
            if res.card_id not in cards or res.card_id in seen:
                continue
            seen.add(res.card_id)
            outcome = res.outcome
            if outcome in ("correct", "incorrect"):  # server re-derives correctness from the key
                outcome = "correct" if res.choice == cards[res.card_id]["answer"] else "incorrect"
            rows.append({"card_id": res.card_id, "outcome": outcome, "choice": res.choice if outcome in ("correct", "incorrect") else None,
                         "ms": res.ms, "chapter": cards[res.card_id]["chapter"], "topic": cards[res.card_id].get("topic", "")})
        for cid in s.card_ids:
            if cid not in seen:
                rows.append({"card_id": cid, "outcome": "skipped", "choice": None, "ms": 0, "chapter": cards.get(cid, {}).get("chapter", ""), "topic": ""})
        count = lambda k: sum(row["outcome"] == k for row in rows)  # noqa: E731
        correct, incorrect = count("correct"), count("incorrect")
        answered = correct + incorrect
        weak = {}
        for row in rows:
            if row["outcome"] in ("incorrect", "timed_out"):  # only cards actually attempted
                weak[row["topic"] or row["chapter"]] = weak.get(row["topic"] or row["chapter"], 0) + 1
        summary = {"total": len(rows), "correct": correct, "incorrect": incorrect, "skipped": count("skipped"),
                   "timed_out": count("timed_out"), "answered": answered, "score": correct,
                   "accuracy": round(100 * correct / answered, 1) if answered else None,
                   "revise_topics": [k for k, _ in sorted(weak.items(), key=lambda x: -x[1])][:5]}
        done = await db.rf_sessions.find_one_and_update({"id": sid, "status": "active"}, {"$set": {"status": "completed", "results": rows, "summary": summary, "completed_at": now_iso()}},
                                                        return_document=ReturnDocument.AFTER)  # the write hands back the finished sprint: no second read
        s = RfSession.from_mongo(done or await db.rf_sessions.find_one({"id": sid}))  # not ours to finish: a twin request did it, or it ran out
        if s.status != "completed":  # left open for over a day and closed by the server: it has no score to pay (this used to answer 500)
            raise HTTPException(409, "This sprint ran out of time. Start a new one.")
        await record_learning(db, uid, "solo:" + sid, s.exam, s.results, list(cards.values()), s.completed_at)
        # Diamonds come from fresh sprints only: replays of the same missed cards never earn them.
        gems, best = phoenix([row["outcome"] for row in s.results]) if s.mode == "fresh" else ({}, 0)
        reward = await award(uid, "solo:" + sid, "solo", s.summary["correct"], s.summary["total"], s.summary["answered"], exam=s.exam, diamonds=gems, phoenix_streak=best)
        return {**s.model_dump(exclude={"mongo_id", "user_id"}), "reward": reward}

    @r.post("/sessions/{sid}/complete")
    async def rf_complete(sid: str, data: SessionComplete, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        s = RfSession.from_mongo(await db.rf_sessions.find_one({"id": sid, "user_id": uid}))
        if not s:
            raise HTTPException(404, "Session not found.")
        resolve_exam(s.exam, s.subject)
        return await finish(uid, s, data.results)

    @r.post("/sessions/offline")
    async def rf_offline(data: OfflineRound, x_rf_user: Optional[str] = Header(None)):
        """A Solo Sprint the phone dealt from its own copy of the cards (rf_bank.py) and played without the server: it is
        written and closed here in one go. The same request_id is the same sprint, so a phone may send it again until it
        hears the answer. No arena seat is asked for: the round is already over."""
        uid = rf_user(x_rf_user)
        exam = require_active_exam(data.exam)
        s = RfSession.from_mongo(await db.rf_sessions.find_one({"user_id": uid, "request_id": data.request_id}))
        if not s:
            ids = list(dict.fromkeys(data.card_ids))
            found = {c["id"]: c["subject"] for c in await db.rf_cards.find({"id": {"$in": ids}, "exam": exam, "retired": {"$ne": True}}, {"_id": 0, "id": 1, "subject": 1}).to_list(MAX_ROUND)}
            ids = [i for i in ids if i in found]  # a card that left the bank (removed or retired) since the phone fetched it is left out
            if not ids:
                raise HTTPException(404, "These cards are no longer in the bank.")
            scope = scope_fields(normalise(data.picks)) if data.picks else None
            s = RfSession(id=str(uuid.uuid4()), user_id=uid, request_id=data.request_id, subject=scope["subject"] if scope else found[ids[0]],
                          chapter=scope["chapter"] if scope else None, exam=exam, mode="repeat_missed" if data.repeat else "fresh", card_ids=ids,
                          **({"picks": scope["picks"], "label": scope["label"]} if scope else {}))
            try:
                await db.rf_sessions.insert_one({**s.to_mongo(), "offline": True, "played_at": data.played_at})
            except DuplicateKeyError:  # the same round sent twice at the same moment
                s = RfSession.from_mongo(await db.rf_sessions.find_one({"user_id": uid, "request_id": data.request_id}))
        return await finish(uid, s, data.results)

    @r.get("/history")
    async def rf_history(exam: Optional[Exam] = None, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        exam = require_active_exam(exam)
        query = {"user_id": uid, "status": "completed", "exam": exam}
        docs = await db.rf_sessions.find(query, {"_id": 0, "user_id": 0, "results": 0}) \
            .sort("completed_at", -1).limit(20).to_list(20)
        won = {a["ref"]: (a.get("reward") or {}).get("diamonds") or {} for a in
               await db.rf_awards.find({"uid": uid, "ref": {"$in": ["solo:" + d["id"] for d in docs]}}, {"_id": 0, "ref": 1, "reward.diamonds": 1}).to_list(20)}
        for d in docs:
            d["diamonds"] = won.get("solo:" + d["id"], {})
        # All-time totals change only when another sprint is finished, so they are added up again only then (a look at the
        # newest finished sprint tells), and at least every 5 minutes. Before, every look added up every sprint ever played.
        newest, hit = docs[0]["completed_at"] if docs else None, history_totals.get((uid, exam))
        if hit and hit[0] == newest and time.monotonic() - hit[1] < 300:
            return {"items": docs, "totals": dict(hit[2])}
        agg = await (await db.rf_sessions.aggregate([{"$match": query},
                                                     {"$group": {"_id": None, "sessions": {"$sum": 1}, "correct": {"$sum": "$summary.correct"},
                                                                 "cards": {"$sum": "$summary.total"}}}])).to_list(1)
        totals = agg[0] if agg else {"sessions": 0, "correct": 0, "cards": 0}
        totals.pop("_id", None)
        if len(history_totals) > 20_000:
            history_totals.clear()
        history_totals[(uid, exam)] = (newest, time.monotonic(), dict(totals))
        return {"items": docs, "totals": totals}

    @r.get("/sessions/{sid}")
    async def rf_get(sid: str, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        s = RfSession.from_mongo(await db.rf_sessions.find_one({"id": sid, "user_id": uid}))
        if not s:
            raise HTTPException(404, "Session not found.")
        resolve_exam(s.exam, s.subject)
        cards = [Card.from_mongo(d) for d in await db.rf_cards.find({"id": {"$in": s.card_ids}}).to_list(MAX_ROUND)]
        by_id = {c.id: c for c in cards}
        recorded = await db.rf_awards.find_one({'uid': uid, 'ref': 'solo:' + sid}, {'_id': 0, 'reward': 1}) if s.status == 'completed' else None
        return {**s.model_dump(exclude={"mongo_id", "user_id"}), "cards": [public_card(by_id[i]) for i in s.card_ids if i in by_id], 'reward': (recorded or {}).get('reward'), "seconds_per_card": CARD_SECONDS}

    return r
