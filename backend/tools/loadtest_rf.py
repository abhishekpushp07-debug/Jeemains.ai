"""Rapid Fire load test: N virtual students play full Practice Rival matches at once (HTTP + live socket) while the app's
inbox poller runs for each of them. Only `TEST-load-*` accounts are used; `--cleanup` removes every trace of them.

    python tools/loadtest_rf.py --players 1000 --procs 4 --think 3
    python tools/loadtest_rf.py --cleanup
"""
import argparse
import asyncio
import hashlib
import json
import multiprocessing as mp
import os
import random
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone

import httpx
import websockets
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
PREFIX = "TEST-load-"
INBOX_S = float(os.environ.get("RF_LOAD_INBOX_S", "25"))  # the app looks at its inbox every 25 s during a live match (8 s elsewhere)


def mongo():
    return MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]


def make_grants(n):
    db, now = mongo(), datetime.now(timezone.utc)
    tokens = [secrets.token_urlsafe(32) for _ in range(n)]
    db.rf_access.insert_many([{"digest": hashlib.sha256(t.encode()).hexdigest(), "uid": f"{PREFIX}{i:06d}", "sid": "", "expires_at": now + timedelta(minutes=40)}
                              for i, t in enumerate(tokens)])
    return tokens


def cleanup():
    db, q = mongo(), {"$regex": "^" + PREFIX}
    out = {"duels": db.rf_duels.delete_many({"players.uid": q}).deleted_count, "profiles": db.rf_profiles.delete_many({"uid": q}).deleted_count,
           "awards": db.rf_awards.delete_many({"uid": q}).deleted_count, "learning": db.rf_learning_events.delete_many({"uid": q}).deleted_count,
           "access": db.rf_access.delete_many({"uid": q}).deleted_count, "sessions": db.rf_sessions.delete_many({"user_id": q}).deleted_count,
           "feed": db.rf_feed.delete_many({"uid": q}).deleted_count}
    print(json.dumps({"cleanup": out}))


def pct(xs, p):
    if not xs:
        return None
    xs = sorted(xs)
    return round(xs[min(len(xs) - 1, int(len(xs) * p))] * 1000, 1)


async def player(i, token, base, ws_base, think, stats, ramp, pairs=False):
    # This container gives a client only 1024 local ports per destination: spread players over loopback addresses
    # (127.0.0.2, .3, ...) so the test measures the server, not the test machine's port limit.
    if "127.0.0.1" in base:
        host = f"127.0.0.{2 + i % 120}"
        base, ws_base = base.replace("127.0.0.1", host), ws_base.replace("127.0.0.1", host)
    await asyncio.sleep(random.uniform(0, ramp))
    h = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    async with httpx.AsyncClient(base_url=base, headers=h, timeout=30) as c:
        async def call(kind, method, path, body=None):
            t = time.perf_counter()
            r, drops = None, 0
            for _ in range(30):  # the server may ask a new player to wait for a seat (arena busy)
                try:
                    r = await c.request(method, path, json=body)
                except (httpx.ReadError, httpx.RemoteProtocolError, httpx.WriteError) as e:
                    # A kept-alive connection closed by the server just as this request went out: every call here is
                    # safe to repeat (request ids / card index), exactly what the app does.
                    drops += 1
                    stats["retried"] += 1
                    if drops <= 2:
                        await asyncio.sleep(0.3)
                        continue
                    stats["errors"].append(f"{kind}:{type(e).__name__}")
                    return None
                except Exception as e:  # noqa: BLE001
                    stats["errors"].append(f"{kind}:{type(e).__name__}")
                    return None
                if r.status_code == 503 and (r.json() or {}).get("code") == "arena_busy":
                    stats["busy"] += 1
                    await asyncio.sleep(float(r.headers.get("retry-after", "5")))
                    continue
                break
            stats[kind].append(time.perf_counter() - t)
            if r.status_code >= 400:
                stats["errors"].append(f"{kind}:{r.status_code}")
                return None
            return r.json()

        stop = asyncio.Event()

        async def inbox():
            await asyncio.sleep(random.uniform(0, 6))
            while not stop.is_set():
                await call("inbox", "GET", "/inbox")
                try:
                    await asyncio.wait_for(stop.wait(), timeout=random.uniform(INBOX_S - 1, INBOX_S + 1))
                except asyncio.TimeoutError:
                    pass

        poller = asyncio.create_task(inbox())
        try:
            if pairs:  # quick match: two load students meet each other, like real students when the arena is full
                d = await call("create", "POST", "/duels", {"exam": "JEE", "subject": "Physics", "picks": [{"subject": "Physics", "chapter": None}], "mode": "random", "name": f"Load {i}", "request_id": uuid.uuid4().hex})
            else:
                d = await call("create", "POST", "/duels", {"exam": "JEE", "subject": "Physics", "picks": [{"subject": "Physics", "chapter": None}], "mode": "invite", "name": f"Load {i}", "request_id": uuid.uuid4().hex})
                if d:
                    d = await call("bot", "POST", f"/duels/{d['id']}/bot", {})
            if not d:
                return
            did, frames, last = d["id"], [0], dict(d)
            try:
                ws = await websockets.connect(f"{ws_base}/duels/{did}/ws", open_timeout=20, max_size=2 ** 22)
                await ws.send(json.dumps({"token": token, "lite": 1}))
            except Exception as e:  # noqa: BLE001
                stats["errors"].append(f"ws:{type(e).__name__}")
                ws = None

            async def reader():
                try:
                    async for msg in ws:
                        frames[0] += 1
                        last.update(json.loads(msg))
                except Exception:  # noqa: BLE001
                    pass
            rd = asyncio.create_task(reader()) if ws else None
            if d["status"] == "waiting":
                t_wait = time.perf_counter()
                while last.get("status") == "waiting" and time.perf_counter() - t_wait < 130:
                    await asyncio.sleep(0.2)
                if last.get("status") != "ready":
                    stats["unpaired"] += 1
                    if ws:
                        await ws.close()
                    return
                stats["pair_wait"].append(time.perf_counter() - t_wait)
                d = dict(last)
            await asyncio.sleep(max(0, d["start_at"] - d["server_now"]) + 0.2)
            for k in range(d["total"]):
                await asyncio.sleep(max(0.3, random.gauss(think, think / 3)))
                res = await call("answer", "POST", f"/duels/{did}/answer", {"index": k, "choice": random.randint(0, 3), "outcome": "answer", "ms": 1000})
                if res is None:
                    break
            t_end = time.perf_counter()
            while last.get("status") != "finished" and time.perf_counter() - t_end < 15:
                await asyncio.sleep(0.2)
            stats["finish_push"].append(time.perf_counter() - t_end)
            stats["finished"] += last.get("status") == "finished"
            stats["frames"] += frames[0]
            if ws:
                await ws.close()
            if rd:
                rd.cancel()
        finally:
            stop.set()
            await poller


