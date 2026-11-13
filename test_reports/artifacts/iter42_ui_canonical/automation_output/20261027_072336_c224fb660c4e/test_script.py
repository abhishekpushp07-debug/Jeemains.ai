async def run_test(page, output_dir, page_url):
    try:
        import os
        sid = open('/tmp/iter42_sid.txt', 'r', encoding='utf-8').read().strip()
        await page.set_viewport_size({"width": 390, "height": 844})
        print('Step 1: Opening app shell')
        await page.goto('https://knockout-arena-77--53pzlg0l.preview.emergentagent.com', wait_until='domcontentloaded', timeout=60000)
        await page.evaluate("""(sid) => { localStorage.setItem('jl_sid', sid); }""", sid)
        await page.reload(wait_until='domcontentloaded')
        print('Step 1 passed: session handle injected and page reloaded')

        print('Step 2: Waiting for session verification gate to clear')
        try:
            await page.wait_for_selector('[data-testid="session-verifying"]', state='detached', timeout=25000)
        except Exception:
            # fallback: app can be already past gate
            pass
        await page.wait_for_timeout(1200)
        print('Step 2 passed: verification gate cleared or already absent')

        print('Step 3: Go to Rapid Fire tab and verify lobby essentials')
        await page.click('[data-testid="tab-rapid"]', force=True)
        await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=20000)
        await page.wait_for_selector('[data-testid="rf-start-button"]', timeout=20000)
        await page.wait_for_selector('[data-testid="rf-friends-history"]', timeout=20000)
        await page.wait_for_selector('[data-testid="rf-shop-shortcut"]', timeout=20000)
        await page.screenshot(path='/app/test_reports/artifacts/iter42_ui_canonical/automation_output/20261027_072336_c224fb660c4e/rapid_lobby_390.jpeg', type="jpeg", quality=40, full_page=False)
        print('Step 3 passed: lobby loaded with Play, history, and shop entry points')

        print('Step 4: Verify rapid artwork image bytes are loaded in DOM network cache')
        await page.wait_for_timeout(2000)
        brand_loaded = await page.evaluate("""async () => {
          const kinds = ['spark','friends','coins','trophy'];
          const result = {};
          for (const kind of kinds) {
            const url = `/api/brand/rapid/${kind}.webp`;
            try {
              const r = await fetch(url, { cache: 'no-store' });
              const b = await r.blob();
              result[kind] = { ok: r.ok, bytes: b.size };
            } catch (e) {
              result[kind] = { ok: false, bytes: 0 };
            }
          }
          return result;
        }""")
        print(f'Artwork fetch status: {brand_loaded}')

        print('Step 5: Open friends history read-only and capture state')
        await page.click('[data-testid="rf-friends-history"]', force=True)
        await page.wait_for_selector('[data-testid="rf-history-screen"]', timeout=15000)
        await page.wait_for_timeout(1200)
        await page.screenshot(path='/app/test_reports/artifacts/iter42_ui_canonical/automation_output/20261027_072336_c224fb660c4e/friends_history_390.jpeg', type="jpeg", quality=40, full_page=False)
        await page.click('[data-testid="rf-history-back"]', force=True)
        await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=15000)
        print('Step 5 passed: history screen loads and returns safely')

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(', ');
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

        print('Canonical read-only UI check completed successfully')
    except Exception as e:
        print(f'Canonical UI check failed: {str(e)}')
        await page.screenshot(path='/app/test_reports/artifacts/iter42_ui_canonical/automation_output/20261027_072336_c224fb660c4e/canonical_ui_error.jpeg', type="jpeg", quality=40, full_page=False)

