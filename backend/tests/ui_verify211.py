"""TEST-ONLY independent browser verification (iteration 211) of PDF Engine 2.0 stacked options + full-page fix tool.
Routes /api to the disposable bridge (tests/cut_bridge210.py, 127.0.0.1:8772). Run: python tests/ui_verify211.py [student results proof boxfix plain typed] [desk mob]
"""
import asyncio, json, os, sys
from playwright.async_api import async_playwright

B = json.load(open('/tmp/uibridge210/bridge.json'))
BASE = [l.split('=', 1)[1].strip() for l in open('/app/frontend/.env') if l.startswith('REACT_APP_BACKEND_URL')][0].rstrip('/')
API = 'http://127.0.0.1:8772'
SS = os.environ.get('SS_DIR', '/app/.screenshots/ui211'); os.makedirs(SS, exist_ok=True)
F = B['f']
SIZES = {'desk': (1920, 800), 'mob': (390, 844)}
R = []

# Independent geometry probe: per option container -> computed grid columns, card rects, picture natural vs drawn ratio
PROBE = """(sel) => [...document.querySelectorAll(sel)].map(box => {
  const r = box.getBoundingClientRect(); const cs = getComputedStyle(box);
  const cols = cs.gridTemplateColumns.split(' ').filter(Boolean).length;
  const cards = [...box.querySelectorAll('[data-testid*="-option-card-"]')].map(c => { const b = c.getBoundingClientRect(); return {x: b.left, y: b.top, w: b.width, h: b.height, cls: c.className}; });
  const pics = [...box.querySelectorAll('img.piece-img, canvas.piece-img')].map(p => { const b = p.getBoundingClientRect(); const nw = p.naturalWidth || p.width, nh = p.naturalHeight || p.height; return {ratioDrawn: b.width / Math.max(b.height, 1), ratioNat: nw / Math.max(nh, 1), w: b.width, nw}; });
  return {layout: box.dataset.layout, display: cs.display, cols, flexDir: cs.flexDirection, x: r.left, w: r.width, cards, pics};
})"""
HOVF = "() => { const out = []; const vw = document.documentElement.clientWidth; for (const e of document.querySelectorAll('body *')) { const b = e.getBoundingClientRect(); if (b.width && b.right > vw + 2) { let s = false; for (let p = e.parentElement; p; p = p.parentElement) { const o = getComputedStyle(p).overflowX; if (o !== 'visible') { s = true; break; } } if (!s) out.push(e.tagName + '.' + String(e.className).slice(0, 40)); } } return {sw: document.documentElement.scrollWidth, vw, out: out.slice(0, 5)}; }"


def ok(name, cond, detail=''):
    R.append((name, bool(cond))); print(('PASS ' if cond else 'FAIL ') + name + ('' if cond else ' :: ' + str(detail)[:500]), flush=True)


def stacked(g):
    """One column, cards top-to-bottom, each card spans the container width."""
    if not g or len(g['cards']) != 4:
        return False
    c = g['cards']
    same_x = all(abs(k['x'] - g['x']) <= 2 for k in c)
    full = all(abs(k['w'] - g['w']) <= 2 for k in c)
    down = all(c[i + 1]['y'] >= c[i]['y'] + c[i]['h'] - 1 for i in range(3))
    return g['cols'] <= 1 and same_x and full and down


def not_squashed(g):
    return all(abs(p['ratioDrawn'] - p['ratioNat']) / max(p['ratioNat'], .01) < .03 for p in g['pics'])


