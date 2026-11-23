"""TEST-ONLY Phase 1 Super Admin UI walk (students block/unblock, machine panel, re-read progress, Hinglish copy, 44px/390px, noindex).
Preview frontend with /api routed to the isolated bridge on 127.0.0.1:8772 (same open_as as ui_cut210.py, copied, not imported).
Run: python tests/ui_phase1_iso222.py
"""
import asyncio, json, os
from playwright.async_api import async_playwright

B = json.load(open('/tmp/uibridge210/bridge.json'))
BASE = [l.split('=', 1)[1].strip() for l in open('/app/frontend/.env') if l.startswith('REACT_APP_BACKEND_URL')][0].rstrip('/')
API = 'http://127.0.0.1:8772'
SS = '/app/.screenshots/ui222'; os.makedirs(SS, exist_ok=True)
F = B['f']
SIZES = {'desk': (1920, 800), 'mob': (390, 844)}
OVERFLOW = "() => { const slides = e => { for (let p = e.parentElement; p; p = p.parentElement) { const o = getComputedStyle(p).overflowX; if (o === 'auto' || o === 'scroll') return true; } return false; }; return [...document.querySelectorAll('*')].filter(e => e.getBoundingClientRect().right > innerWidth + 1 && !slides(e)).slice(0,5).map(e => (e.className && e.className.toString()) || e.tagName); }"
SMALL = """(sels) => { const out = []; for (const s of sels) for (const e of document.querySelectorAll(s)) { const r = e.getBoundingClientRect(); if (r.width === 0 && r.height === 0) continue; if (getComputedStyle(e).display === 'none' || getComputedStyle(e).visibility === 'hidden') continue; if (r.height < 43.5) out.push(s + ' :: ' + (e.dataset.testid || e.textContent.trim().slice(0, 30)) + ' h=' + r.height.toFixed(1)); } return out.slice(0, 12); }"""
TAPS = ['.master-shell .jeelive-button', '[role=dialog] .jeelive-button', '.master-links a', '[data-testid=storage-badge]', '.master-status', '.machine-retry', '.master-check-hit']
CHAPTERS = f"/super-admin/exam/{F['slug']}/{F['chapters']}"
HELD = F['boxed_held'][0]
RESULT = []


def say(name, ok, detail=''):
    RESULT.append((name, bool(ok))); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:600]), flush=True)


async def open_as(pw, role, size):
    br = await pw.chromium.launch()
    ctx = await br.new_context(viewport={'width': SIZES[size][0], 'height': SIZES[size][1]}, has_touch=size == 'mob')
    if role:
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
    page.on('response', lambda r: bad.append((r.status, r.request.method, r.url.split('/api')[-1][:90])) if '/api/' in r.url and r.status >= 400 else None)
    page.on('console', lambda m: logs.append(m.text[:300]) if m.type == 'error' else None)
    page.on('pageerror', lambda e: logs.append('PAGEERROR ' + str(e)[:300]))
    return br, page, bad, logs


async def overflow(page, tag):
    off = await page.evaluate(OVERFLOW); vw = await page.evaluate('document.documentElement.clientWidth')
    sw = await page.evaluate('document.documentElement.scrollWidth')
    say(f'{tag}: no horizontal overflow', not off and sw <= 390, (vw, sw, off))


async def taps(page, tag):
    s = await page.evaluate(SMALL, TAPS)
    say(f'{tag}: tap targets >=44px', not s, s)


async def toast_text(page):
    try:
        await page.wait_for_selector('[data-sonner-toast]', timeout=8000)
        return (await page.locator('[data-sonner-toast]').last.inner_text()).replace('\n', ' ')
    except Exception:
        return ''


