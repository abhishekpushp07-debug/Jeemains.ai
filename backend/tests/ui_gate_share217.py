"""TEST-ONLY (iteration 217): mobile ShareGate opens result only after share (navigator.share stubbed). Run: python tests/ui_gate_share217.py"""
import asyncio, sys
sys.path.insert(0, '/app/backend/tests')
from playwright.async_api import async_playwright
import ui_student217_lib as L


async def main():
    async with async_playwright() as pw:
        br, ctx, page, bad, logs = await L.open_as(pw, 'hero', True)
        await ctx.add_init_script("navigator.share = async () => { window.__shared = (window.__shared||0)+1; }; navigator.canShare = () => true;")
        try:
            await page.goto(L.BASE + '/home'); await page.evaluate(f"localStorage.setItem('share_gate.{L.AID}','1')")
            await page.goto(f'{L.BASE}/results/{L.AID}'); await page.wait_for_selector('[data-testid="share-gate"]', timeout=30000)
            await page.wait_for_timeout(1500)
            await page.click('[data-testid="share-gate-share"]')
            try:
                await page.wait_for_selector('[data-testid="share-gate"]', state='detached', timeout=12000); opened = True
            except Exception:
                opened = False
            print('shared calls', await page.evaluate('window.__shared'), 'note', await page.is_visible('[data-testid="share-gate-note"]'))
            L.ok('mobile: result opens after share', opened, await page.text_content('[data-testid="share-gate"]') if not opened else '')
            L.ok('no page errors', not logs, logs)
        finally:
            await br.close()
    print('TOTAL', len(L.R), 'PASS', sum(1 for _, x in L.R if x), 'FAIL', sum(1 for _, x in L.R if not x))

asyncio.run(main())
