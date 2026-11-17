"""Mock-test load test of OUR server's website proxy (/api/jl/*). Point a test copy of the server at tools/fake_website.py
(never at the real website), then measure what each kind of call costs our server:

    JEELIVE_API=http://127.0.0.1:9100 uvicorn server:app --port 8002 --workers 2      # test copy of the server
    python tools/loadtest_mock.py --kind answer --users 2000 --seconds 40 --base http://127.0.0.1:8002
    python tools/loadtest_mock.py --kind storm --users 5000 --base http://127.0.0.1:8002   # everyone at 00:00
    python tools/loadtest_mock.py --cleanup

kinds: answer (PUT a saved answer, think --think s between), attempt (GET the 58 KB paper), asset (GET a 450 KB image),
storm (every user GETs the paper in the same second, like the timer hitting zero). Only `loadtest-*` cookie jars are made;
--cleanup removes them.
"""
import argparse
import asyncio
import json
import multiprocessing as mp
import os
import random
import time
import uuid

import aiohttp
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
PREFIX = "loadtest-"


def mongo():
    return MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]


def make_jars(n):
    sids = [f"{PREFIX}{uuid.uuid4().hex[:24]}" for _ in range(n)]
    mongo().jl_jars.insert_many([{"sid": s, "cookies": {"jl_access": "a" * 40, "jl_refresh": "r" * 40}, "updated_at": "load"} for s in sids])
    return sids


def cleanup():
    print(json.dumps({"jars_removed": mongo().jl_jars.delete_many({"sid": {"$regex": "^" + PREFIX}}).deleted_count}))


def pct(xs, p):
    xs = sorted(xs)
    return round(xs[min(len(xs) - 1, int(len(xs) * p))] * 1000, 1) if xs else None


def request_for(kind, sid, i):
    aid = f"att-{sid[-8:]}"
    if kind == "answer":
        q = f"q{random.randrange(75):03d}"
        return "PUT", f"/api/jl/attempts/{aid}/answers/{q}", {"value": "2", "marked": False, "revision": i + 1, "request_id": uuid.uuid4().hex}
    if kind == "asset":
        return "GET", f"/api/jl/attempts/{aid}/questions/q{random.randrange(75):03d}/asset/question/0", None
    return "GET", f"/api/jl/attempts/{aid}", None


async def user(session, base, kind, sid, until, think, stats, start_at):
    await asyncio.sleep(max(0.0, start_at - time.time()))
    i = 0
    while True:
        method, path, body = request_for(kind, sid, i)
        t = time.perf_counter()
        try:
            async with session.request(method, base + path, json=body, headers={"X-JL-Sid": sid}) as r:
                n = len(await r.read())
                (stats["ok"] if r.status < 400 else stats["bad"]).append(time.perf_counter() - t)
                stats["bytes"] += n
                if r.status >= 400:
                    stats["codes"][str(r.status)] = stats["codes"].get(str(r.status), 0) + 1
        except Exception as e:  # noqa: BLE001
            stats["codes"][type(e).__name__] = stats["codes"].get(type(e).__name__, 0) + 1
            stats["bad"].append(time.perf_counter() - t)
        i += 1
        if kind == "storm" or time.time() >= until:
            return
        await asyncio.sleep(random.uniform(0.5, 1.5) * think if think else 0)


def run_proc(k, sids, base, kind, seconds, think, start_at, q):
    stats = {"ok": [], "bad": [], "bytes": 0, "codes": {}}

    async def main():
        # A client gets only ~28k local ports per source address: every 400 users talk from their own loopback address
        # (127.0.<proc>.<n>) so the test measures the server, not the test machine's port limit.
        groups = [sids[i:i + 400] for i in range(0, len(sids), 400)]
        sessions = [aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=0, local_addr=(f"127.0.{k + 1}.{g + 2}", 0)),
                                          timeout=aiohttp.ClientTimeout(total=60)) for g in range(len(groups))]
        until = start_at + seconds
        try:
            await asyncio.gather(*(user(s, base, kind, sid, until, think, stats, start_at + (0 if kind == "storm" else random.uniform(0, min(5, seconds / 4))))
                                   for s, group in zip(sessions, groups) for sid in group))
        finally:
            for s in sessions:
                await s.close()
    asyncio.run(main())
    q.put(stats)


def cpu_of(port):
    """CPU seconds so far of the server on this port (uvicorn parent + workers), mongod, and the fake website."""
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
    roots = {pid for pid, (cmd, _, _) in procs.items() if (b"server:app" in cmd or b"proto_proxy:app" in cmd) and f"--port {port}".encode() in cmd}
    own = sum(cpu for pid, (_, ppid, cpu) in procs.items() if pid in roots or ppid in roots)
    db = sum(cpu for cmd, _, cpu in procs.values() if cmd.startswith(b"mongod") or b"/mongod " in cmd)
    fake = sum(cpu for cmd, _, cpu in procs.values() if b"fake_website.py" in cmd)
    return own, db, fake


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=["answer", "attempt", "asset", "storm"], default="answer")
    ap.add_argument("--users", type=int, default=1000)
    ap.add_argument("--seconds", type=float, default=30)
    ap.add_argument("--think", type=float, default=0.0, help="average seconds between one user's calls (0 = as fast as possible)")
    ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--base", default="http://127.0.0.1:8002")
    ap.add_argument("--cleanup", action="store_true")
    a = ap.parse_args()
    if a.cleanup:
        cleanup()
        raise SystemExit
    sids = make_jars(a.users)
    port = int(a.base.rsplit(":", 1)[1].split("/")[0])
    per = -(-a.users // a.procs)
    start_at = time.time() + 2
    q, procs, before = mp.Queue(), [], cpu_of(port)
    for k in range(a.procs):
        chunk = sids[k * per:(k + 1) * per]
        if chunk:
            p = mp.Process(target=run_proc, args=(k, chunk, a.base, a.kind, a.seconds, a.think, start_at, q))
            p.start()
            procs.append(p)
    parts = [q.get() for _ in procs]
    for p in procs:
        p.join()
    wall = time.time() - start_at
    own, db, fake = (x - y for x, y in zip(cpu_of(port), before))
    ok = sum((x["ok"] for x in parts), [])
    bad = sum((x["bad"] for x in parts), [])
    codes = {}
    for x in parts:
        for c, n in x["codes"].items():
            codes[c] = codes.get(c, 0) + n
    total = len(ok) + len(bad)
    print(json.dumps({"kind": a.kind, "users": a.users, "wall_s": round(wall, 1), "requests": total, "ok": len(ok), "failed": len(bad),
                      "req_per_s": round(total / wall, 1), "MB_per_s": round(sum(x["bytes"] for x in parts) / wall / 1e6, 1),
                      "server_cpu_s": round(own, 1), "server_cores_busy": round(own / wall, 2),
                      "ok_req_per_server_cpu_s": round(len(ok) / own, 1) if own else None,
                      "mongod_cores_busy": round(db / wall, 2), "fake_website_cores_busy": round(fake / wall, 2),
                      "latency_ms": {"p50": pct(ok, .5), "p95": pct(ok, .95), "p99": pct(ok, .99), "max": pct(ok, 1)},
                      "errors": codes}, indent=1))
