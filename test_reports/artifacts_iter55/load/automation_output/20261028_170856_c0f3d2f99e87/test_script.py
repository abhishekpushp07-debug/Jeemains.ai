async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width":390,"height":844})
        await page.wait_for_timeout(3000)
        print('TESTIDS', await page.locator('[data-testid]').evaluate_all('(els)=>els.map(e=>({id:e.dataset.testid,text:e.innerText?.slice(0,100)}))'))
        await page.screenshot(path='/app/test_reports/artifacts_iter55/load/automation_output/20261028_170856_c0f3d2f99e87/entry.jpeg', type="jpeg", quality=40, full_page=False)
        print('PASS public preview loaded')
    except Exception as e:
        print('FAIL',str(e))
