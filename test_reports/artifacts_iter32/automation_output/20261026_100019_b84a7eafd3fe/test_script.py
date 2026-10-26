async def run_test(page, output_dir, page_url):
    page.on("console", lambda msg: print(f"CONSOLE: {msg.type}: {msg.text}"))

    try:
        await page.set_viewport_size({"width": 390, "height": 844})
        print("Step 1: Open app")
        await page.wait_for_timeout(1200)

        entry_visible = await page.locator('[data-testid="entry-phone-input"]').count() > 0
        if entry_visible:
            print("Step 2: Logging in with pilot phone")
            await page.fill('[data-testid="entry-phone-input"]', '9000000001')
            await page.click('[data-testid="entry-continue-button"]', force=True)
            await page.wait_for_timeout(2000)

        await page.wait_for_selector('[data-testid="home-screen"]', timeout=15000)
        print("Home screen loaded")

        # Touch target checks on home tiles
        tile_box = await page.locator('[data-testid="home-tile-jee-main"]').bounding_box()
        print(f"home-tile-jee-main size: {tile_box['width']}x{tile_box['height']}")

        await page.click('[data-testid="home-tile-jee-main"]', force=True)
        await page.wait_for_selector('[data-testid="exam-hub-jee-main"]', timeout=10000)
        print("Reached JEE Main hub")

        await page.wait_for_timeout(700)
        await page.screenshot(path='/app/test_reports/artifacts_iter32/automation_output/20261026_100019_b84a7eafd3fe/hub_390.jpeg', type="jpeg", quality=40, full_page=False)

        pyq_count = await page.locator('[data-testid="exam-destination-pyq"]').count()
        mocks_count = await page.locator('[data-testid="exam-destination-mocks"]').count()
        print(f"JEE hub destinations => pyq:{pyq_count}, mocks:{mocks_count}")

        await page.click('[data-testid="exam-destination-pyq"]', force=True)
        await page.wait_for_selector('[data-testid="pyq-screen"]', timeout=10000)
        print("Reached PYQ screen")

        await page.wait_for_timeout(1200)
        total_text = await page.locator('[data-testid="pyq-total"]').first.text_content()
        print(f"PYQ total label: {total_text}")

        empty_count = await page.locator('[data-testid="pyq-empty"]').count()
        list_count = await page.locator('[data-testid="pyq-paper-list"]').count()
        print(f"PYQ empty:{empty_count}, list_present:{list_count}")

        if empty_count:
            await page.click('[data-testid="pyq-empty-refresh"]', force=True)
            await page.wait_for_timeout(1500)
            print("Clicked PYQ refresh on empty state")

        await page.screenshot(path='/app/test_reports/artifacts_iter32/automation_output/20261026_100019_b84a7eafd3fe/pyq_390.jpeg', type="jpeg", quality=40, full_page=False)

        # Redirect checks
        print("Checking /catalogue redirect for jee-main mocks")
        await page.goto('https://jeelive-mobile.preview.emergentagent.com/catalogue?slug=jee-main&kind=mocks')
        await page.wait_for_timeout(1200)
        await page.wait_for_selector('[data-testid="pyq-screen"]', timeout=10000)
        print("mocks redirect landed on PYQ")

        print("Checking /catalogue redirect for jee-main pyq")
        await page.goto('https://jeelive-mobile.preview.emergentagent.com/catalogue?slug=jee-main&kind=pyq')
        await page.wait_for_timeout(1200)
        await page.wait_for_selector('[data-testid="pyq-screen"]', timeout=10000)
        print("pyq redirect landed on PYQ")

        print("Checking chapters route remains catalogue")
        await page.goto('https://jeelive-mobile.preview.emergentagent.com/catalogue?slug=jee-main&kind=chapters')
        await page.wait_for_timeout(1500)
        await page.wait_for_selector('[data-testid="catalogue-jee-main-chapters"]', timeout=10000)
        print("Chapters route unaffected")

        # BITSAT retains mocks
        await page.goto('https://jeelive-mobile.preview.emergentagent.com/(tabs)')
        await page.wait_for_selector('[data-testid="home-screen"]', timeout=10000)
        await page.click('[data-testid="home-tile-bitsat"]', force=True)
        await page.wait_for_selector('[data-testid="exam-hub-bitsat"]', timeout=10000)
        bitsat_mocks = await page.locator('[data-testid="exam-destination-mocks"]').count()
        print(f"BITSAT mocks destination count: {bitsat_mocks}")

        # Horizontal clipping check on current viewport
        overflow = await page.evaluate("""() => ({
          bodyScrollWidth: document.body.scrollWidth,
          innerWidth: window.innerWidth,
          hasOverflow: document.body.scrollWidth > window.innerWidth + 1
        })""")
        print(f"Overflow check: {overflow}")

        # Error scan
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

        print("390px flow test completed")

    except Exception as e:
        print(f"390px flow test failed: {str(e)}")
        await page.screenshot(path='/app/test_reports/artifacts_iter32/automation_output/20261026_100019_b84a7eafd3fe/flow_390_error.jpeg', type="jpeg", quality=40, full_page=False)

