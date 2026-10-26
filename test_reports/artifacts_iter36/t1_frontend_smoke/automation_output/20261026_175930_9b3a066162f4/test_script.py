async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 375, "height": 667})
        print("STEP 1: viewport set")

        await page.wait_for_timeout(1200)
        await page.wait_for_selector('[data-testid="brand-mark"]', timeout=20000)
        print("STEP 2: home loaded with brand mark")

        await page.screenshot(path="/app/test_reports/artifacts_iter36/t1_frontend_smoke/automation_output/20261026_175930_9b3a066162f4/home_mobile_375.jpeg", type="jpeg", quality=40, full_page=False)
        print("STEP 3: screenshot captured")

        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

        tile_count = await page.locator('[data-testid^="home-tile-"]').count()
        print(f"STEP 4: detected home tiles: {tile_count}")
    except Exception as e:
        print(f"TEST FAILED: {str(e)}")
        await page.screenshot(path="/app/test_reports/artifacts_iter36/t1_frontend_smoke/automation_output/20261026_175930_9b3a066162f4/home_mobile_375_error.jpeg", type="jpeg", quality=40, full_page=False)

