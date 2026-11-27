"""TEST-ONLY iteration 261: PICTURES ONLY, nothing is checked and nothing is pressed. The website's Home, Rank, My Tests and Misfire at a
phone's size (390 px), to lay beside the owner's five screenshots of the app (27 Nov 2026, kept in /root/appbook/owner_shots3).
/api is routed to tests/analysis_bridge196.py (127.0.0.1:8783: a signed-in student in a disposable DB).
Run: cd /app/backend && bash /root/p2/solo.sh bash /root/p2/look_ui.sh     -> /app/.screenshots/ui261/*.jpg
"""
import asyncio, os, sys
from pathlib import Path
os.environ.setdefault('BRIDGE_OUT', '/tmp/uibridge260'); os.environ.setdefault('BRIDGE_PORT', '8783')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.async_api import async_playwright  # noqa: E402
from ui_cut210 import open_as, BASE, B  # noqa: E402

SS = '/app/.screenshots/ui261'; os.makedirs(SS, exist_ok=True)
TOP = "sel => { const e = document.querySelector(sel); if (e) scrollTo(0, e.getBoundingClientRect().top + scrollY - 76); return !!e; }"
COLOURS = """() => { const out = {}; const css = (sel, props) => { const e = document.querySelector(sel); if (!e) return; const s = getComputedStyle(e); out[sel] = Object.fromEntries(props.map(p => [p, s[p].slice(0, 140)])); };
  const v = getComputedStyle(document.documentElement); out.vars = Object.fromEntries(['--brand', '--brand-text', '--brand-soft', '--ink', '--page', '--surface', '--surface-alt', '--line', '--text-muted', '--feature-bg'].map(k => [k, v.getPropertyValue(k).trim()]));
  out.font = getComputedStyle(document.body).fontFamily.slice(0, 120);
  css('[data-testid=bottom-tabs]', ['backgroundColor']); css('.practice-card', ['backgroundImage', 'backgroundColor', 'borderColor', 'borderRadius']); css('.practice-card h3, .practice-card strong', ['color']);
  css('.rank-tool', ['backgroundImage', 'backgroundColor', 'borderColor', 'borderRadius', 'color']); css('.fy-icon', ['backgroundColor']); return out; }"""


async def main():
    async with async_playwright() as pw:
        br, page, bad, logs = await open_as(pw, 'hero', 'mob')

        async def shot(name):
            await page.wait_for_timeout(600); await page.screenshot(path=f'{SS}/{name}.jpg', quality=45, type='jpeg'); print('shot', name, flush=True)
        try:
            await page.goto(BASE + '/home'); await page.wait_for_selector('[data-testid=home-for-you-rapid-fire]', timeout=45000); await page.wait_for_timeout(1500)
            print('home colours', await page.evaluate(COLOURS), flush=True)
            await page.evaluate(TOP, '[data-testid=exam-home-exam-card-grid]'); await shot('web_home_practice')
            await page.goto(BASE + '/rank'); await page.wait_for_timeout(4500)
            print('rank colours', await page.evaluate(COLOURS), flush=True); await shot('web_rank_top')
            await page.mouse.wheel(0, 640); await shot('web_rank_2')
            await page.goto(BASE + '/profile'); await page.wait_for_timeout(3500); await shot('web_my_tests')
            await page.goto(BASE + '/misfire'); await page.wait_for_timeout(3500); await shot('web_misfire')
            # added 27 Nov (second walk): the rest of the owner's ten app pictures, and Rank in the website's dark theme
            await page.goto(BASE + '/home'); await page.wait_for_selector('[data-testid=home-greeting]', timeout=45000); await page.wait_for_timeout(1500); await shot('web_home_top')
            if await page.evaluate(TOP, '[data-testid=home-dream]'): await shot('web_home_dream')
            await page.evaluate('scrollTo(0, document.body.scrollHeight)'); await shot('web_home_end')
            await page.goto(f"{BASE}/results/{B['hero_attempt']}"); await page.wait_for_timeout(6000); await shot('web_result_top')
            await page.mouse.wheel(0, 700); await shot('web_result_2')
            await page.evaluate("localStorage.setItem('jeelive-theme', 'dark')")
            await page.goto(BASE + '/rank'); await page.wait_for_timeout(4500)
            print('rank dark colours', await page.evaluate(COLOURS), flush=True); await shot('web_rank_dark_top')
            await page.mouse.wheel(0, 640); await shot('web_rank_dark_2')
            await page.evaluate("localStorage.setItem('jeelive-theme', 'light')")
        except Exception as e:  # noqa: BLE001
            print('ERR', repr(e)[:400])
        finally:
            print('failed calls', bad[:10], flush=True); await br.close()

asyncio.run(main())
