"""TEST-ONLY (iteration 211 T1): red duplicate note shows right after a NEW upload finishes reading (no cache wait). Master bridge 8770.
Run: python tests/ui_dup_new_upload211.py  (prints the created book id; the bridge DB is disposable)"""
import asyncio, json, shutil, sys, time
sys.path.insert(0, '/app/backend/tests')
from playwright.async_api import async_playwright
from ui_master217_lib import open_as, ok, R, BASE, mongo

C = '/tmp/uibridge/TEST_dup_c.pdf'
shutil.copy('/tmp/uibridge/dup_b.pdf', C); open(C, 'ab').write(b'\n%dupc211\n')


async def main():
    async with async_playwright() as pw:
        br, page, bad, logs = await open_as(pw, 'owner', 1920, 1000)
        try:
            await page.goto(f'{BASE}/super-admin/exam/jee-main/jee-main:mocks'); await page.wait_for_selector('[data-testid="mock-list"]', timeout=30000)
            await page.wait_for_timeout(1500)
            before = await page.locator('[data-testid^="mock-duplicates-"]').count(); print('flagged before', before)
            await page.click('[data-testid="type-upload-pdf"]'); await page.wait_for_selector('[data-testid="upload-dialog"]')
            await page.set_input_files('[data-testid="upload-main-input"]', [C]); await page.check('[data-testid="upload-rights"]')
            await page.click('[data-testid="upload-send"]'); await page.wait_for_selector('[data-testid="upload-dialog"]', state='hidden', timeout=60000)
            t0 = time.time(); st = ''
            while time.time() - t0 < 150:
                st = mongo("(db.tejas_books.findOne({'payload.filename':'TEST_dup_c.pdf'})||{}).state")
                if st and st not in ('uploading', 'received', 'reading', 'matching'): break
                await asyncio.sleep(2)
            print('book state', st, round(time.time() - t0))
            bid = mongo("db.tejas_books.findOne({'payload.filename':'TEST_dup_c.pdf'})._id"); mid = mongo(f"db.tejas_book_mocks.findOne({{book_id:'{bid}'}})._id")
            await page.reload(); await page.wait_for_selector('[data-testid="mock-list"]', timeout=30000); await page.wait_for_timeout(1500)
            sel = f'[data-testid="mock-duplicates-{mid}"]'
            vis = await page.is_visible(sel); txt = await page.text_content(sel) if vis else ''
            after = await page.locator('[data-testid^="mock-duplicates-"]').count()
            print('new mock', mid, 'note', txt, 'flagged after', after)
            ok('new upload: red note shown immediately after reading', vis and txt.startswith('2 sawaal is section mein pehle se hain'), txt)
            ok('new upload: older items now also list it (flag count grows)', after == before + 1, (before, after))
            print('created book', bid)
        finally:
            await br.close()
    print('TOTAL', len(R), 'PASS', sum(1 for _, x in R if x), 'FAIL', sum(1 for _, x in R if not x))

asyncio.run(main())
