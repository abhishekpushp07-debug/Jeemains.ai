"""TEST-ONLY (iteration 215, T1): Upload PDF resilience via the bridge (:8772). Upload physics.pdf to the chapter-wise type, same PDF again,
failed -> 'Dobara chalao', failed -> same PDF again carries on, book page polling. Run: python tests/ui_upload215.py [desk|mob]"""
import asyncio, json, subprocess, sys, time
from playwright.async_api import async_playwright
sys.path.insert(0, '/app/backend/tests')
from ui_verify211_lib import open_as, ok, R, BASE, F, SS, no_overflow

DBN = [l for l in open('/tmp/bridge210.log') if l.startswith('READY')][-1].split()[1]
PDF = '/app/data/chapter50/physics.pdf'


def mongo(js):
    return subprocess.run(['mongosh', '--quiet', DBN, '--eval', js], capture_output=True, text=True).stdout.strip()


def books():
    out = mongo("JSON.stringify(db.tejas_books.find({'payload.section_id':'%s','payload.filename':'physics.pdf'},{state:1,'payload.message':1}).toArray())" % F['chapters'])
    return json.loads(out or '[]')


async def upload(page, tag):
    await page.click('[data-testid="type-upload-pdf"]')
    await page.wait_for_selector('[data-testid="upload-dialog"]')
    await page.set_input_files('[data-testid="upload-main-input"]', PDF)
    await page.click('[data-testid="upload-subject"]'); await page.wait_for_timeout(300)
    await page.click('[data-testid="upload-subject-physics"]', force=True); await page.wait_for_timeout(200)
    await page.check('[data-testid="upload-rights"]')
    await page.click('[data-testid="upload-send"]')
    msgs = []; t0 = time.time()
    while time.time() - t0 < 60:
        if not await page.is_visible('[data-testid="upload-dialog"]'):
            break
        if await page.is_visible('[data-testid="upload-progress"]'):
            try: m = (await page.text_content('[data-testid="upload-progress"]', timeout=500) or '').strip()
            except Exception: m = ''
            if m and (not msgs or msgs[-1] != m): msgs.append(m)
        await page.wait_for_timeout(100)
    closed = not await page.is_visible('[data-testid="upload-dialog"]')
    toasts = await page.evaluate("() => [...document.querySelectorAll('[data-sonner-toast]')].map(t => (t.dataset.type||'') + ':' + t.textContent)")
    print(tag, 'progress', msgs, 'toasts', toasts, 'secs', round(time.time() - t0, 1))
    return closed, msgs, toasts


