"""TEST-ONLY iteration 194 UI check via local Playwright: public preview frontend, /api routed to the isolated bridge
(tests/library_bridge194.py on 127.0.0.1:8772). Browser cookies are forwarded as-is so real sign-up/sign-in sessions are used.
Checks postWhenFree (503 retried, 429 not), sign-up / sign-in / forgot PIN / Start at 1920 and 390, guest Home has no /catalog/exams.
Run: PLAYWRIGHT_BROWSERS_PATH=/pw-browsers python tests/ui194.py
"""
import asyncio, json, os, secrets
from playwright.async_api import async_playwright

B = json.load(open(os.environ.get('BRIDGE_OUT', '/tmp/uibridge194') + '/bridge.json'))
BASE = [l.split('=', 1)[1].strip() for l in open('/app/frontend/.env') if l.startswith('REACT_APP_BACKEND_URL')][0].rstrip('/')
API = 'http://127.0.0.1:' + os.environ.get('BRIDGE_PORT', '8772')
SS = '/app/.screenshots/ui194'; os.makedirs(SS, exist_ok=True)
RES = []


def ck(name, ok, detail=''):
    RES.append((name, bool(ok))); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:300]), flush=True)


async def session(pw, w, h):
    br = await pw.chromium.launch()
    ctx = await br.new_context(viewport={'width': w, 'height': h})
    page = await ctx.new_page()
    st = {'log': [], 'inject': {}}  # inject: path suffix -> list of statuses to fake first

    async def handler(route):
        req = route.request
        path = req.url.split('/api', 1)[-1].split('?')[0]
        st['log'].append((req.method, path))
        for suffix, queue in st['inject'].items():
            if path.endswith(suffix) and req.method == 'POST' and queue:
                code = queue.pop(0)
                msg = 'This service is busy. Your saved work is safe; retry shortly.' if code == 503 else 'Too many attempts. Please wait before trying again.'
                return await route.fulfill(status=code, headers={'Retry-After': '1', 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': BASE, 'Access-Control-Allow-Credentials': 'true', 'Access-Control-Expose-Headers': 'Retry-After'},
                                           body=json.dumps({'data': None, 'error': {'code': 'x', 'message': msg}, 'meta': {'api_version': '1'}}))
        hd = {k: v for k, v in req.headers.items() if k.lower() not in ('host', 'referer')}
        hd['origin'] = BASE
        try:
            r = await route.fetch(url=req.url.replace(BASE, API), headers=hd)
            await route.fulfill(response=r)
        except Exception as e:
            print('route err', e); await route.abort()
    await page.route('**/api/**', handler)
    return br, ctx, page, st


def count(st, suffix, method='POST'):
    return sum(1 for m, p in st['log'] if m == method and p.endswith(suffix))


async def flow(pw, w, h):
    tag = f'{w}'
    print(f'\n== {w}x{h}')
    br, ctx, page, st = await session(pw, w, h)
    phone = '95' + f'{secrets.randbelow(10 ** 8):08d}'
    try:
        # guest Home: no /catalog/exams
        await page.goto(BASE + '/'); await page.wait_for_timeout(3500)
        ck(f'{tag} guest Home makes no /catalog/exams call', count(st, '/catalog/exams', 'GET') == 0, st['log'])
        ck(f'{tag} guest Home no refresh call', count(st, '/auth/refresh') == 0, st['log'])
        # sign-up with one injected 503
        st['inject'] = {'/auth/phone/signup': [503]}
        await page.goto(BASE + '/signup'); await page.wait_for_selector('[data-testid="student-login-phone-input"]', timeout=20000)
        await page.fill('[data-testid="student-login-phone-input"]', phone)
        await page.fill('#student-pin-input', '4826'); await page.fill('#student-confirm-pin-input', '4826')
        await page.click('[data-testid="student-login-continue-button"]')
        await page.wait_for_url(lambda u: '/signup' not in u, timeout=20000)
        ck(f'{tag} sign-up succeeds after one 503 (2 requests)', count(st, '/auth/phone/signup') == 2, st['log'][-6:])
        await page.wait_for_timeout(2500)
        ck(f'{tag} signed-in Home calls /catalog/exams', count(st, '/catalog/exams', 'GET') >= 1, [x for x in st['log'] if 'catalog' in x[1]])
        sw = await page.evaluate('[document.documentElement.scrollWidth, window.innerWidth]'); ck(f'{tag} no horizontal overflow on Home', sw[0] <= sw[1], sw)
        await page.screenshot(path=f'{SS}/{tag}_home.jpg', quality=40)
        # Start a test with one injected 503
        st['inject'] = {'/start': [503]}
        await page.goto(f"{BASE}/sets/{B['sets']['pyq']}"); await page.wait_for_selector('[data-testid="set-preflight-start-button"]', timeout=20000)
        await page.click('[data-testid="set-preflight-start-button"]')
        await page.wait_for_url(lambda u: '/attempts/' in u or '/results/' in u, timeout=25000)
        ck(f'{tag} Start succeeds after one 503 (2 requests, same start)', count(st, '/start') == 2, [x for x in st['log'] if x[1].endswith('/start')])
        await page.wait_for_timeout(2000); await page.screenshot(path=f'{SS}/{tag}_attempt.jpg', quality=40)
        # sign out (clear cookies) and sign in with an injected 429 -> not retried, message shown
        await ctx.clear_cookies()
        st['inject'] = {'/auth/phone': [429]}
        await page.goto(BASE + '/login'); await page.wait_for_selector('[data-testid="student-login-phone-input"]', timeout=20000)
        await page.fill('[data-testid="student-login-phone-input"]', phone); await page.fill('#student-pin-input', '4826')
        n0 = count(st, '/auth/phone')
        await page.click('[data-testid="student-login-continue-button"]'); await page.wait_for_timeout(3500)
        err = await page.locator('[data-testid="request-error"]').all_inner_texts()
        ck(f'{tag} 429 on sign-in not retried + message shown', count(st, '/auth/phone') - n0 == 1 and any('Too many attempts' in e for e in err), (count(st, '/auth/phone') - n0, err))
        await page.screenshot(path=f'{SS}/{tag}_429.jpg', quality=40)
        await page.click('[data-testid="student-login-continue-button"]')
        await page.wait_for_url(lambda u: '/login' not in u, timeout=20000)
        ck(f'{tag} sign-in works on second tap', '/login' not in page.url, page.url)
        # forgot PIN
        await ctx.clear_cookies()
        st['inject'] = {'/auth/pin/reset': [503]} if w == 390 else {'/auth/pin/reset': [503, 503, 503, 503]}
        await page.goto(BASE + '/forgot-pin'); await page.wait_for_selector('#forgot-pin-new-input', timeout=20000)
        await page.fill('[data-testid="student-login-phone-input"]', phone); await page.fill('#forgot-pin-new-input', '5937'); await page.fill('#forgot-pin-confirm-input', '5937')
        n0 = count(st, '/auth/pin/reset')
        await page.click('[data-testid="forgot-pin-submit-button"]')
        if w == 390:
            await page.wait_for_url(lambda u: '/forgot-pin' not in u, timeout=25000)
            ck(f'{tag} forgot PIN succeeds after one 503', count(st, '/auth/pin/reset') - n0 == 2, count(st, '/auth/pin/reset') - n0)
        else:
            await page.wait_for_selector('[data-testid="request-error"]', timeout=30000)
            err = await page.locator('[data-testid="request-error"]').all_inner_texts()
            ck(f'{tag} 4 x 503 -> exactly 4 tries then busy message', count(st, '/auth/pin/reset') - n0 == 4 and any('busy' in e for e in err), (count(st, '/auth/pin/reset') - n0, err))
            btn = await page.locator('[data-testid="forgot-pin-submit-button"]').is_enabled()
            ck(f'{tag} button re-enabled after giving up', btn)
            await page.click('[data-testid="forgot-pin-submit-button"]')
            await page.wait_for_url(lambda u: '/forgot-pin' not in u, timeout=20000)
            ck(f'{tag} forgot PIN then succeeds', '/forgot-pin' not in page.url, page.url)
        await ctx.clear_cookies()
        await page.goto(BASE + '/login'); await page.wait_for_selector('[data-testid="student-login-phone-input"]', timeout=20000)
        await page.fill('[data-testid="student-login-phone-input"]', phone); await page.fill('#student-pin-input', '5937')
        await page.click('[data-testid="student-login-continue-button"]'); await page.wait_for_url(lambda u: '/login' not in u, timeout=20000)
        ck(f'{tag} sign-in with new PIN', True)
        sw = await page.evaluate('[document.documentElement.scrollWidth, window.innerWidth]'); ck(f'{tag} no horizontal overflow', sw[0] <= sw[1], sw)
    except Exception as e:
        ck(f'{tag} flow crashed', False, repr(e)); await page.screenshot(path=f'{SS}/{tag}_crash.jpg', quality=40)
        print('last log', st['log'][-10:])
    finally:
        await br.close()


async def main():
    async with async_playwright() as pw:
        await flow(pw, 1920, 1080)
        await flow(pw, 390, 844)
    f = [r for r in RES if not r[1]]
    print(f'TOTAL {len(RES)} PASS {len(RES) - len(f)} FAIL {len(f)}')

asyncio.run(main())
