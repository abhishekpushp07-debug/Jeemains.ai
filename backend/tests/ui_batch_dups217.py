"""TEST-ONLY (iteration 217): multi-PDF upload (batch, failure + resend unsent only), duplicate red alert same section vs other section,
Fix page alert, go Live with duplicates, publish progress doc removed. Bridge 8770 (master_bridge181). Run: python tests/ui_batch_dups217.py"""
import asyncio, json, shutil, sys, time
sys.path.insert(0, '/app/backend/tests')
from playwright.async_api import async_playwright
from ui_master217_lib import open_as, ok, R, BASE, SS, mongo

MOCKS, PYQ = 'jee-main:mocks', 'jee-main:pyq'
A, Bp = '/tmp/uibridge/TEST_dup_a.pdf', '/tmp/uibridge/TEST_dup_b_2023.pdf'
shutil.copy('/tmp/uibridge/dup_a.pdf', A); shutil.copy('/tmp/uibridge/dup_b.pdf', Bp)
C1, C2 = '/tmp/uibridge/TEST_pyq_2021.pdf', '/tmp/uibridge/TEST_pyq_x.pdf'
shutil.copy('/tmp/uibridge/dup_a.pdf', C1); shutil.copy('/tmp/uibridge/dup_b.pdf', C2)


def books(sec):
    return json.loads(mongo("JSON.stringify(db.tejas_books.find({'payload.section_id':'%s'},{state:1,'payload.filename':1,'payload.title':1,'payload.year':1}).toArray())" % sec) or '[]')


def mocks_of(bid):
    return json.loads(mongo("JSON.stringify(db.tejas_book_mocks.find({book_id:'%s'},{_id:1,label:1,status:1,'questions.id':1,'questions.number':1}).toArray())" % bid) or '[]')


async def settle(sec, n, secs=150):
    t0 = time.time()
    while time.time() - t0 < secs:
        b = books(sec)
        if len(b) >= n and all(x['state'] not in ('uploading', 'received', 'reading', 'matching') for x in b):
            return b
        await asyncio.sleep(3)
    return books(sec)


async def open_type(page, sec):
    await page.goto(f'{BASE}/super-admin/exam/jee-main/{sec}')
    await page.wait_for_selector('[data-testid="type-upload-pdf"]', timeout=30000)


