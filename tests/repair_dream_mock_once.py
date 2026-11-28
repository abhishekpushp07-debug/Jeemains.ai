# One-off repair (28 Nov 2026): misfire_web_check.py (before its /api/rf/dream stand-in) made the app take the QA
# learner's real PYQ attempt out of his Dream College meter list on the preview server. Opening that result once,
# normally, lets the app record it again exactly as it always does (POST /api/rf/dream/mocks). Website writes blocked.
import asyncio
import re
import sys

sys.path.insert(0, "/app/tests")
from dotenv import dotenv_values  # noqa: E402
from playwright.async_api import async_playwright  # noqa: E402
from shine_helpers import sign_in  # noqa: E402

BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
AID = "1ea510f2-1d2a-41f7-9bb4-a8b28c16f98f"
SENT, BLOCKED = [], []


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844})

        async def g(route):
            r = route.request
            if r.method in ("GET", "HEAD", "OPTIONS") or "/api/jl/auth" in r.url:
                await route.fallback(); return
            BLOCKED.append(r.method + " " + r.url.split("?")[0])
            await route.fulfill(status=418, content_type="application/json", body='{"data":null,"error":{"code":"blocked","message":"blocked"},"meta":{}}')
        await ctx.route(re.compile(r".*/api/jl/.*"), g)
        page = await ctx.new_page()
        page.on("request", lambda r: SENT.append(r.method + " " + r.url.split("?")[0].replace(BASE, "")) if "/api/rf/dream" in r.url and r.method != "GET" else None)
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await sign_in(page, width=390)
        await page.goto(BASE + f"/result/{AID}", wait_until="domcontentloaded")
        for _ in range(60):
            if any("/api/rf/dream/mocks" in s for s in SENT):
                break
            await page.wait_for_timeout(1000)
        await page.wait_for_timeout(2000)
        print("dream writes:", SENT, "blocked:", BLOCKED)
        await ctx.unroute_all(behavior="ignoreErrors")
        await b.close()


asyncio.run(main())
