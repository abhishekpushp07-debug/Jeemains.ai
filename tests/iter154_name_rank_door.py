# Iteration 154: A (display_name on Home/Account) + B (Meri details <-> website door /profile/rank-details).
# READ-ONLY for the QA learner: every stand-in answers in the browser only; any other write under /api/jl (outside /auth)
# is stopped and counted. Never starts / answers / submits a paper, never saves a name.
import asyncio
import json
import re
import sys
import time

from dotenv import dotenv_values
from playwright.async_api import async_playwright

sys.path.insert(0, "/app/tests")
from shine_helpers import sign_in  # noqa: E402

BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
RES = []
DOOR = "**/api/jl/profile/rank-details*"


def check(name, ok, detail=""):
    RES.append((name, bool(ok)))
    print(("PASS " if ok else "FAIL ") + name + (" | " + str(detail) if detail != "" else ""), flush=True)


async def text(page, tid, timeout=15000):
    el = page.locator(f'[data-testid="{tid}"]').first
    await el.wait_for(timeout=timeout)
    return (await el.inner_text()).strip()


async def ls(page, key):
    return await page.evaluate("k => localStorage.getItem(k)", key)


async def open_rank(page):
    await page.locator('[data-testid="tab-rank"]').first.click()
    await page.wait_for_selector('[data-testid="rank-profile"]', timeout=30000)


async def go_home(page):
    await page.locator('[data-testid="tab-index"]').first.click()
    await page.wait_for_selector('[data-testid="home-greeting"]', timeout=30000)


async def reload_home(page):
    await page.goto(BASE + "/", wait_until="domcontentloaded")
    await page.wait_for_selector('[data-testid="home-greeting"]', timeout=60000)
    await page.wait_for_timeout(2500)


