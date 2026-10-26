async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.wait_for_timeout(1200)
        await page.wait_for_selector('[data-testid="entry-screen"]', timeout=15000)
        print('PASS: Entry screen loaded')
        await page.screenshot(path='/app/test_reports/artifacts_iter38/load_smoke/automation_output/20261026_213106_6c52e426a09d/entry-load.jpeg', type="jpeg", quality=40, full_page=False)
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(', ');
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print('No error messages found on the page')
    except Exception as e:
        print(f'FAIL: load smoke {str(e)}')
        await page.screenshot(path='/app/test_reports/artifacts_iter38/load_smoke/automation_output/20261026_213106_6c52e426a09d/entry-load-fail.jpeg', type="jpeg", quality=40, full_page=False)
