"""TEST-ONLY (iteration 213): Try as student extras — toast on Fix page, back link href + click back, popup-blocked same-tab fallback,
MockList Draft rows open a new tab. Reuses ui_verify211_lib (routes /api on the context to bridge :8772).
Run: python tests/ui_tryst_extra213.py
"""
import asyncio, os, sys, importlib.util
from urllib.parse import unquote
os.environ.setdefault('SS_DIR', '/app/.screenshots/ui213')
sys.argv_saved = sys.argv; sys.argv = [sys.argv[0], 'none']
spec = importlib.util.spec_from_file_location('v211', os.path.join(os.path.dirname(__file__), 'ui_verify211_lib.py'))
v = importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
sys.argv = sys.argv_saved
from playwright.async_api import async_playwright
ok, open_as, F, BASE = v.ok, v.open_as, v.F, v.BASE
SS = '/app/.screenshots/ui213'; os.makedirs(SS, exist_ok=True)


# New tab: toast + back href = Fix path; clicking back lands on Fix page
async def toast_and_back(pw, size):
    tag = f'extra-toast-{size}'
    br, fix, bad, logs = await open_as(pw, 'owner', size)
    try:
        bid, mid = F['boxed_small']; path = f'/super-admin/fix/{bid}/{mid}'
        await fix.goto(BASE + path + '?all=1'); await fix.wait_for_selector('[data-testid="all-questions-list"]', timeout=30000)
        btn = fix.locator(f'[data-testid="mock-try-{mid}"]')
        ok(f'{tag}: Try button label', 'Try as student' in await btn.inner_text())
        async with fix.context.expect_page(timeout=15000) as ti:
            await btn.click()
        tab = await ti.value
        await tab.wait_for_url('**/sets/**', timeout=30000)
        print('   new tab url', tab.url)
        ok(f'{tag}: new tab URL has preview=true&back=<fix path>', 'preview=true' in tab.url and path in unquote(tab.url), tab.url)
        await fix.wait_for_selector('text=Student paper naye tab me khul gaya', timeout=10000)
        ok(f'{tag}: success toast on Fix page', True)
        await fix.screenshot(path=f'{SS}/toast_{size}.jpg', quality=40)
        ok(f'{tag}: first tab still on Fix page', path in fix.url, fix.url)
        await tab.wait_for_selector('[data-testid="set-back"]', timeout=20000)
        href = await tab.get_attribute('[data-testid="set-back"]', 'href')
        ok(f'{tag}: set-back href points to Fix page', href and href.startswith(path), href)
        await tab.click('[data-testid="set-back"]')
        await tab.wait_for_url('**/super-admin/fix/**', timeout=15000)
        ok(f'{tag}: back link navigates to Fix page', path in tab.url, tab.url)
        # tampered back param must be ignored
        await tab.goto(f'{BASE}/sets/{F["live_set"]}?preview=true&back=' + '%2F%2Fevil.com'); await tab.wait_for_selector('[data-testid="set-back"]', timeout=20000)
        href2 = await tab.get_attribute('[data-testid="set-back"]', 'href'); txt = await tab.inner_text('[data-testid="set-back"]')
        ok(f'{tag}: non /super-admin back param ignored', 'evil' not in (href2 or '') and 'Back to Content Studio' in txt, (href2, txt))
        ok(f'{tag}: no API / page errors', not bad and not logs, (bad[:4], logs[:3]))
    except Exception as e:
        ok(tag + ' walk', False, (str(e)[:300], bad[:3], logs[:3])); await fix.screenshot(path=f'{SS}/toast_{size}_err.jpg', quality=40)
    await br.close()


# window.open blocked -> same-tab navigation, back reads Back to Master
async def blocked(pw, size):
    tag = f'extra-blocked-{size}'
    br, fix, bad, logs = await open_as(pw, 'owner', size)
    try:
        await fix.context.add_init_script('window.open = () => null;')
        bid, mid = F['boxed']; path = f'/super-admin/fix/{bid}/{mid}'
        await fix.goto(BASE + path + '?all=1'); await fix.wait_for_selector('[data-testid="all-questions-list"]', timeout=30000)
        n0 = len(fix.context.pages)
        await fix.click(f'[data-testid="mock-try-{mid}"]')
        await fix.wait_for_url('**/sets/**', timeout=30000)
        ok(f'{tag}: same-tab fallback to live set', F['live_set'] in fix.url and len(fix.context.pages) == n0, fix.url)
        await fix.wait_for_selector('[data-testid="set-back"]', timeout=20000)
        ok(f'{tag}: back reads Back to Master', 'Back to Master' in await fix.inner_text('[data-testid="set-back"]'))
        ok(f'{tag}: no API / page errors', not bad and not logs, (bad[:4], logs[:3]))
    except Exception as e:
        ok(tag + ' walk', False, (str(e)[:300], bad[:3], logs[:3])); await fix.screenshot(path=f'{SS}/blocked_{size}_err.jpg', quality=40)
    await br.close()


# MockList Draft rows: Try as student opens a new tab, list stays
async def mocklist(pw, size):
    tag = f'extra-mocklist-{size}'
    br, page, bad, logs = await open_as(pw, 'owner', size)
    try:
        found = False
        for sec in ('chapters', 'section'):
            url = f"{BASE}/super-admin/exam/{F['slug']}/{F[sec]}"
            await page.goto(url); await page.wait_for_selector('[data-testid^="mock-row-"]', timeout=30000); await page.wait_for_timeout(1500)
            tries = page.locator('[data-testid="mock-list"] [data-testid^="mock-try-"], [data-testid^="mock-row-"] [data-testid^="mock-try-"]')
            n = await tries.count(); print(f'   {sec}: try buttons', n)
            if not n: continue
            found = True
            async with page.context.expect_page(timeout=15000) as ti:
                await tries.first.click()
            tab = await ti.value
            await tab.wait_for_url('**/sets/**', timeout=40000)
            ok(f'{tag}: {sec} list stays in first tab', f"/super-admin/exam/{F['slug']}/{F[sec]}" in page.url, page.url)
            await tab.wait_for_selector('[data-testid="set-preflight-start-button"]', timeout=20000)
            ok(f'{tag}: {sec} new tab shows private preview + Back to Master', await tab.locator('[data-testid="private-preview-notice"]').count() == 1 and 'Back to Master' in await tab.inner_text('[data-testid="set-back"]'))
            await tab.screenshot(path=f'{SS}/mocklist_{sec}_{size}.jpg', quality=40)
            await tab.close()
            break
        ok(f'{tag}: at least one Draft row has Try as student', found)
        ok(f'{tag}: no API / page errors', not bad and not logs, (bad[:4], logs[:3]))
    except Exception as e:
        ok(tag + ' walk', False, (str(e)[:300], bad[:3], logs[:3])); await page.screenshot(path=f'{SS}/mocklist_{size}_err.jpg', quality=40)
    await br.close()


async def main():
    async with async_playwright() as pw:
        for s in ('desk', 'mob'):
            await toast_and_back(pw, s); await blocked(pw, s); await mocklist(pw, s)
    print('TOTAL', len(v.R), 'PASS', sum(o for _, o in v.R), 'FAIL', sum(not o for _, o in v.R))

asyncio.run(main())
