async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.wait_for_timeout(700)
        if await page.locator('[data-testid="entry-phone-input"]').count() > 0:
            await page.fill('[data-testid="entry-phone-input"]', '9000000001')
            await page.click('[data-testid="entry-continue-button"]', force=True)
            await page.wait_for_timeout(1500)

        import json
        async def route_handler(route, request):
            url = request.url
            if '/api/jl/pyq/jee-main' in url and request.method == 'GET':
                bad = {"data": {"items": [{"id": "broken-1", "year": "2024", "exam_date": "bad-date", "shift": 1, "count": 90, "minutes": 180, "maximum": 300}], "years": [2024], "total": 1}, "error": None, "meta": {"api_version": "1"}}
                await route.fulfill(status=200, content_type='application/json', body=json.dumps(bad))
                return
            await route.continue_()

        await page.route('**/*', route_handler)
        await page.goto('https://jeelive-mobile.preview.emergentagent.com/pyq')
        await page.wait_for_selector('[data-testid="pyq-screen"]', timeout=12000)
        await page.wait_for_timeout(1200)

        err_count = await page.locator('[data-testid="pyq-load-error"]').count()
        empty_count = await page.locator('[data-testid="pyq-empty"]').count()
        print(f"invalid-schema -> error box count: {err_count}, empty count: {empty_count}")

        await page.screenshot(path='/app/test_reports/artifacts_iter32/automation_output/20261026_100317_2c2840548511/fixture_invalid_schema.jpeg', type="jpeg", quality=40, full_page=False)

        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

    except Exception as e:
        print(f"Invalid schema fixture failed: {str(e)}")
        await page.screenshot(path='/app/test_reports/artifacts_iter32/automation_output/20261026_100317_2c2840548511/fixture_invalid_error.jpeg', type="jpeg", quality=40, full_page=False)

