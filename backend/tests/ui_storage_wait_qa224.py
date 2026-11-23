"""TEST-ONLY iteration 224 QA (testing agent): full Supabase-wait UI flow on the isolated bridge 127.0.0.1:8774.
Phase A (Supabase down): wait note, % bar, badge, popover, machine panel, Upload dialog notice/picker/percent, mobile overflow.
Phase B (recovery): delete flag -> 'Abhi phir try karo' -> wait note goes, PDF proceeds, mock appears, badge back. Re-creates flag after.
Run: cd /app/backend && BRIDGE_OUT=/tmp/uibridge224 BRIDGE_PORT=8774 python tests/ui_storage_wait_qa224.py
"""
import asyncio, json, os, re, sys, time
from pathlib import Path
os.environ.setdefault('BRIDGE_OUT', '/tmp/uibridge224'); os.environ.setdefault('BRIDGE_PORT', '8774')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.async_api import async_playwright  # noqa: E402
from ui_cut210 import open_as, BASE, say, RESULT  # noqa: E402

D = '/tmp/uibridge224/'; FLAG = D + 'supabase_down'
INFO = json.load(open(D + 'bridge.json')); BID = INFO['book']
SS = '/app/.screenshots/ui224qa'; os.makedirs(SS, exist_ok=True)
OVER = """() => { const vw = document.documentElement.clientWidth; const out = [];
  for (const sel of ['[data-testid^=type-upload-]', '[data-testid=storage-details]', '[data-testid=storage-badge]', '[data-testid^=machine-]', '[data-testid=upload-dialog]']) {
    for (const e of document.querySelectorAll(sel)) { if (!e.offsetParent) continue; const r = e.getBoundingClientRect();
      if (r.right > vw + 1 || r.left < -1 || e.scrollWidth > e.clientWidth + 2 && getComputedStyle(e).overflowX === 'visible') out.push([e.dataset.testid, Math.round(r.left), Math.round(r.right), e.scrollWidth, e.clientWidth]); } }
  return {vw, sw: document.documentElement.scrollWidth, out: out.slice(0, 8)}; }"""


async def toasts(page):
    await page.wait_for_timeout(1200); return ' | '.join(await page.locator('[data-sonner-toast]').all_inner_texts())


async def no_overflow(page, tag):
    o = await page.evaluate(OVER); say(f'{tag}: no horizontal overflow', o['sw'] <= o['vw'] + 1 and not o['out'], o)


