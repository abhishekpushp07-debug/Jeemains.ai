"""TEST-ONLY iteration 260 browser walk: the website's three Rapid Fire marks open the app's Google Play page (the owner, 27 Nov 2026).
The marks: the header (desk), the middle of the bottom bar (phone), the "rapid fire" item on Home. Before, all three only said "coming soon".
/api is routed to tests/analysis_bridge196.py (127.0.0.1:8783: a signed-in student in a disposable DB; cookies in /tmp/uibridge260/bridge.json).
Google Play itself is never loaded: the request is answered here by a stand-in page, and the new tab's address is read.
Run: cd /app/backend && bash /root/p2/solo.sh bash /root/p2/rapid_ui.sh
"""
import asyncio, os, re, sys
from pathlib import Path
os.environ.setdefault('BRIDGE_OUT', '/tmp/uibridge260'); os.environ.setdefault('BRIDGE_PORT', '8783')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.async_api import async_playwright  # noqa: E402
from ui_cut210 import open_as, overflow, BASE, say, RESULT  # noqa: E402

PLAY = 'https://play.google.com/store/apps/details?id=com.emergent.jeelivemobile.kt2g15'
SS = '/app/.screenshots/ui260'; os.makedirs(SS, exist_ok=True)
LINK = "e => ({tag: e.tagName, href: e.getAttribute('href'), target: e.getAttribute('target'), rel: e.getAttribute('rel') || '', label: e.getAttribute('aria-label') || '', title: e.getAttribute('title') || '', role: e.getAttribute('role'), text: e.innerText.trim()})"
TABS = "() => [...document.querySelectorAll('[data-testid=bottom-tabs] a')].map(e => e.tagName + ':' + e.dataset.testid)"
HEADER = ['header-nav-home', 'header-nav-rank', 'header-my-tests', 'header-nav-mission', 'header-rapid-fire']


