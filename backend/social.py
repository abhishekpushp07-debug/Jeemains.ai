"""Rapid Fire social layer: verified player identity, profiles, friends (made only with a Friend Code), blocks and one-tap challenges.

Everything lives in the Rapid Fire companion collections (never on the canonical website). Phone numbers are
never stored in clear text: only an HMAC (for exact-number search) and the last 4 digits (for masked names).
"""
import hashlib
import hmac
import re
import secrets
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from gamify import BADGES, crown_of, level_of, vault_total
from scope import label_for, scope_of
from shop import equipped_of, safe_avatar

ONLINE_SECONDS = 60
TITLES = {"Physics": "Physics Ace", "Chemistry": "Chemistry Ace", "Mathematics": "Maths Ace"}
PID_RE = re.compile(r"^P[0-9A-F]{8}$")
_key: dict = {}


async def _phone_key(db) -> str:
    if "k" not in _key:
        doc = await db.rf_settings.find_one_and_update({"_id": "phone-hmac"}, {"$setOnInsert": {"key": secrets.token_hex(32)}},
                                                       upsert=True, return_document=ReturnDocument.AFTER)
        _key["k"] = doc["key"]
    return _key["k"]


def _digits(phone) -> str:
    d = re.sub(r"\D", "", str(phone or ""))
    return d[-10:] if len(d) >= 10 else ""


async def phone_hash(db, phone) -> Optional[str]:
    d = _digits(phone)
    return hmac.new((await _phone_key(db)).encode(), d.encode(), hashlib.sha256).hexdigest() if d else None


def make_pid(uid: str) -> str:
    return "P" + hashlib.sha256(("rf-player:" + uid).encode()).hexdigest()[:8].upper()


# Friend Code: the only way to become friends. It is private to its owner (unlike the public player id) and has no look-alike letters.
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_RE = re.compile(r"^[A-HJ-NP-Z2-9]{8}$")
MAX_FRIENDS = 500


async def friend_code_of(db, uid: str) -> str:
    p = await db.rf_profiles.find_one({"uid": uid}, {"friend_code": 1}) or {}
    for _ in range(6):
        if p.get("friend_code"):
            return p["friend_code"]
        try:
            code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(8))
            p = await db.rf_profiles.find_one_and_update({"uid": uid, "friend_code": {"$exists": False}}, {"$set": {"friend_code": code, "pid": make_pid(uid)}},
                                                         upsert=True, return_document=ReturnDocument.AFTER)
        except DuplicateKeyError:  # another request made it first, or the code is taken: read again
            p = await db.rf_profiles.find_one({"uid": uid}, {"friend_code": 1}) or {}
    raise HTTPException(503, "Could not make your Friend Code. Please try again.")


def public_name(p: dict) -> str:
    """Account name; otherwise the phone with all but the last 4 digits hidden."""
    if p.get("display_name"):
        return p["display_name"]
    if p.get("phone_last4"):
        return "••••••" + p["phone_last4"]
    return p.get("name") or "Player"


async def remember_identity(db, uid: str, user: dict):
    """Called only after the canonical session was verified: the name and number are never client-asserted."""
    name = re.sub(r"\s+", " ", str(user.get("name") or "")).strip()[:24]
    d = _digits(user.get("phone") or user.get("mobile") or user.get("phone_number"))
    fields = {"pid": make_pid(uid), "display_name": name, "seen_ts": time.time()}
    if d:
        fields.update(phone_hash=await phone_hash(db, d), phone_last4=d[-4:])
    fields["name"] = public_name(fields)
    await db.rf_profiles.update_one({"uid": uid}, {"$set": fields}, upsert=True)


def _online(p: dict) -> bool:
    return time.time() - (p.get("seen_ts") or 0) < ONLINE_SECONDS


def card(p: dict) -> dict:
    eq = equipped_of(p)
    return {"pid": p.get("pid") or make_pid(p["uid"]), "name": public_name(p), "avatar": safe_avatar(p.get("avatar")), "frame": eq.get("frame"),
            "entry": eq.get("entry"), "level": level_of(p.get("xp", 0)), "online": _online(p), "seen_ts": p.get("seen_ts"), "crown": crown_of(p)}


