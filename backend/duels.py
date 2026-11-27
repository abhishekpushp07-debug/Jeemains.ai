"""Rapid Fire Duels: two students, same 30 cards, live score race (WebSocket push, polling fallback)."""
import asyncio
import json
import logging
import random
import string
import time
import uuid
import orjson
from typing import List, Literal, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ConfigDict, Field
from pymongo import CursorType, ReturnDocument
from shop import equipped_of, rival_profile, safe_avatar
from exam_groups import Exam, require_active_exam, resolve_exam
from revision import record_learning
from rf_access import maintenance_on, verified_grant
from load_guard import arena_gate, load
from rapid_deck import fresh_deck
from gamify import level_of, phoenix
from social import make_pid, public_name, team_line, team_scores
from scope import CARD_COUNTS, CARD_SECONDS, MAX_PICKS, Pick, label_for, normalise, scope_fields, scope_of
from leagues import record_battle

DUEL_CARDS = 30
MAX_CARDS = max(CARD_COUNTS)
WAIT_SECONDS = 120
MAX_PLAYERS = 5
MAX_WATCHERS = 100  # people watching one live match at the same time
CIRCLE_SECONDS = 20  # how long a player's circle (friends + gang mates) is kept for the lobby's live strip
EVENTS_BYTES, EVENTS_MAX = 128 * 1024 * 1024, 500000  # the live channel between servers (capped: oldest changes roll off)


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
    subject: Literal["Physics", "Chemistry", "Mathematics", "English", "Logical Reasoning", "Biology"] = "Physics"
    chapter: Optional[str] = Field(default=None, max_length=80)
    picks: Optional[List[Pick]] = Field(default=None, max_length=MAX_PICKS)  # whole subjects or chapters; wins over subject and chapter
    mode: Literal["random", "invite"]
    name: str = Field(min_length=1, max_length=24)
    request_id: str = Field(min_length=8, max_length=64)
    exam: Optional[Exam] = None
    count: Literal[30, 50, 100] = DUEL_CARDS  # quick match pairs only players who chose the same count


