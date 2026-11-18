"""TEST-ONLY iteration 196 Analysis 2.0 screenshots via local Playwright: public preview frontend, /api routed to the isolated
bridge (tests/analysis_bridge196.py). Opens the hero's analysis, every section in Personal and Comparative mode, at 1920 and 390.
Run: PLAYWRIGHT_BROWSERS_PATH=/pw-browsers python tests/ui196.py [sections comma list] [who=hero|old]
"""
import asyncio, json, os, sys
from playwright.async_api import async_playwright

OUT = os.environ.get('BRIDGE_OUT', '/tmp/uibridge196')
B = json.load(open(OUT + '/bridge.json'))
BASE = [line.split('=', 1)[1].strip() for line in open('/app/frontend/.env') if line.startswith('REACT_APP_BACKEND_URL')][0].rstrip('/')
API = 'http://127.0.0.1:' + os.environ.get('BRIDGE_PORT', '8773')
SS = '/app/.screenshots/ui196'
os.makedirs(SS, exist_ok=True)
ALL = ['overview', 'performance', 'potential', 'quality', 'time', 'difficulty', 'journey', 'qs']
PICK = sys.argv[1].split(',') if len(sys.argv) > 1 and sys.argv[1] else ALL
WHO = sys.argv[2] if len(sys.argv) > 2 else 'hero'
MODES = os.environ.get('MODES', 'personal').split(',')
SIZES = [tuple(map(int, s.split('x'))) for s in os.environ.get('SIZES', '1920x800,390x844').split(',')]


async def shoot(pw, w, h):
    br = await pw.chromium.launch()
    ctx = await br.new_context(viewport={'width': w, 'height': h})
    cookie = '; '.join(f'{k}={v}' for k, v in B[WHO].items())
    errors = []

    async def handler(route):
        req = route.request
        hd = {k: v for k, v in req.headers.items() if k.lower() not in ('host', 'referer', 'cookie')}
        hd['origin'] = BASE
        hd['cookie'] = cookie
        try:
            r = await route.fetch(url=req.url.replace(BASE, API), headers=hd)
            await route.fulfill(response=r)
        except Exception as e:
            print('route err', e)
            await route.abort()
    page = await ctx.new_page()
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('console', lambda m: m.type == 'error' and errors.append(m.text[:200]))
    await page.route('**/api/**', handler)
    aid = B[WHO + '_attempt']
    for mode in MODES:
        for s in PICK:
            url = f'{BASE}/results/{aid}?a={s}' + ('&mode=compare' if mode == 'compare' else '')
            await page.goto(url)
            try:
                await page.wait_for_selector(f'[data-testid="a2-section-{s}"]', timeout=25000)
            except Exception:
                print('NOT FOUND', s, mode)
            await page.wait_for_timeout(1800)
            el = page.locator('[data-testid="analysis2"]')
            await el.scroll_into_view_if_needed()
            vw = await page.evaluate('document.documentElement.clientWidth')
            off = await page.evaluate("() => [...document.querySelectorAll('[data-testid=analysis2] *')].filter(e => e.getBoundingClientRect().right > innerWidth + 1 && !e.closest('.a2-scroll,.a2-nav,.a2-pills,.a2-qgrid-wrap')).slice(0,5).map(e => (e.className && e.className.baseVal === undefined ? e.className : e.tagName))")
            print(w, mode, s, 'VIEWPORT', vw, 'OVERFLOW', off, flush=True)
            await el.screenshot(path=f'{SS}/{w}_{mode}_{s}.jpg', quality=35)
    print('ERRORS', errors[:8])
    await br.close()


async def main():
    async with async_playwright() as pw:
        for w, h in SIZES:
            await shoot(pw, w, h)

asyncio.run(main())
