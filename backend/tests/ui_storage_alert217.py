"""TEST-ONLY (iteration 217): Storage alert on /super-admin with faked /api/admin/storage/health. Run: python tests/ui_storage_alert217.py"""
import asyncio, json, time, sys
sys.path.insert(0, '/app/backend/tests')
from playwright.async_api import async_playwright
from ui_master217_lib import open_as, ok, R, BASE, SS


def fake(alert):
    n = time.time()
    return {'data': {'mode': 'emergent', 'checked_at': n, 'supabase': {'ok': False, 'configured': True, 'error': 'Supabase file unavailable (503)', 'bucket': 'b'},
                     'emergent': {'ok': True, 'write_ms': 100, 'read_ms': 50}, 'writes': {'supabase': 3, 'emergent': 5}, 'failovers': 5,
                     'last_failover': {'at': n - 700, 'reason': '503'}, 'backup': {'since': n - 900, 'writes': 5, 'alert': alert}}, 'error': None, 'meta': {'api_version': '1'}}


async def run(pw, mode, w, h):
    state = {'mode': mode}

    async def extra(route, req):
        if state['mode'] in ('on', 'off') and req.url.split('?')[0].endswith('/api/admin/storage/health'):
            await route.fulfill(status=200, content_type='application/json', body=json.dumps(fake(state['mode'] == 'on')))
            return True
        return False
    br, page, bad, logs = await open_as(pw, 'owner', w, h, extra)
    tag = f'{mode}-{w}'
    try:
        await page.goto(BASE + '/super-admin'); await page.wait_for_selector('[data-testid="storage-badge"]', timeout=30000)
        await page.wait_for_timeout(2500)
        vis = await page.is_visible('[data-testid="storage-alert"]')
        if mode == 'on':
            ok(f'{tag}: alert shown', vis)
            if vis:
                t = await page.text_content('[data-testid="storage-alert-title"]'); x = await page.text_content('[data-testid="storage-alert-text"]')
                print(tag, 'TITLE', t, '| TEXT', x)
                ok(f'{tag}: alert title/text non-empty', t and x)
                bx = await page.locator('[data-testid="storage-alert"]').bounding_box()
                ok(f'{tag}: alert fits viewport', bx['x'] >= 0 and bx['x'] + bx['width'] <= w + 1, bx)
            print(tag, 'badge:', await page.text_content('[data-testid="storage-badge"]'))
        else:
            ok(f'{tag}: alert NOT shown', not vis)
        sw = await page.evaluate('document.documentElement.scrollWidth')
        ok(f'{tag}: no horizontal overflow', sw <= w + 1, sw)
        await page.screenshot(path=f'{SS}/storage-{tag}.jpg', quality=40)
        ok(f'{tag}: no page errors', not logs, logs)
        print(tag, 'bad responses', bad[:5])
    finally:
        await br.close()


async def main():
    async with async_playwright() as pw:
        await run(pw, 'on', 1920, 900); await run(pw, 'off', 1920, 900); await run(pw, 'real', 1920, 900); await run(pw, 'on', 390, 844)
    print('TOTAL', len(R), 'PASS', sum(1 for _, x in R if x), 'FAIL', sum(1 for _, x in R if not x))

asyncio.run(main())
