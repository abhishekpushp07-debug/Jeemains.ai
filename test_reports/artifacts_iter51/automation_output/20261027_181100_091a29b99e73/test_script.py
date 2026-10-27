async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 390, "height": 844})
        page.on("console", lambda msg: print(f"CONSOLE: {msg.type}: {msg.text}"))
        await page.wait_for_timeout(1000)

        await page.wait_for_selector('[data-testid="entry-title"]', timeout=15000)
        print("PASS: entry-title visible")

        await page.click('[data-testid="entry-privacy-link"]', force=True)
        await page.wait_for_selector('[data-testid="privacy-intro"]', timeout=15000)
        print("PASS: privacy screen loaded")

        await page.screenshot(path="/app/test_reports/artifacts_iter51/automation_output/20261027_181100_091a29b99e73/entry_privacy.jpeg", type="jpeg", quality=40, full_page=False)

        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

    except Exception as e:
        print(f"FAIL: public smoke failed: {str(e)}")
        await page.screenshot(path="/app/test_reports/artifacts_iter51/automation_output/20261027_181100_091a29b99e73/public_smoke_fail.jpeg", type="jpeg", quality=40, full_page=False)

