"""TEST-ONLY (iteration 217): Super Admin regression on master bridge: Master home/exam/type pages, storage badge, Try as student, Library.
Run: python tests/ui_admin_regress217.py"""
import asyncio, sys
sys.path.insert(0, '/app/backend/tests')
from playwright.async_api import async_playwright
from ui_master217_lib import open_as, ok, R, BASE, SS

MID = 'd1f8da2c-aeeb-56c7-91bd-a35f9959fcbb'


async def main():
    async with async_playwright() as pw:
        for w, h in ((1920, 1000), (390, 844)):
            br, page, bad, logs = await open_as(pw, 'owner', w, h)
            tag = f'admin-{w}'
            try:
                await page.goto(BASE + '/super-admin'); await page.wait_for_selector('[data-testid="storage-badge"]', timeout=30000)
                ok(f'{tag}: storage badge visible', await page.is_visible('[data-testid="storage-badge"]'))
                await page.goto(BASE + '/super-admin/exam/jee-main/jee-main:mocks'); await page.wait_for_selector('[data-testid="mock-list"]', timeout=30000)
                await page.wait_for_timeout(1500)
                o = await page.evaluate('[document.documentElement.scrollWidth, document.documentElement.clientWidth]')
                ok(f'{tag}: type page no horizontal overflow', o[0] <= o[1] + 1, o)
                d = page.locator(f'[data-testid="mock-duplicates-{MID}"]')
                if await d.count():
                    await d.locator('summary').click(); await page.wait_for_timeout(300)
                    bx = await d.bounding_box(); ok(f'{tag}: dup note inside viewport', bx and bx['x'] + bx['width'] <= w + 1, bx)
                await page.screenshot(path=f'{SS}/{tag}-type.jpg', quality=40)
                try_btn = page.locator(f'[data-testid="mock-try-{MID}"]')
                if await try_btn.count():
                    pages0 = len(page.context.pages)
                    await try_btn.click(); await page.wait_for_timeout(5000)
                    newp = page.context.pages[-1] if len(page.context.pages) > pages0 else page
                    print(tag, 'try as student ->', newp.url)
                    ids = await newp.evaluate("() => [...document.querySelectorAll('[data-testid]')].map(e=>e.dataset.testid).filter(x=>/player|question|option|preview/.test(x)).slice(0,8)")
                    print(tag, 'ids', ids)
                    ok(f'{tag}: Try as student opens player/preview', len(ids) > 0, (newp.url, ids))
                    await newp.screenshot(path=f'{SS}/{tag}-try.jpg', quality=40)
                else:
                    ok(f'{tag}: try-as-student button present', False)
                await page.goto(BASE + '/super-admin/library'); await page.wait_for_timeout(3000)
                ok(f'{tag}: library page loads', 'Library' in (await page.text_content('body')))
                ok(f'{tag}: no page errors', not logs, logs[:3]); print(tag, 'bad', bad[:6])
            finally:
                await br.close()
    print('TOTAL', len(R), 'PASS', sum(1 for _, x in R if x), 'FAIL', sum(1 for _, x in R if not x))

asyncio.run(main())
