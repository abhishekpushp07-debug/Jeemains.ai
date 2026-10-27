async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 375, "height": 667})
        print("Step 1: Mobile viewport set")

        await page.wait_for_timeout(1000)
        await page.wait_for_selector('[data-testid="entry-screen"]', timeout=20000)
        print("Step 2: Entry screen loaded")

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

        await page.screenshot(path='/app/test_reports/artifacts_iter48/ui_load/automation_output/20261027_103435_1810fa55ae48/entry_mobile_375.jpeg', type="jpeg", quality=40, full_page=False)
        print("Step 3: Screenshot captured")
    except Exception as e:
        print(f"Test failed: {str(e)}")
        await page.screenshot(path='/app/test_reports/artifacts_iter48/ui_load/automation_output/20261027_103435_1810fa55ae48/entry_mobile_375_error.jpeg', type="jpeg", quality=40, full_page=False)

