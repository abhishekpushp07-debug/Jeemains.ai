"""Knockout Cups: single elimination, 15-card matches, every round starts for everyone at the same moment.

Open Cup: 4, 8 or 16 seats, anyone can join; practice rivals take the seats nobody filled. Friends Cup: 4, 8 or 16 seats
for the host's friends or one of their gangs; the host may start early and empty seats become byes. The cup moves on by
itself as soon as a round is decided. Every cup has a 6-letter watch code: up to 100 people can follow it live.
"""
import asyncio
import logging
import os
import random
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from pymongo import ReturnDocument, UpdateOne
from pymongo.errors import DuplicateKeyError

from exam_groups import resolve_exam
from load_guard import arena_gate
from gamify import crown_of
from scope import Pick, normalise, scope_fields, scope_of
from shop import rival_profile
from social import blocked_uids, card, find_player

CUP_CARDS = 15
log = logging.getLogger("cups")
LOBBY_SECONDS = {"open": 40, "private": 300}
BREAK_SECONDS = 10  # between two rounds, so winners can catch their breath
ACTIVE = ["open", "live"]
ROUND_NAMES = {1: "Final", 2: "Semi-finals", 4: "Quarter-finals", 8: "Round of 16"}
SHOWN = ("pid", "name", "avatar", "frame", "level")
MAX_SPECTATORS = 100  # people who follow a cup with its watch code
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
IST = timezone(timedelta(hours=5, minutes=30))
# Cup Night: every day at 8 pm IST, seats from 7 pm. RF_CUP_NIGHT_AT ("HH:MM", IST) moves it for QA only.
NIGHT_HOUR, NIGHT_MINUTE = (int(x) for x in os.environ.get("RF_CUP_NIGHT_AT", "20:00").split(":"))
DOORS_SECONDS = 3600  # seats can be taken an hour before
NIGHT_SEATS = 16
NIGHT_LEAD = 30  # seconds between the 8 pm draw and round 1, so everybody can get to their match
NIGHT_GUARD = 900  # in the last 15 minutes before the start, a player with a seat cannot begin another cup
NIGHT_REMIND = 300  # 7:55 pm: every seat holder gets an in-app reminder
NIGHT_PICKS = [{"subject": s, "chapter": None} for s in ("Physics", "Chemistry", "Mathematics")]
# Diamonds for the champion and the runner-up, straight into the Vault. Real-player cups pay the most, Cup Night most of all.
CUP_GEMS = {4: ({"red": 3}, {"red": 1}), 8: ({"red": 3, "blue": 2}, {"red": 2}), 16: ({"blue": 3, "emerald": 1}, {"blue": 1, "red": 2})}


def cup_gems(c: dict, humans: int, place: int) -> dict:
    if humans <= 1:  # practice rivals only: one red diamond for the champion
        return {"red": 1} if place == 1 else {}
    size = max([s for s in CUP_GEMS if s <= len(c["players"])] or [4])
    g = dict(CUP_GEMS[size][place - 1])
    if c.get("night"):
        bonus = {"gold": 1, "emerald": 1} if place == 1 else {"blue": 1}
        g = {k: g.get(k, 0) + bonus.get(k, 0) for k in {*g, *bonus}}
    return g




def night_of(ts: float):
    """Today's Cup Night (IST date) and the moment it starts."""
    d = datetime.fromtimestamp(ts, IST)
    return d.strftime("%Y-%m-%d"), d.replace(hour=NIGHT_HOUR, minute=NIGHT_MINUTE, second=0, microsecond=0).timestamp()


def ist_time(ts: float) -> str:
    """"8:00 pm" in IST, for the app to show as it is."""
    d = datetime.fromtimestamp(ts, IST)
    return f"{d.hour % 12 or 12}:{d.minute:02d} {'am' if d.hour < 12 else 'pm'}"


class CupCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["open", "private"]
    size: Literal[4, 8, 16] = 4
    picks: Optional[List[Pick]] = Field(default=None, max_length=5)
    pids: List[str] = Field(default_factory=list, max_length=15)
    gang_id: Optional[str] = Field(default=None, max_length=16)


class CupWatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(min_length=6, max_length=8)


