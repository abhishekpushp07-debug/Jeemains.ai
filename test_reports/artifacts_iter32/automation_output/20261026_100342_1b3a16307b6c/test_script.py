async def run_test(page, output_dir, page_url):
    page.on("console", lambda msg: print(f"CONSOLE: {msg.type}: {msg.text}"))

    try:
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.wait_for_timeout(800)

        if await page.locator('[data-testid="entry-phone-input"]').count() > 0:
            await page.fill('[data-testid="entry-phone-input"]', '9000000001')
            await page.click('[data-testid="entry-continue-button"]', force=True)
            await page.wait_for_timeout(1800)

        await page.wait_for_selector('[data-testid="home-screen"]', timeout=12000)
        await page.click('[data-testid="home-rapid-fire-entry"]', force=True)
        await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=12000)
        print('Rapid Fire home loaded')

        await page.wait_for_selector('[data-testid="rf-exam-toggle"]', timeout=8000)
        await page.click('[data-testid="rf-exam-neet"]', force=True)
        await page.wait_for_timeout(1000)
        await page.click('[data-testid="rf-exam-jee"]', force=True)
        await page.wait_for_timeout(700)
        print('JEE/NEET toggle taps succeeded')

        await page.click('[data-testid="rf-pane-board"]', force=True)
        await page.wait_for_timeout(600)
        await page.click('[data-testid="rf-pane-recent"]', force=True)
        await page.wait_for_timeout(600)
        await page.click('[data-testid="rf-pane-trophies"]', force=True)
        await page.wait_for_timeout(600)
        print('Rapid Fire pane navigation succeeded')

        await page.screenshot(path='/app/test_reports/artifacts_iter32/automation_output/20261026_100342_1b3a16307b6c/rapid_smoke_390.jpeg', type="jpeg", quality=40, full_page=False)

        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

    except Exception as e:
        print(f"Rapid Fire smoke failed: {str(e)}")
        await page.screenshot(path='/app/test_reports/artifacts_iter32/automation_output/20261026_100342_1b3a16307b6c/rapid_smoke_error.jpeg', type="jpeg", quality=40, full_page=False)

