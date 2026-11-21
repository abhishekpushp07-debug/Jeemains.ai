"""TEST-ONLY (iteration 217): fix the held Q1 of a duplicate mock, then Go Live (duplicates are warning only) and watch publish progress.
Run: python tests/ui_dup_live217.py <book_id> <mock_id>"""
import asyncio, sys, time
sys.path.insert(0, '/app/backend/tests')
from playwright.async_api import async_playwright
from ui_master217_lib import open_as, ok, R, BASE, SS, mongo

BID, MID = sys.argv[1], sys.argv[2]


async def main():
    async with async_playwright() as pw:
        br, page, bad, logs = await open_as(pw, 'owner', 1920, 1000)
        try:
            await page.goto(f'{BASE}/super-admin/fix/{BID}/{MID}'); await page.wait_for_selector('[data-testid="held-mock-override-open"]', timeout=30000)
            await page.click('[data-testid="held-mock-override-open"]'); await page.wait_for_timeout(300)
            await page.click('[data-testid="held-mock-override-confirm"]'); await page.wait_for_timeout(5000)
            st = mongo(f"db.tejas_book_mocks.findOne({{_id:'{MID}'}}).state")
            print('mock state after save', st)
            toasts = await page.evaluate("() => [...document.querySelectorAll('[data-sonner-toast]')].map(t => (t.dataset.type||'') + ':' + t.textContent)")
            print('toasts', toasts)
            await page.goto(f'{BASE}/super-admin/exam/jee-main/jee-main:mocks'); await page.wait_for_selector('[data-testid="mock-list"]', timeout=30000)
            await page.wait_for_timeout(1500)
            sw = f'[data-testid="mock-live-switch-{MID}"]'
            print('row', await page.text_content(f'[data-testid="mock-row-{MID}"]'))
            dis = await page.is_disabled(sw)
            ok('duplicate mock: Live switch enabled (warning only)', not dis)
            if not dis:
                await page.click(sw)
                seen, prog, facts = [], [], []; t0 = time.time()
                while time.time() - t0 < 100:
                    p = mongo("JSON.stringify(db.tejas_publish_progress.find().toArray())")
                    if p not in ('[]', '') and (not prog or prog[-1] != p): prog.append(p)
                    try:
                        w = await page.text_content(f'[data-testid="mock-live-word-{MID}"]', timeout=1000)
                    except Exception:
                        w = None
                    sets_live = mongo("db.tejas_sets.countDocuments({status:'live'})")
                    seen.append((round(time.time() - t0), w, sets_live))
                    f = await page.locator('[data-testid="mock-list"] small').all_text_contents()
                    f = [x for x in f if 'Pictures' in x]
                    if f: facts.append(f[0])
                    if sets_live not in ('0', ''):
                        break
                    await page.wait_for_timeout(700)
                print('seen', seen[-6:]); print('progress docs', prog[:5]); print('Pictures facts', facts[:3])
                ok('go live: a set became live', seen and seen[-1][2] not in ('0', ''), seen[-3:])
                await asyncio.sleep(3)
                ok('publish progress doc removed', mongo("db.tejas_publish_progress.countDocuments()") == '0')
                await page.reload(); await page.wait_for_selector('[data-testid="mock-list"]', timeout=30000); await page.wait_for_timeout(2000)
                nd = await page.locator('[data-testid^="mock-duplicates-"]').count()
                ok('after Live: both items still flagged', nd == 2, nd)
                await page.screenshot(path=f'{SS}/dups-after-live.jpg', quality=40)
            ok('no page errors', not logs, logs[:3]); print('bad', bad[:8])
        finally:
            await br.close()
    print('TOTAL', len(R), 'PASS', sum(1 for _, x in R if x), 'FAIL', sum(1 for _, x in R if not x))

asyncio.run(main())
