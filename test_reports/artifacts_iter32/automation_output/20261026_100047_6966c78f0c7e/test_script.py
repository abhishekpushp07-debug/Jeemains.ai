async def run_test(page, output_dir, page_url):
    page.on("console", lambda msg: print(f"CONSOLE: {msg.type}: {msg.text}"))

    try:
        await page.set_viewport_size({"width": 320, "height": 844})
        print("Step 1: Open app at 320 width")
        await page.wait_for_timeout(1200)

        if await page.locator('[data-testid="entry-phone-input"]').count() > 0:
            await page.fill('[data-testid="entry-phone-input"]', '9000000001')
            await page.click('[data-testid="entry-continue-button"]', force=True)
            await page.wait_for_timeout(1800)

        await page.wait_for_selector('[data-testid="home-screen"]', timeout=12000)

        # measure key touch targets
        ids = ['home-tile-jee-main', 'home-account-button', 'home-rapid-fire-entry']
        for tid in ids:
            box = await page.locator(f'[data-testid="{tid}"]').first.bounding_box()
            print(f"Touch target {tid}: {box['width']}x{box['height']}")

        await page.click('[data-testid="home-tile-jee-main"]', force=True)
        await page.wait_for_selector('[data-testid="exam-hub-jee-main"]', timeout=10000)

        pyq_box = await page.locator('[data-testid="exam-destination-pyq"]').bounding_box()
        print(f"Touch target exam-destination-pyq: {pyq_box['width']}x{pyq_box['height']}")

        await page.click('[data-testid="exam-destination-pyq"]', force=True)
        await page.wait_for_selector('[data-testid="pyq-screen"]', timeout=10000)

        if await page.locator('[data-testid="pyq-empty-refresh"]').count() > 0:
            refresh_box = await page.locator('[data-testid="pyq-empty-refresh"]').bounding_box()
            print(f"Touch target pyq-empty-refresh: {refresh_box['width']}x{refresh_box['height']}")

        overflow = await page.evaluate("""() => ({
          doc: document.documentElement.scrollWidth,
          body: document.body.scrollWidth,
          inner: window.innerWidth,
          overflow_doc: document.documentElement.scrollWidth > window.innerWidth + 1,
          overflow_body: document.body.scrollWidth > window.innerWidth + 1
        })""")
        print(f"320 overflow check: {overflow}")

        await page.screenshot(path='/app/test_reports/artifacts_iter32/automation_output/20261026_100047_6966c78f0c7e/pyq_320.jpeg', type="jpeg", quality=40, full_page=False)

        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

        print("320px flow test completed")

    except Exception as e:
        print(f"320px flow test failed: {str(e)}")
        await page.screenshot(path='/app/test_reports/artifacts_iter32/automation_output/20261026_100047_6966c78f0c7e/flow_320_error.jpeg', type="jpeg", quality=40, full_page=False)

