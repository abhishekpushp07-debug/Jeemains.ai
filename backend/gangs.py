"""Rapid Fire gangs: a shared group of friends with a name and an emblem. Any member can challenge the whole gang."""
import re
import secrets
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from social import blocked_uids, card, find_player, public_name, team_scores

EMBLEMS = ("lion", "eagle", "thunder", "crown", "shield", "dragon", "wolf", "rocket")
MAX_MEMBERS, MAX_GANGS = 20, 10
# Words a gang name may not contain (checked after removing spaces, symbols and look-alike digits).
BLOCKED = ("fuck", "shit", "bitch", "asshole", "bastard", "pussy", "slut", "whore", "nigg", "rapist", "porn", "chutiya", "chutia", "bhosdi", "bhosad",
           "madarchod", "behenchod", "bhenchod", "gandu", "gaand", "lund", "lauda", "lavda", "randi", "harami", "bsdk", "chod")
LOOKALIKE = str.maketrans("013457@$!", "oieastasi")


def clean_name(raw) -> str:
    name = re.sub(r"\s+", " ", str(raw or "")).strip()
    if not 2 <= len(name) <= 20:
        raise HTTPException(400, "Gang names are 2 to 20 characters.")
    flat = re.sub(r"[^a-z]", "", name.lower().translate(LOOKALIKE))
    if any(w in flat for w in BLOCKED):
        raise HTTPException(400, "Please pick a different gang name.")
    return name


class GangCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=40)
    emblem: str = Field(max_length=12)
    pids: List[str] = Field(default_factory=list, max_length=MAX_MEMBERS - 1)


class GangEdit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Optional[str] = Field(default=None, max_length=40)
    emblem: Optional[str] = Field(default=None, max_length=12)


