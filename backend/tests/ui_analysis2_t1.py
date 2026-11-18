"""TEST-ONLY Analysis 2.0 functional UI test (testing agent). Local Playwright, public preview frontend, /api routed to the isolated
bridge (tests/analysis_bridge196.py must be running). Run: PLAYWRIGHT_BROWSERS_PATH=/pw-browsers python tests/ui_analysis2_t1.py [desktop|mobile|old]
"""
import asyncio, json, os, re, sys
from playwright.async_api import async_playwright

OUT = os.environ.get('BRIDGE_OUT', '/tmp/uibridge196')
B = json.load(open(OUT + '/bridge.json'))
BASE = [line.split('=', 1)[1].strip() for line in open('/app/frontend/.env') if line.startswith('REACT_APP_BACKEND_URL')][0].rstrip('/')
API = 'http://127.0.0.1:' + os.environ.get('BRIDGE_PORT', '8773')
SS = '/app/.screenshots/t1a2'
os.makedirs(SS, exist_ok=True)
ALL = ['overview', 'performance', 'potential', 'quality', 'time', 'difficulty', 'journey', 'qs']
MODE = sys.argv[1] if len(sys.argv) > 1 else 'desktop'
RES = {'pass': 0, 'fail': 0}


def check(name, ok, info=''):
    RES['pass' if ok else 'fail'] += 1
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else f' :: {info}'), flush=True)


async def setup(pw, w, h, who='hero'):
    br = await pw.chromium.launch()
    ctx = await br.new_context(viewport={'width': w, 'height': h}, has_touch=(w < 500), accept_downloads=True)
    cookie = '; '.join(f'{k}={v}' for k, v in B[who].items())
    errors = []
    bodies = {}

    async def handler(route):
        req = route.request
        hd = {k: v for k, v in req.headers.items() if k.lower() not in ('host', 'referer', 'cookie')}
        hd['origin'] = BASE
        hd['cookie'] = cookie
        try:
            r = await route.fetch(url=req.url.replace(BASE, API), headers=hd)
            if r.status >= 400:
                errors.append(f'API {r.status} {req.url[-90:]}')
            await route.fulfill(response=r)
        except Exception as e:
            print('route err', e)
            await route.abort()
    page = await ctx.new_page()
    page.on('pageerror', lambda e: errors.append('PAGEERR ' + str(e)[:200]))
    page.on('console', lambda m: m.type in ('error', 'warning') and ('Warning' in m.text or m.type == 'error') and errors.append(m.text[:240]))
    await page.route('**/api/**', handler)
    return br, page, errors


async def go(page, who, q=''):
    await page.goto(f"{BASE}/results/{B[who + '_attempt']}{q}")
    await page.wait_for_selector('[data-testid="analysis2"]', timeout=30000)
    await page.wait_for_timeout(800)


async def text(page, tid):
    loc = page.locator(f'[data-testid="{tid}"]').first
    return (await loc.inner_text()).strip() if await loc.count() else None


async def overflow(page):
    return await page.evaluate("() => [...document.querySelectorAll('[data-testid=analysis2] *')].filter(e => e.getBoundingClientRect().right > innerWidth + 1 && !e.closest('.a2-scroll,.a2-nav,.a2-pills,.a2-qgrid-wrap')).slice(0,5).map(e => (e.getAttribute('data-testid') || e.className?.baseVal || e.className || e.tagName))")


async def solution_open(page):
    try:
        await page.wait_for_selector('[data-testid="solution-current-question-label"]', timeout=8000)
        return await text(page, 'solution-current-question-label')
    except Exception:
        return None


