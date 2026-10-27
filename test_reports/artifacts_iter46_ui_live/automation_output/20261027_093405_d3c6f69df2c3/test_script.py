async def run_test(page, output_dir, page_url):
    page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))

    try:
        await page.set_viewport_size({"width": 375, "height": 667})
        print("Step 1: wait for login form")
        await page.wait_for_selector('[data-testid="entry-phone-input"]', timeout=15000)
        await page.wait_for_selector('[data-testid="entry-pin-input"]', timeout=15000)

        print("Step 2: canonical sign-in once")
        await page.fill('[data-testid="entry-phone-input"]', '7004186276')
        await page.fill('[data-testid="entry-pin-input"]', '5524')
        await page.click('[data-testid="entry-continue-button"]', force=True)
        await page.wait_for_timeout(5000)

        if await page.is_visible('[data-testid="entry-error"]'):
            err_text = await page.locator('[data-testid="entry-error"]').inner_text()
            raise Exception(f"Login failed: {err_text}")

        await page.wait_for_selector('[data-testid="home-screen"]', timeout=20000)
        print("Step 2 passed: home visible")

        rf_counts = {"catalog": 0, "profile": 0, "history": 0, "shop": 0}
        def on_request(req):
            u = req.url
            if '/api/rf/catalog' in u:
                rf_counts['catalog'] += 1
            if '/api/rf/profile' in u:
                rf_counts['profile'] += 1
            if '/api/rf/duels?' in u:
                rf_counts['history'] += 1
            if '/api/rf/shop' in u and '/buy' not in u and '/equip' not in u:
                rf_counts['shop'] += 1
        page.on('request', on_request)

        print("Step 3: open rapid and read-only tabs")
        await page.click('[data-testid="home-rapid-fire-entry"]', force=True)
        await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=15000)
        await page.wait_for_timeout(2500)

        await page.click('[data-testid="rf-friends-history"]', force=True)
        await page.wait_for_timeout(1500)
        await page.go_back()
        await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=10000)

        await page.click('[data-testid="rf-shop-shortcut"]', force=True)
        await page.wait_for_timeout(1500)
        await page.go_back()
        await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=10000)

        await page.click('[data-testid="rf-subject-physics"]', force=True)
        await page.wait_for_timeout(400)

        print(f"RF request counts observed: {rf_counts}")
        await page.screenshot(path='/app/test_reports/artifacts_iter46_ui_live/automation_output/20261027_093405_d3c6f69df2c3/rapid_readonly_smoke.jpeg', type="jpeg", quality=40, full_page=False)

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

        print("Frontend canonical read-only smoke completed")
    except Exception as e:
        print(f"Frontend canonical smoke failed: {str(e)}")
        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")
