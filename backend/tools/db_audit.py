"""Database audit at crowd scale: what every Rapid Fire call really asks the database.

The real app runs inside this process (no server, no network) against the SCRATCH database only (60,000 practice
players made for the audit). MongoDB's own profiler then tells, for every call, how many database trips it made and
whether each one read only the rows it needed (IXSCAN) or the whole collection (COLLSCAN).

    python tools/db_audit.py startup            # how long a server start takes: new code version, then a plain restart
    python tools/db_audit.py queries            # every screen and every play flow, flagged reads only
    python tools/db_audit.py queries --all      # ... with every database trip listed
    python tools/db_audit.py check              # the short cuts (ranks, weak lists) answer exactly what the full counts did

Nothing here ever touches the live database: the script refuses to run on any other name than the scratch one.
"""
import argparse
import asyncio
import hashlib
import os
import re
import secrets
import sys
import time
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRATCH = "rf_audit_scratch"
os.environ["DB_NAME"] = SCRATCH
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx  # noqa: E402
from pymongo import MongoClient  # noqa: E402

import logging  # noqa: E402

import server  # noqa: E402

logging.getLogger("httpx").setLevel(logging.WARNING)

assert server.db.name == SCRATCH, "the audit only ever runs on the scratch database"
raw = MongoClient(os.environ["MONGO_URL"])[SCRATCH]
profile = raw["system.profile"]
PCM = [{"subject": s, "chapter": None} for s in ("Physics", "Chemistry", "Mathematics")]
SKIP_COMMANDS = ("createIndexes", "listIndexes", "listCollections", "profile", "collStats", "dbStats", "hello", "ping", "endSessions", "create")


def keys(q) -> str:
    out = []
    for k, v in (q or {}).items():
        if k in ("$or", "$and", "$nor"):
            out.append(k + "[" + " | ".join(keys(x) for x in v) + "]")
        elif isinstance(v, dict) and v and all(str(x).startswith("$") for x in v):
            out.append(k + ":" + "".join(v))
        else:
            out.append(k)
    return "{" + ", ".join(out) + "}"


def describe(op: dict):
    """(collection, one-line shape) of a profiled operation, or None for housekeeping."""
    c, coll = op.get("command") or {}, op["ns"].split(".", 1)[1]
    if op["op"] == "getmore":
        c = op.get("originatingCommand") or c
        prefix = "getmore of "
    else:
        prefix = ""
    if coll.startswith("system.") or any(k in c for k in SKIP_COMMANDS) or op["op"] == "insert":
        return None
    if "find" in c:
        tail = (" sort=" + keys(c["sort"]) if c.get("sort") else "") + (f" limit={c['limit']}" if c.get("limit") else "")
        return coll, f"{prefix}find {keys(c.get('filter'))}{tail}"
    if "aggregate" in c:
        stages = c.get("pipeline") or []
        first = keys(stages[0]["$match"]) if stages and "$match" in stages[0] else ""
        return coll, f"{prefix}aggregate {first} " + ">".join(next(iter(s)) for s in stages)
    if "count" in c:
        return coll, f"count {keys(c.get('query'))}"
    if "distinct" in c:
        return coll, f"distinct {c['distinct'] if False else c.get('key')} {keys(c.get('query'))}"
    if "findAndModify" in c or "findandmodify" in c:
        return coll, f"findAndModify {keys(c.get('query'))}" + (" sort=" + keys(c["sort"]) if c.get("sort") else "")
    if op["op"] == "update":
        return coll, f"update {keys(c.get('q'))}" + (" multi" if c.get("multi") else "")
    if op["op"] == "remove":
        return coll, f"delete {keys(c.get('q'))}"
    return None