def run_proc(tokens, offset, base, ws_base, think, ramp, q, pairs=False):
    stats = {"create": [], "bot": [], "answer": [], "inbox": [], "finish_push": [], "pair_wait": [], "errors": [], "finished": 0, "frames": 0, "busy": 0, "retried": 0, "unpaired": 0, "client_cpu": 0.0}

    async def main():
        await asyncio.gather(*(player(offset + i, t, base, ws_base, think, stats, ramp, pairs) for i, t in enumerate(tokens)))
    asyncio.run(main())
    import resource
    u = resource.getrusage(resource.RUSAGE_SELF)
    stats["client_cpu"] = u.ru_utime + u.ru_stime
    q.put(stats)


def backend_cpu(port):
    """CPU seconds used so far by the backend on this port (the uvicorn parent and every worker it spawned), and by mongod."""
    procs = {}
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            cmd = open(f"/proc/{pid}/cmdline", "rb").read().replace(b"\0", b" ")
            f = open(f"/proc/{pid}/stat").read().rsplit(")", 1)[1].split()
            procs[int(pid)] = (cmd, int(f[1]), (int(f[11]) + int(f[12])) / os.sysconf("SC_CLK_TCK"))
        except OSError:
            continue
    roots = {pid for pid, (cmd, _, _) in procs.items() if b"server:app" in cmd and f"--port {port}".encode() in cmd}
    return (sum(cpu for pid, (_, ppid, cpu) in procs.items() if pid in roots or ppid in roots),
            sum(cpu for cmd, _, cpu in procs.values() if cmd.startswith(b"mongod") or b"/mongod " in cmd))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--players", type=int, default=200)
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--think", type=float, default=3.0, help="average seconds a student takes per card")
    ap.add_argument("--ramp", type=float, default=10.0, help="seconds over which players arrive")
    ap.add_argument("--base", default="http://127.0.0.1:8001/api/rf")
    ap.add_argument("--pairs", action="store_true", help="students play each other (quick match) instead of Practice Rivals")
    ap.add_argument("--cleanup", action="store_true")
    a = ap.parse_args()
    if a.cleanup:
        cleanup()
        raise SystemExit
    ws_base = a.base.replace("http", "ws", 1)
    tokens = make_grants(a.players)
    per = -(-a.players // a.procs)
    port = int(a.base.split(":")[2].split("/")[0])
    q, procs, (cpu0, db0), t0 = mp.Queue(), [], backend_cpu(port), time.time()
    for k in range(a.procs):
        chunk = tokens[k * per:(k + 1) * per]
        if chunk:
            p = mp.Process(target=run_proc, args=(chunk, k * per, a.base, ws_base, a.think, a.ramp, q, a.pairs))
            p.start()
            procs.append(p)
    parts = [q.get() for _ in procs]
    for p in procs:
        p.join()
    wall, (cpu, dbcpu) = time.time() - t0, backend_cpu(port)
    cpu, dbcpu = cpu - cpu0, dbcpu - db0
    s = {k: sum((x[k] for x in parts), [] if isinstance(parts[0][k], list) else 0) for k in parts[0]}
    errs = {}
    for e in s["errors"]:
        errs[e] = errs.get(e, 0) + 1
    report = {"players": a.players, "pairs": a.pairs, "think_s": a.think, "wall_s": round(wall, 1), "finished": s["finished"], "unpaired": s["unpaired"], "arena_busy_waits": s["busy"], "retried_drops": s["retried"], "client_cpu_s_per_proc": round(s["client_cpu"] / len(parts), 1),
              "answers": len(s["answer"]), "answers_per_s": round(len(s["answer"]) / wall, 1), "inbox_polls": len(s["inbox"]), "ws_frames": s["frames"],
              "backend_cpu_s": round(cpu, 1), "backend_cpu_pct_of_core": round(100 * cpu / wall, 1), "mongod_cpu_pct_of_core": round(100 * dbcpu / wall, 1),
              **{f"{k}_ms": {"p50": pct(s[k], .5), "p95": pct(s[k], .95), "p99": pct(s[k], .99), "max": pct(s[k], 1)} for k in ("create", "bot", "pair_wait", "answer", "inbox", "finish_push")},
              "errors": errs}
    print(json.dumps(report, indent=1))
