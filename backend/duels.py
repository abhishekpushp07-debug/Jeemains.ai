"""Rapid Fire Duels: two students, same 30 cards, live score race (WebSocket push, polling fallback)."""
import asyncio
import hashlib
import json
import random
import string
import time
import uuid
from typing import List, Literal, Optional

from fastapi import APIRouter, Header, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ConfigDict, Field
from pymongo import ReturnDocument
from shop import rival_profile

DUEL_CARDS = 30
CARD_SECONDS = 20
WAIT_SECONDS = 120


class DuelCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject: Literal["Physics", "Chemistry", "Mathematics"]
    chapter: Optional[str] = Field(default=None, max_length=80)
    mode: Literal["random", "invite"]
    name: str = Field(min_length=1, max_length=24)
    request_id: str = Field(min_length=8, max_length=64)


class DuelJoin(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(min_length=4, max_length=8)
    name: str = Field(min_length=1, max_length=24)


class DuelAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    index: int = Field(ge=0, lt=DUEL_CARDS)
    choice: Optional[int] = Field(default=None, ge=0, le=3)
    outcome: Literal["answer", "skipped", "timed_out"]
    ms: int = Field(default=0, ge=0, le=CARD_SECONDS * 1000 + 1000)


def make_router(db, rf_user, public_card, award):
    r = APIRouter(prefix="/rf/duels")
    card_cache: dict = {}  # cards are immutable during play: cache to skip a DB read per view
    sockets: dict = {}  # did -> {ws: {"uid": str, "sig": str}}
    tickers: dict = {}

    async def get_cards(ids):
        miss = [i for i in ids if i not in card_cache]
        if miss:
            for c in await db.rf_cards.find({"id": {"$in": miss}}, {"_id": 0}).to_list(len(miss)):
                card_cache[c["id"]] = c
            if len(card_cache) > 50000:
                card_cache.clear()
        return {i: card_cache[i] for i in ids if i in card_cache}

    async def push(did):
        """Send the latest per-player view to every open socket of this duel (only if it changed)."""
        conns = sockets.get(did)
        if not conns:
            return
        d = await db.rf_duels.find_one({"id": did})
        if not d:
            return
        for ws, meta in list(conns.items()):
            try:
                v = await view(d, meta["uid"])
                sig = hashlib.md5(json.dumps({k: x for k, x in v.items() if k != "server_now"}, sort_keys=True, default=str).encode()).hexdigest()
                if sig != meta["sig"]:
                    meta["sig"] = sig
                    await ws.send_json(v)
            except Exception:  # noqa: BLE001
                conns.pop(ws, None)

    async def ticker(did):
        """One server-side loop per live duel (not per phone): bot progress, expiry, presence."""
        try:
            while sockets.get(did):
                d = await db.rf_duels.find_one({"id": did}, {"status": 1, "vs_bot": 1})
                if not d or d["status"] in ("finished", "cancelled", "expired"):
                    await push(did)
                    break
                await asyncio.sleep(1 if d.get("vs_bot") else 2)
                await push(did)
        finally:
            tickers.pop(did, None)

    async def player(uid, name):
        prof = await db.rf_profiles.find_one_and_update({"uid": uid}, {"$set": {"name": name.strip()[:24]}}, upsert=True, return_document=True) or {}
        eq = prof.get("equipped", {})
        return {"uid": uid, "name": name.strip()[:24], "avatar": prof.get("avatar") or "robot-happy", "frame": eq.get("frame"), "entry": eq.get("entry"), "answers": [], "score": 0, "ms": 0, "done": False, "joined_ts": time.time(), "seen_ts": time.time(), "last_ts": None, "forfeit": False}

    def start_fields():
        start = time.time() + 5
        return {"status": "ready", "start_at": start, "ends_at": start + DUEL_CARDS * (CARD_SECONDS + 2) + 30}

    async def pick_cards(subject, chapter):
        match = {"subject": subject, **({"chapter": chapter} if chapter else {})}
        docs = await db.rf_cards.aggregate([{"$match": match}, {"$sample": {"size": DUEL_CARDS}}, {"$project": {"id": 1}}]).to_list(DUEL_CARDS)
        if not docs:
            raise HTTPException(404, "No reviewed cards available for this selection yet.")
        return [d["id"] for d in docs]

    def winner(d):
        ps = d["players"]
        if len(ps) < 2:
            return None
        a, b = ps
        if a.get("bot") or b.get("bot"):
            human, bot = (b, a) if a.get("bot") else (a, b)
            return human["uid"] if not human.get("forfeit") and human["score"] > 0 else ("tie" if human["score"] == 0 and not human.get("forfeit") else bot["uid"])
        if a.get("forfeit") != b.get("forfeit"):  # a player who left can never win
            return b["uid"] if a.get("forfeit") else a["uid"]
        if a["score"] != b["score"]:
            return a["uid"] if a["score"] > b["score"] else b["uid"]
        if a["ms"] != b["ms"]:
            return a["uid"] if a["ms"] < b["ms"] else b["uid"]
        return "tie"

    def tie_break(d):
        ps = d["players"]
        return len(ps) == 2 and not (ps[0].get("forfeit") or ps[1].get("forfeit")) and ps[0]["score"] == ps[1]["score"] and ps[0]["ms"] != ps[1]["ms"]

    async def simulate_bot(d):
        """AI Rival: clearly labelled, paces itself and always stays below the student's score."""
        bot = next((p for p in d["players"] if p.get("bot")), None)
        if not bot or d["status"] != "ready":
            return d
        me = next(p for p in d["players"] if not p.get("bot"))
        total = len(d["card_ids"])
        n = total if me["done"] else max(0, min(total, int((time.time() - d["start_at"]) / bot["pace"])))
        score = max(0, min(round(n * bot["acc"]), me["score"] - 1))
        score = max(score, bot["score"]) if bot["score"] <= max(0, me["score"] - 1) else max(0, me["score"] - 1)
        if n != len(bot["answers"]) or score != bot["score"]:
            answers = [{"i": i, "outcome": "bot"} for i in range(n)]
            await db.rf_duels.update_one({"id": d["id"], "players.uid": bot["uid"]}, {"$set": {"players.$.answers": answers, "players.$.score": score, "players.$.done": n >= total}})
            bot.update({"answers": answers, "score": score, "done": n >= total})
        return d

    async def settle(d):
        d = await simulate_bot(d)
        now = time.time()
        if d["status"] == "waiting" and now - d["created_ts"] > (WAIT_SECONDS if d["mode"] == "random" else 1800):
            d = await db.rf_duels.find_one_and_update({"id": d["id"], "status": "waiting"}, {"$set": {"status": "expired"}}, return_document=ReturnDocument.AFTER) or d
        if d["status"] == "ready" and (now > d["ends_at"] or all(p["done"] for p in d["players"])):
            d = await db.rf_duels.find_one_and_update({"id": d["id"], "status": "ready"}, {"$set": {"status": "finished", "winner": winner(d), "tie_break": tie_break(d), "finished_ts": now}},
                                                      return_document=ReturnDocument.AFTER) or await db.rf_duels.find_one({"id": d["id"]})
            for p in [x for x in d["players"] if not x.get("bot")]:  # reward both players at settle time, even if one never returns
                await reward_for(d, p["uid"])
        return d

    async def reward_for(d, uid):
        me = next(p for p in d["players"] if p["uid"] == uid)
        answered = sum(a["outcome"] in ("correct", "incorrect") for a in me["answers"])
        if d.get("vs_bot"):  # practice vs AI Rival: small reward, never counts as a PvP win
            return await award(uid, "duel:" + d["id"], "bot", me["score"], len(d["card_ids"]), answered, None)
        return await award(uid, "duel:" + d["id"], "duel", me["score"], len(d["card_ids"]), answered, d.get("winner") == uid)

    async def view(d, uid):
        mine_p = next((p for p in d["players"] if p["uid"] == uid), None)
        if mine_p and time.time() - mine_p.get("seen_ts", 0) > 3:  # presence write at most every 3 s per player
            await db.rf_duels.update_one({"id": d["id"], "players.uid": uid}, {"$set": {"players.$.seen_ts": time.time()}})
        d = await settle(d)
        if uid not in [p["uid"] for p in d["players"]]:
            raise HTTPException(404, "Duel not found.")
        reveal = d["status"] == "finished"
        reward = None
        if reveal:
            reward = await reward_for(d, uid)
        cards = []
        if d["status"] in ("ready", "finished"):
            docs = await get_cards(d["card_ids"])
            for k, cid in enumerate(d["card_ids"]):
                if cid in docs:
                    c = public_card_dict(docs[cid])
                    if not reveal:  # hide key and bank id so answers can't be looked up mid-duel
                        c.pop("answer", None)
                        c.pop("explain", None)
                        c["id"] = f"{d['id'][:8]}-{k}"
                    cards.append(c)
        return {
            "id": d["id"], "code": d.get("code"), "mode": d["mode"], "subject": d["subject"], "chapter": d.get("chapter"), "status": d["status"],
            "start_at": d.get("start_at"), "ends_at": d.get("ends_at"), "server_now": time.time(), "seconds_per_card": CARD_SECONDS,
            "reward": reward, "winner": d.get("winner"), "tie_break": d.get("tie_break"), "you": uid, "total": len(d["card_ids"]), "cards": cards,
            "vs_bot": d.get("vs_bot", False), "players": [{"you": p["uid"] == uid, "bot": p.get("bot", False), "avatar": p.get("avatar"), "frame": p.get("frame"), "entry": p.get("entry"), "id": p["uid"][:6] if p["uid"] != uid else "you", "name": p["name"], "answered": len(p["answers"]), "score": p["score"],
                         "done": p["done"], **({"answers": p["answers"]} if reveal or p["uid"] == uid else {}), **({"uid": p["uid"]} if reveal else {})} for p in d["players"]],
        }

    def public_card_dict(c):
        return {k: c.get(k) for k in ("id", "subject", "chapter", "topic", "prompt", "formula", "options", "answer", "explain")}

    @r.post("")
    async def create(data: DuelCreate, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        mine = await db.rf_duels.find_one({"request_id": data.request_id, "players.uid": uid})
        if mine:
            return await view(mine, uid)
        if data.mode == "random":
            now = time.time()
            match = await db.rf_duels.find_one_and_update(
                {"status": "waiting", "mode": "random", "subject": data.subject, "chapter": data.chapter, "created_ts": {"$gt": now - WAIT_SECONDS}, "players.0.seen_ts": {"$gt": now - 6}, "players.uid": {"$ne": uid}},
                {"$push": {"players": await player(uid, data.name)}, "$set": start_fields()}, sort=[("created_ts", 1)], return_document=ReturnDocument.AFTER)
            if match:
                await db.rf_duels.update_one({"id": match["id"]}, {"$addToSet": {"request_ids": data.request_id}})
                asyncio.create_task(push(match["id"]))
                return await view(match, uid)
        d = {"id": str(uuid.uuid4()), "code": "".join(random.choices(string.ascii_uppercase.replace("O", "").replace("I", "") + "23456789", k=6)),
             "mode": data.mode, "subject": data.subject, "chapter": data.chapter, "status": "waiting", "card_ids": await pick_cards(data.subject, data.chapter),
             "players": [await player(uid, data.name)], "created_ts": time.time(), "request_id": data.request_id, "request_ids": [data.request_id]}
        await db.rf_duels.insert_one(d)
        return await view(d, uid)

    @r.post("/join")
    async def join(data: DuelJoin, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        code = data.code.strip().upper()
        existing = await db.rf_duels.find_one({"code": code, "players.uid": uid})
        if existing:
            return await view(existing, uid)
        d = await db.rf_duels.find_one_and_update({"code": code, "status": "waiting", "players.uid": {"$ne": uid}},
                                                  {"$push": {"players": await player(uid, data.name)}, "$set": start_fields()}, return_document=ReturnDocument.AFTER)
        if not d:
            raise HTTPException(404, "This code is invalid, already used, or expired.")
        asyncio.create_task(push(d["id"]))
        return await view(d, uid)

    @r.get("/{did}")
    async def get(did: str, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        d = await db.rf_duels.find_one({"id": did, "players.uid": uid})
        if not d:
            raise HTTPException(404, "Duel not found.")
        return await view(d, uid)

    @r.post("/{did}/cancel")
    async def cancel(did: str, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        await db.rf_duels.update_one({"id": did, "status": "waiting", "players.0.uid": uid}, {"$set": {"status": "cancelled"}})
        return {"ok": True}

    @r.post("/{did}/bot")
    async def vs_bot(did: str, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        rival = rival_profile()
        bot = {"uid": "bot-" + uuid.uuid4().hex[:10], "bot": True, "name": rival["name"], "avatar": rival["avatar"], "frame": rival["frame"], "entry": rival["entry"],
               "answers": [], "score": 0, "ms": DUEL_CARDS * CARD_SECONDS * 1000, "done": False, "pace": random.uniform(4.0, 6.5), "acc": random.uniform(0.55, 0.8),
               "joined_ts": time.time(), "seen_ts": time.time(), "last_ts": None, "forfeit": False}
        d = await db.rf_duels.find_one_and_update({"id": did, "status": {"$in": ["waiting", "expired"]}, "players.0.uid": uid, "players": {"$size": 1}},
                                                  {"$push": {"players": bot}, "$set": {**start_fields(), "vs_bot": True}}, return_document=ReturnDocument.AFTER)
        if not d:
            raise HTTPException(409, "This duel already has an opponent.")
        asyncio.create_task(push(did))
        return await view(d, uid)

    @r.post("/{did}/forfeit")
    async def forfeit(did: str, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        await db.rf_duels.update_one({"id": did, "status": "ready", "players.uid": uid}, {"$set": {"players.$.done": True, "players.$.forfeit": True}})
        d = await db.rf_duels.find_one({"id": did, "players.uid": uid})
        if d:
            await settle(d)
            asyncio.create_task(push(did))
        return {"ok": True}

    @r.post("/{did}/answer")
    async def answer(did: str, data: DuelAnswer, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        d = await db.rf_duels.find_one({"id": did, "players.uid": uid})
        if not d:
            raise HTTPException(404, "Duel not found.")
        me = next(p for p in d["players"] if p["uid"] == uid)
        card = (await get_cards([d["card_ids"][data.index]])).get(d["card_ids"][data.index]) if data.index < len(d["card_ids"]) else None
        if not card:
            raise HTTPException(400, "Unknown card.")
        if data.index < len(me["answers"]):  # idempotent replay: never re-score a locked card
            prev = me["answers"][data.index]
            return {"index": data.index, "outcome": prev["outcome"], "answer": card["answer"], "explain": card.get("explain", ""), "score": me["score"]}
        d = await settle(d)
        if d["status"] != "ready" or time.time() < d["start_at"] - 1 or me.get("forfeit"):
            raise HTTPException(409, "This duel is not accepting answers.")
        # Tie-break time is measured by the server, never trusted from the phone.
        since = me.get("last_ts") or d["start_at"]
        server_ms = int(max(0.0, min(time.time() - since, CARD_SECONDS + 1)) * 1000)
        if data.index != len(me["answers"]):
            raise HTTPException(409, "Answer cards in order.")
        outcome = data.outcome if data.outcome != "answer" else ("correct" if data.choice == card["answer"] else "incorrect")
        entry = {"i": data.index, "choice": data.choice if data.outcome == "answer" else None, "outcome": outcome, "ms": server_ms}
        inc = 1 if outcome == "correct" else 0
        done = data.index + 1 >= len(d["card_ids"])
        res = await db.rf_duels.update_one({"id": did, "status": "ready", "players": {"$elemMatch": {"uid": uid, "answers": {"$size": data.index}}}},
                                           {"$push": {"players.$.answers": entry}, "$inc": {"players.$.score": inc, "players.$.ms": server_ms}, "$set": {"players.$.done": done, "players.$.last_ts": time.time()}})
        if not res.modified_count:
            raise HTTPException(409, "Answer already recorded.")
        await settle(await db.rf_duels.find_one({"id": did}))
        asyncio.create_task(push(did))
        return {"index": data.index, "outcome": outcome, "answer": card["answer"], "explain": card.get("explain", ""), "score": me["score"] + inc}

    @r.websocket("/{did}/ws")
    async def live(ws: WebSocket, did: str, u: str = ""):
        await ws.accept()
        try:
            uid = rf_user(u)
            d = await db.rf_duels.find_one({"id": did, "players.uid": uid})
        except HTTPException:
            d = None
        if not d:
            await ws.close(code=4404)
            return
        sockets.setdefault(did, {})[ws] = {"uid": uid, "sig": ""}
        await push(did)
        if did not in tickers:
            tickers[did] = asyncio.create_task(ticker(did))
        try:
            while True:
                await ws.receive_text()  # client pings keep the socket alive; state flows server -> phone
        except (WebSocketDisconnect, RuntimeError):
            pass
        finally:
            conns = sockets.get(did, {})
            conns.pop(ws, None)
            if not conns:
                sockets.pop(did, None)

    @r.get("")
    async def mine(x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        docs = await db.rf_duels.find({"players.uid": uid, "status": "finished", "vs_bot": {"$ne": True}}, {"_id": 0, "card_ids": 0}).sort("finished_ts", -1).limit(10).to_list(10)
        return {"items": [{"id": d["id"], "subject": d["subject"], "chapter": d.get("chapter"), "won": d.get("winner") == uid, "tie": d.get("winner") == "tie",
                           "scores": [{"name": p["name"], "you": p["uid"] == uid, "score": p["score"]} for p in d["players"]]} for d in docs]}

    return r
