async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 375, "height": 667})
        await page.wait_for_timeout(2000)
        await page.screenshot(path="/app/test_reports/artifacts_iter36/automation_output/20261026_175148_320286aa39a5/frontend_load_mobile375.jpeg", type="jpeg", quality=40, full_page=False)
        print("Frontend preview loaded for baseline screenshot")
    except Exception as e:
        print(f"Frontend load failed: {e}")
