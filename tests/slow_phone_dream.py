# Slow-phone check, part 3 (26 Nov 2026): the "Dream Unlocked" celebration in its calm form on a phone at Smooth Mode's
# lowest level (STILL), then with everything moving. ONE sign-in. Every /api/rf/dream call is answered by the browser
# (a made-up dream college and a made-up mock), so the owner's real dream list is neither read nor written.
#   python3 /app/tests/slow_phone_dream.py
import asyncio
import json
import re
import sys
import time
from pathlib import Path

from dotenv import dotenv_values
from playwright.async_api import async_playwright

sys.path.insert(0, "/app/tests")
from shine_helpers import sign_in  # noqa: E402

BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
OUT = Path("/tmp/slow_phone"); OUT.mkdir(exist_ok=True)
KEY = "shine.level.v1"
checks, writes, which = [], [], {"dream": "d-first"}


def check(name, ok, detail=""):
    checks.append(ok)
    print(("PASS " if ok else "FAIL ") + name + (" | " + str(detail) if detail != "" else ""))


async def dream_stand_in(route):
    req = route.request
    path = req.url.split("/api/rf/dream", 1)[1].split("?")[0]
    now = int(time.time() * 1000)
    dream = {"id": which["dream"], "exam": "jee", "college": "Stand-in Institute", "branch": "Computer Science", "need": 150, "note": "", "at": now - 7200000}
    if req.method != "GET":
        writes.append(req.method + " " + path)
        body = {"dreams": [dream]} if path == "/dreams" else {}
    else:
        body = {"dreams": [dream], "cheered": [], "dropped": [],
                "mocks": [{"id": "mock-" + which["dream"], "exam": "jee", "score": 212, "max": 300, "raw": 212, "rawMax": 300, "title": "Stand-in full mock", "at": now - 3600000}]}
    await route.fulfill(status=200, content_type="application/json", body=json.dumps(body))


async def count(page, test_id):
    return await page.locator(f'[data-testid="{test_id}"]').count()


async def level(page):
    """Smooth Mode's level kept on this browser: 0 = everything moves (nothing kept), 1 = CALM, 2 = STILL."""
    kept = await page.evaluate(f"localStorage.getItem('{KEY}')")
    return int(json.loads(kept).split(":")[0]) if kept else 0


