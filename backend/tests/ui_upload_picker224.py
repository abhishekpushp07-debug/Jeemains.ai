"""TEST-ONLY iteration 224/215: Upload PDF dialog file picker fix ('PDF chuniye' button) via local Playwright against the preview
frontend with /api routed to the isolated bridge tests/master_bridge181.py (127.0.0.1:8770, cookies in /tmp/uibridge/bridge.json).
Run: cd /app/backend && BRIDGE_OUT=/tmp/uibridge BRIDGE_PORT=8770 python tests/ui_upload_picker224.py
"""
import asyncio, os, sys, time
from pathlib import Path
os.environ.setdefault('BRIDGE_OUT', '/tmp/uibridge'); os.environ.setdefault('BRIDGE_PORT', '8770')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.async_api import async_playwright  # noqa: E402
from ui_cut210 import open_as, BASE, say, RESULT  # noqa: E402

D = '/tmp/uibridge/'
TYPE = '/super-admin/exam/bitsat/bitsat:mocks'
SS = '/app/.screenshots/ui224'; os.makedirs(SS, exist_ok=True)


async def chooser(page, target, label, touch):
    try:
        async with page.expect_file_chooser(timeout=3000) as fc:
            if touch: await page.locator(target).tap()
            else: await page.locator(target).click()
        f = await fc.value
        say(f'{label}: file chooser opens', True); return f
    except Exception as e:
        say(f'{label}: file chooser opens', False, repr(e)[:200]); return None


async def open_dialog(page, size):
    t = time.time(); await page.click('[data-testid=type-upload-pdf]'); await page.wait_for_selector('[data-testid=upload-dialog]')
    dt = round(time.time() - t, 2); say(f'{size}: dialog opens < 2s', dt < 2, dt); print(f'   dialog open {dt}s')
    await page.wait_for_timeout(500)


async def sizes(page, size):
    # Buttons >= 44x44 and text vs button overlap
    info = await page.evaluate("""() => { const out = [];
      for (const id of ['upload-main','upload-key','upload-solutions']) { const box = document.querySelector(`[data-testid=${id}]`); if (!box) continue;
        const b = box.querySelector(`[data-testid=${id}-pick]`).getBoundingClientRect(); const l = box.querySelector('label').getBoundingClientRect();
        const s = getComputedStyle(box.querySelector(`[data-testid=${id}-pick]`));
        out.push({id, bw: b.width, bh: b.height, overlap: l.right > b.left + 0.5 && l.left < b.right && l.bottom > b.top && l.top < b.bottom, bg: s.backgroundColor, color: s.color, text: box.querySelector(`[data-testid=${id}-pick]`).innerText}); }
      const small = [...document.querySelectorAll('[data-testid=upload-dialog] button')].filter(e => e.offsetParent).map(e => [e.dataset.testid || e.getAttribute('aria-label') || e.innerText, Math.round(e.getBoundingClientRect().width), Math.round(e.getBoundingClientRect().height)]).filter(x => x[1] < 44 || x[2] < 44);
      const dlg = document.querySelector('[data-testid=upload-dialog]'); return {out, small, dsw: dlg.scrollWidth, dcw: dlg.clientWidth, sw: document.documentElement.scrollWidth, vw: document.documentElement.clientWidth}; }""")
    for o in info['out']:
        say(f"{size}: {o['id']}-pick visible text 'PDF chuniye'", 'PDF chuniye' in o['text'], o)
        say(f"{size}: {o['id']}-pick >= 44x44", o['bw'] >= 44 and o['bh'] >= 44, (o['bw'], o['bh']))
        say(f"{size}: {o['id']} label does not overlap button", not o['overlap'])
        print('   colors', o['id'], o['bg'], o['color'])
    say(f'{size}: all dialog buttons >= 44px', not info['small'], info['small'])
    say(f'{size}: no horizontal scroll (page/dialog)', info['sw'] <= info['vw'] + 1 and info['dsw'] <= info['dcw'] + 1, info)


