# My Tests after the exam-tab change: Compare selection + Open result (read only; the compare POST is stopped in the
# browser with 418 and listed), search also filters Misfire mocks. usage: python3 my_tests_tabs_check.py [width]
import asyncio
import re
import sys

sys.path.insert(0, "/app/tests")
from dotenv import dotenv_values  # noqa: E402
from playwright.async_api import async_playwright  # noqa: E402
from shine_helpers import sign_in  # noqa: E402

BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
W = int(sys.argv[1]) if len(sys.argv) > 1 else 390
RES, BLOCKED, ERRORS = [], [], []


def check(name, ok, info=""):
    RES.append((name, bool(ok)))
    print(("PASS " if ok else "FAIL ") + name + (" :: " + str(info) if info != "" else ""), flush=True)


def tid(t):
    return f'[data-testid="{t}"]'


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": W, "height": 844})

        async def g(route):
            r = route.request
            if r.method in ("GET", "HEAD", "OPTIONS") or "/api/jl/auth" in r.url:
                await route.fallback(); return
            BLOCKED.append(r.method + " " + r.url.split("?")[0].replace(BASE, ""))
            await route.fulfill(status=418, content_type="application/json", body='{"data":null,"error":{"code":"blocked","message":"blocked by test"},"meta":{}}')
        await ctx.route(re.compile(r".*/api/jl/.*"), g)
        page = await ctx.new_page()
        page.on("pageerror", lambda e: ERRORS.append(str(e)[:200]))
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await sign_in(page, width=W)
        await page.goto(BASE + "/tests", wait_until="domcontentloaded")
        await page.wait_for_selector(tid("my-tests-exam-filters"), timeout=45000)
        await page.click(tid("my-tests-tab-completed"))
        await page.wait_for_timeout(2500)
        sel = page.locator('[data-testid^="compare-select-"]')
        n = await sel.count()
        check("compare selectors on completed attempts", n >= 2, n)
        if n >= 2:
            await sel.nth(0).click(); await sel.nth(1).click()
            await page.wait_for_timeout(500)
            btn = page.locator(tid("compare-attempts-button"))
            check("compare button appears after 2 picks", await btn.count() == 1)
            if await btn.count():
                await btn.click()
                await page.wait_for_timeout(2500)
                sheet = await page.locator(tid("compare-sheet")).count()
                body = await page.inner_text(tid("compare-sheet")) if sheet else ""
                check("compare sheet opens (POST stopped by test -> error state shown)", sheet == 1, body[:140].replace("\n", " "))
                if await page.locator(tid("compare-close")).count():
                    await page.click(tid("compare-close"))
                await page.wait_for_timeout(500)
        # Open result on first attempt (navigation only; Solutions tab not opened)
        act = page.locator('[data-testid^="attempt-action-label-"]').first
        label = await act.inner_text()
        await act.click()
        await page.wait_for_timeout(3000)
        check("'Open result' navigates to /result/", "/result/" in page.url, f"{label} -> {page.url}")
        # search filter
        await page.goto(BASE + "/tests", wait_until="domcontentloaded")
        await page.wait_for_selector(tid("my-tests-search"), timeout=45000)
        await page.fill(tid("my-tests-search"), "zzzz_no_match")
        await page.wait_for_timeout(2500)
        check("search with no match shows empty", await page.locator(tid("my-tests-empty")).count() == 1)
        await page.screenshot(path=f"/app/test_reports/artifacts/my_tests_search_{W}.png", quality=40, type="jpeg")
        await b.close()
    print("BLOCKED", BLOCKED)
    print("PAGEERRORS", ERRORS)
    print(f"{sum(1 for _, ok in RES if ok)}/{len(RES)} passed")

asyncio.run(main())
