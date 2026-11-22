async def run_test(page, output_dir, page_url):
    page.on("console", lambda msg: print(f"CONSOLE: {msg.type}: {msg.text}"))

    try:
        await page.set_viewport_size({"width": 375, "height": 667})

        # Step 1: Public entry stays usable while session bootstrap is pending.
        try:
            session_calls = {"count": 0}
            auth_posts = {"count": 0}

            async def pending_session(route):
                session_calls["count"] += 1
                await page.wait_for_timeout(6000)
                await route.fulfill(status=200, content_type="application/json", body='{"user":null}')

            async def watch_login(route):
                auth_posts["count"] += 1
                await route.continue_()

            await page.route("**/api/jl/auth/session", pending_session)
            await page.route("**/api/jl/auth/phone", watch_login)

            await page.goto("https://scale-engine-50k--0gu36hlx.preview.emergentagent.com/entry", wait_until="domcontentloaded")
            await page.wait_for_selector('[data-testid="entry-screen"]', timeout=15000)
            await page.fill('[data-testid="entry-phone-input"]', "7004186276")
            await page.fill('[data-testid="entry-pin-input"]', "5524")
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(400)
            await page.click('[data-testid="entry-continue-button"]', force=True)
            await page.wait_for_timeout(800)
            print(f"STEP1: session_calls={session_calls['count']}, auth_posts_while_pending={auth_posts['count']}")
            if auth_posts["count"] == 0:
                print("PASS: No PIN POST while bootstrap pending")
            else:
                print("FAIL: PIN POST fired during bootstrap pending")

            await page.click('[data-testid="entry-privacy-link"]', force=True)
            await page.wait_for_selector('[data-testid="privacy-screen"]', timeout=10000)
            print("PASS: Privacy page opened while session pending")

            await page.wait_for_timeout(6500)
            current_url = page.url
            print(f"STEP1 URL after delayed session resolve: {current_url}")
            if "/privacy" in current_url:
                print("PASS: Late session resolve did not hijack privacy route")
            else:
                print("FAIL: Privacy route got hijacked")

            await page.unroute("**/api/jl/auth/session", pending_session)
            await page.unroute("**/api/jl/auth/phone", watch_login)
        except Exception as e:
            print(f"FAIL step1 pending bootstrap test: {str(e)}")

        # Step 2: Public legal pages are reachable directly without login.
        try:
            await page.goto("https://scale-engine-50k--0gu36hlx.preview.emergentagent.com/privacy", wait_until="domcontentloaded")
            await page.wait_for_selector('[data-testid="privacy-screen"]', timeout=10000)
            await page.wait_for_selector('[data-testid="privacy-contact-email"]', timeout=10000)
            email_text = await page.text_content('[data-testid="privacy-contact-email"]')
            print(f"STEP2 email text: {email_text}")

            await page.goto("https://scale-engine-50k--0gu36hlx.preview.emergentagent.com/delete-account", wait_until="domcontentloaded")
            await page.wait_for_selector('[data-testid="delete-account-screen"]', timeout=10000)
            await page.wait_for_selector('[data-testid="delete-account-status"]', timeout=10000)
            status_text = await page.text_content('[data-testid="delete-account-status"]')
            print(f"STEP2 deletion status: {status_text}")
            await page.screenshot(path="/app/test_reports/artifacts_iter50/ui_auth_gate/automation_output/20261027_164807_815b5f6aca76/public_legal_375.jpeg", type="jpeg", quality=40, full_page=False)
        except Exception as e:
            print(f"FAIL step2 public legal direct routes: {str(e)}")

        # Step 3: Anonymous private route gets guarded back to entry.
        try:
            async def anonymous_session(route):
                await route.fulfill(status=200, content_type="application/json", body='{"user":null}')

            await page.route("**/api/jl/auth/session", anonymous_session)
            await page.goto("https://scale-engine-50k--0gu36hlx.preview.emergentagent.com/performance", wait_until="domcontentloaded")
            await page.wait_for_timeout(2500)
            guarded_url = page.url
            print(f"STEP3 guarded URL: {guarded_url}")
            if "/entry" in guarded_url:
                print("PASS: Private route blocked for anonymous user")
            else:
                print("FAIL: Private route not blocked for anonymous user")
            await page.wait_for_selector('[data-testid="entry-screen"]', timeout=10000)
            await page.unroute("**/api/jl/auth/session", anonymous_session)
        except Exception as e:
            print(f"FAIL step3 private route guard: {str(e)}")

        # Step 4: One live sign-in attempt (max one) to verify normal flow.
        try:
            await page.goto("https://scale-engine-50k--0gu36hlx.preview.emergentagent.com/entry", wait_until="domcontentloaded")
            await page.wait_for_selector('[data-testid="entry-screen"]', timeout=15000)
            await page.fill('[data-testid="entry-phone-input"]', "7004186276")
            await page.fill('[data-testid="entry-pin-input"]', "5524")
            await page.click('[data-testid="entry-continue-button"]', force=True)
            await page.wait_for_timeout(5000)

            if await page.locator('[data-testid="entry-error"]').count() > 0:
                err = await page.text_content('[data-testid="entry-error"]')
                print(f"STEP4 entry error text: {err}")

            current_url = page.url
            print(f"STEP4 live login URL: {current_url}")
            if "/(tabs)" in current_url or current_url.rstrip('/').endswith('.com'):
                print("PASS: Live login appears successful")
            else:
                print("INFO: Live login did not navigate to tabs in this run")
            await page.screenshot(path="/app/test_reports/artifacts_iter50/ui_auth_gate/automation_output/20261027_164807_815b5f6aca76/live_login_state.jpeg", type="jpeg", quality=40, full_page=False)
        except Exception as e:
            print(f"FAIL step4 live login attempt: {str(e)}")

        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

    except Exception as e:
        print(f"FATAL: UI auth/public flow test failed: {str(e)}")
        await page.screenshot(path="/app/test_reports/artifacts_iter50/ui_auth_gate/automation_output/20261027_164807_815b5f6aca76/fatal_auth_gate_error.jpeg", type="jpeg", quality=40, full_page=False)

