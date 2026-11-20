"""TEST-ONLY iteration 207 UI walk for PDF Engine 2.0 via local Playwright against the preview frontend, with /api routed to the
isolated bridge (tests/cut_bridge207.py on 127.0.0.1:8772). Run: python tests/ui_cut207.py [student|results|fix|all|proof ...]
"""
import asyncio, json, os, sys
from playwright.async_api import async_playwright

B = json.load(open(os.environ.get('BRIDGE_OUT', '/tmp/uibridge207') + '/bridge.json'))
BASE = [l.split('=', 1)[1].strip() for l in open('/app/frontend/.env') if l.startswith('REACT_APP_BACKEND_URL')][0].rstrip('/')
API = 'http://127.0.0.1:' + os.environ.get('BRIDGE_PORT', '8772')
SS = '/app/.screenshots/ui207'; os.makedirs(SS, exist_ok=True)
F = B['f']
SIZES = {'desk': (1920, 800), 'mob': (390, 844)}
OVERFLOW = "() => [...document.querySelectorAll('*')].filter(e => e.getBoundingClientRect().right > innerWidth + 1 && !e.closest('.piece-fit')).slice(0,5).map(e => (e.className && e.className.toString()) || e.tagName)"
RESULT = []


def say(name, ok, detail=''):
    RESULT.append((name, bool(ok))); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:500]), flush=True)


async def open_as(pw, role, size):
    br = await pw.chromium.launch()
    ctx = await br.new_context(viewport={'width': SIZES[size][0], 'height': SIZES[size][1]})
    await ctx.add_cookies([{'name': k, 'value': v, 'url': BASE} for k, v in B[role].items()])
    page = await ctx.new_page(); bad, logs = [], []
    async def handler(route):
        req = route.request
        hd = {k: v for k, v in req.headers.items() if k.lower() not in ('cookie', 'host', 'origin', 'referer')}
        hd['cookie'] = '; '.join(f"{c['name']}={c['value']}" for c in await ctx.cookies(BASE))
        hd['origin'] = BASE
        try:
            r = await route.fetch(url=req.url.replace(BASE, API), headers=hd)
            await route.fulfill(response=r)
        except Exception as e:
            print('route err', req.url[-80:], e); await route.abort()
    await page.route('**/api/**', handler)
    page.on('response', lambda r: bad.append((r.status, r.url.split('/api')[-1][:90])) if '/api/' in r.url and r.status >= 400 else None)
    page.on('console', lambda m: logs.append(m.text[:300]) if m.type == 'error' else None)
    page.on('pageerror', lambda e: logs.append('PAGEERROR ' + str(e)[:300]))
    return br, page, bad, logs


async def overflow(page, tag):
    off = await page.evaluate(OVERFLOW); vw = await page.evaluate('document.documentElement.clientWidth')
    sw = await page.evaluate('document.documentElement.scrollWidth')
    say(f'{tag}: no horizontal overflow', not off and sw <= vw + 1, (vw, sw, off))


