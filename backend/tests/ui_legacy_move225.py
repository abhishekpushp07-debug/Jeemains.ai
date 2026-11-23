"""TEST-ONLY iteration 218 (testing agent): 'Purani files' (LegacyMove) section in the Storage badge popover, on the bridge 127.0.0.1:8774.
Usage: cd /app/backend && BRIDGE_OUT=/tmp/uibridge224 BRIDGE_PORT=8774 python tests/ui_legacy_move225.py down|copy|after|mobile
 down  : flag present -> start disabled + wait note, title count 3
 copy  : removes flag, 'Abhi phir try karo', Copy -> 2 copied, 1 failed listed (old_lost.png + reason); re-creates flag
 after : flag present -> no start or disabled/wait note (or 409 toast)
 mobile: 390x844 popover scrolls and no overflow
"""
import asyncio, json, os, sys, time
from pathlib import Path
os.environ.setdefault('BRIDGE_OUT', '/tmp/uibridge224'); os.environ.setdefault('BRIDGE_PORT', '8774')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.async_api import async_playwright  # noqa: E402
from ui_cut210 import open_as, BASE, say, RESULT  # noqa: E402

D = '/tmp/uibridge224/'; FLAG = D + 'supabase_down'
INFO = json.load(open(D + 'bridge.json'))
SS = '/app/.screenshots/ui225move'; os.makedirs(SS, exist_ok=True)


async def popover(page):
    await page.goto(BASE + INFO['type']); await page.wait_for_selector('[data-testid=storage-badge]', timeout=25000)
    await page.click('[data-testid=storage-badge]'); await page.wait_for_selector('[data-testid=storage-details]')
    await page.wait_for_timeout(1500)


async def txt(page, tid):
    loc = page.locator(f'[data-testid={tid}]')
    return await loc.inner_text() if await loc.count() else None


async def toasts(page):
    await page.wait_for_timeout(1200); return ' | '.join(await page.locator('[data-sonner-toast]').all_inner_texts())


async def down(pw):
    br, page, bad, logs = await open_as(pw, 'owner', 'desk')
    try:
        await popover(page)
        say('down: legacy-move section visible', await page.is_visible('[data-testid=legacy-move]'))
        t = await txt(page, 'move-title'); say('down: title Purani files Emergent mein: 3', t and t.strip() == 'Purani files Emergent mein: 3', t)
        say('down: start button disabled', await page.locator('[data-testid=move-start]').is_disabled())
        w = await txt(page, 'move-wait-note'); say('down: wait note', w and 'Supabase abhi taiyaar nahi' in w, w)
        det = await page.inner_text('[data-testid=storage-details]')
        say('down: no storage paths shown', 'tejas/' not in det and 'sb://' not in det, det[:300])
        await page.locator('[data-testid=legacy-move]').scroll_into_view_if_needed()
        await page.screenshot(path=f'{SS}/down.jpg', quality=40, type='jpeg')
        say('down: no 5xx', not [b for b in bad if b[0] >= 500], bad[:5]); print('  bad/logs', bad[:5], logs[:3])
    finally:
        await br.close()


