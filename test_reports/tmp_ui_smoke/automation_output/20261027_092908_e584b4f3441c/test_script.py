async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.wait_for_timeout(2000)
        await page.screenshot(path="/app/test_reports/tmp_ui_smoke/automation_output/20261027_092908_e584b4f3441c/initial_load.jpeg", type="jpeg", quality=40, full_page=False)
        print("Initial frontend load screenshot captured")
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*=\"error\"], [id*=\"error\"]'));
        return errorElements.map(el => el.textContent).join(', ');
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")
    except Exception as e:
        print(f"Frontend load check failed: {str(e)}")
