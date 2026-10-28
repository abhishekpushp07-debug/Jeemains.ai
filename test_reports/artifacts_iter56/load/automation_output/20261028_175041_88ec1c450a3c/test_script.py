async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width":390,"height":844})
        await page.get_by_test_id('launch-download-page').wait_for(state='visible',timeout=15000)
        assert await page.get_by_test_id('download-mobile-zip').is_visible()
        assert await page.locator('script').count()==0
        print('PASS public standalone page loads without scripts')
        await page.screenshot(path='/app/test_reports/artifacts_iter56/load/automation_output/20261028_175041_88ec1c450a3c/downloads390.jpeg', type="jpeg", quality=40, full_page=False)
    except Exception as e:
        print('FAIL public page:',str(e))
    error_text = await page.evaluate("""() => { const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]')); return errorElements.map(el => el.textContent).join(", "); }""")
    print(f'Found error message: {error_text}' if error_text else 'No error messages found on the page')
