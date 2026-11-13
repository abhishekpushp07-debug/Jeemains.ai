"""Rapid Fire Duels: two students, same 30 cards, live score race (WebSocket push, polling fallback)."""
import asyncio
import logging
import hashlib
import json
import random
import string
import time
import uuid
from typing import List, Literal, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ConfigDict, Field
from pymongo import CursorType, ReturnDocument
from shop import equipped_of, rival_profile, safe_avatar
from exam_groups import Exam, require_active_exam, resolve_exam
from revision import record_learning
from rf_access import verified_grant
from rapid_deck import fresh_deck
from gamify import level_of, phoenix
from social import make_pid, public_name, team_line, team_scores
from scope import Pick, label_for, normalise, scope_fields, scope_of
from leagues import record_battle

DUEL_CARDS = 30
CARD_SECONDS = 15
WAIT_SECONDS = 120
MAX_PLAYERS = 5
MAX_WATCHERS = 100  # people watching one live match at the same time


def trailing(answers: list) -> int:
    """Correct answers in a row right now (the Phoenix streak rivals can see)."""
    n = 0
    for a in reversed(answers):
        if a.get("outcome") != "correct":
            break
        n += 1
    return n


def entry_seconds(players: int) -> float:
    """Entry show: 0.5 s build-up, 3.5 s per player, 1.3 s VS slam, 0.7 s FIGHT (2 players = 9.5 s, 5 players = 20 s)."""
    return 0.5 + 3.5 * max(2, min(MAX_PLAYERS, players)) + 1.3 + 0.7


class DuelCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject: Literal["Physics", "Chemistry", "Mathematics", "Biology"] = "Physics"
    chapter: Optional[str] = Field(default=None, max_length=80)
    picks: Optional[List[Pick]] = Field(default=None, max_length=5)  # up to 5 subjects or chapters; wins over subject and chapter
    mode: Literal["random", "invite"]
    name: str = Field(min_length=1, max_length=24)
    request_id: str = Field(min_length=8, max_length=64)
    exam: Optional[Exam] = None


