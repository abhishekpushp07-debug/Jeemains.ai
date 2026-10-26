async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 375, "height": 667})
        print("STEP 1: Mobile viewport set")

        await page.wait_for_selector('[data-testid="entry-phone-input"]', timeout=20000)
        await page.fill('[data-testid="entry-phone-input"]', '9000000001')
        await page.wait_for_timeout(300)
        await page.click('[data-testid="entry-continue-button"]', force=True)
        print("STEP 2: Login submitted")

        await page.wait_for_selector('[data-testid="home-screen"]', timeout=30000)
        await page.wait_for_timeout(1200)
        print("STEP 3: Home loaded")

        await page.screenshot(path="/app/test_reports/artifacts_iter36/t1_ui_cards/automation_output/20261026_180135_225c113175ef/home_after_login_375.jpeg", type="jpeg", quality=40, full_page=False)

        artwork_data = await page.evaluate("""() => {
          const ids = [
            ['jee-main','jee'],
            ['live','live'],
            ['bitsat','bitsat'],
            ['comedk','comedk'],
          ];
          const out = [];
          for (const [slug, kind] of ids) {
            const img = document.querySelector(`[data-testid=\"home-tile-${slug}-image\"]`);
            const art = document.querySelector(`[data-testid=\"home-tile-${slug}-original-artwork\"]`);
            const src = img ? (img.currentSrc || img.src || '') : '';
            const filter = img ? getComputedStyle(img).filter : '';
            const blend = img ? getComputedStyle(img).mixBlendMode : '';
            const has_svg_inside = art ? art.querySelectorAll('svg,path,[data-testid*=\"glyph\"]').length > 0 : false;
            out.push({slug, kind, src, filter, blend, has_svg_inside, has_img: !!img});
          }
          return out;
        }""")
        print(f"STEP 4: Artwork details: {artwork_data}")

        bad_art = [x for x in artwork_data if (not x.get('has_img')) or (f"/api/brand/cards/{x.get('kind')}.jpg" not in x.get('src',''))]
        if bad_art:
          raise Exception(f"Artwork source mismatch: {bad_art}")

        filtered = [x for x in artwork_data if x.get('filter') not in ('none', '')]
        if filtered:
          raise Exception(f"Unexpected image filters detected: {filtered}")

        if any(x.get('has_svg_inside') for x in artwork_data):
          raise Exception(f"Unexpected svg/icon overlay in artwork container: {artwork_data}")

        tile_shine_count = await page.locator('[data-testid$="-shine"][data-testid^="home-tile-"]').count()
        print(f"STEP 5: Tile shine elements count (should be 0): {tile_shine_count}")

        await page.click('[data-testid="home-tile-jee-main"]', force=True)
        await page.wait_for_selector('[data-testid="exam-hub-jee-main"]', timeout=20000)
        print("STEP 6: JEE hub opened")

        await page.click('[data-testid="exam-destination-pyq"]', force=True)
        await page.wait_for_selector('[data-testid="pyq-screen"]', timeout=20000)
        pyq_total_text = await page.locator('[data-testid="pyq-total"]').inner_text()
        print(f"STEP 7: PYQ total label: {pyq_total_text}")
        if "30" not in pyq_total_text:
          raise Exception(f"Expected 30 papers in PYQ label, got: {pyq_total_text}")

        await page.click('[data-testid="pyq-back-button"]', force=True)
        await page.wait_for_selector('[data-testid="exam-hub-jee-main"]', timeout=15000)
        await page.click('[data-testid="exam-hub-back-jee-main"]', force=True)
        await page.wait_for_selector('[data-testid="home-screen"]', timeout=20000)
        print("STEP 8: Returned home from JEE path")

        await page.click('[data-testid="home-tile-live"]', force=True)
        await page.wait_for_selector('[data-testid="series-hub"]', timeout=20000)
        print("STEP 9: Live Series opened")
        await page.go_back()
        await page.wait_for_selector('[data-testid="home-screen"]', timeout=20000)

        await page.click('[data-testid="home-tile-bitsat"]', force=True)
        await page.wait_for_selector('[data-testid="exam-hub-bitsat"]', timeout=20000)
        print("STEP 10: BITSAT hub opened")
        await page.click('[data-testid="exam-hub-back-bitsat"]', force=True)
        await page.wait_for_selector('[data-testid="home-screen"]', timeout=20000)

        await page.click('[data-testid="home-tile-comedk"]', force=True)
        await page.wait_for_selector('[data-testid="exam-hub-comedk"]', timeout=20000)
        print("STEP 11: COMEDK hub opened")
        await page.click('[data-testid="exam-hub-back-comedk"]', force=True)
        await page.wait_for_selector('[data-testid="home-screen"]', timeout=20000)

        toggle_count = await page.locator('[data-testid="home-series-shine-toggle"]').count()
        print(f"STEP 12: Shine toggle visible count: {toggle_count}")
        if toggle_count == 1:
          shine_before = await page.locator('[data-testid="series-home-finish-shine"]').count()
          await page.click('[data-testid="home-series-shine-toggle"]', force=True)
          await page.wait_for_timeout(400)
          shine_after_pause = await page.locator('[data-testid="series-home-finish-shine"]').count()
          await page.click('[data-testid="home-series-shine-toggle"]', force=True)
          await page.wait_for_timeout(400)
          shine_after_resume = await page.locator('[data-testid="series-home-finish-shine"]').count()
          print(f"STEP 13: Shine counts before/pause/resume = {shine_before}/{shine_after_pause}/{shine_after_resume}")
          if shine_before < 1 or shine_after_pause != 0 or shine_after_resume < 1:
            raise Exception(f"Shine toggle behavior mismatch: {shine_before}/{shine_after_pause}/{shine_after_resume}")

        await page.emulate_media(reduced_motion="reduce")
        await page.reload(wait_until="domcontentloaded")
        await page.wait_for_selector('[data-testid="home-screen"]', timeout=25000)
        await page.wait_for_timeout(800)
        reduced_toggle_count = await page.locator('[data-testid="home-series-shine-toggle"]').count()
        reduced_shine_count = await page.locator('[data-testid="series-home-finish-shine"]').count()
        print(f"STEP 14: Reduced motion toggle/shine counts = {reduced_toggle_count}/{reduced_shine_count}")
        if reduced_toggle_count != 0 or reduced_shine_count != 0:
          raise Exception(f"Reduced motion mismatch, toggle={reduced_toggle_count}, shine={reduced_shine_count}")

        await page.screenshot(path="/app/test_reports/artifacts_iter36/t1_ui_cards/automation_output/20261026_180135_225c113175ef/home_reduced_motion_375.jpeg", type="jpeg", quality=40, full_page=False)

        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*=\"error\"], [id*=\"error\"]'));
        return errorElements.map(el => el.textContent).join(', ');
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

        print("TEST PASSED: UI card/navigation/toggle checks completed")
    except Exception as e:
        print(f"TEST FAILED: {str(e)}")
        await page.screenshot(path="/app/test_reports/artifacts_iter36/t1_ui_cards/automation_output/20261026_180135_225c113175ef/ui_cards_failure.jpeg", type="jpeg", quality=40, full_page=False)

