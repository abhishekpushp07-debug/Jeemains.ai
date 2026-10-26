async def run_test(page, output_dir, page_url):
    page.on("console", lambda msg: print(f"CONSOLE: {msg.type}: {msg.text}"))

    try:
        await page.set_viewport_size({"width": 390, "height": 844})
        print("Step 1: Opened jeelive.ai/login")
        await page.wait_for_timeout(1500)

        await page.wait_for_selector('input', timeout=15000)
        await page.locator('input').first.fill('9000000001')
        print("Step 2: Filled phone input")

        if await page.locator('button:has-text("Continue")').count() > 0:
            await page.locator('button:has-text("Continue")').first.click(force=True)
        elif await page.locator('button:has-text("Login")').count() > 0:
            await page.locator('button:has-text("Login")').first.click(force=True)
        else:
            await page.keyboard.press('Enter')
        print("Step 3: Triggered login submit")

        await page.wait_for_timeout(3500)
        print(f"Step 4: Current URL after login => {page.url}")

        pyq_payload = await page.evaluate("""async () => {
          const r = await fetch('/api/pyq/jee-main', { credentials: 'include' });
          const txt = await r.text();
          let body = null;
          try { body = JSON.parse(txt); } catch { body = txt.slice(0, 400); }
          return { status: r.status, body };
        }""")
        print(f"Step 5: /api/pyq/jee-main status => {pyq_payload['status']}")

        body = pyq_payload.get('body')
        if isinstance(body, dict):
          data = body.get('data', body)
          total = data.get('total') if isinstance(data, dict) else None
          years = data.get('years') if isinstance(data, dict) else None
          print(f"Step 6: PYQ total => {total}, years => {years}")
        else:
          print(f"Step 6: Non-JSON response snippet => {str(body)[:200]}")

        await page.screenshot(path='/app/test_reports/artifacts_iter33/automation_output/20261026_132732_d43b10f004ce/jeelive_login_trace.jpeg', type="jpeg", quality=40, full_page=False)
        print("Step 7: Captured website trace screenshot")

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

    except Exception as e:
        print(f"Website trace failed: {str(e)}")
        await page.screenshot(path='/app/test_reports/artifacts_iter33/automation_output/20261026_132732_d43b10f004ce/jeelive_login_trace_error.jpeg', type="jpeg", quality=40, full_page=False)

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")
