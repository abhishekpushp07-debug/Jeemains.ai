"""TEST-ONLY iteration 219 QA (testing agent): LegacyMove ('Purani files Supabase mein copy karo') UI on bridge 127.0.0.1:8774.
A) Supabase down: 3 old files listed, Copy disabled + wait note.  B) Supabase up: Copy -> 2 copied, 1 failed (Hinglish, no path), '3 / 3', bar full.
C) flag re-created, Copy clicked at once (status still says ready) -> 409 toast.  Leaves the flag in place.
Run: cd /app/backend && BRIDGE_OUT=/tmp/uibridge224 BRIDGE_PORT=8774 python tests/ui_legacy_move226.py [mob]
"""
import asyncio, json, os, sys, time
from pathlib import Path
os.environ.setdefault('BRIDGE_OUT', '/tmp/uibridge224'); os.environ.setdefault('BRIDGE_PORT', '8774')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.async_api import async_playwright  # noqa: E402
from ui_cut210 import open_as, BASE, say, RESULT  # noqa: E402

D = '/tmp/uibridge224/'; FLAG = D + 'supabase_down'
INFO = json.load(open(D + 'bridge.json'))
SS = '/app/.screenshots/ui226'; os.makedirs(SS, exist_ok=True)
SIZE = 'mob' if 'mob' in sys.argv else 'desk'


async def toasts(page):
    await page.wait_for_timeout(1200); return ' | '.join(await page.locator('[data-sonner-toast]').all_inner_texts())


async def popover(page):
    await page.click('[data-testid=storage-badge]'); await page.wait_for_selector('[data-testid=storage-details]'); await page.wait_for_timeout(1500)


async def main():
    async with async_playwright() as pw:
        br, page, bad, logs = await open_as(pw, 'owner', SIZE)
        try:
            await page.goto(BASE + INFO['type']); await page.wait_for_selector('[data-testid=storage-badge]', timeout=25000)
            await popover(page)
            if os.path.exists(FLAG):
                title = await page.locator('[data-testid=move-title]').inner_text()
                say('A: title lists 3 old files', title.strip() == 'Purani files Emergent mein: 3', title)
                say('A: Copy disabled while Supabase down', await page.locator('[data-testid=move-start]').is_disabled())
                say('A: wait note shown', await page.is_visible('[data-testid=move-wait-note]'))
                await page.locator('[data-testid=legacy-move]').scroll_into_view_if_needed()
                await page.screenshot(path=f'{SS}/{SIZE}_A_down.jpg', quality=40, type='jpeg')
                os.remove(FLAG); print('   flag removed')
                await page.click('[data-testid=storage-retry-now]'); print('   retry toast:', await toasts(page))
                await page.keyboard.press('Escape'); await page.wait_for_timeout(500); await popover(page)
            say('B: Copy enabled with Supabase up', await page.locator('[data-testid=move-start]').is_enabled())
            await page.click('[data-testid=move-start]')
            t0 = time.time(); prog = ''
            while time.time() - t0 < 60:
                st = await page.locator('[data-testid=move-state]').inner_text() if await page.locator('[data-testid=move-state]').count() else ''
                prog = await page.locator('[data-testid=move-progress]').inner_text() if await page.locator('[data-testid=move-progress]').count() else ''
                if 'poori' in st: break
                await page.wait_for_timeout(1500)
            print('   state/progress:', st, '|', prog)
            say('B: run finished (Copy poori hui)', 'Copy poori hui' in st, st)
            say("B: progress '3 / 3 · 2 copy hui · 1 nahi ho payi'", prog.strip() == '3 / 3 · 2 copy hui · 1 nahi ho payi', prog)
            bar = await page.evaluate("()=>{const p=document.querySelector('[data-testid=legacy-move] progress');return p?[p.value,p.max]:null}")
            say('B: progress bar full', bar and bar[0] == bar[1] == 3, bar)
            fails = await page.locator('[data-testid^=move-failure-]').all_inner_texts()
            print('   failures:', fails)
            say('B: exactly 1 failure listed', len(fails) == 1, fails)
            f = fails[0] if fails else ''
            say('B: failure reason Hinglish', 'Emergent' in f and ('nahi' in f or 'match nahi' in f), f)
            say('B: failure shows no path / raw error', 'tejas/' not in f and 'ui224' not in f.split('\n', 1)[-1] and 'TEST' not in f and '/' not in f.split('\n', 1)[-1], f)
            title = await page.locator('[data-testid=move-title]').inner_text()
            say('B: title now 1 left', title.strip() == 'Purani files Emergent mein: 1', title)
            await page.locator('[data-testid=legacy-move]').scroll_into_view_if_needed()
            await page.screenshot(path=f'{SS}/{SIZE}_B_done.jpg', quality=40, type='jpeg')
            # C: Supabase goes down again; status in the popover still says ready -> click at once
            Path(FLAG).touch(); print('   flag re-created')
            enabled = await page.locator('[data-testid=move-start]').is_enabled()
            say('C: Copy still clickable (stale ready status)', enabled)
            t1 = time.time(); await page.click('[data-testid=move-start]')
            t = await toasts(page); dt = time.time() - t1
            say('C: 409 toast right away', 'Supabase abhi jawab nahi de raha' in t, t)
            print(f'   toast after {dt:.1f}s')
            say('C: toast within 10 s', dt < 10, dt)
            say('C: 409 seen on /move/start', any(b[0] == 409 and 'move/start' in b[1] for b in bad), bad)
            await page.screenshot(path=f'{SS}/{SIZE}_C_409.jpg', quality=40, type='jpeg')
            say('no 5xx', not [b for b in bad if b[0] >= 500], bad[:6]); print('   4xx/console', bad[:6], logs[:4])
            o = await page.evaluate("()=>{const vw=document.documentElement.clientWidth;const e=document.querySelector('[data-testid=legacy-move]');const r=e?e.getBoundingClientRect():null;return {vw,sw:document.documentElement.scrollWidth,l:r&&r.left,r:r&&r.right}}")
            say('legacy-move fits the viewport', o['sw'] <= o['vw'] + 1 and (o['r'] or 0) <= o['vw'] + 1, o)
        except Exception as e:
            say('legacy walk', False, repr(e)[:300]); await page.screenshot(path=f'{SS}/{SIZE}_err.jpg', quality=40, type='jpeg')
        finally:
            Path(FLAG).touch()
            await br.close()
    f = [n for n, ok in RESULT if not ok]
    print(f'TOTAL {len(RESULT)} PASS {len(RESULT) - len(f)} FAIL {len(f)}'); [print('  FAILED', n) for n in f]

if __name__ == '__main__':
    asyncio.run(main())
