async def run_test(page, output_dir, page_url):
    try:
        import re
        await page.set_viewport_size({"width": 390, "height": 844})
        print('Step 1: Open app and perform canonical sign-in if needed')
        await page.goto('https://revise-offline--6pwtbzuy.preview.emergentagent.com', wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(1200)

        # If login screen appears, use secure env file values without logging them
        entry_visible = await page.locator('[data-testid="entry-screen"]').is_visible()
        if entry_visible:
            env_text = open('/app/backend/.env', 'r', encoding='utf-8').read()
            phone = re.search(r'JEELIVE_TEST_PHONE="?([0-9]+)"?', env_text).group(1)
            pin = re.search(r'JEELIVE_TEST_PIN="?([0-9]+)"?', env_text).group(1)
            await page.fill('[data-testid="entry-phone-input"]', phone)
            await page.fill('[data-testid="entry-pin-input"]', pin)
            await page.click('[data-testid="entry-continue-button"]', force=True)
            print('Sign-in action submitted')

        try:
            await page.wait_for_selector('[data-testid="session-verifying"]', state='detached', timeout=25000)
        except Exception:
            pass

        await page.wait_for_selector('[data-testid="tab-rapid"]', timeout=30000)
        print('Step 1 passed: authenticated tabs available')

        print('Step 2: Open Rapid Fire lobby and verify core controls')
        await page.click('[data-testid="tab-rapid"]', force=True)
        await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=20000)
        await page.wait_for_selector('[data-testid="rf-start-button"]', timeout=20000)
        await page.wait_for_selector('[data-testid="rf-friends-history"]', timeout=20000)
        await page.wait_for_selector('[data-testid="rf-shop-shortcut"]', timeout=20000)
        await page.screenshot(path='/app/test_reports/artifacts/iter42_ui_canonical_login/automation_output/20261027_072429_557a6cc5dcc1/rapid_lobby_390.jpeg', type="jpeg", quality=40, full_page=False)
        print('Step 2 passed: lobby loaded')

        print('Step 3: Validate rapid artwork endpoints and bytes from browser')
        brand_loaded = await page.evaluate("""async () => {
          const kinds = ['spark','friends','coins','trophy'];
          const out = {};
          for (const kind of kinds) {
            try {
              const r = await fetch(`/api/brand/rapid/${kind}.webp`, { cache: 'no-store' });
              const b = await r.blob();
              out[kind] = { ok: r.ok, bytes: b.size };
            } catch (e) {
              out[kind] = { ok: false, bytes: 0 };
            }
          }
          return out;
        }""")
        print(f'Artwork check: {brand_loaded}')

        print('Step 4: Open Friends Fight history read-only')
        await page.click('[data-testid="rf-friends-history"]', force=True)
        await page.wait_for_selector('[data-testid="rf-history-screen"]', timeout=15000)
        await page.wait_for_timeout(1200)
        await page.screenshot(path='/app/test_reports/artifacts/iter42_ui_canonical_login/automation_output/20261027_072429_557a6cc5dcc1/friends_history_390.jpeg', type="jpeg", quality=40, full_page=False)
        await page.click('[data-testid="rf-history-back"]', force=True)
        await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=15000)
        print('Step 4 passed: history opened and closed')

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(', ');
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

        print('Canonical login + lobby/history verification complete')
    except Exception as e:
        print(f'Canonical login flow failed: {str(e)}')
        await page.screenshot(path='/app/test_reports/artifacts/iter42_ui_canonical_login/automation_output/20261027_072429_557a6cc5dcc1/canonical_login_error.jpeg', type="jpeg", quality=40, full_page=False)