async def run(pw, size):
    tag = 'upload-' + size
    br, page, bad, logs = await open_as(pw, 'owner', size)
    puts = []; posts = []
    async def onresp(r):
        if r.request.method == 'POST' and r.url.split('?')[0].endswith('/api/admin/books'):
            try: posts.append(await r.json())
            except Exception: pass
    page.on('response', onresp)
    page.on('response', lambda r: puts.append((r.request.method, r.status, r.url.split('/api')[-1])) if '/parts/' in r.url else None)
    try:
        # clean any earlier run of this script (only our physics.pdf books in the disposable bridge DB)
        type_url = f"{BASE}/super-admin/exam/{F['slug']}/{F['chapters']}"
        await page.goto(type_url); await page.wait_for_selector('[data-testid="type-upload-pdf"]', timeout=30000)
        before = books()
        closed, msgs, toasts = await upload(page, tag + ' #1')
        after = books()
        ok(f'{tag}: dialog closed after first upload', closed, msgs)
        ok(f'{tag}: no error toast', not any(t.startswith('error') for t in toasts), toasts)
        new = [b for b in after if b['_id'] not in {x['_id'] for x in before}]
        if before:
            print('NOTE physics.pdf already in this type before this run:', before)
        bid = (new or after)[0]['_id']
        if not before:
            ok(f'{tag}: progress showed "Sending… N of 3 parts"', any('of 3 parts' in m for m in msgs), msgs)
            p = [x for x in puts if x[0] == 'PUT']
            ok(f'{tag}: 3 part PUTs all 200', len(p) == 3 and all(s == 200 for _, s, _ in p), p)
        await page.wait_for_selector(f'[data-testid="type-upload-{bid}"]', timeout=15000)
        st = await page.text_content(f'[data-testid="type-upload-state-{bid}"]')
        ok(f'{tag}: upload row present in Uploads panel', await page.is_visible(f'[data-testid="type-uploads"] [data-testid="type-upload-{bid}"]'), st)
        print(tag, 'row state', st, 'db', books())
        await page.screenshot(path=f'{SS}/{tag}-1.jpg', quality=40)
        # (2) same PDF again
        n0 = len(books()); puts.clear()
        closed, msgs, toasts = await upload(page, tag + ' #2')
        ok(f'{tag}: same PDF again -> no new book', len(books()) == n0, books())
        ok(f'{tag}: same PDF again -> dialog closed, no error', closed and not any(t.startswith('error') for t in toasts), (msgs, toasts))
        ok(f'{tag}: same PDF again -> no part PUTs', not [x for x in puts if x[0] == 'PUT'], puts)
        # wait until the reading settles so the retry has something to resume
        for _ in range(60):
            s = [b for b in books() if b['_id'] == bid][0]['state']
            if s not in ('uploading', 'received', 'reading', 'matching'): break
            await asyncio.sleep(2)
        print(tag, 'settled state', s)
        # (3) failed -> Dobara chalao
        mongo("db.tejas_books.updateOne({_id:'%s'},{$set:{state:'failed','payload.message':'Processing interrupted.'}})" % bid)
        await page.reload(); await page.wait_for_selector(f'[data-testid="type-upload-{bid}"]', timeout=20000)
        rb = f'[data-testid="type-upload-retry-{bid}"]'
        ok(f'{tag}: failed row shows Dobara chalao', await page.is_visible(rb) and 'Dobara chalao' in (await page.text_content(rb)), await page.text_content(f'[data-testid="type-upload-{bid}"]'))
        await page.screenshot(path=f'{SS}/{tag}-failed.jpg', quality=40)
        if await page.is_visible(rb):
            await page.click(rb); seen = []
            try: await page.wait_for_selector('[data-sonner-toast][data-type="success"]:has-text("Phir se")', timeout=4000); rt = True
            except Exception: rt = False
            for _ in range(30):
                st_ = [b for b in books() if b['_id'] == bid][0]['state']
                if not seen or seen[-1] != st_: seen.append(st_)
                await asyncio.sleep(0.1)
            print(tag, 'states after retry click', seen)
            ok(f'{tag}: retry success toast', rt)
            ok(f'{tag}: retry -> book back to reading/matching', any(x in ('reading', 'matching', 'received') for x in seen), seen)
            await page.wait_for_timeout(1500)
            ok(f'{tag}: retry button gone after retry', not await page.is_visible(rb), await page.text_content(f'[data-testid="type-upload-{bid}"]'))
        for _ in range(60):
            s = [b for b in books() if b['_id'] == bid][0]['state']
            if s not in ('uploading', 'received', 'reading', 'matching'): break
            await asyncio.sleep(2)
        # failed -> same PDF again carries on
        mongo("db.tejas_books.updateOne({_id:'%s'},{$set:{state:'failed','payload.message':'Processing interrupted.'}})" % bid)
        await page.reload(); await page.wait_for_selector('[data-testid="type-upload-pdf"]', timeout=20000)
        n0 = len(books()); posts.clear()
        closed, msgs, toasts = await upload(page, tag + ' #3')
        b = [x for x in books() if x['_id'] == bid][0]
        ok(f'{tag}: failed + same PDF -> carries on (same book, not failed)', len(books()) == n0 and b['state'] != 'failed', b)
        pm = json.dumps(posts[-1]) if posts else ''
        print(tag, 'POST /admin/books reply', pm[:400])
        ok(f'{tag}: failed + same PDF -> message', 'Same PDF chosen again' in pm or 'Same PDF chosen again' in (b.get('payload') or {}).get('message', ''), pm[:300])
        ok(f'{tag}: failed + same PDF -> dialog closed, no error', closed and not any(t.startswith('error') for t in toasts), (msgs, toasts))
        for _ in range(60):
            s = [x for x in books() if x['_id'] == bid][0]['state']
            if s not in ('uploading', 'received', 'reading', 'matching'): break
            await asyncio.sleep(2)
        print(tag, 'final state', s)
        # (4) book page: opens fast, mock counts, polling only while working
        hits = []
        page.on('request', lambda r: hits.append(time.time()) if r.url.split('?')[0].endswith(f'/admin/books/{bid}') and r.method == 'GET' else None)
        t0 = time.time(); await page.goto(f'{BASE}/super-admin/upload?book={bid}')
        await page.wait_for_selector('[data-testid="book-map"]', timeout=20000); dt = time.time() - t0
        ok(f'{tag}: book page opens fast ({dt:.1f}s)', dt < 6, dt)
        rows = await page.locator('[data-testid^="book-mock-"] .book-section-heading small').all_text_contents()
        print(tag, 'mock rows', len(rows), rows[:3])
        ok(f'{tag}: mock counts shown (questions/explanations/key-only)', rows and all('questions' in r and 'original explanations' in r and 'key-only' in r for r in rows), rows[:3])
        state = await page.text_content('[data-testid="book-detail-state"]')
        n1 = len(hits); await page.wait_for_timeout(20000); n2 = len(hits)
        print(tag, 'book state', state, 'GETs during 20s idle', n2 - n1)
        if s in ('ready', 'attention_needed', 'chapters_needed'):
            ok(f'{tag}: no polling once {s}', n2 - n1 == 0, n2 - n1)
        await no_overflow(page, tag + ' book page')
        await page.screenshot(path=f'{SS}/{tag}-book.jpg', quality=40)
        ok(f'{tag}: no 4xx/5xx', not bad, bad[:5]); ok(f'{tag}: no page errors', not logs, logs[:3])
    finally:
        await br.close()


async def main():
    async with async_playwright() as pw:
        for s in sys.argv[1:] or ['desk']:
            await run(pw, s)
    print('TOTAL', len(R), 'PASS', sum(1 for _, x in R if x), 'FAIL', sum(1 for _, x in R if not x))

asyncio.run(main())
