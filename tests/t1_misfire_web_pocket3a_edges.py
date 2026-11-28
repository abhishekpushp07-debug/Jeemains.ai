# T1 edge checks, Misfire Mock Pocket 3a (same stand-ins as t1_misfire_web_pocket3a.py: read only for the QA learner).
#   python3 /app/tests/t1_misfire_web_pocket3a_edges.py
# List error/empty, bank error = switch off, the fewer sheet closed then asked again (same key), Student Choice's
# random mock through the refactored askPaper (door C played by the browser), its 404 sentence.
import asyncio
import sys

sys.path.insert(0, "/app/tests")
import t1_misfire_web_pocket3a as k  # noqa: E402
from playwright.async_api import async_playwright  # noqa: E402

ST, ASKS, tid = k.ST, k.ASKS, k.tid


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        k.ST["switch"] = True
        ctx, page = await k.new_page(b)
        # E1 list error -> misfire-web-error with retry -> list
        ST["list"] = "500"
        await k.goto(page, "/misfire?tab=web", "misfire-web-hero", 45000)
        err = await k.vis(page, "misfire-web-error", 15000)
        k.check("E1 list 500 -> misfire-web-error", err, await k.txt(page, "misfire-web-error"))
        ST["list"] = "ok"
        btn = page.locator('[data-testid="misfire-web-error"] [role="button"], [data-testid^="misfire-web-error-retry"]')
        if await btn.count():
            await btn.first.click()
        else:
            await page.get_by_text("Retry", exact=False).first.click()
        k.check("E2 retry brings the list", await k.vis(page, "misfire-web-t1-unstarted-01", 15000))
        # E3 empty
        ST["list"] = "empty"
        await k.goto(page, "/misfire?tab=web", "misfire-web-hero", 45000)
        k.check("E3 empty list -> misfire-web-empty", await k.vis(page, "misfire-web-empty", 15000), await k.txt(page, "misfire-web-empty"))
        ST["list"] = "ok"
        # E4 fewer sheet closed with X, ask again -> same key
        ST["fewer"] = 3
        await k.goto(page, "/misfire/mock/new?web=1", "mock-new-bar-go", 45000)
        await page.wait_for_timeout(1000)
        await page.click(tid("mock-count-mathematics-10")) if await page.locator(tid("mock-count-mathematics-10")).count() else None
        await page.click(tid("mock-subject-mathematics"))
        await page.click(tid("mock-count-mathematics-10"))
        n = len(ASKS)
        await page.click(tid("mock-new-bar-go"))
        await k.vis(page, "mock-making-fewer-note", 10000)
        closer = page.locator('[data-testid="mock-making-sheet-close"], [data-testid="mock-making-sheet"] [aria-label="Close"]')
        if await closer.count():
            await closer.first.click()
        else:
            await page.keyboard.press("Escape")
        await page.wait_for_timeout(800)
        await page.click(tid("mock-new-bar-go"))
        await k.vis(page, "mock-making-fewer-note", 10000)
        keys = [a.get("request_key") for a in ASKS[n:]]
        k.check("E4 fewer sheet closed, asked again: same request_key", len(keys) == 2 and keys[0] == keys[1], keys)
        ST["fewer"] = 0
        await ctx.close()

        # E5 bank error -> switch counts as off: no Mock tab; ?web=1 is Offline Misfire
        ST["bank_fail"] = True
        ctx, page = await k.new_page(b)
        await k.goto(page, "/misfire?tab=web", "misfire-tab-all", 45000)
        await page.wait_for_timeout(4000)
        t = await k.tabs(page)
        k.check("E5 bank 500: no Mock tab", "Mock" not in t, t)
        await k.goto(page, "/misfire/mock/new?web=1", "mock-new-screen", 45000)
        await page.wait_for_timeout(4000)
        k.check("E6 bank 500: ?web=1 is 'Offline Misfire banao'", "Offline Misfire banao" in await k.txt(page, "mock-new-header"), await k.txt(page, "mock-new-header"))
        ST["bank_fail"] = False
        await ctx.close()

        # E7 Student Choice random mock (website-played door C) through askPaper/makePaper
        ST["bank_extra"] = {"random": True}
        ctx, page = await k.new_page(b)
        await k.goto(page, "/choice", "choice-screen", 45000)
        way = await k.vis(page, "choice-way-random", 20000)
        k.check("E7 random way open when bank.random (misfire on too)", way)
        if way:
            await page.click(tid("choice-way-random"))
            await k.vis(page, "choice-random-input", 8000)
            await page.fill(tid("choice-random-input"), "30")
            ST["papers"] = "404x"  # unknown mode -> agreed success shape
            n = len(ASKS)
            await page.click(tid("choice-random-make"))
            await page.wait_for_timeout(3000)
            body = ASKS[n] if len(ASKS) > n else {}
            k.check("E8 random body {exam, request_key, mode random, count 30}", set(body) == {"exam", "request_key", "mode", "count"} and body.get("mode") == "random" and body.get("count") == 30, body)
            k.check("E9 makePaper -> /set/<set_id>", "/set/t1-made-set-01" in page.url, page.url)
            await k.goto(page, "/choice", "choice-way-random", 45000)
            await page.click(tid("choice-way-random"))
            await k.vis(page, "choice-random-input", 8000)
            await page.fill(tid("choice-random-input"), "30")
            ST["papers"] = "405"
            await page.click(tid("choice-random-make"))
            await k.vis(page, "choice-random-error", 8000)
            e = await k.txt(page, "choice-random-error")
            k.check("E10 Student Choice 405 sentence as before", k.NOTYET in e, e)
            ST["papers"] = "429"
            await page.click(tid("choice-random-make"))
            await page.wait_for_timeout(2500)
            k.check("E11 Student Choice 429 shows website sentence", k.SENT["429"][1] in await k.txt(page, "choice-random-error"), await k.txt(page, "choice-random-error"))
        ST["bank_extra"] = {}
        await ctx.close()
        k.check("Z no page errors", not k.ERRORS, k.ERRORS[:4])
        k.check("Z nothing written to the website", not k.BLOCKED, k.BLOCKED)
        print("INFO dream writes faked:", k.DREAM, flush=True)
        await b.close()
    print(f"\n{sum(1 for _, ok in k.RES if ok)}/{len(k.RES)} passed", flush=True)


asyncio.run(main())
