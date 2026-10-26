async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 375, "height": 667})
        print("Step 1: viewport set")
        await page.wait_for_timeout(1200)

        await page.wait_for_selector('[data-testid="home-screen"]', timeout=20000)
        print("Step 2: home screen loaded")

        await page.screenshot(path="/app/test_reports/artifacts_iter35/phase1_load/automation_output/20261026_170209_2a3147b1155d/home_loaded_375.jpeg", type="jpeg", quality=40, full_page=False)
        print("Step 3: screenshot captured")

        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

        print("Frontend quick load check passed")
    except Exception as e:
        print(f"Frontend quick load check failed: {str(e)}")
        await page.screenshot(path="/app/test_reports/artifacts_iter35/phase1_load/automation_output/20261026_170209_2a3147b1155d/home_load_error.jpeg", type="jpeg", quality=40, full_page=False)

