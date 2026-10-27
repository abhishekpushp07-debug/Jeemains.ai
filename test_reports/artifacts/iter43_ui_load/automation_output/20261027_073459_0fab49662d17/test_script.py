async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.wait_for_timeout(1000)
        await page.wait_for_selector('[data-testid="entry-phone-input"]', timeout=30000)
        print('Entry screen loaded')
        await page.screenshot(path='/app/test_reports/artifacts/iter43_ui_load/automation_output/20261027_073459_0fab49662d17/entry_loaded_390.jpeg', type="jpeg", quality=40, full_page=False)

        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(', ');
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

    except Exception as e:
        print(f'Frontend load check failed: {str(e)}')

