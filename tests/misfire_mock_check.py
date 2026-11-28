# Misfire Mock + My Tests exam tabs, end to end in the browser, READ ONLY for the QA learner.
# Every write to the website outside /auth is stopped, except Misfire's "try" and "done" (what a right mock answer
# sends): those are answered by the browser and counted, never reach the website.
# usage: python3 misfire_mock_check.py [width]
import asyncio
import json
import re
import sys

sys.path.insert(0, "/app/tests")
from dotenv import dotenv_values  # noqa: E402
from playwright.async_api import async_playwright  # noqa: E402
from shine_helpers import sign_in  # noqa: E402

BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
W = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 390
# "right": every result's option questions answered in the browser with key "A", so picking A is right (tests "Samajh gaya").
RIGHT = len(sys.argv) > 2 and sys.argv[2] == "right"
RES, BLOCKED, FAKED, ERRORS = [], [], [], []
SHOTS = "/app/test_reports/artifacts/misfire_mock"


def check(name, ok, info=""):
    RES.append((name, bool(ok)))
    print(("PASS " if ok else "FAIL ") + name + (" :: " + str(info) if info else ""), flush=True)


def tid(t):
    return f'[data-testid="{t}"]'


def env(data):
    return json.dumps({"data": data, "error": None, "meta": {"api_version": "1"}})


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
            await route.fulfill(status=200, content_type="application/json", body=env(body)); return
        BLOCKED.append(r.method + " " + path)
        await route.fulfill(status=418, content_type="application/json", body='{"data":null,"error":{"code":"blocked","message":"blocked by test"},"meta":{}}')
    await ctx.route(re.compile(r".*/api/jl/.*"), g)

    async def results(route):
        if route.request.method != "GET":
            await route.fallback(); return
        resp = await route.fetch()
        try:
            j = await resp.json()
            for q in (j.get("data") or {}).get("questions") or []:
                if q.get("options"):
                    q["answer"] = "A"; q["accepted_answers"] = ["A"]
            await route.fulfill(response=resp, body=json.dumps(j))
        except Exception:
            await route.fulfill(response=resp)
    if RIGHT:
        await ctx.route(re.compile(r".*/api/jl/attempts/[^/]+/results.*"), results)


async def visible(page, t, timeout=8000):
    try:
        await page.wait_for_selector(tid(t), state="visible", timeout=timeout); return True
    except Exception:
        return False


