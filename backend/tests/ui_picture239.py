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
    HD = INFO['hold']

    def unhide(wid):
        """TEST: "Supabase" has this test's photos again."""
        keep = [x for x in Path(D + 'gone.txt').read_text().split('\n') if x.strip() and wid not in x]
        Path(D + 'gone.txt').write_text(''.join(x + '\n' for x in keep))

    async def calm():
        for _ in range(40):   # a note that is still on screen can lie over a button on a phone
            if not await page.locator('[data-sonner-toast]').count():
                return
            await page.wait_for_timeout(500)

    async def becomes(t, word, secs=45):
        for _ in range(secs):
            if await text(t) == word:
                return True
            await page.wait_for_timeout(1000)
        return False
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
        # Packet E, the remaining doors: day 3's paper was switched Off and then asked to go Live while its photo is gone.
        line = await text(f"series-day-pictures-{HD['day']}")
        say(f"{size}: series page: a day's paper asked to go Live again while its photo is gone: still Off, the day says why and offers Dobara chalao", await text(f"series-day-live-word-{HD['day']}") == 'Off'
            and await at(f"series-day-pictures-{HD['day']}").get_attribute('data-state') == 'stuck' and 'isliye yeh Live nahi hua (Off hi hai)' in line and '1 picture storage me nahi mili (Q4)' in line
            and '15 minute' in line and await at(f"series-day-pictures-retry-{HD['day']}").is_visible(), line)
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
            unhide(HD['series']); await calm()
            await at(f"series-day-pictures-retry-{HD['day']}").click()
            done = await becomes(f"series-day-live-word-{HD['day']}", 'Live')
            say(f"{size}: series page: the photo is back + Dobara chalao: day 3's paper is Live again and the note is gone, no page reload", done and not await at(f"series-day-pictures-{HD['day']}").count(), await text(f"series-day-{HD['day']}"))
            await page.screenshot(path=f'{SS}/{size}_series_fixed.jpg', quality=40, type='jpeg')
        # Written mocks (a type of their own): a photo that is not in storage keeps the mock a Draft and the owner is told which question.
        W = INFO['written']
        await page.goto(BASE + W['type']); await page.wait_for_selector(f"[data-testid=mock-row-{W['bad']}]", timeout=25000)
        say(f'{size}: written page: the healthy written mock is Live', await text(f"mock-live-word-{W['ok']}") == 'Live', await text(f"mock-live-word-{W['ok']}"))
        await at(f"mock-live-switch-{W['bad']}").click()
        note = page.locator('[data-sonner-toast]').filter(has_text='mock nahi badle').first
        await note.wait_for(timeout=15000)
        told = (await note.inner_text()).strip()
        say(f'{size}: written page: Live karo on the mock whose photo is not in storage: the owner is told which question and what to do', 'Q2 ki photo storage mein nahi mili' in told
            and 'isliye yeh Live nahi hua (Draft hi hai)' in told and 'dobara lagaiye' in told, told)
        await page.wait_for_timeout(800)   # the note has slid in fully, so the picture shows what the owner reads
        await page.screenshot(path=f'{SS}/{size}_written.jpg', quality=40, type='jpeg')
        await page.wait_for_timeout(6000)
        say(f'{size}: written page: the reason is still on screen 6 seconds later', await note.is_visible())
        say(f'{size}: written page: that mock is still a Draft with its switch Off; the other one is still Live', 'Draft' in await text(f"mock-status-{W['bad']}") and await text(f"mock-live-word-{W['bad']}") == 'Off'
            and await text(f"mock-live-word-{W['ok']}") == 'Live', (await text(f"mock-status-{W['bad']}"), await text(f"mock-live-word-{W['bad']}")))
        # Packet E, the remaining doors: a built test that is switched on again stays Off until its pictures are proven, and its row says why.
        why = await text(f"mock-pictures-wait-{HD['bad']}")
        say(f'{size}: hold: an Off test asked to go Live while its photo is gone: chip "Off · pictures saabit nahi hui", switch still Off', 'Off · pictures saabit nahi hui' in await text(f"mock-status-{HD['bad']}")
            and await text(f"mock-live-word-{HD['bad']}") == 'Off', (await text(f"mock-status-{HD['bad']}"), await text(f"mock-live-word-{HD['bad']}")))
        say(f'{size}: hold: its row says why it is still Off, names the question and the 15-minute retry, and offers Dobara chalao', await at(f"mock-pictures-wait-{HD['bad']}").get_attribute('data-state') == 'stuck'
            and 'isliye yeh Live nahi hua (Off hi hai)' in why and '1 picture storage me nahi mili (Q2)' in why and '15 minute' in why and await at(f"mock-pictures-retry-{HD['bad']}").is_visible(), why)
        say(f'{size}: hold: that row has no "Pictures: n / n" line; a healthy Off test has no note', not await at(f"mock-pictures-{HD['bad']}").count() and not await at(f"mock-pictures-wait-{HD['ok']}").count()
            and await text(f"mock-live-word-{HD['ok']}") == 'Off', await text(f"mock-live-word-{HD['ok']}"))
        chk = await text(f"mock-pictures-wait-{HD['checking']}")
        say(f'{size}: hold: a test whose pictures are being checked: chip "Off · pictures ki jaanch"; the row says it goes Live by itself', 'Off · pictures ki jaanch' in await text(f"mock-status-{HD['checking']}")
            and 'jaanchi ja rahi hain' in chk and 'apne aap Live ho jayega' in chk and 'Tab tak Off hai' in chk, chk)
        late = await text(f"mock-pictures-wait-{HD['missed']}")
        say(f'{size}: hold: a test whose chosen time passed while it waited: chip "Off · samay nikal gaya"; it will not open late; no Dobara chalao', 'Off · samay nikal gaya' in await text(f"mock-status-{HD['missed']}")
            and 'der se apne aap nahi khulega' in late and not await at(f"mock-pictures-retry-{HD['missed']}").count(), late)
        await at(f"mock-pictures-wait-{HD['bad']}").scroll_into_view_if_needed()
        await page.screenshot(path=f'{SS}/{size}_hold.jpg', quality=40, type='jpeg')
        await calm()
        await page.click('[data-testid=storage-badge]'); await page.wait_for_selector('[data-testid=storage-reasons]', timeout=10000); await page.wait_for_timeout(600)
        badge = await text('storage-reasons')
        say(f'{size}: hold: the storage badge says tests are Off because their pictures were not proven, and where the reason is', 'test ki pictures storage mein saabit nahi hui, isliye woh Off hain' in badge
            and 'us test ki row mein hai' in badge, badge)
        await page.keyboard.press('Escape')
        if size == 'mob':
            await overflow(page, size + ' written page')
        # The Library: a test that was Live comes back Off until its pictures are proven.
        await page.goto(BASE + '/super-admin/library'); await page.wait_for_selector(f"[data-testid=library-restore-{HD['lib']}]", timeout=25000)
        if size == 'mob':
            await overflow(page, size + ' library page')
        await at(f"library-restore-{HD['lib']}").click()
        await page.wait_for_selector('[data-testid=library-restore-confirm-dialog]', timeout=10000)
        told = await text('library-restore-live')
        say(f'{size}: Library: before a Live test is restored, the box says students see it only once its pictures are proven', 'as soon as its pictures are proven in storage' in told
            and 'stays Off and its row says why' in told, told)
        await page.wait_for_timeout(400)
        await page.screenshot(path=f'{SS}/{size}_library_box.jpg', quality=40, type='jpeg')
        if not fix:
            await at('library-restore-cancel').click()
        else:
            await at('library-restore-confirm').click()
            note = page.locator('[data-sonner-toast]').filter(has_text='Off hain kyunki').first
            await note.wait_for(timeout=25000)
            told = (await note.inner_text()).strip()
            say(f'{size}: Library: restored while its photo is gone: the owner is told it came back Off and where the reason is', '1 test back where it came from' in told
                and '1 test Off hain kyunki unki pictures storage mein saabit nahi hui' in told and 'Dobara chalao' in told, told)
            await page.wait_for_timeout(600)
            await page.screenshot(path=f'{SS}/{size}_library_told.jpg', quality=40, type='jpeg')
            await page.goto(BASE + HD['type']); await page.wait_for_selector(f"[data-testid=mock-row-{HD['lib']}]", timeout=25000)
            why = await text(f"mock-pictures-wait-{HD['lib']}")
            say(f'{size}: Library: the test is back in its type, Off, and its row says it did not return to how it was, with the reason', await text(f"mock-live-word-{HD['lib']}") == 'Off'
                and 'isliye yeh apni purani haalat mein nahi lauta (Off hi hai)' in why and '1 picture storage me nahi mili (Q2)' in why and await at(f"mock-pictures-retry-{HD['lib']}").is_visible(), why)
            await at(f"mock-live-switch-{HD['ok']}").click()
            done = await becomes(f"mock-live-word-{HD['ok']}", 'Live')
            say(f'{size}: hold: Live karo on a healthy Off test: Live, with no note, no page reload', done and not await at(f"mock-pictures-wait-{HD['ok']}").count(), await text(f"mock-status-{HD['ok']}"))
            unhide(HD['bad']); await calm()
            await at(f"mock-pictures-retry-{HD['bad']}").click()
            done = await becomes(f"mock-live-word-{HD['bad']}", 'Live')
            say(f'{size}: hold: the photo is back + Dobara chalao: the test is Live and the note is gone, no page reload', done and not await at(f"mock-pictures-wait-{HD['bad']}").count(), await text(f"mock-status-{HD['bad']}"))
            unhide(HD['lib']); await calm()
            await at(f"mock-pictures-retry-{HD['lib']}").click()
            done = await becomes(f"mock-live-word-{HD['lib']}", 'Live')
            say(f'{size}: Library: the photo is back + Dobara chalao: the restored test is Live again, as before the Library', done and not await at(f"mock-pictures-wait-{HD['lib']}").count(), await text(f"mock-status-{HD['lib']}"))
            await at(f"mock-row-{HD['bad']}").scroll_into_view_if_needed()
            await page.screenshot(path=f'{SS}/{size}_hold_fixed.jpg', quality=40, type='jpeg')
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
