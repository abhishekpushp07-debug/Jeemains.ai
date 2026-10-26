async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 375, "height": 667})
        page.on("console", lambda msg: print(f"CONSOLE: {msg.type}: {msg.text}"))
        await page.wait_for_timeout(4000)
        title = await page.title()
        body_text = (await page.locator('body').inner_text())[:220]
        print(f"Step info: title={title}")
        print(f"Step info: body sample={body_text}")

        if await page.get_by_text("Welcome back.", exact=True).count() > 0:
            print("Step success: Entry copy visible")
            await page.screenshot(path="/app/test_reports/artifacts_iter39/ui_public_smoke_retry/automation_output/20261026_220120_d7c5087782b5/public_entry_copy_375.jpeg", type="jpeg", quality=40, full_page=False)
        elif await page.locator('[data-testid="home-tile-jee-main"]').count() > 0:
            print("Step success: Home tiles visible")
            await page.screenshot(path="/app/test_reports/artifacts_iter39/ui_public_smoke_retry/automation_output/20261026_220120_d7c5087782b5/public_home_tiles_375.jpeg", type="jpeg", quality=40, full_page=False)
        else:
            print("Step warning: expected entry/home selectors not visible")
            await page.screenshot(path="/app/test_reports/artifacts_iter39/ui_public_smoke_retry/automation_output/20261026_220120_d7c5087782b5/public_spinner_375.jpeg", type="jpeg", quality=40, full_page=False)

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
        await page.screenshot(path="/app/test_reports/artifacts_iter39/ui_public_smoke_retry/automation_output/20261026_220120_d7c5087782b5/public_smoke_retry_error.jpeg", type="jpeg", quality=40, full_page=False)

