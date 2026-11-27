# Misfire Mock: "fewer than asked" notice, "nothing readable" error, and the clock running out inside the player.
# READ ONLY: same guards as misfire_mock_check.py. Results are rewritten IN THE BROWSER only (questions marked "dropped")
# to stand in for papers whose questions can not be used; the browser clock is moved forward with a page variable.
# usage: python3 misfire_mock_short_check.py [width]
import asyncio
import json
import re
import sys

sys.path.insert(0, "/app/tests")
from dotenv import dotenv_values  # noqa: E402
from playwright.async_api import async_playwright  # noqa: E402
from shine_helpers import sign_in  # noqa: E402

BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
W = int(sys.argv[1]) if len(sys.argv) > 1 else 390
RES, BLOCKED, FAKED, ERRORS = [], [], [], []
MODE = {"drop": "none"}  # none | few | all
CLOCK = "(() => { const N = Date.now.bind(Date); const off = () => (window.__off || 0); Date.now = () => N() + off(); })()"


def check(name, ok, info=""):
    RES.append((name, bool(ok)))
    print(("PASS " if ok else "FAIL ") + name + (" :: " + str(info) if info != "" else ""), flush=True)


def tid(t):
    return f'[data-testid="{t}"]'


async def guards(ctx):
    async def g(route):
        r = route.request
        if r.method in ("GET", "HEAD", "OPTIONS") or "/api/jl/auth" in r.url:
            await route.fallback(); return
        path = r.url.split("?")[0].replace(BASE, "")
        m = re.search(r"/my/misfire/([^/]+)/(try|done)$", path)
        if m and r.method == "POST":
            FAKED.append(m.group(2) + " " + m.group(1))
            body = {"correct": True, "item": {"id": m.group(1), "status": "open", "tries": 1, "last_correct": True}} if m.group(2) == "try" else {"ok": True}
            await route.fulfill(status=200, content_type="application/json", body=json.dumps({"data": body, "error": None, "meta": {}})); return
        BLOCKED.append(r.method + " " + path)
        await route.fulfill(status=418, content_type="application/json", body='{"data":null,"error":{"code":"blocked","message":"blocked by test"},"meta":{}}')
    await ctx.route(re.compile(r".*/api/jl/.*"), g)

    async def results(route):
        if route.request.method != "GET" or MODE["drop"] == "none":
            await route.fallback(); return
        resp = await route.fetch()
        try:
            j = await resp.json()
            qs = (j.get("data") or {}).get("questions") or []
            for i, q in enumerate(qs):
                if MODE["drop"] == "all" or i >= 2:
                    q["disposition"] = "dropped"
            await route.fulfill(response=resp, body=json.dumps(j))
        except Exception:
            await route.fulfill(response=resp)
    await ctx.route(re.compile(r".*/api/jl/attempts/[^/]+/results.*"), results)


async def visible(page, t, timeout=8000):
    try:
        await page.wait_for_selector(tid(t), state="visible", timeout=timeout); return True
    except Exception:
        return False


async def ask(page, subject, n):
    await page.goto(BASE + "/misfire/mock/new", wait_until="domcontentloaded")
    await visible(page, "mock-new-count", 60000)
    await page.click(tid(f"mock-subject-{subject}"))
    await page.wait_for_timeout(300)
    for _ in range(n):
        await page.click(tid("mock-count-more"))
    await page.click(tid("mock-new-bar-go"))


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": W, "height": 844})
        await ctx.add_init_script(CLOCK)
        await guards(ctx)
        page = await ctx.new_page()
        page.on("pageerror", lambda e: ERRORS.append(str(e)[:200]))
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await sign_in(page, width=W)

        # 1. Only 2 usable questions per paper: asking 20 Maths -> fewer, with the notice.
        MODE["drop"] = "few"
        await ask(page, "mathematics", 20)
        ok = await visible(page, "mock-ready-screen", 120000)
        check("few: ready screen", ok)
        if ok:
            size = await page.inner_text(tid("mock-ready-size"))
            short = await page.locator(tid("mock-ready-short")).count()
            got = int(re.findall(r"\d+", size)[0])
            check("few: fewer than asked + short notice", got < 20 and short == 1, f"{size} short={short}")
            await page.screenshot(path=f"/app/test_reports/artifacts/misfire_mock_short_ready_{W}.png", quality=40, type="jpeg")
            await page.reload(wait_until="domcontentloaded")
            await visible(page, "mock-ready-screen", 30000)
            print("after reload short notice:", await page.locator(tid("mock-ready-short")).count())
            await page.click(tid("mock-remove")); await page.wait_for_timeout(1000)

        # 2. Nothing usable: an error in the sheet, nothing kept.
        MODE["drop"] = "all"
        await ask(page, "chemistry", 5)
        ok = await visible(page, "mock-making-error", 120000)
        check("all dropped: making error shown", ok, (await page.inner_text(tid("mock-making-sheet")))[:160].replace("\n", " ") if ok else "")
        check("all dropped: retry + close buttons", await page.locator(tid("mock-making-retry")).count() == 1 and await page.locator(tid("mock-making-cancel")).count() == 1)
        await page.click(tid("mock-making-cancel")); await page.wait_for_timeout(500)

        # 3. Clock runs out inside the player: answers marked, result opens.
        MODE["drop"] = "none"
        await ask(page, "physics", 2)
        await visible(page, "mock-ready-screen", 120000)
        await page.click(tid("mock-start"))
        await visible(page, "mock-player-screen", 15000)
        if await page.locator(tid("mock-option-B")).count():
            await page.click(tid("mock-option-B"))
        await page.wait_for_timeout(800)
        await page.evaluate("window.__off = 6 * 60 * 1000")
        ok = await visible(page, "mock-result-screen", 20000)
        check("clock out in player -> result", ok, await page.inner_text(tid("mock-result-line")) if ok else await page.inner_text("body"))
        if ok:
            ans = [await page.inner_text(tid(f"mock-result-{o}")) for o in ("correct", "incorrect", "skipped")]
            check("expiry kept the answer (1 answered, 1 skipped)", int(ans[0]) + int(ans[1]) == 1 and ans[2].strip() == "1", ans)
        await b.close()
    print("FAKED", FAKED)
    print("BLOCKED", BLOCKED)
    print("PAGEERRORS", ERRORS)
    print(f"{sum(1 for _, ok in RES if ok)}/{len(RES)} passed")

asyncio.run(main())
