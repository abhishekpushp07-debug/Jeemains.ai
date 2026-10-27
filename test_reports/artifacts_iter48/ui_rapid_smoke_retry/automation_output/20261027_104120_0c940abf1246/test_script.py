async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.wait_for_timeout(2500)

        inputs = page.locator('input')
        count_inputs = await inputs.count()
        print(f"Step 1: input count = {count_inputs}")
        if count_inputs >= 2:
            await inputs.nth(0).fill('7004186276')
            await inputs.nth(1).fill('5524')
            sign_in_buttons = page.get_by_role('button', name='Sign in', exact=True)
            if await sign_in_buttons.count() >= 2:
                await sign_in_buttons.nth(1).click(force=True)
            else:
                await sign_in_buttons.first.click(force=True)
            await page.wait_for_timeout(7000)
            print("Step 2: Sign-in submitted")

        rapid_text = page.get_by_text('RAPID', exact=True)
        if await rapid_text.count() > 0:
            await rapid_text.first.click(force=True)
            await page.wait_for_timeout(3000)
            print("Step 3: Rapid tab clicked")
        else:
            print("Step 3: Rapid tab not visible after login")

        rapid_visible = await page.evaluate("""() => {
          const t = document.body.innerText || '';
          return t.includes('Rapid Fire') || t.includes('Solo Sprint') || t.includes('Duel') || t.includes('formula cards');
        }""")
        print(f"Step 4: Rapid signals present = {rapid_visible}")
        await page.screenshot(path='/app/test_reports/artifacts_iter48/ui_rapid_smoke_retry/automation_output/20261027_104120_0c940abf1246/rapid_readonly_390.jpeg', type="jpeg", quality=40, full_page=False)

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
        await page.screenshot(path='/app/test_reports/artifacts_iter48/ui_rapid_smoke_retry/automation_output/20261027_104120_0c940abf1246/rapid_smoke_error.jpeg', type="jpeg", quality=40, full_page=False)

