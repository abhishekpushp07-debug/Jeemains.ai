async def run_test(page, output_dir, page_url):
    try:
        # 390 mobile checks
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.wait_for_selector('[data-testid="entry-screen"]', timeout=15000)
        print('STEP PASS: entry screen visible at 390')

        # PIN is masked by default + toggle exists
        pin_input = page.locator('[data-testid="entry-pin-input"]')
        await pin_input.fill('0123')
        pin_type_before = await pin_input.get_attribute('type')
        print(f'STEP INFO: PIN input type before toggle: {pin_type_before}')
        await page.click('[data-testid="entry-pin-input-visibility"]', force=True)
        await page.wait_for_timeout(250)
        pin_type_after = await pin_input.get_attribute('type')
        print(f'STEP INFO: PIN input type after toggle: {pin_type_after}')
        print('STEP PASS: PIN visibility toggle clickable')

        # leading zero retained
        pin_value = await pin_input.input_value()
        assert pin_value == '0123'
        print('STEP PASS: leading zero retained in PIN')

        # switch tabs clears pin
        await page.click('[data-testid="entry-tab-signup"]', force=True)
        await page.wait_for_timeout(200)
        await page.click('[data-testid="entry-tab-login"]', force=True)
        await page.wait_for_timeout(200)
        pin_after_switch = await pin_input.input_value()
        assert pin_after_switch == ''
        print('STEP PASS: switching tabs clears PIN input')

        # signup mismatch should be blocked client-side before submit
        await page.click('[data-testid="entry-tab-signup"]', force=True)
        await page.wait_for_timeout(200)
        await page.fill('[data-testid="entry-phone-input"]', '123')
        await page.fill('[data-testid="entry-pin-input"]', '1234')
        await page.fill('[data-testid="entry-confirm-pin-input"]', '5678')
        submit_disabled = await page.locator('[data-testid="entry-continue-button"]').is_disabled()
        print(f'STEP INFO: signup continue disabled={submit_disabled}')
        assert submit_disabled is True
        print('STEP PASS: invalid signup blocked before POST via disabled CTA')

        # forgot PIN route and return
        await page.click('[data-testid="entry-tab-login"]', force=True)
        await page.wait_for_timeout(200)
        await page.click('[data-testid="entry-forgot-pin"]', force=True)
        await page.wait_for_selector('[data-testid="forgot-pin-screen"]', timeout=10000)
        print('STEP PASS: forgot PIN route opens')
        website_btn_visible = await page.locator('[data-testid="forgot-pin-website-button"]').is_visible()
        print(f'STEP INFO: website button visible={website_btn_visible}')
        await page.click('[data-testid="forgot-pin-login-button"]', force=True)
        await page.wait_for_selector('[data-testid="entry-screen"]', timeout=10000)
        print('STEP PASS: return from forgot PIN reaches entry screen')

        # 320 viewport smoke
        await page.set_viewport_size({"width": 320, "height": 700})
        await page.wait_for_timeout(400)
        await page.wait_for_selector('[data-testid="entry-screen"]', timeout=10000)
        print('STEP PASS: entry screen visible at 320')
        await page.screenshot(path='/app/test_reports/artifacts_iter38/ui_public_flows/automation_output/20261026_213210_8a4916739e1c/entry-320.jpeg', type="jpeg", quality=40, full_page=False)

        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(', ');
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

    except Exception as e:
        print(f'STEP FAIL: {str(e)}')
        await page.screenshot(path='/app/test_reports/artifacts_iter38/ui_public_flows/automation_output/20261026_213210_8a4916739e1c/ui-public-fail.jpeg', type="jpeg", quality=40, full_page=False)
