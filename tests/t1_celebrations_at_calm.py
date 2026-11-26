"""T1 extra: at CALM (level 1) celebrations and decoration MUST still move.
Code reading: frontend/src/motion.tsx useLowMotion() = reduced OR level===STILL.
At CALM, both are false, so celebrations behave the same as at FULL.
This mini-run confirms it on the lobby:
  - with level 1 kept, the lobby should still have running CSS animations
    (much more than zero, like the nothing-kept run).
Read-only. One sign-in, direct lobby look, no writes.
  python3 /app/tests/t1_calm_lobby_still_moves.py
"""
import asyncio
import json
import sys
import time

from dotenv import dotenv_values
from playwright.async_api import async_playwright

sys.path.insert(0, "/app/tests")
from shine_helpers import sign_in  # noqa: E402

BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
KEY = "shine.level.v1"


async def main():
    results = []
    async with async_playwright() as p:
        for label, kept in (("nothing kept (FULL)", None), ("CALM kept (1:)", f"1:{int(time.time() * 1000)}"), ("STILL kept (2:)", f"2:{int(time.time() * 1000)}")):
            browser = await p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
            ctx = await browser.new_context(viewport={"width": 390, "height": 844})
            if kept:
                await ctx.add_init_script(f"localStorage.setItem('{KEY}', {json.dumps(json.dumps(kept))});")
            page = await ctx.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            await page.goto(BASE + "/entry", wait_until="domcontentloaded", timeout=90000)
            await sign_in(page, aits=None, board=False)
            await page.goto(BASE + "/rapid", wait_until="domcontentloaded", timeout=90000)
            await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=60000)
            # dismiss daily popup if present
            try:
                await page.click('[data-testid="rf-daily-popup-exit"]', timeout=2000)
            except Exception:  # noqa: BLE001
                pass
            await page.wait_for_timeout(2500)
            running = await page.evaluate("() => { let n=0; for (const el of document.querySelectorAll('*')) { const a = getComputedStyle(el).animationName; if (a && a !== 'none') n++; } return n; }")
            kept_now = await page.evaluate(f"localStorage.getItem('{KEY}')")
            results.append((label, running, kept_now, errors[:]))
            await browser.close()

    for label, running, kept_now, errors in results:
        print(f"{label}: running CSS animations = {running}; kept = {kept_now}; errors = {errors}")

    full = results[0][1]
    calm = results[1][1]
    still = results[2][1]
    print()
    ok = calm > 20 and still <= 3 and full > 20 and calm >= full - 2
    if ok:
        print(f"PASS: CALM moves ({calm}) like FULL ({full}); STILL rests ({still}).")
        sys.exit(0)
    else:
        print(f"FAIL: FULL={full}, CALM={calm}, STILL={still}. CALM should move, STILL should rest.")
        sys.exit(1)


asyncio.run(main())