async def desktop(pw, w=1920, h=800):
    br, page, errors = await setup(pw, w, h)
    try:
        await go(page, 'hero', '?a=overview')
        for t in ['a2-top-bar', 'a2-section-title', 'a2-bottom-bar', 'a2-mode-personal', 'a2-mode-compare'] + ['a2-nav-' + k for k in ALL]:
            check(f'[{w}] visible {t}', await page.locator(f'[data-testid="{t}"]').first.is_visible())
        ov = await page.locator('[data-testid="a2-section-overview"]').inner_text()
        check(f'[{w}] overview score 61/120', '61' in ov and '120' in ov, ov[:300])
        for n in ['17', '7', '6', '14']:
            check(f'[{w}] overview contains {n}', n in ov)
        for t in ['a2-score-ring', 'a2-above', 'a2-distribution', 'a2-qgrid']:
            check(f'[{w}] overview {t}', await page.locator(f'[data-testid="{t}"]').count() > 0)
        print('ABOVE:', await text(page, 'a2-above'))
        tiles = await page.evaluate("() => [...document.querySelectorAll('[data-testid^=a2-tile-]')].map(e=>e.dataset.testid+'='+(e.innerText||'').replace(/\\n/g,' | ').slice(0,60))")
        print('OVERVIEW TILES', tiles[:14])
        await page.screenshot(path=f'{SS}/{w}_overview.jpg', quality=40)
        # nav + URL + section
        for k in ALL:
            await page.click(f'[data-testid="a2-nav-{k}"]')
            try:
                await page.wait_for_selector(f'[data-testid="a2-section-{k}"]', timeout=8000)
                ok = True
            except Exception:
                ok = False
            check(f'[{w}] nav {k} opens section + ?a=', ok and f'a={k}' in page.url, page.url)
            off = await overflow(page)
            check(f'[{w}] {k} no overflow', not off, off)
            await page.screenshot(path=f'{SS}/{w}_personal_{k}.jpg', quality=40)
        # pager
        await page.click('[data-testid="a2-nav-time"]')
        await page.click('[data-testid="a2-next-section"]')
        await page.wait_for_timeout(500)
        check(f'[{w}] next -> difficulty', 'a=difficulty' in page.url, page.url)
        await page.click('[data-testid="a2-prev-section"]')
        await page.click('[data-testid="a2-prev-section"]')
        await page.wait_for_timeout(500)
        check(f'[{w}] prev x2 -> quality', 'a=quality' in page.url, page.url)
        # remembered section
        await go(page, 'hero')
        check(f'[{w}] remembered last section quality', await page.locator('[data-testid="a2-section-quality"]').count() > 0, page.url)
        # quality
        qtext = await page.locator('[data-testid="a2-section-quality"]').inner_text()
        vals = {k: await text(page, f'a2-tile-quality-{k}-value') for k in ['perfect', 'wasted', 'slow_correct', 'costly_overtime', 'confused', 'concept_gap', 'overtime', 'careless']}
        print('QUALITY TILE VALUES', vals)
        for t in ['a2-quality-table', 'a2-speed-map', 'a2-quality-defs']:
            check(f'[{w}] quality {t}', await page.locator(f'[data-testid="{t}"]').count() > 0)
        # potential
        await page.click('[data-testid="a2-nav-potential"]')
        await page.wait_for_selector('[data-testid="a2-section-potential"]')
        pv = {t: await text(page, t) for t in ['a2-potential-current', 'a2-potential-realistic', 'a2-potential-maximum']}
        print('POTENTIAL', pv)
        check(f'[{w}] potential 61/76.4/81.8', '61' in (pv['a2-potential-current'] or '') and '76.4' in (pv['a2-potential-realistic'] or '') and '81.8' in (pv['a2-potential-maximum'] or ''), pv)
        for t in ['a2-potential-waterfall', 'a2-potential-step-careless', 'a2-potential-step-guard', 'a2-potential-step-reinvest', 'a2-guess']:
            check(f'[{w}] potential {t}', await page.locator(f'[data-testid="{t}"]').count() > 0)
        # drill from potential careless
        if await page.locator('[data-testid="a2-potential-questions-careless"]').count():
            await page.click('[data-testid="a2-potential-questions-careless"]')
            await page.wait_for_selector('[data-testid="a2-drill"]', timeout=5000)
            rows = await page.locator('[data-testid^="a2-drill-q-"]').count()
            check(f'[{w}] potential careless drill rows == 2', rows == 2, rows)
            first = await page.locator('[data-testid^="a2-drill-q-"]').first.get_attribute('data-testid')
            await page.locator('[data-testid^="a2-drill-q-"]').first.click()
            lab = await solution_open(page)
            check(f'[{w}] drill row opens solution {first}', lab is not None and first.split('-')[-1] in lab, lab)
            check(f'[{w}] solution insight line visible', await page.locator('[data-testid="solution-insight-line"]').count() > 0)
        else:
            check(f'[{w}] a2-potential-questions-careless present', False)
        # back to analysis via URL deep link compare
        await go(page, 'hero', '?a=time&mode=compare')
        check(f'[{w}] deep link time+compare', await page.locator('[data-testid="a2-section-time"]').count() > 0 and await page.locator('[data-testid="a2-compare-picker"]').count() > 0, page.url)
        await page.screenshot(path=f'{SS}/{w}_compare_time.jpg', quality=40)
        check(f'[{w}] compare pace chart', await page.locator('[data-testid="a2-compare-pace-chart"]').count() > 0)
        # difficulty drill
        await page.click('[data-testid="a2-mode-personal"]')
        await page.click('[data-testid="a2-nav-difficulty"]')
        await page.wait_for_selector('[data-testid="a2-section-difficulty"]')
        dt = await text(page, 'a2-difficulty-table')
        check(f'[{w}] difficulty rows', dt and all(x in dt for x in ['Easy', 'Moderate', 'Tough']), dt)
        print('DIFF TABLE', (dt or '').replace('\n', ' | ')[:400])
        cell = page.locator('[data-testid="a2-difficulty-easy-incorrect"]')
        if await cell.count():
            await cell.click()
            try:
                await page.wait_for_selector('[data-testid="a2-drill"]', timeout=4000)
                check(f'[{w}] easy-incorrect drill', await page.locator('[data-testid^="a2-drill-q-"]').count() >= 1)
                await page.keyboard.press('Escape')
            except Exception as e:
                check(f'[{w}] easy-incorrect drill opens', False, str(e)[:100])
        else:
            print('no a2-difficulty-easy-incorrect cell; ids:', await page.evaluate("() => [...document.querySelectorAll('[data-testid^=a2-difficulty-]')].map(e=>e.dataset.testid)"))
        # journey toggle
        await page.click('[data-testid="a2-nav-journey"]')
        await page.wait_for_selector('[data-testid="a2-section-journey"]')
        before = await page.locator('[data-testid="a2-section-journey"] .a2-visit').first.inner_html() if await page.locator('[data-testid="a2-section-journey"] .a2-visit').count() else ''
        ic1 = await page.locator('[data-testid="a2-section-journey"] .a2-visit svg').count()
        await page.click('[data-testid="a2-journey-tags-toggle"]')
        await page.wait_for_timeout(300)
        ic2 = await page.locator('[data-testid="a2-section-journey"] .a2-visit svg').count()
        await page.click('[data-testid="a2-journey-tags-toggle"]')
        await page.wait_for_timeout(300)
        ic3 = await page.locator('[data-testid="a2-section-journey"] .a2-visit svg').count()
        check(f'[{w}] journey tag toggle hides/shows icons', ic1 > 0 and ic2 < ic1 and ic3 == ic1, [ic1, ic2, ic3])
        check(f'[{w}] journey answer changes', await page.locator('[data-testid="a2-answer-changes"]').count() > 0)
        # qs filters
        await page.click('[data-testid="a2-nav-qs"]')
        await page.wait_for_selector('[data-testid="a2-section-qs"]')
        want = {'wrong': 7, 'skipped': 6, 'careless': 2, 'overtime': 3, 'confused': 1, 'marked': 1, 'changed': 2, 'all': 30}
        for k, n in want.items():
            await page.click(f'[data-testid="a2-pill-qs-filter-{k}"]')
            await page.wait_for_timeout(200)
            c = await page.locator('[data-testid^="a2-qs-row-"]').count()
            check(f'[{w}] qs filter {k} = {n}', c == n, c)
        heads = await page.locator('[data-testid="a2-qs-table"] thead th').all_inner_texts()
        ti = next((i for i, x in enumerate(heads) if x.lower().startswith('topper')), None)
        for qn in (5, 21):
            cells = await page.locator(f'[data-testid="a2-qs-row-{qn}"] td').all_inner_texts()
            check(f'[{w}] Q{qn} topper time is —', ti is not None and cells[ti].strip() == '—', [heads, cells])
        await page.select_option('[data-testid="a2-qs-sort"]', 'time')
        await page.wait_for_timeout(200)
        print('SORT time first row:', (await page.locator('[data-testid^="a2-qs-row-"]').first.inner_text()).replace('\n', ' ')[:120])
        await page.locator('[data-testid="a2-qs-row-12"]').click()
        lab = await solution_open(page)
        check(f'[{w}] qs row 12 opens solution', lab is not None and '12' in lab, lab)
        # solutions filters
        for k in ['careless', 'overtime', 'confused']:
            loc = page.locator(f'[data-testid="results-filter-{k}"]')
            if await loc.count():
                await loc.click()
                await page.wait_for_timeout(500)
                n = await page.locator('[data-testid="results-question-review-item"]').count()
                print(f'solutions filter {k}: {n} items; label', await text(page, 'solution-current-question-label'))
                check(f'[{w}] solutions filter {k} non-empty', n > 0, n)
            else:
                check(f'[{w}] results-filter-{k} present', False)
        # qchip from overview
        await go(page, 'hero', '?a=overview')
        chip = page.locator('[data-testid^="a2-qchip-"]').first
        if await chip.count():
            tid = await chip.get_attribute('data-testid')
            await chip.click()
            lab = await solution_open(page)
            check(f'[{w}] qchip {tid} opens solution', lab is not None and tid.split('-')[-1] in lab, lab)
        # tile drill
        await go(page, 'hero', '?a=performance')
        tbtn = page.locator('button[data-testid^="a2-tile-"]').first
        if await tbtn.count():
            await tbtn.click()
            await page.wait_for_selector('[data-testid="a2-drill"]', timeout=4000)
            print('tile drill title', await text(page, 'a2-drill-title'), await page.locator('[data-testid^="a2-drill-q-"]').count())
            check(f'[{w}] tile drill opens', True)
            await page.keyboard.press('Escape')
        # compare mode switching
        await go(page, 'hero', '?a=performance&mode=compare')
        for tgt in ['topper', 'top10', 'average']:
            await page.click(f'[data-testid="a2-compare-{tgt}"]')
            await page.wait_for_timeout(1500)
            t = await text(page, 'a2-compare') or ''
            check(f'[{w}] compare {tgt} content', len(t) > 50 and await page.locator('[data-testid="a2-compare-subject-table"]').count() > 0, t[:120])
            print(f'COMPARE {tgt}:', t.replace('\n', ' ')[:200])
        for sec, tid in [('quality', 'a2-compare-quality-table'), ('difficulty', 'a2-compare-difficulty-table'), ('time', 'a2-compare-pace-chart')]:
            await page.click(f'[data-testid="a2-nav-{sec}"]')
            await page.wait_for_timeout(1200)
            check(f'[{w}] compare {sec} {tid}', await page.locator(f'[data-testid="{tid}"]').count() > 0)
        await page.click('[data-testid="a2-nav-overview"]')
        await page.wait_for_timeout(1500)
        bc = page.locator('[data-testid^="a2-board-compare-"]')
        check(f'[{w}] leaderboard compare buttons', await bc.count() > 0, await bc.count())
        if await bc.count():
            handle = (await bc.nth(1).get_attribute('data-testid')).replace('a2-board-compare-', '')
            await bc.nth(1).click()
            await page.wait_for_timeout(2000)
            check(f'[{w}] board compare sets vs=user', 'user' in page.url and handle in page.url, page.url)
            await page.click('[data-testid="a2-nav-qs"]')
            await page.wait_for_timeout(1000)
            heads = await page.locator('[data-testid="a2-qs-table"] thead th').all_inner_texts()
            print('QS HEADS IN COMPARE user', heads)
            check(f'[{w}] no other student answer column', not any('jawab' in x.lower() and 'aapka' not in x.lower() and 'sahi' not in x.lower() for x in heads), heads)
        await page.screenshot(path=f'{SS}/{w}_compare_user_qs.jpg', quality=40)
        # report + share
        await go(page, 'hero', '?a=overview')
        async with page.expect_response(lambda r: 'report.pdf' in r.url, timeout=60000) as ri:
            await page.click('[data-testid="a2-download-report"]')
        r = await ri.value
        body = await r.body()
        check(f'[{w}] report pdf', r.status == 200 and body[:5] == b'%PDF-' and 'pdf' in r.headers.get('content-type', ''), [r.status, r.headers.get('content-type'), body[:8]])
        await page.wait_for_timeout(1000)
        async with page.expect_response(lambda r: 'share.png' in r.url, timeout=60000) as ri:
            await page.click('[data-testid="a2-share-scorecard"]')
        r = await ri.value
        body = await r.body()
        check(f'[{w}] share png', r.status == 200 and body[:4] == b'\x89PNG', [r.status, body[:8]])
        await page.wait_for_timeout(1500)
    except Exception as e:
        check(f'[{w}] desktop flow exception', False, str(e)[:400])
        await page.screenshot(path=f'{SS}/{w}_exception.jpg', quality=40)
    print('ERRORS', [e for e in errors][:15])
    await br.close()


