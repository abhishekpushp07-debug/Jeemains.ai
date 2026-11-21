"""TEST-ONLY probe for DOM structure (iteration 212)."""
import asyncio, os, sys, importlib.util
sys.argv = [sys.argv[0]]
spec = importlib.util.spec_from_file_location('v211', os.path.join(os.path.dirname(__file__), 'ui_verify211_lib.py'))
v = importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as pw:
        br, page, bad, logs = await v.open_as(pw, 'owner', 'desk')
        bid, mid = v.F['boxed']
        await page.goto(f'{v.BASE}/super-admin/fix/{bid}/{mid}?all=1')
        await page.wait_for_selector('[data-testid="all-questions-list"]', timeout=30000)
        await page.click('[data-testid="all-questions-filter-proof"]'); await page.wait_for_timeout(4000)
        print(await page.evaluate("() => { const l = document.querySelector('[data-testid=\"proof-list\"]'); return [l.tagName, l.children.length, [...l.children].slice(0,3).map(c => c.tagName + ' ' + c.className + ' ' + c.dataset.testid), l.outerHTML.slice(0, 1500)]; }"))
        # try as student on a real Draft
        for key in ('boxed_small', 'draft'):
            b2, m2 = v.F[key]
            await page.goto(f'{v.BASE}/super-admin/fix/{b2}/{m2}?all=1'); await page.wait_for_selector('[data-testid="all-questions-list"]', timeout=30000)
            await page.locator('[data-testid^="mock-try-"]').first.click(); await page.wait_for_timeout(8000)
            print(key, 'after try ->', page.url, bad[-2:])
        await br.close()
        br, page, bad, logs = await v.open_as(pw, 'student', 'desk')
        await page.goto(f"{v.BASE}/results/{v.F['done_attempt']}?view=solutions"); await page.wait_for_timeout(8000)
        print(await page.evaluate("() => { const s = document.querySelector('[data-testid=\"solution-content-1\"]'); return s ? s.outerHTML.slice(0, 2500) : 'none'; }"))
        await br.close()

asyncio.run(main())