def flags(op: dict, coll: str, sizes: dict) -> list:
    out, plan = [], op.get("planSummary", "")
    docs, keyn, got = op.get("docsExamined", 0), op.get("keysExamined", 0), max(op.get("nreturned", 0), op.get("nMatched", 0), 1)
    if "COLLSCAN" in plan and sizes.get(coll, 0) > 500:
        out.append("COLLSCAN")
    if docs > 100 and docs > 10 * got:
        out.append(f"reads {docs} rows for {got}")
    if keyn > 2000 and keyn > 10 * got:
        out.append(f"walks {keyn} index keys for {got}")
    if op.get("hasSortStage") and docs > 200:
        out.append(f"sorts {docs} rows in memory")
    if op.get("millis", 0) >= 20 and docs + keyn > 100:  # a slow first touch of a cold page is not a query problem
        out.append(f"{op['millis']} ms")
    return out


class Audit:
    def __init__(self, show_all: bool):
        self.show_all, self.sizes = show_all, {n: raw[n].estimated_document_count() for n in raw.list_collection_names()}
        self.found = defaultdict(lambda: {"n": 0, "where": set(), "worst": {}})
        self.calls = []
        self.mark = None

    def start(self):
        last = list(profile.find({}, {"ts": 1}).sort("$natural", -1).limit(1))
        self.mark = last[0]["ts"] if last else datetime(2000, 1, 1)
        time.sleep(0.003)

    def collect(self, label: str, wall_ms: float, status=""):
        time.sleep(0.003)
        ops = [op for op in profile.find({"ts": {"$gt": self.mark}}).sort("$natural", 1) if describe(op)]
        bad = []
        for op in ops:
            coll, text = describe(op)
            why = flags(op, coll, self.sizes)
            if why:
                bad.append((coll, text, why, op))
                row = self.found[(coll, text)]
                row["n"] += 1
                row["where"].add(label)
                if op.get("docsExamined", 0) + op.get("keysExamined", 0) >= row["worst"].get("docsExamined", 0) + row["worst"].get("keysExamined", 0):
                    row["worst"] = op
                row["why"] = why
        self.calls.append((label, status, wall_ms, len(ops), len(bad)))
        print(f"{label:46s} {str(status):>4s} {wall_ms:8.1f} ms  db trips {len(ops):3d}" + (f"  FLAGGED {len(bad)}" if bad else ""))
        for op in ops if self.show_all else [b[3] for b in bad]:
            coll, text = describe(op)
            why = flags(op, coll, self.sizes)
            print(f"      {'!!' if why else '  '} {coll}: {text}  [{op.get('planSummary', '-')}] keys {op.get('keysExamined', 0)} rows {op.get('docsExamined', 0)} "
                  f"out {op.get('nreturned', op.get('nMatched', 0))} {op.get('millis', 0)} ms" + ("  <- " + "; ".join(why) if why else ""))

    def summary(self):
        print("\n" + "=" * 100 + f"\n{len(self.calls)} calls, {sum(c[3] for c in self.calls)} database trips, {len(self.found)} flagged query shapes\n")
        for (coll, text), row in sorted(self.found.items(), key=lambda kv: -(kv[1]["worst"].get("docsExamined", 0) + kv[1]["worst"].get("keysExamined", 0))):
            w = row["worst"]
            print(f"- {coll} ({self.sizes.get(coll, 0)} rows): {text}\n    plan {w.get('planSummary', '-')}, keys {w.get('keysExamined', 0)}, rows {w.get('docsExamined', 0)}, "
                  f"out {w.get('nreturned', w.get('nMatched', 0))}, {w.get('millis', 0)} ms  <- {'; '.join(row['why'])}\n    seen {row['n']}x in: {', '.join(sorted(row['where'])[:6])}")
        heavy = sorted(self.calls, key=lambda c: -c[3])[:12]
        print("\nMost database trips per call: " + ", ".join(f"{c[0].strip()} ({c[3]})" for c in heavy))
        slow = sorted(self.calls, key=lambda c: -c[2])[:12]
        print("Slowest calls (in-process, ms): " + ", ".join(f"{c[0].strip()} ({c[2]:.0f})" for c in slow))


def grant(uid: str) -> dict:
    token = secrets.token_urlsafe(32)
    raw.rf_access.insert_one({"digest": hashlib.sha256(token.encode()).hexdigest(), "uid": uid, "sid": "", "expires_at": datetime.now(timezone.utc) + timedelta(hours=1)})
    return {"Authorization": "Bearer " + token}


