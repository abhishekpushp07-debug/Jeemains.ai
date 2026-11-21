"""TEST-ONLY: montage of the top strip of each worked solution picture on Results (iteration 212), for visual Q-number/Source match."""
import asyncio, os, sys, importlib.util
from PIL import Image
sys.argv_s = sys.argv; sys.argv = [sys.argv[0]]
spec = importlib.util.spec_from_file_location('v211', os.path.join(os.path.dirname(__file__), 'ui_verify211_lib.py'))
v = importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
from playwright.async_api import async_playwright
SS = '/app/.screenshots/ui212'
size = sys.argv_s[1] if len(sys.argv_s) > 1 else 'desk'


async def main():
    async with async_playwright() as pw:
        br, page, bad, logs = await v.open_as(pw, 'student', size)
        await page.goto(f"{v.BASE}/results/{v.F['done_attempt']}?view=solutions")
        await page.wait_for_selector('[data-testid="solution-question-rail"]', timeout=30000)
        strips = []
        for n in range(1, 17):
            await page.click(f'[data-testid="solution-question-{n}"]'); await page.wait_for_timeout(1000)
            sec = page.locator(f'[data-testid="solution-content-{n}"] img').first
            await page.locator(f'[data-testid="solution-content-{n}"]').scroll_into_view_if_needed(); await page.wait_for_timeout(600)
            await page.wait_for_function("(n) => { const i = document.querySelector('[data-testid=\"solution-content-' + n + '\"] img'); return i && i.complete && i.naturalWidth > 0; }", arg=n, timeout=20000)
            await sec.evaluate("e => e.scrollIntoView({block: 'start'})"); await page.wait_for_timeout(300)
            await page.evaluate("window.scrollBy(0, -120)"); await page.wait_for_timeout(200)
            b = await sec.bounding_box()
            p = f'/tmp/strip_{size}_{n}.png'
            stem = page.locator('.piece-stem').first
            await page.screenshot(path=p, clip={'x': b['x'], 'y': b['y'], 'width': b['width'], 'height': min(70 if size == 'desk' else 40, b['height'])})
            strips.append(Image.open(p))
        w = max(s.width for s in strips); h = sum(s.height + 4 for s in strips)
        m = Image.new('RGB', (w, h), 'white'); y = 0
        for s in strips:
            m.paste(s, (0, y)); y += s.height + 4
        m.save(f'{SS}/sol_strips_{size}.jpg', quality=50)
        print('saved', len(strips), bad[:3], logs[:3])
        await br.close()

asyncio.run(main())
