async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 375, "height": 667})
        print("Step 1: Opened preview URL")
        await page.wait_for_timeout(2500)

        # basic visibility check
        body_visible = await page.locator('body').is_visible()
        print(f"Step 2: Body visible = {body_visible}")

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
          print(f"Found error message: {error_text}")
        else:
          print("No error messages found on the page")

        await page.screenshot(path="/app/test_reports/artifacts_iter40/ui_public_smoke/automation_output/20261026_224255_4ffb17ea9a32/preview_smoke.jpeg", type="jpeg", quality=40, full_page=False)
        print("Step 3: Captured smoke screenshot")
    except Exception as e:
        print(f"Smoke test failed: {str(e)}")
        await page.screenshot(path="/app/test_reports/artifacts_iter40/ui_public_smoke/automation_output/20261026_224255_4ffb17ea9a32/preview_smoke_error.jpeg", type="jpeg", quality=40, full_page=False)

