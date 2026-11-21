"""TEST-ONLY (iteration 216): independent phone/desktop width check of the student Player and Results/Solutions pictures.
Phone 390x844: stem + option cards span ~full width, cards inside the screen, no page overflow, options stacked (same width as stem),
selection border + tick visible, zoom buttons work, 'Sahi jawab' badge inside the screen and not clipped. Desktop 1920: layout sane.
Routes /api to the disposable bridge (:8772). Run: python tests/ui_phone_width216.py [mob desk]"""
import asyncio, os, sys, json, importlib.util
want = sys.argv[1:] or ['mob', 'desk']
sys.argv = [sys.argv[0], 'none']
spec = importlib.util.spec_from_file_location('v211', os.path.join(os.path.dirname(__file__), 'ui_verify211_lib.py'))
v = importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
from playwright.async_api import async_playwright
SS = '/app/.screenshots/ui216'; os.makedirs(SS, exist_ok=True)
if os.environ.get('PHONE_W'):  # e.g. PHONE_W=360 to check a narrower phone
    v.SIZES['mob'] = (int(os.environ['PHONE_W']), 780)
ok = v.ok

GEO = """(p) => {
  const r = e => { if (!e) return null; const b = e.getBoundingClientRect(); return {x: Math.round(b.left), r: Math.round(b.right), w: Math.round(b.width), y: Math.round(b.top), h: Math.round(b.height)}; };
  const stem = document.querySelector(p.stem);
  const cards = [...document.querySelectorAll(p.cards)].filter(c => c.getBoundingClientRect().width > 0);
  const clipped = el => { let e = el.parentElement; const b = el.getBoundingClientRect(); while (e && e !== document.body) { const s = getComputedStyle(e); if (/(hidden|clip)/.test(s.overflowX + s.overflow)) { const q = e.getBoundingClientRect(); if (b.left < q.left - .5 || b.right > q.right + .5 || b.top < q.top - .5) return e.className; } e = e.parentElement; } return null; };
  return {vw: innerWidth, sw: document.documentElement.scrollWidth, bw: document.body.scrollWidth,
    stem: r(stem), stemImg: r(stem && stem.querySelector('.piece-img')),
    cards: cards.map(c => ({k: c.dataset.testid.slice(-1), ...r(c), cls: c.className, img: r(c.querySelector('.piece-img')), clip: clipped(c),
       tick: r(c.querySelector('.piece-tick')), mark: r(c.querySelector('.piece-mark')), markClip: c.querySelector('.piece-mark') ? clipped(c.querySelector('.piece-mark')) : null,
       bl: getComputedStyle(c).borderLeftWidth}))};
}"""


def check_geo(tag, g, size, want_stem=None):
    vw = g['vw']
    ok(f'{tag}: no horizontal page overflow', g['sw'] <= vw + 1 and g['bw'] <= vw + 1, (g['sw'], g['bw'], vw))
    ok(f'{tag}: question picture present', bool(g['stem']) and bool(g['stemImg']), g['stem'])
    cs = g['cards']
    if not cs:
        return
    ok(f'{tag}: options stacked one per line', all(cs[i + 1]['y'] >= cs[i]['y'] + cs[i]['h'] - 1 for i in range(len(cs) - 1)) and len({c['x'] for c in cs}) == 1, [(c['k'], c['x'], c['y'], c['w']) for c in cs])
    ok(f'{tag}: option cards same width as question box (±4)', all(abs(c['w'] - g['stem']['w']) <= 4 and abs(c['x'] - g['stem']['x']) <= 4 for c in cs), (g['stem'], [(c['x'], c['w']) for c in cs]))
    ok(f'{tag}: cards/borders inside the screen and not clipped', all(c['x'] >= 0 and c['r'] <= vw and not c['clip'] for c in cs), [(c['k'], c['x'], c['r'], c['clip']) for c in cs])
    if want_stem:
        ok(f'{tag}: question box spans almost full width (>= {want_stem}px of {vw})', g['stem']['w'] >= want_stem, g['stem'])


