"""Iter115 L5 probe: many TEST players each do lobby reads + solo session + practice-rival duel.

Measures: 2xx vs 503 arena_busy vs other errors, p50/p95, by endpoint. Uses TEST-iter115-* grants
written straight to rf_access (same shim as conftest/perf_rf_probe). On exit it ends its own grants and retires its
own profiles in place; it never deletes rows.

    python backend/tests/iter115_load_probe.py --users 25
    python backend/tests/iter115_load_probe.py --users 50
    python backend/tests/iter115_load_probe.py --users 100
    python backend/tests/iter115_load_probe.py --users 200
"""
import argparse
import asyncio
import hashlib
import json
import os
import secrets
import statistics
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import aiohttp
from dotenv import dotenv_values, load_dotenv
from pymongo import MongoClient

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / "backend" / ".env")
_front = dotenv_values(ROOT / "frontend" / ".env")
BASE = (os.environ.get("PROBE_BASE") or _front.get("EXPO_PUBLIC_BACKEND_URL") or _front.get("EXPO_BACKEND_URL")).rstrip("/") + "/api"
PREFIX = "TEST-iter115-"


def make_grants(n):
    db = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    tokens = [secrets.token_urlsafe(32) for _ in range(n)]
    now = datetime.now(timezone.utc)
    db.rf_access.insert_many([
        {"digest": hashlib.sha256(t.encode()).hexdigest(), "uid": f"{PREFIX}{i:05d}",
         "sid": "", "test_shim": "iter115", "expires_at": now + timedelta(minutes=30)}
        for i, t in enumerate(tokens)
    ])
    return tokens


def cleanup():
    """Nothing is deleted (project rule). The probe's grants end now and its throwaway profiles are retired in place:
    a TEST uid and a TEST name keep them off every real board."""
    db = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    q = {"$regex": "^" + PREFIX}
    db.rf_access.update_many({"uid": q}, {"$set": {"expires_at": datetime.now(timezone.utc)}})
    db.rf_profiles.update_many({"uid": q}, {"$set": {"name": "TEST iter115 (retired)"}})


async def one_player(i, token, session, stats):
    headers = {"Authorization": f"Bearer {token}"}

    async def hit(label, method, path, body=None):
        t0 = time.perf_counter()
        try:
            async with session.request(method, BASE + path, json=body, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as r:
                try:
                    data = await r.json(content_type=None)
                except Exception:
                    data = None
                dt_ms = (time.perf_counter() - t0) * 1000
                stats[label]["lat"].append(dt_ms)
                code = r.status
                if code == 503 and isinstance(data, dict) and data.get("code") == "arena_busy":
                    stats[label]["arena_busy"] += 1
                elif 200 <= code < 300:
                    stats[label]["ok"] += 1
                else:
                    stats[label]["other"] += 1
                    stats[label]["other_codes"].setdefault(code, 0)
                    stats[label]["other_codes"][code] += 1
                return code, data
        except Exception as e:
            stats[label]["exc"] += 1
            stats[label]["exc_types"].setdefault(type(e).__name__, 0)
            stats[label]["exc_types"][type(e).__name__] += 1
            return 0, None

    # Lobby reads
    await hit("GET /rf/catalog", "GET", "/rf/catalog?exam=JEE")
    await hit("GET /rf/profile", "GET", "/rf/profile")
    await hit("GET /rf/inbox", "GET", "/rf/inbox")

    # Solo sprint create + complete
    code, s = await hit("POST /rf/sessions", "POST", "/rf/sessions",
                       {"exam": "JEE", "subject": "Physics", "count": 30, "request_id": uuid.uuid4().hex})
    if code == 200 and s and "cards" in s:
        results = [{"card_id": c["id"], "outcome": "correct", "choice": c.get("answer", 0), "ms": 1500} for c in s["cards"][:10]]
        await hit("POST /rf/sessions/complete", "POST", f"/rf/sessions/{s['id']}/complete", {"results": results})

    # Practice rival (bot)
    code, d = await hit("POST /rf/duels (invite)", "POST", "/rf/duels",
                        {"exam": "JEE", "subject": "Physics", "picks": [{"subject": "Physics", "chapter": None}],
                         "mode": "invite", "name": f"T{i}", "count": 30, "request_id": uuid.uuid4().hex})
    if code == 200 and d and "id" in d:
        await hit("POST /rf/duels/bot", "POST", f"/rf/duels/{d['id']}/bot", {})


def new_stat():
    return {"ok": 0, "arena_busy": 0, "other": 0, "exc": 0, "lat": [],
            "other_codes": {}, "exc_types": {}}


async def main(users):
    tokens = make_grants(users)
    stats = {k: new_stat() for k in ("GET /rf/catalog", "GET /rf/profile", "GET /rf/inbox",
                                     "POST /rf/sessions", "POST /rf/sessions/complete",
                                     "POST /rf/duels (invite)", "POST /rf/duels/bot")}
    conn = aiohttp.TCPConnector(limit=0, ttl_dns_cache=300)
    t0 = time.perf_counter()
    try:
        async with aiohttp.ClientSession(connector=conn) as session:
            await asyncio.gather(*(one_player(i, tok, session, stats) for i, tok in enumerate(tokens)))
    finally:
        elapsed = time.perf_counter() - t0
        try:
            cleanup()
        except Exception as e:
            print("cleanup error:", e)

    print(f"\n=== users={users} elapsed={elapsed:.1f}s base={BASE} ===")
    print(f"{'endpoint':30} {'ok':>5} {'503':>5} {'other':>5} {'exc':>5} {'p50ms':>7} {'p95ms':>7}")
    for k, v in stats.items():
        lat = v["lat"]
        p50 = statistics.median(lat) if lat else 0
        p95 = (sorted(lat)[int(len(lat) * 0.95)] if len(lat) >= 2 else (lat[0] if lat else 0))
        print(f"{k:30} {v['ok']:>5} {v['arena_busy']:>5} {v['other']:>5} {v['exc']:>5} {p50:>7.1f} {p95:>7.1f}")
        if v['other_codes']:
            print(f"    other_codes: {v['other_codes']}")
        if v['exc_types']:
            print(f"    exc_types: {v['exc_types']}")
    # dump JSON for parsing
    out = {"users": users, "elapsed": elapsed, "base": BASE,
           "stats": {k: {**{kk: vv for kk, vv in v.items() if kk != "lat"},
                        "n": len(v["lat"]),
                        "p50": statistics.median(v["lat"]) if v["lat"] else 0,
                        "p95": (sorted(v["lat"])[int(len(v["lat"]) * 0.95)] if len(v["lat"]) >= 2 else (v["lat"][0] if v["lat"] else 0))}
                     for k, v in stats.items()}}
    print(json.dumps(out))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--users", type=int, default=25)
    ap.add_argument("--cleanup", action="store_true")
    args = ap.parse_args()
    if args.cleanup:
        cleanup()
        print("cleaned up TEST-iter115-*")
    else:
        asyncio.run(main(args.users))
