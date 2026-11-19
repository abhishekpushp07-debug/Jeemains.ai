async def run_test(page, output_dir, page_url):
    try:
        import re
        await page.set_viewport_size({"width": 360, "height": 800})
        await page.goto('https://handoff-zip-hub--8kn8pvyh.preview.emergentagent.com', wait_until='domcontentloaded', timeout=60000)
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

        overflow = await page.evaluate("""() => {
          const w = document.documentElement.scrollWidth;
          const iw = window.innerWidth;
          return {scrollWidth: w, innerWidth: iw, overflow: w > iw + 2};
        }""")
        print(f'Overflow check rapid home: {overflow}')

        await page.click('[data-testid="rf-friends-history"]', force=True)
        await page.wait_for_selector('[data-testid="rf-history-screen"]', timeout=15000)
        overflow2 = await page.evaluate("""() => {
          const w = document.documentElement.scrollWidth;
          const iw = window.innerWidth;
          return {scrollWidth: w, innerWidth: iw, overflow: w > iw + 2};
        }""")
        print(f'Overflow check history: {overflow2}')
        await page.screenshot(path='/app/test_reports/artifacts/iter42_ui_360/automation_output/20261027_072533_a9256f88f35e/rapid_history_360.jpeg', type="jpeg", quality=40, full_page=False)

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(', ');
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

        print('360x800 layout check completed')
    except Exception as e:
        print(f'360 layout check failed: {str(e)}')
        await page.screenshot(path='/app/test_reports/artifacts/iter42_ui_360/automation_output/20261027_072533_a9256f88f35e/layout_360_error.jpeg', type="jpeg", quality=40, full_page=False)

