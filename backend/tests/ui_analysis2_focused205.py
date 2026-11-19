"""Focused UI checks for Analysis 2.0 that the walk script does not cover.
Routes **/api/** to the bridge on 127.0.0.1:8773 with the hero/old/friend cookies.
Prints PASS/FAIL per check. Does not edit app code."""
import asyncio, json, os, re, sys
from playwright.async_api import async_playwright

B = json.load(open('/tmp/uibridge196/bridge.json'))
BASE = [l.split('=', 1)[1].strip() for l in open('/app/frontend/.env') if l.startswith('REACT_APP_BACKEND_URL')][0].rstrip('/')
API = 'http://127.0.0.1:8773'
OUT = '/tmp/shots_focus'
os.makedirs(OUT, exist_ok=True)
R = []
def rec(name, ok, detail=''):
    R.append((name, ok, detail))
    print(('PASS' if ok else 'FAIL'), name, '' if ok else '::' + str(detail)[:200], flush=True)

async def make_page(pw, who='hero', w=1920, h=1000, theme='light'):
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
            await route.fulfill(response=r)
        except Exception:
            await route.abort()
    page = await ctx.new_page()
    page.on('pageerror', lambda e: errors.append('PAGEERR ' + str(e)[:200]))
    await page.route('**/api/**', handler)
    return br, page, errors

async def goto(page, who, q=''):
    await page.goto(f"{BASE}/results/{B[who + '_attempt']}{q}")
    await page.wait_for_selector('[data-testid="analysis2"]', timeout=40000)
    await page.wait_for_timeout(1000)

async def check_score_ring(pw):
    br, page, _ = await make_page(pw, 'hero', 390, 844)
    try:
        await goto(page, 'hero', '?a=overview')
        # score ring — whole visible text must be one visual line (no vertical stacking of digits)
        txt = (await page.locator('[data-testid="a2-score-ring"]').inner_text()).strip()
        rect = await page.locator('[data-testid="a2-score-ring"]').bounding_box()
        # inside ring: look for element containing "61" and measure its width vs line height
        info = await page.evaluate("""() => {
          const r = document.querySelector('[data-testid=a2-score-ring]'); if(!r) return null;
          const walk = (n, out) => { if(n.nodeType===3){ const t=n.textContent.trim(); if(t) out.push({t, parent:n.parentElement}); } else n.childNodes.forEach(c=>walk(c,out)); };
          const out=[]; walk(r, out);
          const big = out.find(x => /\\d+/.test(x.t) && !/\\//.test(x.t));
          if(!big) return {texts: out.map(x=>x.t)};
          const el = big.parent; const rect = el.getBoundingClientRect();
          const cs = getComputedStyle(el);
          return { t: big.t, w: rect.width, h: rect.height, fontSize: cs.fontSize, lineHeight: cs.lineHeight, whiteSpace: cs.whiteSpace };
        }""")
        rec('score ring text has digits', bool(txt) and re.search(r'\d+', txt), txt)
        # horizontal: width should be comfortably >= fontSize*0.6 per digit (e.g. 2 digits -> w > fontSize)
        if info and 't' in info:
            fs = float(re.sub('[^0-9.]', '', info['fontSize']))
            rec('score ring digits on one line (not stacked)', info['w'] >= fs * 0.8, info)
        else:
            rec('score ring digits on one line (not stacked)', False, info)
        await page.screenshot(path=f'{OUT}/score_ring_mobile.jpg', type='jpeg', quality=45, clip={'x':0,'y':0,'width':390,'height':700})
    finally:
        await br.close()

async def check_tiles_fullwidth(pw):
    br, page, _ = await make_page(pw, 'hero', 390, 844)
    try:
        await goto(page, 'hero', '?a=overview')
        data = await page.evaluate("""() => {
          const ids = ['rank','percentile','accuracy','time'];
          const r = {};
          for (const id of ids) {
            const t = document.querySelector(`[data-testid=a2-tile-${id}]`);
            if(!t){ r[id] = null; continue; }
            const parent = t.parentElement; // grid cell
            const pr = parent.getBoundingClientRect();
            const tr = t.getBoundingClientRect();
            r[id] = { tileW: tr.width, parentW: pr.width, ratio: tr.width/pr.width };
          }
          return r;
        }""")
        for k, v in data.items():
            ok = v and v['ratio'] >= 0.95
            rec(f'tile {k} fills grid cell width', ok, v)
    finally:
        await br.close()

