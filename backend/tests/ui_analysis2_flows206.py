"""TEST-ONLY: Analysis 2.0 flows in a browser (toggles, 3 seekh, leaderboard search + Compare, empty filter, contrast, leftover English, sticky bar). Needs tests/analysis_bridge196.py running."""
import asyncio, re
from ui_analysis2_walk204 import ALL, async_playwright, go, setup
R = []
def check(name, ok, info=''):
    R.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name, info, flush=True)
EN = re.compile(r'\b(the|and|your|with|for|are|was|this|that|from|have|not|you|will|can|only|shown|never)\b', re.I)
CONTRAST = """() => {
  const lum = c => { const [r, g, b] = c.slice(0, 3).map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
  const parse = s => { const m = s.match(/rgba?\\(([^)]+)\\)/); if (!m) return null; const p = m[1].split(/[, \\/]+/).filter(Boolean).map(Number); return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1]; };
  const bgOf = el => { for (let e = el; e; e = e.parentElement) { const cs = getComputedStyle(e); if (cs.backgroundImage !== 'none') return null; const c = parse(cs.backgroundColor); if (c && c[3] > 0.5) return c; } return null; };
  const out = [];
  for (const el of document.querySelectorAll('[data-testid=analysis2] *')) {
    if (![...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim().length > 1)) continue;
    const r = el.getBoundingClientRect(); if (!r.width || !r.height) continue;
    const cs = getComputedStyle(el); if (cs.visibility === 'hidden' || +cs.opacity < 0.6) continue;
    const fg = parse(cs.color), bg = bgOf(el); if (!fg || !bg) continue;
    const a = lum(fg), b = lum(bg), ratio = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
    if (ratio < 3) out.push(ratio.toFixed(2) + ' ' + String(el.getAttribute('data-testid') || el.className || el.tagName).slice(0, 36) + ' "' + el.textContent.trim().slice(0, 22) + '" fg ' + cs.color + ' bg rgb(' + bg.slice(0, 3).join(',') + ')');
  }
  return [...new Set(out)].slice(0, 8);
}"""
ROWS = '[data-testid="a2-block-leaderboard"] tr[data-testid^="a2-board-row-"]'

