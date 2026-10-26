async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 375, "height": 667})
        await page.wait_for_selector('[data-testid="entry-phone-input"]', timeout=20000)
        await page.fill('[data-testid="entry-phone-input"]', '9000000001')
        await page.click('[data-testid="entry-continue-button"]', force=True)
        await page.wait_for_selector('[data-testid="home-screen"]', timeout=25000)
        await page.wait_for_timeout(1200)

        dom_info = await page.evaluate("""() => {
          const el = document.querySelector('[data-testid="home-tile-jee-main-image"]');
          const wrap = document.querySelector('[data-testid="home-tile-jee-main-original-artwork"]');
          return {
            tag: el ? el.tagName : null,
            attrs: el ? Array.from(el.attributes).map(a => [a.name, a.value]) : [],
            style: el ? getComputedStyle(el).cssText : '',
            outer: el ? el.outerHTML.slice(0, 500) : '',
            wrap_outer: wrap ? wrap.outerHTML.slice(0, 800) : '',
          };
        }""")
        print(f"DOM INFO: {dom_info}")

        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*=\"error\"], [id*=\"error\"]'));
        return errorElements.map(el => el.textContent).join(', ');
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")
    except Exception as e:
        print(f"TEST FAILED: {str(e)}")

