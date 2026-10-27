async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 390, "height": 844})
        print("Step 1: Viewport set")

        await page.wait_for_timeout(3000)
        if await page.locator('[data-testid="entry-phone-input"]').count() > 0:
            await page.fill('[data-testid="entry-phone-input"]', '7004186276')
            await page.fill('[data-testid="entry-pin-input"]', '5524')
            await page.click('[data-testid="entry-continue-button"]', force=True)
            await page.wait_for_timeout(5000)
            print("Step 2: Logged in")

        rapid_tab = page.get_by_text('RAPID', exact=True)
        if await rapid_tab.count() > 0:
            await rapid_tab.first.click(force=True)
        else:
            await page.click('[data-testid="tab-rapid"]', force=True)
        await page.wait_for_timeout(4000)

        rapid_visible = await page.evaluate("""() => {
          const text = document.body.innerText || '';
          return text.includes('Rapid Fire') || text.includes('formula cards') || text.includes('Challenge');
        }""")
        print(f"Step 3: Rapid screen visible signal = {rapid_visible}")

        await page.screenshot(path='/app/test_reports/artifacts_iter48/ui_rapid_smoke/automation_output/20261027_104033_f57c9bc82cc8/rapid_readonly_390.jpeg', type="jpeg", quality=40, full_page=False)

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
        print(f"Test failed: {str(e)}")
        await page.screenshot(path='/app/test_reports/artifacts_iter48/ui_rapid_smoke/automation_output/20261027_104033_f57c9bc82cc8/rapid_smoke_error.jpeg', type="jpeg", quality=40, full_page=False)

