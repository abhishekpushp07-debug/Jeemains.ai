async def run_test(page, output_dir, page_url):
    import os
    import time
    from dotenv import dotenv_values

    creds = dotenv_values('/app/backend/.env')
    phone = str(creds.get('JEELIVE_TEST_PHONE') or '')
    pin = str(creds.get('JEELIVE_TEST_PIN') or '')

    asset_req_start = {}
    asset_records = []
    inflight = 0
    max_parallel = 0

    def is_asset(url: str):
        return '/asset/question/' in url or '/asset/solution/' in url

    def on_request(req):
        global inflight, max_parallel
        if is_asset(req.url):
            inflight += 1
            if inflight > max_parallel:
                max_parallel = inflight
            asset_req_start[req.url + '|' + req.method + '|' + str(time.time())] = time.time()

    def on_response(res):
        global inflight
        u = res.url
        if is_asset(u):
            h = res.headers
            cl = h.get('content-length', '')
            try:
                size = int(cl) if cl else 0
            except Exception:
                size = 0
            asset_records.append({
                't': time.time(),
                'url': u,
                'status': res.status,
                'size': size,
                'etag': h.get('etag', ''),
                'lm': h.get('last-modified', ''),
                'cr': h.get('content-range', ''),
                'ar': h.get('accept-ranges', ''),
                'cc': h.get('cache-control', ''),
            })
            inflight = max(0, inflight - 1)

    page.on('request', on_request)
    page.on('response', on_response)
    page.on('console', lambda msg: print(f"CONSOLE: {msg.type}: {msg.text}"))

    try:
        await page.set_viewport_size({'width': 390, 'height': 844})
        await page.wait_for_selector('[data-testid="entry-screen"]', timeout=35000)

        if not phone or not pin:
            raise Exception('Missing JEELIVE_TEST_PHONE/PIN env values')

        await page.fill('[data-testid="entry-phone-input"]', phone)
        await page.fill('[data-testid="entry-pin-input"]', pin)
        await page.click('[data-testid="entry-continue-button"]', force=True)
        await page.wait_for_timeout(3500)

        # Move to My Tests and collect baseline history counts.
        await page.click('[data-testid="tab-tests"]', force=True)
        await page.wait_for_selector('[data-testid="my-tests-screen"]', timeout=30000)

        progress_count = await page.locator('[data-testid="my-tests-count-progress"]').first.inner_text() if await page.locator('[data-testid="my-tests-count-progress"]').count() else 'NA'
        completed_count = await page.locator('[data-testid="my-tests-count-completed"]').first.inner_text() if await page.locator('[data-testid="my-tests-count-completed"]').count() else 'NA'
        print(f'Baseline history counts progress={progress_count} completed={completed_count}')

        # Prefer existing in-progress attempt for read-only validation.
        await page.click('[data-testid="my-tests-tab-progress"]', force=True)
        await page.wait_for_timeout(1200)

        opened_player = False
        if await page.locator('[data-testid^="attempt-card-"]').first.count() > 0:
            await page.locator('[data-testid^="attempt-card-"]').first.click(force=True)
            await page.wait_for_timeout(1200)
            if await page.locator('[data-testid="player-screen"]').count() > 0:
                opened_player = True

        if not opened_player:
            print('No progress attempt opened; trying JEE hub -> PYQ continue only')
            await page.click('[data-testid="tab-jee"]', force=True)
            await page.wait_for_selector('[data-testid="exam-hub-jee-main"]', timeout=25000)
            await page.click('[data-testid="exam-destination-pyq"]', force=True)
            await page.wait_for_selector('[data-testid="pyq-screen"]', timeout=35000)

            # Continue button only to avoid creating a new attempt
            cont = page.locator('[data-testid^="pyq-continue-button-"]')
            if await cont.count() > 0:
                await cont.first.click(force=True)
                await page.wait_for_timeout(1200)
                opened_player = await page.locator('[data-testid="player-screen"]').count() > 0
            else:
                print('No Continue button found in PYQ cards; skipping write-path Start/Re-attempt')

        if opened_player:
            print('Player opened directly (no ready-sheet expected)')
            # check no readiness sheet/countdown markers
            ready_sheet = await page.locator('text=Ready to start').count()
            countdown_30 = await page.locator('text=30s').count()
            print(f'Ready markers ready={ready_sheet} countdown30={countdown_30}')

            # first question image load timing (best-effort)
            t0 = time.time()
            qimg = page.locator('[data-testid^="question-image-"]').first
            if await qimg.count() > 0:
                await qimg.wait_for(state='visible', timeout=25000)
                t1 = time.time()
                print(f'First question image visible in {round((t1 - t0)*1000)} ms')

            # no 75/78 image counter
            c7578 = await page.locator('text=75/78').count()
            print(f'Counter 75/78 occurrences in player={c7578}')

            # subject label and navigation
            subj = await page.locator('[data-testid="player-subject-position"]').inner_text() if await page.locator('[data-testid="player-subject-position"]').count() else ''
            print(f'Player subject position: {subj}')

            if await page.locator('[data-testid="player-palette-button"]').count() > 0:
                await page.click('[data-testid="player-palette-button"]', force=True)
                await page.wait_for_timeout(500)
                palette = await page.locator('[data-testid="player-palette-sheet"]').count() > 0
                print(f'Palette sheet opened={palette}')
                if await page.locator('[data-testid^="palette-q-"]').first.count() > 0:
                    await page.locator('[data-testid^="palette-q-"]').first.click(force=True)
                    await page.wait_for_timeout(500)

            if await page.locator('[data-testid="player-next-button"]').count() > 0:
                await page.click('[data-testid="player-next-button"]', force=True)
                await page.wait_for_timeout(700)

            # leave without editing
            await page.click('[data-testid="player-exit-button"]', force=True)
            await page.wait_for_timeout(300)
            if await page.locator('[data-testid="player-exit-confirm"]').count() > 0:
                await page.click('[data-testid="player-exit-confirm"]', force=True)
                await page.wait_for_timeout(1200)

        # Completed/results read-only flow
        await page.click('[data-testid="tab-tests"]', force=True)
        await page.wait_for_selector('[data-testid="my-tests-screen"]', timeout=25000)
        await page.click('[data-testid="my-tests-tab-completed"]', force=True)
        await page.wait_for_timeout(1500)
        if await page.locator('[data-testid^="attempt-card-"]').first.count() > 0:
            await page.locator('[data-testid^="attempt-card-"]').first.click(force=True)
            await page.wait_for_selector('[data-testid="result-screen"]', timeout=35000)
            print('Opened completed result')
            if await page.locator('[data-testid="result-tab-solutions"]').count() > 0:
                await page.click('[data-testid="result-tab-solutions"]', force=True)
                await page.wait_for_timeout(1800)
                csol = await page.locator('text=75/78').count()
                print(f'Counter 75/78 occurrences in solutions={csol}')
                if await page.locator('[data-testid="solution-grid-open"]').count() > 0:
                    await page.click('[data-testid="solution-grid-open"]', force=True)
                    await page.wait_for_timeout(500)
                    if await page.locator('[data-testid="solution-grid-sheet"]').count() > 0:
                        await page.click('[data-testid="solution-grid-close"]', force=True)

            await page.screenshot(path='/app/test_reports/artifacts/iter41_ui_run2/automation_output/20261027_062141_35e6966f241e/result_state.jpeg', type="jpeg", quality=40, full_page=False)

        # reload for persistence and cache
        pre_reload_asset = len(asset_records)
        await page.reload(wait_until='domcontentloaded')
        await page.wait_for_timeout(3000)
        persisted = await page.locator('[data-testid="tab-tests"]').count() > 0
        print(f'Session persisted after reload={persisted}')

        # attempt logout and route guard
        if await page.locator('[data-testid="tab-index"]').count() > 0:
            await page.click('[data-testid="tab-index"]', force=True)
            await page.wait_for_timeout(900)
        if await page.locator('[data-testid="home-account-button"]').count() > 0:
            await page.click('[data-testid="home-account-button"]', force=True)
            await page.wait_for_timeout(1200)
            for sel in ['[data-testid="account-signout-button"]', '[data-testid="account-logout-button"]', 'text=Sign out', 'text=Logout']:
                if await page.locator(sel).first.count() > 0:
                    await page.locator(sel).first.click(force=True)
                    await page.wait_for_timeout(1200)
                    break

        await page.goto('https://jeelive-mobile.preview.emergentagent.com/(tabs)/tests')
        await page.wait_for_timeout(1500)
        blocked = await page.locator('[data-testid="entry-screen"]').count() > 0
        print(f'Private route blocked after logout={blocked}')

        # metrics summary
        statuses = {}
        bytes_total = 0
        by_url = {}
        validator_seen = 0
        for r in asset_records:
            statuses[r['status']] = statuses.get(r['status'], 0) + 1
            bytes_total += r['size']
            by_url[r['url']] = by_url.get(r['url'], 0) + 1
            if r['etag'] or r['lm'] or r['cr'] or r['ar']:
                validator_seen += 1

        duplicates = sum(1 for _, c in by_url.items() if c > 1)
        print(f'Asset requests total={len(asset_records)} pre_reload={pre_reload_asset} post_reload={len(asset_records)-pre_reload_asset}')
        print(f'Asset statuses={statuses} bytes={bytes_total} max_parallel={max_parallel} duplicate_urls={duplicates} validator_header_hits={validator_seen}')

        for s in asset_records[:8]:
            print('ASSET_SAMPLE', s['status'], 'etag=', bool(s['etag']), 'lm=', bool(s['lm']), 'cr=', s['cr'], 'ar=', s['ar'])

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
        await page.screenshot(path='/app/test_reports/artifacts/iter41_ui_run2/automation_output/20261027_062141_35e6966f241e/ui_error.jpeg', type="jpeg", quality=40, full_page=False)

