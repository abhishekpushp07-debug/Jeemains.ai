async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 375, "height": 667})
        print("Step 1: viewport set")
        await page.wait_for_load_state("domcontentloaded")
        await page.wait_for_timeout(2500)

        login_visible = await page.get_by_text("Phone number", exact=True).is_visible()
        if login_visible:
            print("Auth gate visible: cannot validate authenticated Rapid UI live.")
            await page.screenshot(path="/app/test_reports/artifacts_iter37/ui_isolated/automation_output/20261026_185017_fa36e9132b4c/rapid_auth_gate.jpeg", type="jpeg", quality=40, full_page=False)
        else:
            jee_label = await page.locator('[data-testid="rf-exam-label"]').is_visible()
            neet_toggle_count = await page.locator('[data-testid="rf-exam-neet"]').count()
            biology_shortcut = await page.locator('text=Biology').count()
            print(f"JEE label visible: {jee_label}")
            print(f"NEET selector count: {neet_toggle_count}")
            print(f"Biology visible text count: {biology_shortcut}")
            await page.screenshot(path="/app/test_reports/artifacts_iter37/ui_isolated/automation_output/20261026_185017_fa36e9132b4c/rapid_isolated.jpeg", type="jpeg", quality=40, full_page=False)

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

    except Exception as e:
        print(f"Isolated rapid probe failed: {str(e)}")
        await page.screenshot(path="/app/test_reports/artifacts_iter37/ui_isolated/automation_output/20261026_185017_fa36e9132b4c/rapid_isolated_error.jpeg", type="jpeg", quality=40, full_page=False)
