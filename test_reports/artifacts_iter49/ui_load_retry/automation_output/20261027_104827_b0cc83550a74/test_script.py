async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 375, "height": 667})
        print("Step 1: Mobile viewport set")
        await page.wait_for_timeout(1200)

        await page.wait_for_selector('[data-testid="entry-phone-input"]', timeout=25000)
        await page.wait_for_selector('[data-testid="entry-pin-input"]', timeout=10000)
        print("Step 2: Entry inputs visible")

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*=\"error\"], [id*=\"error\"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

        await page.screenshot(path='/app/test_reports/artifacts_iter49/ui_load_retry/automation_output/20261027_104827_b0cc83550a74/home_entry_375.jpeg', type="jpeg", quality=40, full_page=False)
        print("Step 3: Screenshot captured")
    except Exception as e:
        print(f"UI smoke failed: {str(e)}")
        await page.screenshot(path='/app/test_reports/artifacts_iter49/ui_load_retry/automation_output/20261027_104827_b0cc83550a74/home_entry_error_375.jpeg', type="jpeg", quality=40, full_page=False)

