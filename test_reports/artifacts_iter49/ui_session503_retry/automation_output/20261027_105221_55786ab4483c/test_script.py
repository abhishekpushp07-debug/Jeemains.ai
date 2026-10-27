async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 375, "height": 667})
        print("Step 1: Viewport set")

        async def handle_route(route):
            url = route.request.url
            if '/api/jl/auth/session' in url:
                await route.fulfill(status=503, content_type='application/json', body='{"detail":"forced test 503"}')
            else:
                await route.continue_()

        await page.route('**/*', handle_route)
        await page.wait_for_timeout(200)
        await page.reload(wait_until='domcontentloaded')
        await page.wait_for_timeout(1400)

        await page.wait_for_selector('[data-testid="entry-phone-input"]', timeout=20000)
        await page.wait_for_selector('[data-testid="entry-pin-input"]', timeout=10000)
        print("Step 2: Entry form rendered")

        await page.fill('[data-testid="entry-phone-input"]', '7000000000')
        await page.fill('[data-testid="entry-pin-input"]', '0000')
        print("Step 3: Form editable under forced 503")

        retry_button = page.get_by_text('Retry', exact=True)
        if await retry_button.first.is_visible():
            await retry_button.first.click(force=True)
            await page.wait_for_timeout(500)
            print("Step 4: Retry clickable")
        else:
            print("Step 4: Retry text not visible")

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*=\"error\"], [id*=\"error\"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

        await page.screenshot(path='/app/test_reports/artifacts_iter49/ui_session503_retry/automation_output/20261027_105221_55786ab4483c/session_503_recovery.jpeg', type="jpeg", quality=40, full_page=False)
    except Exception as e:
        print(f"503 recovery test failed: {str(e)}")
        await page.screenshot(path='/app/test_reports/artifacts_iter49/ui_session503_retry/automation_output/20261027_105221_55786ab4483c/session_503_recovery_error.jpeg', type="jpeg", quality=40, full_page=False)

