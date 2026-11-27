"""TEST-ONLY qa216: Super Admin storage badge + upload-dialog notice via master bridge (:8770). Modes faked by fulfilling /api/admin/storage/health.
Run: python tests/ui_storage_badge_qa216.py"""
import asyncio, json, time
from playwright.async_api import async_playwright

BASE = 'https://rank-predictor-11--5rzs66bc.preview.emergentagent.com'
API = 'http://127.0.0.1:8770'
B = json.load(open('/tmp/uibridge/bridge.json'))
R = []
SS = '/app/.screenshots/qa216'
FAKE = {'mode': None}
HEALTH_CALLS = []


def ok(n, c, d=''):
    R.append((n, bool(c))); print(('PASS ' if c else 'FAIL ') + n + ('' if c else ' :: ' + str(d)[:400]), flush=True)


def fake(mode):
    now = time.time()
    sb_ok = mode in ('supabase', 'slow')
    return {'mode': mode, 'checked_at': now - 5,
            'supabase': {'ok': sb_ok, 'configured': True, 'bucket': 'jeelive-test-bucket', 'write_ms': 300 if mode == 'supabase' else (1400 if sb_ok else 0),
                         'read_ms': 500 if mode == 'supabase' else (1600 if sb_ok else 0), 'error': '' if sb_ok else 'Supabase connection failed: ConnectTimeout', 'resting_until': 0 if sb_ok else now + 30},
            'emergent': {'ok': mode != 'down', 'write_ms': 140, 'read_ms': 80, 'error': '' if mode != 'down' else 'Private storage unavailable (503).'},
            'writes': {'supabase': 12, 'emergent': 3}, 'failovers': 0 if mode == 'supabase' else 2,
            'last_failover': None if mode == 'supabase' else {'at': now - 120, 'reason': 'Supabase did not save the file (503)'}}


async def setup(pw, w, h, role='owner'):
    br = await pw.chromium.launch()
    ctx = await br.new_context(viewport={'width': w, 'height': h})
    await ctx.add_cookies([{'name': k, 'value': v, 'url': BASE} for k, v in B[role].items()])
    async def handler(route):
        req = route.request
        if '/api/admin/storage/health' in req.url:
            HEALTH_CALLS.append((time.time(), req.url.split('/api')[-1]))
            if FAKE['mode']:
                return await route.fulfill(status=200, content_type='application/json', body=json.dumps(fake(FAKE['mode'])))
        hd = {k: v for k, v in req.headers.items() if k.lower() not in ('cookie', 'host', 'origin', 'referer')}
        hd['cookie'] = '; '.join(f"{c['name']}={c['value']}" for c in await ctx.cookies(BASE)); hd['origin'] = BASE
        try:
            r = await route.fetch(url=req.url.replace(BASE, API), headers=hd); await route.fulfill(response=r)
        except Exception as e:
            await route.abort()
    await ctx.route('**/api/**', handler)
    page = await ctx.new_page(); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)[:200]))
    return br, page, errs


async def badge_mode(page, mode, label_expect, tone):
    FAKE['mode'] = mode
    await page.goto(BASE + '/super-admin', wait_until='domcontentloaded')
    await page.wait_for_selector('[data-testid="storage-badge"]', timeout=20000)
    await page.wait_for_function(f"document.querySelector('[data-testid=storage-badge]').classList.contains('{tone}')", timeout=10000)
    lab = await page.inner_text('[data-testid="storage-badge-label"]')
    cls = await page.get_attribute('[data-testid="storage-badge"]', 'class')
    ok(f'[{mode}] badge label "{lab}" ~ expect "{label_expect}"', label_expect.lower() in lab.lower(), lab)
    ok(f'[{mode}] badge tone {tone}', tone in cls.split(), cls)
    await page.click('[data-testid="storage-badge"]')
    await page.wait_for_selector('[data-testid="storage-details"]', timeout=5000)
    txt = await page.inner_text('[data-testid="storage-mode-text"]')
    ok(f'[{mode}] details text', len(txt) > 10, txt); print('   mode text:', txt)
    ok(f'[{mode}] rows', await page.locator('[data-testid="storage-row-supabase"]').count() == 1 and await page.locator('[data-testid="storage-row-emergent"]').count() == 1)
    wr = await page.inner_text('[data-testid="storage-writes"]'); ok(f'[{mode}] writes shown', 'Supabase 12' in wr and 'Emergent 3' in wr, wr)
    lf = await page.locator('[data-testid="storage-last-failover"]').count()
    ok(f'[{mode}] last failover shown iff failover', (lf == 1) == (mode != 'supabase'), lf)
    if mode in ('emergent', 'down'):
        rowt = await page.inner_text('[data-testid="storage-row-supabase"]'); ok(f'[{mode}] supabase error shown', 'ConnectTimeout' in rowt, rowt)
    await page.screenshot(path=f'{SS}_{mode}.jpg', quality=40, full_page=False)
    n0 = len(HEALTH_CALLS)
    await page.click('[data-testid="storage-check-now"]'); await page.wait_for_timeout(800)
    ok(f'[{mode}] check-now refetches fresh=true', len(HEALTH_CALLS) > n0 and 'fresh=true' in HEALTH_CALLS[-1][1], HEALTH_CALLS[-3:])
    await page.keyboard.press('Escape')


