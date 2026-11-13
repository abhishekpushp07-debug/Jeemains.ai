"""Rapid Fire Phase 3 backend: Friend Codes, up to 5 picks, rematch (Badla), watching a live match, weekly leagues and knockout cups.

Uses TEST-prefixed throwaway players with grants written straight into rf_access (no canonical accounts touched)
and removes every document it created.
"""
import asyncio
import hashlib
import os
import re
import secrets
import sys
import time
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
from gamify import ist_week  # noqa: E402
from social import make_pid, remember_identity  # noqa: E402

BASE = "http://localhost:8001/api/rf"
PCM = [{"subject": s} for s in ("Physics", "Chemistry", "Mathematics")]


class Api:
    def __init__(self, s):
        self.s = s

    async def get(self, path, who):
        return await self.s.get(path, headers=who["h"])

    async def post(self, path, who, body=None):
        return await self.s.post(path, json=body or {}, headers=who["h"])

    async def delete(self, path, who):
        return await self.s.delete(path, headers=who["h"])

    async def code(self, who):
        return (await self.get("/friends/code", who)).json()["code"]

    async def befriend(self, a, b):
        r = await self.post("/friends", a, {"code": await self.code(b)})
        assert r.status_code == 200, r.text

    async def match(self, a, b, body=None):
        """A started 1 v 1 between two friends; returns the match id."""
        room = (await self.post("/challenges", a, {"pids": [b["pid"]], **(body or {"subject": "Physics"})})).json()
        return (await self.post(f"/challenges/{room['id']}/accept", b)).json()["duel_id"]


