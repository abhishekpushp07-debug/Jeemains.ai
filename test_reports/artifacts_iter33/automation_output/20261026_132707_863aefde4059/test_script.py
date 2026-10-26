async def run_test(page, output_dir, page_url):
    page.on("console", lambda msg: print(f"CONSOLE: {msg.type}: {msg.text}"))

    try:
        await page.set_viewport_size({"width": 390, "height": 844})
        print("Step 1: Opened app at 390x844")
        await page.wait_for_timeout(1200)

        await page.wait_for_selector('[data-testid="entry-phone-input"]', timeout=15000)
        print("Step 2: Entry screen loaded")

        await page.fill('[data-testid="entry-phone-input"]', '9000000001')
        await page.click('[data-testid="entry-continue-button"]', force=True)
        await page.wait_for_timeout(2500)
        print("Step 3: Login attempted")

        await page.wait_for_selector('[data-testid="home-tile-jee-main"]', timeout=15000)
        print("Step 4: Home loaded with JEE tile")

        await page.click('[data-testid="home-tile-jee-main"]', force=True)
        await page.wait_for_selector('[data-testid="exam-hub-jee-main"]', timeout=15000)
        print("Step 5: JEE hub opened")

        await page.click('[data-testid="exam-destination-pyq"]', force=True)
        await page.wait_for_selector('[data-testid="pyq-screen"]', timeout=15000)
        await page.wait_for_timeout(1800)
        print("Step 6: PYQ screen opened")

        total_text = await page.locator('[data-testid="pyq-total"]').first.text_content()
        print(f"Step 7: PYQ total text => {total_text}")

        empty_visible = await page.locator('[data-testid="pyq-empty"]').first.is_visible()
        print(f"Step 8: Empty state visible => {empty_visible}")

        if empty_visible:
            body_text = await page.locator('[data-testid="pyq-empty"]').first.text_content()
            print(f"Step 9: Empty state text => {body_text}")

        await page.screenshot(path='/app/test_reports/artifacts_iter33/automation_output/20261026_132707_863aefde4059/pyq_live_390.jpeg', type="jpeg", quality=40, full_page=False)
        print("Step 10: Captured 390 screenshot")

        await page.set_viewport_size({"width": 320, "height": 667})
        await page.wait_for_timeout(800)
        await page.wait_for_selector('[data-testid="pyq-screen"]', timeout=10000)
        await page.screenshot(path='/app/test_reports/artifacts_iter33/automation_output/20261026_132707_863aefde4059/pyq_live_320.jpeg', type="jpeg", quality=40, full_page=False)
        print("Step 11: Captured 320 screenshot")

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

        print("UI test completed successfully")

    except Exception as e:
        print(f"UI test failed: {str(e)}")
        await page.screenshot(path='/app/test_reports/artifacts_iter33/automation_output/20261026_132707_863aefde4059/pyq_live_error.jpeg', type="jpeg", quality=40, full_page=False)

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")
