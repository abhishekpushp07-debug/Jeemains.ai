# Focused re-check: feature_entry_viewed for the Rapid Store tab and sub-pages (misfire -> /misfire/mock/new). READ ONLY.
import asyncio
import sys

sys.path.insert(0, "/app/tests")
from playwright.async_api import async_playwright  # noqa: E402
from shine_helpers import sign_in  # noqa: E402
from misfire_mock_check import BASE, RES, check, guards  # noqa: E402
import jl_tracker_full_check as J  # noqa: E402  (main guarded below)


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844})
        await ctx.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => false })")
        await guards(ctx)
        await J.collector(ctx)
        page = await ctx.new_page()
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await page.wait_for_timeout(7000)
        first = [e for e in J.SENT if e.get("event_name") == "screen_view"]
        check("the first screen is counted (screen_view on opening)", bool(first), [e.get("context", {}).get("screen") for e in J.SENT][:5])
        await sign_in(page, width=390)
        await page.wait_for_timeout(4000)
        # misfire sub-page
        await J.goto(page, "/misfire", 8000)
        cta = page.locator('[data-testid="misfire-mock-cta"]')
        if await cta.count():
            j = len(J.SENT)
            await cta.click(force=True)
            await page.wait_for_timeout(7000)
            check("B2 /misfire -> sub-page no 2nd misfire entry", "/misfire/" in page.url and not J.since(j, "feature_entry_viewed"), (page.url, J.since(j)))
        else:
            print("misfire-mock-cta absent (no open misfires)")
        # Rapid tab: store, trophy, store, then home tab and back
        await J.goto(page, "/", 6000)
        await page.click('[data-testid="tab-rapid"]', force=True)
        await page.wait_for_timeout(6000)
        if await page.locator('[data-testid="rf-daily-popup-exit"]').count():  # All India Rapid's daily popup covers the tab
            await page.click('[data-testid="rf-daily-popup-exit"]', force=True)
            await page.wait_for_timeout(1500)
        await page.screenshot(path="/tmp/jl_rapid_lobby.png", quality=40, type="jpeg")
        expect = {"store": ["store"], "arena": [], "trophy": ["leagues"], "gang": ["gangs"]}
        for key in ("store", "arena", "store", "trophy", "gang"):
            j = len(J.SENT)
            await page.click(f'[data-testid="arena-tab-{key}"]', force=True)
            await page.wait_for_timeout(7000)
            got = [e["props"].get("feature") for e in J.SENT[j:] if e.get("event_name") == "feature_entry_viewed"]
            check(f"rapid tab {key} -> {expect[key]}", got == expect[key], got)
        # gang tab, then a gang page, then back: still the one entry into gangs
        j = len(J.SENT)
        await page.click('[data-testid="rf-new-gang"]', force=True)
        await page.wait_for_timeout(7000)
        check("gang tab -> /rapid/gang/new: no 2nd gangs entry", "/rapid/gang/new" in page.url and not J.since(j, "feature_entry_viewed"), (page.url, J.since(j, "feature_entry_viewed")))
        j = len(J.SENT)
        await page.go_back()
        await page.wait_for_timeout(7000)
        check("back to the gang tab: no 2nd gangs entry", not J.since(j, "feature_entry_viewed"), J.since(j, "feature_entry_viewed"))
        j = len(J.SENT)
        await page.click('[data-testid="arena-tab-home"]', force=True)  # the Rapid screen's own bar: Home leaves Rapid Fire
        await page.wait_for_timeout(2500)
        await page.click('[data-testid="tab-rapid"]', force=True)
        await page.wait_for_timeout(7000)
        got = [e["props"].get("feature") for e in J.SENT[j:] if e.get("event_name") == "feature_entry_viewed"]
        check("home -> rapid (gang still selected) = a new gangs entry", got == ["gangs"], got)
        await b.close()
    print(f"{sum(1 for _, ok in RES if ok)}/{len(RES)} passed")

asyncio.run(main())
