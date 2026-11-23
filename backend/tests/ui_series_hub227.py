"""TEST-ONLY iteration 227 smoke: All India hub in the app look with /api routed to tests/series_hub_bridge227.py
(127.0.0.1:8775, clock frozen at day 6). Marks on day buttons, today's marks + Analysis buttons, day tap -> analysis
(Back -> list, Back -> hub), finished unattempted day tap -> test starts.
Run: BRIDGE_OUT=/tmp/uibridge227 BRIDGE_PORT=8775 python tests/ui_series_hub227.py
"""
import asyncio, json, os, sys
from pathlib import Path
os.environ.setdefault('BRIDGE_OUT', '/tmp/uibridge227'); os.environ.setdefault('BRIDGE_PORT', '8775')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.async_api import async_playwright  # noqa: E402
from ui_cut210 import open_as, BASE, say, RESULT  # noqa: E402

INFO = json.load(open('/tmp/uibridge227/bridge.json'))
SS = '/app/.screenshots/ui227'; os.makedirs(SS, exist_ok=True)
A = INFO['attempts']


async def walk(pw, size):
    br, page, bad, logs = await open_as(pw, 'hero', size)
    try:
        await page.goto(BASE + '/series/all-india-jee'); await page.wait_for_selector('[data-testid=streak-journey]', timeout=30000)
        await page.wait_for_selector('[data-testid=series-chip-marks-1]', timeout=20000)
        await page.wait_for_timeout(800)
        await page.screenshot(path=f'{SS}/{size}_hub_top.png')
        say(f'{size}: chip marks day 1/2/3', [await page.locator(f'[data-testid=series-chip-marks-{d}]').inner_text() for d in (1, 2, 3)] == ['188', '205', '61'], '')
        say(f'{size}: map marks day 2', await page.locator('[data-testid=series-map-marks-2]').inner_text() == '205', '')
        say(f'{size}: no marks on day 4', await page.locator('[data-testid=series-chip-marks-4]').count() == 0, '')
        say(f'{size}: today marks shows Start', 'Start' in await page.locator('[data-testid=today-marks-value]').inner_text(), '')
        sw = await page.evaluate('document.documentElement.scrollWidth'); vw = await page.evaluate('document.documentElement.clientWidth')
        say(f'{size}: no side scroll', sw <= vw, (sw, vw))
        await page.locator('[data-testid=series-day-strip]').scroll_into_view_if_needed(); await page.wait_for_timeout(500)
        await page.screenshot(path=f'{SS}/{size}_hub_days.png')
        await page.locator('[data-testid=series-calendar]').scroll_into_view_if_needed(); await page.wait_for_timeout(500)
        await page.screenshot(path=f'{SS}/{size}_hub_map.png')
        await page.click('[data-testid=series-chip-3]')
        await page.wait_for_selector('[data-testid=series-analysis-detail]', timeout=20000)
        say(f'{size}: day 3 tap opens its analysis', page.url.endswith('/analysis/' + A['3']), page.url)
        await page.wait_for_selector('[data-testid=analysis2] [data-testid=a2-top-bar]', timeout=30000)
        await page.screenshot(path=f'{SS}/{size}_detail.png')
        await page.go_back(); await page.wait_for_selector('[data-testid=series-analysis-list]', timeout=15000)
        await page.wait_for_selector('[data-testid^=series-analysis-row-]', timeout=15000)
        rows = await page.locator('[data-testid^=series-analysis-row-]').evaluate_all('els => els.map(e => e.dataset.testid)')
        say(f'{size}: back -> list, newest first', rows == ['series-analysis-row-' + A[k] for k in ('3', '2', '1')], rows)
        await page.screenshot(path=f'{SS}/{size}_list.png')
        await page.go_back(); await page.wait_for_selector('[data-testid=streak-journey]', timeout=15000)
        say(f'{size}: back again -> hub', page.url.endswith('/series/all-india-jee'), page.url)
        await page.click('[data-testid=today-analysis-button]'); await page.wait_for_selector('[data-testid=series-analysis-list]', timeout=15000)
        await page.click('[data-testid=series-analysis-back]'); await page.wait_for_selector('[data-testid=streak-journey]', timeout=15000)
        say(f'{size}: Analysis button -> list -> in-page back -> hub', page.url.endswith('/series/all-india-jee'), page.url)
        day = '4' if size == 'desk' else '5'
        starts = []
        page.on('request', lambda r: starts.append(r.url) if r.method == 'POST' and r.url.endswith('/start') else None)
        await page.click(f'[data-testid=series-chip-{day}]')
        await page.wait_for_url('**/sets/' + INFO['sets'][day], timeout=20000)
        for _ in range(40):
            if starts: break
            await page.wait_for_timeout(250)
        say(f'{size}: finished unattempted day {day} opens its paper and starts it by itself', any(INFO['sets'][day] in u for u in starts), (page.url, starts))
        await page.wait_for_timeout(1000)
        await page.screenshot(path=f'{SS}/{size}_started.png')
    finally:
        bad = [b for b in bad if not b[1].endswith('/start')]
        say(f'{size}: no page errors', not [l for l in logs if 'PAGEERROR' in l], logs[:3])
        say(f'{size}: no 5xx', not [b for b in bad if b[0] >= 500], bad[:5])
        await br.close()


async def main():
    async with async_playwright() as pw:
        for size in ('desk', 'mob'):
            await walk(pw, size)
    ok = sum(1 for r in RESULT if (r[1] if isinstance(r, tuple) else r))
    print('TOTAL', len(RESULT), 'PASS', ok, 'FAIL', len(RESULT) - ok)

asyncio.run(main())
