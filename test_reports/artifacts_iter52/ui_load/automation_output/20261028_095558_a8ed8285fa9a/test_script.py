async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 390, "height": 844})
        print("Step 1: Open app URL")
        await page.goto("https://scale-engine-50k--0gu36hlx.preview.emergentagent.com", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)
        await page.screenshot(path="/app/test_reports/artifacts_iter52/ui_load/automation_output/20261028_095558_a8ed8285fa9a/jeelive-series-opacity390.jpeg", type="jpeg", quality=40, full_page=False)
        print("Step 1 PASS: App loaded at 390 viewport")

        print("Step 2: Switch to 320 width")
        await page.set_viewport_size({"width": 320, "height": 844})
        await page.wait_for_timeout(1200)
        await page.screenshot(path="/app/test_reports/artifacts_iter52/ui_load/automation_output/20261028_095558_a8ed8285fa9a/jeelive-series-opacity320.jpeg", type="jpeg", quality=40, full_page=False)
        print("Step 2 PASS: Screenshot captured at 320 viewport")

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
        await page.screenshot(path="/app/test_reports/artifacts_iter52/ui_load/automation_output/20261028_095558_a8ed8285fa9a/load_failure.jpeg", type="jpeg", quality=40, full_page=False)
