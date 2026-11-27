"""TEST-ONLY iteration 257 browser walk (pocket C1b): the owner's switch "AITS ke analysis mein chapter ke naam dikhao" and what the
student then sees in the analysis of an All India paper. /api is routed to tests/names_bridge257.py (127.0.0.1:8782, cookies in
/tmp/uibridge257/bridge.json). Each size: Off -> On -> Off again.
Run: cd /app/backend && python tests/ui_names257.py [desk] [mob]
"""
import asyncio, json, os, sys
from pathlib import Path
os.environ.setdefault('BRIDGE_OUT', '/tmp/uibridge257'); os.environ.setdefault('BRIDGE_PORT', '8782')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.async_api import async_playwright  # noqa: E402
from ui_cut210 import open_as, overflow, BASE, say, RESULT  # noqa: E402

INFO = json.load(open('/tmp/uibridge257/bridge.json'))
SS = '/app/.screenshots/ui257'; os.makedirs(SS, exist_ok=True)
URL, N, NAME = f"{BASE}/series/all-india-jee/analysis/{INFO['attempt']}", INFO['number'], INFO['chapter']
SLUG = NAME.lower().replace(' ', '-')


async def walk(pw, size):
    sbr, sp, sbad, slogs = await open_as(pw, 'student', size)
    obr, op, obad, _ = await open_as(pw, 'owner', size)
    S = lambda t: sp.locator(f'[data-testid={t}]')  # noqa: E731
    O = lambda t: op.locator(f'[data-testid={t}]')  # noqa: E731

    async def text(loc):
        return (await loc.first.inner_text()).strip() if await loc.count() else ''

    async def section(key):
        await sp.goto(f'{URL}?a={key}'); await sp.wait_for_selector(f'[data-testid=a2-section-{key}]', timeout=30000); await sp.wait_for_timeout(600)

    async def flip(on):
        await op.goto(BASE + INFO['type']); await op.wait_for_selector('[data-testid=links-show-switch]', timeout=25000)
        sw = O('links-show-switch'); await sw.scroll_into_view_if_needed(); await op.wait_for_timeout(300)
        if (await sw.get_attribute('aria-checked') == 'true') != on:
            await sw.click()
        for _ in range(60):
            if (await O('links-show-switch').get_attribute('aria-checked') == 'true') == on and not await O('links-show-switch').is_disabled():
                break
            await op.wait_for_timeout(250)
        return await O('links-show-switch').get_attribute('aria-checked')

    async def shot(page, name):
        await page.screenshot(path=f'{SS}/{size}_{name}.jpg', quality=40, type='jpeg')
    try:
        off = await flip(False); await section('performance')
        stats = await text(S('series-analysis-stats'))
        say(f'{size}: switch Off: the student\'s Performance says this paper has no chapter tags; no chapter list is shown', off == 'false' and await S('a2-no-chapters').count() == 1
            and not await S('a2-weak-chapters').count() and bool(stats), (off, await S('a2-no-chapters').count(), stats))
        await S('a2-no-chapters').scroll_into_view_if_needed(); await shot(sp, 'off')
        on = await flip(True); await shot(op, 'switch_on'); await section('performance')
        weak = ' '.join((await text(S('a2-weak-' + SLUG))).split())
        say(f'{size}: the owner switches it On: "Marks kis chapter se gaye" now shows {NAME} (Chemistry): 1 galat, 5 marks gaye; the "no chapter tags" line is gone',
            on == 'true' and NAME in weak and 'Chemistry · 1 galat, 0 chhode' in weak and weak.endswith('5') and not await S('a2-no-chapters').count(), (on, weak))
        await S('a2-weak-chapters').scroll_into_view_if_needed(); await sp.wait_for_timeout(300); await shot(sp, 'on_weak')
        await S('a2-pill-perf-subject-chemistry').click(); await sp.wait_for_selector('[data-testid=a2-chapter-table]', timeout=10000)
        cells = [c.strip() for c in await S('a2-chapter-row-' + SLUG).locator('td').all_inner_texts()]
        say(f'{size}: Chemistry › chapter-wise table: {NAME}: 1 sawaal, 0 sahi, 1 galat, 0 chhode, 5 marks gaye; only that one row', cells[:5] == [NAME, '1', '0', '1', '0'] and cells[6].endswith('5')
            and await S('a2-chapter-table').locator('tbody tr').count() == 1, cells)
        await S('a2-chapter-table').scroll_into_view_if_needed(); await sp.wait_for_timeout(300); await shot(sp, 'on_chapters')
        await section('qs')
        if size == 'desk':
            head = [h.strip().capitalize() for h in await S('a2-qs-table').locator('thead th').all_inner_texts()]   # the page prints headings in capitals
            row = [c.strip() for c in await S(f'a2-qs-row-{N}').locator('td').all_inner_texts()]
            named = [n for n in range(1, 76) if NAME in await text(S(f'a2-qs-row-{n}'))]
            say(f'{size}: Qs by Qs has a Chapter column; Q{N} says {NAME}; no other question carries a chapter', head[:3] == ['Q', 'Subject', 'Chapter'] and row[:3] == [str(N), 'Chemistry', NAME] and named == [N], (head[:4], row[:4], named))
            await S(f'a2-qs-row-{N}').scroll_into_view_if_needed()
        else:
            card = ' '.join((await text(S(f'a2-qs-card-{N}'))).split())
            say(f'{size}: Qs by Qs: the card of Q{N} says {NAME}', f'Chemistry · {NAME}' in card, card)
            await S(f'a2-qs-card-{N}').scroll_into_view_if_needed()
            await overflow(sp, size + ' Qs by Qs')
        await sp.wait_for_timeout(300); await shot(sp, 'on_qs')
        again = await text(S('series-analysis-stats'))
        say(f'{size}: the marks, correct, incorrect and accuracy on top of the page are what they were', again == stats, (stats, again))
        off = await flip(False); await section('performance')
        say(f'{size}: switched Off again: the analysis is back to "no chapter tags", no chapter list', off == 'false' and await S('a2-no-chapters').count() == 1 and not await S('a2-weak-chapters').count(), off)
        if size == 'mob':
            await overflow(sp, size + ' Performance')
    except Exception as e:
        say(f'{size}: walk', False, repr(e)[:500]); await shot(sp, 'err_student'); await shot(op, 'err_owner')
    finally:
        both = [b for b in sbad + obad if '/dream' not in b[1]]
        print('   failed calls:', both[:8], '| console:', [l for l in slogs if 'dream' not in l and '503' not in l][:4], flush=True)
        say(f'{size}: no failed call for the analysis or the switch, and no server error anywhere', not [b for b in both if b[0] >= 500 or '/analysis' in b[1] or '/admin/links' in b[1]], both[:6])
        await sbr.close(); await obr.close()


async def main():
    sizes = [s for s in ('desk', 'mob') if s in sys.argv] or ['desk', 'mob']
    async with async_playwright() as pw:
        for size in sizes:
            await walk(pw, size)
    ok = sum(1 for r in RESULT if r[1])
    print('TOTAL', len(RESULT), 'PASS', ok, 'FAIL', len(RESULT) - ok)

asyncio.run(main())
