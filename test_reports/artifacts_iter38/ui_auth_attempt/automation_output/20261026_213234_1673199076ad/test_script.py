async def run_test(page, output_dir, page_url):
    import os

    try:
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.wait_for_selector('[data-testid="entry-screen"]', timeout=15000)

        phone = os.environ.get('JEELIVE_TEST_PHONE', '')
        pin = os.environ.get('JEELIVE_TEST_PIN', '')
        if not phone or not pin:
            print('STEP FAIL: secure env credentials missing in runtime')
        else:
            status_holder = {'code': None}

            async def on_response(resp):
                url = resp.url
                if '/auth/phone' in url and '/signup' not in url:
                    status_holder['code'] = resp.status

            page.on('response', on_response)
            await page.fill('[data-testid="entry-phone-input"]', phone)
            await page.fill('[data-testid="entry-pin-input"]', pin)
            await page.click('[data-testid="entry-continue-button"]', force=True)
            await page.wait_for_timeout(3000)

            code = status_holder['code']
            print(f'STEP INFO: login response status={code}')
            if code in [401, 429]:
                print('STEP STOP: credential flow rejected; halting further authenticated UI checks')
            elif code == 200:
                print('STEP PASS: credential login succeeded in browser session')
            else:
                print('STEP INFO: login status unresolved from network capture')

        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(', ');
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")
    except Exception as e:
        print(f'STEP FAIL: browser auth attempt failed: {str(e)}')
