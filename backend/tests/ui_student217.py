"""TEST-ONLY (iteration 217): student UI via bridge 8773 (analysis_bridge196): desktop/mobile ShareGate, Home Misfire card, /misfire page,
chapter report, Results regression. Run: python tests/ui_student217.py"""
import asyncio, json, os, sys, time
from playwright.async_api import async_playwright

B = json.load(open('/tmp/uibridge196/bridge.json'))
BASE = [l.split('=', 1)[1].strip() for l in open('/app/frontend/.env') if l.startswith('REACT_APP_BACKEND_URL')][0].rstrip('/')
API = 'http://127.0.0.1:8773'
SS = '/app/.screenshots/ui217'; os.makedirs(SS, exist_ok=True)
AID = B['hero_attempt']
R = []
HOVF = "() => { const vw = document.documentElement.clientWidth; const out=[]; for (const e of document.querySelectorAll('body *')) { const b = e.getBoundingClientRect(); if (b.width && b.right > vw + 2) { let s=false; for (let p=e.parentElement;p;p=p.parentElement){ if (getComputedStyle(p).overflowX!=='visible'){s=true;break;} } if(!s) out.push(e.tagName+'.'+String(e.className).slice(0,40)+'#'+(e.dataset.testid||'')); } } return {sw: document.documentElement.scrollWidth, vw, out: out.slice(0,5)}; }"


def ok(name, cond, detail=''):
    R.append((name, bool(cond))); print(('PASS ' if cond else 'FAIL ') + name + ('' if cond else ' :: ' + str(detail)[:500]), flush=True)


async def open_as(pw, role, mobile):
    br = await pw.chromium.launch()
    if mobile:
        ctx = await br.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, device_scale_factor=2)
    else:
        ctx = await br.new_context(viewport={'width': 1920, 'height': 800})
    cookie = '; '.join(f'{k}={v}' for k, v in B[role].items())

    async def handler(route):
        req = route.request
        hd = {k: v for k, v in req.headers.items() if k.lower() not in ('cookie', 'host', 'origin', 'referer', 'content-length')}
        hd['cookie'] = cookie
        try:
            r = await route.fetch(url=req.url.replace(BASE, API), headers=hd)
            rh = {k: v for k, v in r.headers.items() if k.lower() not in ('set-cookie', 'content-encoding', 'content-length')}
            await route.fulfill(status=r.status, headers=rh, body=await r.body())
        except Exception:
            await route.abort()
    await ctx.route('**/api/**', handler)
    page = await ctx.new_page(); bad, logs = [], []
    page.on('response', lambda r: bad.append((r.status, r.url.split('/api')[-1][:120])) if '/api/' in r.url and r.status >= 400 else None)
    page.on('pageerror', lambda e: logs.append(str(e)[:200]))
    return br, ctx, page, bad, logs


async def gate(pw, mobile):
    tag = 'gate-' + ('mob' if mobile else 'desk')
    br, ctx, page, bad, logs = await open_as(pw, 'hero', mobile)
    try:
        await page.goto(BASE + '/home'); await page.evaluate(f"localStorage.setItem('share_gate.{AID}','1')")
        await page.goto(f'{BASE}/results/{AID}')
        await page.wait_for_selector('[data-testid="share-gate"]', timeout=30000)
        title = await page.text_content('[data-testid="share-gate-title"]')
        has_cd = await page.is_visible('[data-testid="share-gate-countdown"]')
        print(tag, 'title', title)
        if not mobile:
            ok(f'{tag}: desktop title', 'taiyaar ho raha hai' in title, title)
            ok(f'{tag}: countdown visible', has_cd)
            c1 = await page.text_content('[data-testid="share-gate-countdown"]') if has_cd else ''
            print(tag, 'countdown', c1)
            ok(f'{tag}: countdown text', 'Result aur analysis' in c1 and 'second mein khulenge' in c1, c1)
            await page.screenshot(path=f'{SS}/{tag}.jpg', quality=40)
            t0 = time.time()
            try:
                await page.wait_for_selector('[data-testid="share-gate"]', state='detached', timeout=9000); dt = time.time() - t0
            except Exception:
                dt = None
            print(tag, 'gate closed after', dt)
            ok(f'{tag}: result opens by itself in ~5 s', dt is not None and 3 <= dt + 0.5 <= 7.5, dt)
            await page.wait_for_timeout(2500)
            flag = await page.evaluate(f"localStorage.getItem('share_gate.{AID}')")
            print(tag, 'flag after', flag, 'url', page.url)
            ids = await page.evaluate("() => [...document.querySelectorAll('[data-testid]')].map(e=>e.dataset.testid).filter(x=>/result|analysis|solution/.test(x)).slice(0,15)")
            print(tag, 'result ids', ids)
            ok(f'{tag}: result/analysis rendered', len(ids) > 3, ids)
            await page.screenshot(path=f'{SS}/{tag}-after.jpg', quality=40)
            await page.reload(); await page.wait_for_timeout(3000)
            ok(f'{tag}: gate not shown again after reload', not await page.is_visible('[data-testid="share-gate"]'))
        else:
            ok(f'{tag}: mobile title unchanged', 'ek share door hai' in title, title)
            ok(f'{tag}: no countdown on mobile', not has_cd)
            ok(f'{tag}: lock note visible', 'ek share ke baad khulenge' in (await page.text_content('.ms-gate-head')))
            await page.wait_for_timeout(7000)
            ok(f'{tag}: still gated after 7 s', await page.is_visible('[data-testid="share-gate"]'))
            o = await page.evaluate(HOVF); ok(f'{tag}: no overflow', o['sw'] <= o['vw'] + 1 and not o['out'], o)
            await page.screenshot(path=f'{SS}/{tag}.jpg', quality=40)
        ok(f'{tag}: no page errors', not logs, logs)
        print(tag, 'bad', bad[:5])
    finally:
        await br.close()


