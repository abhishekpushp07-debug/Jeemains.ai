"""TEST-ONLY recheck: tap sizes after open animations settle (popover / dialogs), PIN reset dialog, retry busy state. Uses ui_phase1_iso222 helpers."""
import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ui_phase1_iso222 import open_as, BASE, taps, say, toast_text, SS, CHAPTERS, overflow, RESULT  # noqa: E402


async def run():
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        for size in ('mob', 'desk'):
            br, page, bad, logs = await open_as(pw, 'owner', size)
            try:
                await page.goto(BASE + '/super-admin'); await page.wait_for_selector('[data-testid=machine-attention-dot]', timeout=20000)
                await page.click('[data-testid=storage-badge]'); await page.wait_for_selector('[data-testid=machine-panel]'); await page.wait_for_timeout(1200)
                await taps(page, f'machine {size} settled')
                h = await page.evaluate("() => [...document.querySelectorAll('.machine-retry,[data-testid=storage-check-now]')].map(e => [e.dataset.testid, e.getBoundingClientRect().height])")
                print('   heights', h)
                # busy state: delay the control response so the spinner can be seen
                async def slow(route):
                    await asyncio.sleep(2); await route.fulfill(status=409, content_type='application/json', body='{"detail":"TEST_ delayed 409"}')
                await page.route('**/control', slow)
                await page.click('[data-testid=machine-retry-qa-stuck-book]'); await page.wait_for_timeout(500)
                dis = await page.locator('[data-testid=machine-retry-qa-stuck-book]').is_disabled()
                spin = await page.locator('[data-testid=machine-retry-qa-stuck-book] .spin').count()
                op = await page.evaluate("() => getComputedStyle(document.querySelector('[data-testid=machine-retry-qa-stuck-book]')).opacity")
                say(f'machine {size}: retry button busy (disabled+spinner+dimmed)', dis and spin == 1 and float(op) < 1, (dis, spin, op))
                t = await toast_text(page); print('   toast', t)
                if size == 'mob': await page.screenshot(path=f'{SS}/machine_mob_busy.png', quality=40, type='jpeg')
                await page.keyboard.press('Escape')
                await page.goto(BASE + CHAPTERS); await page.wait_for_selector('[data-testid=mock-list]', timeout=20000)
                await page.locator('button:has-text("Upload PDF")').first.click(); await page.wait_for_selector('[data-testid=upload-dialog]'); await page.wait_for_timeout(1200)
                await taps(page, f'upload dialog {size} settled')
                if size == 'mob':
                    await overflow(page, 'upload dialog mob')
                    await page.screenshot(path=f'{SS}/upload_dialog_mob.png', quality=40, type='jpeg')
                await page.keyboard.press('Escape'); await page.wait_for_timeout(500)
                await page.goto(BASE + '/super-admin/students'); await page.wait_for_selector('[data-testid=student-directory]', timeout=20000)
                o = page.locator('[data-testid$=-open][data-testid^=owner-reset-]').first
                tid = (await o.get_attribute('data-testid'))[:-5]; await o.click(); await page.wait_for_selector(f'[data-testid={tid}-dialog]'); await page.wait_for_timeout(1000)
                print('   PIN dialog:', (await page.inner_text(f'[data-testid={tid}-dialog]')).replace('\n', ' | '))
                say(f'PIN reset dialog {size} opens', True); await taps(page, f'PIN dialog {size}')
                if size == 'mob': await overflow(page, 'PIN dialog mob')
                await page.click(f'[data-testid={tid}-cancel]'); await page.wait_for_timeout(500)
                say(f'PIN dialog {size} cancel closes', await page.locator(f'[data-testid={tid}-dialog]').count() == 0)
                # block dialog tap sizes
                bb = page.locator('[data-testid^=student-block-]').first; await bb.click(); await page.wait_for_timeout(1000)
                await taps(page, f'block dialog {size}')
                await page.keyboard.press('Escape')
            except Exception as e:
                say(f'recheck {size} exception', False, e)
            finally:
                await br.close()
    print(f"\nTOTAL {sum(o for _, o in RESULT)}/{len(RESULT)}"); [print('  FAILED', n) for n, o in RESULT if not o]

if __name__ == '__main__':
    asyncio.run(run())
