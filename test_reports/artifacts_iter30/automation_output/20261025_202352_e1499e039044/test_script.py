async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.wait_for_timeout(1500)
        await page.wait_for_selector('[data-testid="login-phone-input"]', timeout=20000)
        print('Login screen loaded')
        await page.screenshot(path='/app/test_reports/artifacts_iter30/automation_output/20261025_202352_e1499e039044/frontend_load_mobile.jpeg', type="jpeg", quality=40, full_page=False)

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(', ');
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print('No error messages found on the page')

        print('Phase 1 frontend load check passed')
    except Exception as e:
        print(f'Phase 1 frontend load check failed: {str(e)}')
        await page.screenshot(path='/app/test_reports/artifacts_iter30/automation_output/20261025_202352_e1499e039044/frontend_load_error.jpeg', type="jpeg", quality=40, full_page=False)

