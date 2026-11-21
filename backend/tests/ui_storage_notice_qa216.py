"""TEST-ONLY qa216: upload dialog storage notice per mode (master bridge :8770, faked health)."""
import asyncio
NS = {}
exec(open('/app/backend/tests/ui_storage_badge_qa216.py').read().split('async def badge_mode')[0], NS)  # shared setup of the badge test
async_playwright, setup, FAKE, BASE, ok, SS, R = (NS[k] for k in ('async_playwright', 'setup', 'FAKE', 'BASE', 'ok', 'SS', 'R'))


async def m():
    async with async_playwright() as pw:
        br, page, errs = await setup(pw, 1920, 800)
        try:
            FAKE['mode'] = None
            await page.goto(BASE + '/super-admin', wait_until='domcontentloaded')
            await page.click('[data-testid="master-exam-jee-main"]'); await page.wait_for_timeout(2500)
            ids = await page.evaluate("Array.from(document.querySelectorAll('[data-testid]')).map(e=>e.dataset.testid).filter(t=>/type|mock/.test(t)).slice(0,40)")
            print('exam page ids', ids, page.url)
            card = page.locator('[data-testid="master-type-open-mocks"]')
            await card.click(); await page.wait_for_timeout(2500); type_url = page.url; print('type url', type_url)
            for mode, want in ((None, 'Emergent'), ('supabase', None), ('slow', None), ('emergent', 'Emergent'), ('down', 'Thodi der baad upload')):
                FAKE['mode'] = mode
                await page.goto(type_url, wait_until='domcontentloaded')
                await page.wait_for_selector('[data-testid="type-upload-pdf"]', timeout=20000)
                await page.click('[data-testid="type-upload-pdf"]'); await page.wait_for_selector('[data-testid="upload-dialog"]'); await page.wait_for_timeout(1500)
                n = await page.locator('[data-testid="upload-storage-notice"]').count()
                txt = await page.inner_text('[data-testid="upload-storage-notice"]') if n else ''
                print(f'mode={mode} notice={n} text={txt!r}')
                ok(f'notice [{mode}] ' + ('present w/ ' + want if want else 'shown (brief: green "upload aaram se")'), (want in txt) if want else n == 1, (n, txt))
                if mode == 'down': await page.screenshot(path=SS + '_upload_down.jpg', quality=40)
                await page.keyboard.press('Escape'); await page.wait_for_timeout(300)
            ok('no page errors', not errs, errs)
        finally:
            await br.close()
    print(f'TOTAL {len(R)} PASS {sum(1 for r in R if r[1])} FAIL {sum(1 for r in R if not r[1])}')


asyncio.run(m())
