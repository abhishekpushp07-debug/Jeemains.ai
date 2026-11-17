async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 390, "height": 844})
        print("Step 1: Viewport set to 390x844")

        await page.wait_for_load_state("domcontentloaded")
        await page.wait_for_timeout(4000)

        # Wait for either login or home
        for _ in range(30):
            has_entry = await page.locator('[data-testid="entry-phone-input"]').count() > 0
            has_home = await page.locator('[data-testid="home-tile-jee-main"]').count() > 0
            if has_entry or has_home:
                break
            await page.wait_for_timeout(1000)

        if await page.locator('[data-testid="entry-phone-input"]').count() > 0:
            print("Step 2: Entry form visible, logging in once")
            await page.fill('[data-testid="entry-phone-input"]', '7004186276')
            await page.fill('[data-testid="entry-pin-input"]', '5524')
            await page.click('[data-testid="entry-continue-button"]', force=True)
            await page.wait_for_timeout(6000)
        else:
            print("Step 2: Reused existing session")

        await page.wait_for_selector('[data-testid="home-tile-jee-main"]', timeout=30000)
        await page.screenshot(path='/app/test_reports/artifacts_iter48/ui_readonly/automation_output/20261027_103735_619caec402b9/home_390.jpeg', type="jpeg", quality=40, full_page=False)
        print("Step 3: Home loaded at 390")

        artwork_check = await page.evaluate("""() => {
          const imgs = Array.from(document.querySelectorAll('img')).map(i => i.src || '');
          const required = ['jee.jpg', 'bitsat.jpg', 'comedk.jpg', 'live.jpg'];
          const found = required.filter(x => imgs.some(src => src.includes(x)));
          return {found, total: imgs.length};
        }""")
        print(f"Step 4: Artwork files found: {artwork_check}")

        await page.set_viewport_size({"width": 320, "height": 667})
        await page.wait_for_timeout(1000)
        await page.screenshot(path='/app/test_reports/artifacts_iter48/ui_readonly/automation_output/20261027_103735_619caec402b9/home_320.jpeg', type="jpeg", quality=40, full_page=False)
        print("Step 5: Home loaded at 320")

        await page.goto('https://share-card-stats--1s9i9qdg.preview.emergentagent.com/performance')
        await page.wait_for_timeout(3000)
        perf_visible = await page.locator('[data-testid="loading-performance-screen"]').count() > 0
        print(f"Step 6: Performance screen visible: {perf_visible}")

        privacy_text = await page.locator('[data-testid="loading-performance-privacy"]').first.text_content() if perf_visible else ''
        print(f"Step 7: Performance privacy text present: {bool(privacy_text)}")

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

    except Exception as e:
        print(f"Test failed: {str(e)}")
        await page.screenshot(path='/app/test_reports/artifacts_iter48/ui_readonly/automation_output/20261027_103735_619caec402b9/ui_readonly_error.jpeg', type="jpeg", quality=40, full_page=False)

