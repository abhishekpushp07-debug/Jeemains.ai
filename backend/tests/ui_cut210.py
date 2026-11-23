"""TEST-ONLY iteration 210 UI walk for PDF Engine 2.0 (printed boxes first) via local Playwright against the preview frontend,
with /api routed to the isolated bridge (tests/cut_bridge210.py on 127.0.0.1:8772).
Run: python tests/ui_cut210.py [student|results|fix|draw|plain|proof ...] [desk|mob]
"""
import asyncio, json, os, sys
from playwright.async_api import async_playwright

B = json.load(open(os.environ.get('BRIDGE_OUT', '/tmp/uibridge210') + '/bridge.json'))
BASE = [l.split('=', 1)[1].strip() for l in open('/app/frontend/.env') if l.startswith('REACT_APP_BACKEND_URL')][0].rstrip('/')
API = 'http://127.0.0.1:' + os.environ.get('BRIDGE_PORT', '8772')
SS = '/app/.screenshots/ui210'; os.makedirs(SS, exist_ok=True)
F = B.get('f', {})
SIZES = {'desk': (1920, 800), 'mob': (390, 844)}
# Things inside a strip that slides sideways by design (a zoomed picture, the question-number rail) are not page overflow.
OVERFLOW = "() => { const slides = e => { for (let p = e.parentElement; p; p = p.parentElement) { const o = getComputedStyle(p).overflowX; if (o === 'auto' || o === 'scroll') return true; } return false; }; return [...document.querySelectorAll('*')].filter(e => e.getBoundingClientRect().right > innerWidth + 1 && !slides(e)).slice(0,5).map(e => (e.className && e.className.toString()) || e.tagName); }"
LOADED = "() => [...document.querySelectorAll('.piece-img')].length >= 1 && [...document.querySelectorAll('.piece-img')].every(e => e.tagName === 'IMG' && e.complete && e.naturalWidth > 0)"
LAYOUT = """(sel) => { const box = document.querySelector(sel); if (!box) return null; const r = box.getBoundingClientRect();
  const cards = [...box.querySelectorAll('[data-testid*="-option-card-"]')].map(e => { const c = e.getBoundingClientRect(); return [c.left, c.top, c.width, c.height, e.className]; });
  return {layout: box.dataset.layout, left: r.left, width: r.width, gap: parseFloat(getComputedStyle(box).columnGap) || 0, cards}; }"""
SAYS = {'stack': 'A, B, C, D ek ke neeche ek, poori chaudai me'}
RESULT = []


def shaped(d):
    """True when the four option cards really sit one below another (A, B, C, D), each as wide as the options area."""
    if not d or len(d['cards']) != 4 or d['layout'] != 'stack':
        return False
    c = d['cards']; near = lambda a, b: abs(a - b) <= 2
    return all(near(x[0], d['left']) and near(x[2], d['width']) for x in c) and all(c[i + 1][1] >= c[i][1] + c[i][3] - 1 for i in range(3))


def say(name, ok, detail=''):
    RESULT.append((name, bool(ok))); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:600]), flush=True)


async def open_as(pw, role, size):
    br = await pw.chromium.launch()
    ctx = await br.new_context(viewport={'width': SIZES[size][0], 'height': SIZES[size][1]}, has_touch=size == 'mob')
    await ctx.add_cookies([{'name': k, 'value': v, 'url': BASE} for k, v in B[role].items()])
    # The site scrolls smoothly; a mouse drag measured in the middle of that glide lands in the wrong place, so the glide is switched off here.
    await ctx.add_init_script("addEventListener('DOMContentLoaded', () => { const s = document.createElement('style'); s.textContent = 'html{scroll-behavior:auto !important}'; document.head.appendChild(s); })")
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


