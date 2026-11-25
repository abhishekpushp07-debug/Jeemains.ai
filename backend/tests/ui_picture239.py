"""TEST-ONLY iteration 239 browser walk (Packet E step 2): Super Admin says "Atki hai: pictures storage mein saabit nahi hui" with the count
on the upload, its mock and the machine panel; a proven Live mock says "Pictures: n / n · Storage: Supabase"; Dobara chalao makes the mock
Live once Supabase keeps the pictures. /api is routed to tests/picture_bridge239.py (127.0.0.1:8778, cookies in /tmp/uibridge239/bridge.json).
Run: cd /app/backend && python tests/ui_picture239.py [desk|mob] [fix]     ("fix" empties vanish.txt and presses Dobara chalao: once per bridge)
"""
import asyncio, json, os, sys
from pathlib import Path
os.environ.setdefault('BRIDGE_OUT', '/tmp/uibridge239'); os.environ.setdefault('BRIDGE_PORT', '8778')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.async_api import async_playwright  # noqa: E402
from ui_cut210 import open_as, overflow, BASE, say, RESULT  # noqa: E402

D = '/tmp/uibridge239/'
INFO = json.load(open(D + 'bridge.json'))
SS = '/app/.screenshots/ui239'; os.makedirs(SS, exist_ok=True)
OK, PRF, PAIR = INFO['ok'], INFO['proof'], INFO['two']
BOOK, MID = PRF['book'], PRF['mock']
WHY = f"{PRF['pictures']} pictures storage me nahi mili"
LINE = lambda n: f'Pictures: {n} / {n} · Storage: Supabase'  # noqa: E731


