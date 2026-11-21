"""TEST-ONLY (iteration 211 T1): desktop ShareGate fires onOpen once when Share is pressed during the countdown; /misfire chapter shadcn Select,
MCQ option text inside buttons, green is-right on correct second try, reopen is blind. Bridge 8773. Run: python tests/ui_student211.py"""
import asyncio, sys
sys.path.insert(0, '/app/backend/tests')
from playwright.async_api import async_playwright
import ui_student217_lib as L

COUNT = """(() => { const k = 'share_gate.%s'; const orig = Storage.prototype.removeItem;
  Storage.prototype.removeItem = function (x) { if (x === k) window.__unlock = (window.__unlock || 0) + 1; return orig.call(this, x); };
  navigator.share = async () => { window.__shared = (window.__shared || 0) + 1; }; navigator.canShare = () => true; })();"""


async def gate_once(pw, delay_ms):
    tag = f'gate-desk-share@{delay_ms}ms'
    br, ctx, page, bad, logs = await L.open_as(pw, 'hero', False)
    await ctx.add_init_script(COUNT % L.AID)
    try:
        await page.goto(L.BASE + '/home'); await page.evaluate(f"localStorage.setItem('share_gate.{L.AID}','1')")
        await page.goto(f'{L.BASE}/results/{L.AID}'); await page.wait_for_selector('[data-testid="share-gate-countdown"]', timeout=30000)
        await page.wait_for_timeout(delay_ms)
        await page.click('[data-testid="share-gate-share"]')
        try:
            await page.wait_for_selector('[data-testid="share-gate"]', state='detached', timeout=10000); opened = True
        except Exception:
            opened = False
        await page.wait_for_timeout(2500)
        n = await page.evaluate('window.__unlock || 0'); sh = await page.evaluate('window.__shared || 0')
        print(tag, 'unlock calls', n, 'share calls', sh, 'url', page.url)
        L.ok(f'{tag}: result opened', opened)
        L.ok(f'{tag}: onOpen fired exactly once', n == 1, n)
        L.ok(f'{tag}: gate not back', not await page.is_visible('[data-testid="share-gate"]'))
        L.ok(f'{tag}: no page errors', not logs, logs)
    finally:
        await br.close()


