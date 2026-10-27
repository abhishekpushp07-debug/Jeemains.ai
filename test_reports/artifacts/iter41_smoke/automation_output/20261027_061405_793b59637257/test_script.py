async def run_test(page, output_dir, page_url):
    page.on("console", lambda msg: print(f"CONSOLE: {msg.type}: {msg.text}"))
    try:
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.wait_for_timeout(1200)
        print("Page opened")
        await page.screenshot(path="/app/test_reports/artifacts/iter41_smoke/automation_output/20261027_061405_793b59637257/preview_smoke.jpeg", type="jpeg", quality=40, full_page=False)
        print("Smoke screenshot captured")
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*=\"error\"], [id*=\"error\"]'));
        return errorElements.map(el => el.textContent).join(', ');
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")
    except Exception as e:
        print(f"Smoke test failed: {str(e)}")
