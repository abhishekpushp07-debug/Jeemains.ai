# JLive Command tracker (src/jlTracker.ts) in the browser preview, READ ONLY.
# The collector (student-radar-5) is answered by the browser: nothing reaches the real dashboard. Every write to the
# website outside /auth is stopped (same stand-ins as misfire_mock_check.py).
# usage: python3 jl_tracker_check.py [path ...]   (extra paths are opened after sign-in and their events printed)
import asyncio
import json
import re
import sys

sys.path.insert(0, "/app/tests")
from playwright.async_api import async_playwright  # noqa: E402
from shine_helpers import sign_in  # noqa: E402
from misfire_mock_check import BASE, BLOCKED, ERRORS, RES, check, guards  # noqa: E402

SENT, HEADERS = [], []
PII = re.compile(r"(\+91)?[6-9]\d{9}|@[a-z0-9-]+\.[a-z]|\bpin\b|password|token", re.I)


async def collector(ctx):
    async def g(route):
        r = route.request
        if r.method == "POST":
            HEADERS.append(dict(r.headers))
            try:
                body = json.loads(r.post_data or "{}")
                SENT.extend(body.get("events") or [])
            except Exception:
                pass
        await route.fulfill(status=200, content_type="application/json", body='{"ok":true}',
                            headers={"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "*", "Access-Control-Allow-Methods": "POST, OPTIONS"})
    await ctx.route(re.compile(r"https://student-radar-5\.emergent\.host/.*"), g)


def names():
    return [e.get("event_name") for e in SENT]


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        # An automated browser is not counted by the app: nothing may be sent at all.
        robot = await b.new_context(viewport={"width": 390, "height": 844})
        await collector(robot)
        rp = await robot.new_page()
        await rp.goto(BASE + "/", wait_until="domcontentloaded")
        await rp.wait_for_selector('[data-testid="entry-phone-input"]', timeout=60000)
        await rp.wait_for_timeout(9000)
        check("automated browser sends nothing", not SENT and not HEADERS, len(SENT))
        await robot.close()
        # From here the browser says it is not automated, as a student's browser does.
        ctx = await b.new_context(viewport={"width": 390, "height": 844})
        await ctx.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => false })")
        await guards(ctx)
        await collector(ctx)
        page = await ctx.new_page()
        page.on("pageerror", lambda e: ERRORS.append(str(e)[:200]))
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await sign_in(page, width=390)
        for p in sys.argv[1:]:
            before = len(SENT)
            await page.goto(BASE + p, wait_until="domcontentloaded")
            await page.wait_for_timeout(9000)
            print(p, "->", [(e["event_name"], e.get("props")) for e in SENT[before:]])
        await page.wait_for_timeout(8000)
        n = names()
        print("events:", n)
        for want in ("app_open", "session_start", "screen_view", "identify"):
            check(f"{want} sent", want in n)
        ids = [e for e in SENT if e.get("event_name") == "identify"]
        check("identify carries a website uid", bool(ids) and re.fullmatch(r"[0-9a-f-]{36}", ids[-1].get("uid") or "") is not None, ids[-1].get("uid") if ids else None)
        check("public key header only", all(h.get("x-jl-key", "").startswith("pk_") for h in HEADERS) and not any("sk_" in json.dumps(h) for h in HEADERS))
        blob = json.dumps(SENT)
        check("no phone / email / pin / token in events", not PII.search(blob), PII.search(blob).group(0) if PII.search(blob) else "")
        check("identify once per app run", n.count("identify") == n.count("app_open"), f"{n.count('identify')} / {n.count('app_open')}")
        await b.close()
    print("BLOCKED", BLOCKED)
    print("PAGEERRORS", ERRORS)
    print(f"{sum(1 for _, ok in RES if ok)}/{len(RES)} passed")

asyncio.run(main())
