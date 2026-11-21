"""TEST-ONLY (iteration 212 T1): batch Pause retest on master bridge 8770.
S1: Pause while PDF 1 of 2 is in flight -> row back to 'waiting' + Paused msg, info toast 'Paused: 0 of 2', no error toast/red row; Upload resumes both.
S2: Pause while PDF 2 of 2 is in flight -> info toast 'Paused: 1 of 2'; Upload resumes the rest.
Run: python tests/ui_upload_pause212.py  (creates TEST_pause212_* books; prints ids for cleanup)"""
import asyncio, json, shutil, sys, time
sys.path.insert(0, '/app/backend/tests')
from playwright.async_api import async_playwright
from ui_master217_lib import open_as, ok, R, BASE, SS, mongo

FILES = {}
for tag, src in (('a', 'dup_a'), ('b', 'dup_b'), ('c', 'dup_a'), ('d', 'dup_b')):
    dst = f'/tmp/uibridge/TEST_pause212_{tag}.pdf'; shutil.copy(f'/tmp/uibridge/{src}.pdf', dst)
    open(dst, 'ab').write(f'\n%pause212{tag}{time.time()}\n'.encode()); FILES[tag] = dst
SLOW = set()


async def toasts(page):
    return await page.evaluate("() => [...document.querySelectorAll('[data-sonner-toast]')].map(t => (t.dataset.type||'') + ':' + t.textContent)")


async def wait_toast(page, needle, secs=40):
    t0 = time.time(); ts = []
    while time.time() - t0 < secs:
        ts = await toasts(page)
        if any(needle in t for t in ts): break
        await page.wait_for_timeout(300)
    return ts


async def rows(page):
    return await page.evaluate("() => [...document.querySelectorAll('[data-testid^=\"upload-batch-row-\"]')].map(li => [li.className, li.querySelector('small')?.textContent])")


async def scenario(page, posts, name, files, slow, expect_sent):
    SLOW.clear(); SLOW.update(slow); posts.clear()
    await page.goto(f'{BASE}/super-admin/exam/jee-main/jee-main:mocks'); await page.wait_for_selector('[data-testid="type-upload-pdf"]', timeout=30000)
    await page.click('[data-testid="type-upload-pdf"]'); await page.wait_for_selector('[data-testid="upload-dialog"]')
    await page.set_input_files('[data-testid="upload-main-input"]', files); await page.wait_for_selector('[data-testid="upload-batch-list"]', timeout=5000)
    await page.check('[data-testid="upload-rights"]'); await page.click('[data-testid="upload-send"]')
    await page.wait_for_selector('[data-testid="upload-pause"]', timeout=5000)
    # wait until the slow POST is in flight
    t0 = time.time()
    while time.time() - t0 < 20 and not any(p in slow for p in posts):
        await page.wait_for_timeout(100)
    await page.click('[data-testid="upload-pause"]')
    ts = await wait_toast(page, 'PDF')
    rs = await rows(page)
    print(name, 'toasts', ts, 'rows', rs, 'posts', posts)
    ok(f'{name}: info toast "Paused: {expect_sent} of 2 PDFs sent"', any(t.startswith('info:') and f'Paused: {expect_sent} of 2 PDFs sent' in t for t in ts), ts)
    ok(f'{name}: no error toast', not any(t.startswith('error:') for t in ts), ts)
    ok(f'{name}: no red/failed row', not any('is-failed' in c for c, _ in rs), rs)
    paused_row = rs[expect_sent] if len(rs) > expect_sent else ['', '']
    ok(f'{name}: paused row back to waiting with Paused msg', 'is-waiting' in paused_row[0] and (paused_row[1] or '').startswith('Paused. Press Upload to carry on'), paused_row)
    if expect_sent: ok(f'{name}: first row stays done', 'is-done' in rs[0][0], rs)
    bt = (await page.text_content('[data-testid="upload-send"]')).strip()
    ok(f'{name}: button "Upload {2 - expect_sent} PDF{"s" if 2 - expect_sent != 1 else ""}"', bt == f'Upload {2 - expect_sent} PDF{"s" if 2 - expect_sent != 1 else ""}', bt)
    ok(f'{name}: later PDF not posted after pause', len(posts) == expect_sent + 1, posts)
    await page.screenshot(path=f'{SS}/pause212-{name}.jpg', quality=40)
    # resume
    SLOW.clear(); posts.clear()
    await page.click('[data-testid="upload-send"]')
    t0 = time.time()
    while time.time() - t0 < 60 and await page.is_visible('[data-testid="upload-dialog"]'):
        await page.wait_for_timeout(300)
    closed = not await page.is_visible('[data-testid="upload-dialog"]')
    ts = await toasts(page)
    print(name, 'resume posts', posts, 'toasts', ts)
    ok(f'{name}: resume finishes all and closes dialog', closed, await rows(page) if not closed else '')
    ok(f'{name}: resume re-posts only the unsent PDFs', len(posts) == 2 - expect_sent, posts)
    ok(f'{name}: no error toast on resume', not any(t.startswith('error:') for t in ts), ts)


async def main():
    posts = []

    async def extra(route, req):
        if req.method == 'POST' and req.url.split('?')[0].endswith('/api/admin/books'):
            fn = json.loads(req.post_data or '{}').get('filename'); posts.append(fn)
            if fn in SLOW: await asyncio.sleep(3)
        return False
    async with async_playwright() as pw:
        br, page, bad, logs = await open_as(pw, 'owner', 1920, 1000, extra)
        try:
            await scenario(page, posts, 'S1', [FILES['a'], FILES['b']], {'TEST_pause212_a.pdf'}, 0)
            await scenario(page, posts, 'S2', [FILES['c'], FILES['d']], {'TEST_pause212_d.pdf'}, 1)
            await page.wait_for_timeout(3000)
            books = json.loads(mongo("JSON.stringify(db.tejas_books.find({'payload.filename':/^TEST_pause212_/},{_id:1,state:1,'payload.filename':1}).toArray())") or '[]')
            print('books', books)
            ok('server: 4 books, none left in uploading', len(books) == 4 and all(b['state'] != 'uploading' for b in books), books)
            ok('no page errors', not logs, logs[:3]); print('bad', bad[:8])
        finally:
            await br.close()
    print('TOTAL', len(R), 'PASS', sum(1 for _, x in R if x), 'FAIL', sum(1 for _, x in R if not x))

asyncio.run(main())
