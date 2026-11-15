async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 390, "height": 844})
        print("Step 1: Open entry screen")
        await page.goto("https://jeelive-unified--01f8rch2.preview.emergentagent.com/entry", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_selector('[data-testid="entry-screen"]', timeout=10000)
        print("Step 1 PASS: Entry screen loaded")

        print("Step 2: Perform one approved sign-in attempt")
        await page.fill('[data-testid="entry-phone-input"]', "7004186276")
        await page.fill('[data-testid="entry-pin-input"]', "5524")
        await page.click('[data-testid="entry-continue-button"]', force=True)
        await page.wait_for_timeout(3500)

        if await page.locator('[data-testid="home-screen"]').count() == 0:
            err = await page.locator('[data-testid="entry-error"]').first.text_content()
            print(f"Step 2 FAIL: Login did not reach home. entry-error={err}")
            await page.screenshot(path="/app/test_reports/artifacts_iter52/ui_series/automation_output/20261028_095923_41711e1a932f/login_failure.jpeg", type="jpeg", quality=40, full_page=False)
            raise Exception("Login failed; stopping as instructed (no retries)")
        print("Step 2 PASS: Reached home screen")

        print("Step 3: Verify all-india banner and gradient stop attributes")
        await page.wait_for_selector('[data-testid="all-india-series-banner"]', timeout=10000)
        stop_data = await page.evaluate("""() => {
          const banner = document.querySelector('[data-testid="all-india-series-banner"]');
          if (!banner) return { count: 0, opacities: [], colors: [] };
          const stops = Array.from(banner.querySelectorAll('stop'));
          return {
            count: stops.length,
            opacities: stops.map(s => s.getAttribute('stop-opacity')).filter(v => v !== null),
            colors: stops.map(s => s.getAttribute('stop-color')).filter(v => v !== null)
          };
        }""")
        print(f"Banner stop count={stop_data['count']}")
        print(f"Banner sample stop opacities={stop_data['opacities'][:12]}")
        print(f"Banner sample stop colors={stop_data['colors'][:12]}")

        print("Step 4: Toggle Pause shine -> Play shine")
        label_before = await page.locator('[data-testid="home-series-shine-label"]').first.text_content()
        await page.click('[data-testid="home-series-shine-toggle"]', force=True)
        await page.wait_for_timeout(300)
        label_after = await page.locator('[data-testid="home-series-shine-label"]').first.text_content()
        await page.click('[data-testid="home-series-shine-toggle"]', force=True)
        await page.wait_for_timeout(300)
        label_restore = await page.locator('[data-testid="home-series-shine-label"]').first.text_content()
        print(f"Shine labels: before={label_before}, afterToggle={label_after}, restored={label_restore}")

        print("Step 5: Open and close series explainer modal")
        await page.click('[data-testid="series-explainer-button"]', force=True)
        await page.wait_for_selector('[data-testid="series-explainer"]', timeout=10000)
        await page.click('[data-testid="series-explainer-close"]', force=True)
        await page.wait_for_timeout(500)
        print("Step 5 PASS: Explainer opened and closed")

        print("Step 6: Capture 390 screenshot")
        await page.screenshot(path="/app/test_reports/artifacts_iter52/ui_series/automation_output/20261028_095923_41711e1a932f/jeelive-series-opacity390.jpeg", type="jpeg", quality=40, full_page=False)

        print("Step 7: Capture 320 screenshot")
        await page.set_viewport_size({"width": 320, "height": 844})
        await page.wait_for_timeout(1200)
        await page.screenshot(path="/app/test_reports/artifacts_iter52/ui_series/automation_output/20261028_095923_41711e1a932f/jeelive-series-opacity320.jpeg", type="jpeg", quality=40, full_page=False)

        print("Step 8: Open hub and verify /live route")
        await page.click('[data-testid="series-open-hub-button"]', force=True)
        await page.wait_for_timeout(1500)
        current_url = page.url
        print(f"Current URL after open hub={current_url}")

        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*=\"error\"], [id*=\"error\"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

    except Exception as e:
        print(f"Test failed: {str(e)}")
        await page.screenshot(path="/app/test_reports/artifacts_iter52/ui_series/automation_output/20261028_095923_41711e1a932f/ui_failure.jpeg", type="jpeg", quality=40, full_page=False)
