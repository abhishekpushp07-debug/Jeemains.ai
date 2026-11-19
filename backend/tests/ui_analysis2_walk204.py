import asyncio, json, os, sys
from playwright.async_api import async_playwright
from PIL import Image
B = json.load(open('/tmp/uibridge196/bridge.json'))
BASE = [l.split('=', 1)[1].strip() for l in open('/app/frontend/.env') if l.startswith('REACT_APP_BACKEND_URL')][0].rstrip('/')
API = 'http://127.0.0.1:8773'
OUT = '/tmp/shots'
ALL = ['overview', 'performance', 'potential', 'quality', 'time', 'difficulty', 'journey', 'qs']
WANT = sys.argv[1:] or ['d', 'm', 'k']

async def setup(pw, w, h, theme='light', who='hero'):
    br = await pw.chromium.launch()
    ctx = await br.new_context(viewport={'width': w, 'height': h}, has_touch=(w < 500))
    await ctx.add_init_script("try{localStorage.setItem('jeelive-theme','%s')}catch(e){}" % theme)
    cookie = '; '.join(f'{k}={v}' for k, v in B[who].items())
    errors = []
    async def handler(route):
        req = route.request
        hd = {k: v for k, v in req.headers.items() if k.lower() not in ('host', 'referer', 'cookie')}
        hd['origin'] = BASE; hd['cookie'] = cookie
        try:
            r = await route.fetch(url=req.url.replace(BASE, API), headers=hd)
            if r.status >= 400: errors.append(f'API {r.status} {req.url[-80:]}')
            await route.fulfill(response=r)
        except Exception as e:
            await route.abort()
    page = await ctx.new_page()
    page.on('pageerror', lambda e: errors.append('PAGEERR ' + str(e)[:200]))
    page.on('console', lambda m: m.type == 'error' and errors.append('CONSOLE ' + m.text[:200]))
    await page.route('**/api/**', handler)
    return br, page, errors

async def go(page, q='', who='hero'):
    await page.goto(f"{BASE}/results/{B[who + '_attempt']}{q}")
    await page.wait_for_selector('[data-testid="analysis2"]', timeout=40000)
    await page.wait_for_timeout(1300)

OVER = "() => [...document.querySelectorAll('[data-testid=analysis2] *, [data-testid=result-solutions-panel] *')].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.right > innerWidth + 1 && !e.closest('.a2-scroll,.a2-nav,.a2-pills,.solution-question-rail,.recharts-wrapper'); }).slice(0,6).map(e => (e.getAttribute('data-testid') || (e.className && e.className.baseVal) || e.className || e.tagName))"

async def shot(page, tid, name, sel=None):
    loc = page.locator(sel or f'[data-testid="{tid}"]').first
    if not await loc.count():
        print('MISSING', tid or sel); return None
    path = f'{OUT}/{name}.jpg'
    await loc.scroll_into_view_if_needed()
    await page.wait_for_timeout(350)
    await loc.screenshot(path=path, type='jpeg', quality=45)
    return path

def sheet(name, paths, across=False, limit=1500):
    ims = [Image.open(p) for p in paths if p]
    out, cur, size = [], [], 0
    for im in ims:
        d = im.width if across else im.height
        if cur and size + d > limit: out.append(cur); cur, size = [], 0
        cur.append(im); size += d + 12
    if cur: out.append(cur)
    names = []
    for i, group in enumerate(out):
        if across:
            W, H = sum(x.width + 12 for x in group), max(x.height for x in group)
        else:
            W, H = max(x.width for x in group), sum(x.height + 12 for x in group)
        can = Image.new('RGB', (W, H), '#888888'); at = 0
        for x in group:
            can.paste(x, (at, 0) if across else (0, at)); at += (x.width if across else x.height) + 12
        p = f'{OUT}/{name}_{i + 1}.jpg'; can.save(p, quality=55); names.append((p, can.size))
    print('SHEET', names)

BLOCKS = {'overview': ['score', 'ledger', 'next3', 'standing', 'leaderboard', 'vs-class', 'grid', 'subjects', 'learnings'], 'performance': ['performance', 'weak'], 'potential': ['potential', 'potential-steps', 'potential-rank', 'potential-chapters', 'guess'],
          'quality': ['quality', 'speed-map', 'painful', 'lucky', 'quality-subjects'], 'time': ['time', 'time-subjects', 'time-journey', 'pace', 'first-look', 'last-stretch', 'slowest'],
          'difficulty': ['difficulty', 'tough-solved'], 'journey': ['journey', 'changes', 'journey-chips'], 'qs': ['qs-grid', 'qs']}