async def open_home(page, kept):
    """Home again, from the start of the app (the level kept on the phone is read when the app starts)."""
    await page.evaluate(f"localStorage.setItem('{KEY}', {json.dumps(json.dumps(kept))})" if kept else f"localStorage.removeItem('{KEY}')")
    await page.goto(BASE + "/", wait_until="domcontentloaded", timeout=90000)
    await page.wait_for_selector('[data-testid="dream-cheer"]', timeout=60000)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"])
        ctx = await browser.new_context(viewport={"width": 390, "height": 844})
        page = await ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        await page.route(re.compile(r".*/api/rf/dream(/|\?|$).*"), dream_stand_in)
        await page.goto(BASE + "/entry", wait_until="domcontentloaded", timeout=90000)
        await sign_in(page, aits=None, board=False)

        # --- STILL: the calm form (a celebration plays once per dream college, so each run has its own made-up college)
        await page.wait_for_timeout(2500)
        if await count(page, "dream-cheer"):  # the first stand-in dream opened it right after sign-in: close it
            await page.wait_for_selector('[data-testid="dream-cheer-skip"], [data-testid="dream-cheer-continue"]', timeout=20000)
            await page.locator('[data-testid="dream-cheer-skip"], [data-testid="dream-cheer-continue"]').first.click()
        which["dream"] = "d-still"
        await open_home(page, f"2:{int(time.time() * 1000)}")
        await page.wait_for_selector('[data-testid="dream-cheer-continue"]', timeout=20000)  # after its loading (4 s at most): straight to the end
        still = {t: await count(page, "dream-cheer-" + t) for t in ("stage", "lead", "holder-1", "holder-2", "card", "college", "score", "share", "continue", "skip", "again", "cannons", "chant-text")}
        still["confetti"] = await count(page, "rf-confetti")
        still["chant"] = await page.locator('[data-testid="dream-cheer-chant-text"]').inner_text() if still["chant-text"] else None
        still["score"] = await page.locator('[data-testid="dream-cheer-score"]').inner_text()
        await page.screenshot(path=str(OUT / "D_still_dream.jpeg"), type="jpeg", quality=40)
        await page.click('[data-testid="dream-cheer-continue"]')
        await page.wait_for_selector('[data-testid="dream-cheer"]', state="detached", timeout=15000)
        still["home_after"] = await count(page, "home-tile-choice")
        print("STILL:", still)

        # --- everything moves (`slow_phone_dream.py 6` = this part in a browser slowed 6 times)
        which["dream"] = "d-full"
        if len(sys.argv) > 1:
            cdp = await ctx.new_cdp_session(page)
            await cdp.send("Emulation.setCPUThrottlingRate", {"rate": int(sys.argv[1])})
        await open_home(page, None)
        await page.wait_for_selector('[data-testid="dream-cheer-stage"] [data-testid="dream-cheer-lead"]', timeout=40000)
        began = time.monotonic()  # the 30-second routine starts now: 64 counts, the drop at count 32 (15.0 s), the finale at count 60 (28.1 s)

        async def shots(at):
            """How many cannon volleys and confetti showers have gone off, `at` seconds into the routine."""
            await page.wait_for_timeout(max(0, int((began + at - time.monotonic()) * 1000)))
            return [await count(page, "dream-cheer-cannons"), await count(page, "rf-confetti")]

        full = {"start": await shots(1.5)}
        full.update({t: await count(page, "dream-cheer-" + t) for t in ("lead", "skip", "continue", "progress")})
        await page.screenshot(path=str(OUT / "D_full_dream.jpeg"), type="jpeg", quality=40)
        full["before_drop"] = await shots(13.5)
        full["after_drop"] = await shots(17.0)
        full["before_finale"] = await shots(26.6)
        full["after_finale"] = await shots(29.6)
        await page.wait_for_selector('[data-testid="dream-cheer-continue"]', timeout=25000)  # the end: Share and Continue, and Phir se unless the phone stopped keeping up
        full["end_buttons"] = [await count(page, "dream-cheer-" + t) for t in ("again", "share", "continue", "skip")]
        full["level_at_end"] = await level(page)
        if full["end_buttons"][0]:
            await page.click('[data-testid="dream-cheer-again"]')
            await page.wait_for_selector('[data-testid="dream-cheer-skip"]', timeout=15000)
            began = time.monotonic()
            full["again_start"] = await shots(1.5)
            full["again_before_drop"] = await shots(13.5)
            full["again_after_drop"] = await shots(17.0)
            full["level_after_again"] = await level(page)
            # A browser that dropped to STILL during the second round is at its calm end (Continue), not at Skip.
            await page.locator('[data-testid="dream-cheer-skip"], [data-testid="dream-cheer-continue"]').first.click()
        else:
            await page.click('[data-testid="dream-cheer-continue"]')
        await page.wait_for_selector('[data-testid="dream-cheer"]', state="detached", timeout=15000)
        full["home_after"] = await count(page, "home-tile-choice")
        print("moving:", full)
        await browser.close()

    check("no page error", not errors, errors)
    check("every dream call was answered by the browser (writes seen, none sent on)", all(w.split(" ")[1] in ("/cheered", "/mocks", "/dreams") for w in writes), sorted(set(writes)))
    check("still: the stage, the squad, the card, Share and Continue are there",
          all(still[t] == 1 for t in ("stage", "lead", "holder-1", "holder-2", "card", "college", "share", "continue")), still)
    check("still: it goes straight to its end: no Skip, no Phir se, no cannons, no confetti",
          still["skip"] == 0 and still["again"] == 0 and still["cannons"] == 0 and still["confetti"] == 0, still)
    check("still: the score is shown and Continue goes back to Home", still["score"] == "212" and still["home_after"] == 1, (still["score"], still["home_after"]))
    check("moving: the routine plays (Skip and the progress bar are there, the end buttons are not)", full["lead"] == 1 and full["skip"] == 1 and full["continue"] == 0 and full["progress"] == 1, full)
    # A browser that could not keep up drops to STILL while the celebration plays: the calm end then has no Phir se.
    calm_end = full["level_at_end"] == 2
    if calm_end:
        print("note: this browser dropped to STILL while the celebration played: calm end, no confetti to count, no second round")
    check("moving: at the end Share and Continue replace Skip (and Phir se, unless the browser dropped to STILL), then back to Home",
          full["end_buttons"] == [0 if calm_end else 1, 1, 1, 0] and full["home_after"] == 1, (full["end_buttons"], full["level_at_end"], full["home_after"]))
    if not calm_end:
        # [cannon volleys, confetti showers] so far. Each one goes off at its own moment, not all at the start.
        check("moving: at the start only the opening cannons fire", full["start"] == [1, 0] and full["before_drop"] == [1, 0], (full["start"], full["before_drop"]))
        check("moving: the confetti falls on the drop (count 32)", full["after_drop"] == [1, 1] and full["before_finale"] == [1, 1], (full["after_drop"], full["before_finale"]))
        check("moving: the finale (count 60) fires the cannons and the confetti again", full["after_finale"] == [2, 2], full["after_finale"])
        if full["level_after_again"] == 2:
            print("note: this browser dropped to STILL during the second round: its confetti is not counted")
        else:
            check("moving: Phir se starts a clean round (opening cannons only, then the drop)",
                  full["again_start"] == [1, 0] and full["again_before_drop"] == [1, 0] and full["again_after_drop"] == [1, 1],
                  (full["again_start"], full["again_before_drop"], full["again_after_drop"]))
    print(f"\n{sum(checks)} of {len(checks)} checks passed; pictures in {OUT}")
    sys.exit(0 if all(checks) else 1)


asyncio.run(main())
