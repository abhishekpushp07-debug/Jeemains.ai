"""TEST-ONLY iteration 231 smoke (Pocket 2): Super Admin shows "Atki hai" with the reason on the stuck upload, its mock and the machine panel,
the 15-minute alert in the upload's own row, and Dobara chalao finishes the mock once Supabase takes the picture.
/api is routed to tests/storage_stuck_bridge231.py (127.0.0.1:8775, cookies in /tmp/uibridge231/bridge.json).
Run: cd /app/backend && python tests/ui_storage_stuck231.py [desk|mob] [fix]     ("fix" empties returned.txt and presses Dobara chalao: once per bridge)
"""
import asyncio, json, os, sys
from pathlib import Path
os.environ.setdefault('BRIDGE_OUT', '/tmp/uibridge231'); os.environ.setdefault('BRIDGE_PORT', '8775')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.async_api import async_playwright  # noqa: E402
from ui_cut210 import open_as, overflow, BASE, say, RESULT  # noqa: E402

D = '/tmp/uibridge231/'
INFO = json.load(open(D + 'bridge.json'))
SS = '/app/.screenshots/ui231'; os.makedirs(SS, exist_ok=True)
PIC, MID, BIG, ONE, TWO = INFO['pic']['book'], INFO['pic']['mock'], INFO['big'], INFO['file'], INFO['blocked']


async def walk(pw, size, fix):
    br, page, bad, _ = await open_as(pw, 'owner', size)
    asked = []
    page.on('request', lambda r: asked.append(1) if '/api/admin/machine/status' in r.url else None)
    at = lambda t: page.locator(f'[data-testid={t}]')  # noqa: E731
    try:
        await page.goto(BASE + INFO['type']); await page.wait_for_selector(f'[data-testid=type-upload-{PIC}]', timeout=25000)
        note = await at(f'type-upload-wait-{PIC}').inner_text()
        say(f'{size}: picture row chip says Atki hai', (await at(f'type-upload-state-{PIC}').inner_text()).strip() == 'Atki hai', await at(f'type-upload-state-{PIC}').inner_text())
        say(f'{size}: picture row: Atki hai, the mock\'s name, the code and the 15-minute retry', await at(f'type-upload-wait-{PIC}').get_attribute('data-kind') == 'stuck' and 'Atki hai' in note
            and INFO['pic']['label'] in note and '(400)' in note and '15 minute' in note, note)
        alert = await at(f'type-upload-alert-{PIC}').inner_text() if await at(f'type-upload-alert-{PIC}').count() else ''
        say(f'{size}: 15-minute alert inside the upload row', 'minute se' in alert and 'Supabase mein nahi gayi' in alert, alert)
        say(f'{size}: stuck row offers Dobara chalao, not "Abhi phir try karo"', await at(f'type-upload-retry-{PIC}').is_visible() and not await at(f'type-upload-wait-retry-{PIC}').count())
        note = await at(f'type-upload-wait-{BIG}').inner_text()
        say(f'{size}: big PDF row: Atki hai with the code, no alert before 15 minutes', 'Atki hai' in note and 'Yeh PDF' in note and '(400)' in note and not await at(f'type-upload-alert-{BIG}').count(), note)
        note = await at(f'type-upload-wait-{ONE}').inner_text()
        say(f'{size}: "this file only" row says the machine retries, with the code', 'abhi Supabase mein nahi gayi' in note and '(423)' in note and await at(f'type-upload-wait-retry-{ONE}').is_visible(), note)
        note = await at(f'type-upload-wait-{TWO}').inner_text()
        say(f'{size}: blocked row says the project is blocked and where to look', 'Supabase project par rok' in note and '(402)' in note and 'Billing' in note, note)
        say(f'{size}: the stuck mock\'s row says Atki hai with the reason', 'Atki hai' in await at(f'mock-status-{MID}').inner_text() and (await at(f'mock-live-word-{MID}').inner_text()).strip() == 'Atki hai'
            and '(400)' in await at(f'mock-stuck-{MID}').inner_text(), await at(f'mock-status-{MID}').inner_text())
        words = [w.strip() for w in await page.locator('[data-testid^=mock-live-word-]').all_inner_texts()]
        say(f'{size}: the other mock is Live', words.count('Live') == 1, words)
        if size == 'mob':
            await overflow(page, size + ' type page')
        await at(f'type-upload-{PIC}').scroll_into_view_if_needed()
        await page.screenshot(path=f'{SS}/{size}_type.jpg', quality=40, type='jpeg')
        say(f'{size}: five waiting rows ask the machine once together, not once each', len(asked) <= 4, len(asked))
        await page.click('[data-testid=storage-badge]'); await page.wait_for_selector('[data-testid=machine-panel]', timeout=10000); await page.wait_for_timeout(800)
        say(f'{size}: machine panel counts 2 stuck files and lists both with Dobara chalao', (await at('machine-storage-stuck-value').inner_text()).strip() == '2'
            and await at(f'machine-storage-stuck-{PIC}').count() == 1 and await at(f'machine-storage-stuck-{BIG}').count() == 1 and await at(f'machine-retry-{PIC}').count() == 1,
            await at('machine-storage-stuck-value').inner_text())
        say(f'{size}: machine panel gives the reason', '(400)' in await at(f'machine-storage-stuck-{PIC}').inner_text(), await at(f'machine-storage-stuck-{PIC}').inner_text())
        await at('machine-storage-stuck-list').scroll_into_view_if_needed()
        await page.screenshot(path=f'{SS}/{size}_machine.jpg', quality=40, type='jpeg')
        if fix:
            await page.keyboard.press('Escape'); Path(D + 'returned.txt').write_text('')
            await at(f'type-upload-retry-{PIC}').click()
            done = False
            for _ in range(40):
                await page.wait_for_timeout(1000)
                words = [w.strip() for w in await page.locator('[data-testid^=mock-live-word-]').all_inner_texts()]
                if words.count('Live') == 2 and not await at(f'type-upload-wait-{PIC}').count():
                    done = True; break
            say(f'{size}: Dobara chalao after Supabase takes the picture: the mock is Live, the stuck note is gone, no page reload', done and not await page.locator('[data-testid^=mock-stuck-]').count(), words)
            await page.screenshot(path=f'{SS}/{size}_fixed.jpg', quality=40, type='jpeg')
    finally:
        say(f'{size}: no failed API calls', not [b for b in bad if '/dream' not in b[1]], bad[:4])
        await br.close()


async def main():
    sizes = [s for s in ('desk', 'mob') if s in sys.argv] or ['desk', 'mob']
    async with async_playwright() as pw:
        for i, size in enumerate(sizes):
            await walk(pw, size, 'fix' in sys.argv and i == len(sizes) - 1)
    ok = sum(1 for r in RESULT if r[1])
    print('TOTAL', len(RESULT), 'PASS', ok, 'FAIL', len(RESULT) - ok)

asyncio.run(main())
