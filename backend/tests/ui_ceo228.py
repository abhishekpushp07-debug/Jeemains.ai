# UI: Mission contacts picker (mocked Contact Picker), usage events from UI, login/signup/AITS regression - through the bridge.
import asyncio, json, os, re
from playwright.async_api import async_playwright

OUT = os.environ.get('BRIDGE_OUT', '/tmp/ceobridge228')
API = 'http://127.0.0.1:' + os.environ.get('BRIDGE_PORT', '8776')
BASE = [l.split('=', 1)[1].strip() for l in open('/app/frontend/.env') if l.startswith('REACT_APP_BACKEND_URL')][0].rstrip('/')
B = json.load(open(f'{OUT}/bridge.json'))
SHOTS = '/app/.screenshots'
os.makedirs(SHOTS, exist_ok=True)
RES = []

PICKER = """window.ContactsManager = function(){};
Object.defineProperty(navigator, 'contacts', {value: {select: async () => [{name:['Dost A'], tel:['098222 00001']}, {name:['No number'], tel:[]}, {name:['Dost B'], tel:['+91 98222 00009']}]}});"""


def say(name, ok, extra=''):
    RES.append((name, ok)); print(('PASS ' if ok else 'FAIL ') + name, extra if not ok or extra else '')


async def open_as(pw, role, picker=False, w=390, h=844):
    br = await pw.chromium.launch()
    ctx = await br.new_context(viewport={'width': w, 'height': h}, has_touch=True, is_mobile=True)
    if role:
        await ctx.add_cookies([{'name': k, 'value': v, 'url': BASE} for k, v in B[role].items()])
    if picker:
        await ctx.add_init_script(PICKER)
    page = await ctx.new_page(); bad, logs, posts = [], [], []

    async def handler(route):
        req = route.request
        hd = {k: v for k, v in req.headers.items() if k.lower() not in ('cookie', 'host', 'origin', 'referer')}
        hd['cookie'] = '; '.join(f"{c['name']}={c['value']}" for c in await ctx.cookies(BASE))
        hd['origin'] = BASE
        if req.method == 'POST' and req.url.endswith('/api/events'):
            posts.append(req.post_data)
        if '/api/auth/phone/signup' in req.url:
            posts.append('SIGNUP ' + (req.post_data or ''))
        try:
            r = await route.fetch(url=req.url.replace(BASE, API), headers=hd)
            await route.fulfill(response=r)
        except Exception as e:
            print('route err', req.url[-80:], e); await route.abort()
    await page.route('**/api/**', handler)
    page.on('response', lambda r: bad.append((r.status, r.url.split('/api')[-1][:90])) if '/api/' in r.url and r.status >= 400 else None)
    page.on('console', lambda m: logs.append(m.text[:200]) if m.type == 'error' else None)
    page.on('pageerror', lambda e: logs.append('PAGEERROR ' + str(e)[:200]))
    return br, page, bad, logs, posts


async def overflow(page, tag):
    vw = await page.evaluate('document.documentElement.clientWidth'); sw = await page.evaluate('document.documentElement.scrollWidth')
    say(f'{tag}: no horizontal overflow', sw <= vw + 1, (vw, sw))


async def mission_no_picker(pw):
    br, page, bad, logs, posts = await open_as(pw, 'arjun')
    try:
        await page.goto(f'{BASE}/mission'); await page.wait_for_timeout(5000)
        say('no picker: mission-contacts absent', await page.locator('[data-testid="mission-contacts"]').count() == 0)
        shares = page.locator('[data-testid^="mission-share-"]')
        n = await shares.count(); say('no picker: share buttons present', n > 0, n)
        say('page_open mission sent', any('"page_open"' in (p or '') and '"mission"' in (p or '') for p in posts), posts)
        if n:
            await page.evaluate("navigator.share = undefined")
            await shares.first.click(); await page.wait_for_timeout(1500)
            say('mission_share event sent', any('mission_share' in (p or '') for p in posts), posts)
        await overflow(page, 'mission no picker')
        await page.screenshot(path=f'{SHOTS}/m228_nopicker.jpg', quality=40, full_page=False)
        print('bad responses', bad[:10]); print('console errors', [l for l in logs if '503' not in l][:6])
    finally:
        await br.close()


