async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 390, "height": 844})
        print('Step 1: Viewport set to 390x844')

        await page.wait_for_selector('[data-testid="entry-phone-input"]', timeout=20000)
        await page.fill('[data-testid="entry-phone-input"]', '9000000001')
        await page.wait_for_timeout(300)
        await page.click('[data-testid="entry-continue-button"]', force=True)
        print('Step 2: Login submitted')

        await page.wait_for_timeout(2000)
        if '/rapid' not in page.url:
            await page.goto('https://jeelive-mobile.preview.emergentagent.com/rapid')
            await page.wait_for_timeout(2000)

        await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=25000)
        await page.wait_for_timeout(1000)
        await page.screenshot(path='/app/test_reports/artifacts_iter30/automation_output/20261025_202737_b3fdb5cbb354/rapid_home_390.jpeg', type="jpeg", quality=40, full_page=False)
        print('Step 3: Rapid home loaded and stable screenshot taken')

        await page.click('[data-testid="rf-exam-neet"]', force=True)
        await page.wait_for_timeout(800)
        neet_bio_visible = await page.is_visible('[data-testid="rf-subject-biology"]')
        print(f'Step 4: NEET toggle works, Biology visible: {neet_bio_visible}')

        # Leaderboard exam switch no stale title
        await page.click('[data-testid="rf-pane-board"]', force=True)
        await page.wait_for_timeout(500)
        neet_title = await page.text_content('[data-testid="rf-leaderboard-title"]')
        await page.click('[data-testid="rf-exam-jee"]', force=True)
        await page.wait_for_timeout(800)
        jee_title = await page.text_content('[data-testid="rf-leaderboard-title"]')
        await page.click('[data-testid="rf-exam-neet"]', force=True)
        await page.wait_for_timeout(800)
        neet_title_again = await page.text_content('[data-testid="rf-leaderboard-title"]')
        print(f'Step 5: Board titles: NEET={neet_title}, JEE={jee_title}, NEET2={neet_title_again}')

        # Diagram shortcut and sprint
        await page.wait_for_selector('[data-testid="rf-diagram-sprint"]', timeout=10000)
        await page.click('[data-testid="rf-diagram-sprint"]', force=True)
        await page.wait_for_selector('[data-testid="rf-session-screen"]', timeout=20000)
        await page.wait_for_selector('[data-testid="rf-card-counter"]', timeout=10000)
        counter_text = await page.text_content('[data-testid="rf-card-counter"]')
        print(f'Step 6: Diagram sprint started, counter: {counter_text}')

        seen = set()
        for idx in range(18):
            await page.wait_for_selector('[data-testid="rf-card-diagram-title"]', timeout=10000)
            title = (await page.text_content('[data-testid="rf-card-diagram-title"]') or '').lower()
            if 'heart' in title:
                seen.add('heart')
            if 'nephron' in title:
                seen.add('nephron')
            if 'flower' in title:
                seen.add('flower')

            if idx == 0:
                await page.click('[data-testid="rf-option-0"]', force=True)
                await page.wait_for_selector('[data-testid="rf-feedback"]', timeout=5000)
                await page.click('[data-testid="rf-next-button"]', force=True)
            elif idx == 1:
                await page.click('[data-testid="rf-skip-button"]', force=True)
            else:
                await page.click('[data-testid="rf-skip-button"]', force=True)
            await page.wait_for_timeout(350)

        await page.wait_for_selector('[data-testid="rf-summary"]', timeout=30000)
        print(f'Step 7: Diagram sprint completed. Diagram kinds seen: {seen}')

        review_btn = await page.is_visible('[data-testid="rf-review-missed"]')
        if review_btn:
            await page.click('[data-testid="rf-review-missed"]', force=True)
            await page.wait_for_timeout(500)
            print('Step 8: Review missed opened')
        else:
            print('Step 8: Review missed button not visible (possible if no misses)')

        await page.click('[data-testid="rf-done"]', force=True)
        await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=20000)
        print('Step 9: Returned to arena')

        # One-tap weak revision from arena
        revise_visible = await page.is_visible('[data-testid="rf-revise-chapter-0"]')
        print(f'Step 10: Revision shortcut visible: {revise_visible}')
        if revise_visible:
            chapter_label = await page.text_content('[data-testid="rf-weak-chapter-0"]')
            await page.click('[data-testid="rf-revise-chapter-0"]', force=True)
            await page.wait_for_selector('[data-testid="rf-session-exam"]', timeout=12000)
            sess_header = await page.text_content('[data-testid="rf-session-exam"]')
            print(f'Step 10b: Revision opened. Chapter tile={chapter_label}, session={sess_header}')
            await page.click('[data-testid="rf-exit-button"]', force=True)
            await page.wait_for_selector('[data-testid="rf-exit-sheet"]', timeout=6000)
            await page.click('[data-testid="rf-exit-discard"]', force=True)
            await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=12000)

        # narrow 320 overflow check
        await page.set_viewport_size({"width": 320, "height": 700})
        await page.wait_for_timeout(1000)
        has_overflow = await page.evaluate("""() => {
          const doc = document.documentElement;
          return doc.scrollWidth > window.innerWidth;
        }""")
        print(f'Step 11: Narrow width overflow detected: {has_overflow}')
        await page.screenshot(path='/app/test_reports/artifacts_iter30/automation_output/20261025_202737_b3fdb5cbb354/rapid_home_320.jpeg', type="jpeg", quality=40, full_page=False)

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(', ');
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

        print('UI flow test completed successfully')
    except Exception as e:
        print(f'UI flow test failed: {str(e)}')
        await page.screenshot(path='/app/test_reports/artifacts_iter30/automation_output/20261025_202737_b3fdb5cbb354/ui_flow_error.jpeg', type="jpeg", quality=40, full_page=False)