async def students(pw, size):
    tag = 'students ' + size
    br, page, bad, logs = await open_as(pw, 'owner', size)
    try:
        await page.goto(BASE + '/super-admin/students'); await page.wait_for_selector('[data-testid=student-directory]', timeout=20000)
        await page.wait_for_timeout(800)
        rows = await page.evaluate("() => [...document.querySelectorAll('[data-testid^=student-row-]')].map(e => [e.dataset.testid.slice(12), e.innerText.replace(/\\n/g,' | ')])")
        print('   rows:', rows)
        ids = {r[1].split(' | ')[0]: r[0] for r in rows}
        say(f'{tag}: 3 students listed', len(rows) == 3 and {'+919128119195', '+919000000001', '+919000000002'} <= set(ids), rows)
        say(f'{tag}: title', await page.title() == 'Students · Super Admin · JEELIVE.AI', await page.title())
        say(f'{tag}: noindex meta', await page.locator('head meta[name=robots][content="noindex, nofollow"]').count() >= 1)
        a, b = ids.get('+919000000001'), ids.get('+919000000002')
        say(f'{tag}: QA Topper name', 'QA Topper' in (await page.inner_text(f'[data-testid=student-name-{a}]')))
        say(f'{tag}: blocked row chip + Chalu karo', await page.locator(f'[data-testid=student-blocked-{b}]').inner_text() == 'Band hai' and 'Chalu karo' in await page.inner_text(f'[data-testid=student-unblock-{b}]'))
        say(f'{tag}: unblocked row Band karo', 'Band karo' in await page.inner_text(f'[data-testid=student-block-{a}]') and await page.locator(f'[data-testid=student-blocked-{a}]').count() == 0)
        body = await page.inner_text('[data-testid=admin-students-page]')
        say(f'{tag}: Hinglish copy', all(w in body for w in ['PIN reset', 'Naam hatao']) and await page.get_attribute('[data-testid=student-search]', 'placeholder') == 'Mobile number se dhoondhein', body[:300])
        if size == 'mob':
            await overflow(page, tag); await taps(page, tag)
        await page.screenshot(path=f'{SS}/students_{size}.png', quality=40, type='jpeg')
        if size == 'desk':
            # Cancel
            await page.click(f'[data-testid=student-block-{a}]'); await page.wait_for_selector(f'[data-testid=student-block-{a}-confirm]')
            dtext = await page.inner_text(f'[data-testid=student-block-{a}-confirm]'); print('   block dialog:', dtext.replace('\n', ' | '))
            await page.click(f'[data-testid=student-block-{a}-confirm-cancel]'); await page.wait_for_timeout(600)
            say(f'{tag}: cancel closes w/o change', await page.locator(f'[data-testid=student-block-{a}-confirm]').count() == 0 and await page.locator(f'[data-testid=student-blocked-{a}]').count() == 0)
            # Block
            await page.click(f'[data-testid=student-block-{a}]'); await page.wait_for_selector(f'[data-testid=student-block-{a}-confirm-save]')
            await page.screenshot(path=f'{SS}/students_block_dialog.png', quality=40, type='jpeg')
            await page.click(f'[data-testid=student-block-{a}-confirm-save]'); t = await toast_text(page); print('   block toast:', t)
            await page.wait_for_selector(f'[data-testid=student-blocked-{a}]', timeout=8000)
            say(f'{tag}: block toast has band', 'band' in t.lower(), t)
            say(f'{tag}: row now blocked + Chalu karo', 'Chalu karo' in await page.inner_text(f'[data-testid=student-unblock-{a}]'))
            await page.wait_for_timeout(4500)
            # Unblock
            await page.click(f'[data-testid=student-unblock-{a}]'); await page.wait_for_selector(f'[data-testid=student-unblock-{a}-confirm-save]')
            await page.click(f'[data-testid=student-unblock-{a}-confirm-save]'); t = await toast_text(page); print('   unblock toast:', t)
            await page.wait_for_selector(f'[data-testid=student-block-{a}]', timeout=8000)
            say(f'{tag}: unblock toast has chalu', 'chalu' in t.lower(), t)
            say(f'{tag}: chip gone', await page.locator(f'[data-testid=student-blocked-{a}]').count() == 0)
            # Search
            await page.fill('[data-testid=student-search]', '9000000002'); await page.wait_for_timeout(1500)
            n = await page.locator('[data-testid^=student-row-]').count()
            say(f'{tag}: search filters by digits', n == 1 and await page.locator(f'[data-testid=student-row-{b}]').count() == 1, n)
            await page.fill('[data-testid=student-search]', '91281'); await page.wait_for_timeout(1500)
            say(f'{tag}: search 91281 -> 1', await page.locator('[data-testid^=student-row-]').count() == 1)
            await page.fill('[data-testid=student-search]', 'abc'); await page.wait_for_timeout(300)
            say(f'{tag}: letters stripped from search', await page.input_value('[data-testid=student-search]') == '')
            await page.fill('[data-testid=student-search]', ''); await page.wait_for_timeout(1500)
            # PIN reset dialog
            pin = page.locator('[data-testid^=owner-reset-]').first
            tid = await pin.get_attribute('data-testid'); await pin.click(); await page.wait_for_timeout(800)
            dlg = page.locator(f'[data-testid={tid}-dialog]')
            if await dlg.count():
                print('   PIN dialog:', (await dlg.inner_text()).replace('\n', ' | ')[:400]); say(f'{tag}: PIN reset dialog opens', True)
                await page.screenshot(path=f'{SS}/pin_dialog.png', quality=40, type='jpeg'); await page.keyboard.press('Escape')
            else:
                say(f'{tag}: PIN reset dialog opens', False, tid)
        say(f'{tag}: no unexpected api errors', not bad, bad)
    except Exception as e:
        say(f'{tag}: exception', False, e)
    finally:
        await br.close()