async def walk(pw, size, fix):
    br, page, bad, _ = await open_as(pw, 'owner', size)
    at = lambda t: page.locator(f'[data-testid={t}]')  # noqa: E731

    async def text(t):
        return (await at(t).inner_text()).strip() if await at(t).count() else ''
    try:
        await page.goto(BASE + INFO['type']); await page.wait_for_selector(f'[data-testid=type-upload-{BOOK}]', timeout=25000)
        note = await text(f'type-upload-wait-{BOOK}')
        say(f'{size}: the upload row chip says Atki hai', await text(f'type-upload-state-{BOOK}') == 'Atki hai', await text(f'type-upload-state-{BOOK}'))
        say(f'{size}: the upload row says the pictures were not proven: the mock\'s name, how many, the 15-minute retry', await at(f'type-upload-wait-{BOOK}').get_attribute('data-kind') == 'stuck'
            and 'Atki hai' in note and f'"{PRF["label"]}" ki pictures storage mein saabit nahi hui' in note and WHY in note and '15 minute' in note, note)
        say(f'{size}: ...and does not blame a picture "not going into Supabase"', 'Supabase mein nahi ja rahi' not in note and 'Emergent mein kuch nahi gaya' not in note, note)
        alert = await text(f'type-upload-alert-{BOOK}')
        say(f'{size}: the 15-minute alert inside the upload row speaks of the proof', 'minute se' in alert and 'is mock ki pictures saabit nahi hui' in alert, alert)
        say(f'{size}: the row offers Dobara chalao, not "Abhi phir try karo"', await at(f'type-upload-retry-{BOOK}').is_visible() and not await at(f'type-upload-wait-retry-{BOOK}').count())
        note = await text(f"type-upload-wait-{PAIR['book']}")
        say(f'{size}: PDF with two unproven mocks: its row names the first and counts the other; no alert before 15 minutes', f"\"{PAIR['first']}\" aur 1 doosre mock ki pictures storage mein saabit nahi hui" in note
            and 'pictures storage me nahi mili' in note and not await at(f"type-upload-alert-{PAIR['book']}").count(), note)
        row = await text(f'mock-stuck-{MID}')
        say(f'{size}: the mock\'s own row: Atki hai, pictures not proven, how many, Dobara chalao', 'Atki hai' in await text(f'mock-status-{MID}') and await text(f'mock-live-word-{MID}') == 'Atki hai'
            and 'iski pictures storage mein saabit nahi hui' in row and WHY in row and 'Dobara chalao' in row and 'ek picture Supabase mein nahi ja rahi' not in row, row)
        both = [await text(f'mock-stuck-{m}') for m in PAIR['mocks']]
        say(f'{size}: each of the two mocks of the other PDF says the same with its own count', all('saabit nahi hui' in t and 'pictures storage me nahi mili' in t for t in both), both)
        say(f'{size}: the proven Live mock says "{LINE(OK["pictures"])}"', await text(f"mock-pictures-{OK['set']}") == LINE(OK['pictures']), await text(f"mock-pictures-{OK['set']}"))
        say(f'{size}: an unproven mock has no "Pictures" line', await page.locator('[data-testid^=mock-pictures-]').count() == 1, await page.locator('[data-testid^=mock-pictures-]').count())
        words = [w.strip() for w in await page.locator('[data-testid^=mock-live-word-]').all_inner_texts()]
        say(f'{size}: one mock is Live, three say Atki hai', words.count('Live') == 1 and words.count('Atki hai') == 3, words)
        # Packet E step 3: the mock whose chosen time went by is Draft again, says which time, and is not called stuck.
        L = INFO['late']; gone = await text(f"mock-missed-{L['mock']}")
        say(f'{size}: the mock whose chosen time passed: chip "Draft · samay nikal gaya", switch Off and usable', 'Draft · samay nikal gaya' in await text(f"mock-status-{L['mock']}")
            and await text(f"mock-live-word-{L['mock']}") == 'Off' and await at(f"mock-live-switch-{L['mock']}").is_enabled(), (await text(f"mock-status-{L['mock']}"), await text(f"mock-live-word-{L['mock']}")))
        say(f'{size}: ...its row gives the time that passed, says it will not open late by itself, and what to press', 'Chuna hua samay (' in gone and 'IST) nikal gaya' in gone and 'isliye yeh Live nahi hua' in gone
            and 'der se apne aap nahi khulega' in gone and 'Live karo' in gone and 'naya samay chuniye' in gone, gone)
        say(f'{size}: ...it is not called stuck and its PDF is not in the waiting uploads', not await at(f"mock-stuck-{L['mock']}").count() and not await at(f"type-upload-{L['book']}").count()
            and await page.locator('[data-testid^=mock-missed-]').count() == 1, await page.locator('[data-testid^=mock-missed-]').count())
        await at(f"mock-missed-{L['mock']}").scroll_into_view_if_needed()
        await page.screenshot(path=f'{SS}/{size}_late.jpg', quality=40, type='jpeg')
        if size == 'mob':
            await overflow(page, size + ' type page')
        await at(f'type-upload-{BOOK}').scroll_into_view_if_needed()
        await page.screenshot(path=f'{SS}/{size}_type.jpg', quality=40, type='jpeg')
        await at(f'mock-stuck-{MID}').scroll_into_view_if_needed()
        await page.screenshot(path=f'{SS}/{size}_mocks.jpg', quality=40, type='jpeg')
        await page.click('[data-testid=storage-badge]'); await page.wait_for_selector('[data-testid=machine-panel]', timeout=10000); await page.wait_for_timeout(800)
        line = await text(f'machine-storage-stuck-{BOOK}')
        say(f'{size}: machine panel counts 3 stuck files (two of this type, one of the test series) and lists them with Dobara chalao', await text('machine-storage-stuck-value') == '3' and await at(f"machine-storage-stuck-{INFO['aits']['book']}").count() == 1 and await at(f'machine-retry-{BOOK}').count() == 1
            and await at(f"machine-storage-stuck-{PAIR['book']}").count() == 1, await text('machine-storage-stuck-value'))
        say(f'{size}: machine panel says the pictures were not proven, with the count', f'"{PRF["label"]}" ki pictures storage mein saabit nahi hui' in line and WHY in line and 'Supabase mein nahi ja rahi' not in line, line)
        say(f'{size}: machine panel counts the other PDF\'s second mock', 'aur 1 doosre mock ki pictures storage mein saabit nahi hui' in await text(f"machine-storage-stuck-{PAIR['book']}"), await text(f"machine-storage-stuck-{PAIR['book']}"))
        await at('machine-storage-stuck-list').scroll_into_view_if_needed()
        await page.screenshot(path=f'{SS}/{size}_machine.jpg', quality=40, type='jpeg')
        if fix:
            await page.keyboard.press('Escape'); Path(D + 'vanish.txt').write_text('')
            await at(f'type-upload-retry-{BOOK}').click()
            done = False
            for _ in range(60):
                await page.wait_for_timeout(1000)
                words = [w.strip() for w in await page.locator('[data-testid^=mock-live-word-]').all_inner_texts()]
                if words.count('Live') == 2 and not await at(f'type-upload-wait-{BOOK}').count():
                    done = True; break
            lines = [t.strip() for t in await page.locator('[data-testid^=mock-pictures-]').all_inner_texts()]
            say(f'{size}: Supabase keeps the pictures + Dobara chalao: the mock is Live, the stuck note is gone, no page reload', done and not await at(f'mock-stuck-{MID}').count(), words)
            say(f'{size}: ...and its row now says "{LINE(PRF["pictures"])}"', sorted(lines) == sorted([LINE(OK['pictures']), LINE(PRF['pictures'])]), lines)
            await page.screenshot(path=f'{SS}/{size}_fixed.jpg', quality=40, type='jpeg')
            await at(f"mock-live-switch-{L['mock']}").click()
            done = False
            for _ in range(60):
                await page.wait_for_timeout(1000)
                words = [w.strip() for w in await page.locator('[data-testid^=mock-live-word-]').all_inner_texts()]
                if words.count('Live') == 3 and not await page.locator('[data-testid^=mock-missed-]').count():
                    done = True; break
            say(f'{size}: Live karo on the mock whose time passed: it goes Live now and the note is gone, no page reload', done, words)
            await page.screenshot(path=f'{SS}/{size}_late_live.jpg', quality=40, type='jpeg')
        # The All India Test Series page of the same exam: day 1 has its paper, day 2's paper waits for its pictures.
        A = INFO['aits']; why = f"{A['pictures']} pictures storage me nahi mili"
        await page.goto(BASE + A['type']); await page.wait_for_selector('[data-testid=series-day-list]', timeout=25000)
        await page.wait_for_selector(f"[data-testid=type-upload-{A['book']}]", timeout=25000)
        note = await text(f"type-upload-wait-{A['book']}")
        say(f'{size}: series page: the PDF above the days says Atki hai, pictures not proven, with the count', await text(f"type-upload-state-{A['book']}") == 'Atki hai'
            and f'"{A["label"]}" ki pictures storage mein saabit nahi hui' in note and why in note and await at(f"type-upload-retry-{A['book']}").is_visible(), note)
        line, day2 = await text('series-day-stuck-2'), await text('series-day-2')
        say(f'{size}: series page: day 2 says why its paper is not ready and how to try again', 'Atki hai' in line and 'iski pictures storage mein saabit nahi hui' in line and 'is din ka paper abhi taiyaar nahi hua' in line
            and why in line and '15 minute' in line and 'Dobara chalao' in line and 'Live nahi hua' not in line, line)
        say(f'{size}: series page: day 2 names the paper and no longer says "taiyaar ho raha hai"', A['label'] in day2 and 'taiyaar ho raha hai' not in day2, day2)
        say(f'{size}: series page: day 1 has its built paper with the Live switch and no stuck note', await at('series-day-live-1').count() == 1 and not await at('series-day-stuck-1').count()
            and await page.locator('[data-testid^=series-day-stuck-]').count() == 1, await page.locator('[data-testid^=series-day-stuck-]').count())
        if size == 'mob':
            await overflow(page, size + ' series page')
        await at('series-day-2').scroll_into_view_if_needed()
        await page.screenshot(path=f'{SS}/{size}_series.jpg', quality=40, type='jpeg')
        if fix:
            await at(f"type-upload-retry-{A['book']}").click()
            done = False
            for _ in range(60):
                await page.wait_for_timeout(1000)
                if await at('series-day-live-2').count() and not await at('series-day-stuck-2').count():
                    done = True; break
            say(f'{size}: series page: Supabase keeps the pictures + Dobara chalao: day 2 has its paper, the stuck note is gone, no page reload', done and not await at(f"type-upload-wait-{A['book']}").count(), await text('series-day-2'))
            await page.screenshot(path=f'{SS}/{size}_series_fixed.jpg', quality=40, type='jpeg')
    finally:
        say(f'{size}: no failed API calls', not [b for b in bad if '/dream' not in b[1]], bad[:4])
        await br.close()


async def main():
    sizes = [s for s in ('desk', 'mob') if s in sys.argv] or ['desk', 'mob']
    async with async_playwright() as pw:
        for i, size in enumerate(sizes):
            await walk(pw, size, 'fix' in sys.argv and i == len(sizes) - 1)
    ok = sum(1 for r in RESULT if r[1])
    print('TOTAL', len(RESULT), 'PASS', ok, 'FAIL', len(RESULT) - ok)

asyncio.run(main())
