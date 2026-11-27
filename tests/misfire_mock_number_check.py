# Misfire Mock serial numbers: two mocks made each from a cold /misfire/mock/new (the list never opened first) must be
# #n and #n+1. READ ONLY for the QA learner (same stand-ins as misfire_mock_check.py; nothing is submitted).
import asyncio
import re
import sys

sys.path.insert(0, "/app/tests")
from playwright.async_api import async_playwright  # noqa: E402
from shine_helpers import sign_in  # noqa: E402
from misfire_mock_check import BASE, BLOCKED, ERRORS, RES, check, guards, tid, visible  # noqa: E402

W = int(sys.argv[1]) if len(sys.argv) > 1 else 390


async def make(page):
    await page.goto(BASE + "/misfire/mock/new", wait_until="domcontentloaded")
    await visible(page, "mock-new-count", 60000)
    await page.click(tid("mock-subject-physics"))
    await page.click(tid("mock-count-physics-5"))
    await page.click(tid("mock-new-bar-go"))
    ok = await visible(page, "mock-ready-screen", 120000)
    title = await page.inner_text(tid("mock-ready-header")) if ok else ""
    m = re.search(r"#(\d+)", title)
    return int(m.group(1)) if m else None


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": W, "height": 844})
        await guards(ctx)
        page = await ctx.new_page()
        page.on("pageerror", lambda e: ERRORS.append(str(e)[:200]))
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await sign_in(page, width=W)
        a = await make(page)
        b2 = await make(page)
        c = await make(page)
        check("serials go up from a cold start", a is not None and b2 == a + 1 and c == a + 2, f"{a} {b2} {c}")
        await b.close()
    print("BLOCKED", BLOCKED)
    print("PAGEERRORS", ERRORS)
    print(f"{sum(1 for _, ok in RES if ok)}/{len(RES)} passed")

asyncio.run(main())
