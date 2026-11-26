# Slow-phone check (26 Nov 2026): on a phone that cannot move anything smoothly (Smooth Mode's lowest level, STILL) the
# endless decoration of Rapid Fire rests too, and nothing goes missing. Read-only: signs the QA learner in, opens Home
# and the Rapid Fire lobby, plays nothing. The All India daily is answered by the browser (fake_daily_done).
#   python3 /app/tests/slow_phone_check.py
# Three runs in one browser each:
#   A  nothing kept on the phone            -> everything moves (the look as designed)
#   B  "shine.level.v1" = STILL kept        -> the lobby rests from the first frame
#   C  a slowed-down browser on Home        -> Smooth Mode itself decides, then the lobby (no reload) rests
import asyncio
import json
import sys
import time
from pathlib import Path

from dotenv import dotenv_values
from playwright.async_api import async_playwright

sys.path.insert(0, "/app/tests")
from rf_daily_fixture import fake_daily_done  # noqa: E402
from shine_helpers import sign_in  # noqa: E402

BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
OUT = Path("/tmp/slow_phone"); OUT.mkdir(exist_ok=True)
KEY = "shine.level.v1"
RUNNING = "document.getAnimations().filter(a => a.playState === 'running').length"
# The phoenix's wing: the first moving layer inside rf-phoenix (its transform changes while the wings beat).
WING = """() => { const el = document.querySelector('[data-testid="rf-phoenix"]'); if (!el || !el.firstElementChild) return null;
  const s = getComputedStyle(el.firstElementChild); return { transform: s.transform, opacity: s.opacity }; }"""
checks = []


def check(name, ok, detail=""):
    checks.append(ok)
    print(("PASS " if ok else "FAIL ") + name + (" | " + str(detail) if detail != "" else ""))


async def lobby_state(page, tag):
    await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=60000)
    await page.wait_for_selector('[data-testid="rf-phoenix"]', timeout=30000)
    await page.wait_for_timeout(2500)  # the lobby's own loading settles
    running = await page.evaluate(RUNNING)
    w1 = await page.evaluate(WING)
    await page.wait_for_timeout(650)
    w2 = await page.evaluate(WING)
    card = await page.locator('[data-testid="rf-all-india"]').count()
    await page.screenshot(path=str(OUT / f"{tag}_lobby.jpeg"), type="jpeg", quality=40, full_page=False)
    kept = await page.evaluate(f"localStorage.getItem('{KEY}')")
    # The other three tabs of the arena (only opened and looked at: nothing is bought, joined or claimed).
    if await page.locator('[data-testid="rf-daily-popup-exit"]').count():  # today's All India offer: EXIT stays in the lobby, nothing is sent
        await page.click('[data-testid="rf-daily-popup-exit"]')
        await page.wait_for_selector('[data-testid="rf-daily-popup"]', state="detached", timeout=15000)
    tabs = {}
    for key, tid in (("trophy", "arena-tab-trophy"), ("gang", "arena-tab-gang"), ("store", "arena-tab-store")):
        await page.click(f'[data-testid="{tid}"]')
        await page.wait_for_timeout(2200)
        tabs[key] = await page.evaluate(RUNNING)
    tabs["store_screen"] = await page.locator('[data-testid="shop-screen"]').count()
    return {"running_css": running, "wing_moves": w1 != w2, "wing": w2, "all_india_card": card, "kept": kept, "tabs": tabs}


