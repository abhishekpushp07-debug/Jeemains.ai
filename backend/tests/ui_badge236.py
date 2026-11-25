"""TEST-ONLY iteration 236 browser walk (packet D): the storage badge's colour and reasons, its three lines, "Badi file ka test",
the list of storage failures and the speed line. /api is routed to tests/badge_bridge236.py (127.0.0.1:8777, cookies in /tmp/uibridge236/bridge.json).
Run: cd /app/backend && python tests/ui_badge236.py [desk|mob] [fix]     ("fix" lets the stuck picture through and expects green: once per bridge, on the last size)
"""
import asyncio, json, os, sys
from pathlib import Path
os.environ.setdefault('BRIDGE_OUT', '/tmp/uibridge236'); os.environ.setdefault('BRIDGE_PORT', '8777')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.async_api import async_playwright  # noqa: E402
from ui_cut210 import open_as, overflow, BASE, say, RESULT  # noqa: E402

D = '/tmp/uibridge236/'
INFO = json.load(open(D + 'bridge.json'))
SS = '/app/.screenshots/ui236'; os.makedirs(SS, exist_ok=True)
PIC = INFO['pic']['book']
GREEN = 'Supabase ke dono raaste theek hain aur koi file ruki nahi hai.'
fine = lambda t: t == 'theek' or t.endswith(' ms')  # noqa: E731


