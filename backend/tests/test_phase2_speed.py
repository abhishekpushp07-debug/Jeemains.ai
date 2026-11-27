"""Phase 2 (Levels 3-4): the split server and the speed parts.

- Weak lists: after the first full pass, a finished round is added on its own (incremental) and gives exactly what a
  fresh full pass gives; a round recorded late (it sorts before rounds already read) makes a full pass again.
- Public caches: a copy past its time answers once more while one reload runs behind it.
- Shared passes (boards): a quick pass is waited for; a slow one runs in the background while the old copy answers.
- The server file only wires things together; every route is still there.

Scratch database only (`<DB_NAME>_phase2_selftest`, a new TEST uid every run; nothing live is touched, nothing is deleted).
Run:  cd /app/backend && python -m pytest tests/test_phase2_speed.py -q
"""
import asyncio
import os
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv
from pymongo import AsyncMongoClient

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

import revision  # noqa: E402
from database import Collections  # noqa: E402
from metadata_cache import MetadataCache  # noqa: E402
from shared_pass import QUICK, SharedPass  # noqa: E402


def run(coro):
    return asyncio.run(coro)


def event(uid, ref, at, rows):
    return {"uid": uid, "ref": ref, "exam": "JEE", "completed_at": at,
            "results": [{"card_id": c, "subject": "Physics", "chapter": ch, "outcome": o} for c, ch, o in rows]}


def full(marks):
    return sorted(tuple(m) for m in marks)


def test_incremental_card_marks_equal_a_full_pass():
    async def main():
        client = AsyncMongoClient(os.environ["MONGO_URL"])
        db = Collections(client[os.environ["DB_NAME"] + "_phase2_selftest"])  # one collection object, so the count below sees every pass
        uid = f"TEST-p2-{uuid.uuid4().hex[:8]}"
        try:
            await db.rf_learning_events.insert_many([
                event(uid, "solo:a", "2026-11-20T10:00:00+00:00", [("c1", "Optics", "incorrect"), ("c2", "Optics", "correct")]),
                event(uid, "solo:b", "2026-11-20T11:00:00+00:00", [("c1", "Optics", "timed_out"), ("c3", "Waves", "incorrect")]),
            ])
            first = await revision.card_marks(db, uid, "JEE")
            assert {m.card: (m.latest, m.tries, m.misses) for m in first} == {"c1": ("timed_out", 2, 2), "c2": ("correct", 1, 0), "c3": ("incorrect", 1, 1)}
            # A new round that comes after the others: added on its own, same answer as a full pass.
            await db.rf_learning_events.insert_one(event(uid, "duel:c", "2026-11-20T12:00:00+00:00", [("c1", "Optics", "correct"), ("c4", "Heat", "incorrect")]))
            calls = []
            aggregate = db.rf_learning_events.aggregate

            async def counted(*a, **kw):
                calls.append(1)
                return await aggregate(*a, **kw)
            db.rf_learning_events.aggregate = counted
            step = await revision.card_marks(db, uid, "JEE")
            assert calls == [], "a round after the others must not make a full pass"
            revision._marks.clear()
            assert full(step) == full(await revision.card_marks(db, uid, "JEE")) and calls == [1]
            # A round recorded late (it sorts before the newest already read): a full pass again, still the same answer.
            await db.rf_learning_events.insert_one(event(uid, "duel:late", "2026-11-20T09:00:00+00:00", [("c3", "Waves", "correct"), ("c5", "Heat", "timed_out")]))
            late = await revision.card_marks(db, uid, "JEE")
            assert calls == [1, 1]
            revision._marks.clear()
            assert full(late) == full(await revision.card_marks(db, uid, "JEE"))
            assert {m.card: m.latest for m in late}["c3"] == "incorrect"  # the late round was played first: c3's latest stays wrong
        finally:
            await client.close()  # the scratch rows stay (a new uid every run), nothing is deleted
    run(main())


def test_public_cache_answers_past_its_time_while_one_reload_runs():
    async def main():
        cache, loads = MetadataCache(), []

        async def load():
            loads.append(time.monotonic())
            await asyncio.sleep(0.05)
            return {"n": len(loads)}
        assert (await cache.get_or_load("k", load, ttl=0.1)) == ({"n": 1}, "MISS")
        assert (await cache.get_or_load("k", load, ttl=0.1))[1] == "HIT-MEMORY"
        await asyncio.sleep(0.12)  # past its time, inside the grace
        stale = await asyncio.gather(*(cache.get_or_load("k", load, ttl=0.1) for _ in range(5)))
        assert all(v == ({"n": 1}, "HIT-STALE") for v in stale) and len(loads) == 2  # five answers, one reload behind
        await asyncio.sleep(0.08)
        assert (await cache.get_or_load("k", load, ttl=0.1)) == ({"n": 2}, "HIT-MEMORY")
        await asyncio.sleep(0.25)  # past the grace too: waited for again
        assert (await cache.get_or_load("k", load, ttl=0.1)) == ({"n": 3}, "MISS")
        await cache.invalidate_prefix("k")
        assert (await cache.get_or_load("k", load, ttl=0.1))[1] == "MISS"  # a bank change is never answered from the old copy
    run(main())


def test_shared_pass_waits_for_quick_and_runs_slow_in_background():
    async def main():
        state = {"delay": 0.0, "n": 0}

        async def load(_):
            await asyncio.sleep(state["delay"])
            state["n"] += 1
            return state["n"]
        quick = SharedPass(load, keep=0.05)
        assert await quick.get("k") == 1
        await asyncio.sleep(0.06)
        assert await quick.get("k") == 2  # a quick pass is waited for: always fresh
        state["delay"] = QUICK * 3
        await asyncio.sleep(0.06)
        assert await quick.get("k") == 3  # this pass was slow (waited for once, then marked)
        await asyncio.sleep(0.06)
        began = time.monotonic()
        assert await quick.get("k") == 3 and time.monotonic() - began < QUICK  # old copy answers at once, the pass runs behind
        await asyncio.sleep(QUICK * 4)
        assert await quick.get("k") == 4
    run(main())


def test_server_only_wires_things_together():
    import server
    src = (ROOT / "server.py").read_text()
    assert len(src.splitlines()) < 200
    for name in ("database.py", "jl_proxy.py", "card_bank.py", "sprints.py", "db_setup.py", "jobs.py", "shared_pass.py"):
        assert (ROOT / name).exists(), name
    paths = {getattr(r, "path", "") for r in server.app.routes}
    for path in ("/api/jl/{path:path}", "/api/rf/catalog", "/api/rf/sessions", "/api/rf/sessions/{sid}/complete", "/api/rf/history",
                 "/api/rf/sessions/{sid}", "/api/rf/daily", "/api/rf/duels", "/api/rf/leaderboard", "/api/rf/league/gangwar", "/api/health/load", "/health"):
        assert path in paths, path
    # 144 after the split + the App Health page and its data (Phase 3) = 146, + the 15 of what came after (none removed,
    # compared route by route on 26 Nov 2026): app switches, the CEO page (2), Student Choice (2), Matched (3),
    # health alerts (2), rank cutoff (3), All India misses, removing a dream mock. + 2 on 27 Nov 2026 (none removed, compared
    # route by route): GET /api/app/classes (Class 11 / Class 12 list) and GET /api/rf/name (the student's own name).
    assert len(server.app.routes) == 163
