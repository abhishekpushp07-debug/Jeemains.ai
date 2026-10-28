async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({'width':390,'height':844})
        await page.wait_for_timeout(2000)
        print('SESSION available without another login',await page.locator('[data-testid="home-screen"]').is_visible())
        print('STORAGE key names only',await page.evaluate('Object.keys(localStorage)'))
        await page.context.storage_state(path='/tmp/iter55_browser_state.json')
    except Exception as e:
        print('FAIL session reuse inspection',str(e))