async def walk(pw, size):
    br, page, bad, logs = await open_as(pw, 'owner', size); touch = size == 'mob'
    try:
        await page.goto(BASE + TYPE); await page.wait_for_selector('[data-testid=type-upload-pdf]', timeout=25000)
        await open_dialog(page, size)
        await page.screenshot(path=f'{SS}/{size}_dialog.png', quality=40, type='jpeg')
        await sizes(page, size)
        # 1. every pick button + label opens the chooser
        for tid in ('upload-main', 'upload-key', 'upload-solutions'):
            await chooser(page, f'[data-testid={tid}-pick]', f'{size} {tid}-pick', touch)
        await chooser(page, '[data-testid=upload-main] label', f'{size} main label text', touch)
        # 2. pick one file -> name/size, has-file, Badlo, X
        fc = await chooser(page, '[data-testid=upload-main-pick]', f'{size} main pick (again)', touch)
        if fc: await fc.set_files(D + 'two_mocks.pdf')
        await page.wait_for_selector('[data-testid=upload-main].has-file', timeout=5000)
        txt = await page.inner_text('[data-testid=upload-main]')
        say(f'{size}: name + MB shown', 'two_mocks.pdf' in txt and 'MB' in txt, txt)
        say(f'{size}: button reads Badlo', 'Badlo' in await page.inner_text('[data-testid=upload-main-pick]'))
        say(f'{size}: X remove visible', await page.is_visible('[data-testid=upload-main-remove]'))
        await page.screenshot(path=f'{SS}/{size}_picked.png', quality=40, type='jpeg')
        await sizes(page, size + ' picked')
        if touch: await page.locator('[data-testid=upload-main-remove]').tap()
        else: await page.click('[data-testid=upload-main-remove]')
        await page.wait_for_timeout(300)
        say(f'{size}: X clears file', not await page.locator('[data-testid=upload-main].has-file').count() and 'PDF chuniye' in await page.inner_text('[data-testid=upload-main-pick]'))
        # 3. two files -> batch
        fc = await chooser(page, '[data-testid=upload-main-pick]', f'{size} main pick (batch)', touch)
        if fc:
            say(f'{size}: chooser allows multiple', fc.is_multiple(), '')
            await fc.set_files([D + 'two_mocks.pdf', D + 'single_paper.pdf'])
        await page.wait_for_timeout(600)
        rows = await page.locator('[data-testid^=upload-batch-]:not([data-testid=upload-batch-clear]):not([data-testid=upload-batch-note])').count()
        say(f'{size}: batch list shows', rows >= 2 and await page.is_visible('[data-testid=upload-batch-clear]'), rows)
        await page.screenshot(path=f'{SS}/{size}_batch.png', quality=40, type='jpeg')
        await page.click('[data-testid=upload-batch-clear]'); await page.wait_for_timeout(400)
        say(f'{size}: Sab hatao clears batch', not await page.locator('[data-testid=upload-batch-clear]').count() and await page.is_visible('[data-testid=upload-key-pick]'))
        # 4. Cancel closes
        await page.click('[data-testid=upload-cancel]')
        await page.wait_for_selector('[data-testid=upload-dialog]', state='detached', timeout=4000); say(f'{size}: Cancel closes', True)
        if size == 'desk':
            # 5. full upload two_mocks.pdf, watch for Roko
            before = await page.inner_text('[data-testid=type-uploads]') if await page.locator('[data-testid=type-uploads]').count() else ''
            await open_dialog(page, size + ' re-open')
            fc = await chooser(page, '[data-testid=upload-main-pick]', f'{size} pick for upload', touch); await fc.set_files(D + 'two_mocks.pdf')
            await page.check('[data-testid=upload-rights]')
            t = time.time(); await page.click('[data-testid=upload-send]')
            try:
                await page.wait_for_selector('[data-testid=upload-pause]', timeout=3000); say(f'{size}: Roko shown while uploading', True)
            except Exception as e:
                say(f'{size}: Roko shown while uploading', False, 'not seen within 3s (upload may be too fast) ' + repr(e)[:80])
            await page.wait_for_selector('[data-testid=upload-dialog]', state='detached', timeout=60000)
            dt = round(time.time() - t, 2); say(f'{size}: upload completes, dialog closes', True); print(f'   upload took {dt}s')
            toast = await page.locator('[data-sonner-toast]').all_inner_texts(); say(f'{size}: success toast', any('Upload ho gaya' in x for x in toast), toast)
            await page.wait_for_timeout(2500)
            after = await page.inner_text('[data-testid=type-uploads]') if await page.locator('[data-testid=type-uploads]').count() else ''
            say(f'{size}: uploads panel shows new row', 'two_mocks' in after, after[:300]); print('   before uploads:', before[:150].replace('\n', ' | '))
            await page.screenshot(path=f'{SS}/{size}_after_upload.png', quality=40, type='jpeg')
            # 6. questions + answer key merge
            await open_dialog(page, size + ' merge')
            await (await chooser(page, '[data-testid=upload-main-pick]', 'merge main', False)).set_files(D + 'questions_only.pdf')
            await (await chooser(page, '[data-testid=upload-key-pick]', 'merge key', False)).set_files(D + 'answer_key_only.pdf')
            await page.wait_for_selector('[data-testid=upload-key].has-file', timeout=4000)
            say('key box shows Badlo', 'Badlo' in await page.inner_text('[data-testid=upload-key-pick]'))
            await page.check('[data-testid=upload-rights]'); t = time.time(); await page.click('[data-testid=upload-send]')
            await page.wait_for_selector('[data-testid=upload-dialog]', state='detached', timeout=60000)
            print(f'   merge upload took {time.time() - t:.2f}s')
            toast = await page.locator('[data-sonner-toast]').all_inner_texts(); say('merge: success, no error toast', any('Upload ho gaya' in x for x in toast), toast)
        say(f'{size}: no API 5xx', not [b for b in bad if b[0] >= 500], bad[:6]); print('   4xx:', bad[:6], 'console', logs[:4])
    except Exception as e:
        say(f'{size}: walk', False, repr(e)[:300]); await page.screenshot(path=f'{SS}/{size}_error.png', quality=40, type='jpeg')
    finally:
        await br.close()


async def main():
    async with async_playwright() as pw:
        for size in ('desk', 'mob'):
            await walk(pw, size)
    f = [n for n, ok in RESULT if not ok]
    print(f'TOTAL {len(RESULT)} PASS {len(RESULT) - len(f)} FAIL {len(f)}'); [print('  FAILED', n) for n in f]

if __name__ == '__main__':
    asyncio.run(main())