async def misfire(pw, mobile):
    tag = 'misfire-' + ('mob' if mobile else 'desk')
    br, ctx, page, bad, logs = await open_as(pw, 'hero', mobile)
    try:
        await page.goto(BASE + '/home'); await page.wait_for_selector('[data-testid="home-misfire-card"]', timeout=30000)
        order = await page.evaluate("""() => { const q = s => document.querySelector(`[data-testid="${s}"]`); const a=q('exam-home-exam-card-grid'), m=q('home-misfire-card'), f=q('home-for-you');
          const pos=(x,y)=>x&&y?!!(x.compareDocumentPosition(y)&Node.DOCUMENT_POSITION_FOLLOWING):null; const ra=a&&a.getBoundingClientRect(), rm=m.getBoundingClientRect(), rf=f&&f.getBoundingClientRect();
          return {grid_before_card: pos(a,m), card_before_foryou: pos(m,f), y:[ra&&ra.bottom, rm.top, rm.bottom, rf&&rf.top], href: m.getAttribute('href') || (m.querySelector('a')||{}).href}; }""")
        print(tag, 'order', order)
        ok(f'{tag}: card between practice grid and For you', order['grid_before_card'] and order['card_before_foryou'] and order['y'][0] <= order['y'][1] and order['y'][2] <= order['y'][3], order)
        txt = await page.text_content('[data-testid="home-misfire-card"]'); print(tag, 'card text', txt)
        ok(f'{tag}: card text "sawaal dobara solve karne hain"', 'sawaal dobara solve karne hain' in txt, txt)
        chips = await page.locator('[data-testid^="home-misfire-subject-"]').count(); ok(f'{tag}: subject chips', chips >= 1, chips)
        cnt_vis = await page.is_visible('[data-testid="home-misfire-count"]')
        ok(f'{tag}: count chip {"hidden" if mobile else "visible"}', cnt_vis != mobile, cnt_vis)
        if mobile:
            o = await page.evaluate(HOVF); ok(f'{tag}: home no overflow', o['sw'] <= o['vw'] + 1 and not o['out'], o)
        await page.locator('[data-testid="home-misfire-card"]').scroll_into_view_if_needed()
        await page.screenshot(path=f'{SS}/{tag}-home.jpg', quality=40)
        await page.click('[data-testid="home-misfire-card"]'); await page.wait_for_url('**/misfire', timeout=10000)
        await page.wait_for_selector('[data-testid="misfire-list"]', timeout=20000)
        open0 = await page.text_content('[data-testid="misfire-count-open"]'); fixed0 = await page.text_content('[data-testid="misfire-count-fixed"]')
        print(tag, 'counts', open0, fixed0)
        # subject filter
        await page.click('[data-testid="misfire-subject-chemistry"]'); await page.wait_for_timeout(1200)
        subj = await page.locator('[data-testid^="misfire-item-"]').count(); print(tag, 'chemistry items', subj)
        ok(f'{tag}: subject filter narrows list', subj >= 1 and subj < int(''.join(c for c in open0 if c.isdigit()) or 99), subj)
        await page.click('[data-testid="misfire-subject-all"]'); await page.wait_for_timeout(1200)
        ok(f'{tag}: chapter filter present', await page.is_visible('[data-testid="misfire-chapter-filter"]'))
        items = await page.evaluate("() => [...document.querySelectorAll('[data-testid^=\"misfire-item-\"]')].map(e=>e.dataset.testid.slice(13))")
        # pick an mcq item without a try yet
        target = None
        for mid in items:
            if await page.locator(f'[data-testid="misfire-option-{mid}-A"]').count() and not await page.locator(f'[data-testid="misfire-wrong-{mid}"]').count():
                target = mid; break
        ok(f'{tag}: found MCQ item', target, items[:3])
        if target:
            for opt in 'ABCD':
                await page.click(f'[data-testid="misfire-option-{target}-{opt}"]'); await page.click(f'[data-testid="misfire-check-{target}"]'); await page.wait_for_timeout(1200)
                if await page.is_visible(f'[data-testid="misfire-right-{target}"]'):
                    break
                w = await page.text_content(f'[data-testid="misfire-wrong-{target}"]') if await page.is_visible(f'[data-testid="misfire-wrong-{target}"]') else ''
                print(tag, 'wrong', opt, w)
                if w:
                    ok(f'{tag}: wrong shows "Galat. Sahi jawab"', 'Galat' in w and 'Sahi jawab' in w, w)
                    ok(f'{tag}: show solution button', await page.is_visible(f'[data-testid="misfire-show-solution-{target}"]'))
                    ans = w.split('Sahi jawab:')[-1].strip()[:1]
                    if ans in 'ABCD':
                        await page.click(f'[data-testid="misfire-option-{target}-{ans}"]'); await page.click(f'[data-testid="misfire-check-{target}"]'); await page.wait_for_timeout(1200)
                        break
            ok(f'{tag}: right state shown', await page.is_visible(f'[data-testid="misfire-right-{target}"]'))
            await page.screenshot(path=f'{SS}/{tag}-right.jpg', quality=40)
            if await page.is_visible(f'[data-testid="misfire-done-{target}"]'):
                await page.click(f'[data-testid="misfire-done-{target}"]'); await page.wait_for_timeout(1500)
                ok(f'{tag}: item left open list', not await page.locator(f'[data-testid="misfire-item-{target}"]').count())
                open1 = await page.text_content('[data-testid="misfire-count-open"]'); print(tag, 'open after', open1)
                await page.click('[data-testid="misfire-tab-fixed"]'); await page.wait_for_timeout(1500)
                ok(f'{tag}: item in Samajh gaya tab with reopen', await page.is_visible(f'[data-testid="misfire-reopen-{target}"]'))
                await page.click(f'[data-testid="misfire-reopen-{target}"]'); await page.wait_for_timeout(1500)
                ok(f'{tag}: reopen removes from fixed tab', not await page.locator(f'[data-testid="misfire-item-{target}"]').count())
        if mobile:
            await page.click('[data-testid="misfire-tab-open"]'); await page.wait_for_timeout(1000)
            o = await page.evaluate(HOVF); ok(f'{tag}: misfire no overflow', o['sw'] <= o['vw'] + 1 and not o['out'], o)
        # chapter report
        await page.click('[data-testid="misfire-tab-chapters"]'); await page.wait_for_selector('[data-testid="chapter-report"]', timeout=15000); await page.wait_for_timeout(1500)
        subs = await page.locator('[data-testid^="chapter-subject-"]').count(); rows = await page.locator('[data-testid^="chapter-row-"]').all_text_contents()
        print(tag, 'chapter subjects', subs, 'rows', len(rows), rows[:3])
        ok(f'{tag}: chapter report 3 subjects + rows', subs == 3 and len(rows) >= 5, (subs, len(rows)))
        ok(f'{tag}: trend word shown', all(any(w in r for w in ('Behtar', 'Kamzor', 'Waisa hi', 'Ek hi paper')) for r in rows), rows[:3])
        if mobile:
            o = await page.evaluate(HOVF); ok(f'{tag}: chapter report no overflow', o['sw'] <= o['vw'] + 1 and not o['out'], o)
        await page.screenshot(path=f'{SS}/{tag}-chapters.jpg', quality=40)
        ok(f'{tag}: no page errors', not logs, logs); ok(f'{tag}: no 4xx/5xx', not bad, bad[:5])
    finally:
        await br.close()


