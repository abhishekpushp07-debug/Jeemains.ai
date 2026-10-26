async def run_test(page, output_dir, page_url):
    page.on("console", lambda msg: print(f"CONSOLE: {msg.type}: {msg.text}"))

    try:
        await page.set_viewport_size({"width": 375, "height": 667})
        print("Step 1: viewport set")

        await page.wait_for_selector('[data-testid="entry-phone-input"]', timeout=20000)
        await page.fill('[data-testid="entry-phone-input"]', '9000000001')
        await page.click('[data-testid="entry-continue-button"]', force=True)
        print("Step 2: login submitted")

        await page.wait_for_selector('[data-testid="home-screen"]', timeout=30000)
        await page.wait_for_timeout(1200)
        print("Step 3: home loaded")

        await page.screenshot(path="/app/test_reports/artifacts_iter36/ui_e2e/automation_output/20261026_175339_0d7f99038f97/home_after_login.jpeg", type="jpeg", quality=40, full_page=False)

        await page.click('[data-testid="home-tile-jee-main"]', force=True)
        await page.wait_for_selector('[data-testid="exam-hub-jee-main"]', timeout=15000)
        print("Step 4: entered JEE hub")

        await page.click('[data-testid="exam-destination-pyq"]', force=True)
        await page.wait_for_selector('[data-testid="pyq-screen"]', timeout=20000)
        await page.wait_for_timeout(1800)
        print("Step 5: entered PYQ screen")

        start_buttons = page.locator('[data-testid^="pyq-start-button-"]')
        start_count = await start_buttons.count()
        if start_count == 0:
            raise Exception("No Start button found; cannot run approved new-attempt pilot flow")

        start_btn = start_buttons.first
        start_tid = await start_btn.get_attribute('data-testid')
        paper_id = start_tid.replace('pyq-start-button-', '') if start_tid else ''
        if not paper_id:
            raise Exception("Could not infer target paper id from Start button")

        attempt_count_badge = page.locator(f'[data-testid="pyq-attempt-count-{paper_id}"]')
        has_attempt_badge = await attempt_count_badge.count()
        if has_attempt_badge > 0:
            raise Exception("Selected paper appears to have existing attempts; expected attempt_count=0")

        await start_btn.click(force=True)
        await page.wait_for_selector('[data-testid="player-screen"]', timeout=30000)
        await page.wait_for_timeout(2500)
        print("Step 6: started new attempt from attempt_count=0 paper")

        first_attempt_url = page.url
        first_attempt_id = first_attempt_url.split('/attempt/')[-1] if '/attempt/' in first_attempt_url else ''
        print(f"Step 6b: first attempt url captured: {bool(first_attempt_id)}")

        opt_a = page.locator('[data-testid="player-option-A"]')
        if await opt_a.count() > 0:
            await opt_a.first.click(force=True)
            await page.wait_for_timeout(1800)
            print("Step 7: selected option A")
        else:
            integer_input = page.locator('[data-testid="player-integer-input"]')
            if await integer_input.count() > 0:
                await integer_input.fill('1')
                await page.wait_for_timeout(1800)
                print("Step 7: filled integer answer")
            else:
                raise Exception("No answer input control found on first question")

        await page.click('[data-testid="player-exit-button"]', force=True)
        await page.wait_for_selector('[data-testid="player-exit-sheet"]', timeout=10000)
        await page.click('[data-testid="player-exit-confirm"]', force=True)
        await page.wait_for_selector('[data-testid="pyq-screen"]', timeout=20000)
        await page.wait_for_timeout(1500)
        print("Step 8: left attempt to PYQ list")

        continue_btn = page.locator(f'[data-testid="pyq-continue-button-{paper_id}"]')
        if await continue_btn.count() == 0:
            raise Exception("Continue button not found for the same paper after leaving")

        await continue_btn.first.click(force=True)
        await page.wait_for_selector('[data-testid="player-screen"]', timeout=25000)
        await page.wait_for_timeout(1200)
        resumed_url = page.url
        resumed_attempt_id = resumed_url.split('/attempt/')[-1] if '/attempt/' in resumed_url else ''
        if not first_attempt_id or not resumed_attempt_id or first_attempt_id != resumed_attempt_id:
            raise Exception("Resume did not reopen SAME attempt id")
        print("Step 9: continue reopened same attempt id")

        await page.click('[data-testid="player-palette-button"]', force=True)
        await page.wait_for_selector('[data-testid="player-palette-sheet"]', timeout=10000)
        await page.click('[data-testid="player-palette-submit"]', force=True)
        await page.wait_for_selector('[data-testid="player-submit-sheet"]', timeout=10000)
        await page.click('[data-testid="player-confirm-submit"]', force=True)
        print("Step 10: submit triggered")

        await page.wait_for_timeout(3000)
        # Either ready result screen or grading state on result screen
        await page.wait_for_selector('[data-testid="result-screen"]', timeout=30000)
        print("Step 11: result screen loaded")

        # Open solutions tab when available
        solutions_tab = page.locator('[data-testid="result-tab-solutions"]')
        if await solutions_tab.count() > 0:
            await solutions_tab.first.click(force=True)
            await page.wait_for_timeout(2500)
            print("Step 12: opened solutions tab")

        await page.screenshot(path="/app/test_reports/artifacts_iter36/ui_e2e/automation_output/20261026_175339_0d7f99038f97/result_after_submit.jpeg", type="jpeg", quality=40, full_page=False)

        # Navigate back and re-attempt same paper (new id)
        await page.click('[data-testid="result-back-button"]', force=True)
        await page.wait_for_timeout(1000)
        # Ensure we are at tests; go to home then JEE->PYQ for deterministic selector path
        if '/(tabs)/tests' in page.url or await page.locator('[data-testid="my-tests-screen"]').count() > 0:
            await page.click('[data-testid="tabs-home"]', force=True)
            await page.wait_for_timeout(1000)
        await page.goto('https://jeelive-mobile.preview.emergentagent.com/pyq')
        await page.wait_for_selector('[data-testid="pyq-screen"]', timeout=20000)
        reattempt_btn = page.locator(f'[data-testid="pyq-reattempt-button-{paper_id}"]')
        if await reattempt_btn.count() > 0:
            await reattempt_btn.first.click(force=True)
            await page.wait_for_selector('[data-testid="player-screen"]', timeout=25000)
            await page.wait_for_timeout(1200)
            new_attempt_url = page.url
            new_attempt_id = new_attempt_url.split('/attempt/')[-1] if '/attempt/' in new_attempt_url else ''
            print(f"Step 13: reattempt opened new id differs: {bool(new_attempt_id and new_attempt_id != first_attempt_id)}")
        else:
            print("Step 13: reattempt button not available yet (likely grading/pending)")

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

        print("UI E2E flow completed")

    except Exception as e:
        print(f"UI E2E failed: {str(e)}")
        await page.screenshot(path="/app/test_reports/artifacts_iter36/ui_e2e/automation_output/20261026_175339_0d7f99038f97/ui_e2e_failure.jpeg", type="jpeg", quality=40, full_page=False)

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")
