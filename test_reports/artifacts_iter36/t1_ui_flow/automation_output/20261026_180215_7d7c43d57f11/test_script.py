async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 375, "height": 667})
        print("STEP 1: Viewport set")

        await page.wait_for_selector('[data-testid="entry-phone-input"]', timeout=20000)
        await page.fill('[data-testid="entry-phone-input"]', '9000000001')
        await page.click('[data-testid="entry-continue-button"]', force=True)
        await page.wait_for_selector('[data-testid="home-screen"]', timeout=30000)
        await page.wait_for_timeout(1000)
        print("STEP 2: Logged in and home loaded")

        artwork_data = await page.evaluate("""() => {
          const ids = [
            ['jee-main','jee'],
            ['live','live'],
            ['bitsat','bitsat'],
            ['comedk','comedk'],
          ];
          return ids.map(([slug, kind]) => {
            const imageHost = document.querySelector(`[data-testid=\"home-tile-${slug}-image\"]`);
            const img = imageHost ? imageHost.querySelector('img') : null;
            const art = document.querySelector(`[data-testid=\"home-tile-${slug}-original-artwork\"]`);
            const src = img ? (img.currentSrc || img.getAttribute('src') || '') : '';
            const filter = img ? getComputedStyle(img).filter : '';
            const has_icon = art ? art.querySelectorAll('svg path, [data-testid*=\"glyph\"], [class*=\"glyph\"]').length > 0 : false;
            return { slug, kind, src, filter, has_img: !!img, has_icon };
          });
        }""")
        print(f"STEP 3: Artwork render data: {artwork_data}")

        bad_src = [x for x in artwork_data if (not x.get('has_img')) or (f"/api/brand/cards/{x.get('kind')}.jpg" not in x.get('src',''))]
        if bad_src:
            raise Exception(f"Card artwork source mismatch: {bad_src}")
        bad_filter = [x for x in artwork_data if x.get('filter') not in ('none', '')]
        if bad_filter:
            raise Exception(f"Unexpected card image filter: {bad_filter}")

        await page.screenshot(path="/app/test_reports/artifacts_iter36/t1_ui_flow/automation_output/20261026_180215_7d7c43d57f11/home_cards_375.jpeg", type="jpeg", quality=40, full_page=False)

        await page.click('[data-testid="home-tile-jee-main"]', force=True)
        await page.wait_for_selector('[data-testid="exam-hub-jee-main"]', timeout=20000)
        await page.click('[data-testid="exam-destination-pyq"]', force=True)
        await page.wait_for_selector('[data-testid="pyq-screen"]', timeout=20000)
        pyq_total_text = await page.locator('[data-testid="pyq-total"]').inner_text()
        print(f"STEP 4: JEE->PYQ total label = {pyq_total_text}")
        if "30" not in pyq_total_text:
            raise Exception(f"PYQ total is not 30 in label: {pyq_total_text}")

        await page.click('[data-testid="pyq-back-button"]', force=True)
        await page.wait_for_selector('[data-testid="exam-hub-jee-main"]', timeout=15000)
        await page.click('[data-testid="exam-hub-back-jee-main"]', force=True)
        await page.wait_for_selector('[data-testid="home-screen"]', timeout=20000)
        print("STEP 5: JEE flow validated")

        await page.click('[data-testid="home-tile-live"]', force=True)
        await page.wait_for_selector('[data-testid="series-hub"]', timeout=20000)
        print("STEP 6: Live Series opened")
        await page.go_back()
        await page.wait_for_selector('[data-testid="home-screen"]', timeout=20000)

        await page.click('[data-testid="home-tile-bitsat"]', force=True)
        await page.wait_for_selector('[data-testid="exam-hub-bitsat"]', timeout=20000)
        print("STEP 7: BITSAT hub opened")
        await page.click('[data-testid="exam-hub-back-bitsat"]', force=True)
        await page.wait_for_selector('[data-testid="home-screen"]', timeout=20000)

        await page.click('[data-testid="home-tile-comedk"]', force=True)
        await page.wait_for_selector('[data-testid="exam-hub-comedk"]', timeout=20000)
        print("STEP 8: COMEDK hub opened")
        await page.click('[data-testid="exam-hub-back-comedk"]', force=True)
        await page.wait_for_selector('[data-testid="home-screen"]', timeout=20000)

        toggle_count = await page.locator('[data-testid="home-series-shine-toggle"]').count()
        if toggle_count != 1:
            raise Exception(f"Expected shine toggle on home, got count={toggle_count}")
        shine_before = await page.locator('[data-testid="series-home-finish-shine"]').count()
        await page.click('[data-testid="home-series-shine-toggle"]', force=True)
        await page.wait_for_timeout(400)
        shine_paused = await page.locator('[data-testid="series-home-finish-shine"]').count()
        await page.click('[data-testid="home-series-shine-toggle"]', force=True)
        await page.wait_for_timeout(400)
        shine_resumed = await page.locator('[data-testid="series-home-finish-shine"]').count()
        print(f"STEP 9: Shine toggle before/pause/resume = {shine_before}/{shine_paused}/{shine_resumed}")
        if shine_before < 1 or shine_paused != 0 or shine_resumed < 1:
            raise Exception(f"Shine toggle mismatch: {shine_before}/{shine_paused}/{shine_resumed}")

        await page.emulate_media(reduced_motion='reduce')
        await page.reload(wait_until='domcontentloaded')
        await page.wait_for_selector('[data-testid="home-screen"]', timeout=25000)
        await page.wait_for_timeout(1000)
        reduced_toggle = await page.locator('[data-testid="home-series-shine-toggle"]').count()
        reduced_shine = await page.locator('[data-testid="series-home-finish-shine"]').count()
        print(f"STEP 10: Reduced motion toggle/shine = {reduced_toggle}/{reduced_shine}")
        if reduced_toggle != 0 or reduced_shine != 0:
            raise Exception(f"Reduced motion behavior mismatch: toggle={reduced_toggle}, shine={reduced_shine}")

        await page.screenshot(path="/app/test_reports/artifacts_iter36/t1_ui_flow/automation_output/20261026_180215_7d7c43d57f11/home_reduced_motion_375.jpeg", type="jpeg", quality=40, full_page=False)

        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*=\"error\"], [id*=\"error\"]'));
        return errorElements.map(el => el.textContent).join(', ');
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

        print("TEST PASSED")
    except Exception as e:
        print(f"TEST FAILED: {str(e)}")
        await page.screenshot(path="/app/test_reports/artifacts_iter36/t1_ui_flow/automation_output/20261026_180215_7d7c43d57f11/ui_flow_failure.jpeg", type="jpeg", quality=40, full_page=False)