class DuelJoin(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(min_length=4, max_length=8)
    name: str = Field(min_length=1, max_length=24)
    exam: Optional[Exam] = None


class DuelAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    index: int = Field(ge=0, lt=DUEL_CARDS)
    choice: Optional[int] = Field(default=None, ge=0, le=3)
    outcome: Literal["answer", "skipped", "timed_out"]
    ms: int = Field(default=0, ge=0, le=CARD_SECONDS * 1000 + 1000)


log = logging.getLogger("duels")


def make_router(db, rf_user, public_card, award):
    r = APIRouter(prefix="/rf/duels")
    card_cache: dict = {}  # cards are immutable during play: cache to skip a DB read per view
    sockets: dict = {}  # did -> {ws: {"uid": str, "sig": str}}
    tickers: dict = {}
    hooks: list = []  # called once with every match that just finished (knockout cups move on from here)
    watching: dict = {}  # did -> {uid: last look} for the "watching" count
    node = uuid.uuid4().hex  # this server process
    bus = {"task": None}

    # Shared live channel across every server: a capped MongoDB collection tailed by each process.
    # Any server that changes a duel publishes {did}; every server holding a socket for it pushes fresh state.
    async def ensure_bus():
        if bus["task"]:
            return
        bus["task"] = asyncio.create_task(tail())

    async def ensure_capped():
        if "rf_events" not in await db.list_collection_names():
            try:
                await db.create_collection("rf_events", capped=True, size=32 * 1024 * 1024, max=200000)
            except Exception:  # noqa: BLE001  (another server created it first)
                pass
        if not (await db.rf_events.options()).get("capped"):
            try:  # created as a plain collection by an early insert: convert it
                await db.command("convertToCapped", "rf_events", size=32 * 1024 * 1024)
            except Exception as e:  # noqa: BLE001
                log.warning("rf_events convertToCapped failed: %s", e)
        if not await db.rf_events.find_one():
            await db.rf_events.insert_one({"did": "", "node": node, "ts": time.time()})

    async def tail():
        from collections import deque
        last_ts = None
        seen, order = set(), deque(maxlen=5000)  # ids are made per server, so filter by time and de-dupe instead
        while True:
            try:
                await ensure_capped()
                if last_ts is None:
                    last_ts = time.time()
                cur = db.rf_events.find({"ts": {"$gt": last_ts - 5}}, cursor_type=CursorType.TAILABLE_AWAIT).max_await_time_ms(300)
                while cur.alive:
                    async for ev in cur:
                        if ev["_id"] in seen:
                            continue
                        if len(order) == order.maxlen:
                            seen.discard(order[0])
                        order.append(ev["_id"])
                        seen.add(ev["_id"])
                        last_ts = max(last_ts, ev.get("ts", 0))
                        if ev.get("node") != node and ev.get("did") in sockets:
                            asyncio.create_task(push(ev["did"]))
                    await asyncio.sleep(0.05)
                await asyncio.sleep(0.2)
            except asyncio.CancelledError:
                raise
            except Exception as e:  # noqa: BLE001
                log.warning("duel live channel error: %s", e)
                await asyncio.sleep(1)

    async def publish(did):
        try:
            await db.rf_events.insert_one({"did": did, "node": node, "ts": time.time()})
        except Exception as e:  # noqa: BLE001
            log.warning("duel live channel publish failed: %s", e)

    def notify(did):
        """Push locally right away and tell the other servers."""
        asyncio.create_task(push(did))
        asyncio.create_task(publish(did))
        asyncio.create_task(ensure_bus())

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

    async def player(uid, name=""):
        prof = await db.rf_profiles.find_one({"uid": uid}) or {}
        # Verified account name (or masked number) wins over anything the phone sends.
        shown = public_name(prof) if (prof.get("display_name") or prof.get("phone_last4")) else (name.strip()[:24] or "Player")
        prof = await db.rf_profiles.find_one_and_update({"uid": uid}, {"$set": {"name": shown, "pid": make_pid(uid)}}, upsert=True, return_document=True) or {}
        eq = equipped_of(prof)
        return {"uid": uid, "pid": make_pid(uid), "name": shown, "level": level_of(prof.get("xp", 0)), "wins": prof.get("wins", 0), "avatar": safe_avatar(prof.get("avatar")), "frame": eq.get("frame"), "entry": eq.get("entry"),
                "answers": [], "score": 0, "ms": 0, "done": False, "joined_ts": time.time(), "seen_ts": time.time(), "last_ts": None, "forfeit": False}

    async def active_owned_duel(did, uid):
        d = await db.rf_duels.find_one({"id": did, "players.uid": uid}, {"_id": 0})
        if not d:
            raise HTTPException(404, "Duel not found.")
        resolve_exam(d.get("exam"), d["subject"])
        return d

    def start_fields(players=2, cards=DUEL_CARDS, delay=0.0):
        # Every phone plays the entry show against this server clock, so card 1 opens at the same moment for all.
        show = entry_seconds(players)
        start = time.time() + delay + show + 1.0
        return {"status": "ready", "start_at": start, "entry_seconds": show, "ends_at": start + cards * (CARD_SECONDS + 2) + 30}

    async def pick_cards(exam, picks, count=DUEL_CARDS):
        return [d["id"] for d in await fresh_deck(db, exam, picks[0]["subject"], count=count, picks=picks)]

    def make_bot(rival=None, cards=DUEL_CARDS):
        """A practice rival's seat. A knockout cup passes its own rival so the same one plays every round."""
        rival = rival or rival_profile()
        return {"uid": rival.get("uid") or "bot-" + uuid.uuid4().hex[:10], "bot": True, "name": rival["name"], "avatar": rival["avatar"], "frame": rival["frame"], "entry": rival["entry"],
                "level": rival.get("level") or random.randint(3, 14), "wins": rival.get("wins") or random.randint(4, 90),
                "answers": [], "score": 0, "ms": cards * CARD_SECONDS * 1000, "done": False, "pace": rival.get("pace") or random.uniform(4.0, 6.5), "acc": rival.get("acc") or random.uniform(0.55, 0.8),
                "joined_ts": time.time(), "seen_ts": time.time(), "last_ts": None, "forfeit": False}

    async def seat_duel(exam, picks, uids, challenge_id, gang_id=None, teams=None, extra=None, cards=DUEL_CARDS, bots=(), delay=0.0):
        """A Match Room or a cup round started: 2 to 5 players seated at once (or two gang teams of up to 5), entry show starts on every phone."""
        existing = await db.rf_duels.find_one({"challenge_id": challenge_id}, {"id": 1})
        if existing:
            return existing["id"]
        if not teams:
            uids = uids[:MAX_PLAYERS]
        players = [await player(u) for u in uids] + [make_bot(b, cards) for b in bots]
        more = {"vs_bot": True} if bots else {}
        if teams:  # Gang vs Gang: each side enters as one team, so the show is as long as a 1 v 1
            side = {u: t for t in ("a", "b") for u in teams[t]["uids"]}
            for p in players:
                p["team"] = side[p["uid"]]
            more = {"team_mode": True, "teams": {t: {k: teams[t][k] for k in ("id", "name", "emblem")} for t in ("a", "b")}}
        d = {"id": str(uuid.uuid4()), "code": None, "exam": exam, "mode": "friend", **scope_fields(picks), "card_ids": await pick_cards(exam, picks, cards),
             "players": players, "created_ts": time.time(), "request_id": "challenge:" + challenge_id,
             "request_ids": ["challenge:" + challenge_id], "challenge_id": challenge_id, "gang_id": gang_id, **more, **(extra or {}), **start_fields(2 if teams else len(players), cards, delay)}
        await db.rf_duels.insert_one(d)
        notify(d["id"])
        return d["id"]

    def ranking(d):
        """Live order: players who left go last, then higher score, then less answer time."""
        return sorted(d["players"], key=lambda p: (bool(p.get("forfeit")), -p["score"], p["ms"]))

    def winner(d):
        ps = d["players"]
        if len(ps) < 2:
            return None
        if d.get("team_mode"):  # the higher team score wins; a side where everybody left cannot win
            ts = team_scores(d)
            gone = {t: all(p.get("forfeit") for p in ps if p.get("team") == t) for t in ("a", "b")}
            if gone["a"] != gone["b"]:
                return "team:b" if gone["a"] else "team:a"
            a, b = (ts["a"]["score"], -ts["a"]["ms"]), (ts["b"]["score"], -ts["b"]["ms"])
            return "tie" if a == b else "team:a" if a > b else "team:b"
        if len(ps) > 2:  # everyone plays for themselves: first place wins
            first, second = ranking(d)[:2]
            if first.get("forfeit"):
                return "tie"
            return "tie" if not second.get("forfeit") and (first["score"], first["ms"]) == (second["score"], second["ms"]) else first["uid"]
        a, b = ps
        if a.get("bot") or b.get("bot"):
            human, bot = (b, a) if a.get("bot") else (a, b)
            if human.get("forfeit"):
                return bot["uid"]
            if human["score"] != bot["score"]:  # decided purely by score, like any match
                return human["uid"] if human["score"] > bot["score"] else bot["uid"]
            return "tie"
        if a.get("forfeit") != b.get("forfeit"):  # a player who left can never win
            return b["uid"] if a.get("forfeit") else a["uid"]
        if a["score"] != b["score"]:
            return a["uid"] if a["score"] > b["score"] else b["uid"]
        if a["ms"] != b["ms"]:
            return a["uid"] if a["ms"] < b["ms"] else b["uid"]
        return "tie"

    def tie_break(d):
        if len(d["players"]) < 2:
            return False
        if d.get("team_mode"):
            ts = team_scores(d)
            return ts["a"]["score"] == ts["b"]["score"] and ts["a"]["ms"] != ts["b"]["ms"]
        a, b = ranking(d)[:2]
        return not (a.get("forfeit") or b.get("forfeit")) and a["score"] == b["score"] and a["ms"] != b["ms"]

    async def simulate_bot(d):
        """Seated arena opponent (fills a quick match when no student joins): paces itself; never lowers its score."""
        bot = next((p for p in d["players"] if p.get("bot")), None)
        if not bot or d["status"] != "ready":
            return d
        me = next(p for p in d["players"] if not p.get("bot"))
        total = len(d["card_ids"])
        n = total if me["done"] else max(0, min(total, int((time.time() - d["start_at"]) / bot["pace"])))
        # Which cards the rival gets right is fixed per match, so it has real runs of correct answers (and a Phoenix streak rivals can see).
        rng = random.Random(d["id"])
        hits = [rng.random() < bot["acc"] for _ in range(total)][:n]
        natural = max(bot["score"], sum(hits))  # the opponent's score never goes down
        if me["score"] >= 5 and natural >= me["score"]:
            # a student who is really playing: hold the opponent until the student overtakes, then stay just behind
            gap = 1 + int(d["id"].replace("-", "")[:2], 16) % 3  # ends 1-3 behind, varies per match so it never looks scripted
            score = bot["score"] if bot["score"] >= me["score"] else max(bot["score"], me["score"] - gap)
        else:
            score = natural
        if n != len(bot["answers"]) or score != bot["score"]:
            answers = [{"i": i, "outcome": "bot"} for i in range(n)]
            more, gained = n - len(bot["answers"]), score - bot["score"]
            if score == sum(hits):  # playing its own game: the streak is the run of correct cards it is on right now
                streak = next((k for k, hit in enumerate(reversed(hits)) if not hit), n)
            else:  # held back behind the student: count from what its score just did
                streak = bot.get("streak", 0) + gained if gained >= more else gained
            await db.rf_duels.update_one({"id": d["id"], "players.uid": bot["uid"]}, {"$set": {"players.$.answers": answers, "players.$.score": score, "players.$.done": n >= total, "players.$.streak": streak}})
            bot.update({"answers": answers, "score": score, "done": n >= total, "streak": streak})
        return d

    async def settle(d):
        resolve_exam(d.get("exam"), d["subject"])
        d = await simulate_bot(d)
        now = time.time()
        if d["status"] == "waiting" and now - d["created_ts"] > (WAIT_SECONDS if d["mode"] == "random" else 1800):
            d = await db.rf_duels.find_one_and_update({"id": d["id"], "status": "waiting"}, {"$set": {"status": "expired"}}, return_document=ReturnDocument.AFTER) or d
        if d["status"] == "ready" and (now > d["ends_at"] or all(p["done"] for p in d["players"])):
            win = winner(d)
            fields = {"status": "finished", "winner": win, "tie_break": tie_break(d), "finished_ts": now}
            if d.get("team_mode"):
                fields["winners"] = [p["uid"] for p in d["players"] if win == "team:" + p.get("team", "") and not p.get("forfeit")]
                fields["team_scores"] = team_scores(d)
            flipped = await db.rf_duels.find_one_and_update({"id": d["id"], "status": "ready"}, {"$set": fields}, return_document=ReturnDocument.AFTER)
            if flipped and d.get("team_mode"):  # the gangs' battle record and league points, counted once
                await record_battle(db, d, win)
            d = flipped or await db.rf_duels.find_one({"id": d["id"]})
            for p in [x for x in d["players"] if not x.get("bot")]:  # reward both players at settle time, even if one never returns
                await reward_for(d, p["uid"])
            for hook in hooks if flipped else ():
                try:
                    await hook(d)
                except Exception as e:  # noqa: BLE001  (the cup catches up on its next look)
                    log.warning("match-end hook failed: %s", e)
        return d

    def won_by(d, uid):
        return d.get("winner") == uid or uid in (d.get("winners") or [])

    async def reward_for(d, uid):
        me = next(p for p in d["players"] if p["uid"] == uid)
        answered = sum(a["outcome"] in ("correct", "incorrect") for a in me["answers"])
        docs = await get_cards(d["card_ids"])
        rows = [{**a, "card_id": d["card_ids"][a["i"]]} for a in me["answers"] if a["i"] < len(d["card_ids"])]
        await record_learning(db, uid, "duel:" + d["id"], d["exam"], rows, list(docs.values()),
                              datetime.fromtimestamp(d["finished_ts"], timezone.utc).isoformat())
        # Seated arena opponents count exactly like a live match (coins, record, wins, badges).
        # Diamonds are only kept by players who finished: leaving the match forfeits them.
        gems, best = ({}, 0) if me.get("forfeit") else phoenix([a["outcome"] for a in me["answers"]])
        others = [p for p in d["players"] if p["uid"] != uid]
        line = team_line(d, uid)
        meta = ({"team": line["mine"], "vs": line["theirs"], "mine": line["my_score"], "theirs": line["their_score"]} if line
                else {"bot": True} if any(p.get("bot") for p in others)
                else {"vs": others[0]["name"], "mine": me["score"], "theirs": others[0]["score"]} if len(others) == 1 else {"players": len(d["players"]), "mine": me["score"]})
        return await award(uid, "duel:" + d["id"], "duel", me["score"], len(d["card_ids"]), answered, won_by(d, uid), exam=d["exam"], diamonds=gems, phoenix_streak=best, meta=meta)

    async def view(d, uid):
        if await db.rf_maintenance.find_one({'_id': 'portrait-cleanup', 'active': True}):
            raise HTTPException(503, 'Rapid Fire is refreshing. Please retry shortly.')
        # Reject archived matches before presence, bot, settlement or reward writes.
        resolve_exam(d.get("exam"), d["subject"])
        mine_p = next((p for p in d["players"] if p["uid"] == uid), None)
        if mine_p and d['status'] != 'finished' and time.time() - mine_p.get("seen_ts", 0) > 3:  # no presence mutations for historical reads
            await db.rf_duels.update_one({"id": d["id"], "players.uid": uid}, {"$set": {"players.$.seen_ts": time.time()}})
        d = await settle(d)
        if uid not in [p["uid"] for p in d["players"]]:
            raise HTTPException(404, "Duel not found.")
        reveal = d["status"] == "finished"
        reward = None
        if reveal:
            recorded = await db.rf_awards.find_one({'uid': uid, 'ref': 'duel:' + d['id']}, {'_id': 0, 'reward': 1})
            reward = (recorded or {}).get('reward')
        cards = []
        if d["status"] in ("ready", "finished"):
            docs = await get_cards(d["card_ids"])
            for k, cid in enumerate(d["card_ids"]):
                if cid in docs:
                    c = public_card_dict(docs[cid])
                    if not reveal:  # hide key and bank id so answers can't be looked up mid-duel
                        c.pop("answer", None)
                        c.pop("explain", None)
                        c.pop("formula", None)  # answer-side formula reference, not a prompt premise
                        c["id"] = f"{d['id'][:8]}-{k}"
                    cards.append(c)
        place = {p["uid"]: k + 1 for k, p in enumerate(ranking(d))}
        team = {}
        if d.get("team_mode"):
            ts = d.get("team_scores") if reveal and d.get("team_scores") else team_scores(d)
            team = {"team_mode": True, "my_team": next((p.get("team") for p in d["players"] if p["uid"] == uid), None), "teams": {t: {**d["teams"][t], **ts[t]} for t in ("a", "b")}}
        return {
            **team, "you_won": won_by(d, uid),
            "id": d["id"], "exam": d["exam"], "code": d.get("code"), "mode": d["mode"], "subject": d["subject"], "chapter": d.get("chapter"), "status": d["status"],
            "label": label_for(d), "picks": scope_of(d), "cup_id": d.get("cup_id"), "watchers": sum(time.time() - t < 6 for t in watching.get(d["id"], {}).values()),
            "start_at": d.get("start_at"), "ends_at": d.get("ends_at"), "server_now": time.time(), "seconds_per_card": CARD_SECONDS, "entry_seconds": d.get("entry_seconds") or entry_seconds(2), "challenge_id": d.get("challenge_id"),
            "reward": reward, "winner": d.get("winner"), "tie_break": d.get("tie_break"), "you": uid, "total": len(d["card_ids"]), "cards": cards,
            "finished_at": datetime.fromtimestamp(d['finished_ts'], timezone.utc).isoformat() if d.get('finished_ts') else None,
            "vs_bot": d.get("vs_bot", False), "players": [{"you": p["uid"] == uid, "bot": p.get("bot", False), "avatar": p.get("avatar"), "frame": p.get("frame"), "entry": p.get("entry"), "id": p["uid"][:6] if p["uid"] != uid else "you", "name": p["name"], "answered": len(p["answers"]), "score": p["score"],
                         "pid": None if p.get("bot") else p.get("pid") or make_pid(p["uid"]), "level": p.get("level", 1), "wins": p.get("wins", 0), "rank": place[p["uid"]], "team": p.get("team"),
                         "streak": p.get("streak", 0) if p.get("bot") else trailing(p["answers"]),
                         "done": p["done"], "forfeit": bool(p.get("forfeit")), **({"answers": p["answers"]} if reveal or p["uid"] == uid else {}), **({"uid": p["uid"]} if reveal else {})} for p in d["players"]],
        }

    async def can_watch(d, uid):
        """Friends of a player, their gang mates, and everybody in the same knockout cup may watch a match."""
        uids = [p["uid"] for p in d["players"] if not p.get("bot")]
        if uid in uids or await db.rf_friends.find_one({"uid": uid, "fid": {"$in": uids}}, {"_id": 1}):
            return True
        gangs = [g for g in [d.get("gang_id"), *(t["id"] for t in (d.get("teams") or {}).values())] if g]
        if await db.rf_gangs.find_one({"closed": {"$ne": True}, "$and": [{"members.uid": uid}, {"$or": [{"id": {"$in": gangs}}, {"members.uid": {"$in": uids}}]}]}, {"_id": 1}):
            return True
        return bool(d.get("cup_id") and await db.rf_cups.find_one({"id": d["cup_id"], "$or": [{"players.uid": uid}, {"invites": uid}, {"spectators": uid}]}, {"_id": 1}))

    async def spectate(d):
        """What a spectator sees: live scores, streaks and progress. Never the cards, so nobody can help a player from outside."""
        d = await settle(d)
        place = {p["uid"]: k + 1 for k, p in enumerate(ranking(d))}
        ts = (d.get("team_scores") or team_scores(d)) if d.get("team_mode") else None
        return {"spectator": True, "id": d["id"], "label": label_for(d), "status": d["status"], "watchers": sum(time.time() - t < 6 for t in watching.get(d["id"], {}).values()),
                "team_mode": bool(d.get("team_mode")), "winner_team": d.get("winner", "")[5:] if str(d.get("winner", "")).startswith("team:") else None, "start_at": d.get("start_at"), "ends_at": d.get("ends_at"), "server_now": time.time(),
                "total": len(d["card_ids"]), "cup_id": d.get("cup_id"), "tie": d.get("winner") == "tie", "teams": {t: {**d["teams"][t], **ts[t]} for t in ("a", "b")} if ts else None,
                "players": [{"name": p["name"], "avatar": p.get("avatar"), "frame": p.get("frame"), "pid": None if p.get("bot") else p.get("pid") or make_pid(p["uid"]), "bot": bool(p.get("bot")),
                             "level": p.get("level", 1), "score": p["score"], "answered": len(p["answers"]), "rank": place[p["uid"]], "team": p.get("team"), "done": p["done"], "forfeit": bool(p.get("forfeit")),
                             "streak": p.get("streak", 0) if p.get("bot") else trailing(p["answers"]), "won": d["status"] == "finished" and (won_by(d, p["uid"]) or d.get("winner") == "team:" + str(p.get("team"))),
                             "trail": [a["outcome"] == "correct" for a in p["answers"][-8:]] if not p.get("bot") else []} for p in d["players"]]}

    def public_card_dict(c):
        return {k: c.get(k) for k in ("id", "exam", "subject", "chapter", "topic", "prompt", "formula", "options", "answer", "explain", "diagram")}

    @r.post("")
    async def create(data: DuelCreate, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        picks = normalise(data.picks, data.subject, data.chapter)
        exam, scope = resolve_exam(data.exam, picks[0]["subject"]), scope_fields(picks)
        mine = await db.rf_duels.find_one({"request_id": data.request_id, "players.uid": uid})
        if mine:
            return await view(mine, uid)
        if data.mode == "random":
            now = time.time()
            match = await db.rf_duels.find_one_and_update(
                {"exam": exam, "status": "waiting", "mode": "random", "scope_key": scope["scope_key"], "created_ts": {"$gt": now - WAIT_SECONDS}, "players.0.seen_ts": {"$gt": now - 6}, "players.uid": {"$ne": uid}},
                {"$push": {"players": await player(uid, data.name)}, "$set": start_fields()}, sort=[("created_ts", 1)], return_document=ReturnDocument.AFTER)
            if match:
                await db.rf_duels.update_one({"id": match["id"]}, {"$addToSet": {"request_ids": data.request_id}})
                notify(match["id"])
                return await view(match, uid)
        d = {"id": str(uuid.uuid4()), "code": "".join(random.choices(string.ascii_uppercase.replace("O", "").replace("I", "") + "23456789", k=6)),
             "exam": exam, "mode": data.mode, **scope, "status": "waiting", "card_ids": await pick_cards(exam, picks),
             "players": [await player(uid, data.name)], "created_ts": time.time(), "request_id": data.request_id, "request_ids": [data.request_id]}
        await db.rf_duels.insert_one(d)
        return await view(d, uid)

    @r.post("/join")
    async def join(data: DuelJoin, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        exam = require_active_exam(data.exam)
        code = data.code.strip().upper()
        existing = await db.rf_duels.find_one({"code": code, "players.uid": uid})
        if existing:
            resolve_exam(existing.get("exam"), existing["subject"])
            if data.exam and existing["exam"] != data.exam:
                raise HTTPException(409, f"This is a {existing['exam']} duel. Switch your arena exam to join.")
            return await view(existing, uid)
        invitation = await db.rf_duels.find_one({"code": code}, {"_id": 0, "exam": 1, "subject": 1, "status": 1, "created_ts": 1, "players.uid": 1})
        if invitation:
            resolve_exam(invitation.get("exam"), invitation["subject"])
        if not invitation or invitation["status"] != "waiting" or invitation["created_ts"] <= time.time() - 1800:
            raise HTTPException(404, "This code is invalid, already used, or expired.")
        if invitation and data.exam and invitation["exam"] != data.exam:
            raise HTTPException(409, f"This is a {invitation['exam']} duel. Switch your arena exam to join.")
        # Codes never make strangers rivals: only friends (made with a Friend Code) can take this seat.
        if not await db.rf_friends.find_one({"uid": uid, "fid": invitation["players"][0]["uid"]}, {"_id": 1}):
            raise HTTPException(403, "Duel codes are only for friends. Add this player with their Friend Code first.")
        d = await db.rf_duels.find_one_and_update({"code": code, "status": "waiting", "created_ts": {"$gt": time.time() - 1800}, "players.uid": {"$ne": uid}, "exam": exam},
                                                  {"$push": {"players": await player(uid, data.name)}, "$set": start_fields()}, return_document=ReturnDocument.AFTER)
        if not d:
            raise HTTPException(404, "This code is invalid, already used, or expired.")
        notify(d["id"])
        return await view(d, uid)

    @r.get("/live")
    async def live_now(x_rf_user: Optional[str] = Header(None)):
        """Matches being played right now by your friends and gang mates, to watch."""
        uid = rf_user(x_rf_user)
        blocks = await db.rf_blocks.find({"$or": [{"uid": uid}, {"bid": uid}]}, {"_id": 0}).to_list(500)
        hidden = {uid} | {b["bid"] for b in blocks} | {b["uid"] for b in blocks}
        uids = {f["fid"] for f in await db.rf_friends.find({"uid": uid}, {"_id": 0, "fid": 1}).to_list(500)}
        for g in await db.rf_gangs.find({"members.uid": uid, "closed": {"$ne": True}}, {"_id": 0, "members.uid": 1}).to_list(10):
            uids |= {m["uid"] for m in g["members"][:200]}
        now = time.time()
        docs = await db.rf_duels.find({"status": "ready", "ends_at": {"$gt": now}, "players.uid": {"$in": list(uids - hidden), "$ne": uid}},
                                      {"_id": 0, "id": 1, "subject": 1, "chapter": 1, "label": 1, "picks": 1, "start_at": 1, "cup_id": 1, "card_ids": 1, "teams": 1, "players.name": 1, "players.avatar": 1,
                                       "players.frame": 1, "players.score": 1, "players.answers.i": 1}).sort("start_at", -1).limit(8).to_list(8)
        return {"items": [{"id": d["id"], "label": label_for(d), "cup": bool(d.get("cup_id")), "started": d["start_at"] <= now, "total": len(d["card_ids"]),
                           "teams": [d["teams"][t]["name"] for t in ("a", "b")] if d.get("teams") else None,
                           "players": [{"name": p["name"], "avatar": p.get("avatar"), "frame": p.get("frame"), "score": p["score"], "answered": len(p.get("answers") or [])} for p in d["players"][:5]]} for d in docs]}

    @r.get("/{did}/watch")
    async def watch(did: str, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        d = await db.rf_duels.find_one({"id": did}, {"_id": 0})
        if not d or d["status"] not in ("ready", "finished") or not await can_watch(d, uid):
            raise HTTPException(404, "This match is not open to watch.")
        if d["status"] == "ready":
            seen, now = watching.setdefault(did, {}), time.time()
            if now - seen.get(uid, 0) >= 6 and sum(now - t < 6 for t in seen.values()) >= MAX_WATCHERS:
                raise HTTPException(409, f"{MAX_WATCHERS} people are already watching this match. Try again in a moment.")
            seen[uid] = now
            if len(watching) > 2000:
                watching.clear()
        return await spectate(d)

    @r.get("/{did}")
    async def get(did: str, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        d = await active_owned_duel(did, uid)
        return await view(d, uid)

    @r.post("/{did}/cancel")
    async def cancel(did: str, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        await active_owned_duel(did, uid)
        await db.rf_duels.update_one({"id": did, "status": "waiting", "players.0.uid": uid}, {"$set": {"status": "cancelled"}})
        return {"ok": True}

    @r.post("/{did}/bot")
    async def vs_bot(did: str, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        await active_owned_duel(did, uid)
        bot = make_bot()
        d = await db.rf_duels.find_one_and_update({"id": did, "status": {"$in": ["waiting", "expired"]}, "players.0.uid": uid, "players": {"$size": 1}},
                                                  {"$push": {"players": bot}, "$set": {**start_fields(), "vs_bot": True}}, return_document=ReturnDocument.AFTER)
        if not d:
            raise HTTPException(409, "This duel already has an opponent.")
        notify(did)
        return await view(d, uid)

    @r.post("/{did}/forfeit")
    async def forfeit(did: str, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        await active_owned_duel(did, uid)
        await db.rf_duels.update_one({"id": did, "status": "ready", "players.uid": uid}, {"$set": {"players.$.done": True, "players.$.forfeit": True}})
        d = await db.rf_duels.find_one({"id": did, "players.uid": uid})
        if d:
            await settle(d)
            notify(did)
        return {"ok": True}

    @r.post("/{did}/answer")
    async def answer(did: str, data: DuelAnswer, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        d = await active_owned_duel(did, uid)
        me = next(p for p in d["players"] if p["uid"] == uid)
        card = (await get_cards([d["card_ids"][data.index]])).get(d["card_ids"][data.index]) if data.index < len(d["card_ids"]) else None
        if not card:
            raise HTTPException(400, "Unknown card.")
        if data.index < len(me["answers"]):  # idempotent replay: never re-score a locked card
            prev = me["answers"][data.index]
            return {"index": data.index, "outcome": prev["outcome"], "answer": card["answer"], "explain": card.get("explain", ""), "formula": card.get('formula', ''), "score": me["score"]}
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
        notify(did)
        return {"index": data.index, "outcome": outcome, "answer": card["answer"], "explain": card.get("explain", ""), "formula": card.get('formula', ''), "score": me["score"] + inc}

    @r.websocket("/{did}/ws")
    async def live(ws: WebSocket, did: str, u: str = ""):
        await ws.accept()
        try:
            # A UID in the URL never proves membership. First frame carries an
            # expiring opaque grant; tokens stay out of URL/access logs.
            hello = json.loads(await asyncio.wait_for(ws.receive_text(), timeout=8))
            if not isinstance(hello, dict):
                raise HTTPException(401, 'Invalid socket authentication.')
            grant = await verified_grant(db, hello.get('token', ''))
            uid = grant['uid']
            d = await db.rf_duels.find_one({"id": did, "players.uid": uid})
            if d:
                resolve_exam(d.get("exam"), d["subject"])
        except (HTTPException, ValueError, asyncio.TimeoutError, WebSocketDisconnect):
            d = None
        if not d:
            await ws.close(code=4404)
            return
        await ensure_bus()
        sockets.setdefault(did, {})[ws] = {"uid": uid, "sig": ""}
        await push(did)
        if did not in tickers:
            tickers[did] = asyncio.create_task(ticker(did))
        try:
            while True:
                ttl = grant['expires_at'].replace(tzinfo=timezone.utc).timestamp() - time.time()
                if ttl <= 0:
                    raise asyncio.TimeoutError
                # Expire even an idle socket; a UID or an old token is not a session.
                await asyncio.wait_for(ws.receive_text(), timeout=ttl)
        except asyncio.TimeoutError:
            await ws.close(code=4401)
        except (WebSocketDisconnect, RuntimeError):
            pass
        finally:
            conns = sockets.get(did, {})
            conns.pop(ws, None)
            if not conns:
                sockets.pop(did, None)

    @r.get("")
    async def mine(exam: Optional[Exam] = None, friends_only: bool = False, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        exam = require_active_exam(exam)
        query = {"players.uid": uid, "status": "finished", "exam": exam}
        if friends_only:
            query.update(mode={'$in': ['invite', 'friend']}, vs_bot={'$ne': True})
        docs = await db.rf_duels.find(query, {"_id": 0, "card_ids": 0}).sort("finished_ts", -1).limit(50).to_list(50)
        won = {a["ref"]: (a.get("reward") or {}).get("diamonds") or {} for a in
               await db.rf_awards.find({"uid": uid, "ref": {"$in": ["duel:" + d["id"] for d in docs]}}, {"_id": 0, "ref": 1, "reward.diamonds": 1}).to_list(50)}
        return {"items": [{"id": d["id"], "exam": d["exam"], "subject": d["subject"], "chapter": d.get("chapter"), "label": label_for(d), "cup": bool(d.get("cup_id")), "won": won_by(d, uid), "tie": d.get("winner") == "tie", "team": team_line(d, uid),
                           "finished_at": datetime.fromtimestamp(d['finished_ts'], timezone.utc).isoformat(), 'mode': d['mode'], "diamonds": won.get("duel:" + d["id"], {}),
                           "place": next(k + 1 for k, p in enumerate(ranking(d)) if p["uid"] == uid),
                           "scores": [{"name": p["name"], "you": p["uid"] == uid, "score": p["score"], "bot": bool(p.get("bot")), "pid": None if p.get("bot") else p.get("pid") or make_pid(p["uid"]),
                                       "avatar": p.get("avatar"), "frame": p.get("frame")} for p in ranking(d)]} for d in docs]}

    return r, {"seat": seat_duel, "settle": settle, "hooks": hooks}
