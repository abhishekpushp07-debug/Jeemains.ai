# T1 debug: cold list error, and the 'Misfire kholo' button from a result (visible-only check). READ ONLY.
import asyncio, sys
sys.path.insert(0, "/app/tests")
import misfire_web_t1_extra as X
from playwright.async_api import async_playwright
from shine_helpers import sign_in

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844})
        await X.setup(ctx)
        page = await ctx.new_page()
        X.S["hist"] = "500"
        await page.goto(X.BASE + "/", wait_until="domcontentloaded")
        await sign_in(page, width=390)
        await page.goto(X.BASE + "/misfire?tab=web", wait_until="domcontentloaded")
        await X.vis(page, "misfire-web-hero", 45000); await page.wait_for_timeout(5000)
        ids = await page.locator('[data-testid^="misfire-web-"]').evaluate_all("els => els.map(e => e.dataset.testid)")
        X.check("D1 cold list 500 -> ErrorBox", any("error" in i for i in ids), ids)
        await page.screenshot(path=X.SHOTS + "_cold_err.jpg", quality=40, type="jpeg")
        X.S["hist"] = "two"
        await page.goto(X.BASE + f"/result/{X.FIN}", wait_until="domcontentloaded")
        await X.vis(page, "result-misfire-open", 60000)
        await page.click(X.tid("result-misfire-open"))
        await page.wait_for_timeout(6000)
        heroes = await page.locator(X.tid("misfire-web-hero")).count()
        vis_heroes = await page.locator(X.tid("misfire-web-hero") + " >> visible=true").count()
        sel = await page.locator('[data-testid="misfire-tab-web"]').evaluate_all("els => els.map(e => [e.getAttribute('aria-selected'), e.offsetParent !== null])")
        X.check("D2 Misfire kholo shows the Mock tab", vis_heroes >= 1, [page.url, heroes, vis_heroes, sel])
        await page.screenshot(path=X.SHOTS + "_kholo.jpg", quality=40, type="jpeg")
        await b.close()
    print("blocked", X.BLOCKED, "dream", X.DREAM)

asyncio.run(main())
