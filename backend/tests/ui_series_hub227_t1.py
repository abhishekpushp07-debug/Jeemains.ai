"""TEST-ONLY iteration 227 independent checks (testing agent) for the All India hub on the isolated bridge 8775.
Header/brand/no tabs, More links -> ?tab views, upcoming chip selection colours, map cell text, gloss frames,
guest pink card, map-cell tap -> analysis, dark mode look.
Run: BRIDGE_OUT=/tmp/uibridge227 BRIDGE_PORT=8775 python tests/ui_series_hub227_t1.py
"""
import asyncio, json, os, sys
from pathlib import Path
os.environ.setdefault('BRIDGE_OUT', '/tmp/uibridge227'); os.environ.setdefault('BRIDGE_PORT', '8775')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.async_api import async_playwright  # noqa: E402
from ui_cut210 import open_as, BASE, API, say, RESULT  # noqa: E402

INFO = json.load(open('/tmp/uibridge227/bridge.json'))
SS = '/app/.screenshots/ui227t1'; os.makedirs(SS, exist_ok=True)
A = INFO['attempts']
HUB = BASE + '/series/all-india-jee'


async def colours(page, sel):
    return await page.locator(sel).evaluate("e => { const s = getComputedStyle(e); return [s.backgroundImage.slice(0,80), s.backgroundColor, s.color]; }")


async def walk(pw, size):
    br, page, bad, logs = await open_as(pw, 'hero', size)
    try:
        await page.goto(HUB); await page.wait_for_selector('[data-testid=streak-journey]', timeout=30000)
        await page.wait_for_selector('[data-testid=series-chip-marks-1]', timeout=20000)
        hdr = [await page.locator(f'[data-testid={t}]').count() for t in ('series-back-home', 'series-hub-title', 'series-about', 'series-100ai-ribbon', 'series-astra-identity-hub')]
        say(f'{size}: header + brand present', hdr == [1] * 5, hdr)
        eyebrow = await page.locator('.sh-header-text span').first.inner_text()
        say(f'{size}: eyebrow text', '50 DAYS' in eyebrow.upper() and 'FULL SYLLABUS' in eyebrow.upper(), eyebrow)
        say(f'{size}: no tab bar on default hub', await page.locator('[role=tablist]').count() == 0, '')
        cups = [await page.locator(f'[data-testid=streak-cup-{d}]').count() for d in (7, 15, 30, 45, 50)]
        say(f'{size}: cups 7/15/30/45/50', cups == [1] * 5, cups)
        # map cell text for upcoming / missed days
        txt = {d: (await page.locator(f'[data-testid=series-calendar-day-{d}]').inner_text()).strip() for d in (4, 6, 7, 20)}
        print(f'{size}: map cell text', txt)
        say(f'{size}: upcoming map cell 7 shows a day number', txt[7] == '7', txt)
        # gloss frames of the pink card
        card = page.locator('[data-testid=streak-journey]')
        await card.scroll_into_view_if_needed()
        for i in range(6):
            await card.screenshot(path=f'{SS}/{size}_gloss_{i}.png'); await page.wait_for_timeout(850)
        # upcoming chip selection
        await page.locator('[data-testid=series-chip-8]').scroll_into_view_if_needed()
        await page.click('[data-testid=series-chip-8]'); await page.wait_for_timeout(600)
        say(f'{size}: upcoming chip 8 stays on hub', page.url.endswith('/series/all-india-jee'), page.url)
        sel_card = page.locator('[data-testid=series-day-card-8]')
        if await sel_card.count():
            print(f'{size}: day card 8 colours', await colours(page, '[data-testid=series-day-card-8]'), await sel_card.get_attribute('class'))
        print(f'{size}: chip 8 colours', await colours(page, '[data-testid=series-chip-8]'))
        await page.screenshot(path=f'{SS}/{size}_sel8.png')
        # strip scrolled to start shows marks on chips 1-3
        await page.locator('[data-testid=series-day-strip]').evaluate('e => e.scrollTo({left:0})'); await page.wait_for_timeout(400)
        await page.locator('[data-testid=series-day-strip]').screenshot(path=f'{SS}/{size}_strip_start.png')
        # map cell day 2 -> analysis, back -> hub? (list in history)
        await page.click('[data-testid=series-calendar-day-2]')
        await page.wait_for_selector('[data-testid=series-analysis-detail]', timeout=20000)
        say(f'{size}: map day 2 opens its analysis', page.url.endswith('/analysis/' + A['2']), page.url)
        await page.go_back(); await page.wait_for_selector('[data-testid=series-analysis-list]', timeout=15000)
        await page.go_back(); await page.wait_for_selector('[data-testid=streak-journey]', timeout=15000)
        say(f'{size}: map tap back/back -> hub', page.url.endswith('/series/all-india-jee'), page.url)
        # today's marks button
        await page.click('[data-testid=today-marks-button]'); await page.wait_for_timeout(1500)
        print(f'{size}: today-marks Start ->', page.url)
        say(f'{size}: Start opens today paper', INFO['sets']['6'] in page.url, page.url)
        await page.goto(HUB); await page.wait_for_selector('[data-testid=series-more-links]', timeout=30000)
        for t in ('archive', 'analytics', 'solutions'):
            await page.goto(HUB); await page.wait_for_selector('[data-testid=series-more-links]', timeout=30000)
            await page.click(f'[data-testid=series-more-links] [data-testid=series-tab-{t}]')
            await page.wait_for_timeout(1500)
            ok = page.url.endswith('?tab=' + t) and await page.locator('[role=tablist]').count() == 1
            say(f'{size}: More {t} opens tab view with tabs', ok, page.url)
            await page.screenshot(path=f'{SS}/{size}_tab_{t}.png')
        # tab back to today hides tabs
        await page.click('[data-testid=series-tab-today]'); await page.wait_for_timeout(1200)
        say(f'{size}: Live & schedule tab -> hub without tabs', await page.locator('[role=tablist]').count() == 0 and await page.locator('[data-testid=series-more-links]').count() == 1, page.url)
        # bottom of page: More links not hidden behind mobile nav
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)'); await page.wait_for_timeout(600)
        await page.screenshot(path=f'{SS}/{size}_bottom.png')
        sw = await page.evaluate('document.documentElement.scrollWidth'); vw = await page.evaluate('document.documentElement.clientWidth')
        say(f'{size}: no side scroll', sw <= vw, (sw, vw))
    finally:
        say(f'{size}: no page errors', not [l for l in logs if 'PAGEERROR' in l], logs[:3])
        say(f'{size}: no 5xx', not [b for b in bad if b[0] >= 500], bad[:5])
        print(f'{size} 4xx:', bad[:8])
        await br.close()


