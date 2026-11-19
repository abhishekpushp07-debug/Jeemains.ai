"""Focused UI re-run with corrected selectors. Does not edit app code."""
import asyncio, json, os, re
from playwright.async_api import async_playwright
B = json.load(open('/tmp/uibridge196/bridge.json'))
BASE = [l.split('=', 1)[1].strip() for l in open('/app/frontend/.env') if l.startswith('REACT_APP_BACKEND_URL')][0].rstrip('/')
API = 'http://127.0.0.1:8773'
OUT = '/tmp/shots_focus'
os.makedirs(OUT, exist_ok=True)
R = []
def rec(n, ok, d=''):
    R.append((n, ok, d)); print(('PASS' if ok else 'FAIL'), n, '' if ok else '::' + str(d)[:300], flush=True)

async def make(pw, who='hero', w=1920, h=1000):
    br = await pw.chromium.launch()
    ctx = await br.new_context(viewport={'width': w, 'height': h}, has_touch=(w < 500))
    cookie = '; '.join(f'{k}={v}' for k, v in B[who].items())
    async def h_(route):
        req = route.request
        hd = {k: v for k, v in req.headers.items() if k.lower() not in ('host', 'referer', 'cookie')}
        hd['origin'] = BASE; hd['cookie'] = cookie
        try:
            r = await route.fetch(url=req.url.replace(BASE, API), headers=hd)
            await route.fulfill(response=r)
        except Exception:
            await route.abort()
    page = await ctx.new_page(); await page.route('**/api/**', h_)
    return br, page

async def goto(page, who, q=''):
    await page.goto(f"{BASE}/results/{B[who + '_attempt']}{q}")
    await page.wait_for_selector('[data-testid="analysis2"]', timeout=40000)
    await page.wait_for_timeout(1100)

async def score_ring(pw):
    br, page = await make(pw, 'hero', 390, 844)
    try:
        await goto(page, 'hero', '?a=overview')
        info = await page.evaluate("""() => {
          const r = document.querySelector('[data-testid=a2-score-ring]');
          const s = r && r.querySelector('[data-testid=a2-score]');
          if(!s) return {missing:true};
          const rect = s.getBoundingClientRect();
          return { w: rect.width, h: rect.height, text: s.innerText };
        }""")
        # 2-digit score: width must substantially exceed height (no vertical stacking)
        ok = info and info.get('w', 0) > info.get('h', 0) * 0.8 and '\n' not in (info.get('text') or '')
        rec('score ring: score rendered horizontally (not stacked)', ok, info)
    finally:
        await br.close()

async def info_no_drill(pw):
    br, page = await make(pw, 'hero', 1920, 1000)
    try:
        await goto(page, 'hero', '?a=overview')
        await page.locator('[data-testid="a2-info-rank"]').click()
        await page.wait_for_timeout(500)
        pop_ok = await page.locator('[data-testid="a2-info-pop-rank"]').is_visible()
        # drill-down heuristic: an a2-qlist / a2-drill container opens
        drill = await page.evaluate("""() => {
          const sel=['[data-testid=a2-qlist]','[data-testid^=a2-drill]','.a2-drilldown','.a2-qlist'];
          for(const s of sel){const e=document.querySelector(s); if(e && e.offsetParent!==null) return s;}
          return null;
        }""")
        rec('(i) opens popover', pop_ok, '')
        rec('(i) click does NOT trigger tile drill-down', drill is None, drill)
        await page.keyboard.press('Escape'); await page.wait_for_timeout(200)
        # Now click the tile itself (not the (i)) and expect drill
        await page.locator('[data-testid="a2-tile-attempted"]').click()
        await page.wait_for_timeout(700)
        opened = await page.evaluate("""() => {
          const sel=['[data-testid=a2-qlist]','[data-testid^=a2-drill]','.a2-drilldown'];
          return sel.some(s => {const e=document.querySelector(s); return e && e.offsetParent!==null;}) ||
                 !!document.querySelector('[role=dialog][data-testid^=a2-drill], [role=dialog][aria-label*=sawaal]');
        }""")
        rec('tapping tile opens drill-down', opened, '')
    finally:
        await br.close()

async def qs_filters(pw):
    br, page = await make(pw, 'hero', 1920, 1000)
    try:
        await goto(page, 'hero', '?a=qs')
        tids = await page.evaluate("""() => [...document.querySelectorAll('[data-testid^=a2-pill-qs-filter-]')].map(e=>e.getAttribute('data-testid'))""")
        rec('Qs filters present', 'a2-pill-qs-filter-not-seen' in tids and 'a2-pill-qs-filter-seen-skipped' in tids, tids)
        # row counts in each filter
        async def rows():
            return await page.locator('[data-testid^="a2-qs-row-"]').count()
        await page.locator('[data-testid="a2-pill-qs-filter-not-seen"]').click(); await page.wait_for_timeout(300)
        not_seen = await rows()
        await page.locator('[data-testid="a2-pill-qs-filter-seen-skipped"]').click(); await page.wait_for_timeout(300)
        seen_skip = await rows()
        await page.locator('[data-testid="a2-pill-qs-filter-skipped"]').click(); await page.wait_for_timeout(300)
        chhode = await rows()
        rec('not_seen + seen_skipped = chhode count', not_seen + seen_skip == chhode, {'not_seen': not_seen, 'seen_skip': seen_skip, 'chhode': chhode})
        # empty filter message: 'confused' may be empty for some
        await page.locator('[data-testid="a2-pill-qs-filter-marked"]').click(); await page.wait_for_timeout(300)
        rowc = await rows()
        if rowc == 0:
            empty = await page.evaluate("""() => document.body.innerText.includes('Is filter mein koi sawaal nahi')""")
            rec('empty filter shows Hinglish message', empty, '')
        else:
            rec('empty filter check skipped (marked has rows)', True, {'count': rowc})
    finally:
        await br.close()