async def open_as(pw, role, size):
    br = await pw.chromium.launch()
    ctx = await br.new_context(viewport={'width': SIZES[size][0], 'height': SIZES[size][1]}, has_touch=size == 'mob')
    await ctx.add_cookies([{'name': k, 'value': v, 'url': BASE} for k, v in B[role].items()])
    await ctx.add_init_script("addEventListener('DOMContentLoaded', () => { const s = document.createElement('style'); s.textContent = 'html{scroll-behavior:auto !important}'; document.head.appendChild(s); })")
    page = await ctx.new_page(); bad, logs = [], []

    async def handler(route):
        req = route.request
        hd = {k: v for k, v in req.headers.items() if k.lower() not in ('cookie', 'host', 'origin', 'referer')}
        hd['cookie'] = '; '.join(f"{c['name']}={c['value']}" for c in await ctx.cookies(BASE)); hd['origin'] = BASE
        try:
            await route.fulfill(response=await route.fetch(url=req.url.replace(BASE, API), headers=hd))
        except Exception:
            await route.abort()
    await page.route('**/api/**', handler)
    page.on('response', lambda r: bad.append((r.status, r.url.split('/api')[-1][:80])) if '/api/' in r.url and r.status >= 400 and '/dream' not in r.url else None)
    page.on('pageerror', lambda e: logs.append(str(e)[:200]))
    return br, page, bad, logs


async def no_overflow(page, tag):
    o = await page.evaluate(HOVF)
    ok(f'{tag}: no horizontal page overflow', o['sw'] <= o['vw'] + 1 and not o['out'], o)


async def wait_pics(page):
    await page.wait_for_function("() => { const p = [...document.querySelectorAll('.piece-img')]; return p.length && p.every(e => e.tagName !== 'IMG' || (e.complete && e.naturalWidth > 0)); }", timeout=25000)
    await page.wait_for_timeout(300)


