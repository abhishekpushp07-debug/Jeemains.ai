"""TEST-ONLY iteration 217 QA (testing agent): FIX 1 badge staleness + FIX 4 waiting message, on the isolated bridge 127.0.0.1:8774.
(a) Supabase up, badge 'Storage: Supabase' -> flag on -> new upload waits -> badge turns 'Supabase ka intezaar' within seconds (no 60 s lag).
(b) flag off -> row 'Abhi phir try karo' -> badge 'Storage: Supabase' within ~5 s, machine panel no longer lists the book. No page reload.
Run: cd /app/backend && BRIDGE_OUT=/tmp/uibridge224 BRIDGE_PORT=8774 python tests/ui_storage_badge_event224.py [qa_variant3.pdf]
"""
import asyncio, json, os, sys, time
from pathlib import Path
os.environ.setdefault('BRIDGE_OUT', '/tmp/uibridge224'); os.environ.setdefault('BRIDGE_PORT', '8774')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.async_api import async_playwright  # noqa: E402
from ui_cut210 import open_as, BASE, say, RESULT  # noqa: E402

D = '/tmp/uibridge224/'; FLAG = D + 'supabase_down'
INFO = json.load(open(D + 'bridge.json'))
PDF = D + (sys.argv[1] if len(sys.argv) > 1 else 'qa_variant3.pdf')
SS = '/app/.screenshots/ui217qa'; os.makedirs(SS, exist_ok=True)
WAITS = "es=>es.map(e=>e.dataset.testid).filter(t=>!t.includes('retry'))"


async def label(page):
    return (await page.locator('[data-testid=storage-badge-label]').inner_text()).strip()


async def until(page, fn, secs, step=250):
    t0 = time.time()
    while time.time() - t0 < secs:
        if await fn(): return round(time.time() - t0, 2)
        await page.wait_for_timeout(step)
    return None


