async def run_test(page, output_dir, page_url):
    import time
    from dotenv import dotenv_values

    creds = dotenv_values('/app/backend/.env')
    phone = str(creds.get('JEELIVE_TEST_PHONE') or '')
    pin = str(creds.get('JEELIVE_TEST_PIN') or '')

    assets = []
    inflight = 0
    max_parallel = 0

    def is_asset(url):
        return '/asset/question/' in url or '/asset/solution/' in url

    def on_request(req):
        global inflight, max_parallel
        if is_asset(req.url):
            inflight += 1
            max_parallel = max(max_parallel, inflight)

    def on_response(res):
        global inflight
        if is_asset(res.url):
            h = res.headers
            cl = h.get('content-length', '')
            try:
                size = int(cl) if cl else 0
            except Exception:
                size = 0
            assets.append({
                'url': res.url,
                'status': res.status,
                'size': size,
                'etag': h.get('etag', ''),
                'lm': h.get('last-modified', ''),
                'cr': h.get('content-range', ''),
                'ar': h.get('accept-ranges', ''),
            })
            inflight = max(0, inflight - 1)

    page.on('request', on_request)
    page.on('response', on_response)
    page.on('console', lambda msg: print(f"CONSOLE: {msg.type}: {msg.text}"))

    try:
        await page.set_viewport_size({'width': 390, 'height': 844})
        await page.wait_for_selector('[data-testid="entry-screen"]', timeout=35000)

        if not phone or not pin:
            raise Exception('Missing JEELIVE_TEST_PHONE/PIN')

        await page.fill('[data-testid="entry-phone-input"]', phone)
        await page.fill('[data-testid="entry-pin-input"]', pin)

        signed_in = False
        for attempt in range(2):
            await page.click('[data-testid="entry-continue-button"]', force=True)
            await page.wait_for_timeout(3500)
            if await page.locator('[data-testid="tab-tests"]').count() > 0 or await page.locator('[data-testid="home-screen"]').count() > 0:
                signed_in = True
                break
            err = ''
            if await page.locator('[data-testid="entry-error"]').count() > 0:
                err = await page.locator('[data-testid="entry-error"]').inner_text()
            print(f'Login attempt {attempt+1} did not enter app. error={err}')

        if not signed_in:
            raise Exception('Unable to login after retry (transient proxy/API issue)')

        print('Signed in successfully')

        # JEE/RF tabs visible and NEET absent
        neet_count = await page.locator('text=NEET').count()
        print(f'neet_text_count={neet_count}')

        await page.click('[data-testid="tab-tests"]', force=True)
        await page.wait_for_selector('[data-testid="my-tests-screen"]', timeout=25000)

        p = await page.locator('[data-testid="my-tests-count-progress"]').first.inner_text() if await page.locator('[data-testid="my-tests-count-progress"]').count() else 'NA'
        c = await page.locator('[data-testid="my-tests-count-completed"]').first.inner_text() if await page.locator('[data-testid="my-tests-count-completed"]').count() else 'NA'
        print(f'Counts progress={p} completed={c}')

        # Open progress attempt first (read-only)
        await page.click('[data-testid="my-tests-tab-progress"]', force=True)
        await page.wait_for_timeout(1300)
        opened_player = False
        if await page.locator('[data-testid^="attempt-card-"]').first.count() > 0:
            await page.locator('[data-testid^="attempt-card-"]').first.click(force=True)
            await page.wait_for_timeout(1500)
            opened_player = await page.locator('[data-testid="player-screen"]').count() > 0

        if opened_player:
            ready = await page.locator('text=Ready to start').count()
            c7578 = await page.locator('text=75/78').count()
            print(f'Player direct-open readySheetHits={ready} counter7578={c7578}')

            t0 = time.time()
            qimg = page.locator('[data-testid^="question-image-"]').first
            if await qimg.count() > 0:
                await qimg.wait_for(state='visible', timeout=25000)
                print(f'First question image visible ms={round((time.time()-t0)*1000)}')

            if await page.locator('[data-testid="player-palette-button"]').count() > 0:
                await page.click('[data-testid="player-palette-button"]', force=True)
                await page.wait_for_timeout(500)
                print(f'Palette visible={await page.locator("[data-testid=\"player-palette-sheet\"]").count() > 0}')
                if await page.locator('[data-testid^="palette-q-"]').first.count() > 0:
                    await page.locator('[data-testid^="palette-q-"]').first.click(force=True)
                    await page.wait_for_timeout(500)

            await page.click('[data-testid="player-exit-button"]', force=True)
            await page.wait_for_timeout(400)
            if await page.locator('[data-testid="player-exit-confirm"]').count() > 0:
                await page.click('[data-testid="player-exit-confirm"]', force=True)
                await page.wait_for_timeout(1000)

        # Open completed result -> solutions
        await page.click('[data-testid="tab-tests"]', force=True)
        await page.wait_for_selector('[data-testid="my-tests-screen"]', timeout=25000)
        await page.click('[data-testid="my-tests-tab-completed"]', force=True)
        await page.wait_for_timeout(1500)

        if await page.locator('[data-testid^="attempt-card-"]').first.count() > 0:
            await page.locator('[data-testid^="attempt-card-"]').first.click(force=True)
            await page.wait_for_selector('[data-testid="result-screen"]', timeout=35000)
            if await page.locator('[data-testid="result-tab-solutions"]').count() > 0:
                await page.click('[data-testid="result-tab-solutions"]', force=True)
                await page.wait_for_timeout(1800)
                sol_counter = await page.locator('text=75/78').count()
                print(f'Solutions counter7578={sol_counter}')

        pre = len(assets)
        await page.reload(wait_until='domcontentloaded')
        await page.wait_for_timeout(3000)
        print(f'Session persisted after reload={await page.locator("[data-testid=\"tab-tests\"]").count() > 0}')

        # Logout + route guard
        if await page.locator('[data-testid="tab-index"]').count() > 0:
            await page.click('[data-testid="tab-index"]', force=True)
            await page.wait_for_timeout(900)
        if await page.locator('[data-testid="home-account-button"]').count() > 0:
            await page.click('[data-testid="home-account-button"]', force=True)
            await page.wait_for_selector('[data-testid="account-signout-button"]', timeout=20000)
            await page.click('[data-testid="account-signout-button"]', force=True)
            await page.wait_for_timeout(1000)

        await page.goto('https://jeelive-mobile.preview.emergentagent.com/(tabs)/tests')
        await page.wait_for_timeout(1300)
        print(f'Private route blocked after logout={await page.locator("[data-testid=\"entry-screen\"]").count() > 0}')

        # Metrics
        statuses = {}
        bytes_total = 0
        by_url = {}
        validator_hits = 0
        for r in assets:
            statuses[r['status']] = statuses.get(r['status'], 0) + 1
            bytes_total += r['size']
            by_url[r['url']] = by_url.get(r['url'], 0) + 1
            if r['etag'] or r['lm'] or r['cr'] or r['ar']:
                validator_hits += 1
        dups = sum(1 for _, count in by_url.items() if count > 1)
        print(f'Asset metrics total={len(assets)} pre_reload={pre} post_reload={len(assets)-pre} statuses={statuses} bytes={bytes_total} max_parallel={max_parallel} dups={dups} validator_hits={validator_hits}')

        for s in assets[:6]:
            print('ASSET_SAMPLE', s['status'], bool(s['etag']), bool(s['lm']), s['cr'], s['ar'])

        await page.screenshot(path='/app/test_reports/artifacts/iter41_ui_run3/automation_output/20261027_062305_ef54c7af9c2b/post_logout.jpeg', type="jpeg", quality=40, full_page=False)

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

