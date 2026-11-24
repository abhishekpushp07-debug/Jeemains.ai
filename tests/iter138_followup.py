# Iteration 138 follow-up: investigate 4 failing checks (one sign-in).
import asyncio, os, re, sys, json
from playwright.async_api import async_playwright
sys.path.insert(0, "/app/tests")
from misfire_fixture import fake_aits
from aits_board_fixture import fake_board
from rf_daily_fixture import fake_daily_done, count_sounds, sounds

BASE = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "https://scale-engine-50k--0gu36hlx.preview.emergentagent.com").rstrip("/")
PHONE, PIN = "7004186276", "5524"


async def is_visible(page, tid):
    el = await page.query_selector(f'[data-testid="{tid}"]')
    return bool(el and await el.is_visible())


async def main():
    out = {}
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 390, "height": 844})
        page = await ctx.new_page()
        await fake_aits(page, "done")
        await fake_board(page, state="preparing")
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

        # ---- A4 waiting: preparing is active from the start, go /live -> board
        await page.click('[data-testid="home-tile-live"]', force=True)
        await page.wait_for_timeout(2500)
        await page.click('[data-testid="series-open-leaderboard"]', force=True)
        await page.wait_for_timeout(3000)
        wait_vis = await is_visible(page, "aits-board-wait")
        wait_note = await is_visible(page, "aits-board-wait-note")
        out["A4_waiting_default"] = {"wait": wait_vis, "note": wait_note}
        # Also chip-2 switch
        try:
            await page.click('[data-testid="aits-board-chip-2"]', force=True, timeout=3000)
            await page.wait_for_timeout(2500)
            out["A4_waiting_day2"] = {"wait": await is_visible(page, "aits-board-wait")}
        except Exception as e:
            out["A4_waiting_day2"] = {"err": str(e)[:120]}

        # ---- B: now change the board route to 'ready', then switch to wide screen
        await page.unroute(re.compile(r".*/api/jl/attempts/[^/]+/leaderboard.*"))
        await fake_board(page)

        # ---- Rapid Fire: reload behaviour check
        await page.set_viewport_size({"width": 750, "height": 860})
        await page.goto(f"{BASE}/", wait_until="domcontentloaded")
        await page.wait_for_timeout(2500)
        await page.click('[data-testid="tab-rapid"]', force=True)
        await page.wait_for_timeout(3000)
        # open daily result first time -> sounds should play
        await page.click('[data-testid="rf-all-india"]', force=True)
        await page.wait_for_timeout(3000)
        if await is_visible(page, "rf-daily-popup"):
            await page.click('[data-testid="rf-daily-popup-enter"]', force=True)
            await page.wait_for_timeout(3000)
        await page.wait_for_selector('[data-testid="rf-daily-result"]', timeout=8000)
        first_sounds = await sounds(page)
        out["C_first_open_sounds"] = first_sounds

        # Reload while on daily
        await page.evaluate("location.reload()")
        await page.wait_for_timeout(6000)
        reload_url = page.url
        out["C_reload_url"] = reload_url
        out["C_reload_has_tab_rapid"] = await is_visible(page, "tab-rapid")
        out["C_reload_has_rf_all_india"] = await is_visible(page, "rf-all-india")
        out["C_reload_has_daily_result"] = await is_visible(page, "rf-daily-result")
        # If daily-result is visible we are still on daily after reload
        # sounds captured after reload (count_sounds init script survives)
        reload_sounds = await sounds(page)
        out["C_reload_sounds"] = reload_sounds

        # Navigate to /rapid explicitly then open daily again — expect NO sounds (same day)
        try:
            # Go via tab-rapid or direct URL
            if await is_visible(page, "tab-rapid"):
                await page.click('[data-testid="tab-rapid"]', force=True)
            else:
                await page.goto(f"{BASE}/(tabs)/rapid", wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
            # play sounds snapshot
            await page.evaluate("window.__plays = []")
            if await is_visible(page, "rf-all-india"):
                await page.click('[data-testid="rf-all-india"]', force=True)
                await page.wait_for_timeout(3000)
                if await is_visible(page, "rf-daily-popup"):
                    await page.click('[data-testid="rf-daily-popup-enter"]', force=True)
                    await page.wait_for_timeout(3000)
            out["C_same_day_reopen_sounds"] = await sounds(page)
        except Exception as e:
            out["C_same_day_reopen_sounds"] = f"ERR {e}"[:200]

        # New day memory reset
        try:
            await page.evaluate('localStorage.setItem("rf.heard.v1", JSON.stringify(JSON.stringify({card: "2000-01-01", charge: "2000-01-01"})))')
            await page.evaluate("location.reload()")
            await page.wait_for_timeout(6000)
            out["C_newday_url"] = page.url
            if await is_visible(page, "tab-rapid"):
                await page.click('[data-testid="tab-rapid"]', force=True)
                await page.wait_for_timeout(2500)
            await page.evaluate("window.__plays = []")
            if await is_visible(page, "rf-all-india"):
                await page.click('[data-testid="rf-all-india"]', force=True)
                await page.wait_for_timeout(3000)
                if await is_visible(page, "rf-daily-popup"):
                    await page.click('[data-testid="rf-daily-popup-enter"]', force=True)
                    await page.wait_for_timeout(3000)
            out["C_newday_sounds"] = await sounds(page)
        except Exception as e:
            out["C_newday_sounds"] = f"ERR {e}"[:200]

        # D: style preview — use rf-daily-style-<id>
        try:
            # back to lobby
            if await is_visible(page, "rf-daily-exit"):
                await page.click('[data-testid="rf-daily-exit"]', force=True)
                await page.wait_for_timeout(2000)
            if await is_visible(page, "rf-all-india-style"):
                await page.click('[data-testid="rf-all-india-style"]', force=True)
                await page.wait_for_timeout(2500)
                tids = await page.evaluate("""() => Array.from(document.querySelectorAll('[data-testid^="rf-daily-style-"]')).map(e => e.getAttribute('data-testid')).slice(0, 10)""")
                out["D_style_tids"] = tids
                await page.evaluate("window.__plays = []")
                # tap one that's not already in use
                tap_tid = next((t for t in tids if t.startswith("rf-daily-style-") and not t.startswith("rf-daily-style-use-") and not t.startswith("rf-daily-style-card-")), None)
                if tap_tid:
                    # Actually prefer tapping the card for sound preview
                    card_tid = next((t for t in tids if t.startswith("rf-daily-style-card-")), None)
                    if card_tid:
                        await page.click(f'[data-testid="{card_tid}"]', force=True)
                        await page.wait_for_timeout(1500)
                    else:
                        await page.click(f'[data-testid="{tap_tid}"]', force=True)
                        await page.wait_for_timeout(1500)
                    out["D_style_sounds"] = await sounds(page)
                    # tap again - should still play preview (not once-a-day)
                    await page.evaluate("window.__plays = []")
                    if card_tid:
                        await page.click(f'[data-testid="{card_tid}"]', force=True)
                        await page.wait_for_timeout(1500)
                    out["D_style_sounds_again"] = await sounds(page)
            else:
                out["D_style_tids"] = "rf-all-india-style NOT visible"
        except Exception as e:
            out["D_err"] = str(e)[:200]

        print(json.dumps(out, indent=2))
        await browser.close()


asyncio.run(main())