async def mission_picker(pw):
    br, page, bad, logs, posts = await open_as(pw, 'riya', picker=True)
    try:
        await page.goto(f'{BASE}/mission'); await page.wait_for_timeout(5000)
        for t in ('mission-contacts', 'mission-contacts-pick', 'mission-contacts-consent'):
            say(f'picker: {t} visible', await page.locator(f'[data-testid="{t}"]').is_visible())
        await page.locator('[data-testid="mission-contacts"]').scroll_into_view_if_needed()
        await page.screenshot(path=f'{SHOTS}/m228_picker_before.jpg', quality=40, full_page=False)
        await page.click('[data-testid="mission-contacts-pick"]'); await page.wait_for_timeout(2500)
        lst = page.locator('[data-testid="mission-contacts-list"]')
        say('picker: list visible', await lst.is_visible())
        rows = page.locator('[data-testid^="mission-contact-"]:is(li)')
        n = await rows.count(); say('picker: rows shown', n >= 2, n)
        note = await page.locator('[data-testid="mission-contacts-note"]').text_content() if await page.locator('[data-testid="mission-contacts-note"]').count() else None
        say('picker: note shows joined count', bool(note and re.search(r'\d+ dost jude', note)), note)
        say('contacts_pick event sent', any('contacts_pick' in (p or '') for p in posts))
        ids = [ (await rows.nth(i).get_attribute('data-testid')).replace('mission-contact-', '') for i in range(n)]
        texts = [await rows.nth(i).inner_text() for i in range(n)]
        print('rows', list(zip(ids, texts)))
        for cid in ids:
            href = await page.get_attribute(f'[data-testid="mission-contact-wa-{cid}"]', 'href')
            say(f'wa link {cid[:8]}', bool(href and re.match(r'^https://wa\.me/91\d{10}\?text=.+', href)), href)
        await page.locator('[data-testid="mission-contacts-list"]').scroll_into_view_if_needed()
        await page.screenshot(path=f'{SHOTS}/m228_picker_after.jpg', quality=40, full_page=False)
        await overflow(page, 'mission with picker')
        target = ids[0]
        await page.click(f'[data-testid="mission-contact-remove-{target}"]'); await page.wait_for_timeout(1500)
        say('remove: row gone', await page.locator(f'[data-testid="mission-contact-{target}"]').count() == 0)
        await page.reload(); await page.wait_for_timeout(5000)
        say('remove: stays gone after reload', await page.locator(f'[data-testid="mission-contact-{target}"]').count() == 0)
        left = [(await page.locator('[data-testid^="mission-contact-"]:is(li)').nth(i).get_attribute('data-testid')).replace('mission-contact-', '')
                for i in range(await page.locator('[data-testid^="mission-contact-"]:is(li)').count())]
        say('remove: other rows remain after reload', len(left) == n - 1, left)
        # clean up rows this test created
        for cid in left:
            await page.click(f'[data-testid="mission-contact-remove-{cid}"]'); await page.wait_for_timeout(700)
        print('bad responses', bad[:10]); print('console errors', [l for l in logs if '503' not in l][:6])
    finally:
        await br.close()


async def rank_and_regress(pw):
    br, page, bad, logs, posts = await open_as(pw, 'arjun')
    try:
        await page.goto(f'{BASE}/rank'); await page.wait_for_timeout(5000)
        say('rank page renders', await page.locator('[data-testid="rank-page"]').count() == 1)
        posts.clear()
        tile = page.locator('[data-testid="rank-tool-target"]')
        if await tile.count():
            await tile.click(); await page.wait_for_timeout(1500)
        say('rank_tool_open target sent', any('rank_tool_open' in (p or '') and '"target"' in (p or '') for p in posts), posts)
        await page.goto(f'{BASE}/series/all-india-jee'); await page.wait_for_timeout(5000)
        body = await page.inner_text('body')
        say('AITS hub loads', len(body) > 200 and 'error' not in body.lower()[:200], body[:120])
        say('page_open aits sent', any('"aits"' in (p or '') for p in posts), posts)
        await page.goto(f'{BASE}/home'); await page.wait_for_timeout(3000)
        say('page_open home sent', any('"home"' in (p or '') for p in posts), posts)
        ev_bad = [b for b in bad if '/events' in b[1]]
        say('no failing /events calls', not ev_bad, ev_bad)
    finally:
        await br.close()
    br, page, bad, logs, posts = await open_as(pw, None)
    try:
        await page.goto(f'{BASE}/signup?utm_source=insta&utm_medium=reel&utm_campaign=aits'); await page.wait_for_timeout(4000)
        src = await page.evaluate("localStorage.getItem('jl.src')")
        say('captureSource stored utm', bool(src and 'insta' in src), src)
        say('signup renders', await page.locator('input').count() >= 2)
        await page.screenshot(path=f'{SHOTS}/m228_signup.jpg', quality=40, full_page=False)
        tids = await page.evaluate("[...document.querySelectorAll('[data-testid]')].map(e=>e.dataset.testid).filter(t=>/signup|phone|pin/.test(t))")
        print('signup testids', tids)
        await page.goto(f'{BASE}/login'); await page.wait_for_timeout(3000)
        say('login renders', await page.locator('input').count() >= 1)
        print('anon bad', bad[:8]); print('anon console', [l for l in logs if '503' not in l][:5])
    finally:
        await br.close()


async def main():
    async with async_playwright() as pw:
        for f in (mission_no_picker, mission_picker, rank_and_regress):
            try:
                await f(pw)
            except Exception as e:
                say(f.__name__ + ' crashed', False, str(e)[:300])
    print(f"\n{sum(ok for _, ok in RES)}/{len(RES)} passed")

asyncio.run(main())
