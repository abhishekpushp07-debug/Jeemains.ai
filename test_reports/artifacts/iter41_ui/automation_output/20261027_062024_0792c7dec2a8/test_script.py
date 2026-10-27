async def run_test(page, output_dir, page_url):
    import os
    import time
    from dotenv import dotenv_values

    creds = dotenv_values('/app/backend/.env')
    phone = str(creds.get('JEELIVE_TEST_PHONE') or '')
    pin = str(creds.get('JEELIVE_TEST_PIN') or '')

    img_responses = []
    request_log = []

    def on_request(req):
        u = req.url
        if '/asset/' in u:
            request_log.append((time.time(), req.method, u))

    def on_response(res):
        u = res.url
        if '/asset/' in u:
            h = res.headers
            cl = h.get('content-length', '')
            try:
                size = int(cl) if cl else 0
            except Exception:
                size = 0
            img_responses.append({
                'ts': time.time(),
                'status': res.status,
                'url': u,
                'size': size,
                'etag': h.get('etag', ''),
                'last_modified': h.get('last-modified', ''),
                'content_range': h.get('content-range', ''),
                'accept_ranges': h.get('accept-ranges', ''),
                'cache_control': h.get('cache-control', '')
            })

    page.on('request', on_request)
    page.on('response', on_response)
    page.on('console', lambda msg: print(f"CONSOLE: {msg.type}: {msg.text}"))

    try:
        await page.set_viewport_size({'width': 390, 'height': 844})
        await page.wait_for_timeout(1200)

        print('Step: wait entry')
        await page.wait_for_selector('[data-testid="entry-screen"]', timeout=30000)

        if not phone or not pin:
            raise Exception('Missing JEELIVE_TEST_PHONE or JEELIVE_TEST_PIN')

        print('Step: login once')
        await page.fill('[data-testid="entry-phone-input"]', phone)
        await page.fill('[data-testid="entry-pin-input"]', pin)
        await page.click('[data-testid="entry-continue-button"]', force=True)

        await page.wait_for_timeout(3000)
        if await page.locator('[data-testid="home-screen"]').count() == 0:
            # Sometimes redirects to jee/tests first depending on cache state.
            await page.wait_for_timeout(2500)

        if await page.locator('[data-testid="home-screen"]').count() > 0:
            print('Home screen loaded')
        else:
            print('Home screen not immediate; continuing with tabs')

        # RF unchanged + JEE tab present, NEET absent quick UI check
        tab_jee = await page.locator('[data-testid="tab-jee"]').count()
        tab_rapid = await page.locator('[data-testid="tab-rapid"]').count()
        tab_tests = await page.locator('[data-testid="tab-tests"]').count()
        tab_mission = await page.locator('[data-testid="tab-mission"]').count()
        neet_text = await page.locator('text=NEET').count()
        print(f'Tabs present jee={tab_jee} rapid={tab_rapid} tests={tab_tests} mission={tab_mission}; neet_text_count={neet_text}')

        print('Step: open JEE -> PYQ list')
        await page.click('[data-testid="tab-jee"]', force=True)
        await page.wait_for_timeout(1200)

        # Prefer direct PYQ route trigger if visible in hub
        pyq_entry_candidates = [
            '[data-testid="exam-hub-pyq-entry"]',
            '[data-testid="jee-pyq-entry"]',
            'text=PYQ',
            'text=Real papers',
        ]
        opened_pyq = False
        for sel in pyq_entry_candidates:
            if await page.locator(sel).first.count() > 0:
                await page.locator(sel).first.click(force=True)
                opened_pyq = True
                break
        if not opened_pyq:
            await page.goto('https://jeelive-mobile.preview.emergentagent.com/pyq')

        await page.wait_for_selector('[data-testid="pyq-screen"]', timeout=30000)
        await page.wait_for_timeout(1500)
        total_text = await page.locator('[data-testid="pyq-total"]').inner_text()
        print(f'PYQ total text: {total_text}')

        # Open first paper card button (continue/reattempt/start)
        print('Step: open first PYQ paper')
        first_action = page.locator('[data-testid^="pyq-"][data-testid$="-button-"]').first
        if await first_action.count() == 0:
            # fallback for exact buttons by contains
            first_action = page.locator('button:has-text("Continue"), button:has-text("Re-attempt"), button:has-text("Start")').first
        await first_action.click(force=True)

        # Attempt screen should come directly (no ready sheet)
        await page.wait_for_timeout(1500)
        await page.wait_for_selector('[data-testid="player-screen"], [data-testid="result-screen"]', timeout=40000)

        if await page.locator('[data-testid="player-screen"]').count() > 0:
            print('Player opened directly')
            ready_sheet = await page.locator('text=Ready').count()
            countdown = await page.locator('text=30').count()
            print(f'Ready/countdown markers: ready={ready_sheet} countdownTextCount={countdown}')

            # detect no image counter strings
            counter_7578 = await page.locator('text=75/78').count()
            counter_imgword = await page.locator('text=/78').count()
            print(f'Image counter markers 75/78={counter_7578} any /78={counter_imgword}')

            # Capture subject tabs and position text
            subj_pos = ''
            if await page.locator('[data-testid="player-subject-position"]').count() > 0:
                subj_pos = await page.locator('[data-testid="player-subject-position"]').inner_text()
            print(f'Player subject position: {subj_pos}')

            # Open palette grid and close
            await page.click('[data-testid="player-palette-button"]', force=True)
            await page.wait_for_timeout(600)
            if await page.locator('[data-testid="player-palette-sheet"]').count() > 0:
                print('Palette opened')
            # pick first question in grid
            if await page.locator('[data-testid^="palette-q-"]').first.count() > 0:
                await page.locator('[data-testid^="palette-q-"]').first.click(force=True)
                await page.wait_for_timeout(500)

            # next within subject
            if await page.locator('[data-testid="player-next-button"]').count() > 0:
                await page.click('[data-testid="player-next-button"]', force=True)
                await page.wait_for_timeout(700)

            # minimal screenshot without auth fields
            await page.screenshot(path='/app/test_reports/artifacts/iter41_ui/automation_output/20261027_062024_0792c7dec2a8/player_state.jpeg', type="jpeg", quality=40, full_page=False)

            # leave attempt safely without edits
            await page.click('[data-testid="player-exit-button"]', force=True)
            await page.wait_for_timeout(400)
            if await page.locator('[data-testid="player-exit-confirm"]').count() > 0:
                await page.click('[data-testid="player-exit-confirm"]', force=True)
                await page.wait_for_timeout(1200)

        if await page.locator('[data-testid="result-screen"]').count() > 0:
            print('Result screen opened')
            # open solutions tab
            if await page.locator('[data-testid="result-tab-solutions"]').count() > 0:
                await page.click('[data-testid="result-tab-solutions"]', force=True)
                await page.wait_for_timeout(1600)
                counter_7578_sol = await page.locator('text=75/78').count()
                print(f'Solution image counter 75/78 markers={counter_7578_sol}')
                if await page.locator('[data-testid="solution-grid-open"]').count() > 0:
                    await page.click('[data-testid="solution-grid-open"]', force=True)
                    await page.wait_for_timeout(500)
                    if await page.locator('[data-testid="solution-grid-sheet"]').count() > 0:
                        await page.click('[data-testid="solution-grid-close"]', force=True)
                await page.screenshot(path='/app/test_reports/artifacts/iter41_ui/automation_output/20261027_062024_0792c7dec2a8/result_solutions.jpeg', type="jpeg", quality=40, full_page=False)

        # Reload to test session persistence and cached image behavior
        before_count = len(img_responses)
        print(f'Image responses before reload: {before_count}')
        await page.reload(wait_until='domcontentloaded')
        await page.wait_for_timeout(3000)

        # If session persisted, private screens still accessible via tests tab.
        if await page.locator('[data-testid="tab-tests"]').count() > 0:
            await page.click('[data-testid="tab-tests"]', force=True)
            await page.wait_for_selector('[data-testid="my-tests-screen"]', timeout=20000)
            print('Session persisted after reload')
        else:
            print('Session did not persist to authenticated tabs after reload')

        # logout and verify private route blocked
        if await page.locator('[data-testid="home-account-button"]').count() == 0 and await page.locator('[data-testid="tab-index"]').count() > 0:
            await page.click('[data-testid="tab-index"]', force=True)
            await page.wait_for_timeout(900)
        if await page.locator('[data-testid="home-account-button"]').count() > 0:
            await page.click('[data-testid="home-account-button"]', force=True)
            await page.wait_for_timeout(1000)
            # best-effort selector for signout button
            for sel in ['[data-testid="account-signout-button"]', '[data-testid="account-logout-button"]', 'text=Sign out', 'text=Logout']:
                if await page.locator(sel).first.count() > 0:
                    await page.locator(sel).first.click(force=True)
                    await page.wait_for_timeout(1200)
                    break

        # verify private page blocked after logout by direct navigation
        await page.goto('https://jeelive-mobile.preview.emergentagent.com/(tabs)/tests')
        await page.wait_for_timeout(1500)
        blocked = await page.locator('[data-testid="entry-screen"]').count() > 0
        print(f'Private route blocked after logout: {blocked}')

        after_count = len(img_responses)
        print(f'Image responses after reload/flows: {after_count}')

        statuses = {}
        total_bytes = 0
        by_url = {}
        for row in img_responses:
          statuses[row['status']] = statuses.get(row['status'], 0) + 1
          total_bytes += row['size']
          by_url[row['url']] = by_url.get(row['url'], 0) + 1

        duplicates = sum(1 for _, c in by_url.items() if c > 1)
        print(f'Image response status counts: {statuses}')
        print(f'Image total content-length bytes: {total_bytes}')
        print(f'Image duplicated URL count: {duplicates}')

        # show few sample validator headers
        for sample in img_responses[:6]:
            print('IMG_SAMPLE', sample['status'], 'etag=', bool(sample['etag']), 'lm=', bool(sample['last_modified']), 'cr=', sample['content_range'], 'ar=', sample['accept_ranges'], 'cc=', sample['cache_control'])

        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*=\"error\"], [id*=\"error\"]'));
        return errorElements.map(el => el.textContent).join(', ');
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

    except Exception as e:
        print(f'UI flow failed: {str(e)}')
        await page.screenshot(path='/app/test_reports/artifacts/iter41_ui/automation_output/20261027_062024_0792c7dec2a8/ui_error.jpeg', type="jpeg", quality=40, full_page=False)