async def main():
    door_log, blocked = [], []
    door = {"mode": "real", "get": None}
    name = {"value": "unset"}

    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844})
        page = await ctx.new_page()

        def on_req(req):
            if "/api/jl/profile/rank-details" in req.url:
                door_log.append((req.method, req.post_data, door["mode"]))
        page.on("request", on_req)

        async def guard(route):
            r = route.request
            u = r.url
            if r.method in ("GET", "HEAD", "OPTIONS") or "/api/jl/auth/" in u or "/profile/rank-details" in u:
                await route.fallback()
                return
            blocked.append(r.method + " " + u)
            await route.fulfill(status=418, content_type="application/json", body='{"error":{"code":"blocked_by_test"}}')
        await page.route(re.compile(r".*/api/jl/.*"), guard)

        async def door_route(route):
            r = route.request
            if door["mode"] == "real":
                await route.fallback()
                return
            if r.method == "PUT":
                body = json.loads(r.post_data or "{}")
                await route.fulfill(status=200, content_type="application/json",
                                    body=json.dumps({"data": body, "error": None, "meta": {"api_version": "1"}}))
                return
            await route.fulfill(status=200, content_type="application/json",
                                body=json.dumps({"data": door["get"], "error": None, "meta": {"api_version": "1"}}))
        await page.route(DOOR, door_route)

        async def name_route(route):
            if name["value"] == "unset":
                await route.fallback()
                return
            resp = await route.fetch()
            try:
                j = await resp.json()
                d = j.get("data") if isinstance(j, dict) else None
                if isinstance(d, dict):
                    tgt = d["user"] if isinstance(d.get("user"), dict) else d
                    tgt["display_name"] = name["value"]
                await route.fulfill(response=resp, body=json.dumps(j))
            except Exception:
                await route.fulfill(response=resp)
        await page.route(re.compile(r".*/api/jl/auth/(session|me)(\?.*)?$"), name_route)

        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await sign_in(page)
        await page.wait_for_timeout(3000)

        # ---- A. NAME, real answer
        g = await text(page, "home-greeting")
        check("A1 greeting ends ', learner.' (real website answer)", g.endswith(", learner."), g)
        await page.goto(BASE + "/account", wait_until="domcontentloaded")
        acc_real = await text(page, "account-name", 30000)
        print("INFO account-name (real):", acc_real)

        # ---- B1. door missing (real website 404)
        await reload_home(page)
        door_log.clear()
        await open_rank(page)
        await page.wait_for_timeout(4000)
        gets = [d for d in door_log if d[0] == "GET"]
        stamp = await ls(page, "rank.details.door")
        check("B1a one GET to the door on opening Rank", len(gets) == 1, door_log)
        check("B1b rank.details.door stamped", bool(stamp) and abs(int(float(stamp)) - time.time() * 1000) < 120000, stamp)
        await go_home(page)
        await open_rank(page)
        await page.wait_for_timeout(2000)
        await reload_home(page)
        await open_rank(page)
        await page.wait_for_timeout(3000)
        check("B1c no further door request (tab reopen + reload)", len(door_log) == 1, door_log)
        before = (await text(page, "rank-profile-title"), await text(page, "rank-profile-summary"))
        print("INFO bar before:", before)
        await page.locator('[data-testid="rank-profile"]').first.click()
        await page.wait_for_selector('[data-testid="rpf-jee-marks"]', timeout=10000)
        await page.locator('[data-testid="rpf-jee-marks"]').first.fill("180")
        await page.locator('[data-testid="rpf-save"]').first.click()
        await page.wait_for_selector('[data-testid="rank-profile-saved"]', timeout=10000)
        s = await text(page, "rank-profile-summary")
        check("B1d bar shows 180 marks", "180 marks" in s, s)
        await page.wait_for_timeout(2500)
        check("B1e no PUT while door closed", not [d for d in door_log if d[0] == "PUT"], door_log)
        cut, form = await ls(page, "rank.cutoff.v1"), await ls(page, "rank.form.v1")
        check("B1f Cut off form prefilled 180", cut and '\\"text\\":\\"180\\"' in cut or (cut and '"text":"180"' in cut), cut)
        check("B1g College predictor form prefilled 180", form and "180" in form, form)
        await page.locator('[data-testid="rank-tool-cutoff"]').first.click()
        await page.wait_for_timeout(1500)
        vals = await page.evaluate("() => Array.from(document.querySelectorAll('input')).map(i => i.value).filter(Boolean)")
        check("B1h Cut off screen shows 180", "180" in vals, vals)
        await page.screenshot(path="/tmp/shots/i154_b1_cutoff.jpg", type="jpeg", quality=30)
        await page.locator('[data-testid="rank-tool-college"]').first.click()
        await page.wait_for_timeout(1500)
        vals = await page.evaluate("() => Array.from(document.querySelectorAll('input')).map(i => i.value).filter(Boolean)")
        check("B1i College predictor shows 180", "180" in vals, vals)
        await page.locator('[data-testid="rank-profile"]').first.click()
        await page.locator('[data-testid="rpf-clear"]').first.click()
        await page.wait_for_timeout(1000)
        t = await text(page, "rank-profile-title")
        check("B1j 'Meri details hatao' -> Add details", t == "Add details", t)
        await page.wait_for_timeout(1500)
        check("B1k still no PUT / no extra GET", len(door_log) == 1, door_log)

        # ---- A. NAME, stand-in display_name
        name["value"] = "Asha Rao"
        await reload_home(page)
        g = await text(page, "home-greeting")
        check("A2 greeting ', asha.' with display_name", g.endswith(", asha."), g)
        await page.goto(BASE + "/account", wait_until="domcontentloaded")
        acc = await text(page, "account-name", 30000)
        print("INFO account-name with display_name 'Asha Rao':", acc, "(real copy was:", acc_real + ")")
        name["value"] = None
        await reload_home(page)
        g = await text(page, "home-greeting")
        check("A3 greeting back to ', learner.' with display_name null", g.endswith(", learner."), g)
        await page.goto(BASE + "/account", wait_until="domcontentloaded")
        acc = await text(page, "account-name", 30000)
        check("A4 account-name with null = as before", acc == acc_real, acc)
        name["value"] = "unset"

        # ---- B2. door open, account copy newer
        await page.evaluate("() => localStorage.removeItem('rank.details.door')")
        now = int(time.time() * 1000)
        door["mode"] = "fake"
        door["get"] = {"rank_details": {"at": now + 60000, "jee": {"marks": "222", "pct": "", "rank": "", "level": "normal", "category": "OBC-NCL",
                                                                    "female": False, "pwd": False, "state": None},
                                        "comedk": {"marks": "", "rank": ""}, "bitsat": {"score": "301"}}, "at": now + 60000}
        door_log.clear()
        await reload_home(page)
        await open_rank(page)
        await page.wait_for_timeout(4000)
        s = await text(page, "rank-profile-summary")
        check("B2a account's newer copy shown", "222 marks" in s and "OBC-NCL" in s and "301" in s, s)
        cut = await ls(page, "rank.cutoff.v1")
        check("B2b tools filled from account copy", cut and "222" in cut and "301" in (await ls(page, "rank.bitsat.v1") or ""), cut)
        check("B2c one GET, no PUT", [d[0] for d in door_log] == ["GET"], door_log)
        await page.screenshot(path="/tmp/shots/i154_b2.jpg", type="jpeg", quality=30)

        # ---- B3. edit -> PUT
        door_log.clear()
        await page.locator('[data-testid="rank-profile"]').first.click()
        await page.locator('[data-testid="rpf-jee-marks"]').first.fill("199")
        await page.locator('[data-testid="rpf-save"]').first.click()
        await page.wait_for_timeout(3000)
        puts = [json.loads(d[1] or "{}") for d in door_log if d[0] == "PUT"]
        ok = len(puts) == 1 and (puts[0].get("rank_details") or {}).get("jee", {}).get("marks") == "199" and int(puts[0].get("at") or 0) > now + 60000
        check("B3 PUT with jee.marks 199 and newer at", ok, [d[0] for d in door_log] + [puts])
        if puts:
            print("INFO B3 PUT keys:", list(puts[0].get("rank_details", {}).keys()), "uid leaked:", "uid" in json.dumps(puts[0]))

        # ---- B4. clear -> PUT null
        door_log.clear()
        await page.locator('[data-testid="rank-profile"]').first.click()
        await page.locator('[data-testid="rpf-clear"]').first.click()
        await page.wait_for_timeout(3000)
        puts = [json.loads(d[1] or "{}") for d in door_log if d[0] == "PUT"]
        check("B4 PUT rank_details null with at", len(puts) == 1 and puts[0].get("rank_details") is None and int(puts[0].get("at") or 0) > 0, puts)

        # ---- B5. account empty (at 0), phone has details -> phone PUTs its own
        door["get"] = {"rank_details": None, "at": 0}
        await page.locator('[data-testid="rank-profile"]').first.click()
        await page.locator('[data-testid="rpf-jee-marks"]').first.fill("150")
        await page.locator('[data-testid="rpf-save"]').first.click()
        await page.wait_for_timeout(2500)
        door_log.clear()
        await reload_home(page)
        await open_rank(page)
        await page.wait_for_timeout(4000)
        puts = [json.loads(d[1] or "{}") for d in door_log if d[0] == "PUT"]
        check("B5 GET then PUT of the phone's details (150)", [d[0] for d in door_log] == ["GET", "PUT"] and puts and puts[0]["rank_details"]["jee"]["marks"] == "150", door_log)
        s = await text(page, "rank-profile-summary")
        check("B5b bar still 150 marks", "150 marks" in s, s)

        # ---- B6. garbage
        door["get"] = {"rank_details": "x", "at": int(time.time() * 1000) + 999999}
        door_log.clear()
        await reload_home(page)
        await open_rank(page)
        await page.wait_for_timeout(4000)
        s2 = await text(page, "rank-profile-summary")
        check("B6 garbage: unchanged, no PUT", "150 marks" in s2 and [d[0] for d in door_log] == ["GET"], [door_log, s2])

        # ---- B7. signed out
        await page.goto(BASE + "/account", wait_until="domcontentloaded")
        await page.locator('[data-testid="account-signout-button"]').first.click()
        await page.wait_for_timeout(2500)
        sheet = page.locator('text=Keep')
        if await sheet.count():
            print("INFO sign-out sheet shown")
        await page.wait_for_selector('[data-testid="entry-phone-input"]', timeout=30000)
        door_log.clear()
        await page.evaluate("() => localStorage.removeItem('rank.details.door')")
        await page.goto(BASE + "/rank", wait_until="domcontentloaded")
        await page.wait_for_timeout(6000)
        has_bar = await page.locator('[data-testid="rank-profile"]').count()
        print("INFO signed out /rank shows rank-profile:", has_bar, "url:", page.url)
        if has_bar:
            s3 = await text(page, "rank-profile-summary")
            print("INFO signed-out bar:", s3)
        check("B7 no door request when signed out", not door_log, door_log)
        await page.screenshot(path="/tmp/shots/i154_b7.jpg", type="jpeg", quality=30)

        check("Z no blocked writes under /api/jl", not blocked, blocked)
        await b.close()
    p = sum(1 for _, ok in RES if ok)
    print(f"RESULT {p}/{len(RES)}")


if __name__ == "__main__":
    asyncio.run(main())