async def copy(pw):
    br, page, bad, logs = await open_as(pw, 'owner', 'desk')
    try:
        if os.path.exists(FLAG): os.remove(FLAG)
        await popover(page)
        if await page.locator('[data-testid=storage-retry-now]').count():
            await page.click('[data-testid=storage-retry-now]'); print('  retry toast:', await toasts(page))
        await page.wait_for_timeout(1500)
        await page.keyboard.press('Escape'); await page.wait_for_timeout(300)
        await popover(page)
        t0 = time.time()
        while time.time() - t0 < 20 and await page.locator('[data-testid=move-start]').is_disabled():
            await page.wait_for_timeout(1000)
        say('copy: start enabled when Supabase up', not await page.locator('[data-testid=move-start]').is_disabled())
        await page.click('[data-testid=move-start]'); states = []
        t0 = time.time()
        while time.time() - t0 < 60:
            s = await txt(page, 'move-state'); p = await txt(page, 'move-progress'); states.append((s, p))
            if s and 'poori' in s: break
            await page.wait_for_timeout(1000)
        print('  states seen:', list(dict.fromkeys(states))[:8])
        prog = await txt(page, 'move-progress'); st = await txt(page, 'move-state'); title = await txt(page, 'move-title')
        say('copy: state done', st and 'Copy poori hui' in st, st)
        say('copy: progress 2 copied 1 failed', prog and '3 / 3' in prog and '2 copy hui' in prog and '1 nahi ho payi' in prog, prog)
        say('copy: title now 1 left', title and title.strip().endswith(': 1'), title)
        f = await txt(page, 'move-failure-0'); say('copy: failure lists old_lost.png with reason', f and 'old_lost.png' in f and len(f) > 30, f)
        say('copy: only one failure', await page.locator('[data-testid^=move-failure-]').count() == 1)
        say('copy: failure has no storage paths', f and 'tejas/' not in f and 'sb://' not in f, f)
        say('copy: stop button gone after done', not await page.locator('[data-testid=move-stop]').count())
        say('copy: start offered again for the failed one', await page.locator('[data-testid=move-start]').count() == 1)
        await page.locator('[data-testid=legacy-move]').scroll_into_view_if_needed()
        await page.screenshot(path=f'{SS}/copy_done.jpg', quality=40, type='jpeg')
        say('copy: no 5xx', not [b for b in bad if b[0] >= 500], bad[:5]); print('  bad/logs', bad[:5], logs[:3])
    finally:
        Path(FLAG).touch(); print('  flag re-created')
        await br.close()


async def after(pw):
    br, page, bad, logs = await open_as(pw, 'owner', 'desk')
    try:
        await page.wait_for_timeout(1000)
        await popover(page)
        start = page.locator('[data-testid=move-start]')
        if await start.count() and not await start.is_disabled():
            await start.click(); t = await toasts(page); say('after: Copy while down -> 409 toast', 'Supabase' in t, t)
        else:
            w = await txt(page, 'move-wait-note'); say('after: start disabled / wait note while down', (not await start.count()) or (w and 'taiyaar nahi' in w), w)
        print('  title/state:', await txt(page, 'move-title'), '|', await txt(page, 'move-state'), '|', await txt(page, 'move-progress'))
        await page.screenshot(path=f'{SS}/after_down.jpg', quality=40, type='jpeg')
        r = await page.evaluate("async()=>{const r=await fetch('/api/admin/storage/move/start',{method:'POST',credentials:'include'});return [r.status, await r.text()]}")
        say('after: API start while down -> 409', r[0] == 409, r)
    finally:
        await br.close()


async def mobile(pw):
    br, page, bad, logs = await open_as(pw, 'owner', 'mob')
    try:
        await popover(page)
        o = await page.evaluate("""()=>{const vw=document.documentElement.clientWidth;const d=document.querySelector('[data-testid=storage-details]');const r=d.getBoundingClientRect();
          const out=[...d.querySelectorAll('*')].filter(e=>{const b=e.getBoundingClientRect();return e.offsetParent&&(b.right>vw+1||b.left<-1)}).map(e=>e.dataset.testid||e.tagName).slice(0,6);
          return {vw,sw:document.documentElement.scrollWidth,left:r.left,right:r.right,top:r.top,bottom:r.bottom,vh:innerHeight,sh:d.scrollHeight,ch:d.clientHeight,oy:getComputedStyle(d).overflowY,out}}""")
        print('  mobile popover', o)
        say('mobile: popover inside viewport width', o['left'] >= -1 and o['right'] <= o['vw'] + 1 and not o['out'] and o['sw'] <= o['vw'] + 1, o)
        say('mobile: popover fits height or scrolls', o['bottom'] <= o['vh'] + 1 or o['oy'] in ('auto', 'scroll'), o)
        await page.locator('[data-testid=legacy-move]').scroll_into_view_if_needed()
        say('mobile: legacy-move reachable', await page.locator('[data-testid=legacy-move]').is_visible())
        await page.screenshot(path=f'{SS}/mobile.jpg', quality=40, type='jpeg')
    finally:
        await br.close()


async def main():
    async with async_playwright() as pw:
        await {'down': down, 'copy': copy, 'after': after, 'mobile': mobile}[sys.argv[1]](pw)
    print(f"TOTAL {len(RESULT)} PASS {sum(1 for r in RESULT if r[1])} FAIL {sum(1 for r in RESULT if not r[1])}")


if __name__ == '__main__':
    asyncio.run(main())
