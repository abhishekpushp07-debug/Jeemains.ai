async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 375, "height": 667})
        print("Step 1: Mobile viewport set")

        await page.wait_for_timeout(800)
        await page.wait_for_load_state("domcontentloaded")
        print("Step 2: DOM content loaded")

        await page.screenshot(path="/app/test_reports/artifacts_iter54/ui_load/automation_output/20261028_124302_9ab03de6b576/iter54_frontend_load.jpeg", type="jpeg", quality=40, full_page=False)
        print("Step 3: Frontend load screenshot captured")

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

        print("Frontend quick load verification completed")
    except Exception as e:
        print(f"Frontend quick load verification failed: {str(e)}")
