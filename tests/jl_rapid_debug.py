# Debug: Rapid tab first Store click + browser back from /rapid/gang/new. READ ONLY (same guards as the other checks).
import asyncio
import sys

sys.path.insert(0, "/app/tests")
from playwright.async_api import async_playwright  # noqa: E402
from shine_helpers import sign_in  # noqa: E402
from misfire_mock_check import BASE, check, guards  # noqa: E402
import jl_tracker_full_check as J  # noqa: E402


def feats(i):
    return [e["props"].get("feature") for e in J.SENT[i:] if e.get("event_name") == "feature_entry_viewed"]


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844})
        await ctx.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => false })")
        await guards(ctx)
        await J.collector(ctx)
        page = await ctx.new_page()
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await sign_in(page, width=390)
        await page.wait_for_timeout(4000)
        j = len(J.SENT)
        await page.click('[data-testid="tab-rapid"]', force=True)
        await page.wait_for_selector('[data-testid="arena-tab-store"]', timeout=30000)
        await page.wait_for_timeout(2000)
        if await page.locator('[data-testid="rf-daily-popup-exit"]').count():  # All India Rapid's daily popup covers the tab
            await page.click('[data-testid="rf-daily-popup-exit"]', force=True)
            await page.wait_for_timeout(1500)
        loc = page.locator('[data-testid="arena-tab-store"]')
        print("store tabs:", await loc.count(), [await loc.nth(i).is_visible() for i in range(await loc.count())],
              "popup left:", await page.locator('[data-testid="rf-daily-popup"]').count())
        print("on rapid ->", feats(j), "selected:", await page.locator('[data-testid="arena-tab-store"]').get_attribute("aria-selected"))
        j = len(J.SENT)
        await page.click('[data-testid="arena-tab-store"]')
        await page.wait_for_timeout(7000)
        check("first store click -> store", feats(j) == ["store"], feats(j))
        await page.click('[data-testid="arena-tab-gang"]')
        await page.wait_for_timeout(3000)
        await page.click('[data-testid="rf-new-gang"]')
        await page.wait_for_timeout(4000)
        print("url", page.url)
        await page.go_back()
        await page.wait_for_timeout(5000)
        print("after back url", page.url, "tab-index count", await page.locator('[data-testid="tab-index"]').count())
        await page.screenshot(path="/tmp/jl_after_back.jpg", quality=40, type="jpeg")
        await b.close()


asyncio.run(main())