def quiet(bad, logs):
    return [b for b in bad if '/dream' not in b[1]], [l for l in logs if '503' not in l and 'dream' not in l]


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
            await page.wait_for_selector('[data-testid="get-ready-begin"]', timeout=8000); await page.wait_for_timeout(3500)
            print('   get-ready load:', (await page.inner_text('[data-testid="get-ready-load"]')).replace('\n', ' ')); await page.click('[data-testid="get-ready-begin"]')
        except Exception:
            pass
        await page.wait_for_selector('[data-testid="player-piece-stem"]', timeout=25000)
        seen_mcq = seen_num = 0; layouts = {}
        for n in range(1, 17):
            await page.wait_for_function(LOADED, timeout=20000)
            heading = await page.inner_text('[data-testid="player-question-heading"]')
            mcq = await page.locator('[data-testid="player-piece-options"]').count()
            if mcq:
                seen_mcq += 1; await page.wait_for_timeout(250)
                d = await page.evaluate(LAYOUT, '[data-testid="player-piece-options"]'); layouts[heading.strip()] = d['layout']
                say(f'{tag} {heading}: 4 options {d["layout"]}: {SAYS.get(d["layout"])}', shaped(d), d)
                pane = await page.locator('[data-testid="player-piece-stem"]').evaluate("e => e.getBoundingClientRect().width")
                say(f'{tag} {heading}: options as wide as the question area', abs(pane - d['width']) <= 4, (pane, d['width']))
                say(f'{tag} {heading}: old "read options above" hint gone', await page.locator('[data-testid="player-source-options-hint"]').count() == 0)
                sizes = await page.locator('.piece-img').evaluate_all("els => els.map(e => [e.naturalWidth, e.getBoundingClientRect().width, e.getBoundingClientRect().height])")
                scale = [round(s[1] / s[0], 4) for s in sizes if s[0]]
                say(f'{tag} {heading}: question and options drawn at one zoom', max(scale) - min(scale) < .01 * max(scale) + .002, (scale, sizes))
                fits = await page.locator('[data-testid="player-piece-options"] .piece-fit').evaluate_all("els => els.every(e => e.scrollWidth <= e.clientWidth + 1)")
                say(f'{tag} {heading}: every option picture fits its card, nothing slides sideways', fits)
                if d['layout'] == 'stack' and 'stack' not in list(layouts.values())[:-1]:
                    await page.locator('[data-testid="player-piece-options"]').scroll_into_view_if_needed(); await page.screenshot(path=f'{SS}/student_{size}_long_q{n}.jpg', quality=45)
                if seen_mcq == 1:
                    await page.screenshot(path=f'{SS}/student_{size}_q{n}.jpg', quality=45)
                    await page.click('[data-testid="player-option-card-B"]'); await page.wait_for_timeout(500)
                    say(f'{tag}: tapping option B selects it', await page.locator('[data-testid="player-option-B"]').is_checked() and 'selected' in (await page.get_attribute('[data-testid="player-option-card-B"]', 'class')))
                    await page.locator('[data-testid="player-piece-options"]').scroll_into_view_if_needed()
                    await page.screenshot(path=f'{SS}/student_{size}_q{n}_picked.jpg', quality=45)
                    zin = page.locator('[data-testid="piece-zoom-in"]')
                    if await zin.count():
                        w0 = await page.locator('.piece-img').first.evaluate('e => e.getBoundingClientRect().width')
                        await zin.click(); await page.wait_for_timeout(300)
                        w1 = await page.locator('.piece-img').first.evaluate('e => e.getBoundingClientRect().width')
                        say(f'{tag}: zoom-in makes the pieces bigger', w1 > w0 * 1.2, (w0, w1))
                        await overflow(page, tag + ' zoomed')
                        await page.click('[data-testid="piece-zoom-out"]'); await page.wait_for_timeout(200)
                elif seen_mcq == 2:
                    await page.screenshot(path=f'{SS}/student_{size}_q{n}.jpg', quality=45)
                await overflow(page, f'{tag} {heading}')
            elif not mcq and not seen_num:
                seen_num = 1
                say(f'{tag} {heading}: numerical question shows its picture and a number box', await page.locator('[data-testid="player-numerical-input"]').count() == 1 and await page.locator('.piece-img').count() >= 1)
                await page.screenshot(path=f'{SS}/student_{size}_numerical.jpg', quality=45)
                await overflow(page, f'{tag} {heading}')
            if seen_num:
                break
            nxt = page.locator('[data-testid="player-next"]')
            if not await nxt.count() or await nxt.is_disabled():
                break
            await nxt.click(); await page.wait_for_timeout(450)
        say(f'{tag}: saw MCQ questions and a numerical one', seen_mcq >= 4 and seen_num == 1, (seen_mcq, seen_num))
        print('   layouts', layouts)
        say(f'{tag}: every question shows its options one below another, never 2 x 2', layouts and all(v == 'stack' for v in layouts.values()), layouts)
        bad, logs = quiet(bad, logs)
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
        await page.wait_for_function(LOADED, timeout=20000)
        await page.wait_for_timeout(300)
        d = await page.evaluate(LAYOUT, '[data-testid^="review-"][data-testid$="-piece-options"]')
        say(f'{tag}: 4 option cards ({SAYS["stack"]}), right one marked', shaped(d) and sum('is-correct' in c[4] for c in d['cards']) == 1, d)
        print('   marks', await page.locator('[data-testid*="-option-mark-"]').all_inner_texts())
        mark = await page.locator('[data-testid*="-option-mark-"]').first.evaluate("e => { const m = e.getBoundingClientRect(), c = e.closest('.piece-option').getBoundingClientRect(); return [m.left - c.left, c.right - m.right]; }")
        say(f'{tag}: the "Sahi jawab" mark stays inside its own card', mark[0] >= 0 and mark[1] >= 0, mark)
        await page.evaluate("document.querySelector('[data-testid^=\"review-piece-stem-\"]').scrollIntoView({block: 'center', behavior: 'instant'})"); await page.wait_for_timeout(300)
        await page.screenshot(path=f'{SS}/results_{size}.jpg', quality=45)
        await overflow(page, tag)
        bad, logs = quiet(bad, logs)
        say(f'{tag}: no failed API calls', not bad, bad); say(f'{tag}: no console errors', not logs, logs[:4])
    except Exception as e:
        say(tag + ' walk', False, (e, bad, logs[:4])); await page.screenshot(path=f'{SS}/results_{size}_err.jpg', quality=40)
    await br.close()


