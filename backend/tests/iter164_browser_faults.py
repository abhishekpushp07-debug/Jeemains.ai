"""TEST-ONLY iteration 164 browser fault-injection (prod build, isolated bridge). MOCKED faults are injected in the
Playwright proxy only: first asset request -> 401 (stale token), a later asset -> 503 (Retry-After) then success on manual retry.
Also real A -> logout -> B switch with isolated synthetic B user created via bridge API (disposable DB only).
Run: python /app/backend/tests/iter164_browser_faults.py
"""
import asyncio, json, secrets
from pathlib import Path
import httpx
import iter164_browser_prod as base  # reuses handler/jar/LOG (module run guarded below)

ORIGIN, LOG, jar = base.ORIGIN, base.LOG, base.jar
OUT = {}
FAULT = {'401_once': True, '503_path': None, '503_left': 0}
real_handler = base.handler


async def handler(route):
    p = route.request.url[len(ORIGIN):] if route.request.url.startswith(ORIGIN) else ''
    if '/asset/' in p and FAULT['401_once']:
        FAULT['401_once'] = False; LOG.append(('GET', p.split('?')[0], 'INJ401', 0))
        return await route.fulfill(status=401, headers={'content-type': 'application/json'}, body='{"error":"expired"}')
    if FAULT['503_path'] and p.split('?')[0].endswith(FAULT['503_path']) and FAULT['503_left'] > 0:
        FAULT['503_left'] -= 1; LOG.append(('GET', p.split('?')[0], 'INJ503', 0))
        return await route.fulfill(status=503, headers={'content-type': 'application/json', 'retry-after': '1'}, body='{"error":"busy"}')
    return await real_handler(route)


def ok(n, c, d=''):
    OUT[n] = {'pass': bool(c), 'detail': d}; print(('PASS ' if c else 'FAIL ') + n, d)