async def _setup(db, tag, n):
    users = {}
    for k in "abcde"[:n]:
        uid = f"TEST-p3-{tag}-{k}"
        token = secrets.token_urlsafe(24)
        await db.rf_access.insert_one({"digest": hashlib.sha256(token.encode()).hexdigest(), "uid": uid, "sid": "", "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10)})
        await remember_identity(db, uid, {"name": f"TESTP3{k.upper()}", "phone": ""})
        users[k] = {"uid": uid, "pid": make_pid(uid), "h": {"Authorization": "Bearer " + token}}
    return users


async def _cleanup(db, users):
    uids = [u["uid"] for u in users.values()]
    await db.rf_access.delete_many({"uid": {"$in": uids}})
    await db.rf_profiles.delete_many({"uid": {"$in": uids}})
    await db.rf_friends.delete_many({"$or": [{"uid": {"$in": uids}}, {"fid": {"$in": uids}}]})
    await db.rf_blocks.delete_many({"$or": [{"uid": {"$in": uids}}, {"bid": {"$in": uids}}]})
    await db.rf_notices.delete_many({"$or": [{"uid": {"$in": uids}}, {"from_uid": {"$in": uids}}]})
    await db.rf_challenges.delete_many({"from_uid": {"$in": uids}})
    await db.rf_gangs.delete_many({"members.by": {"$in": uids}})
    await db.rf_cups.delete_many({"$or": [{"host_uid": {"$in": uids}}, {"players.uid": {"$in": uids}}]})
    await db.rf_duels.delete_many({"players.uid": {"$in": uids}})
    await db.rf_sessions.delete_many({"user_id": {"$in": uids}})
    await db.rf_awards.delete_many({"uid": {"$in": uids}})
    await db.rf_feed.delete_many({"uid": {"$in": uids}})
    await db.rf_learning_events.delete_many({"uid": {"$in": uids}})


def run(body, n=4):
    async def main():
        db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
        tag = uuid.uuid4().hex[:6]
        users = await _setup(db, tag, n)
        try:
            async with httpx.AsyncClient(base_url=BASE, timeout=30) as s:
                await body(db, Api(s), users, tag)
        finally:
            await _cleanup(db, users)
    asyncio.run(main())


# ---------- Friend Code: the only way to become friends ----------
def test_friend_code():
    run(_friend_code)


async def _friend_code(db, api, u, tag):
    a, b, c = u["a"], u["b"], u["c"]
    code_a = await api.code(a)
    assert re.fullmatch(r"[A-HJ-NP-Z2-9]{8}", code_a) and await api.code(a) == code_a
    assert (await api.get(f"/players/{a['pid']}", a)).json()["friend_code"] == code_a
    assert "friend_code" not in (await api.get(f"/players/{a['pid']}", b)).json()  # private to its owner
    assert (await api.post("/friends", b, {"pid": a["pid"]})).status_code == 422  # a player id no longer adds anybody
    assert (await api.get("/players/search?q=TESTP3", b)).status_code == 404  # no search by name or phone number
    seen = (await api.get(f"/friends/code/{code_a}", b)).json()
    assert seen["pid"] == a["pid"] and seen["is_me"] is False and seen["friend"] is False
    # typed in small letters with a dash: still found, and one add makes both players friends
    added = (await api.post("/friends", b, {"code": f"{code_a[:4].lower()}-{code_a[4:].lower()}"})).json()
    assert added["friend"]["pid"] == a["pid"] and added["relation"] == {"friend": True, "follows_you": True, "blocked": False}
    assert [f["pid"] for f in (await api.get("/friends", a)).json()["items"]] == [b["pid"]]
    assert [(n["kind"], n["from"]["pid"]) for n in (await api.get("/inbox", a)).json()["notices"]] == [("friend_added", b["pid"])]
    assert (await api.get(f"/friends/code/{code_a}", b)).json()["friend"] is True
    assert (await api.post("/friends", b, {"code": code_a})).status_code == 200  # adding again changes nothing
    assert await db.rf_friends.count_documents({"uid": {"$in": [a["uid"], b["uid"]]}}) == 2
    assert (await api.post("/friends", a, {"code": code_a})).status_code == 400  # your own code
    assert (await api.post("/friends", a, {"code": "ZZZZ2222"})).status_code == 404
    # removing a friend removes both sides
    assert (await api.delete(f"/friends/{a['pid']}", b)).json()["relation"] == {"friend": False, "follows_you": False, "blocked": False}
    assert (await api.get("/friends", a)).json()["items"] == []
    # a blocked player cannot use the code, and cannot tell that it exists
    await api.post("/blocks", a, {"pid": c["pid"]})
    assert (await api.get(f"/friends/code/{code_a}", c)).status_code == 404
    assert (await api.post("/friends", c, {"code": code_a})).status_code == 404
    assert (await api.s.get(f"/invite/{a['pid']}")).status_code == 404  # the old public "add me" page is gone


# ---------- up to 5 subjects or chapters, and PCM Mixed ----------
def test_picks():
    run(_picks)


async def _picks(db, api, u, tag):
    a, b = u["a"], u["b"]
    cat = (await api.s.get("/catalog", params={"exam": "JEE"})).json()
    chapters = {s["name"]: sorted(s["chapters"], key=lambda c: -c["count"]) for s in cat["subjects"]}
    top = {s: rows[0]["name"] for s, rows in chapters.items()}

    async def sprint(body):
        return await api.post("/sessions", a, {**body, "request_id": uuid.uuid4().hex})

    s = (await sprint({"picks": PCM})).json()
    assert s["label"] == "PCM Mixed" and Counter(c["subject"] for c in s["cards"]) == {"Physics": 10, "Chemistry": 10, "Mathematics": 10}
    two = [{"subject": "Physics", "chapter": top["Physics"]}, {"subject": "Chemistry", "chapter": top["Chemistry"]}]
    s = (await sprint({"picks": two})).json()
    assert s["label"] == f"{top['Physics']} +1 more" and Counter(c["chapter"] for c in s["cards"]) == {top["Physics"]: 15, top["Chemistry"]: 15}
    assert len({c["prompt"] for c in s["cards"]}) == 30
    # a whole subject swallows its own chapters
    s = (await sprint({"picks": [{"subject": "Physics"}, {"subject": "Physics", "chapter": top["Physics"]}]})).json()
    assert s["label"] == "Mixed Physics" and s["picks"] == [{"subject": "Physics", "chapter": None}] and len({c["chapter"] for c in s["cards"]}) > 5
    # a whole subject and one chapter of another share the round half and half
    s = (await sprint({"picks": [{"subject": "Mathematics"}, {"subject": "Chemistry", "chapter": top["Chemistry"]}]})).json()
    assert s["label"] == "Mixed Maths +1 more" and Counter(c["subject"] for c in s["cards"]) == {"Chemistry": 15, "Mathematics": 15}
    assert (await sprint({"picks": [{"subject": "Physics", "chapter": c["name"]} for c in chapters["Physics"][:6]]})).status_code == 422  # 5 at most
    # older apps send one subject and one chapter: unchanged
    s = (await sprint({"subject": "Chemistry", "chapter": top["Chemistry"]})).json()
    assert (s["label"], s["subject"], s["chapter"]) == (top["Chemistry"], "Chemistry", top["Chemistry"]) and {c["chapter"] for c in s["cards"]} == {top["Chemistry"]}

    duel = (await api.post("/duels", a, {"picks": two, "mode": "invite", "name": "x", "exam": "JEE", "request_id": uuid.uuid4().hex})).json()
    assert duel["label"] == f"{top['Physics']} +1 more" and duel["picks"] == two and duel["status"] == "waiting"
    await api.post(f"/duels/{duel['id']}/cancel", a)

    await api.befriend(a, b)
    room = (await api.post("/challenges", a, {"pids": [b["pid"]], "picks": PCM})).json()
    assert room["label"] == "PCM Mixed" and len(room["picks"]) == 3 and room["revenge"] is False
    assert (await api.get("/inbox", b)).json()["challenges"][0]["label"] == "PCM Mixed"
    page = await api.s.get(f"/c/{room['id']}")
    assert page.status_code == 200 and "PCM Mixed" in page.text and "Search" not in page.text
    did = (await api.post(f"/challenges/{room['id']}/accept", b)).json()["duel_id"]
    duel = (await api.get(f"/duels/{did}", b)).json()
    assert duel["label"] == "PCM Mixed" and duel["total"] == 30 and Counter(c["subject"] for c in duel["cards"]) == {"Physics": 10, "Chemistry": 10, "Mathematics": 10}


# ---------- Badla: the player who lost a 1 v 1 calls the same match again ----------
def test_rematch_revenge():
    run(_revenge)


async def _revenge(db, api, u, tag):
    a, b, c, d = u["a"], u["b"], u["c"], u["d"]
    await api.befriend(a, b)
    did = await api.match(a, b, {"picks": PCM})
    await db.rf_duels.update_one({"id": did}, {"$set": {"status": "finished", "winner": b["uid"], "finished_ts": time.time()}})
    last = (await api.get(f"/players/{b['pid']}", a)).json()["head_to_head"]
    assert last == {"you": 0, "them": 1, "played": 1, "last": {"id": did, "won": False, "tie": False, "picks": [{**p, "chapter": None} for p in PCM]}}
    h2h = (await api.get(f"/players/{b['pid']}/h2h", a)).json()["items"]
    assert h2h[0]["id"] == did and [p["subject"] for p in h2h[0]["picks"]] == ["Physics", "Chemistry", "Mathematics"]
    # Badla lo: the loser picks a new battleground first; the challenge still goes to the same friend
    room = (await api.post("/challenges", a, {"rematch_of": did, "picks": [{"subject": "Chemistry", "chapter": None}]})).json()
    assert room["revenge"] is True and room["label"] == "Mixed Chemistry" and room["rematch_of"] == did and room["single"]
    await api.post(f"/challenges/{room['id']}/cancel", a, {})
    room = (await api.post("/challenges", a, {"rematch_of": did})).json()
    assert room["revenge"] is True and room["label"] == "PCM Mixed" and room["rematch_of"] == did and room["single"]
    assert (await api.get("/inbox", b)).json()["challenges"][0]["revenge"] is True
    # the winner pressing rematch takes the seat in the same room and the match starts
    taken = (await api.post("/challenges", b, {"rematch_of": did})).json()
    assert taken["id"] == room["id"] and taken["status"] == "started" and taken["duel_id"] != did
    # a winner who opens the rematch first is not on a revenge
    await db.rf_duels.update_one({"id": taken["duel_id"]}, {"$set": {"status": "finished", "winner": a["uid"], "finished_ts": time.time()}})
    assert (await api.post("/challenges", a, {"rematch_of": taken["duel_id"]})).json()["revenge"] is False
    # strangers from a quick match cannot be called back until they are friends
    stranger = "p3-" + uuid.uuid4().hex
    seat = lambda who: {"uid": who["uid"], "pid": who["pid"], "name": "x", "score": 1, "ms": 1, "answers": [], "done": True}  # noqa: E731
    await db.rf_duels.insert_one({"id": stranger, "exam": "JEE", "mode": "random", "subject": "Physics", "status": "finished", "winner": d["uid"], "finished_ts": time.time(), "card_ids": [], "players": [seat(c), seat(d)]})
    r = await api.post("/challenges", c, {"rematch_of": stranger})
    assert r.status_code == 403 and "Friend Code" in r.json()["detail"]
    await api.befriend(c, d)
    assert (await api.post("/challenges", c, {"rematch_of": stranger})).json()["revenge"] is True


# ---------- watching a live match ----------
def test_watch_live():
    run(_watch, n=5)


async def _watch(db, api, u, tag):
    a, b, c, d, e = u["a"], u["b"], u["c"], u["d"], u["e"]
    await api.befriend(a, b)
    await api.befriend(c, a)
    batch = (await api.post("/gangs", a, {"name": f"TESTP3 Batch {tag}", "emblem": "rocket", "kind": "batch"})).json()["id"]
    link = (await api.get(f"/gangs/{batch}", a)).json()["invite_code"]
    assert (await api.post(f"/gangs/{batch}/join", e, {"code": link})).status_code == 200
    did = await api.match(a, b)
    live = (await api.get("/duels/live", c)).json()["items"]
    assert [m["id"] for m in live] == [did] and live[0]["label"] == "Mixed Physics" and live[0]["total"] == 30 and len(live[0]["players"]) == 2 and live[0]["cup"] is False
    assert [m["id"] for m in (await api.get("/duels/live", e)).json()["items"]] == [did]  # a gang mate
    assert (await api.get("/duels/live", d)).json()["items"] == [] and (await api.get("/duels/live", a)).json()["items"] == []
    w = (await api.get(f"/duels/{did}/watch", c)).json()
    assert w["spectator"] is True and "cards" not in w and w["status"] == "ready" and w["total"] == 30
    assert [(p["score"], p["answered"], p["streak"], p["trail"]) for p in w["players"]] == [(0, 0, 0, [])] * 2 and {p["pid"] for p in w["players"]} == {a["pid"], b["pid"]}
    assert (await api.get(f"/duels/{did}/watch", e)).status_code == 200
    assert (await api.get(f"/duels/{did}/watch", d)).status_code == 404  # a stranger
    assert (await api.get(f"/duels/{did}", c)).status_code == 404  # a spectator never gets the cards
    assert (await api.get(f"/duels/{did}", a)).json()["watchers"] == 2
    # the result stays open to the same people
    await db.rf_duels.update_one({"id": did}, {"$set": {"ends_at": time.time() - 1}})
    done = (await api.get(f"/duels/{did}/watch", c)).json()
    assert done["status"] == "finished" and done["tie"] is True
    assert (await api.get("/duels/live", c)).json()["items"] == []


# ---------- a gang is a circle of friends; a batch is open to anyone with its link ----------
def test_gang_links():
    run(_gang_links)


async def _gang_links(db, api, u, tag):
    a, b, c = u["a"], u["b"], u["c"]
    gang = (await api.post("/gangs", a, {"name": f"TESTP3 Gang {tag}", "emblem": "lion"})).json()["id"]
    detail = (await api.get(f"/gangs/{gang}", a)).json()
    assert detail["kind"] == "gang" and detail["max"] == 20 and "league" not in detail
    r = await api.post(f"/gangs/{gang}/join", b, {"code": detail["invite_code"]})
    assert r.status_code == 403 and "Friend Code" in r.json()["detail"]
    await api.befriend(b, a)
    assert (await api.post(f"/gangs/{gang}/join", b, {"code": detail["invite_code"]})).status_code == 200
    batch = (await api.post("/gangs", a, {"name": f"TESTP3 Batch {tag}", "emblem": "rocket", "kind": "batch"})).json()["id"]
    detail = (await api.get(f"/gangs/{batch}", a)).json()
    assert detail["kind"] == "batch" and detail["max"] == 200
    assert (await api.post(f"/gangs/{batch}/join", c, {"code": detail["invite_code"]})).status_code == 200
    assert {g["id"]: g["kind"] for g in (await api.get("/gangs", a)).json()["items"]} == {gang: "gang", batch: "batch"}


# ---------- weekly leagues ----------
def test_leagues():
    run(_leagues)


async def _leagues(db, api, u, tag):
    a, b, c, d = u["a"], u["b"], u["c"], u["d"]
    await api.befriend(a, b)
    await api.befriend(a, c)
    week, last = ist_week(), ist_week(time.time() - 7 * 86400)
    lg = (await api.get("/league/friends", a)).json()
    assert lg["week"] == week and 0 < lg["ends_in"] <= 7 * 86400 and lg["friends"] == 2 and len(lg["items"]) == 3 and len(lg["all_time"]) == 3
    assert lg["prizes"] == [150, 100, 50] and lg["last"]["can_claim"] is False
    assert (await api.post("/league/friends/claim", a)).status_code == 409
    assert (await api.get("/league/friends", d)).json()["friends"] == 0
    # last week: b 500 XP, a 300, c 100. a finished 2nd of 3 and collects 100 coins, once.
    for who, xp in ((a, 300), (b, 500), (c, 100)):
        await db.rf_profiles.update_one({"uid": who["uid"]}, {"$set": {"week_stats": {"week": last, "xp": xp, "wins": 1, "correct": 5, "matches": 1}, "coins": 0}})
    lg = (await api.get("/league/friends", a)).json()
    assert [(x["pid"], x["xp"], x["rank"]) for x in lg["last"]["items"]] == [(b["pid"], 500, 1), (a["pid"], 300, 2), (c["pid"], 100, 3)]
    assert (lg["last"]["rank"], lg["last"]["prize"], lg["last"]["can_claim"]) == (2, 100, True)
    assert all(x["xp"] == 0 for x in lg["items"])  # the new week starts from zero
    assert (await api.post("/league/friends/claim", a)).json() == {"coins": 100, "coins_total": 100}
    assert (await api.post("/league/friends/claim", a)).status_code == 409
    assert (await api.get("/league/friends", a)).json()["last"]["claimed"] is True

    # Gang War board: a Gang War that ends level adds a tie to both gangs, and both players join the top-100 scorers board
    g1 = (await api.post("/gangs", a, {"name": f"TESTP3 Lions {tag}", "emblem": "lion"})).json()["id"]
    g2 = (await api.post("/gangs", d, {"name": f"TESTP3 Wolves {tag}", "emblem": "wolf"})).json()["id"]
    room = (await api.post("/challenges", a, {"gang_id": g1, "rival_gang_id": g2})).json()
    assert room["team_mode"] is True
    did = (await api.post(f"/challenges/{room['id']}/accept", d)).json()["duel_id"]
    await db.rf_duels.update_one({"id": did, "players.uid": d["uid"]}, {"$set": {"players.$.score": 4}})
    await db.rf_duels.update_one({"id": did}, {"$set": {"ends_at": time.time() - 1}})
    assert (await api.get(f"/duels/{did}", a)).json()["winner"] == "team:b"
    detail = (await api.get(f"/gangs/{g1}", a)).json()
    assert "league" not in detail and detail["record"] == {"wins": 0, "losses": 1, "ties": 0}
    assert (await api.get(f"/gangs/{g2}", d)).json()["record"] == {"wins": 1, "losses": 0, "ties": 0}
    await asyncio.sleep(21)  # the top-100 list is cached for 20 s
    board = (await api.get("/league/gangwar", d)).json()
    assert board["size"] == 100 and len(board["items"]) <= 100
    rows = {x["pid"]: x for x in board["items"]}
    assert (rows[d["pid"]]["score"], rows[d["pid"]]["wins"], rows[d["pid"]]["matches"], rows[d["pid"]]["you"]) == (4, 1, 1, True)
    assert board["you"]["score"] == 4 and board["you"]["rank"] == rows[d["pid"]]["rank"]
    assert rows[a["pid"]]["wins"] == 0 and (await api.get("/league/gangwar", b)).json()["you"] is None  # b never played a Gang War
    assert (await api.get("/league/gangs", a)).status_code in (404, 405)  # the weekly gang table is gone
    # playing this week moved last week's totals aside; the finished league still reads them
    mine = await db.rf_profiles.find_one({"uid": a["uid"]})
    assert mine["week_stats"]["week"] == week and mine["last_week"]["xp"] == 300
    assert (await api.get("/league/friends", a)).json()["last"]["rank"] == 2


# ---------- knockout cups ----------
def test_cups():
    run(_cups)


async def _win(db, api, did, winner):
    """Finish a cup match at once with `winner` on a perfect score (answering card by card is covered by the match tests)."""
    total = len((await db.rf_duels.find_one({"id": did}))["card_ids"])
    answers = [{"i": i, "choice": 0, "outcome": "correct", "ms": 1000} for i in range(total)]
    await db.rf_duels.update_one({"id": did, "players.uid": winner["uid"]}, {"$set": {"players.$.answers": answers, "players.$.score": total, "players.$.ms": total * 1000}})
    await db.rf_duels.update_one({"id": did}, {"$set": {"players.$[h].done": True}}, array_filters=[{"h.bot": {"$ne": True}}])
    return (await api.get(f"/duels/{did}", winner)).json()


async def _cups(db, api, u, tag):
    a, b, c, d = u["a"], u["b"], u["c"], u["d"]
    picks = [{"subject": "Physics"}, {"subject": "Chemistry"}]
    # Open Cup: anyone joins the cup that is filling for the same subjects
    cup = (await api.post("/cups", a, {"kind": "open", "picks": picks})).json()
    cid = cup["id"]
    assert (cup["status"], cup["size"], cup["cards"], cup["label"], cup["joined"], cup["is_host"], len(cup["players"])) == ("open", 4, 15, "Mixed Physics + Chemistry", True, True, 1)
    same = (await api.post("/cups", b, {"kind": "open", "picks": picks})).json()
    assert same["id"] == cid and len(same["players"]) == 2 and same["is_host"] is False
    assert (await api.post("/cups", a, {"kind": "open", "picks": [{"subject": "Mathematics"}]})).json()["id"] == cid  # one cup at a time
    assert (await api.get("/inbox", a)).json()["cup"] == cid
    assert (await api.get(f"/cups/{cid}", d)).status_code == 404  # a stranger cannot look in
    # the lobby closes: practice rivals take the empty seats and the semi-finals are seated
    await db.rf_cups.update_one({"id": cid}, {"$set": {"expires_ts": time.time() - 1}})
    cup = (await api.get(f"/cups/{cid}", a)).json()
    assert cup["status"] == "live" and len(cup["players"]) == 4 and sum(p["bot"] for p in cup["players"]) == 2 and cup["round"] == 0
    assert cup["rounds"][0]["name"] == "Semi-finals" and len(cup["rounds"][0]["matches"]) == 2 and cup["my_duel"]
    duel = (await api.get(f"/duels/{cup['my_duel']}", a)).json()
    assert (duel["cup_id"], duel["mode"], duel["total"], duel["status"], len(duel["cards"])) == (cid, "cup", 15, "ready", 15)
    assert (await api.get(f"/duels/{cup['my_duel']}/watch", b)).status_code == 200  # everybody in the cup may watch its matches
    assert (await api.get(f"/duels/{cup['my_duel']}/watch", c)).status_code == 404
    # a wins every match; b leaves theirs
    for _ in range(6):
        cup = (await api.get(f"/cups/{cid}", a)).json()
        if cup["status"] != "live":
            break
        if cup["my_duel"]:
            await _win(db, api, cup["my_duel"], a)
        other = (await api.get(f"/cups/{cid}", b)).json()
        if other["status"] == "live" and other["my_duel"]:
            await api.post(f"/duels/{other['my_duel']}/forfeit", b)
    cup = (await api.get(f"/cups/{cid}", a)).json()
    assert cup["status"] == "finished" and cup["players"][cup["champion"]]["you"] and cup["prize"] == 70 and [r["name"] for r in cup["rounds"]] == ["Semi-finals", "Final"]
    assert all(m["winner"] is not None and m["score"] for r in cup["rounds"] for m in r["matches"])
    assert next(p for p in (await api.get(f"/cups/{cid}", b)).json()["players"] if p["you"])["out"] is True
    prof = await db.rf_profiles.find_one({"uid": a["uid"]})
    assert prof["cups_won"] == 1 and "cup_champion" in prof["badges"] and prof["coins"] >= 70
    assert (await api.get("/inbox", a)).json()["cup"] is None
    assert any(m["cup"] for m in (await api.get("/duels?exam=JEE", a)).json()["items"])

    # Watch code: anybody with it can follow the cup and its live matches, up to 100 people
    look = (await db.rf_cups.find_one({"id": cid}))
    assert re.fullmatch(r"[A-HJ-NP-Z2-9]{6}", look["code"])
    assert (await api.post("/cups/watch", d, {"code": "ZZZZZZ"})).status_code == 404
    seen = (await api.post("/cups/watch", d, {"code": look["code"].lower()})).json()
    assert seen["spectating"] is True and seen["joined"] is False and seen["spectators"] == 1 and seen["code"] == look["code"]
    assert (await api.get(f"/cups/{cid}", d)).status_code == 200
    assert (await api.post("/cups/watch", d, {"code": look["code"]})).json()["spectators"] == 1  # once per person
    await db.rf_cups.update_one({"id": cid}, {"$set": {"spectators": [d["uid"]] + [f"TEST-x{i}" for i in range(99)]}})
    assert (await api.post("/cups/watch", c, {"code": look["code"]})).status_code == 409
    assert (await api.get("/cups", a)).json()["items"][0]["id"] == cid

    # 16 seats: an Open Cup of 16 fills with practice rivals and starts at the Round of 16
    big = (await api.post("/cups", d, {"kind": "open", "size": 16, "picks": [{"subject": "Mathematics"}]})).json()
    assert big["size"] == 16 and big["status"] == "open"
    await db.rf_cups.update_one({"id": big["id"]}, {"$set": {"expires_ts": time.time() - 1}})
    big = (await api.get(f"/cups/{big['id']}", d)).json()
    assert big["status"] == "live" and len(big["players"]) == 16 and big["rounds"][0]["name"] == "Round of 16" and len(big["rounds"][0]["matches"]) == 8
    await api.post(f"/duels/{big['my_duel']}/forfeit", d)
    assert next(p for p in (await api.get(f"/cups/{big['id']}", d)).json()["players"] if p["you"])["out"] is True

    # Friends Cup: only invited friends, the host starts it
    await api.befriend(a, b)
    await api.befriend(a, c)
    assert (await api.post("/cups", a, {"kind": "private", "size": 4, "pids": [d["pid"]]})).status_code == 403  # not a friend
    assert (await api.post("/cups", a, {"kind": "private", "size": 4})).status_code == 400
    cup = (await api.post("/cups", a, {"kind": "private", "size": 4, "pids": [b["pid"], c["pid"]]})).json()
    cid = cup["id"]
    assert cup["kind"] == "private" and cup["label"] == "Mixed Physics" and cup["can_start"] is False and cup["expires_in"] > 290
    assert [(n["id"], n["from"]["pid"], n["joined"], n["size"]) for n in (await api.get("/inbox", b)).json()["cups"]] == [(cid, a["pid"], 1, 4)]
    look = (await api.get(f"/cups/{cid}", c)).json()
    assert look["invited"] is True and look["joined"] is False
    assert (await api.post(f"/cups/{cid}/join", d)).status_code == 404
    assert (await api.post(f"/cups/{cid}/start", a)).status_code == 409  # nobody has joined yet
    joined = (await api.post(f"/cups/{cid}/join", b)).json()
    assert joined["joined"] is True and len(joined["players"]) == 2 and (await api.get("/inbox", b)).json()["cups"] == []
    assert (await api.post(f"/cups/{cid}/start", b)).status_code == 403
    live = (await api.post(f"/cups/{cid}/start", a)).json()
    assert live["status"] == "live" and len(live["players"]) == 2 and [r["name"] for r in live["rounds"]] == ["Final"] and not any(p["bot"] for p in live["players"])
    assert (await api.post(f"/cups/{cid}/join", c)).status_code == 409  # already started
    assert (await api.post(f"/cups/{cid}/leave", a)).status_code == 409
    await _win(db, api, live["my_duel"], b)
    done = (await api.get(f"/cups/{cid}", b)).json()
    assert done["status"] == "finished" and done["players"][done["champion"]]["you"] and done["prize"] == 70
    assert (await api.get(f"/cups/{cid}", a)).json()["prize"] == 0

    # the host leaving a Friends Cup before it starts closes it
    cup = (await api.post("/cups", c, {"kind": "private", "size": 8, "pids": [a["pid"]]})).json()
    assert cup["size"] == 8 and (await api.post(f"/cups/{cup['id']}/leave", c)).json() == {"ok": True}
    assert (await db.rf_cups.find_one({"id": cup["id"]}))["status"] == "cancelled"
    assert (await api.get("/inbox", a)).json()["cups"] == []


if __name__ == "__main__":
    pytest.main([__file__, "-q", "-o", "addopts="])