async def walk(pw, w, h, tag, theme='light', only=None):
    br, page, errors = await setup(pw, w, h, theme)
    for key in (only or ALL):
        await go(page, '?a=' + key)
        have = await page.evaluate("() => [...document.querySelectorAll('[data-testid^=a2-block-]')].map(e => e.getAttribute('data-testid').slice(9))")
        print(f'[{tag}] {key}: blocks={have} overflow={await page.evaluate(OVER)} docW={await page.evaluate("document.documentElement.scrollWidth")}')
        paths = []
        if key == 'difficulty': paths.append(await shot(page, 'a2-leak', f'{tag}_{key}_leak'))
        for b in BLOCKS[key]:
            if b in have: paths.append(await shot(page, 'a2-block-' + b, f'{tag}_{key}_{b}'))
        sheet(f'S_{tag}_{key}', paths, across=(w < 500), limit=1560 if w < 500 else 1500)
    # (i) popover
    await go(page, '?a=overview')
    await page.locator('[data-testid="a2-info-rank"]').click()
    await page.wait_for_timeout(500)
    print(f'[{tag}] popover visible', await page.locator('[data-testid="a2-info-pop-rank"]').is_visible())
    await page.evaluate("window.scrollTo(0, Math.max(0, document.querySelector('[data-testid=a2-info-pop-rank]').getBoundingClientRect().top + scrollY - 300))")
    await page.wait_for_timeout(300)
    await page.screenshot(path=f'{OUT}/V_{tag}_popover.jpg', type='jpeg', quality=40)
    await page.keyboard.press('Escape')
    # bottom bar + top bar in the viewport
    await page.evaluate("window.scrollTo(0, 500)"); await page.wait_for_timeout(300)
    await page.screenshot(path=f'{OUT}/V_{tag}_bar.jpg', type='jpeg', quality=40)
    # solutions: Q11 (two visits, changed answer)
    await page.locator('[data-testid="a2-qgrid-q-11"]').first.click()
    await page.wait_for_selector('[data-testid="solution-insight"]', timeout=15000)
    await page.wait_for_timeout(900)
    print(f'[{tag}] solutions overflow={await page.evaluate(OVER)} docW={await page.evaluate("document.documentElement.scrollWidth")}')
    p1 = await shot(page, 'solution-insight', f'{tag}_sol_insight')
    p2 = await shot(page, None, f'{tag}_sol_nav', '.solution-number-panel, [data-testid="solution-question-rail"]')
    p3 = await shot(page, 'solution-navigation-legend', f'{tag}_sol_legend')
    sheet(f'S_{tag}_solutions', [p2, p3, p1], across=False, limit=2200)
    # compare
    await go(page, '?a=overview&mode=compare&vs=topper')
    have = await page.evaluate("() => [...document.querySelectorAll('[data-testid^=a2-block-compare]')].map(e => e.getAttribute('data-testid').slice(9))")
    print(f'[{tag}] compare overview: {have} overflow={await page.evaluate(OVER)}')
    paths = [await shot(page, 'a2-compare-picker', f'{tag}_cmp_picker')] + [await shot(page, 'a2-block-' + b, f'{tag}_cmp_{b}') for b in have]
    sheet(f'S_{tag}_compare', paths, across=(w < 500))
    for key in ALL[1:]:
        await go(page, f'?a={key}&mode=compare&vs=top10')
        print(f'[{tag}] compare {key}: overflow={await page.evaluate(OVER)} docW={await page.evaluate("document.documentElement.scrollWidth")}')
    print(f'[{tag}] ERRORS', errors[:12])
    await br.close()

async def main():
    async with async_playwright() as pw:
        if 'd' in WANT: await walk(pw, 1920, 800, 'd')
        if 'm' in WANT: await walk(pw, 390, 844, 'm')
        if 'k' in WANT: await walk(pw, 1920, 800, 'k', 'dark', ['overview', 'quality', 'journey'])
        if 'km' in WANT: await walk(pw, 390, 844, 'km', 'dark', ['overview', 'qs'])
if __name__ == '__main__':
    asyncio.run(main())