async def held_card(page, key):
    bid, mid = F[key]
    await page.goto(f'{BASE}/super-admin/fix/{bid}/{mid}')
    await page.wait_for_selector('[data-testid^="cut-q-"][data-testid$="-status"]', timeout=30000)
    tag = (await page.locator('[data-testid^="cut-q-"][data-testid$="-status"]').first.get_attribute('data-testid'))[:-len('-status')]
    await page.wait_for_selector('[data-testid="cut-frame"] canvas', timeout=30000); await page.wait_for_timeout(1500)
    return tag


async def frame_box(page):
    return await page.locator('[data-testid="cut-frame"]').bounding_box()


async def aim(page, rect):
    """Scroll so this part of the page picture (0..1 of it) is in the middle of the screen, as a person would before drawing there."""
    await page.evaluate("""(r) => { const f = document.querySelector('[data-testid="cut-frame"]').getBoundingClientRect(); window.scrollBy({top: f.top + (r[1] + r[3]) / 2 * f.height - innerHeight / 2, behavior: 'instant'}); }""", rect)
    await page.wait_for_timeout(200)
    return await frame_box(page)


async def drag(page, size, box, rect):
    """Pull a rectangle on the page picture; rect is 0..1 of the picture shown."""
    box = await aim(page, rect)
    x0, y0, x1, y1 = box['x'] + rect[0] * box['width'], box['y'] + rect[1] * box['height'], box['x'] + rect[2] * box['width'], box['y'] + rect[3] * box['height']
    await page.mouse.move(x0, y0); await page.mouse.down(); await page.mouse.move((x0 + x1) / 2, (y0 + y1) / 2, steps=4); await page.mouse.move(x1, y1, steps=4); await page.mouse.up()
    await page.wait_for_timeout(250)


