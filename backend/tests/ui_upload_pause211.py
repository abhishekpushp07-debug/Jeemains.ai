"""TEST-ONLY (iteration 211 T1): Upload dialog 'Clear all' + Pause info toast (master bridge 8770). Run: python tests/ui_upload_pause211.py
Creates at most one book (TEST_pause_a.pdf) and prints its id for cleanup."""
import asyncio, json, shutil, sys, time
sys.path.insert(0, '/app/backend/tests')
from playwright.async_api import async_playwright
from ui_master217_lib import open_as, ok, R, BASE, SS, mongo

A, Bp = '/tmp/uibridge/TEST_pause_a.pdf', '/tmp/uibridge/TEST_pause_b.pdf'
for src, dst in (('/tmp/uibridge/dup_a.pdf', A), ('/tmp/uibridge/dup_b.pdf', Bp)):
    shutil.copy(src, dst); open(dst, 'ab').write(b'\n%pause211\n')


async def main():
    posts = []

    async def extra(route, req):
        if req.method == 'POST' and req.url.split('?')[0].endswith('/api/admin/books'):
            posts.append(json.loads(req.post_data or '{}').get('filename'))
            await asyncio.sleep(3)  # slow the first PDF so Pause can be pressed while busy
        return False
    async with async_playwright() as pw:
        br, page, bad, logs = await open_as(pw, 'owner', 1920, 1000, extra)
        try:
            await page.goto(f'{BASE}/super-admin/exam/jee-main/jee-main:mocks'); await page.wait_for_selector('[data-testid="type-upload-pdf"]', timeout=30000)
            await page.click('[data-testid="type-upload-pdf"]'); await page.wait_for_selector('[data-testid="upload-dialog"]')
            await page.set_input_files('[data-testid="upload-main-input"]', [A, Bp]); await page.wait_for_selector('[data-testid="upload-batch-list"]', timeout=5000)
            ok('clear: button visible when not busy', await page.is_visible('[data-testid="upload-batch-clear"]'))
            await page.click('[data-testid="upload-batch-clear"]'); await page.wait_for_timeout(400)
            ok('clear: batch list emptied', not await page.is_visible('[data-testid="upload-batch-list"]'))
            bt = (await page.text_content('[data-testid="upload-send"]')).strip()
            ok('clear: back to single mode (button "Upload", title field)', bt == 'Upload' and await page.is_visible('[data-testid="upload-title"]'), bt)
            ok('clear: nothing posted', posts == [], posts)
            # Pause while the first PDF is being sent
            await page.set_input_files('[data-testid="upload-main-input"]', [A, Bp]); await page.wait_for_selector('[data-testid="upload-batch-list"]', timeout=5000)
            await page.check('[data-testid="upload-rights"]'); await page.click('[data-testid="upload-send"]')
            await page.wait_for_selector('[data-testid="upload-pause"]', timeout=5000)
            ok('pause: Clear all hidden while busy', not await page.is_visible('[data-testid="upload-batch-clear"]'))
            await page.click('[data-testid="upload-pause"]')
            t0 = time.time(); toasts = []
            while time.time() - t0 < 40:
                toasts = await page.evaluate("() => [...document.querySelectorAll('[data-sonner-toast]')].map(t => (t.dataset.type||'') + ':' + t.textContent)")
                if any('PDF' in t for t in toasts): break
                await page.wait_for_timeout(300)
            print('toasts', toasts, 'posts', posts)
            ok('pause: info toast "Paused: 1 of 2 PDFs sent"', any(t.startswith('info:') and 'Paused: 1 of 2 PDFs sent' in t for t in toasts), toasts)
            ok('pause: second PDF not posted', posts == ['TEST_pause_a.pdf'], posts)
            still = await page.is_visible('[data-testid="upload-dialog"]')
            bt = (await page.text_content('[data-testid="upload-send"]')).strip() if still else ''
            ok('pause: dialog open, button "Upload 1 PDF"', still and bt == 'Upload 1 PDF', bt)
            await page.screenshot(path=f'{SS}/upload-paused.jpg', quality=40)
            if still: await page.click('[data-testid="upload-cancel"]')
            ok('no page errors', not logs, logs[:3])
        finally:
            await br.close()
    print('created', mongo("JSON.stringify(db.tejas_books.find({'payload.filename':/^TEST_pause_/},{_id:1}).toArray())"))
    print('TOTAL', len(R), 'PASS', sum(1 for _, x in R if x), 'FAIL', sum(1 for _, x in R if not x))

asyncio.run(main())
