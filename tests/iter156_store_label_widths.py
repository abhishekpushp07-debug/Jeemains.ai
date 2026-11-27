# Iteration 156: is the store button's label cut off at common phone widths in the browser copy? (read-only, duel answered by the browser)
import asyncio
import sys

from playwright.async_api import async_playwright

sys.path.insert(0, "/app/tests")
from iter156_get_app_card import ANDROID_UA, BASE, BLOCKED, IPHONE_UA, guards, open_review  # noqa: E402
from shine_helpers import sign_in  # noqa: E402

MEASURE = """(tid) => { const b = document.querySelector(`[data-testid="${tid}"]`); if (!b) return null;
  const t = [...b.querySelectorAll('div,span')].find(e => /^(GOOGLE PLAY|APP STORE)$/.test(e.textContent) && e.children.length === 0);
  return t ? {text: t.textContent, cut: t.scrollWidth > t.clientWidth + 1, sw: t.scrollWidth, cw: t.clientWidth, font: getComputedStyle(t).fontSize} : null; }"""


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844})
        await guards(ctx)
        page = await ctx.new_page()
        await page.goto(BASE + "/api/arena/entry", wait_until="domcontentloaded")
        await sign_in(page, aits=None, board=False, landing="rapid-fire-home")
        state = await ctx.storage_state()
        await ctx.close()
        for ua, ios, tid in [(ANDROID_UA, "", "arena-get-app-android"), (IPHONE_UA, "https://apps.apple.com/app/id000000", "arena-get-app-ios")]:
            for w in (320, 360, 375, 390, 412, 430, 480):
                c = await b.new_context(viewport={"width": w, "height": 844}, user_agent=ua, storage_state=state, has_touch=True)
                await guards(c, ios)
                p = await c.new_page()
                await open_review(p, "/api/arena")
                r = await p.evaluate(MEASURE, tid)
                print(tid, w, r)
                if w == 320:
                    await p.locator(f'[data-testid="{tid}"]').scroll_into_view_if_needed()
                    await p.screenshot(path=f"/tmp/iter156_{tid}_320.jpg", quality=40, type="jpeg")
                await c.close()
        print("blocked:", BLOCKED)
        await b.close()

asyncio.run(main())
