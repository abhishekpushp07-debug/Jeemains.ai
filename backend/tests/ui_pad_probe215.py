"""TEST-ONLY probe (iteration 215): every box between the phone screen edge and the question picture (padding, margin, border). Bridge :8772."""
import asyncio, os, sys, json, importlib.util
sys.argv = [sys.argv[0]]
spec = importlib.util.spec_from_file_location('v211', os.path.join(os.path.dirname(__file__), 'ui_verify211_lib.py'))
v = importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
from playwright.async_api import async_playwright

CHAIN = """(sel) => {
  const img = document.querySelector(sel); if (!img) return 'none';
  const out = []; let e = img;
  while (e && e !== document.body) { const s = getComputedStyle(e), b = e.getBoundingClientRect();
    out.push([e.tagName + '.' + String(e.className).split(' ').slice(0, 2).join('.'), Math.round(b.left), Math.round(b.width), s.paddingLeft, s.paddingRight, s.marginLeft, s.borderLeftWidth]); e = e.parentElement; }
  return out;
}"""


async def main():
    async with async_playwright() as pw:
        br, page, bad, logs = await v.open_as(pw, 'student', 'mob')
        await page.goto(f"{v.BASE}/attempts/{v.F['active_attempt']}")
        try:
            await page.wait_for_selector('[data-testid="get-ready-begin"]', timeout=8000); await page.wait_for_timeout(3000)
            await page.click('[data-testid="get-ready-begin"]')
        except Exception:
            pass
        await page.wait_for_selector('[data-testid="player-piece-stem"] .piece-img', timeout=30000)
        for row in await page.evaluate(CHAIN, '[data-testid="player-piece-stem"] .piece-img'):
            print('player', row)
        for row in (await page.evaluate(CHAIN, '[data-testid="player-option-card-A"] .piece-img'))[:4]:
            print('player-opt', row)
        await page.goto(f"{v.BASE}/results/{v.F['done_attempt']}?view=solutions")
        await page.wait_for_selector('[data-testid^="review-piece-stem-"] .piece-img', timeout=30000)
        for row in await page.evaluate(CHAIN, '[data-testid^="review-piece-stem-"] .piece-img'):
            print('results', row)
        await page.screenshot(path='/app/.screenshots/zoom215_results_mob.jpg', quality=40)
        print('errors', bad[:3], logs[:3])
        await br.close()

asyncio.run(main())
