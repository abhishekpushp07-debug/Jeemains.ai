import asyncio, json, os
from playwright.async_api import async_playwright
B = json.load(open('/tmp/uibridge196/bridge.json'))
BASE = [l.split('=', 1)[1].strip() for l in open('/app/frontend/.env') if l.startswith('REACT_APP_BACKEND_URL')][0].rstrip('/')
API = 'http://127.0.0.1:8773'

async def make(pw, who='hero', w=1920):
    br = await pw.chromium.launch()
    ctx = await br.new_context(viewport={'width': w, 'height': 1000})
    cookie = '; '.join(f'{k}={v}' for k, v in B[who].items())
    async def h(route):
        req = route.request
        hd = {k: v for k, v in req.headers.items() if k.lower() not in ('host', 'referer', 'cookie')}
        hd['origin'] = BASE; hd['cookie'] = cookie
        try:
            r = await route.fetch(url=req.url.replace(BASE, API), headers=hd)
            await route.fulfill(response=r)
        except Exception:
            await route.abort()
    page = await ctx.new_page(); await page.route('**/api/**', h)
    return br, page

async def main():
    async with async_playwright() as pw:
        br, page = await make(pw, 'hero', 1920)
        await page.goto(f"{BASE}/results/{B['hero_attempt']}?a=overview")
        await page.wait_for_selector('[data-testid="analysis2"]', timeout=40000)
        await page.wait_for_timeout(1200)

        # 1. Score ring structure
        html = await page.locator('[data-testid="a2-score-ring"]').inner_html()
        print('SCORE RING HTML:', html[:800])

        # 2. Click rank (i) and dump role=dialog contents
        await page.locator('[data-testid="a2-info-rank"]').click()
        await page.wait_for_timeout(500)
        dialogs = await page.evaluate("""() => [...document.querySelectorAll('[role=dialog]')].map(e=>({testid:e.getAttribute('data-testid'), cls:e.className, text:(e.innerText||'').slice(0,80)}))""")
        print('ROLE=DIALOG after (i):', dialogs)

        # 3. QsByQs filter testids
        await page.goto(f"{BASE}/results/{B['hero_attempt']}?a=qs")
        await page.wait_for_selector('[data-testid="analysis2"]', timeout=40000)
        await page.wait_for_timeout(1000)
        tids = await page.evaluate("""() => [...document.querySelectorAll('[data-testid*=qs], [data-testid*=filter]')].map(e=>e.getAttribute('data-testid')).slice(0,40)""")
        print('qs testids:', tids)

        # 4. friend display-name dialog
        await page.close(); await br.close()
        br2, page2 = await make(pw, 'friend', 1920)
        await page2.goto(f"{BASE}/results/{B['friend_attempt']}?a=overview")
        await page2.wait_for_selector('[data-testid="analysis2"]', timeout=40000)
        await page2.wait_for_timeout(1200)
        await page2.locator('[data-testid="a2-board-name-ask"]').click()
        await page2.wait_for_timeout(800)
        tids2 = await page2.evaluate("""() => [...document.querySelectorAll('[data-testid]')].filter(e=>/display|name|dialog/i.test(e.getAttribute('data-testid'))).map(e=>e.getAttribute('data-testid'))""")
        print('display-name testids visible:', tids2)
        inputs = await page2.evaluate("""() => [...document.querySelectorAll('input')].map(e=>({id:e.id,name:e.name,ph:e.placeholder}))""")
        print('inputs:', inputs)
        await br2.close()

        # 5. old attempt journey
        br3, page3 = await make(pw, 'old', 1920)
        await page3.goto(f"{BASE}/results/{B['old_attempt']}?a=journey")
        await page3.wait_for_selector('[data-testid="analysis2"]', timeout=40000)
        await page3.wait_for_timeout(1000)
        jblocks = await page3.evaluate("""() => [...document.querySelectorAll('[data-testid^=a2-block-]')].map(e=>e.getAttribute('data-testid'))""")
        print('old journey blocks:', jblocks)
        later = await page3.evaluate("""() => [...document.querySelectorAll('[data-testid^=a2-later-]')].map(e=>e.getAttribute('data-testid'))""")
        print('old journey later cards:', later)
        await br3.close()

asyncio.run(main())
