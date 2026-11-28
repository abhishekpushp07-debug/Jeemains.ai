# Offline Misfire (Pocket 1) — extra checks 2 by the testing agent, READ ONLY for the QA learner.
#   python3 /app/tests/iter_offline_misfire_extra2.py
# - cold load of /misfire/mock/new with a line never flashes the phone notice (fix 1 of the main agent)
# - website list down -> phone notice; "Website se dobara laao" with the list back -> website list (notice gone)
# - AITS screens (series-analysis, series-leaderboard) open read-only without page errors
import asyncio
import re
import sys
import time

sys.path.insert(0, "/app/tests")
from dotenv import dotenv_values  # noqa: E402
from playwright.async_api import async_playwright  # noqa: E402
from shine_helpers import sign_in  # noqa: E402

BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
RES, BLOCKED, ERRORS = [], [], []


def check(name, ok, info=""):
    RES.append((name, bool(ok)))
    print(("PASS " if ok else "FAIL ") + name + (" :: " + str(info) if info != "" else ""), flush=True)


def tid(t):
    return f'[data-testid="{t}"]'


async def txt(page, t):
    loc = page.locator(tid(t))
    return (await loc.first.inner_text()).strip() if await loc.count() else ""


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844})

        async def g(route):
            r = route.request
            if r.method in ("GET", "HEAD", "OPTIONS") or "/api/jl/auth" in r.url:
                await route.fallback(); return
            BLOCKED.append(r.method + " " + r.url.split("?")[0].replace(BASE, ""))
            await route.fulfill(status=418, content_type="application/json", body='{"data":null,"error":{"code":"blocked","message":"blocked"},"meta":{}}')
        await ctx.route(re.compile(r".*/api/jl/.*"), g)
        page = await ctx.new_page()
        page.on("pageerror", lambda e: ERRORS.append(str(e)[:200]))
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await sign_in(page, width=390)
        await page.wait_for_timeout(60000)  # let the keeper keep the finished paper

        # 1. Cold load with a line: never the phone notice.
        await page.goto(BASE + "/misfire/mock/new", wait_until="domcontentloaded")
        seen, t0 = False, time.time()
        while time.time() - t0 < 25:
            if await page.locator(tid("mock-new-phone")).count():
                seen = True; break
            if await page.locator(tid("mock-new-count")).count() and time.time() - t0 > 8:
                break
            await page.wait_for_timeout(150)
        check("C1 cold load online: website list, phone notice never shown", not seen and await page.locator(tid("mock-new-count")).count() > 0, await txt(page, "mock-new-open-physics"))

        # 2. List down -> phone; retry with the list back -> website list.
        state = {"down": True}

        async def down(route):
            if state["down"]:
                await route.fulfill(status=503, content_type="application/json", body='{"data":null,"error":{"code":"down","message":"down"},"meta":{}}')
            else:
                await route.fallback()
        await page.route(re.compile(r".*/api/jl/my/misfire\?.*status=open.*"), down)
        await page.goto(BASE + "/misfire/mock/new", wait_until="domcontentloaded")
        try:
            await page.wait_for_selector(tid("mock-new-phone"), timeout=90000)
            ok = True
        except Exception:
            ok = False
        note = await txt(page, "mock-new-phone")
        check("C2 list 503 -> phone notice starts 'Website se list abhi nahi aa paayi.'", ok and note.startswith("Website se list abhi nahi aa paayi."), note)
        check("C3 retry pill visible", await page.locator(tid("mock-new-web-retry")).is_visible() if await page.locator(tid("mock-new-web-retry")).count() else False)
        box = await page.locator(tid("mock-new-web-retry")).bounding_box() if await page.locator(tid("mock-new-web-retry")).count() else None
        print("   retry pill box:", box, flush=True)
        state["down"] = False
        await page.click(tid("mock-new-web-retry"))
        gone = False
        for _ in range(60):
            await page.wait_for_timeout(500)
            if not await page.locator(tid("mock-new-phone")).count() and await page.locator(tid("mock-new-count")).count():
                gone = True; break
        check("C4 retry with the list back -> website list, notice gone", gone, await txt(page, "mock-new-phone"))

        # 3. AITS screens read-only.
        for path in ("/series-analysis", "/series-leaderboard", "/misfire?tab=mock"):
            before = len(ERRORS)
            await page.goto(BASE + path, wait_until="domcontentloaded")
            await page.wait_for_timeout(7000)
            err = await page.evaluate("""() => [...document.querySelectorAll('[data-testid*="error"]')].filter(e => e.offsetParent).map(e => e.innerText.slice(0,80)).join(' | ')""")
            check(f"R {path} opens without errors", len(ERRORS) == before and not err, err or ERRORS[before:][:2])
            await page.screenshot(path=f"/app/test_reports/artifacts/offline_misfire_extra/r{path.replace('/', '_').replace('?', '_')}.jpg", type="jpeg", quality=40)
        check("Z nothing written / no page errors", not BLOCKED and not ERRORS, (BLOCKED[:4], ERRORS[:3]))
        await b.close()
    print(f"\n{sum(1 for _, ok in RES if ok)}/{len(RES)} passed", flush=True)


asyncio.run(main())
