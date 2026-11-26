# Whole-app smoke run in both motion forms (test-only, read-only: see smoke_all.py): every main screen once with
# everything moving, then once on a phone at Smooth Mode's lowest level (STILL kept on the phone).
#   python3 /app/tests/slow_phone_smoke.py
import asyncio
import json
import sys
import time

from dotenv import dotenv_values
from playwright.async_api import async_playwright

sys.path.insert(0, "/app/tests")
import smoke_all  # noqa: E402

BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
KEY = "shine.level.v1"


async def one(p, kept):
    browser = await p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    ctx = await browser.new_context(viewport={"width": 390, "height": 844})
    if kept:
        await ctx.add_init_script(f"localStorage.setItem('{KEY}', {json.dumps(json.dumps(kept))});")
    page = await ctx.new_page()
    await page.goto(BASE + "/entry", wait_until="domcontentloaded", timeout=90000)
    rows = await smoke_all.run(page)
    level = await page.evaluate(f"localStorage.getItem('{KEY}')")
    await browser.close()
    return rows, level


async def main():
    async with async_playwright() as p:
        print("=== everything moves")
        full, kept = await one(p, None)
        print("level kept at the end:", kept)
        print("=== STILL kept on the phone")
        still, kept = await one(p, f"2:{int(time.time() * 1000)}")
        print("level kept at the end:", kept)
    bad = [(form, r[0], r[1]) for form, rows in (("moving", full), ("still", still)) for r in rows if r[1] != "ok"]
    print(f"\nBOTH FORMS: {len(full)} + {len(still)} screens opened, {len(bad)} not ok", bad or "")
    sys.exit(1 if bad or len(full) != len(smoke_all.SCREENS) or len(still) != len(smoke_all.SCREENS) else 0)


asyncio.run(main())