async def check_info_stop_propagation(pw):
    br, page, _ = await make_page(pw, 'hero', 1920, 1000)
    try:
        await goto(page, 'hero', '?a=overview')
        # Click (i) on rank tile and ensure drill-down modal did not open
        await page.locator('[data-testid="a2-info-rank"]').click()
        await page.wait_for_timeout(500)
        pop_visible = await page.locator('[data-testid="a2-info-pop-rank"]').is_visible()
        # heuristic for drill-down: look for an opened dialog/modal or question list
        drill = await page.evaluate("""() => {
          const sel = ['[role=dialog]','.a2-drilldown','[data-testid^=a2-drill]','[data-testid=a2-qlist]','.a2-modal'];
          for(const s of sel){ const e=document.querySelector(s); if(e && e.offsetParent!==null) return s; }
          return null;
        }""")
        rec('(i) opens popover', pop_visible, {})
        rec('(i) does NOT trigger tile drill-down', drill is None, {'drill': drill})
        # Escape closes popover
        await page.keyboard.press('Escape')
        await page.wait_for_timeout(300)
        rec('Escape closes popover', not await page.locator('[data-testid="a2-info-pop-rank"]').is_visible(), '')
        # tappable tile: tap 'attempted' should open list
        await page.locator('[data-testid="a2-tile-attempted"]').click()
        await page.wait_for_timeout(600)
        opened = await page.evaluate("""() => !!document.querySelector('[role=dialog], .a2-drilldown, [data-testid=a2-qlist]')""")
        rec('tapping tile opens drill-down', opened, '')
    finally:
        await br.close()

async def check_pace_toggle_last_line(pw):
    br, page, _ = await make_page(pw, 'hero', 1920, 1000)
    try:
        await goto(page, 'hero', '?a=time')
        # all three toggles
        for key in ['sab', 'sahi', 'galat']:
            el = page.locator(f'[data-testid="a2-pace-toggle-{key}"]')
            rec(f'pace toggle {key} exists', await el.count() > 0, '')
        # turn off two, try to turn off the last one
        await page.locator('[data-testid="a2-pace-toggle-sab"]').click()
        await page.wait_for_timeout(200)
        await page.locator('[data-testid="a2-pace-toggle-sahi"]').click()
        await page.wait_for_timeout(200)
        # Now try to click galat (should be refused / stays on)
        before = await page.locator('[data-testid="a2-pace-toggle-galat"]').get_attribute('aria-pressed') or \
                 await page.locator('[data-testid="a2-pace-toggle-galat"]').get_attribute('data-active')
        await page.locator('[data-testid="a2-pace-toggle-galat"]').click()
        await page.wait_for_timeout(200)
        after = await page.locator('[data-testid="a2-pace-toggle-galat"]').get_attribute('aria-pressed') or \
                await page.locator('[data-testid="a2-pace-toggle-galat"]').get_attribute('data-active')
        rec('pace last visible line cannot be turned off', before == after or after in ('true', '1', 'on'), {'before': before, 'after': after})
    finally:
        await br.close()

async def check_qs_counts(pw):
    br, page, _ = await make_page(pw, 'hero', 1920, 1000)
    try:
        await goto(page, 'hero', '?a=qs')
        # find filter pills by data-testid prefix
        filters = await page.evaluate("""() => [...document.querySelectorAll('[data-testid^=a2-qs-filter-]')].map(e => ({id: e.getAttribute('data-testid'), text: e.innerText}))""")
        print('filters', filters[:20])
        # find 'Chhode' count
        txt = await page.locator('[data-testid="analysis2"]').inner_text()
        def nget(key):
            m = re.search(rf'{key}[^0-9]{{0,30}}(\d+)', txt, re.I)
            return int(m.group(1)) if m else None
        chhode = nget('chhode|skipped')
        rec('Qs by Qs page loads', bool(filters), '')
    finally:
        await br.close()