async def flows(pw):
    br, page, errors = await setup(pw, 1920, 800)
    await go(page, '?a=quality')
    dots = lambda: page.locator('[data-testid="a2-speed-map"] .recharts-scatter-symbol').count()
    chip = page.locator('[data-testid="a2-speed-map-tag-perfect"]')
    k = int(re.search(r'\((\d+)\)', await chip.inner_text()).group(1))
    n0 = await dots(); await chip.click(); await page.wait_for_timeout(500)
    n1 = await dots(); pressed = await chip.get_attribute('aria-pressed'); await chip.click(); await page.wait_for_timeout(500)
    check('speed map: a tag chip hides its dots and brings them back', n0 > 0 and n0 - n1 == k and await dots() == n0 and pressed == 'false', [n0, n1, k])
    await go(page, '?a=time')
    lines = lambda: page.locator('[data-testid="a2-pace-chart"] path.recharts-line-curve').count()
    a = await lines(); await page.locator('[data-testid="a2-pace-toggle-galat"]').click(); await page.wait_for_timeout(500)
    b = await lines(); await page.locator('[data-testid="a2-pace-toggle-galat"]').click(); await page.wait_for_timeout(500)
    check('pace chart: a line chip hides its line and brings it back', a == 3 and b == 2 and await lines() == 3, [a, b])
    await go(page, '?a=overview')
    vals = ['Easy sawaal pehle round mein', 'Guess tabhi jab 2 option kat jaayein', 'Par ke 2 guna par aage badho']
    for i, v in enumerate(vals): await page.fill(f'[data-testid="a2-learning-input-{i}"]', v)
    await page.locator('[data-testid="a2-learnings-save"]').click(); await page.wait_for_timeout(1500)
    toast = await page.evaluate("[...document.querySelectorAll('[data-sonner-toast]')].map(e => e.innerText).join(' | ')")
    await go(page, '?a=overview')
    back = [await page.input_value(f'[data-testid="a2-learning-input-{i}"]') for i in range(3)]
    check('3 seekh: save, reload, they come back', back == vals and 'save ho gayi' in toast, [toast[:70]])
    box = page.locator('[data-testid="a2-board-search"]')
    await box.fill('arj'); await page.wait_for_timeout(1400)
    check('leaderboard: search by name', await page.locator(ROWS).count() >= 1 and 'Arjun' in await page.locator(ROWS).first.inner_text())
    await box.fill('1'); await page.wait_for_timeout(1400)
    first = await page.locator(ROWS).first.inner_text()
    check('leaderboard: search by Rank', await page.locator(ROWS).count() == 1 and '#1' in first, first[:30].replace('\n', ' '))
    await box.fill('zzqq'); await page.wait_for_timeout(1400)
    check('leaderboard: nothing found message', await page.locator('[data-testid="a2-board-none"]').count() == 1)
    await box.fill(''); await page.wait_for_timeout(1400)
    btn = page.locator('[data-testid^="a2-board-compare-"]').first
    handle = (await btn.get_attribute('data-testid')).split('-')[-1]
    who = (await page.locator(f'[data-testid="a2-board-row-{handle}"] td').nth(1).inner_text()).strip()
    await btn.click(); await page.wait_for_selector('[data-testid="a2-block-compare-head"]', timeout=15000); await page.wait_for_timeout(600)
    head = await page.locator('[data-testid="a2-block-compare-head"]').inner_text()
    check('Compare on a leaderboard row opens "Aap vs <that student>"', handle in page.url and who in head, [who, head.split('\n')[1][:40] if '\n' in head else head[:40]])
    await page.locator('[data-testid="a2-compare-above"]').click(); await page.wait_for_timeout(2500)
    check('"Aapse ek Rank upar" picks the student one Rank above', 'user' in page.url and await page.locator('[data-testid="a2-compare-above"]').get_attribute('aria-pressed') == 'true', page.url.split('?')[1][:70])
    await go(page, '?a=qs')
    levels = await page.locator('[data-testid="a2-qs-level"] option').evaluate_all("els => els.map(e => e.value)")
    pills = await page.evaluate("[...document.querySelectorAll('[data-testid=a2-block-qs] [data-testid^=a2-pill-]')].map(e => e.getAttribute('data-testid'))")
    empty = None
    for lv in levels[1:]:
        await page.select_option('[data-testid="a2-qs-level"]', lv)
        for pid in pills:
            await page.locator(f'[data-testid="{pid}"]').click(); await page.wait_for_timeout(120)
            if await page.locator('[data-testid="a2-qs-empty"]').count():
                empty = (lv, pid, await page.locator('[data-testid="a2-qs-empty"]').inner_text()); break
        if empty: break
    check('Qs by Qs: an empty filter says so', empty and empty[2] == 'Is filter mein koi sawaal nahi.', empty)
    print('ERR', [e for e in errors if 'dream' not in e and '503' not in e][:5], flush=True)
    await br.close()

async def looks(pw):
    for w, h, tag, theme in ((1920, 800, 'd', 'light'), (390, 844, 'm', 'light'), (1920, 800, 'k', 'dark'), (390, 844, 'km', 'dark')):
        br, page, errors = await setup(pw, w, h, theme)
        low, english = [], []
        for key in ALL + ['overview&mode=compare&vs=topper']:
            await go(page, '?a=' + key)
            low += [f'{key[:9]}: {x}' for x in await page.evaluate(CONTRAST)]
            if tag == 'd':
                text = await page.locator('[data-testid="analysis2"]').inner_text()
                english += [f'{key[:9]}: {l.strip()[:90]}' for l in text.split('\n') if len(l.split()) > 3 and len(EN.findall(l)) >= 2]
        check(f'[{tag}] no low-contrast text (ratio under 3) on a solid background', not low, low[:10])
        if tag == 'd': check('[d] no English sentence left in the Analysis tab', not english, sorted(set(english))[:12])
        await go(page, '?a=overview')
        await page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)"); await page.wait_for_timeout(500)
        hit = await page.evaluate("""() => ['a2-next-section', 'advanced-result-analysis-toggle'].map(id => { const el = document.querySelector(`[data-testid="${id}"]`); if (!el) return id + ':missing'; const r = el.getBoundingClientRect(); const top = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); return id + ':' + (r.bottom <= innerHeight && top && (el === top || el.contains(top)) ? 'clear' : 'covered by ' + (top ? (top.getAttribute('data-testid') || top.className || top.tagName) : 'offscreen')); })""")
        check(f'[{tag}] end of page: last buttons are not hidden behind a sticky bar', all(x.endswith(':clear') for x in hit), hit)
        await br.close()

async def main():
    async with async_playwright() as pw:
        await flows(pw)
        await looks(pw)
    print(f'\n{sum(R)}/{len(R)} passed', flush=True)
if __name__ == '__main__':
    asyncio.run(main())
