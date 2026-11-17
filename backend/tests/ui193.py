"""TEST-ONLY iteration 193 UI check via local Playwright against the public preview frontend, with /api routed to the
isolated bridge (tests/override_bridge193.py on 127.0.0.1:8771). Run: python tests/ui193.py
"""
import asyncio, json, os
from playwright.async_api import async_playwright

B = json.load(open('/tmp/uibridge193/bridge.json'))
BASE = [l.split('=', 1)[1].strip() for l in open('/app/frontend/.env') if l.startswith('REACT_APP_BACKEND_URL')][0].rstrip('/')
API = 'http://127.0.0.1:' + os.environ.get('BRIDGE_PORT', '8771')
SS = '/app/.screenshots/ui193'; os.makedirs(SS, exist_ok=True)


def ck(role): return '; '.join(f'{k}={v}' for k, v in B[role].items())


async def ctx_for(pw, role, w, h):
    br = await pw.chromium.launch()
    page = await br.new_page(viewport={'width': w, 'height': h})
    bad = []
    async def handler(route):
        req = route.request
        hd = {k: v for k, v in req.headers.items() if k.lower() not in ('cookie', 'host', 'origin', 'referer')}
        hd['cookie'] = ck(role)
        try:
            r = await route.fetch(url=req.url.replace(BASE, API), headers=hd)
            await route.fulfill(response=r)
        except Exception as e:
            print('route err', e); await route.abort()
    await page.route('**/api/**', handler)
    page.on('response', lambda r: bad.append((r.status, r.url.split('/api')[-1])) if '/api/' in r.url and r.status >= 400 else None)
    return br, page, bad


async def owner_fix(pw, key, w, h):
    print(f'\n== owner {key} {w}x{h}')
    br, page, bad = await ctx_for(pw, 'owner', w, h)
    try:
        bid, mid = B['f'][key]
        await page.goto(f'{BASE}/super-admin/fix/{bid}/{mid}')
        await page.wait_for_selector('[data-testid="held-mock-override-open"]', timeout=25000)
        await page.wait_for_timeout(1500)
        print('title', await page.inner_text('[data-testid="held-fixer-title"]'))
        print('sol-page buttons', await page.locator('[data-testid*="-sol-page-"]').evaluate_all("els=>els.map(e=>e.dataset.testid+':'+e.textContent)"))
        print('sol imgs before open', await page.locator('[data-testid*="-sol-img-"]').count())
        print('issue texts', await page.locator('[data-testid="held-fixer"] li, [data-testid$="-issues"] li').all_inner_texts())
        sw = await page.evaluate('[document.documentElement.scrollWidth, window.innerWidth]'); print('scrollWidth/inner', sw)
        await page.screenshot(path=f'{SS}/{key}_1.jpg', quality=40)
        await page.click('[data-testid="held-mock-override-open"]'); await page.wait_for_timeout(300)
        print('confirm text', await page.inner_text('[data-testid="held-mock-override"]'))
        sw = await page.evaluate('[document.documentElement.scrollWidth, window.innerWidth]'); print('scrollWidth/inner (confirm open)', sw)
        await page.locator('[data-testid="held-mock-override"]').scroll_into_view_if_needed()
        await page.screenshot(path=f'{SS}/{key}_2.jpg', quality=40)
        await page.click('[data-testid="held-mock-override-cancel"]'); await page.wait_for_timeout(300)
        print('after cancel: open visible', await page.is_visible('[data-testid="held-mock-override-open"]'), 'confirm visible', await page.is_visible('[data-testid="held-mock-override-confirm"]'))
        await page.click('[data-testid="held-mock-override-open"]')
        await page.click('[data-testid="held-mock-override-confirm"]')
        t = await page.wait_for_selector('[data-sonner-toast]', timeout=8000); print('toast', await t.inner_text())
        await page.wait_for_timeout(7000)
        print('clear shown', await page.is_visible('[data-testid="held-fixer-clear"]'), 'override still', await page.is_visible('[data-testid="held-mock-override-open"]'))
        await page.screenshot(path=f'{SS}/{key}_3.jpg', quality=40)
        print('4xx/5xx', bad)
    except Exception as e:
        print('ERR', e, bad); await page.screenshot(path=f'{SS}/{key}_err.jpg', quality=40)
    await br.close()


async def lazy_imgs(pw):
    print('\n== lazy solution images (rev mock as owner)')
    br, page, bad = await ctx_for(pw, 'owner', 1920, 1080)
    try:
        bid, mid = B['f']['rev']
        await page.goto(f'{BASE}/super-admin/fix/{bid}/{mid}')
        await page.wait_for_selector('[data-testid="held-mock-override-open"]', timeout=25000); await page.wait_for_timeout(1500)
        det = page.locator('details[data-testid$="-solutions"]'); n = await det.count(); print('solution details', n)
        print('imgs before', await page.locator('[data-testid*="-sol-img-"]').count())
        if n:
            await det.first.locator('summary').click(); await page.wait_for_timeout(2500)
            print('imgs after open', await page.locator('[data-testid*="-sol-img-"]').count())
            print('img loaded', await page.locator('[data-testid*="-sol-img-"] img, img[data-testid*="-sol-img-"]').evaluate_all("els=>els.map(e=>e.naturalWidth)"))
        print('4xx/5xx', bad)
    except Exception as e:
        print('ERR', e, bad)
    await br.close()


async def reviewer(pw):
    print('\n== reviewer')
    br, page, bad = await ctx_for(pw, 'reviewer', 1920, 1080)
    try:
        bid, mid = B['f']['rev']
        await page.goto(f'{BASE}/super-admin/fix/{bid}/{mid}')
        await page.wait_for_selector('[data-testid="held-fixer-title"]', timeout=25000); await page.wait_for_timeout(3000)
        print('title', await page.inner_text('[data-testid="held-fixer-title"]'))
        print('override count (expect 0)', await page.locator('[data-testid="held-mock-override-open"]').count())
        print('4xx/5xx', bad)
    except Exception as e:
        print('ERR', e, bad)
    await br.close()


async def student_pin(pw, w, h):
    print(f'\n== student change pin {w}x{h}')
    br, page, bad = await ctx_for(pw, 'student', w, h)
    try:
        await page.goto(f'{BASE}/profile')
        await page.wait_for_selector('[data-testid="profile-change-pin"]', timeout=25000)
        await page.click('[data-testid="profile-change-pin"]')
        await page.fill('#change-pin-new', '2468'); await page.fill('#change-pin-confirm', '2468')
        await page.click('[data-testid="change-pin-save"]'); await page.wait_for_timeout(2500)
        print('dialog text', (await page.inner_text('[data-testid="change-pin-dialog"]'))[:400])
        await page.screenshot(path=f'{SS}/pin_{w}.jpg', quality=40)
        print('4xx/5xx', bad)
    except Exception as e:
        print('ERR', e, bad); await page.screenshot(path=f'{SS}/pin_err_{w}.jpg', quality=40)
    await br.close()


async def main():
    async with async_playwright() as pw:
        await lazy_imgs(pw)
        await reviewer(pw)
        await owner_fix(pw, 'desk', 1920, 1080)
        await owner_fix(pw, 'mob', 390, 844)
        await student_pin(pw, 390, 844)

asyncio.run(main())
