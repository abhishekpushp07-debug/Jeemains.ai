async def run_test(page, output_dir, page_url):
    # Enable console logs
    page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))

    try:
        await page.set_viewport_size({"width": 375, "height": 667})
        print("Step 1: Waiting for entry screen")
        await page.wait_for_selector('[data-testid="entry-screen"]', timeout=15000)
        print("Step 1 passed: Entry screen visible")

        # Track RF request counts for duplicate-call/coalescing visibility
        rf_counts = {"catalog": 0, "profile": 0, "history": 0, "shop": 0}
        def on_request(req):
            url = req.url
            if '/api/rf/catalog' in url:
                rf_counts['catalog'] += 1
            if '/api/rf/profile' in url:
                rf_counts['profile'] += 1
            if '/api/rf/duels?' in url:
                rf_counts['history'] += 1
            if '/api/rf/shop' in url and '/buy' not in url and '/equip' not in url:
                rf_counts['shop'] += 1
        page.on("request", on_request)

        print("Step 2: Attempting safe fixture login")
        await page.fill('[data-testid="entry-phone-input"]', '7000000000')
        await page.fill('[data-testid="entry-pin-input"]', '0000')
        await page.click('[data-testid="entry-continue-button"]', force=True)
        await page.wait_for_timeout(3000)

        home_visible = await page.is_visible('[data-testid="home-screen"]')
        if not home_visible:
            print("Fixture login did not reach home; checking error state")
            err_visible = await page.is_visible('[data-testid="entry-error"]')
            if err_visible:
                err_text = await page.locator('[data-testid="entry-error"]').inner_text()
                print(f"Entry error: {err_text}")
            else:
                print("No explicit entry-error element visible")
            raise Exception("Cannot continue RF smoke because login did not reach home")

        print("Step 2 passed: Home screen visible")

        print("Step 3: Open Rapid Fire from home")
        await page.click('[data-testid="home-rapid-fire-entry"]', force=True)
        await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=15000)
        await page.wait_for_timeout(2500)
        print("Step 3 passed: Rapid Fire home loaded")

        print("Step 4: Verify key RF interactions and read-only screens")
        await page.click('[data-testid="rf-subject-chemistry"]', force=True)
        await page.wait_for_timeout(400)
        await page.click('[data-testid="rf-solo-history"]', force=True)
        await page.wait_for_timeout(1500)
        await page.go_back()
        await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=10000)

        await page.click('[data-testid="rf-shop-shortcut"]', force=True)
        await page.wait_for_timeout(1500)
        await page.go_back()
        await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=10000)

        await page.click('[data-testid="rf-friends-history"]', force=True)
        await page.wait_for_timeout(1500)
        await page.go_back()
        await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=10000)
        print("Step 4 passed: Navigation taps work")

        print(f"RF request counts observed: {rf_counts}")

        await page.screenshot(path='/app/test_reports/artifacts_iter46_ui/automation_output/20261027_093340_221dacf62bef/rapid_home_after_login.jpeg', type="jpeg", quality=40, full_page=False)

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

        print("Frontend RF smoke completed successfully")
    except Exception as e:
        print(f"Frontend RF smoke failed: {str(e)}")
        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")