async def mobile(pw, w=390, h=844):
    br, page, errors = await setup(pw, w, h)
    try:
        for mode in (['', '&mode=compare'] if os.environ.get('FULL') else []):
            for k in ALL:
                await go(page, 'hero', f'?a={k}{mode}')
                await page.wait_for_timeout(1000)
                off = await overflow(page)
                sw = await page.evaluate('document.documentElement.scrollWidth')
                check(f'[390{mode}] {k} no overflow', not off and sw <= w, [off, sw])
                await page.screenshot(path=f'{SS}/390{mode.replace("&mode=", "_")}_{k}.jpg', quality=40)
        await go(page, 'hero', '?a=qs')
        cards = await page.locator('[data-testid^="a2-qs-card-"]').count()
        vis = await page.locator('[data-testid="a2-qs-table"]').is_visible() if await page.locator('[data-testid="a2-qs-table"]').count() else False
        check('[390] qs phone cards shown, table hidden', cards == 30 and not vis, [cards, vis])
        await page.locator('[data-testid="a2-section-qs"]').scroll_into_view_if_needed()
        await page.mouse.wheel(0, 600)
        await page.wait_for_timeout(500)
        bb = await page.locator('[data-testid="a2-bottom-bar"]').bounding_box()
        await page.screenshot(path=f'{SS}/390_qs_scrolled.jpg', quality=40)
        check('[390] bottom bar in viewport', bb and bb['y'] + bb['height'] <= h + 1 and bb['y'] > h / 2, bb)
        # waterfall labels overlap
        await go(page, 'hero', '?a=potential')
        await page.locator('[data-testid="a2-potential-waterfall"]').scroll_into_view_if_needed()
        await page.wait_for_timeout(1500)
        await page.screenshot(path=f'{SS}/390_waterfall.jpg', quality=40)
        print('WF HTML', (await page.locator('[data-testid="a2-potential-waterfall"]').inner_html())[:300])
        boxes = await page.evaluate("() => [...document.querySelectorAll('[data-testid=a2-potential-waterfall] .recharts-xAxis text, [data-testid=a2-potential-waterfall] .xAxis text')].map(t => {const b=t.getBoundingClientRect(); return [t.textContent, b.left, b.right]})")
        print('WATERFALL TICKS', boxes)
        ovl = any(boxes[i][2] > boxes[i + 1][1] for i in range(len(boxes) - 1))
        check('[390] waterfall x labels do not overlap', boxes and not ovl, boxes)
        # swipe
        await go(page, 'hero', '?a=time')
        st = page.locator('[data-testid="a2-section-title"]')
        await page.locator('[data-testid="a2-section-time"]').scroll_into_view_if_needed()
        await page.wait_for_timeout(300)
        box = await page.locator('[data-testid="a2-section-time"]').bounding_box()
        y = max(box['y'], 0) + 120
        print('SWIPE target', await page.evaluate("([y]) => { const e=document.elementFromPoint(300,y); return e && (e.className||e.tagName) }", [y]))
        await page.evaluate("""([y]) => { const el = document.elementFromPoint(300, y); const mk=(t,x)=>new TouchEvent(t,{bubbles:true,cancelable:true,touches: t==='touchend'?[]:[new Touch({identifier:1,target:el,clientX:x,clientY:y})], changedTouches:[new Touch({identifier:1,target:el,clientX:x,clientY:y})]});
            el.dispatchEvent(mk('touchstart',320)); el.dispatchEvent(mk('touchmove',200)); el.dispatchEvent(mk('touchmove',60)); el.dispatchEvent(mk('touchend',60)); }""", [y])
        await page.wait_for_timeout(700)
        check('[390] swipe left -> difficulty', 'a=difficulty' in page.url, [page.url, await st.inner_text()])
        await page.locator('[data-testid="a2-section-difficulty"]').scroll_into_view_if_needed()
        await page.wait_for_timeout(300)
        b2 = await page.locator('[data-testid="a2-section-difficulty"]').bounding_box()
        y = max(b2['y'], 0) + 260
        print('SWIPE2 target', await page.evaluate("([y]) => { const e=document.elementFromPoint(100,y); return e && (e.className||e.tagName) + ' ' + !!e.closest('.a2-scroll, .a2-pills, .recharts-wrapper, .a2-qgrid') }", [y]))
        await page.evaluate("""([y]) => { const el = document.elementFromPoint(100, y); const mk=(t,x)=>new TouchEvent(t,{bubbles:true,cancelable:true,touches: t==='touchend'?[]:[new Touch({identifier:1,target:el,clientX:x,clientY:y})], changedTouches:[new Touch({identifier:1,target:el,clientX:x,clientY:y})]});
            el.dispatchEvent(mk('touchstart',60)); el.dispatchEvent(mk('touchmove',200)); el.dispatchEvent(mk('touchmove',330)); el.dispatchEvent(mk('touchend',330)); }""", [y])
        await page.wait_for_timeout(700)
        check('[390] swipe right -> time', 'a=time' in page.url, page.url)
        # mobile drill
        await go(page, 'hero', '?a=quality')
        t = page.locator('button[data-testid^="a2-tile-quality-"]').first
        await t.click()
        await page.wait_for_selector('[data-testid="a2-drill"]', timeout=4000)
        dbox = await page.locator('[data-testid="a2-drill"]').bounding_box()
        check('[390] drill dialog fits', dbox and dbox['x'] >= 0 and dbox['x'] + dbox['width'] <= w + 1, dbox)
        await page.screenshot(path=f'{SS}/390_drill.jpg', quality=40)
        await page.locator('[data-testid^="a2-drill-q-"]').first.click()
        lab = await solution_open(page)
        check('[390] drill->solution', lab is not None, lab)
    except Exception as e:
        check('[390] mobile flow exception', False, str(e)[:400])
    print('ERRORS', errors[:15])
    await br.close()


async def old(pw):
    for w, h in [(1920, 800), (390, 844)]:
        br, page, errors = await setup(pw, w, h, 'old')
        try:
            for k in ALL:
                await go(page, 'old', f'?a={k}')
                await page.wait_for_timeout(800)
                locked = await page.locator(f'[data-testid="a2-section-{k}"] [data-testid^="a2-later-"]').count()
                sec = await page.locator(f'[data-testid="a2-section-{k}"]').count()
                exp = k in ('time', 'quality', 'journey')
                check(f'[{w} old] {k} locked={exp}', sec > 0 and (locked > 0) == exp, [sec, locked])
                if k in ('time', 'overview'):
                    await page.screenshot(path=f'{SS}/{w}_old_{k}.jpg', quality=40)
        except Exception as e:
            check(f'[{w} old] exception', False, str(e)[:300])
        print('ERRORS', errors[:10])
        await br.close()


async def main():
    async with async_playwright() as pw:
        if MODE in ('desktop', 'all'):
            await desktop(pw)
        if MODE in ('mobile', 'all'):
            await mobile(pw)
        if MODE in ('old', 'all'):
            await old(pw)
    print(f"\n{RES['pass']} passed, {RES['fail']} failed")

asyncio.run(main())
