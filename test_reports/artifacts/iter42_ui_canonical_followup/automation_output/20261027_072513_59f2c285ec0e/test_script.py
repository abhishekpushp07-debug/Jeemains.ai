async def run_test(page, output_dir, page_url):
    try:
        import re
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.goto('https://rapid-fire-208--04cp9c5d.preview.emergentagent.com', wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(1200)

        if await page.locator('[data-testid="entry-screen"]').is_visible():
            env_text = open('/app/backend/.env', 'r', encoding='utf-8').read()
            phone = re.search(r'JEELIVE_TEST_PHONE="?([0-9]+)"?', env_text).group(1)
            pin = re.search(r'JEELIVE_TEST_PIN="?([0-9]+)"?', env_text).group(1)
            await page.fill('[data-testid="entry-phone-input"]', phone)
            await page.fill('[data-testid="entry-pin-input"]', pin)
            await page.click('[data-testid="entry-continue-button"]', force=True)

        await page.wait_for_selector('[data-testid="tab-rapid"]', timeout=30000)
        await page.click('[data-testid="tab-rapid"]', force=True)
        await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=20000)
        await page.wait_for_selector('[data-testid="rf-play-now"]', timeout=20000)
        await page.wait_for_selector('[data-testid="game-hud-coins"]', timeout=20000)
        coins = await page.locator('[data-testid="game-hud-coins"]').inner_text()
        print(f'Visible coins on lobby: {coins}')

        assets = await page.evaluate("""async () => {
          const names = ['spark','friends','coins','trophy'];
          const out = [];
          for (const n of names) {
            const r = await fetch(`/api/brand/rapid/${n}.webp`, { cache: 'no-store' });
            const b = await r.blob();
            out.push({n, ok: r.ok, bytes: b.size});
          }
          return out;
        }""")
        print(f'Rapid asset checks: {assets}')

        await page.click('[data-testid="rf-friends-history"]', force=True)
        await page.wait_for_selector('[data-testid="rf-history-screen"]', timeout=15000)
        await page.screenshot(path='/app/test_reports/artifacts/iter42_ui_canonical_followup/automation_output/20261027_072513_59f2c285ec0e/friends_history_390.jpeg', type="jpeg", quality=40, full_page=False)
        await page.click('[data-testid="rf-history-back"]', force=True)
        await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=15000)
        await page.click('[data-testid="rf-shop-shortcut"]', force=True)
        await page.wait_for_selector('[data-testid="shop-screen"]', timeout=15000)
        await page.screenshot(path='/app/test_reports/artifacts/iter42_ui_canonical_followup/automation_output/20261027_072513_59f2c285ec0e/shop_390.jpeg', type="jpeg", quality=40, full_page=False)

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(', ');
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

        print('Canonical follow-up checks completed')
    except Exception as e:
        print(f'Canonical follow-up failed: {str(e)}')
        await page.screenshot(path='/app/test_reports/artifacts/iter42_ui_canonical_followup/automation_output/20261027_072513_59f2c285ec0e/canonical_followup_error.jpeg', type="jpeg", quality=40, full_page=False)