async def main():
    import os
    os.makedirs(SHOTS, exist_ok=True)
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": W, "height": 844})
        await guards(ctx)
        page = await ctx.new_page()
        page.on("pageerror", lambda e: ERRORS.append(str(e)[:200]))
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await sign_in(page, width=W)

        # 1. My Tests: four exam tabs, no outcome filters, the chosen one red.
        await page.goto(BASE + "/tests", wait_until="domcontentloaded")
        ok = await visible(page, "my-tests-exam-filters", 45000)
        check("my tests exam filter row shows", ok)
        tabs = page.locator(tid("my-tests-exam-filters") + ' [role="tab"]')
        n = await tabs.count()
        labels = [await tabs.nth(i).inner_text() for i in range(n)]
        check("exactly 4 exam tabs", n == 4, labels)
        body = await page.inner_text("body")
        check("no outcome filters (All outcomes..Sealed)", not any(x in body for x in ["All outcomes", "Time expired", "Sealed"]))
        if n >= 2:
            await tabs.nth(1).click()
            await page.wait_for_timeout(1200)
            check("2nd exam tab selected", await tabs.nth(1).get_attribute("aria-selected") == "true")
            await tabs.nth(0).click()
            await page.wait_for_timeout(800)
        await page.screenshot(path=f"{SHOTS}/1_my_tests.png")

        # 2. Misfire → Mock tab → new mock.
        await page.goto(BASE + "/misfire", wait_until="domcontentloaded")
        check("misfire mock CTA on Sab tab", await visible(page, "misfire-mock-cta", 45000))
        await page.click(tid("misfire-tab-mock"))
        check("mock tab hero", await visible(page, "misfire-mock-hero", 15000))
        await page.click(tid("misfire-mock-new"))
        ok = await visible(page, "mock-new-count", 60000)
        check("new mock screen loads pool", ok)
        await page.screenshot(path=f"{SHOTS}/2_new.png")
        for s in ["physics", "chemistry", "mathematics"]:
            await page.click(tid(f"mock-subject-{s}"))
            await page.wait_for_timeout(300)
            await page.click(tid(f"mock-count-{s}-5"))
            await page.wait_for_timeout(200)
            v = await page.inner_text(tid("mock-count-value"))
            check(f"{s}: 5 chosen", v.strip().startswith("5"), v)
        # chapters: untick all, then pick two in Maths
        await page.click(tid("mock-chapter-all"))
        check("select-all off shows hint", await visible(page, "mock-chapter-none", 4000))
        v = await page.inner_text(tid("mock-count-value"))
        check("count follows unticked chapters (0)", v.strip().startswith("0"), v)
        await page.click(tid("mock-chapter-0"))
        if await page.locator(tid("mock-chapter-1")).count():
            await page.click(tid("mock-chapter-1"))
        await page.click(tid("mock-count-more"))
        await page.click(tid("mock-count-more"))
        await page.click(tid("mock-count-more"))
        v = await page.inner_text(tid("mock-count-value"))
        print("maths after chapters:", v, "most:", await page.inner_text(tid("mock-new-most")))
        await page.screenshot(path=f"{SHOTS}/3_chapters.png")
        print("bar:", await page.inner_text(tid("mock-new-bar")))
        await page.click(tid("mock-new-bar-go"))
        ok = await visible(page, "mock-ready-screen", 120000)
        check("mock made, ready screen", ok, await page.inner_text(tid("mock-making-sheet")) if not ok and await page.locator(tid("mock-making-sheet")).count() else "")
        if not ok:
            raise SystemExit
        print("ready:", await page.inner_text(tid("mock-ready-size")))
        await page.wait_for_timeout(2500)
        await page.screenshot(path=f"{SHOTS}/4_ready.png")

        # 3. Take it: answer a few, submit.
        await page.click(tid("mock-start"))
        check("player opens", await visible(page, "mock-player-screen", 15000))
        t1 = await page.inner_text(tid("mock-timer-label"))
        await page.wait_for_timeout(2200)
        t2 = await page.inner_text(tid("mock-timer-label"))
        check("timer runs", t1 != t2, f"{t1} -> {t2}")
        await page.screenshot(path=f"{SHOTS}/5_player.png")
        for i in range(4):
            if await page.locator(tid("mock-integer-input")).count():
                await page.fill(tid("mock-integer-input"), "2")
            elif await page.locator(tid("mock-option-A")).count():
                await page.click(tid("mock-option-A"))
            else:
                opts = page.locator('[data-testid^="mock-option-"], [data-testid^="mock-piece-option"]')
                if await opts.count():
                    await opts.first.click()
            nxt = page.locator(tid("mock-next-button"))
            if await nxt.count():
                await nxt.click()
                await page.wait_for_timeout(500)
        ans = await page.inner_text(tid("mock-count-answered"))
        check("answers counted", ans.strip()[0] != "0", ans)
        # leave and come back: answers kept
        await page.click(tid("mock-exit-button"))
        await page.click(tid("mock-exit-confirm"))
        await page.wait_for_timeout(1500)
        await page.goto(BASE + "/tests?tab=progress", wait_until="domcontentloaded")
        ok = await visible(page, "my-tests-exam-filters", 45000)
        await page.click(tid("my-tests-tab-progress"))
        await page.wait_for_timeout(1500)
        cards = page.locator('[data-testid^="mock-card-"]')
        check("active mock listed in My Tests > In progress", await cards.count() >= 1)
        await page.screenshot(path=f"{SHOTS}/6_tests_progress.png")
        await cards.first.click()
        check("resume opens player", await visible(page, "mock-player-screen", 15000))
        ans2 = await page.inner_text(tid("mock-count-answered"))
        check("answers kept after leaving", ans2 == ans, f"{ans} / {ans2}")
        await page.click(tid("mock-submit-top"))
        await page.click(tid("mock-confirm-submit"))
        ok = await visible(page, "mock-result-screen", 20000)
        check("result screen", ok)
        await page.wait_for_timeout(3000)
        c, w, s = [await page.inner_text(tid(f"mock-result-{o}")) for o in ("correct", "incorrect", "skipped")]
        print("result:", c, w, s, await page.inner_text(tid("mock-result-line")))
        await page.screenshot(path=f"{SHOTS}/7_result.png")
        await page.locator(tid("mock-solution-card")).scroll_into_view_if_needed()
        await page.wait_for_timeout(1500)
        await page.screenshot(path=f"{SHOTS}/8_solution.png")
        key = await page.inner_text(tid("mock-solution-key"))
        check("answer key shown", bool(key.strip()) and key.strip() != "—", key)
        check("understood box", await page.locator(tid("mock-result-understood")).count() == 1, await page.inner_text(tid("mock-result-understood")))

        # 4. Listed under Completed and in Misfire's Mock tab.
        await page.goto(BASE + "/tests", wait_until="domcontentloaded")
        await visible(page, "my-tests-exam-filters", 45000)
        await page.click(tid("my-tests-tab-completed"))
        await page.wait_for_timeout(1500)
        check("done mock in My Tests > Completed", await page.locator('[data-testid^="mock-score-"]').count() >= 1)
        await page.screenshot(path=f"{SHOTS}/9_tests_completed.png")
        await page.goto(BASE + "/misfire", wait_until="domcontentloaded")
        await visible(page, "misfire-tab-mock", 45000)
        await page.click(tid("misfire-tab-mock"))
        await page.wait_for_timeout(1500)
        check("mock in Misfire > Mock", await page.locator('[data-testid^="misfire-mock-score-"]').count() >= 1)
        await page.screenshot(path=f"{SHOTS}/10_misfire_mocks.png")
        await b.close()
    print("FAKED", FAKED)
    print("BLOCKED", BLOCKED)
    print("PAGEERRORS", ERRORS)
    print(f"{sum(1 for _, ok in RES if ok)}/{len(RES)} passed")

if __name__ == "__main__":
    asyncio.run(main())
