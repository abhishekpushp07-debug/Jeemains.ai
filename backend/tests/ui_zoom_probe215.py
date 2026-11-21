"""TEST-ONLY probe (iteration 215): how wide the question and option pictures are on a phone. Routes /api to bridge :8772."""
import asyncio, os, sys, json, importlib.util
sys.argv = [sys.argv[0]] + sys.argv[1:]
want = sys.argv[1:] or ['mob']
sys.argv = [sys.argv[0]]
spec = importlib.util.spec_from_file_location('v211', os.path.join(os.path.dirname(__file__), 'ui_verify211_lib.py'))
v = importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
from playwright.async_api import async_playwright

PROBE = """() => {
  const r = e => { if (!e) return null; const b = e.getBoundingClientRect(); return [Math.round(b.left), Math.round(b.width)]; };
  const stem = document.querySelector('[data-testid="player-piece-stem"]');
  const opts = [...document.querySelectorAll('[data-testid^="player-option-card-"]')];
  return {vw: innerWidth, main: r(document.querySelector('.question-card')), stemPaper: r(stem && stem.querySelector('.piece-paper')), stemFit: r(stem && stem.querySelector('.piece-fit')),
    stemImgs: stem ? [...stem.querySelectorAll('.piece-img')].map(i => [Math.round(i.getBoundingClientRect().width), i.naturalWidth || 0]) : [],
    opts: opts.map(o => ({card: r(o), fit: r(o.querySelector('.piece-fit')), img: r(o.querySelector('.piece-img'))})),
    font: getComputedStyle(document.body).fontSize};
}"""


async def main():
    async with async_playwright() as pw:
        for size in want:
            br, page, bad, logs = await v.open_as(pw, 'student', size)
            await page.goto(f"{v.BASE}/attempts/{v.F['active_attempt']}")
            try:
                await page.wait_for_selector('[data-testid="get-ready-begin"]', timeout=8000); await page.wait_for_timeout(3000)
                await page.click('[data-testid="get-ready-begin"]')
            except Exception:
                pass
            await page.wait_for_selector('[data-testid="player-piece-stem"]', timeout=30000)
            for n in range(3):
                await v.wait_pics(page)
                print(size, 'q', n + 1, json.dumps(await page.evaluate(PROBE)))
                await page.screenshot(path=f'/app/.screenshots/zoom215_{size}_{n + 1}.jpg', quality=40)
                nx = page.locator('[data-testid="player-next"]')
                if not await nx.count() or await nx.is_disabled():
                    break
                await nx.click(); await page.wait_for_timeout(600)
            print('errors', bad[:3], logs[:3])
            await br.close()

asyncio.run(main())