async def guest(pw, size):
    br = await pw.chromium.launch()
    ctx = await br.new_context(viewport={'width': 1920 if size == 'desk' else 390, 'height': 1080 if size == 'desk' else 844})
    page = await ctx.new_page(); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)[:200]))

    async def handler(route):
        req = route.request
        hd = {k: v for k, v in req.headers.items() if k.lower() not in ('cookie', 'host', 'origin', 'referer')}
        hd['origin'] = BASE
        r = await route.fetch(url=req.url.replace(BASE, API), headers=hd); await route.fulfill(response=r)
    await page.route('**/api/**', handler)
    try:
        await page.goto(HUB); await page.wait_for_selector('[data-testid=streak-signin-card]', timeout=30000)
        href = await page.locator('[data-testid=streak-signin-link]').get_attribute('href')
        bg = await page.locator('[data-testid=streak-signin-card] .sh-journey-body').evaluate('e => getComputedStyle(e).backgroundImage.slice(0,90)')
        say(f'guest {size}: pink sign-in card + link', 'login' in href and 'FFEAF1'.lower() in bg.lower() or 'rgb(255, 234, 241)' in bg, (href, bg))
        await page.wait_for_timeout(1200)
        await page.screenshot(path=f'{SS}/guest_{size}.png')
        await page.click('[data-testid=streak-signin-link]'); await page.wait_for_timeout(1200)
        say(f'guest {size}: link opens login', '/login' in page.url, page.url)
        say(f'guest {size}: no page errors', not errs, errs[:2])
    finally:
        await br.close()


async def dark(pw):
    br, page, bad, logs = await open_as(pw, 'hero', 'mob')
    try:
        await page.goto(HUB); await page.wait_for_selector('[data-testid=streak-journey]', timeout=30000)
        btn = page.locator('[data-testid=theme-toggle]')
        if await btn.count():
            await btn.first.click(); await page.wait_for_timeout(800)
            await page.screenshot(path=f'{SS}/mob_dark_top.png')
            await page.locator('[data-testid=series-day-strip]').scroll_into_view_if_needed(); await page.wait_for_timeout(500)
            await page.screenshot(path=f'{SS}/mob_dark_days.png')
            await page.locator('[data-testid=series-calendar]').scroll_into_view_if_needed(); await page.wait_for_timeout(500)
            await page.screenshot(path=f'{SS}/mob_dark_map.png')
            await btn.first.click()
        else:
            print('no theme-toggle testid')
    finally:
        await br.close()


async def main():
    async with async_playwright() as pw:
        for size in ('desk', 'mob'):
            await walk(pw, size)
            await guest(pw, size)
        await dark(pw)
    ok = sum(1 for r in RESULT if (r[1] if isinstance(r, tuple) else r))
    print('TOTAL', len(RESULT), 'PASS', ok, 'FAIL', len(RESULT) - ok)

asyncio.run(main())
