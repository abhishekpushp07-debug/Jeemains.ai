"""TEST-ONLY (iteration 216): open the boxed chapter Proof view on desktop 1920 via the bridge and print every /api 4xx with its full URL and body."""
import asyncio, os, sys, importlib.util
sys.argv = [sys.argv[0], 'none']
spec = importlib.util.spec_from_file_location('v211', os.path.join(os.path.dirname(__file__), 'ui_verify211_lib.py'))
v = importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as pw:
        br, page, bad, logs = await v.open_as(pw, 'owner', 'desk')
        async def show(r):
            if '/api/' in r.url and r.status >= 400:
                try: body = (await r.text())[:300]
                except Exception as e: body = str(e)
                print('BAD', r.status, r.request.method, r.url.split('/api')[-1], body)
        page.on('response', lambda r: asyncio.ensure_future(show(r)))
        bid, mid = v.F['boxed']
        await page.goto(f'{v.BASE}/super-admin/fix/{bid}/{mid}?all=1')
        await page.wait_for_selector('[data-testid="all-questions-list"]', timeout=30000)
        await page.click('[data-testid="all-questions-filter-proof"]')
        await page.wait_for_timeout(12000)
        errs = await page.locator('text=Page ki picture nahi khuli').count()
        print('picture errors on page:', errs, 'bad', bad, 'logs', logs)
        await br.close()

asyncio.run(main())
