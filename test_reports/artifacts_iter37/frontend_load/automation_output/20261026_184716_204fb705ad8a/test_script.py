async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 375, "height": 667})
        print("Step 1: viewport set")

        await page.wait_for_timeout(1200)
        await page.wait_for_load_state("domcontentloaded")
        print("Step 2: page dom loaded")

        await page.wait_for_timeout(2500)

        title = await page.title()
        print(f"Step 3: page title -> {title}")

        body_visible = await page.locator("body").is_visible()
        print(f"Step 4: body visible -> {body_visible}")

        await page.screenshot(path="/app/test_reports/artifacts_iter37/frontend_load/automation_output/20261026_184716_204fb705ad8a/mobile_load.jpeg", type="jpeg", quality=40, full_page=False)
        print("Step 5: screenshot captured")

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

        print("Frontend load smoke PASS")
    except Exception as e:
        print(f"Frontend load smoke FAIL: {str(e)}")
        await page.screenshot(path="/app/test_reports/artifacts_iter37/frontend_load/automation_output/20261026_184716_204fb705ad8a/mobile_load_error.jpeg", type="jpeg", quality=40, full_page=False)