async def fix(pw, size):
    """The owner's boxed PDF with a stray mark: held. Fixed on the full page with the printed boxes in one tap."""
    tag = 'fix-boxed ' + size
    br, page, bad, logs = await open_as(pw, 'owner', size)
    try:
        t = await held_card(page, 'boxed_held' if size == 'desk' else 'boxed_held_mob')
        print('   summary:', await page.inner_text('[data-testid="held-cut-summary"]'))
        print('   reason:', await page.inner_text(f'[data-testid="{t}-held-reason"]'))
        say(f'{tag}: opens on the full page, in draw mode', await page.get_attribute(f'[data-testid="{t}-view-full"]', 'aria-pressed') == 'true' and await page.get_attribute(f'[data-testid="{t}-mode-draw"]', 'aria-pressed') == 'true')
        fb = await frame_box(page)
        say(f'{tag}: the whole page is shown (page shape)', 1.2 < fb['height'] / fb['width'] < 1.6, fb)
        say(f'{tag}: five printed boxes are outlined on the page', await page.locator('[data-testid^="cut-printed-"]').count() == 5, await page.locator('[data-testid^="cut-printed-"]').count())
        boxes = await page.locator('[data-testid^="cut-box-"]').count()
        say(f'{tag}: five starting boxes (Sawaal, A, B, C, D)', boxes == 5, boxes)
        await page.locator(f'[data-testid="{t}"]').scroll_into_view_if_needed()
        await page.screenshot(path=f'{SS}/fix_boxed_{size}_1.jpg', quality=45)
        # Way 1: tap a printed box, then say whose it is.
        await page.evaluate("document.querySelector('[data-testid=\"cut-printed-1\"]').scrollIntoView({block: 'center', behavior: 'instant'})"); await page.wait_for_timeout(300)
        async def on_page(sel):
            b = await page.locator(sel).bounding_box(); f = await frame_box(page)
            return [(b['x'] - f['x']) / f['width'], (b['y'] - f['y']) / f['height'], b['width'] / f['width'], b['height'] / f['height']]
        first = await page.locator('[data-testid="cut-printed-1"]').bounding_box(); want = await on_page('[data-testid="cut-printed-1"]')
        await page.mouse.click(first['x'] + first['width'] * .7, first['y'] + first['height'] / 2); await page.wait_for_timeout(250)
        say(f'{tag}: tapping a printed box selects that whole box', await page.locator('[data-testid="cut-pending"]').count() == 1 and 'kiska' in (await page.inner_text(f'[data-testid="{t}-assign-title"]')))
        await page.locator(f'[data-testid="{t}-assign"]').scroll_into_view_if_needed()
        await page.screenshot(path=f'{SS}/fix_boxed_{size}_2_tap.jpg', quality=45)
        await page.click(f'[data-testid="{t}-assign-A"]'); await page.wait_for_timeout(250)
        a = await on_page('[data-testid="cut-box-A"]')
        say(f'{tag}: that box became option A, exactly the printed box', all(abs(x - y) < .004 for x, y in zip(a, want)), (a, want))
        # One tap: all five printed boxes.
        await page.click(f'[data-testid="{t}-use-printed"]')
        await page.wait_for_selector(f'[data-testid="{t}-reason"], [data-testid="{t}-good"]', timeout=20000); await page.wait_for_timeout(1200)
        why = await page.locator(f'[data-testid="{t}-reason"]').all_inner_texts()
        say(f'{tag}: the stray mark between the boxes is reported, not hidden', bool(why) and 'kisi bhi box me nahi' in why[0], why)
        n = await page.locator(f'[data-testid="{t}-preview"] canvas.piece-img').count()
        say(f'{tag}: live preview shows the question and four options', n == 5, n)
        d = await page.evaluate(LAYOUT, f'[data-testid="{t}-preview"] [data-testid$="-piece-options"]')
        say(f'{tag}: preview shows the options as the student gets them ({(d or {}).get("layout")})', shaped(d), d)
        say(f'{tag}: cannot save while a check fails', await page.locator(f'[data-testid="{t}-save"]').is_disabled())
        await page.check(f'[data-testid="{t}-accept-outside"]')
        await page.wait_for_selector(f'[data-testid="{t}-good"]', timeout=20000)
        await page.locator(f'[data-testid="{t}-preview"]').scroll_into_view_if_needed()
        await page.screenshot(path=f'{SS}/fix_boxed_{size}_3_preview.jpg', quality=45)
        await page.click(f'[data-testid="{t}-save"]')
        await page.wait_for_selector(f'[data-testid="{t}-saved"]', timeout=20000)
        say(f'{tag}: boxes saved', True)
        await page.wait_for_timeout(6000); await page.click('[data-testid="held-fixer-refresh"]'); await page.wait_for_timeout(2500)
        print('   summary after save:', await page.inner_text('[data-testid="held-cut-summary"]'))
        say(f'{tag}: after saving nothing is left to look at', 'aapko dekhne' not in await page.inner_text('[data-testid="held-cut-summary"]'), await page.inner_text('[data-testid="held-cut-summary"]'))
        await overflow(page, tag)
        bad, logs = quiet(bad, logs)
        say(f'{tag}: no failed API calls', not bad, bad); say(f'{tag}: no console errors', not logs, logs[:4])
    except Exception as e:
        say(tag + ' walk', False, (e, bad, logs[:4])); await page.screenshot(path=f'{SS}/fix_boxed_{size}_err.jpg', quality=40)
    await br.close()