def make_router(db, rf_user, duels):
    r = APIRouter(prefix="/rf/cups")
    after = ReturnDocument.AFTER

    def seat_of(p):
        return {"uid": p["uid"], **{k: card(p)[k] for k in SHOWN}, "ts": time.time()}

    async def seat(uid):
        return seat_of(await db.rf_profiles.find_one({"uid": uid}) or {"uid": uid})

    def rival_seat():
        rival = rival_profile()
        return {"uid": "bot-" + uuid.uuid4().hex[:10], "bot": True, "pid": None, **{k: rival[k] for k in ("name", "avatar", "frame", "entry")},
                "level": random.randint(3, 14), "wins": random.randint(4, 90), "acc": random.uniform(0.5, 0.75), "pace": random.uniform(4.0, 6.5)}

    async def fresh(cid):
        return await db.rf_cups.find_one({"id": cid})

    async def fill(c, rnd, pairs):
        """Seat every match of a round. Safe to run twice: matches are found again by their cup, round and number."""
        seats, matches = {p["uid"]: p for p in c["players"]}, []
        for m, (a, b) in enumerate(pairs):
            row = {"a": a, "b": b, "winner": None, "duel_id": None, "score": None}
            humans = [u for u in (a, b) if u and not seats[u].get("bot")]
            if not a or not b:  # a bye
                row["winner"] = a or b
            elif not humans:  # two practice rivals: decided at once
                rng = random.Random(f"{c['id']}:{rnd}:{m}")
                score = [rng.randint(6, 13), rng.randint(6, 13)]
                row.update(winner=a if score[0] >= score[1] else b, score=score)
            else:
                row["duel_id"] = await duels["seat"](c["exam"], scope_of(c), humans, f"cup:{c['id']}:{rnd}:{m}", gang_id=c.get("gang_id"), cards=CUP_CARDS,
                                                     extra={"mode": "cup", "cup_id": c["id"], "cup_round": rnd}, bots=[seats[u] for u in (a, b) if seats[u].get("bot")],
                                                     delay=BREAK_SECONDS if rnd else NIGHT_LEAD if c.get("night") else 2)
            matches.append(row)
        return await db.rf_cups.find_one_and_update({"id": c["id"]}, {"$set": {f"rounds.{rnd}": matches}}, return_document=after)

    async def build(c, rnd, pairs, was):
        got = await db.rf_cups.find_one_and_update({"id": c["id"], **was}, {"$set": {"round": rnd, "pairs": pairs, "built_ts": time.time()}}, return_document=after)
        return await fill(got, rnd, pairs) if got else await fresh(c["id"])

    async def begin(c):
        """The lobby closes: practice rivals fill an Open Cup, the draw is made and round 1 starts."""
        players = list(c["players"]) + ([rival_seat() for _ in range(c["size"] - len(c["players"]))] if c["kind"] == "open" else [])
        random.Random(c["id"]).shuffle(players)
        n = 2
        while n < len(players):
            n *= 2
        slots = [p["uid"] for p in players] + [None] * (n - len(players))
        pairs, now = [[slots[i], slots[n - 1 - i]] for i in range(n // 2)], time.time()
        got = await db.rf_cups.find_one_and_update({"id": c["id"], "status": "open", "players": {"$size": len(c["players"])}},
                                                   {"$set": {"players": players, "size": n, "started_ts": now, "status": "live", "round": 0, "pairs": pairs, "built_ts": now}}, return_document=after)
        # No update means somebody joined or left this very moment: the next look starts the cup.
        return await fill(got, 0, pairs) if got else await fresh(c["id"])

    def decide(d, row):
        """Who goes through. A tie goes to the real player over a practice rival, then to the faster one."""
        ps = {p["uid"]: p for p in d["players"]}
        a, b = ps[row["a"]], ps[row["b"]]
        win = d.get("winner") if d.get("winner") in ps else min((a, b), key=lambda p: (bool(p.get("forfeit")), bool(p.get("bot")), p["ms"]))["uid"]
        return win, [a["score"], b["score"]]

    async def finish(c, champion):
        seats = {p["uid"]: p for p in c["players"]}
        humans = [p for p in c["players"] if not p.get("bot")]
        final = c["rounds"][-1][0]
        runner = final["b"] if final["a"] == champion else final["a"]
        prizes = {}
        if not seats[champion].get("bot"):
            prizes[champion] = 30 + 40 * (len(humans) - 1)
        if runner and not seats[runner].get("bot") and len(humans) > 2:
            prizes[runner] = 15 * (len(humans) - 1)
        gems = {u: g for u, g in ((champion, cup_gems(c, len(humans), 1)), (runner, cup_gems(c, len(humans), 2))) if u and g and not seats[u].get("bot")}
        got = await db.rf_cups.find_one_and_update({"id": c["id"], "status": "live"}, {"$set": {"status": "finished", "champion": champion, "prizes": prizes, "gems": gems, "finished_ts": time.time()}}, return_document=after)
        if not got:
            return await fresh(c["id"])
        for uid, g in gems.items():  # diamonds straight into the Vault
            await db.rf_profiles.update_one({"uid": uid}, {"$inc": {f"diamonds.{colour}": n for colour, n in g.items()}})
        for uid, coins in prizes.items():  # paid once: only the request that closed the cup gets here
            won = uid == champion
            p = await db.rf_profiles.find_one_and_update({"uid": uid}, {"$inc": {"coins": coins, **({"cups_won": 1, **({"cups_real": 1} if len(humans) > 1 else {})} if won else {})},
                                                                        **({"$addToSet": {"badges": "cup_champion"}} if won and len(humans) > 1 else {})}, return_document=after)
            if won and p:  # kept on the cup: this was the champion's title number N, for the crown celebration
                got["title_no"] = p.get("cups_won", 1)
                await db.rf_cups.update_one({"id": c["id"]}, {"$set": {"title_no": got["title_no"]}})
        if champion in prizes and len(humans) > 1 and not champion.startswith("TEST"):
            await db.rf_feed.insert_one({"id": "cup:" + c["id"], "uid": champion, "kind": "cup", "data": {"players": len(c["players"]), "label": c["label"]}, "ts": time.time(), "at": datetime.now(timezone.utc)})
        return got

    async def settle(c):
        """Move the cup on when its moment has come: start it, record finished matches, seat the next round, crown the champion."""
        now = time.time()
        if c["status"] == "open":
            full, late = len(c["players"]) >= c["size"], now > c["expires_ts"]
            if full or c.get("go") or (late and (c["kind"] == "open" or len(c["players"]) >= 2)):
                return await begin(c)
            if late:
                return await db.rf_cups.find_one_and_update({"id": c["id"], "status": "open"}, {"$set": {"status": "expired"}}, return_document=after) or c
            return c
        if c["status"] != "live":
            return c
        rnd = c["round"]
        if len(c.get("rounds") or []) <= rnd:  # the round is still being seated (or the server stopped half-way: seat it again)
            return await fill(c, rnd, c["pairs"]) if now - c["built_ts"] > 8 else c
        changed = False
        for m, row in enumerate(c["rounds"][rnd]):
            if row["winner"] or not row["duel_id"]:
                continue
            d = await db.rf_duels.find_one({"id": row["duel_id"]})
            d = await duels["settle"](d) if d else None
            if d and d["status"] == "finished":
                win, score = decide(d, row)
                await db.rf_cups.update_one({"id": c["id"], f"rounds.{rnd}.{m}.winner": None}, {"$set": {f"rounds.{rnd}.{m}.winner": win, f"rounds.{rnd}.{m}.score": score}})
                changed = True
        if changed:
            c = await fresh(c["id"])
        winners = [row["winner"] for row in c["rounds"][rnd]]
        if c["status"] != "live" or c["round"] != rnd or not all(winners):
            return c
        if len(winners) == 1:
            return await finish(c, winners[0])
        return await build(c, rnd + 1, [winners[i:i + 2] for i in range(0, len(winners), 2)], {"status": "live", "round": rnd})

    async def on_match_end(d):
        if d.get("cup_id"):
            c = await fresh(d["cup_id"])
            if c:
                await settle(c)

    duels["hooks"].append(on_match_end)

    async def view(c, uid):
        c = await settle(c)
        now, rounds, rnd = time.time(), c.get("rounds") or [], c.get("round", -1)
        idx = {p["uid"]: i for i, p in enumerate(c["players"])}
        current = rounds[rnd] if c["status"] == "live" and 0 <= rnd < len(rounds) else []
        ids = [m["duel_id"] for m in current if m["duel_id"] and not m["winner"]]
        live = {d["id"]: d for d in await db.rf_duels.find({"id": {"$in": ids}}, {"_id": 0, "id": 1, "start_at": 1, "players.uid": 1, "players.score": 1}).to_list(8)} if ids else {}
        out = {u for rd in rounds for m in rd if m["winner"] for u in (m["a"], m["b"]) if u and u != m["winner"]}

        def match(m):
            d = live.get(m["duel_id"])
            score = {p["uid"]: p["score"] for p in d["players"]} if d else {}
            return {"a": idx.get(m["a"]), "b": idx.get(m["b"]), "winner": idx.get(m["winner"]), "score": m["score"] or ([score.get(m["a"], 0), score.get(m["b"], 0)] if d else None),
                    "duel_id": m["duel_id"], "live": bool(d) and d["start_at"] <= now, "starts_in": max(0, round(d["start_at"] - now)) if d else 0, "mine": uid in (m["a"], m["b"])}

        mine = next((m for m in current if uid in (m["a"], m["b"]) and m["duel_id"] and not m["winner"]), None)
        host = c["host_uid"] == uid
        title_no, my_crown = 0, None
        if c["status"] == "finished" and c.get("champion") == uid:  # every cup you win: the crown celebration, with your title count
            title_no = c.get("title_no") or await db.rf_cups.count_documents({"champion": uid, "status": "finished", "finished_ts": {"$lte": c.get("finished_ts", now)}})
            my_crown = crown_of(await db.rf_profiles.find_one({"uid": uid}, {"_id": 0, "cups_won": 1, "cups_real": 1}) or {})
        invited = []
        if host and c["kind"] == "private" and c["status"] == "open" and c.get("invites"):  # the host sees who was invited and who is in
            profs = await db.rf_profiles.find({"uid": {"$in": c["invites"][:40]}}).to_list(40)
            invited = [{**{k: card(p)[k] for k in SHOWN}, "joined": p["uid"] in idx} for p in profs]
            invited.sort(key=lambda p: not p["joined"])
        return {"id": c["id"], "kind": c["kind"], "status": c["status"], "label": c["label"], "picks": c["picks"], "size": c["size"], "cards": CUP_CARDS, "code": c.get("code"),
                "spectators": len(c.get("spectators") or []), "max_spectators": MAX_SPECTATORS, "spectating": uid not in idx and uid in (c.get("spectators") or []),
                "round": rnd, "is_host": host, "joined": uid in idx, "invited": uid in c.get("invites", []), "expires_in": max(0, round(c["expires_ts"] - now)),
                "can_start": host and c["status"] == "open" and c["kind"] == "private" and len(c["players"]) >= 2,
                "players": [{**{k: p.get(k) for k in SHOWN}, "bot": bool(p.get("bot")), "you": p["uid"] == uid, "out": p["uid"] in out} for p in c["players"]],
                "rounds": [{"name": ROUND_NAMES.get(len(rd), f"Round {k + 1}"), "matches": [match(m) for m in rd]} for k, rd in enumerate(rounds)],
                "my_duel": mine["duel_id"] if mine else None, "champion": idx.get(c.get("champion")), "prize": (c.get("prizes") or {}).get(uid, 0), "gems_won": (c.get("gems") or {}).get(uid, {}), "invited_players": invited,
                "first_title": title_no == 1, "title_no": title_no, "my_crown": my_crown, "real_players": sum(not p.get("bot") for p in c["players"]), "night": c.get("night"), "night_no": c.get("night_no")}

    async def open_for(cid, uid):
        """A cup this player may look at: they play in it, were invited, follow it with its code, or are friends with someone playing."""
        c = await fresh(cid)
        uids = [p["uid"] for p in (c or {}).get("players", []) if not p.get("bot")]
        if not c or not (uid in uids or uid in c.get("invites", []) or uid in (c.get("spectators") or [])
                         or await db.rf_friends.find_one({"uid": uid, "fid": {"$in": uids}}, {"_id": 1})):
            raise HTTPException(404, "Cup not found.")
        return c

    async def insert(c):
        """Store a new cup with a watch code nobody else has."""
        for _ in range(5):
            c["code"] = "".join(secrets.choice(CODE_ALPHABET) for _ in range(6))
            try:
                await db.rf_cups.insert_one(c)
                return c
            except DuplicateKeyError:
                c.pop("_id", None)
        raise HTTPException(503, "Could not open the cup. Please try again.")

    @r.get("")
    async def mine(x_rf_user: Optional[str] = Header(None)):
        """Your last 10 cups, newest first."""
        uid = rf_user(x_rf_user)
        docs = await db.rf_cups.find({"players.uid": uid, "status": {"$in": ["open", "live", "finished"]}}, {"_id": 0, "id": 1, "label": 1, "size": 1, "status": 1, "kind": 1, "champion": 1, "night": 1,
                                                                                                                "players.uid": 1, "players.name": 1, "prizes": 1, "gems": 1, "created_ts": 1}).sort("created_ts", -1).limit(10).to_list(10)
        name = lambda c, u: next((p["name"] for p in c["players"] if p["uid"] == u), None)  # noqa: E731
        return {"items": [{"id": c["id"], "label": c["label"], "size": c["size"], "status": c["status"], "kind": c["kind"], "players": len(c["players"]), "won": c.get("champion") == uid,
                           "champion": name(c, c.get("champion")), "prize": (c.get("prizes") or {}).get(uid, 0), "gems_won": (c.get("gems") or {}).get(uid, {}), "night": bool(c.get("night"))} for c in docs]}

    # ---------- Cup Night: every day at 8 pm IST ----------
    # Every seat is its own small document in rf_night_seats ({day}:{uid}), so a night with 100,000 students never becomes
    # one huge document that every phone reads. The 8 pm draw runs in the background on one server process; it writes the
    # groups to the seats first, so another process can finish the draw if this one stops half-way.
    nights, counts, lists = {}, {}, {}  # day -> (read_at, value): tiny per-process caches shared by everybody polling

    def seat_key(day, uid):
        return f"{day}:{uid}"

    async def night_doc(day, start, fresh_=False):
        hit = nights.get(day)
        if hit and not fresh_ and time.monotonic() - hit[0] < 1:
            return hit[1]
        n = await db.rf_cup_nights.find_one({"_id": day}, {"uids": 0, "missed": 0, "cups": 0}) or {"_id": day, "status": "open", "start_ts": start, "new": True}
        nights[day] = (time.monotonic(), n)
        return n

    async def seat_count(day):
        hit = counts.get(day)
        if hit and time.monotonic() - hit[0] < 3:
            return hit[1]
        n = await db.rf_night_seats.count_documents({"day": day})
        counts[day] = (time.monotonic(), n)
        return n

    async def night_list(day):
        """The first 20 cups of the night (the same for everybody); a player's own cup is added to it separately."""
        hit = lists.get(day)
        if hit and time.monotonic() - hit[0] < 2:
            return hit[1]
        rows = await db.rf_cups.find({"night": day}, {"_id": 0, "id": 1, "night_no": 1, "size": 1, "status": 1, "code": 1, "round": 1, "rounds": 1, "champion": 1,
                                                      "players.uid": 1, "players.name": 1, "players.avatar": 1, "players.frame": 1, "players.bot": 1}).sort("night_no", 1).limit(20).to_list(20)
        lists[day] = (time.monotonic(), rows)
        return rows

    async def draw(day):
        """8 pm: everybody with a seat is drawn into cups of up to 16 (evenly split); practice rivals fill the empty seats."""
        n = await db.rf_cup_nights.find_one({"_id": day}, {"uids": 0})
        if not n.get("groups_ready"):
            uids = [s["uid"] for s in await db.rf_night_seats.find({"day": day}, {"_id": 0, "uid": 1}).sort("uid", 1).to_list(None)]
            busy = set()
            for i in range(0, len(uids), 1000):  # already in another cup: that one comes first
                chunk = set(uids[i:i + 1000])
                async for c in db.rf_cups.find({"players.uid": {"$in": list(chunk)}, "status": {"$in": ACTIVE}, "night": {"$ne": day}}, {"_id": 0, "players.uid": 1}):
                    busy |= {p["uid"] for p in c["players"]} & chunk
            drawn = [u for u in uids if u not in busy]
            random.Random(day).shuffle(drawn)
            k, at, ops = -(-len(drawn) // NIGHT_SEATS), 0, []
            for i in range(k):
                size = len(drawn) // k + (1 if i < len(drawn) % k else 0)
                ops += [UpdateOne({"_id": seat_key(day, u)}, {"$set": {"group": i + 1, "pos": pos}}) for pos, u in enumerate(drawn[at:at + size])]
                at += size
            ops += [UpdateOne({"_id": seat_key(day, u)}, {"$set": {"missed": True}}) for u in uids if u in busy]  # told on the Cup Night screen
            for i in range(0, len(ops), 1000):
                await db.rf_night_seats.bulk_write(ops[i:i + 1000], ordered=False)
            n = await db.rf_cup_nights.find_one_and_update({"_id": day}, {"$set": {"groups_ready": True, "groups": k, "seated": len(drawn)}}, projection={"uids": 0}, return_document=after)
        picks = normalise(NIGHT_PICKS)
        exam, scope = resolve_exam("JEE", picks[0]["subject"]), scope_fields(picks)

        async def open_cup(no):
            cid = f"night-{day}-{no}"
            if not await db.rf_cups.find_one({"id": cid}, {"_id": 1}):
                uids = [s["uid"] for s in await db.rf_night_seats.find({"day": day, "group": no}, {"_id": 0, "uid": 1, "pos": 1}).sort("pos", 1).to_list(NIGHT_SEATS)]
                if not uids:
                    return
                profs = {p["uid"]: p for p in await db.rf_profiles.find({"uid": {"$in": uids}}).to_list(len(uids))}
                now = time.time()
                await insert({"id": cid, "kind": "open", "night": day, "night_no": no, "size": 4 if len(uids) <= 4 else 8 if len(uids) <= 8 else 16,
                              "host_uid": uids[0], "exam": exam, **scope, "status": "open", "created_ts": now, "expires_ts": now, "gang_id": None, "invites": [],
                              "players": [seat_of(profs.get(u) or {"uid": u}) for u in uids], "spectators": [], "rounds": [], "round": -1})
            await settle(await fresh(cid))  # the lobby is already over: the draw is made and round 1 starts
            await db.rf_night_seats.update_many({"day": day, "group": no}, {"$set": {"cup": cid}})

        todo = list(range(1, n.get("groups", 0) + 1))
        for i in range(0, len(todo), 25):  # 25 cups at a time; each finished batch tells the other servers this draw is alive
            for res in await asyncio.gather(*(open_cup(no) for no in todo[i:i + 25]), return_exceptions=True):
                if isinstance(res, Exception):
                    log.warning("cup night seating failed: %s", res)
            await db.rf_cup_nights.update_one({"_id": day}, {"$set": {"seating_ts": time.time()}})
        lists.pop(day, None)
        await db.rf_cup_nights.update_one({"_id": day}, {"$set": {"status": "seated", "cups_n": len(todo)}})
        nights.pop(day, None)

    drawing = {}  # day -> the draw task this process is running

    async def night_now():
        now = time.time()
        day, start = night_of(now)
        n = await night_doc(day, start)
        start = n.get("start_ts", start)  # a night keeps the start it was opened with
        if now >= start and n.get("status") == "open" and not n.get("new"):
            # The background tick draws within 3 s anyway; a look at the right moment starts it at once and waits briefly,
            # so a small night is drawn before this answer. A huge one keeps drawing in the background ("seating").
            task = drawing.get(day)
            if not task or task.done():
                task = drawing[day] = asyncio.create_task(night_tick())
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=3)
            except Exception:  # noqa: BLE001  (still drawing, or failed: the tick loop finishes it)
                pass
            n = await night_doc(day, start, fresh_=True)
        return n, now, day, n.get("start_ts", start)

    async def night_tick():
        """Called every few seconds by every server: the 7:55 pm reminder, then the 8 pm draw (one server does it), even if nobody has the app open."""
        now = time.time()
        day, start = night_of(now)
        n = await night_doc(day, start, fresh_=True)
        if n.get("new"):
            return
        start = n.get("start_ts", start)
        if n.get("status") == "open" and not n.get("reminded") and 0 < start - now <= NIGHT_REMIND:
            if await db.rf_cup_nights.find_one_and_update({"_id": day, "status": "open", "reminded": {"$ne": True}}, {"$set": {"reminded": True}}):
                batch = []  # once per night, to everybody holding a seat at that moment
                async for s in db.rf_night_seats.find({"day": day}, {"_id": 0, "uid": 1}):
                    batch.append({"id": str(uuid.uuid4()), "uid": s["uid"], "from_uid": s["uid"], "kind": "cup_night", "ts": now, "done": False, "expires_ts": start + 120,
                                  "night": {"day": day, "start_ts": start, "time_label": ist_time(start)}})
                    if len(batch) == 1000:
                        await db.rf_notices.insert_many(batch)
                        batch = []
                if batch:
                    await db.rf_notices.insert_many(batch)
        if now >= start and n.get("status") == "open":
            if await db.rf_cup_nights.find_one_and_update({"_id": day, "status": "open"}, {"$set": {"status": "seating", "seating_ts": now}}, projection={"_id": 1}):
                await draw(day)
        elif n.get("status") == "seating" and now - n.get("seating_ts", now) > 60:  # the server drawing tonight stopped: finish its draw
            if await db.rf_cup_nights.find_one_and_update({"_id": day, "status": "seating", "seating_ts": n.get("seating_ts")}, {"$set": {"seating_ts": now}}, projection={"_id": 1}):
                await draw(day)

    r.night_tick = night_tick

    async def migrate_nights():
        """Once: nights stored the old way (every seat in one `uids` list) move to one seat document each."""
        async for n in db.rf_cup_nights.find({"uids": {"$exists": True}}):
            day, missed = n["_id"], set(n.get("missed") or [])
            cup_of = {p["uid"]: c["id"] for c in await db.rf_cups.find({"night": day}, {"_id": 0, "id": 1, "players.uid": 1}).to_list(None) for p in c["players"]}
            ops = [UpdateOne({"_id": seat_key(day, u)}, {"$setOnInsert": {"day": day, "uid": u, "ts": k, **({"missed": True} if u in missed else {}), **({"cup": cup_of[u]} if u in cup_of else {})}}, upsert=True)
                   for k, u in enumerate(n["uids"])]
            if ops:
                await db.rf_night_seats.bulk_write(ops, ordered=False)
            done = {"groups_ready": True, "cups_n": len(n.get("cups") or [])} if n.get("status") in ("seated", "seating") else {}
            await db.rf_cup_nights.update_one({"_id": day}, {"$unset": {"uids": "", "missed": ""}, **({"$set": done} if done else {})})

    r.migrate_nights = migrate_nights

    @r.get("/night")
    async def night(x_rf_user: Optional[str] = Header(None)):
        """Tonight's Cup Night: the countdown, who has joined (your friends first), and after 8 pm the cups with their champions."""
        uid = rf_user(x_rf_user)
        n, now, day, start = await night_now()
        mine_seat = await db.rf_night_seats.find_one({"_id": seat_key(day, uid)}, {"_id": 0, "cup": 1, "missed": 1})
        fids = [e["fid"] for e in await db.rf_friends.find({"uid": uid}, {"_id": 0, "fid": 1}).to_list(500)]
        seated = {s["uid"] for s in await db.rf_night_seats.find({"_id": {"$in": [seat_key(day, f) for f in fids]}}, {"_id": 0, "uid": 1}).to_list(500)} if fids else set()
        seated -= await blocked_uids(db, uid) if seated else set()
        friends = [{k: card(p)[k] for k in SHOWN} for p in await db.rf_profiles.find({"uid": {"$in": list(seated)[:12]}}).to_list(12)]
        cups, my_cup = [], (mine_seat or {}).get("cup")
        if n.get("status") in ("seating", "seated"):
            rows = list(await night_list(day))
            if my_cup and all(c["id"] != my_cup for c in rows):
                own = await db.rf_cups.find_one({"id": my_cup}, {"_id": 0})
                rows = [own] + rows if own else rows
            for c in rows:
                champ = next((p for p in c["players"] if p["uid"] == c.get("champion")), None)
                left = len(c["rounds"][c["round"]]) if c["status"] == "live" and c.get("rounds") and 0 <= c["round"] < len(c["rounds"]) else 0
                cups.append({"id": c["id"], "no": c.get("night_no"), "size": c["size"], "status": c["status"], "code": c.get("code"), "mine": c["id"] == my_cup,
                             "real_players": sum(not p.get("bot") for p in c["players"]), "round": ROUND_NAMES.get(left) if left else None,
                             "champion": {k: champ.get(k) for k in ("name", "avatar", "frame")} | {"bot": bool(champ.get("bot")), "you": champ["uid"] == uid} if champ else None})
        phase = "soon" if now < start - DOORS_SECONDS else "doors" if now < start else "live"
        count = n["seated"] if n["status"] == "seated" and "seated" in n else await seat_count(day)
        return {"day": day, "now": now, "start_ts": start, "doors_ts": start - DOORS_SECONDS, "next_ts": start + 86400, "phase": phase, "status": n["status"],
                "time_label": ist_time(start), "doors_label": ist_time(start - DOORS_SECONDS), "joined": bool(mine_seat), "missed": bool((mine_seat or {}).get("missed")),
                "count": count, "friends": friends, "my_cup": my_cup, "cups": cups, "cups_total": max(n.get("cups_n") or n.get("groups") or 0, len(cups)),
                "label": "PCM Mixed", "cards": CUP_CARDS, "seats": NIGHT_SEATS}

    async def night_start(day, start):
        """The start of today's night: the one it was opened with, else the daily time."""
        return (await night_doc(day, start)).get("start_ts", start)

    async def night_guard(uid):
        """In the last 15 minutes before Cup Night, a player with a seat stays free for it."""
        now = time.time()
        day, start = night_of(now)
        n = await night_doc(day, start)
        start = n.get("start_ts", start)
        if n.get("status") == "open" and 0 < start - now <= NIGHT_GUARD and await db.rf_night_seats.find_one({"_id": seat_key(day, uid)}, {"_id": 1}):
            raise HTTPException(409, f"Cup Night starts at {ist_time(start)} and your seat is waiting. Leave Cup Night first to play another cup now.")

    @r.post("/night/join", dependencies=[Depends(arena_gate)])
    async def night_join(x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        now = time.time()
        day, start = night_of(now)
        start = await night_start(day, start)
        if now >= start:
            raise HTTPException(409, f"Tonight's Cup Night has started. The next one is tomorrow at {ist_time(start)}.")
        if now < start - DOORS_SECONDS:
            raise HTTPException(409, f"Doors open at {ist_time(start - DOORS_SECONDS)}. Come back then to take your seat.")
        if await db.rf_cups.find_one({"players.uid": uid, "status": {"$in": ACTIVE}}, {"_id": 1}):
            raise HTTPException(409, "Finish the cup you are in first.")
        await db.rf_cup_nights.update_one({"_id": day}, {"$setOnInsert": {"status": "open", "start_ts": start}}, upsert=True)
        await db.rf_night_seats.update_one({"_id": seat_key(day, uid)}, {"$setOnInsert": {"day": day, "uid": uid, "ts": now}}, upsert=True)
        nights.pop(day, None)
        counts.pop(day, None)
        return await night(x_rf_user)

    @r.post("/night/leave")
    async def night_leave(x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        day, start = night_of(time.time())
        if time.time() >= await night_start(day, start):
            raise HTTPException(409, "Cup Night has started. Leaving a match now counts as a loss.")
        if await db.rf_cup_nights.find_one({"_id": day, "status": "open"}, {"_id": 1}):
            await db.rf_night_seats.delete_one({"_id": seat_key(day, uid)})
            counts.pop(day, None)
        await db.rf_notices.update_many({"uid": uid, "kind": "cup_night", "done": False}, {"$set": {"done": True}})  # no seat, no reminder
        return await night(x_rf_user)

    @r.get("/champions")
    async def champions(x_rf_user: Optional[str] = Header(None)):
        """Champions Wall: the last Cup Night's champions (real players only), shown until the next night's doors open."""
        uid = rf_user(x_rf_user)
        now = time.time()
        day, start = night_of(now)
        start = await night_start(day, start)
        if now >= start:  # tonight's cups, as their champions are crowned
            show, until = day, night_of(now + 86400)[1] - DOORS_SECONDS
        elif now < start - DOORS_SECONDS:  # last night's, until tonight's doors open
            show, until = night_of(now - 86400)[0], start - DOORS_SECONDS
        else:
            return {"day": None, "tonight": False, "items": [], "until_ts": start, "time_label": ist_time(start)}
        docs = await db.rf_cups.find({"night": show, "status": "finished"}, {"_id": 0, "id": 1, "night_no": 1, "size": 1, "champion": 1, "title_no": 1,
                                                                          "players.uid": 1, "players.bot": 1}).to_list(100)
        won = [(c, next((p for p in c["players"] if p["uid"] == c.get("champion") and not p.get("bot")), None)) for c in docs]
        won = [(c, p["uid"]) for c, p in won if p]
        hidden = await blocked_uids(db, uid)
        profiles = {p["uid"]: p for p in await db.rf_profiles.find({"uid": {"$in": [u for _, u in won]}}).to_list(100)}
        items = [{"cup_id": c["id"], "no": c.get("night_no"), "size": c["size"], "real_players": sum(not p.get("bot") for p in c["players"]), "title_no": c.get("title_no") or 0,
                  "you": u == uid, **{k: v for k, v in card(profiles[u]).items() if k in (*SHOWN, "crown")}}
                 for c, u in sorted(won, key=lambda w: w[0].get("night_no", 0)) if u in profiles and u not in hidden]
        return {"day": show, "tonight": show == day, "items": items[:12], "until_ts": until, "time_label": ist_time(start)}

    @r.post("/watch")
    async def watch(data: CupWatch, x_rf_user: Optional[str] = Header(None)):
        """Follow a cup with its watch code: its bracket and every live match. Up to 100 people per cup."""
        uid = rf_user(x_rf_user)
        code = "".join(ch for ch in data.code.upper() if ch.isalnum())
        c = await db.rf_cups.find_one({"code": code, "status": {"$in": ["open", "live", "finished"]}})
        if not c:
            raise HTTPException(404, "No cup has this code. Check it and try again.")
        if uid in [p["uid"] for p in c["players"]] or uid in c.get("invites", []) or uid in (c.get("spectators") or []):
            return await view(c, uid)
        got = await db.rf_cups.find_one_and_update({"id": c["id"], "spectators": {"$ne": uid}, f"spectators.{MAX_SPECTATORS - 1}": {"$exists": False}},
                                                   {"$push": {"spectators": uid}}, return_document=after)
        if not got:
            got = await fresh(c["id"])
            if uid not in (got.get("spectators") or []):
                raise HTTPException(409, f"{MAX_SPECTATORS} people are already watching this cup.")
        return await view(got, uid)

    @r.post("", dependencies=[Depends(arena_gate)])
    async def create(data: CupCreate, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        now = time.time()
        mine = await db.rf_cups.find_one({"players.uid": uid, "status": {"$in": ACTIVE}})
        mine = await settle(mine) if mine else None
        if mine and mine["status"] in ACTIVE:  # one cup at a time: back to the one you are in
            return await view(mine, uid)
        await night_guard(uid)
        picks = normalise(data.picks)
        exam, scope, me = resolve_exam("JEE", picks[0]["subject"]), scope_fields(picks), await seat(uid)
        invites, gang_id, size = [], None, data.size
        if data.kind == "open":
            c = await db.rf_cups.find_one_and_update({"kind": "open", "status": "open", "size": size, "scope_key": scope["scope_key"], "expires_ts": {"$gt": now + 3}, "players.uid": {"$ne": uid}, f"players.{size - 1}": {"$exists": False}},
                                                     {"$push": {"players": me}}, sort=[("created_ts", 1)], return_document=after)
            if c:
                return await view(c, uid)
        else:
            hidden = await blocked_uids(db, uid)
            targets = [(await find_player(db, pid))["uid"] for pid in data.pids]
            friends = {f["fid"] for f in await db.rf_friends.find({"uid": uid, "fid": {"$in": targets}}, {"_id": 0, "fid": 1}).to_list(len(targets) or 1)}
            if uid in targets or hidden & set(targets) or set(targets) - friends:
                raise HTTPException(403, "Add this player with their Friend Code first.")
            if data.gang_id:
                gang = await db.rf_gangs.find_one({"id": data.gang_id, "members.uid": uid, "closed": {"$ne": True}})
                if not gang:
                    raise HTTPException(404, "Gang not found.")
                gang_id = gang["id"]
                targets += [m["uid"] for m in sorted(gang["members"], key=lambda m: -m["ts"]) if m["uid"] != uid and m["uid"] not in hidden][:40]
            invites = list(dict.fromkeys(targets))
            if not invites:
                raise HTTPException(400, "Pick friends or a gang for your cup.")
        c = {"id": str(uuid.uuid4()), "kind": data.kind, "size": size, "host_uid": uid, "exam": exam, **scope, "status": "open", "created_ts": now, "expires_ts": now + LOBBY_SECONDS[data.kind],
             "gang_id": gang_id, "invites": invites, "players": [me], "spectators": [], "rounds": [], "round": -1}
        return await view(await insert(c), uid)

    @r.get("/{cid}")
    async def get(cid: str, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        return await view(await open_for(cid, uid), uid)

    @r.post("/{cid}/join", dependencies=[Depends(arena_gate)])
    async def join(cid: str, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        c = await fresh(cid)
        if not c or (c["kind"] == "private" and uid not in c["invites"] and uid != c["host_uid"]):
            raise HTTPException(404, "This cup is for invited friends.")
        if await db.rf_cups.find_one({"players.uid": uid, "status": {"$in": ACTIVE}, "id": {"$ne": cid}}, {"_id": 1}):
            raise HTTPException(409, "Finish the cup you are in first.")
        await night_guard(uid)
        got = await db.rf_cups.find_one_and_update({"id": cid, "status": "open", "expires_ts": {"$gt": time.time()}, "players.uid": {"$ne": uid}, f"players.{c['size'] - 1}": {"$exists": False}},
                                                   {"$push": {"players": await seat(uid)}}, return_document=after)
        if not got:
            got = await fresh(cid)
            if not any(p["uid"] == uid for p in got["players"]):
                raise HTTPException(409, "This cup is full or has already started.")
        return await view(got, uid)

    @r.post("/{cid}/leave")
    async def leave(cid: str, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        c = await db.rf_cups.find_one({"id": cid, "players.uid": uid})
        if not c:
            raise HTTPException(404, "Cup not found.")
        if c["status"] != "open":
            raise HTTPException(409, "The cup has started. Leaving a match now counts as a loss.")
        rest = [p for p in c["players"] if p["uid"] != uid]
        if c["host_uid"] == uid and (c["kind"] == "private" or not rest):
            await db.rf_cups.update_one({"id": cid, "status": "open"}, {"$set": {"status": "cancelled"}})
        else:
            await db.rf_cups.update_one({"id": cid, "status": "open"}, {"$pull": {"players": {"uid": uid}}, **({"$set": {"host_uid": rest[0]["uid"]}} if c["host_uid"] == uid else {})})
        return {"ok": True}

    @r.post("/{cid}/start")
    async def start(cid: str, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        c = await db.rf_cups.find_one({"id": cid, "host_uid": uid})
        if not c:
            raise HTTPException(403, "Only the player who opened the cup can start it.")
        if c["status"] == "open" and len(c["players"]) < 2:
            raise HTTPException(409, "Wait for at least one friend to join.")
        await db.rf_cups.update_one({"id": cid, "status": "open"}, {"$set": {"go": True}})
        return await view(await fresh(cid), uid)

    return r
