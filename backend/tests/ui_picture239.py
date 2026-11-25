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
        if size == 'mob':
            await overflow(page, size + ' type page')
        await at(f'type-upload-{BOOK}').scroll_into_view_if_needed()
        await page.screenshot(path=f'{SS}/{size}_type.jpg', quality=40, type='jpeg')
        await at(f'mock-stuck-{MID}').scroll_into_view_if_needed()
        await page.screenshot(path=f'{SS}/{size}_mocks.jpg', quality=40, type='jpeg')
        await page.click('[data-testid=storage-badge]'); await page.wait_for_selector('[data-testid=machine-panel]', timeout=10000); await page.wait_for_timeout(800)
        line = await text(f'machine-storage-stuck-{BOOK}')
        say(f'{size}: machine panel counts 2 stuck files and lists them with Dobara chalao', await text('machine-storage-stuck-value') == '2' and await at(f'machine-retry-{BOOK}').count() == 1
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