async def check_old_attempt(pw):
    br, page, _ = await make_page(pw, 'old', 1920, 1000)
    try:
        await goto(page, 'old', '?a=quality')
        later_q = await page.locator('[data-testid="a2-later-quality"]').count()
        await goto(page, 'old', '?a=time')
        later_t = await page.locator('[data-testid="a2-later-time"]').count()
        await goto(page, 'old', '?a=journey')
        later_j = await page.locator('[data-testid="a2-later-journey"]').count()
        changes_visible = await page.locator('[data-testid="a2-block-changes"]').count() > 0
        await goto(page, 'old', '?a=potential')
        partial = await page.locator('[data-testid="a2-potential-partial"]').count()
        rec('old attempt: Quality shows Agle mock card', later_q > 0, {})
        rec('old attempt: Time shows Agle mock card', later_t > 0, {})
        rec('old attempt: Journey shows Agle mock card', later_j > 0, {})
        rec('old attempt: Journey still shows answer changes', changes_visible, {})
        rec('old attempt: Potential shows partial note', partial > 0, {})
    finally:
        await br.close()

async def check_display_name(pw):
    br, page, _ = await make_page(pw, 'friend', 1920, 1000)
    try:
        await goto(page, 'friend', '?a=overview')
        ask = page.locator('[data-testid="a2-board-name-ask"]')
        rec('friend sees Naam likho box', await ask.count() > 0, '')
        if await ask.count() > 0:
            await ask.click()
            await page.wait_for_selector('[data-testid="display-name-dialog"]', timeout=5000)
            # phone-number refused
            await page.fill('#display-name-input', '9876543210')
            await page.locator('[data-testid="display-name-save"]').click()
            await page.wait_for_timeout(600)
            err = await page.evaluate("""() => { const e = document.querySelector('[data-testid=display-name-dialog] .error, [data-testid=display-name-dialog] [class*=error]'); return e? e.innerText : null; }""")
            rec('phone-number name refused', err and ('phone' in err.lower() or 'number' in err.lower()), err)
            # 1-letter refused
            await page.fill('#display-name-input', 'A')
            await page.locator('[data-testid="display-name-save"]').click()
            await page.wait_for_timeout(400)
            err2 = await page.evaluate("""() => { const e = document.querySelector('[data-testid=display-name-dialog] .error, [data-testid=display-name-dialog] [class*=error]'); return e? e.innerText : null; }""")
            rec('1-letter name refused', bool(err2), err2)
            # abusive
            await page.fill('#display-name-input', 'chutiya')
            await page.locator('[data-testid="display-name-save"]').click()
            await page.wait_for_timeout(400)
            err3 = await page.evaluate("""() => { const e = document.querySelector('[data-testid=display-name-dialog] .error, [data-testid=display-name-dialog] [class*=error]'); return e? e.innerText : null; }""")
            rec('abusive name refused', bool(err3), err3)
            # valid saves
            await page.fill('#display-name-input', 'Test Dost')
            await page.locator('[data-testid="display-name-save"]').click()
            await page.wait_for_timeout(1200)
            still_dialog = await page.locator('[data-testid="display-name-dialog"]').is_visible()
            rec('valid name saves and closes dialog', not still_dialog, '')
            await page.wait_for_timeout(800)
            # The ask box should no longer appear
            still_ask = await page.locator('[data-testid="a2-board-name-ask"]').count()
            rec('Naam likho box disappears after save', still_ask == 0, '')
    finally:
        await br.close()