class Members(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pids: List[str] = Field(min_length=1, max_length=MAX_MEMBERS - 1)


class Report(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str = Field(default="", max_length=200)


class Join(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(min_length=8, max_length=8)


def record_of(g: dict) -> dict:
    """Gang Battle record: battles won and lost against other gangs."""
    return {"wins": int(g.get("wins", 0)), "losses": int(g.get("losses", 0))}


def make_router(db, rf_user):
    r = APIRouter(prefix="/rf/gangs")
    live = {"closed": {"$ne": True}}

    def emblem_of(raw):
        if raw not in EMBLEMS:
            raise HTTPException(400, "Pick one of the gang emblems.")
        return raw

    async def member_gang(gid, uid, leader=False):
        g = await db.rf_gangs.find_one({"id": gid, "members.uid": uid, **live}, {"_id": 0})
        if not g:
            raise HTTPException(404, "Gang not found.")
        if leader and g["leader_uid"] != uid:
            raise HTTPException(403, "Only the gang leader can do this.")
        return g

    async def add(g, uid, pids):
        """Any member adds their own friends straight in. Returns how many joined and why the rest could not."""
        hidden = await blocked_uids(db, uid)
        targets = list(dict.fromkeys([(await find_player(db, pid))["uid"] for pid in pids]))
        friends = {f["fid"] for f in await db.rf_friends.find({"uid": uid, "fid": {"$in": targets}}, {"_id": 0, "fid": 1}).to_list(len(targets) or 1)}
        have = {m["uid"] for m in g["members"]}
        added, skipped = 0, []
        for t in targets:
            if t in have:
                continue
            reason = ("Not in your friends" if t not in friends or t in hidden else "Gang is full" if len(have) >= MAX_MEMBERS
                      else "Already in 10 gangs" if await db.rf_gangs.count_documents({"members.uid": t, **live}) >= MAX_GANGS else "")
            if reason:
                skipped.append(reason)
                continue
            res = await db.rf_gangs.update_one({"id": g["id"], "members.uid": {"$ne": t}, f"members.{MAX_MEMBERS - 1}": {"$exists": False}},
                                               {"$push": {"members": {"uid": t, "ts": time.time(), "by": uid}}})
            if res.modified_count:
                have.add(t)
                added += 1
                await db.rf_notices.insert_one({"id": str(uuid.uuid4()), "uid": t, "from_uid": uid, "kind": "gang_added", "ts": time.time(), "done": False,
                                                "gang": {"id": g["id"], "name": g["name"], "emblem": g["emblem"]}})
        return {"added": added, "skipped": skipped}

    def online_count(profs):
        return sum(card(p)["online"] for p in profs)

    @r.get("")
    async def mine(x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        gangs = await db.rf_gangs.find({"members.uid": uid, **live}, {"_id": 0}).sort("created_ts", 1).to_list(MAX_GANGS)
        uids = list({m["uid"] for g in gangs for m in g["members"]})
        profs = {p["uid"]: p for p in await db.rf_profiles.find({"uid": {"$in": uids}}, {"uid": 1, "seen_ts": 1}).to_list(len(uids) or 1)}
        return {"items": [{"id": g["id"], "name": g["name"], "emblem": g["emblem"], "members": len(g["members"]), "leader": g["leader_uid"] == uid,
                           "online": online_count([profs[m["uid"]] for m in g["members"] if m["uid"] in profs and m["uid"] != uid])} for g in gangs]}

    @r.post("")
    async def create(data: GangCreate, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        name, emblem = clean_name(data.name), emblem_of(data.emblem)
        if await db.rf_gangs.count_documents({"members.uid": uid, **live}) >= MAX_GANGS:
            raise HTTPException(409, "You’re already in 10 gangs. Leave one to start another.")
        g = {"id": "G" + uuid.uuid4().hex[:10].upper(), "name": name, "emblem": emblem, "leader_uid": uid, "created_ts": time.time(), "closed": False,
             "members": [{"uid": uid, "ts": time.time(), "by": uid}]}
        await db.rf_gangs.insert_one(g)
        result = await add(g, uid, data.pids) if data.pids else {"added": 0, "skipped": []}
        return {"id": g["id"], **result}

    @r.get("/search")
    async def search(q: str = Query(min_length=2, max_length=40), x_rf_user: Optional[str] = Header(None)):
        """Find a rival gang for a Gang Battle by its name or its gang code."""
        uid = rf_user(x_rf_user)
        term = q.strip()
        query = {"id": term.upper()} if re.fullmatch(r"[Gg][0-9A-Fa-f]{10}", term) else {"name": {"$regex": re.escape(term), "$options": "i"}}
        rows = await db.rf_gangs.find({**query, **live, "members.uid": {"$ne": uid}}, {"_id": 0}).limit(20).to_list(20)
        return {"items": [{"id": g["id"], "name": g["name"], "emblem": g["emblem"], "members": len(g["members"]), **record_of(g)} for g in rows]}

    @r.get("/{gid}")
    async def detail(gid: str, code: Optional[str] = Query(default=None, max_length=8), x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        g = await db.rf_gangs.find_one({"id": gid, **live}, {"_id": 0})
        inside = bool(g) and any(m["uid"] == uid for m in g["members"])
        if not g or not (inside or (code and code.upper() == g.get("invite_code"))):
            raise HTTPException(404, "Gang not found.")
        if not inside:  # opened from an invite link: a preview with one Join button
            leader = await db.rf_profiles.find_one({"uid": g["leader_uid"]}) or {}
            return {"member": False, "id": g["id"], "name": g["name"], "emblem": g["emblem"], "size": len(g["members"]), "max": MAX_MEMBERS, "leader": public_name(leader), "record": record_of(g)}
        if not g.get("invite_code"):
            g["invite_code"] = secrets.token_hex(4).upper()
            await db.rf_gangs.update_one({"id": gid, "invite_code": {"$exists": False}}, {"$set": {"invite_code": g["invite_code"]}})
            g["invite_code"] = (await db.rf_gangs.find_one({"id": gid}, {"invite_code": 1}))["invite_code"]
        profs = {p["uid"]: p for p in await db.rf_profiles.find({"uid": {"$in": [m["uid"] for m in g["members"]]}}).to_list(MAX_MEMBERS)}
        members = [{**card(profs.get(m["uid"], {"uid": m["uid"]})), "leader": m["uid"] == g["leader_uid"], "you": m["uid"] == uid} for m in g["members"]]
        members.sort(key=lambda m: (not m["you"], not m["online"], -(m.get("seen_ts") or 0)))
        # Every finished gang match and Gang Battle this gang played (newest first) feeds the recent list, the rivals and the leaderboard.
        duels = await db.rf_duels.find({"status": "finished", "$or": [{"gang_id": gid}, {"teams.a.id": gid}, {"teams.b.id": gid}]},
                                       {"_id": 0, "id": 1, "subject": 1, "chapter": 1, "winner": 1, "winners": 1, "finished_ts": 1, "team_mode": 1, "teams": 1, "team_scores": 1,
                                        "players.uid": 1, "players.name": 1, "players.team": 1, "players.score": 1, "players.ms": 1, "players.forfeit": 1}).sort("finished_ts", -1).limit(200).to_list(200)
        wins, played, rivals, recent = Counter(), Counter(), {}, []
        for d in duels:
            side = next((t for t in ("a", "b") if d.get("team_mode") and d["teams"][t]["id"] == gid), None)
            for p in d["players"]:
                if p["uid"] in profs and (not side or p.get("team") == side):
                    played[p["uid"]] += 1
                    wins[p["uid"]] += d.get("winner") == p["uid"] or p["uid"] in (d.get("winners") or [])
            battle = None
            if side:
                other = "b" if side == "a" else "a"
                ts = d.get("team_scores") or team_scores(d)
                rivals.setdefault(d["teams"][other]["id"], d["teams"][other])
                battle = {"rival": d["teams"][other]["name"], "emblem": d["teams"][other]["emblem"], "us": ts[side]["score"], "them": ts[other]["score"], "won": d.get("winner") == "team:" + side}
            if len(recent) < 5:
                recent.append({"id": d["id"], "subject": d["subject"], "chapter": d.get("chapter"), "players": len(d["players"]), "battle": battle,
                               "winner": next((p["name"] for p in d["players"] if p["uid"] == d.get("winner")), "Tie"), "you_played": any(p["uid"] == uid for p in d["players"]),
                               "finished_at": datetime.fromtimestamp(d["finished_ts"], timezone.utc).isoformat()})
        board = sorted(({**{k: m[k] for k in ("pid", "name", "avatar", "frame", "you")}, "wins": wins[u], "played": played[u]}
                        for u, m in ((m["uid"], next(x for x in members if x["pid"] == card(profs.get(m["uid"], {"uid": m["uid"]}))["pid"])) for m in g["members"]) if played[u]),
                       key=lambda row: (-row["wins"], -row["played"]))
        return {"member": True, "id": g["id"], "name": g["name"], "emblem": g["emblem"], "is_leader": g["leader_uid"] == uid, "max": MAX_MEMBERS, "members": members,
                "online": sum(m["online"] and not m["you"] for m in members), "record": record_of(g), "invite_code": g["invite_code"],
                "board": board[:10], "rivals": list(rivals.values())[:5], "recent": recent}

    @r.post("/{gid}/join")
    async def join(gid: str, data: Join, x_rf_user: Optional[str] = Header(None)):
        """Join with the gang's invite link."""
        uid = rf_user(x_rf_user)
        g = await db.rf_gangs.find_one({"id": gid, "invite_code": data.code.upper(), **live})
        if not g:
            raise HTTPException(404, "This invite link no longer works. Ask for a new one.")
        if any(m["uid"] == uid for m in g["members"]):
            return {"ok": True}
        if g["leader_uid"] in await blocked_uids(db, uid):
            raise HTTPException(403, "You can’t join this gang.")
        if await db.rf_gangs.count_documents({"members.uid": uid, **live}) >= MAX_GANGS:
            raise HTTPException(409, "You’re already in 10 gangs. Leave one to join another.")
        res = await db.rf_gangs.update_one({"id": gid, "members.uid": {"$ne": uid}, f"members.{MAX_MEMBERS - 1}": {"$exists": False}},
                                           {"$push": {"members": {"uid": uid, "ts": time.time(), "by": uid}}})
        if not res.modified_count:
            raise HTTPException(409, "This gang is full.")
        return {"ok": True}

    @r.patch("/{gid}")
    async def edit(gid: str, data: GangEdit, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        await member_gang(gid, uid, leader=True)
        fields = {**({"name": clean_name(data.name)} if data.name is not None else {}), **({"emblem": emblem_of(data.emblem)} if data.emblem is not None else {})}
        if fields:
            await db.rf_gangs.update_one({"id": gid}, {"$set": fields})
        return {"ok": True}

    @r.delete("/{gid}")
    async def close(gid: str, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        await member_gang(gid, uid, leader=True)
        await db.rf_gangs.update_one({"id": gid}, {"$set": {"closed": True}})
        await db.rf_challenges.update_many({"gang_id": gid, "status": "open"}, {"$set": {"status": "cancelled"}})
        return {"ok": True}

    @r.post("/{gid}/members")
    async def add_members(gid: str, data: Members, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        return await add(await member_gang(gid, uid), uid, data.pids)

    @r.delete("/{gid}/members/{pid}")
    async def remove_member(gid: str, pid: str, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        await member_gang(gid, uid, leader=True)
        them = (await find_player(db, pid))["uid"]
        if them == uid:
            raise HTTPException(400, "Use Leave to step out of your own gang.")
        await db.rf_gangs.update_one({"id": gid}, {"$pull": {"members": {"uid": them}}})
        return {"ok": True}

    @r.post("/{gid}/leave")
    async def leave(gid: str, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        g = await member_gang(gid, uid)
        rest = sorted((m for m in g["members"] if m["uid"] != uid), key=lambda m: m["ts"])
        update = {"$pull": {"members": {"uid": uid}}}
        if not rest:
            update["$set"] = {"closed": True}
        elif g["leader_uid"] == uid:  # the longest-standing member takes over
            update["$set"] = {"leader_uid": rest[0]["uid"]}
        await db.rf_gangs.update_one({"id": gid}, update)
        await db.rf_notices.update_many({"uid": uid, "kind": "gang_added", "gang.id": gid}, {"$set": {"done": True}})
        return {"ok": True}

    @r.post("/{gid}/report")
    async def report(gid: str, data: Report, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        g = await member_gang(gid, uid)
        await db.rf_gang_reports.update_one({"gang_id": gid, "uid": uid}, {"$set": {"name": g["name"], "reason": data.reason.strip(), "ts": time.time()}}, upsert=True)
        return {"ok": True}

    return r