async def machine(pw, size):
    tag = 'machine ' + size
    br, page, bad, logs = await open_as(pw, 'owner', size)
    try:
        await page.goto(BASE + '/super-admin'); await page.wait_for_selector('[data-testid=storage-badge]', timeout=20000)
        await page.wait_for_selector('[data-testid=machine-attention-dot]', timeout=10000)
        say(f'{tag}: red attention dot', True)
        await page.click('[data-testid=storage-badge]'); await page.wait_for_selector('[data-testid=machine-panel]', timeout=8000)
        g = lambda t: page.inner_text(f'[data-testid={t}]')
        say(f'{tag}: title dhyan dijiye', await g('machine-title') == 'Machine: dhyan dijiye', await g('machine-title'))
        vals = {t: await g(t + '-value') for t in ['machine-cron', 'machine-failed-jobs', 'machine-stuck', 'machine-failed', 'machine-disk']}
        print('   machine values:', vals)
        say(f'{tag}: failed jobs 1 · PDF padhna 1', vals['machine-failed-jobs'] == '1 · PDF padhna 1', vals)
        say(f'{tag}: stuck 1 / failed 1', vals['machine-stuck'] == '1' and vals['machine-failed'] == '1', vals)
        say(f'{tag}: book list rows', await page.locator('[data-testid=machine-stuck-qa-stuck-book]').count() == 1 and await page.locator('[data-testid=machine-failed-qa-failed-book]').count() == 1)
        print('   book list:', (await g('machine-book-list')).replace('\n', ' | '))
        if size == 'mob':
            await overflow(page, tag); await taps(page, tag)
            box = await page.locator('[data-testid=storage-details]').bounding_box(); print('   popover box', box)
            say(f'{tag}: popover inside viewport', box and box['x'] >= 0 and box['x'] + box['width'] <= 391, box)
        await page.screenshot(path=f'{SS}/machine_{size}.png', quality=40, type='jpeg')
        if size == 'desk':
            reqs = []
            page.on('request', lambda r: reqs.append((r.method, r.url.split('/api')[-1], r.post_data)) if '/control' in r.url or '/machine/status' in r.url else None)
            btn = page.locator('[data-testid=machine-retry-qa-failed-book]')
            await btn.click(); await page.wait_for_timeout(60)
            dis = await btn.is_disabled() if await btn.count() else None
            t = await toast_text(page); print('   retry toast:', t, '| disabled while busy:', dis)
            await page.wait_for_timeout(1500)
            ctl = [r for r in reqs if '/control' in r[1]]
            say(f'{tag}: retry POST control action=retry', ctl and ctl[0][0] == 'POST' and '"retry"' in (ctl[0][2] or ''), reqs)
            say(f'{tag}: retry toast shown', bool(t), t)
            say(f'{tag}: panel reloaded after retry', any('/machine/status' in r[1] for r in reqs), reqs)
            print('   after retry list:', (await page.inner_text('[data-testid=machine-panel]')).replace('\n', ' | ')[:500])
            reqs.clear(); await page.click('[data-testid=storage-check-now]'); await page.wait_for_timeout(1500)
            print('   check-now reqs:', reqs)
            say(f'{tag}: check-now reloads machine status', any('/machine/status' in r[1] for r in reqs), reqs)
            # stuck retry too
            if await page.locator('[data-testid=machine-retry-qa-stuck-book]').count():
                await page.click('[data-testid=machine-retry-qa-stuck-book]'); t = await toast_text(page); print('   stuck retry toast:', t)
        say(f'{tag}: api errors (info)', True); print('   bad:', bad)
    except Exception as e:
        say(f'{tag}: exception', False, e)
    finally:
        await br.close()


