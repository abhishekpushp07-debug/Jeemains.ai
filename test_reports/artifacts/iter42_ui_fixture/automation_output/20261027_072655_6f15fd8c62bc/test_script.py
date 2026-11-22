async def run_test(page, output_dir, page_url):
    try:
        import json
        from datetime import datetime, timedelta, timezone

        fx = json.loads(open('/tmp/iter42_ui_fixture.json', 'r', encoding='utf-8').read())
        uid = fx['uid']
        token = fx['token']
        exp = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()

        await page.set_viewport_size({"width": 390, "height": 844})

        async def handle_route(route):
            url = route.request.url
            if '/api/jl/auth/session' in url:
                await route.fulfill(status=200, content_type='application/json', body=json.dumps({"user": {"id": uid, "name": "TEST-RF-portrait-ui", "phone": "7000000000", "role": "student", "pin_set": True}}))
                return
            if '/api/jl/auth/me' in url:
                await route.fulfill(status=200, content_type='application/json', body=json.dumps({"id": uid, "name": "TEST-RF-portrait-ui", "phone": "7000000000", "role": "student", "pin_set": True}))
                return
            if '/api/rf/access' in url:
                await route.fulfill(status=200, content_type='application/json', body=json.dumps({"token": token, "user_id": uid, "expires_at": exp}))
                return
            await route.continue_()

        await page.route('**/*', handle_route)

        print('Step 1: Open app with isolated auth fixture')
        await page.goto('https://scale-engine-50k--0gu36hlx.preview.emergentagent.com', wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_selector('[data-testid="tab-rapid"]', timeout=30000)
        print('Step 1 passed: fixture auth loaded')

        print('Step 2: Open Rapid lobby and capture')
        await page.click('[data-testid="tab-rapid"]', force=True)
        await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=20000)
        await page.wait_for_selector('[data-testid="rf-play-now"]', timeout=20000)
        await page.screenshot(path='/app/test_reports/artifacts/iter42_ui_fixture/automation_output/20261027_072655_6f15fd8c62bc/rapid_lobby_fixture_390.jpeg', type="jpeg", quality=40, full_page=False)
        print('Step 2 passed: fixture lobby visible')

        print('Step 3: Start solo and verify card behavior')
        await page.click('[data-testid="rf-play-now"]', force=True)
        await page.wait_for_selector('[data-testid="rf-play-sheet"]', timeout=10000)
        await page.click('[data-testid="rf-start-button"]', force=True)
        await page.wait_for_selector('[data-testid="rf-session-screen"]', timeout=20000)
        await page.wait_for_selector('[data-testid="rf-card"]', timeout=20000)
        await page.screenshot(path='/app/test_reports/artifacts/iter42_ui_fixture/automation_output/20261027_072655_6f15fd8c62bc/solo_card_390.jpeg', type="jpeg", quality=40, full_page=False)

        formula_count = await page.locator('[data-testid="rf-card-formula"]').count()
        print(f'Formula visible before answer count: {formula_count}')

        found_diagram = False
        for _ in range(8):
            has_diagram = await page.evaluate("""() => {
              const host = document.querySelector('[data-testid="rf-card-diagram"]');
              if (!host) return false;
              return !!host.querySelector('svg,img,canvas,path,g,polygon,circle,ellipse,line');
            }""")
            if has_diagram:
                found_diagram = True
                await page.screenshot(path='/app/test_reports/artifacts/iter42_ui_fixture/automation_output/20261027_072655_6f15fd8c62bc/solo_diagram_390.jpeg', type="jpeg", quality=40, full_page=False)
                break
            await page.click('[data-testid="rf-skip-button"]', force=True)
            await page.wait_for_timeout(1200)
        print(f'Diagram card found: {found_diagram}')

        await page.click('[data-testid="rf-option-0"]', force=True)
        await page.wait_for_selector('[data-testid="rf-feedback"]', timeout=8000)
        await page.screenshot(path='/app/test_reports/artifacts/iter42_ui_fixture/automation_output/20261027_072655_6f15fd8c62bc/solo_feedback_390.jpeg', type="jpeg", quality=40, full_page=False)

        await page.click('[data-testid="rf-exit-button"]', force=True)
        await page.wait_for_selector('[data-testid="rf-exit-sheet"]', timeout=8000)
        await page.click('[data-testid="rf-exit-finish"]', force=True)
        await page.wait_for_selector('[data-testid="rf-summary"]', timeout=20000)
        await page.screenshot(path='/app/test_reports/artifacts/iter42_ui_fixture/automation_output/20261027_072655_6f15fd8c62bc/solo_summary_390.jpeg', type="jpeg", quality=40, full_page=False)
        await page.click('[data-testid="rf-done"]', force=True)
        await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=15000)
        print('Step 3 passed: solo start, feedback, partial finish summary validated')

        print('Step 4: Open quick match duel and capture state')
        await page.click('[data-testid="rf-play-now"]', force=True)
        await page.wait_for_selector('[data-testid="rf-play-sheet"]', timeout=10000)
        await page.click('[data-testid="rf-duel-random"]', force=True)
        await page.wait_for_selector('[data-testid="duel-screen"]', timeout=20000)
        await page.wait_for_timeout(7000)
        if await page.locator('[data-testid="duel-play"]').count() > 0:
            await page.screenshot(path='/app/test_reports/artifacts/iter42_ui_fixture/automation_output/20261027_072655_6f15fd8c62bc/duel_play_390.jpeg', type="jpeg", quality=40, full_page=False)
        elif await page.locator('[data-testid="duel-waiting"]').count() > 0:
            await page.screenshot(path='/app/test_reports/artifacts/iter42_ui_fixture/automation_output/20261027_072655_6f15fd8c62bc/duel_waiting_390.jpeg', type="jpeg", quality=40, full_page=False)
        else:
            await page.screenshot(path='/app/test_reports/artifacts/iter42_ui_fixture/automation_output/20261027_072655_6f15fd8c62bc/duel_state_390.jpeg', type="jpeg", quality=40, full_page=False)
        print('Step 4 passed: duel state captured')

        print('Step 5: Open shop directly and capture wallet state')
        await page.goto('https://scale-engine-50k--0gu36hlx.preview.emergentagent.com/rapid/shop', wait_until='domcontentloaded', timeout=40000)
        await page.wait_for_selector('[data-testid="shop-screen"]', timeout=15000)
        await page.wait_for_timeout(1500)
        await page.screenshot(path='/app/test_reports/artifacts/iter42_ui_fixture/automation_output/20261027_072655_6f15fd8c62bc/shop_fixture_390.jpeg', type="jpeg", quality=40, full_page=False)
        print('Step 5 passed: shop captured')

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(', ');
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

        print('Isolated fixture UI flow completed')
    except Exception as e:
        print(f'Isolated fixture flow failed: {str(e)}')
        await page.screenshot(path='/app/test_reports/artifacts/iter42_ui_fixture/automation_output/20261027_072655_6f15fd8c62bc/fixture_ui_error.jpeg', type="jpeg", quality=40, full_page=False)

