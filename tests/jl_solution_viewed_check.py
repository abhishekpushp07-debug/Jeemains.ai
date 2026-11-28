# solution_viewed {set_id, question_no} on a finished result's Solutions tab. READ ONLY: solution-open POST stopped in the browser.
import asyncio
import re
import sys

sys.path.insert(0, "/app/tests")
from playwright.async_api import async_playwright  # noqa: E402
from shine_helpers import sign_in  # noqa: E402
from misfire_mock_check import BASE, BLOCKED, RES, check, guards  # noqa: E402
import jl_tracker_full_check as J  # noqa: E402

STOPPED = []
AID, SID = "1ea510f2-1d2a-41f7-9bb4-a8b28c16f98f", "jee-main-pyq-2025-01-22-s2"  # QA learner's finished JEE Main PYQ (from My Tests completed)


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844})
        await ctx.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => false })")
        await guards(ctx)
        await J.collector(ctx)

        async def stop(route):
            if route.request.method != "GET":
                STOPPED.append(route.request.method + " " + route.request.url.split("?")[0].replace(BASE, ""))
                await route.fulfill(status=418, content_type="application/json", body='{"data":null,"error":{"code":"blocked","message":"blocked by test"},"meta":{}}')
            else:
                await route.fallback()
        await ctx.route(re.compile(r".*/solution-open.*"), stop)  # registered last = runs first
        page = await ctx.new_page()
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await sign_in(page, width=390)
        await page.wait_for_timeout(3000)
        i = await J.goto(page, f"/result/{AID}", 12000)
        await page.click('[data-testid="result-tab-solutions"]', force=True)
        await page.wait_for_timeout(8000)
        sv = J.since(i, "solution_viewed")
        print("events:", J.since(i))
        check("solution_viewed {set_id, question_no}", bool(sv) and sv[0][1].get("set_id") == SID and isinstance(sv[0][1].get("question_no"), int) and set(sv[0][1]) == {"set_id", "question_no"}, sv)
        check("solution-open POST stopped (never reached website)", bool(STOPPED) and all("solution-open" in s for s in STOPPED), STOPPED)
        await page.screenshot(path="/tmp/jl_solutions.png", quality=40, type="jpeg")
        await b.close()
    print("BLOCKED", BLOCKED)
    print(f"{sum(1 for _, ok in RES if ok)}/{len(RES)} passed")

asyncio.run(main())