async def run_queries(show_all: bool):
    audit = Audit(show_all)
    await server.db.command("profile", 2)
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=server.app), base_url="http://audit/api/rf", timeout=120)
    heavy, plain, friend = "audit-heavy-0001", "audit-p-000000", "audit-p-000001"
    tag = uuid.uuid4().hex[:8]
    new_a, new_b = f"audit-new-{tag}-a", f"audit-new-{tag}-b"
    who = {u: grant(u) for u in (heavy, plain, friend, new_a, new_b)}
    pid = {p["uid"]: p.get("pid") for p in raw.rf_profiles.find({"uid": {"$in": [heavy, plain, friend, "audit-p-000002"]}}, {"uid": 1, "pid": 1})}
    gang = raw.rf_gangs.find_one({"members.uid": plain}, {"id": 1}) or {}
    cup = raw.rf_cups.find_one({"players.uid": plain}, {"id": 1, "code": 1}) or raw.rf_cups.find_one({}, {"id": 1, "code": 1}) or {}
    coded = raw.rf_cups.find_one({"code": {"$type": "string"}}, {"code": 1}) or {}
    duel = raw.rf_duels.find_one({"players.uid": heavy, "status": "finished"}, {"id": 1}) or {}
    yesterday = (datetime.now(timezone(timedelta(hours=5, minutes=30))) - timedelta(days=1)).strftime("%Y-%m-%d")

    async def call(uid, method, path, body=None, label=None):
        audit.start()
        t = time.perf_counter()
        r = await client.request(method, path, json=body, headers=who[uid])
        audit.collect(label or f"{method} {path.split('?')[0][:38]}", (time.perf_counter() - t) * 1000, r.status_code)
        try:
            return r.json() if r.status_code < 400 else None
        except ValueError:
            return None

    async def background(label, fn):
        audit.start()
        t = time.perf_counter()
        await fn()
        audit.collect(label, (time.perf_counter() - t) * 1000)

    print(f"--- screens, as a player with a long history ({heavy}) ---")
    for path in ("/profile", "/catalog?exam=JEE", "/inbox", "/daily?exam=JEE", "/daily/board?exam=JEE", f"/daily/board?exam=JEE&day={yesterday}", "/cups", "/cups/night",
                 "/cups/champions", "/duels?exam=JEE", "/duels?exam=JEE&friends_only=true", "/duels/live", "/feed", "/friends", "/friends/code", "/gangs", "/gangs/search?q=Gang",
                 "/history?exam=JEE", "/leaderboard?exam=JEE", "/league/friends", "/league/gangwar", "/mission/me", "/badla", "/revision?exam=JEE", "/weak-topics?exam=JEE",
                 "/shop", "/squads", "/dream", f"/players/{pid.get(plain)}", f"/players/{pid.get(plain)}/h2h", f"/players/{pid.get(heavy)}", "/cards?subject=Physics&exam=JEE",
                 f"/duels/{duel.get('id')}", f"/cups/{cup.get('id')}"):
        await call(heavy, "GET", path)
    print(f"\n--- the same screens as an ordinary player ({plain}) ---")
    for path in ("/profile", "/inbox", "/daily?exam=JEE", f"/daily/board?exam=JEE&day={yesterday}", "/cups", "/cups/night", "/duels?exam=JEE", "/duels/live", "/feed", "/friends", "/gangs",
                 f"/gangs/{gang.get('id')}", "/history?exam=JEE", "/leaderboard?exam=JEE", "/league/friends", "/league/gangwar", "/badla", "/revision?exam=JEE", "/weak-topics?exam=JEE",
                 f"/players/{pid.get(heavy)}", f"/players/{pid.get(heavy)}/h2h", f"/cups/{cup.get('id')}"):
        await call(plain, "GET", path)

    print("\n--- a brand-new player opens the app ---")
    for path in ("/profile", "/inbox", "/daily?exam=JEE", "/cups", "/cups/night", "/leaderboard?exam=JEE", "/league/gangwar", "/friends", "/gangs", "/history?exam=JEE", "/weak-topics?exam=JEE"):
        await call(new_a, "GET", path)

    print("\n--- solo sprint ---")
    for uid in (heavy, new_a):
        s = await call(uid, "POST", "/sessions", {"picks": PCM, "count": 30, "request_id": uuid.uuid4().hex, "exam": "JEE"})
        if s:
            await call(uid, "GET", f"/sessions/{s['id']}")
            results = [{"card_id": c["id"], "outcome": "incorrect", "choice": (k % 4), "ms": 1500} for k, c in enumerate(s["cards"])]
            await call(uid, "POST", f"/sessions/{s['id']}/complete", {"results": results})
            await call(uid, "POST", f"/sessions/{s['id']}/complete", {"results": results}, label="POST /sessions/{sid}/complete (repeat)")
    await call(heavy, "POST", "/sessions", {"weak_topics": True, "count": 30, "request_id": uuid.uuid4().hex, "exam": "JEE"}, label="POST /sessions (weak topics)")
    await call(heavy, "POST", "/sessions", {"revision": True, "subject": "Physics", "request_id": uuid.uuid4().hex, "exam": "JEE"}, label="POST /sessions (revision)")
    await call(heavy, "GET", "/history?exam=JEE")

    print("\n--- match against a Practice Rival (30 cards) ---")
    d = await call(heavy, "POST", "/duels", {"picks": PCM, "mode": "invite", "name": "Audit", "request_id": uuid.uuid4().hex, "exam": "JEE"})
    if d:
        d = await call(heavy, "POST", f"/duels/{d['id']}/bot", {}) or d
        await call(heavy, "GET", f"/duels/{d['id']}")
        await call(plain, "GET", f"/duels/{d['id']}/watch")
        await asyncio.sleep(max(0.0, d.get("start_at", 0) - d.get("server_now", 0)) + 0.3)
        for k in range(d.get("total", 30)):
            res = await call(heavy, "POST", f"/duels/{d['id']}/answer", {"index": k, "choice": k % 4, "outcome": "answer", "ms": 1200},
                             label="POST /duels/{did}/answer" + (" (first)" if k == 0 else " (last)" if k == d.get("total", 30) - 1 else ""))
            if res is None:
                break
            await asyncio.sleep(0.05)
        await call(heavy, "GET", f"/duels/{d['id']}", label="GET /duels/{did} (finished)")

    print("\n--- quick match: two students meet ---")
    a = await call(new_a, "POST", "/duels", {"picks": PCM, "mode": "random", "name": "New A", "request_id": uuid.uuid4().hex, "exam": "JEE"}, label="POST /duels (quick, waits)")
    b = await call(new_b, "POST", "/duels", {"picks": PCM, "mode": "random", "name": "New B", "request_id": uuid.uuid4().hex, "exam": "JEE"}, label="POST /duels (quick, pairs)")
    if a and b:
        await call(new_a, "GET", f"/duels/{a['id']}")
        await call(new_a, "GET", "/duels/live")
        await call(new_a, "POST", f"/duels/{a['id']}/forfeit", {})
        await call(new_b, "POST", f"/duels/{b['id']}/forfeit", {})
    inv = await call(new_a, "POST", "/duels", {"picks": PCM, "mode": "invite", "name": "New A", "request_id": uuid.uuid4().hex, "exam": "JEE"}, label="POST /duels (invite)")
    if inv and inv.get("code"):
        await call(new_b, "POST", "/duels/join", {"code": inv["code"], "name": "New B", "exam": "JEE"})
        await call(new_a, "POST", f"/duels/{inv['id']}/forfeit", {})
        await call(new_b, "POST", f"/duels/{inv['id']}/forfeit", {})
    await call(new_a, "POST", "/duels", {"picks": PCM, "mode": "invite", "name": "New A", "request_id": uuid.uuid4().hex, "exam": "JEE"}, label="POST /duels (invite, then cancel)")

    print("\n--- All India Rapid (today's round) ---")
    st = await call(new_a, "POST", "/daily/start", {"exam": "JEE"})
    if st and st.get("status") == "playing":
        await asyncio.sleep(st.get("show_in_ms", 3000) / 1000 + 0.2)
        for k in range(3):
            res = await call(new_a, "POST", "/daily/answer", {"exam": "JEE", "i": st["i"] + k, "choice": k % 4})
            if not res or res.get("status") != "playing":
                break
            await asyncio.sleep(res.get("show_in_ms", 2400) / 1000 + 0.1)
        await call(new_a, "POST", "/daily/finish", {"exam": "JEE"})
        await call(new_a, "GET", "/daily?exam=JEE", label="GET /daily (after playing)")
        await call(new_a, "GET", "/daily/board?exam=JEE", label="GET /daily/board (after playing)")

    print("\n--- Knockout Cup, Cup Night, challenges, friends, gangs, rewards ---")
    c = await call(new_a, "POST", "/cups", {"kind": "open", "size": 4, "picks": PCM})
    if c:
        await call(new_a, "GET", f"/cups/{c['id']}")
        await call(new_b, "POST", f"/cups/{c['id']}/join", {})
        await call(new_a, "GET", "/cups", label="GET /cups (in a cup)")
        await call(new_a, "GET", "/inbox", label="GET /inbox (in a cup)")
        await call(new_b, "POST", f"/cups/{c['id']}/leave", {})
        await call(new_a, "POST", f"/cups/{c['id']}/leave", {})
    if coded.get("code"):
        await call(new_a, "POST", "/cups/watch", {"code": coded["code"]})
    await call(new_a, "POST", "/cups/night/join", {})
    await call(new_a, "GET", "/cups/night", label="GET /cups/night (seated)")
    await call(new_a, "POST", "/cups/night/leave", {})
    code = await call(new_b, "GET", "/friends/code")
    if code and code.get("code"):
        await call(new_a, "GET", f"/friends/code/{code['code']}")
        await call(new_a, "POST", "/friends", {"code": code["code"]})
    me_b = raw.rf_profiles.find_one({"uid": new_b}, {"pid": 1}) or {}
    room = await call(new_a, "POST", "/challenges", {"pids": [me_b.get("pid")], "picks": PCM, "count": 30})
    if room:
        await call(new_b, "GET", "/inbox", label="GET /inbox (challenged)")
        await call(new_b, "GET", f"/challenges/{room['id']}")
        await call(new_b, "POST", f"/challenges/{room['id']}/decline", {})
        await call(new_a, "POST", f"/challenges/{room['id']}/cancel", {})
    g = await call(new_a, "POST", "/gangs", {"name": f"Audit {tag}", "emblem": "lion", "kind": "gang", "pids": []})
    if g:
        await call(new_a, "GET", f"/gangs/{g['id']}")
        await call(new_a, "DELETE", f"/gangs/{g['id']}")
    await call(new_a, "POST", "/blocks", {"pid": pid.get("audit-p-000002")})
    await call(new_a, "DELETE", f"/blocks/{pid.get('audit-p-000002')}")
    await call(new_a, "DELETE", f"/friends/{me_b.get('pid')}")
    for path in ("/quests/claim", "/rush/claim", "/league/friends/claim"):
        await call(heavy, "POST", path, {})
    await call(new_a, "POST", "/profile/name", {"name": "Audit New"})

    print("\n--- work the server does by itself ---")
    await background("cup night tick (every 3 s)", server.cups_router.night_tick)
    await background("sweep (every 5 min)", server.sweep)
    await background("card sync (every 60 s)", server.sync_cards)
    await server.db.command("profile", 0)
    audit.summary()
    await client.aclose()


