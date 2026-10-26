async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 375, "height": 667})
        page.on("console", lambda msg: print(f"CONSOLE: {msg.type}: {msg.text}"))
        await page.wait_for_timeout(1200)
        if await page.locator('[data-testid="entry-screen"]').count() > 0:
            print("Step success: Entry screen visible")
            await page.screenshot(path="/app/test_reports/artifacts_iter39/ui_public_smoke/automation_output/20261026_215934_6d0aec21bc78/public_entry_375.jpeg", type="jpeg", quality=40, full_page=False)
        elif await page.locator('[data-testid="home-screen"]').count() > 0:
            print("Step success: Home screen visible (existing session)")
            await page.screenshot(path="/app/test_reports/artifacts_iter39/ui_public_smoke/automation_output/20261026_215934_6d0aec21bc78/public_home_375.jpeg", type="jpeg", quality=40, full_page=False)
        else:
            print("Step info: Neither entry nor home testID detected")
            await page.screenshot(path="/app/test_reports/artifacts_iter39/ui_public_smoke/automation_output/20261026_215934_6d0aec21bc78/public_unknown_375.jpeg", type="jpeg", quality=40, full_page=False)

        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*=\"error\"], [id*=\"error\"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")
    except Exception as e:
        print(f"Step failed: {str(e)}")
        await page.screenshot(path="/app/test_reports/artifacts_iter39/ui_public_smoke/automation_output/20261026_215934_6d0aec21bc78/public_smoke_error.jpeg", type="jpeg", quality=40, full_page=False)