async def run(pw):
    fail_once = {'n': 0, 'armed': True}
    posts = []

    async def extra(route, req):
        if req.method == 'POST' and req.url.split('?')[0].endswith('/api/admin/books'):
            posts.append(json.loads(req.post_data or '{}').get('filename'))
            if fail_once['armed'] and len(posts) == 2:
                fail_once['armed'] = False
                await route.fulfill(status=503, content_type='application/json', body=json.dumps({'detail': 'TEST forced failure'}))
                return True
        return False
    br, page, bad, logs = await open_as(pw, 'owner', 1920, 1000, extra)
    try:
        # ---- batch into Mock Tests (2 PDFs, second fails once) ----
        await open_type(page, MOCKS)
        await page.click('[data-testid="type-upload-pdf"]'); await page.wait_for_selector('[data-testid="upload-dialog"]')
        await page.set_input_files('[data-testid="upload-main-input"]', [A, Bp])
        await page.wait_for_selector('[data-testid="upload-batch-list"]', timeout=5000)
        ok('batch: 2 rows', await page.locator('[data-testid^="upload-batch-row-"]').count() == 2)
        ok('batch: key/solutions boxes hidden', not await page.is_visible('[data-testid="upload-key"]') and not await page.is_visible('[data-testid="upload-solutions"]'))
        ok('batch: title field hidden', not await page.is_visible('[data-testid="upload-title"]'))
        ok('batch: no year inputs in non-PYQ', await page.locator('[data-testid^="upload-batch-year-"]').count() == 0)
        bt = (await page.text_content('[data-testid="upload-send"]')).strip()
        ok('batch: button "Upload 2 PDFs"', bt == 'Upload 2 PDFs', bt)
        ok('batch: send disabled before rights', await page.is_disabled('[data-testid="upload-send"]'))
        await page.check('[data-testid="upload-rights"]')
        await page.screenshot(path=f'{SS}/batch-chosen.jpg', quality=40)
        await page.click('[data-testid="upload-send"]')
        t0 = time.time()
        while time.time() - t0 < 60:
            s1 = await page.text_content('[data-testid="upload-batch-status-1"]') if await page.is_visible('[data-testid="upload-batch-status-1"]') else ''
            if not await page.is_visible('[data-testid="upload-dialog"]') or ('fail' in (s1 or '').lower() or 'TEST' in (s1 or '')):
                break
            await page.wait_for_timeout(300)
        await page.wait_for_timeout(800)
        still = await page.is_visible('[data-testid="upload-dialog"]')
        ok('batch failure: dialog stays open', still)
        st0 = await page.text_content('[data-testid="upload-batch-status-0"]') if still else ''
        st1 = await page.text_content('[data-testid="upload-batch-status-1"]') if still else ''
        cls1 = await page.get_attribute('[data-testid="upload-batch-row-1"]', 'class') if still else ''
        print('row0', st0, '| row1', st1, cls1)
        ok('batch failure: row0 done, row1 failed', 'is-failed' in (cls1 or '') and 'Sent' in (st0 or ''), (st0, st1, cls1))
        toasts = await page.evaluate("() => [...document.querySelectorAll('[data-sonner-toast]')].map(t => (t.dataset.type||'') + ':' + t.textContent)")
        print('toasts', toasts)
        ok('batch failure: error toast "1 of 2 PDFs sent"', any('1 of 2 PDFs sent' in t for t in toasts), toasts)
        bt = (await page.text_content('[data-testid="upload-send"]')).strip() if still else ''
        ok('batch failure: button now "Upload 1 PDFs"', bt.startswith('Upload 1'), bt)
        await page.screenshot(path=f'{SS}/batch-failed.jpg', quality=40)
        n_posts = len(posts)
        if still:
            await page.click('[data-testid="upload-send"]')
            try: await page.wait_for_selector('[data-testid="upload-dialog"]', state='hidden', timeout=60000)
            except Exception: pass
        ok('batch resend: dialog closed', not await page.is_visible('[data-testid="upload-dialog"]'))
        print('POST filenames', posts)
        ok('batch resend: only unsent PDF re-posted', posts[n_posts:] == ['TEST_dup_b_2023.pdf'], posts)
        mb = await settle(MOCKS, 2)
        print('mock books', mb)
        ok('batch: 2 books in Mock Tests, each own book', len(mb) == 2 and {b['payload']['filename'] for b in mb} == {'TEST_dup_a.pdf', 'TEST_dup_b_2023.pdf'}, mb)
        ok('batch: titles from file names', {b['payload'].get('title') for b in mb} == {'TEST_dup_a', 'TEST_dup_b_2023'}, mb)
        # ---- duplicates on Master list ----
        await open_type(page, MOCKS); await page.wait_for_timeout(1500)
        info = {}
        for b in mb:
            for m in mocks_of(b['_id']):
                info[m['_id']] = (b['_id'], m)
        print('mocks', {k: (v[1]['label'], v[1].get('status'), len(v[1]['questions'])) for k, v in info.items()})
        for mid, (bid, m) in info.items():
            sel = f'[data-testid="mock-duplicates-{mid}"]'
            vis = await page.is_visible(sel)
            txt = (await page.text_content(sel)) if vis else ''
            ok(f'dups: mock {mid[:8]} shows red note', vis and txt.startswith('2 sawaal is section mein pehle se hain'), txt)
            if vis:
                await page.click(sel + ' summary')
                items = await page.locator(f'[data-testid^="mock-duplicate-{mid}-"]').all_text_contents()
                print('  items', items)
                q3 = [q['id'] for q in m['questions'] if q.get('number') == 3]
                ok(f'dups: mock {mid[:8]} 2 items, Q3 not flagged', len(items) == 2 and all('Q3' not in t.split('=')[0] for t in items)
                   and not any(await page.is_visible(f'[data-testid="mock-duplicate-{mid}-{q}"]') for q in q3), items)
                color = await page.evaluate(f"() => getComputedStyle(document.querySelector('{sel} summary')).color")
                print('  summary color', color)
        await page.screenshot(path=f'{SS}/dups-list.jpg', quality=40)
        # ---- Fix page alert ----
        if info:
            mid, (bid, m) = next(iter(info.items()))
            await page.goto(f'{BASE}/super-admin/fix/{bid}/{mid}')
            try:
                await page.wait_for_selector('[data-testid="fix-duplicate-alert"]', timeout=20000)
                n = await page.locator('[data-testid^="fix-duplicate-"]:not([data-testid="fix-duplicate-alert"])').count()
                ok('fix page: red alert with 2 rows', n == 2, n)
            except Exception as e:
                ok('fix page: red alert shown', False, e)
            await page.screenshot(path=f'{SS}/dups-fix.jpg', quality=40)
        # ---- different section: PYQ (batch with year prefill), no cross-section alert ----
        await open_type(page, PYQ)
        await page.click('[data-testid="type-upload-pdf"]'); await page.wait_for_selector('[data-testid="upload-dialog"]')
        await page.set_input_files('[data-testid="upload-main-input"]', [C1, C2])
        y0 = await page.input_value('[data-testid="upload-batch-year-0"]'); y1 = await page.input_value('[data-testid="upload-batch-year-1"]')
        ok('pyq batch: year prefilled from file name / empty otherwise', y0 == '2021' and y1 == '', (y0, y1))
        await page.check('[data-testid="upload-rights"]')
        ok('pyq batch: send disabled while a year is missing', await page.is_disabled('[data-testid="upload-send"]'))
        await page.fill('[data-testid="upload-batch-year-1"]', '2022')
        ok('pyq batch: send enabled after year', await page.is_enabled('[data-testid="upload-send"]'))
        # back to one file -> single flow (title + year visible)
        await page.set_input_files('[data-testid="upload-main-input"]', [C1])
        ok('pyq single: batch list gone, title + year + key box back', not await page.is_visible('[data-testid="upload-batch-list"]') and await page.is_visible('[data-testid="upload-title"]')
           and await page.is_visible('[data-testid="upload-year"]') and await page.is_visible('[data-testid="upload-key"]'))
        tv = await page.input_value('[data-testid="upload-title"]')
        ok('pyq single: title from file name', tv == 'TEST_pyq_2021', tv)
        await page.fill('[data-testid="upload-year"]', '2021')
        await page.click('[data-testid="upload-send"]')
        msgs = []; t0 = time.time()
        while time.time() - t0 < 60 and await page.is_visible('[data-testid="upload-dialog"]'):
            if await page.is_visible('[data-testid="upload-progress"]'):
                try: m_ = (await page.text_content('[data-testid="upload-progress"]', timeout=300) or '').strip()
                except Exception: m_ = ''
                if m_ and (not msgs or msgs[-1] != m_): msgs.append(m_)
            await page.wait_for_timeout(100)
        print('single progress', msgs)
        ok('pyq single: dialog closed after upload', not await page.is_visible('[data-testid="upload-dialog"]'))
        pb = await settle(PYQ, 1)
        print('pyq books', pb)
        ok('pyq single: year saved', pb and pb[0]['payload'].get('year') in (2021, '2021'), pb)
        await open_type(page, PYQ); await page.wait_for_timeout(1500)
        nd = await page.locator('[data-testid^="mock-duplicates-"]').count()
        ok('cross-section: no duplicate alert in PYQ', nd == 0, nd)
        # mock list must still show the 2 alerts in Mock Tests (other section unaffected)
        # ---- Go Live a duplicate mock (warning only) + publish progress ----
        await open_type(page, MOCKS); await page.wait_for_timeout(1000)
        if info:
            mid = next(iter(info))
            sw = f'[data-testid="mock-live-switch-{mid}"]'
            dis = await page.is_disabled(sw)
            print('live switch disabled?', dis, await page.text_content(f'[data-testid="mock-row-{mid}"]'))
            if not dis:
                await page.click(sw)
                seen = []; t0 = time.time()
                while time.time() - t0 < 90:
                    w = (await page.text_content(f'[data-testid="mock-live-word-{mid}"]')) if await page.is_visible(f'[data-testid="mock-live-word-{mid}"]') else '?'
                    pp = mongo("JSON.stringify(db.tejas_publish_progress.find().toArray())")
                    seen.append((w, pp[:120]))
                    if w == 'Live': break
                    await page.wait_for_timeout(1000)
                    if len(seen) % 5 == 0: await page.reload(); await page.wait_for_selector('[data-testid="mock-list"]', timeout=20000)
                print('publish seen', seen[:12])
                rows = await page.locator('[data-testid="mock-list"] small').all_text_contents()
                live_sets = mongo("db.tejas_sets.countDocuments({status:'live'})")
                print('live sets', live_sets)
                ok('go live with duplicates: becomes Live', any(w == 'Live' for w, _ in seen) or live_sets not in ('0', ''), seen[-3:])
                await asyncio.sleep(3)
                left = mongo("db.tejas_publish_progress.countDocuments()")
                ok('publish progress doc removed after publish', left == '0', left)
                await page.reload(); await page.wait_for_timeout(2500)
                nd = await page.locator('[data-testid^="mock-duplicates-"]').count()
                print('dup notes after live', nd)
                ok('after Live: duplicates still flagged on both items (set + waiting mock)', nd == 2, nd)
                await page.screenshot(path=f'{SS}/dups-after-live.jpg', quality=40)
            else:
                ok('go live switch enabled for duplicate mock', False, 'disabled')
        ok('no page errors', not logs, logs[:3])
        print('bad responses', bad[:10])
    finally:
        await br.close()


async def main():
    async with async_playwright() as pw:
        await run(pw)
    print('TOTAL', len(R), 'PASS', sum(1 for _, x in R if x), 'FAIL', sum(1 for _, x in R if not x))

asyncio.run(main())