async def check_downloads(pw):
    br, page, _ = await make_page(pw, 'hero', 1920, 1000)
    try:
        await goto(page, 'hero', '?a=overview')
        # PDF report
        async with page.expect_download(timeout=60000) as di:
            await page.locator('[data-testid="a2-download-report"]').click()
        d = await di.value
        p = os.path.join(OUT, d.suggested_filename)
        await d.save_as(p)
        head = open(p, 'rb').read(8)
        size = os.path.getsize(p)
        rec('PDF downloads', size > 10000 and head.startswith(b'%PDF-'), {'name': d.suggested_filename, 'size': size})
        rec('PDF filename pattern JEELIVE_*_*.pdf', bool(re.match(r'JEELIVE_.+_.+\.pdf$', d.suggested_filename)), d.suggested_filename)
        # scorecard PNG
        async with page.expect_download(timeout=60000) as di2:
            await page.locator('[data-testid="a2-share-scorecard"]').click()
        d2 = await di2.value
        p2 = os.path.join(OUT, d2.suggested_filename)
        await d2.save_as(p2)
        head2 = open(p2, 'rb').read(8)
        rec('Scorecard downloads as PNG', head2.startswith(b'\x89PNG'), {'name': d2.suggested_filename, 'size': os.path.getsize(p2)})
        # Scan PDF text for phone numbers
        try:
            import subprocess
            txt = subprocess.run(['pdftotext', p, '-'], capture_output=True, text=True, timeout=30).stdout
            phones = re.findall(r'\b[6-9]\d{9}\b', txt)
            rec('PDF contains no phone number', not phones, phones[:3])
            pages = txt.count('\x0c')
            rec('PDF has ~8 pages for hero', 7 <= pages <= 10, {'pages': pages})
            rec('PDF cover contains "Is report mein"', 'Is report mein' in txt, '')
            for phrase in ['Speed-Accuracy', 'Pace curve', 'Aapka raasta', 'Tags ke matlab']:
                rec(f'PDF contains "{phrase}"', phrase in txt, '')
        except FileNotFoundError:
            rec('pdftotext available', False, 'pdftotext not installed')
    finally:
        await br.close()

async def check_advanced_link(pw):
    br, page, _ = await make_page(pw, 'hero', 1920, 1000)
    try:
        await goto(page, 'hero', '?a=overview')
        link = page.locator('[data-testid="advanced-result-analysis-toggle"]')
        rec('Advanced link exists', await link.count() > 0, '')
        if await link.count() > 0:
            t = (await link.inner_text()).strip()
            rec('Advanced link Hinglish copy', 'Advanced' in t and ('60-metric' in t or 'ledger' in t), t)
            await link.click()
            await page.wait_for_timeout(1500)
            opened = await page.evaluate("""() => !!document.querySelector('[data-testid=advanced-result-analysis-panel], .advanced-analysis, [data-testid=old-ledger]') || document.body.innerText.includes('metric')""")
            rec('Advanced link opens old ledger', opened, '')
    finally:
        await br.close()

async def check_dark_fresh_light(pw):
    br = await pw.chromium.launch()
    ctx = await br.new_context(viewport={'width': 1280, 'height': 800})
    cookie = '; '.join(f'{k}={v}' for k, v in B['hero'].items())
    async def handler(route):
        req = route.request
        hd = {k: v for k, v in req.headers.items() if k.lower() not in ('host', 'referer', 'cookie')}
        hd['origin'] = BASE; hd['cookie'] = cookie
        try:
            r = await route.fetch(url=req.url.replace(BASE, API), headers=hd)
            await route.fulfill(response=r)
        except Exception:
            await route.abort()
    page = await ctx.new_page()
    await page.route('**/api/**', handler)
    await page.goto(f"{BASE}/results/{B['hero_attempt']}?a=overview")
    await page.wait_for_selector('[data-testid="analysis2"]', timeout=40000)
    await page.wait_for_timeout(800)
    theme_attr = await page.evaluate("() => document.documentElement.getAttribute('data-theme') || document.documentElement.classList.contains('dark') ? 'dark':'light'")
    rec('fresh browser defaults to light theme', 'dark' not in (theme_attr or '').lower(), theme_attr)
    await br.close()

async def main():
    async with async_playwright() as pw:
        for fn in (check_score_ring, check_tiles_fullwidth, check_info_stop_propagation,
                   check_pace_toggle_last_line, check_qs_counts, check_old_attempt,
                   check_display_name, check_downloads, check_advanced_link, check_dark_fresh_light):
            try:
                await fn(pw)
            except Exception as e:
                rec(fn.__name__, False, 'EXC ' + str(e)[:300])
    passed = sum(1 for _, ok, _ in R if ok)
    print(f'\n{passed}/{len(R)} passed')
    json.dump([{'name': n, 'ok': ok, 'detail': str(d)[:300]} for n, ok, d in R], open('/tmp/shots_focus/focused_results.json', 'w'), indent=2)

asyncio.run(main())
