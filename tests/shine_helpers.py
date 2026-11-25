# Test-only helpers for the browser checks of the AITS shine / name / share / overall Rank work (26 Nov 2026).
# Nothing here changes the app. The stand-ins answer in the browser only; nothing reaches the website.
#
#   sys.path.insert(0, "/app/tests"); from shine_helpers import *
#   await sign_in(page)                      # the QA learner, with stand-in All India days and a stand-in class
#   await fake_name(page, calls)             # the browser answers PUT /profile/display-name (no real name is changed)
#   await fake_overall(page)                 # the browser answers GET /series/all-india-jee/leaderboard (the website has none yet)
import json
import re
import sys
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, "/app/tests")
from aits_board_fixture import NAMES, build, fake_board  # noqa: E402
from misfire_fixture import fake_aits  # noqa: E402

PHONE, PIN = "7004186276", "5524"


async def sign_in(page, aits="done", board=True, width=390, height=844, **board_args):
    """Signs the QA learner in from the entry screen. Stand-ins are registered first, so no stand-in day ever asks the website."""
    await page.set_viewport_size({"width": width, "height": height})
    await page.wait_for_selector('[data-testid="entry-phone-input"]', timeout=60000)
    if aits:
        await fake_aits(page, aits)
    if board:
        await fake_board(page, **board_args)
    await page.fill('[data-testid="entry-phone-input"]', PHONE)
    await page.fill('[data-testid="entry-pin-input"]', PIN)
    # The button rests until the app has finished checking for an old session.
    await page.wait_for_selector('[data-testid="entry-continue-button"]:not([aria-disabled="true"])', timeout=45000)
    await page.click('[data-testid="entry-continue-button"]')
    await page.wait_for_selector('[data-testid="home-tile-choice"]', timeout=45000)


async def fake_name(page, calls=None, fail=None, state=None):
    """PUT /profile/display-name answered by the browser, in the website's own words (seen for real on 26 Nov 2026).
    `state` = a dict shared with `fake_board_named`, so the board shows the saved name afterwards. `fail` = (status, message)."""
    async def handler(route):
        req = route.request
        if req.method != "PUT":
            await route.continue_()
            return
        name = (json.loads(req.post_data or "{}").get("name") or "").strip()
        if calls is not None:
            calls.append(name)
        if fail:
            body = {"data": None, "error": {"code": "http_%d" % fail[0], "message": fail[1]}, "meta": {"api_version": "1"}}
            await route.fulfill(status=fail[0], content_type="application/json", body=json.dumps(body))
            return
        if name and not re.fullmatch(r"[^\W_][\w ]{1,19}", name):
            body = {"data": None, "error": {"code": "http_422", "message": "Naam 2 se 20 akshar ka rakho: sirf akshar, ank aur space."}, "meta": {"api_version": "1"}}
            await route.fulfill(status=422, content_type="application/json", body=json.dumps(body))
            return
        if state is not None:
            state["name"] = name
        await route.fulfill(status=200, content_type="application/json",
                            body=json.dumps({"data": {"display_name": name}, "error": None, "meta": {"api_version": "1"}}))

    await page.route("**/api/jl/profile/display-name", handler)


async def fake_board_named(page, state, n=4310, you_rank=12, calls=None):
    """Like fake_board, but the learner's own row carries state["name"] once a name is saved (register INSTEAD of fake_board)."""
    def mine(row):
        if row.get("is_you") and state.get("name"):
            row.update(name=state["name"], named=True)
        return row

    async def handler(route):
        url = urlparse(route.request.url)
        attempt_id = url.path.split("/attempts/")[1].split("/")[0]
        q = parse_qs(url.query).get("q", [""])[0]
        if calls is not None:
            calls.append(attempt_id + ("?q=" + q if q else ""))
        d = build(attempt_id, q, n, you_rank)
        for key in ("rows", "around", "found"):
            d[key] = [mine(r) for r in d[key]]
        if d.get("you"):
            mine(d["you"])
        await route.fulfill(status=200, content_type="application/json", body=json.dumps(d))

    await page.route(re.compile(r".*/api/jl/attempts/[^/]+/leaderboard.*"), handler)


def overall(q="", n=5120, you_rank=9, days=12, state="ready"):
    """The whole-series leaderboard exactly as asked for in /app/memory/WEBSITE_SERIES_RANK_NOTE.md."""
    def row(rank):
        named = rank % 5 != 0 and rank != you_rank
        took = max(1, days - rank % 4)
        return {"rank": rank, "name": NAMES[(rank * 5) % len(NAMES)] if named else "Learner %08X" % ((rank * 40503) % 2 ** 32), "named": named,
                "handle": "%016x" % ((rank * 0xC2B2AE3D27D4EB4F) % 2 ** 64), "score": max(0, 281 * days - 37 * (rank - 1)), "days": took,
                "attempted": 70 * took, "accuracy": round(max(20.0, 95 - rank * 0.3), 1), "time": 9500 * took, "is_you": rank == you_rank}
    base = {"state": state, "n": n, "title": "All India JEE Mains · poori series", "days_counted": days, "maximum": 300 * days, "query": q, "min_finishers": 10}
    if state != "ready":
        return {**base, "rows": [], "around": [], "found": [], "you": None}
    if q.isdigit():
        found = [row(int(q))] if 1 <= int(q) <= n else []
    elif q:
        found = [r for r in (row(k) for k in range(1, 300)) if q.lower() in r["name"].lower()][:20]
    else:
        found = []
    return {**base, "rows": [row(r) for r in range(1, 51)], "around": [row(r) for r in range(max(1, you_rank - 3), you_rank + 4)], "found": found, "you": row(you_rank)}


async def fake_overall(page, calls=None, status=200, body=None, **args):
    """GET /series/all-india-jee/leaderboard answered by the browser. Register AFTER fake_aits (the later route wins).
    `status` 404 = the website as it is today; `body` = any other answer (to check that a wrong shape stays hidden)."""
    async def handler(route):
        q = parse_qs(urlparse(route.request.url).query).get("q", [""])[0]
        if calls is not None:
            calls.append(q)
        if status != 200:
            await route.fulfill(status=status, content_type="application/json", body='{"detail":"Not Found"}')
            return
        await route.fulfill(status=200, content_type="application/json", body=json.dumps(body if body is not None else overall(q, **args)))

    await page.route(re.compile(r".*/api/jl/series/all-india-jee/leaderboard.*"), handler)


async def shot(page, name):
    await page.screenshot(path="/tmp/shots/%s.jpg" % name, type="jpeg", quality=20, full_page=False)
