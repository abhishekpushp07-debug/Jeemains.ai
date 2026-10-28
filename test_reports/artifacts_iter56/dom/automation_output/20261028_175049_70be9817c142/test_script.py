async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({'width':390,'height':844})
        print('URL',page.url)
        print('TESTIDS',await page.locator('[data-testid]').evaluate_all('(els)=>els.map(e=>({tag:e.tagName,id:e.getAttribute("data-testid")}))'))
        print('ROOT',await page.locator('#root').get_attribute('data-testid'))
        print('HTML', (await page.content())[:6000])
        print('PASS DOM inspected')
    except Exception as e:
        print('FAIL DOM',repr(e))
