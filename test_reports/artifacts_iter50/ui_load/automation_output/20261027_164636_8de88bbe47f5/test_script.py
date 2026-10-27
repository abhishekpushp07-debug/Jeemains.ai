async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 375, "height": 667})
        page.on("console", lambda msg: print(f"CONSOLE: {msg.type}: {msg.text}"))
        await page.wait_for_timeout(500)
        await page.wait_for_selector('[data-testid="entry-screen"]', timeout=20000)
        print("PASS: Entry screen loaded")
        await page.screenshot(path="/app/test_reports/artifacts_iter50/ui_load/automation_output/20261027_164636_8de88bbe47f5/entry_load_375.jpeg", type="jpeg", quality=40, full_page=False)
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")
    except Exception as e:
        print(f"FAIL: Load smoke failed: {str(e)}")
        await page.screenshot(path="/app/test_reports/artifacts_iter50/ui_load/automation_output/20261027_164636_8de88bbe47f5/entry_load_error.jpeg", type="jpeg", quality=40, full_page=False)

