"""OPERATIONAL (owner-approved, 2026-11-21): read-only look at the boxed book's Draft chapters on the REAL preview, signed in as the owner.
Proof view of two chapters on desktop and phone: every question drawn, options one below another, nothing sliding sideways. Nothing is changed.
Reads ADMIN_EMAIL / ADMIN_PASSWORD from backend/.env inside the script (never printed); signs out at the end.
Run: cd /app/backend && python tests/preview_ui211.py <book_id> <mock_id> [<mock_id> ...]
"""
import asyncio, os, sys
from pathlib import Path
from dotenv import dotenv_values
from playwright.async_api import async_playwright
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ui_cut210 import LAYOUT, OVERFLOW, shaped, say, RESULT  # noqa: E402

ENV = dotenv_values(Path(__file__).resolve().parents[1] / '.env')
BASE = [l.split('=', 1)[1].strip() for l in open('/app/frontend/.env') if l.startswith('REACT_APP_BACKEND_URL')][0].rstrip('/')
SS = '/app/.screenshots/preview211'; os.makedirs(SS, exist_ok=True)


async def main(bid, mids):
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        ctx = await br.new_context(viewport={'width': 1920, 'height': 800})
        page = await ctx.new_page()
        await page.goto(f'{BASE}/owner-login')
        await page.fill('#login-email-input', ENV['ADMIN_EMAIL']); await page.fill('#login-password-input', ENV['ADMIN_PASSWORD'])
        await page.keyboard.press('Enter'); await page.wait_for_url('**/super-admin**', timeout=30000)
        try:
            for size, (w, h) in (('desk', (1920, 800)), ('mob', (390, 844))):
                await page.set_viewport_size({'width': w, 'height': h})
                for mid in mids:
                    tag = f'preview {size} {mid[:8]}'
                    await page.goto(f'{BASE}/super-admin/fix/{bid}/{mid}?all=1')
                    await page.click('[data-testid="all-questions-filter-proof"]', timeout=30000)
                    await page.wait_for_selector('[data-testid="proof-list"] canvas.piece-img', timeout=60000); await page.wait_for_timeout(4000)
                    rows = await page.locator('[data-testid="proof-list"] > li').count()
                    boxes = page.locator('[data-testid="proof-list"] [data-testid$="-piece-options"]')
                    n = await boxes.count(); good = 0
                    for i in range(n):
                        tid = await boxes.nth(i).get_attribute('data-testid')
                        good += shaped(await page.evaluate(LAYOUT, f'[data-testid="{tid}"]'))
                    say(f'{tag}: every option question shows A, B, C, D one below another ({good} of {n}, {rows} questions)', n and good == n, (good, n))
                    over = await page.evaluate(OVERFLOW)
                    say(f'{tag}: nothing slides sideways', not over, over)
                    await page.screenshot(path=f'{SS}/proof_{size}_{mid[:8]}.jpg', quality=40)
        finally:
            await page.evaluate("fetch('/api/auth/logout', {method: 'POST', credentials: 'include'})"); await page.wait_for_timeout(800)
            await br.close()
    print('TOTAL', len(RESULT), 'PASS', sum(ok for _, ok in RESULT))


if __name__ == '__main__':
    asyncio.run(main(sys.argv[1], sys.argv[2:]))