async def main():
    from playwright.async_api import async_playwright
    pb = f'99164{secrets.randbelow(10**5):05d}'; pin = f'{secrets.randbelow(10000):04d}'
    async with httpx.AsyncClient(base_url=base.BRIDGE) as c:  # isolated B user (synthetic, disposable DB)
        r = await c.post('/api/auth/phone/signup', json={'phone': pb, 'pin': pin, 'confirm_pin': pin}, headers={'origin': ORIGIN})
        ok('B signup isolated', r.status_code == 200, r.status_code)
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path='/pw-browsers/chromium_headless_shell-1208/chrome-linux/headless_shell')
        ctx = await b.new_context(viewport={'width': 1920, 'height': 800}); await ctx.route('**/*', handler)
        pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(ORIGIN + '/login', wait_until='networkidle')
        await pg.fill('[data-testid="student-login-phone-input"]', base.CREDS['phone']); await pg.fill('#student-pin-input', base.CREDS['pin'])
        await pg.click('[data-testid="student-login-continue-button"]'); await pg.wait_for_timeout(1200)
        sid = 'jee-main-pyq-2026-04-08-s2'
        await pg.goto(ORIGIN + '/sets/' + sid, wait_until='networkidle')
        await pg.click('[data-testid="preflight-run-check"]'); await pg.wait_for_selector('[data-testid="preflight-check-success"]', timeout=90000)
        await pg.click('[data-testid="preflight-acknowledge"]')
        FAULT['401_once'] = True; mark = len(LOG)
        await pg.click('[data-testid="set-preflight-start-button"]'); await pg.wait_for_url('**/attempts/**', timeout=20000)
        aid = pg.url.split('/attempts/')[1].split('?')[0]
        await pg.locator('.source-image canvas, .source-image img').first.wait_for(timeout=30000); await pg.wait_for_timeout(1200)
        refreshes = [x for x in LOG[mark:] if x[1] == '/api/auth/refresh']
        inj = [x for x in LOG[mark:] if x[2] == 'INJ401']
        ok('401 on image -> exactly one refresh + retry loaded', len(inj) == 1 and len(refreshes) == 1, [x[1:3] for x in LOG[mark:] if 'asset' in x[1] or 'refresh' in x[1]][:6])
        # 503 on Q3 asset (not prefetched yet? Q2 prefetched). Use question 4's first asset path discovered later.
        att = (await base.http.get(f'/api/attempts/{aid}', headers={'origin': ORIGIN, 'cookie': '; '.join(f'{k}={v}' for k, v in jar.items())})).json()  # direct to isolated bridge
        att = att.get('data', att); q4 = att['questions'][3]
        FAULT['503_path'] = f'/questions/{q4["id"]}/asset/question/0'; FAULT['503_left'] = 2
        for _ in range(3):
            await pg.click('[data-testid="player-next"]'); await pg.wait_for_timeout(700)
        await pg.wait_for_timeout(800)
        err = pg.locator('.source-image [data-testid*="retry"], .source-image button:has-text("Retry"), .source-image button:has-text("Try again")').first
        has_err = await err.count() > 0
        opt = pg.locator('[data-testid^="player-option-"]:not([data-testid*="label"]):not([data-testid*="math"])').first
        disabled = (await opt.is_disabled()) if await opt.count() else None
        await pg.screenshot(path=str(base.SHOTS / 'desktop_503_source_error.jpeg'), quality=40, type='jpeg')
        r503 = [x for x in LOG if x[2] == 'INJ503']
        print('503 log', [x[1][-40:]+' '+str(x[2]) for x in LOG if FAULT['503_path'] in x[1]])
        ok('503 shows retryable source error, no refresh triggered', has_err and len(r503) == 2 and len([x for x in LOG if x[1] == '/api/auth/refresh']) == 1, {'err_visible': has_err})
        ok('answers blocked while source failed', disabled is True or (await pg.locator('[data-testid="player-source-options-hint"]').count()) > 0, {'option_disabled': disabled})
        if has_err:
            await err.click(); await pg.wait_for_timeout(1500)
            ok('manual retry loads image', await pg.locator('.source-image canvas, .source-image img').first.count() > 0 and await pg.locator('.source-image [data-testid*="retry"]').count() == 0)
            ok('answers enabled after retry', (await opt.is_disabled()) is False if await opt.count() else False)
        # ---- logout A -> login B, A's attempt must be inaccessible, no stale A image
        a_blobs = await pg.evaluate("[...document.querySelectorAll('img')].map(i=>i.src).filter(s=>s.startsWith('blob:'))")
        await pg.goto(ORIGIN + '/', wait_until='networkidle')
        try:
            await pg.click('[data-testid$="profile-menu"]', timeout=8000); await pg.wait_for_timeout(400); await pg.click('[data-testid="logout"]', timeout=8000); await pg.wait_for_timeout(800)
        except Exception as e:
            await pg.screenshot(path='/tmp/iter164_logout_fail.jpeg', quality=40, type='jpeg'); print('LOGOUT FAIL', str(e)[:300], pg.url); raise
        dlg = pg.locator('[role="alertdialog"] button').first
        if await dlg.count(): await pg.locator('[role="alertdialog"] button:has-text("Keep"), [role="alertdialog"] button').first.click(); await pg.wait_for_timeout(800)
        ok('logout cleared cookies', not jar, list(jar))
        await pg.goto(ORIGIN + '/login', wait_until='networkidle')
        await pg.fill('[data-testid="student-login-phone-input"]', pb); await pg.fill('#student-pin-input', pin)
        await pg.click('[data-testid="student-login-continue-button"]'); await pg.wait_for_timeout(1200)
        m = len(LOG); await pg.goto(ORIGIN + f'/attempts/{aid}', wait_until='networkidle'); await pg.wait_for_timeout(1500)
        cross = [x for x in LOG[m:] if aid in x[1]]
        imgs = await pg.evaluate("[...document.querySelectorAll('img,canvas')].length")
        ok('B cannot read A attempt (404/403) and no A images shown', cross and all(x[2] in (403, 404) for x in cross) and not await pg.locator('.source-image img').count(), cross[:4])
        stale = await pg.evaluate("""async (urls) => { const out=[]; for (const u of urls) { try { await fetch(u); out.push(u); } catch { } } return out; }""", a_blobs)
        ok('A blob URLs revoked after switch', not stale, {'a_blobs': len(a_blobs), 'still_readable': len(stale)})
        ok('no page errors', not errs, errs[:3])
        await b.close()
    Path('/app/test_reports/iter164_browser_faults.json').write_text(json.dumps(OUT, indent=1))

asyncio.run(main())
