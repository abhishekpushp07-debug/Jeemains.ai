async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 375, "height": 667})
        print("Step 1: Opened /catalogue")
        await page.wait_for_timeout(2500)

        body_text = await page.locator('body').inner_text()
        has_runtime = ('Code: catalogue.tsx' in body_text) or ('Cannot read properties of undefined' in body_text)
        print(f"Step 2: runtime overlay detected = {has_runtime}")

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
          print(f"Found error message: {error_text}")
        else:
          print("No error messages found on the page")

        await page.screenshot(path="/app/test_reports/artifacts_iter40/ui_catalogue_probe/automation_output/20261026_224507_9cce5693b533/catalogue_probe.jpeg", type="jpeg", quality=40, full_page=False)
        print("Step 3: Captured /catalogue screenshot")
    except Exception as e:
        print(f"Catalogue probe failed: {str(e)}")
        await page.screenshot(path="/app/test_reports/artifacts_iter40/ui_catalogue_probe/automation_output/20261026_224507_9cce5693b533/catalogue_probe_error.jpeg", type="jpeg", quality=40, full_page=False)

