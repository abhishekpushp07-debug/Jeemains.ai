"""TEST-ONLY iteration 197 quick check: section nav + mode switch (functional URL updates) and Solutions filter jumping subjects.
Needs tests/analysis_bridge196.py running. Run: PLAYWRIGHT_BROWSERS_PATH=/pw-browsers python tests/ui197_check.py
"""
import asyncio, json, os
from playwright.async_api import async_playwright

B = json.load(open(os.environ.get('BRIDGE_OUT', '/tmp/uibridge196') + '/bridge.json'))
BASE = [line.split('=', 1)[1].strip() for line in open('/app/frontend/.env') if line.startswith('REACT_APP_BACKEND_URL')][0].rstrip('/')
API = 'http://127.0.0.1:' + os.environ.get('BRIDGE_PORT', '8773')


async def main():
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        page = await (await br.new_context(viewport={'width': 1920, 'height': 800})).new_page()
        cookie = '; '.join(f'{k}={v}' for k, v in B['hero'].items())
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))

        async def handler(route):
            hd = {k: v for k, v in route.request.headers.items() if k.lower() not in ('host', 'referer', 'cookie')}
            hd.update(origin=BASE, cookie=cookie)
            await route.fulfill(response=await route.fetch(url=route.request.url.replace(BASE, API), headers=hd))
        await page.route('**/api/**', handler)
        await page.goto(f"{BASE}/results/{B['hero_attempt']}?a=overview")
        await page.wait_for_selector('[data-testid="a2-section-overview"]', timeout=25000)
        await page.click('[data-testid="a2-nav-time"]')
        await page.wait_for_selector('[data-testid="a2-section-time"]')
        print('nav time', 'a=time' in page.url)
        await page.click('[data-testid="a2-mode-compare"]')
        await page.wait_for_selector('[data-testid="a2-compare"]', timeout=15000)
        print('compare on', 'mode=compare' in page.url)
        await page.click('[data-testid="a2-mode-personal"]')
        await page.click('[data-testid="a2-nav-qs"]')
        await page.wait_for_selector('[data-testid="a2-section-qs"]')
        await page.wait_for_timeout(800)
        print('fast personal then qs', 'a=qs' in page.url and 'mode=compare' not in page.url, page.url.split('?')[1])
        await page.click('[data-testid="a2-view-solutions"]')
        await page.wait_for_selector('[data-testid="results-filter-careless"]')
        await page.click('[data-testid="result-view-solutions"]')
        await page.click('[data-testid="solution-subject-chemistry"]')
        await page.wait_for_timeout(500)
        subjects = await page.locator('[data-testid="solution-current-question-label"]').inner_text()
        await page.click('[data-testid="results-filter-careless"]')
        await page.wait_for_timeout(800)
        label = await page.locator('[data-testid="solution-current-question-label"]').inner_text()
        print('careless filter lands on a question', subjects, '->', label, 'Choose another' not in label)
        print('ERRORS', errors)
        await br.close()

asyncio.run(main())
