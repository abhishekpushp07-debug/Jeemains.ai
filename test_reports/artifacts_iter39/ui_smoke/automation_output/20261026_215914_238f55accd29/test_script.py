async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 375, "height": 667})
        page.on("console", lambda msg: print(f"CONSOLE: {msg.type}: {msg.text}"))
        await page.wait_for_timeout(800)
        await page.wait_for_selector('[data-testid="entry-screen"]', timeout=15000)
        print("Step success: Entry screen loaded")
        await page.screenshot(path="/app/test_reports/artifacts_iter39/ui_smoke/automation_output/20261026_215914_238f55accd29/entry_mobile_375.jpeg", type="jpeg", quality=40, full_page=False)
        print("Step success: Screenshot captured")
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*=\"error\"], [id*=\"error\"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")
    except Exception as e:
        print(f"Step failed: {str(e)}")
        await page.screenshot(path="/app/test_reports/artifacts_iter39/ui_smoke/automation_output/20261026_215914_238f55accd29/entry_mobile_375_error.jpeg", type="jpeg", quality=40, full_page=False)