async def student(pw, size):
    tag = 'student-' + size
    br, page, bad, logs = await open_as(pw, 'student', size)
    try:
        await page.goto(f"{BASE}/attempts/{F['active_attempt']}")
        try:
            await page.wait_for_selector('[data-testid="get-ready-begin"]', timeout=8000); await page.wait_for_timeout(3000)
            await page.click('[data-testid="get-ready-begin"]')
        except Exception:
            pass
        await page.wait_for_selector('[data-testid="player-piece-stem"]', timeout=25000)
        mcq = num = 0; fails = []
        for n in range(1, 31):
            await wait_pics(page)
            head = (await page.inner_text('[data-testid="player-question-heading"]')).strip()
            if await page.locator('[data-testid="player-piece-options"]').count():
                mcq += 1
                g = (await page.evaluate(PROBE, '[data-testid="player-piece-options"]'))[0]
                stem_w = await page.locator('[data-testid="player-piece-stem"]').evaluate('e => e.getBoundingClientRect().width')
                if not (stacked(g) and g['layout'] == 'stack' and abs(stem_w - g['w']) <= 4 and not_squashed(g)):
                    fails.append((head, g['cols'], [round(c['x']) for c in g['cards']], round(stem_w), round(g['w'])))
                # same zoom: drawn width / natural width equal for stem and options
                sc = await page.locator('.piece-img').evaluate_all("els => els.map(e => e.getBoundingClientRect().width / (e.naturalWidth || e.width))")
                if max(sc) - min(sc) > .01 * max(sc) + .002:
                    fails.append((head, 'zoom mismatch', sc))
                if mcq == 1:
                    await page.screenshot(path=f'{SS}/student_{size}_first.jpg', quality=40)
                    # pick C then D: only the last stays selected
                    await page.click('[data-testid="player-option-card-C"]'); await page.wait_for_timeout(300)
                    await page.click('[data-testid="player-option-card-D"]'); await page.wait_for_timeout(400)
                    sel = await page.evaluate("() => [...document.querySelectorAll('[data-testid^=\"player-option-card-\"]')].filter(e => e.classList.contains('selected')).map(e => e.dataset.testid.slice(-1))")
                    st = await page.locator('[data-testid="player-option-card-D"]').evaluate("e => { const s = getComputedStyle(e); return [s.borderTopColor, s.boxShadow.slice(0, 40)]; }")
                    ok(f'{tag}: picking C then D leaves only D selected', sel == ['D'], sel)
                    print('   selected card style', st)
                    await page.locator('[data-testid="player-piece-options"]').scroll_into_view_if_needed()
                    await page.screenshot(path=f'{SS}/student_{size}_picked.jpg', quality=40)
                    zi = page.locator('[data-testid="piece-zoom-in"]')
                    if await zi.count():
                        w0 = await page.locator('.piece-img').last.evaluate('e => e.getBoundingClientRect().width')
                        await zi.click(); await page.wait_for_timeout(300); await zi.click(); await page.wait_for_timeout(300)
                        w1 = await page.locator('.piece-img').last.evaluate('e => e.getBoundingClientRect().width')
                        g2 = (await page.evaluate(PROBE, '[data-testid="player-piece-options"]'))[0]
                        ok(f'{tag}: zoom-in x2 grows option pictures and keeps stack', w1 > w0 * 1.15 and stacked(g2), (w0, w1, g2['cols']))
                        await no_overflow(page, tag + ' zoomed')
                        await page.screenshot(path=f'{SS}/student_{size}_zoomed.jpg', quality=40)
                        zo = page.locator('[data-testid="piece-zoom-out"]')
                        await zo.click(); await page.wait_for_timeout(200); await zo.click(); await page.wait_for_timeout(300)
                        w2 = await page.locator('.piece-img').last.evaluate('e => e.getBoundingClientRect().width')
                        ok(f'{tag}: zoom-out x2 returns to original size', abs(w2 - w0) < 2, (w0, w2))
                    else:
                        ok(f'{tag}: zoom buttons present', False)
                await no_overflow(page, f'{tag} {head}')
            elif not num:
                num = 1
                inp = page.locator('[data-testid="player-numerical-input"]')
                ok(f'{tag} {head}: numerical shows picture + number box', await inp.count() == 1 and await page.locator('.piece-img').count() >= 1)
                await inp.fill('12.5'); await page.wait_for_timeout(200)
                ok(f'{tag}: number box accepts typing', (await inp.input_value()) == '12.5', await inp.input_value())
                await inp.fill('')
                await page.screenshot(path=f'{SS}/student_{size}_numerical.jpg', quality=40)
                await no_overflow(page, f'{tag} numerical')
                break
            nx = page.locator('[data-testid="player-next"]')
            if not await nx.count() or await nx.is_disabled():
                break
            await nx.click(); await page.wait_for_timeout(400)
        ok(f'{tag}: every MCQ ({mcq}) stacked full-width, same zoom, unsquashed', mcq >= 4 and not fails, fails[:4])
        ok(f'{tag}: saw a numerical question', num == 1)
        ok(f'{tag}: no API errors / page errors', not bad and not logs, (bad[:4], logs[:3]))
    except Exception as e:
        ok(tag + ' walk', False, (e, bad[:3], logs[:3])); await page.screenshot(path=f'{SS}/student_{size}_err.jpg', quality=40)
    await br.close()


async def results(pw, size):
    tag = 'results-' + size
    br, page, bad, logs = await open_as(pw, 'student', size)
    try:
        await page.goto(f"{BASE}/results/{F['done_attempt']}?view=solutions")
        await page.wait_for_selector('[data-testid$="-piece-options"]', timeout=30000); await wait_pics(page)
        gs = await page.evaluate(PROBE, '[data-testid$="-piece-options"]')
        badg = [i for i, g in enumerate(gs) if not (stacked(g) and g['layout'] == 'stack' and not_squashed(g))]
        ok(f'{tag}: all {len(gs)} option groups stacked one below another', gs and not badg, [(gs[i]['cols'], [round(c['x']) for c in gs[i]['cards']]) for i in badg[:3]])
        right = [sum('is-correct' in c['cls'] for c in g['cards']) for g in gs]
        ok(f'{tag}: exactly one correct card per question', all(x == 1 for x in right), right)
        marks = await page.evaluate("() => [...document.querySelectorAll('[data-testid*=\"-option-mark-\"]')].map(m => { const c = m.closest('.piece-option'); const a = m.getBoundingClientRect(), b = c.getBoundingClientRect(); return {t: m.innerText, inside: a.left >= b.left - 1 && a.right <= b.right + 1 && a.bottom <= b.bottom + 1 && (!c.previousElementSibling || a.top >= c.previousElementSibling.getBoundingClientRect().bottom),  right: c.classList.contains('is-correct')}; })")
        ok(f'{tag}: "Sahi jawab" marks inside their own (correct) card', marks and all(m['inside'] for m in marks) and any('Sahi jawab' in m['t'] and m['right'] for m in marks), marks[:4])
        await page.locator('[data-testid$="-piece-options"]').first.scroll_into_view_if_needed()
        await page.screenshot(path=f'{SS}/results_{size}.jpg', quality=40)
        await no_overflow(page, tag)
        ok(f'{tag}: no API errors / page errors', not bad and not logs, (bad[:4], logs[:3]))
    except Exception as e:
        ok(tag + ' walk', False, (e, bad[:3], logs[:3])); await page.screenshot(path=f'{SS}/results_{size}_err.jpg', quality=40)
    await br.close()


