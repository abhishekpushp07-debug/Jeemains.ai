async def run_test(page, output_dir, page_url):
    page.on("console", lambda msg: print(f"CONSOLE: {msg.type}: {msg.text}"))
    try:
        await page.set_viewport_size({"width": 375, "height": 667})
        await page.wait_for_timeout(1500)
        await page.screenshot(path="/app/test_reports/artifacts_iter32/automation_output/20261026_095843_328bccf83bbf/quick_load_mobile.jpeg", type="jpeg", quality=40, full_page=False)
        print("Quick load screenshot captured")
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")
    except Exception as e:
        print(f"Quick load failed: {str(e)}")
