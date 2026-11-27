"""TEST-ONLY iteration 250 browser walk (pocket S1b): Super Admin > storage badge > "Purani pictures jinmein 'Source' line ho sakti hai".
/api is routed to tests/repaint_bridge250.py (127.0.0.1:8779, cookies in /tmp/uibridge250/bridge.json).
Run: cd /app/backend && python tests/ui_repaint250.py [desk] [mob]   (the first size runs "Line hatao"; the last one puts the odd picture right and finishes)
"""
import asyncio, json, os, sys
from pathlib import Path
os.environ.setdefault('BRIDGE_OUT', '/tmp/uibridge250'); os.environ.setdefault('BRIDGE_PORT', '8779')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.async_api import async_playwright  # noqa: E402
from ui_cut210 import open_as, overflow, BASE, say, RESULT  # noqa: E402

D = '/tmp/uibridge250/'
INFO = json.load(open(D + 'bridge.json'))
SS = '/app/.screenshots/ui250'; os.makedirs(SS, exist_ok=True)
N, LINED, ODD = INFO['pictures'], INFO['with_line'], INFO['odd']


async def walk(pw, size, first, last):
    br, page, bad, _ = await open_as(pw, 'owner', size)
    at = lambda t: page.locator(f'[data-testid={t}]')  # noqa: E731

    async def text(t):
        return (await at(t).inner_text()).strip() if await at(t).count() else ''

    async def until(t, ok, secs=120):
        got = ''
        for _ in range(secs * 2):
            got = await text(t)
            if ok(got):
                break
            await page.wait_for_timeout(500)
        return got
    try:
        await page.goto(BASE + INFO['type']); await page.wait_for_selector('[data-testid=storage-badge]', timeout=25000)
        await at('storage-badge').click(); await page.wait_for_selector('[data-testid=source-line]', timeout=15000)
        await at('source-line').scroll_into_view_if_needed(); await page.wait_for_timeout(500)
        title = await text('source-line-title')
        if first:
            say(f'{size}: the box says how many older pictures may still show the line', title.endswith(f': {N}'), title)
            say(f'{size}: "Line hatao" is offered and nothing runs yet', await at('source-line-start').is_visible() and not await at('source-line-stop').count() and not await at('source-line-progress').count(), '')
            await page.screenshot(path=f'{SS}/{size}_before.jpg', quality=40, type='jpeg')
            await at('source-line-start').click()
            state = await until('source-line-state', lambda t: t.startswith('Kaam poora'))
            prog, fails = await text('source-line-progress'), await text('source-line-failures')
            say(f'{size}: the run finishes; the line under the bar says how many were cleaned and how many could not be', state == 'Kaam poora hua.' and prog.startswith(f'{N} / {N}')
                and f'{LINED - 1} saaf hui' in prog and '1 nahi ho payi' in prog, (state, prog))
            say(f'{size}: the picture that could not be proven is named (test, question, sawaal or solution) with its reason', f'Q{ODD[0]} · {ODD[1]}' in fails and 'kisi aur PDF' in fails
                and await at('source-line-failure-0').count() == 1 and not await at('source-line-failure-1').count(), fails)
            say(f'{size}: the box now says one picture still waits, and "Line hatao" is offered again', (await text('source-line-title')).endswith(': 1') and await at('source-line-start').is_visible(), await text('source-line-title'))
            await at('source-line').scroll_into_view_if_needed()
            await page.screenshot(path=f'{SS}/{size}_left.jpg', quality=40, type='jpeg')
        else:
            say(f'{size}: opened again later: one picture still waits', title.endswith(': 1'), title)
        if size == 'mob':
            await overflow(page, size + ' source-line box')
            tall = round((await at('source-line-start').bounding_box())['height'])
            say(f'{size}: "Line hatao" is at least 44 px tall', tall >= 44, tall)
        if last:
            Path(D + 'fix').touch()
            for _ in range(40):
                if not os.path.exists(D + 'fix'):
                    break
                await page.wait_for_timeout(250)
            await at('source-line-start').click()
            done = await until('source-line-all-done', bool)
            say(f'{size}: the odd picture is put right and "Line hatao" is pressed again: one quiet line says all {LINED} are clean; the box is gone', f'{LINED} se' in done and 'nahi bachi' in done
                and not await at('source-line').count(), done)
            await at('source-line-all-done').scroll_into_view_if_needed()
            await page.screenshot(path=f'{SS}/{size}_done.jpg', quality=40, type='jpeg')
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
