"""TEST-ONLY iteration 234 browser walk (packets B + C): the Delete button and its box, the "latke kadam" lines, the pending clean-up line.
/api is routed to tests/delete_bridge234.py (127.0.0.1:8776, cookies in /tmp/uibridge234/bridge.json).
Run: cd /app/backend && python tests/ui_delete234.py [desk|mob] [fix]     ("fix" really deletes two uploads: once per bridge, on the last size)
"""
import asyncio, json, os, sys
from pathlib import Path
os.environ.setdefault('BRIDGE_OUT', '/tmp/uibridge234'); os.environ.setdefault('BRIDGE_PORT', '8776')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.async_api import async_playwright  # noqa: E402
from ui_cut210 import open_as, overflow, BASE, say, RESULT  # noqa: E402

INFO = json.load(open('/tmp/uibridge234/bridge.json'))
SS = '/app/.screenshots/ui234'; os.makedirs(SS, exist_ok=True)
BIG, HUNG, HM, DRAFT, DM, KEEP = INFO['big'], INFO['hung']['book'], INFO['hung']['mock'], INFO['draft']['book'], INFO['draft']['mock'], INFO['keep']['draft']


async def walk(pw, size, fix):
    br, page, bad, logs = await open_as(pw, 'owner', size)
    at = lambda t: page.locator(f'[data-testid={t}]')  # noqa: E731

    async def tall(t):
        box = await at(t).bounding_box()
        return round(box['height']) if box else 0
    try:
        await page.goto(BASE + INFO['type']); await page.wait_for_selector(f'[data-testid=type-upload-{BIG}]', timeout=25000)
        say(f'{size}: stuck big PDF row: Atki hai, with Dobara chalao AND Delete', (await at(f'type-upload-state-{BIG}').inner_text()).strip() == 'Atki hai'
            and await at(f'type-upload-retry-{BIG}').is_visible() and await at(f'type-upload-delete-{BIG}').is_visible(), await at(f'type-upload-state-{BIG}').inner_text())
        note = await at(f'type-upload-wait-{HUNG}').inner_text()
        say(f'{size}: hung PDF row says its work went silent again and again, with the reason and the hourly try', await at(f'type-upload-wait-{HUNG}').get_attribute('data-kind') == 'hang'
            and 'latak gaya' in note and '3 baar' in note and 'Har ghante' in note and 'Supabase mein nahi' not in note, note)
        alert = await at(f'type-upload-alert-{HUNG}').inner_text() if await at(f'type-upload-alert-{HUNG}').count() else ''
        say(f'{size}: its 15-minute alert speaks of the PDF not moving, not of Supabase', 'aage nahi badhi' in alert and 'Supabase' not in alert, alert)
        text = await at(f'mock-stuck-{HM}').inner_text() if await at(f'mock-stuck-{HM}').count() else ''
        say(f'{size}: the hung PDF\'s mock says Atki hai (not "Live ho raha hai")', (await at(f'mock-live-word-{HM}').inner_text()).strip() == 'Atki hai' and 'latak gaya' in text, text)
        await at(f'mock-status-{KEEP}').click(); await page.wait_for_selector(f'[data-testid=mock-library-{KEEP}]', timeout=8000)
        say(f'{size}: Draft mock of a PDF that reached students: NO "Is PDF ko delete karo"', await at(f'mock-delete-upload-{KEEP}').count() == 0)
        await page.keyboard.press('Escape'); await page.wait_for_timeout(300)
        await at(f'mock-status-{DM}').click(); await page.wait_for_selector(f'[data-testid=mock-delete-upload-{DM}]', timeout=8000)
        say(f'{size}: Draft mock of a PDF that never reached students: the menu offers "Is PDF ko delete karo…"', 'Is PDF ko delete karo' in await at(f'mock-delete-upload-{DM}').inner_text(), await tall(f'mock-delete-upload-{DM}'))
        await page.wait_for_timeout(400)  # the menu opens with a short zoom; it is measured once it stands still
        if size == 'mob':
            say(f'{size}: menu item and row Delete button are at least 44 px tall', await tall(f'mock-delete-upload-{DM}') >= 44, await tall(f'mock-delete-upload-{DM}'))
        await at(f'mock-delete-upload-{DM}').click(); await page.wait_for_selector('[data-testid=upload-delete-facts]', timeout=10000)
        facts, kept = await at('upload-delete-facts').inner_text(), await at('upload-delete-kept').inner_text()
        say(f'{size}: the box names the PDF, counts what leaves, then says what stays', (await at('upload-delete-title').inner_text()).strip() == 'TEST_DRAFT_PDF' and '1 Draft mock' in await at('upload-delete-mocks').inner_text()
            and 'page' in await at('upload-delete-pages').inner_text() and 'Supabase se hategi' in await at('upload-delete-original').inner_text() and 'wapas nahi' in facts
            and 'JEE Main PYQ' in kept and 'dobara upload' in kept, (facts, kept))
        say(f'{size}: "Hamesha ke liye delete karo" is off until DELETE is typed', await at('upload-delete-confirm').is_disabled())
        await at('upload-delete-input').fill('delete')
        off = await at('upload-delete-confirm').is_disabled()
        await at('upload-delete-input').fill('DELETE')
        say(f'{size}: small letters do not arm it; DELETE does', off and await at('upload-delete-confirm').is_enabled())
        if size == 'mob':
            await overflow(page, size + ' delete box')
            say(f'{size}: the box\'s input and buttons are at least 44 px tall', min(await tall('upload-delete-input'), await tall('upload-delete-confirm'), await tall('upload-delete-cancel')) >= 44,
                [await tall('upload-delete-input'), await tall('upload-delete-confirm'), await tall('upload-delete-cancel')])
        await page.screenshot(path=f'{SS}/{size}_box.jpg', quality=40, type='jpeg')
        if fix:
            await at('upload-delete-confirm').click()
            gone = False
            for _ in range(30):
                await page.wait_for_timeout(500)
                if not await at(f'mock-row-{DM}').count() and not await at('upload-delete-dialog').count():
                    gone = True; break
            say(f'{size}: DELETE typed and pressed: the box closes and the Draft mock leaves the list, no page reload', gone)
            await at(f'type-upload-delete-{BIG}').click(); await page.wait_for_selector('[data-testid=upload-delete-facts]', timeout=10000)
            say(f'{size}: stuck PDF: the box says the half-sent PDF pieces on the server leave', '0 Draft mock' in await at('upload-delete-mocks').inner_text() and 'Server par pade' in await at('upload-delete-original').inner_text(),
                await at('upload-delete-facts').inner_text())
            await at('upload-delete-input').fill('DELETE'); await at('upload-delete-confirm').click()
            gone = False
            for _ in range(30):
                await page.wait_for_timeout(500)
                if not await at(f'type-upload-{BIG}').count():
                    gone = True; break
            say(f'{size}: the stuck upload\'s row leaves the Uploads list at once', gone)
            say(f'{size}: the other rows are untouched (hung PDF row, Live mock, kept Draft)', await at(f'type-upload-{HUNG}').count() == 1 and await at(f"mock-row-{INFO['keep']['live']}").count() == 1 and await at(f'mock-row-{KEEP}').count() == 1)
        else:
            await at('upload-delete-cancel').click(); await page.wait_for_timeout(400)
            say(f'{size}: Cancel closes the box and nothing is deleted', not await at('upload-delete-dialog').count() and await at(f'mock-row-{DM}').count() == 1)
        if size == 'mob':
            await overflow(page, size + ' type page')
        await page.screenshot(path=f'{SS}/{size}_type.jpg', quality=40, type='jpeg')
        # The AITS days screen: the same Delete, as a small dustbin on a paper whose PDF never reached students.
        A = INFO['aits']; AD, AK = A['draft'], A['kept']
        await page.goto(BASE + A['path']); await page.wait_for_selector(f'[data-testid=series-paper-{AD}]', timeout=25000)
        say(f'{size}: AITS: the paper of a PDF that never reached students has the dustbin; the paper of one that did has none',
            await at(f'series-paper-delete-{AD}').count() == 1 and await at(f'series-paper-{AK}').count() == 1 and await at(f'series-paper-delete-{AK}').count() == 0)
        if size == 'mob':
            box = await at(f'series-paper-delete-{AD}').bounding_box()
            say(f'{size}: AITS: the dustbin is at least 44 px each way', min(box['width'], box['height']) >= 44, box)
        await at(f'series-paper-delete-{AD}').click(); await page.wait_for_selector('[data-testid=upload-delete-facts]', timeout=10000)
        say(f'{size}: AITS: the same box opens, names that PDF, and is off until DELETE is typed', (await at('upload-delete-title').inner_text()).strip() == 'TEST_AITS_DRAFT_PDF'
            and await at('upload-delete-confirm').is_disabled(), await at('upload-delete-title').inner_text())
        if fix:
            await at('upload-delete-input').fill('DELETE'); await at('upload-delete-confirm').click()
            gone = False
            for _ in range(30):
                await page.wait_for_timeout(500)
                if not await at(f'series-paper-{AD}').count() and not await at('upload-delete-dialog').count():
                    gone = True; break
            say(f'{size}: AITS: DELETE typed and pressed: that paper leaves the list, the other paper stays', gone and await at(f'series-paper-{AK}').count() == 1)
        else:
            await at('upload-delete-cancel').click(); await page.wait_for_timeout(400)
            say(f'{size}: AITS: Cancel closes the box and the paper stays', not await at('upload-delete-dialog').count() and await at(f'series-paper-{AD}').count() == 1)
        if size == 'mob':
            await overflow(page, size + ' AITS page')
        await page.screenshot(path=f'{SS}/{size}_aits.jpg', quality=40, type='jpeg')
        await page.click('[data-testid=storage-badge]'); await page.wait_for_selector('[data-testid=machine-panel]', timeout=10000); await page.wait_for_timeout(900)
        say(f'{size}: Machine: "Latke kadam (24 ghante)" 1, the hung PDF listed with Dobara chalao, the last silent step named', (await at('machine-step-hangs-value').inner_text()).strip() == '1'
            and await at(f'machine-hung-{HUNG}').count() == 1 and await at(f'machine-retry-{HUNG}').count() == 1 and 'publish_ready' in await at('machine-step-hang-last').inner_text(),
            await at('machine-step-hangs-value').inner_text())
        say(f'{size}: Machine: "Delete ki safai baaki" 1 with the reason', (await at('machine-delete-pending-value').inner_text()).strip() == '1' and 'TEST_SAFAI_BAAKI' in await at('machine-delete-note').inner_text()
            and 'Supabase' in await at('machine-delete-note').inner_text(), await at('machine-delete-pending-value').inner_text())
        await at('machine-delete-pending').scroll_into_view_if_needed()
        await page.screenshot(path=f'{SS}/{size}_machine.jpg', quality=40, type='jpeg')
    finally:
        say(f'{size}: no failed API calls, no page errors', not [b for b in bad if '/dream' not in b[1]] and not [x for x in logs if 'PAGEERROR' in x], (bad[:4], logs[:3]))
        await br.close()


async def main():
    sizes = [s for s in ('desk', 'mob') if s in sys.argv] or ['desk', 'mob']
    async with async_playwright() as pw:
        for i, size in enumerate(sizes):
            await walk(pw, size, 'fix' in sys.argv and i == len(sizes) - 1)
    ok = sum(1 for r in RESULT if r[1])
    print('TOTAL', len(RESULT), 'PASS', ok, 'FAIL', len(RESULT) - ok)

asyncio.run(main())