async def plain(pw, size):
    """A page without printed boxes, labels not lined up: both ways of giving a rectangle to Sawaal / A / B / C / D."""
    tag = 'fix-draw ' + size
    br, page, bad, logs = await open_as(pw, 'owner', size)
    try:
        t = await held_card(page, 'held')
        print('   reason:', await page.inner_text(f'[data-testid="{t}-held-reason"]'))
        if size == 'desk':
            await page.click(f'[data-testid="{t}-wide"]'); await page.wait_for_timeout(300)
        await page.locator('[data-testid="cut-frame"]').scroll_into_view_if_needed(); await page.wait_for_timeout(300)
        fb = await frame_box(page)
        say(f'{tag}: the whole page is shown', 1.2 < fb['height'] / fb['width'] < 1.6, fb)
        # Where the held question sits on the page: its starting boxes tell us.
        async def box_of(key):
            b = await page.locator(f'[data-testid="cut-box-{key}"]').bounding_box(); f = await frame_box(page)
            return [(b['x'] - f['x']) / f['width'], (b['y'] - f['y']) / f['height'], (b['x'] + b['width'] - f['x']) / f['width'], (b['y'] + b['height'] - f['y']) / f['height']]
        start = {k: await box_of(k) for k in ['q', 'A', 'B', 'C', 'D']}
        # On the phone the whole page is about 270 px wide, so one pixel is over 2 points: the hand-drawn boxes stay closer to the print there.
        px, py = (.012, .004) if size == 'desk' else (.006, .001)
        pad = lambda r: [r[0] - px, r[1] - py, r[2] + px, r[3] + py]
        # Way 1: draw first, then say whose it is.
        await drag(page, size, await frame_box(page), pad(start['q']))
        say(f'{tag}: drawing a rectangle asks "Yeh hissa kiska hai?"', 'Yeh hissa kiska hai' in await page.inner_text(f'[data-testid="{t}-assign-title"]'), await page.inner_text(f'[data-testid="{t}-assign-title"]'))
        bar = await page.locator(f'[data-testid="{t}-assign"]').bounding_box(); pend = await page.locator('[data-testid="cut-pending"]').bounding_box()
        low = SIZES[size][1] - (66 if size == 'mob' else 0)
        say(f'{tag}: the rectangle and the "kiska hai" buttons are on screen together, no scrolling', bar and pend and bar['y'] >= 60 and bar['y'] + bar['height'] <= low + 1 and pend['y'] >= 60 and pend['y'] + pend['height'] <= bar['y'] + 1, (bar, pend, low))
        await page.screenshot(path=f'{SS}/fix_draw_{size}_1_ask.jpg', quality=45)
        await page.click(f'[data-testid="{t}-assign-q"]'); await page.wait_for_timeout(200)
        got = await box_of('q')
        say(f'{tag}: draw first, then Sawaal: the box sits where it was drawn', all(abs(a - b) < .012 for a, b in zip(got, pad(start['q']))), (got, pad(start['q'])))
        # Way 2: say whose it is first, then draw; the next one is picked by itself.
        await page.click(f'[data-testid="{t}-assign-A"]'); await page.wait_for_timeout(150)
        say(f'{tag}: choosing A first arms the tool', 'A ka box kheencho' in await page.inner_text(f'[data-testid="{t}-assign-title"]'), await page.inner_text(f'[data-testid="{t}-assign-title"]'))
        await aim(page, start['A'])
        await page.screenshot(path=f'{SS}/fix_draw_{size}_2_armed.jpg', quality=45)
        for k, nxt in (('A', 'B'), ('B', 'C'), ('C', 'D')):
            await drag(page, size, await frame_box(page), pad(start[k]))
            title = await page.inner_text(f'[data-testid="{t}-assign-title"]')
            say(f'{tag}: {k} drawn without another tap, {nxt} is picked by itself', f'{nxt} ka box kheencho' in title and await page.locator('[data-testid="cut-pending"]').count() == 0, title)
        await drag(page, size, await frame_box(page), pad(start['D']))
        await page.wait_for_selector(f'[data-testid="{t}-good"]', timeout=20000)
        say(f'{tag}: all five placed, every check passes', True)
        say(f'{tag}: tool goes back to "Box hilao" when all five are placed', await page.get_attribute(f'[data-testid="{t}-mode-move"]', 'aria-pressed') == 'true')
        n = await page.locator(f'[data-testid="{t}-preview"] canvas.piece-img').count()
        say(f'{tag}: live preview shows the question and four options', n == 5, n)
        await page.locator(f'[data-testid="{t}-preview"]').scroll_into_view_if_needed()
        await page.screenshot(path=f'{SS}/fix_draw_{size}_3_preview.jpg', quality=45)
        # Two boxes on top of each other are refused in plain words.
        await page.click(f'[data-testid="{t}-mode-draw"]'); await page.click(f'[data-testid="{t}-assign-B"]')
        await drag(page, size, await frame_box(page), pad(start['A']))
        await page.wait_for_selector(f'[data-testid="{t}-reason"]', timeout=20000)
        why = await page.inner_text(f'[data-testid="{t}-reason"]')
        say(f'{tag}: a box drawn over another box is refused with the reason', 'chadh' in why and await page.locator(f'[data-testid="{t}-save"]').is_disabled(), why)
        await page.click(f'[data-testid="{t}-reset"]'); await page.wait_for_timeout(300)
        await overflow(page, tag)
        bad, logs = quiet(bad, logs)
        say(f'{tag}: no failed API calls', not bad, bad); say(f'{tag}: no console errors', not logs, logs[:4])
    except Exception as e:
        say(tag + ' walk', False, (e, bad, logs[:4])); await page.screenshot(path=f'{SS}/fix_draw_{size}_err.jpg', quality=40)
    await br.close()


