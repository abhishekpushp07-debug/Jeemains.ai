"""TEST-ONLY (iteration 214): Solutions class wait text uses '1 student' singular when one student finished.
Run: python tests/ui_class_wait214.py
"""
import asyncio, os, sys, importlib.util, re
sys.argv_saved = sys.argv; sys.argv = [sys.argv[0], 'none']
spec = importlib.util.spec_from_file_location('v211', os.path.join(os.path.dirname(__file__), 'ui_verify211_lib.py'))
v = importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
sys.argv = sys.argv_saved
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as pw:
        for size in ('desk', 'mob'):
            br, page, bad, logs = await v.open_as(pw, 'student', size)
            try:
                await page.goto(f"{v.BASE}/results/{v.F['done_attempt']}?view=solutions")
                await page.wait_for_selector('[data-testid="solution-question-rail"]', timeout=30000)
                await page.wait_for_timeout(1500)
                ws = await page.locator('[data-testid="solution-class-wait"]').all_inner_texts()
                print('   wait texts', size, ws[:2])
                bad_plural = [w for w in ws if re.search(r'\b1 students\b', w)]
                n = [re.search(r'Abhi (\d+) (\w+) ne', w) for w in ws]
                good = all((m.group(2) == ('student' if m.group(1) == '1' else 'students')) for m in n if m)
                v.ok(f'class-wait-{size}: wait text shown', len(ws) > 0, ws)
                v.ok(f'class-wait-{size}: singular/plural correct', good and not bad_plural, ws[:2])
            except Exception as e:
                v.ok(f'class-wait-{size} walk', False, str(e)[:300])
            await br.close()
    print('TOTAL', len(v.R), 'PASS', sum(o for _, o in v.R), 'FAIL', sum(not o for _, o in v.R))

asyncio.run(main())
