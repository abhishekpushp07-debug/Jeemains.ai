"""TEST-ONLY iteration 223 repro: Upload PDF dialog file chooser + upload speed, via local Playwright against the preview frontend
with /api routed to the isolated bridge tests/master_bridge181.py (127.0.0.1:8770, cookies in /tmp/uibridge/bridge.json).
Run: BRIDGE_OUT=/tmp/uibridge BRIDGE_PORT=8770 python tests/ui_upload_repro223.py
"""
import asyncio, os, sys, time
from pathlib import Path
os.environ.setdefault('BRIDGE_OUT', '/tmp/uibridge'); os.environ.setdefault('BRIDGE_PORT', '8770')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.async_api import async_playwright  # noqa: E402
from ui_cut210 import open_as, BASE, say, RESULT  # noqa: E402

PDF = '/tmp/uibridge/two_mocks.pdf'
TYPE = '/super-admin/exam/bitsat/bitsat:mocks'
SS = '/app/.screenshots/ui223'; os.makedirs(SS, exist_ok=True)


async def chooser(page, target, label, touch):
    try:
        async with page.expect_file_chooser(timeout=3000) as fc:
            if touch: await page.locator(target).tap()
            else: await page.locator(target).click()
        say(f'{label}: file chooser opens', True); return await fc.value
    except Exception as e:
        say(f'{label}: file chooser opens', False, repr(e)[:200]); return None


async def walk(pw, size):
    br, page, bad, logs = await open_as(pw, 'owner', size); touch = size == 'mob'
    try:
        await page.goto(BASE + TYPE); await page.wait_for_selector('[data-testid=type-upload-pdf]', timeout=20000)
        t = time.time(); await page.click('[data-testid=type-upload-pdf]'); await page.wait_for_selector('[data-testid=upload-dialog]')
        say(f'{size}: dialog opens fast', time.time() - t < 2, round(time.time() - t, 2))
        await page.wait_for_timeout(600); await page.screenshot(path=f'{SS}/{size}_dialog.png')
        for target, label in (('[data-testid=upload-main] label', 'box text'),):
            await chooser(page, target, f'{size} {label}', touch)
        if await page.locator('[data-testid=upload-main-pick]').count():
            fc = await chooser(page, '[data-testid=upload-main-pick]', f'{size} Select button', touch)
        else:
            say(f'{size}: a visible Select button exists', False, 'no upload-main-pick'); fc = None
        if fc is None:
            await page.set_input_files('[data-testid=upload-main-input]', PDF)
        else:
            await fc.set_files(PDF)
        await page.wait_for_selector('[data-testid=upload-main].has-file', timeout=5000)
        say(f'{size}: picked PDF shows its name', 'two_mocks' in await page.inner_text('[data-testid=upload-main]'))
        await page.check('[data-testid=upload-rights]')
        t = time.time(); await page.click('[data-testid=upload-send]')
        await page.wait_for_selector('[data-testid=upload-dialog]', state='detached', timeout=60000)
        say(f'{size}: upload finishes and dialog closes', True, round(time.time() - t, 2)); print(f'   upload took {time.time() - t:.2f}s')
        await page.screenshot(path=f'{SS}/{size}_after.png')
        say(f'{size}: no API errors', not [b for b in bad if b[0] >= 500], bad[:6]); print('   console', logs[:4])
    except Exception as e:
        say(f'{size}: walk', False, repr(e)[:300]); await page.screenshot(path=f'{SS}/{size}_error.png')
    finally:
        await br.close()


async def main():
    async with async_playwright() as pw:
        for size in ('desk', 'mob'):
            await walk(pw, size)
    f = [n for n, ok in RESULT if not ok]
    print(f'TOTAL {len(RESULT)} PASS {len(RESULT) - len(f)} FAIL {len(f)}'); [print('  FAILED', n) for n in f]

if __name__ == '__main__':
    asyncio.run(main())