async def player(pw, size):
    tag = f'player-{size}'
    br, page, bad, logs = await v.open_as(pw, 'student', size)
    try:
        await page.goto(f"{v.BASE}/attempts/{v.F['active_attempt']}")
        try:
            await page.wait_for_selector('[data-testid="get-ready-begin"]', timeout=8000); await page.wait_for_timeout(3000)
            await page.click('[data-testid="get-ready-begin"]')
        except Exception:
            pass
        await page.wait_for_selector('[data-testid="player-piece-stem"]', timeout=30000)
        sel = {'stem': '[data-testid="player-piece-stem"]', 'cards': '[data-testid^="player-option-card-"]'}
        for n in range(3):
            await v.wait_pics(page)
            g = await page.evaluate(GEO, sel)
            print(f'   {tag} q{n + 1}', json.dumps({'vw': g['vw'], 'sw': g['sw'], 'stem': g['stem'], 'img': g['stemImg'], 'cards': [(c['k'], c['x'], c['w'], c['img'] and c['img']['w']) for c in g['cards']]}))
            check_geo(f'{tag} q{n + 1}', g, size, 355 if size == 'mob' else None)
            if n == 0 and g['cards']:
                k = g['cards'][1]['k']
                await page.click(f'[data-testid="player-option-card-{k}"]'); await page.wait_for_timeout(500)
                g2 = await page.evaluate(GEO, sel)
                c = [c for c in g2['cards'] if c['k'] == k][0]
                ok(f'{tag}: selected card shows selected border + tick inside screen', 'selected' in c['cls'] and c['tick'] and c['tick']['r'] <= g2['vw'] and c['r'] <= g2['vw'], c)
                await page.screenshot(path=f'{SS}/{tag}_selected.jpg', quality=40)
                z = page.locator('.piece-zoom button')
                print('   zoom buttons:', await z.count(), await z.all_inner_texts())
                if await z.count():
                    before = g2['stemImg']['w']
                    await page.click('[data-testid="piece-zoom-in"]')
                    await page.wait_for_timeout(600)
                    g3 = await page.evaluate(GEO, sel)
                    print('   zoom stem img', before, '->', g3['stemImg'])
                    ok(f'{tag}: zoom-in makes the picture bigger, page still not overflowing', g3['stemImg']['w'] > before and g3['sw'] <= g3['vw'] + 1, (before, g3['stemImg'], g3['sw']))
                    await page.screenshot(path=f'{SS}/{tag}_zoomed.jpg', quality=40)
                    o = await page.evaluate("() => { const f = document.querySelector('[data-testid=\"player-piece-stem\"] .piece-fit'); return f ? [f.scrollWidth, f.clientWidth, getComputedStyle(f).overflowX] : null; }")
                    print('   zoomed piece-fit scroll/client/overflowX', o)
                    await page.click('[data-testid="piece-zoom-out"]')
                    await page.wait_for_timeout(400)
            await page.screenshot(path=f'{SS}/{tag}_q{n + 1}.jpg', quality=40)
            nx = page.locator('[data-testid="player-next"]')
            if not await nx.count() or await nx.is_disabled():
                break
            await nx.click(); await page.wait_for_timeout(700)
        ok(f'{tag}: no API errors / page errors', not bad and not logs, (bad[:3], logs[:3]))
    except Exception as e:
        ok(tag + ' walk', False, (e, bad[:3], logs[:3])); await page.screenshot(path=f'{SS}/{tag}_err.jpg', quality=40)
    await br.close()


async def results(pw, size):
    tag = f'results-{size}'
    br, page, bad, logs = await v.open_as(pw, 'student', size)
    try:
        await page.goto(f"{v.BASE}/results/{v.F['done_attempt']}?view=solutions")
        await page.wait_for_selector('[data-testid^="review-piece-stem-"] .piece-img', timeout=30000)
        await v.wait_pics(page)
        qs = page.locator('.review-question')
        n = await qs.count(); print('   review questions', n)
        marks = 0
        for i in range(min(n, 4)):
            q = qs.nth(i); await q.scroll_into_view_if_needed(); await page.wait_for_timeout(500)
            tid = await q.locator('[data-testid^="review-piece-stem-"]').first.get_attribute('data-testid')
            qid = tid.split('review-piece-stem-')[-1]
            # option cards inside the same review question
            g = await page.evaluate(GEO.replace("document.querySelectorAll(p.cards)", "document.querySelectorAll('.review-question')[p.i].querySelectorAll('[data-testid*=\"-option-card-\"]')"), {'stem': f'[data-testid="{tid}"]', 'cards': '', 'i': i})
            print(f'   {tag} q{i + 1}', json.dumps({'stem': g['stem'], 'img': g['stemImg'], 'cards': [(c['k'], c['x'], c['w'], c['mark'], c['markClip']) for c in g['cards']]}))
            check_geo(f'{tag} q{i + 1}', g, size, 325 if size == 'mob' else None)
            for c in g['cards']:
                if c['mark']:
                    marks += 1
                    ok(f'{tag} q{i + 1}: "Sahi jawab"/key badge inside screen, on the card top edge, not clipped', c['mark']['x'] >= 0 and c['mark']['r'] <= g['vw'] and not c['markClip'] and c['mark']['y'] < c['y'] + 4 and c['mark']['y'] + c['mark']['h'] > c['y'], (c['mark'], c['y'], c['markClip']))
            await q.screenshot(path=f'{SS}/{tag}_q{i + 1}.jpg', quality=40)
        ok(f'{tag}: at least one answer badge checked', marks > 0, marks)
        ok(f'{tag}: no API errors / page errors', not bad and not logs, (bad[:3], logs[:3]))
    except Exception as e:
        ok(tag + ' walk', False, (e, bad[:3], logs[:3])); await page.screenshot(path=f'{SS}/{tag}_err.jpg', quality=40)
    await br.close()


async def main():
    async with async_playwright() as pw:
        for s in want:
            await player(pw, s)
            await results(pw, s)
    print('TOTAL', len(v.R), 'PASS', sum(o for _, o in v.R), 'FAIL', sum(not o for _, o in v.R))

asyncio.run(main())