async def results(pw):
    tag = 'results-desk'
    br, ctx, page, bad, logs = await open_as(pw, 'old', False)
    try:
        await page.goto(f"{BASE}/results/{B['old_attempt']}"); await page.wait_for_timeout(5000)
        ok(f'{tag}: no share gate without flag', not await page.is_visible('[data-testid="share-gate"]'))
        ids = await page.evaluate("() => [...new Set([...document.querySelectorAll('[data-testid]')].map(e=>e.dataset.testid))].filter(x=>/tab/.test(x)).slice(0,20)")
        print(tag, 'tabs', ids)
        for t in [x for x in ids if 'solution' in x or 'analysis' in x][:2]:
            await page.click(f'[data-testid="{t}"]'); await page.wait_for_timeout(1500)
        await page.screenshot(path=f'{SS}/{tag}.jpg', quality=40)
        ok(f'{tag}: no page errors', not logs, logs); print(tag, 'bad', bad[:5])
    finally:
        await br.close()


async def main():
    which = sys.argv[1:] or ['gate', 'misfire', 'results']
    async with async_playwright() as pw:
        if 'gate' in which:
            await gate(pw, False); await gate(pw, True)
        if 'misfire' in which:
            await misfire(pw, False); await misfire(pw, True)
        if 'results' in which:
            await results(pw)
    print('TOTAL', len(R), 'PASS', sum(1 for _, x in R if x), 'FAIL', sum(1 for _, x in R if not x))

if __name__ == '__main__':
    asyncio.run(main())