async def proof(pw, size):
    tag = 'proof-' + size
    br, page, bad, logs = await open_as(pw, 'owner', size)
    try:
        bid, mid = F['boxed_small']
        await page.goto(f'{BASE}/super-admin/fix/{bid}/{mid}?all=1')
        await page.wait_for_selector('[data-testid="all-questions-list"]', timeout=30000)
        flags = await page.locator('[data-testid^="all-q-cut-"]').all_inner_texts()
        ok(f'{tag}: every boxed question flagged "Saaf kata" ({len(flags)})', flags and all('Saaf kata' in f for f in flags), flags[:5])
        await page.click('[data-testid="all-questions-filter-proof"]')
        await page.wait_for_selector('[data-testid="proof-list"] .piece-img', timeout=30000); await page.wait_for_timeout(2500)
        gs = await page.evaluate(PROBE, '[data-testid="proof-list"] [data-testid$="-piece-options"]')
        badg = [i for i, g in enumerate(gs) if not stacked(g)]
        ok(f'{tag}: all {len(gs)} proof option groups stacked', gs and not badg, [(gs[i]['cols'], len(gs[i]['cards'])) for i in badg[:3]])
        await page.locator('[data-testid="proof-list"] [data-testid$="-piece-options"]').first.scroll_into_view_if_needed()
        await page.screenshot(path=f'{SS}/proof_{size}.jpg', quality=40)
        await no_overflow(page, tag)
        ok(f'{tag}: no API errors / page errors', not bad and not logs, (bad[:4], logs[:3]))
    except Exception as e:
        ok(tag + ' walk', False, (e, bad[:3], logs[:3])); await page.screenshot(path=f'{SS}/proof_{size}_err.jpg', quality=40)
    await br.close()


async def open_fix(page, key):
    bid, mid = F[key]
    await page.goto(f'{BASE}/super-admin/fix/{bid}/{mid}')
    await page.wait_for_selector('[data-testid^="cut-q-"][data-testid$="-status"]', timeout=30000)
    t = (await page.locator('[data-testid^="cut-q-"][data-testid$="-status"]').first.get_attribute('data-testid'))[:-7]
    await page.wait_for_selector('[data-testid="cut-frame"] canvas', timeout=30000); await page.wait_for_timeout(1500)
    return t


async def rect_of(page, sel):
    b = await page.locator(sel).bounding_box(); f = await page.locator('[data-testid="cut-frame"]').bounding_box()
    return [(b['x'] - f['x']) / f['width'], (b['y'] - f['y']) / f['height'], (b['x'] + b['width'] - f['x']) / f['width'], (b['y'] + b['height'] - f['y']) / f['height']]


