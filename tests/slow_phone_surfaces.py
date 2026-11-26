# Slow-phone check, part 2 (26 Nov 2026): the celebrations in their calm form on a phone at Smooth Mode's lowest level
# (STILL), next to the same screens with everything moving. Read-only: the Cheer Squad PREVIEW (nothing is bought), the
# All India result answered by the browser (fake_daily_done, nothing is played), the vault. Nothing is written.
#   python3 /app/tests/slow_phone_surfaces.py
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
checks = []
LOOK = """(id) => { const el = document.querySelector(`[data-testid="${id}"]`); if (!el) return null;
  const inner = el.querySelector('div') || el, a = getComputedStyle(el), b = getComputedStyle(inner);
  return { opacity: a.opacity, transform: a.transform, inner: b.transform + '|' + b.opacity }; }"""
RUNNING_IN = """(id) => { const el = document.querySelector(`[data-testid="${id}"]`);
  return el ? el.getAnimations({ subtree: true }).filter(a => a.playState === 'running').length : -1; }"""


def check(name, ok, detail=""):
    checks.append(ok)
    print(("PASS " if ok else "FAIL ") + name + (" | " + str(detail) if detail != "" else ""))


async def count(page, test_id):
    return await page.locator(f'[data-testid="{test_id}"]').count()


async def moves(page, test_id, gap=500):
    one = await page.evaluate(LOOK, test_id)
    await page.wait_for_timeout(gap)
    two = await page.evaluate(LOOK, test_id)
    return one != two, two


async def surfaces(p, tag, kept=None):
    browser = await p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    ctx = await browser.new_context(viewport={"width": 390, "height": 844})
    if kept:
        await ctx.add_init_script(f"localStorage.setItem('{KEY}', {json.dumps(json.dumps(kept))});")
    page = await ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)[:200]))
    await fake_daily_done(page, rank=7)
    await page.goto(BASE + "/entry", wait_until="domcontentloaded", timeout=90000)
    await sign_in(page, aits=None, board=False)
    got = {}

    # 1. Cheer Squad preview
    await page.goto(BASE + "/rapid/squads", wait_until="domcontentloaded", timeout=90000)
    await page.wait_for_selector('[data-testid="squads-screen"]', timeout=60000)
    await page.locator('[data-testid$="-preview"]').first.click()
    await page.wait_for_selector('[data-testid="cheer-squad"]', timeout=30000)
    await page.wait_for_timeout(900)
    got["confetti"] = await count(page, "rf-confetti")
    got["squad_parts"] = [await count(page, t) for t in ("cheer-level", "cheer-stage", "cheer-lead", "cheer-holder-1", "cheer-holder-2", "cheer-line", "cheer-again", "cheer-close")]
    got["lead_moves"], got["lead"] = await moves(page, "cheer-lead")
    got["burst_moves"], got["burst"] = await moves(page, "cheer-burst", 700)
    await page.screenshot(path=str(OUT / f"{tag}_cheer.jpeg"), type="jpeg", quality=40)
    await page.click('[data-testid="cheer-again"]')  # the button still answers (a sound and, when it moves, a new shower)
    await page.wait_for_timeout(400)
    got["confetti_again"] = await count(page, "rf-confetti")
    await page.click('[data-testid="cheer-close"]')
    await page.wait_for_selector('[data-testid="cheer-squad"]', state="detached", timeout=15000)
    got["squads_after_close"] = await count(page, "squads-screen")

    # 2. All India result, top 100: Battleground Victory
    await page.goto(BASE + "/rapid/daily", wait_until="domcontentloaded", timeout=90000)
    await page.wait_for_selector('[data-testid="rf-battle-victory"]', timeout=60000)
    await page.wait_for_timeout(2600)  # the charge has ended by now
    got["victory_running"] = await page.evaluate(RUNNING_IN, "rf-battle-victory")
    got["victory_badge"] = await count(page, "rf-battle-victory-badge")
    await page.screenshot(path=str(OUT / f"{tag}_victory.jpeg"), type="jpeg", quality=40)

    # 3. The vault's phoenix
    await page.goto(BASE + "/rapid/vault", wait_until="domcontentloaded", timeout=90000)
    await page.wait_for_selector('[data-testid="vault-phoenix"]', timeout=60000)
    await page.wait_for_timeout(1500)
    got["vault_moves"], got["vault"] = await moves(page, "vault-phoenix", 650)
    got["kept"] = await page.evaluate(f"localStorage.getItem('{KEY}')")
    await browser.close()
    return got, errors


async def main():
    async with async_playwright() as p:
        full, e1 = await surfaces(p, "S_full")
        print("everything moves:", full)
        still, e2 = await surfaces(p, "S_still", kept=f"2:{int(time.time() * 1000)}")
        print("STILL kept:      ", still)
    clean = not full["kept"]
    if not clean:
        print("note: this browser was itself too slow, Smooth Mode kept", full["kept"], "- the 'everything moves' run is not clean")
    check("moving: no page error", not e1, e1)
    check("moving: every part of the Cheer Squad is there", all(n == 1 for n in full["squad_parts"]), full["squad_parts"])
    if clean:
        check("moving: confetti falls, the lead dances, fireworks burst", full["confetti"] == 1 and full["lead_moves"] and full["burst_moves"], (full["confetti"], full["lead_moves"], full["burst_moves"]))
        check("moving: Battleground Victory is alive", full["victory_running"] > 0, full["victory_running"])
        check("moving: the vault's phoenix beats", full["vault_moves"])
    check("still: no page error", not e2, e2)
    check("still: every part of the Cheer Squad is there", all(n == 1 for n in still["squad_parts"]), still["squad_parts"])
    check("still: no confetti, the lead stands, no firework is drawn", still["confetti"] == 0 and not still["lead_moves"] and not still["burst_moves"] and float(still["burst"]["opacity"]) == 0.0,
          (still["confetti"], still["lead_moves"], still["burst"]))
    check("still: Cheer again adds no confetti, Continue closes the squad", still["confetti_again"] == 0 and still["squads_after_close"] == 1, (still["confetti_again"], still["squads_after_close"]))
    check("still: Battleground Victory is drawn and rests", still["victory_running"] == 0 and still["victory_badge"] == 1, (still["victory_running"], still["victory_badge"]))
    check("still: the vault's phoenix is drawn and rests", not still["vault_moves"] and still["vault"] is not None, still["vault"])
    print(f"\n{sum(checks)} of {len(checks)} checks passed; pictures in {OUT}")
    sys.exit(0 if all(checks) else 1)


asyncio.run(main())