async def main():
    async with async_playwright() as pw:
        br, page, bad, logs = await open_as(pw, 'owner', 'desk')
        fresh = []
        page.on('request', lambda r: fresh.append(time.time()) if '/admin/storage/health?fresh=true' in r.url else None)
        try:
            if os.path.exists(FLAG): os.remove(FLAG)
            await page.goto(BASE + INFO['type']); await page.wait_for_selector('[data-testid=storage-badge-label]', timeout=25000)
            nav0 = await page.evaluate('performance.getEntriesByType("navigation").length + ":" + performance.timeOrigin')
            ok = await until(page, lambda: _eq(page, 'Storage: Supabase'), 75, 1000)
            say('setup: Supabase up -> badge Storage: Supabase', ok is not None, await label(page))
            before = set(await page.locator('[data-testid^=type-upload-wait-]').evaluate_all(WAITS))
            # (a) Supabase goes down; a new upload has to wait
            Path(FLAG).touch()
            await page.click('[data-testid=type-upload-pdf]'); await page.wait_for_selector('[data-testid=upload-dialog]')
            async with page.expect_file_chooser(timeout=5000) as fc:
                await page.click('[data-testid=upload-main-pick]')
            await (await fc.value).set_files(PDF); await page.check('[data-testid=upload-rights]')
            await page.click('[data-testid=upload-send]')
            await page.wait_for_selector('[data-testid=upload-dialog]', state='detached', timeout=60000)
            print('   badge right after upload:', await label(page))
            new = []
            async def row():
                now = set(await page.locator('[data-testid^=type-upload-wait-]').evaluate_all(WAITS)); new[:] = list(now - before); return bool(new)
            t_row = await until(page, row, 120, 300)
            t_row_abs = time.time()
            say('(a) new upload row shows type-upload-wait-<id>', t_row is not None, (before,))
            if not new: raise RuntimeError('no waiting row')
            nid = new[0].replace('type-upload-wait-', ''); print('   waiting book', nid, 'after', t_row, 's')
            lab = await label(page); print('   badge when row appeared:', lab)
            dt = await until(page, lambda: _eq(page, 'Storage: Supabase ka intezaar'), 20)
            say('(a) badge turns "Storage: Supabase ka intezaar" within 8 s of the waiting row', dt is not None and dt <= 8, (dt, await label(page)))
            print(f'   badge lag after row: {dt}s; fresh health requests after row: {len([t for t in fresh if t >= t_row_abs - 1])}')
            await page.screenshot(path=f'{SS}/a_waiting.jpg', quality=40, type='jpeg')
            st = await page.evaluate("()=>fetch('/api/admin/machine/status',{credentials:'include'}).then(r=>r.json()).then(j=>j.data||j)")
            w = [b for b in st.get('storage_waiting', []) if b.get('id') == nid]
            say('(a) machine status lists the new book as waiting', bool(w), st.get('storage_waiting'))
            msg = (w[0].get('message') if w else '') or ''
            allb = [b for k in ('books', 'stuck', 'recent') for b in (st.get(k) or []) if isinstance(b, dict) and b.get('id') == nid]
            msgs = [msg] + [b.get('message', '') for b in allb]
            print('   machine messages for book:', msgs)
            say('FIX4: no "Transfer complete. Validating" for the waiting book', not any('Transfer complete' in m for m in msgs), msgs)
            rowtxt = await page.locator(f'[data-testid=type-upload-{nid}]').inner_text()
            say('FIX4: row has no "Transfer complete. Validating"', 'Transfer complete' not in rowtxt, rowtxt[:300])
            # (b) Supabase comes back; the row retry fixes the badge and machine panel without a reload
            os.remove(FLAG); t0 = time.time()
            await page.click(f'[data-testid=type-upload-wait-retry-{nid}]')
            dt = await until(page, lambda: _eq(page, 'Storage: Supabase'), 15)
            say('(b) badge back to "Storage: Supabase" within 5 s of retry click', dt is not None and time.time() - t0 <= 15 and dt <= 5, (dt, await label(page)))
            await page.click('[data-testid=storage-badge]'); await page.wait_for_selector('[data-testid=storage-details]')
            gone = await until(page, lambda: _none(page, f'[data-testid=machine-waiting-{nid}]'), 10)
            say('(b) machine panel no longer lists the book (within 10 s of opening popover)', gone is not None, gone)
            if gone is None:
                late = await until(page, lambda: _none(page, f'[data-testid=machine-waiting-{nid}]'), 70, 1000)
                print(f'   machine panel cleared only after a further {late}s (60 s poll)')
                rowgone = await page.locator(f'[data-testid=type-upload-wait-{nid}]').count() == 0
                print('   row wait note gone meanwhile:', rowgone)
            ml = await page.locator('[data-testid=machine-storage-waiting]').inner_text() if await page.locator('[data-testid=machine-storage-waiting]').count() else ''
            print('   machine waiting line now:', ml)
            await page.screenshot(path=f'{SS}/b_recovered.jpg', quality=40, type='jpeg')
            nav1 = await page.evaluate('performance.getEntriesByType("navigation").length + ":" + performance.timeOrigin')
            say('(b) no page reload happened', nav0 == nav1, (nav0, nav1))
            say('no 5xx', not [b for b in bad if b[0] >= 500], bad[:6]); print('   4xx/console', bad[:6], logs[:4])
        except Exception as e:
            say('badge event walk', False, repr(e)[:300]); await page.screenshot(path=f'{SS}/err.jpg', quality=40, type='jpeg')
        finally:
            Path(FLAG).touch(); print('   flag re-created')
            await br.close()
    f = [n for n, ok in RESULT if not ok]
    print(f'TOTAL {len(RESULT)} PASS {len(RESULT) - len(f)} FAIL {len(f)}'); [print('  FAILED', n) for n in f]


async def _eq(page, text):
    return await label(page) == text


async def _none(page, sel):
    return await page.locator(sel).count() == 0

if __name__ == '__main__':
    asyncio.run(main())