async def pull(page, r):
    await page.evaluate("(r) => { const f = document.querySelector('[data-testid=\"cut-frame\"]').getBoundingClientRect(); window.scrollBy(0, f.top + (r[1] + r[3]) / 2 * f.height - innerHeight / 2); }", r)
    await page.wait_for_timeout(200)
    f = await page.locator('[data-testid="cut-frame"]').bounding_box()
    x0, y0, x1, y1 = f['x'] + r[0] * f['width'], f['y'] + r[1] * f['height'], f['x'] + r[2] * f['width'], f['y'] + r[3] * f['height']
    await page.mouse.move(x0, y0); await page.mouse.down(); await page.mouse.move(x1, y1, steps=8); await page.mouse.up(); await page.wait_for_timeout(300)


async def boxfix(pw, size):
    tag = 'boxfix-' + size
    br, page, bad, logs = await open_as(pw, 'owner', size)
    try:
        t = await open_fix(page, 'boxed_held' if size == 'desk' else 'boxed_held_mob')
        print('   held reason:', (await page.inner_text(f'[data-testid="{t}-held-reason"]'))[:200])
        ok(f'{tag}: full page + draw mode by default', await page.get_attribute(f'[data-testid="{t}-view-full"]', 'aria-pressed') == 'true' and await page.get_attribute(f'[data-testid="{t}-mode-draw"]', 'aria-pressed') == 'true')
        np, nb = await page.locator('[data-testid^="cut-printed-"]').count(), await page.locator('[data-testid^="cut-box-"]').count()
        ok(f'{tag}: 5 printed outlines + 5 starting boxes', np == 5 and nb == 5, (np, nb))
        keys = sorted([await page.locator('[data-testid^="cut-box-"]').nth(i).get_attribute('data-testid') for i in range(nb)])
        ok(f'{tag}: starting boxes are q/A/B/C/D', keys == sorted(['cut-box-' + k for k in 'qABCD']), keys)
        await page.locator(f'[data-testid="{t}"]').scroll_into_view_if_needed(); await page.screenshot(path=f'{SS}/boxfix_{size}_open.jpg', quality=40)
        # Tap the LAST printed box (different from reference walk) and assign it to C
        last = '[data-testid="cut-printed-4"]'
        want = await rect_of(page, last)
        await page.evaluate("document.querySelector('[data-testid=\"cut-printed-4\"]').scrollIntoView({block:'center'})"); await page.wait_for_timeout(300)
        b = await page.locator(last).bounding_box()
        await page.mouse.click(b['x'] + b['width'] * .3, b['y'] + b['height'] * .5); await page.wait_for_timeout(300)
        title = await page.inner_text(f'[data-testid="{t}-assign-title"]')
        ok(f'{tag}: tapping printed box asks "Yeh hissa kiska hai?"', 'kiska hai' in title and await page.locator('[data-testid="cut-pending"]').count() == 1, title)
        bar = await page.locator(f'[data-testid="{t}-assign"]').bounding_box(); pend = await page.locator('[data-testid="cut-pending"]').bounding_box()
        vh = SIZES[size][1]
        ok(f'{tag}: pending box and assign bar both on screen', bar and pend and 0 <= bar['y'] and bar['y'] + bar['height'] <= vh and 0 <= pend['y'] and pend['y'] + pend['height'] <= vh, (bar, pend))
        await page.screenshot(path=f'{SS}/boxfix_{size}_ask.jpg', quality=40)
        await page.click(f'[data-testid="{t}-assign-A"]'); await page.wait_for_timeout(300)
        got = await rect_of(page, '[data-testid="cut-box-A"]')
        ok(f'{tag}: choosing A puts box A exactly on that printed box', all(abs(x - y) < .005 for x, y in zip(got, want)), (got, want))
        await page.click(f'[data-testid="{t}-use-printed"]')
        await page.wait_for_selector(f'[data-testid="{t}-reason"], [data-testid="{t}-good"]', timeout=20000); await page.wait_for_timeout(1500)
        reasons = await page.locator(f'[data-testid="{t}-reason"]').all_inner_texts()
        ok(f'{tag}: stray print reported ("kisi bhi box me nahi")', any('kisi bhi box me nahi' in r for r in reasons), reasons)
        ok(f'{tag}: save disabled while check fails', await page.locator(f'[data-testid="{t}-save"]').is_disabled())
        gs = await page.evaluate(PROBE, f'[data-testid="{t}-preview"] [data-testid$="-piece-options"]')
        ok(f'{tag}: preview options stacked', gs and stacked(gs[0]), gs[:1])
        await page.check(f'[data-testid="{t}-accept-outside"]')
        await page.wait_for_selector(f'[data-testid="{t}-good"]', timeout=20000)
        ok(f'{tag}: override tick passes checks, Save enabled', await page.locator(f'[data-testid="{t}-save"]').is_enabled())
        await page.locator(f'[data-testid="{t}-preview"]').scroll_into_view_if_needed(); await page.screenshot(path=f'{SS}/boxfix_{size}_preview.jpg', quality=40)
        await no_overflow(page, tag + ' before save')
        await page.click(f'[data-testid="{t}-save"]')
        await page.wait_for_selector(f'[data-testid="{t}-saved"]', timeout=25000)
        ok(f'{tag}: "Save ho gaya" shown', 'Save ho gaya' in await page.inner_text(f'[data-testid="{t}-saved"]'), await page.inner_text(f'[data-testid="{t}-saved"]'))
        await page.wait_for_timeout(6000); await page.reload(); await page.wait_for_timeout(5000)
        left = await page.locator('[data-testid^="cut-q-"][data-testid$="-status"]').count()
        summ = await page.locator('[data-testid="held-cut-summary"]').all_inner_texts()
        print('   after reload summary:', summ, 'cards left', left)
        ok(f'{tag}: after page reload no held card left', left == 0, (left, summ))
        await page.screenshot(path=f'{SS}/boxfix_{size}_after.jpg', quality=40)
        ok(f'{tag}: no API errors / page errors', not bad and not logs, (bad[:4], logs[:3]))
    except Exception as e:
        ok(tag + ' walk', False, (e, bad[:3], logs[:3])); await page.screenshot(path=f'{SS}/boxfix_{size}_err.jpg', quality=40)
    await br.close()


