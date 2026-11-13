"""Rapid Fire Match Rooms: challenge one friend, several friends (up to 4) or a whole gang. Up to 5 players per match.

A room stays open for 3 minutes. It starts when the single invited friend accepts, when the host presses START,
when all 5 seats are full, when everyone invited has answered, or at the 3-minute mark with whoever joined.
"""
import html
import re
import time
import uuid
from typing import List, Literal, Optional

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field
from pymongo import ReturnDocument

from exam_groups import resolve_exam
from scope import Pick, label_for, normalise, scope_fields, scope_of
from social import blocked_uids, card, find_player, make_pid, public_name

ROOM_SECONDS = 180
SEATS = 5
MAX_INVITES = 25  # a big batch invites its most recently active members, not all 200
APP_SCHEME = "frontend"  # the scheme this app registers (app.json)
WAITING = ["sent", "seen"]
ORDER = {"joined": 0, "seen": 1, "sent": 2, "declined": 3, "left": 3}


class RoomCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pids: List[str] = Field(default_factory=list, max_length=SEATS - 1)
    gang_id: Optional[str] = Field(default=None, max_length=16)
    subject: Literal["Physics", "Chemistry", "Mathematics"] = "Physics"
    chapter: Optional[str] = Field(default=None, max_length=80)
    picks: Optional[List[Pick]] = Field(default=None, max_length=5)  # up to 5 subjects or chapters; wins over subject and chapter
    rematch_of: Optional[str] = Field(default=None, max_length=64)
    # Gang Battle: my gang (gang_id) against this gang, as two teams of up to 5.
    rival_gang_id: Optional[str] = Field(default=None, max_length=16)