async def down_walk(pw, size):
    br, page, bad, logs = await open_as(pw, 'owner', size); touch = size == 'mob'
    try:
        await page.goto(BASE + INFO['type']); await page.wait_for_selector(f'[data-testid=type-upload-{BID}]', timeout=25000)
        await page.locator(f'[data-testid=type-upload-{BID}]').scroll_into_view_if_needed()
        tx = await page.locator(f'[data-testid=type-upload-transfer-{BID}]').inner_text()
        say(f'{size}: % bar text format', re.search(r'Original Supabase mein: \d+% · [\d.]+ (KB|MB) / [\d.]+ (KB|MB)', tx), tx)
        wt = await page.locator(f'[data-testid=type-upload-wait-{BID}]').inner_text()
        say(f'{size}: wait note text', 'Supabase ka intezaar' in wt and 'Emergent mein kuch nahi gaya' in wt, wt)
        say(f'{size}: row retry button visible', await page.is_visible(f'[data-testid=type-upload-wait-retry-{BID}]'))
        say(f'{size}: no failed retry button on waiting row', not await page.locator(f'[data-testid=type-upload-retry-{BID}]').count())
        await no_overflow(page, size + ' type page')
        await page.screenshot(path=f'{SS}/{size}_down_type.jpg', quality=40, type='jpeg')
        # retry while still down -> error toast
        await page.click(f'[data-testid=type-upload-wait-retry-{BID}]'); t = await toasts(page)
        say(f'{size}: retry while down -> still-down toast', 'abhi bhi jawab nahi' in t, t)
        say(f'{size}: wait note still there after retry', await page.is_visible(f'[data-testid=type-upload-wait-{BID}]'))
        # badge + popover
        label = await page.locator('[data-testid=storage-badge-label]').inner_text()
        say(f'{size}: badge label waiting', label.strip() == 'Storage: Supabase ka intezaar', label)
        await page.click('[data-testid=storage-badge]'); await page.wait_for_selector('[data-testid=storage-details]'); await page.wait_for_timeout(1200)
        say(f'{size}: popover retry-now button', await page.is_visible('[data-testid=storage-retry-now]'))
        ml = await page.locator('[data-testid=machine-storage-waiting]').inner_text() if await page.locator('[data-testid=machine-storage-waiting]').count() else ''
        say(f'{size}: machine storage-waiting line', 'Supabase ka intezaar' in ml and 'PDF' in ml, ml)
        say(f'{size}: machine waiting item', await page.locator(f'[data-testid=machine-waiting-{BID}]').count() == 1)
        say(f'{size}: machine retry button', await page.locator('[data-testid=machine-storage-retry]').count() == 1)
        det = await page.inner_text('[data-testid=storage-details]')
        say(f'{size}: popover has no Emergent-backup wording', 'backup' not in det.lower(), det[:400])
        await no_overflow(page, size + ' popover')
        await page.screenshot(path=f'{SS}/{size}_down_popover.jpg', quality=40, type='jpeg')
        await page.click('[data-testid=storage-retry-now]'); t = await toasts(page)
        say(f'{size}: popover retry while down toast', 'abhi bhi jawab nahi' in t, t)
        await page.keyboard.press('Escape'); await page.wait_for_timeout(400)
        # Upload dialog
        await page.click('[data-testid=type-upload-pdf]'); await page.wait_for_selector('[data-testid=upload-dialog]'); await page.wait_for_timeout(1500)
        n = await page.locator('[data-testid=upload-storage-notice]').inner_text() if await page.locator('[data-testid=upload-storage-notice]').count() else ''
        say(f'{size}: dialog Supabase notice', 'Supabase abhi ruka' in n and 'upload kar sakte' in n.lower(), n)
        try:
            async with page.expect_file_chooser(timeout=3000) as fc:
                if touch: await page.locator('[data-testid=upload-main-pick]').tap()
                else: await page.click('[data-testid=upload-main-pick]')
            f = await fc.value; say(f'{size}: Select PDF opens chooser', True)
        except Exception as e:
            f = None; say(f'{size}: Select PDF opens chooser', False, repr(e)[:200])
        await no_overflow(page, size + ' dialog')
        await page.screenshot(path=f'{SS}/{size}_dialog.jpg', quality=40, type='jpeg')
        if size == 'desk' and f:
            before = set(await page.locator('[data-testid^=type-upload-wait-]:not([data-testid*=retry])').evaluate_all('es=>es.map(e=>e.dataset.testid)'))
            await f.set_files(D + 'qa_variant.pdf'); await page.check('[data-testid=upload-rights]')
            seen = []
            async def watch():
                for _ in range(80):
                    if await page.locator('[data-testid=upload-progress]').count():
                        try: seen.append(await page.locator('[data-testid=upload-progress]').inner_text(timeout=200))
                        except Exception: pass
                    await asyncio.sleep(0.05)
            w = asyncio.create_task(watch()); await page.click('[data-testid=upload-send]')
            try:
                await page.wait_for_selector('[data-testid=upload-dialog]', state='detached', timeout=60000); closed = True
            except Exception: closed = False
            await w; print('   progress seen:', seen[:6])
            say('desk: upload-progress shows N% ·', any(re.search(r'\d+% ·', s) for s in seen), seen[:5])
            t = await toasts(page); print('   toasts:', t)
            say('desk: upload while down accepted (dialog closed)', closed, t)
            await page.wait_for_timeout(8000)
            after = set(await page.locator('[data-testid^=type-upload-wait-]:not([data-testid*=retry])').evaluate_all('es=>es.map(e=>e.dataset.testid)'))
            print('   wait notes before/after', before, after)
            say('desk: new upload also waits for Supabase (new wait note)', len(after - before) >= 1, (before, after))
            await page.screenshot(path=f'{SS}/desk_after_upload.jpg', quality=40, type='jpeg')
        else:
            await page.keyboard.press('Escape')
        say(f'{size}: no 5xx', not [b for b in bad if b[0] >= 500], bad[:6]); print('   4xx/console', bad[:6], logs[:4])
    except Exception as e:
        say(f'{size}: down walk', False, repr(e)[:300]); await page.screenshot(path=f'{SS}/{size}_err.jpg', quality=40, type='jpeg')
    finally:
        await br.close()