async def main():
    async with async_playwright() as pw:
        br, page, errs = await setup(pw, 1920, 800)
        try:
            # real bridge (no fake): expect amber emergent
            FAKE['mode'] = None
            await page.goto(BASE + '/super-admin', wait_until='domcontentloaded')
            await page.wait_for_selector('[data-testid="storage-badge"]', timeout=30000)
            await page.wait_for_timeout(2500)
            lab = await page.inner_text('[data-testid="storage-badge-label"]'); cls = await page.get_attribute('[data-testid="storage-badge"]', 'class')
            ok(f'real bridge badge amber (label "{lab}")', 'warn' in cls.split(), cls)
            for mode, lab, tone in (('supabase', 'Supabase', 'ok'), ('slow', 'slow', 'warn'), ('emergent', 'Emergent backup', 'warn'), ('down', 'Storage band', 'bad')):
                try: await badge_mode(page, mode, lab, tone)
                except Exception as e: ok(f'[{mode}] flow', False, e)
            # polling: count calls over 8 s on a quiet page
            FAKE['mode'] = 'supabase'
            await page.goto(BASE + '/super-admin', wait_until='domcontentloaded'); await page.wait_for_selector('[data-testid="storage-badge"]')
            await page.wait_for_timeout(1500); n0 = len(HEALTH_CALLS); await page.wait_for_timeout(8000)
            ok('no tight polling (<=1 call in 8 s idle)', len(HEALTH_CALLS) - n0 <= 1, len(HEALTH_CALLS) - n0)
            ok('no page errors (desktop)', not errs, errs)
            ov = await page.evaluate('document.documentElement.scrollWidth - window.innerWidth'); ok('desktop no horizontal overflow', ov <= 0, ov)
            # find an upload button
            await page.goto(BASE + '/super-admin/master', wait_until='domcontentloaded'); await page.wait_for_timeout(4000)
            links = await page.evaluate("Array.from(document.querySelectorAll('[data-testid]')).map(e=>e.dataset.testid).slice(0,80)")
            print('testids:', links)
        finally:
            await br.close()
        br, page, errs = await setup(pw, 390, 844)
        try:
            for mode in ('supabase', 'down'):
                FAKE['mode'] = mode
                await page.goto(BASE + '/super-admin', wait_until='domcontentloaded'); await page.wait_for_selector('[data-testid="storage-badge"]', timeout=20000)
                await page.wait_for_timeout(1500)
                ov = await page.evaluate('document.documentElement.scrollWidth - window.innerWidth'); ok(f'mobile [{mode}] no horizontal overflow', ov <= 0, ov)
                bb = await page.locator('[data-testid="storage-badge"]').bounding_box(); ok(f'mobile [{mode}] badge inside viewport', bb and bb['x'] >= 0 and bb['x'] + bb['width'] <= 390, bb)
                await page.click('[data-testid="storage-badge"]'); await page.wait_for_selector('[data-testid="storage-details"]')
                pb = await page.locator('[data-testid="storage-details"]').bounding_box(); ok(f'mobile [{mode}] popover inside viewport', pb and pb['x'] >= 0 and pb['x'] + pb['width'] <= 391, pb)
                await page.screenshot(path=f'{SS}_mob_{mode}.jpg', quality=40, full_page=False); await page.keyboard.press('Escape')
            ok('no page errors (mobile)', not errs, errs)
        finally:
            await br.close()
    print(f'TOTAL {len(R)} PASS {sum(1 for r in R if r[1])} FAIL {sum(1 for r in R if not r[1])}')

asyncio.run(main())
