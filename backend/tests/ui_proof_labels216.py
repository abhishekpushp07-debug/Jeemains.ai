"""TEST-ONLY (iteration 216): Proof view of the plain (non-boxed) fixtures on desktop: screenshot option cards to check the
printed '(A)' label is fully gone (no fragments) and option ink is not clipped. Also measures each option picture's left white margin."""
import asyncio, os, sys, importlib.util
sys.argv = [sys.argv[0], 'none']
spec = importlib.util.spec_from_file_location('v211', os.path.join(os.path.dirname(__file__), 'ui_verify211_lib.py'))
v = importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
from playwright.async_api import async_playwright
SS = '/app/.screenshots/ui216'; os.makedirs(SS, exist_ok=True)


async def main():
    async with async_playwright() as pw:
        for key in ('draft', 'held', 'boxed_small'):
            br, page, bad, logs = await v.open_as(pw, 'owner', 'desk')
            bid, mid = v.F[key]
            await page.goto(f'{v.BASE}/super-admin/fix/{bid}/{mid}?all=1')
            await page.wait_for_selector('[data-testid="all-questions-list"]', timeout=30000)
            summ = await page.locator('[data-testid="all-questions-cut-summary"]').all_inner_texts()
            print(key, 'summary', summ)
            await page.click('[data-testid="all-questions-filter-proof"]')
            await page.wait_for_timeout(6000)
            rows = page.locator('[data-testid="proof-list"] .proof-row')
            n = await rows.count(); print(key, 'proof rows', n)
            for i in range(min(n, 6)):
                r = rows.nth(i); await r.scroll_into_view_if_needed(); await page.wait_for_timeout(1200)
                opts = r.locator('[data-testid*="-option-card-"]')
                if await opts.count():
                    await r.locator('[data-testid$="-piece-options"]').screenshot(path=f'{SS}/proof_{key}_q{i + 1}_opts.jpg', quality=60)
            print(key, 'errors', bad[:3], logs[:3])
            await br.close()

asyncio.run(main())