async def recovery(pw):
    br, page, bad, logs = await open_as(pw, 'owner', 'desk')
    try:
        await page.goto(BASE + INFO['type']); await page.wait_for_selector(f'[data-testid=type-upload-{BID}]', timeout=25000)
        mocks0 = await page.locator('[data-testid^=mock-row-]').count()
        os.remove(FLAG); print('   flag removed')
        await page.click(f'[data-testid=type-upload-wait-retry-{BID}]'); t = await toasts(page)
        say('recovery: toast Supabase wapas aa gaya', 'Supabase wapas aa gaya' in t or 'Supabase theek hai' in t, t)
        say('recovery: toast mentions woke jobs', 'Supabase wapas aa gaya' in t, t)
        t0 = time.time(); gone = prog = False; mocks = mocks0; states = []
        while time.time() - t0 < 45:
            gone = not await page.locator('[data-testid^=type-upload-wait-]').count()
            prog = prog or await page.locator(f'[data-testid=type-upload-progress-{BID}]').count() > 0
            mocks = await page.locator('[data-testid^=mock-row-]').count()
            row = await page.locator(f'[data-testid=type-upload-{BID}]').inner_text() if await page.locator(f'[data-testid=type-upload-{BID}]').count() else '(row gone)'
            states.append((round(time.time() - t0), gone, prog, mocks, row[:90].replace('\n', ' | ')))
            if gone and mocks > mocks0: break
            await page.wait_for_timeout(1500)
        for s in states[::3]: print('   ', s)
        say('recovery: all wait notes gone', gone, states[-1])
        say('recovery: page progress seen or mock appeared', prog or mocks > mocks0, states[-1])
        say('recovery: mock appeared', mocks > mocks0, (mocks0, mocks))
        print(f'   recovery took ~{states[-1][0]}s')
        label = await page.locator('[data-testid=storage-badge-label]').inner_text()
        say('recovery: badge back to Storage: Supabase', label.strip() == 'Storage: Supabase', label)
        await page.screenshot(path=f'{SS}/desk_recovered.jpg', quality=40, type='jpeg')
        say('recovery: no 5xx', not [b for b in bad if b[0] >= 500], bad[:6])
    except Exception as e:
        say('recovery walk', False, repr(e)[:300]); await page.screenshot(path=f'{SS}/recovery_err.jpg', quality=40, type='jpeg')
    finally:
        Path(FLAG).touch(); print('   flag re-created')
        await br.close()


async def main():
    async with async_playwright() as pw:
        if 'recover' not in sys.argv:
            for size in ('desk', 'mob'):
                await down_walk(pw, size)
        if 'down' not in sys.argv:
            await recovery(pw)
    f = [n for n, ok in RESULT if not ok]
    print(f'TOTAL {len(RESULT)} PASS {len(RESULT) - len(f)} FAIL {len(f)}'); [print('  FAILED', n) for n in f]

if __name__ == '__main__':
    asyncio.run(main())