async def student(pw, size):
    tag = 'student ' + size
    br, page, bad, logs = await open_as(pw, 'student', size)
    try:
        await page.goto(f"{BASE}/attempts/{F['active_attempt']}")
        try:
            await page.wait_for_selector('[data-testid="get-ready-begin"]', timeout=6000); await page.wait_for_timeout(2500)
            print('get-ready load', await page.inner_text('[data-testid="get-ready-load"]')); await page.click('[data-testid="get-ready-begin"]')
        except Exception:
            pass
        await page.wait_for_selector('[data-testid="player-piece-options"]', timeout=25000)
        for n in range(1, 5):
            await page.wait_for_function("() => [...document.querySelectorAll('[data-testid=\"player-question-stem\"] img, [data-testid=\"player-piece-options\"] img')].length >= 5 && [...document.querySelectorAll('.piece-img')].every(e => e.tagName === 'IMG' && e.complete && e.naturalWidth > 0)", timeout=20000)
            cards = await page.locator('[data-testid^="player-option-card-"]').evaluate_all("els => els.map(e => { const r = e.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; })")
            box = await page.locator('[data-testid="player-piece-options"]').evaluate("e => { const r = e.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.width)]; }")
            stacked = len(cards) == 4 and all(c[0] == cards[0][0] and abs(c[2] - box[1]) <= 2 for c in cards) and all(cards[i + 1][1] >= cards[i][1] + cards[i][3] for i in range(3))
            say(f'{tag} Q{n}: 4 options one below another, full width', stacked, (cards, box))
            hint = await page.locator('[data-testid="player-source-options-hint"]').count()
            say(f'{tag} Q{n}: old "read options above" hint gone', hint == 0)
            heights = await page.locator('.piece-img').evaluate_all("els => els.map(e => [e.naturalWidth, Math.round(e.getBoundingClientRect().width), Math.round(e.getBoundingClientRect().height)])")
            print(f'   Q{n} piece sizes natural/shown', heights)
            if n == 1:
                await page.screenshot(path=f'{SS}/student_{size}_q1.jpg', quality=45)
                await page.click('[data-testid="player-option-card-B"]'); await page.wait_for_timeout(500)
                say(f'{tag}: tapping option B selects it', await page.locator('[data-testid="player-option-B"]').is_checked() and 'selected' in (await page.get_attribute('[data-testid="player-option-card-B"]', 'class')))
                await page.screenshot(path=f'{SS}/student_{size}_q1_picked.jpg', quality=45)
                zin = page.locator('[data-testid="piece-zoom-in"]')
                if await zin.count():
                    w0 = await page.locator('[data-testid="player-piece-0"]').evaluate('e => e.getBoundingClientRect().width')
                    await zin.click(); await page.wait_for_timeout(300)
                    w1 = await page.locator('[data-testid="player-piece-0"]').evaluate('e => e.getBoundingClientRect().width')
                    say(f'{tag}: zoom-in makes the pieces bigger', w1 > w0 * 1.2, (w0, w1))
                    await overflow(page, tag + ' zoomed')
                    await page.screenshot(path=f'{SS}/student_{size}_q1_zoom.jpg', quality=45)
                    await page.click('[data-testid="piece-zoom-out"]'); await page.wait_for_timeout(200)
            if n in (3, 4):
                await page.screenshot(path=f'{SS}/student_{size}_q{n}.jpg', quality=45)
            await overflow(page, f'{tag} Q{n}')
            if n < 4:
                await page.click('[data-testid="player-next"]'); await page.wait_for_timeout(500)
        say(f'{tag}: no failed API calls', not bad, bad); say(f'{tag}: no console errors', not logs, logs[:4])
    except Exception as e:
        say(tag + ' walk', False, (e, bad, logs[:4])); await page.screenshot(path=f'{SS}/student_{size}_err.jpg', quality=40)
    await br.close()


async def results(pw, size):
    tag = 'results ' + size
    br, page, bad, logs = await open_as(pw, 'student', size)
    try:
        await page.goto(f"{BASE}/results/{F['done_attempt']}?view=solutions")
        await page.wait_for_selector('[data-testid^="review-piece-stem-"]', timeout=30000)
        await page.wait_for_function("() => [...document.querySelectorAll('.piece-img')].length >= 5 && [...document.querySelectorAll('.piece-img')].every(e => e.tagName === 'IMG' && e.complete && e.naturalWidth > 0)", timeout=20000)
        cards = await page.locator('[data-testid^="review-1-option-card-"]').evaluate_all("els => els.map(e => { const r = e.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.width), e.className]; })")
        say(f'{tag}: 4 option cards stacked, right one marked', len(cards) == 4 and len({(c[0], c[1]) for c in cards}) == 1 and sum('is-correct' in c[2] for c in cards) == 1, cards)
        print('   marks', await page.locator('[data-testid^="review-1-option-mark-"]').all_inner_texts())
        await page.locator('[data-testid^="review-piece-stem-"]').first.scroll_into_view_if_needed()
        await page.screenshot(path=f'{SS}/results_{size}.jpg', quality=45)
        await overflow(page, tag)
        say(f'{tag}: no failed API calls', not [b for b in bad if '/dream' not in b[1]], bad); say(f'{tag}: no console errors', not [l for l in logs if '503' not in l and 'dream' not in l], logs[:4])
    except Exception as e:
        say(tag + ' walk', False, (e, bad, logs[:4])); await page.screenshot(path=f'{SS}/results_{size}_err.jpg', quality=40)
    await br.close()


