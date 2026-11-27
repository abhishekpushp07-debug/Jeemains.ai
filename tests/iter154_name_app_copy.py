# Iteration 154 A6: the app server's copy of the chosen name (GET /api/rf/name, answered by the browser) wins on Account
# over the website's display_name. Read-only: nothing is saved.
import asyncio
import json
import re
import sys

from playwright.async_api import async_playwright

sys.path.insert(0, "/app/tests")
from shine_helpers import sign_in  # noqa: E402
from iter154_name_rank_door import BASE, check, text, reload_home, RES  # noqa: E402


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        page = await (await b.new_context(viewport={"width": 390, "height": 844})).new_page()
        blocked = []

        async def guard(route):
            r = route.request
            if r.method in ("GET", "HEAD", "OPTIONS") or "/api/jl/auth/" in r.url:
                await route.fallback(); return
            blocked.append(r.method + " " + r.url)
            await route.fulfill(status=418, body="{}")
        await page.route(re.compile(r".*/api/jl/.*"), guard)
        await page.route(re.compile(r".*/api/rf/name(\?.*)?$"), lambda route: route.fulfill(
            status=200, content_type="application/json", body=json.dumps({"name": "Ravi Kumar"})) if route.request.method == "GET" else route.abort())

        async def nm(route):
            resp = await route.fetch(); j = await resp.json(); d = j.get("data")
            if isinstance(d, dict):
                (d["user"] if isinstance(d.get("user"), dict) else d)["display_name"] = "Asha Rao"
            await route.fulfill(response=resp, body=json.dumps(j))
        await page.route(re.compile(r".*/api/jl/auth/(session|me)(\?.*)?$"), nm)
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await sign_in(page)
        await reload_home(page)
        g = await text(page, "home-greeting")
        check("A6a Home greeting uses display_name (asha)", g.endswith(", asha."), g)
        await page.locator('[data-testid="home-account-button"]').first.click()
        await page.wait_for_selector('[data-testid="account-name"]', timeout=20000)
        await page.wait_for_timeout(4000)
        a = await text(page, "account-name")
        check("A6b Account: app server copy (Ravi Kumar) wins over display_name", a == "Ravi Kumar", a)
        check("A6z no blocked writes", not blocked, blocked)
        await b.close()
    print(f"RESULT {sum(1 for _, o in RES if o)}/{len(RES)}")


asyncio.run(main())
