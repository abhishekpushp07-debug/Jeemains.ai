async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.wait_for_selector('[data-testid="entry-phone-input"]', timeout=20000)
        await page.fill('[data-testid="entry-phone-input"]', '9000000001')
        await page.click('[data-testid="entry-continue-button"]', force=True)
        await page.wait_for_timeout(2000)
        if '/rapid' not in page.url:
            await page.goto('https://jeelive-mobile.preview.emergentagent.com/rapid')
            await page.wait_for_timeout(2000)
        await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=25000)
        await page.click('[data-testid="rf-exam-neet"]', force=True)
        await page.wait_for_timeout(700)

        visible = await page.is_visible('[data-testid="rf-revise-chapter-0"]')
        print(f'Revision button visible after seeding: {visible}')
        if visible:
            chapter = await page.text_content('[data-testid="rf-weak-chapter-0"]')
            await page.click('[data-testid="rf-revise-chapter-0"]', force=True)
            await page.wait_for_selector('[data-testid="rf-session-screen"]', timeout=12000)
            session_exam = await page.text_content('[data-testid="rf-session-exam"]')
            print(f'Revision launch chapter={chapter} session_header={session_exam}')
            await page.screenshot(path='/app/test_reports/artifacts_iter30/automation_output/20261025_202831_b8ede670c303/revision_one_tap.jpeg', type="jpeg", quality=40, full_page=False)
        else:
            print('Revision button still not visible')

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(', ');
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print('No error messages found on the page')
    except Exception as e:
        print(f'Revision check failed: {str(e)}')