async def fix(pw, size, key='held'):
    tag = 'fix ' + size
    br, page, bad, logs = await open_as(pw, 'owner', size)
    try:
        bid, mid = F[key]
        await page.goto(f'{BASE}/super-admin/fix/{bid}/{mid}')
        await page.wait_for_selector('[data-testid="cut-q-4"]', timeout=30000)
        print('   summary:', await page.inner_text('[data-testid="held-cut-summary"]'))
        print('   reason:', await page.inner_text('[data-testid="cut-q-4-held-reason"]'))
        await page.wait_for_selector('[data-testid="cut-frame"] canvas', timeout=30000); await page.wait_for_timeout(2500)
        boxes = await page.locator('[data-testid^="cut-box-"]').evaluate_all("els => els.map(e => { const r = e.getBoundingClientRect(); return [e.dataset.testid, Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; })")
        say(f'{tag}: five boxes (Sawaal, A, B, C, D) on the page', len(boxes) == 5, boxes)
        await page.locator('[data-testid="cut-q-4"]').scroll_into_view_if_needed()
        await page.screenshot(path=f'{SS}/fix_{size}_1.jpg', quality=45)
        print('   first check:', (await page.locator('[data-testid="cut-q-4-reason"], [data-testid="cut-q-4-good"]').all_inner_texts()))
        await overflow(page, tag)
        say(f'{tag}: no failed API calls', not bad, bad); say(f'{tag}: no console errors', not logs, logs[:4])
    except Exception as e:
        say(tag + ' walk', False, (e, bad, logs[:4])); await page.screenshot(path=f'{SS}/fix_{size}_err.jpg', quality=40)
    await br.close()


async def proof(pw, size):
    tag = 'proof ' + size
    br, page, bad, logs = await open_as(pw, 'owner', size)
    try:
        bid, mid = F['draft']
        await page.goto(f'{BASE}/super-admin/fix/{bid}/{mid}?all=1')
        await page.wait_for_selector('[data-testid="all-questions-list"]', timeout=30000)
        print('   summary:', await page.inner_text('[data-testid="all-questions-cut-summary"]'))
        print('   flags:', await page.locator('[data-testid^="all-q-cut-"]').all_inner_texts())
        await page.screenshot(path=f'{SS}/all_{size}.jpg', quality=45)
        await page.click('[data-testid="all-questions-filter-proof"]')
        await page.wait_for_selector('[data-testid="proof-list"] canvas', timeout=30000); await page.wait_for_timeout(2500)
        n = await page.locator('[data-testid^="proof-"] canvas.piece-img').count()
        say(f'{tag}: proof view draws the pieces', n >= 5, n)
        await page.screenshot(path=f'{SS}/proof_{size}.jpg', quality=45)
        await overflow(page, tag)
        say(f'{tag}: no failed API calls', not bad, bad); say(f'{tag}: no console errors', not logs, logs[:4])
    except Exception as e:
        say(tag + ' walk', False, (e, bad, logs[:4])); await page.screenshot(path=f'{SS}/proof_{size}_err.jpg', quality=40)
    await br.close()


async def main():
    want = sys.argv[1:] or ['student', 'results', 'fix', 'proof']
    async with async_playwright() as pw:
        for size in ('desk', 'mob'):
            if 'student' in want: await student(pw, size)
            if 'results' in want: await results(pw, size)
            if 'fix' in want: await fix(pw, size)
            if 'proof' in want: await proof(pw, size)
    print('TOTAL', len(RESULT), 'PASS', sum(ok for _, ok in RESULT), 'FAIL', sum(not ok for _, ok in RESULT))

asyncio.run(main())
