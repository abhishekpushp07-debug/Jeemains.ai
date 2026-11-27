# Screenshots of the app (web preview, phone size 390 x 844) for the website's look kit (website_look_kit/screens).
# QA learner, reads only: Home, My Tests (3 tabs), a finished paper's Analysis (never Solutions: it posts), chapter-wise
# (All / Class 11 / Class 12), Rank, Student Choice, Misfire, All India series. Stand-ins answer the All India days in
# the browser (shine_helpers), as in every check since 26 Nov.
import asyncio, os, sys
from playwright.async_api import async_playwright
sys.path.insert(0, "/app/tests")
from shine_helpers import sign_in  # noqa: E402

URL = os.environ.get("APP", "http://localhost:3000")
OUT = "/app/website_look_kit/screens"
RESULT = "c0061f81-7ae9-432b-8ca5-312c8d39d4b5"  # PYQ 22 Jan 2026 S1, finished
os.makedirs(OUT, exist_ok=True)
done = []


async def shot(page, name, scrolls=(0,)):
    await page.wait_for_timeout(2500)
    for i, dy in enumerate(scrolls):
        if dy:
            await page.mouse.move(195, 500)
            await page.mouse.wheel(0, dy)
            await page.wait_for_timeout(1200)
        path = f"{OUT}/{name}{'' if len(scrolls) == 1 else f'_{i + 1}'}.png"
        await page.screenshot(path=path, full_page=False)
        done.append(path.rsplit("/", 1)[1])


async def go(page, path, wait):
    await page.evaluate(f"window.history.pushState(null, '', '{path}'); window.dispatchEvent(new PopStateEvent('popstate'))")
    try:
        await page.wait_for_selector(f'[data-testid="{wait}"]', timeout=30000)
    except Exception:
        await page.goto(URL + path)
        await page.wait_for_selector(f'[data-testid="{wait}"]', timeout=45000)


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        page = await (await browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2)).new_page()
        blocked = []
        async def guard(route):
            r = route.request
            if r.method not in ("GET", "HEAD", "OPTIONS") and "/api/jl/" in r.url and "/auth/" not in r.url:
                blocked.append(f"{r.method} {r.url}"); await route.abort(); return
            await route.continue_()
        await page.route("**/api/jl/**", guard)
        await page.goto(URL + "/", wait_until="domcontentloaded")
        try:
            await sign_in(page, landing="home-screen")
        except Exception as e:
            await page.screenshot(path="/tmp/kit_signin_fail.png")
            print("sign-in failed; blocked:", blocked, "url:", page.url, str(e)[:200]); raise
        await shot(page, "01_home", scrolls=(0, 700, 700, 700, 900))
        for tab in ["completed", "progress", "saved"]:
            await go(page, f"/tests?tab={tab}&at={tab}", "my-tests-screen")
            await shot(page, f"02_my_tests_{tab}")
        await go(page, f"/result/{RESULT}", "result-score-version-label")
        await shot(page, "03_result_analysis", scrolls=(0, 700, 700))
        await go(page, "/catalogue?slug=jee-main&kind=chapters", "catalogue-jee-main-chapters")
        await shot(page, "04_chapter_wise_all", scrolls=(0, 900))
        for cls in ["11", "12"]:
            try:
                await page.click(f'[data-testid="catalogue-class-{cls}"]', timeout=8000)
                await shot(page, f"04_chapter_wise_class_{cls}")
            except Exception as e:
                print("class tab", cls, "not clicked:", str(e)[:120])
        await go(page, "/rank", "rank-screen")
        await shot(page, "05_rank", scrolls=(0, 800))
        await go(page, "/choice", "choice-screen")
        await shot(page, "06_student_choice", scrolls=(0, 800))
        await go(page, "/misfire", "misfire-screen")
        await shot(page, "07_misfire")
        await go(page, "/live", "series-hub")
        await shot(page, "08_all_india_series")
        await browser.close()
        print("blocked writes:", blocked)
    print("saved:", done)

asyncio.run(main())