async def reread(pw, size):
    tag = 'chapter type ' + size
    br, page, bad, logs = await open_as(pw, 'owner', size)
    try:
        await page.goto(BASE + CHAPTERS); await page.wait_for_selector('[data-testid=mock-list]', timeout=25000); await page.wait_for_timeout(1000)
        p = await page.inner_text(f'[data-testid=type-upload-progress-{HELD}]')
        say(f'{tag}: upload progress text', 'dobara padhi ja rahi hai · 12 / 38 page' in p, p)
        rr = await page.evaluate("() => [...document.querySelectorAll('[data-testid^=mock-rereading-]')].map(e => [e.dataset.testid.slice(15), e.innerText])")
        print('   rereading mocks:', rr)
        say(f'{tag}: mocks show rereading 12/38', rr and all('dobara padhi ja rahi hai · 12/38 page' in x[1] for x in rr), rr)
        for mid, _ in rr[:3]:
            row = f'[data-testid=mock-row-{mid}]'
            sw = page.locator(f'[data-testid=mock-live-switch-{mid}]')
            say(f'{tag}: live switch disabled {mid[:8]}', await sw.is_disabled())
            acts = await page.evaluate("(s) => [...document.querySelector(s).querySelectorAll('[data-testid]')].map(e => e.dataset.testid).filter(t => /mock-(fix|edit|edit-questions|try)-|try-student/.test(t))", row)
            txt = await page.inner_text(row)
            say(f'{tag}: no Fix/Edit/Try {mid[:8]}', not acts and 'Student ki tarah try karo' not in txt, acts)
            if size == 'desk' and mid == rr[0][0]:
                await page.click(f'[data-testid=mock-status-{mid}]'); await page.wait_for_timeout(400)
                l = await page.get_attribute(f'[data-testid=mock-make-live-{mid}]', 'data-disabled')
                s = await page.get_attribute(f'[data-testid=mock-schedule-{mid}]', 'data-disabled')
                say(f'{tag}: menu Live/Schedule disabled', l is not None and s is not None, (l, s))
                await page.keyboard.press('Escape'); await page.wait_for_timeout(300)
        title = await page.title(); print('   title:', title)
        if size == 'mob':
            await overflow(page, tag); await taps(page, tag)
            # disabled look
            op = await page.evaluate("() => { const e = document.querySelector('[data-testid^=mock-live-switch-][disabled]'); return e ? getComputedStyle(e).opacity : null; }")
            say(f'{tag}: disabled switch dimmed', op is not None and float(op) < 1, op)
        await page.screenshot(path=f'{SS}/chapters_{size}.png', quality=40, type='jpeg')
        if size == 'desk':
            body = await page.inner_text('body'); print('   page text sample:', body.replace('\n', ' | ')[:900])
            # Upload dialog
            up = page.locator('[data-testid*=upload-pdf], [data-testid=type-upload-button], button:has-text("Upload PDF")').first
            await up.click(); await page.wait_for_selector('[data-testid=upload-dialog]', timeout=6000)
            ut = await page.inner_text('[data-testid=upload-dialog]'); print('   upload dialog:', ut.replace('\n', ' | '))
            say(f'{tag}: upload dialog title + 100 MB', 'mein PDF upload karo' in ut and '100 MB' in ut, ut[:300])
            await taps(page, tag + ' upload dialog')
            await page.screenshot(path=f'{SS}/upload_dialog.png', quality=40, type='jpeg'); await page.keyboard.press('Escape'); await page.wait_for_timeout(500)
            wr = page.locator('[data-testid*=write-button], [data-testid=type-write], button:has-text("Write")').first
            await wr.click(); await page.wait_for_selector('[data-testid=write-dialog]', timeout=6000)
            print('   write dialog:', (await page.inner_text('[data-testid=write-dialog]')).replace('\n', ' | ')); say(f'{tag}: write dialog opens', True)
            await page.keyboard.press('Escape'); await page.wait_for_timeout(500)
            # Schedule dialog from a ready (non-rereading, not to_fix) mock
            ids = await page.evaluate("() => [...document.querySelectorAll('[data-testid^=mock-make-live-], [data-testid^=mock-status-]')].map(e => e.dataset.testid.replace('mock-status-',''))")
            opened = False
            for mid in ids:
                if any(mid == x[0] for x in rr): continue
                await page.click(f'[data-testid=mock-status-{mid}]'); await page.wait_for_timeout(300)
                if await page.get_attribute(f'[data-testid=mock-schedule-{mid}]', 'data-disabled') is None:
                    await page.click(f'[data-testid=mock-schedule-{mid}]', force=True); await page.wait_for_selector('[data-testid=schedule-dialog]', timeout=5000)
                    print('   schedule dialog:', (await page.inner_text('[data-testid=schedule-dialog]')).replace('\n', ' | '))
                    await page.screenshot(path=f'{SS}/schedule_dialog.png', quality=40, type='jpeg')
                    await page.keyboard.press('Escape'); opened = True; break
                await page.keyboard.press('Escape'); await page.wait_for_timeout(200)
            say(f'{tag}: schedule dialog opens from ready mock', opened)
        print('   bad:', bad)
    except Exception as e:
        say(f'{tag}: exception', False, e)
    finally:
        await br.close()