async def plain(pw, size):
    tag = 'plain-' + size
    br, page, bad, logs = await open_as(pw, 'owner', size)
    try:
        t = await open_fix(page, 'held')
        st = {k: await rect_of(page, f'[data-testid="cut-box-{k}"]') for k in 'qABCD'}
        px, py = (.01, .003) if size == 'desk' else (.005, .001)
        pad = lambda r: [r[0] - px, r[1] - py, r[2] + px, r[3] + py]
        await pull(page, pad(st['q']))
        title = await page.inner_text(f'[data-testid="{t}-assign-title"]')
        ok(f'{tag}: drawn rectangle asks "Yeh hissa kiska hai?"', 'Yeh hissa kiska hai' in title, title)
        bar = await page.locator(f'[data-testid="{t}-assign"]').bounding_box(); pend = await page.locator('[data-testid="cut-pending"]').bounding_box()
        vh = SIZES[size][1]
        ok(f'{tag}: rectangle and kiska-hai bar visible together', bar and pend and bar['y'] >= 0 and bar['y'] + bar['height'] <= vh and pend['y'] >= 0 and pend['y'] + pend['height'] <= vh, (bar, pend))
        await page.screenshot(path=f'{SS}/plain_{size}_ask.jpg', quality=40)
        await page.click(f'[data-testid="{t}-assign-q"]'); await page.wait_for_timeout(250)
        await page.click(f'[data-testid="{t}-assign-A"]'); await page.wait_for_timeout(200)
        titles = []
        for k in 'ABCD':
            await pull(page, pad(st[k]))
            if k != 'D':
                titles.append(await page.inner_text(f'[data-testid="{t}-assign-title"]'))
        ok(f'{tag}: next letter auto-picked after A, B, C', all(f'{n} ka box' in titles[i] for i, n in enumerate('BCD')), titles)
        await page.wait_for_selector(f'[data-testid="{t}-good"]', timeout=20000)
        ok(f'{tag}: assign bar hides / tool switches to move after D', await page.get_attribute(f'[data-testid="{t}-mode-move"]', 'aria-pressed') == 'true')
        ok(f'{tag}: all checks pass after 5 boxes, Save enabled', await page.locator(f'[data-testid="{t}-save"]').is_enabled())
        gs = await page.evaluate(PROBE, f'[data-testid="{t}-preview"] [data-testid$="-piece-options"]')
        nimg = await page.locator(f'[data-testid="{t}-preview"] .piece-img').count()
        ok(f'{tag}: preview = question + 4 stacked options', nimg == 5 and gs and stacked(gs[0]), (nimg, gs[:1]))
        await page.locator(f'[data-testid="{t}-preview"]').scroll_into_view_if_needed(); await page.screenshot(path=f'{SS}/plain_{size}_preview.jpg', quality=40)
        # overlap: draw D over C's print
        await page.click(f'[data-testid="{t}-mode-draw"]'); await page.click(f'[data-testid="{t}-assign-D"]'); await page.wait_for_timeout(150)
        await pull(page, pad(st['C']))
        await page.wait_for_selector(f'[data-testid="{t}-reason"]', timeout=20000)
        why = ' '.join(await page.locator(f'[data-testid="{t}-reason"]').all_inner_texts())
        ok(f'{tag}: box over other option refused with "chadh" reason, Save disabled', 'chadh' in why and await page.locator(f'[data-testid="{t}-save"]').is_disabled(), why)
        await page.screenshot(path=f'{SS}/plain_{size}_overlap.jpg', quality=40)
        await page.click(f'[data-testid="{t}-reset"]'); await page.wait_for_timeout(300)
        await no_overflow(page, tag)
        ok(f'{tag}: no API errors / page errors', not bad and not logs, (bad[:4], logs[:3]))
    except Exception as e:
        ok(tag + ' walk', False, (e, bad[:3], logs[:3])); await page.screenshot(path=f'{SS}/plain_{size}_err.jpg', quality=40)
    await br.close()


