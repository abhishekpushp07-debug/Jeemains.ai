"""TEST-ONLY probe 2: personal-mode stale compare column + compare payload privacy."""
import asyncio, sys, json, requests
sys.argv = [sys.argv[0], 'none']
import ui_analysis2_t1 as T
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as pw:
        br, page, errors = await T.setup(pw, 1920, 800)
        await T.go(page, 'hero', '?a=time&mode=compare')
        await page.wait_for_selector('[data-testid="a2-compare-picker"]', timeout=15000)
        await page.click('[data-testid="a2-mode-personal"]')
        print('URL1', page.url)
        for k in ['difficulty', 'journey', 'qs']:
            await page.click(f'[data-testid="a2-nav-{k}"]')
            await page.wait_for_timeout(600)
        print('URL2', page.url)
        print('HEADS', await page.locator('[data-testid="a2-qs-table"] thead th').all_inner_texts())
        print('compare picker visible in personal?', await page.locator('[data-testid="a2-compare-picker"]').count())
        await page.wait_for_timeout(3000)
        print('HEADS after 3s', await page.locator('[data-testid="a2-qs-table"] thead th').all_inner_texts())
        await br.close()
    B = T.B
    for vs in ['topper', 'average']:
        d = requests.get(f"http://127.0.0.1:8773/api/attempts/{B['hero_attempt']}/analysis?mode=comparative&compare={vs}", cookies=B['hero']).json()['data']
        c = d['compare']
        print(vs, 'compare keys', list(c.keys()))
        times = c.get('times') or {}
        print(vs, 'zero times', sum(1 for v in times.values() if not v), 'of', len(times))
        blob = json.dumps(c)
        print(vs, 'contains response/answer keys?', any(x in blob for x in ['"response"', '"answer"', '"responses"', '"answers"']))

asyncio.run(main())