def make_router(db, rf_user, seat_duel):
    r = APIRouter(prefix="/rf")
    after = ReturnDocument.AFTER
    open_gang = {"closed": {"$ne": True}}

    async def most_active(uids):
        if len(uids) <= MAX_INVITES:
            return uids
        seen = {p["uid"]: p.get("seen_ts") or 0 for p in await db.rf_profiles.find({"uid": {"$in": uids}}, {"uid": 1, "seen_ts": 1}).to_list(len(uids))}
        return sorted(uids, key=lambda u: -seen.get(u, 0))[:MAX_INVITES]

    def joined_of(c):
        return sorted((i for i in c["invites"] if i["status"] == "joined"), key=lambda i: i["ts"])

    def team_counts(c):
        """Joined players on each side of a Gang Battle (the host is on team A and is not counted here)."""
        joined = joined_of(c)
        a = sum(i.get("team") == "a" for i in joined)
        return a, len(joined) - a

    async def battle_sides(uid, mine_id, rival_id, hidden):
        """Both gangs of a Gang Battle and who gets invited to which team."""
        mine = await db.rf_gangs.find_one({"id": mine_id, "members.uid": uid, **open_gang})
        rival = await db.rf_gangs.find_one({"id": rival_id, **open_gang})
        if not mine or not rival or mine["id"] == rival["id"]:
            raise HTTPException(404, "Gang not found.")
        ours = await most_active([m["uid"] for m in mine["members"] if m["uid"] != uid and m["uid"] not in hidden])
        theirs = await most_active([m["uid"] for m in rival["members"] if m["uid"] != uid and m["uid"] not in hidden and m["uid"] not in ours])
        if not theirs:
            raise HTTPException(400, "That gang has nobody to battle yet.")
        tag = lambda g: {k: g[k] for k in ("id", "name", "emblem")}  # noqa: E731
        return mine["id"], {"a": tag(mine), "b": tag(rival)}, {**{u: "a" for u in ours}, **{u: "b" for u in theirs}}

    async def start(c):
        got = await db.rf_challenges.find_one_and_update({"id": c["id"], "status": "open"}, {"$set": {"status": "starting"}}, return_document=after)
        if not got:  # another request is already starting this room
            return await db.rf_challenges.find_one({"id": c["id"]})
        joined, teams = joined_of(got), None
        if got.get("team_mode"):
            teams = {"a": {**got["vs"]["a"], "uids": [got["from_uid"]] + [i["uid"] for i in joined if i.get("team") == "a"][:SEATS - 1]},
                     "b": {**got["vs"]["b"], "uids": [i["uid"] for i in joined if i.get("team") == "b"][:SEATS]}}
            seats = teams["a"]["uids"] + teams["b"]["uids"]
        else:
            seats = [got["from_uid"]] + [i["uid"] for i in joined][:SEATS - 1]
        duel_id = await seat_duel(got["exam"], scope_of(got), seats, got["id"], got.get("gang_id"), teams)
        return await db.rf_challenges.find_one_and_update({"id": c["id"]}, {"$set": {"status": "started", "duel_id": duel_id}}, return_document=after)

    async def settle(c):
        """Start or close a room whose moment has come."""
        if c["status"] != "open":
            return c
        joined = len(joined_of(c))
        if c.get("team_mode"):  # a Gang Battle needs at least one rival in the room
            a, b = team_counts(c)
            ready, full = b >= 1, a >= SEATS - 1 and b >= SEATS
        else:
            ready, full = joined >= 1, joined >= SEATS - 1
        waiting = any(i["status"] in WAITING for i in c["invites"])
        late = time.time() > c["expires_ts"]
        if ready and (c.get("single") or c.get("go") or full or not waiting or late):
            return await start(c)
        if not ready and (late or not waiting):
            return await db.rf_challenges.find_one_and_update({"id": c["id"], "status": "open"}, {"$set": {"status": "expired" if late else "declined"}},
                                                              return_document=after) or await db.rf_challenges.find_one({"id": c["id"]})
        return c

    async def gang_tag(c):
        return await db.rf_gangs.find_one({"id": c["gang_id"]}, {"_id": 0, "id": 1, "name": 1, "emblem": 1}) if c.get("gang_id") else None

    async def view(c, uid):
        c = await settle(c)
        uids = [c["from_uid"]] + [i["uid"] for i in c["invites"]]
        profs = {p["uid"]: p for p in await db.rf_profiles.find({"uid": {"$in": uids}}).to_list(len(uids))}
        mine = next((i for i in c["invites"] if i["uid"] == uid), None)
        host = c["from_uid"] == uid
        joined = len(joined_of(c))
        battle, vs, ready = bool(c.get("team_mode")), None, joined >= 1
        if battle:
            a, b = team_counts(c)
            ready = b >= 1
            vs = {"a": {**c["vs"]["a"], "joined": a + 1, "seats": SEATS}, "b": {**c["vs"]["b"], "joined": b, "seats": SEATS}}
        return {"id": c["id"], "status": c["status"], "subject": c["subject"], "chapter": c.get("chapter"), "label": label_for(c), "picks": scope_of(c), "revenge": bool(c.get("revenge")), "exam": c["exam"], "duel_id": c.get("duel_id"), "single": bool(c.get("single")),
                "rematch_of": c.get("rematch_of"), "expires_in": max(0, round(c["expires_ts"] - time.time())), "seats": SEATS, "joined": joined + 1, "is_host": host,
                "my_status": "host" if host else mine["status"], "can_start": host and c["status"] == "open" and ready, "gang": await gang_tag(c),
                "team_mode": battle, "vs": vs, "my_team": ("a" if host else mine.get("team")) if battle else None,
                "host": card(profs.get(c["from_uid"], {"uid": c["from_uid"]})),
                "players": [{**card(profs.get(i["uid"], {"uid": i["uid"]})), "status": i["status"], "you": i["uid"] == uid, "team": i.get("team")}
                            for i in sorted(c["invites"], key=lambda i: (ORDER[i["status"]], i["ts"]))]}

    async def owned(cid, uid):
        c = await db.rf_challenges.find_one({"id": cid, "$or": [{"from_uid": uid}, {"invites.uid": uid}]})
        if not c:
            raise HTTPException(404, "This challenge isn’t for you, or it no longer exists.")
        return c

    async def free(uid, keep=None):
        """One open challenge at a time: close the rooms this player hosts and leave the ones they joined."""
        await db.rf_challenges.update_many({"from_uid": uid, "status": "open", "id": {"$ne": keep}}, {"$set": {"status": "cancelled"}})
        await db.rf_challenges.update_many({"status": "open", "id": {"$ne": keep}, "invites": {"$elemMatch": {"uid": uid, "status": "joined"}}},
                                           {"$set": {"invites.$.status": "left"}, "$inc": {"joined": -1}})

    def seat_rule(c, uid):
        """The condition that keeps a room from over-filling. A Gang Battle counts seats per team: 5 each, the host holds one of team A's."""
        if not c.get("team_mode"):
            return {"joined": {"$lt": SEATS - 1}}
        team = next((i.get("team") for i in c["invites"] if i["uid"] == uid), "b")
        taken = {"$size": {"$filter": {"input": "$invites", "cond": {"$and": [{"$eq": ["$$this.status", "joined"]}, {"$eq": ["$$this.team", team]}]}}}}
        return {"$expr": {"$lt": [taken, SEATS - 1 if team == "a" else SEATS]}}

    async def join(cid, uid):
        now = time.time()
        before = await owned(cid, uid)
        if before["from_uid"] == uid:
            raise HTTPException(403, "Only invited players can accept.")
        c = await db.rf_challenges.find_one_and_update(
            {"id": cid, "status": "open", "expires_ts": {"$gt": now}, **seat_rule(before, uid), "invites": {"$elemMatch": {"uid": uid, "status": {"$ne": "joined"}}}},
            {"$set": {"invites.$.status": "joined", "invites.$.ts": now}, "$inc": {"joined": 1}}, return_document=after)
        if not c:
            c = await owned(cid, uid)
            if any(i["uid"] == uid and i["status"] == "joined" for i in c["invites"]):
                return await view(c, uid)
            raise HTTPException(409, "Match full." if c["status"] == "open" and c["expires_ts"] > now else "This challenge is no longer open.")
        await free(uid, keep=cid)
        return await view(c, uid)

    @r.post("/challenges")
    async def create(data: RoomCreate, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        picks = normalise(data.picks, data.subject, data.chapter)
        now, gang_id, hidden = time.time(), None, await blocked_uids(db, uid)
        vs, team_of, revenge = None, {}, False
        if data.rematch_of:
            duel = await db.rf_duels.find_one({"id": data.rematch_of, "players.uid": uid, "status": "finished"},
                                              {"players.uid": 1, "players.bot": 1, "players.team": 1, "gang_id": 1, "team_mode": 1, "teams": 1, "subject": 1, "chapter": 1, "picks": 1, "winner": 1})
            if not duel:
                raise HTTPException(404, "Match not found.")
            # A rematch is on the same subjects and chapters, unless the player chose a new battleground (Badla lo).
            picks = normalise(data.picks) if data.picks else scope_of(duel)
            waiting = await db.rf_challenges.find_one({"rematch_of": data.rematch_of, "status": "open", "expires_ts": {"$gt": now}, "invites.uid": uid})
            if waiting:  # someone already opened the rematch room: take a seat
                return await join(waiting["id"], uid)
            if duel.get("team_mode"):  # the same two gangs again, my gang as team A
                side = next(p.get("team") for p in duel["players"] if p["uid"] == uid)
                gang_id, vs, team_of = await battle_sides(uid, duel["teams"][side]["id"], duel["teams"]["b" if side == "a" else "a"]["id"], hidden)
                targets = list(team_of)
            else:
                targets = [p["uid"] for p in duel["players"] if p["uid"] != uid and not p.get("bot") and p["uid"] not in hidden]
                gang_id = duel.get("gang_id")
                if not gang_id:  # outside a gang, only friends can be called back
                    friends = {f["fid"] for f in await db.rf_friends.find({"uid": uid, "fid": {"$in": targets}}, {"_id": 0, "fid": 1}).to_list(len(targets) or 1)}
                    targets = [t for t in targets if t in friends]
                    if not targets:
                        raise HTTPException(403, "Rematches are for friends. Add this player with their Friend Code first.")
                # Badla: you lost this 1 v 1 and want it back.
                revenge = len(duel["players"]) == 2 and duel.get("winner") not in (uid, "tie")
        elif data.gang_id and data.rival_gang_id:
            gang_id, vs, team_of = await battle_sides(uid, data.gang_id, data.rival_gang_id, hidden)
            targets = list(team_of)
        elif data.gang_id:
            gang = await db.rf_gangs.find_one({"id": data.gang_id, "members.uid": uid, "closed": {"$ne": True}})
            if not gang:
                raise HTTPException(404, "Gang not found.")
            gang_id = gang["id"]
            targets = await most_active([m["uid"] for m in gang["members"] if m["uid"] != uid and m["uid"] not in hidden])
        else:
            targets = list(dict.fromkeys([(await find_player(db, pid))["uid"] for pid in data.pids]))
            if uid in targets:
                raise HTTPException(400, "You can’t challenge yourself.")
            if hidden & set(targets):
                raise HTTPException(403, "You can’t challenge this player.")
            friends = {f["fid"] for f in await db.rf_friends.find({"uid": uid, "fid": {"$in": targets}}, {"_id": 0, "fid": 1}).to_list(len(targets))}
            if set(targets) - friends:
                raise HTTPException(403, "Add this player with their Friend Code first.")
        if not targets:
            raise HTTPException(400, "There’s nobody to challenge here yet.")
        await free(uid)
        exam = resolve_exam("JEE", picks[0]["subject"])
        c = {"id": str(uuid.uuid4()), "from_uid": uid, "exam": exam, **scope_fields(picks), "revenge": revenge, "status": "open", "created_ts": now,
             "expires_ts": now + ROOM_SECONDS, "rematch_of": data.rematch_of, "gang_id": gang_id, "single": len(targets) == 1 and not data.gang_id and not vs, "joined": 0,
             **({"team_mode": True, "vs": vs} if vs else {}),
             "invites": [{"uid": t, "status": "sent", "ts": now, **({"team": team_of[t]} if vs else {})} for t in targets]}
        await db.rf_challenges.insert_one(c)
        return await view(c, uid)

    @r.get("/challenges/{cid}")
    async def get(cid: str, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        return await view(await owned(cid, uid), uid)

    @r.post("/challenges/{cid}/accept")
    async def accept(cid: str, x_rf_user: Optional[str] = Header(None)):
        return await join(cid, rf_user(x_rf_user))

    async def change(cid, uid, query, update):
        await owned(cid, uid)
        await db.rf_challenges.update_one({"id": cid, "status": "open", **query}, update)
        return await view(await owned(cid, uid), uid)

    @r.post("/challenges/{cid}/decline")
    async def decline(cid: str, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        return await change(cid, uid, {"invites": {"$elemMatch": {"uid": uid, "status": {"$in": WAITING}}}}, {"$set": {"invites.$.status": "declined"}})

    @r.post("/challenges/{cid}/leave")
    async def leave(cid: str, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        return await change(cid, uid, {"invites": {"$elemMatch": {"uid": uid, "status": "joined"}}}, {"$set": {"invites.$.status": "left"}, "$inc": {"joined": -1}})

    @r.post("/challenges/{cid}/start")
    async def start_now(cid: str, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        c = await owned(cid, uid)
        if c["from_uid"] != uid:
            raise HTTPException(403, "Only the player who sent the challenge can start it.")
        if c["status"] == "open" and c.get("team_mode") and not team_counts(c)[1]:
            raise HTTPException(409, "Wait for at least one rival to join.")
        if c["status"] == "open" and not joined_of(c):
            raise HTTPException(409, "Wait for at least one friend to join.")
        return await change(cid, uid, {"from_uid": uid}, {"$set": {"go": True}})

    @r.post("/challenges/{cid}/cancel")
    async def cancel(cid: str, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        return await change(cid, uid, {"from_uid": uid}, {"$set": {"status": "cancelled"}})

    # ---------- inbox: presence, challenge banner, red dot and notices ----------
    @r.get("/inbox")
    async def inbox(x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        now = time.time()
        me = await db.rf_profiles.find_one_and_update({"uid": uid}, {"$set": {"seen_ts": now, "pid": make_pid(uid)}}, upsert=True, return_document=after)
        live = {"status": "open", "expires_ts": {"$gt": now}}
        await db.rf_challenges.update_many({**live, "invites": {"$elemMatch": {"uid": uid, "status": "sent"}}}, {"$set": {"invites.$.status": "seen"}})
        rooms = await db.rf_challenges.find({**live, "invites": {"$elemMatch": {"uid": uid, "status": "seen"}}}).sort("created_ts", -1).limit(3).to_list(3)
        mine = await db.rf_challenges.find_one({"status": "open", "$or": [{"from_uid": uid}, {"invites": {"$elemMatch": {"uid": uid, "status": "joined"}}}]}, {"id": 1}, sort=[("created_ts", -1)])
        notices = await db.rf_notices.find({"uid": uid, "done": False}).sort("ts", -1).limit(6).to_list(6)
        people = {p["uid"]: p for p in await db.rf_profiles.find({"uid": {"$in": [c["from_uid"] for c in rooms] + [n["from_uid"] for n in notices]}}).to_list(12)}
        cups = await db.rf_cups.find({"status": "open", "expires_ts": {"$gt": now}, "invites": uid, "players.uid": {"$ne": uid}}).sort("created_ts", -1).limit(2).to_list(2)
        my_cup = await db.rf_cups.find_one({"players.uid": uid, "status": {"$in": ["open", "live"]}}, {"id": 1})
        hosts = {p["uid"]: p for p in await db.rf_profiles.find({"uid": {"$in": [c["host_uid"] for c in cups]}}).to_list(2)} if cups else {}
        return {"me": card(me), "room": mine["id"] if mine else None, "cup": my_cup["id"] if my_cup else None,
                "cups": [{"id": c["id"], "label": c["label"], "size": c["size"], "joined": len(c["players"]), "expires_in": max(0, round(c["expires_ts"] - now)),
                          "from": card(hosts.get(c["host_uid"], {"uid": c["host_uid"]}))} for c in cups],
                "challenges": [{"id": c["id"], "subject": c["subject"], "chapter": c.get("chapter"), "label": label_for(c), "revenge": bool(c.get("revenge")), "expires_in": max(0, round(c["expires_ts"] - now)), "joined": c.get("joined", 0) + 1,
                                "seats": SEATS * 2 if c.get("vs") else SEATS, "single": bool(c.get("single")), "gang": await gang_tag(c), "vs": c.get("vs"),
                                "team": next((i.get("team") for i in c["invites"] if i["uid"] == uid), None), "from": card(people.get(c["from_uid"], {"uid": c["from_uid"]}))} for c in rooms],
                "notices": [{"id": n["id"], "kind": n["kind"], "ts": n["ts"], "gang": n.get("gang"), "from": card(people[n["from_uid"]])} for n in notices if n["from_uid"] in people]}

    # ---------- public link pages (WhatsApp invites; no login, no private data) ----------
    def page(title, lead, button, deep, code="", hint=""):
        t, lead_ = html.escape(title), html.escape(lead)
        box = f'<div class="code" data-testid="rf-link-code">{html.escape(code)}</div>' if code else ""
        return HTMLResponse(f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{t} · JEECIRCLE.AI</title><style>body{{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:radial-gradient(circle at 50% 0,#8C1227,#3D0610);color:#fff;font-family:system-ui,sans-serif}}
main{{max-width:380px;padding:32px 24px;text-align:center}}.k{{letter-spacing:3px;font-size:12px;color:#FFD75E;font-weight:800}}h1{{font-size:28px;margin:14px 0 8px;color:#FFD75E}}p{{color:#9EF3E6;line-height:1.5}}
a{{display:block;margin-top:14px;padding:16px;border-radius:16px;font-weight:800;text-decoration:none}}.p{{background:linear-gradient(#2FE0C8,#12B5A0);border-bottom:5px solid #0A6E63;color:#fff}}.s{{border:1px solid #8A2A3C;background:#3E0A14;color:#fff}}
.code{{margin-top:22px;padding:12px;border-radius:14px;border:1px dashed #C2485C;font-size:20px;letter-spacing:4px;font-weight:800}}</style></head>
<body><main data-testid="rf-link-page"><div class="k">JEECIRCLE.AI · RAPID FIRE</div><h1 data-testid="rf-link-title">{t}</h1><p>{lead_}</p>
<a class="p" data-testid="rf-link-open" href="{deep}">{html.escape(button)}</a><a class="s" data-testid="rf-link-download" href="https://jeelive.ai">Get the app</a>
{box}<p style="font-size:12px">{html.escape(hint)}</p></main></body></html>""",
                            headers={"Cache-Control": "no-store"})

    @r.get("/g/{gid}/{code}", include_in_schema=False)
    async def gang_page(gid: str, code: str):
        ok = re.fullmatch(r"G[0-9A-F]{10}", gid) and re.fullmatch(r"[0-9A-F]{8}", code)
        g = await db.rf_gangs.find_one({"id": gid, "invite_code": code, **open_gang}) if ok else None
        if not g:
            raise HTTPException(404, "Gang not found.")
        return page(f"Join {g['name']} on Rapid Fire", f"{len(g['members'])} players are already in. Take your place and battle other gangs together.",
                    "Join the gang", f"{APP_SCHEME}://rapid/gang/{gid}?code={code}", gid, "Rival gangs can battle you with this gang code.")

    @r.get("/c/{cid}", include_in_schema=False)
    async def challenge_page(cid: str):
        c = await db.rf_challenges.find_one({"id": cid}) if re.fullmatch(r"[0-9a-f-]{36}", cid) else None
        if not c:
            raise HTTPException(404, "Challenge not found.")
        p = await db.rf_profiles.find_one({"uid": c["from_uid"]}) or {}
        open_ = c["status"] == "open" and c["expires_ts"] > time.time()
        return page(f"{public_name(p)} challenged you · {label_for(c)}" if open_ else "This challenge has closed",
                    "30 cards · 15 seconds each. Take your seat in the Match Room before the timer runs out." if open_ else "Ask your friend to send a new one from Rapid Fire.",
                    "Open the Match Room", f"{APP_SCHEME}://rapid/room/{cid}", hint="Already in the app? The invitation is waiting on your Rapid Fire screen.")

    return r