async def proof(pw, size):
    tag = 'proof ' + size
    br, page, bad, logs = await open_as(pw, 'owner', size)
    try:
        bid, mid = F['boxed_small']
        await page.goto(f'{BASE}/super-admin/fix/{bid}/{mid}?all=1')
        await page.wait_for_selector('[data-testid="all-questions-list"]', timeout=30000)
        print('   summary:', await page.inner_text('[data-testid="all-questions-cut-summary"]'))
        flags = await page.locator('[data-testid^="all-q-cut-"]').all_inner_texts()
        say(f'{tag}: every question of the boxed chapter is cut cleanly', flags and all('Saaf kata' in x for x in flags), flags)
        await page.click('[data-testid="all-questions-filter-proof"]')
        await page.wait_for_selector('[data-testid="proof-list"] canvas', timeout=30000); await page.wait_for_timeout(2500)
        n = await page.locator('[data-testid^="proof-"] canvas.piece-img').count()
        say(f'{tag}: proof view draws the pieces', n >= 5, n)
        boxes = await page.locator('[data-testid="proof-list"] [data-testid$="-piece-options"]').count()
        d = await page.evaluate(LAYOUT, '[data-testid="proof-list"] [data-testid$="-piece-options"]')
        say(f'{tag}: proof view shows the options one below another', boxes >= 1 and shaped(d), (boxes, d))
        await page.screenshot(path=f'{SS}/proof_{size}.jpg', quality=45)
        await overflow(page, tag)
        bad, logs = quiet(bad, logs)
        say(f'{tag}: no failed API calls', not bad, bad); say(f'{tag}: no console errors', not logs, logs[:4])
    except Exception as e:
        say(tag + ' walk', False, (e, bad, logs[:4])); await page.screenshot(path=f'{SS}/proof_{size}_err.jpg', quality=40)
    await br.close()


async def main():
    args = sys.argv[1:]
    sizes = [a for a in args if a in SIZES] or ['desk', 'mob']
    want = [a for a in args if a not in SIZES] or ['student', 'results', 'plain', 'proof', 'fix']
    async with async_playwright() as pw:
        for size in sizes:
            for name, walk in (('student', student), ('results', results), ('plain', plain), ('proof', proof), ('fix', fix)):
                if name in want:
                    await walk(pw, size)
    print('TOTAL', len(RESULT), 'PASS', sum(ok for _, ok in RESULT), 'FAIL', sum(not ok for _, ok in RESULT))

if __name__ == '__main__':
    asyncio.run(main())