async def misfire(pw, mobile):
    tag = 'misfire-' + ('mob' if mobile else 'desk')
    br, ctx, page, bad, logs = await L.open_as(pw, 'hero', mobile)
    try:
        await page.goto(L.BASE + '/misfire'); await page.wait_for_selector('[data-testid="misfire-list"]', timeout=30000); await page.wait_for_timeout(1200)
        all_n = await page.locator('[data-testid^="misfire-item-"]').count()
        trig = '[data-testid="misfire-chapter-filter"]'
        L.ok(f'{tag}: chapter Select trigger visible', await page.is_visible(trig))
        L.ok(f'{tag}: trigger is a shadcn button (not native select)', await page.evaluate(f"() => document.querySelector('{trig}').tagName") == 'BUTTON')
        await page.click(trig); await page.wait_for_timeout(300)
        opts = await page.locator('[data-testid^="misfire-chapter-"]').all_text_contents()
        print(tag, 'chapter options', opts)
        L.ok(f'{tag}: options include Saare chapter + chapters', len(opts) >= 3 and 'Saare chapter' in opts[0], opts)
        name = (await page.text_content('[data-testid="misfire-chapter-0"]')).strip()
        want = int(name.rsplit('(', 1)[-1].rstrip(')')) if '(' in name else None
        await page.click('[data-testid="misfire-chapter-0"]', force=True); await page.wait_for_timeout(1500)
        got = await page.locator('[data-testid^="misfire-item-"]').count()
        chap = name.rsplit(' (', 1)[0]
        txt = await page.text_content(trig)
        print(tag, 'chose', name, 'items', got, 'trigger', txt)
        L.ok(f'{tag}: chapter filter narrows to its count', got == min(want or got, 20) and got <= all_n, (got, want, all_n))
        L.ok(f'{tag}: trigger shows chosen chapter', chap in (txt or ''), txt)
        await page.screenshot(path=f'{L.SS}/{tag}-chapter.jpg', quality=40)
        await page.click(trig); await page.wait_for_timeout(300)
        await page.click('[data-testid="misfire-chapter-all"]', force=True); await page.wait_for_timeout(1500)
        back = await page.locator('[data-testid^="misfire-item-"]').count()
        L.ok(f'{tag}: Saare chapter resets list', back == all_n, (back, all_n))
        # option text inside the MCQ button + green is-right after a correct 2nd try
        items = await page.evaluate("() => [...document.querySelectorAll('[data-testid^=\"misfire-item-\"]')].map(e=>e.dataset.testid.slice(13))")
        target = None
        for mid in items:
            if await page.locator(f'[data-testid="misfire-option-{mid}-A"]').count() and not await page.locator(f'[data-testid="misfire-wrong-{mid}"]').count():
                target = mid; break
        L.ok(f'{tag}: MCQ item found', target, items[:3])
        if not target:
            return
        spans = await page.locator(f'[data-testid^="misfire-option-{target}-"] span').all_text_contents()
        print(tag, 'option spans', spans)
        L.ok(f'{tag}: MCQ buttons show typed option text', len(spans) >= 2 and all(s.strip() for s in spans), spans)
        right_opt = None
        for opt in 'ABCD':
            await page.click(f'[data-testid="misfire-option-{target}-{opt}"]'); await page.click(f'[data-testid="misfire-check-{target}"]'); await page.wait_for_timeout(1200)
            if await page.is_visible(f'[data-testid="misfire-right-{target}"]'):
                right_opt = opt; break
            w = await page.text_content(f'[data-testid="misfire-wrong-{target}"]') if await page.is_visible(f'[data-testid="misfire-wrong-{target}"]') else ''
            ans = w.split('Sahi jawab:')[-1].strip()[:1]
            if ans in 'ABCD':
                await page.click(f'[data-testid="misfire-option-{target}-{ans}"]'); await page.click(f'[data-testid="misfire-check-{target}"]'); await page.wait_for_timeout(1200)
                right_opt = ans; break
        L.ok(f'{tag}: right after second try', right_opt and await page.is_visible(f'[data-testid="misfire-right-{target}"]'))
        if right_opt:
            sel = f'[data-testid="misfire-option-{target}-{right_opt}"]'
            cls = await page.get_attribute(sel, 'class'); bg = await page.evaluate(f"() => getComputedStyle(document.querySelector('{sel}')).backgroundColor + ' / ' + getComputedStyle(document.querySelector('{sel}')).borderColor")
            print(tag, 'chosen class', cls, bg)
            L.ok(f'{tag}: chosen option has is-right', 'is-right' in (cls or ''), cls)
            await page.screenshot(path=f'{L.SS}/{tag}-isright.jpg', quality=40)
            if await page.is_visible(f'[data-testid="misfire-done-{target}"]'):
                await page.click(f'[data-testid="misfire-done-{target}"]'); await page.wait_for_timeout(1500)
                await page.click('[data-testid="misfire-tab-fixed"]'); await page.wait_for_timeout(1500)
                await page.click(f'[data-testid="misfire-reopen-{target}"]'); await page.wait_for_timeout(1500)
                await page.click('[data-testid="misfire-tab-open"]'); await page.wait_for_timeout(1500)
                vis = await page.locator(f'[data-testid="misfire-item-{target}"]').count()
                blind = vis and not await page.is_visible(f'[data-testid="misfire-right-{target}"]') and not await page.is_visible(f'[data-testid="misfire-wrong-{target}"]')
                ocls = await page.locator(f'[data-testid^="misfire-option-{target}-"]').evaluate_all('es => es.map(e => e.className)')
                L.ok(f'{tag}: reopened item blind again (no verdict, no pick)', blind and not any('is-' in c for c in ocls), ocls)
        L.ok(f'{tag}: no page errors', not logs, logs); L.ok(f'{tag}: no 4xx/5xx', not bad, bad[:5])
    finally:
        await br.close()


async def main():
    async with async_playwright() as pw:
        await gate_once(pw, 3900)   # thanks timer (900 ms) overlaps the countdown end
        await gate_once(pw, 1000)
        await misfire(pw, False); await misfire(pw, True)
    print('TOTAL', len(L.R), 'PASS', sum(1 for _, x in L.R if x), 'FAIL', sum(1 for _, x in L.R if not x))

asyncio.run(main())