async def run_startup():
    """A new code version runs setup_database() once; every other start only looks for the marker."""
    await server.db.command("profile", 0)
    await server.db.command("profile", 1, slowms=20)
    mark = list(profile.find({}, {"ts": 1}).sort("$natural", -1).limit(1))
    mark = mark[0]["ts"] if mark else datetime(2000, 1, 1)
    t = time.perf_counter()
    await server.setup_database()
    full = time.perf_counter() - t
    await server.db.rf_meta.update_one({"_id": "setup:" + server.SETUP_VERSION}, {"$set": {"done": True, "ts": time.time()}}, upsert=True)
    t = time.perf_counter()
    await server.startup()
    again = time.perf_counter() - t
    await server.db.command("profile", 0)
    sizes = {n: raw[n].estimated_document_count() for n in ("rf_profiles", "rf_duels", "rf_cups", "rf_sessions", "rf_awards", "rf_cards", "rf_daily_plays")}
    print(f"\nscratch sizes: {sizes}")
    print(f"new code version (setup_database): {full:.2f} s")
    print(f"plain restart (startup, marker present): {again * 1000:.0f} ms")
    slow = [op for op in profile.find({"ts": {"$gt": mark}}).sort("millis", -1) if not op["ns"].endswith("system.profile")]
    print(f"database operations of 20 ms or more during setup: {len(slow)}")
    for op in slow[:15]:
        d = describe(op)
        print(f"  {op.get('millis', 0):6d} ms  {op['ns'].split('.', 1)[1]}: {d[1] if d else next(iter(op.get('command') or {}), op['op'])}  [{op.get('planSummary', '-')}] rows {op.get('docsExamined', 0)}")
    for task in asyncio.all_tasks():
        if task is not asyncio.current_task():
            task.cancel()


