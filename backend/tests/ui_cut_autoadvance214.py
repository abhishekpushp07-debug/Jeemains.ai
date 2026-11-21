"""TEST-ONLY (iteration 214): CutTool draw-first auto-advance on the plain held fix tool (no save, no mutation):
draw -> kiska hai -> Sawaal -> A armed; re-tap armed A keeps it armed; draw A/B/C/D auto-advance; after D -> Box hilao (move).
Wrap: draw -> D -> next armed is Sawaal. Save race watcher: -good never visible while -checking shown or Save disabled.
Run: python tests/ui_cut_autoadvance214.py
"""
import asyncio, os, sys, importlib.util
os.environ.setdefault('SS_DIR', '/app/.screenshots/ui214')
sys.argv_saved = sys.argv; sys.argv = [sys.argv[0], 'none']
spec = importlib.util.spec_from_file_location('v211', os.path.join(os.path.dirname(__file__), 'ui_verify211_lib.py'))
v = importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
sys.argv = sys.argv_saved
from playwright.async_api import async_playwright
ok, open_as = v.ok, v.open_as
SS = '/app/.screenshots/ui214'; os.makedirs(SS, exist_ok=True)

WATCH = """(t) => { window.__race = []; const chk = () => { const g = document.querySelector('[data-testid="' + t + '-good"]');
 if (!g) return; const c = document.querySelector('[data-testid="' + t + '-checking"]'); const s = document.querySelector('[data-testid="' + t + '-save"]');
 if (c || (s && s.disabled)) window.__race.push({checking: !!c, disabled: !!(s && s.disabled)}); };
 new MutationObserver(chk).observe(document.body, {subtree: true, childList: true, attributes: true}); }"""

# five thin non-overlapping strips down the page
RECTS = [[.08, .10 + i * .12, .92, .16 + i * .12] for i in range(5)]


async def title(page, t):
    return await page.inner_text(f'[data-testid="{t}-assign-title"]')


async def flow(pw, size):
    tag = f'auto-{size}'
    br, page, bad, logs = await open_as(pw, 'owner', size)
    try:
        t = await v.open_fix(page, 'held' if size == 'desk' else 'held')
        await page.evaluate(WATCH, t)
        await v.pull(page, RECTS[0])
        t1 = await title(page, t)
        ok(f'{tag}: draw first asks "Yeh hissa kiska hai?"', 'kiska hai' in t1, t1)
        await page.click(f'[data-testid="{t}-assign-q"]'); await page.wait_for_timeout(300)
        t2 = await title(page, t)
        ok(f'{tag}: after Sawaal, A armed', 'A ka box' in t2, t2)
        await page.click(f'[data-testid="{t}-assign-A"]'); await page.wait_for_timeout(300)
        t2b = await title(page, t)
        ok(f'{tag}: re-tapping armed A keeps A armed', 'A ka box' in t2b and await page.get_attribute(f'[data-testid="{t}-assign-A"]', 'aria-pressed') == 'true', (t2b, await page.get_attribute(f'[data-testid="{t}-assign-A"]', 'aria-pressed')))
        seq = []
        for i, (k, nxt) in enumerate([('A', 'B'), ('B', 'C'), ('C', 'D')]):
            await v.pull(page, RECTS[i + 1])
            tt = await title(page, t); seq.append(tt)
            ok(f'{tag}: drawn rect goes to {k}, {nxt} armed', f'{nxt} ka box' in tt and 'kiska hai' not in tt, tt)
        await v.pull(page, RECTS[4])
        mv = await page.get_attribute(f'[data-testid="{t}-mode-move"]', 'aria-pressed')
        ok(f'{tag}: after D, tool switches to Box hilao (move)', mv == 'true', mv)
        nbox = {k: await page.locator(f'[data-testid="cut-box-{k}"]').count() for k in 'qABCD'}
        ok(f'{tag}: all five boxes present', all(nbox.values()), nbox)
        await page.wait_for_timeout(4000)
        await page.screenshot(path=f'{SS}/auto_{size}_done.jpg', quality=40)
        race = await page.evaluate('window.__race')
        ok(f'{tag}: "Saare check paas" never shown while checking / Save disabled', not race, race[:5])
        # wrap: reset, draw, choose D -> Sawaal armed
        await page.reload(); await page.wait_for_selector('[data-testid="cut-frame"] canvas', timeout=30000); await page.wait_for_timeout(1500)
        t = (await page.locator('[data-testid^="cut-q-"][data-testid$="-status"]').first.get_attribute('data-testid'))[:-7]
        await v.pull(page, RECTS[0])
        await page.click(f'[data-testid="{t}-assign-D"]'); await page.wait_for_timeout(300)
        tw = await title(page, t)
        ok(f'{tag}: after D (no Sawaal box yet) next wraps to Sawaal', 'Sawaal ka box' in tw or 'sawaal ka box' in tw.lower(), tw)
        await v.no_overflow(page, tag)
        ok(f'{tag}: no API / page errors', not bad and not logs, (bad[:4], logs[:3]))
    except Exception as e:
        ok(tag + ' walk', False, (str(e)[:300], bad[:3], logs[:3])); await page.screenshot(path=f'{SS}/auto_{size}_err.jpg', quality=40)
    await br.close()


async def main():
    async with async_playwright() as pw:
        for s in ('desk', 'mob'):
            await flow(pw, s)
    print('TOTAL', len(v.R), 'PASS', sum(o for _, o in v.R), 'FAIL', sum(not o for _, o in v.R))

asyncio.run(main())
