async def run_test(page, output_dir, page_url):
    page.on("console", lambda msg: print(f"CONSOLE: {msg.type}: {msg.text}"))

    try:
        await page.set_viewport_size({"width": 375, "height": 667})
        await page.wait_for_selector('[data-testid="privacy-screen"]', timeout=15000)

        try:
            await page.click('[data-testid="privacy-contact"]', force=True)
            await page.wait_for_timeout(1200)
            if await page.locator('[data-testid="privacy-link-error"]').count() > 0:
                link_error = await page.text_content('[data-testid="privacy-link-error"]')
                print(f"PASS: Contact error feedback visible: {link_error}")
            else:
                print("INFO: No contact-link error shown (platform may handle mailto)")
        except Exception as e:
            print(f"FAIL: contact link interaction failed: {str(e)}")

        try:
            await page.click('[data-testid="privacy-public-page"]', force=True)
            await page.wait_for_timeout(1200)
            if await page.locator('[data-testid="privacy-link-error"]').count() > 0:
                open_error = await page.text_content('[data-testid="privacy-link-error"]')
                print(f"INFO: Public-page open error shown: {open_error}")
            else:
                print("PASS: Public-page action did not trigger local error")
        except Exception as e:
            print(f"FAIL: public-page link interaction failed: {str(e)}")

        await page.screenshot(path="/app/test_reports/artifacts_iter50/ui_legal_links/automation_output/20261027_164839_a79aee9ed2e1/privacy_links_375.jpeg", type="jpeg", quality=40, full_page=False)

        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

    except Exception as e:
        print(f"FATAL: legal link test failed: {str(e)}")

