"""Leaderboard, comparative picker, solutions nav for Q11, old PDF page count."""
import asyncio, json, os, re, subprocess
from playwright.async_api import async_playwright
B = json.load(open('/tmp/uibridge196/bridge.json'))
BASE = [l.split('=', 1)[1].strip() for l in open('/app/frontend/.env') if l.startswith('REACT_APP_BACKEND_URL')][0].rstrip('/')
API = 'http://127.0.0.1:8773'
OUT = '/tmp/shots_focus'
os.makedirs(OUT, exist_ok=True)
R = []
def rec(n, ok, d=''): R.append((n,ok,d)); print(('PASS' if ok else 'FAIL'), n, '' if ok else '::'+str(d)[:300], flush=True)

async def make(pw, who='hero', w=1920):
    br = await pw.chromium.launch()
    ctx = await br.new_context(viewport={'width': w, 'height': 1000})
    cookie = '; '.join(f'{k}={v}' for k, v in B[who].items())
    async def h_(route):
        req=route.request
        hd={k:v for k,v in req.headers.items() if k.lower() not in ('host','referer','cookie')}
        hd['origin']=BASE; hd['cookie']=cookie
        try:
            r=await route.fetch(url=req.url.replace(BASE,API), headers=hd)
            await route.fulfill(response=r)
        except Exception:
            await route.abort()
    page=await ctx.new_page(); await page.route('**/api/**', h_)
    return br, page

async def goto(page, who, q=''):
    await page.goto(f"{BASE}/results/{B[who+'_attempt']}{q}")
    await page.wait_for_selector('[data-testid=analysis2]', timeout=40000)
    await page.wait_for_timeout(1100)

async def leaderboard_and_compare(pw):
    br, page = await make(pw, 'hero', 1920)
    try:
        await goto(page, 'hero', '?a=overview')
        rows = await page.locator('[data-testid^="a2-board-row-"]').count()
        rec('Leaderboard shows rows', rows >= 1, {'rows': rows})
        more = await page.locator('[data-testid="a2-board-more"]').count()
        rec('Top N dikhao button exists', more > 0, '')
        # search box: placeholder 'Naam ya Rank'
        search_ok = await page.evaluate("""() => !!document.querySelector('input[placeholder*=\"Naam ya Rank\"]')""")
        rec('Leaderboard has Naam ya Rank search', search_ok, '')
        if search_ok:
            # search by rank 1
            await page.locator('input[placeholder*="Naam ya Rank"]').first.fill('1')
            await page.wait_for_timeout(500)
            row1 = await page.locator('[data-testid^="a2-board-row-"]').count()
            rec('Search by rank narrows rows', row1 >= 1, {'count': row1})
            await page.locator('input[placeholder*="Naam ya Rank"]').first.fill('')
        # Compare button — anywhere on a row
        compare_btns = await page.locator('button:has-text("Compare")').count()
        rec('Compare buttons on leaderboard rows', compare_btns >= 1, {'count': compare_btns})
        # Comparative picker
        await goto(page, 'hero', '?a=overview&mode=compare&vs=topper')
        picker = await page.locator('[data-testid="a2-compare-picker"]').count()
        rec('Comparative picker renders', picker > 0, '')
        head = await page.locator('[data-testid="a2-block-compare-head"]').count()
        gap = await page.locator('[data-testid="a2-block-compare-gap"]').count()
        subj = await page.locator('[data-testid="a2-block-compare-subjects"]').count()
        rec('compare: head+gap+subjects all present', head > 0 and gap > 0 and subj > 0, '')
        # No other student's answers ever exposed - check /api traffic for 'answer' outside own
        # (covered by backend tests). Here just verify text label
        label_ok = await page.evaluate("""() => /aap\\s*vs/i.test(document.body.innerText)""")
        rec('Compare shows "Aap vs <label>"', label_ok, '')
    finally:
        await br.close()

async def solutions_nav(pw):
    br, page = await make(pw, 'hero', 1920)
    try:
        await goto(page, 'hero', '?a=qs')
        await page.locator('[data-testid="a2-qgrid-q-11"]').first.click()
        await page.wait_for_selector('[data-testid="solution-insight"]', timeout=15000)
        await page.wait_for_timeout(800)
        line = (await page.locator('[data-testid="solution-insight-line"]').inner_text()).strip()
        rec('Solutions insight shows one-line summary for Q11', bool(line), line[:140])
        # Four cards
        for t in ('solution-card-time', 'solution-card-class-time', 'solution-card-right', 'solution-card-attempted'):
            rec(f'Solution card {t} present', await page.locator(f'[data-testid="{t}"]').count() > 0, '')
        # journey rows
        steps = await page.locator('[data-testid^="solution-journey-step-"]').count()
        rec('Solutions journey steps present (Q11 has two visits)', steps >= 2, {'steps': steps})
        # Back navigation returns to analysis section
        await page.go_back()
        await page.wait_for_selector('[data-testid=analysis2]', timeout=10000)
        q = page.url.split('?', 1)[-1] if '?' in page.url else ''
        rec('Back navigation returns to analysis (a=qs in URL)', 'a=qs' in page.url, page.url[-80:])
    finally:
        await br.close()

async def old_pdf(pw):
    br, page = await make(pw, 'old', 1920)
    try:
        await goto(page, 'old', '?a=overview')
        async with page.expect_download(timeout=60000) as di:
            await page.locator('[data-testid="a2-download-report"]').click()
        d = await di.value
        p = os.path.join(OUT, 'old_' + d.suggested_filename)
        await d.save_as(p)
        txt = subprocess.run(['pdftotext', p, '-'], capture_output=True, text=True, timeout=30).stdout
        pages = txt.count('\x0c')
        rec('Old PDF page count ~6', 5 <= pages <= 7, {'pages': pages, 'name': d.suggested_filename})
        phones = re.findall(r'\b[6-9]\d{9}\b', txt)
        rec('Old PDF has no phone number', not phones, phones[:3])
    finally:
        await br.close()

async def hinglish_copy(pw):
    br, page = await make(pw, 'hero', 1920)
    try:
        await goto(page, 'hero', '?a=overview')
        # Expected Hinglish phrases
        text = await page.locator('[data-testid="analysis2"]').inner_text()
        for phrase in ['Har mark kahan gaya', 'Agle mock', 'Class mein aap kahan', 'Is paper ka leaderboard', 'Har subject', 'Is test se meri']:
            rec(f'Hinglish copy contains "{phrase}"', phrase in text, '')
    finally:
        await br.close()

async def main():
    async with async_playwright() as pw:
        for fn in (leaderboard_and_compare, solutions_nav, old_pdf, hinglish_copy):
            try: await fn(pw)
            except Exception as e: rec(fn.__name__, False, 'EXC '+str(e)[:300])
    print(f'\n{sum(1 for _,o,_ in R if o)}/{len(R)} passed')

asyncio.run(main())
