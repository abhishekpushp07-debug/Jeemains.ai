"""TEST-ONLY iteration 224 smoke: Super Admin shows a PDF waiting for Supabase (Supabase %, wait note, badge, machine panel),
with /api routed to tests/storage_wait_bridge224.py (127.0.0.1:8774, cookies in /tmp/uibridge224/bridge.json).
Run: BRIDGE_OUT=/tmp/uibridge224 BRIDGE_PORT=8774 python tests/ui_storage_wait224.py
"""
import asyncio, json, os, sys
from pathlib import Path
os.environ.setdefault('BRIDGE_OUT', '/tmp/uibridge224'); os.environ.setdefault('BRIDGE_PORT', '8774')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.async_api import async_playwright  # noqa: E402
from ui_cut210 import open_as, BASE, say, RESULT  # noqa: E402

INFO = json.load(open('/tmp/uibridge224/bridge.json'))
SS = '/app/.screenshots/ui224'; os.makedirs(SS, exist_ok=True)


async def walk(pw, size):
    br, page, bad, logs = await open_as(pw, 'owner', size)
    bid = INFO['book']
    try:
        await page.goto(BASE + INFO['type']); await page.wait_for_selector(f'[data-testid=type-upload-{bid}]', timeout=25000)
        wait = page.locator(f'[data-testid=type-upload-wait-{bid}]')
        say(f'{size}: wait note shown', await wait.is_visible(), '')
        txt = await page.locator(f'[data-testid=type-upload-transfer-{bid}]').inner_text()
        say(f'{size}: Supabase % shown', 'Supabase' in txt and '%' in txt, txt)
        await page.locator(f'[data-testid=type-upload-{bid}]').scroll_into_view_if_needed()
        await page.screenshot(path=f'{SS}/{size}_type.png')
        await page.click('[data-testid=storage-badge]'); await page.wait_for_selector('[data-testid=storage-details]')
        await page.wait_for_timeout(800)
        label = await page.locator('[data-testid=storage-badge-label]').inner_text()
        say(f'{size}: badge says waiting', 'intezaar' in label, label)
        say(f'{size}: machine lists waiting book', await page.locator(f'[data-testid=machine-waiting-{bid}]').count() == 1, '')
        await page.screenshot(path=f'{SS}/{size}_badge.png')
    finally:
        say(f'{size}: no page errors', not bad, bad[:3])
        await br.close()


async def main():
    async with async_playwright() as pw:
        for size in ('desk', 'mob'):
            await walk(pw, size)
    ok = sum(1 for r in RESULT if (r[0] if isinstance(r, tuple) else r))
    print('TOTAL', len(RESULT), 'PASS', ok, 'FAIL', len(RESULT) - ok)

asyncio.run(main())
