"""App load test: N virtual students use the app at once through any address (the public preview URL included) - the
screens a student opens around a mock test that run on OUR server: Rapid Fire profile + inbox, the Rank tab (marks ->
rank estimate, college list), and Dream College (read, save a mock score). The website (jeelive.ai) is never called.
Only `TEST-loadapp-*` identities with short grants are made; `--cleanup` removes exactly those.

    python tools/loadtest_app.py --users 1000 --seconds 60 --think 2 --base https://<preview>/api
    python tools/loadtest_app.py --cleanup
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
from datetime import datetime, timedelta, timezone

import aiohttp
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
PREFIX = "TEST-loadapp-"


def mongo():
    return MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]


def make_grants(n):
    tokens, now = [secrets.token_urlsafe(32) for _ in range(n)], datetime.now(timezone.utc)
    mongo().rf_access.insert_many([{"digest": hashlib.sha256(t.encode()).hexdigest(), "uid": f"{PREFIX}{i:06d}", "sid": "",
                                    "expires_at": now + timedelta(minutes=40)} for i, t in enumerate(tokens)])
    return tokens


def cleanup():
    db, q = mongo(), {"$regex": "^" + PREFIX}
    print(json.dumps({"cleanup": {"profiles": db.rf_profiles.delete_many({"uid": q}).deleted_count, "dreams": db.rf_dreams.delete_many({"uid": q}).deleted_count,
                                  "access": db.rf_access.delete_many({"uid": q}).deleted_count, "feed": db.rf_feed.delete_many({"uid": q}).deleted_count}}))


def step(i, k):
    """The k-th screen of student i, in the order a student moves through the app."""
    marks = random.randint(-10, 300)
    return [
        ("profile", "GET", "/rf/profile", None),
        ("inbox", "GET", "/rf/inbox", None),
        ("rank_estimate", "POST", "/rank/estimate", {"exam": "jee", "marks": marks, "level": random.choice(["tough", "normal", "easy"]), "category": "GEN"}),
        ("rank_colleges", "POST", "/rank/predict", {"marks": max(0, marks), "level": "normal", "category": random.choice(["GEN", "OBC-NCL", "EWS"])}),
        ("dream_read", "GET", "/rf/dream", None),
        ("dream_mock", "POST", "/rf/dream/mocks", {"mocks": [{"id": f"m{i}-{k}", "exam": "jee", "score": marks, "max": 300, "raw": marks, "rawMax": 300,
                                                                "title": "Load mock", "at": time.time() * 1000}]}),
        ("catalog", "GET", "/rf/catalog", None),
    ][k % 7]


async def student(i, token, base, until, think, stats, session):
    await asyncio.sleep(random.uniform(0, min(10, think * 3 + 1)))
    k = random.randrange(7)
    h = {"Authorization": "Bearer " + token}
    while time.time() < until:
        name, method, path, body = step(i, k)
        t = time.perf_counter()
        try:
            async with session.request(method, base + path, json=body, headers=h) as r:
                await r.read()
                code = r.status
        except Exception as e:  # noqa: BLE001
            code = type(e).__name__
        took = time.perf_counter() - t
        stats["lat"].setdefault(name, []).append(took)
        if code != 200:
            stats["errors"][f"{name}:{code}"] = stats["errors"].get(f"{name}:{code}", 0) + 1
        k += 1
        await asyncio.sleep(max(0.05, random.gauss(think, think / 3)))


def run_proc(offset, tokens, base, seconds, think, start_at, q):
    stats = {"lat": {}, "errors": {}}

    async def main():
        await asyncio.sleep(max(0, start_at - time.time()))
        conn = aiohttp.TCPConnector(limit=0, ttl_dns_cache=300)
        async with aiohttp.ClientSession(connector=conn, timeout=aiohttp.ClientTimeout(total=30)) as s:
            until = time.time() + seconds
            await asyncio.gather(*(student(offset + j, t, base, until, think, stats, s) for j, t in enumerate(tokens)))
    asyncio.run(main())
    q.put(stats)


def cpu_of(port):
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
    return (sum(c for pid, (_, ppid, c) in procs.items() if pid in roots or ppid in roots),
            sum(c for cmd, _, c in procs.values() if cmd.startswith(b"mongod") or b"/mongod " in cmd))


def pct(xs, p):
    xs = sorted(xs)
    return round(xs[min(len(xs) - 1, int(len(xs) * p))] * 1000, 1) if xs else None


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--users", type=int, default=100)
    ap.add_argument("--seconds", type=float, default=60)
    ap.add_argument("--think", type=float, default=2.0, help="average seconds a student spends on a screen")
    ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--base", default="http://127.0.0.1:8001/api")
    ap.add_argument("--port", type=int, default=8001, help="local port of the server under test (for its CPU use)")
    ap.add_argument("--cleanup", action="store_true")
    a = ap.parse_args()
    if a.cleanup:
        cleanup()
        raise SystemExit
    tokens = make_grants(a.users)
    per, start_at = -(-a.users // a.procs), time.time() + 2
    q, procs, (cpu0, db0) = mp.Queue(), [], cpu_of(a.port)
    for k in range(a.procs):
        chunk = tokens[k * per:(k + 1) * per]
        if chunk:
            p = mp.Process(target=run_proc, args=(k * per, chunk, a.base.rstrip("/"), a.seconds, a.think, start_at, q))
            p.start()
            procs.append(p)
    parts = [q.get() for _ in procs]
    for p in procs:
        p.join()
    wall = time.time() - start_at
    cpu, dbcpu = (x - y for x, y in zip(cpu_of(a.port), (cpu0, db0)))
    lat, errors = {}, {}
    for x in parts:
        for name, xs in x["lat"].items():
            lat.setdefault(name, []).extend(xs)
        for e, n in x["errors"].items():
            errors[e] = errors.get(e, 0) + n
    total = sum(len(v) for v in lat.values())
    failed = sum(errors.values())
    print(json.dumps({"users": a.users, "think_s": a.think, "wall_s": round(wall, 1), "requests": total, "failed": failed,
                      "error_rate_pct": round(100 * failed / total, 2) if total else None, "req_per_s": round(total / wall, 1),
                      "server_cores_busy": round(cpu / wall, 2), "ok_req_per_server_cpu_s": round((total - failed) / cpu, 1) if cpu else None,
                      "mongod_cores_busy": round(dbcpu / wall, 2),
                      "latency_ms": {n: {"n": len(xs), "p50": pct(xs, .5), "p95": pct(xs, .95), "p99": pct(xs, .99)} for n, xs in sorted(lat.items())},
                      "all_p50_ms": pct(sum(lat.values(), []), .5), "all_p95_ms": pct(sum(lat.values(), []), .95), "all_p99_ms": pct(sum(lat.values(), []), .99),
                      "errors": errors}, indent=1))