async def walk(pw, size, first, fix):
    br, page, bad, _ = await open_as(pw, 'owner', size)
    at = lambda t: page.locator(f'[data-testid={t}]')  # noqa: E731

    async def text(t):
        return (await at(t).inner_text()).strip() if await at(t).count() else ''

    async def level(want, secs=30):
        for _ in range(secs * 2):
            if await at('storage-badge').get_attribute('data-level') in want:
                return True
            await page.wait_for_timeout(500)
        return False

    async def until(t, ok, secs=45):
        got = ''
        for _ in range(secs * 2):
            got = await text(t)
            if ok(got):
                break
            await page.wait_for_timeout(500)
        return got
    try:
        await page.goto(BASE + INFO['type']); await page.wait_for_selector('[data-testid=storage-badge]', timeout=25000)
        say(f'{size}: a picture is stuck: the badge is YELLOW (not green) and still says "Storage: Supabase"', await level(['yellow']) and await text('storage-badge-label') == 'Storage: Supabase'
            and 'warn' in await at('storage-badge').get_attribute('class'), (await at('storage-badge').get_attribute('data-level'), await text('storage-badge-label')))
        await at('storage-badge').click(); await page.wait_for_selector('[data-testid=storage-row-big]', timeout=10000); await page.wait_for_timeout(900)
        rows = [await text(t) for t in ('storage-row-supabase', 'storage-row-big', 'storage-row-emergent')]
        say(f'{size}: three lines: Supabase · Pictures (chhoti file), Supabase · PDF (badi file), Emergent (fallback)', 'Supabase · Pictures (chhoti file)' in rows[0] and 'Supabase · PDF (badi file)' in rows[1]
            and 'Emergent (fallback)' in rows[2], rows)
        say(f'{size}: each line says when and how it was checked', 'pehle' in rows[0] and ('naye naam ki jaanch file' in rows[0] or 'Asli file save hui' in rows[0]) and 'ek hi naam' in rows[2] and 'pehle' in rows[2], rows)
        why = await text('storage-reasons')
        say(f'{size}: the reason for the colour is written: a file is stuck', 'atki hai' in why, why)
        if first:
            say(f'{size}: the big-file route was never tried: it says so, the line says "jaancha nahi"', 'jaancha nahi gaya' in why and await text('storage-row-big-value') == 'jaancha nahi', (why, await text('storage-row-big-value')))
            await page.screenshot(path=f'{SS}/{size}_first.jpg', quality=40, type='jpeg')
            await at('storage-big-test').click()
            v = await until('storage-row-big-value', lambda t: t.startswith('theek'))
            note, why = await text('storage-row-big-note'), await text('storage-reasons')
            say(f'{size}: "Badi file ka test" runs: the line turns to theek with the seconds it took', v.startswith('theek ·') and 'second' in v, v)
            say(f'{size}: ...the note says the 7 MB test file went in pieces, was read back and removed; still yellow, now only for the stuck file', 'Test file (7.0 MB)' in note and 'hatayi gayi' in note
                and 'jaancha nahi gaya' not in why and 'atki hai' in why and await level(['yellow'], 5), (note, why))
            Path(D + 'tus_down').touch()
            await at('storage-big-test').click()
            v = await until('storage-row-big-value', lambda t: t == 'fail')
            err = await text('storage-row-big-error')
            say(f'{size}: big-file route broken while pictures go: the line says fail and why; the badge does not say Supabase is away', v == 'fail' and 'tukde' in err and await text('storage-badge-label') == 'Storage: Supabase'
                and fine(await text('storage-row-supabase-value')) and await level(['yellow'], 5), (v, err, await text('storage-row-supabase-value')))
            await page.screenshot(path=f'{SS}/{size}_bigfail.jpg', quality=40, type='jpeg')
            os.unlink(D + 'tus_down')
            await at('storage-big-test').click()
            v = await until('storage-row-big-value', lambda t: t.startswith('theek'))
            say(f'{size}: route repaired: the next test turns the line back to theek', v.startswith('theek'), v)
        else:
            say(f'{size}: the big-file line still shows the earlier proof', (await text('storage-row-big-value')).startswith('theek'), await text('storage-row-big-value'))
        lines = await text('machine-storage-errors')
        say(f'{size}: Machine lists the last storage failures: which file, which store, which route, why', 'TEST_PICTURE_ATKI · picture' in lines and 'Supabase' in lines and 'chhoti file ka raasta' in lines and '(400)' in lines
            and 'pehle' in lines, lines[:500])
        say(f'{size}: ...and counts them on its own line', (await text('machine-storage-errors-count-value'))[:1].isdigit() and 'aakhri' in await text('machine-storage-errors-count-value'), await text('machine-storage-errors-count-value'))
        speed = await text('storage-speed')
        say(f'{size}: real speed numbers of both stores', 'Supabase: aam taur par' in speed and 'Emergent: aam taur par' in speed and 'jaanch)' in speed, speed)
        Path(D + 'supabase_down').touch(); await page.wait_for_timeout(10500)
        await at('storage-check-now').click()
        red = await level(['red'])
        why = await text('storage-reasons')
        say(f'{size}: Supabase stops answering: RED, "Supabase ka intezaar", the reason, the retry button', red and await text('storage-badge-label') == 'Storage: Supabase ka intezaar' and 'Supabase abhi file nahi le raha' in why
            and await at('storage-retry-now').is_visible() and await text('storage-row-supabase-value') == 'band' and 'bad' in await at('storage-badge').get_attribute('class'), (why, await text('storage-row-supabase-value')))
        await at('storage-reasons').scroll_into_view_if_needed()
        await page.screenshot(path=f'{SS}/{size}_red.jpg', quality=40, type='jpeg')
        if size == 'mob':
            await overflow(page, size + ' badge popover')
            tall = {t: round((await at(t).bounding_box())['height']) for t in ('storage-check-now', 'storage-retry-now', 'machine-storage-errors-toggle') + (('storage-big-test',) if await at('storage-big-test').count() else ())}
            say(f'{size}: the buttons in the box are at least 44 px tall', all(h >= 44 for h in tall.values()), tall)
        os.unlink(D + 'supabase_down')
        await at('storage-retry-now').click()
        back = await level(['yellow', 'green'])
        say(f'{size}: Supabase back + "Abhi phir try karo": not red any more, "Storage: Supabase"', back and await text('storage-badge-label') == 'Storage: Supabase' and fine(await text('storage-row-supabase-value')),
            (await at('storage-badge').get_attribute('data-level'), await text('storage-row-supabase-value')))
        if fix:
            await page.keyboard.press('Escape'); await page.wait_for_timeout(400)
            Path(D + 'returned.txt').write_text('')
            await at(f'type-upload-retry-{PIC}').click()
            done = False
            for _ in range(40):
                await page.wait_for_timeout(1000)
                words = [w.strip() for w in await page.locator('[data-testid^=mock-live-word-]').all_inner_texts()]
                if words.count('Live') == 2 and not await at(f'type-upload-wait-{PIC}').count():
                    done = True; break
            await at('storage-badge').click(); await page.wait_for_selector('[data-testid=storage-check-now]', timeout=10000)
            await at('storage-check-now').click()
            green = await level(['green'])
            why = await text('storage-reasons')
            say(f'{size}: the stuck picture is through (Dobara chalao): the badge is GREEN with its one line', done and green and why == GREEN and 'ok' in (await at('storage-badge').get_attribute('class')).split(),
                (done, await at('storage-badge').get_attribute('data-level'), why))
            await at('storage-reasons').scroll_into_view_if_needed()
            await page.screenshot(path=f'{SS}/{size}_green.jpg', quality=40, type='jpeg')
    finally:
        say(f'{size}: no failed API calls', not [b for b in bad if '/dream' not in b[1]], bad[:4])
        await br.close()


async def main():
    sizes = [s for s in ('desk', 'mob') if s in sys.argv] or ['desk', 'mob']
    async with async_playwright() as pw:
        for i, size in enumerate(sizes):
            await walk(pw, size, i == 0, 'fix' in sys.argv and i == len(sizes) - 1)
    ok = sum(1 for r in RESULT if r[1])
    print('TOTAL', len(RESULT), 'PASS', ok, 'FAIL', len(RESULT) - ok)

asyncio.run(main())
