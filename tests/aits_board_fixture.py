# AITS Leaderboard UI checks: test-only Playwright helper (import into browser automation). Nothing here changes the app
# and nothing reaches the website: the browser itself answers GET /api/jl/attempts/<id>/leaderboard with a stand-in class.
#
# Use with `fake_aits(page)` from /app/tests/misfire_fixture.py (stand-in All India days), registered BEFORE this one:
#     await fake_aits(page, "done"); await fake_board(page)
# Each day gets its own class size and its own Rank for the learner, so switching the day visibly changes the board.
# `state` other than "ready" (for example "preparing") shows the waiting card. `fail=True` answers 500 (the error card).
import json
import re
from urllib.parse import parse_qs, urlparse

NAMES = ["Aarav Sharma", "Diya Patel", "Kabir Singh", "Ananya Iyer", "Vivaan Gupta", "Ishita Reddy", "Arjun Nair", "Meera Joshi", "Rohan Das",
         "Saanvi Kulkarni", "Aditya Verma", "Tanvi Menon", "Krish Malhotra", "Riya Banerjee", "Dev Chauhan", "Nisha Pillai", "Yash Thakur"]


def _row(rank, n, you_rank):
    named = rank % 4 != 0 and rank != you_rank
    name = NAMES[(rank * 7) % len(NAMES)] if named else "Learner %08X" % ((rank * 2654435761) % 2 ** 32)
    score = 288 - 3 * (rank - 1) if rank <= 60 else max(-15, 111 - (rank - 60) // max(1, n // 130))
    return {"rank": rank, "name": name, "named": named, "handle": "%016x" % ((rank * 0x9E3779B97F4A7C15) % 2 ** 64), "score": score,
            "attempted": 75 - rank % 9, "accuracy": round(max(20.0, 96 - rank * 0.4), 1), "time": 9000 + (rank * 137) % 1700, "is_you": rank == you_rank}


def build(attempt_id, q="", n=4310, you_rank=12, state="ready"):
    shift = sum(attempt_id.encode()) % 30
    n, you_rank = n + shift * 17, min(n, you_rank + shift)
    if state != "ready":
        return {"state": state, "n": n, "title": "All India JEE Mains", "rows": [], "around": [], "found": [], "you": None, "query": q, "min_finishers": 10}
    rows = [_row(r, n, you_rank) for r in range(1, min(n, 50) + 1)]
    around = [_row(r, n, you_rank) for r in range(max(1, you_rank - 3), min(n, you_rank + 3) + 1)]
    if q.isdigit():
        found = [_row(int(q), n, you_rank)] if 1 <= int(q) <= n else []
    elif q:
        found = [r for r in (_row(k, n, you_rank) for k in range(1, min(n, 400) + 1)) if q.lower() in r["name"].lower()][:20]
    else:
        found = []
    return {"state": "ready", "n": n, "title": "All India JEE Mains · " + attempt_id, "rows": rows, "around": around, "found": found,
            "you": _row(you_rank, n, you_rank), "query": q, "min_finishers": 10}


async def fake_board(page, n=4310, you_rank=12, state="ready", fail=False, calls=None):
    async def handler(route):
        url = urlparse(route.request.url)
        attempt_id = url.path.split("/attempts/")[1].split("/")[0]
        q = parse_qs(url.query).get("q", [""])[0]
        if calls is not None:
            calls.append(attempt_id + ("?q=" + q if q else ""))
        if fail:
            await route.fulfill(status=500, content_type="application/json", body='{"detail":"fixture"}')
            return
        await route.fulfill(status=200, content_type="application/json", body=json.dumps(build(attempt_id, q, n, you_rank, state)))

    await page.route(re.compile(r".*/api/jl/attempts/[^/]+/leaderboard.*"), handler)
