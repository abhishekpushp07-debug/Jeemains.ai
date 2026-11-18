"""TEST-ONLY follow-up probes (solutions filters per subject, downloads, personal-mode compare column)."""
import asyncio, sys
sys.argv = [sys.argv[0], 'none']
import ui_analysis2_t1 as T
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as pw:
        br, page, errors = await T.setup(pw, 1920, 800)
        await page.goto(f"{T.BASE}/results/{T.B['hero_attempt']}?view=solutions")
        await page.wait_for_selector('[data-testid="solution-subject-tabs"]', timeout=30000)
        await page.wait_for_timeout(1500)
        subs = await page.evaluate("() => [...document.querySelectorAll('[data-testid^=solution-subject-]')].map(e=>e.dataset.testid).filter(x=>!x.includes('count')&&!x.includes('tabs')&&!x.includes('question'))")
        print('SUBJECT TABS', subs)
        for k in ['careless', 'overtime', 'confused']:
            await page.click(f'[data-testid="results-filter-{k}"]')
            await page.wait_for_timeout(400)
            for s in subs:
                await page.click(f'[data-testid="{s}"]')
                await page.wait_for_timeout(400)
                print(k, s, '| label:', await T.text(page, 'solution-current-question-label'), '| count:', await T.text(page, 'solution-navigation-count'),
                      '| rail:', await page.locator('[data-testid="solution-question-rail"] button').count())
        print('INSIGHT', await T.text(page, 'solution-insight-line'))
        # downloads
        await T.go(page, 'hero', '?a=overview')
        async with page.expect_download(timeout=60000) as d:
            await page.click('[data-testid="a2-download-report"]')
        p = await (await d.value).path()
        head = open(p, 'rb').read(8)
        T.check('report download is PDF', head[:5] == b'%PDF-', head)
        print('pdf name', (await d.value).suggested_filename)
        async with page.expect_download(timeout=60000) as d:
            await page.click('[data-testid="a2-share-scorecard"]')
        p = await (await d.value).path()
        head = open(p, 'rb').read(8)
        T.check('share scorecard downloads PNG', head[:4] == b'\x89PNG', head)
        print('png name', (await d.value).suggested_filename)
        # personal mode qs columns, fresh context
        await T.go(page, 'hero', '?a=qs&mode=personal')
        await page.wait_for_timeout(800)
        print('URL', page.url)
        print('PERSONAL HEADS', await page.locator('[data-testid="a2-qs-table"] thead th').all_inner_texts())
        await T.go(page, 'hero', '?a=qs&mode=compare')
        await page.wait_for_timeout(1500)
        await page.click('[data-testid="a2-mode-personal"]')
        await page.wait_for_timeout(1500)
        print('URL after personal', page.url)
        print('HEADS after switching to personal', await page.locator('[data-testid="a2-qs-table"] thead th').all_inner_texts())
        print('ERRORS', errors[:10])
        await br.close()

asyncio.run(main())