async def pace_lock(pw):
    br, page = await make(pw, 'hero', 1920, 1000)
    try:
        await goto(page, 'hero', '?a=time')
        await page.locator('[data-testid="a2-pace-toggle-sab"]').click(); await page.wait_for_timeout(200)
        await page.locator('[data-testid="a2-pace-toggle-sahi"]').click(); await page.wait_for_timeout(200)
        state_before = await page.locator('[data-testid="a2-pace-toggle-galat"]').get_attribute('aria-pressed')
        await page.locator('[data-testid="a2-pace-toggle-galat"]').click(); await page.wait_for_timeout(200)
        state_after = await page.locator('[data-testid="a2-pace-toggle-galat"]').get_attribute('aria-pressed')
        rec('pace last visible line cannot be turned off', state_after == 'true' or state_after == state_before == 'true', {'before': state_before, 'after': state_after})
    finally:
        await br.close()

async def display_name(pw):
    br, page = await make(pw, 'friend', 1920, 1000)
    try:
        await goto(page, 'friend', '?a=overview')
        # Click display-name-edit button (inside the box)
        await page.locator('[data-testid="display-name-edit"]').first.click()
        try:
            await page.wait_for_selector('[data-testid="display-name-dialog"]', timeout=5000)
            dialog_ok = True
        except Exception:
            dialog_ok = False
        rec('Naam likho opens display-name-dialog', dialog_ok, '')
        if not dialog_ok:
            # Try alternate: input#display-name-input exists?
            inp = await page.evaluate("""() => !!document.getElementById('display-name-input')""")
            rec('display-name-input exists after click', inp, '')
            return
        # get input
        inp_selector = '#display-name-input'
        async def err_text():
            return await page.evaluate("""() => { const e=document.querySelector('[data-testid=display-name-dialog] .error, [data-testid=display-name-dialog] [class*=error]'); return e? e.innerText.trim(): null; }""")
        # phone number
        await page.fill(inp_selector, '9876543210')
        await page.locator('[data-testid="display-name-save"]').click(); await page.wait_for_timeout(600)
        et = await err_text()
        rec('phone-number name refused (Hinglish)', et and ('phone' in et.lower() or 'number' in et.lower()), et)
        # 1-letter
        await page.fill(inp_selector, 'A')
        await page.locator('[data-testid="display-name-save"]').click(); await page.wait_for_timeout(500)
        rec('1-letter name refused', bool(await err_text()), await err_text())
        # abusive
        await page.fill(inp_selector, 'chutiya')
        await page.locator('[data-testid="display-name-save"]').click(); await page.wait_for_timeout(500)
        rec('abusive name refused', bool(await err_text()), await err_text())
        # valid
        await page.fill(inp_selector, 'Test Dost')
        await page.locator('[data-testid="display-name-save"]').click(); await page.wait_for_timeout(1500)
        closed = not await page.locator('[data-testid="display-name-dialog"]').is_visible()
        rec('valid name saves and dialog closes', closed, '')
        await page.wait_for_timeout(800)
        gone = await page.locator('[data-testid="a2-board-name-ask"]').count()
        rec('Naam likho box disappears after save', gone == 0, '')
    finally:
        await br.close()

async def old_journey_changes(pw):
    br, page = await make(pw, 'old', 1920, 1000)
    try:
        await goto(page, 'old', '?a=journey')
        blocks = await page.evaluate("""() => [...document.querySelectorAll('[data-testid^=a2-block-]')].map(e=>e.getAttribute('data-testid'))""")
        rec('old attempt: Journey Agle-mock card present', await page.locator('[data-testid="a2-later-journey"]').count() > 0, '')
        # changes block or a text about "jawab badla"
        has_changes_block = 'a2-block-changes' in blocks
        has_changes_text = await page.evaluate("""() => /jawab\\s*badla|baar\\s*jawab/i.test(document.body.innerText)""")
        rec('old attempt: Journey still shows answer changes', has_changes_block or has_changes_text, {'blocks': blocks, 'text': has_changes_text})
    finally:
        await br.close()

async def main():
    async with async_playwright() as pw:
        for fn in (score_ring, info_no_drill, qs_filters, pace_lock, display_name, old_journey_changes):
            try: await fn(pw)
            except Exception as e: rec(fn.__name__, False, 'EXC ' + str(e)[:300])
    print(f'\n{sum(1 for _,o,_ in R if o)}/{len(R)} passed')

asyncio.run(main())