def team_scores(d: dict) -> dict:
    """Gang vs Gang: each side's best N scores count, N = the size of the smaller side, so 3 v 5 stays fair."""
    sides = {t: sorted((p for p in d["players"] if p.get("team") == t), key=lambda p: (bool(p.get("forfeit")), -p["score"], p["ms"])) for t in ("a", "b")}
    n = min(len(sides["a"]), len(sides["b"]))
    return {t: {"score": sum(p["score"] for p in ps[:n]), "ms": sum(p["ms"] for p in ps[:n]), "counted": n, "players": len(ps)} for t, ps in sides.items()}


def team_line(d: dict, uid: str) -> Optional[dict]:
    """One player's view of a gang battle: my gang against theirs, with both team scores."""
    if not d.get("team_mode"):
        return None
    mine = next((p.get("team") for p in d["players"] if p["uid"] == uid), "a")
    theirs = "b" if mine == "a" else "a"
    ts = d.get("team_scores") or team_scores(d)
    return {"mine": d["teams"][mine]["name"], "theirs": d["teams"][theirs]["name"], "emblem": d["teams"][theirs]["emblem"], "my_score": ts[mine]["score"], "their_score": ts[theirs]["score"]}


class Target(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pid: str = Field(min_length=9, max_length=9)


class FriendCode(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(min_length=8, max_length=12)


async def find_player(db, pid: str) -> dict:
    p = await db.rf_profiles.find_one({"pid": str(pid).upper()}) if PID_RE.match(str(pid).upper()) else None
    if not p:
        raise HTTPException(404, "Player not found.")
    return p


async def blocked_uids(db, uid: str) -> set:
    """Everyone this player blocked, or who blocked this player."""
    rows = await db.rf_blocks.find({"$or": [{"uid": uid}, {"bid": uid}]}, {"_id": 0}).to_list(1000)
    return ({b["bid"] for b in rows} | {b["uid"] for b in rows}) - {uid}


def make_router(db, rf_user):
    r = APIRouter(prefix="/rf")
    stats_cache: dict = {}
    misses: dict = {}  # uid -> times of wrong Friend Codes (stops code guessing)

    async def by_code(uid, raw):
        """The player who owns this Friend Code. Wrong codes are counted: 20 in 10 minutes locks the search for a while."""
        now = time.time()
        recent = misses[uid] = [t for t in misses.get(uid, []) if now - t < 600]
        if len(recent) >= 20:
            raise HTTPException(429, "Too many wrong codes. Try again in a few minutes.")
        code = re.sub(r"[^A-Za-z0-9]", "", str(raw or "")).upper()
        p = await db.rf_profiles.find_one({"friend_code": code}) if CODE_RE.match(code) else None
        if not p or (p["uid"] != uid and await blocked_between(uid, p["uid"])):
            recent.append(now)
            raise HTTPException(404, "No player has this Friend Code. Check it and try again.")
        return p

    async def me_profile(uid):
        p = await db.rf_profiles.find_one({"uid": uid}) or {"uid": uid}
        if not p.get("pid"):
            await db.rf_profiles.update_one({"uid": uid}, {"$set": {"pid": make_pid(uid)}}, upsert=True)
            p["pid"] = make_pid(uid)
        return p

    async def by_pid(pid):
        return await find_player(db, pid)

    async def blocked_between(a, b) -> bool:
        return bool(await db.rf_blocks.find_one({"$or": [{"uid": a, "bid": b}, {"uid": b, "bid": a}]}, {"_id": 1}))

    async def stats_of(uid):
        hit = stats_cache.get(uid)
        if hit and time.time() - hit[0] < 30:
            return hit[1]
        q = {"players.uid": uid, "status": "finished"}
        mine_won = {"$or": [{"winner": uid}, {"winners": uid}]}
        matches = await db.rf_duels.count_documents(q)
        wins = await db.rf_duels.count_documents({**q, **mine_won})
        docs = await db.rf_duels.find(q, {"_id": 0, "id": 1, "subject": 1, "chapter": 1, "label": 1, "picks": 1, "winner": 1, "winners": 1, "finished_ts": 1, "vs_bot": 1, "mode": 1, "team_mode": 1, "teams": 1, "team_scores": 1,
                                         "players.uid": 1, "players.pid": 1, "players.name": 1, "players.score": 1, "players.bot": 1, "players.team": 1, "players.ms": 1, "players.forfeit": 1, "players.answers.outcome": 1}
                                  ).sort("finished_ts", -1).limit(300).to_list(300)
        won = lambda d: d.get("winner") == uid or uid in (d.get("winners") or [])  # noqa: E731
        streak = best = correct = answered = 0
        for d in reversed(docs):
            streak = streak + 1 if won(d) else 0
            best = max(best, streak)
            mine = next((p for p in d["players"] if p["uid"] == uid), {})
            outs = [a.get("outcome") for a in mine.get("answers", [])]
            correct += outs.count("correct")
            answered += outs.count("correct") + outs.count("incorrect")
        fav = Counter(d["subject"] for d in docs).most_common(1)
        recent = []
        for d in docs[:5]:
            mine = next((p for p in d["players"] if p["uid"] == uid), {})
            others = [p for p in d["players"] if p["uid"] != uid]
            opp = max(others, key=lambda p: p.get("score", 0)) if others else {}
            group = len(others) > 1
            line = team_line(d, uid)
            recent.append({"id": d["id"], "subject": d["subject"], "chapter": d.get("chapter"), "label": label_for(d), "won": won(d), "tie": d.get("winner") == "tie", "players": len(d["players"]), "team": line,
                           "score": mine.get("score", 0), "opp_score": opp.get("score", 0), "opp_name": f"{len(others)} players" if group else opp.get("name") or "Rival",
                           "opp_pid": None if group or opp.get("bot") else opp.get("pid"),
                           "opp_bot": bool(opp.get("bot")), "finished_at": datetime.fromtimestamp(d["finished_ts"], timezone.utc).isoformat()})
        out = {"matches": matches, "wins": wins, "win_rate": round(100 * wins / matches) if matches else 0, "best_streak": best,
               "accuracy": round(100 * correct / answered) if answered else None, "title": TITLES.get(fav[0][0], "Arena Rookie") if fav else "Arena Rookie", "recent": recent}
        stats_cache[uid] = (time.time(), out)
        if len(stats_cache) > 5000:
            stats_cache.clear()
        return out

    async def relation(me, them):
        mine = await db.rf_friends.find_one({"uid": me, "fid": them}, {"_id": 1})
        theirs = await db.rf_friends.find_one({"uid": them, "fid": me}, {"_id": 1})
        blocked = await db.rf_blocks.find_one({"uid": me, "bid": them}, {"_id": 1})
        return {"friend": bool(mine), "follows_you": bool(theirs), "blocked": bool(blocked)}

    # ---------- profiles ----------
    @r.get("/players/{pid}")
    async def player_profile(pid: str, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        p = await by_pid(pid)
        them = p["uid"]
        if them != uid and await db.rf_blocks.find_one({"uid": them, "bid": uid}, {"_id": 1}):
            raise HTTPException(404, "Player not found.")
        stats = await stats_of(them)
        out = {**card(p), "is_me": them == uid, "title": stats["title"], "stats": {k: stats[k] for k in ("matches", "wins", "win_rate", "best_streak", "accuracy")},
               "recent": stats["recent"], "trophies": [{"id": b, "title": BADGES[b][0], "body": BADGES[b][1]} for b in BADGES if b in p.get("badges", [])],
               "diamonds": vault_total(p), "best_phoenix": p.get("best_phoenix", 0)}
        # Cup Champion showcase: every cup won (real-player wins counted apart) and the last five titles.
        wins = await db.rf_cups.find({"champion": them, "status": "finished"}, {"_id": 0, "id": 1, "label": 1, "size": 1, "kind": 1, "players.bot": 1, "finished_ts": 1}).sort("finished_ts", -1).limit(5).to_list(5)
        out["cups"] = {**(crown_of(p) or {"won": 0, "real": 0}), "played": await db.rf_cups.count_documents({"players.uid": them, "status": "finished"}),
                       "recent": [{"id": c["id"], "label": c["label"], "size": c["size"], "kind": c["kind"], "humans": sum(not x.get("bot") for x in c["players"]),
                                   "finished_at": datetime.fromtimestamp(c["finished_ts"], timezone.utc).isoformat()} for c in wins]}
        if them != uid:
            out["relation"] = await relation(uid, them)
            both = {"players.uid": {"$all": [uid, them]}, "players": {"$size": 2}, "status": "finished", "team_mode": {"$ne": True}}  # head-to-head counts 1 v 1 matches only
            last = await db.rf_duels.find_one(both, {"_id": 0, "id": 1, "winner": 1, "subject": 1, "chapter": 1, "picks": 1}, sort=[("finished_ts", -1)])
            out["head_to_head"] = {"you": await db.rf_duels.count_documents({**both, "winner": uid}), "them": await db.rf_duels.count_documents({**both, "winner": them}),
                                   "played": await db.rf_duels.count_documents(both),
                                   "last": {"id": last["id"], "won": last.get("winner") == uid, "tie": last.get("winner") == "tie", "picks": scope_of(last)} if last else None}
        else:
            out["friend_count"] = await db.rf_friends.count_documents({"uid": uid})
            out["friend_code"] = await friend_code_of(db, uid)
        return out

    @r.get("/players/{pid}/h2h")
    async def head_to_head(pid: str, x_rf_user: Optional[str] = Header(None)):
        """Every 1 v 1 match between you and this player, newest first."""
        uid = rf_user(x_rf_user)
        them = (await by_pid(pid))["uid"]
        if them == uid or await db.rf_blocks.find_one({"uid": them, "bid": uid}, {"_id": 1}):
            raise HTTPException(404, "Player not found.")
        docs = await db.rf_duels.find({"players.uid": {"$all": [uid, them]}, "players": {"$size": 2}, "status": "finished", "team_mode": {"$ne": True}},
                                      {"_id": 0, "id": 1, "subject": 1, "chapter": 1, "label": 1, "picks": 1, "winner": 1, "finished_ts": 1, "players.uid": 1, "players.score": 1}).sort("finished_ts", -1).limit(30).to_list(30)
        score = lambda d, u: next((p.get("score", 0) for p in d["players"] if p["uid"] == u), 0)  # noqa: E731
        return {"items": [{"id": d["id"], "subject": d["subject"], "chapter": d.get("chapter"), "label": label_for(d), "picks": scope_of(d), "you": score(d, uid), "them": score(d, them), "won": d.get("winner") == uid, "tie": d.get("winner") == "tie",
                           "finished_at": datetime.fromtimestamp(d["finished_ts"], timezone.utc).isoformat()} for d in docs]}

    @r.get("/feed")
    async def feed(x_rf_user: Optional[str] = Header(None)):
        """What your friends did in the arena over the last 7 days: wins, win runs, rare diamonds, level-ups and trophies."""
        uid = rf_user(x_rf_user)
        hidden = await blocked_uids(db, uid)
        fids = [e["fid"] for e in await db.rf_friends.find({"uid": uid}, {"_id": 0, "fid": 1}).to_list(500) if e["fid"] not in hidden]
        rows = await db.rf_feed.find({"uid": {"$in": fids}, "ts": {"$gt": time.time() - 7 * 86400}}, {"_id": 0, "at": 0}).sort("ts", -1).limit(30).to_list(30)
        profs = {p["uid"]: p for p in await db.rf_profiles.find({"uid": {"$in": list({e["uid"] for e in rows})}}).to_list(len(rows) or 1)}
        return {"items": [{"id": e["id"], "kind": e["kind"], "data": e.get("data") or {}, "ts": e["ts"], "from": card(profs[e["uid"]])} for e in rows if e["uid"] in profs]}

    # ---------- friends ----------
    @r.get("/friends")
    async def friends(x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        edges = await db.rf_friends.find({"uid": uid}, {"_id": 0, "fid": 1}).to_list(500)
        rows = await db.rf_profiles.find({"uid": {"$in": [e["fid"] for e in edges]}}).to_list(500)
        back = {f["uid"] for f in await db.rf_friends.find({"fid": uid, "uid": {"$in": [p["uid"] for p in rows]}}, {"_id": 0, "uid": 1}).to_list(500)}
        items = [{**card(p), "follows_you": p["uid"] in back} for p in rows]
        items.sort(key=lambda x: (not x["online"], -(x.get("seen_ts") or 0)))
        return {"items": items}

    @r.get("/friends/code")
    async def my_code(x_rf_user: Optional[str] = Header(None)):
        """Your own Friend Code, to share with the people you want as friends."""
        return {"code": await friend_code_of(db, rf_user(x_rf_user))}

    @r.get("/friends/code/{code}")
    async def friend_preview(code: str, x_rf_user: Optional[str] = Header(None)):
        """Who owns this Friend Code (shown before you add them)."""
        uid = rf_user(x_rf_user)
        p = await by_code(uid, code)
        return {**card(p), "is_me": p["uid"] == uid, "friend": (await relation(uid, p["uid"]))["friend"]}

    @r.post("/friends")
    async def add_friend(data: FriendCode, x_rf_user: Optional[str] = Header(None)):
        """A Friend Code makes both players friends at once: whoever shares their code agrees to it."""
        uid = rf_user(x_rf_user)
        p = await by_code(uid, data.code)
        them = p["uid"]
        if them == uid:
            raise HTTPException(400, "That’s your own code! Share it with a friend.")
        if not await db.rf_friends.find_one({"uid": uid, "fid": them}, {"_id": 1}):
            for a in (uid, them):
                if await db.rf_friends.count_documents({"uid": a}) >= MAX_FRIENDS:
                    raise HTTPException(409, "Your friend list is full." if a == uid else "This player’s friend list is full.")
        new = False
        for a, b in ((uid, them), (them, uid)):
            try:
                await db.rf_friends.insert_one({"uid": a, "fid": b, "ts": time.time()})
                new = True
            except DuplicateKeyError:
                pass
        if new:
            await db.rf_notices.update_one({"uid": them, "from_uid": uid, "kind": "friend_added"},
                                           {"$set": {"ts": time.time(), "done": False}, "$setOnInsert": {"id": str(uuid.uuid4())}}, upsert=True)
        await db.rf_notices.update_many({"uid": uid, "from_uid": them, "kind": "friend_added"}, {"$set": {"done": True}})
        return {"friend": card(p), "relation": await relation(uid, them)}

    @r.delete("/friends/{pid}")
    async def remove_friend(pid: str, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        p = await by_pid(pid)
        await db.rf_friends.delete_many({"$or": [{"uid": uid, "fid": p["uid"]}, {"uid": p["uid"], "fid": uid}]})
        await db.rf_notices.update_many({"$or": [{"uid": uid, "from_uid": p["uid"]}, {"uid": p["uid"], "from_uid": uid}], "kind": "friend_added"}, {"$set": {"done": True}})
        return {"relation": await relation(uid, p["uid"])}

    @r.post("/blocks")
    async def block(data: Target, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        p = await by_pid(data.pid)
        them = p["uid"]
        if them == uid:
            raise HTTPException(400, "That’s you!")
        await db.rf_blocks.update_one({"uid": uid, "bid": them}, {"$set": {"ts": time.time()}}, upsert=True)
        await db.rf_friends.delete_many({"$or": [{"uid": uid, "fid": them}, {"uid": them, "fid": uid}]})
        await db.rf_notices.update_many({"$or": [{"uid": uid, "from_uid": them}, {"uid": them, "from_uid": uid}]}, {"$set": {"done": True}})
        for host, guest in ((uid, them), (them, uid)):  # open invitations between the two close quietly
            await db.rf_challenges.update_many({"from_uid": host, "status": "open", "invites": {"$elemMatch": {"uid": guest, "status": {"$in": ["sent", "seen"]}}}},
                                               {"$set": {"invites.$.status": "declined"}})
        return {"relation": await relation(uid, them)}

    @r.delete("/blocks/{pid}")
    async def unblock(pid: str, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        p = await by_pid(pid)
        await db.rf_blocks.delete_one({"uid": uid, "bid": p["uid"]})
        return {"relation": await relation(uid, p["uid"])}

    @r.post("/notices/{nid}/dismiss")
    async def dismiss(nid: str, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        await db.rf_notices.update_one({"id": nid, "uid": uid}, {"$set": {"done": True}})
        return {"ok": True}

    return r
