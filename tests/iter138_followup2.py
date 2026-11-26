# Iteration 138 follow-up 2: verify C new-day behaviour + D style preview after proper navigation.
import asyncio, os, sys, json
from playwright.async_api import async_playwright
sys.path.insert(0, "/app/tests")
from misfire_fixture import fake_aits
from aits_board_fixture import fake_board
from rf_daily_fixture import fake_daily_done, count_sounds, sounds

BASE = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "https://jeelive-feature-book--3o05z2vs.preview.emergentagent.com").rstrip("/")
PHONE, PIN = "7004186276", "5524"


async def vis(page, tid):
    el = await page.query_selector(f'[data-testid="{tid}"]')
    return bool(el and await el.is_visible())


async def main():
    out = {}
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 390, "height": 844})
        page = await ctx.new_page()
        await fake_aits(page, "done")
        await fake_board(page)
        await fake_daily_done(page)
        await count_sounds(page)

        await page.goto(f"{BASE}/entry", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        await page.click('[data-testid="entry-phone-input"]', force=True)
        await page.keyboard.type(PHONE, delay=60)
        await page.click('[data-testid="entry-pin-input"]', force=True)
        await page.keyboard.type(PIN, delay=60)
        await page.click('[data-testid="entry-continue-button"]', force=True)
        await page.wait_for_timeout(7500)

        # Go to Rapid Fire lobby via home
        if await vis(page, "tab-rapid"):
            await page.click('[data-testid="tab-rapid"]', force=True)
            await page.wait_for_timeout(3500)
        out["lobby_visible"] = await vis(page, "rf-all-india")
        out["style_pill_visible"] = await vis(page, "rf-all-india-style")

        # ---- D: Styles page, preview sound (and NOT limited to once-a-day) ----
        if await vis(page, "rf-all-india-style"):
            await page.click('[data-testid="rf-all-india-style"]', force=True)
            await page.wait_for_timeout(3000)
            out["styles_page_open"] = await vis(page, "rf-daily-styles")
            tids = await page.evaluate("""() => Array.from(document.querySelectorAll('[data-testid^="rf-daily-style-"]')).map(e => e.getAttribute('data-testid'))""")
            out["style_tids"] = tids
            await page.evaluate("window.__plays = []")
            card_tids = [t for t in tids if t.startswith("rf-daily-style-card-")]
            if card_tids:
                # pick a style not in use (second one)
                await page.click(f'[data-testid="{card_tids[1]}"]', force=True)
                await page.wait_for_timeout(1500)
                out["style_tap_sounds_1"] = await sounds(page)
                await page.evaluate("window.__plays = []")
                # Tap same again -> preview should play again (not daily-limited)
                await page.click(f'[data-testid="{card_tids[2]}"]', force=True)
                await page.wait_for_timeout(1500)
                out["style_tap_sounds_2"] = await sounds(page)
            # back to lobby via back
            try:
                await page.go_back()
                await page.wait_for_timeout(2000)
            except Exception:
                pass

        # ---- C new-day: set old date in localStorage, reload, then navigate lobby -> daily ----
        await page.evaluate('localStorage.setItem("rf.heard.v1", JSON.stringify(JSON.stringify({card: "2000-01-01", charge: "2000-01-01"})))')
        await page.evaluate("location.reload()")
        await page.wait_for_timeout(6000)
        # If we reload while on lobby, we need to be at lobby; otherwise navigate via tab-rapid
        out["newday_url"] = page.url
        if not await vis(page, "rf-all-india"):
            # try navigating
            if await vis(page, "tab-rapid"):
                await page.click('[data-testid="tab-rapid"]', force=True)
                await page.wait_for_timeout(3500)
        # measure sounds since reload
        card_sounds_after_reload = await sounds(page)
        out["sounds_after_newday_reload"] = card_sounds_after_reload
        # Now open daily result
        if await vis(page, "rf-all-india"):
            await page.evaluate("window.__plays = []")
            await page.click('[data-testid="rf-all-india"]', force=True)
            await page.wait_for_timeout(3500)
            if await vis(page, "rf-daily-popup"):
                await page.click('[data-testid="rf-daily-popup-enter"]', force=True)
                await page.wait_for_timeout(3500)
            out["sounds_after_newday_open"] = await sounds(page)

        print(json.dumps(out, indent=2))
        await browser.close()


asyncio.run(main())