async def screens(pw, size):
    tag = 'screens ' + size
    br, page, bad, logs = await open_as(pw, 'owner', size)
    try:
        await page.goto(BASE + '/super-admin'); await page.wait_for_selector('.master-shell', timeout=20000); await page.wait_for_timeout(2000)
        t = await page.inner_text('.master-shell'); print('   home text:', t.replace('\n', ' | ')[:1200])
        say(f'{tag}: home Hinglish words', all(w in t for w in ['Aaj', 'Naya exam']), t[:300])
        print('   home has "mock fix karne hain":', 'mock fix karne hain' in t, '| "Live ke liye taiyaar":', 'Live ke liye taiyaar' in t)
        say(f'{tag}: master rereading chip', await page.locator(f'[data-testid=master-rereading-{HELD}]').count() == 1)
        say(f'{tag}: noindex on /super-admin', await page.locator('head meta[name=robots][content="noindex, nofollow"]').count() >= 1)
        if size == 'mob':
            await overflow(page, tag + ' home'); await taps(page, tag + ' home')
        await page.screenshot(path=f'{SS}/home_{size}.png', quality=40, type='jpeg')
        for path, words, name in [(f"/super-admin/exam/{F['slug']}", ['Mock type jodo', 'Student ki tarah dekho'], 'exam'),
                                  ('/super-admin/library', ['Tests ka recycle bin', 'Sab ZIP mein download karo'], 'library'),
                                  ('/super-admin/team', ['Review access do'], 'team'), ('/super-admin/fix', [], 'fix')]:
            await page.goto(BASE + path); await page.wait_for_selector('.master-shell', timeout=20000); await page.wait_for_timeout(2500)
            t = await page.inner_text('.master-shell'); print(f'   {name} text:', t.replace('\n', ' | ')[:900])
            say(f'{tag}: {name} copy', all(w in t for w in words), [w for w in words if w not in t])
            if name == 'fix':
                say(f'{tag}: fix-rereading-note', await page.locator('[data-testid=fix-rereading-note]').count() == 1)
                link = page.locator('a[href*="/super-admin/fix/"]').first
                if size == 'desk' and await link.count():
                    await link.click(); await page.wait_for_timeout(3000); print('   fix page title:', await page.title(), page.url)
                    say(f'{tag}: FixMock title', await page.title() == 'Fix · Super Admin · JEELIVE.AI', await page.title())
            if size == 'mob' and name in ('library', 'team'):
                await overflow(page, f'{tag} {name}'); await taps(page, f'{tag} {name}')
            if name in ('library', 'team'):
                await page.screenshot(path=f'{SS}/{name}_{size}.png', quality=40, type='jpeg')
        if size == 'mob':
            await page.goto(BASE + CHAPTERS); await page.wait_for_selector('[data-testid=mock-list]', timeout=20000)
            # disabled buttons not clickable
            d = await page.evaluate("() => [...document.querySelectorAll('.master-shell button[disabled]')].slice(0,5).map(e => [e.dataset.testid, getComputedStyle(e).opacity, getComputedStyle(e).pointerEvents])")
            print('   disabled buttons:', d)
        print('   bad:', bad, 'logs:', logs[:5])
    except Exception as e:
        say(f'{tag}: exception', False, e)
    finally:
        await br.close()