async def one(p, tag, kept=None, slow=0):
    browser = await p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    ctx = await browser.new_context(viewport={"width": 390, "height": 844})
    if kept:
        await ctx.add_init_script(f"localStorage.setItem('{KEY}', {json.dumps(json.dumps(kept))});")
    page = await ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)[:200]))
    await fake_daily_done(page)
    await page.goto(BASE + "/entry", wait_until="domcontentloaded", timeout=90000)
    await sign_in(page, aits=None, board=False)
    home = None
    if slow:
        cdp = await ctx.new_cdp_session(page)
        await cdp.send("Emulation.setCPUThrottlingRate", {"rate": slow})
        began = time.time()
        while time.time() - began < 45:  # Home has Shines: Smooth Mode looks at the frames here
            now = await page.evaluate(f"localStorage.getItem('{KEY}')")
            if now:
                break
            await page.wait_for_timeout(1000)
        home = {"kept_after_home": await page.evaluate(f"localStorage.getItem('{KEY}')"), "seconds": round(time.time() - began, 1)}
        await cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
    await page.click('[data-testid="tab-rapid"]')  # no reload: the level in memory is what counts
    state = await lobby_state(page, tag)
    await browser.close()
    return state, home, errors


async def main():
    rate = int(sys.argv[1]) if len(sys.argv) > 1 else 20  # `slow_phone_check.py 60` = run C alone, slowed 60 times
    async with async_playwright() as p:
        if len(sys.argv) > 1:
            return await run_c(p, rate)
        a, _, ea = await one(p, "A_full")
        print("A (nothing kept):", a)
        check("A: no page error", not ea, ea)
        check("A: the All India card is there", a["all_india_card"] == 1)
        if a["kept"]:
            print("     note: this browser itself was too slow on the way, Smooth Mode kept", a["kept"], "- A is not a clean 'everything moves' run")
        else:
            check("A: the lobby moves (CSS animations running)", a["running_css"] > 0, a["running_css"])
            check("A: the phoenix's wings beat", a["wing_moves"], a["wing"])
            check("A: the trophy, gang and store tabs open and something moves in them", a["tabs"]["store_screen"] == 1 and a["tabs"]["trophy"] + a["tabs"]["gang"] + a["tabs"]["store"] > 0, a["tabs"])

        b, _, eb = await one(p, "B_still", kept=f"2:{int(time.time() * 1000)}")
        print("B (STILL kept):  ", b)
        check("B: no page error", not eb, eb)
        check("B: the All India card is there", b["all_india_card"] == 1)
        check("B: nothing runs in the lobby (CSS animations)", b["running_css"] == 0, b["running_css"])
        check("B: the trophy, gang and store tabs open and nothing runs in them", b["tabs"] == {"trophy": 0, "gang": 0, "store": 0, "store_screen": 1}, b["tabs"])
        check("B: the phoenix rests", not b["wing_moves"], b["wing"])
        check("B: the phoenix's wings are drawn (opacity 1)", b["wing"] is not None and float(b["wing"]["opacity"]) == 1.0, b["wing"])

        await run_c(p, rate)


async def run_c(p, rate):
    c, home, ec = await one(p, "C_slowed", slow=rate)
    print(f"C (slowed {rate} times on Home):", home, c)
    check("C: no page error", not ec, ec)
    level = (home["kept_after_home"] or "").strip('"').split(":")[0]
    if level == "2":
        check("C: after Smooth Mode chose STILL, nothing runs in the lobby", c["running_css"] == 0, c["running_css"])
        check("C: nothing runs in the trophy, gang and store tabs either", c["tabs"] == {"trophy": 0, "gang": 0, "store": 0, "store_screen": 1}, c["tabs"])
        check("C: the phoenix rests and is drawn", (not c["wing_moves"]) and c["wing"] is not None and float(c["wing"]["opacity"]) == 1.0, c["wing"])
    elif level == "1":
        check("C: Smooth Mode chose CALM: the lobby still moves (only the Shine calms at this level)", c["running_css"] > 0 and c["wing_moves"], c["running_css"])
    else:
        print("     note: Smooth Mode chose nothing in this run (kept:", home["kept_after_home"], ")")


def report():
    print(f"\n{sum(checks)} of {len(checks)} checks passed; pictures in {OUT}")
    sys.exit(0 if all(checks) else 1)


asyncio.run(main())
report()