class DuelJoin(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(min_length=4, max_length=8)
    name: str = Field(min_length=1, max_length=24)
    exam: Optional[Exam] = None


class DuelAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    index: int = Field(ge=0, lt=MAX_CARDS)
    choice: Optional[int] = Field(default=None, ge=0, le=3)
    outcome: Literal["answer", "skipped", "timed_out"]
    ms: int = Field(default=0, ge=0, le=CARD_SECONDS * 1000 + 1000)


log = logging.getLogger("duels")


def make_router(db, rf_user, public_card, award):
    r = APIRouter(prefix="/rf/duels")
    card_cache: dict = {}  # cards are immutable during play: cache to skip a DB read per view
    sockets: dict = {}  # did -> {ws: {"uid": str, "sig": tuple | None}}
    docs: dict = {}  # did -> (latest duel doc this process knows, when it was read): heartbeats reuse it instead of re-reading
    due: dict = {}  # did -> next heartbeat (monotonic): practice-rival moves, expiry, matchmaking presence
    dirty: dict = {}  # did -> (doc, read_at) to push now, or None to re-read first (changed on another server)
    outbox: dict = {}  # server -> duels changed here that this server shows on open sockets (sent in one batch)
    wide: set = set()  # changes whose socket holders are unknown: told to every server
    hooks: list = []  # called once with every match that just finished (knockout cups move on from here)
    watching: dict = {}  # did -> {uid: when this process last recorded that look in rf_watch}
    wcount: dict = {}  # did -> (read_at, watchers on every server), only for matches someone is watching
    circles: dict = {}  # uid -> (read_at, friends and gang mates whose live matches the lobby strip may show)
    fixed: dict = {}  # did -> (card_ids, start_at, ends_at, uids): never change once a match is ready, so answers skip a read
    bot_runs: dict = {}  # did -> which cards the practice rival gets right (fixed per match)
    node = uuid.uuid4().hex  # this server process
    bus: dict = {}
    wake, flush = asyncio.Event(), asyncio.Event()

    # One live engine per server process (not one loop per match):
    #   pusher    - pushes every changed match to its open sockets; bursts are coalesced, missing docs read in one query
    #   heartbeat - wakes only the matches whose moment has come (next rival move, expiry), using the doc it already has
    #   publisher - tells the servers holding a match's sockets that it changed, one capped-collection insert per 50 ms
    #   tail      - receives only the changes addressed to this server and marks those matches dirty here
    # Every match lists the servers holding its sockets (`ws_nodes`), so a change reaches only those servers (nobody else
    # reads it), and a match whose sockets are all on the server that changed it sends nothing at all. With many servers
    # this keeps the traffic in proportion to the changes instead of changes x servers.
    def ensure_bus():
        if bus:
            return
        bus.update(tail=asyncio.create_task(tail()), pusher=asyncio.create_task(pusher()),
                   heartbeat=asyncio.create_task(heartbeat()), publisher=asyncio.create_task(publisher()))

    async def ensure_capped():
        if "rf_events" not in await db.list_collection_names():
            try:
                await db.create_collection("rf_events", capped=True, size=EVENTS_BYTES, max=EVENTS_MAX)
            except Exception:  # noqa: BLE001  (another server created it first)
                pass
        opts = await db.rf_events.options()
        if not opts.get("capped"):
            try:  # created as a plain collection by an early insert: convert it
                await db.command("convertToCapped", "rf_events", size=EVENTS_BYTES)
            except Exception as e:  # noqa: BLE001
                log.warning("rf_events convertToCapped failed: %s", e)
        elif opts.get("size", 0) < EVENTS_BYTES:
            try:  # older, smaller channel: room for ~a minute of a big crowd's changes
                await db.command("collMod", "rf_events", cappedSize=EVENTS_BYTES, cappedMax=EVENTS_MAX)
            except Exception as e:  # noqa: BLE001
                log.warning("rf_events resize failed: %s", e)
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
                cur = db.rf_events.find({"ts": {"$gt": last_ts - 5}, "$or": [{"to": node}, {"all": True}]}, {"by." + node: 1, "dids": 1, "node": 1, "ts": 1},
                                        cursor_type=CursorType.TAILABLE_AWAIT).max_await_time_ms(300)
                while cur.alive:
                    async for ev in cur:
                        if ev["_id"] in seen:
                            continue
                        if len(order) == order.maxlen:
                            seen.discard(order[0])
                        order.append(ev["_id"])
                        seen.add(ev["_id"])
                        last_ts = max(last_ts, ev.get("ts", 0))
                        if ev.get("node") != node:
                            for did in (ev.get("by") or {}).get(node, []) + (ev.get("dids") or []):
                                mark(did, None)
                    await asyncio.sleep(0.05)
                await asyncio.sleep(0.2)
            except asyncio.CancelledError:
                raise
            except Exception as e:  # noqa: BLE001
                log.warning("duel live channel error: %s", e)
                await asyncio.sleep(1)

    async def publisher():
        while True:
            await flush.wait()
            await asyncio.sleep(0.05)  # gather everything that changes in the same instant
            flush.clear()
            by, everyone = {n: list(s) for n, s in outbox.items() if s}, list(wide)
            outbox.clear()
            wide.clear()
            if not by and not everyone:
                continue
            ev = {"node": node, "ts": time.time(), "to": list(by), "by": by}
            if everyone:
                ev.update(all=True, dids=everyone)
            try:
                await db.rf_events.insert_one(ev)
            except Exception as e:  # noqa: BLE001
                log.warning("duel live channel publish failed: %s", e)

    def mark(did, entry):
        """Queue a push for this match if anyone here is watching it. `entry` is (doc, read_at), or None to re-read."""
        if did in sockets:
            dirty[did] = entry
            wake.set()

    def notify(did, doc=None):
        """A match changed: push here right away and tell only the other servers that hold its sockets."""
        ensure_bus()
        mark(did, (doc, time.monotonic()) if doc else None)
        if doc is None:
            wide.add(did)
        else:
            others = [n for n in doc.get("ws_nodes") or () if n != node]
            if not others:
                return  # every socket of this match is here (or nobody is connected): nothing to tell
            for n in others:
                outbox.setdefault(n, set()).add(did)
        flush.set()

    async def pusher():
        while True:
            await wake.wait()
            wake.clear()
            try:
                batch = {did: e for did, e in dirty.items() if did in sockets}
                dirty.clear()
                need = [did for did, e in batch.items() if e is None]
                for i in range(0, len(need), 500):
                    now = time.monotonic()
                    for d in await db.rf_duels.find({"id": {"$in": need[i:i + 500]}}, {"_id": 0}).to_list(500):
                        batch[d["id"]] = (d, now)
                ready = [e for e in batch.values() if e]
                for i in range(0, len(ready), 200):
                    await asyncio.gather(*(deliver(*e) for e in ready[i:i + 200]), return_exceptions=True)
            except Exception as e:  # noqa: BLE001  (one bad batch must never stop live play)
                log.warning("duel pusher error: %s", e)
                await asyncio.sleep(0.2)

    async def heartbeat():
        while True:
            await asyncio.sleep(0.25)
            now = time.monotonic()
            for did, at in list(due.items()):
                if at <= now:
                    due[did] = now + 5  # deliver() sets the real next moment
                    known = docs.get(did)
                    mark(did, known if known and now - known[1] < 10 else None)  # re-read at least every 10 s, just in case

    def next_beat(d):
        """Seconds until this match needs a look without anyone doing anything."""
        now = time.time()
        if d["status"] == "waiting":
            return 2.0  # keeps the host visible to quick-match and expires the wait on time
        if d["status"] != "ready":
            return None
        if d.get("vs_bot"):
            bot = next((p for p in d["players"] if p.get("bot")), None)
            if bot and d["start_at"] > now:
                return min(5.0, max(0.25, d["start_at"] - now + 0.05))
            if bot and not bot["done"]:
                step = (int((now - d["start_at"]) / bot["pace"]) + 1) * bot["pace"] + d["start_at"]
                return min(3.0, max(0.25, step - now + 0.05))
        return min(5.0, max(0.5, d["ends_at"] - now + 0.05))

    def state_sig(d, uid, watchers, reward):
        """What a player's screen shows, minus the clock: a push goes out only when this changes."""
        return (d["status"], d.get("start_at"), d.get("winner"), watchers, bool(reward), uid,
                tuple((p["uid"], len(p["answers"]), p["score"], p["done"], bool(p.get("forfeit")), p.get("streak", 0)) for p in d["players"]))

    async def deliver(d, read_at):
        did = d["id"]
        if not sockets.get(did):
            return
        d = await settle(d)
        docs[did] = (d, read_at)
        remember(d)
        await count_watchers(did, d)
        beat = next_beat(d)
        if beat is None:
            due.pop(did, None)
        else:
            due[did] = time.monotonic() + beat
        if d["status"] == "waiting":
            await presence(d, [m["uid"] for m in sockets.get(did, {}).values()])
        watchers = live_watchers(did)
        rewards = {}
        for ws, meta in list(sockets.get(did, {}).items()):
            uid = meta["uid"]
            try:
                if d["status"] == "finished" and uid not in rewards:
                    rewards[uid] = await reward_of(d, uid)
                sig = state_sig(d, uid, watchers, rewards.get(uid))
                if sig == meta["sig"]:
                    continue
                deck = "reveal" if d["status"] == "finished" else "hidden" if d["status"] == "ready" else None
                held = meta["lite"] and deck and meta["deck"] == deck  # this phone already has these 30 cards
                v = await render(d, uid, rewards.get(uid), with_cards=not held)
                if held:
                    v.pop("cards", None)  # send only what moved: a few hundred bytes instead of the whole deck
                await asyncio.wait_for(ws.send_text(frame(v)), timeout=5)
                meta["sig"], meta["deck"] = sig, deck
            except Exception:  # noqa: BLE001  (a dead or stuck phone loses its socket; it reconnects or polls)
                sockets.get(did, {}).pop(ws, None)

    def frame(v):
        try:
            return orjson.dumps(v).decode()
        except TypeError:
            return json.dumps(v, default=str)

    async def presence(d, uids):
        """Waiting rooms only: quick-match pairs a student with a host seen in the last 6 seconds."""
        now = time.time()
        for p in d["players"]:
            if p["uid"] in uids and now - p.get("seen_ts", 0) > 3:
                p["seen_ts"] = now
                await db.rf_duels.update_one({"id": d["id"], "players.uid": p["uid"]}, {"$set": {"players.$.seen_ts": now}})

    def live_watchers(did):
        hit = wcount.get(did)
        return hit[1] if hit and time.monotonic() - hit[0] < 10 else 0

    async def count_watchers(did, d=None):
        """Spectators on every server (rf_watch). Matches nobody watches (no recent `watched_ts`) cost nothing."""
        if d is not None and d.get("watched_ts", 0) < time.time() - 10:
            return 0
        hit = wcount.get(did)
        if hit and time.monotonic() - hit[0] < 2:
            return hit[1]
        n = await db.rf_watch.count_documents({"did": did, "ts": {"$gt": time.time() - 6}})
        if len(wcount) > 5000:
            wcount.clear()
        wcount[did] = (time.monotonic(), n)
        return n

    def remember(d):
        if d.get("status") == "ready" and d["id"] not in fixed:
            if len(fixed) > 50000:
                fixed.clear()
            fixed[d["id"]] = (d["card_ids"], d["start_at"], d["ends_at"], frozenset(p["uid"] for p in d["players"]))

    async def reward_of(d, uid):
        recorded = await db.rf_awards.find_one({'uid': uid, 'ref': 'duel:' + d['id']}, {'_id': 0, 'reward': 1})
        return (recorded or {}).get('reward')

    async def get_cards(ids):
        miss = [i for i in ids if i not in card_cache]
        if miss:
            for c in await db.rf_cards.find({"id": {"$in": miss}}, {"_id": 0}).to_list(len(miss)):
                card_cache[c["id"]] = c
            if len(card_cache) > 50000:
                card_cache.clear()
        return {i: card_cache[i] for i in ids if i in card_cache}

    async def player(uid, name=""):
        prof = await db.rf_profiles.find_one({"uid": uid}) or {}
        # Verified account name (or masked number) wins over anything the phone sends.
        shown = public_name(prof) if (prof.get("chosen_name") or prof.get("display_name") or prof.get("phone_last4")) else (name.strip()[:24] or "Player")
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

    async def pick_cards(exam, picks, count=DUEL_CARDS, uid=None):
        """The deck for a match. When the chosen subjects or chapters are too small for 50 or 100 cards, the largest count that fits is dealt."""
        for n in [count] + sorted((c for c in CARD_COUNTS if c < count), reverse=True):
            try:
                return [d["id"] for d in await fresh_deck(db, exam, picks[0]["subject"], count=n, picks=picks, uid=uid)]
            except HTTPException as e:
                if e.status_code != 400 or n <= DUEL_CARDS:
                    raise

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
        card_ids = await pick_cards(exam, picks, cards)
        cards = len(card_ids)
        players = [await player(u) for u in uids] + [make_bot(b, cards) for b in bots]
        more = {"vs_bot": True} if bots else {}
        if teams:  # Gang vs Gang: each side enters as one team, so the show is as long as a 1 v 1
            side = {u: t for t in ("a", "b") for u in teams[t]["uids"]}
            for p in players:
                p["team"] = side[p["uid"]]
            more = {"team_mode": True, "teams": {t: {k: teams[t][k] for k in ("id", "name", "emblem")} for t in ("a", "b")}}
        d = {"id": str(uuid.uuid4()), "code": None, "exam": exam, "mode": "friend", **scope_fields(picks), "card_ids": card_ids, "cards_n": cards,
             "players": players, "created_ts": time.time(), "request_id": "challenge:" + challenge_id,
             "request_ids": ["challenge:" + challenge_id], "challenge_id": challenge_id, "gang_id": gang_id, **more, **(extra or {}), **start_fields(2 if teams else len(players), cards, delay)}
        await db.rf_duels.insert_one(d)
        notify(d["id"], d)
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
        runs = bot_runs.get(d["id"])
        if runs is None or len(runs) != total:
            rng = random.Random(d["id"])
            runs = [rng.random() < bot["acc"] for _ in range(total)]
            if len(bot_runs) > 20000:
                bot_runs.clear()
            bot_runs[d["id"]] = runs
        hits = runs[:n]
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
            # Every player is paid at settle time, even one who never returns; the players' rewards are independent of
            # each other, so they are written side by side (the last answer of a 5-player room waited for 5 in a row).
            await asyncio.gather(*(reward_for(d, p["uid"]) for p in d["players"] if not p.get("bot")))
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
        """A player's look over HTTP (first load and the polling fallback)."""
        if await maintenance_on(db):
            raise HTTPException(503, 'Rapid Fire is refreshing. Please retry shortly.')
        # Reject archived matches before presence, bot, settlement or reward writes.
        resolve_exam(d.get("exam"), d["subject"])
        if d["status"] == "waiting":  # no presence mutations for live or historical reads
            await presence(d, [uid])
        d = await settle(d)
        if uid not in [p["uid"] for p in d["players"]]:
            raise HTTPException(404, "Duel not found.")
        await count_watchers(d["id"], d)
        return await render(d, uid, await reward_of(d, uid) if d["status"] == "finished" else None)

    async def render(d, uid, reward, with_cards=True):
        """The per-player state of a settled match. No database writes; cards come from the in-memory cache."""
        reveal = d["status"] == "finished"
        cards = []
        if with_cards and d["status"] in ("ready", "finished"):
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
            "label": label_for(d), "picks": scope_of(d), "cup_id": d.get("cup_id"), "watchers": live_watchers(d["id"]),
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
        await count_watchers(d["id"])
        place = {p["uid"]: k + 1 for k, p in enumerate(ranking(d))}
        ts = (d.get("team_scores") or team_scores(d)) if d.get("team_mode") else None
        return {"spectator": True, "id": d["id"], "label": label_for(d), "status": d["status"], "watchers": live_watchers(d["id"]),
                "team_mode": bool(d.get("team_mode")), "winner_team": d.get("winner", "")[5:] if str(d.get("winner", "")).startswith("team:") else None, "start_at": d.get("start_at"), "ends_at": d.get("ends_at"), "server_now": time.time(),
                "total": len(d["card_ids"]), "cup_id": d.get("cup_id"), "tie": d.get("winner") == "tie", "teams": {t: {**d["teams"][t], **ts[t]} for t in ("a", "b")} if ts else None,
                "players": [{"name": p["name"], "avatar": p.get("avatar"), "frame": p.get("frame"), "pid": None if p.get("bot") else p.get("pid") or make_pid(p["uid"]), "bot": bool(p.get("bot")),
                             "level": p.get("level", 1), "score": p["score"], "answered": len(p["answers"]), "rank": place[p["uid"]], "team": p.get("team"), "done": p["done"], "forfeit": bool(p.get("forfeit")),
                             "streak": p.get("streak", 0) if p.get("bot") else trailing(p["answers"]), "won": d["status"] == "finished" and (won_by(d, p["uid"]) or d.get("winner") == "team:" + str(p.get("team"))),
                             "trail": [a["outcome"] == "correct" for a in p["answers"][-8:]] if not p.get("bot") else []} for p in d["players"]]}

    def public_card_dict(c):
        return {k: c.get(k) for k in ("id", "exam", "subject", "chapter", "topic", "prompt", "formula", "options", "answer", "explain", "diagram")}

    @r.post("", dependencies=[Depends(arena_gate)])
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
                {"exam": exam, "status": "waiting", "mode": "random", "scope_key": scope["scope_key"], "cards_n": data.count, "created_ts": {"$gt": now - WAIT_SECONDS}, "players.0.seen_ts": {"$gt": now - 6}, "players.uid": {"$ne": uid}},
                {"$push": {"players": await player(uid, data.name)}, "$set": start_fields(cards=data.count), "$addToSet": {"request_ids": data.request_id}}, sort=[("created_ts", 1)], return_document=ReturnDocument.AFTER)
            if match:
                notify(match["id"], match)
                return await view(match, uid)
        card_ids = await pick_cards(exam, picks, data.count, uid)
        d = {"id": str(uuid.uuid4()), "code": "".join(random.choices(string.ascii_uppercase.replace("O", "").replace("I", "") + "23456789", k=6)),
             "exam": exam, "mode": data.mode, **scope, "status": "waiting", "card_ids": card_ids, "cards_n": len(card_ids),
             "players": [await player(uid, data.name)], "created_ts": time.time(), "request_id": data.request_id, "request_ids": [data.request_id]}
        await db.rf_duels.insert_one(d)
        return await view(d, uid)

    @r.post("/join", dependencies=[Depends(arena_gate)])
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
        invitation = await db.rf_duels.find_one({"code": code}, {"_id": 0, "exam": 1, "subject": 1, "status": 1, "created_ts": 1, "players.uid": 1, "cards_n": 1})
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
                                                  {"$push": {"players": await player(uid, data.name)}, "$set": start_fields(cards=invitation.get("cards_n") or DUEL_CARDS)}, return_document=ReturnDocument.AFTER)
        if not d:
            raise HTTPException(404, "This code is invalid, already used, or expired.")
        notify(d["id"], d)
        return await view(d, uid)

    async def circle_of(uid: str) -> list:
        """The players whose live matches this player may see on the lobby strip: friends and gang mates, without anyone
        blocked either way. Every open lobby asks for the strip every 8 s, and each time it read the block list, the
        friend list and the gangs again; they change rarely, so one read (the three side by side) now serves 20 s.
        Opening a match to watch is still checked against the database at that moment (can_watch)."""
        hit = circles.get(uid)
        if hit and time.time() - hit[0] < CIRCLE_SECONDS:
            return hit[1]
        blocks, friends, gangs = await asyncio.gather(
            db.rf_blocks.find({"$or": [{"uid": uid}, {"bid": uid}]}, {"_id": 0}).to_list(500),
            db.rf_friends.find({"uid": uid}, {"_id": 0, "fid": 1}).batch_size(500).to_list(500),
            db.rf_gangs.find({"members.uid": uid, "closed": {"$ne": True}}, {"_id": 0, "members.uid": 1}).to_list(10))
        hidden = {uid} | {b["bid"] for b in blocks} | {b["uid"] for b in blocks}
        seen = {f["fid"] for f in friends} | {m["uid"] for g in gangs for m in g["members"][:200]}
        if len(circles) > 10_000:
            circles.clear()
        circles[uid] = (time.time(), list(seen - hidden))
        return circles[uid][1]

    @r.get("/live")
    async def live_now(x_rf_user: Optional[str] = Header(None)):
        """Matches being played right now by your friends and gang mates, to watch."""
        uid = rf_user(x_rf_user)
        uids, now = await circle_of(uid), time.time()
        if not uids:
            return {"items": []}
        docs = await db.rf_duels.find({"status": "ready", "ends_at": {"$gt": now}, "players.uid": {"$in": uids, "$ne": uid}},
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
            seen, now, key = watching.setdefault(did, {}), time.time(), f"{did}:{uid}"
            # The limit counts spectators on every server; one already watching (here or on another server) keeps their seat.
            if now - seen.get(uid, 0) >= 6 and await count_watchers(did) >= MAX_WATCHERS and \
                    not await db.rf_watch.find_one({"_id": key, "ts": {"$gt": now - 6}}, {"_id": 1}):
                raise HTTPException(409, f"{MAX_WATCHERS} people are already watching this match. Try again in a moment.")
            if now - seen.get(uid, 0) >= 3:  # a look every 1.5 s is written at most every 3 s
                await db.rf_watch.update_one({"_id": key}, {"$set": {"did": did, "ts": now, "at": datetime.now(timezone.utc)}}, upsert=True)
                if now - seen.get(uid, 0) >= 6:  # a new spectator here: count again
                    wcount.pop(did, None)
                seen[uid] = now
                if d.get("watched_ts", 0) < now - 3:  # tells the players' servers to count spectators for this match
                    await db.rf_duels.update_one({"id": did}, {"$set": {"watched_ts": now}})
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
        own = await active_owned_duel(did, uid)
        n = len(own["card_ids"])
        bot = make_bot(cards=n)
        d = await db.rf_duels.find_one_and_update({"id": did, "status": {"$in": ["waiting", "expired"]}, "players.0.uid": uid, "players": {"$size": 1}},
                                                  {"$push": {"players": bot}, "$set": {**start_fields(cards=n), "vs_bot": True}}, return_document=ReturnDocument.AFTER)
        if not d:
            raise HTTPException(409, "This duel already has an opponent.")
        notify(did, d)
        return await view(d, uid)

    @r.post("/{did}/forfeit")
    async def forfeit(did: str, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        await active_owned_duel(did, uid)
        d = await db.rf_duels.find_one_and_update({"id": did, "status": "ready", "players.uid": uid}, {"$set": {"players.$.done": True, "players.$.forfeit": True}},
                                                  return_document=ReturnDocument.AFTER) or await db.rf_duels.find_one({"id": did, "players.uid": uid})
        if d:
            notify(did, await settle(d))
        return {"ok": True}

    def reply(index, outcome, card, score):
        return {"index": index, "outcome": outcome, "answer": card["answer"], "explain": card.get("explain", ""), "formula": card.get('formula', ''), "score": score}

    async def quick_answer(did, uid, data):
        """The common case in one database round trip: no read before the write. The server measures the answer time
        inside the update from the player's last answer, exactly like the full path. Anything unusual (a replay, a card out
        of order, a match that is over, a player who left) gets None and takes the full path, which explains it."""
        f = fixed.get(did)
        now = time.time()
        if not f or uid not in f[3] or data.index >= len(f[0]) or not (f[1] - 1 <= now <= f[2]):
            return None
        cid = f[0][data.index]
        card = (await get_cards([cid])).get(cid)
        if not card:
            return None
        outcome = data.outcome if data.outcome != "answer" else ("correct" if data.choice == card["answer"] else "incorrect")
        inc = 1 if outcome == "correct" else 0
        ms = {"$toInt": {"$multiply": [{"$max": [0, {"$min": [{"$subtract": [now, {"$ifNull": ["$$p.last_ts", "$start_at"]}]}, CARD_SECONDS + 1]}]}, 1000]}}
        entry = {"i": data.index, "choice": {"$literal": data.choice if data.outcome == "answer" else None}, "outcome": {"$literal": outcome}, "ms": "$$ms"}
        mine = {"$let": {"vars": {"ms": ms}, "in": {"$mergeObjects": ["$$p", {"answers": {"$concatArrays": ["$$p.answers", [entry]]}, "score": {"$add": ["$$p.score", inc]},
                                                                               "ms": {"$add": ["$$p.ms", "$$ms"]}, "done": data.index + 1 >= len(f[0]), "last_ts": now}]}}}
        got = await db.rf_duels.find_one_and_update(
            {"id": did, "status": "ready", "ends_at": {"$gte": now}, "players": {"$elemMatch": {"uid": uid, "answers": {"$size": data.index}, "forfeit": {"$ne": True}}}},
            [{"$set": {"players": {"$map": {"input": "$players", "as": "p", "in": {"$cond": [{"$eq": ["$$p.uid", {"$literal": uid}]}, mine, "$$p"]}}}}}],
            projection={"_id": 0}, return_document=ReturnDocument.AFTER)
        if not got:
            return None
        score = next(p["score"] for p in got["players"] if p["uid"] == uid)
        notify(did, await settle(got))
        return reply(data.index, outcome, card, score)

    @r.post("/{did}/answer")
    async def answer(did: str, data: DuelAnswer, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        quick = await quick_answer(did, uid, data)
        if quick:
            load.answers_quick += 1
            return quick
        load.answers_full += 1
        d = await active_owned_duel(did, uid)
        remember(d)
        me = next(p for p in d["players"] if p["uid"] == uid)
        card = (await get_cards([d["card_ids"][data.index]])).get(d["card_ids"][data.index]) if data.index < len(d["card_ids"]) else None
        if not card:
            raise HTTPException(400, "Unknown card.")
        if data.index < len(me["answers"]):  # idempotent replay: never re-score a locked card
            return reply(data.index, me["answers"][data.index]["outcome"], card, me["score"])
        now = time.time()
        if d["status"] == "ready" and now > d["ends_at"]:  # time is up: close the match instead of taking the answer
            d = await settle(d)
        if d["status"] != "ready" or now < d["start_at"] - 1 or me.get("forfeit"):
            raise HTTPException(409, "This duel is not accepting answers.")
        # Tie-break time is measured by the server, never trusted from the phone.
        since = me.get("last_ts") or d["start_at"]
        server_ms = int(max(0.0, min(now - since, CARD_SECONDS + 1)) * 1000)
        if data.index != len(me["answers"]):
            raise HTTPException(409, "Answer cards in order.")
        outcome = data.outcome if data.outcome != "answer" else ("correct" if data.choice == card["answer"] else "incorrect")
        entry = {"i": data.index, "choice": data.choice if data.outcome == "answer" else None, "outcome": outcome, "ms": server_ms}
        inc = 1 if outcome == "correct" else 0
        done = data.index + 1 >= len(d["card_ids"])
        got = await db.rf_duels.find_one_and_update({"id": did, "status": "ready", "players": {"$elemMatch": {"uid": uid, "answers": {"$size": data.index}}}},
                                                    {"$push": {"players.$.answers": entry}, "$inc": {"players.$.score": inc, "players.$.ms": server_ms}, "$set": {"players.$.done": done, "players.$.last_ts": now}},
                                                    projection={"_id": 0}, return_document=ReturnDocument.AFTER)
        if not got:
            raise HTTPException(409, "Answer already recorded.")
        notify(did, await settle(got))  # the answer write already returned the new state: no extra read before the push
        return reply(data.index, outcome, card, me["score"] + inc)

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
            # The first socket of a match on this server writes this server into the match, so changes made on other
            # servers come here; the same atomic step returns the doc, so no change can slip between the two.
            d = await db.rf_duels.find_one({"id": did, "players.uid": uid}) if sockets.get(did) else await db.rf_duels.find_one_and_update(
                {"id": did, "players.uid": uid}, {"$addToSet": {"ws_nodes": node}}, return_document=ReturnDocument.AFTER)
            if d:
                resolve_exam(d.get("exam"), d["subject"])
        except (HTTPException, ValueError, asyncio.TimeoutError, WebSocketDisconnect):
            d = None
        if not d:
            try:
                await ws.close(code=4404)
            except RuntimeError:  # the phone already hung up before saying hello
                pass
            return
        ensure_bus()
        # New apps say "lite": after the first frame they keep the cards they have, so each push is a few hundred bytes.
        sockets.setdefault(did, {})[ws] = {"uid": uid, "sig": None, "lite": bool(hello.get("lite")), "deck": None}
        load.sockets += 1
        mark(did, (d, time.monotonic()))  # the doc just read: first frame goes out without another read
        due.setdefault(did, time.monotonic() + 1)
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
            load.sockets -= 1
            conns = sockets.get(did, {})
            conns.pop(ws, None)
            if not conns and not stopping:
                for live in (sockets, docs, due, dirty):
                    live.pop(did, None)
                try:  # no socket of this match left here: other servers stop telling this one about it
                    await db.rf_duels.update_one({"id": did}, {"$pull": {"ws_nodes": node}})
                    if sockets.get(did):  # a new socket arrived meanwhile: stay on the list
                        await db.rf_duels.update_one({"id": did}, {"$addToSet": {"ws_nodes": node}})
                except Exception as e:  # noqa: BLE001
                    log.warning("socket list update failed: %s", e)

    stopping: list = []  # one item once this server copy is shutting down

    async def close_all():
        """This copy is stopping (a new release, a restart): every phone here is told at once (1012 = "service restart")
        and reconnects within a second or two to another copy, which picks the match up from the database; meanwhile the
        app keeps the match going by polling. This copy leaves every match's socket list in one write."""
        stopping.append(True)
        dids = list(sockets)
        await asyncio.gather(*(ws.close(code=1012) for did in dids for ws in list(sockets.get(did, {}))), return_exceptions=True)
        if dids:
            try:
                await db.rf_duels.update_many({"id": {"$in": dids}}, {"$pull": {"ws_nodes": node}})
            except Exception as e:  # noqa: BLE001
                log.warning("socket list cleanup at shutdown failed: %s", e)
        return len(dids)

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

    return r, {"seat": seat_duel, "settle": settle, "hooks": hooks, "close_all": close_all}