async def run_check():
    """The short cuts must answer exactly what the full counts answered: a place on both boards and both weak lists."""
    import revision
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=server.app), base_url="http://audit/api/rf", timeout=120)
    bad = 0

    def same(what, got, want):
        nonlocal bad
        if got != want:
            bad += 1
            print(f"  DIFFERENT {what}: got {str(got)[:160]} want {str(want)[:160]}")

    # 1. XP board: your rank = everyone with more XP, or the same XP and an id that sorts first (QA players left out).
    field = "exam_stats.JEE.xp"
    tied = [r["_id"] for r in raw.rf_profiles.aggregate([{"$match": {field: {"$gt": 0}}}, {"$group": {"_id": "$" + field, "n": {"$sum": 1}}}, {"$match": {"n": {"$gt": 1}}}, {"$limit": 5}])]
    people = list(raw.rf_profiles.aggregate([{"$match": {field: {"$gt": 0}}}, {"$sample": {"size": 40}}, {"$project": {"uid": 1, "exam_stats": 1}}]))
    people += list(raw.rf_profiles.find({field: {"$in": tied}}, {"uid": 1, "exam_stats": 1}).limit(20))
    people += list(raw.rf_profiles.find({field: {"$gt": 0}}, {"uid": 1, "exam_stats": 1}).sort([(field, -1), ("uid", 1)]).limit(3))
    people += list(raw.rf_profiles.find({field: {"$gt": 0}}, {"uid": 1, "exam_stats": 1}).sort([(field, 1), ("uid", -1)]).limit(3))
    qa = {"$or": [{"uid": {"$regex": "^TEST"}}, {"name": {"$regex": "^TEST"}}]}
    for p in people:
        xp = p["exam_stats"]["JEE"]["xp"]
        above = {"$or": [{field: {"$gt": xp}}, {field: xp, "uid": {"$lt": p["uid"]}}]}
        want = 1 + raw.rf_profiles.count_documents(above) - raw.rf_profiles.count_documents({"$and": [above, qa]})
        got = (await client.get("/leaderboard?exam=JEE", headers=grant(p["uid"]))).json()["you"]
        same(f"XP rank of {p['uid']} ({xp} XP)", got["rank"], want)
    print(f"XP board: {len(people)} players checked (with {len(tied)} tied XP values, the top 3 and the bottom 3)")

    # 2. All India board: your place = more right answers, or as many in less time, or the same and finished earlier.
    day = next(iter(raw.rf_daily_plays.aggregate([{"$match": {"exam": "JEE", "status": "done", "test": False}}, {"$group": {"_id": "$day", "n": {"$sum": 1}}}, {"$sort": {"n": -1}}, {"$limit": 1}])))["_id"]  # the busiest day
    base = {"exam": "JEE", "day": day, "test": False, "status": "done"}
    plays = list(raw.rf_daily_plays.aggregate([{"$match": base}, {"$sample": {"size": 60}}]))
    plays += list(raw.rf_daily_plays.find(base).sort([("correct", -1), ("ms", 1), ("finished_ts", 1)]).skip(95).limit(10))  # around the top-100 line
    plays += list(raw.rf_daily_plays.find(base).sort([("correct", 1), ("ms", -1)]).limit(3))
    for p in plays:
        want = 1 + raw.rf_daily_plays.count_documents({**base, "$or": [{"correct": {"$gt": p["correct"]}}, {"correct": p["correct"], "ms": {"$lt": p["ms"]}},
                                                                        {"correct": p["correct"], "ms": p["ms"], "finished_ts": {"$lt": p["finished_ts"]}}]})
        got = (await client.get(f"/daily/board?exam=JEE&day={day}", headers=grant(p["uid"]))).json()
        same(f"All India place of {p['uid']} ({p['correct']} right, {p['ms']} ms)", got["you"]["rank"], want)
        same("All India players", got["players"], raw.rf_daily_plays.count_documents(base))
    print(f"All India board {day}: {len(plays)} runs checked out of {raw.rf_daily_plays.count_documents(base)}")

    # 3. Weak lists: the one-pass version against the pipelines it replaced (the pipelines are the specification).
    async def chapters_spec(uid):
        return await (await server.db.rf_learning_events.aggregate([
            {"$match": {"uid": uid, "exam": "JEE"}}, {"$sort": {"completed_at": 1, "ref": 1}}, {"$unwind": "$results"},
            {"$group": {"_id": "$results.card_id", "subject": {"$last": "$results.subject"}, "chapter": {"$last": "$results.chapter"}, "latest": {"$last": "$results.outcome"},
                        "misses": {"$sum": {"$cond": [{"$in": ["$results.outcome", ["incorrect", "timed_out"]]}, 1, 0]}}}},
            {"$match": {"latest": {"$ne": "correct"}, "misses": {"$gt": 0}}},
            {"$lookup": {"from": "rf_cards", "localField": "_id", "foreignField": "id", "as": "card"}},
            {"$match": {"card": {"$elemMatch": {"exam": "JEE", "retired": {"$ne": True}}}}},
            {"$sort": {"misses": -1, "_id": 1}},
            {"$group": {"_id": {"subject": "$subject", "chapter": "$chapter"}, "misses": {"$sum": "$misses"}, "card_ids": {"$push": "$_id"}}},
            {"$sort": {"misses": -1, "_id.subject": 1, "_id.chapter": 1}},
            {"$project": {"_id": 0, "subject": "$_id.subject", "chapter": "$_id.chapter", "misses": 1, "remaining": {"$size": "$card_ids"}, "card_ids": {"$slice": ["$card_ids", 30]}}},
        ])).to_list(150)

    learners = raw.rf_learning_events.distinct("uid", {"exam": "JEE"})[:40]
    for uid in learners:
        t = time.perf_counter()
        want = await chapters_spec(uid)
        old_ms = (time.perf_counter() - t) * 1000
        t = time.perf_counter()
        got = await revision.weak_chapters(server.db, uid, "JEE")
        new_ms = (time.perf_counter() - t) * 1000
        same(f"weak chapters of {uid}", [{k: r[k] for k in sorted(r)} for r in got], [{k: r[k] for k in sorted(r)} for r in want])
        if len(want) > 20:
            t = time.perf_counter()
            await revision.weak_topics(server.db, uid, "JEE")
            print(f"  {uid}: {len(want)} weak chapters; before {old_ms:.0f} ms, now {new_ms:.0f} ms, then the weak topics from the same pass {(time.perf_counter() - t) * 1000:.0f} ms")
    print(f"Weak chapters: {len(learners)} students checked")
    print("\nALL THE SAME" if not bad else f"\n{bad} DIFFERENCES")
    await client.aclose()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["startup", "queries", "check"])
    ap.add_argument("--all", action="store_true", help="list every database trip, not only the flagged ones")
    args = ap.parse_args()
    asyncio.run({"startup": run_startup, "check": run_check}[args.mode]() if args.mode != "queries" else run_queries(args.all))
