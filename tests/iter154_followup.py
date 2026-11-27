# Iteration 154 follow-up: Account name (opened from Home, after the session settles) + B3/B4 with a realistic
# stand-in door (PUT updates the copy). Same read-only rules as iter154_name_rank_door.py.
import asyncio
import json
import re
import sys
import time

from dotenv import dotenv_values
from playwright.async_api import async_playwright

sys.path.insert(0, "/app/tests")
from shine_helpers import sign_in  # noqa: E402
from iter154_name_rank_door import BASE, check, text, ls, open_rank, reload_home, RES  # noqa: E402


async def main():
    log, blocked, srv = [], [], {"copy": None}
    name = {"value": "unset"}
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        page = await (await b.new_context(viewport={"width": 390, "height": 844})).new_page()
        page.on("request", lambda r: log.append((r.method, r.post_data)) if "/profile/rank-details" in r.url else None)

        async def guard(route):
            r = route.request
            if r.method in ("GET", "HEAD", "OPTIONS") or "/api/jl/auth/" in r.url or "/profile/rank-details" in r.url:
                await route.fallback(); return
            blocked.append(r.method + " " + r.url)
            await route.fulfill(status=418, body="{}")
        await page.route(re.compile(r".*/api/jl/.*"), guard)

        async def door(route):
            r = route.request
            if r.method == "PUT":
                srv["copy"] = json.loads(r.post_data or "{}")
            await route.fulfill(status=200, content_type="application/json",
                                body=json.dumps({"data": srv["copy"], "error": None, "meta": {"api_version": "1"}}))
        await page.route("**/api/jl/profile/rank-details*", door)

        async def nm(route):
            if name["value"] == "unset":
                await route.fallback(); return
            resp = await route.fetch(); j = await resp.json(); d = j.get("data")
            if isinstance(d, dict):
                (d["user"] if isinstance(d.get("user"), dict) else d)["display_name"] = name["value"]
            await route.fulfill(response=resp, body=json.dumps(j))
        await page.route(re.compile(r".*/api/jl/auth/(session|me)(\?.*)?$"), nm)

        async def account_name():
            await page.locator('[data-testid="home-account-button"]').first.click()
            await page.wait_for_selector('[data-testid="account-name"]', timeout=20000)
            await page.wait_for_timeout(4000)
            v = await text(page, "account-name")
            await page.locator('[data-testid="account-back-button"]').first.click()
            await page.wait_for_selector('[data-testid="home-greeting"]', timeout=20000)
            return v

        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await sign_in(page)
        await page.wait_for_timeout(4000)
        user = await page.evaluate("() => Object.keys(localStorage).filter(k => /auth|user|session/i.test(k))")
        print("INFO storage keys:", user)
        a0 = await account_name()
        print("INFO A account-name real (via Home, settled):", a0)
        name["value"] = "Asha Rao"
        await reload_home(page)
        await page.wait_for_timeout(2000)
        print("INFO A greeting w/ Asha:", await text(page, "home-greeting"))
        a1 = await account_name()
        print("INFO A account-name with display_name Asha Rao:", a1)
        name["value"] = None
        await reload_home(page)
        a2 = await account_name()
        check("A5 account-name with display_name null == real", a2 == a0, a2)
        name["value"] = "unset"

        # B3/B4 with the spec's copy (at = now + 60 s) -> what happens to a save made within that minute
        await page.evaluate("() => localStorage.removeItem('rank.details.door')")
        now = int(time.time() * 1000)
        prof = lambda m, at: {"at": at, "jee": {"marks": m, "pct": "", "rank": "", "level": "normal", "category": "OBC-NCL", "female": False, "pwd": False, "state": None},
                              "comedk": {"marks": "", "rank": ""}, "bitsat": {"score": "301"}}
        srv["copy"] = {"rank_details": prof("222", now + 60000), "at": now + 60000}
        await reload_home(page)
        await open_rank(page)
        await page.wait_for_timeout(3500)
        print("INFO B2 bar:", await text(page, "rank-profile-summary"))
        log.clear()
        await page.locator('[data-testid="rank-profile"]').first.click()
        await page.locator('[data-testid="rpf-jee-marks"]').first.fill("199")
        await page.locator('[data-testid="rpf-save"]').first.click()
        await page.wait_for_timeout(3500)
        s = await text(page, "rank-profile-summary")
        print("INFO B3-skew requests:", [m for m, _ in log], "bar after save 199:", s)
        check("B3-skew a save made while the account copy's at is ahead keeps 199", "199 marks" in s, s)

        # Realistic: the account copy is older than the save (at = now - 1 s)
        t = int(time.time() * 1000) - 1000
        srv["copy"] = {"rank_details": prof("222", t), "at": t}
        log.clear()
        await page.locator('[data-testid="rank-profile"]').first.click()
        await page.locator('[data-testid="rpf-jee-marks"]').first.fill("199")
        await page.locator('[data-testid="rpf-save"]').first.click()
        await page.wait_for_timeout(3500)
        puts = [json.loads(p or "{}") for m, p in log if m == "PUT"]
        ok = len(puts) == 1 and puts[0]["rank_details"]["jee"]["marks"] == "199" and puts[0]["at"] > t and "uid" not in json.dumps(puts[0])
        check("B3 save -> GET then PUT {rank_details.jee.marks 199, at newer}, no uid", ok, [[m for m, _ in log], puts])
        check("B3b bar 199", "199 marks" in await text(page, "rank-profile-summary"))
        log.clear()
        await page.locator('[data-testid="rank-profile"]').first.click()
        await page.locator('[data-testid="rpf-clear"]').first.click()
        await page.wait_for_timeout(3500)
        puts = [json.loads(p or "{}") for m, p in log if m == "PUT"]
        check("B4 hatao -> PUT rank_details null + at", len(puts) == 1 and puts[0]["rank_details"] is None and puts[0]["at"] > t, [[m for m, _ in log], puts])
        check("B4b bar Add details", await text(page, "rank-profile-title") == "Add details")
        # reload: the emptied copy stays emptied (account copy is now null + at)
        await reload_home(page)
        await open_rank(page)
        await page.wait_for_timeout(3500)
        check("B4c after reload still Add details, no PUT", await text(page, "rank-profile-title") == "Add details", [m for m, _ in log])
        check("Z no blocked writes", not blocked, blocked)
        await b.close()
    print(f"RESULT {sum(1 for _, o in RES if o)}/{len(RES)}")


asyncio.run(main())
