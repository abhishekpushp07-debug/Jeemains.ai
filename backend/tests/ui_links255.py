"""TEST-ONLY iteration 255 browser walk (pocket C1a): Super Admin > JEE Main > All India Test Series > "Jod: ek sawaal, ek record".
/api is routed to tests/links_bridge255.py (127.0.0.1:8781, cookies in /tmp/uibridge255/bridge.json).
Run: cd /app/backend && python tests/ui_links255.py [desk] [mob]
(the first size presses "Jod banao", then sees a changed Draft and the owner's list; the last one puts the Draft right and joins again)
"""
import asyncio, json, os, sys
from pathlib import Path
os.environ.setdefault('BRIDGE_OUT', '/tmp/uibridge255'); os.environ.setdefault('BRIDGE_PORT', '8781')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.async_api import async_playwright  # noqa: E402
from ui_cut210 import open_as, overflow, BASE, say, RESULT  # noqa: E402

D = '/tmp/uibridge255/'
INFO = json.load(open(D + 'bridge.json'))
SS = '/app/.screenshots/ui255'; os.makedirs(SS, exist_ok=True)
C, PER, (KEY, OTHER) = INFO['counts'], INFO['per_mock'], INFO['answers']


async def walk(pw, size, first, last):
    br, page, bad, _ = await open_as(pw, 'owner', size)
    at = lambda t: page.locator(f'[data-testid={t}]')  # noqa: E731

    async def text(t):
        return (await at(t).inner_text()).strip() if await at(t).count() else ''

    async def count(k):
        return (await page.locator(f'[data-testid=links-count-{k}] strong').inner_text()).strip() if await at('links-count-' + k).count() else ''

    async def counts():
        return {k: await count(k) for k in ('records', 'linked', 'paper', 'chapter', 'review', 'bare')}

    async def until(fn, ok, secs=60):
        got = None
        for _ in range(secs * 2):
            got = await fn()
            if ok(got):
                break
            await page.wait_for_timeout(500)
        return got

    async def touch(name):
        Path(D + name).touch()
        for _ in range(60):
            if not os.path.exists(D + name):
                break
            await page.wait_for_timeout(250)

    async def opened():
        await page.goto(BASE + INFO['type']); await page.wait_for_selector('[data-testid=links-panel]', timeout=25000)
        await at('links-panel').scroll_into_view_if_needed(); await page.wait_for_timeout(400)

    async def shot(name):
        await at('links-panel').scroll_into_view_if_needed(); await page.wait_for_timeout(300)
        await page.screenshot(path=f'{SS}/{size}_{name}.jpg', quality=40, type='jpeg')
    want = {**{k: str(v) for k, v in C.items()}, 'review': '0', 'bare': '0'}
    broken = {**want, 'linked': str(C['linked'] - 1), 'review': '1'}
    try:
        await opened()
        if first:
            never = await text('links-never')
            say(f'{size}: before anything is made the box says so, says how many uploads it will read, and offers "Jod banao"', 'abhi nahi bana' in never and '2 upload' in never
                and (await text('links-run')) == 'Jod banao' and not await at('links-counts').count() and await at('links-books').count() == 1, (never, await text('links-run')))
            await shot('before')
            await at('links-run').click()
            got = await until(counts, lambda c: c == want)
            say(f'{size}: "Jod banao": the six counts appear: records, joined in both, only in a paper, only in the chapter book, for the owner, without an address', got == want, (got, want))
            state = await text('links-state')
            say(f'{size}: the line under them says when it was made and that nothing changed since; the button now says "Dobara jodo"', await at('links-state').get_attribute('data-fresh') == 'yes'
                and 'Tab se koi upload ya Draft nahi badla' in state and 'IST' in state and (await text('links-run')) == 'Dobara jodo' and not await at('links-never').count(), (state, await text('links-run')))
            rows = {n: await text('links-mock-count-' + n) for n in PER}
            say(f'{size}: each paper has its row: how many of its 75 questions are joined to the chapter book', rows == {n: f'{v} / 75' for n, v in PER.items()} and not await at('links-review').count(), rows)
            books = await text('links-books')
            say(f'{size}: the uploads that were read are named, with how many questions of each printed an address', 'TEST_AITS_06_07' in books and '2 mock · 150 sawaal · 150 par pata' in books
                and 'TEST_CHEM_CH08' in books and 'Chapter-wise' in books, books)
            await shot('made')
            label, sw = await text('links-show-label'), at('links-show-switch')
            say(f'{size}: the switch for chapter names in the AITS analysis is there, Off, and says how many AITS questions got a chapter name',
                await sw.get_attribute('aria-checked') == 'false' and f"{INFO['named']} AITS sawaalon" in label and 'Score aur rank nahi badalte' in label, label)
            await sw.click()
            on = await until(lambda: sw.get_attribute('aria-checked'), lambda v: v == 'true', 15)
            await opened()
            say(f'{size}: switched On: it is still On when the page is opened again', on == 'true' and await at('links-show-switch').get_attribute('aria-checked') == 'true', on)
            await at('links-show-switch').click()
            off = await until(lambda: at('links-show-switch').get_attribute('aria-checked'), lambda v: v == 'false', 15)
            say(f'{size}: switched Off again', off == 'false', off)
            await touch('break'); await opened()
            state = await until(lambda: at('links-state').get_attribute('data-fresh'), lambda v: v == 'no', 20)
            say(f'{size}: a Draft answer is changed afterwards: the line says the join is older than the Drafts and asks for "Dobara jodo"; the counts wait for the button',
                state == 'no' and '“Dobara jodo” dabaiye' in await text('links-state') and await counts() == want, (state, await text('links-state')))
            await at('links-run').click()
            got = await until(counts, lambda c: c == broken)
            item = await text('links-review-0')
            say(f"{size}: pressed: that question is no longer joined; it is on the owner's list with its address, both answers and where the other copy is",
                got == broken and 'AITS Mock 06 / Q65' in item and f'jawab alag: {KEY} aur {OTHER}' in item and INFO['where'] in item and await at('links-review-1').count() == 0, (got, item))
            say(f'{size}: its paper row says one question waits for the owner', (await text('links-mock-review-6')) == '1 aap dekhiye' and (await text('links-mock-count-6')) == f"{PER['6'] - 1} / 75"
                and not await at('links-mock-review-7').count(), (await text('links-mock-review-6'), await text('links-mock-count-6')))
            await shot('review')
        else:
            got = await until(counts, lambda c: c == broken, 20)
            say(f"{size}: opened again later: the same counts, and the owner's list is still there", got == broken and await at('links-review-0').count() == 1, got)
        if size == 'mob':
            await overflow(page, size + ' Jod box')
            tall = round((await at('links-run').bounding_box())['height'])
            say(f'{size}: the button is at least 44 px tall', tall >= 44, tall)
            await shot('review')
        if last:
            await touch('fix'); await opened()
            await until(lambda: at('links-state').get_attribute('data-fresh'), lambda v: v == 'no', 20)
            await at('links-run').click()
            got = await until(counts, lambda c: c == want)
            say(f"{size}: the Draft is put right and the button pressed: joined again, the owner's list is gone, the line says nothing changed since", got == want and not await at('links-review').count()
                and await at('links-state').get_attribute('data-fresh') == 'yes' and (await text('links-mock-count-6')) == f"{PER['6']} / 75", (got, await text('links-state')))
            await shot('done')
    finally:
        say(f'{size}: no failed API calls', not [b for b in bad if '/dream' not in b[1]], bad[:4])
        await br.close()


async def main():
    sizes = [s for s in ('desk', 'mob') if s in sys.argv] or ['desk', 'mob']
    async with async_playwright() as pw:
        for i, size in enumerate(sizes):
            await walk(pw, size, i == 0, i == len(sizes) - 1)
    ok = sum(1 for r in RESULT if r[1])
    print('TOTAL', len(RESULT), 'PASS', ok, 'FAIL', len(RESULT) - ok)

asyncio.run(main())
