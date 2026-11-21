"""TEST-ONLY (iteration 217): Misfire empty states with faked API replies (bridge 8773). Run: python tests/ui_misfire_empty217.py"""
import asyncio, json, sys
sys.path.insert(0, '/app/backend/tests')
from playwright.async_api import async_playwright
import ui_student217_lib as L


async def fake(ctx, path, body):
    async def h(route):
        if route.request.url.split('?')[0].endswith(path):
            await route.fulfill(status=200, content_type='application/json', body=json.dumps({'data': body, 'error': None, 'meta': {'api_version': '1'}}))
        else:
            await route.fallback()
    await ctx.route('**/api/**', h)


async def main():
    async with async_playwright() as pw:
        br, ctx, page, bad, logs = await L.open_as(pw, 'hero', False)
        try:
            await fake(ctx, '/api/my/chapters', {'papers': 0, 'waiting': 0, 'chapters': [], 'subjects': [], 'untagged': 0})
            await page.goto(L.BASE + '/misfire'); await page.wait_for_selector('[data-testid="misfire-page"]', timeout=30000)
            await page.click('[data-testid="misfire-tab-chapters"]'); await page.wait_for_timeout(2000)
            L.ok('chapter report empty state', await page.is_visible('[data-testid="chapter-report-empty"]'), (await page.text_content('[data-testid="misfire-page"]'))[-300:])
            print('empty text', (await page.text_content('[data-testid="misfire-page"]'))[-300:])
        finally:
            await br.close()
        br, ctx, page, bad, logs = await L.open_as(pw, 'hero', False)
        try:
            await fake(ctx, '/api/my/chapters', {'papers': 2, 'waiting': 0, 'chapters': [], 'untagged': 60,
                                                  'subjects': [{'subject': 'Physics', 'chapter': '', 'papers': 2, 'total': 20, 'correct': 10, 'wrong': 5, 'skipped': 5, 'lost': 40, 'sahi': 50, 'accuracy': 66, 'trend': 'up'}]})
            await page.goto(L.BASE + '/misfire'); await page.wait_for_selector('[data-testid="misfire-page"]', timeout=30000)
            await page.click('[data-testid="misfire-tab-chapters"]'); await page.wait_for_timeout(2000)
            L.ok('no-chapters note shown', await page.is_visible('[data-testid="chapter-report-no-chapters"]'), (await page.text_content('[data-testid="misfire-page"]'))[-300:])
            L.ok('subject card still shown with Behtar', 'Behtar' in (await page.text_content('[data-testid="chapter-subject-physics"]') or ''))
            print('no-chapters text', (await page.text_content('[data-testid="misfire-page"]'))[-300:])
        finally:
            await br.close()
        br, ctx, page, bad, logs = await L.open_as(pw, 'hero', False)
        try:
            await fake(ctx, '/api/my/misfire/summary', {'open': 0, 'fixed': 0, 'subjects': [], 'waiting': 0})
            await fake(ctx, '/api/my/misfire', {'items': [], 'total': 0, 'page': 1, 'pages': 1, 'waiting': 0, 'chapters': []})
            await page.goto(L.BASE + '/home'); await page.wait_for_selector('[data-testid="home-for-you"]', timeout=30000); await page.wait_for_timeout(1500)
            vis = await page.is_visible('[data-testid="home-misfire-card"]')
            print('home card with 0 open visible?', vis, (await page.text_content('[data-testid="home-misfire-card"]')) if vis else '')
            await page.goto(L.BASE + '/misfire'); await page.wait_for_timeout(2500)
            L.ok('misfire empty state', await page.is_visible('[data-testid="misfire-empty"]'))
            print('empty list text', await page.text_content('[data-testid="misfire-empty"]') if await page.is_visible('[data-testid="misfire-empty"]') else '')
            L.ok('no page errors', not logs, logs)
        finally:
            await br.close()
    print('TOTAL', len(L.R), 'PASS', sum(1 for _, x in L.R if x), 'FAIL', sum(1 for _, x in L.R if not x))

asyncio.run(main())
