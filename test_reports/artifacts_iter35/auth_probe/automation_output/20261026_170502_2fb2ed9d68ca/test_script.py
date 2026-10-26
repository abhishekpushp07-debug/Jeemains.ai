async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 390, "height": 844})
        print("Step 1: viewport set")
        await page.wait_for_timeout(1000)

        phone_input = page.locator('input[placeholder*="98765"]').first
        await phone_input.wait_for(timeout=15000)
        await phone_input.fill("9000000001")
        print("Step 2: phone filled")

        await page.get_by_role("button", name="Continue", exact=True).click(force=True)
        await page.wait_for_timeout(2500)
        print("Step 3: continue clicked")

        await page.screenshot(path="/app/test_reports/artifacts_iter35/auth_probe/automation_output/20261026_170502_2fb2ed9d68ca/auth_result_390.jpeg", type="jpeg", quality=40, full_page=False)

        txt = await page.locator("body").inner_text()
        if "Too many requests" in txt:
            print("Auth rate limit message visible")
        elif "Your exam." in txt or "home-screen" in txt:
            print("Likely logged in and reached home")
        else:
            print("Auth outcome unclear; captured screenshot")

        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

    except Exception as e:
        print(f"Auth probe failed: {str(e)}")
        await page.screenshot(path="/app/test_reports/artifacts_iter35/auth_probe/automation_output/20261026_170502_2fb2ed9d68ca/auth_probe_error.jpeg", type="jpeg", quality=40, full_page=False)