async def public(pw):
    br, page, bad, logs = await open_as(pw, None, 'desk')
    try:
        for p in ['/login', '/owner-login', '/signup', '/']:
            await page.goto(BASE + p); await page.wait_for_timeout(2500)
            n = await page.locator('head meta[name=robots][data-testid=robots-noindex]').count()
            say(f'noindex {p}', n == 0 if p == '/' else n >= 1, n)
            if p == '/owner-login':
                say('owner-login title', await page.title() == 'Sign in · Super Admin · JEELIVE.AI', await page.title())
        r = await page.goto(BASE + '/robots.txt'); txt = await page.inner_text('body')
        say('robots.txt disallows', all(f'Disallow: {x}' in txt for x in ['/super-admin', '/studio', '/owner-login', '/login', '/signup', '/forgot-pin']) and 'text/plain' in (r.headers.get('content-type') or ''), (r.headers.get('content-type'), txt[:300]))
    finally:
        await br.close()


async def reviewer(pw):
    br, page, bad, logs = await open_as(pw, 'reviewer', 'desk')
    try:
        await page.goto(BASE + '/super-admin'); await page.wait_for_timeout(4000)
        t = await page.inner_text('body'); print('   reviewer home:', t.replace('\n', ' | ')[:600])
        say('reviewer home copy', 'Fix karne wali cheezein' in t and 'Reviewer: fix karne wale mock aur students ki reports.' in t, t[:300])
        say('reviewer no storage badge / machine', await page.locator('[data-testid=storage-badge]').count() == 0 and await page.locator('[data-testid=machine-panel]').count() == 0)
        await page.screenshot(path=f'{SS}/reviewer_home.png', quality=40, type='jpeg')
        await page.goto(BASE + '/super-admin/students'); await page.wait_for_timeout(3500)
        say('reviewer /students redirects', page.url.rstrip('/').endswith('/super-admin'), page.url)
    finally:
        await br.close()


async def main():
    async with async_playwright() as pw:
        for f in [lambda: students(pw, 'desk'), lambda: students(pw, 'mob'), lambda: machine(pw, 'mob'), lambda: machine(pw, 'desk'),
                  lambda: reread(pw, 'desk'), lambda: reread(pw, 'mob'), lambda: screens(pw, 'desk'), lambda: screens(pw, 'mob'),
                  lambda: public(pw), lambda: reviewer(pw)]:
            await f()
    print(f"\nTOTAL {sum(o for _, o in RESULT)}/{len(RESULT)}"); [print('  FAILED', n) for n, o in RESULT if not o]

if __name__ == '__main__':
    asyncio.run(main())