async def walk(pw, size):
    br, page, bad, logs = await open_as(pw, 'hero', size)
    asked = []

    async def play(route):
        asked.append(route.request.url)
        await route.fulfill(status=200, content_type='text/html', body='<title>Google Play (stand-in)</title>')
    await page.context.route(re.compile(r'^https://play\.google\.com/'), play)
    T = lambda t: page.locator(f'[data-testid={t}]')  # noqa: E731

    async def link(t):
        d = await T(t).first.evaluate(LINK)
        ok = (d['tag'] == 'A' and d['href'] == PLAY and d['target'] == '_blank' and 'noopener' in d['rel'] and 'Google Play' in d['label'] and d['role'] is None
              and 'coming soon' not in (d['label'] + d['title']).lower() and d['text'].lower().endswith('rapid fire'))
        return ok, d

    async def opens(do, what):
        try:
            before = len(asked)
            async with page.context.expect_page(timeout=8000) as info:
                await do()
            tab = await info.value; await tab.wait_for_load_state('domcontentloaded')
            url, alone = tab.url, await tab.evaluate('window.opener === null')
            await tab.close()
            say(f'{size}: {what}: a new tab opens at the app\'s Google Play page (asked once); the new tab cannot reach back into the website; the website stays on Home',
                url == PLAY and alone and asked[before:] == [PLAY] and page.url.rstrip('/').endswith('/home'), (url, alone, asked[before:], page.url))
        except Exception as e:  # noqa: BLE001
            say(f'{size}: {what}: a new tab opens at the app\'s Google Play page', False, repr(e)[:400])
    try:
        await page.goto(BASE + '/home'); await page.wait_for_selector('[data-testid=home-for-you-rapid-fire]', timeout=45000); await page.wait_for_timeout(1500)
        await page.screenshot(path=f'{SS}/{size}_home_top.jpg', quality=40, type='jpeg')
        if size == 'desk':
            ok, d = await link('header-rapid-fire')
            say('desk: the header\'s "Rapid Fire" mark is shown and is a link to the app\'s Google Play page (new tab, no "coming soon"); the bottom bar is not shown',
                ok and await T('header-rapid-fire').is_visible() and not await T('bottom-tabs').is_visible(), d)
            names = [await a.get_attribute('data-testid') for a in await page.locator('[data-testid=header-nav] a').all()]
            say('desk: the header is Home, Rank, My Tests, Mission, then the mark; the four before it still open inside the website', names == HEADER
                and not await page.locator('[data-testid=header-nav] a[target=_blank]:not([data-testid=header-rapid-fire])').count(), names)
            await opens(lambda: T('header-rapid-fire').click(), 'the header\'s mark is clicked')
        else:
            ok, d = await link('bottom-tab-rapid-fire')
            order = await page.evaluate(TABS)
            say('phone: the bottom bar is Home, Rank, Rapid Fire, My Tests, Mission; Rapid Fire in the middle is a link to the app\'s Google Play page (new tab, no "coming soon"); the header mark is not shown',
                ok and await T('bottom-tab-rapid-fire').is_visible() and not await T('header-rapid-fire').is_visible()
                and order == ['A:bottom-tab-home', 'A:bottom-tab-rank', 'A:bottom-tab-rapid-fire', 'A:bottom-tab-my-tests', 'A:bottom-tab-mission'], (d, order))
            await opens(lambda: T('bottom-tab-rapid-fire').locator('span').click(), 'the words "Rapid Fire" in the bottom bar are tapped')
            box = await T('bottom-tab-rapid-fire').locator('img').bounding_box(); bar = await T('bottom-tabs').bounding_box()
            say('phone: the blue gem stands out above the bottom bar', bool(box and bar) and box['y'] + 14 < bar['y'], (box, bar))
            await opens(lambda: page.mouse.click(box['x'] + box['width'] / 2, box['y'] + 12), 'the top of the gem, above the bar, is tapped')
        ok, d = await link('home-for-you-rapid-fire')
        await T('home-for-you-rapid-fire').scroll_into_view_if_needed(); await page.wait_for_timeout(400)
        others = [await a.get_attribute('href') for a in await page.locator('[data-testid=home-for-you] a:not([data-testid=home-for-you-rapid-fire])').all()]
        say(f'{size}: Home\'s "rapid fire" item is a link to the app\'s Google Play page (new tab, no "coming soon"); the three items beside it still open My Tests',
            ok and await T('home-for-you-rapid-fire').is_visible() and len(others) == 3 and all(h and h.startswith('/profile?tab=') for h in others), (d, others))
        await page.screenshot(path=f'{SS}/{size}_home_item.jpg', quality=40, type='jpeg')
        await opens(lambda: T('home-for-you-rapid-fire').click(), 'Home\'s "rapid fire" item is clicked')
        await overflow(page, size + ' Home')
        if size == 'mob':
            await T('bottom-tab-my-tests').click(); await page.wait_for_url('**/profile**', timeout=20000); await page.wait_for_timeout(600)
            say('phone: the My Tests tab next to it still opens My Tests inside the website, and is lit', '/profile' in page.url and 'is-active' in (await T('bottom-tab-my-tests').get_attribute('class') or ''), page.url)
    except Exception as e:  # noqa: BLE001
        say(f'{size}: walk', False, repr(e)[:500]); await page.screenshot(path=f'{SS}/{size}_err.jpg', quality=40, type='jpeg')
    finally:
        print('   failed calls:', [b for b in bad if '/dream' not in b[1]][:8], '| console:', [l for l in logs if 'dream' not in l and '503' not in l][:4], flush=True)
        say(f'{size}: no page error (uncaught exception) during the walk', not [l for l in logs if l.startswith('PAGEERROR')], [l for l in logs if l.startswith('PAGEERROR')][:3])
        await br.close()


async def main():
    sizes = [s for s in ('desk', 'mob') if s in sys.argv] or ['desk', 'mob']
    async with async_playwright() as pw:
        for size in sizes:
            await walk(pw, size)
    ok = sum(1 for r in RESULT if r[1])
    print('TOTAL', len(RESULT), 'PASS', ok, 'FAIL', len(RESULT) - ok)

asyncio.run(main())