async def typed(pw, size):
    """CSS check: .answer-options must compute to a single column at this width."""
    tag = 'typed-' + size
    br, page, bad, logs = await open_as(pw, 'student', size)
    try:
        await page.goto(f"{BASE}/results/{F['done_attempt']}?view=solutions"); await page.wait_for_timeout(4000)
        cols = await page.evaluate("() => { const d = document.createElement('div'); d.className = 'answer-options'; d.style.width = '1200px'; for (let i = 0; i < 4; i++) { const c = document.createElement('label'); c.className = 'answer-option'; c.textContent = 'x'; d.appendChild(c); } const host = document.querySelector('main') || document.body; host.appendChild(d); const n = getComputedStyle(d).gridTemplateColumns.split(' ').length; const xs = [...d.children].map(c => Math.round(c.getBoundingClientRect().left)); d.remove(); return [n, xs]; }")
        ok(f'{tag}: .answer-options is one column (typed-text options)', cols[0] == 1 and len(set(cols[1])) == 1, cols)
        n = await page.locator('.answer-options').count()
        print('   real .answer-options on page:', n)
    except Exception as e:
        ok(tag + ' walk', False, e)
    await br.close()


async def main():
    a = sys.argv[1:]
    sizes = [x for x in a if x in SIZES] or ['desk', 'mob']
    want = [x for x in a if x not in SIZES] or ['student', 'results', 'proof', 'typed', 'plain', 'boxfix']
    walks = {'student': student, 'results': results, 'proof': proof, 'typed': typed, 'plain': plain, 'boxfix': boxfix}
    async with async_playwright() as pw:
        for s in sizes:
            for w in want:
                await walks[w](pw, s)
    print('TOTAL', len(R), 'PASS', sum(o for _, o in R), 'FAIL', sum(not o for _, o in R))

asyncio.run(main())
